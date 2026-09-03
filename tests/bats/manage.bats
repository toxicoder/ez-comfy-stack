#!/usr/bin/env bats
#
# ## manage.bats
#
# Purpose:
#   Cover scripts/manage.sh CLI and every cmd_* function by direct call after
#   source (strict coverage inventory).
#
# Hermetic:
#   Docker/HF/wondershaper mocks; headroom mocks.
#

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  install_wondershaper_mock
  install_speedtest_mock 100
  install_hf_mock
  chmod +x "${MANAGE_SH}"
  # shellcheck disable=SC1090
  source "${MANAGE_SH}"
  # Re-assert hermetic MODELS_DIR after manage.sh load_dotenv / defaults
  export MODELS_DIR="${TEST_TMP_DIR}/models"
}

teardown() {
  teardown_repo_env
}

@test "manage CLI help unknown doctor status start stop cleanup download" {
  run bash "${MANAGE_SH}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"doctor"* ]]
  [[ "${output}" == *"setup"* ]]
  run bash "${MANAGE_SH}" not-a-command
  [ "${status}" -ne 0 ]
  run bash "${MANAGE_SH}" doctor
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"writable"* || "${output}" == *"Doctor OK"* ]]
  export LAB_MOCK_FREE_MEM_GIB=4
  run bash "${MANAGE_SH}" doctor
  [ "${status}" -ne 0 ]
  unset LAB_MOCK_FREE_MEM_GIB
  export LAB_MOCK_FREE_MEM_GIB=64
  # Unwritable MODELS_DIR is a hard doctor failure
  local ro
  ro="${TEST_TMP_DIR}/ro_mnt"
  mkdir -p "${ro}"
  chmod 555 "${ro}"
  run bash -c "MODELS_DIR=\"${ro}/models\" LAB_MOCK_FREE_MEM_GIB=64 bash \"${MANAGE_SH}\" doctor"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"not writable"* ]]
  # download-models fails early on unwritable MODELS_DIR (parent still 555)
  run bash -c "MODELS_DIR=\"${ro}/models\" DOWNLOAD_LIMIT=off LAB_MOCK_HF_DOWNLOAD=1 bash \"${MANAGE_SH}\" download-models"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"not writable"* ]]
  chmod 755 "${ro}"
  run bash "${MANAGE_SH}" status
  [ "${status}" -eq 0 ]
  run bash "${MANAGE_SH}" status --json
  [ "${status}" -eq 0 ]
  run bash -c "echo no | bash \"${MANAGE_SH}\" start"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Aborted"* ]]
  run bash -c "LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN= bash \"${MANAGE_SH}\" start"
  [ "${status}" -ne 0 ]
  run bash -c "LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes bash \"${MANAGE_SH}\" start"
  [ "${status}" -eq 0 ]
  export LAB_MOCK_FREE_MEM_GIB=1
  run bash -c "LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes bash \"${MANAGE_SH}\" start"
  [ "${status}" -ne 0 ]
  export LAB_MOCK_FREE_MEM_GIB=64
  run bash "${MANAGE_SH}" stop
  [ "${status}" -eq 0 ]
  run bash -c "echo nope | bash \"${MANAGE_SH}\" cleanup"
  [ "${status}" -eq 0 ]
  run bash -c "LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=DELETE bash \"${MANAGE_SH}\" cleanup"
  [ "${status}" -eq 0 ]
  run bash "${MANAGE_SH}" download-limit status --json
  [ "${status}" -eq 0 ]
  run bash -c "DOWNLOAD_LIMIT=off LAB_MOCK_HF_DOWNLOAD=1 bash \"${MANAGE_SH}\" download-models"
  [ "${status}" -eq 0 ]
}

