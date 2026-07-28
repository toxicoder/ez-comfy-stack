#!/usr/bin/env bats
#
# ## lib_unit.bats
#
# Purpose:
#   Unit-test every public function in scripts/lib/*.sh by direct call (strict
#   coverage inventory requires function names under tests/).
#
# Hermetic:
#   Uses test_helper mocks; no GPU, sudo, or network required.
#
# Style:
#   BATS suite; shell fragments follow Google Shell Style Guide practices
#   (quoted expansions, [[ ]], 2-space indent via shfmt where applicable).
#

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/compose.sh"
}

teardown() {
  teardown_repo_env
}

@test "paths: lab_script_dir lab_repo_root lab_compose_file lab_models_dir" {
  run lab_script_dir 0
  [ "${status}" -eq 0 ]
  run lab_repo_root
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ez-comfy-stack"* ]]
  run lab_compose_file
  [[ "${output}" == *"docker-compose.yml"* ]]
  run lab_models_dir
  [ "${status}" -eq 0 ]
}

@test "common: log warn err die load_dotenv require_cmd" {
  run log "hi"
  [ "${status}" -eq 0 ]
  run warn "w"
  [ "${status}" -eq 0 ]
  run err "e"
  [ "${status}" -eq 0 ]
  run die "boom"
  [ "${status}" -eq 1 ]
  run load_dotenv "${TEST_TMP_DIR}"
  [ "${status}" -eq 0 ]
  echo 'export FOO_FROM_ENV=1' >"${TEST_TMP_DIR}/.env"
  run load_dotenv "${TEST_TMP_DIR}"
  [ "${status}" -eq 0 ]
  run require_cmd bash
  [ "${status}" -eq 0 ]
  run require_cmd definitely-not-a-real-cmd-xyz
  [ "${status}" -ne 0 ]
}

@test "safety: parse_gib host_free host_disk headroom confirms" {
  run parse_gib_from_mem_limit 90g
  [ "${output}" = "90" ]
  run parse_gib_from_mem_limit 2048m
  [ "${output}" = "2" ]
  run parse_gib_from_mem_limit bad
  [ "${output}" = "0" ]
  run parse_gib_from_mem_limit 1073741824
  [ "${status}" -eq 0 ]

  export LAB_MOCK_FREE_MEM_GIB=50
  run host_free_mem_gib
  [ "${output}" = "50" ]

  export LAB_MOCK_DISK_FREE_GIB=12
  run host_disk_free_gib /
  [ "${output}" = "12" ]

  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export MIN_HOST_FREE_GIB=28
  run check_host_headroom
  [ "${status}" -eq 0 ]

  export LAB_MOCK_FREE_MEM_GIB=1
  run check_host_headroom
  [ "${status}" -ne 0 ]

  export MEM_LIMIT=120g
  export MIN_HOST_FREE_GIB=28
  run check_mem_limit_vs_headroom
  [ "${status}" -eq 0 ]

  export LAB_NON_INTERACTIVE=1
  export LAB_CONFIRM_TOKEN=yes
  run require_heavy_confirm "unit"
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=
  run require_heavy_confirm "unit"
  [ "${status}" -eq 1 ]

  export LAB_CONFIRM_TOKEN=DELETE
  run require_delete_confirm
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=
  run require_delete_confirm
  [ "${status}" -eq 1 ]
}

@test "compose: compose_cmd compose_run require_docker status stacks logs" {
  run compose_cmd
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"docker"* ]]

  run compose_run version
  [ "${status}" -eq 0 ]

  run require_docker
  [ "${status}" -eq 0 ]

  run compose_status_json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-to-ltx"* ]]

  run compose_is_running
  [ "${status}" -ne 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  install_docker_mocks
  run compose_is_running
  [ "${status}" -eq 0 ]

  export MODELS_DIR="${TEST_TMP_DIR}/models"
  run stack_start
  [ "${status}" -eq 0 ]
  run stack_stop
  [ "${status}" -eq 0 ]
  run stack_cleanup_state
  [ "${status}" -eq 0 ]
  run stack_logs
  [ "${status}" -eq 0 ]
}
