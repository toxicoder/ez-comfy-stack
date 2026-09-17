#!/usr/bin/env bats
#
# Cover scripts/utilities/compress-cinema-clip.sh. Hermetic ffmpeg mock.

load 'test_helper'

setup() {
  setup_repo_env
  export CC="${UTILITIES_DIR}/compress-cinema-clip.sh"
  chmod +x "${CC}"
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  # shellcheck disable=SC1090
  source "${CC}"
}

teardown() {
  teardown_repo_env
}

@test "compress-cinema-clip parse_args help unknown dry-run" {
  parse_args --in a.mp4 --out b.mp4 --poster c.jpg --crf 30 --max-bytes 100 --dry-run
  [ "${IN_MP4}" = "a.mp4" ]
  [ "${OUT_MP4}" = "b.mp4" ]
  [ "${POSTER}" = "c.jpg" ]
  [ "${CRF}" = "30" ]
  [ "${MAX_BYTES}" = "100" ]
  [ "${DRY_RUN}" -eq 1 ]
  run bash "${CC}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"854"* ]]
  [[ "${output}" == *"CRF"* ]]
  [[ "${output}" == *"faststart"* ]]
  run bash "${CC}" --nope
  [ "${status}" -ne 0 ]
}

@test "compress-cinema-clip video_filter compress_argv poster_argv" {
  parse_args --in in.mp4 --out out.mp4 --poster poster.jpg
  run video_filter
  [[ "${output}" == *"854:480"* ]]
  [[ "${output}" == *"fps=24"* ]]
  run compress_argv 28
  [[ "${output}" == *"libx264"* ]]
  [[ "${output}" == *"-an"* ]]
  [[ "${output}" == *"crf"* ]]
  [[ "${output}" == *"faststart"* ]]
  [[ "${output}" == *"yuv420p"* ]]
  run poster_argv
  [[ "${output}" == *"poster.jpg"* ]]
  [[ "${output}" == *"-frames:v"* ]]
}

@test "compress-cinema-clip file_size_bytes over_max_bytes require_ffmpeg" {
  local blob="${TEST_TMP_DIR}/blob.bin"
  printf 'abcd' >"${blob}"
  run file_size_bytes "${blob}"
  [ "${output}" = "4" ]
  MAX_BYTES=3
  run over_max_bytes "${blob}"
  [ "${status}" -eq 0 ]
  MAX_BYTES=10
  run over_max_bytes "${blob}"
  [ "${status}" -ne 0 ]
  run require_ffmpeg
  [ "${status}" -eq 0 ]
}

@test "compress-cinema-clip cmd_run dry-run and missing args" {
  IN_MP4=""
  OUT_MP4=""
  run cmd_run
  [ "${status}" -ne 0 ]
  parse_args --in "${TEST_TMP_DIR}/missing.mp4" --out "${TEST_TMP_DIR}/out.mp4" --dry-run
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"libx264"* ]]
  : >"${TEST_TMP_DIR}/in.mp4"
  parse_args --in "${TEST_TMP_DIR}/in.mp4" --out "${TEST_TMP_DIR}/out.mp4" --poster "${TEST_TMP_DIR}/p.jpg"
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'libx264' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q 'faststart' "${TEST_TMP_DIR}/ffmpeg.log"
  [ -f "${TEST_TMP_DIR}/out.mp4" ]
  [ -f "${TEST_TMP_DIR}/p.jpg" ]
}

@test "compress-cinema-clip does not start docker" {
  run bash -n "${CC}"
  [ "${status}" -eq 0 ]
  ! grep -q 'compose up' "${CC}"
}

@test "compress-cinema-clip still_motion_filter still_argv compress_still_once" {
  parse_args --still in.jpg --move zoom_in --out out.mp4 --poster p.jpg --dry-run
  [ "${STILL}" = "in.jpg" ]
  [ "${MOVE}" = "zoom_in" ]
  run still_motion_filter hold
  [[ "${output}" == *"zoompan"* ]]
  run still_motion_filter zoom_in
  [[ "${output}" == *"min(1.0+0.0035"* ]]
  run still_motion_filter zoom_out
  [[ "${output}" == *"1.42"* ]]
  run still_motion_filter pan_left
  [[ "${output}" == *"1-on/119"* ]]
  run still_motion_filter pan_right
  [[ "${output}" == *"on/119"* ]]
  run still_motion_filter tilt_up
  [[ "${output}" == *"ih-ih/zoom"* ]]
  run still_motion_filter tilt_down
  [[ "${output}" == *"ih-ih/zoom"* ]]
  run still_motion_filter rise
  [[ "${output}" == *"zoompan"* ]]
  run still_motion_filter drop
  [[ "${output}" == *"zoompan"* ]]
  run still_motion_filter orbit
  [[ "${output}" == *"sin"* ]]
  run still_motion_filter jitter
  [[ "${output}" == *"sin"* ]]
  run still_motion_filter whip_left
  [[ "${output}" == *"lt(on,14)"* ]]
  run still_motion_filter whip_right
  [[ "${output}" == *"lt(on,14)"* ]]
  run still_motion_filter nope
  [ "${status}" -ne 0 ]
  run still_argv 28
  [[ "${output}" == *"-loop 1"* ]]
  [[ "${output}" == *"libx264"* ]]
  : >"${TEST_TMP_DIR}/still.jpg"
  STILL="${TEST_TMP_DIR}/still.jpg"
  OUT_MP4="${TEST_TMP_DIR}/fromstill.mp4"
  POSTER="${TEST_TMP_DIR}/fromstill.jpg"
  MOVE="hold"
  run compress_still_once 28
  [ "${status}" -eq 0 ]
  run bash "${CC}" --still "${TEST_TMP_DIR}/still.jpg" --move pan_left --out "${TEST_TMP_DIR}/pan.mp4" --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"zoompan"* ]]
}

@test "compress-cinema-clip compress_once extract_poster cmd_help main" {
  run cmd_help
  [ "${status}" -eq 0 ]
  : >"${TEST_TMP_DIR}/in.mp4"
  IN_MP4="${TEST_TMP_DIR}/in.mp4"
  OUT_MP4="${TEST_TMP_DIR}/out.mp4"
  POSTER="${TEST_TMP_DIR}/p.jpg"
  run compress_once 28
  [ "${status}" -eq 0 ]
  run extract_poster
  [ "${status}" -eq 0 ]
  run main --in "${TEST_TMP_DIR}/in.mp4" --out "${TEST_TMP_DIR}/wired.mp4" --dry-run
  [ "${status}" -eq 0 ]
}
