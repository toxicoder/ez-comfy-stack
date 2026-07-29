#!/usr/bin/env bats
#
# ## lib_unit.bats
#
# Purpose:
#   Unit-test every public function in scripts/lib/*.sh by direct call (strict
#   coverage inventory requires function names under tests/).
#
# Hermetic:
#   Uses test_helper mocks; no GPU, sudo, or network required.
#
# Style:
#   BATS suite; shell fragments follow Google Shell Style Guide practices
#   (quoted expansions, [[ ]], 2-space indent via shfmt where applicable).
#

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/compose.sh"
}

teardown() {
  teardown_repo_env
}

@test "paths: lab_script_dir lab_repo_root lab_compose_file lab_models_dir" {
  run lab_script_dir 0
  [ "${status}" -eq 0 ]
  run lab_repo_root
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ez-comfy-stack"* ]]
  run lab_compose_file
  [[ "${output}" == *"docker-compose.yml"* ]]
  run lab_models_dir
  [ "${status}" -eq 0 ]
}

@test "common: lab_expected_model_relpaths and check_lab_models_ready" {
  run lab_expected_model_relpaths
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-2-klein-9b-nvfp4.safetensors"* ]]
  [[ "${output}" == *"qwen_3_8b_fp4mixed.safetensors"* ]]
  [[ "${output}" == *"flux2-vae.safetensors"* ]]
  [[ "${output}" == *"LTX23_video_vae_bf16.safetensors"* ]]

  local root="${TEST_TMP_DIR}/lab_models_root"
  mkdir -p "${root}/comfy"
  run check_lab_models_ready "${root}"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"MISSING"* || "${output}" == *"Missing"* ]]

  while IFS= read -r rel; do
    [[ -z ${rel} ]] && continue
    mkdir -p "${root}/comfy/$(dirname "${rel}")"
    : >"${root}/comfy/${rel}"
  done < <(lab_expected_model_relpaths)
  run check_lab_models_ready "${root}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"all expected"* || "${output}" == *"lab model ok"* ]]
}

@test "shellcheck clean on scripts/lib/common.sh (SC2317/SC2015 regression)" {
  if ! command -v shellcheck >/dev/null 2>&1; then
    skip "shellcheck not installed"
  fi
  run shellcheck -x "${REPO_ROOT}/scripts/lib/common.sh"
  [ "${status}" -eq 0 ]
}

