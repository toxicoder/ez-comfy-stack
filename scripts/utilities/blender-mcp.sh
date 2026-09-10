#!/usr/bin/env bash
#
# ## blender-mcp
#
# In-tree Blender MCP (typed tools, no execute_code, no telemetry).
# Host only — never in docker/Dockerfile. bpy tools require blender-desk.
#
# Usage:
#   ./scripts/utilities/blender-mcp.sh [--stdio]
#   ./scripts/utilities/blender-mcp.sh --list-tools
#   ./scripts/utilities/blender-mcp.sh --call TOOL [JSON]
#
# @command blender-mcp

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
# Print blender-mcp help.
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
  echo "Usage: blender-mcp.sh [--stdio] | --list-tools | --call TOOL [JSON]" >&2
  echo "  In-tree Blender MCP. No execute_code. No telemetry." >&2
  echo "  bpy tools need occupancy enter blender-desk. Never in Dockerfile." >&2
  echo "  See docs/occupancy.md" >&2
}

#######################################
# True when this invocation is occupancy-only (no bpy).
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   None
# Returns:
#   0 occupancy-only; 1 needs desk
#######################################
mcp_occupancy_only() {
  local tool="${2:-}"
  case "${1:-}" in
    --list-tools | -h | --help | help) return 0 ;;
    --call)
      case "${tool}" in
        occupancy_status | occupancy_enter) return 0 ;;
      esac
      ;;
  esac
  return 1
}

#######################################
# Run the stdlib MCP server.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  blender_mcp.py args
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
    refuse_if_heavy_gpu "Blender MCP (occupancy)" || return $?
    occupancy_set_mcp_pid $$
  fi
  exec python3 "${REPO_ROOT}/scripts/lib/blender_mcp.py" "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
