#!/usr/bin/env bats
#
# Cover compile-film.sh + print-shot.sh with a fake Comfy HTTP API.

load 'test_helper'

setup() {
  setup_repo_env
  export CF="${UTILITIES_DIR}/compile-film.sh"
  export PS="${UTILITIES_DIR}/print-shot.sh"
  chmod +x "${CF}" "${PS}"
  export COMFY_URL="http://127.0.0.1:8188"
  export LAB_PRINT_SHOT_POLL=0
  install_mock_bin curl '
echo "curl $*" >>"${TEST_TMP_DIR}/curl_calls.log"
if [[ "$*" == *"/prompt"* && "$*" != *"/history"* ]]; then
  echo "{\"prompt_id\":\"shot12\"}"
  exit 0
fi
echo "{\"shot12\":{\"status\":\"success\"}}"
exit 0
'
  install_mock_bin ffprobe 'echo 5.00'
  # shellcheck disable=SC1090
  source "${CF}"
  # shellcheck disable=SC1090
  source "${PS}"
}

teardown() {
  if declare -F cleanup_temp_files >/dev/null; then
    cleanup_temp_files
  fi
  teardown_repo_env
}

#######################################
# Curl mock that keeps the /prompt request body for inspection.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   curl_calls.log + posted_body.json under TEST_TMP_DIR
# Returns:
#   0
#######################################
install_prompt_capture_mock() {
  install_mock_bin curl '
echo "curl $*" >>"${TEST_TMP_DIR}/curl_calls.log"
if [[ "$*" == *"/prompt"* && "$*" != *"/history"* ]]; then
  for arg in "$@"; do
    if [[ ${arg} == @* ]]; then
      cp "${arg#@}" "${TEST_TMP_DIR}/posted_body.json"
    fi
  done
  echo "{\"prompt_id\":\"shot12\"}"
  exit 0
fi
echo "{\"shot12\":{\"status\":\"success\"}}"
exit 0
'
}

#######################################
# Replace a compiled shot stub with an ltx graph + KSampler + EZQuality.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  shot id
#   $2  tier to record on the EZQuality widget ('' = no widget value)
# Outputs:
#   shots/<id>.json
# Returns:
#   0
#######################################
write_shot_graph() {
  local sid="${1}" tier="${2}"
  python3 - "${COMFY_OUTPUT_DIR}/films/gosee/shots/${sid}.json" "${tier}" <<'PY'
import json
import sys

path, tier = sys.argv[1], sys.argv[2]
widgets = [tier] if tier else []
graph = {
    "nodes": [
        {"id": 1, "type": "EZQuality", "widgets_values": widgets},
        {"id": 2, "type": "KSampler", "widgets_values": [7, "fixed", 20, 1.0]},
    ],
    "extra": {"lab_app_mode": {"occupancy": "ltx"}},
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(graph, handle)
PY
}

@test "compile-film go-see writes 18 pending ids" {
  run compile_film_slug go-see
  [ "${output}" = "gosee" ]
  run compile_film_slug nope
  [ "${status}" -ne 0 ]
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/films/gosee/state.json ]]
  [[ -f ${COMFY_OUTPUT_DIR}/films/gosee/shots/12.json ]]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["shots"])==18; assert d["shots"][0]["id"]=="01"; assert d["shots"][-1]["id"]=="18"' \
    "${COMFY_OUTPUT_DIR}/films/gosee/state.json"
  run bash "${CF}" --help
  [ "${status}" -eq 0 ]
  run bash "${CF}"
  [ "${status}" -ne 0 ]
}

@test "print-shot go-see 12 writes shots/12.mp4 ok" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  run print_one_shot go-see 12
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/films/gosee/shots/12.mp4 ]]
  grep -q '/prompt' "${TEST_TMP_DIR}/curl_calls.log"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); s=d["shots"][11]; assert s["id"]=="12"; assert s["status"]=="ok"' \
    "${COMFY_OUTPUT_DIR}/films/gosee/state.json"
  run print_one_shot go-see 99
  [ "${status}" -ne 0 ]
  run print_one_shot nope 01
  [ "${status}" -ne 0 ]
}

