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
  run llm35_repo
  [[ "${output}" == "unsloth/Qwen3.6-35B-A3B-MTP-GGUF" ]]
  run llm35_include_pattern
  [[ "${output}" == *"UD-Q4_K_XL.gguf"* ]]
  run llm35_files_ready
  [ "${status}" -ne 0 ]
  run type cleanup_one_dir
  [ "${status}" -eq 0 ]
  run type link_llm35_into_comfy
  [ "${status}" -eq 0 ]
  run type run_one_tier
  [ "${status}" -eq 0 ]
  run type tier_status_json
  [ "${status}" -eq 0 ]
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

@test "download-llm link heals comfy/llm relative symlink" {
  local tdir dest tgt
  tdir="$(llm_dir)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/$(llm_filename)"
  dest="${MODELS_DIR}/comfy/llm/$(llm_filename)"
  run cmd_link
  [ "${status}" -eq 0 ]
  [[ -L ${dest} ]]
  tgt="$(readlink "${dest}")"
  [[ ${tgt} != /* ]]
  rm -f "${dest}"
  run bash "${DL}" link
  [ "${status}" -eq 0 ]
  [[ -L ${dest} ]]
}

@test "download-llm link is quiet when comfy/llm is not writable but dest exists" {
  local tdir dest lldir
  tdir="$(llm_dir)"
  lldir="${MODELS_DIR}/comfy/llm"
  dest="${lldir}/$(llm_filename)"
  mkdir -p "${tdir}" "${lldir}"
  echo x >"${tdir}/$(llm_filename)"
  run cmd_link
  [ "${status}" -eq 0 ]
  [[ -L ${dest} ]]
  chmod a-w "${lldir}"
  run cmd_link
  chmod u+w "${lldir}"
  [ "${status}" -eq 0 ]
  [[ "${output}" != *"failed to link"* ]]
  [[ "${output}" != *"Permission denied"* ]]
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

@test "download-llm --tier enhance or default reports 4B not 35B" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen3-4B-Instruct-2507"* ]]
  [[ "${output}" != *"Qwen3.6-35B-A3B"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier enhance --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen3-4B-Instruct-2507"* ]]
  [[ "${output}" == *"enhance"* ]]
}

@test "download-llm --tier qwen36-35b-a3b status missing ready false" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" status --tier qwen36-35b-a3b --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"unsloth/Qwen3.6-35B-A3B-MTP-GGUF"* ]]
  [[ "${output}" == *"Qwen3.6-35B-A3B"* ]]
  [[ "${output}" == *'"ready":false'* || "${output}" == *'"ready": false'* ]]
  run llm35_filename
  [[ "${output}" == "Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf" ]]
  run llm35_min_gb
  [ "${output}" = "23" ]
  run llm35_dir
  [[ "${output}" == *"unsloth__Qwen3.6-35B-A3B-MTP-GGUF_llm-35b" ]]
}

@test "download-llm unknown and banned tiers exit 1" {
  run bash "${DL}" status --tier nope
  [ "${status}" -eq 1 ]
  run bash "${DL}" run --tier h3
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"Banned"* ]]
  run bash "${DL}" --tier 120b
  [ "${status}" -eq 1 ]
  run bash "${DL}" --tier flash-next
  [ "${status}" -eq 1 ]
  run bash "${DL}" --tier deepseek-v4
  [ "${status}" -eq 1 ]
  run bash "${DL}" --tier minimax
  [ "${status}" -eq 1 ]
  run refuse_banned_llm_tier enhance
  [ "${status}" -eq 0 ]
}

@test "download-llm mock run --tier qwen36-35b-a3b links relative gguf" {
  local dest tgt
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DL}\" run --tier qwen36-35b-a3b"
  [ "${status}" -eq 0 ]
  dest="${MODELS_DIR}/comfy/llm/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
  [[ -e ${dest} ]]
  [[ -L ${dest} ]]
  tgt="$(readlink "${dest}")"
  [[ ${tgt} != /* ]]
  [[ -d "$(llm35_dir)" ]]
}

@test "download-llm cleanup --tier qwen36-35b-a3b keeps XL gguf" {
  local tdir extra
  tdir="$(llm35_dir)"
  mkdir -p "${tdir}"
  echo keep >"${tdir}/$(llm35_filename)"
  extra="${tdir}/junk.gguf"
  echo waste >"${extra}"
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DL}\" cleanup --tier qwen36-35b-a3b --yes"
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ -f ${tdir}/$(llm35_filename) ]]
}

@test "download-llm run with no tier does not pull 35B" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DL}\" run"
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf" ]]
  [[ ! -e "${MODELS_DIR}/comfy/llm/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf" ]]
  [[ ! -d "$(llm35_dir)" ]]
}
