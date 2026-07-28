#!/usr/bin/env bats
#
# ## comfy_scripts.bats
#
# Purpose:
#   Cover docker/install-comfy.sh and docker/entrypoint.sh helpers without a
#   real ComfyUI install (strict shell inventory includes docker/*.sh).
#
# Hermetic:
#   Temp COMFY_HOME / MODELS_ROOT; mocked install command for entrypoint.
#

load 'test_helper'

setup() {
  setup_repo_env
  export COMFY_HOME="${TEST_TMP_DIR}/ComfyUI"
  export MODELS_ROOT="${TEST_TMP_DIR}/models"
  export STAMP="${COMFY_HOME}/.lab-install-complete"
  export VENV="${COMFY_HOME}/.venv"
  mkdir -p "${MODELS_ROOT}"
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
}

teardown() {
  teardown_repo_env
}

@test "install-comfy log warn link_models clone_node" {
  run log "hello"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"[comfy-install]"* ]]
  run warn "careful"
  [ "${status}" -eq 0 ]

  INSTALL_T0="$(date +%s)"
  run install_elapsed_s
  [ "${status}" -eq 0 ]
  run install_format_elapsed 90
  [ "${output}" = "1:30" ]
  run step 1 11 "Clone ComfyUI"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"step 1/11"* ]]
  [[ "${output}" == *"Clone ComfyUI"* ]]

  mkdir -p "${COMFY_HOME}/models"
  run link_models diffusion_models
  [ "${status}" -eq 0 ]
  [[ -L "${COMFY_HOME}/models/diffusion_models" ]]

  # Empty existing dir path branch
  rm -f "${COMFY_HOME}/models/vae"
  mkdir -p "${COMFY_HOME}/models/vae"
  run link_models vae
  [ "${status}" -eq 0 ]

  # clone_node soft-fails without network if git missing target — mock git
  export CUSTOM="${TEST_TMP_DIR}/custom_nodes"
  mkdir -p "${CUSTOM}"
  install_mock_bin git 'echo "git $*"; exit 1'
  install_mock_bin pip 'echo "pip $*"; exit 0'
  run clone_node "https://example.com/node.git" "DemoNode"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"custom node"* ]]
}

@test "main with mocked install and NO_EXEC" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  mkdir -p "${VENV}/bin"
  printf '#!/usr/bin/env bash\necho ok\n' >"${VENV}/bin/python"
  chmod +x "${VENV}/bin/python"
  # fake activate
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  : >"${STAMP}"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_ENTRYPOINT_NO_EXEC"* || "${output}" == *"phase"* || "${output}" == *"refresh"* ]]
}

@test "entrypoint seeds from prebuilt when stamp missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local pre="${TEST_TMP_DIR}/prebuilt"
  export LAB_PREBUILT_ROOT="${pre}"
  export COMFY_HOME="${TEST_TMP_DIR}/seeded_comfy"
  export VENV="${COMFY_HOME}/.venv"
  export STAMP="${COMFY_HOME}/.lab-install-complete"
  mkdir -p "${pre}/.venv/bin" "${pre}/user"
  printf '#!/usr/bin/env bash\necho ok\n' >"${pre}/.venv/bin/python"
  chmod +x "${pre}/.venv/bin/python"
  printf 'export VIRTUAL_ENV=1\n' >"${pre}/.venv/bin/activate"
  echo stamp >"${pre}/.lab-install-complete"
  echo tree >"${pre}/marker.txt"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  unset LAB_FORCE_COLD_INSTALL
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Seeding"* || "${output}" == *"prebuilt"* || "${output}" == *"Seed"* ]]
  [[ -f ${COMFY_HOME}/marker.txt ]]
  [[ -x ${COMFY_HOME}/.venv/bin/python ]]
}

@test "prebuilt_ready detects venv python" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LAB_PREBUILT_ROOT="${TEST_TMP_DIR}/empty_pre"
  mkdir -p "${LAB_PREBUILT_ROOT}"
  run prebuilt_ready
  [ "${status}" -ne 0 ]
  mkdir -p "${LAB_PREBUILT_ROOT}/.venv/bin"
  printf '#!/bin/sh\n' >"${LAB_PREBUILT_ROOT}/.venv/bin/python"
  chmod +x "${LAB_PREBUILT_ROOT}/.venv/bin/python"
  run prebuilt_ready
  [ "${status}" -eq 0 ]
}

@test "main fails when venv python missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  rm -rf "${VENV}"
  run main
  [ "${status}" -ne 0 ]
}
