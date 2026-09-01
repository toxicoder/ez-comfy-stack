#!/usr/bin/env bats
#
# ## queue-h3-film.bats
#
# Cover scripts/utilities/queue-h3-film.sh (strict inventory). Hermetic HTTP/ffmpeg mocks.
#

load 'test_helper'

setup() {
  setup_repo_env
  export QH="${UTILITIES_DIR}/queue-h3-film.sh"
  chmod +x "${QH}"
  install_mock_bin curl '
echo "curl $*" >>"${TEST_TMP_DIR}/curl_calls.log"
if [[ "$*" == *"/prompt"* ]]; then
  echo "{\"prompt_id\":\"abc123\"}"
  exit 0
fi
echo "{\"abc123\":{\"status\":\"success\"}}"
exit 0
'
  install_mock_bin ffmpeg '
echo "ffmpeg $*" >>"${TEST_TMP_DIR}/ffmpeg_calls.log"
out=""
prev=""
for a in "$@"; do
  if [[ ${prev} == "-t" ]]; then
    echo "${a}" >>"${TEST_TMP_DIR}/ffmpeg_t.log"
  fi
  prev="${a}"
  out="${a}"
done
mkdir -p "$(dirname "${out}")"
echo mock >"${out}"
exit 0
'
  install_mock_bin ffprobe '
if [[ -f ${TEST_TMP_DIR}/ffprobe_dur ]]; then
  cat "${TEST_TMP_DIR}/ffprobe_dur"
else
  echo 90.0
fi
exit 0
'
  # shellcheck disable=SC1090
  source "${QH}"
}

teardown() {
  teardown_repo_env
}

@test "queue-h3-film film_workflow_path parse_args help unknown" {
  run film_workflow_path go-see
  [[ "${output}" == *"h3-go-see-90s-lab-example.json"* ]]
  run film_workflow_path still-here
  [[ "${output}" == *"still-here"* ]]
  run film_workflow_path switchyard
  [[ "${output}" == *"switchyard"* ]]
  run film_workflow_path nope
  [ "${status}" -ne 0 ]
  parse_args --film go-see --url http://spark-0:8188 --seed 509201 --size 864x480 --relay
  [ "${FILM}" = "go-see" ]
  [ "${SEED}" = "509201" ]
  [ "${SIZE}" = "864x480" ]
  [ "${RELAY}" = "1" ]
  parse_args stitch --dir /tmp --out /tmp/x.mp4
  [ "${CMD}" = "stitch" ]
  run bash "${QH}" --help
  [ "${status}" -eq 0 ]
  run bash "${QH}" --soundtrack
  [ "${status}" -ne 0 ]
  run bash "${QH}" --nope
  [ "${status}" -ne 0 ]
}

@test "queue-h3-film ui_graph_to_prompt apply overrides post poll relay" {
  local wf
  wf="$(film_workflow_path go-see)"
  run ui_graph_to_prompt "${wf}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"MiniMaxH3ImageToVideo"* ]]
  [[ "${output}" == *"\"prompt\""* ]]
  SEED=42
  SIZE=864x480
  local body
  body="$(ui_graph_to_prompt "${wf}" | apply_prompt_overrides)"
  [[ "${body}" == *"864"* ]]
  [[ "${body}" == *"480"* ]]
  echo "${body}" >"${TEST_TMP_DIR}/body.json"
  run post_prompt "${TEST_TMP_DIR}/body.json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == "abc123" ]]
  run poll_history abc123
  [ "${status}" -eq 0 ]
  RELAY=1
  FARM_SHARE="${TEST_TMP_DIR}/farm"
  run write_relay_stubs
  [ "${status}" -eq 0 ]
  [[ -f ${FARM_SHARE}/relay/shot-1/last_frame.png ]]
  [[ -f ${FARM_SHARE}/relay/shot-6/bed.wav ]]
  FILM=go-see
  COMFY_URL="http://127.0.0.1:8188"
  RELAY=0
  run cmd_queue
  [ "${status}" -eq 0 ]
}

@test "queue-h3-film stitch caps 90s and refuses soundtrack" {
  local d="${TEST_TMP_DIR}/shots"
  mkdir -p "${d}"
  echo x >"${d}/01.mp4"
  echo x >"${d}/02.mp4"
  SHOT_DIR="${d}"
  OUT_MP4="${d}/out.mp4"
  echo 90.0 >"${TEST_TMP_DIR}/ffprobe_dur"
  run cmd_stitch
  [ "${status}" -eq 0 ]
  [[ -f ${d}/out.mp4 ]]
  grep -q '90' "${TEST_TMP_DIR}/ffmpeg_t.log"
  echo 90.5 >"${TEST_TMP_DIR}/ffprobe_dur"
  run cmd_stitch
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"90.00"* || "${output}" == *"exceeds"* ]]
  run probe_duration "${d}/out.mp4"
  [ "${status}" -eq 0 ]
  run cmd_stitch --soundtrack
  [ "${status}" -ne 0 ]
}

@test "queue-h3-film CLI queue and stitch" {
  local d="${TEST_TMP_DIR}/shots"
  mkdir -p "${d}"
  echo x >"${d}/a.mp4"
  echo 89.9 >"${TEST_TMP_DIR}/ffprobe_dur"
  run bash "${QH}" stitch --dir "${d}" --out "${d}/film.mp4"
  [ "${status}" -eq 0 ]
  run bash "${QH}" --film go-see --url http://127.0.0.1:8188
  [ "${status}" -eq 0 ]
}
