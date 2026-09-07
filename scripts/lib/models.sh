#!/usr/bin/env bash
# ## models
#
# Shared keep-set / realpath / MODELS_DIR safety for reap-models.
#
# Audience: sourced by reap-models.sh and models-manifest.sh.
#

#######################################
# Path to config/model-manifest.yaml.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   path on stdout
# Returns:
#   0
#######################################
models_manifest_path() {
  echo "${REPO_ROOT}/config/model-manifest.yaml"
}

#######################################
# Print keep-set basenames (union of all pack files).
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   one basename per line
# Returns:
#   python status
#######################################
models_keep_set() {
  python3 "${REPO_ROOT}/scripts/lib/model_manifest.py" \
    --manifest "$(models_manifest_path)" keep-set
}

#######################################
# Print default-pack keep-set basenames (live files; never reap).
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   one basename per line
# Returns:
#   python status
#######################################
models_default_keep_set() {
  python3 "${REPO_ROOT}/scripts/lib/model_manifest.py" \
    --manifest "$(models_manifest_path)" default-keep-set
}

#######################################
# Print refuse-list tokens.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   one token per line
# Returns:
#   python status
#######################################
models_refuse_list() {
  python3 "${REPO_ROOT}/scripts/lib/model_manifest.py" \
    --manifest "$(models_manifest_path)" refuse
}

#######################################
# True if basename is in the keep-set.
# Arguments:
#   $1  basename
# Outputs:
#   None
# Returns:
#   0 keep; 1 not
#######################################
models_is_keep_file() {
  local base="${1}"
  models_default_keep_set | grep -Fxq -- "${base}"
}

#######################################
# Resolve path; abort unless it is under MODELS_DIR.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  path
# Outputs:
#   realpath on stdout
# Returns:
#   0; 1 escape
#######################################
models_realpath_under() {
  local target="${1}"
  local root t
  root="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${MODELS_DIR}")"
  t="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${target}")"
  case "${t}/" in
    "${root}/"*) echo "${t}" ;;
    *)
      err "path escapes MODELS_DIR: ${target}"
      return 1
      ;;
  esac
}

#######################################
# Abort if MODELS_DIR is /, $HOME, /mnt, or a symlink to /.
# Globals:
#   MODELS_DIR, HOME
# Arguments:
#   None
# Outputs:
#   err
# Returns:
#   0 safe; 1 unsafe
#######################################
models_dir_is_safe() {
  local real home
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${MODELS_DIR}")"
  home="$(python3 -c 'import os; print(os.path.realpath(os.path.expanduser("~")))')"
  case "${real}" in
    / | /mnt | "${home}")
      err "MODELS_DIR is unsafe: ${MODELS_DIR} → ${real}"
      return 1
      ;;
  esac
  return 0
}
