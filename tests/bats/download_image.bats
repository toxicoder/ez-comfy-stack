#!/usr/bin/env bats
#
# ## download_image.bats
#
# Cover scripts/utilities/download-image.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DI="${UTILITIES_DIR}/download-image.sh"
  chmod +x "${DI}"
  # shellcheck disable=SC1090
  source "${DI}"
}

teardown() {
  teardown_repo_env
}

@test "download-image CLI help status fast unknown and banned 9b" {
  run bash "${DI}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DI}\" status --tier fast --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash "${DI}" status --nope
  [ "${status}" -ne 0 ]
  run bash "${DI}" run --tier quality
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"banned"* || "${output}" == *"Banned"* ]]
}

@test "download-image helpers tier_repo min dir includes process" {
  run tier_repo fast
  [[ "${output}" == *"FLUX.2-klein-4b-fp8"* ]]
  run tier_repo nvfp4
  [[ "${output}" == *"nvfp4"* ]]
  run tier_repo bogus
  [ "${output}" = "" ]
  run tier_min_gb fast
  [ "${output}" = "3" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_include_patterns fast
  [[ "${output}" == *"flux-2-klein-4b-fp8.safetensors"* ]]
  run tier_include_patterns te
  [[ "${output}" == *"qwen_3_4b"* ]]
  run tier_include_patterns vae
  [[ "${output}" == *"flux2-vae"* ]]
  TIER=fast
  run tiers_to_process
  [[ "${output}" == *"fast"* && "${output}" == *"te"* && "${output}" == *"vae"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"zimage"* ]]
  parse_args status --tier fast --json
  [ "${CMD}" = "status" ]
  run check_hf_cli
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
}

@test "download-image link_into_comfy cmd_status cmd_run mock" {
  local tdir
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/flux-2-klein-4b-fp8.safetensors"
  run link_into_comfy fast
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/flux-2-klein-4b-fp8.safetensors" ]]
  TIER=fast
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier fast"
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen_3_4b.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=fast
  rm -rf "$(tier_dir fast)" "$(tier_dir te)" "$(tier_dir vae)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-image cleanup keep selective and prune" {
  local tdir extra
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}"
  echo keep >"${tdir}/flux-2-klein-4b-fp8.safetensors"
  extra="${tdir}/junk.safetensors"
  echo waste >"${extra}"
  echo meta >"${tdir}/LICENSE"
  run is_ltx_keep_relpath fast "flux-2-klein-4b-fp8.safetensors"
  [ "${status}" -eq 0 ]
  run is_ltx_keep_relpath fast "junk.safetensors"
  [ "${status}" -ne 0 ]
  run list_extra_ltx_files fast
  [[ "${output}" == *"${extra}"* ]]
  CLEANUP_YES=1
  TIER=fast
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ -f ${tdir}/flux-2-klein-4b-fp8.safetensors ]]
  run prune_empty_dirs "${tdir}"
  [ "${status}" -eq 0 ]
}
