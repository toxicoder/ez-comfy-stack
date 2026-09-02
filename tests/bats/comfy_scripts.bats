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
  export LAB_OUTPUTS_MOUNT="${TEST_TMP_DIR}/outputs"
  mkdir -p "${MODELS_ROOT}" "${LAB_OUTPUTS_MOUNT}"
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
}

teardown() {
  teardown_repo_env
}

@test "install-comfy phase_nodes and ensure_lab_video_nodes require VideoHelperSuite" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  run grep -F 'ComfyUI-VideoHelperSuite' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'ensure_lab_video_nodes' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'ensure_lab_video_nodes' "${REPO_ROOT}/docker/install-comfy.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'COMFYUI_VHS_REF' "${REPO_ROOT}/docker/install-comfy/common.sh"
  [ "${status}" -eq 0 ]
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

@test "link_comfy_output_dir migrates volume output and symlinks to mount" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local vol_out mount
  vol_out="${TEST_TMP_DIR}/ComfyUI/output"
  mount="${TEST_TMP_DIR}/host_outputs"
  mkdir -p "${vol_out}"
  echo oldpng >"${vol_out}/legacy.png"
  export LAB_OUTPUTS_MOUNT="${mount}"
  export COMFY_HOME="${TEST_TMP_DIR}/ComfyUI"
  run link_comfy_output_dir "${vol_out}"
  [ "${status}" -eq 0 ]
  [[ -L ${TEST_TMP_DIR}/ComfyUI/output ]]
  [[ -f ${mount}/legacy.png ]]
  [[ "$(readlink "${TEST_TMP_DIR}/ComfyUI/output")" == "${mount}" ]]
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
  export LAB_OUTPUTS_MOUNT="${TEST_TMP_DIR}/outputs_main"
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_ENTRYPOINT_NO_EXEC"* || "${output}" == *"phase"* || "${output}" == *"refresh"* ]]
  [[ -L ${COMFY_HOME}/output ]]
}

@test "entrypoint reseeds prebuilt when volume pin lags" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local pre="${TEST_TMP_DIR}/prebuilt_pin"
  export LAB_PREBUILT_ROOT="${pre}"
  export COMFY_HOME="${TEST_TMP_DIR}/old_vol"
  export VENV="${COMFY_HOME}/.venv"
  export STAMP="${COMFY_HOME}/.lab-install-complete"
  mkdir -p "${pre}/.venv/bin" "${COMFY_HOME}/.venv/bin"
  printf '#!/usr/bin/env bash\necho ok\n' >"${pre}/.venv/bin/python"
  chmod +x "${pre}/.venv/bin/python"
  cp "${pre}/.venv/bin/python" "${COMFY_HOME}/.venv/bin/python"
  printf 'export VIRTUAL_ENV=1\n' >"${pre}/.venv/bin/activate"
  printf 'export VIRTUAL_ENV=1\n' >"${COMFY_HOME}/.venv/bin/activate"
  echo stamp >"${STAMP}"
  echo v0.29.0 >"${COMFY_HOME}/.lab-comfyui-ref"
  echo fromimg >"${pre}/marker_pin.txt"
  export COMFYUI_REF="v0.34.0"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  unset LAB_FORCE_COLD_INSTALL
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"pin"* || "${output}" == *"Re-seeding"* ]]
  [[ -f ${COMFY_HOME}/marker_pin.txt ]]
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
  # Last arg of git clone is destination; create it so ensure_lab_video_nodes succeeds
  install_mock_bin git 'echo "git $*"; dest="${@: -1}"; mkdir -p "${dest}" 2>/dev/null || true; mkdir -p "${COMFY_HOME}/.git"; echo ok >"${COMFY_HOME}/requirements.txt"; exit 0'

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
  [[ -f ${COMFY_HOME}/.lab-comfyui-ref ]]
}

@test "comfy pin file write read match" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  mkdir -p "${COMFY_HOME}"
  COMFYUI_REF="v0.34.0"
  run write_comfy_pin
  [ "${status}" -eq 0 ]
  run read_comfy_pin
  [ "${output}" = "v0.34.0" ]
  run comfy_pin_matches
  [ "${status}" -eq 0 ]
  COMFYUI_REF="v0.29.0"
  run comfy_pin_matches
  [ "${status}" -ne 0 ]
  run comfy_pin_file
  [[ "${output}" == *".lab-comfyui-ref"* ]]
}

