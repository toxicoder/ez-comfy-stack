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
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier 2.5 --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier 2.5"
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier all --json"
  [ "${status}" -eq 0 ]
  run bash "${DL}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-ltx helpers tier_repo min dir size tiers parse check_hf hf_download" {
  run tier_repo 2.5
  [[ "${output}" == *"Lightricks/LTX-2.5"* ]]
  run tier_repo balanced
  [[ "${output}" == *"LTX"* || "${output}" == *"Kijai"* ]]
  run tier_repo quality
  [ "${status}" -eq 0 ]
  run tier_repo gemma
  [[ "${output}" == *"Comfy-Org/ltx-2"* ]]
  run tier_repo x
  [ "${output}" = "" ]
  run tier_min_gb balanced
  [ "${output}" = "20" ]
  run tier_min_gb quality
  [ "${output}" = "35" ]
  run tier_min_gb gemma
  [ "${output}" = "8" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_dir balanced
  [[ "${output}" == *"${MODELS_DIR}"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"2.5"* ]]
  [[ "${output}" == *"2.3"* ]]
  [[ "${output}" == *"gemma"* ]]
  TIER=balanced
  run tiers_to_process
  [[ "${output}" == *"balanced"* ]]
  [[ "${output}" == *"gemma"* ]]
  parse_args status --tier balanced --json
  [ "${CMD}" = "status" ]
  run check_hf_cli
  [ "${status}" -eq 0 ]
  export LAB_MOCK_HF_DOWNLOAD=1
  run hf_download "org/ltx" --local-dir "${MODELS_DIR}/ltx_mock"
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/ltx_mock"
  [ "${status}" -eq 0 ]
  run tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
}

@test "download-ltx 2.5 distilled includes INT8-convrot pack" {
  run tier_include_patterns 2.5
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"* ]]
  [[ "${output}" == *"gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"* ]]
  [[ "${output}" == *"ltx-2.5-video-vae-bf16.safetensors"* ]]
  [[ "${output}" == *"ltx-2.5-audio-vae-bf16.safetensors"* ]]
  [[ "${output}" != *"400 GB"* ]]
}

@test "download-ltx tier_include_patterns selective balanced quality gemma" {
  run tier_include_patterns balanced
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"fp8_input_scaled_v3"* ]]
  [[ "${output}" == *"text_encoders/ltx-2.3_text_projection_bf16.safetensors"* ]]
  [[ "${output}" == *"vae/LTX23_video_vae_bf16.safetensors"* ]]
  [[ "${output}" == *"vae/LTX23_audio_vae_bf16.safetensors"* ]]
  # Must not request every monorepo variant / bf16 transformer on balanced
  [[ "${output}" != *"dev_transformer"* ]]
  [[ "${output}" != *"distilled_transformer_only_bf16"* ]]
  [[ "${output}" != *"loras/"* ]]
  run tier_include_patterns quality
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"distilled_transformer_only_bf16"* ]]
  [[ "${output}" == *"text_encoders/"* ]]
  [[ "${output}" != *"fp8_input_scaled_v3"* ]]
  run tier_include_patterns gemma
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"gemma_3_12B_it_fp4_mixed.safetensors"* ]]
  [[ "${output}" == *"split_files/text_encoders/"* ]]
  run tier_include_patterns bogus
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "download-ltx cmd_run passes --include patterns to hf (selective)" {
  : >"${TEST_TMP_DIR}/hf_calls.log"
  unset LAB_MOCK_HF_DOWNLOAD
  TIER=balanced
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'hf download Kijai/LTX2.3_comfy' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q 'hf download Comfy-Org/ltx-2' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q -- '--include' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q 'fp8_input_scaled_v3' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q 'text_projection' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q 'gemma_3_12B_it_fp4_mixed' "${TEST_TMP_DIR}/hf_calls.log"
}

@test "download-ltx cmd_run LTX_FULL_REPO=1 omits --include for Kijai not gemma" {
  : >"${TEST_TMP_DIR}/hf_calls.log"
  unset LAB_MOCK_HF_DOWNLOAD
  export LTX_FULL_REPO=1
  TIER=balanced
  run cmd_run
  [ "${status}" -eq 0 ]
  grep -q 'hf download Kijai/LTX2.3_comfy' "${TEST_TMP_DIR}/hf_calls.log"
  grep -q 'hf download Comfy-Org/ltx-2' "${TEST_TMP_DIR}/hf_calls.log"
  # Kijai full monorepo line has no --include; gemma companion still selective
  ! grep -E 'hf download Kijai/LTX2.3_comfy .*--include' "${TEST_TMP_DIR}/hf_calls.log"
  grep -E 'hf download Comfy-Org/ltx-2' "${TEST_TMP_DIR}/hf_calls.log" | grep -q -- '--include' \
    || grep -q 'gemma_3_12B_it_fp4_mixed' "${TEST_TMP_DIR}/hf_calls.log"
  unset LTX_FULL_REPO
}

