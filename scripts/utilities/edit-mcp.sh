#!/usr/bin/env bash
#
# ## edit-mcp
#
# In-tree editing-lane MCP: host thin client of the ComfyUI /ez_edit routes.
# One typed tool per protocol.TOOL_CATALOG name, one HTTP call per tool.
# No execute_code, no telemetry, no arbitrary fetch_url, no Queue of its own.
#
# Usage:
#   bazelisk run //scripts:run-utility -- edit-mcp [--stdio]
#   ./scripts/utilities/edit-mcp.sh [--stdio]
#   ./scripts/utilities/edit-mcp.sh --list-tools
#   ./scripts/utilities/edit-mcp.sh --call TOOL [JSON]
#   ./scripts/utilities/edit-mcp.sh status [--json]
#
# The ComfyUI origin is EZ_EDIT_COMFY_URL, else http://127.0.0.1:${COMFY_PORT:-8188}.
#
# @command edit-mcp

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
# Print edit-mcp help.
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
  echo "Usage: edit-mcp.sh [--stdio] | --list-tools | --call TOOL [JSON] | status [--json]" >&2
  echo "  In-tree editing MCP. Typed tools only; no execute_code, no telemetry," >&2
  echo "  no arbitrary fetch_url. Every tool is one call to a ComfyUI /ez_edit route." >&2
  echo "  stdio refuses when ComfyUI is unreachable: ./scripts/manage.sh start first." >&2
  echo "  Origin: EZ_EDIT_COMFY_URL, else loopback http://127.0.0.1:8188 (COMFY_PORT)" >&2
  echo "  See docs/occupancy.md" >&2
}

#######################################
# True when this invocation is discovery-only (no ComfyUI HTTP at all).
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   None
# Returns:
#   0 discovery-only; 1 talks to ComfyUI
#######################################
mcp_occupancy_only() {
  local tool="${2:-}"
  case "${1:-}" in
    --list-tools | -h | --help | help) return 0 ;;
    --call)
      case "${tool}" in
        occupancy_status) return 0 ;;
      esac
      ;;
  esac
  return 1
}

#######################################
# True when this invocation serves the MCP client on stdin/stdout.
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   None
# Returns:
#   0 stdio mode (the default verb); 1 another verb
#######################################
mcp_stdio_mode() {
  case "${1:-}" in
    --stdio | stdio) return 0 ;;
  esac
  [[ ${#} -eq 0 ]]
}

#######################################
# ComfyUI origin for the /ez_edit routes (loopback by default).
# Globals:
#   EZ_EDIT_COMFY_URL, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   Origin URL on stdout (no trailing slash)
# Returns:
#   0
#######################################
edit_comfy_url() {
  if [[ -n ${EZ_EDIT_COMFY_URL:-} ]]; then
    printf '%s\n' "${EZ_EDIT_COMFY_URL%/}"
    return 0
  fi
  occupancy_comfy_url
}

#######################################
# True when ComfyUI answers /system_stats (same probe as status --json).
# Globals:
#   EZ_EDIT_COMFY_URL, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 reachable; non-zero (curl status) unreachable
#######################################
comfy_reachable() {
  curl -sf --max-time 3 "$(edit_comfy_url)/system_stats" >/dev/null 2>&1
}

#######################################
# Record this PID as mcp_pid without changing occupancy mode.
# blender occupancy_set_mcp_pid maps idle -> blender-desk; edit must not.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
edit_set_mcp_pid() {
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
# Print edit-mcp status (human or JSON): ComfyUI reachability + occupancy.
# Globals:
#   COMFY_OUTPUT_DIR, EZ_EDIT_ENABLED, EZ_EDIT_COMFY_URL, COMFY_PORT
# Arguments:
#   $1  Optional --json
# Outputs:
#   JSON on stdout when --json; log line on stderr otherwise
# Returns:
#   0
#######################################
cmd_status() {
  local json_flag="" reachable="false" url occupancy enabled="true"
  [[ ${1:-} == "--json" ]] && json_flag="--json"
  url="$(edit_comfy_url)"
  if comfy_reachable; then
    reachable="true"
  fi
  occupancy="$(occupancy_mode)"
  [[ ${EZ_EDIT_ENABLED:-1} == "0" ]] && enabled="false"
  if [[ ${json_flag} == "--json" ]]; then
    printf '{"reachable":%s,"url":"%s","occupancy":"%s","server":"ez-edit","enabled":%s}\n' \
      "${reachable}" "${url}" "${occupancy}" "${enabled}"
    return 0
  fi
  log "edit-mcp server=ez-edit reachable=${reachable} url=${url} occupancy=${occupancy} enabled=${enabled}"
}

#######################################
# Run the stdlib MCP server.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  edit_mcp.py args
# Outputs:
#   MCP JSON; refuse text on stderr
# Returns:
#   python status; 2 when stdio cannot reach ComfyUI
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  if mcp_stdio_mode "$@" && ! comfy_reachable; then
    err "ComfyUI unreachable at $(edit_comfy_url) - edit tools cannot answer"
    err "  ./scripts/manage.sh start   then: ./scripts/utilities/edit-mcp.sh status --json"
    return 2
  fi
  if ! mcp_occupancy_only "$@"; then
    edit_set_mcp_pid
  fi
  export PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}"
  exec python3 "${REPO_ROOT}/scripts/lib/edit_mcp.py" "$@"
}

#######################################
# Dispatch the operator verbs.
# Globals:
#   None
# Arguments:
#   $@  CLI args
# Outputs:
#   Whatever the chosen verb prints
# Returns:
#   Verb status
#######################################
cmd_main() {
  case "${1:-}" in
    -h | --help | help)
      cmd_help
      return 0
      ;;
    status)
      shift
      cmd_status "$@"
      ;;
    *)
      cmd_run "$@"
      ;;
  esac
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_main "$@"
fi
