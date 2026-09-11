#!/usr/bin/env bash
#
# ## occupancy
#
# Occupancy desk: park Comfy, run host Workbench Blender, then restore a
# heavy graph family (klein / trellis / wan / ltx). One GB10 GPU job.
#
# Usage:
#   ./scripts/utilities/occupancy.sh status [--json]
#   ./scripts/utilities/occupancy.sh enter blender-desk|llm-desk|klein|trellis|wan|ltx|idle [--yes]
#
# Safety:
#   Does not start Compose (start still types yes). Does not weaken
#   restart: "no", mem_limit 90g, headroom, or download-limit clear-on-exit.
#   NVENC stays XOR with compose-up. blender-desk is POST /free + Workbench.
#   llm-desk is POST /free + host llama-server (XOR with blender-desk / visual).
#
# @command occupancy

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/occupancy.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/occupancy.sh"

JSON_FLAG=""
YES=0
CMD="status"
TARGET=""

#######################################
# Print occupancy CLI help.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: occupancy.sh status [--json]" >&2
  echo "       occupancy.sh enter MODE [--yes]" >&2
  echo "  Modes: $(occupancy_modes)" >&2
  echo "  blender-desk parks Comfy (POST /free) for host Workbench dumps." >&2
  echo "  llm-desk parks Comfy and starts the host 35B sidecar (127.0.0.1)." >&2
  echo "  Heavy modes stop the Blender desk and the 35B sidecar; they do not start Compose." >&2
  echo "  Graph occupancy label llm is not a CLI mode. See docs/occupancy.md." >&2
  echo "  Never in docker/Dockerfile." >&2
}

#######################################
# Parse occupancy CLI.
# Globals:
#   JSON_FLAG, YES, CMD, TARGET
# Arguments:
#   $@  CLI args
# Outputs:
#   Help; errors on unknown args
# Returns:
#   0; exits 0 on help; 1 on bad args
#######################################
parse_args() {
  JSON_FLAG=""
  YES=0
  CMD="status"
  TARGET=""
  if [[ $# -eq 0 ]]; then
    CMD="status"
    return 0
  fi
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      -h | --help | help)
        cmd_help
        exit 0
        ;;
      --json) JSON_FLAG="--json" ;;
      --yes | -y) YES=1 ;;
      --mode)
        CMD="enter"
        shift
        TARGET="${1:-}"
        if [[ -z ${TARGET} ]]; then
          err "occupancy --mode requires a mode"
          exit 1
        fi
        ;;
      status) CMD="status" ;;
      enter)
        CMD="enter"
        if [[ $# -ge 2 && ${2} != --* ]]; then
          shift
          TARGET="${1}"
        fi
        ;;
      idle)
        CMD="enter"
        TARGET="idle"
        ;;
      --*)
        err "Unknown arg: ${1}"
        exit 1
        ;;
      *)
        err "Unknown arg: ${1}"
        cmd_help
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# Print occupancy status (human or JSON).
# Globals:
#   JSON_FLAG
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; logs on stderr
# Returns:
#   0
#######################################
cmd_status() {
  local json mode parked queue compose_live
  json="$(occupancy_status_json)"
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '%s\n' "${json}"
    return 0
  fi
  mode="$(printf '%s' "${json}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("mode","idle"))')"
  parked="$(printf '%s' "${json}" | python3 -c 'import json,sys; print("true" if json.load(sys.stdin).get("parked") else "false")')"
  queue="$(printf '%s' "${json}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("queue","idle"))')"
  compose_live="$(printf '%s' "${json}" | python3 -c 'import json,sys; print("true" if json.load(sys.stdin).get("compose_live") else "false")')"
  log "occupancy mode=${mode} parked=${parked} compose=${compose_live} queue=${queue}"
}

#######################################
# Enter an occupancy mode.
# Globals:
#   TARGET, YES
# Arguments:
#   None
# Outputs:
#   Status on stderr
# Returns:
#   occupancy_enter status
#######################################
cmd_enter() {
  if [[ -z ${TARGET} ]]; then
    err "occupancy enter requires a mode"
    cmd_help
    return 1
  fi
  occupancy_enter "${TARGET}" "${YES}"
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@  CLI args
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    enter) cmd_enter ;;
    *)
      err "Unknown command: ${CMD}"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