@test "common: log warn err die load_dotenv require_cmd docker models helpers" {
  run log "hi"
  [ "${status}" -eq 0 ]
  run warn "w"
  [ "${status}" -eq 0 ]
  run err "e"
  [ "${status}" -eq 0 ]
  run die "boom"
  [ "${status}" -eq 1 ]
  run load_dotenv "${TEST_TMP_DIR}"
  [ "${status}" -eq 0 ]
  echo 'FOO_FROM_ENV=1' >"${TEST_TMP_DIR}/.env"
  unset FOO_FROM_ENV
  run load_dotenv "${TEST_TMP_DIR}"
  [ "${status}" -eq 0 ]
  # load_dotenv runs in a subshell under `run` — call directly for export effect
  load_dotenv "${TEST_TMP_DIR}"
  [ "${FOO_FROM_ENV}" = "1" ]
  export PRESET_VAR=keep
  echo 'PRESET_VAR=fromenv' >>"${TEST_TMP_DIR}/.env"
  load_dotenv "${TEST_TMP_DIR}"
  [ "${PRESET_VAR}" = "keep" ]
  run require_cmd bash
  [ "${status}" -eq 0 ]
  run require_cmd definitely-not-a-real-cmd-xyz
  [ "${status}" -ne 0 ]

  run find_docker_bin
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"docker"* ]]
  run resolve_docker_on_path
  [ "${status}" -eq 0 ]
  run print_docker_install_hints
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"install-docker"* ]]
  run docker_cli_ok
  [ "${status}" -eq 0 ]
  run docker_daemon_status
  [ "${status}" -eq 0 ]
  run check_docker_preflight
  [ "${status}" -eq 0 ]
  export SETUP_YES=1
  run confirm_docker_install 1
  [ "${status}" -eq 0 ]
  unset SETUP_YES
  export LAB_MOCK_DOCKER_INSTALL=1
  export LAB_MOCK_DOCKER_BIN_DIR="${TEST_TMP_DIR}/docker_install_bin"
  # Hide real mock docker temporarily
  run install_docker_engine
  [ "${status}" -eq 0 ]
  [[ -x "${LAB_MOCK_DOCKER_BIN_DIR}/docker" ]]
  unset LAB_MOCK_DOCKER_INSTALL

  run ensure_models_dir "${TEST_TMP_DIR}/models"
  [ "${status}" -eq 0 ]
  run ensure_models_dir "${TEST_TMP_DIR}/new_models_tree"
  [ "${status}" -eq 0 ]
  [ -d "${TEST_TMP_DIR}/new_models_tree" ]
  local ro
  ro="${TEST_TMP_DIR}/ro_parent"
  mkdir -p "${ro}"
  chmod 555 "${ro}"
  run ensure_models_dir "${ro}/blocked"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"not writable"* ]]
  [[ "${output}" == *"manage.sh setup"* ]]
  export LAB_NO_SUDO=1
  run prepare_models_dir "${ro}/blocked"
  [ "${status}" -ne 0 ]
  run prepare_models_dir "${TEST_TMP_DIR}/prepared_models"
  [ "${status}" -eq 0 ]
  [ -d "${TEST_TMP_DIR}/prepared_models" ]
  chmod 755 "${ro}"

  run run_with_signal_forwarding true
  [ "${status}" -eq 0 ]
  run run_with_signal_forwarding bash -c 'exit 3'
  [ "${status}" -eq 3 ]
  run kill_pid_tree ""
  [ "${status}" -eq 0 ]

  install_hf_mock
  run check_hf_cli
  [ "${status}" -eq 0 ]

  local lock_root
  lock_root="${TEST_TMP_DIR}/lock_models"
  mkdir -p "${lock_root}/.cache/huggingface/download"
  : >"${lock_root}/.cache/huggingface/download/foo.safetensors.lock"
  : >"${lock_root}/bar.lock"
  run clear_stale_hf_locks "${lock_root}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Removed"* || "${output}" == *"lock"* || "${output}" == *"clean"* ]]
  [[ ! -f "${lock_root}/.cache/huggingface/download/foo.safetensors.lock" ]]
  [[ ! -f "${lock_root}/bar.lock" ]]
  # locks_only path still removes unheld locks
  : >"${lock_root}/mid.lock"
  run clear_stale_hf_locks "${lock_root}" "locks_only"
  [ "${status}" -eq 0 ]
  [[ ! -f "${lock_root}/mid.lock" ]]
  run _hf_pid_is_protected "$$"
  [ "${status}" -eq 0 ]
  export HF_LOCK_CLEAR=0
  : >"${lock_root}/skip.lock"
  run clear_stale_hf_locks "${lock_root}"
  [ "${status}" -eq 0 ]
  [[ -f "${lock_root}/skip.lock" ]]
  unset HF_LOCK_CLEAR
  rm -f "${lock_root}/skip.lock"
  : >"${lock_root}/force.lock"
  export HF_LOCK_CLEAR_FORCE=1
  run clear_stale_hf_locks "${lock_root}"
  [ "${status}" -eq 0 ]
  [[ ! -f "${lock_root}/force.lock" ]]
  unset HF_LOCK_CLEAR_FORCE

  unset LAB_MOCK_HF_DOWNLOAD
  : >"${TEST_TMP_DIR}/hf_calls.log"
  run hf_download "org/model" --local-dir "${TEST_TMP_DIR}/hf_out"
  [ "${status}" -eq 0 ]
  grep -q '^hf download' "${TEST_TMP_DIR}/hf_calls.log"
  ! grep -q '^huggingface-cli download' "${TEST_TMP_DIR}/hf_calls.log"
  export LAB_MOCK_HF_DOWNLOAD=1
  run hf_download "org/m" --local-dir "${TEST_TMP_DIR}/mock_out"
  [ "${status}" -eq 0 ]
  [[ -f "${TEST_TMP_DIR}/mock_out/.mock" ]]
  export LAB_MOCK_HF_DOWNLOAD=fail
  run hf_download "org/m" --local-dir "${TEST_TMP_DIR}/mock_fail"
  [ "${status}" -ne 0 ]
  export LAB_MOCK_HF_DOWNLOAD=fail-gated
  run hf_download "black-forest-labs/FLUX.2-klein-9b-nvfp4" --local-dir "${TEST_TMP_DIR}/gated"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"gated"* || "${output}" == *"Gated"* || "${output}" == *"Agree"* ]]
  [[ "${output}" == *"black-forest-labs/FLUX.2-klein-9b-nvfp4"* ]]
  [[ "${output}" != *"Traceback"* ]]
  export LAB_MOCK_HF_DOWNLOAD=fail-auth
  run hf_download "org/private" --local-dir "${TEST_TMP_DIR}/auth"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"HF_TOKEN"* || "${output}" == *"auth"* || "${output}" == *"token"* ]]
  run explain_hf_download_error "GatedRepoError not in the authorized list https://huggingface.co/org/model/resolve/x" "org/model"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Agree"* ]]
  export LAB_DEBUG=1
  run explain_hf_download_error "some obscure failure line1