@test "manage setup creates env and models under LAB_NO_SUDO" {
  export LAB_NO_SUDO=1
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  # Hermetic REPO_ROOT is the real repo; use writable MODELS_DIR only
  export MODELS_DIR="${TEST_TMP_DIR}/setup_models"
  # Point dotenv at a temp tree that has .env.example only
  local fake_root
  fake_root="${TEST_TMP_DIR}/fake_repo"
  mkdir -p "${fake_root}"
  cp "${REPO_ROOT}/.env.example" "${fake_root}/.env.example"
  # cmd_setup uses global REPO_ROOT; override for this test
  REPO_ROOT="${fake_root}"
  export REPO_ROOT
  # lab_compose_file will miss compose — doctor will fail compose check.
  # Provide minimal compose path structure for doctor.
  mkdir -p "${fake_root}/docker"
  echo 'services: {}' >"${fake_root}/docker/docker-compose.yml"
  # Re-source paths with new REPO_ROOT or rely on REPO_ROOT export in lab_repo_root
  run cmd_setup
  [ "${status}" -eq 0 ]
  [ -f "${fake_root}/.env" ]
  [ -d "${TEST_TMP_DIR}/setup_models" ]
  [[ "${output}" == *"Setup OK"* || "${output}" == *"Doctor OK"* ]]
}

@test "manage setup --install-docker uses mock install path" {
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export MODELS_DIR="${TEST_TMP_DIR}/models"
  export LAB_MOCK_DOCKER_INSTALL=1
  export LAB_MOCK_DOCKER_BIN_DIR="${TEST_TMP_DIR}/fresh_docker_bin"
  # Host docker may exist (CI); --install-docker + LAB_MOCK_DOCKER_INSTALL must still
  # materialize the mock binary under LAB_MOCK_DOCKER_BIN_DIR.
  run cmd_setup --install-docker --yes
  [ "${status}" -eq 0 ]
  [[ -x "${LAB_MOCK_DOCKER_BIN_DIR}/docker" ]]
  [[ "${output}" == *"LAB_MOCK_DOCKER_INSTALL"* || "${output}" == *"mock docker"* || -x "${LAB_MOCK_DOCKER_BIN_DIR}/docker" ]]
  unset LAB_MOCK_DOCKER_INSTALL
  unset LAB_MOCK_DOCKER_BIN_DIR
}

