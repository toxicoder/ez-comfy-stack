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
#   Phase implementations live under install-comfy/ so Docker can COPY only the
#   modules each prebuild RUN needs (torch survives nodes-only edits):
#     install-comfy.sh --phase venv|torch|comfy|nodes|finalize
#   Default (no --phase): full cold install or stamp-based refresh.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   Sourcable for hermetic BATS via source guard at bottom.
#
# Environment:
#   COMFY_HOME, COMFY_USER, MODELS_ROOT — defaults in install-comfy/common.sh
#   COMFYUI_REF — ComfyUI git pin (default v0.34.0; empty = default branch)
#   COMFYUI_MANAGER_REF — Manager pin (default 4.2.2)
#   COMFYUI_NUNCHAKU_NODE_REF — nunchaku node pin (default v1.2.1)
#   COMFYUI_VHS_REF — VideoHelperSuite git ref (default empty = main; required for LTX MP4)
#   LAB_PACKAGE_PARTS=1 — split tree into /opt/parts/{venv,app} (Docker only)
#
set -euo pipefail

_INSTALL_COMFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Dynamic path: modules live next to this orchestrator (compose bind-mount / image).
# shellcheck disable=SC1091
source "${_INSTALL_COMFY_DIR}/install-comfy/common.sh"
# shellcheck disable=SC1091
source "${_INSTALL_COMFY_DIR}/install-comfy/phase-venv-torch.sh"
# shellcheck disable=SC1091
source "${_INSTALL_COMFY_DIR}/install-comfy/phase-comfy.sh"
# shellcheck disable=SC1091
source "${_INSTALL_COMFY_DIR}/install-comfy/phase-nodes.sh"
# shellcheck disable=SC1091
source "${_INSTALL_COMFY_DIR}/install-comfy/phase-finalize.sh"

# Re-bind paths after COMFY_HOME may be overridden by the environment.
STAMP="${COMFY_HOME}/.lab-install-complete"
VENV="${COMFY_HOME}/.venv"

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
#   Sets INSTALL_PHASE (empty = full install path)
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
# When the volume Comfy pin lags COMFYUI_REF, sync sources (prebuilt rsync or git).
# Globals:
#   COMFY_HOME, COMFYUI_REF, LAB_PREBUILT_ROOT, VENV
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
refresh_comfy_pin_if_needed() {
  local want="${COMFYUI_REF:-}"
  local have pre
  have="$(read_comfy_pin)"
  if [[ ${have} == "${want}" ]]; then
    log "Comfy pin ${want} already on volume"
    return 0
  fi
  log "Syncing ComfyUI to pin ${want} (volume had ${have:-none})"
  pre="${LAB_PREBUILT_ROOT:-/opt/comfy-prebuilt}"
  if [[ -x ${pre}/.venv/bin/python || -f ${pre}/main.py ]]; then
    log "Re-seeding ${COMFY_HOME} from prebuilt"
    mkdir -p "${COMFY_HOME}"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a "${pre}/" "${COMFY_HOME}/"
    else
      cp -a "${pre}/." "${COMFY_HOME}/"
    fi
    activate_venv
  else
    log "Prebuilt missing — cloning COMFYUI_REF=${want}"
    phase_clone_comfy
    activate_venv
    if [[ -f ${COMFY_HOME}/requirements.txt ]]; then
      pip_install -r "${COMFY_HOME}/requirements.txt"
    fi
  fi
  write_comfy_pin
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
  # Used by install_elapsed_s / step in install-comfy/common.sh
  export INSTALL_T0
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
    total=6
    log "Install stamp present — fast refresh (pin sync + links + patch)"
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

    step 6 "${total}" "Install custom nodes (Manager, VideoHelperSuite, Nunchaku)"
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
    step 1 "${total}" "Sync ComfyUI pin if the volume lags COMFYUI_REF"
    refresh_comfy_pin_if_needed
    step 2 "${total}" "Refresh model directory links"
    link_all_models
    step 3 "${total}" "Ensure VideoHelperSuite (LTX lab MP4)"
    ensure_lab_video_nodes || warn "VideoHelperSuite refresh failed — LTX lab MP4 may be unavailable"
    step 4 "${total}" "Remove wrong PyPI nunchaku if present"
    cleanup_wrong_nunchaku
    step 5 "${total}" "Apply Spark free-memory patch"
    apply_free_memory_patch
    step 6 "${total}" "Refresh complete"
  fi

  log "══ Install complete ══ total elapsed $(install_format_elapsed "$(install_elapsed_s)")"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
