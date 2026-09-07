#!/usr/bin/env bats
#
# Cover scripts/utilities/download-dreamx.sh

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DX="${UTILITIES_DIR}/download-dreamx.sh"
  chmod +x "${DX}"
  # shellcheck disable=SC1090
  source "${DX}"
}

teardown() {
  teardown_repo_env
}

@test "download-dreamx help status refuse World" {
  run bash "${DX}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Creator"* ]]
  [[ "${output}" == *"World"* ]]
  run bash "${DX}" status --tier world
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"DreamX-World"* ]]
  run refuse_dreamx_world creator
  [ "${status}" -eq 0 ]
}

@test "download-dreamx helpers and mock run" {
  run tier_repo creator
  [[ "${output}" == *"DreamX-Creator"* ]]
  run tier_include_patterns creator
  [[ "${output}" == *"cross_attn_weights.safetensors"* ]]
  parse_args status --tier creator --json
  [ "${CMD}" = "status" ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DX}\" run --tier creator"
  [ "${status}" -eq 0 ]
  [[ -e ${MODELS_DIR}/comfy/diffusion_models/cross_attn_weights.safetensors ]]
}