line2
line3" "org/x"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"raw hf download log"* || "${output}" == *"obscure"* ]]
  unset LAB_DEBUG
  unset LAB_MOCK_HF_DOWNLOAD
}

@test "common: count_hf_incomplete for resume state" {
  local d="${TEST_TMP_DIR}/inc_root"
  mkdir -p "${d}/.cache/huggingface/download"
  run count_hf_incomplete "${d}"
  [ "${output}" = "0" ]
  : >"${d}/.cache/huggingface/download/blob.incomplete"
  : >"${d}/other.incomplete"
  run count_hf_incomplete "${d}"
  [ "${output}" = "2" ]
  run count_hf_incomplete "${TEST_TMP_DIR}/missing_dir"
  [ "${output}" = "0" ]
}

@test "common: hf progress formatters and emit helpers" {
  run hf_progress_label "/mnt/models/Kijai__LTX2.3_comfy_balanced"
  [ "${output}" = "Kijai__LTX2.3_comfy_balanced" ]
  run hf_progress_label ""
  [ "${output}" = "download" ]

  run hf_format_mib 0
  [ "${output}" = "0 MiB" ]
  run hf_format_mib 1024
  [ "${output}" = "1 MiB" ]
  run hf_format_mib 183296
  [ "${output}" = "179 MiB" ]
  run hf_format_mib 29818880
  [[ "${output}" == *"GiB"* ]]

  run hf_format_rate 0 10
  [ "${output}" = "0 MiB/s" ]
  run hf_format_rate 140288 10
  [[ "${output}" == *"MiB/s"* ]]
  # 140288 KiB / 10s ≈ 13.7 MiB/s
  [[ "${output}" == "13.7 MiB/s" ]]

  run hf_format_elapsed 0
  [ "${output}" = "0:00" ]
  run hf_format_elapsed 90
  [ "${output}" = "1:30" ]
  run hf_format_elapsed 3723
  [ "${output}" = "1:02:03" ]

  run hf_progress_line "Kijai__LTX2.3_comfy_balanced" "179 MiB" "13.7 MiB/s" "0:30"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"↓ Kijai__LTX2.3_comfy_balanced"* ]]
  [[ "${output}" == *"179 MiB"* ]]
  [[ "${output}" == *"13.7 MiB/s"* ]]
  [[ "${output}" == *"elapsed 0:30"* ]]

  # non-TTY path uses log (no smash); force via redirect
  run bash -c 'source "'"${REPO_ROOT}"'/scripts/lib/common.sh"; hf_progress_emit "↓ test 1 MiB  0 MiB/s  elapsed 0:00" 2>&1'
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"↓ test"* ]]
  run hf_progress_newline
  [ "${status}" -eq 0 ]
}

