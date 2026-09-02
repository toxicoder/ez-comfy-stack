#!/usr/bin/env bash
#
# ## install-comfy/phase-finalize.sh
#
# Docker cache phase: stamp, strip, link models, patch, optional parts package.
# Source common.sh before this file.
#

#######################################
# Split prebuilt tree into /opt/parts/{venv,app} for multi-layer runtime COPY.
# Uses move (not full tree duplicate) to limit builder disk. Only when
# LAB_PACKAGE_PARTS=1 (Dockerfile finalize). Cold install never sets this.
# Globals:
#   COMFY_HOME, LAB_PARTS_ROOT, LAB_PACKAGE_PARTS
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success or when packaging disabled; 1 if venv missing when enabled
#######################################
package_prebuilt_parts() {
  local parts="${LAB_PARTS_ROOT:-/opt/parts}"
  if [[ ${LAB_PACKAGE_PARTS:-0} != "1" ]]; then
    return 0
  fi
  if [[ ! -d ${COMFY_HOME}/.venv ]]; then
    warn "package_prebuilt_parts: missing ${COMFY_HOME}/.venv"
    return 1
  fi
  log "package_prebuilt_parts: splitting ${COMFY_HOME} → ${parts}/{venv,app}"
  rm -rf "${parts}"
  mkdir -p "${parts}"
  mv "${COMFY_HOME}/.venv" "${parts}/venv"
  # Remaining tree (ComfyUI sources, custom_nodes, stamp) becomes app layer
  mv "${COMFY_HOME}" "${parts}/app"
  # Leave empty COMFY_HOME so callers still see a directory
  mkdir -p "${COMFY_HOME}"
  if [[ -d ${parts}/app/.venv ]]; then
    warn "package_prebuilt_parts: unexpected .venv under app"
    return 1
  fi
  if [[ ! -d ${parts}/venv || ! -d ${parts}/app ]]; then
    warn "package_prebuilt_parts: incomplete parts tree"
    return 1
  fi
  log "package_prebuilt_parts: done (venv + app)"
  return 0
}

#######################################
# Stamp, strip, link models, optional patch, optional parts package.
# Globals:
#   COMFY_HOME, STAMP, VENV, LAB_PACKAGE_PARTS
# Arguments:
#   None
# Outputs:
#   Progress via log
# Returns:
#   0
#######################################
phase_finalize() {
  activate_venv
  touch "${STAMP}"
  log "Wrote install stamp ${STAMP}"
  write_comfy_pin
  strip_prebuilt "${COMFY_HOME}"
  link_all_models
  apply_free_memory_patch
  package_prebuilt_parts
}
