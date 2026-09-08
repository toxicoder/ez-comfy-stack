#!/usr/bin/env bats
#
# Cover scripts/utilities/stem-mix.sh

load 'test_helper'

setup() {
  setup_repo_env
  export SM="${UTILITIES_DIR}/stem-mix.sh"
  chmod +x "${SM}"
  # shellcheck disable=SC1090
  source "${SM}"
}

teardown() {
  teardown_repo_env
}

@test "stem-mix help unknown film missing args" {
  run bash "${SM}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"loudnorm"* ]]
  [[ "${output}" == *"-15"* ]]
  run mix_film_slug switchyard
  [ "${output}" = "switchyard" ]
  run mix_film_slug nope
  [ "${status}" -ne 0 ]
  FILM=""
  SHOT_ID=""
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "stem-mix does not start docker and mentions occupancy" {
  ! grep -q 'compose up' "${SM}"
  grep -q 'occupancy' "${SM}"
}
