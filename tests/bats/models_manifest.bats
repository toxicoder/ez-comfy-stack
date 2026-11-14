#!/usr/bin/env bats
#
# Cover models-manifest.sh keep-set / status / render.

load 'test_helper'

setup() {
  setup_repo_env
  export MM="${UTILITIES_DIR}/models-manifest.sh"
  chmod +x "${MM}"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/models.sh"
  # shellcheck disable=SC1090
  source "${MM}"
}

teardown() {
  teardown_repo_env
}

@test "models-manifest keep-set status render help" {
  run cmd_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux2-vae.safetensors"* ]]
  [[ "${output}" == *"Qwen3-4B-Instruct-2507-Q4_K_M.gguf"* ]]
  [[ "${output}" == *"Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"* ]]
  run models_default_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen3-4B-Instruct-2507-Q4_K_M.gguf"* ]]
  [[ "${output}" != *"Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"* ]]
  run cmd_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"keep-set"* ]]
  run cmd_render
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"klein-4b-fp8"* ]]
  run bash "${MM}" --help
  [ "${status}" -eq 0 ]
  run bash "${MM}" nope
  [ "${status}" -ne 0 ]
  run models_manifest_path
  [[ "${output}" == *"model-manifest.yaml"* ]]
}

@test "models-manifest includes opt-in llm-qwen36-35b-a3b default false" {
  run cmd_render
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"llm-qwen36-35b-a3b"* ]]
  [[ "${output}" == *"llm-qwen3-4b"* ]]
  run grep -A6 'llm-qwen36-35b-a3b:' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"* ]]
  run grep -E 'MiniMax-H3|FLUX.2-klein-9b' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
}

@test "models-manifest refuses the declined weights that stay banned" {
  # Arete-27B is a 54.7 GB text model with no GGUF and no media lane;
  # MiniMax-H3 is US-excluded for weights and outputs. Both stay in the
  # fail-closed refuse lane. NVIDIA research models moved out of it into the
  # research lane, so they must not appear here.
  run grep -E '^  - (Arete-27B|MiniMax-H3|Inria-3DGS|DA3-LARGE|Pixal3D-as-default)$' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Arete-27B"* ]]
  [[ "${output}" == *"MiniMax-H3"* ]]
  [[ "${output}" != *"Lyra"* ]]
  run models_default_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" != *"Arete"* ]]
}

@test "models-manifest lists NVIDIA research candidates without downloading them" {
  # The research lane is a disclosure list: it tells the operator the license
  # and the permitted use, and it must never feed a download or the keep-set.
  run grep -E '^  (Lyra-2\.0|ArtiFixer|3DGRUT|DVLT):$' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Lyra-2.0"* ]]
  [[ "${output}" == *"ArtiFixer"* ]]
  # Every research row states what the output may be used for.
  run grep -c '^    use: ' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [ "${lines[0]}" -ge 11 ]
  run grep -c '^    license: ' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [ "${lines[0]}" -ge 11 ]
  # And none of it reaches download-models.
  run models_default_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" != *"Lyra"* ]]
  [[ "${output}" != *"artifixer"* ]]
}

@test "models-manifest includes opt-in flux3 klein packs default false" {
  run cmd_render
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux3-klein-distilled-int8"* ]]
  [[ "${output}" == *"flux3-qwen3vl-te"* ]]
  [[ "${output}" == *"flux3-prompt-upsampler"* ]]
  run models_default_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" != *"flux3-image-klein"* ]]
  [[ "${output}" != *"qwen3vl_4b_int8_convrot"* ]]
  run grep -A10 'flux3-klein-distilled-int8:' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"flux3-image-klein-int8-convrot.safetensors"* ]]
  [[ "${output}" == *"download-image --tier flux3"* ]]
  run grep -A6 'flux3-qwen3vl-te:' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"qwen3vl_4b_int8_convrot.safetensors"* ]]
  [[ "${output}" == *"download-image --tier flux3-te"* ]]
}

@test "models-manifest includes opt-in qwen image 2.1 packs default false" {
  run cmd_render
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"qwen-image"* ]]
  [[ "${output}" == *"qwen-image-turbo-nvfp4"* ]]
  [[ "${output}" == *"qwen-image-te"* ]]
  [[ "${output}" == *"qwen-image-vae"* ]]
  run models_default_keep_set
  [ "${status}" -eq 0 ]
  [[ "${output}" != *"qwen_image_2.1"* ]]
  [[ "${output}" != *"qwen3vl_8b"* ]]
  run grep -A10 '  qwen-image:$' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"qwen_image_2.1_int8_convrot.safetensors"* ]]
  [[ "${output}" == *"download-image --tier qwen-image"* ]]
  run grep -A10 '  qwen-image-nvfp4:$' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"qwen_image_2.1_nvfp4.safetensors"* ]]
  [[ "${output}" == *"qwen3vl_8b_nvfp4.safetensors"* ]]
  [[ "${output}" == *"download-image --tier qwen-image-nvfp4"* ]]
  run grep -A6 '  qwen-image-vae:$' "${REPO_ROOT}/config/model-manifest.yaml"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"default: false"* ]]
  [[ "${output}" == *"qwen_image_2.1_vae_bf16.safetensors"* ]]
  [[ "${output}" == *"download-image --tier qwen-image-vae"* ]]
}
