#!/usr/bin/env bash
#
# ## install-comfy/core.sh
#
# Torch-stable helpers only (log, pip, venv). Copied into the Docker torch
# stage so edits to clone/link/strip in common.sh do not bust multi-GB torch.
#
# Style: Google Shell Style Guide (project deviations in docs/project-conventions.md).
#

# Idempotent: common.sh and phase-venv-torch.sh both source this file.
if [[ -n ${_EZ_COMFY_CORE_LOADED:-} ]]; then
  return 0
fi
_EZ_COMFY_CORE_LOADED=1

# Defaults when sourced standalone (Dockerfile phases set COMFY_HOME first).
# Do not put COMFYUI_REF here — bumping that pin must not invalidate torch COPY.
COMFY_HOME="${COMFY_HOME:-/comfy-state/ComfyUI}"
COMFY_USER="${COMFY_USER:-0}"
MODELS_ROOT="${MODELS_ROOT:-/models}"
STAMP="${STAMP:-${COMFY_HOME}/.lab-install-complete}"
VENV="${VENV:-${COMFY_HOME}/.venv}"
# Validated cu130 pin (see docs/models-and-cache.md). Override via ARG/ENV.
TORCH_VERSION="${TORCH_VERSION:-2.14.0}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu130}"

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
