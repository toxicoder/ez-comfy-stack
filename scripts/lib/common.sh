#!/usr/bin/env bash
# ## common
#
# Shared logging, fatal helpers, and environment loading for ez-comfy-stack.
#
# Purpose:
#   Keep operator diagnostics consistent (prefixed; always on stderr) so stdout
#   remains free for machine-readable data such as --json payloads.
#
# Audience:
#   Sourced by manage.sh and utilities after paths.sh. Not executable alone.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   All error/status messages go to STDERR (Google S3).
#

# shellcheck disable=SC2034
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

#######################################
# Emit an informational diagnostic to stderr with [ez-comfy] prefix.
# Globals:
#   GREEN, NC
# Arguments:
#   $@ - Message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0
#######################################
log() {
  echo -e "${GREEN}[ez-comfy]${NC} $*" >&2
}

#######################################
# Emit a non-fatal warning to stderr with [ez-comfy][WARN] prefix.
# Globals:
#   YELLOW, NC
# Arguments:
#   $@ - Warning message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0
#######################################
warn() {
  echo -e "${YELLOW}[ez-comfy][WARN]${NC} $*" >&2
}

#######################################
# Emit an error diagnostic to stderr with [ez-comfy][ERROR] prefix.
# Does not exit; pair with return/exit or die.
# Globals:
#   RED, NC
# Arguments:
#   $@ - Error message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0 (caller controls process exit)
#######################################
err() {
  echo -e "${RED}[ez-comfy][ERROR]${NC} $*" >&2
}

#######################################
# Log an error and terminate the process with status 1.
# Globals:
#   None
# Arguments:
#   $@ - Error message fragments passed to err
# Outputs:
#   Writes to stderr via err
# Returns:
#   Does not return; exits 1
#######################################
die() {
  err "$@"
  exit 1
}

#######################################
# Load a .env file from a directory if present (best-effort).
# Only assigns keys that are not already set in the environment so operator
# exports and hermetic tests (e.g. MODELS_DIR) take precedence over .env.
# Globals:
#   REPO_ROOT (read, optional default root)
# Arguments:
#   $1 - Directory containing .env (default REPO_ROOT or .)
# Outputs:
#   None
# Returns:
#   0 always (missing file is not an error)
#######################################
load_dotenv() {
  local root="${1:-${REPO_ROOT:-.}}"
  local env_file="${root}/.env"
  local line key val
  if [[ ! -f ${env_file} ]]; then
    return 0
  fi
  while IFS= read -r line || [[ -n ${line} ]]; do
    line="${line//$'\r'/}"
    [[ ${line} =~ ^[[:space:]]*$ ]] && continue
    [[ ${line} =~ ^[[:space:]]*# ]] && continue
    if [[ ${line} =~ ^[[:space:]]*export[[:space:]]+(.*)$ ]]; then
      line="${BASH_REMATCH[1]}"
    fi
    [[ ${line} == *"="* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    # trim whitespace around key
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ ${key} =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    # Do not clobber variables already present in the environment
    if [[ -n ${!key+x} ]]; then
      continue
    fi
    if [[ ${val} =~ ^\"(.*)\"$ ]]; then
      val="${BASH_REMATCH[1]}"
    elif [[ ${val} =~ ^\'(.*)\'$ ]]; then
      val="${BASH_REMATCH[1]}"
    fi
    export "${key}=${val}"
  done <"${env_file}"
}

#######################################
# Fail fatally if a required executable is not on PATH.
# Globals:
#   None
# Arguments:
#   $1 - Command name
# Outputs:
#   Error on stderr if missing
# Returns:
#   0 if found; otherwise exits 1 via die
#######################################
require_cmd() {
  local name="${1}"
  if ! command -v "${name}" >/dev/null 2>&1; then
    die "Required command not found: ${name}"
  fi
}

#######################################
# Locate a docker client binary (PATH first, then common absolute paths).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Absolute or PATH-resolved docker path on stdout when found
# Returns:
#   0 when found; 1 when missing
#######################################
find_docker_bin() {
  local candidate
  if candidate=$(command -v docker 2>/dev/null); then
    echo "${candidate}"
    return 0
  fi
  for candidate in /usr/bin/docker /usr/local/bin/docker; do
    if [[ -x ${candidate} ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

#######################################
# Ensure docker is available as the bare command "docker" on PATH.
# If only an absolute path exists, prepends its directory to PATH.
# Globals:
#   PATH (may be modified)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when docker is invocable; 1 otherwise
#######################################
resolve_docker_on_path() {
  local bin dir
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  if ! bin=$(find_docker_bin); then
    return 1
  fi
  dir="$(dirname "${bin}")"
  export PATH="${dir}:${PATH}"
  command -v docker >/dev/null 2>&1
}

#######################################
# Print copy-pasteable Docker CE install + docker group guidance.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Hints on stderr via err
# Returns:
#   0
#######################################
print_docker_install_hints() {
  local user
  user="$(id -un)"
  err "docker missing — install Docker CE (not snap) on DGX Spark, then re-login:"
  err "  sudo apt-get update"
  err "  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
  err "  sudo usermod -aG docker ${user}"
  err "  newgrp docker   # or disconnect/reconnect SSH"
  err "Then: ./scripts/manage.sh setup && ./scripts/manage.sh doctor"
}

#######################################
# Ensure MODELS_DIR exists and is writable by the current user.
# Tries mkdir -p as the current user; never uses sudo.
# Globals:
#   MODELS_DIR (read when $1 omitted)
# Arguments:
#   $1 - Directory path (default MODELS_DIR or /mnt/models)
# Outputs:
#   Actionable error text on stderr when not writable
# Returns:
#   0 when the directory exists and is writable; 1 otherwise
#######################################
ensure_models_dir() {
  local dir="${1:-${MODELS_DIR:-/mnt/models}}"
  local user group
  user="$(id -un)"
  group="$(id -gn)"
  if [[ ! -d ${dir} ]]; then
    mkdir -p "${dir}" 2>/dev/null || true
  fi
  if [[ -d ${dir} && -w ${dir} ]]; then
    return 0
  fi
  err "MODELS_DIR=${dir} is not writable."
  err "  ./scripts/manage.sh setup"
  err "  # or: sudo mkdir -p '${dir}' && sudo chown ${user}:${group} '${dir}'"
  err "or set MODELS_DIR to a path you own in .env (e.g. ~/models)."
  return 1
}

#######################################
# Create MODELS_DIR with sudo and chown to the current user when needed.
# Skips sudo when LAB_NO_SUDO=1 (tests / restricted environments).
# Globals:
#   LAB_NO_SUDO, MODELS_DIR
# Arguments:
#   $1 - Directory path (default MODELS_DIR or /mnt/models)
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when writable afterward; 1 on failure
#######################################
prepare_models_dir() {
  local dir="${1:-${MODELS_DIR:-/mnt/models}}"
  if ensure_models_dir "${dir}" 2>/dev/null; then
    return 0
  fi
  # ensure_models_dir already printed errors; clear intent for setup path
  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    err "MODELS_DIR=${dir} not writable and LAB_NO_SUDO=1 (cannot sudo)"
    return 1
  fi
  log "Creating MODELS_DIR with sudo: ${dir}"
  if ! sudo mkdir -p "${dir}"; then
    err "sudo mkdir -p '${dir}' failed"
    return 1
  fi
  if ! sudo chown "$(id -u):$(id -g)" "${dir}"; then
    err "sudo chown failed for '${dir}'"
    return 1
  fi
  ensure_models_dir "${dir}"
}
