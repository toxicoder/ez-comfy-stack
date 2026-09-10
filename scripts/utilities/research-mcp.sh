#!/usr/bin/env bash
#
# ## research-mcp
#
# In-tree creative research MCP (typed tools, no execute_code, no telemetry).
# CPU GGUF + SSRF-safe HTTPS search. Does not refuse a GPU Comfy session.
#
# Usage:
#   ./scripts/utilities/research-mcp.sh [--stdio]
#   ./scripts/utilities/research-mcp.sh --list-tools
#   ./scripts/utilities/research-mcp.sh --call TOOL [JSON]
#
# @command research-mcp

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
# Print research-mcp help.
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
  echo "Usage: research-mcp.sh [--stdio] | --list-tools | --call TOOL [JSON]" >&2
  echo "  In-tree research MCP. No execute_code. No telemetry." >&2
  echo "  CPU Qwen3-4B + web search. Does not refuse a GPU session." >&2
  echo "  Does not switch occupancy idle → blender-desk." >&2
  echo "  See docs/occupancy.md" >&2
}

#######################################
# True when this invocation is occupancy/discovery-only (no llama, no search).
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   None
# Returns:
#   0 occupancy-only; 1 needs research pipeline
#######################################
mcp_occupancy_only() {
  local tool="${2:-}"
  case "${1:-}" in
    --list-tools | -h | --help | help) return 0 ;;
    --call)
      case "${tool}" in
        occupancy_status | list_lab_apps | describe_app) return 0 ;;
      esac
      ;;
  esac
  return 1
}

#######################################
# Record this PID as mcp_pid without changing occupancy mode.
# blender occupancy_set_mcp_pid maps idle → blender-desk; research must not.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
research_set_mcp_pid() {
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
#   $@  research_mcp.py args
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
    research_set_mcp_pid
  fi
  export PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}"
  exec python3 "${REPO_ROOT}/scripts/lib/research_mcp.py" "$@"
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
