#!/usr/bin/env bash
# ## disk_scan
#
# Read-only filesystem / docker survey helpers for disk-wizard.
# Source after common.sh. Not executable.
#
# Safety:
#   Does not delete. Realpath jail. Hermetic tests set LAB_HERMETIC=1 and
#   DISK_WIZARD_HOME so $HOME is never walked on a developer laptop.

#######################################
# Home used for ~/.cache and ~/.ollama (tests override DISK_WIZARD_HOME).
# Globals:
#   DISK_WIZARD_HOME, HOME
# Outputs:
#   Absolute home path
# Returns:
#   0
#######################################
disk_scan_home() {
  printf '%s\n' "${DISK_WIZARD_HOME:-${HOME}}"
}

#######################################
# True when this is a hermetic test run (no real /tmp or live docker).
# Globals:
#   LAB_HERMETIC
# Returns:
#   0 hermetic
#######################################
disk_scan_hermetic() {
  [[ ${LAB_HERMETIC:-0} == "1" ]]
}

#######################################
# Print allowed root directories (one per line), existing only.
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR, DISK_WIZARD_ROOTS, DISK_WIZARD_SCAN_TMP
# Outputs:
#   Paths on stdout
# Returns:
#   0
#######################################
disk_allowed_roots() {
  local home root extra
  for root in \
    "${MODELS_DIR:-/mnt/models}" \
    "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"; do
    if [[ -d ${root} ]]; then
      python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${root}"
    fi
  done
  # Hermetic tests must set DISK_WIZARD_HOME; never walk the developer laptop cache.
  if [[ -n ${DISK_WIZARD_HOME:-} ]] || ! disk_scan_hermetic; then
    home="$(disk_scan_home)"
    for root in "${home}/.cache" "${home}/.ollama"; do
      if [[ -d ${root} ]]; then
        python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${root}"
      fi
    done
  fi
  if [[ ${DISK_WIZARD_SCAN_TMP:-0} == "1" ]] || ! disk_scan_hermetic; then
    for root in /tmp /var/tmp; do
      if [[ -d ${root} ]]; then
        python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${root}"
      fi
    done
  fi
  extra="${DISK_WIZARD_ROOTS:-}"
  if [[ -n ${extra} ]]; then
    local IFS=':'
    local part
    for part in ${extra}; do
      [[ -z ${part} ]] && continue
      if [[ -d ${part} ]]; then
        python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${part}"
      fi
    done
  fi
}

#######################################
# True if realpath(path) is under one of the allowed roots.
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR, DISK_WIZARD_HOME, DISK_WIZARD_ROOTS
# Arguments:
#   $1  path
# Returns:
#   0 allowed
#######################################
disk_root_is_allowed() {
  local target="${1}"
  local real root
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${target}")" || return 1
  while IFS= read -r root; do
    [[ -z ${root} ]] && continue
    case "${real}/" in
      "${root}/"*) return 0 ;;
    esac
  done < <(disk_allowed_roots)
  return 1
}

#######################################
# Realpath; fail unless under an allowed root.
# Arguments:
#   $1  path
# Outputs:
#   realpath
# Returns:
#   0; 1 escape
#######################################
disk_realpath_under_any() {
  local target="${1}"
  local real
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${target}")" || return 1
  if disk_root_is_allowed "${real}"; then
    printf '%s\n' "${real}"
    return 0
  fi
  err "path escapes disk-wizard roots: ${target}"
  return 1
}

#######################################
# File size in bytes (0 if missing).
# Arguments:
#   $1  path
# Outputs:
#   integer
# Returns:
#   0
#######################################
disk_file_size_bytes() {
  local path="${1}"
  local sz
  if [[ -L ${path} && ! -e ${path} ]]; then
    echo 0
    return 0
  fi
  if [[ ! -e ${path} ]]; then
    echo 0
    return 0
  fi
  case "$(uname -s)" in
    Darwin) sz="$(stat -f %z "${path}" 2>/dev/null || true)" ;;
    *) sz="$(stat -c %s "${path}" 2>/dev/null || true)" ;;
  esac
  echo "${sz:-0}"
}

