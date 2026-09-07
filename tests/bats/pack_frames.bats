#!/usr/bin/env bats
#
# Cover scripts/utilities/pack-frames.sh (software libx264 mux, not NVENC).

load 'test_helper'

setup() {
  setup_repo_env
  export PF="${UTILITIES_DIR}/pack-frames.sh"
  chmod +x "${PF}"
  # shellcheck disable=SC1090
  source "${PF}"
}

teardown() {
  teardown_repo_env
}

@test "pack-frames help unknown and missing args" {
  run bash "${PF}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"libx264"* ]]
  [[ "${output}" == *"NVENC"* ]]
  run bash "${PF}" --nope
  [ "${status}" -ne 0 ]
  run cmd_run
  [ "${status}" -eq 1 ]
}

@test "pack-frames parse_args ffmpeg_mux_argv and mock mux" {
  parse_args --in /tmp/rgb --out /tmp/clay.mp4 --fps 24 --pattern '%04d.png'
  [ "${IN_DIR}" = "/tmp/rgb" ]
  [ "${OUT_MP4}" = "/tmp/clay.mp4" ]
  [ "${FPS}" = "24" ]
  run ffmpeg_mux_argv
  [[ "${output}" == *"libx264"* ]]
  [[ "${output}" == *"1280x704"* ]]
  [[ "${output}" != *"h264_nvenc"* ]]
  IN_DIR="${TEST_TMP_DIR}/rgb"
  OUT_MP4="${TEST_TMP_DIR}/clay.mp4"
  mkdir -p "${IN_DIR}"
  : >"${IN_DIR}/0001.png"
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q libx264 "${TEST_TMP_DIR}/ffmpeg.log"
  grep -qv h264_nvenc "${TEST_TMP_DIR}/ffmpeg.log"
}
