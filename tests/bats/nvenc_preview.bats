#!/usr/bin/env bats
#
# Cover scripts/utilities/nvenc-preview.sh. Hermetic ffmpeg + compose mocks.

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export NV="${UTILITIES_DIR}/nvenc-preview.sh"
  chmod +x "${NV}"
  # shellcheck disable=SC1090
  source "${NV}"
}

teardown() {
  teardown_repo_env
}

@test "nvenc-preview parse_args help unknown dry-run" {
  parse_args --in /tmp/a.mp4 --out /tmp/b.mp4 --dry-run
  [ "${DRY_RUN}" -eq 1 ]
  [ "${IN_MP4}" = "/tmp/a.mp4" ]
  parse_args --yes --in /tmp/a.mp4 --out /tmp/b.mp4
  [ "${DRY_RUN}" -eq 0 ]
  run bash "${NV}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--in"* ]]
  run bash "${NV}" --nope
  [ "${status}" -ne 0 ]
}

@test "nvenc-preview refuses when compose is running" {
  touch "${TEST_TMP_DIR}/compose_running"
  IN_MP4="${TEST_TMP_DIR}/in.mp4"
  OUT_MP4="${TEST_TMP_DIR}/out.mp4"
  : >"${IN_MP4}"
  DRY_RUN=1
  run refuse_if_comfy_running
  [ "${status}" -eq 2 ]
  run cmd_run
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"running"* ]]
}

@test "nvenc-preview dry-run and yes with mock ffmpeg" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  IN_MP4="${TEST_TMP_DIR}/in.mp4"
  OUT_MP4="${TEST_TMP_DIR}/out.mp4"
  : >"${IN_MP4}"
  DRY_RUN=1
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  [[ "${output}" == *"h264_nvenc"* ]]
  DRY_RUN=0
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q -- 'h264_nvenc' "${TEST_TMP_DIR}/ffmpeg.log"
  IN_MP4=""
  run cmd_run
  [ "${status}" -ne 0 ]
}
