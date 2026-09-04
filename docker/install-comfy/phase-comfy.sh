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
# Write a pip constraint file pinning already-installed torch/tv/ta.
# Prevents ComfyUI requirements.txt (unpinned torch) from replacing cu130.
# Globals:
#   None (uses active venv pip)
# Arguments:
#   $1  Destination path
# Outputs:
#   Constraint lines at $1 when freeze has torch pins
# Returns:
#   0 if the file is non-empty; 1 if freeze had no torch lines
#######################################
write_torch_pip_constraint() {
  local dest="${1:?write_torch_pip_constraint requires dest path}"
  pip freeze 2>/dev/null | grep -E '^(torch|torchvision|torchaudio)==' >"${dest}" || true
  [[ -s ${dest} ]]
}

#######################################
# True if the active venv torch reports a CUDA build.
# Globals:
#   None (uses active venv python)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if torch.version.cuda is set; 1 if torch imported without CUDA;
#   2 if torch is not importable
#######################################
assert_torch_cuda() {
  local py
  py="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || true)"
  if [[ -z ${py} ]]; then
    return 2
  fi
  "${py}" - <<'PY' 2>/dev/null
import sys

try:
    import torch
except Exception:
    sys.exit(2)
cuda = getattr(getattr(torch, "version", None), "cuda", None)
sys.exit(0 if cuda else 1)
PY
}

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
  local constraint rc=0
  phase_clone_comfy
  activate_venv
  constraint="$(mktemp)"
  if write_torch_pip_constraint "${constraint}"; then
    log "Comfy requirements constrained to $(tr '\n' ' ' <"${constraint}")"
    pip_install -r "${COMFY_HOME}/requirements.txt" -c "${constraint}"
  else
    warn "No torch freeze pins — installing Comfy requirements unconstrained"
    pip_install -r "${COMFY_HOME}/requirements.txt"
  fi
  rm -f "${constraint}"
  pip_install psutil huggingface_hub safetensors einops
  assert_torch_cuda || rc=$?
  if [[ ${rc} -eq 1 ]]; then
    warn "torch has no CUDA after Comfy requirements — cu130 wheel may have been replaced"
    if [[ ${LAB_PACKAGE_PARTS:-0} == "1" ]]; then
      return 1
    fi
  fi
  return 0
}
