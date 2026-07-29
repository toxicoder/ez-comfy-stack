#!/usr/bin/env bash
#
# ## install-comfy
#
# Idempotent installer for ComfyUI, Python deps, custom nodes, and model links.
#
# Purpose:
#   Populate the comfy-state volume on first container start (or when the install
#   stamp is missing). Clones ComfyUI, creates a venv, installs PyTorch (cu130
#   when available), Comfy requirements, Manager + Nunchaku nodes (fail-soft),
#   links $MODELS_ROOT/comfy/* into ComfyUI/models/*, and applies the Spark
#   free-memory patch.
#
#   For Docker layer caching, phases can be run alone so multi-GB torch stays
#   cached when only Comfy or custom-node steps change:
#     install-comfy.sh --phase venv|torch|comfy|nodes|finalize
#   Default (no --phase): full cold install or stamp-based refresh.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   Sourcable for hermetic BATS via source guard at bottom.
#
# Environment:
#   COMFY_HOME, COMFY_USER, MODELS_ROOT — defaults below
#   COMFYUI_REF — optional git ref for ComfyUI clone (default: empty = default branch)
#
set -euo pipefail

COMFY_HOME="${COMFY_HOME:-/comfy-state/ComfyUI}"
COMFY_USER="${COMFY_USER:-0}"
MODELS_ROOT="${MODELS_ROOT:-/models}"
STAMP="${COMFY_HOME}/.lab-install-complete"
VENV="${COMFY_HOME}/.venv"
# Install wall-clock start (unix seconds); set in main
INSTALL_T0="${INSTALL_T0:-}"
COMFYUI_REPO="${COMFYUI_REPO:-https://github.com/comfyanonymous/ComfyUI.git}"
COMFYUI_REF="${COMFYUI_REF:-}"

#######################################
# Log an install progress line to stdout (container logs).
# Globals:
#   None
# Arguments:
#   $@ - Message fragments
# Outputs:
#   Writes to stdout
# Returns:
#   0
#######################################
log() {
  echo "[comfy-install] $*"
}

#######################################
# Log an install warning to stderr.
# Globals:
#   None
# Arguments:
#   $@ - Warning fragments
# Outputs:
#   Writes to stderr
# Returns:
#   0
#######################################
warn() {
  echo "[comfy-install] WARN: $*" >&2
}

#######################################
# Elapsed seconds since INSTALL_T0 (or 0 if unset).
# Globals:
#   INSTALL_T0
# Arguments:
#   None
# Outputs:
#   Integer seconds on stdout
# Returns:
#   0
#######################################
install_elapsed_s() {
  local now
  now="$(date +%s)"
  if [[ -z ${INSTALL_T0} ]]; then
    echo 0
    return 0
  fi
  echo $((now - INSTALL_T0))
}

#######################################
# Format seconds as m:ss or h:mm:ss for install logs.
# Globals:
#   None
# Arguments:
#   $1  Seconds
# Outputs:
#   Human elapsed on stdout
# Returns:
#   0
#######################################
install_format_elapsed() {
  local secs="${1:-0}" h m s
  if [[ ${secs} -lt 0 ]]; then
    secs=0
  fi
  h=$((secs / 3600))
  m=$(((secs % 3600) / 60))
  s=$((secs % 60))
  if [[ ${h} -gt 0 ]]; then
    printf '%d:%02d:%02d' "${h}" "${m}" "${s}"
  else
    printf '%d:%02d' "${m}" "${s}"
  fi
}

#######################################
# Numbered phase banner with elapsed time.
# Globals:
#   INSTALL_T0
# Arguments:
#   $1  Step number
#   $2  Total steps
#   $3+ Message
# Outputs:
#   Progress log line
# Returns:
#   0
#######################################
step() {
  local n="${1:?}"
  local total="${2:?}"
  shift 2
  log "══ step ${n}/${total} ══ $*  [elapsed $(install_format_elapsed "$(install_elapsed_s)")]"
}

#######################################
# Run pip with unbuffered output and progress bar when available.
# Globals:
#   None
# Arguments:
#   $@  Passed to pip
# Outputs:
#   pip stdout/stderr; short log of the command
# Returns:
#   pip exit status
#######################################
pip_install() {
  local -a cmd=(pip install)
  export PYTHONUNBUFFERED=1
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  # Prefer progress bar when this pip supports it
  if pip install --help 2>&1 | grep -q -- '--progress-bar'; then
    cmd+=(--progress-bar on)
  fi
  log "pip: ${*}"
  "${cmd[@]}" "$@"
}

