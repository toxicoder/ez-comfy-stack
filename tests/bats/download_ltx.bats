#!/usr/bin/env bats
#
# ## download_ltx.bats
#
# Purpose:
#   Cover every function in scripts/utilities/download-ltx.sh (strict inventory).
#
# Hermetic:
#   LAB_MOCK_HF_DOWNLOAD; no network.
#

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DL="${UTILITIES_DIR}/download-ltx.sh"
  chmod +x "${DL}"
  # shellcheck disable=SC1090
  source "${DL}"
}

teardown() {
  teardown_repo_env
}

@test "download-ltx CLI help status all unknown" {
  run bash "${DL}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier balanced --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier balanced"
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier all --json"
  [ "${status}" -eq 0 ]
  run bash "${DL}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-ltx helpers tier_repo min dir size tiers parse check_hf hf_download" {
  run tier_repo balanced
  [[ "${output}" == *"LTX"* || "${output}" == *"Kijai"* ]]
  run tier_repo quality
  [ "${status}" -eq 0 ]
  run tier_repo x
  [ "${output}" = "" ]
  run tier_min_gb balanced
  [ "${output}" = "20" ]
  run tier_min_gb quality
  [ "${output}" = "35" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_dir balanced
  [[ "${output}" == *"${MODELS_DIR}"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"quality"* ]]
  TIER=balanced
  run tiers_to_process
  [ "${output}" = "balanced" ]
  parse_args status --tier balanced --json
  [ "${CMD}" = "status" ]
  run check_hf_cli
  [ "${status}" -eq 0 ]
  run hf_download "org/ltx" --local-dir "${MODELS_DIR}/ltx_mock"
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/ltx_mock"
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
}

@test "download-ltx link_into_comfy cmd_status cmd_run" {
  local tdir
  tdir="$(tier_dir balanced)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/vid.safetensors"
  echo y >"${tdir}/text_encoder.safetensors"
  echo z >"${tdir}/audio_vae.safetensors"
  run link_into_comfy balanced
  [ "${status}" -eq 0 ]
  TIER=balanced
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DL}\" run --tier balanced"
  [ "${status}" -eq 0 ]
  TIER=balanced
  LAB_MOCK_HF_DOWNLOAD=1
  run cmd_run
  [ "${status}" -eq 0 ]
}
