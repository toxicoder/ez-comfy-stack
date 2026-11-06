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

@test "download-image CLI help status fast unknown and banned quality" {
  run bash "${DI}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"9b"* ]]
  [[ "${output}" == *"Non-Commercial"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DI}\" status --tier fast --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  run bash "${DI}" status --nope
  [ "${status}" -ne 0 ]
  run bash "${DI}" run --tier quality
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"banned"* || "${output}" == *"Banned"* || "${output}" == *"quality image tier"* ]]
  run bash "${DI}" run --tier nunchaku
  [ "${status}" -ne 0 ]
}

@test "download-image 9b is opt-in NC not default all" {
  run tier_repo 9b
  [[ "${output}" == *"FLUX.2-klein-9b-fp8"* ]]
  run tier_include_patterns 9b
  [[ "${output}" == *"flux-2-klein-9b-fp8.safetensors"* ]]
  run tier_include_patterns te8b
  [[ "${output}" == *"qwen_3_8b_fp8mixed"* ]]
  run tier_include_patterns small-vae
  [[ "${output}" == *"full_encoder_small_decoder"* ]]
  run is_nc_image_tier 9b
  [ "${status}" -eq 0 ]
  run is_nc_image_tier fast
  [ "${status}" -ne 0 ]
  run warn_flux_nc_image_tier 9b
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Non-Commercial"* ]]
  [[ "${output}" == *"not monetized YouTube"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" != *"9b"* ]]
  [[ "${output}" != *"flux2-dev"* ]]
  TIER=9b
  run tiers_to_process
  [[ "${output}" == *"9b"* && "${output}" == *"te8b"* && "${output}" == *"small-vae"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier 9b"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Non-Commercial"* ]]
  [[ -e "${MODELS_DIR}/comfy/diffusion_models/flux-2-klein-9b-fp8.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen_3_8b_fp8mixed.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/full_encoder_small_decoder.safetensors" ]]
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
  [[ "${output}" == *"══"* ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen_3_4b.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=fast
  rm -rf "$(tier_dir fast)" "$(tier_dir te)" "$(tier_dir vae)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-image cmd_run heals unwritable comfy and links cache hit" {
  local tdir
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}" "${MODELS_DIR}/comfy"
  echo x >"${tdir}/flux-2-klein-4b-fp8.safetensors"
  chmod a-w "${MODELS_DIR}/comfy"
  unset LAB_NO_SUDO
  install_sudo_heal_mock
  TIER=fast
  run cmd_run
  chmod -R u+w "${MODELS_DIR}/comfy" 2>/dev/null || true
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/flux-2-klein-4b-fp8.safetensors" ]]
}

@test "download-image cmd_run heals unwritable comfy child on cache hit" {
  local tdir
  tdir="$(tier_dir fast)"
  mkdir -p "${tdir}" "${MODELS_DIR}/comfy/diffusion_models"
  echo x >"${tdir}/flux-2-klein-4b-fp8.safetensors"
  chmod a-w "${MODELS_DIR}/comfy/diffusion_models"
  unset LAB_NO_SUDO
  install_sudo_heal_mock
  TIER=fast
  run cmd_run
  chmod -R u+w "${MODELS_DIR}/comfy" 2>/dev/null || true
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/flux-2-klein-4b-fp8.safetensors" ]]
}

@test "download-image flux3 tiers are gated opt-in NC on the pinned repo" {
  local t
  for t in flux3 flux3-base flux3-nvfp4 flux3-bf16 flux3-te flux3-pup; do
    run tier_repo "${t}"
    [[ "${output}" == *"black-forest-labs/flux-3-image-klein-comfy"* ]]
    run is_nc_image_tier "${t}"
    [ "${status}" -eq 0 ]
    run warn_flux_nc_image_tier "${t}"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Non-Commercial"* ]]
    [[ "${output}" == *"Kommunity"* ]]
    [[ "${output}" != *"hf_"* ]]
  done
  run tier_include_patterns flux3
  [[ "${output}" == *"diffusion_models/flux3-image-klein-int8-convrot.safetensors"* ]]
  run tier_include_patterns flux3-base
  [[ "${output}" == *"diffusion_models/flux3-image-klein-base-int8-convrot.safetensors"* ]]
  run tier_include_patterns flux3-nvfp4
  [[ "${output}" == *"diffusion_models/flux3-image-klein-base-nvfp4.safetensors"* ]]
  run tier_include_patterns flux3-bf16
  [[ "${output}" == *"diffusion_models/flux3-image-klein-base-bf16.safetensors"* ]]
  run tier_include_patterns flux3-te
  [[ "${output}" == *"text_encoders/qwen3vl_4b_int8_convrot.safetensors"* ]]
  run tier_include_patterns flux3-pup
  [[ "${output}" == *"text_encoders/qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors"* ]]
  run tier_min_gb flux3-bf16
  [ "${output}" = "12" ]
  run tier_min_gb flux3-te
  [ "${output}" = "5" ]
  run tier_min_gb flux3-pup
  [ "${output}" = "10" ]
  run tier_dir flux3-te
  [[ "${output}" == *"black-forest-labs__flux-3-image-klein-comfy_flux3-te"* ]]
  run is_nc_image_tier fast
  [ "${status}" -ne 0 ]
}

@test "download-image flux3 never enters tier all" {
  local t
  TIER=all
  run tiers_to_process
  [[ "${output}" != *"flux3"* ]]
  for t in flux3-base flux3-nvfp4 flux3-bf16 flux3-te flux3-pup; do
    TIER="${t}"
    run tiers_to_process
    [[ "${output}" != *"all"* ]]
  done
  TIER=flux3
  run tiers_to_process
  [ "${output}" = "flux3 flux3-te" ]
  TIER=flux3-bf16
  run tiers_to_process
  [ "${output}" = "flux3-bf16 flux3-te" ]
  TIER=flux3-te
  run tiers_to_process
  [ "${output}" = "flux3-te" ]
  TIER=flux3-pup
  run tiers_to_process
  [ "${output}" = "flux3-pup" ]
}

@test "download-image flux3 parse_args accepts tiers still bans quality" {
  local t
  for t in flux3 flux3-base flux3-nvfp4 flux3-bf16 flux3-te flux3-pup; do
    run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DI}\" status --tier ${t} --json"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"tiers"* ]]
  done
  run bash "${DI}" status --tier flux3-bogus
  [ "${status}" -ne 0 ]
  run bash "${DI}" run --tier quality
  [ "${status}" -ne 0 ]
  run bash "${DI}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux3-te"* ]]
  [[ "${output}" == *"Kommunity"* ]]
}