#######################################
# Activate the ComfyUI venv if present.
# Globals:
#   VENV
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if activated or activate missing (no-op); non-zero if required and missing
#######################################
activate_venv() {
  # shellcheck disable=SC1091
  if [[ -f "${VENV}/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "${VENV}/bin/activate"
  fi
}

#######################################
# Clone or update a ComfyUI custom node and install its requirements.
# Globals:
#   CUSTOM — custom_nodes directory (must be set by caller)
# Arguments:
#   $1 - Git URL
#   $2 - Directory name under CUSTOM
# Outputs:
#   Progress via log/warn
# Returns:
#   0 even on soft failures (clone/pip may warn and continue)
#######################################
clone_node() {
  local url="${1}"
  local name="${2}"
  log "custom node: begin ${name}"
  if [[ ! -d "${CUSTOM}/${name}/.git" ]]; then
    log "custom node: cloning ${name}…"
    git clone --depth 1 "${url}" "${CUSTOM}/${name}" || warn "clone failed: ${name}"
  else
    log "custom node: updating ${name}…"
    git -C "${CUSTOM}/${name}" pull --ff-only || true
  fi
  if [[ -f "${CUSTOM}/${name}/requirements.txt" ]]; then
    log "custom node: pip requirements for ${name}…"
    pip_install -r "${CUSTOM}/${name}/requirements.txt" || warn "requirements failed: ${name}"
  fi
  log "custom node: done ${name}"
}

#######################################
# Symlink a Comfy models subdir to the host cache under MODELS_ROOT/comfy.
# Host MODELS_ROOT/comfy is the source of truth for weights (download-models).
# Always retarget COMFY_HOME/models/<sub> → host dir so prebuilt/seeded trees
# cannot leave a real directory that hides host files from ComfyUI.
# Globals:
#   MODELS_ROOT, COMFY_HOME
# Arguments:
#   $1 - Subdirectory name (e.g. diffusion_models)
# Outputs:
#   Log line when (re)linked
# Returns:
#   0
#######################################
link_models() {
  local sub="${1}"
  local host_dir="${MODELS_ROOT}/comfy/${sub}"
  local comfy_dir="${COMFY_HOME}/models/${sub}"
  local target=""
  mkdir -p "${host_dir}" "${COMFY_HOME}/models"

  # Already correctly linked?
  if [[ -L ${comfy_dir} ]]; then
    target="$(readlink -f "${comfy_dir}" 2>/dev/null || readlink "${comfy_dir}" || true)"
    if [[ ${target} == "$(readlink -f "${host_dir}" 2>/dev/null || echo "${host_dir}")" ]] ||
      [[ ${target} == "${host_dir}" ]]; then
      return 0
    fi
    log "retarget models/${sub} → ${host_dir} (was symlink → ${target})"
    rm -f "${comfy_dir}" 2>/dev/null || true
  elif [[ -d ${comfy_dir} ]]; then
    # Real dir (even non-empty) blocks host weights — move aside once
    if [[ -n "$(ls -A "${comfy_dir}" 2>/dev/null || true)" ]]; then
      local bak
      bak="${comfy_dir}.bak.$(date +%s)"
      log "moving non-empty models/${sub} aside → ${bak} (host weights take over)"
      mv "${comfy_dir}" "${bak}" 2>/dev/null || rm -rf "${comfy_dir}" 2>/dev/null || true
    else
      rmdir "${comfy_dir}" 2>/dev/null || rm -rf "${comfy_dir}" 2>/dev/null || true
    fi
  elif [[ -e ${comfy_dir} ]]; then
    rm -f "${comfy_dir}" 2>/dev/null || true
  fi

  ln -sfn "${host_dir}" "${comfy_dir}"
  log "link models/${sub} → ${host_dir}"
}

#######################################
# Strip bloat from a prebuilt Comfy tree (image size / seed speed).
# Removes VCS metadata, bytecode caches, and common non-runtime dirs.
# Safe for runtime: does not delete Python packages or model links.
# Globals:
#   None
# Arguments:
#   $1 - Root directory (default: COMFY_HOME)
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
strip_prebuilt() {
  local root="${1:-${COMFY_HOME}}"
  if [[ ! -d ${root} ]]; then
    warn "strip_prebuilt: not a directory: ${root}"
    return 0
  fi
  log "strip_prebuilt: cleaning ${root}"
  # Git metadata from shallow clones (ComfyUI + custom nodes)
  find "${root}" -type d -name '.git' -prune -exec rm -rf {} + 2>/dev/null || true
  # Bytecode / test caches
  find "${root}" \( -type d -name '__pycache__' -o -type d -name '.pytest_cache' \
    -o -type d -name '.mypy_cache' \) -prune -exec rm -rf {} + 2>/dev/null || true
  find "${root}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
  # Pip cache if install used a local cache under the tree
  rm -rf "${root}/.cache" 2>/dev/null || true
  if command -v pip >/dev/null 2>&1; then
    # Purge in-tree/user cache only when not using a BuildKit cache mount path
    # that operators may want to retain across Docker layers.
    if [[ ${LAB_KEEP_PIP_CACHE:-0} != "1" ]]; then
      pip cache purge >/dev/null 2>&1 || true
    fi
  fi
  log "strip_prebuilt: done"
}

#######################################
# Clone or update ComfyUI into COMFY_HOME.
# Globals:
#   COMFY_HOME, COMFYUI_REPO, COMFYUI_REF
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success; non-zero if clone fails under set -e
#######################################
phase_clone_comfy() {
  local -a clone_args=(--depth 1)
  if [[ -n ${COMFYUI_REF} ]]; then
    clone_args+=(--branch "${COMFYUI_REF}")
  fi
  if [[ ! -d "${COMFY_HOME}/.git" ]]; then
    mkdir -p "$(dirname "${COMFY_HOME}")"
    # Destination may already exist (empty volume + old workflow bind mount created
    # intermediate dirs). git clone refuses non-empty targets — clone then merge.
    if [[ -d ${COMFY_HOME} && -n "$(ls -A "${COMFY_HOME}" 2>/dev/null || true)" ]]; then
      local tmp_clone
      tmp_clone="$(mktemp -d)"
      log "git clone (temp) then merge into existing ${COMFY_HOME}…"
      git clone "${clone_args[@]}" "${COMFYUI_REPO}" "${tmp_clone}/ComfyUI"
      if command -v rsync >/dev/null 2>&1; then
        rsync -a "${tmp_clone}/ComfyUI/" "${COMFY_HOME}/"
      else
        cp -a "${tmp_clone}/ComfyUI/." "${COMFY_HOME}/"
      fi
      rm -rf "${tmp_clone}"
    else
      log "git clone into ${COMFY_HOME}…"
      git clone "${clone_args[@]}" "${COMFYUI_REPO}" "${COMFY_HOME}"
    fi
  else
    log "ComfyUI tree present; pulling latest (best-effort)"
    git -C "${COMFY_HOME}" pull --ff-only || warn "git pull failed; continuing"
  fi
}

#######################################
# Create venv and upgrade pip tooling (Docker phase: venv).
# Globals:
#   COMFY_HOME, VENV
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0 on success
#######################################
phase_venv() {
  mkdir -p "$(dirname "${COMFY_HOME}")" "${COMFY_HOME}"
  if [[ ! -d ${VENV} ]]; then
    log "python3 -m venv ${VENV}"
    python3 -m venv "${VENV}"
  else
    log "venv already exists"
  fi
  activate_venv
  pip_install -U pip setuptools wheel
}

#######################################
# Install PyTorch wheels (Docker phase: torch). Multi-GB; rare invalidation.
# Globals:
#   VENV
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success
#######################################
phase_torch() {
  activate_venv
  log "Expect large wheels (torch + cuda toolkit + cudnn); progress bars below…"
  pip_install --upgrade torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu130 || {
    warn "cu130 index failed; falling back to default PyPI torch"
    pip_install --upgrade torch torchvision torchaudio
  }
}

#######################################
# Clone ComfyUI and install requirements + hub extras (Docker phase: comfy).
# Globals:
#   COMFY_HOME, VENV
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0 on success
#######################################
phase_comfy() {
  phase_clone_comfy
  activate_venv
  pip_install -r "${COMFY_HOME}/requirements.txt"
  pip_install psutil huggingface_hub safetensors einops
}

#######################################
# Install custom nodes and optional packages (Docker phase: nodes).
# Globals:
#   COMFY_HOME, VENV, CUSTOM
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 (soft-fail optional packages)
#######################################
#######################################
# True if the installed nunchaku package looks like the real SVDQuant engine.
# Globals:
#   None (uses active venv python)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if real nunchaku; 1 if missing or wrong PyPI stats package
#######################################
nunchaku_is_real() {
  python - <<'PY' 2>/dev/null
import importlib.util
import sys

if importlib.util.find_spec("nunchaku") is None:
    sys.exit(1)
try:
    import nunchaku

    # Real engine exposes model classes; PyPI "nunchaku" is unrelated Bayesian stats
    if hasattr(nunchaku, "NunchakuFluxTransformer2dModel") or hasattr(nunchaku, "NunchakuT5EncoderModel"):
        sys.exit(0)
    if importlib.util.find_spec("nunchaku.models") is not None:
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PY
}

#######################################
# Remove the wrong PyPI "nunchaku" stats package if present (not SVDQuant).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft)
#######################################
cleanup_wrong_nunchaku() {
  if ! python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('nunchaku') else 1)" 2>/dev/null; then
    return 0
  fi
  if nunchaku_is_real; then
    return 0
  fi
  warn "Removing wrong PyPI 'nunchaku' package (stats lib, not SVDQuant engine)"
  pip uninstall -y nunchaku >/dev/null 2>&1 || true
}

#######################################
# Map machine arch to manylinux wheel platform tag used by nunchaku releases.
# Globals:
#   None
# Arguments:
#   $1  Machine arch (e.g. from uname -m: x86_64, aarch64)
# Outputs:
#   Platform tag on stdout (empty if unsupported)
# Returns:
#   0
#######################################
nunchaku_platform_tag() {
  local arch="${1:?nunchaku_platform_tag requires arch}"
  case "${arch}" in
    x86_64 | amd64) echo "linux_x86_64" ;;
    aarch64 | arm64) echo "linux_aarch64" ;;
    *) echo "" ;;
  esac
}

