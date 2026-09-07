#!/usr/bin/env bats
#
# Cover scripts/utilities/download-restore.sh (SeedVR2-3B opt-in).

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DR="${UTILITIES_DIR}/download-restore.sh"
  chmod +x "${DR}"
  # shellcheck disable=SC1090
  source "${DR}"
}

teardown() {
  teardown_repo_env
}

@test "download-restore CLI help status unknown tier" {
  run bash "${DR}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"seedvr2-3b"* ]]
  [[ "${output}" != *"download-models"* ]] || true
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DR}\" status --tier seedvr2-3b --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"seedvr2-3b"* ]]
  run bash "${DR}" status --tier nope
  [ "${status}" -ne 0 ]
}

@test "download-restore helpers and mock run" {
  run tier_repo seedvr2-3b
  [[ "${output}" == *"SeedVR2-3B"* ]]
  run tier_include_patterns seedvr2-3b
  [[ "${output}" == *"seedvr2_ema_3b.pth"* ]]
  [[ "${output}" != *"apex"* ]]
  parse_args status --tier seedvr2-3b --json
  [ "${CMD}" = "status" ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DR}\" run --tier seedvr2-3b"
  [ "${status}" -eq 0 ]
  [[ -e ${MODELS_DIR}/comfy/upscale_models/seedvr2_ema_3b.pth ]]
}
