#!/usr/bin/env bats
#
# ## download_llm.bats
#
# Cover scripts/utilities/download-llm.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DL="${UTILITIES_DIR}/download-llm.sh"
  chmod +x "${DL}"
  # shellcheck disable=SC1090
  source "${DL}"
}

teardown() {
  teardown_repo_env
}

@test "download-llm CLI help status unknown" {
  run bash "${DL}" --help
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  [[ "${output}" == *"Qwen3-4B-Instruct-2507"* ]]
  run bash "${DL}" status --nope
  [ "${status}" -ne 0 ]
}

@test "download-llm helpers repo filename dir ready" {
  run llm_repo
  [[ "${output}" == "unsloth/Qwen3-4B-Instruct-2507-GGUF" ]]
  run llm_filename
  [[ "${output}" == "Qwen3-4B-Instruct-2507-Q4_K_M.gguf" ]]
  run llm_min_gb
  [ "${output}" = "3" ]
  run llm_include_pattern
  [[ "${output}" == *"Q4_K_M.gguf"* ]]
  run llm_dir
  [[ "${output}" == *"_llm" ]]
  run llm_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
  run llm_files_ready
  [ "${status}" -ne 0 ]
}

@test "download-llm link_llm_into_comfy cmd_status cmd_run mock" {
  local tdir
  tdir="$(llm_dir)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/$(llm_filename)"
  run link_llm_into_comfy
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/llm/$(llm_filename)" ]]
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DL}\" run"
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf" ]]
  LAB_MOCK_HF_DOWNLOAD=fail
  rm -rf "$(llm_dir)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-llm cleanup keeps gguf" {
  local tdir extra
  tdir="$(llm_dir)"
  mkdir -p "${tdir}"
  echo keep >"${tdir}/$(llm_filename)"
  extra="${tdir}/junk.gguf"
  echo waste >"${extra}"
  CLEANUP_YES=1
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ -f ${tdir}/$(llm_filename) ]]
}