@test "manage doctor and start heal llm comfy link from snapshot" {
  export MODELS_DIR="${TEST_TMP_DIR}/models"
  local snap dest
  snap="${MODELS_DIR}/unsloth__Qwen3-4B-Instruct-2507-GGUF_llm"
  dest="${MODELS_DIR}/comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
  mkdir -p "${snap}"
  echo x >"${snap}/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
  run ensure_prompt_enhance_gguf
  [ "${status}" -eq 0 ]
  [[ -L ${dest} ]]
  [[ $(readlink "${dest}") != /* ]]
  rm -f "${dest}"
  run cmd_doctor
  [ "${status}" -eq 0 ]
  [[ -L ${dest} ]]
}

@test "manage cmd_* direct: help setup doctor status start stop restart logs download cleanup" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"setup"* ]]
  [[ "${output}" == *"clear-hf-locks"* ]]
  export LAB_NO_SUDO=1
  export MODELS_DIR="${TEST_TMP_DIR}/models"
  run cmd_setup
  [ "${status}" -eq 0 ]
  run cmd_clear_hf_locks
  [ "${status}" -eq 0 ]
  run cmd_doctor
  [ "${status}" -eq 0 ]
  run cmd_status
  [ "${status}" -eq 0 ]
  run cmd_status --json
  [ "${status}" -eq 0 ]
  export LAB_NON_INTERACTIVE=1
  export LAB_CONFIRM_TOKEN=yes
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  run cmd_start
  [ "${status}" -eq 0 ]
  run cmd_stop
  [ "${status}" -eq 0 ]
  run cmd_restart
  [ "${status}" -eq 0 ]
  run cmd_logs
  [ "${status}" -eq 0 ]
  export DOWNLOAD_LIMIT=off
  export LAB_MOCK_HF_DOWNLOAD=1
  run cmd_download_models
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"lab workflow weights ready"* || "${output}" == *"lab model ok"* ]]
  [[ -e "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
  [[ ! -e "${MODELS_DIR}/comfy/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" ]]
  run cmd_help
  [[ "${output}" != *"download-h3"* ]]
  [[ "${output}" != *"farm-h3"* ]]
  [[ "${output}" == *"Refuses MiniMax H3"* ]]
  run cmd_download_models --with-h3
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"US Excluded Territory"* ]]
  run cmd_download_models --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"banned"* || "${output}" == *"US Excluded"* ]]
  # Wipe comfy links only — cache hit + link_into_comfy should restore
  rm -f "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors"
  run cmd_download_models
  [ "${status}" -eq 0 ]
  [[ -e "${MODELS_DIR}/comfy/vae/flux2-vae.safetensors" ]]
  # Gate fails when downloads fail and lab files are gone
  rm -rf "${MODELS_DIR}/comfy" \
    "${MODELS_DIR}/black-forest-labs__FLUX.2-klein-4b-fp8_fast" \
    "${MODELS_DIR}/Comfy-Org__z_image_turbo_te" \
    "${MODELS_DIR}/Comfy-Org__flux2-dev_vae" \
    "${MODELS_DIR}/Comfy-Org__Wan_2.2_ComfyUI_Repackaged_5b" \
    "${MODELS_DIR}/Lightricks__LTX-2.5_2.5"
  export LAB_MOCK_HF_DOWNLOAD=fail
  run cmd_download_models
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"incomplete"* || "${output}" == *"MISSING"* || "${output}" == *"failed"* ]]
  run cmd_download_limit status --json
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=DELETE
  run cmd_cleanup
  [ "${status}" -eq 0 ]
}

@test "download-models --limit accepts manual Mbps and overrides env" {
  export LAB_MOCK_HF_DOWNLOAD=1
  export DOWNLOAD_LIMIT=auto

  run cmd_download_models --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--limit"* ]]
  [[ "${output}" == *"Mbps"* ]]

  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--limit"* ]]

  run cmd_download_models --limit
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"limit"* ]]

  run cmd_download_models --limit nope
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Invalid"* || "${output}" == *"invalid"* || "${output}" == *"limit"* ]]

  run cmd_download_models --limit=-1
  [ "${status}" -ne 0 ]

  run cmd_download_models --limit off
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"DOWNLOAD_LIMIT=off"* || "${output}" == *"saturating"* ]]
  [[ "${output}" == *"lab workflow weights ready"* || "${output}" == *"lab model ok"* ]]

  export DOWNLOAD_LIMIT=auto
  run cmd_download_models --limit 40
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"lab workflow weights ready"* || "${output}" == *"lab model ok"* ]]
}

@test "reset-hf-partials and download-models --drop-incomplete" {
  export LAB_MOCK_HF_DOWNLOAD=1
  mkdir -p "${MODELS_DIR}/.cache/huggingface/download"
  : >"${MODELS_DIR}/.cache/huggingface/download/blob.incomplete"
  : >"${MODELS_DIR}/keep.safetensors"

  run cmd_reset_hf_partials --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"incomplete"* ]]

  export LAB_MOCK_HF_RUNNING=1
  run cmd_reset_hf_partials --yes
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"still running"* ]]
  [[ -f "${MODELS_DIR}/.cache/huggingface/download/blob.incomplete" ]]
  unset LAB_MOCK_HF_RUNNING

  run cmd_reset_hf_partials --yes
  [ "${status}" -eq 0 ]
  [[ ! -f "${MODELS_DIR}/.cache/huggingface/download/blob.incomplete" ]]
  [[ -f "${MODELS_DIR}/keep.safetensors" ]]

  : >"${MODELS_DIR}/.cache/huggingface/download/blob.incomplete"
  run cmd_download_models --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--drop-incomplete"* ]]
  run cmd_help
  [[ "${output}" == *"reset-hf-partials"* ]]

  export DOWNLOAD_LIMIT=off
  run cmd_download_models --drop-incomplete
  [ "${status}" -eq 0 ]
  [[ ! -f "${MODELS_DIR}/.cache/huggingface/download/blob.incomplete" ]]
  [[ "${output}" == *"drop"* || "${output}" == *"incomplete"* || "${output}" == *"lab workflow weights ready"* ]]
}
