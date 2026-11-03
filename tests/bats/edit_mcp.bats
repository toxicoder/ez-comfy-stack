#!/usr/bin/env bats
#
# Cover edit-mcp.sh (thin client verbs, occupancy pid, stdio refuse).
#
# Hermetic: curl is mocked (no socket ever opens) and the MCP python server
# runs for real but only on verbs that need no network (--list-tools,
# --call occupancy_status, --call <unknown>).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export MCP="${UTILITIES_DIR}/edit-mcp.sh"
  export EZ_EDIT_COMFY_URL="http://127.0.0.1:8188"
  chmod +x "${MCP}"
  # shellcheck disable=SC1090
  source "${MCP}"
}

teardown() {
  teardown_repo_env
}

# @param $1 exit code the curl mock should return
mock_curl() {
  install_mock_bin curl "exit ${1:-0}"
}

@test "edit-mcp help documents verbs and forbids execute_code" {
  run bash "${MCP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--list-tools"* ]]
  [[ "${output}" == *"status [--json]"* ]]
  [[ "${output}" == *"no execute_code"* ]]
  [[ "${output}" == *"/ez_edit"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  run type cmd_main
  [ "${status}" -eq 0 ]
  run type cmd_run
  [ "${status}" -eq 0 ]
  run type cmd_status
  [ "${status}" -eq 0 ]
  run type mcp_occupancy_only
  [ "${status}" -eq 0 ]
  run type mcp_stdio_mode
  [ "${status}" -eq 0 ]
  run type edit_comfy_url
  [ "${status}" -eq 0 ]
  run type comfy_reachable
  [ "${status}" -eq 0 ]
  run type edit_set_mcp_pid
  [ "${status}" -eq 0 ]
}

@test "edit-mcp classifies discovery-only and stdio invocations" {
  run mcp_occupancy_only --list-tools
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --help
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call occupancy_status
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call edit_get_state
  [ "${status}" -eq 1 ]
  run mcp_occupancy_only --stdio
  [ "${status}" -eq 1 ]
  run mcp_stdio_mode
  [ "${status}" -eq 0 ]
  run mcp_stdio_mode --stdio
  [ "${status}" -eq 0 ]
  run mcp_stdio_mode stdio
  [ "${status}" -eq 0 ]
  run mcp_stdio_mode --list-tools
  [ "${status}" -eq 1 ]
}

@test "edit-mcp comfy url follows EZ_EDIT_COMFY_URL then COMFY_PORT" {
  unset EZ_EDIT_COMFY_URL
  export COMFY_PORT=8199
  run edit_comfy_url
  [ "${output}" = "http://127.0.0.1:8199" ]
  export EZ_EDIT_COMFY_URL="http://127.0.0.1:8189/"
  run edit_comfy_url
  [ "${output}" = "http://127.0.0.1:8189" ]
  mock_curl 0
  run comfy_reachable
  [ "${status}" -eq 0 ]
  mock_curl 22
  run comfy_reachable
  [ "${status}" -ne 0 ]
}

@test "edit-mcp status --json reports ComfyUI reachability" {
  occupancy_write idle false 0 0
  mock_curl 0
  run bash -c "bash \"${MCP}\" status --json 2>/dev/null"
  [ "${status}" -eq 0 ]
  [ "${#lines[@]}" -eq 1 ]
  python3 -c 'import json, sys
d = json.loads(sys.argv[1])
assert d["reachable"] is True, d
assert d["url"] == "http://127.0.0.1:8188", d
assert d["occupancy"] == "idle", d
assert d["server"] == "ez-edit", d
assert d["enabled"] is True, d
' "${output}"
  mock_curl 22
  run bash -c "bash \"${MCP}\" status --json 2>/dev/null"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"reachable":false'* ]]
  export EZ_EDIT_ENABLED=0
  run bash -c "bash \"${MCP}\" status --json 2>/dev/null"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"enabled":false'* ]]
  unset EZ_EDIT_ENABLED
  mock_curl 0
  run bash "${MCP}" status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"reachable=true"* ]]
  [[ "${output}" == *"server=ez-edit"* ]]
  run cmd_status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"reachable":true'* ]]
}

@test "edit-mcp records mcp_pid without switching occupancy mode" {
  occupancy_write idle false 0 0
  mock_curl 0
  run edit_set_mcp_pid
  [ "${status}" -eq 0 ]
  run occupancy_field mcp_pid
  [ "${output}" != "0" ]
  run occupancy_mode
  [ "${output}" = "idle" ]
}

@test "edit-mcp list-tools prints every catalog tool with Comfy down" {
  mock_curl 22
  run bash "${MCP}" --list-tools
  [ "${status}" -eq 0 ]
  for tool in edit_get_state edit_import edit_apply_ops edit_render \
    edit_job_status edit_generate_clip edit_export_edl occupancy_status; do
    [[ "${output}" == *"${tool}"* ]] || return 1
  done
  [[ "${output}" != *"execute_code"* ]]
  [[ "${output}" != *"fetch_url"* ]]
  run cmd_run --list-tools
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"edit_apply_ops"* ]]
  run cmd_run --help
  [ "${status}" -eq 0 ]
}

@test "edit-mcp call reports unknown tools and reads occupancy offline" {
  mock_curl 22
  run bash "${MCP}" --call nope_tool
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown tool"* ]]
  occupancy_write klein false 0 0
  run bash "${MCP}" --call occupancy_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"mode": "klein"'* ]]
  run bash "${MCP}" --call edit_import '{}'
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"missing required path"* ]]
}

@test "edit-mcp stdio refuses when ComfyUI is unreachable" {
  occupancy_write idle false 0 0
  mock_curl 22
  run bash -c "bash \"${MCP}\" --stdio </dev/null"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"ComfyUI unreachable"* ]]
  run bash -c "bash \"${MCP}\" </dev/null"
  [ "${status}" -eq 2 ]
  run occupancy_mode
  [ "${output}" = "idle" ]
}

@test "edit-mcp stdio serves initialize when ComfyUI is reachable" {
  occupancy_write idle false 0 0
  mock_curl 0
  local req="${TEST_TMP_DIR}/rpc.jsonl"
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize"}' >"${req}"
  run bash -c "bash \"${MCP}\" --stdio <\"${req}\""
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ez-edit"* ]]
  [[ "${output}" == *"2024-11-05"* ]]
  run occupancy_field mcp_pid
  [ "${output}" != "0" ]
}

@test "edit-mcp stdio does not refuse a heavy GPU occupancy" {
  occupancy_write ltx false 0 0
  touch "${TEST_TMP_DIR}/compose_running"
  mock_curl 0
  run bash -c "bash \"${MCP}\" --stdio </dev/null"
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "ltx" ]
}

@test "edit-mcp cmd_main dispatches help and unknown args" {
  mock_curl 22
  run cmd_main --help
  [ "${status}" -eq 0 ]
  run cmd_main status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"reachable":false'* ]]
  run cmd_main --nope
  [ "${status}" -ne 0 ]
}
