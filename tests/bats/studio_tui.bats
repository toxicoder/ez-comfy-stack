#!/usr/bin/env bats
#
# Cover scripts/utilities/studio-tui.sh (guarded operator console launcher).
#
# The launcher's whole job is the environment it hands to `python3 -m tui.cli`:
# the two PYTHONPATH roots the package needs, the repository root it reads the
# lab tree from, and a verbatim flag forward. python3 is mocked so the suite
# stays hermetic and never opens a curses screen.

load 'test_helper'

setup() {
  setup_repo_env
  export TUI="${UTILITIES_DIR}/studio-tui.sh"
  chmod +x "${TUI}"
  # shellcheck disable=SC1090
  source "${TUI}"
}

teardown() {
  teardown_repo_env
}

@test "studio-tui help via cmd_help cmd_run" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage: studio-tui.sh"* ]]
  [[ "${output}" == *"--check"* ]]
  [[ "${output}" == *"--read-only"* ]]
  [[ "${output}" == *"typed confirmations"* ]]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage: studio-tui.sh"* ]]
  run cmd_run help
  [ "${status}" -eq 0 ]
  run bash "${TUI}" --help
  [ "${status}" -eq 0 ]
}

@test "studio-tui execs tui.cli with both PYTHONPATH roots" {
  install_mock_bin python3 'printf "%s\n" "PY=${PYTHONPATH}" "ARGC=${#}" "ARGS=$*" > "${TEST_TMP_DIR}/call.txt"; exit 0'
  run cmd_run --check
  [ "${status}" -eq 0 ]
  read -r py_line < "${TEST_TMP_DIR}/call.txt"
  [ "${py_line}" == "PY=${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib" ]
  grep -q '^ARGS=-m tui.cli --check$' "${TEST_TMP_DIR}/call.txt"
}

@test "studio-tui forwards every flag verbatim" {
  install_mock_bin python3 'printf "%s\n" "ARGS=$*" > "${TEST_TMP_DIR}/call.txt"; exit 0'
  run cmd_run --dry-run --read-only --group film --timeout 30
  [ "${status}" -eq 0 ]
  grep -q '^ARGS=-m tui.cli --dry-run --read-only --group film --timeout 30$' \
    "${TEST_TMP_DIR}/call.txt"
}

@test "studio-tui keeps an inherited PYTHONPATH" {
  install_mock_bin python3 'printf "%s\n" "PY=${PYTHONPATH}" > "${TEST_TMP_DIR}/call.txt"; exit 0'
  PYTHONPATH="/opt/extra" run cmd_run --check
  [ "${status}" -eq 0 ]
  read -r py_line < "${TEST_TMP_DIR}/call.txt"
  [ "${py_line}" == "PY=${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib:/opt/extra" ]
}

@test "studio-tui honours BUILD_WORKSPACE_DIRECTORY under bazel run" {
  install_mock_bin python3 'printf "%s\n" "PWD=${PWD}" "PY=${PYTHONPATH}" > "${TEST_TMP_DIR}/call.txt"; exit 0'
  local fake_ws="${TEST_TMP_DIR}/fake-ws"
  mkdir -p "${fake_ws}"
  BUILD_WORKSPACE_DIRECTORY="${fake_ws}" run cmd_run --check
  [ "${status}" -eq 0 ]
  grep -q "^PWD=${fake_ws}$" "${TEST_TMP_DIR}/call.txt"
  grep -q "^PY=${fake_ws}/custom_nodes:${fake_ws}/scripts/lib$" "${TEST_TMP_DIR}/call.txt"
}

@test "studio-tui propagates the child exit status" {
  install_mock_bin python3 'exit 3'
  run cmd_run --check
  [ "${status}" -eq 3 ]
}
