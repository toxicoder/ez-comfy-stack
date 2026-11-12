#!/usr/bin/env bats
#
# Cover scripts/utilities/icon-pack.sh (help, argv forwarding, python3 guard). Hermetic python3 mock.

load 'test_helper'

bats_require_minimum_version 1.5.0

setup() {
  setup_repo_env
  export ICON_PACK="${UTILITIES_DIR}/icon-pack.sh"
  chmod +x "${ICON_PACK}"
  # shellcheck disable=SC2016  # the mock body must not expand at install time
  install_mock_bin python3 '
echo "$*" >>"${TEST_TMP_DIR}/python3.log"
echo "$@"
exit 0
'
  # shellcheck disable=SC1090
  source "${ICON_PACK}"
}

teardown() {
  teardown_repo_env
}

#######################################
# Install a python3 mock that mirrors the ez_icons.pack argparse contract.
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
if [[ ${1:-} != "-m" || ${2:-} != "ez_icons.pack" ]]; then
  echo "mock: unexpected invocation: $*" >&2
  exit 3
fi
shift 2
while [[ $# -gt 0 ]]; do
  case "${1}" in
    --out | --catalog | --art-dir | --pack-name | --pack-version | --scaffold | --name | --package | --glyph)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_icons.pack: error: argument ${1}: expected one argument" >&2
        exit 2
      fi
      shift 2
      ;;
    --icon | --category)
      if [[ $# -lt 2 || ${2} == --* ]]; then
        echo "ez_icons.pack: error: argument ${1}: expected one argument" >&2
        exit 2
      fi
      shift 2
      ;;
    --validate-only | --dry-run)
      shift
      ;;
    *)
      echo "ez_icons.pack: error: unrecognized arguments: ${1}" >&2
      exit 2
      ;;
  esac
done
echo "contract ok"
exit 0
'
}

@test "icon-pack cmd_help prints the verb and its flags" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"icon-pack"* ]]
  [[ "${output}" == *"--out"* ]]
  [[ "${output}" == *"--catalog"* ]]
  [[ "${output}" == *"--validate-only"* ]]
  [[ "${output}" == *"--scaffold"* ]]
  [[ "${output}" == *"--glyph"* ]]
  [[ "${output}" == *"--dry-run"* ]]
}

@test "icon-pack help paths skip python3 entirely" {
  mock_path_hide python3
  for arg in --help -h help; do
    run bash "${ICON_PACK}" "${arg}"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Usage: icon-pack.sh"* ]]
    [[ "${output}" == *"--out"* ]]
  done
  run cmd_run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"store-ready"* ]]
  [ ! -e "${TEST_TMP_DIR}/python3.log" ]
  mock_path_restore
}

@test "icon-pack forwards argv to ez_icons.pack verbatim" {
  run cmd_run --out "${TEST_TMP_DIR}/pack" --icon alpha --icon beta \
    --glyph disc --glyph hex --pack-version 3 --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"-m ez_icons.pack"* ]]
  [[ "${output}" == *"--out ${TEST_TMP_DIR}/pack"* ]]
  [[ "${output}" == *"--icon alpha --icon beta"* ]]
  [[ "${output}" == *"--glyph disc --glyph hex"* ]]
  [[ "${output}" == *"--pack-version 3"* ]]
  [[ "${output}" == *"--dry-run"* ]]
  grep -Fq -- '-m ez_icons.pack' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--dry-run' "${TEST_TMP_DIR}/python3.log"
}

@test "icon-pack forwards the documented flags from a bare invocation" {
  run bash "${ICON_PACK}" --out "${TEST_TMP_DIR}/pack" --catalog "${TEST_TMP_DIR}/o.json" \
    --art-dir "${TEST_TMP_DIR}/art" --pack-name "My Pack" --validate-only --dry-run
  [ "${status}" -eq 0 ]
  grep -Fq -- '-m ez_icons.pack' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--catalog' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--art-dir' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--pack-name My Pack' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--validate-only' "${TEST_TMP_DIR}/python3.log"
  grep -Fq -- '--dry-run' "${TEST_TMP_DIR}/python3.log"
}

@test "icon-pack propagates the module usage error instead of swallowing it" {
  install_argparse_contract_mock
  run cmd_run --out "${TEST_TMP_DIR}/pack" --nope
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unrecognized arguments: --nope"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/pack" --pack-version
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--pack-version: expected one argument"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/pack" --icon alpha --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"contract ok"* ]]
}

@test "icon-pack needs python3 to build a pack" {
  mock_path_hide python3
  run -127 cmd_run --out "${TEST_TMP_DIR}/pack" --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"python3"* ]]
  run -127 bash "${ICON_PACK}" --out "${TEST_TMP_DIR}/pack" --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"python3"* ]]
  mock_path_restore
}

@test "icon-pack is parse-clean, docker-free, and carries its CLI banner" {
  run bash -n "${ICON_PACK}"
  [ "${status}" -eq 0 ]
  run ! grep -q 'compose up' "${ICON_PACK}"
  run ! grep -Eq 'docker (start|compose|run)|systemctl|sudo ' "${ICON_PACK}"
  grep -q '^# @command icon-pack$' "${ICON_PACK}"
}
