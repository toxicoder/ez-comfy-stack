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
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   Sourcable for hermetic BATS via source guard at bottom.
#
# Environment:
#   COMFY_HOME, COMFY_USER, MODELS_ROOT — defaults below
#
set -euo pipefail

COMFY_HOME="${COMFY_HOME:-/comfy-state/ComfyUI}"
COMFY_USER="${COMFY_USER:-0}"
MODELS_ROOT="${MODELS_ROOT:-/models}"
STAMP="${COMFY_HOME}/.lab-install-complete"
VENV="${COMFY_HOME}/.venv"
# Install wall-clock start (unix seconds); set in main
INSTALL_T0="${INSTALL_T0:-}"

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
# Full install or refresh path for ComfyUI on the comfy-state volume.
# Globals:
#   COMFY_HOME, COMFY_USER, MODELS_ROOT, STAMP, VENV
# Arguments:
#   None
# Outputs:
#   Progress logs
# Returns:
#   0 on success; non-zero if a hard step fails under set -e
#######################################
main() {
  local total=11 refresh=0 sub
  export DEBIAN_FRONTEND=noninteractive
  export PYTHONUNBUFFERED=1
  INSTALL_T0="$(date +%s)"
  log "Install started at $(date -u +%Y-%m-%dT%H:%MZ)"
  log "Markers: ══ step N/M ══ — pip shows multi-GB wheel bars when downloading"

  if [[ -f ${STAMP} && -x "${VENV}/bin/python" ]]; then
    refresh=1
    total=3
    log "Install stamp present — fast refresh (3 steps; cold install skipped)"
  else
    log "Cold install path (~10–30+ min common on first start)"
  fi

  if [[ ${refresh} -eq 0 ]]; then
    step 1 "${total}" "Clone or update ComfyUI into ${COMFY_HOME}"
    if [[ ! -d "${COMFY_HOME}/.git" ]]; then
      mkdir -p "$(dirname "${COMFY_HOME}")"
      # Destination may already exist (empty volume + old workflow bind mount created
      # intermediate dirs). git clone refuses non-empty targets — clone then merge.
      if [[ -d ${COMFY_HOME} && -n "$(ls -A "${COMFY_HOME}" 2>/dev/null || true)" ]]; then
        local tmp_clone
        tmp_clone="$(mktemp -d)"
        log "git clone (temp) then merge into existing ${COMFY_HOME}…"
        git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "${tmp_clone}/ComfyUI"
        if command -v rsync >/dev/null 2>&1; then
          rsync -a "${tmp_clone}/ComfyUI/" "${COMFY_HOME}/"
        else
          cp -a "${tmp_clone}/ComfyUI/." "${COMFY_HOME}/"
        fi
        rm -rf "${tmp_clone}"
      else
        log "git clone into ${COMFY_HOME}…"
        git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "${COMFY_HOME}"
      fi
    else
      log "ComfyUI tree present; pulling latest (best-effort)"
      git -C "${COMFY_HOME}" pull --ff-only || warn "git pull failed; continuing"
    fi
    log "step 1 done"

    step 2 "${total}" "Create Python venv (if missing)"
    if [[ ! -d ${VENV} ]]; then
      log "python3 -m venv ${VENV}"
      python3 -m venv "${VENV}"
    else
      log "venv already exists"
    fi
    # shellcheck disable=SC1091
    source "${VENV}/bin/activate"
    log "step 2 done"

    step 3 "${total}" "Upgrade pip, setuptools, wheel"
    pip_install -U pip setuptools wheel
    log "step 3 done"

    step 4 "${total}" "Install PyTorch (cu130 when available) — multi-GB; many minutes"
    log "Expect large wheels (torch + cuda toolkit + cudnn); progress bars below…"
    pip_install --upgrade torch torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/cu130 || {
      warn "cu130 index failed; falling back to default PyPI torch"
      pip_install --upgrade torch torchvision torchaudio
    }
    log "step 4 done (elapsed $(install_format_elapsed "$(install_elapsed_s)"))"

    step 5 "${total}" "Install ComfyUI requirements.txt"
    pip_install -r "${COMFY_HOME}/requirements.txt"
    log "step 5 done"

    step 6 "${total}" "Install hub/runtime extras (psutil, huggingface_hub, …)"
    pip_install psutil huggingface_hub safetensors einops
    log "step 6 done"

    step 7 "${total}" "Install custom nodes (Manager, Nunchaku)"
    CUSTOM="${COMFY_HOME}/custom_nodes"
    mkdir -p "${CUSTOM}"
    clone_node "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"
    clone_node "https://github.com/mit-han-lab/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
      clone_node "https://github.com/nunchaku-tech/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
      warn "Nunchaku custom node unavailable"
    log "step 7 done"

    step 8 "${total}" "Optional SageAttention (fail-soft on aarch64)"
    pip_install sageattention || warn "SageAttention pip install failed (optional on aarch64)"
    log "step 8 done"

    step 9 "${total}" "Optional nunchaku package (fail-soft)"
    pip_install nunchaku || warn "nunchaku package install failed (optional)"
    log "step 9 done"

    touch "${STAMP}"
    log "Wrote install stamp ${STAMP}"

    step 10 "${total}" "Link model subdirs under ${MODELS_ROOT}/comfy"
  else
    # shellcheck disable=SC1091
    source "${VENV}/bin/activate"
    step 1 "${total}" "Refresh model directory links"
  fi

  # shellcheck disable=SC1091
  [[ -f "${VENV}/bin/activate" ]] && source "${VENV}/bin/activate"

  for sub in checkpoints diffusion_models text_encoders vae loras clip clip_vision \
    unet controlnet embeddings upscale_models audio_encoders; do
    link_models "${sub}"
  done
  log "model links done"

  if [[ ${refresh} -eq 1 ]]; then
    step 2 "${total}" "Apply Spark free-memory patch"
  else
    step 11 "${total}" "Apply Spark free-memory patch"
  fi
  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${COMFY_HOME}" || warn "patch failed"
  else
    warn "patch_get_free_memory.py not found in image"
  fi

  if [[ ${refresh} -eq 1 ]]; then
    step 3 "${total}" "Refresh complete"
  fi
  log "══ Install complete ══ total elapsed $(install_format_elapsed "$(install_elapsed_s)")"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
