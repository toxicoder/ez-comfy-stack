#!/usr/bin/env bats
#
# Cover scripts/utilities/podcast-loudnorm.sh (strict inventory). Hermetic ffmpeg mock.

load 'test_helper'

setup() {
  setup_repo_env
  export PL="${UTILITIES_DIR}/podcast-loudnorm.sh"
  chmod +x "${PL}"
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  # shellcheck disable=SC1090
  source "${PL}"
}

teardown() {
  teardown_repo_env
}

@test "podcast-loudnorm parse_args help unknown targets" {
  parse_args status --json --target podcast
  [ "${CMD}" = "status" ]
  [ "${TARGET}" = "podcast" ]
  parse_args run --in /tmp/a.flac --out /tmp/b.flac --youtube
  [ "${TARGET}" = "youtube" ]
  run bash "${PL}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LUFS"* ]]
  run bash "${PL}" --nope
  [ "${status}" -ne 0 ]
  run bash "${PL}" run --target nope
  [ "${status}" -ne 0 ]
}

@test "podcast-loudnorm helpers filter status run mock" {
  TARGET=podcast
  run loudness_i
  [ "${output}" = "-16" ]
  run loudnorm_filter
  [[ "${output}" == *"I=-16"* ]]
  TARGET=youtube
  run loudness_i
  [ "${output}" = "-14" ]
  run require_ffmpeg
  [ "${status}" -eq 0 ]
  JSON_FLAG="--json"
  TARGET=podcast
  run cmd_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"lufs"* ]]
  IN_FILE="${TEST_TMP_DIR}/ep.flac"
  echo x >"${IN_FILE}"
  run default_out_path
  [[ "${output}" == *"-podcast-lufs.flac"* ]]
  OUT_FILE="${TEST_TMP_DIR}/out.flac"
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'loudnorm=I=-16' "${TEST_TMP_DIR}/ffmpeg.log"
  [[ -f ${OUT_FILE} ]]
  IN_FILE=""
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "podcast-loudnorm fails when ffmpeg missing" {
  local saved_path="${PATH}"
  rm -f "${TEST_TMP_DIR}/bin/ffmpeg"
  PATH="${TEST_TMP_DIR}/bin:/bin:/usr/bin"
  export PATH
  run require_ffmpeg
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  run cmd_status
  [ "${status}" -ne 0 ]
  PATH="${saved_path}"
  export PATH
}
