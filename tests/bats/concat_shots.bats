#!/usr/bin/env bats
#
# Cover scripts/utilities/concat-shots.sh (strict inventory). Hermetic ffmpeg mock.

load 'test_helper'

setup() {
  setup_repo_env
  export CS="${UTILITIES_DIR}/concat-shots.sh"
  chmod +x "${CS}"
  export COMFY_OUTPUT_DIR="${TEST_TMP_DIR}/out"
  mkdir -p "${COMFY_OUTPUT_DIR}"
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; exit 0'
  # shellcheck disable=SC1090
  source "${CS}"
}

teardown() {
  teardown_repo_env
}

@test "concat-shots parse_args help unknown dry-run" {
  parse_args --dir "${COMFY_OUTPUT_DIR}" --dry-run
  [ "${DRY_RUN}" -eq 1 ]
  parse_args --yes --out /tmp/x.mp4
  [ "${DRY_RUN}" -eq 0 ]
  [ "${OUT_MP4}" = "/tmp/x.mp4" ]
  run bash "${CS}" --help
  [ "${status}" -eq 0 ]
  run bash "${CS}" --nope
  [ "${status}" -ne 0 ]
  : >"${COMFY_OUTPUT_DIR}/ez_shot_01_video.mp4"
  run bash "${CS}" --dir "${COMFY_OUTPUT_DIR}" --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
}

@test "concat-shots list glob and --files" {
  : >"${COMFY_OUTPUT_DIR}/ez_shot_01_video_00001.mp4"
  : >"${COMFY_OUTPUT_DIR}/ez_shot_02_video_00001.mp4"
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  FILE_CSV=""
  run list_shot_files
  [[ "${output}" == *"ez_shot_01"* ]]
  [[ "${output}" == *"ez_shot_02"* ]]
  FILE_CSV="a.mp4, b.mp4"
  run list_shot_files
  [[ "${output}" == *"a.mp4"* ]]
  [[ "${output}" == *"b.mp4"* ]]
}

@test "concat-shots dry-run and --yes ffmpeg" {
  : >"${COMFY_OUTPUT_DIR}/ez_shot_01_video.mp4"
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  FILE_CSV=""
  DRY_RUN=1
  OUT_MP4=""
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  DRY_RUN=0
  OUT_MP4="${COMFY_OUTPUT_DIR}/joined.mp4"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'ffmpeg' "${TEST_TMP_DIR}/ffmpeg.log"
  run write_concat_list "${TEST_TMP_DIR}/list.txt" "${COMFY_OUTPUT_DIR}/ez_shot_01_video.mp4"
  [ "${status}" -eq 0 ]
  grep -q "file '" "${TEST_TMP_DIR}/list.txt"
  FILE_CSV=""
  rm -f "${COMFY_OUTPUT_DIR}"/*.mp4
  DRY_RUN=1
  run cmd_run
  [ "${status}" -ne 0 ]
}
