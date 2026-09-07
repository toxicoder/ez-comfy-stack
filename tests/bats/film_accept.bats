#!/usr/bin/env bats
#
# Cover scripts/utilities/film-accept.sh

load 'test_helper'

setup() {
  setup_repo_env
  export FA="${UTILITIES_DIR}/film-accept.sh"
  chmod +x "${FA}"
  # shellcheck disable=SC1090
  source "${FA}"
}

teardown() {
  teardown_repo_env
}

@test "film-accept help unknown film" {
  run bash "${FA}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"1280x704"* ]]
  run accept_film_slug go-see
  [ "${output}" = "gosee" ]
  run accept_film_slug still-here
  [ "${output}" = "stillhere" ]
  run accept_film_slug switchyard
  [ "${output}" = "switchyard" ]
  run accept_film_slug nope
  [ "${status}" -ne 0 ]
  run cmd_run nope
  [ "${status}" -ne 0 ]
}

@test "film-accept fail-closed without jobstore" {
  run cmd_run go-see
  [ "${status}" -ne 0 ]
}
