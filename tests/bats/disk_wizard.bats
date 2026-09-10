#!/usr/bin/env bats
#
# Hermetic disk-wizard (no GPU, no network, no real $HOME scan).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export DW="${UTILITIES_DIR}/disk-wizard.sh"
  chmod +x "${DW}"
  export DISK_WIZARD_HOME="${TEST_TMP_DIR}/home"
  mkdir -p \
    "${DISK_WIZARD_HOME}/.cache/huggingface/hub" \
    "${DISK_WIZARD_HOME}/.ollama/models" \
    "${MODELS_DIR}/Lightricks__LTX-2.5_2.5" \
    "${MODELS_DIR}/Lightricks__LTX-2.3_2.3" \
    "${MODELS_DIR}/comfy/diffusion_models" \
    "${COMFY_OUTPUT_DIR}"
  echo live >"${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
  echo old >"${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors"
  echo part >"${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors.incomplete"
  ln -sfn "${MODELS_DIR}/missing-target" "${MODELS_DIR}/comfy/diffusion_models/broken.safetensors"
  echo dump >"${MODELS_DIR}/junk.incomplete"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/models.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/disk_scan.sh"
  # shellcheck disable=SC1090
  source "${DW}"
}

teardown() {
  teardown_repo_env
}

@test "disk-wizard functions exist for coverage inventory" {
  local f
  for f in \
    disk_scan_home disk_scan_hermetic disk_allowed_roots disk_root_is_allowed \
    disk_realpath_under_any disk_file_size_bytes disk_skip_dir_name disk_walk_root \
    disk_df_report disk_docker_df disk_docker_in_use disk_hf_pid_present disk_compose_up \
    disk_wizard_usage parse_args disk_is_tty disk_log disk_plan_file disk_catalog_path \
    disk_rank_candidates disk_survey_jsonl disk_survey disk_print_plan disk_wizard_steps \
    disk_apply_guards disk_quarantine_base disk_quarantine_one disk_delete_one \
    disk_apply_one disk_apply disk_restore disk_json_report; do
    type "${f}"
  done
}

@test "disk-wizard --plan lists junk not live 2.5 keep-set" {
  run bash "${DW}" --plan
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"read-only disk survey"* ]]
  [[ "${output}" == *"Scanning"* ]]
  [[ "${output}" == *"Ranking"* ]]
  [[ "${output}" == *"Plan written"* ]]
  [[ "${output}" == *"hf-incomplete"* || "${output}" == *".incomplete"* ]]
  [[ "${output}" == *"junk.incomplete"* || "${output}" == *"incomplete"* ]]
  [[ "${output}" != *"PLAN live"* ]]
}

@test "disk-wizard --json includes step A junk and keep-set as C" {
  run bash "${DW}" --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"hf-incomplete"* ]]
  [[ "${output}" == *"keep-set-weight"* || "${output}" == *"dangerous"* ]]
}

@test "disk-wizard --json stdout is JSON; progress on stderr" {
  local errf stdout
  errf="${TEST_TMP_DIR}/dw.err"
  stdout="$(bash "${DW}" --json 2>"${errf}")"
  python3 -c 'import json,sys; json.load(sys.stdin)' <<<"${stdout}"
  grep -q 'read-only disk survey' "${errf}"
  grep -q 'Scanning' "${errf}"
  grep -q 'Ranking' "${errf}"
  grep -q 'Plan written' "${errf}"
  [[ "${stdout}" == *"hf-incomplete"* ]]
}

@test "disk-wizard --apply without --yes fails" {
  run bash "${DW}" --apply
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"--yes"* ]]
}

@test "disk-wizard --apply --yes deletes incomplete not keep-set" {
  run bash "${DW}" --plan
  [ "${status}" -eq 0 ]
  run bash "${DW}" --apply --yes
  [ "${status}" -eq 0 ]
  [[ ! -e ${MODELS_DIR}/junk.incomplete ]]
  [[ ! -e ${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors.incomplete ]]
  [[ -f ${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors ]]
}

@test "disk-wizard review-class quarantines when STEP_B=1" {
  export DISK_WIZARD_STEP_B=1
  run bash "${DW}" --plan
  [ "${status}" -eq 0 ]
  run bash "${DW}" --apply --yes
  [ "${status}" -eq 0 ]
  [[ ! -e ${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors ]]
  run find "${MODELS_DIR}" "${COMFY_OUTPUT_DIR}" -name 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors'
  [ "${status}" -eq 0 ]
  [[ "${output}" == *".disk-quarantine"* ]]
}

@test "disk-wizard restore --from moves files back" {
  mkdir -p "${MODELS_DIR}/.disk-quarantine/stamp"
  echo x >"${MODELS_DIR}/.disk-quarantine/stamp/restored.bin"
  echo '{}' >"${MODELS_DIR}/.disk-quarantine/stamp/MANIFEST.jsonl"
  run bash "${DW}" restore --from .disk-quarantine/stamp
  [ "${status}" -eq 0 ]
  [[ -f ${MODELS_DIR}/restored.bin ]]
}

@test "disk-wizard refuses path escape on delete" {
  run disk_delete_one junk /etc/passwd
  [ "${status}" -ne 0 ]
}

@test "disk-wizard apply guards refuse hf pid" {
  echo 1 >"${MODELS_DIR}/.hf-download.pid"
  YES=1
  FORCE=0
  run disk_apply_guards
  [ "${status}" -ne 0 ]
}

@test "disk-wizard skip dir names" {
  run disk_skip_dir_name node_modules
  [ "${status}" -eq 0 ]
  run disk_skip_dir_name models
  [ "${status}" -ne 0 ]
}

@test "disk_walk_root prunes nested skip dirs" {
  mkdir -p "${MODELS_DIR}/node_modules/pkg"
  echo x >"${MODELS_DIR}/node_modules/pkg/x.js"
  echo y >"${MODELS_DIR}/ok.bin"
  run disk_walk_root "${MODELS_DIR}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ok.bin"* ]]
  [[ "${output}" != *"x.js"* ]]
}

@test "disk_file_size_bytes uses native stat" {
  printf 'abcd' >"${MODELS_DIR}/sz.bin"
  run disk_file_size_bytes "${MODELS_DIR}/sz.bin"
  [ "${status}" -eq 0 ]
  [[ "${output}" == "4" ]]
}

@test "manage.sh help lists disk-wizard" {
  run bash "${MANAGE_SH}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"disk-wizard"* ]]
}

@test "manage.sh disk-wizard --plan dispatches" {
  run bash "${MANAGE_SH}" disk-wizard --plan
  [ "${status}" -eq 0 ]
}
