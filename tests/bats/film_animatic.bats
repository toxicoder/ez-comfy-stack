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

@test "animatic_guides_dir prefers the film id and falls back to the prefix" {
  local root="${TEST_TMP_DIR}/out"
  mkdir -p "${root}/guides/go-see" "${root}/guides/gosee"
  run animatic_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/go-see" ]

  rm -rf "${root}/guides/go-see"
  run animatic_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/gosee" ]

  rm -rf "${root}/guides/gosee"
  run animatic_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/go-see" ]

  mkdir -p "${root}/guides/switchyard"
  run animatic_guides_dir "${root}" switchyard switchyard
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/switchyard" ]
}