@test "film-resume skips ok duration and reprints crashed running" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  run print_one_shot go-see 12
  [ "${status}" -eq 0 ]
  # 12 is ok + ffprobe 5.00 -> skip
  run print_one_shot go-see 12
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"skip"* ]]
  PYTHONPATH="${REPO_ROOT}/custom_nodes" python3 -m ez_film.jobstore mark \
    --dest "${COMFY_OUTPUT_DIR}/films/gosee" --id 11 --status running
  rm -f "${COMFY_OUTPUT_DIR}/films/gosee/shots/11.mp4"
  FILM=go-see
  RESUME=1
  SHOT_ID=""
  run film_resume_run go-see
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/films/gosee/shots/11.mp4 ]]
}

@test "print-shot help and manage dispatch names" {
  run bash "${PS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"01"* ]]
  run bash "${MANAGE_SH}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"print-shot"* ]]
  [[ "${output}" == *"film-resume"* ]]
  parse_args --resume go-see
  [ "${RESUME}" -eq 1 ]
  [ "${FILM}" = "go-see" ]
  run print_shot_slug go-see
  [ "${output}" = "gosee" ]
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  run jobstore_cli get --dest "${COMFY_OUTPUT_DIR}/films/gosee" --id 01
  [ "${status}" -eq 0 ]
  run comfy_post_prompt "${COMFY_OUTPUT_DIR}/films/gosee/shots/01.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "shot12" ]
  run comfy_wait_history shot12
  [ "${status}" -eq 0 ]
}

@test "print-shot --quality posts the overlaid graph" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  install_prompt_capture_mock
  export COMFY_URL="http://127.0.0.1:1"
  write_shot_graph 12 lab
  run bash "${PS}" go-see 12 --quality draft
  [ "${status}" -eq 0 ]
  grep -q '/prompt' "${TEST_TMP_DIR}/curl_calls.log"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); n=d["nodes"]; assert n[0]["widgets_values"]==["lab"]; assert n[1]["widgets_values"][2]==12, n[1]' \
    "${TEST_TMP_DIR}/posted_body.json"
}

@test "print-shot help documents the quality flag" {
  run bash "${PS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--quality"* ]]
}

@test "print-shot uses the tier the graph records when no flag is given" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  install_prompt_capture_mock
  export COMFY_URL="http://127.0.0.1:1"
  write_shot_graph 12 max
  run bash "${PS}" go-see 12
  [ "${status}" -eq 0 ]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["nodes"][1]["widgets_values"][2]==32, d["nodes"][1]' \
    "${TEST_TMP_DIR}/posted_body.json"
}

@test "print-shot EZ_QUALITY env is the fallback for --quality" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  install_prompt_capture_mock
  export COMFY_URL="http://127.0.0.1:1"
  export EZ_QUALITY="standard"
  write_shot_graph 12 max
  run bash "${PS}" go-see 12
  [ "${status}" -eq 0 ]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["nodes"][1]["widgets_values"][2]==20, d["nodes"][1]' \
    "${TEST_TMP_DIR}/posted_body.json"
}

@test "print-shot quality_apply_graph writes into the scratch dir cleanup removes" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  COMFY_URL="http://127.0.0.1:1"
  QUALITY="draft"
  write_shot_graph 12 lab
  local dir out
  dir="${RUN_TMP_DIR}"
  out="$(quality_apply_graph "${COMFY_OUTPUT_DIR}/films/gosee/shots/12.json")"
  [[ -f ${out} ]]
  [[ ${out} == "${dir}"/* ]]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["nodes"][1]["widgets_values"][2]==12, d["nodes"][1]' \
    "${out}"
  cleanup_temp_files
  [[ ! -d ${dir} ]]
  parse_args go-see 12 --quality high
  [ "${QUALITY}" = "high" ]
  [ "${FILM}" = "go-see" ]
  [ "${SHOT_ID}" = "12" ]
}

@test "print-shot does not POST when the quality transform fails" {
  run compile_film_run go-see
  [ "${status}" -eq 0 ]
  install_prompt_capture_mock
  export COMFY_URL="http://127.0.0.1:1"
  printf '%s' 'not json at all' >"${COMFY_OUTPUT_DIR}/films/gosee/shots/12.json"
  run bash "${PS}" go-see 12 --quality draft
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Quality overlay failed"* ]]
  ! grep -q '/prompt' "${TEST_TMP_DIR}/curl_calls.log"
}