@test "refresh_comfy_pin_if_needed skips when pin matches" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  mkdir -p "${COMFY_HOME}" "${VENV}/bin"
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  COMFYUI_REF="v0.34.0"
  write_comfy_pin
  run refresh_comfy_pin_if_needed
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"already on volume"* ]]
}

@test "refresh_comfy_pin_if_needed clones when volume pin lags and prebuilt missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  mkdir -p "${VENV}/bin"
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  printf '#!/bin/sh\n' >"${VENV}/bin/python"
  chmod +x "${VENV}/bin/python"
  echo v0.29.0 >"${COMFY_HOME}/.lab-comfyui-ref"
  export LAB_PREBUILT_ROOT="${TEST_TMP_DIR}/empty_pre"
  mkdir -p "${LAB_PREBUILT_ROOT}"
  install_mock_bin pip 'echo pip; exit 0'
  install_mock_bin git 'echo "git $*"; dest="${@: -1}"; mkdir -p "${dest}" "${COMFY_HOME}/.git" 2>/dev/null || true; echo ok >"${COMFY_HOME}/requirements.txt"; exit 0'
  COMFYUI_REF="v0.34.0"
  run refresh_comfy_pin_if_needed
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cloning"* || "${output}" == *"Syncing"* ]]
  run read_comfy_pin
  [ "${output}" = "v0.34.0" ]
}

@test "refresh_comfy_pin_if_needed reseeds from prebuilt when pin lags" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  mkdir -p "${VENV}/bin"
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  echo v0.29.0 >"${COMFY_HOME}/.lab-comfyui-ref"
  local pre="${TEST_TMP_DIR}/pre_pin"
  export LAB_PREBUILT_ROOT="${pre}"
  mkdir -p "${pre}"
  echo seeded >"${pre}/from_image.txt"
  echo 'print("ok")' >"${pre}/main.py"
  COMFYUI_REF="v0.34.0"
  run refresh_comfy_pin_if_needed
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_HOME}/from_image.txt ]]
  [[ "${output}" == *"Re-seeding"* || "${output}" == *"prebuilt"* ]]
}

@test "install-comfy main stamp-present refresh invokes pin sync" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  mkdir -p "${VENV}/bin" "${COMFY_HOME}/comfy_extras" \
    "${COMFY_HOME}/custom_nodes/ComfyUI-VideoHelperSuite/.git"
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  printf '#!/bin/sh\n' >"${VENV}/bin/python"
  chmod +x "${VENV}/bin/python"
  : >"${STAMP}"
  install_mock_bin git 'echo "git $*"; exit 0'
  install_mock_bin pip 'echo "pip $*"; exit 0'
  COMFYUI_REF="v0.34.0"
  write_comfy_pin
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"fast refresh"* || "${output}" == *"already on volume"* ]]
  [[ "${output}" == *"Install complete"* ]]
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

@test "package_prebuilt_parts splits venv and app when LAB_PACKAGE_PARTS=1" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  local root parts
  root="${TEST_TMP_DIR}/prebuilt_tree"
  parts="${TEST_TMP_DIR}/parts"
  mkdir -p "${root}/.venv/bin" "${root}/custom_nodes/demo" "${root}/comfy"
  echo py >"${root}/.venv/bin/python"
  echo app >"${root}/main.py"
  echo node >"${root}/custom_nodes/demo/node.py"
  export COMFY_HOME="${root}"
  export LAB_PARTS_ROOT="${parts}"
  export LAB_PACKAGE_PARTS=1
  run package_prebuilt_parts
  [ "${status}" -eq 0 ]
  [[ -f ${parts}/venv/bin/python ]]
  [[ -f ${parts}/app/main.py ]]
  [[ -f ${parts}/app/custom_nodes/demo/node.py ]]
  [[ ! -e ${parts}/app/.venv ]]
  # Disabled path is a no-op
  export LAB_PACKAGE_PARTS=0
  run package_prebuilt_parts
  [ "${status}" -eq 0 ]
}

@test "default pins are non-empty validated tags" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  [[ -n ${COMFYUI_REF} ]]
  [[ "${COMFYUI_REF}" == v0.* ]]
  [[ -n ${COMFYUI_MANAGER_REF} ]]
  [[ -n ${COMFYUI_NUNCHAKU_NODE_REF} ]]
  [[ "${COMFYUI_NUNCHAKU_NODE_REF}" == v* ]]
}

