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
}

teardown() {
  teardown_repo_env
}

@test "manage CLI help unknown doctor status start stop cleanup download" {
  run bash "${MANAGE_SH}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"doctor"* ]]
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

@test "manage cmd_* direct: help doctor status start stop restart logs download cleanup" {
  run cmd_help
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
  run cmd_download_models
  [ "${status}" -eq 0 ]
  run cmd_download_limit status --json
  [ "${status}" -eq 0 ]
  export LAB_CONFIRM_TOKEN=DELETE
  run cmd_cleanup
  [ "${status}" -eq 0 ]
}
