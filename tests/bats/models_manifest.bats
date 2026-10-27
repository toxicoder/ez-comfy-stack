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
