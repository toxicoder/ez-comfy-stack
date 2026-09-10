#!/usr/bin/env bats
#
# Cover scripts/utilities/audio-still-video.sh (strict inventory). Hermetic ffmpeg mock.

load 'test_helper'

setup() {
  setup_repo_env
  export ASV="${UTILITIES_DIR}/audio-still-video.sh"
  chmod +x "${ASV}"
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  # shellcheck disable=SC1090
  source "${ASV}"
}

teardown() {
  teardown_repo_env
}

@test "audio-still-video parse_args help unknown sizes" {
  parse_args --audio /tmp/a.flac --image /tmp/i.png --size 1280x720 --fit crop --loudnorm youtube --out /tmp/o.mp4 --dry-run
  [ "${CMD}" = "run" ]
  [ "${AUDIO_FILE}" = "/tmp/a.flac" ]
  [ "${IMAGE_FILE}" = "/tmp/i.png" ]
  [ "${SIZE}" = "1280x720" ]
  [ "${SIZE_W}" -eq 1280 ]
  [ "${SIZE_H}" -eq 720 ]
  [ "${FIT}" = "crop" ]
  [ "${LOUDNORM}" = "youtube" ]
  [ "${OUT_FILE}" = "/tmp/o.mp4" ]
  [ "${DRY_RUN}" -eq 1 ]
  parse_args status --json --size 1080x1920
  [ "${CMD}" = "status" ]
  [ "${JSON_FLAG}" = "--json" ]
  [ "${SIZE_W}" -eq 1080 ]
  [ "${SIZE_H}" -eq 1920 ]
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"YouTube"* ]]
  [[ "${output}" == *"--audio"* ]]
  run bash "${ASV}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"letterbox"* ]]
  run bash "${ASV}" --nope
  [ "${status}" -ne 0 ]
  run parse_args --size nope
  [ "${status}" -ne 0 ]
  run parse_args --fit nope
  [ "${status}" -ne 0 ]
  run parse_args --loudnorm nope
  [ "${status}" -ne 0 ]
}

@test "audio-still-video helpers filter argv run mock" {
  parse_size 1920x1080
  [ "${SIZE_W}" -eq 1920 ]
  [ "${SIZE_H}" -eq 1080 ]
  FIT=letterbox
  run scale_filter
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"force_original_aspect_ratio=decrease"* ]]
  [[ "${output}" == *"pad=1920:1080"* ]]
  [[ "${output}" == *"fps=30"* ]]
  [[ "${output}" == *"format=yuv420p"* ]]
  FIT=crop
  run scale_filter
  [[ "${output}" == *"force_original_aspect_ratio=increase"* ]]
  [[ "${output}" == *"crop=1920:1080"* ]]
  FIT=stretch
  run scale_filter
  [ "${output}" = "scale=1920:1080,fps=30,format=yuv420p" ]
  FIT=nope
  run scale_filter
  [ "${status}" -ne 0 ]
  parse_size 1280x720
  [ "${SIZE_W}" -eq 1280 ]
  parse_size 1080x1920
  [ "${SIZE_H}" -eq 1920 ]
  run parse_size 720x480
  [ "${status}" -ne 0 ]
  AUDIO_FILE="${TEST_TMP_DIR}/ez_rap_full_00001_.flac"
  echo x >"${AUDIO_FILE}"
  IMAGE_FILE="${TEST_TMP_DIR}/cover.png"
  echo x >"${IMAGE_FILE}"
  OUT_FILE=""
  run default_out_path
  [ "${output}" = "${TEST_TMP_DIR}/ez_rap_full_00001_.mp4" ]
  SIZE="1920x1080"
  SIZE_W=1920
  SIZE_H=1080
  FIT=letterbox
  LOUDNORM=off
  OUT_FILE="${TEST_TMP_DIR}/out.mp4"
  build_ffmpeg_argv
  joined="${FFMPEG_ARGV[*]}"
  [[ "${joined}" == *"-loop 1"* ]]
  [[ "${joined}" == *"libx264"* ]]
  [[ "${joined}" == *"stillimage"* ]]
  [[ "${joined}" == *"aac"* ]]
  [[ "${joined}" == *"-shortest"* ]]
  [[ "${joined}" == *"+faststart"* ]]
  [[ "${joined}" != *"loudnorm"* ]]
  LOUDNORM=youtube
  build_ffmpeg_argv
  joined="${FFMPEG_ARGV[*]}"
  [[ "${joined}" == *"loudnorm=I=-14"* ]]
  JSON_FLAG="--json"
  SIZE="1920x1080"
  FIT=letterbox
  LOUDNORM=off
  run cmd_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  DRY_RUN=1
  LOUDNORM=off
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  [ ! -s "${TEST_TMP_DIR}/ffmpeg.log" ]
  DRY_RUN=0
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'libx264' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q 'stillimage' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -Fq -- '-shortest' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -Fq '+faststart' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q 'fps=30' "${TEST_TMP_DIR}/ffmpeg.log"
  [[ -f ${OUT_FILE} ]]
  AUDIO_FILE=""
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "audio-still-video fails when ffmpeg missing" {
  local saved_path="${PATH}"
  rm -f "${TEST_TMP_DIR}/bin/ffmpeg"
  PATH="${TEST_TMP_DIR}/bin:/bin:/usr/bin"
  export PATH
  run require_ffmpeg
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  run cmd_status
  [ "${status}" -ne 0 ]
  AUDIO_FILE="${TEST_TMP_DIR}/a.flac"
  IMAGE_FILE="${TEST_TMP_DIR}/i.png"
  echo x >"${AUDIO_FILE}"
  echo x >"${IMAGE_FILE}"
  OUT_FILE="${TEST_TMP_DIR}/missing.mp4"
  DRY_RUN=0
  run cmd_run
  [ "${status}" -ne 0 ]
  PATH="${saved_path}"
  export PATH
}

@test "audio-still-video does not start docker" {
  run bash -n "${ASV}"
  [ "${status}" -eq 0 ]
  ! grep -q 'compose up' "${ASV}"
}
