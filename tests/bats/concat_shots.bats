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
  FILM=""
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
  parse_args --skip-accept --yes
  [ "${SKIP_ACCEPT}" -eq 1 ]
  run bash "${CS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--film"* ]]
  [[ "${output}" == *"--cap-seconds"* ]]
  [[ "${output}" == *"--xfade"* ]]
  [[ "${output}" == *"film-accept"* ]]
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

@test "concat-shots film_slug and go-see order with 90s cap" {
  run film_slug go-see
  [ "${output}" = "gosee" ]
  run film_slug still-here
  [ "${output}" = "stillhere" ]
  run film_slug switchyard
  [ "${output}" = "switchyard" ]
  run film_slug nope
  [ "${status}" -ne 0 ]
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00001.mp4"
    done
  done
  : >"${COMFY_OUTPUT_DIR}/ez_gosee_b1_s1_wan_video_00001.mp4"
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  run list_film_shot_files
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"/ez_gosee_b1_s1_ltx_video"* ]]
  [[ "${output}" != *"_wan_video"* ]]
  local n
  n="$(printf '%s\n' "${output}" | grep -c 'ez_gosee_b')"
  [ "${n}" -eq 18 ]
  DRY_RUN=1
  OUT_MP4=""
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ez_gosee_90s.mp4"* ]]
  [[ "${output}" == *"cap 90s"* ]]
  DRY_RUN=0
  SKIP_ACCEPT=1
  OUT_MP4="${COMFY_OUTPUT_DIR}/cap.mp4"
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q -- '-t 90' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q -- 'aac' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q -- 'loudnorm' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q -- 'libx264' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q -- 'faststart' "${TEST_TMP_DIR}/ffmpeg.log"
  [[ -f "${COMFY_OUTPUT_DIR}/cap.html" ]]
  run type concat_playable
  [ "${status}" -eq 0 ]
  run write_preview_html "${COMFY_OUTPUT_DIR}/cap.mp4"
  [ "${status}" -eq 0 ]
  [[ -f "${COMFY_OUTPUT_DIR}/cap.html" ]]
  run first_glob "${COMFY_OUTPUT_DIR}/ez_gosee_b1_s1_ltx_video*.mp4"
  [[ "${output}" == *"ltx_video"* ]]
  run probe_mp4_seconds "${COMFY_OUTPUT_DIR}/cap.mp4"
  [ "${status}" -eq 0 ]
  FILM=nope
  run cmd_run
  [ "${status}" -ne 0 ]
  FILM=go-see
  rm -f "${COMFY_OUTPUT_DIR}/ez_gosee_b6_s3_ltx_video_00001.mp4"
  DRY_RUN=1
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"expected 18"* ]]
}

@test "concat-shots prefers latest VHS *-audio.mp4 over silent intermediates" {
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00006.mp4"
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00006-audio.mp4"
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00007.mp4"
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00007-audio.mp4"
    done
  done
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  run list_film_shot_files
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"_ltx_video_00007-audio.mp4"* ]]
  [[ "${output}" != *"_ltx_video_00006"* ]]
  local n
  n="$(printf '%s\n' "${output}" | grep -cF '_00007-audio.mp4' || true)"
  [ "${n}" -eq 18 ]
  n="$(printf '%s\n' "${output}" | grep -cE '_ltx_video_00007\.mp4$' || true)"
  [ "${n}" -eq 0 ]
  run best_shot_mp4 "${COMFY_OUTPUT_DIR}/ez_gosee_b1_s1_ltx_video*.mp4"
  [[ "${output}" == *"_ltx_video_00007-audio.mp4"* ]]
}

@test "concat-shots film falls back to Wan when no LTX mp4 exists" {
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_wan_video_00001.mp4"
    done
  done
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  run list_film_shot_files
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"_wan_video_00001.mp4"* ]]
  [[ "${output}" != *"_ltx_video"* ]]
  local n
  n="$(printf '%s\n' "${output}" | grep -c '_wan_video')"
  [ "${n}" -eq 18 ]
}

