#!/usr/bin/env bash
#
# ## install-comfy/phase-finalize.sh
#
# Docker cache phase: stamp, strip, link models, patch, optional parts package.
# Source common.sh before this file.
#

#######################################
# True if a venv-extra tree contains torch libs (would duplicate multi-GB).
# Globals:
#   None
# Arguments:
#   $1  Directory to scan (venv-extra)
# Outputs:
#   None
# Returns:
#   0 if torch artifacts found; 1 if not or path missing
#######################################
venv_extra_has_torch() {
  local extra="${1:?venv_extra_has_torch requires a directory}"
  if [[ ! -d ${extra} ]]; then
    return 1
  fi
  if find "${extra}" \( -iname 'libtorch*.so*' -o -path '*/site-packages/torch/__init__.py' \
    -o -path '*/site-packages/torch-*.dist-info/*' \) -print 2>/dev/null | grep -q .; then
    return 0
  fi
  return 1
}

#######################################
# Split prebuilt tree into /opt/parts/{venv,venv-extra,app} for runtime COPY.
# venv is the torch snapshot (from snapshot_torch_venv) or the full venv when
# no snapshot exists. venv-extra is the rsync delta after comfy+nodes pip.
# Only when LAB_PACKAGE_PARTS=1 (Dockerfile finalize). Cold install never sets this.
# Globals:
#   COMFY_HOME, VENV, LAB_PARTS_ROOT, LAB_PACKAGE_PARTS
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success or when packaging disabled; 1 if venv missing / torch leaked
#######################################
package_prebuilt_parts() {
  local parts="${LAB_PARTS_ROOT:-/opt/parts}"
  local torch_snap extra_dest
  if [[ ${LAB_PACKAGE_PARTS:-0} != "1" ]]; then
    return 0
  fi
  if [[ ! -d ${COMFY_HOME}/.venv ]]; then
    warn "package_prebuilt_parts: missing ${COMFY_HOME}/.venv"
    return 1
  fi
  mkdir -p "${parts}"
  extra_dest="${parts}/venv-extra"
  rm -rf "${extra_dest}"
  mkdir -p "${extra_dest}"

  if [[ -d ${parts}/venv ]]; then
    log "package_prebuilt_parts: delta ${COMFY_HOME}/.venv vs torch snapshot → venv-extra"
    torch_snap="$(cd "${parts}/venv" && pwd)"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --compare-dest="${torch_snap}/" "${COMFY_HOME}/.venv/" "${extra_dest}/"
    else
      warn "package_prebuilt_parts: rsync missing — copying full venv into extra"
      cp -a "${COMFY_HOME}/.venv/." "${extra_dest}/"
    fi
    find "${extra_dest}" -type d -empty -delete 2>/dev/null || true
    mkdir -p "${extra_dest}"
  else
    log "package_prebuilt_parts: no torch snapshot; moving full venv → ${parts}/venv"
    mv "${COMFY_HOME}/.venv" "${parts}/venv"
  fi
  printf 'ez-comfy-venv-extra\n' >"${extra_dest}/.lab-venv-extra"

  if venv_extra_has_torch "${extra_dest}"; then
    warn "package_prebuilt_parts: venv-extra contains torch — overlay would re-pull multi-GB"
    return 1
  fi

  rm -rf "${COMFY_HOME}/.venv"
  # Remaining tree (ComfyUI sources, custom_nodes, stamp) becomes app layer
  log "package_prebuilt_parts: splitting ${COMFY_HOME} → ${parts}/app"
  mv "${COMFY_HOME}" "${parts}/app"
  mkdir -p "${COMFY_HOME}"
  if [[ -d ${parts}/app/.venv ]]; then
    warn "package_prebuilt_parts: unexpected .venv under app"
    return 1
  fi
  if [[ ! -d ${parts}/venv || ! -d ${parts}/app || ! -d ${parts}/venv-extra ]]; then
    warn "package_prebuilt_parts: incomplete parts tree"
    return 1
  fi
  log "package_prebuilt_parts: done (venv + venv-extra + app)"
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
