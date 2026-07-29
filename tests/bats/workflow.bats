#!/usr/bin/env bats
#
# ## workflow.bats
#
# Purpose:
#   Guard lab ComfyUI workflows track stack model basenames and stay free of
#   Z-Image template files.
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
  local -a files=(
    lab-flux-txt2img.json
    lab-flux-img2img.json
    lab-ltx-i2v.json
    lab-ltx-t2v.json
    lab-flux-to-ltx.json
  )
  for wf in "${files[@]}"; do
    [[ -f ${dir}/${wf} ]]
    run python3 -c "import json; json.load(open('${dir}/${wf}'))"
    [ "${status}" -eq 0 ]
    # No Z-Image pack basenames as model widgets
    run grep -E 'z_image_turbo|qwen_3_4b|"ae\.safetensors"' "${dir}/${wf}"
    [ "${status}" -ne 0 ]
  done

  # Image graphs need Flux UNET + TE + VAE
  run grep -F 'flux-2-klein-9b-nvfp4.safetensors' "${dir}/lab-flux-txt2img.json"
  [ "${status}" -eq 0 ]
  run grep -F 'qwen_3_8b_fp4mixed.safetensors' "${dir}/lab-flux-txt2img.json"
  [ "${status}" -eq 0 ]
  run grep -F 'flux2-vae.safetensors' "${dir}/lab-flux-txt2img.json"
  [ "${status}" -eq 0 ]
  run grep -F 'KSampler' "${dir}/lab-flux-txt2img.json"
  [ "${status}" -eq 0 ]
  run grep -F 'SaveImage' "${dir}/lab-flux-txt2img.json"
  [ "${status}" -eq 0 ]

  # Video graphs need LTX pack
  run grep -F 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' \
    "${dir}/lab-ltx-i2v.json"
  [ "${status}" -eq 0 ]
  run grep -F 'LTX23_video_vae_bf16.safetensors' "${dir}/lab-ltx-i2v.json"
  [ "${status}" -eq 0 ]
  run grep -F 'KSampler' "${dir}/lab-ltx-i2v.json"
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
}
