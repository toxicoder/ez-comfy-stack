#!/usr/bin/env bats
#
# Cover scripts/utilities/asset-ls.sh (read-only Asset Bible catalog).

load 'test_helper'

setup() {
  setup_repo_env
  export ALS="${UTILITIES_DIR}/asset-ls.sh"
  chmod +x "${ALS}"
  # shellcheck disable=SC1090
  source "${ALS}"
}

teardown() {
  teardown_repo_env
}

@test "asset-ls help via cmd_help parse_args cmd_run" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage: asset-ls.sh"* ]]
  [[ "${output}" == *"--json"* ]]
  [[ "${output}" == *"asset-new"* ]]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Read-only Asset Bible"* ]]
  run bash "${ALS}" --help
  [ "${status}" -eq 0 ]
  parse_args --json
  [ "${JSON_FLAG}" -eq 1 ]
}

@test "asset-ls empty catalog is success" {
  local empty
  empty="${TEST_TMP_DIR}/empty-assets"
  mkdir -p "${empty}"
  run cmd_run --output-dir "${empty}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"0 assets"* ]]
  [[ "${output}" == *"Catalog is empty"* ]]
  run cmd_run --json --output-dir "${empty}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"[]"* ]]
  run bash "${ALS}" --output-dir "${empty}" --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"[]"* ]]
}

@test "asset-ls fixture catalog via --output-dir" {
  local catalog
  catalog="${REPO_ROOT}/tests/fixtures/assets"
  run cmd_run --output-dir "${catalog}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"mug-cobalt-chipped"* ]]
  [[ "${output}" == *"klein-trellis2"* ]]
  run cmd_run --json --output-dir "${catalog}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"mug-cobalt-chipped"* ]]
  [[ "${output}" == *"object"* ]]
  local copied
  copied="${TEST_TMP_DIR}/copied-assets"
  mkdir -p "${copied}/objects/mug-cobalt-chipped"
  cp -R "${catalog}/objects/mug-cobalt-chipped/." "${copied}/objects/mug-cobalt-chipped/"
  run bash "${ALS}" --output-dir "${copied}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"mug-cobalt-chipped"* ]]
}

@test "asset-ls unknown flag fails" {
  run cmd_run --nope
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Unknown flag"* ]]
  run bash "${ALS}" --bogus
  [ "${status}" -ne 0 ]
  run parse_args --output-dir
  [ "${status}" -ne 0 ]
}
