#!/usr/bin/env bats
#
# Cover scripts/utilities/llm-sidecar.sh (host llama-server, hermetic mock).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export LS="${UTILITIES_DIR}/llm-sidecar.sh"
  chmod +x "${LS}"
  chmod +x "${UTILITIES_DIR}/download-llm.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/compose.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/occupancy.sh"
}

teardown() {
  teardown_repo_env
}

@test "llm-sidecar helpers exist for coverage inventory" {
  # shellcheck disable=SC1090
  source "${LS}"
  run type sidecar_bind_host
  [ "${status}" -eq 0 ]
  run sidecar_bind_host
  [ "${output}" = "127.0.0.1" ]
  run sidecar_port
  [ "${output}" = "30000" ]
  run sidecar_ctx
  [ "${output}" = "8192" ]
  run sidecar_log_path
  [[ "${output}" == *"llm-sidecar.log"* ]]
  run sidecar_pid_file
  [[ "${output}" == *"llm-sidecar.pid"* ]]
  run sidecar_gguf_path
  [ "${status}" -ne 0 ]
  run type mock_start
  [ "${status}" -eq 0 ]
  run type print_llama_server_hint
  [ "${status}" -eq 0 ]
  run type sidecar_start_allowed
  [ "${status}" -eq 0 ]
  occupancy_write llm-desk false 0 0 0
  run sidecar_start_allowed
  [ "${status}" -eq 0 ]
}

@test "llm-sidecar help and unknown arg" {
  run bash "${LS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"llm-desk"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run bash "${LS}" nope
  [ "${status}" -ne 0 ]
  run bash "${LS}" --nope
  [ "${status}" -ne 0 ]
}

@test "llm-sidecar status --json GGUF missing ready false" {
  occupancy_write idle false 0 0 0
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" bash \"${LS}\" status --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"ready":false'* || "${output}" == *'"ready": false'* ]]
  [[ "${output}" == *'"bind":"127.0.0.1"'* || "${output}" == *'"bind": "127.0.0.1"'* ]]
  [[ "${output}" == *'"occupancy"'* ]]
}

@test "llm-sidecar start without mock exits 1 with host hint" {
  occupancy_write llm-desk false 0 0 0
  unset LAB_MOCK_LLAMA_SERVER
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" LAB_HERMETIC=1 bash \"${LS}\" start"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"llama-server"* ]]
  [[ "${output}" == *"Dockerfile"* || "${output}" == *"host"* ]]
}

@test "llm-sidecar LAB_MOCK start stop status" {
  export LAB_MOCK_LLAMA_SERVER=1
  occupancy_write llm-desk false 0 0 0
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" LAB_MOCK_LLAMA_SERVER=1 bash \"${LS}\" start"
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" LAB_MOCK_LLAMA_SERVER=1 bash \"${LS}\" status --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"bind":"127.0.0.1"'* || "${output}" == *'"bind": "127.0.0.1"'* ]]
  [[ -f "${COMFY_OUTPUT_DIR}/llm-sidecar.pid" ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" bash \"${LS}\" stop"
  [ "${status}" -eq 0 ]
}

@test "llm-sidecar start refused when occupancy is ltx" {
  export LAB_MOCK_LLAMA_SERVER=1
  occupancy_write ltx false 0 0 0
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" LAB_MOCK_LLAMA_SERVER=1 bash \"${LS}\" start"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"ltx"* ]]
}

@test "llm-sidecar status bind is loopback" {
  occupancy_write llm-desk false 0 0 0
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" COMFY_OUTPUT_DIR=\"${COMFY_OUTPUT_DIR}\" bash \"${LS}\" status --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"127.0.0.1"* ]]
  [[ "${output}" != *"0.0.0.0"* ]]
}
