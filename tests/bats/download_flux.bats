#!/usr/bin/env bats
#
# ## download_flux.bats
#
# Purpose:
#   Cover every function in scripts/utilities/download-flux.sh via source + direct
#   calls and CLI status/run (strict coverage inventory).
#
# Hermetic:
#   LAB_MOCK_HF_DOWNLOAD and PATH mocks; no network.
#

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DF="${UTILITIES_DIR}/download-flux.sh"
  chmod +x "${DF}"
  # shellcheck disable=SC1090
  source "${DF}"
}

teardown() {
  teardown_repo_env
}

@test "download-flux CLI help status quality unknown" {
  run bash "${DF}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DF}\" status --tier fast --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DF}\" status --tier fast"
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DF}\" status --tier quality --json"
  [ "${status}" -eq 0 ]
  run bash "${DF}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-flux helpers tier_repo tier_min_gb tier_dir comfy_link_dir" {
  run tier_repo fast
  [[ "${output}" == *"FLUX"* || "${output}" == *"klein"* || "${output}" == *"black-forest"* ]]
  run tier_repo quality
  [ "${status}" -eq 0 ]
  run tier_repo nunchaku
  [ "${status}" -eq 0 ]
  run tier_repo bogus
  [ "${output}" = "" ]
  run tier_min_gb fast
  [ "${output}" = "12" ]
  run tier_min_gb quality
  [ "${output}" = "30" ]
  run tier_min_gb nunchaku
  [ "${output}" = "4" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  TIER=fast
  run tier_dir fast
  [[ "${output}" == *"${MODELS_DIR}"* ]]
  run comfy_link_dir fast
  [[ "${output}" == *"diffusion_models"* ]]
}

@test "download-flux tiers_to_process parse_args check_hf_cli hf_download" {
  TIER=all
  INCLUDE_NUNCHAKU=1
  run tiers_to_process
  [[ "${output}" == *"fast"* ]]
  TIER=all
  INCLUDE_NUNCHAKU=0
  run tiers_to_process
  [[ "${output}" == *"quality"* ]]
  TIER=fast
  INCLUDE_NUNCHAKU=1
  run tiers_to_process
  [[ "${output}" == *"nunchaku"* ]]
  TIER=fast
  INCLUDE_NUNCHAKU=0
  run tiers_to_process
  [ "${output}" = "fast" ]
  TIER=quality
  run tiers_to_process
  [ "${output}" = "quality" ]
  TIER=nunchaku
  run tiers_to_process
  [ "${output}" = "nunchaku" ]
  TIER=custom
  run tiers_to_process
  [ "${output}" = "custom" ]

  parse_args status --tier fast --json
  [ "${CMD}" = "status" ]
  [ "${TIER}" = "fast" ]
  parse_args run --no-nunchaku
  [ "${INCLUDE_NUNCHAKU}" = "0" ]

  run check_hf_cli
  [ "${status}" -eq 0 ]

  run hf_download "org/model" --local-dir "${MODELS_DIR}/mock_repo"
  [ "${status}" -eq 0 ]
  [[ -f "${MODELS_DIR}/mock_repo/.mock" ]]
}

@test "download-flux link_into_comfy tier_size_gb cmd_status cmd_run" {
  local tdir
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/model.safetensors"
  run tier_size_gb "${tdir}"
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/missing"
  [ "${output}" = "0" ]
  run link_into_comfy fast
  [ "${status}" -eq 0 ]
  TIER=fast
  INCLUDE_NUNCHAKU=0
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DF}\" run --tier fast --no-nunchaku"
  [ "${status}" -eq 0 ]
  # cmd_run via sourced function
  TIER=fast
  INCLUDE_NUNCHAKU=0
  LAB_MOCK_HF_DOWNLOAD=1
  run cmd_run
  [ "${status}" -eq 0 ]
}
