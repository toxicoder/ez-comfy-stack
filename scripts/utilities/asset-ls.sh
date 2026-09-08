#!/usr/bin/env bash
#
# ## asset-ls
#
# Read-only Asset Bible catalog (status-like). Lists slugs under
# COMFY_OUTPUT_DIR/assets. Does not download, Queue, or write.
#
# Usage:
#   ./scripts/utilities/asset-ls.sh [--json] [--output-dir DIR]
#
# Environment:
#   COMFY_OUTPUT_DIR — default catalog is ${COMFY_OUTPUT_DIR}/assets
#
# Safety:
#   Assets are outputs, never MODELS_DIR. Occupancy unchanged.
#
# @command asset-ls

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

JSON_FLAG=0
OUTPUT_DIR=""
SHOW_HELP=0

#######################################
# Print usage (read-only catalog; later verbs are not shipped).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: asset-ls.sh [--json] [--output-dir DIR]" >&2
  echo "  Read-only Asset Bible catalog (status-like)." >&2
  echo "  Default DIR: ${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/assets" >&2
  echo "  Empty catalog is success." >&2
  echo "  Assets live under COMFY_OUTPUT_DIR/assets, never MODELS_DIR or guides/." >&2
  echo "  Operator verb today: asset-ls. Coming later: asset-new / asset-iterate / asset-promote." >&2
}

#######################################
# Parse CLI flags into globals.
# Globals:
#   JSON_FLAG, OUTPUT_DIR, SHOW_HELP
# Arguments:
#   $@  CLI arguments
# Outputs:
#   Error on stderr for unknown flags
# Returns:
#   0 on success; 1 on unknown/missing args
#######################################
parse_args() {
  JSON_FLAG=0
  OUTPUT_DIR=""
  SHOW_HELP=0
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json)
        JSON_FLAG=1
        ;;
      --output-dir)
        shift
        if [[ $# -lt 1 ]]; then
          err "asset-ls: --output-dir requires a directory"
          return 1
        fi
        OUTPUT_DIR="${1}"
        ;;
      -h | --help | help)
        SHOW_HELP=1
        ;;
      --*)
        err "Unknown flag: ${1}"
        return 1
        ;;
      *)
        err "Unexpected arg: ${1}"
        return 1
        ;;
    esac
    shift
  done
  return 0
}

#######################################
# List the Asset Bible catalog (read-only).
# Globals:
#   JSON_FLAG, OUTPUT_DIR, SHOW_HELP, COMFY_OUTPUT_DIR, REPO_ROOT
# Arguments:
#   $@  CLI arguments
# Outputs:
#   Human catalog or JSON on stdout; help/errors on stderr
# Returns:
#   0 on success (including empty catalog); 1 on bad flags / contract failure
#######################################
cmd_run() {
  parse_args "$@" || return $?
  if [[ ${SHOW_HELP} -eq 1 ]]; then
    cmd_help
    return 0
  fi
  local dir
  if [[ -n ${OUTPUT_DIR} ]]; then
    dir="${OUTPUT_DIR}"
  else
    dir="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/assets"
  fi
  local args
  args=(ls --output-dir "${dir}")
  if [[ ${JSON_FLAG} -eq 1 ]]; then
    args+=(--json)
  fi
  python3 "${REPO_ROOT}/scripts/lib/asset_bible.py" "${args[@]}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
