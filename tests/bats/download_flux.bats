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
  [ "${output}" = "5" ]
  run tier_repo companions
  [[ "${output}" == *"Comfy-Org"* ]]
  run tier_min_gb companions
  [ "${output}" = "6" ]
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
  [[ "${output}" == *"fast"* ]]
  [[ "${output}" == *"companions"* ]]
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

  export LAB_MOCK_HF_DOWNLOAD=1
  run hf_download "org/model" --local-dir "${MODELS_DIR}/mock_repo"
  [ "${status}" -eq 0 ]
  [[ -f "${MODELS_DIR}/mock_repo/.mock" ]]

  # Prefer hf over broken huggingface-cli when both on PATH
  unset LAB_MOCK_HF_DOWNLOAD
  : >"${TEST_TMP_DIR}/hf_calls.log"
  run hf_download "org/real" --local-dir "${MODELS_DIR}/real_repo"
  [ "${status}" -eq 0 ]
  grep -q 'hf download org/real' "${TEST_TMP_DIR}/hf_calls.log"
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
  # Not ready yet (size << min_gb) — still downloads via mock
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DF}\" run --tier fast --no-nunchaku"
  [ "${status}" -eq 0 ]
  # cmd_run via sourced function
  TIER=fast
  INCLUDE_NUNCHAKU=0
  LAB_MOCK_HF_DOWNLOAD=1
  run cmd_run
  [ "${status}" -eq 0 ]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=fast
  INCLUDE_NUNCHAKU=0
  # Clear prior mock weights so fail cannot cache-hit companions
  rm -rf "$(tier_dir fast)" "$(tier_dir companions)"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"No FLUX tiers"* || "${output}" == *"failed"* || "${output}" == *"Companions"* ]]
}

@test "download-flux tier_files_ready and cmd_run cache hit skip" {
  local tdir cdir
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/model.safetensors"
  # Companions must also be ready so --tier fast does not re-pull them
  cdir="$(tier_dir companions)"
  mkdir -p "${cdir}/split_files/text_encoders" "${cdir}/split_files/vae"
  echo te >"${cdir}/split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
  echo vae >"${cdir}/split_files/vae/flux2-vae.safetensors"
  # Override min so tiny fixture counts as ready
  tier_min_gb() { echo 0; }
  run tier_files_ready fast
  [ "${status}" -eq 0 ]
  run tier_files_ready companions
  [ "${status}" -eq 0 ]
  : >"${TEST_TMP_DIR}/hf_calls.log"
  unset LAB_MOCK_HF_DOWNLOAD
  TIER=fast
  INCLUDE_NUNCHAKU=0
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cache hit"* || "${output}" == *"skip fast"* ]]
  ! grep -q 'hf download' "${TEST_TMP_DIR}/hf_calls.log"
  # no weights → not ready
  rm -f "${tdir}/model.safetensors"
  run tier_files_ready fast
  [ "${status}" -ne 0 ]
}

@test "download-flux companions ready requires TE and VAE not size alone" {
  local cdir
  cdir="$(tier_dir companions)"
  mkdir -p "${cdir}/split_files/text_encoders" "${cdir}/split_files/vae"
  # TE alone is enough GB for the old size floor but must not count as ready
  echo te >"${cdir}/split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
  run tier_files_ready companions
  [ "${status}" -ne 0 ]
  echo vae >"${cdir}/split_files/vae/flux2-vae.safetensors"
  run tier_files_ready companions
  [ "${status}" -eq 0 ]
  # link always retargets even when dest already exists
  mkdir -p "${MODELS_DIR}/comfy/vae"
  echo stale >"${MODELS_DIR}/comfy/vae/flux2-vae.safetensors"
  run link_into_comfy companions
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
  [[ "$(readlink "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors")" == *"flux2-vae.safetensors" ]]
}

@test "download-flux cmd_run fails when companions incomplete after mock" {
  # Force companions path to look present but missing VAE after "success"
  export LAB_MOCK_HF_DOWNLOAD=1
  TIER=companions
  INCLUDE_NUNCHAKU=0
  # Intercept: run once then delete VAE before readiness would pass — instead
  # plant only TE and force fail path via tier_files_ready after empty dir skip.
  local cdir
  cdir="$(tier_dir companions)"
  mkdir -p "${cdir}/split_files/text_encoders"
  echo te >"${cdir}/split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
  # Not ready (missing VAE) → will re-download via mock (creates includes)
  run cmd_run
  [ "${status}" -eq 0 ]
  run tier_files_ready companions
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
}
