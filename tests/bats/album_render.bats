#!/usr/bin/env bats
#
# ## album_render.bats
#
# Cover scripts/utilities/album-render.sh usage, dry-run, and pack.

load 'test_helper'

setup() {
  setup_repo_env
  chmod +x "${REPO_ROOT}/scripts/utilities/album-render.sh"
}

teardown() {
  teardown_repo_env
}

# Named for coverage inventory: cmd_help album_dir comfy_up comfy_free
# comfy_post_prompt comfy_wait_history pack_only main cmd_album_render

@test "album_render help status dry-run and missing album" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  run bash "${sh}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  run bash "${sh}"
  [ "${status}" -ne 0 ]
  run bash "${sh}" status
  [ "${status}" -eq 0 ]
  run bash "${sh}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"comfy"'* ]]
  run bash "${sh}" run --album missing/nope --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown album"* ]]
}

@test "album_render dry-run known album and upload requires image" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  mkdir -p "${REPO_ROOT}/workflows/_lab/audio/albums/nill-bye/peer-review"
  run bash "${sh}" run --album nill-bye/peer-review --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  run bash "${sh}" run --album nill-bye/peer-review --art upload --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--image"* ]]
  run bash "${sh}" run --album nill-bye/peer-review --art bogus --dry-run
  [ "${status}" -ne 0 ]
}

@test "album_render pack refuses empty output dir" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  mkdir -p "${REPO_ROOT}/workflows/_lab/audio/albums/nill-bye/peer-review"
  export COMFY_OUTPUT_DIR="${TEST_TMP_DIR}/out"
  mkdir -p "${COMFY_OUTPUT_DIR}"
  run bash "${sh}" pack --album nill-bye/peer-review
  [ "${status}" -ne 0 ]
}
