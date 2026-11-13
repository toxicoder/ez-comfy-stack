#!/usr/bin/env bats
#
# Cover scripts/utilities/watch-face.sh (help, argv forwarding, python3 guard). Hermetic python3 mock.

load 'test_helper'

bats_require_minimum_version 1.5.0

setup() {
  setup_repo_env
  export WATCH_FACE="${UTILITIES_DIR}/watch-face.sh"
  chmod +x "${WATCH_FACE}"
  # shellcheck disable=SC2016  # the mock body must not expand at install time
  install_mock_bin python3 '
echo "$*" >>"${TEST_TMP_DIR}/python3.log"
echo "$@"
exit 0
'
  # shellcheck disable=SC1090
  source "${WATCH_FACE}"
}

teardown() {
  teardown_repo_env
}

#######################################
# Install a python3 mock that mirrors the ez_watch.project argparse contract.
# Used to prove cmd_run forwards argv unfiltered and returns the module status.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   argparse-shaped diagnostics on stderr; exit 2 on a usage error
# Returns:
#   0
#######################################
install_argparse_contract_mock() {
  # shellcheck disable=SC2016  # the mock body must not expand at install time
  install_mock_bin python3 '
if [[ ${1:-} != "-m" || ${2:-} != "ez_watch.project" ]]; then
  echo "mock: unexpected invocation: $*" >&2
  exit 3
fi
shift 2
have_out=0
while [[ $# -gt 0 ]]; do
  case "${1}" in
    --out)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_watch.project: error: argument --out: expected one argument" >&2
        exit 2
      fi
      have_out=1
      shift 2
      ;;
    --face | --catalog)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_watch.project: error: argument ${1}: expected one argument" >&2
        exit 2
      fi
      shift 2
      ;;
    --style)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_watch.project: error: argument --style: expected one argument" >&2
        exit 2
      fi
      case "${2}" in
        analog | digital | hybrid | complication) shift 2 ;;
        *)
          echo "ez_watch.project: error: argument --style: invalid choice: ${2}" >&2
          exit 2
          ;;
      esac
      ;;
    --wff-version | --preview-edge)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_watch.project: error: argument ${1}: expected one argument" >&2
        exit 2
      fi
      if [[ ${2} =~ [^0-9] ]]; then
        echo "ez_watch.project: error: argument ${1}: invalid value: ${2}" >&2
        exit 2
      fi
      shift 2
      ;;
    --size-variants | --validate-only | --dry-run)
      shift
      ;;
    *)
      echo "ez_watch.project: error: unrecognized arguments: ${1}" >&2
      exit 2
      ;;
  esac
done
if [[ ${have_out} -ne 1 ]]; then
  echo "ez_watch.project: error: the following arguments are required: --out" >&2
  exit 2
fi
echo "contract ok"
exit 0
'
}

@test "watch-face cmd_help prints the verb and its flags" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"watch-face"* ]]
  [[ "${output}" == *"--out"* ]]
  [[ "${output}" == *"--face"* ]]
  [[ "${output}" == *"--style"* ]]
  [[ "${output}" == *"--wff-version"* ]]
  [[ "${output}" == *"--validate-only"* ]]
  [[ "${output}" == *"Watch Face Format"* ]]
}

@test "watch-face help paths skip python3 entirely" {
  mock_path_hide python3
  for arg in --help -h help; do
    run bash "${WATCH_FACE}" "${arg}"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Usage: watch-face.sh"* ]]
    [[ "${output}" == *"--dry-run"* ]]
  done
  run cmd_run help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Watch Face Format"* ]]
  [ ! -e "${TEST_TMP_DIR}/python3.log" ]
  mock_path_restore
}

@test "watch-face forwards argv to ez_watch.project verbatim" {
  run cmd_run --out "${TEST_TMP_DIR}/faces" --face aurora --face meridian \
    --style analog --size-variants --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"-m ez_watch.project"* ]]
  [[ "${output}" == *"--out ${TEST_TMP_DIR}/faces"* ]]
  [[ "${output}" == *"--face aurora --face meridian"* ]]
  [[ "${output}" == *"--style analog"* ]]
  [[ "${output}" == *"--size-variants"* ]]
  [[ "${output}" == *"--dry-run"* ]]
  grep -Fq -- '-m ez_watch.project' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--size-variants' "${TEST_TMP_DIR}/python3.log"
}

@test "watch-face forwards the documented flags from a bare invocation" {
  run bash "${WATCH_FACE}" --out "${TEST_TMP_DIR}/faces" --catalog "${TEST_TMP_DIR}/o.json" \
    --wff-version 4 --preview-edge 480 --validate-only --dry-run
  [ "${status}" -eq 0 ]
  grep -Fq -- '-m ez_watch.project' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--catalog' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--wff-version 4' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--preview-edge 480' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--validate-only' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--dry-run' "${TEST_TMP_DIR}/python3.log"
}

@test "watch-face propagates the module usage error instead of swallowing it" {
  install_argparse_contract_mock
  run cmd_run --face aurora
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"required: --out"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/faces" --style nope
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--style: invalid choice: nope"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/faces" --wff-version nine
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--wff-version: invalid value: nine"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/faces" --nope
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unrecognized arguments: --nope"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/faces" --face aurora --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"contract ok"* ]]
}

@test "watch-face needs python3 to emit a face" {
  mock_path_hide python3
  run -127 cmd_run --out "${TEST_TMP_DIR}/faces" --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"python3"* ]]
  run -127 bash "${WATCH_FACE}" --out "${TEST_TMP_DIR}/faces" --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"python3"* ]]
  mock_path_restore
}

@test "watch-face is parse-clean, docker-free, and carries its CLI banner" {
  run bash -n "${WATCH_FACE}"
  [ "${status}" -eq 0 ]
  run ! grep -q 'compose up' "${WATCH_FACE}"
  run ! grep -Eq 'docker (start|compose|run)|systemctl|sudo ' "${WATCH_FACE}"
  grep -q '^# @command watch-face$' "${WATCH_FACE}"
}