@test "download-image run --tier flux3 links diffusion_models and text_encoders" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier flux3"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Kommunity"* ]]
  [[ -e "${MODELS_DIR}/comfy/diffusion_models/flux3-image-klein-int8-convrot.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen3vl_4b_int8_convrot.safetensors" ]]
  [[ ! -e "${MODELS_DIR}/comfy/diffusion_models/flux3-image-klein-base-bf16.safetensors" ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier flux3-pup"
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors" ]]
}

@test "download-image flux3 gated failure exits non-zero with guidance" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=fail-gated bash \"${DI}\" run --tier flux3"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"gated"* || "${output}" == *"Gated"* || "${output}" == *"Agree"* ]]
  [[ "${output}" == *"flux-3-image-klein-comfy"* ]]
  [[ ! -e "${MODELS_DIR}/comfy/diffusion_models/flux3-image-klein-int8-convrot.safetensors" ]]
}

@test "download-image flux3 pins HF revision 9b does not" {
  run tier_revision flux3
  [ "${output}" = "feef60b0aaf63a4773ace96636ebbcf43b881312" ]
  run tier_revision flux3-pup
  [ "${output}" = "feef60b0aaf63a4773ace96636ebbcf43b881312" ]
  run tier_revision fast
  [ "${output}" = "" ]
  run tier_revision 9b
  [ "${output}" = "" ]
  unset LAB_MOCK_HF_DOWNLOAD
  export HF_PROGRESS=0
  install_mock_bin hf '
if [[ ${2:-} == "--help" ]]; then
  echo "Usage: hf download [OPTIONS] REPO_ID"
  echo "  --revision TEXT   Git revision id"
  echo "  --token TEXT"
  echo "  --local-dir PATH"
  exit 0
fi
echo "hf $*" >>"${TEST_TMP_DIR}/hf_calls.log"
echo "hf $*"
exit 0
'
  : >"${TEST_TMP_DIR}/hf_calls.log"
  run hf_download "black-forest-labs/flux-3-image-klein-comfy" \
    --local-dir "${MODELS_DIR}/rev" --include "diffusion_models/x.safetensors" \
    --revision "$(tier_revision flux3)"
  [ "${status}" -eq 0 ]
  grep -q -- '--revision feef60b0aaf63a4773ace96636ebbcf43b881312' "${TEST_TMP_DIR}/hf_calls.log"
  : >"${TEST_TMP_DIR}/hf_calls.log"
  run hf_download "black-forest-labs/FLUX.2-klein-9b-fp8" \
    --local-dir "${MODELS_DIR}/norev" --include "flux-2-klein-9b-fp8.safetensors" \
    --revision "$(tier_revision 9b)"
  [ "${status}" -eq 0 ]
  ! grep -q -- '--revision' "${TEST_TMP_DIR}/hf_calls.log"
  export LAB_MOCK_HF_DOWNLOAD=1
}

