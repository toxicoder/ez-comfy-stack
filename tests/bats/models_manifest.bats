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
