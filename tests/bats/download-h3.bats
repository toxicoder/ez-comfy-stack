#!/usr/bin/env bats
#
# ## download-h3.bats
#
# Purpose:
#   Cover every function in scripts/utilities/download-h3.sh (strict inventory).
#
# Hermetic:
#   LAB_MOCK_HF_DOWNLOAD and PATH mocks; no network.
#

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DH="${UTILITIES_DIR}/download-h3.sh"
  chmod +x "${DH}"
  # shellcheck disable=SC1090
  source "${DH}"
}

teardown() {
  teardown_repo_env
}

@test "download-h3 CLI help status pruned unknown" {
  run bash "${DH}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DH}\" status --tier pruned --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DH}\" status --tier pruned"
  [ "${status}" -eq 0 ]
  run bash "${DH}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-h3 helpers tier_repo min dir size process includes" {
  run tier_repo pruned
  [[ "${output}" == "Comfy-Org/MiniMax-H3" ]]
  run tier_repo ref2va
  [[ "${output}" == *"MiniMax-H3"* ]]
  run tier_repo turbo
  [[ "${output}" == *"MiniMax-H3"* ]]
  run tier_repo bogus
  [ "${output}" = "" ]
  run tier_min_gb pruned
  [ "${output}" = "35" ]
  run tier_min_gb ref2va
  [ "${output}" = "15" ]
  run tier_min_gb turbo
  [ "${output}" = "1" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_dir pruned
  [[ "${output}" == *"${MODELS_DIR}"* ]]
  run comfy_link_dir
  [[ "${output}" == *"diffusion_models"* ]]
  run tier_size_gb "${MODELS_DIR}/missing"
  [ "${output}" = "0" ]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"pruned"* ]]
  [[ "${output}" == *"ref2va"* ]]
  TIER=pruned
  run tiers_to_process
  [ "${output}" = "pruned" ]
  TIER=ref2va
  run tiers_to_process
  [ "${output}" = "ref2va" ]
  TIER=turbo
  run tiers_to_process
  [ "${output}" = "turbo" ]
  TIER=custom
  run tiers_to_process
  [ "${output}" = "custom" ]
  run tier_include_patterns pruned
  [[ "${output}" == *"minimax_h3_fl2va_pruned_int8_convrot"* ]]
  [[ "${output}" == *"qwen3vl_32b_minimax_h3_nvfp4_awq"* ]]
  [[ "${output}" == *"minimax_h3_video_vae_fp16"* ]]
  [[ "${output}" == *"minimax_h3_audio_vae_fp32"* ]]
  run tier_include_patterns ref2va
  [[ "${output}" == *"ref2va"* ]]
  run tier_include_patterns turbo
  [[ "${output}" == *"turbo"* ]]
}

@test "download-h3 parse_args check_hf link status run cache hit" {
  parse_args status --tier pruned --json
  [ "${CMD}" = "status" ]
  [ "${TIER}" = "pruned" ]
  [ "${JSON_FLAG}" = "--json" ]
  parse_args run --tier turbo
  [ "${CMD}" = "run" ]
  [ "${TIER}" = "turbo" ]

  run check_hf_cli
  [ "${status}" -eq 0 ]

  local tdir
  tdir="$(tier_dir pruned)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/model.safetensors"
  run tier_size_gb "${tdir}"
  [ "${status}" -eq 0 ]
  run link_into_comfy pruned
  [ "${status}" -eq 0 ]
  TIER=pruned
  run cmd_status
  [ "${status}" -eq 0 ]

  export LAB_MOCK_HF_DOWNLOAD=1
  TIER=pruned
  run cmd_run
  [ "${status}" -eq 0 ]
  run tier_files_ready pruned
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" ]]
  local link_tgt
  link_tgt="$(readlink "${MODELS_DIR}/comfy/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors")"
  [[ "${link_tgt}" != /* ]]
  [[ "${link_tgt}" == ../* ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/minimax_h3_video_vae_fp16.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/minimax_h3_audio_vae_fp32.safetensors" ]]

  : >"${TEST_TMP_DIR}/hf_calls.log"
  unset LAB_MOCK_HF_DOWNLOAD
  TIER=pruned
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cache hit"* || "${output}" == *"skip pruned"* ]]
  ! grep -q 'hf download' "${TEST_TMP_DIR}/hf_calls.log"

  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=pruned
  rm -rf "$(tier_dir pruned)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-h3 CLI run pruned and ready requires all four files" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DH}\" run --tier pruned"
  [ "${status}" -eq 0 ]
  local tdir
  tdir="$(tier_dir pruned)"
  run tier_files_ready pruned
  [ "${status}" -eq 0 ]
  rm -f "${tdir}/vae/minimax_h3_audio_vae_fp32.safetensors"
  run tier_files_ready pruned
  [ "${status}" -ne 0 ]
}