@test "download-image qwen image tiers are opt-in research-license on pinned repos" {
  local t
  for t in qwen-image qwen-image-turbo qwen-image-te qwen-image-vae; do
    run tier_repo "${t}"
    [[ "${output}" == *"Comfy-Org/Qwen-Image-2.1"* ]]
  done
  run tier_repo qwen-image-nvfp4
  [[ "${output}" == *"BennyDaBall/Qwen-Image-2.1-NVFP4"* ]]
  run tier_repo qwen-image-turbo-nvfp4
  [[ "${output}" == *"BennyDaBall/Qwen-Image-2.1-Turbo-NVFP4"* ]]
  for t in qwen-image qwen-image-turbo qwen-image-nvfp4 qwen-image-turbo-nvfp4 qwen-image-te qwen-image-vae; do
    run is_nc_image_tier "${t}"
    [ "${status}" -eq 0 ]
    run warn_flux_nc_image_tier "${t}"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Qwen Research License"* ]]
    [[ "${output}" == *"Non-Commercial"* ]]
    [[ "${output}" == *"Commercial use needs a separate paid license from Qwen"* ]]
    [[ "${output}" == *"Klein 4B"* ]]
    [[ "${output}" == *"docs/licenses.md"* ]]
    [[ "${output}" != *"Gated Hugging Face card"* ]]
  done
  for t in qwen-image-nvfp4 qwen-image-turbo-nvfp4; do
    run warn_flux_nc_image_tier "${t}"
    [[ "${output}" == *"conversion"* ]]
  done
  run is_nc_image_tier fast
  [ "${status}" -ne 0 ]
}

@test "download-image qwen image repo min dir and includes are selective" {
  run tier_include_patterns qwen-image
  [ "${output}" = "diffusion_models/qwen_image_2.1_int8_convrot.safetensors" ]
  run tier_include_patterns qwen-image-turbo
  [ "${output}" = "diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors" ]
  run tier_include_patterns qwen-image-te
  [ "${output}" = "text_encoders/qwen3vl_8b_int8_convrot.safetensors" ]
  run tier_include_patterns qwen-image-vae
  [ "${output}" = "vae/qwen_image_2.1_vae_bf16.safetensors" ]
  run tier_include_patterns qwen-image-nvfp4
  [ "${lines[0]}" = "diffusion_models/qwen_image_2.1_nvfp4.safetensors" ]
  [ "${lines[1]}" = "text_encoders/qwen3vl_8b_nvfp4.safetensors" ]
  run tier_include_patterns qwen-image-turbo-nvfp4
  [ "${lines[0]}" = "diffusion_models/qwen_image_2.1_turbo_nvfp4.safetensors" ]
  [ "${lines[1]}" = "text_encoders/qwen3vl_8b_turbo_nvfp4.safetensors" ]
  run tier_min_gb qwen-image
  [ "${output}" = "8" ]
  run tier_min_gb qwen-image-turbo
  [ "${output}" = "8" ]
  run tier_min_gb qwen-image-nvfp4
  [ "${output}" = "12" ]
  run tier_min_gb qwen-image-turbo-nvfp4
  [ "${output}" = "15" ]
  run tier_min_gb qwen-image-te
  [ "${output}" = "10" ]
  run tier_min_gb qwen-image-vae
  [ "${output}" = "1" ]
  run tier_dir qwen-image
  [ "${output}" = "${MODELS_DIR}/Comfy-Org__Qwen-Image-2.1_qwen-image" ]
  run tier_dir qwen-image-nvfp4
  [ "${output}" = "${MODELS_DIR}/BennyDaBall__Qwen-Image-2.1-NVFP4_qwen-image-nvfp4" ]
}

