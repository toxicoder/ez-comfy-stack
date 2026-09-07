#!/usr/bin/env bats
#
# Cover scripts/utilities/download-longcat.sh

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DL="${UTILITIES_DIR}/download-longcat.sh"
  chmod +x "${DL}"
  # shellcheck disable=SC1090
  source "${DL}"
}

teardown() {
  teardown_repo_env
}

@test "download-longcat help status refuse context-parallel" {
  run bash "${DL}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"NCCL"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier video --json"
  [ "${status}" -eq 0 ]
  run bash "${DL}" --context-parallel status --tier video
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"LAB_ALLOW_CONTEXT_PARALLEL"* ]]
}

@test "download-longcat helpers and mock run" {
  run tier_repo video
  [[ "${output}" == *"LongCat-Video"* ]]
  run tier_repo avatar
  [[ "${output}" == *"Avatar"* ]]
  run refuse_context_parallel
  [ "${status}" -eq 0 ]
  parse_args status --tier video --json
  [ "${CMD}" = "status" ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DL}\" run --tier video"
  [ "${status}" -eq 0 ]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"video"* && "${output}" == *"avatar"* ]]
  run link_into_comfy video
  [ "${status}" -eq 0 ]
}
