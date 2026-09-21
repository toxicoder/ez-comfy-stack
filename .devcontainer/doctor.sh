#!/usr/bin/env bash
#
# ## Devcontainer / contributor environment doctor
#
# Verifies CLI tools required for bazelisk //:fix, //:lint, and //:validate.
#
# Usage:
#   bash .devcontainer/doctor.sh
#   bash .devcontainer/doctor.sh --help
#   bash .devcontainer/doctor.sh --quiet
#
# Environment:
#   DEVCONTAINER_DOCTOR_STRICT=0 — warn only (exit 0)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSIONS_FILE="${SCRIPT_DIR}/tool-versions.env"
QUIET=0
STRICT="${DEVCONTAINER_DOCTOR_STRICT:-1}"
FAIL=0

#######################################
# Print usage.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage on stdout
# Returns:
#   0
#######################################
usage() {
  cat <<'EOF'
Usage: doctor.sh [--quiet] [--help]

Verify contributor tooling (bazelisk, shellcheck, shfmt, buildifier,
python3, node, grok) against .devcontainer/tool-versions.env.

Preferred next step: bazelisk run //:validate

Platform notes:
  - Container is always Linux (amd64 or arm64).
  - Hosts: macOS Apple Silicon, Windows x86_64 (Docker Desktop/WSL2), Linux, DGX Spark.
  - Grok Build talks to host LLMs at host.docker.internal (not --network=host).
EOF
}

#######################################
# Log unless --quiet.
# Globals:
#   QUIET
# Arguments:
#   $@ - message
# Outputs:
#   Message on stdout
# Returns:
#   0
#######################################
log() {
  if [[ ${QUIET} -eq 0 ]]; then
    echo "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    -q | --quiet)
      QUIET=1
      shift
      ;;
    *)
      echo "doctor: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f ${VERSIONS_FILE} ]]; then
  echo "doctor: missing ${VERSIONS_FILE}" >&2
  exit 2
fi

set -a
# shellcheck source=tool-versions.env disable=SC1091
source "${VERSIONS_FILE}"
set +a

require() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    log "ok ${name}"
  else
    echo "missing ${name}" >&2
    FAIL=1
  fi
}

require bazelisk
require buildifier
require shfmt
require shellcheck
require python3
require node
require grok

if [[ ${FAIL} -ne 0 ]]; then
  if [[ ${STRICT} == "0" ]]; then
    log "doctor: missing tools (strict=0)"
    exit 0
  fi
  exit 1
fi
log "doctor: contributor tools present"
exit 0
