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
  export HOME="${TEST_TMP_DIR}/home"
  mkdir -p "${HOME}" "${TEST_TMP_DIR}/empty"
  unset BLENDER_BIN
  export PATH="${TEST_TMP_DIR}/empty:/usr/bin:/bin"
  run bash "${BL}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
  [[ "${output}" == *"blender-install"* ]]
  [[ "${output}" == *"apt-get install -y blender"* ]]
}

@test "blender refuses when compose is running" {
  touch "${TEST_TMP_DIR}/compose_running"
  run refuse_if_comfy_running
  [ "${status}" -eq 2 ]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  run cmd_run -- --background
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

@test "blender execs when compose is parked blender-desk" {
  touch "${TEST_TMP_DIR}/compose_running"
  occupancy_write blender-desk true 0 0
  install_mock_bin blender 'echo blender-parked:"$*"; exit 0'
  run cmd_run -- --background --version
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"blender-parked:--background --version"* ]]
}

@test "blender execs BLENDER_BIN off PATH" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  export HOME="${TEST_TMP_DIR}/home"
  mkdir -p "${HOME}" "${TEST_TMP_DIR}/offpath" "${TEST_TMP_DIR}/empty"
  local off="${TEST_TMP_DIR}/offpath/blender"
  printf '%s\n' '#!/usr/bin/env bash' 'echo blender-off:"$*"' 'exit 0' >"${off}"
  chmod +x "${off}"
  export BLENDER_BIN="${off}"
  export PATH="${TEST_TMP_DIR}/empty:/usr/bin:/bin"
  run cmd_run -- --background --version
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"blender-off:--background --version"* ]]
}
