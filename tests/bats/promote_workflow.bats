#!/usr/bin/env bats
#
# ## promote_workflow.bats
#
# Cover scripts/utilities/promote-workflow.sh: refuse banned / bad id /
# bad lane, copy into workflows/_lab.

load 'test_helper'

setup() {
  setup_repo_env
  chmod +x "${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
}

teardown() {
  teardown_repo_env
}

@test "promote_workflow helpers usage lane_ok refuse_banned" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  run promote_usage
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  run promote_lane_ok stills
  [ "${status}" -eq 0 ]
  run promote_lane_ok nope
  [ "${status}" -ne 0 ]
  local src="${TEST_TMP_DIR}/ok.json"
  printf '%s\n' '{"id":"ok"}' >"${src}"
  run promote_refuse_banned "${src}"
  [ "${status}" -eq 0 ]
  printf '%s\n' '{"id":"x","note":"MiniMax"}' >"${src}"
  run promote_refuse_banned "${src}"
  [ "${status}" -ne 0 ]
}

@test "promote_workflow refuses banned strings bad id and bad lane" {
  local src sh
  sh="${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  src="${TEST_TMP_DIR}/bad.json"
  printf '%s\n' '{"id":"x","note":"MiniMax"}' >"${src}"
  run bash "${sh}" --from "${src}" --lane stills --id my-hook
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"MiniMax"* ]]
  printf '%s\n' '{"id":"ok"}' >"${src}"
  run bash "${sh}" --from "${src}" --lane stills --id '..'
  [ "${status}" -ne 0 ]
  run bash "${sh}" --from "${src}" --lane nope --id my-hook
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown lane"* ]]
  run bash "${sh}" --from "${TEST_TMP_DIR}/missing.json" --lane stills --id my-hook
  [ "${status}" -ne 0 ]
  run bash "${sh}" --help
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Usage:"* ]]
}

@test "promote_workflow refuses 9B UNET pin but allows 9B in notes" {
  local src
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  src="${TEST_TMP_DIR}/note.json"
  printf '%s\n' '{"id":"ok","nodes":[],"extra":{"lab_note":"Quality ultra may select Klein 9B"}}' >"${src}"
  run promote_refuse_banned "${src}"
  [ "${status}" -eq 0 ]
  printf '%s\n' '{"id":"x","nodes":[{"type":"UNETLoader","widgets_values":["flux-2-klein-9b-fp8.safetensors","default"]}]}' >"${src}"
  run promote_refuse_banned "${src}"
  [ "${status}" -ne 0 ]
}

@test "promote_workflow copies into _lab and never the reverse" {
  local src dest sh
  sh="${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  src="${TEST_TMP_DIR}/keep-me.json"
  printf '%s\n' '{"id":"my-hook","nodes":[]}' >"${src}"
  dest="${REPO_ROOT}/workflows/_lab/stills/my-hook.json"
  run bash "${sh}" --from "${src}" --lane stills --id my-hook
  [ "${status}" -eq 0 ]
  [[ -f ${dest} ]]
  grep -F 'my-hook' "${dest}"
  [[ "${output}" == *"stamp App Mode"* ]]
  rm -f "${dest}"
  dest="${REPO_ROOT}/workflows/_lab/audio/albums/demo/hook.json"
  run bash "${sh}" --from "${src}" --lane audio --id hook --subdir albums/demo
  [ "${status}" -eq 0 ]
  [[ -f ${dest} ]]
  rm -rf "${REPO_ROOT}/workflows/_lab/audio/albums/demo"
  run bash "${sh}" --from "${REPO_ROOT}/workflows/_lab/stills/still-draft.json" \
    --lane stills --id cloned
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"never copy _lab"* ]]
}
