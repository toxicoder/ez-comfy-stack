#!/usr/bin/env bats
#
# ## workflow.bats
#
# Purpose:
#   Guard the lab ComfyUI workflow so it tracks stack model basenames and
#   never references Z-Image template files.
#

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "lab-flux-to-ltx workflow uses stack models not Z-Image" {
  local wf="${REPO_ROOT}/workflows/lab-flux-to-ltx.json"
  [[ -f ${wf} ]]
  # Valid JSON
  run python3 -c "import json; json.load(open('${wf}'))"
  [ "${status}" -eq 0 ]

  # Stack Flux + LTX basenames present
  run grep -F 'flux-2-klein-9b-nvfp4.safetensors' "${wf}"
  [ "${status}" -eq 0 ]
  run grep -F 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' "${wf}"
  [ "${status}" -eq 0 ]
  run grep -F 'ltx-2.3_text_projection_bf16.safetensors' "${wf}"
  [ "${status}" -eq 0 ]
  run grep -F 'LTX23_video_vae_bf16.safetensors' "${wf}"
  [ "${status}" -eq 0 ]
  run grep -F 'LTX23_audio_vae_bf16.safetensors' "${wf}"
  [ "${status}" -eq 0 ]

  # Must not pull operators into Z-Image missing-model UI
  run grep -E 'z_image_turbo|qwen_3_4b|"ae\.safetensors"' "${wf}"
  [ "${status}" -ne 0 ]
}
