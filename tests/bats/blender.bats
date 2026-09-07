#!/usr/bin/env bats
#
# Cover scripts/utilities/blender.sh (host sidecar; occupancy refuse).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export BL="${UTILITIES_DIR}/blender.sh"
  chmod +x "${BL}"
  # shellcheck disable=SC1090
  source "${BL}"
}

teardown() {
  teardown_repo_env
}

@test "blender help and missing binary" {
  run bash "${BL}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"host Blender"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  export PATH="${TEST_TMP_DIR}/bin:/usr/bin:/bin"
  run bash "${BL}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
}

@test "blender refuses when compose is running" {
  touch "${TEST_TMP_DIR}/compose_running"
  run refuse_if_comfy_running
  [ "${status}" -eq 2 ]
  run cmd_run --help
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"occupancy"* ]]
}

@test "blender execs host mock after compose idle" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  install_mock_bin blender 'echo blender-args:"$*"; exit 0'
  run cmd_run -- --background --version
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"blender-args:--background --version"* ]]
}
