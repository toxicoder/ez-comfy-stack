#!/usr/bin/env bats
#
# ## download_wan.bats
#
# Cover scripts/utilities/download-wan.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DW="${UTILITIES_DIR}/download-wan.sh"
  chmod +x "${DW}"
  # shellcheck disable=SC1090
  source "${DW}"
}

teardown() {
  teardown_repo_env
}

@test "download-wan CLI help status 5b unknown" {
  run bash "${DW}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DW}\" status --tier 5b --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash "${DW}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-wan helpers tier_repo includes 5b a14b" {
  run tier_repo 5b
  [[ "${output}" == *"Wan_2.2_ComfyUI_Repackaged"* ]]
  run tier_repo a14b
  [[ "${output}" == *"Wan_2.2_ComfyUI_Repackaged"* ]]
  run tier_repo x
  [ "${output}" = "" ]
  run tier_min_gb 5b
  [ "${output}" = "12" ]
  run tier_include_patterns 5b
  [[ "${output}" == *"wan2.2_ti2v_5B_fp16.safetensors"* ]]
  [[ "${output}" == *"wan2.2_vae.safetensors"* ]]
  [[ "${output}" == *"umt5_xxl_fp8_e4m3fn_scaled.safetensors"* ]]
  run tier_include_patterns a14b
  [[ "${output}" == *"wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"5b"* && "${output}" == *"a14b"* ]]
  parse_args status --tier 5b --json
  [ "${CMD}" = "status" ]
  run check_hf_cli
  [ "${status}" -eq 0 ]
}

@test "download-wan link_into_comfy cmd_run mock and fail" {
  local tdir
  tdir="$(tier_dir 5b)"
  mkdir -p "${tdir}/split_files/diffusion_models" "${tdir}/split_files/vae" \
    "${tdir}/split_files/text_encoders"
  echo u >"${tdir}/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"
  echo v >"${tdir}/split_files/vae/wan2.2_vae.safetensors"
  echo t >"${tdir}/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
  run link_into_comfy 5b
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/vae/wan2.2_vae.safetensors" ]]
  TIER=5b
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DW}\" run --tier 5b"
  [ "${status}" -eq 0 ]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=5b
  rm -rf "$(tier_dir 5b)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-wan cleanup keep selective" {
  local tdir extra
  tdir="$(tier_dir 5b)"
  mkdir -p "${tdir}/split_files/diffusion_models"
  echo keep >"${tdir}/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"
  extra="${tdir}/split_files/diffusion_models/extra.safetensors"
  echo waste >"${extra}"
  run is_ltx_keep_relpath 5b "split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"
  [ "${status}" -eq 0 ]
  run list_extra_ltx_files 5b
  [[ "${output}" == *"${extra}"* ]]
  CLEANUP_YES=1
  TIER=5b
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  run prune_empty_dirs "${tdir}"
  [ "${status}" -eq 0 ]
}
