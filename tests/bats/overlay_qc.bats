#!/usr/bin/env bats
#
# Cover scripts/utilities/overlay-qc.sh. Hermetic ffmpeg mock.

load 'test_helper'

setup() {
  setup_repo_env
  export OQ="${UTILITIES_DIR}/overlay-qc.sh"
  chmod +x "${OQ}"
  # shellcheck disable=SC1090
  source "${OQ}"
}

teardown() {
  teardown_repo_env
}

@test "overlay-qc help unknown film and missing args" {
  run bash "${OQ}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"1280x704"* ]]
  run overlay_film_slug go-see
  [ "${output}" = "gosee" ]
  run overlay_film_slug nope
  [ "${status}" -ne 0 ]
  FILM=""
  SHOT_ID=""
  LOOK=""
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "overlay_guides_dir prefers the film id and falls back to the prefix" {
  local root="${TEST_TMP_DIR}/out"
  mkdir -p "${root}/guides/go-see" "${root}/guides/gosee"
  run overlay_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/go-see" ]

  rm -rf "${root}/guides/go-see"
  run overlay_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/gosee" ]

  rm -rf "${root}/guides/gosee"
  run overlay_guides_dir "${root}" go-see gosee
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/go-see" ]

  mkdir -p "${root}/guides/switchyard"
  run overlay_guides_dir "${root}" switchyard switchyard
  [ "${status}" -eq 0 ]
  [ "${output}" = "${root}/guides/switchyard" ]
}

@test "overlay-qc does not start docker" {
  run bash -n "${OQ}"
  [ "${status}" -eq 0 ]
  if grep -q 'docker compose' "${OQ}"; then
    grep -q 'does not start' "${OQ}" || grep -qv 'compose up' "${OQ}"
  fi
  ! grep -q 'compose up' "${OQ}"
}
