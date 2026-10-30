#!/usr/bin/env bats
#
# Hermetic tests for docker/compose_config_test.sh.
#
# The script is the //docker:compose_config gate. It renders the compose file
# with `docker compose config -q`, so the cases below mock the docker CLI and
# pin the checkout root rather than talking to a daemon.

load 'test_helper'

setup() {
  setup_repo_env
  SCRIPT="${REPO_ROOT}/docker/compose_config_test.sh"
  FAKE_ROOT="${TEST_TMP_DIR}/fake-checkout"
  mkdir -p "${FAKE_ROOT}/docker"
  printf 'services: {}\n' >"${FAKE_ROOT}/docker/docker-compose.yml"
}

teardown() {
  teardown_repo_env
}

# Pin bazel_checkout_root to a scratch tree so the gate never reads the real
# checkout, then run one function from the sourced script.
_run_gate() {
  local fn="$1" root="$2"
  run bash -c "
    source '${SCRIPT}'
    bazel_checkout_root() { printf '%s\n' '${root}'; }
    ${fn}
  "
}

@test "run_compose_config passes when compose renders" {
  install_mock_bin docker 'exit 0'
  _run_gate run_compose_config "${FAKE_ROOT}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Compose config is valid."* ]]
}

@test "run_compose_config fails when the compose file is absent" {
  install_mock_bin docker 'exit 0'
  _run_gate run_compose_config "${TEST_TMP_DIR}/nowhere"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"no docker/docker-compose.yml"* ]]
}

@test "run_compose_config fails when compose reports a problem" {
  install_mock_bin docker 'echo "bad anchor" >&2; exit 1'
  _run_gate run_compose_config "${FAKE_ROOT}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"does not render"* ]]
}

@test "run_compose_config passes the real file to compose" {
  install_mock_bin docker 'echo "docker $*" >>"${TEST_TMP_DIR}/docker.log"; exit 0'
  _run_gate run_compose_config "${FAKE_ROOT}"
  [ "${status}" -eq 0 ]
  grep -q -- 'config -q' "${TEST_TMP_DIR}/docker.log"
  grep -q 'docker/docker-compose.yml' "${TEST_TMP_DIR}/docker.log"
}

@test "main skips when the docker CLI is absent" {
  mock_path_hide docker
  _run_gate main "${FAKE_ROOT}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"docker missing"* ]]
  mock_path_restore
}

@test "main fails when docker is absent under REQUIRE_LINT_TOOLS" {
  mock_path_hide docker
  run bash -c "
    export REQUIRE_LINT_TOOLS=1
    source '${SCRIPT}'
    bazel_checkout_root() { printf '%s\n' '${FAKE_ROOT}'; }
    main
  "
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"docker missing"* ]]
  mock_path_restore
}