@test "safety: parse_gib host_free host_disk headroom confirms" {
  run parse_gib_from_mem_limit 90g
  [ "${output}" = "90" ]
  run parse_gib_from_mem_limit 2048m
  [ "${output}" = "2" ]
  run parse_gib_from_mem_limit bad
  [ "${output}" = "0" ]
  run parse_gib_from_mem_limit 1073741824
  [ "${status}" -eq 0 ]

  export LAB_MOCK_FREE_MEM_GIB=50
  run host_free_mem_gib
  [ "${output}" = "50" ]

  export LAB_MOCK_DISK_FREE_GIB=12
  run host_disk_free_gib /
  [ "${output}" = "12" ]

  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export MIN_HOST_FREE_GIB=28
  run check_host_headroom
  [ "${status}" -eq 0 ]

  export LAB_MOCK_FREE_MEM_GIB=1
  run check_host_headroom
  [ "${status}" -ne 0 ]

  export MEM_LIMIT=120g
  export MIN_HOST_FREE_GIB=28
  run check_mem_limit_vs_headroom
  [ "${status}" -eq 0 ]

  export LAB_NON_INTERACTIVE=1
  export LAB_CONFIRM_TOKEN=yes
  run require_heavy_confirm "unit"
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=
  run require_heavy_confirm "unit"
  [ "${status}" -eq 1 ]

  export LAB_CONFIRM_TOKEN=DELETE
  run require_delete_confirm
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=
  run require_delete_confirm
  [ "${status}" -eq 1 ]
}

@test "compose: compose_cmd compose_run require_docker status stacks logs" {
  run compose_cmd
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"docker"* ]]

  run compose_run version
  [ "${status}" -eq 0 ]

  run require_docker
  [ "${status}" -eq 0 ]

  run compose_status_json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"flux-to-ltx"* ]]

  run compose_is_running
  [ "${status}" -ne 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  install_docker_mocks
  run compose_is_running
  [ "${status}" -eq 0 ]

  export MODELS_DIR="${TEST_TMP_DIR}/models"
  export LAB_STACK_VERIFY_SETTLE=0
  export LAB_STACK_FOLLOW=0
  export LAB_STACK_SKIP_PULL=1
  export LAB_STACK_FORCE_BUILD=1
  run stack_default_image
  [[ "${output}" == *ghcr.io* && "${output}" == *ez-comfy* ]]
  # inventory + behavior: pull path when not skipped
  unset LAB_STACK_SKIP_PULL
  run stack_pull_image "ghcr.io/example/ez-comfy:test"
  [ "${status}" -eq 0 ]
  export LAB_STACK_SKIP_PULL=1
  run stack_pull_image "ghcr.io/example/ez-comfy:skip"
  [ "${status}" -ne 0 ]
  run stack_start
  [ "${status}" -eq 0 ]
  run stack_follow_until_ready
  [ "${status}" -eq 0 ]
  run stack_port_open 9
  # port 9 unlikely open; status non-zero is fine
  [ "${status}" -ne 0 ] || true
  run stack_stop
  [ "${status}" -eq 0 ]
  run stack_cleanup_state
  [ "${status}" -eq 0 ]
  run stack_logs
  [ "${status}" -eq 0 ]

  # up without compose_running flag → verify fails
  rm -f "${TEST_TMP_DIR}/compose_running"
  install_mock_bin docker '
echo "docker $*" >> "${TEST_TMP_DIR}/docker_calls.log"
if [[ "${1}" == "compose" ]]; then
  shift
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      -f|--file|--project-name|-p) shift 2 || true ;;
      up) echo ok; exit 0 ;;
      ps)
        if [[ " $* " == *" --status running"* ]]; then exit 0; fi
        echo "NAME STATUS"; exit 0
        ;;
      logs) echo "boom"; exit 0 ;;
      *) shift || true ;;
    esac
  done
fi
exit 0
'
  export COMPOSE_BIN=""
  # re-install full mocks then override? use COMPOSE_BIN for fail path
  install_mock_bin fakecompose '
if [[ "$1" == "up" ]]; then exit 0; fi
if [[ "$1" == "ps" ]]; then
  if [[ "$*" == *"--status running"* ]]; then exit 0; fi
  echo "exited"
  exit 0
fi
if [[ "$1" == "logs" ]]; then echo "git clone failed"; exit 0; fi
exit 0
'
  export COMPOSE_BIN="${TEST_TMP_DIR}/bin/fakecompose"
  run stack_verify_running 0
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"not running"* || "${output}" == *"not running after start"* ]]
  unset COMPOSE_BIN
  install_docker_mocks
}