#######################################
# Build a candidate GitHub release wheel URL for nunchaku (no network).
# Globals:
#   NUNCHAKU_VERSION — default 1.2.1
# Arguments:
#   $1  Platform tag (linux_x86_64, …)
#   $2  Python tag (cp312)
#   $3  CUDA tag (cu13.0)
#   $4  Torch tag (torch2.11)
# Outputs:
#   URL on stdout
# Returns:
#   0
#######################################
nunchaku_wheel_url() {
  local plat="${1}"
  local py_tag="${2}"
  local cu_tag="${3}"
  local torch_tag="${4}"
  local ver="${NUNCHAKU_VERSION:-1.2.1}"
  local wheel="nunchaku-${ver}+${cu_tag}${torch_tag}-${py_tag}-${py_tag}-${plat}.whl"
  echo "https://github.com/nunchaku-ai/nunchaku/releases/download/v${ver}/${wheel}"
}

#######################################
# Install real nunchaku from GitHub wheels only (never bare PyPI nunchaku).
# Lab workflows use core loaders; this is fail-soft optional acceleration.
# Globals:
#   NUNCHAKU_VERSION, NUNCHAKU_WHEEL_URL (optional full override)
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_nunchaku_wheel() {
  local plat py_tag torch_mm cu_tag torch_tag url
  local -a torch_cands cu_cands

  cleanup_wrong_nunchaku
  if nunchaku_is_real; then
    log "nunchaku already installed (real engine)"
    return 0
  fi

  if [[ -n ${NUNCHAKU_WHEEL_URL:-} ]]; then
    log "Installing nunchaku from NUNCHAKU_WHEEL_URL"
    if pip_install "${NUNCHAKU_WHEEL_URL}"; then
      log "nunchaku wheel install ok"
      return 0
    fi
    warn "nunchaku wheel install failed from NUNCHAKU_WHEEL_URL (optional)"
    return 0
  fi

  plat="$(nunchaku_platform_tag "$(uname -m)")"
  if [[ -z ${plat} ]]; then
    warn "nunchaku: unsupported arch $(uname -m); skipping (optional)"
    return 0
  fi
  # Official v1.2.1 release assets are linux_x86_64 / win_amd64 only — no aarch64
  if [[ ${plat} == "linux_aarch64" ]]; then
    warn "nunchaku: no official linux_aarch64 wheels (GB10/Spark) — skipping"
    warn "lab-flux/lab-ltx graphs use core UNET/CLIP/VAE loaders and do not need nunchaku"
    return 0
  fi

  py_tag="$(python -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")' 2>/dev/null || echo "cp312")"
  torch_mm="$(python -c 'import torch; v=torch.__version__.split("+")[0].split("."); print(f"{v[0]}.{v[1]}")' 2>/dev/null || echo "2.11")"
  # Prefer exact torch minor, then published nunchaku wheel train
  torch_cands=("${torch_mm}" "2.11" "2.10" "2.9")
  cu_cands=("cu13.0" "cu12.8")

  local t c tried=0
  for t in "${torch_cands[@]}"; do
    torch_tag="torch${t}"
    for c in "${cu_cands[@]}"; do
      cu_tag="${c}"
      url="$(nunchaku_wheel_url "${plat}" "${py_tag}" "${cu_tag}" "${torch_tag}")"
      tried=$((tried + 1))
      log "Trying nunchaku wheel: ${url}"
      if pip_install "${url}"; then
        if nunchaku_is_real; then
          log "nunchaku wheel install ok (${cu_tag}${torch_tag})"
          return 0
        fi
        warn "Installed wheel but import check failed; uninstalling"
        pip uninstall -y nunchaku >/dev/null 2>&1 || true
      fi
    done
  done
  warn "nunchaku wheel not available for ${plat}/${py_tag}/torch${torch_mm} after ${tried} tries (optional)"
  warn "Do not pip install bare 'nunchaku' from PyPI — that is an unrelated stats package"
  return 0
}

