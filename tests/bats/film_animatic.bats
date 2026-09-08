#!/usr/bin/env bats
#
# Cover scripts/utilities/film-animatic.sh

load 'test_helper'

setup() {
  setup_repo_env
  export FA="${UTILITIES_DIR}/film-animatic.sh"
  chmod +x "${FA}"
  # shellcheck disable=SC1090
  source "${FA}"
}

teardown() {
  teardown_repo_env
}

@test "film-animatic help and unknown film" {
  run bash "${FA}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"animatic"* ]]
  run animatic_film_slug still-here
  [ "${output}" = "stillhere" ]
  run animatic_film_slug nope
  [ "${status}" -ne 0 ]
  FILM=""
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "film-animatic does not start docker" {
  ! grep -q 'compose up' "${FA}"
  ! grep -q 'docker compose' "${FA}"
}
