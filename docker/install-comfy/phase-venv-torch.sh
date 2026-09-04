#!/usr/bin/env bash
#
# ## install-comfy/phase-venv-torch.sh
#
# Docker cache phase: create venv and install multi-GB PyTorch (cu130).
# Source core.sh (or common.sh) before this file. Torch-stage Dockerfile
# copies only core.sh + this module.
#

# Allow sourcing this file alone in the torch stage (core.sh is a sibling).
if [[ -z ${_EZ_COMFY_CORE_LOADED:-} ]]; then
  # shellcheck disable=SC1091
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/core.sh"
fi

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
# Copy the torch-only venv aside so later pip can compute a delta overlay.
# Uses a real copy (not hardlinks): later pip must not mutate the snapshot.
# Globals:
#   VENV, LAB_PARTS_ROOT, LAB_PACKAGE_PARTS
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success or when packaging disabled; 1 if venv missing when enabled
#######################################
snapshot_torch_venv() {
  local parts="${LAB_PARTS_ROOT:-/opt/parts}"
  if [[ ${LAB_PACKAGE_PARTS:-0} != "1" ]]; then
    return 0
  fi
  if [[ ! -d ${VENV} ]]; then
    warn "snapshot_torch_venv: missing ${VENV}"
    return 1
  fi
  log "snapshot_torch_venv: ${VENV} → ${parts}/venv"
  rm -rf "${parts}/venv"
  mkdir -p "${parts}"
  cp -a "${VENV}" "${parts}/venv"
  return 0
}

#######################################
# Install PyTorch wheels (Docker phase: torch). Multi-GB; rare invalidation.
# Globals:
#   VENV, TORCH_VERSION, TORCH_INDEX_URL, LAB_PACKAGE_PARTS
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success
#######################################
phase_torch() {
  local ver="${TORCH_VERSION:-2.14.0}"
  local index="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu130}"
  activate_venv
  log "Expect large wheels (torch + cuda toolkit + cudnn); pin torch==${ver}"
  pip_install --upgrade "torch==${ver}" torchvision torchaudio \
    --index-url "${index}" || {
    warn "cu130 index failed; falling back to default PyPI torch==${ver}"
    pip_install --upgrade "torch==${ver}" torchvision torchaudio
  }
  snapshot_torch_venv
}