@test "concat-shots pads 113-frame LTX stems to 5.00s" {
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00001-audio.mp4"
    done
  done
  run type maybe_pad_ltx_neighbor
  [ "${status}" -eq 0 ]
  run is_ltx_120_floor_s 4.708333
  [ "${status}" -eq 0 ]
  run is_ltx_120_floor_s 5.00
  [ "${status}" -ne 0 ]
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  install_mock_bin ffprobe 'echo 4.708333'
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  DRY_RUN=0
  SKIP_ACCEPT=1
  OUT_MP4="${COMFY_OUTPUT_DIR}/cap.mp4"
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q -- 'tpad=stop_mode=clone:stop=7' "${TEST_TMP_DIR}/ffmpeg.log"
  [[ "${output}" == *"padded"* ]]
}

@test "concat-shots film duration over cap fails" {
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00001.mp4"
    done
  done
  install_mock_bin ffmpeg 'echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg.log"; touch "${@: -1}"; exit 0'
  install_mock_bin ffprobe 'echo 91'
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  DRY_RUN=0
  SKIP_ACCEPT=1
  OUT_MP4="${COMFY_OUTPUT_DIR}/over.mp4"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"exceeds cap"* ]]
}

@test "concat-shots film --yes fail-closed without accept" {
  local b s
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      : >"${COMFY_OUTPUT_DIR}/ez_gosee_b${b}_s${s}_ltx_video_00001.mp4"
    done
  done
  FILM=go-see
  FILE_CSV=""
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  DRY_RUN=0
  SKIP_ACCEPT=0
  OUT_MP4="${COMFY_OUTPUT_DIR}/nope.mp4"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"film-accept"* ]]
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

@test "concat-shots --xfade parse and missing-audio guard" {
  parse_args --xfade 10 --yes
  [ "${XFADE_CS}" -eq 10 ]
  [ "${DRY_RUN}" -eq 0 ]
  : >"${COMFY_OUTPUT_DIR}/a.mp4"
  : >"${COMFY_OUTPUT_DIR}/b.mp4"
  FILE_CSV="${COMFY_OUTPUT_DIR}/a.mp4,${COMFY_OUTPUT_DIR}/b.mp4"
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  FILM=""
  DRY_RUN=1
  XFADE_CS=10
  OUT_MP4="${COMFY_OUTPUT_DIR}/xfade.mp4"
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"xfade_cs=10"* ]]
  DRY_RUN=0
  install_mock_bin ffprobe 'exit 0'
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"requires audio"* || "${output}" == *"xfade"* ]]
  XFADE_CS=99
  DRY_RUN=0
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"0–50"* || "${output}" == *"0-50"* ]]
}

@test "concat-shots xfade three-step ffmpeg when audio present" {
  : >"${COMFY_OUTPUT_DIR}/a.mp4"
  : >"${COMFY_OUTPUT_DIR}/b.mp4"
  FILE_CSV="${COMFY_OUTPUT_DIR}/a.mp4,${COMFY_OUTPUT_DIR}/b.mp4"
  SHOT_DIR="${COMFY_OUTPUT_DIR}"
  FILM=""
  DRY_RUN=0
  XFADE_CS=10
  OUT_MP4="${COMFY_OUTPUT_DIR}/xfade.mp4"
  install_mock_bin ffprobe 'echo audio'
  : >"${TEST_TMP_DIR}/ffmpeg.log"
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q -- '-an' "${TEST_TMP_DIR}/ffmpeg.log"
  grep -q -- 'acrossfade' "${TEST_TMP_DIR}/ffmpeg.log"
  run shot_has_audio "${COMFY_OUTPUT_DIR}/a.mp4"
  [ "${status}" -eq 0 ]
  run concat_xfade_audio "${COMFY_OUTPUT_DIR}/xfade2.mp4" \
    "${COMFY_OUTPUT_DIR}/a.mp4" "${COMFY_OUTPUT_DIR}/b.mp4"
  [ "${status}" -eq 0 ]
}

@test "audio_acrossfade_filter two and many inputs" {
  run audio_acrossfade_filter 1 0.10
  [ "${status}" -ne 0 ]
  run audio_acrossfade_filter 2 0.10
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"acrossfade=d=0.10"* ]]
  run audio_acrossfade_filter 18 0.10
  [ "${status}" -eq 0 ]
  local n
  n="$(printf '%s' "${output}" | grep -o 'acrossfade=' | wc -l | tr -d ' ')"
  [ "${n}" -eq 17 ]
}