#######################################
# True if a directory basename should not be descended.
# Arguments:
#   $1  basename
# Returns:
#   0 skip
#######################################
disk_skip_dir_name() {
  case "${1}" in
    .git | node_modules | __pycache__ | .venv | venv | .tox | .disk-quarantine | .reap-quarantine) return 0 ;;
  esac
  return 1
}

#######################################
# Walk one root (files and broken symlinks). Depth-capped.
# Globals:
#   DISK_WIZARD_MAX_DEPTH
# Arguments:
#   $1  root
# Outputs:
#   paths on stdout
# Returns:
#   0
#######################################
disk_walk_root() {
  local root="${1}"
  local depth="${DISK_WIZARD_MAX_DEPTH:-6}"
  local p
  [[ -d ${root} ]] || return 0
  # Prune skip dirs at any depth (keep in sync with disk_catalog.SKIP_DIR_NAMES).
  while IFS= read -r p; do
    [[ -z ${p} ]] && continue
    case "$(basename "${p}")" in
      .disk-wizard-plan.json | .disk-wizard.log | .reap-log | .reap-models.log)
        continue
        ;;
    esac
    printf '%s\n' "${p}"
  done < <(find "${root}" -maxdepth "${depth}" \
    \( -name .git -o -name node_modules -o -name __pycache__ -o -name .venv \
    -o -name venv -o -name .tox -o -name .disk-quarantine -o -name .reap-quarantine \) -prune \
    -o \( -type f -o -type l \) -print 2>/dev/null)
}

#######################################
# Human df -h for MODELS_DIR's filesystem (or mock).
# Globals:
#   MODELS_DIR, LAB_MOCK_DF
# Outputs:
#   df text
# Returns:
#   0
#######################################
disk_df_report() {
  if [[ -n ${LAB_MOCK_DF:-} ]]; then
    printf '%s\n' "${LAB_MOCK_DF}"
    return 0
  fi
  df -h "${MODELS_DIR:-/}" 2>/dev/null || df -h /
}

#######################################
# Docker disk usage JSON (or LAB_MOCK_DOCKER_DF file/text).
# Globals:
#   LAB_MOCK_DOCKER_DF, LAB_HERMETIC
# Outputs:
#   JSON or empty
# Returns:
#   0
#######################################
disk_docker_df() {
  if [[ -n ${LAB_MOCK_DOCKER_DF:-} ]]; then
    if [[ -f ${LAB_MOCK_DOCKER_DF} ]]; then
      cat "${LAB_MOCK_DOCKER_DF}"
    else
      printf '%s\n' "${LAB_MOCK_DOCKER_DF}"
    fi
    return 0
  fi
  if disk_scan_hermetic; then
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    docker system df --format '{{json .}}' 2>/dev/null || true
  fi
}

#######################################
# Image ids in use (docker ps -a image), one per line.
# Globals:
#   LAB_MOCK_DOCKER_IN_USE, LAB_HERMETIC
# Outputs:
#   ids
# Returns:
#   0
#######################################
disk_docker_in_use() {
  if [[ -n ${LAB_MOCK_DOCKER_IN_USE:-} ]]; then
    printf '%s\n' "${LAB_MOCK_DOCKER_IN_USE}"
    return 0
  fi
  if disk_scan_hermetic; then
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    docker ps -a --format '{{.Image}}' 2>/dev/null || true
  fi
}

#######################################
# True if an hf download PID or pidfile is present.
# Globals:
#   MODELS_DIR
# Returns:
#   0 running
#######################################
disk_hf_pid_present() {
  if [[ -f ${MODELS_DIR}/.hf-download.pid ]]; then
    return 0
  fi
  if type hf_download_pids_running >/dev/null 2>&1; then
    hf_download_pids_running
    return $?
  fi
  return 1
}

#######################################
# True if studio compose is up.
# Returns:
#   0 running
#######################################
disk_compose_up() {
  if type compose_is_running >/dev/null 2>&1; then
    compose_is_running
    return $?
  fi
  return 1
}
