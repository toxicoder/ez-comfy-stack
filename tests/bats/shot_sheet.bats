#!/usr/bin/env bats
#
# Cover scripts/utilities/shot-sheet.sh

load 'test_helper'

setup() {
  setup_repo_env
  export SS="${UTILITIES_DIR}/shot-sheet.sh"
  chmod +x "${SS}"
  # shellcheck disable=SC1090
  source "${SS}"
}

teardown() {
  teardown_repo_env
}

@test "shot-sheet help and unknown film" {
  run bash "${SS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"shots.yaml"* ]]
  run sheet_film_slug go-see
  [ "${output}" = "gosee" ]
  run sheet_film_slug nope
  [ "${status}" -ne 0 ]
  FILM=go-see
  FROM_PATH=""
  run source_yaml
  [[ "${output}" == *"go-see.shots.yaml"* ]]
  LAB_EXAMPLE=0
  OUT_PATH=""
  run dest_yaml
  [[ "${output}" == *"films/gosee/shots.yaml"* ]]
}

@test "shot-sheet status json and run writes dest not lab yaml" {
  FILM=go-see
  run cmd_status
  [ "${status}" -eq 0 ]
  JSON_FLAG="--json"
  FILM=go-see
  run cmd_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"gosee"* ]]
  FILM=go-see
  LAB_EXAMPLE=0
  FROM_PATH=""
  OUT_PATH="${COMFY_OUTPUT_DIR}/films/gosee/shots.yaml"
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ -f ${OUT_PATH} ]]
  grep -q "audio_policy: world-only" "${OUT_PATH}"
  grep -q "clay: skip" "${OUT_PATH}"
  ! grep -q "audio_policy: world-only" "${REPO_ROOT}/workflows/shorts/go-see.shots.yaml"
}

@test "shot-sheet refuses lab overwrite without --lab-example" {
  FILM=go-see
  LAB_EXAMPLE=0
  FROM_PATH=""
  OUT_PATH="${REPO_ROOT}/workflows/shorts/go-see.shots.yaml"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"lab-example"* ]]
}
