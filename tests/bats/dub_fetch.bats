#!/usr/bin/env bats
#
# ## dub_fetch.bats
#
# Cover scripts/utilities/dub-fetch.sh. Hermetic: mock yt-dlp, no network.

load 'test_helper'

setup() {
  setup_repo_env
  export DF="${UTILITIES_DIR}/dub-fetch.sh"
  chmod +x "${DF}"
  # shellcheck disable=SC1090
  source "${DF}"
}

teardown() {
  teardown_repo_env
}

@test "dub-fetch help status mock run and refuse bad url" {
  run bash "${DF}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"url"* ]]
  dub_fetch_parse_args status --url "https://example.invalid/v"
  [ "${CMD}" = "status" ]
  [ "${URL}" = "https://example.invalid/v" ]
  run dub_is_http_url "https://example.invalid/v"
  [ "${status}" -eq 0 ]
  run dub_is_http_url "/tmp/file.wav"
  [ "${status}" -ne 0 ]
  unset LAB_MOCK_YT_DLP
  run dub_require_ytdlp
  [ "${status}" -ne 0 ]
  export LAB_MOCK_YT_DLP=1
  run dub_require_ytdlp
  [ "${status}" -eq 0 ]
  OUT_DIR="${COMFY_OUTPUT_DIR}/input"
  run dub_fetch_cmd_status
  [ "${status}" -eq 0 ]
  URL=""
  run dub_fetch_cmd_run
  [ "${status}" -ne 0 ]
  URL="https://example.invalid/watch?v=abc"
  run dub_fetch_cmd_run
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/input/ez_dub_fetch.wav ]]
  run bash "${DF}" run --nope
  [ "${status}" -ne 0 ]
  run bash "${DF}" status
  [ "${status}" -eq 0 ]
}
