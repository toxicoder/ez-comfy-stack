#!/usr/bin/env bats
#
# Cover scripts/lib/occupancy.sh and scripts/utilities/occupancy.sh.

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export OCC="${UTILITIES_DIR}/occupancy.sh"
  chmod +x "${OCC}"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/compose.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/occupancy.sh"
}

teardown() {
  teardown_repo_env
}

@test "occupancy help status modes and default json" {
  run bash "${OCC}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"blender-desk"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run occupancy_modes
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"idle"* ]]
  [[ "${output}" == *"blender-desk"* ]]
  [[ "${output}" == *"trellis"* ]]
  run occupancy_valid_mode idle
  [ "${status}" -eq 0 ]
  run occupancy_valid_mode nope
  [ "${status}" -eq 1 ]
  run occupancy_default_json
  [[ "${output}" == *'"mode": "idle"'* || "${output}" == *'"mode":"idle"'* ]]
  run occupancy_state_path
  [[ "${output}" == *".occupancy.json"* ]]
  run occupancy_comfy_url
  [[ "${output}" == *"127.0.0.1"* ]]
  run occupancy_read
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "idle" ]
  run occupancy_is_parked
  [ "${status}" -eq 1 ]
}

@test "occupancy write field parked and refuse_if_heavy_gpu park exception" {
  occupancy_write blender-desk true 0 0
  run occupancy_field mode
  [ "${output}" = "blender-desk" ]
  run occupancy_field parked
  [ "${output}" = "true" ]
  run occupancy_is_parked
  [ "${status}" -eq 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  export LAB_MOCK_COMFY_QUEUE=idle
  run refuse_if_heavy_gpu "Blender (occupancy)"
  [ "${status}" -eq 0 ]
  run refuse_if_comfy_running "NVENC preview (encoder contention)"
  [ "${status}" -eq 2 ]
  occupancy_write idle false 0 0
  run refuse_if_heavy_gpu "guide pack dump (occupancy)"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"blender-desk"* ]]
}

@test "occupancy http mock queue free stats and busy refuse" {
  export LAB_MOCK_COMFY_QUEUE=idle
  run occupancy_http_mock GET /queue
  [[ "${output}" == *"queue_running"* ]]
  run occupancy_http GET /queue
  [ "${status}" -eq 0 ]
  run occupancy_http POST /free '{"unload_models":true}'
  [ "${status}" -eq 0 ]
  run occupancy_http GET /system_stats
  [ "${status}" -eq 0 ]
  run occupancy_http GET /nope
  [ "${status}" -eq 1 ]
  rm -f "${TEST_TMP_DIR}/compose_running"
  run comfy_queue_busy
  [ "${status}" -eq 1 ]
  run comfy_free_memory
  [ "${status}" -eq 0 ]
  run comfy_system_stats
  [[ "${output}" == "{}" ]]
  touch "${TEST_TMP_DIR}/compose_running"
  export LAB_MOCK_COMFY_QUEUE=busy
  run comfy_queue_busy
  [ "${status}" -eq 0 ]
  occupancy_write blender-desk true 0 0
  run refuse_if_heavy_gpu "house views dump (occupancy)"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"queue"* ]]
  export LAB_MOCK_COMFY_QUEUE=idle
  run comfy_free_memory
  [ "${status}" -eq 0 ]
  run comfy_system_stats
  [[ "${output}" == *"ram_free"* || "${output}" == *"devices"* ]]
  export LAB_MOCK_COMFY_FREE=fail
  run comfy_free_memory
  [ "${status}" -eq 1 ]
}

@test "occupancy pids stop_blender_desk cycles refuse and enter" {
  occupancy_write blender-desk false $$ 0
  run blender_pid_alive
  [ "${status}" -eq 0 ]
  run mcp_pid_alive
  [ "${status}" -eq 1 ]
  run occupancy_pid_alive 0
  [ "${status}" -eq 1 ]
  occupancy_stop_pid 0
  occupancy_stop_pid $$
  occupancy_set_blender_pid 0
  occupancy_set_mcp_pid 0
  stop_blender_desk
  run blender_pid_alive
  [ "${status}" -eq 1 ]
  touch "${TEST_TMP_DIR}/compose_running"
  export CYCLES_DEVICE=CUDA
  run refuse_cycles_while_compose --background
  [ "${status}" -eq 2 ]
  unset CYCLES_DEVICE
  run refuse_cycles_while_compose --engine CYCLES
  [ "${status}" -eq 2 ]
  run refuse_cycles_while_compose --background
  [ "${status}" -eq 0 ]
  rm -f "${TEST_TMP_DIR}/compose_running"
  export CYCLES_DEVICE=CUDA
  run refuse_cycles_while_compose
  [ "${status}" -eq 0 ]
  unset CYCLES_DEVICE
  occupancy_write idle false 0 0
  run occupancy_enter blender-desk
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "blender-desk" ]
  run occupancy_enter trellis
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"start"* ]]
  touch "${TEST_TMP_DIR}/compose_running"
  export LAB_MOCK_COMFY_QUEUE=idle
  run occupancy_enter blender-desk
  [ "${status}" -eq 0 ]
  run occupancy_is_parked
  [ "${status}" -eq 0 ]
  occupancy_set_blender_pid $$
  run occupancy_enter klein
  [ "${status}" -eq 2 ]
  run occupancy_enter klein 1
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "klein" ]
  run occupancy_status_json
  [[ "${output}" == *"compose_live"* ]]
  run occupancy_enter idle
  [ "${status}" -eq 0 ]
  run occupancy_mode
  [ "${output}" = "idle" ]
}

@test "occupancy utility functions exist for coverage inventory" {
  # shellcheck disable=SC1090
  source "${OCC}"
  run type cmd_help
  [ "${status}" -eq 0 ]
  run type parse_args
  [ "${status}" -eq 0 ]
  run type cmd_status
  [ "${status}" -eq 0 ]
  run type cmd_enter
  [ "${status}" -eq 0 ]
}

@test "occupancy.sh CLI status enter idle json and unknown" {
  run bash "${OCC}" status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"mode="* ]]
  run bash "${OCC}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"\"mode\""* ]]
  run bash "${OCC}" enter blender-desk
  [ "${status}" -eq 0 ]
  run bash "${OCC}" enter --mode klein
  [ "${status}" -eq 1 ]
  run bash "${OCC}" idle
  [ "${status}" -eq 0 ]
  run bash "${OCC}" enter
  [ "${status}" -eq 1 ]
  run bash "${OCC}" --nope
  [ "${status}" -eq 1 ]
  run bash "${OCC}" nope
  [ "${status}" -eq 1 ]
}
