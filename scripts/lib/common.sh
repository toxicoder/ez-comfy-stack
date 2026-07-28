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
# Source a .env file from a directory if present (best-effort).
# Enables set -a while sourcing so assignments export automatically.
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
  if [[ -f ${env_file} ]]; then
    # shellcheck disable=SC1090
    set -a
    # shellcheck source=/dev/null
    source "${env_file}"
    set +a
  fi
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
