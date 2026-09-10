#!/usr/bin/env bats
#
# Cover research-mcp.sh (occupancy pid, no execute_code, no GPU refuse).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export MCP="${UTILITIES_DIR}/research-mcp.sh"
  chmod +x "${MCP}"
  # shellcheck disable=SC1090
  source "${MCP}"
}

teardown() {
  teardown_repo_env
}

@test "research-mcp help list-tools occupancy_status and no execute_code" {
  run bash "${MCP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"execute_code"* ]] || [[ "${output}" == *"No execute_code"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  run type cmd_run
  [ "${status}" -eq 0 ]
  run type research_set_mcp_pid
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --list-tools
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call occupancy_status
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call list_lab_apps
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call describe_app
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call web_search
  [ "${status}" -eq 1 ]
  run mcp_occupancy_only --stdio
  [ "${status}" -eq 1 ]
  run bash "${MCP}" --list-tools
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"occupancy_status"* ]]
  [[ "${output}" == *"research"* ]]
  [[ "${output}" != *"execute_code"* ]]
  occupancy_write idle false 0 0
  run bash "${MCP}" --call occupancy_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"idle"* ]]
}

@test "research-mcp stdio on idle does not switch to blender-desk" {
  occupancy_write idle false 0 0
  run bash -c "bash \"${MCP}\" --stdio </dev/null"
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "idle" ]
}

@test "research-mcp stdio does not refuse a heavy GPU occupancy" {
  occupancy_write ltx false 0 0
  touch "${TEST_TMP_DIR}/compose_running"
  run bash -c "bash \"${MCP}\" --stdio </dev/null"
  [ "${status}" -eq 0 ]
}
