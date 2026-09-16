#!/usr/bin/env bash
#
# ## studio-mcp
#
# In-tree studio MCP (typed tools, no execute_code, no telemetry, no Queue).
# Clones shipped _lab graphs into live _user/. CPU GGUF optional.
# Does not refuse a GPU Comfy session.
#
# Usage:
#   ./scripts/utilities/studio-mcp.sh [--stdio]
#   ./scripts/utilities/studio-mcp.sh --list-tools
#   ./scripts/utilities/studio-mcp.sh --call TOOL [JSON]
#
# @command studio-mcp

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

#######################################
# Print studio-mcp help.
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
  echo "Usage: studio-mcp.sh [--stdio] | --list-tools | --call TOOL [JSON]" >&2
  echo "  In-tree studio MCP. No execute_code. No telemetry. No Queue." >&2
  echo "  Clones shipped _lab graphs into live _user/. Optional CPU GGUF." >&2
  echo "  Does not refuse a GPU session. Does not switch occupancy idle → blender-desk." >&2
  echo "  See docs/occupancy.md" >&2
}

#######################################
# True when this invocation is occupancy/discovery-only (no llama).
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   None
# Returns:
#   0 occupancy-only; 1 needs forge pipeline
#######################################
mcp_occupancy_only() {
  local tool="${2:-}"
  case "${1:-}" in
    --list-tools | -h | --help | help) return 0 ;;
    --call)
      case "${tool}" in
        occupancy_status | search_templates | get_template | describe_app | validate_workflow)
          return 0
          ;;
      esac
      ;;
  esac
  return 1
}

#######################################
# Record this PID as mcp_pid without changing occupancy mode.
# blender occupancy_set_mcp_pid maps idle → blender-desk; studio must not.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
studio_set_mcp_pid() {
  local mode parked blender
  mode="$(occupancy_mode)"
  parked="$(occupancy_field parked)"
  blender="$(occupancy_field blender_pid)"
  [[ -n ${mode} ]] || mode="idle"
  [[ -n ${parked} ]] || parked="false"
  [[ -n ${blender} ]] || blender="0"
  occupancy_write "${mode}" "${parked}" "${blender}" "$$"
}

#######################################
# Run the stdlib MCP server.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  studio_mcp.py args
# Outputs:
#   MCP JSON
# Returns:
#   python status
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  if ! mcp_occupancy_only "$@"; then
    studio_set_mcp_pid
  fi
  export PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}"
  exec python3 "${REPO_ROOT}/scripts/lib/studio_mcp.py" "$@"
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
