#!/usr/bin/env bash
#
# ## install-comfy/phase-venv-torch.sh
#
# Docker cache phase: create venv and install multi-GB PyTorch (cu130).
# Source common.sh before this file.
#

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
