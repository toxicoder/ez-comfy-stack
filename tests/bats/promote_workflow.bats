#!/usr/bin/env bats
#
# ## promote_workflow.bats
#
# Cover scripts/utilities/promote-workflow.sh: refuse banned / bad suffix /
# bad lane, copy into workflows/_lab.

load 'test_helper'

setup() {
  setup_repo_env
  chmod +x "${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
}

teardown() {
  teardown_repo_env
}

# Named for coverage inventory: promote_usage promote_lane_ok
# promote_refuse_banned promote_run

@test "promote_workflow refuses banned strings bad suffix and bad lane" {
  local src sh
  sh="${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  src="${TEST_TMP_DIR}/bad.json"
  printf '%s\n' '{"id":"x","note":"MiniMax"}' >"${src}"
  run bash "${sh}" --from "${src}" --lane klein --id klein-hook-lab-example
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"MiniMax"* ]]
  printf '%s\n' '{"id":"ok"}' >"${src}"
  run bash "${sh}" --from "${src}" --lane klein --id not-an-example
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"-lab-example"* ]]
  run bash "${sh}" --from "${src}" --lane nope --id klein-hook-lab-example
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown lane"* ]]
  run bash "${sh}" --from "${TEST_TMP_DIR}/missing.json" --lane klein --id klein-hook-lab-example
  [ "${status}" -ne 0 ]
  run bash "${sh}" --help
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Usage:"* ]]
}

@test "promote_workflow copies into _lab and never the reverse" {
  local src dest sh
  sh="${REPO_ROOT}/scripts/utilities/promote-workflow.sh"
  src="${TEST_TMP_DIR}/keep-me.json"
  printf '%s\n' '{"id":"klein-my-hook-lab-example","nodes":[]}' >"${src}"
  dest="${REPO_ROOT}/workflows/_lab/klein/klein-my-hook-lab-example.json"
  run bash "${sh}" --from "${src}" --lane klein --id klein-my-hook-lab-example
  [ "${status}" -eq 0 ]
  [[ -f ${dest} ]]
  grep -F 'klein-my-hook-lab-example' "${dest}"
  [[ "${output}" == *"stamp App Mode"* ]]
  rm -f "${dest}"
  run bash "${sh}" --from "${REPO_ROOT}/workflows/_lab/klein/klein-still-draft-lab-example.json" \
    --lane klein --id klein-cloned-lab-example
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"never copy _lab"* ]]
}
