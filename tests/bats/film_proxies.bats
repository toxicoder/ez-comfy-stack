#!/usr/bin/env bats
#
# Cover film-proxies.sh (refuse if compose running; dry-run default).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export FP="${UTILITIES_DIR}/film-proxies.sh"
  chmod +x "${FP}"
  # shellcheck disable=SC1090
  source "${FP}"
}

teardown() {
  teardown_repo_env
}

@test "film-proxies parse_args help unknown" {
  run bash "${FP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"960"* ]]
  run bash "${FP}" --nope
  [ "${status}" -ne 0 ]
}

@test "film-proxies refuses when compose is running" {
  touch "${TEST_TMP_DIR}/compose_running"
  parse_args go-see
  run cmd_run
  [ "${status}" -eq 2 ]
}

@test "film-proxies dry-run lists scale 960x528 and does not rewrite masters" {
  local dest shot
  dest="${COMFY_OUTPUT_DIR}/films/gosee"
  mkdir -p "${dest}/shots"
  shot="${dest}/shots/01.mp4"
  echo master >"${shot}"
  parse_args go-see --dry-run
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"960:528"* ]]
  [[ "${output}" == *"h264_nvenc"* ]]
  [[ $(cat "${shot}") == "master" ]]
  [[ ! -f ${dest}/proxies/01.mp4 ]]
}
