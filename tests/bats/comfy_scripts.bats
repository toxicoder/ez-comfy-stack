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
  run clone_node "https://example.com/node.git" "DemoNode"
  [ "${status}" -eq 0 ]
}

@test "main with mocked install and NO_EXEC" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  mkdir -p "${VENV}/bin"
  printf '#!/usr/bin/env bash\necho ok\n' >"${VENV}/bin/python"
  chmod +x "${VENV}/bin/python"
  # fake activate
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  # point patch path missing is fine
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_ENTRYPOINT_NO_EXEC"* || "${output}" == *"starting ComfyUI"* || "${output}" == *"installing"* ]]
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
