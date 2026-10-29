#!/usr/bin/env bats
#
# ## album_render.bats
#
# Cover scripts/utilities/album-render.sh usage, dry-run, and pack.

load 'test_helper'

setup() {
  setup_repo_env
  chmod +x "${REPO_ROOT}/scripts/utilities/album-render.sh"
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
  echo "{\"prompt_id\":\"track1\"}"
  exit 0
fi
echo "{\"track1\":{\"status\":\"success\"}}"
exit 0
'
}

#######################################
# Write an ACE-Step shaped track graph (audio occupancy).
# Globals:
#   None
# Arguments:
#   $1  destination path
#   $2  tier to record on the EZQuality widget ('' = no widget value)
# Outputs:
#   The graph file at $1
# Returns:
#   0
#######################################
write_track_graph() {
  local path="${1}" tier="${2}"
  python3 - "${path}" "${tier}" <<'PY'
import json
import sys

path, tier = sys.argv[1], sys.argv[2]
widgets = [tier] if tier else []
graph = {
    "nodes": [
        {"id": 1, "type": "EZQuality", "widgets_values": widgets},
        {"id": 2, "type": "KSampler", "widgets_values": [3, "fixed", 20, 1.0]},
        {"id": 3, "type": "SaveAudio", "widgets_values": ["take"]},
    ],
    "extra": {"lab_app_mode": {"occupancy": "audio"}},
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(graph, handle)
PY
}

@test "album_render helpers comfy_up comfy_free pack_only cmd_album_render" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/utilities/album-render.sh"
  install_mock_bin curl 'exit 0'
  run comfy_up
  [ "${status}" -eq 0 ]
  run comfy_free
  [ "${status}" -eq 0 ]
  run pack_only "nill-bye/peer-review"
  [ "${status}" -ne 0 ]
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/manage.sh"
  run cmd_album_render --help
  [ "${status}" -eq 0 ]
}

@test "album_render help status dry-run and missing album" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  run bash "${sh}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  run bash "${sh}"
  [ "${status}" -ne 0 ]
  run bash "${sh}" status
  [ "${status}" -eq 0 ]
  run bash "${sh}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"comfy"'* ]]
  run bash "${sh}" run --album missing/nope --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown album"* ]]
}

@test "album_render dry-run known album and upload requires image" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  mkdir -p "${REPO_ROOT}/workflows/_lab/audio/albums/nill-bye/peer-review"
  run bash "${sh}" run --album nill-bye/peer-review --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  run bash "${sh}" run --album nill-bye/peer-review --art upload --dry-run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--image"* ]]
  run bash "${sh}" run --album nill-bye/peer-review --art bogus --dry-run
  [ "${status}" -ne 0 ]
}

@test "album_render pack refuses empty output dir" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  mkdir -p "${REPO_ROOT}/workflows/_lab/audio/albums/nill-bye/peer-review"
  export COMFY_OUTPUT_DIR="${TEST_TMP_DIR}/out"
  mkdir -p "${COMFY_OUTPUT_DIR}"
  run bash "${sh}" pack --album nill-bye/peer-review
  [ "${status}" -ne 0 ]
}

@test "album_render --quality is accepted and documented" {
  local sh
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  mkdir -p "${REPO_ROOT}/workflows/_lab/audio/albums/nill-bye/peer-review"
  run bash "${sh}" run --album nill-bye/peer-review --quality draft --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry-run"* ]]
  run bash "${sh}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--quality"* ]]
  run bash "${sh}" run --album nill-bye/peer-review --quality
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--quality needs a tier"* ]]
}

@test "album_render posts the quality-overlaid track graph" {
  local sh graph out status
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  # shellcheck disable=SC1091
  source "${sh}"
  install_prompt_capture_mock
  COMFY_URL="http://127.0.0.1:1"
  QUALITY="draft"
  graph="${TEST_TMP_DIR}/01-track.json"
  write_track_graph "${graph}" lab
  out="$(quality_apply_graph "${graph}")"
  [[ -f ${out} ]]
  [[ ${out} == "${RUN_TMP_DIR}"/* ]]
  status="$(comfy_post_prompt "${out}")"
  [ "${status}" = "track1" ]
  grep -q '/prompt' "${TEST_TMP_DIR}/curl_calls.log"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); n=d["nodes"]; assert n[0]["widgets_values"]==["lab"], n[0]; assert n[1]["widgets_values"][2]==4, n[1]' \
    "${TEST_TMP_DIR}/posted_body.json"
}

@test "album_render uses the tier the graph records when no flag is given" {
  local sh graph out status
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  # shellcheck disable=SC1091
  source "${sh}"
  install_prompt_capture_mock
  COMFY_URL="http://127.0.0.1:1"
  QUALITY=""
  graph="${TEST_TMP_DIR}/01-track.json"
  write_track_graph "${graph}" high
  out="$(quality_apply_graph "${graph}")"
  status="$(comfy_post_prompt "${out}")"
  [ "${status}" = "track1" ]
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["nodes"][1]["widgets_values"][2]==16, d["nodes"][1]' \
    "${TEST_TMP_DIR}/posted_body.json"
}

@test "album_render does not POST when the quality transform fails" {
  local sh graph
  sh="${REPO_ROOT}/scripts/utilities/album-render.sh"
  # shellcheck disable=SC1091
  source "${sh}"
  install_prompt_capture_mock
  COMFY_URL="http://127.0.0.1:1"
  QUALITY="draft"
  graph="${TEST_TMP_DIR}/01-track.json"
  printf '%s' 'not json at all' >"${graph}"
  run quality_apply_graph "${graph}"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Quality overlay failed"* ]]
  ! grep -q '/prompt' "${TEST_TMP_DIR}/curl_calls.log"
}