@test "download-image qwen image never enters tier all" {
  local t
  TIER=all
  run tiers_to_process
  [[ "${output}" != *"qwen"* ]]
  [[ "${output}" == *"fast"* ]]
  for t in qwen-image qwen-image-turbo qwen-image-nvfp4 qwen-image-turbo-nvfp4 qwen-image-te qwen-image-vae; do
    TIER="${t}"
    run tiers_to_process
    [[ "${output}" != *"all"* ]]
  done
}

@test "download-image qwen image companions pull te plus vae and nvfp4 pulls vae only" {
  TIER=qwen-image
  run tiers_to_process
  [ "${output}" = "qwen-image qwen-image-te qwen-image-vae" ]
  TIER=qwen-image-turbo
  run tiers_to_process
  [ "${output}" = "qwen-image-turbo qwen-image-te qwen-image-vae" ]
  TIER=qwen-image-nvfp4
  run tiers_to_process
  [ "${output}" = "qwen-image-nvfp4 qwen-image-vae" ]
  [[ "${output}" != *"qwen-image-te"* ]]
  TIER=qwen-image-turbo-nvfp4
  run tiers_to_process
  [ "${output}" = "qwen-image-turbo-nvfp4 qwen-image-vae" ]
  [[ "${output}" != *"qwen-image-te"* ]]
  TIER=qwen-image-te
  run tiers_to_process
  [ "${output}" = "qwen-image-te" ]
  TIER=qwen-image-vae
  run tiers_to_process
  [ "${output}" = "qwen-image-vae" ]
}

@test "download-image qwen image parse_args accepts tiers still rejects unknown" {
  local t
  for t in qwen-image qwen-image-turbo qwen-image-nvfp4 qwen-image-turbo-nvfp4 qwen-image-te qwen-image-vae; do
    run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DI}\" status --tier ${t} --json"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"tiers"* ]]
  done
  run bash "${DI}" status --tier qwen-image-bogus
  [ "${status}" -ne 0 ]
  run bash "${DI}" status --tier qwen
  [ "${status}" -ne 0 ]
  run bash "${DI}" run --tier quality
  [ "${status}" -ne 0 ]
  run bash "${DI}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"qwen-image-te"* ]]
  [[ "${output}" == *"Qwen Research License"* ]]
}

@test "download-image qwen image nvfp4 includes never match manifest sidecars" {
  local tdir sidecar
  for t in qwen-image-nvfp4 qwen-image-turbo-nvfp4; do
    run tier_include_patterns "${t}"
    [[ "${output}" != *".manifest.json"* ]]
    run is_ltx_keep_relpath "${t}" "diffusion_models/qwen_image_2.1_nvfp4.manifest.json"
    [ "${status}" -ne 0 ]
  done
  tdir="$(tier_dir qwen-image-nvfp4)"
  mkdir -p "${tdir}/diffusion_models"
  echo keep >"${tdir}/diffusion_models/qwen_image_2.1_nvfp4.safetensors"
  sidecar="${tdir}/diffusion_models/qwen_image_2.1_nvfp4.manifest.json"
  echo waste >"${sidecar}"
  run list_extra_ltx_files qwen-image-nvfp4
  [[ "${output}" == *"${sidecar}"* ]]
  CLEANUP_YES=1
  TIER=qwen-image-nvfp4
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${sidecar} ]]
  [[ -f ${tdir}/diffusion_models/qwen_image_2.1_nvfp4.safetensors ]]
}

