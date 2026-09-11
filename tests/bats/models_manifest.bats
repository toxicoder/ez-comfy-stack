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