phase_nodes() {
  activate_venv
  CUSTOM="${COMFY_HOME}/custom_nodes"
  mkdir -p "${CUSTOM}"
  clone_node "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"
  clone_node "https://github.com/mit-han-lab/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
    clone_node "https://github.com/nunchaku-tech/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
    clone_node "https://github.com/nunchaku-ai/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
    warn "Nunchaku custom node unavailable"
  pip_install sageattention || warn "SageAttention pip install failed (optional on aarch64)"
  install_nunchaku_wheel
}

#######################################
# Link all standard Comfy model subdirs to MODELS_ROOT/comfy.
# Globals:
#   MODELS_ROOT, COMFY_HOME
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
link_all_models() {
  local sub
  for sub in checkpoints diffusion_models text_encoders vae loras clip clip_vision \
    unet controlnet embeddings upscale_models audio_encoders; do
    link_models "${sub}"
  done
  log "model links done"
}

#######################################
# Apply Spark free-memory patch when the script is present in the image.
# Globals:
#   COMFY_HOME
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 (patch failures are soft)
#######################################
apply_free_memory_patch() {
  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${COMFY_HOME}" || warn "patch failed"
  else
    warn "patch_get_free_memory.py not found in image"
  fi
}

#######################################
# Stamp, strip, link models, optional patch (Docker phase: finalize).
# Globals:
#   COMFY_HOME, STAMP, VENV
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
phase_finalize() {
  activate_venv
  touch "${STAMP}"
  log "Wrote install stamp ${STAMP}"
  strip_prebuilt "${COMFY_HOME}"
  link_all_models
  apply_free_memory_patch
}

