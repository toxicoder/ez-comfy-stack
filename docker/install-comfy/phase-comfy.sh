#!/usr/bin/env bash
#
# ## install-comfy/phase-comfy.sh
#
# Docker cache phase: clone pinned ComfyUI and install requirements.
# Source common.sh before this file.
#

# Defaults when shellcheck/lint analyze this file without common.sh sourced first.
# Runtime always sources common.sh; ENV/Dockerfile may override.
COMFYUI_REPO="${COMFYUI_REPO:-https://github.com/comfyanonymous/ComfyUI.git}"
COMFYUI_REF="${COMFYUI_REF:-v0.34.0}"

#######################################
# Clone or update ComfyUI into COMFY_HOME (honours COMFYUI_REF pin).
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
    log "ComfyUI pin: COMFYUI_REF=${COMFYUI_REF}"
  else
    log "ComfyUI pin: empty COMFYUI_REF (default branch)"
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
    log "ComfyUI tree present; syncing to pin (best-effort)"
    if [[ -n ${COMFYUI_REF} ]]; then
      git -C "${COMFY_HOME}" fetch --depth 1 origin "${COMFYUI_REF}" 2>/dev/null || true
      git -C "${COMFY_HOME}" checkout "${COMFYUI_REF}" 2>/dev/null ||
        git -C "${COMFY_HOME}" pull --ff-only || warn "git sync to pin failed; continuing"
    else
      git -C "${COMFY_HOME}" pull --ff-only || warn "git pull failed; continuing"
    fi
  fi
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
