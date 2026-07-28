#!/usr/bin/env bash
#
# ## entrypoint
#
# Container entrypoint for the ez-comfy flux-to-ltx image.
#
# Purpose:
#   1) Run install-comfy.sh (idempotent ComfyUI + custom nodes + model symlinks)
#   2) Re-apply the Spark free-memory patch
#   3) Exec ComfyUI listening on 0.0.0.0:8188
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   Sourcable for hermetic BATS via source guard.
#
# Environment:
#   COMFY_HOME — ComfyUI root (default /comfy-state/ComfyUI)
#   PYTORCH_CUDA_ALLOC_CONF — defaults to expandable_segments:True
#   LAB_ENTRYPOINT_INSTALL_CMD — optional override for install invocation (tests)
#
set -euo pipefail

COMFY_HOME="${COMFY_HOME:-/comfy-state/ComfyUI}"
VENV="${COMFY_HOME}/.venv"

#######################################
# Run install, patch, and exec ComfyUI (or stop before exec in tests).
# Globals:
#   COMFY_HOME, VENV, LAB_ENTRYPOINT_INSTALL_CMD, LAB_ENTRYPOINT_NO_EXEC
# Arguments:
#   None
# Outputs:
#   Progress on stdout/stderr
# Returns:
#   Does not return on success (exec); non-zero if install/venv missing
#######################################
main() {
  local install_cmd="${LAB_ENTRYPOINT_INSTALL_CMD:-bash /opt/ez-comfy/install-comfy.sh}"
  echo "[entrypoint] installing / refreshing ComfyUI"
  # shellcheck disable=SC2086
  ${install_cmd}

  if [[ ! -x "${VENV}/bin/python" ]]; then
    echo "[entrypoint] ERROR: venv missing at ${VENV}" >&2
    exit 1
  fi

  # shellcheck disable=SC1091
  source "${VENV}/bin/activate"

  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${COMFY_HOME}" || true
  fi

  mkdir -p "${COMFY_HOME}/user/default/workflows"
  # Workflow is bind-mounted under /opt/ez-comfy/workflows (not into COMFY_HOME)
  if [[ -f /opt/ez-comfy/workflows/lab-flux-to-ltx.json ]]; then
    cp -f /opt/ez-comfy/workflows/lab-flux-to-ltx.json \
      "${COMFY_HOME}/user/default/workflows/lab-flux-to-ltx.json"
    echo "[entrypoint] installed lab-flux-to-ltx workflow"
  fi

  export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
  cd "${COMFY_HOME}"
  echo "[entrypoint] starting ComfyUI on 0.0.0.0:8188"
  if [[ ${LAB_ENTRYPOINT_NO_EXEC:-} == "1" ]]; then
    echo "[entrypoint] LAB_ENTRYPOINT_NO_EXEC=1; skipping exec"
    return 0
  fi
  exec python main.py --listen 0.0.0.0 --port 8188
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