#######################################
# Run a single named install phase (Docker layer cache entrypoint).
# Globals:
#   COMFY_HOME, VENV, MODELS_ROOT, STAMP
# Arguments:
#   $1  Phase name: venv|torch|comfy|nodes|finalize
# Outputs:
#   Progress via log
# Returns:
#   0 on success; 2 on unknown phase
#######################################
run_install_phase() {
  local phase="${1:?phase name required}"
  case "${phase}" in
    venv) phase_venv ;;
    torch) phase_torch ;;
    comfy) phase_comfy ;;
    nodes) phase_nodes ;;
    finalize) phase_finalize ;;
    *)
      warn "unknown phase: ${phase} (expected venv|torch|comfy|nodes|finalize)"
      return 2
      ;;
  esac
}

#######################################
# Parse CLI for optional --phase NAME.
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   Sets INSTALL_PHASE via nameref-style echo to caller pattern — use globals
#   INSTALL_PHASE (empty = full install path)
# Returns:
#   0 on success; 2 on bad usage
#######################################
parse_install_args() {
  INSTALL_PHASE=""
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --phase)
        if [[ $# -lt 2 || -z ${2} ]]; then
          warn "usage: install-comfy.sh [--phase venv|torch|comfy|nodes|finalize]"
          return 2
        fi
        INSTALL_PHASE="${2}"
        shift 2
        ;;
      -h | --help)
        log "usage: install-comfy.sh [--phase venv|torch|comfy|nodes|finalize]"
        return 1
        ;;
      *)
        warn "unknown argument: ${1}"
        warn "usage: install-comfy.sh [--phase venv|torch|comfy|nodes|finalize]"
        return 2
        ;;
    esac
  done
  return 0
}