@test "install-comfy modules exist for Docker phase COPY contract" {
  [[ -f ${REPO_ROOT}/docker/install-comfy/common.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-venv-torch.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-comfy.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-nodes.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-finalize.sh ]]
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

@test "find_libcuda_dir and ensure_triton_build_env set LIBRARY_PATH" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local fake_dir
  fake_dir="${TEST_TMP_DIR}/fakecuda"
  mkdir -p "${fake_dir}"
  : >"${fake_dir}/libcuda.so.1"
  export LD_LIBRARY_PATH="${fake_dir}"
  unset LIBRARY_PATH

  run find_libcuda_dir
  [ "${status}" -eq 0 ]
  [[ "${output}" == "${fake_dir}" ]]

  run ensure_triton_build_env
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"libcuda dir=${fake_dir}"* ]]
  # ensure_triton_build_env exports in subshell via run — re-run in current shell
  ensure_triton_build_env
  [[ "${LIBRARY_PATH}" == *"${fake_dir}"* ]]
  [[ "${LD_LIBRARY_PATH}" == *"${fake_dir}"* ]]
}

@test "find_libcuda_dir fails when libcuda missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LD_LIBRARY_PATH="${TEST_TMP_DIR}/empty_ld"
  mkdir -p "${LD_LIBRARY_PATH}"
  # Hide system ldconfig results by putting a no-op ldconfig first if present is hard;
  # just assert search of empty LD path + missing common files may still find host
  # libcuda on developer machines. Force failure by only using a private path
  # and stubbing ldconfig.
  install_mock_bin ldconfig 'exit 1'
  run find_libcuda_dir
  [ "${status}" -ne 0 ]
}

@test "triton_build_deps_ok requires gcc Python.h and libcuda" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  install_mock_bin ldconfig 'exit 1'
  export LD_LIBRARY_PATH="${TEST_TMP_DIR}/no_cuda"
  mkdir -p "${LD_LIBRARY_PATH}"
  # Host may still have gcc + Python.h; without libcuda this must fail.
  run triton_build_deps_ok
  [ "${status}" -ne 0 ]

  local fake_dir py_inc
  fake_dir="${TEST_TMP_DIR}/okcuda"
  mkdir -p "${fake_dir}"
  : >"${fake_dir}/libcuda.so.1"
  export LD_LIBRARY_PATH="${fake_dir}"
  install_mock_bin gcc 'exit 0'
  # Provide a fake Python that reports include under TEST_TMP and a real Python.h
  py_inc="${TEST_TMP_DIR}/pyinc"
  mkdir -p "${py_inc}"
  : >"${py_inc}/Python.h"
  install_mock_bin python "echo '${py_inc}'"
  run triton_build_deps_ok
  [ "${status}" -eq 0 ]
}

@test "configure_torch_native_triton force and auto-disable" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LAB_PYTHONPATH_ROOT="${REPO_ROOT}/docker/pythonpath"
  unset PYTHONPATH

  export LAB_DISABLE_TORCH_NATIVE_TRITON=1
  run configure_torch_native_triton
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_DISABLE_TORCH_NATIVE_TRITON=1"* ]]
  configure_torch_native_triton
  [[ "${PYTHONPATH}" == *"${LAB_PYTHONPATH_ROOT}"* ]]

  # Auto-disable when deps incomplete
  export LAB_DISABLE_TORCH_NATIVE_TRITON=0
  install_mock_bin ldconfig 'exit 1'
  export LD_LIBRARY_PATH="${TEST_TMP_DIR}/no_cuda2"
  mkdir -p "${LD_LIBRARY_PATH}"
  configure_torch_native_triton
  [[ "${LAB_DISABLE_TORCH_NATIVE_TRITON}" == "1" ]]
}

@test "configure_torch_native_triton keeps Triton when deps OK" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LAB_PYTHONPATH_ROOT="${REPO_ROOT}/docker/pythonpath"
  export LAB_DISABLE_TORCH_NATIVE_TRITON=0
  local fake_dir py_inc
  fake_dir="${TEST_TMP_DIR}/okcuda2"
  py_inc="${TEST_TMP_DIR}/pyinc2"
  mkdir -p "${fake_dir}" "${py_inc}"
  : >"${fake_dir}/libcuda.so.1"
  : >"${py_inc}/Python.h"
  export LD_LIBRARY_PATH="${fake_dir}"
  install_mock_bin ldconfig 'exit 1'
  install_mock_bin gcc 'exit 0'
  install_mock_bin python "echo '${py_inc}'"
  configure_torch_native_triton
  [[ "${LAB_DISABLE_TORCH_NATIVE_TRITON}" == "0" ]]
}
