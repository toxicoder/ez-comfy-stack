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
  teardown_repo_env
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
  # 12 is ok + ffprobe 5.00 → skip
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
