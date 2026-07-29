#!/usr/bin/env bats
#
# ## workflow.bats
#
# Purpose:
#   Guard lab ComfyUI workflows track stack model basenames, use correct
#   Flux.2 Klein node types, stay free of Z-Image templates, and avoid
#   optional third-party nodes not installed by this stack.
#

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "lab workflows parse and use stack models not Z-Image" {
  local wf dir="${REPO_ROOT}/workflows"
  local n=0
  shopt -s nullglob
  local -a files=("${dir}"/lab-*.json)
  shopt -u nullglob
  [[ ${#files[@]} -ge 10 ]]

  for wf in "${files[@]}"; do
    n=$((n + 1))
    [[ -f ${wf} ]]
    run python3 -c "import json; json.load(open('${wf}'))"
    [ "${status}" -eq 0 ]
    # No Z-Image pack basenames as model widgets
    run grep -E 'z_image_turbo|qwen_3_4b|"ae\.safetensors"' "${wf}"
    [ "${status}" -ne 0 ]
    # No optional VHS (not installed by install-comfy.sh)
    run grep -F 'VHS_VideoCombine' "${wf}"
    [ "${status}" -ne 0 ]
  done
  [[ ${n} -ge 10 ]]
}

@test "flux lab graphs use flux2 CLIP EmptyFlux2Latent and stack weights" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in \
    lab-flux-txt2img.json \
    lab-flux-txt2img-portrait.json \
    lab-flux-txt2img-landscape.json \
    lab-flux-txt2img-quick.json \
    lab-flux-img2img.json \
    lab-flux-to-ltx.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'flux-2-klein-9b-nvfp4.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_3_8b_fp4mixed.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'flux2-vae.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    # CLIP type must be flux2 (not qwen_image)
    run grep -E '"flux2"' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'qwen_image' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
    run grep -F 'KSampler' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
  done

  # Txt2img family uses EmptyFlux2LatentImage (not SD3)
  for wf in \
    lab-flux-txt2img.json \
    lab-flux-txt2img-portrait.json \
    lab-flux-txt2img-landscape.json \
    lab-flux-txt2img-quick.json \
    lab-flux-to-ltx.json; do
    run grep -F 'EmptyFlux2LatentImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'EmptySD3LatentImage' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
  done

  # Geometry / steps variants
  run grep -F '768' "${dir}/lab-flux-txt2img-portrait.json"
  [ "${status}" -eq 0 ]
  run grep -F '1024' "${dir}/lab-flux-txt2img-portrait.json"
  [ "${status}" -eq 0 ]
  run grep -F '1280' "${dir}/lab-flux-txt2img-landscape.json"
  [ "${status}" -eq 0 ]
  run grep -F '720' "${dir}/lab-flux-txt2img-landscape.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_flux_quick' "${dir}/lab-flux-txt2img-quick.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_flux_to_ltx' "${dir}/lab-flux-to-ltx.json"
  [ "${status}" -eq 0 ]
}

@test "ltx lab graphs use balanced FP8 pack and short variants" {
  local dir="${REPO_ROOT}/workflows"
  local wf
  for wf in lab-ltx-i2v.json lab-ltx-i2v-short.json lab-ltx-t2v.json lab-ltx-t2v-short.json; do
    [[ -f ${dir}/${wf} ]]
    run grep -F 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' \
      "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'LTX23_video_vae_bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'ltx-2.3_text_projection_bf16.safetensors' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'KSampler' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
    run grep -F 'SaveImage' "${dir}/${wf}"
    [ "${status}" -eq 0 ]
  done

  # Short demos use 33-frame length in LTX latent widgets
  run python3 -c "import json; d=json.load(open('${dir}/lab-ltx-i2v-short.json'));
assert any(n.get('type')=='LTXVImgToVideo' and n['widgets_values'][2]==33 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run python3 -c "import json; d=json.load(open('${dir}/lab-ltx-t2v-short.json'));
assert any(n.get('type')=='EmptyLTXVLatentVideo' and n['widgets_values'][2]==33 for n in d['nodes'])"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_ltx_i2v_short' "${dir}/lab-ltx-i2v-short.json"
  [ "${status}" -eq 0 ]
  run grep -F 'ez_ltx_t2v_short' "${dir}/lab-ltx-t2v-short.json"
  [ "${status}" -eq 0 ]
}

@test "download-flux companions tier and includes" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/utilities/download-flux.sh"
  run tier_repo companions
  [[ "${output}" == *"Comfy-Org/flux2-klein-9B"* ]]
  run tier_include_patterns companions
  [[ "${output}" == *"qwen_3_8b_fp4mixed"* ]]
  [[ "${output}" == *"flux2-vae"* ]]
  TIER=fast
  INCLUDE_NUNCHAKU=0
  run tiers_to_process
  [[ "${output}" == *"companions"* ]]
  [[ "${output}" == *"fast"* ]]
  # TE-only dir is not ready (regression: size floor skipped VAE)
  local cdir
  cdir="$(tier_dir companions)"
  mkdir -p "${cdir}/split_files/text_encoders"
  echo te >"${cdir}/split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
  run tier_files_ready companions
  [ "${status}" -ne 0 ]
}

@test "lab_expected_model_relpaths matches download-models pack" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/common.sh"
  run lab_expected_model_relpaths
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-2-klein-9b-nvfp4.safetensors"* ]]
  [[ "${output}" == *"qwen_3_8b_fp4mixed.safetensors"* ]]
  [[ "${output}" == *"flux2-vae.safetensors"* ]]
  [[ "${output}" == *"fp8_input_scaled_v3"* ]]
  [[ "${output}" == *"ltx-2.3_text_projection_bf16"* ]]
  [[ "${output}" == *"LTX23_video_vae_bf16"* ]]
  [[ "${output}" == *"LTX23_audio_vae_bf16"* ]]
}