@test "download-ltx tier_files_ready skip and cleanup keeps resume cache" {
  local tdir gdir keep extra cache_inc
  tdir="$(tier_dir balanced)"
  mkdir -p "${tdir}/diffusion_models" "${tdir}/text_encoders" "${tdir}/vae" "${tdir}/loras" \
    "${tdir}/.cache/huggingface/download"
  keep="diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors"
  echo keep >"${tdir}/${keep}"
  echo te >"${tdir}/text_encoders/ltx-2.3_text_projection_bf16.safetensors"
  echo vv >"${tdir}/vae/LTX23_video_vae_bf16.safetensors"
  echo av >"${tdir}/vae/LTX23_audio_vae_bf16.safetensors"
  echo meta >"${tdir}/LICENSE"
  cache_inc="${tdir}/.cache/huggingface/download/blob.incomplete"
  echo partial >"${cache_inc}"
  extra="${tdir}/diffusion_models/ltx-2.3-22b-dev_transformer_only_bf16.safetensors"
  echo waste >"${extra}"
  echo waste >"${tdir}/loras/some_lora.safetensors"
  echo waste >"${tdir}/.cache_junk"
  # Gemma companion must also be ready so balanced cmd_run is a pure cache hit
  gdir="$(tier_dir gemma)"
  mkdir -p "${gdir}/split_files/text_encoders"
  echo g >"${gdir}/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"

  run tier_files_ready balanced
  [ "${status}" -eq 0 ]
  run tier_files_ready gemma
  [ "${status}" -eq 0 ]
  rm -f "${tdir}/vae/LTX23_audio_vae_bf16.safetensors"
  run tier_files_ready balanced
  [ "${status}" -ne 0 ]
  echo av >"${tdir}/vae/LTX23_audio_vae_bf16.safetensors"

  run is_ltx_keep_relpath balanced "${keep}"
  [ "${status}" -eq 0 ]
  run is_ltx_keep_relpath balanced ".cache/huggingface/download/blob.incomplete"
  [ "${status}" -eq 0 ]
  run is_ltx_keep_relpath balanced "diffusion_models/ltx-2.3-22b-dev_transformer_only_bf16.safetensors"
  [ "${status}" -ne 0 ]

  run list_extra_ltx_files balanced
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"${extra}"* ]]
  [[ "${output}" == *"loras/some_lora"* ]]
  [[ "${output}" != *".cache/huggingface"* ]]
  [[ "${output}" != *"fp8_input_scaled_v3"* ]]

  : >"${TEST_TMP_DIR}/hf_calls.log"
  unset LAB_MOCK_HF_DOWNLOAD
  TIER=balanced
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cache hit"* || "${output}" == *"skip balanced"* || "${output}" == *"skip gemma"* ]]
  ! grep -q 'hf download' "${TEST_TMP_DIR}/hf_calls.log"

  CLEANUP_YES=1
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ ! -f ${tdir}/loras/some_lora.safetensors ]]
  [[ -f ${tdir}/${keep} ]]
  [[ -f ${cache_inc} ]]
  [[ -f ${tdir}/LICENSE ]]

  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" cleanup --tier balanced --dry-run"
  [ "${status}" -eq 0 ]

  run prune_empty_dirs "${tdir}"
  [ "${status}" -eq 0 ]
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
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=balanced
  # Wipe both auto-tiers so fail cannot soft-succeed on gemma cache hit alone
  rm -rf "$(tier_dir balanced)" "$(tier_dir gemma)"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"No LTX tiers"* || "${output}" == *"failed"* ]]
}

@test "download-ltx link_into_comfy routes by HF path not *te* in safetensors" {
  local tdir gdir
  tdir="$(tier_dir balanced)"
  mkdir -p "${tdir}/diffusion_models" "${tdir}/text_encoders" "${tdir}/vae"
  echo u >"${tdir}/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors"
  echo t >"${tdir}/text_encoders/ltx-2.3_text_projection_bf16.safetensors"
  echo v >"${tdir}/vae/LTX23_video_vae_bf16.safetensors"
  echo a >"${tdir}/vae/LTX23_audio_vae_bf16.safetensors"
  run link_into_comfy balanced
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/text_encoders/ltx-2.3_text_projection_bf16.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/vae/LTX23_video_vae_bf16.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/vae/LTX23_audio_vae_bf16.safetensors" ]]
  # Must not land transformers/VAEs under text_encoders via *te* ↔ safetensors
  [[ ! -e ${MODELS_DIR}/comfy/text_encoders/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors ]]
  [[ ! -e ${MODELS_DIR}/comfy/text_encoders/LTX23_video_vae_bf16.safetensors ]]
  # Relative links (container mount path independence)
  local vlink
  vlink="$(readlink "${MODELS_DIR}/comfy/vae/LTX23_video_vae_bf16.safetensors")"
  [[ "${vlink}" != /* ]]
  [[ "${vlink}" == ../* ]]
  [[ -e "${MODELS_DIR}/comfy/vae/LTX23_video_vae_bf16.safetensors" ]]

  # Gemma companion from Comfy-Org split_files layout
  gdir="$(tier_dir gemma)"
  mkdir -p "${gdir}/split_files/text_encoders"
  echo g >"${gdir}/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"
  run link_into_comfy gemma
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors" ]]
  local glink
  glink="$(readlink "${MODELS_DIR}/comfy/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors")"
  [[ "${glink}" != /* ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors" ]]
}