#######################################
# Full install or refresh path for ComfyUI on the comfy-state volume.
# Globals:
#   COMFY_HOME, COMFY_USER, MODELS_ROOT, STAMP, VENV, INSTALL_PHASE
# Arguments:
#   $@  Optional --phase NAME for single Docker-cacheable phase
# Outputs:
#   Progress logs
# Returns:
#   0 on success; non-zero if a hard step fails under set -e
#######################################
main() {
  local total=12 refresh=0
  export DEBIAN_FRONTEND=noninteractive
  export PYTHONUNBUFFERED=1
  INSTALL_T0="$(date +%s)"
  INSTALL_PHASE=""
  parse_install_args "$@" || return $?

  log "Install started at $(date -u +%Y-%m-%dT%H:%MZ)"
  log "Markers: ══ step N/M ══ — pip shows multi-GB wheel bars when downloading"

  # Single phase (Dockerfile multi-layer prebuild) — never take refresh short-circuit
  if [[ -n ${INSTALL_PHASE} ]]; then
    log "Docker phase: ${INSTALL_PHASE}"
    run_install_phase "${INSTALL_PHASE}"
    log "══ Phase ${INSTALL_PHASE} complete ══ elapsed $(install_format_elapsed "$(install_elapsed_s)")"
    return 0
  fi

  if [[ -f ${STAMP} && -x "${VENV}/bin/python" ]]; then
    refresh=1
    total=3
    log "Install stamp present — fast refresh (3 steps; cold install skipped)"
  else
    log "Cold install path (~10–30+ min common on first start)"
  fi

  if [[ ${refresh} -eq 0 ]]; then
    # Order matches Docker phased layers: venv → torch → comfy → nodes → finalize
    step 1 "${total}" "Create Python venv + upgrade pip tooling"
    phase_venv
    log "step 1 done"

    step 2 "${total}" "Install PyTorch (cu130 when available) — multi-GB; many minutes"
    phase_torch
    log "step 2 done (elapsed $(install_format_elapsed "$(install_elapsed_s)"))"

    step 3 "${total}" "Clone or update ComfyUI into ${COMFY_HOME}"
    step 4 "${total}" "Install ComfyUI requirements.txt"
    step 5 "${total}" "Install hub/runtime extras (psutil, huggingface_hub, …)"
    phase_comfy
    log "step 3–5 done"

    step 6 "${total}" "Install custom nodes (Manager, Nunchaku)"
    step 7 "${total}" "Optional SageAttention (fail-soft on aarch64)"
    step 8 "${total}" "Optional nunchaku package (fail-soft)"
    phase_nodes
    log "step 6–8 done"

    step 9 "${total}" "Write install stamp"
    step 10 "${total}" "Strip prebuilt bloat (.git, bytecode, caches)"
    step 11 "${total}" "Link model subdirs under ${MODELS_ROOT}/comfy"
    step 12 "${total}" "Apply Spark free-memory patch"
    phase_finalize
    log "step 9–12 done"
  else
    activate_venv
    step 1 "${total}" "Refresh model directory links"
    link_all_models
    step 2 "${total}" "Remove wrong PyPI nunchaku if present"
    cleanup_wrong_nunchaku
    step 3 "${total}" "Apply Spark free-memory patch"
    apply_free_memory_patch
    step 4 "${total}" "Refresh complete"
  fi

  log "══ Install complete ══ total elapsed $(install_format_elapsed "$(install_elapsed_s)")"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
