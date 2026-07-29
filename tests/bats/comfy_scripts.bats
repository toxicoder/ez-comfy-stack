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

@test "install-comfy nunchaku helpers never use bare PyPI nunchaku" {
  run nunchaku_platform_tag x86_64
  [ "${output}" = "linux_x86_64" ]
  run nunchaku_platform_tag aarch64
  [ "${output}" = "linux_aarch64" ]
  run nunchaku_platform_tag bogus
  [ "${output}" = "" ]
  run nunchaku_wheel_url "linux_x86_64" "cp312" "cu13.0" "torch2.11"
  [[ "${output}" == *"nunchaku-ai/nunchaku/releases/download"* ]]
  [[ "${output}" == *"linux_x86_64.whl"* ]]
  [[ "${output}" == *"cp312"* ]]
  [[ "${output}" != *"pypi.org"* ]]

  # aarch64 path: skip without attempting bare PyPI nunchaku
  : >"${TEST_TMP_DIR}/pip_calls.log"
  install_mock_bin pip 'echo "pip $*" >>"'"${TEST_TMP_DIR}"'/pip_calls.log"; exit 1'
  # python: package not installed, then version helpers unused on aarch64 skip
  install_mock_bin python 'exit 1'
  nunchaku_platform_tag() { echo "linux_aarch64"; }
  nunchaku_is_real() { return 1; }
  cleanup_wrong_nunchaku() { return 0; }
  run install_nunchaku_wheel
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"aarch64"* || "${output}" == *"skipping"* || "${output}" == *"no official"* ]]
  # Must never install the bare package name from PyPI
  if [[ -s ${TEST_TMP_DIR}/pip_calls.log ]]; then
    ! grep -qE 'pip install( --[^ ]+)* nunchaku( |$)' "${TEST_TMP_DIR}/pip_calls.log"
  fi
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
  run step 1 12 "Clone ComfyUI"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"step 1/12"* ]]
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
  [[ -L "${COMFY_HOME}/models/vae" ]]

  # Non-empty real dir must be moved aside and replaced with host symlink
  rm -f "${COMFY_HOME}/models/text_encoders"
  mkdir -p "${COMFY_HOME}/models/text_encoders"
  echo junk >"${COMFY_HOME}/models/text_encoders/old.bin"
  run link_models text_encoders
  [ "${status}" -eq 0 ]
  [[ -L "${COMFY_HOME}/models/text_encoders" ]]
  [[ ! -f ${COMFY_HOME}/models/text_encoders/old.bin ]]
  [[ -d ${MODELS_ROOT}/comfy/text_encoders ]]

  # clone_node soft-fails without network if git missing target — mock git
  export CUSTOM="${TEST_TMP_DIR}/custom_nodes"
  mkdir -p "${CUSTOM}"
  install_mock_bin git 'echo "git $*"; exit 1'
  install_mock_bin pip 'echo "pip $*"; exit 0'
  run clone_node "https://example.com/node.git" "DemoNode"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"custom node"* ]]

  # strip_prebuilt removes .git and bytecode junk
  local strip_root
  strip_root="${TEST_TMP_DIR}/strip_tree"
  mkdir -p "${strip_root}/.git" "${strip_root}/pkg/__pycache__" "${strip_root}/pkg"
  : >"${strip_root}/pkg/__pycache__/x.pyc"
  : >"${strip_root}/pkg/mod.py"
  run strip_prebuilt "${strip_root}"
  [ "${status}" -eq 0 ]
  [[ ! -d ${strip_root}/.git ]]
  [[ ! -d ${strip_root}/pkg/__pycache__ ]]
  [[ -f ${strip_root}/pkg/mod.py ]]
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

@test "entrypoint ep_log and seed_from_prebuilt helpers" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  run ep_log "progress marker"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"[entrypoint"* ]]
  [[ "${output}" == *"progress marker"* ]]

  local pre dest
  pre="${TEST_TMP_DIR}/seed_src"
  dest="${TEST_TMP_DIR}/seed_dst"
  mkdir -p "${pre}/sub"
  echo payload >"${pre}/sub/file.txt"
  export LAB_PREBUILT_ROOT="${pre}"
  export COMFY_HOME="${dest}"
  run seed_from_prebuilt
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/sub/file.txt ]]
  [[ "$(cat "${dest}/sub/file.txt")" == "payload" ]]
}

@test "install-comfy pip_install wrapper" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  install_mock_bin pip 'echo "pip $*"; exit 0'
  run pip_install -U pip
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"pip:"* || "${output}" == *"pip "* ]]
}

@test "install-comfy parse_install_args and run_install_phase" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  # Direct call (not `run`) so INSTALL_PHASE is set in this shell
  INSTALL_PHASE=""
  parse_install_args --phase venv
  [ "${INSTALL_PHASE}" = "venv" ]

  run parse_install_args --phase
  [ "${status}" -eq 2 ]

  run parse_install_args --bogus
  [ "${status}" -eq 2 ]

  run run_install_phase not-a-phase
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"unknown phase"* ]]
}

@test "install-comfy phase helpers with mocks" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  install_mock_bin python3 'if [[ "$*" == *venv* ]]; then mkdir -p "${VENV}/bin"; printf "export VIRTUAL_ENV=1\n" >"${VENV}/bin/activate"; printf "#!/bin/sh\n" >"${VENV}/bin/python"; chmod +x "${VENV}/bin/python"; exit 0; fi; exit 0'
  install_mock_bin pip 'echo "pip $*"; exit 0'
  install_mock_bin git 'echo "git $*"; mkdir -p "${COMFY_HOME}/.git"; echo ok >"${COMFY_HOME}/requirements.txt"; exit 0'

  run phase_venv
  [ "${status}" -eq 0 ]
  [[ -f ${VENV}/bin/activate ]]

  # Named for coverage inventory (also used by every phase)
  run activate_venv
  [ "${status}" -eq 0 ]

  run phase_torch
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"pip:"* || "${output}" == *"torch"* ]]

  run phase_clone_comfy
  [ "${status}" -eq 0 ]

  run phase_comfy
  [ "${status}" -eq 0 ]

  run phase_nodes
  [ "${status}" -eq 0 ]

  run link_all_models
  [ "${status}" -eq 0 ]
  [[ -L ${COMFY_HOME}/models/diffusion_models ]]

  run apply_free_memory_patch
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"not found"* || "${output}" == *"patch"* || -z ${output} ]]

  # finalize with mocked strip deps
  run phase_finalize
  [ "${status}" -eq 0 ]
  [[ -f ${STAMP} ]]
}

@test "install-comfy main --phase dispatches without full cold install" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  install_mock_bin python3 'if [[ "$*" == *venv* ]]; then mkdir -p "${VENV}/bin"; printf "export VIRTUAL_ENV=1\n" >"${VENV}/bin/activate"; printf "#!/bin/sh\n" >"${VENV}/bin/python"; chmod +x "${VENV}/bin/python"; exit 0; fi; exit 0'
  install_mock_bin pip 'echo "pip $*"; exit 0'
  run main --phase venv
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Docker phase: venv"* || "${output}" == *"phase venv"* || "${output}" == *"venv"* ]]
  [[ "${output}" == *"Phase venv complete"* || "${output}" == *"complete"* ]]
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
