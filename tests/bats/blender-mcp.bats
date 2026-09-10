#!/usr/bin/env bats
#
# Cover blender-mcp.sh and blender-llm.sh (occupancy, no execute_code).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export MCP="${UTILITIES_DIR}/blender-mcp.sh"
  export LLM="${UTILITIES_DIR}/blender-llm.sh"
  chmod +x "${MCP}" "${LLM}"
  # shellcheck disable=SC1090
  source "${MCP}"
}

teardown() {
  teardown_repo_env
}

@test "blender-mcp help list-tools occupancy_status and refuse heavy" {
  run bash "${MCP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"execute_code"* ]] || [[ "${output}" == *"No execute_code"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  run type cmd_run
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --list-tools
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --call occupancy_status
  [ "${status}" -eq 0 ]
  run mcp_occupancy_only --stdio
  [ "${status}" -eq 1 ]
  run bash "${MCP}" --list-tools
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"occupancy_status"* ]]
  [[ "${output}" != *"execute_code"* ]]
  occupancy_write blender-desk true 0 0
  run bash "${MCP}" --call occupancy_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"blender-desk"* ]]
  occupancy_write ltx false 0 0
  touch "${TEST_TMP_DIR}/compose_running"
  run bash "${MCP}" --stdio
  [ "${status}" -eq 2 ]
}

@test "blender-llm help path-d mock and missing prompt" {
  # shellcheck disable=SC1090
  source "${LLM}"
  run bash "${LLM}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Path D"* ]] || [[ "${output}" == *"llama"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  run type cmd_run
  [ "${status}" -eq 0 ]
  run llm_gguf_path
  [[ "${output}" == *"Qwen3-4B"* ]]
  run print_path_d_hint
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Path D"* ]]
  run host_llama_available
  run bash "${LLM}"
  [ "${status}" -eq 1 ]
  occupancy_write blender-desk true 0 0
  export LAB_MOCK_LLAMA=1
  run bash "${LLM}" "greybox mug"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"occupancy"* || "${output}" == *"ok"* ]]
}
