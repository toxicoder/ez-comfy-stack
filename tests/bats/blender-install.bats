#!/usr/bin/env bats
#
# Cover scripts/utilities/blender-install.sh (host apt; never Dockerfile).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export BI="${UTILITIES_DIR}/blender-install.sh"
  chmod +x "${BI}"
  export HOME="${TEST_TMP_DIR}/home"
  mkdir -p "${HOME}" "${TEST_TMP_DIR}/empty" "${TEST_TMP_DIR}/core-tools"
  local t
  for t in bash mkdir cat chmod dirname basename date uname; do
    ln -sf "$(command -v "${t}")" "${TEST_TMP_DIR}/core-tools/${t}"
  done
  export BATS_KEEP_PATH="${PATH}"
  unset BLENDER_BIN
  unset LAB_MOCK_BLENDER_INSTALL
  # shellcheck disable=SC1090
  source "${BI}"
}

teardown() {
  export PATH="${BATS_KEEP_PATH:-${PATH}}"
  teardown_repo_env
}

@test "blender-install help and unknown arg" {
  run bash "${BI}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Host apt"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  [[ "${output}" == *"does not install Blender"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  run bash "${BI}" nope
  [ "${status}" -eq 1 ]
}

@test "blender-install no-ops when blender_host_bin resolves" {
  install_mock_bin blender 'echo already; exit 0'
  run bash "${BI}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"already present"* ]]
}

@test "blender-install LAB_MOCK_BLENDER_INSTALL writes mock bin" {
  export PATH="${TEST_TMP_DIR}/empty:${TEST_TMP_DIR}/core-tools"
  hash -r
  export LAB_MOCK_BLENDER_INSTALL=1
  export LAB_MOCK_BLENDER_BIN_DIR="${TEST_TMP_DIR}/mock-blender"
  run bash "${BI}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_MOCK_BLENDER_INSTALL"* ]]
  [[ -x "${LAB_MOCK_BLENDER_BIN_DIR}/blender" ]]
  run type mock_blender_install
  [ "${status}" -eq 0 ]
}

@test "blender-install LAB_NO_SUDO prints host hint" {
  export PATH="${TEST_TMP_DIR}/empty:${TEST_TMP_DIR}/core-tools"
  hash -r
  export LAB_NO_SUDO=1
  unset LAB_MOCK_BLENDER_INSTALL
  run bash "${BI}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"LAB_NO_SUDO"* ]]
  [[ "${output}" == *"blender-install"* ]]
  [[ "${output}" == *"apt-get install -y blender"* ]]
  [[ "${output}" != *"docker/Dockerfile as install"* ]]
}

@test "blender-install without apt-get refuses unofficial tarball path" {
  # PATH must not include /bin: on Ubuntu 24.04 /bin → /usr/bin, so apt-get
  # is found and this test would sudo apt-get install blender on CI.
  export PATH="${TEST_TMP_DIR}/empty:${TEST_TMP_DIR}/core-tools"
  hash -r
  unset LAB_NO_SUDO
  unset LAB_MOCK_BLENDER_INSTALL
  run bash "${BI}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"apt-get not found"* ]]
  [[ "${output}" == *"Path D"* ]]
  [[ "${output}" != *"github.com"* ]]
}
