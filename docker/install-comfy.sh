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
  if [[ ! -d "${CUSTOM}/${name}/.git" ]]; then
    log "Installing custom node: ${name}"
    git clone --depth 1 "${url}" "${CUSTOM}/${name}" || warn "clone failed: ${name}"
  else
    git -C "${CUSTOM}/${name}" pull --ff-only || true
  fi
  if [[ -f "${CUSTOM}/${name}/requirements.txt" ]]; then
    pip install -r "${CUSTOM}/${name}/requirements.txt" || warn "requirements failed: ${name}"
  fi
}

#######################################
# Symlink a Comfy models subdir to the host cache under MODELS_ROOT/comfy.
# Globals:
#   MODELS_ROOT, COMFY_HOME
# Arguments:
#   $1 - Subdirectory name (e.g. diffusion_models)
# Outputs:
#   None
# Returns:
#   0
#######################################
link_models() {
  local sub="${1}"
  local host_dir="${MODELS_ROOT}/comfy/${sub}"
  local comfy_dir="${COMFY_HOME}/models/${sub}"
  mkdir -p "${host_dir}" "${COMFY_HOME}/models"
  if [[ -L ${comfy_dir} ]] || [[ ! -e ${comfy_dir} ]]; then
    rm -rf "${comfy_dir}" 2>/dev/null || true
    ln -sfn "${host_dir}" "${comfy_dir}"
  elif [[ -d ${comfy_dir} && -z "$(ls -A "${comfy_dir}" 2>/dev/null || true)" ]]; then
    rmdir "${comfy_dir}" 2>/dev/null || true
    ln -sfn "${host_dir}" "${comfy_dir}"
  fi
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
  export DEBIAN_FRONTEND=noninteractive

  if [[ -f ${STAMP} && -x "${VENV}/bin/python" ]]; then
    log "Install stamp present; refreshing models links only"
  else
    if [[ ! -d "${COMFY_HOME}/.git" ]]; then
      log "Cloning ComfyUI into ${COMFY_HOME}"
      mkdir -p "$(dirname "${COMFY_HOME}")"
      git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "${COMFY_HOME}"
    else
      log "ComfyUI tree present; pulling latest (best-effort)"
      git -C "${COMFY_HOME}" pull --ff-only || warn "git pull failed; continuing"
    fi

    if [[ ! -d ${VENV} ]]; then
      log "Creating venv"
      python3 -m venv "${VENV}"
    fi
    # shellcheck disable=SC1091
    source "${VENV}/bin/activate"
    pip install -U pip setuptools wheel

    log "Installing PyTorch (cu130 when available)"
    pip install --upgrade torch torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/cu130 ||
      pip install --upgrade torch torchvision torchaudio

    log "Installing ComfyUI requirements"
    pip install -r "${COMFY_HOME}/requirements.txt"
    pip install psutil huggingface_hub safetensors einops

    CUSTOM="${COMFY_HOME}/custom_nodes"
    mkdir -p "${CUSTOM}"

    clone_node "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager"
    clone_node "https://github.com/mit-han-lab/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
      clone_node "https://github.com/nunchaku-tech/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" ||
      warn "Nunchaku custom node unavailable"

    log "Attempting SageAttention install (fail-soft)"
    pip install sageattention || warn "SageAttention pip install failed (optional on aarch64)"
    log "Attempting nunchaku package (fail-soft)"
    pip install nunchaku || warn "nunchaku package install failed (optional)"

    touch "${STAMP}"
  fi

  # shellcheck disable=SC1091
  [[ -f "${VENV}/bin/activate" ]] && source "${VENV}/bin/activate"

  local sub
  for sub in checkpoints diffusion_models text_encoders vae loras clip clip_vision \
    unet controlnet embeddings upscale_models audio_encoders; do
    link_models "${sub}"
  done

  log "Applying Spark unified-memory patches"
  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${COMFY_HOME}" || warn "patch failed"
  fi

  log "Install complete"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