@test "download-image qwen image pins HF revisions 9b does not" {
  local t sha
  run tier_revision qwen-image
  [ "${output}" = "aacf31a6d48e707f352ecba714cee0680da3479b" ]
  run tier_revision qwen-image-turbo
  [ "${output}" = "aacf31a6d48e707f352ecba714cee0680da3479b" ]
  run tier_revision qwen-image-te
  [ "${output}" = "aacf31a6d48e707f352ecba714cee0680da3479b" ]
  run tier_revision qwen-image-vae
  [ "${output}" = "aacf31a6d48e707f352ecba714cee0680da3479b" ]
  run tier_revision qwen-image-nvfp4
  [ "${output}" = "b0e954a1ba86f00e30f76bac2494f45b0a221948" ]
  run tier_revision qwen-image-turbo-nvfp4
  [ "${output}" = "82226d8cadaf20a678338f8faf5e5a0cfc3e1dfd" ]
  for t in qwen-image qwen-image-turbo qwen-image-nvfp4 qwen-image-turbo-nvfp4 qwen-image-te qwen-image-vae; do
    run tier_revision "${t}"
    sha="${output}"
    [ "${#sha}" -eq 40 ]
    printf '%s' "${sha}" | grep -Eq '^[0-9a-f]{40}$'
  done
  run tier_revision fast
  [ "${output}" = "" ]
  run tier_revision 9b
  [ "${output}" = "" ]
  unset LAB_MOCK_HF_DOWNLOAD
  export HF_PROGRESS=0
  install_mock_bin hf '
if [[ ${2:-} == "--help" ]]; then
  echo "Usage: hf download [OPTIONS] REPO_ID"
  echo "  --revision TEXT   Git revision id"
  echo "  --token TEXT"
  echo "  --local-dir PATH"
  exit 0
fi
echo "hf $*" >>"${TEST_TMP_DIR}/hf_calls.log"
echo "hf $*"
exit 0
'
  : >"${TEST_TMP_DIR}/hf_calls.log"
  run hf_download "BennyDaBall/Qwen-Image-2.1-NVFP4" \
    --local-dir "${MODELS_DIR}/rev" --include "diffusion_models/x.safetensors" \
    --revision "$(tier_revision qwen-image-nvfp4)"
  [ "${status}" -eq 0 ]
  grep -q -- '--revision b0e954a1ba86f00e30f76bac2494f45b0a221948' "${TEST_TMP_DIR}/hf_calls.log"
  export LAB_MOCK_HF_DOWNLOAD=1
}

@test "download-image run --tier qwen image links all three model dirs" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier qwen-image"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen Research License"* ]]
  [[ -e "${MODELS_DIR}/comfy/diffusion_models/qwen_image_2.1_int8_convrot.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen3vl_8b_int8_convrot.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/qwen_image_2.1_vae_bf16.safetensors" ]]
  [[ ! -e "${MODELS_DIR}/comfy/diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors" ]]
  [[ ! -d "$(tier_dir qwen-image-nvfp4)" ]]
}

@test "download-image run --tier qwen image turbo nvfp4 carries its own text encoder" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DI}\" run --tier qwen-image-turbo-nvfp4"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen Research License"* ]]
  [[ "${output}" == *"conversion"* ]]
  [[ -e "${MODELS_DIR}/comfy/diffusion_models/qwen_image_2.1_turbo_nvfp4.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/text_encoders/qwen3vl_8b_turbo_nvfp4.safetensors" ]]
  [[ -e "${MODELS_DIR}/comfy/vae/qwen_image_2.1_vae_bf16.safetensors" ]]
  [[ ! -e "${MODELS_DIR}/comfy/text_encoders/qwen3vl_8b_int8_convrot.safetensors" ]]
  [[ ! -d "$(tier_dir qwen-image-te)" ]]
}

@test "download-image qwen image usage tier lists match the accepted tiers" {
  local a b c t
  a=$(grep -m1 -oE '\[--tier fast\|[^]]*\]' "${DI}")
  b=$(grep -m2 -oE '\[--tier fast\|[^]]*\]' "${DI}" | sed -n '2p')
  c=$(grep -m3 -oE '\[--tier fast\|[^]]*\]' "${DI}" | sed -n '3p')
  [ -n "${a}" ]
  [ "${a}" = "${b}" ]
  [ "${b}" = "${c}" ]
  for t in qwen-image qwen-image-turbo qwen-image-nvfp4 qwen-image-turbo-nvfp4 qwen-image-te qwen-image-vae; do
    [[ "${a}" == *"${t}"* ]]
    run bash "${DI}" --help
    [[ "${output}" == *"${t}"* ]]
  done
  run bash "${DI}" --help
  [[ "${output}" == *"kitchen-sink"* || "${output}" == *"all"* ]]
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
