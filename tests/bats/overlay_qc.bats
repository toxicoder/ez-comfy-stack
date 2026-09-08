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

@test "overlay-qc does not start docker" {
  run bash -n "${OQ}"
  [ "${status}" -eq 0 ]
  if grep -q 'docker compose' "${OQ}"; then
    grep -q 'does not start' "${OQ}" || grep -qv 'compose up' "${OQ}"
  fi
  ! grep -q 'compose up' "${OQ}"
}
