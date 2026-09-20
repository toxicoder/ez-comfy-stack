#!/usr/bin/env bats
#
# ## setup_client.bats
#
# Purpose:
#   Cover detect_client_os, write_ez_spark_ssh_config, ensure_ssh_key,
#   client_missing_tools, install_client_packages, client_is_spark_host,
#   ssh_config_path, setup_client_usage, remote_spark_bootstrap,
#   spark_ui_tunnel, run_laptop_client, run_onboard, setup_client_main.
#
# Hermetic:
#   Temp HOME + EZ_SSH_CONFIG; LAB_MOCK_SSH; LAB_MOCK_CLIENT_INSTALL.
#

load 'test_helper'

setup() {
  setup_repo_env
  export HOME="${TEST_TMP_DIR}/home"
  mkdir -p "${HOME}/.ssh"
  export EZ_SSH_CONFIG="${HOME}/.ssh/config"
  export EZ_SSH_KEY="${HOME}/.ssh/id_ed25519"
  export LAB_MOCK_SSH=1
  export LAB_MOCK_CLIENT_INSTALL=1
  export EZ_ONBOARD_ROLE=laptop
  export EZ_CLIENT_OS=darwin
  export SPARK_HOST=10.0.0.9
  export SPARK_USER=spark
  export COMFY_PORT=8188
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/client_os.sh"
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/utilities/setup-client.sh"
}

teardown() {
  teardown_repo_env
}

@test "detect_client_os honors EZ_CLIENT_OS" {
  export EZ_CLIENT_OS=linux
  run detect_client_os
  [ "${status}" -eq 0 ]
  [ "${output}" = "linux" ]
}

@test "write_ez_spark_ssh_config writes Host ez-spark and replaces the block" {
  run write_ez_spark_ssh_config 10.0.0.9 spark 8188
  [ "${status}" -eq 0 ]
  grep -q "Host ez-spark" "${EZ_SSH_CONFIG}"
  grep -q "HostName 10.0.0.9" "${EZ_SSH_CONFIG}"
  grep -q "LocalForward 8188 127.0.0.1:8188" "${EZ_SSH_CONFIG}"
  run write_ez_spark_ssh_config 10.0.0.10 other 9191
  [ "${status}" -eq 0 ]
  [[ "$(grep -c 'BEGIN ez-comfy-stack ez-spark' "${EZ_SSH_CONFIG}")" -eq 1 ]]
  grep -q "HostName 10.0.0.10" "${EZ_SSH_CONFIG}"
  ! grep -q "10.0.0.9" "${EZ_SSH_CONFIG}"
}

@test "ensure_ssh_key mock writes ed25519 files" {
  run ensure_ssh_key
  [ "${status}" -eq 0 ]
  [ -f "${EZ_SSH_KEY}" ]
  [ -f "${EZ_SSH_KEY}.pub" ]
}

@test "ssh_config_path uses EZ_SSH_CONFIG" {
  run ssh_config_path
  [ "${status}" -eq 0 ]
  [ "${output}" = "${EZ_SSH_CONFIG}" ]
}

@test "client_is_spark_host respects EZ_ONBOARD_ROLE" {
  export EZ_ONBOARD_ROLE=spark
  run client_is_spark_host
  [ "${status}" -eq 0 ]
  export EZ_ONBOARD_ROLE=laptop
  run client_is_spark_host
  [ "${status}" -eq 1 ]
}

@test "install_client_packages mock skips brew" {
  run install_client_packages darwin
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_MOCK_CLIENT_INSTALL"* || "${output}" == *"client tools"* ]]
}

@test "client_missing_tools is quiet when git ssh python3 exist" {
  run client_missing_tools
  [ "${status}" -eq 0 ]
}

@test "run_laptop_client writes ssh config without starting compose" {
  run run_laptop_client
  [ "${status}" -eq 0 ]
  grep -q "Host ez-spark" "${EZ_SSH_CONFIG}"
  [[ "${output}" == *"never auto-started"* ]]
  [[ "${output}" != *"compose up"* ]]
}

@test "remote_spark_bootstrap mock does not start" {
  run remote_spark_bootstrap development 0
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_MOCK_SSH"* ]]
  [[ "${output}" != *"manage.sh start"* ]]
}

@test "spark_ui_tunnel mock prints forward" {
  run spark_ui_tunnel
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"8188"* ]]
}

@test "setup_client_main --help" {
  run setup_client_main --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"setup-client.sh"* ]]
}

@test "setup_client_main --onboard laptop mock" {
  run setup_client_main --onboard --host 10.1.2.3 --user spark --port 8188
  [ "${status}" -eq 0 ]
  grep -q "HostName 10.1.2.3" "${EZ_SSH_CONFIG}"
  [[ "${output}" == *"NOT started"* ]]
}

@test "run_onboard laptop mock does not start" {
  run run_onboard 0
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"NOT started"* ]]
}

@test "setup_client_usage mentions never starts" {
  run setup_client_usage
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Never starts"* ]]
}
