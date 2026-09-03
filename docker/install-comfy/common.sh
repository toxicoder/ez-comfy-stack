#!/usr/bin/env bash
#
# ## install-comfy/common.sh
#
# Shared helpers for ComfyUI install phases (logging, pip, venv, model links).
# Sourced by install-comfy.sh and by Dockerfile phase RUN steps.
#
# Style: Google Shell Style Guide (project deviations in docs/project-conventions.md).
#

# Defaults when sourced standalone (Dockerfile phases set COMFY_HOME first).
COMFY_HOME="${COMFY_HOME:-/comfy-state/ComfyUI}"
COMFY_USER="${COMFY_USER:-0}"
MODELS_ROOT="${MODELS_ROOT:-/models}"
STAMP="${STAMP:-${COMFY_HOME}/.lab-install-complete}"
VENV="${VENV:-${COMFY_HOME}/.venv}"
INSTALL_T0="${INSTALL_T0:-}"
COMFYUI_REPO="${COMFYUI_REPO:-https://github.com/comfyanonymous/ComfyUI.git}"
# Validated pins (see docs/models-and-cache.md). Empty COMFYUI_REF floats default branch.
COMFYUI_REF="${COMFYUI_REF:-v0.34.0}"
COMFYUI_MANAGER_REF="${COMFYUI_MANAGER_REF:-4.2.2}"
COMFYUI_NUNCHAKU_NODE_REF="${COMFYUI_NUNCHAKU_NODE_REF:-v1.2.1}"
# Empty = clone default branch (main). Set to a tag/branch/SHA branch name when available.
COMFYUI_VHS_REF="${COMFYUI_VHS_REF:-}"

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
# Path of the volume ComfyUI pin stamp.
# Globals:
#   COMFY_HOME
# Arguments:
#   None
# Outputs:
#   Absolute path
# Returns:
#   0
#######################################
comfy_pin_file() {
  echo "${COMFY_HOME}/.lab-comfyui-ref"
}

#######################################
# Record COMFYUI_REF on the volume.
# Globals:
#   COMFYUI_REF, COMFY_HOME
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
write_comfy_pin() {
  local f dest
  f="$(comfy_pin_file)"
  dest="$(dirname "${f}")"
  mkdir -p "${dest}"
  printf '%s\n' "${COMFYUI_REF:-}" >"${f}"
  log "Wrote Comfy pin ${COMFYUI_REF:-} → ${f}"
}

#######################################
# Read volume ComfyUI pin (empty if missing).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Pin string without trailing newline
# Returns:
#   0
#######################################
read_comfy_pin() {
  local f
  f="$(comfy_pin_file)"
  if [[ -f ${f} ]]; then
    tr -d '\n' <"${f}"
  fi
}

#######################################
# True if volume pin matches COMFYUI_REF.
# Globals:
#   COMFYUI_REF
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 match; 1 mismatch or missing
#######################################
comfy_pin_matches() {
  [[ "$(read_comfy_pin)" == "${COMFYUI_REF:-}" ]]
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
#   0 if activated or activate missing (no-op)
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
#   $3 - Optional git ref (tag/branch/SHA); shallow clone uses --branch when set
# Outputs:
#   Progress via log/warn
# Returns:
#   0 even on soft failures (clone/pip may warn and continue)
#######################################
clone_node() {
  local url="${1}"
  local name="${2}"
  local ref="${3:-}"
  local -a clone_args=(--depth 1)
  log "custom node: begin ${name}${ref:+ (ref ${ref})}"
  if [[ -n ${ref} ]]; then
    clone_args+=(--branch "${ref}")
  fi
  if [[ ! -d "${CUSTOM}/${name}/.git" ]]; then
    log "custom node: cloning ${name}…"
    git clone "${clone_args[@]}" "${url}" "${CUSTOM}/${name}" || warn "clone failed: ${name}"
  else
    log "custom node: updating ${name}…"
    if [[ -n ${ref} ]]; then
      git -C "${CUSTOM}/${name}" fetch --depth 1 origin "${ref}" 2>/dev/null || true
      git -C "${CUSTOM}/${name}" checkout "${ref}" 2>/dev/null ||
        git -C "${CUSTOM}/${name}" pull --ff-only || true
    else
      git -C "${CUSTOM}/${name}" pull --ff-only || true
    fi
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
    unet controlnet embeddings upscale_models audio_encoders llm; do
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
