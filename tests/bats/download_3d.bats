#!/usr/bin/env bats
#
# Cover scripts/utilities/download-3d.sh (TRELLIS.2 native + DA3-BASE).

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export D3="${UTILITIES_DIR}/download-3d.sh"
  chmod +x "${D3}"
  # shellcheck disable=SC1090
  source "${D3}"
}

teardown() {
  teardown_repo_env
}

@test "download-3d CLI help status unknown and banned DA3-LARGE" {
  run bash "${D3}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"trellis2"* ]]
  [[ "${output}" == *"nvdiffrast"* ]]
  [[ "${output}" == *"DA3-LARGE"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${D3}\" status --tier trellis2 --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"trellis2"* ]]
  run bash "${D3}" status --tier da3-large
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"DA3-LARGE"* ]]
  run bash "${D3}" status --tier nvdiffrast
  [ "${status}" -ne 0 ]
  run bash "${D3}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-3d helpers refuse_banned_3d_tier and mock run" {
  run tier_repo trellis2
  [[ "${output}" == *"TRELLIS.2"* ]]
  run tier_repo da3-base
  [[ "${output}" == *"DA3-BASE"* ]]
  run tier_repo da3-large
  [ "${output}" = "" ]
  run tier_include_patterns trellis2
  [[ "${output}" == *"ss_flow_img_dit_xl.safetensors"* ]]
  run tier_include_patterns da3-base
  [[ "${output}" == *"model.safetensors"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"trellis2"* && "${output}" == *"da3-base"* ]]
  run refuse_banned_3d_tier da3-large
  [ "${status}" -eq 1 ]
  run refuse_banned_3d_tier trellis2
  [ "${status}" -eq 0 ]
  parse_args status --tier trellis2 --json
  [ "${CMD}" = "status" ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${D3}\" run --tier trellis2"
  [ "${status}" -eq 0 ]
  [[ -e ${MODELS_DIR}/comfy/3d/ss_flow_img_dit_xl.safetensors ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${D3}\" run --tier da3-base"
  [ "${status}" -eq 0 ]
  [[ -e ${MODELS_DIR}/comfy/diffusion_models/model.safetensors ]]
}

@test "download-3d link_into_comfy cmd_status cache hit" {
  local tdir
  tdir="$(tier_dir trellis2)"
  mkdir -p "${tdir}/ckpts"
  echo t >"${tdir}/ckpts/ss_flow_img_dit_xl.safetensors"
  run link_into_comfy trellis2
  [ "${status}" -eq 0 ]
  [[ -L ${MODELS_DIR}/comfy/3d/ss_flow_img_dit_xl.safetensors ]]
  TIER=trellis2
  run cmd_status
  [ "${status}" -eq 0 ]
  run tier_files_ready trellis2
  [ "${status}" -eq 0 ]
}
