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

@test "install_llama_cpp_cpu is fail-soft and disables CUDA" {
  run grep -F 'install_llama_cpp_cpu' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'GGML_CUDA=OFF' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'https://abetlen.github.io/llama-cpp-python/whl/cpu' \
    "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -E 'extra-index-url[^[:cntrl:]]*cu1' \
    "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -ne 0 ]
  pip_install() {
    printf '%s\n' "$*" >>"${TEST_TMP_DIR}/pip_llama.log"
    return 1
  }
  : >"${TEST_TMP_DIR}/pip_llama.log"
  run install_llama_cpp_cpu
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"pass through"* || "${output}" == *"failed"* ]]
  grep -q 'extra-index-url' "${TEST_TMP_DIR}/pip_llama.log"
  grep -q 'llama-cpp-python' "${TEST_TMP_DIR}/pip_llama.log"
  grep -q 'only-binary' "${TEST_TMP_DIR}/pip_llama.log"
  if grep -E 'cu11|cu12|cu13' "${TEST_TMP_DIR}/pip_llama.log"; then
    return 1
  fi
  pip_install() { return 0; }
  run install_llama_cpp_cpu
  [ "${status}" -eq 0 ]
}

@test "install_dub_wheels is fail-soft" {
  run grep -F 'install_dub_wheels' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'faster-whisper' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  pip_install() { return 1; }
  run install_dub_wheels
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"empty mix"* || "${output}" == *"failed"* ]]
  pip_install() { return 0; }
  run install_dub_wheels
  [ "${status}" -eq 0 ]
}

@test "install_dub_wheels splits ASR from chatterbox --no-deps" {
  run grep -F 'install_faster_whisper_wheel' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'install_chatterbox_wheel' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -E 'pip_install[^[:cntrl:]]*faster-whisper[^[:cntrl:]]*chatterbox' \
    "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -ne 0 ]
  run grep -F -- '--no-deps' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F -- '--force-reinstall' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'resemble-ai/chatterbox/archive' \
    "${REPO_ROOT}/docker/install-comfy/common.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'chatterbox_tts_zip_url' \
    "${REPO_ROOT}/docker/install-comfy/common.sh"
  [ "${status}" -eq 0 ]
  run chatterbox_tts_zip_url
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"resemble-ai/chatterbox/archive"* ]]
  run grep -E 'pip_install --no-deps chatterbox-tts' \
    "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -ne 0 ]
  pip_install() {
    printf '%s\n' "$*" >>"${TEST_TMP_DIR}/pip_dub.log"
    if [[ $* == *resemble-ai/chatterbox* && $* != *--no-deps* ]]; then
      return 1
    fi
    return 0
  }
  : >"${TEST_TMP_DIR}/pip_dub.log"
  run install_faster_whisper_wheel
  [ "${status}" -eq 0 ]
  run install_chatterbox_wheel
  [ "${status}" -eq 0 ]
  run install_dub_wheels
  [ "${status}" -eq 0 ]
  grep -q 'faster-whisper' "${TEST_TMP_DIR}/pip_dub.log"
  grep -q -- '--no-deps' "${TEST_TMP_DIR}/pip_dub.log"
  grep -q -- '--force-reinstall' "${TEST_TMP_DIR}/pip_dub.log"
  grep -q 'resemble-ai/chatterbox' "${TEST_TMP_DIR}/pip_dub.log"
  grep -q 'spacy-pkuseg' "${TEST_TMP_DIR}/pip_dub.log"
  if grep -E 'faster-whisper.*chatterbox' "${TEST_TMP_DIR}/pip_dub.log"; then
    return 1
  fi
}

@test "install-comfy phase_nodes and ensure_lab_video_nodes require VideoHelperSuite" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  run grep -F 'ComfyUI-VideoHelperSuite' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'ComfyUI-MagCache' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'apply_magcache_compat_patch' "${REPO_ROOT}/docker/install-comfy.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'patch_magcache_compat' "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'configure_nunchaku_pack' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'LAB_ENABLE_LTX_DIRECTOR' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'ComfyUI-OpenCut' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'MiniMaxH3-Director' "${REPO_ROOT}/docker/install-comfy/phase-nodes.sh"
  [ "${status}" -ne 0 ]
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
  export HOST_UID
  HOST_UID="$(id -u)"
  export HOST_GID
  HOST_GID="$(id -g)"
  run layout_host_uid_gid
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"$(id -u)"* ]]
  run link_models diffusion_models
  [ "${status}" -eq 0 ]
  [[ -L "${COMFY_HOME}/models/diffusion_models" ]]
  [[ -d ${MODELS_ROOT}/comfy/diffusion_models ]]
  unset HOST_UID HOST_GID
  run layout_host_uid_gid
  [ "${status}" -eq 0 ]
  [[ "${output}" == *":"* ]]

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
  run clone_node_ref_is_sha 47bdd2aca97e568087c4e92d2d2f0426bdce7a37
  [ "${status}" -eq 0 ]
  run clone_node_ref_is_sha 0.5.0
  [ "${status}" -ne 0 ]
  run clone_node_ref_is_sha main
  [ "${status}" -ne 0 ]

  # strip_prebuilt removes .git and bytecode junk
  local strip_root
  strip_root="${TEST_TMP_DIR}/strip_tree"
  mkdir -p "${strip_root}/.git" "${strip_root}/pkg/__pycache__" "${strip_root}/pkg"
  : >"${strip_root}/pkg/__pycache__/x.pyc"
  : >"${strip_root}/pkg/mod.py"
  mkdir -p "${strip_root}/tests" "${strip_root}/.github" "${strip_root}/input"
  echo t >"${strip_root}/tests/test_foo.py"
  echo yml >"${strip_root}/.github/workflows.yml"
  echo png >"${strip_root}/input/example.png"
  echo keep >"${strip_root}/input/keep.txt"
  run strip_prebuilt "${strip_root}"
  [ "${status}" -eq 0 ]
  [[ ! -d ${strip_root}/.git ]]
  [[ ! -d ${strip_root}/pkg/__pycache__ ]]
  [[ -f ${strip_root}/pkg/mod.py ]]
  [[ ! -d ${strip_root}/tests ]]
  [[ ! -d ${strip_root}/.github ]]
  [[ ! -f ${strip_root}/input/example.png ]]
  [[ -f ${strip_root}/input/keep.txt ]]
}

@test "link_comfy_input_dir migrates volume input and symlinks to mount" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local vol_in mount
  vol_in="${TEST_TMP_DIR}/ComfyUI/input"
  mount="${TEST_TMP_DIR}/host_inputs"
  mkdir -p "${vol_in}"
  echo startpng >"${vol_in}/start.png"
  export LAB_INPUTS_MOUNT="${mount}"
  export COMFY_HOME="${TEST_TMP_DIR}/ComfyUI"
  run link_comfy_input_dir "${vol_in}"
  [ "${status}" -eq 0 ]
  [[ -L ${TEST_TMP_DIR}/ComfyUI/input ]]
  [[ -f ${mount}/start.png ]]
  [[ "$(readlink "${TEST_TMP_DIR}/ComfyUI/input")" == "${mount}" ]]
}

@test "seed_from_prebuilt rsync excludes user and input" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local pre dest
  pre="${TEST_TMP_DIR}/prebuilt"
  dest="${TEST_TMP_DIR}/ComfyUI"
  mkdir -p "${pre}/.venv/bin" "${pre}/user/default" "${pre}/input" \
    "${pre}/custom_nodes/_user" "${pre}/custom_nodes/ez_prompt_enhance" \
    "${dest}/user/default" "${dest}/input" "${dest}/custom_nodes/_user"
  printf '#!/usr/bin/env bash\necho ok\n' >"${pre}/.venv/bin/python"
  chmod +x "${pre}/.venv/bin/python"
  echo pre >"${pre}/main.py"
  echo wipe-me >"${pre}/user/default/lab.json"
  echo keep-me >"${dest}/user/default/mine.json"
  echo oldstart >"${dest}/input/start.png"
  echo prestart >"${pre}/input/example.png"
  echo poison >"${pre}/custom_nodes/_user/poison.py"
  echo ok >"${pre}/custom_nodes/ez_prompt_enhance/__init__.py"
  echo keep-pack >"${dest}/custom_nodes/_user/mine.py"
  export LAB_PREBUILT_ROOT="${pre}"
  export COMFY_HOME="${dest}"
  run prebuilt_exclude_patterns
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"custom_nodes/_user/"* ]]
  run seed_from_prebuilt
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/main.py ]]
  [[ -f ${dest}/user/default/mine.json ]]
  [[ ! -f ${dest}/user/default/lab.json ]]
  [[ -f ${dest}/input/start.png ]]
  [[ ! -f ${dest}/input/example.png ]]
  [[ -f ${dest}/custom_nodes/_user/mine.py ]]
  [[ ! -f ${dest}/custom_nodes/_user/poison.py ]]
  [[ -f ${dest}/custom_nodes/ez_prompt_enhance/__init__.py ]]
}

@test "copy_prebuilt_tree skips user input and custom_nodes/_user" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local pre dest
  pre="${TEST_TMP_DIR}/prebuilt_cp"
  dest="${TEST_TMP_DIR}/ComfyUI_cp"
  mkdir -p "${pre}/.venv/bin" "${pre}/user/default" "${pre}/custom_nodes/_user" \
    "${pre}/custom_nodes/ez_film" "${dest}/user/default" "${dest}/custom_nodes/_user"
  echo pre >"${pre}/main.py"
  echo wipe >"${pre}/user/default/lab.json"
  echo keep >"${dest}/user/default/mine.json"
  echo poison >"${pre}/custom_nodes/_user/poison.py"
  echo ok >"${pre}/custom_nodes/ez_film/__init__.py"
  echo keep-pack >"${dest}/custom_nodes/_user/mine.py"
  run copy_prebuilt_tree "${pre}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/main.py ]]
  [[ -f ${dest}/user/default/mine.json ]]
  [[ ! -f ${dest}/user/default/lab.json ]]
  [[ -f ${dest}/custom_nodes/_user/mine.py ]]
  [[ ! -f ${dest}/custom_nodes/_user/poison.py ]]
  [[ -f ${dest}/custom_nodes/ez_film/__init__.py ]]
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

@test "install_lab_custom_nodes copies pack and no-ops when missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local src dest
  src="${TEST_TMP_DIR}/ez_prompt_enhance"
  dest="${TEST_TMP_DIR}/ComfyUI/custom_nodes/ez_prompt_enhance"
  mkdir -p "${src}/prompts" "${src}/js"
  echo 'ok' >"${src}/__init__.py"
  echo 'sys' >"${src}/prompts/klein_t2i.txt"
  echo 'preview' >"${src}/js/ez_prompt_enhance.js"
  run install_lab_custom_nodes "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/__init__.py ]]
  [[ -f ${dest}/prompts/klein_t2i.txt ]]
  [[ -f ${dest}/js/ez_prompt_enhance.js ]]
  run install_lab_custom_nodes "${TEST_TMP_DIR}/missing-nodes" "${TEST_TMP_DIR}/ComfyUI/custom_nodes/ez_prompt_enhance2"
  [ "${status}" -eq 0 ]
  [[ ! -d ${TEST_TMP_DIR}/ComfyUI/custom_nodes/ez_prompt_enhance2 ]]
}

@test "install_all_lab_custom_nodes copies packs and skips non-packs" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local src dest
  src="${TEST_TMP_DIR}/custom_nodes_src"
  dest="${TEST_TMP_DIR}/ComfyUI/custom_nodes_all"
  mkdir -p "${src}/ez_prompt_enhance" "${src}/ez_ltx_spatial" "${src}/not_a_pack"
  echo 'ok' >"${src}/ez_prompt_enhance/__init__.py"
  echo 'ok' >"${src}/ez_ltx_spatial/__init__.py"
  mkdir -p "${src}/ez_studio_blocks/subgraphs"
  echo 'ok' >"${src}/ez_studio_blocks/__init__.py"
  echo '{}' >"${src}/ez_studio_blocks/subgraphs/klein-t2i-backbone.json"
  echo 'skip' >"${src}/not_a_pack/readme.txt"
  echo 'file' >"${src}/stray.txt"
  run install_all_lab_custom_nodes "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/ez_prompt_enhance/__init__.py ]]
  [[ -f ${dest}/ez_ltx_spatial/__init__.py ]]
  [[ -f ${dest}/ez_studio_blocks/subgraphs/klein-t2i-backbone.json ]]
  [[ ! -d ${dest}/not_a_pack ]]
  [[ ! -f ${dest}/stray.txt ]]
  [[ "${output}" == *"installed 3 custom node pack"* ]]
  run install_all_lab_custom_nodes "${TEST_TMP_DIR}/missing-root" "${TEST_TMP_DIR}/ComfyUI/custom_nodes_missing"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"optional mount"* ]]
  mkdir -p "${TEST_TMP_DIR}/empty_packs"
  run install_all_lab_custom_nodes "${TEST_TMP_DIR}/empty_packs" "${TEST_TMP_DIR}/ComfyUI/custom_nodes_empty"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"no custom node packs under"* ]]
}

@test "lab_workflow_lane maps _lab and legacy globs" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  run lab_workflow_lane "_lab/klein/klein-still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "klein" ]
  run lab_workflow_lane "klein-still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "klein" ]
  run lab_workflow_lane "shorts/film-go-see-90s-run-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "shorts" ]
  run lab_workflow_lane "dcc/klein-from-clay-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "dcc" ]
  run lab_workflow_lane "optional/wan-i2v-a14b-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "optional" ]
  run lab_workflow_lane "podcast-audio-first-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "audio" ]
  run lab_workflow_lane "music-rap-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "audio" ]
  run lab_workflow_lane "_lab/audio/nill-bye/phase0/music-rap-nill-bye-lab-coat-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "audio" ]
  run lab_workflow_lane "_lab/audio/drive-through/phase0/music-edm-drive-through-open-lane-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "audio" ]
  run lab_workflow_lane "prompt-forge-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "inspire" ]
  run lab_workflow_lane "beat-sheet-lab-example.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "inspire" ]
  run lab_workflow_lane "_lab/_user/keep-me.json"
  [ "${status}" -ne 0 ]
  run lab_workflow_lane "quality/NOTICE.md"
  [ "${status}" -ne 0 ]
}

@test "install_lab_workflows seeds nested _lab and preserves _user" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local src dest
  src="${TEST_TMP_DIR}/wf"
  dest="${TEST_TMP_DIR}/user_wf"
  mkdir -p \
    "${src}/_lab/klein" \
    "${src}/_lab/shorts" \
    "${src}/_lab/dcc" \
    "${src}/_lab/optional" \
    "${src}/_lab/audio/nill-bye/phase0" \
    "${src}/_lab/audio/drive-through/phase0" \
    "${src}/_user" \
    "${src}/shorts" \
    "${src}/quality/ltx-2.5" \
    "${dest}/_lab/klein" \
    "${dest}/_user"
  echo '{}' >"${src}/_lab/klein/klein-still-draft-lab-example.json"
  echo '{}' >"${src}/_lab/shorts/film-go-see-90s-run-lab-example.json"
  echo '{}' >"${src}/_lab/dcc/klein-from-clay-lab-example.json"
  echo '{}' >"${src}/_lab/optional/wan-i2v-a14b-lab-example.json"
  echo '{}' >"${src}/_lab/audio/nill-bye/phase0/music-rap-nill-bye-lab-coat-lab-example.json"
  echo '{}' >"${src}/_lab/audio/drive-through/phase0/music-edm-drive-through-open-lane-lab-example.json"
  echo '{}' >"${src}/_user/keep-me.json"
  echo 'film: go-see' >"${src}/shorts/go-see.shots.yaml"
  echo 'notice' >"${src}/quality/ltx-2.5/NOTICE.md"
  echo poison >"${dest}/_user/keep-me.json"
  echo leftover >"${dest}/klein-still-draft-lab-example.json"
  echo stale >"${dest}/_lab/klein/stale-gone-lab-example.json"
  run sync_lab_json_dir "${src}/_lab" "${dest}/_lab"
  [ "${status}" -eq 0 ]
  run install_lab_workflows "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/_lab/klein/klein-still-draft-lab-example.json ]]
  [[ -f ${dest}/_lab/shorts/film-go-see-90s-run-lab-example.json ]]
  [[ -f ${dest}/_lab/dcc/klein-from-clay-lab-example.json ]]
  [[ -f ${dest}/_lab/optional/wan-i2v-a14b-lab-example.json ]]
  [[ -f ${dest}/_lab/audio/nill-bye/phase0/music-rap-nill-bye-lab-coat-lab-example.json ]]
  [[ -f ${dest}/_lab/audio/drive-through/phase0/music-edm-drive-through-open-lane-lab-example.json ]]
  [[ ! -f ${dest}/film-go-see-90s-run-lab-example.json ]]
  [[ ! -f ${dest}/go-see.shots.yaml ]]
  [[ ! -f ${dest}/_lab/shorts/go-see.shots.yaml ]]
  [[ ! -f ${dest}/NOTICE.md ]]
  [[ ! -f ${dest}/_lab/klein/stale-gone-lab-example.json ]]
  [[ -f ${dest}/_user/keep-me.json ]]
  [[ "$(cat "${dest}/_user/keep-me.json")" == poison ]]
  [[ -f ${dest}/klein-still-draft-lab-example.json ]]
  [[ "$(cat "${dest}/klein-still-draft-lab-example.json")" == leftover ]]
  [[ "${output}" == *"in _lab/klein"* ]]
  run log_lab_seed_counts "${dest}/_lab"
  [ "${status}" -eq 0 ]
  run install_lab_workflows "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ "$(cat "${dest}/_user/keep-me.json")" == poison ]]
  run install_lab_workflows "${TEST_TMP_DIR}/missing-wf" "${TEST_TMP_DIR}/user_wf2"
  [ "${status}" -eq 0 ]
}

@test "install_lab_workflows maps legacy flat globs into _lab" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local src dest
  src="${TEST_TMP_DIR}/wf_legacy"
  dest="${TEST_TMP_DIR}/user_wf_legacy"
  mkdir -p "${src}/shorts" "${src}/dcc" "${src}/optional"
  echo '{}' >"${src}/klein-still-draft-lab-example.json"
  echo '{}' >"${src}/podcast-audio-first-lab-example.json"
  echo '{}' >"${src}/shorts/film-go-see-90s-run-lab-example.json"
  echo '{}' >"${src}/dcc/klein-from-clay-lab-example.json"
  echo '{}' >"${src}/optional/wan-i2v-a14b-lab-example.json"
  echo 'film: go-see' >"${src}/shorts/go-see.shots.yaml"
  run seed_legacy_lab_workflows "${src}" "${dest}/_lab"
  [ "${status}" -eq 0 ]
  run install_lab_workflows "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/_lab/klein/klein-still-draft-lab-example.json ]]
  [[ -f ${dest}/_lab/audio/podcast-audio-first-lab-example.json ]]
  [[ -f ${dest}/_lab/shorts/film-go-see-90s-run-lab-example.json ]]
  [[ -f ${dest}/_lab/dcc/klein-from-clay-lab-example.json ]]
  [[ -f ${dest}/_lab/optional/wan-i2v-a14b-lab-example.json ]]
  [[ ! -f ${dest}/klein-still-draft-lab-example.json ]]
  [[ ! -f ${dest}/go-see.shots.yaml ]]
  [[ -d ${dest}/_user ]]
}

@test "install_lab_workflows seeds App Mode graphs as app.json" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local src dest
  src="${TEST_TMP_DIR}/wf_apps"
  dest="${TEST_TMP_DIR}/user_wf_apps"
  mkdir -p "${src}/_lab/klein" "${src}/_lab/inspire" "${src}/_lab/shorts" "${dest}"
  printf '%s\n' '{"extra":{"linearMode":true,"lab_app_mode":{"enabled":true,"default_view":"app"}}}' \
    >"${src}/_lab/klein/klein-still-draft-lab-example.json"
  printf '%s\n' '{"extra":{"lab_app_mode":{"enabled":true,"default_view":"app"}}}' \
    >"${src}/_lab/inspire/prompt-forge-lab-example.json"
  printf '%s\n' '{"extra":{"lab_app_mode":{"enabled":true,"default_view":"graph"}}}' \
    >"${src}/_lab/shorts/film-go-see-90s-run-lab-example.json"
  echo '{}' >"${src}/_lab/klein/plain-lab-example.json"
  echo 'not json' >"${src}/_lab/klein/broken-lab-example.json"
  mkdir -p "${dest}/_lab/klein"
  echo '{}' >"${dest}/_lab/klein/klein-still-draft-lab-example.json"
  run lab_workflow_is_app "${src}/_lab/klein/klein-still-draft-lab-example.json"
  [ "${status}" -eq 0 ]
  run lab_workflow_is_app "${src}/_lab/inspire/prompt-forge-lab-example.json"
  [ "${status}" -eq 0 ]
  run lab_workflow_is_app "${src}/_lab/shorts/film-go-see-90s-run-lab-example.json"
  [ "${status}" -eq 1 ]
  run lab_workflow_is_app "${src}/_lab/klein/plain-lab-example.json"
  [ "${status}" -eq 1 ]
  run lab_workflow_is_app "${src}/_lab/klein/broken-lab-example.json"
  [ "${status}" -eq 1 ]
  run install_lab_workflows "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [ -f "${dest}/_lab/klein/klein-still-draft-lab-example.app.json" ]
  [ ! -f "${dest}/_lab/klein/klein-still-draft-lab-example.json" ]
  [ -f "${dest}/_lab/inspire/prompt-forge-lab-example.app.json" ]
  [ ! -f "${dest}/_lab/inspire/prompt-forge-lab-example.json" ]
  [ -f "${dest}/_lab/shorts/film-go-see-90s-run-lab-example.json" ]
  [ ! -f "${dest}/_lab/shorts/film-go-see-90s-run-lab-example.app.json" ]
  [ -f "${dest}/_lab/klein/plain-lab-example.json" ]
  [ ! -f "${dest}/_lab/klein/plain-lab-example.app.json" ]
  [ -f "${dest}/_lab/klein/broken-lab-example.json" ]
  [ ! -f "${dest}/_lab/klein/broken-lab-example.app.json" ]
  run apply_lab_app_json_names "${dest}/_lab"
  [ "${status}" -eq 0 ]
  run install_lab_workflows "${src}" "${dest}"
  [ "${status}" -eq 0 ]
  [ -f "${dest}/_lab/klein/klein-still-draft-lab-example.app.json" ]
  [ ! -f "${dest}/_lab/klein/klein-still-draft-lab-example.json" ]
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
  mkdir -p "${TEST_TMP_DIR}/cn/ez_ltx_spatial"
  echo 'ok' >"${TEST_TMP_DIR}/cn/ez_ltx_spatial/__init__.py"
  export LAB_CUSTOM_NODES_SRC="${TEST_TMP_DIR}/cn"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  export LAB_OUTPUTS_MOUNT="${TEST_TMP_DIR}/outputs_main"
  run main
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"LAB_ENTRYPOINT_NO_EXEC"* || "${output}" == *"phase"* || "${output}" == *"refresh"* ]]
  [[ -L ${COMFY_HOME}/output ]]
  [[ -f ${COMFY_HOME}/custom_nodes/ez_ltx_spatial/__init__.py ]]
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
  export COMFYUI_REF="v0.34.6"
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
  [[ -L ${COMFY_HOME}/models/llm ]]

  run apply_free_memory_patch
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"not found"* || "${output}" == *"patch"* || -z ${output} ]]

  run apply_unified_memory_copy_patch
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"not found"* || "${output}" == *"patch"* || -z ${output} ]]

  run apply_magcache_compat_patch
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"not found"* || "${output}" == *"patch"* || "${output}" == *"magcache"* || -z ${output} ]]

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
  COMFYUI_REF="v0.34.6"
  run write_comfy_pin
  [ "${status}" -eq 0 ]
  run read_comfy_pin
  [ "${output}" = "v0.34.6" ]
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
  COMFYUI_REF="v0.34.6"
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
  COMFYUI_REF="v0.34.6"
  run refresh_comfy_pin_if_needed
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cloning"* || "${output}" == *"Syncing"* ]]
  run read_comfy_pin
  [ "${output}" = "v0.34.6" ]
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
  mkdir -p "${pre}/custom_nodes/_user" "${COMFY_HOME}/custom_nodes/_user"
  echo poison >"${pre}/custom_nodes/_user/poison.py"
  echo keep >"${COMFY_HOME}/custom_nodes/_user/mine.py"
  COMFYUI_REF="v0.34.6"
  run refresh_comfy_pin_if_needed
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_HOME}/from_image.txt ]]
  [[ -f ${COMFY_HOME}/custom_nodes/_user/mine.py ]]
  [[ ! -f ${COMFY_HOME}/custom_nodes/_user/poison.py ]]
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
  COMFYUI_REF="v0.34.6"
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
  export VENV="${root}/.venv"
  export LAB_PARTS_ROOT="${parts}"
  export LAB_PACKAGE_PARTS=1
  run package_prebuilt_parts
  [ "${status}" -eq 0 ]
  [[ -f ${parts}/venv/bin/python ]]
  [[ -f ${parts}/venv-extra/.lab-venv-extra ]]
  [[ -f ${parts}/app/main.py ]]
  [[ -f ${parts}/app/custom_nodes/demo/node.py ]]
  [[ ! -e ${parts}/app/.venv ]]
  run venv_extra_has_torch "${parts}/venv-extra"
  [ "${status}" -ne 0 ]
  # Disabled path is a no-op
  export LAB_PACKAGE_PARTS=0
  run package_prebuilt_parts
  [ "${status}" -eq 0 ]
}

@test "snapshot_torch_venv plus package_prebuilt_parts overlays extra pip only" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  local root parts
  root="${TEST_TMP_DIR}/prebuilt_overlay"
  parts="${TEST_TMP_DIR}/parts_overlay"
  mkdir -p "${root}/.venv/lib/python3.12/site-packages/torch" \
    "${root}/custom_nodes/demo"
  echo torch >"${root}/.venv/lib/python3.12/site-packages/torch/__init__.py"
  echo app >"${root}/main.py"
  export COMFY_HOME="${root}"
  export VENV="${root}/.venv"
  export LAB_PARTS_ROOT="${parts}"
  export LAB_PACKAGE_PARTS=1
  run snapshot_torch_venv
  [ "${status}" -eq 0 ]
  [[ -f ${parts}/venv/lib/python3.12/site-packages/torch/__init__.py ]]
  mkdir -p "${root}/.venv/lib/python3.12/site-packages/einops"
  echo extra >"${root}/.venv/lib/python3.12/site-packages/einops/__init__.py"
  run package_prebuilt_parts
  [ "${status}" -eq 0 ]
  [[ -f ${parts}/venv/lib/python3.12/site-packages/torch/__init__.py ]]
  [[ -f ${parts}/venv-extra/lib/python3.12/site-packages/einops/__init__.py ]]
  [[ ! -f ${parts}/venv-extra/lib/python3.12/site-packages/torch/__init__.py ]]
  run venv_extra_has_torch "${parts}/venv-extra"
  [ "${status}" -ne 0 ]
  run venv_extra_has_torch "${parts}/venv"
  [ "${status}" -eq 0 ]
}

@test "write_torch_pip_constraint and assert_torch_cuda" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  local cfile
  cfile="${TEST_TMP_DIR}/torch-constraint.txt"
  install_mock_bin pip 'printf "torch==2.14.0+cu130\ntorchvision==0.25.0+cu130\nrequests==2.0\n"'
  run write_torch_pip_constraint "${cfile}"
  [ "${status}" -eq 0 ]
  grep -q '^torch==' "${cfile}"
  grep -q '^torchvision==' "${cfile}"
  ! grep -q requests "${cfile}"
  install_mock_bin pip 'printf "requests==2.0\n"'
  run write_torch_pip_constraint "${cfile}"
  [ "${status}" -ne 0 ]
  run assert_torch_cuda
  # Hermetic hosts: torch missing (2) or CPU-only (1); CUDA (0) is also fine.
  [[ "${status}" -eq 0 || "${status}" -eq 1 || "${status}" -eq 2 ]]
}

@test "default pins are non-empty validated tags" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  [[ -n ${COMFYUI_REF} ]]
  [[ "${COMFYUI_REF}" == v0.* ]]
  [[ -n ${COMFYUI_MANAGER_REF} ]]
  [[ -n ${COMFYUI_NUNCHAKU_NODE_REF} ]]
  [[ "${COMFYUI_NUNCHAKU_NODE_REF}" == v* ]]
  [[ "${COMFYUI_OPENCUT_REF}" == "0.5.0" ]]
  [[ ${#COMFYUI_MAGCACHE_REF} -ge 7 ]]
  [[ ${#COMFYUI_LTX_DIRECTOR_REF} -ge 7 ]]
  [[ -n ${TORCH_VERSION} ]]
  [[ "${TORCH_INDEX_URL}" == *cu130* ]]
}

@test "install-comfy modules exist for Docker phase COPY contract" {
  [[ -f ${REPO_ROOT}/docker/install-comfy/core.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/common.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-venv-torch.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-comfy.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-nodes.sh ]]
  [[ -f ${REPO_ROOT}/docker/install-comfy/phase-finalize.sh ]]
  run grep -F 'TORCH_VERSION' "${REPO_ROOT}/docker/install-comfy/core.sh"
  [ "${status}" -eq 0 ]
  # Comfy pins must not live in the torch-stage COPY
  run grep -E 'COMFYUI_REF=' "${REPO_ROOT}/docker/install-comfy/core.sh"
  [ "${status}" -ne 0 ]
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

@test "comfy_exec_args is Kitchen XOR Sage and never highvram" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  run comfy_exec_args
  [ "${status}" -eq 0 ]
  local args="${output}"
  [[ "${args}" == *"--use-ck-attention"* ]]
  [[ "${args}" == *"--disable-mmap"* ]]
  [[ "${args}" == *"--bf16-unet"* ]]
  [[ "${args}" == *"--input-directory"* ]]
  [[ "${args}" == *"--output-directory"* ]]
  # One token per line from comfy_exec_args. grep -Fx so bash 3.2 set -e
  # does not swallow a failed [[ != ]] in the middle of the test function.
  run grep -Fx -- '--use-sage-attention' <<< "${args}"
  [ "${status}" -ne 0 ]
  run grep -Fx -- '--highvram' <<< "${args}"
  [ "${status}" -ne 0 ]
  run grep -Fx -- '--gpu-only' <<< "${args}"
  [ "${status}" -ne 0 ]
  run grep -Fx -- '--lowvram' <<< "${args}"
  [ "${status}" -ne 0 ]
  run grep -Fx -- '--normalvram' <<< "${args}"
  [ "${status}" -ne 0 ]
}

@test "install_sage_wheel_if_pinned skips without URL and refuses URL without sha" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/install-comfy.sh"
  unset LAB_SAGE_WHEEL_URL
  unset LAB_SAGE_WHEEL_SHA256
  run install_sage_wheel_if_pinned
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Kitchen"* || "${output}" == *"skipped"* ]]
  export LAB_SAGE_WHEEL_URL="https://example.invalid/sage.whl"
  unset LAB_SAGE_WHEEL_SHA256
  run install_sage_wheel_if_pinned
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"SHA256"* || "${output}" == *"refusing"* ]]
  export LAB_SAGE_WHEEL_SHA256="deadbeef"
  pip_install() { echo "pip ${1}"; return 0; }
  run install_sage_wheel_if_pinned
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"pip ok"* || "${output}" == *"pinned"* ]]
  pip_install() { return 1; }
  run install_sage_wheel_if_pinned
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"failed"* || "${output}" == *"optional"* ]]
}

@test "ensure_llama_cpp_cpu installs CPU wheel when Llama missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export DUB_PIP_LOG="${TEST_TMP_DIR}/llama_pip.log"
  : >"${DUB_PIP_LOG}"
  cat >"${TEST_TMP_DIR}/fake-python-llama" <<'PY'
#!/usr/bin/env bash
log="${DUB_PIP_LOG:?}"
if [[ ${1} == -c ]]; then
  case "${2}" in
    *llama_cpp*|*Llama*) exit "${LLAMA_IMPORT_RC:-1}" ;;
  esac
  exit 0
fi
if [[ ${1} == -m && ${2} == pip ]]; then
  printf '%s\n' "$*" >>"${log}"
  if [[ ${LLAMA_PIP_FAIL:-0} == 1 ]]; then
    exit 1
  fi
  exit 0
fi
exit 0
PY
  chmod +x "${TEST_TMP_DIR}/fake-python-llama"
  export COMFY_HOME="${TEST_TMP_DIR}/comfy_llama"
  mkdir -p "${COMFY_HOME}/.venv/bin"
  cp "${TEST_TMP_DIR}/fake-python-llama" "${COMFY_HOME}/.venv/bin/python"
  chmod +x "${COMFY_HOME}/.venv/bin/python"
  unset VIRTUAL_ENV

  run grep -F 'ensure_llama_cpp_cpu' "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'https://abetlen.github.io/llama-cpp-python/whl/cpu' \
    "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -eq 0 ]
  run grep -E 'extra-index-url[^[:cntrl:]]*cu1' \
    "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -ne 0 ]

  : >"${DUB_PIP_LOG}"
  export LLAMA_IMPORT_RC=1
  run ensure_llama_cpp_cpu
  [ "${status}" -eq 0 ]
  grep -q 'llama-cpp-python' "${DUB_PIP_LOG}"
  grep -q 'extra-index-url' "${DUB_PIP_LOG}"
  grep -q 'only-binary' "${DUB_PIP_LOG}"
  if grep -E 'cu11|cu12|cu13' "${DUB_PIP_LOG}"; then
    return 1
  fi

  : >"${DUB_PIP_LOG}"
  export LLAMA_IMPORT_RC=0
  run ensure_llama_cpp_cpu
  [ "${status}" -eq 0 ]
  [[ ! -s ${DUB_PIP_LOG} ]]

  export LLAMA_PIP_FAIL=1
  export LLAMA_IMPORT_RC=1
  run install_llama_cpp_cpu_wheel "${COMFY_HOME}/.venv/bin/python"
  [ "${status}" -eq 0 ]
}

@test "ensure_dub_wheels installs ASR when WhisperModel missing" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export DUB_PIP_LOG="${TEST_TMP_DIR}/dub_pip.log"
  : >"${DUB_PIP_LOG}"
  cat >"${TEST_TMP_DIR}/fake-python" <<'PY'
#!/usr/bin/env bash
log="${DUB_PIP_LOG:?}"
if [[ ${1} == -c ]]; then
  case "${2}" in
    *WhisperModel*) exit "${WHISPER_IMPORT_RC:-1}" ;;
    *t3_model*) exit "${CLONE_T3_RC:-${CLONE_IMPORT_RC:-1}}" ;;
    *ChatterboxMultilingualTTS*) exit "${CLONE_IMPORT_RC:-1}" ;;
  esac
  exit 0
fi
if [[ ${1} == -m && ${2} == pip ]]; then
  printf '%s\n' "$*" >>"${log}"
  if [[ ${DUB_PIP_FAIL:-0} == 1 ]]; then
    exit 1
  fi
  exit 0
fi
exit 0
PY
  chmod +x "${TEST_TMP_DIR}/fake-python"
  export COMFY_HOME="${TEST_TMP_DIR}/comfy_dub"
  mkdir -p "${COMFY_HOME}/.venv/bin"
  cp "${TEST_TMP_DIR}/fake-python" "${COMFY_HOME}/.venv/bin/python"
  chmod +x "${COMFY_HOME}/.venv/bin/python"
  local py="${COMFY_HOME}/.venv/bin/python"

  run grep -F 'ensure_dub_wheels' "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'dub_chatterbox_has_t3_v3' "${REPO_ROOT}/docker/entrypoint.sh"
  [ "${status}" -eq 0 ]
  run dub_chatterbox_has_t3_v3 "${py}"
  [ "${status}" -ne 0 ]
  run dub_python_can_import "${py}" "from faster_whisper import WhisperModel"
  [ "${status}" -ne 0 ]
  run install_dub_asr_wheel "${py}"
  [ "${status}" -eq 0 ]
  run install_dub_clone_wheel "${py}"
  [ "${status}" -eq 0 ]
  : >"${DUB_PIP_LOG}"
  run ensure_dub_wheels
  [ "${status}" -eq 0 ]
  grep -q 'faster-whisper' "${DUB_PIP_LOG}"
  grep -q -- '--no-deps' "${DUB_PIP_LOG}"
  grep -q -- '--force-reinstall' "${DUB_PIP_LOG}"
  grep -q 'resemble-ai/chatterbox' "${DUB_PIP_LOG}"
  if grep -E 'faster-whisper.*chatterbox' "${DUB_PIP_LOG}"; then
    return 1
  fi

  : >"${DUB_PIP_LOG}"
  export WHISPER_IMPORT_RC=0
  export CLONE_IMPORT_RC=0
  export CLONE_T3_RC=0
  run ensure_dub_wheels
  [ "${status}" -eq 0 ]
  [[ ! -s ${DUB_PIP_LOG} ]]

  : >"${DUB_PIP_LOG}"
  export CLONE_T3_RC=1
  run ensure_dub_wheels
  [ "${status}" -eq 0 ]
  grep -q -- '--no-deps' "${DUB_PIP_LOG}"
  grep -q 'resemble-ai/chatterbox' "${DUB_PIP_LOG}"

  export DUB_PIP_FAIL=1
  export WHISPER_IMPORT_RC=1
  run install_dub_asr_wheel "${py}"
  [ "${status}" -eq 0 ]
}

@test "comfy_runtime_python prefers VIRTUAL_ENV over volume venv" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export DUB_PIP_LOG="${TEST_TMP_DIR}/dub_pip_live.log"
  : >"${DUB_PIP_LOG}"
  cat >"${TEST_TMP_DIR}/live-python" <<'PY'
#!/usr/bin/env bash
log="${DUB_PIP_LOG:?}"
if [[ ${1} == -c ]]; then
  case "${2}" in
    *WhisperModel*) exit "${WHISPER_IMPORT_RC:-1}" ;;
    *t3_model*) exit "${CLONE_T3_RC:-${CLONE_IMPORT_RC:-1}}" ;;
    *ChatterboxMultilingualTTS*) exit "${CLONE_IMPORT_RC:-1}" ;;
  esac
  exit 0
fi
if [[ ${1} == -m && ${2} == pip ]]; then
  printf '%s\n' "$*" >>"${log}"
  exit 0
fi
exit 0
PY
  chmod +x "${TEST_TMP_DIR}/live-python"
  export VIRTUAL_ENV="${TEST_TMP_DIR}/livevenv"
  mkdir -p "${VIRTUAL_ENV}/bin" "${COMFY_HOME}/.venv/bin"
  cp "${TEST_TMP_DIR}/live-python" "${VIRTUAL_ENV}/bin/python"
  printf '#!/usr/bin/env bash\nexit 1\n' >"${COMFY_HOME}/.venv/bin/python"
  chmod +x "${VIRTUAL_ENV}/bin/python" "${COMFY_HOME}/.venv/bin/python"
  export WHISPER_IMPORT_RC=1
  export CLONE_IMPORT_RC=1
  run comfy_runtime_python
  [ "${status}" -eq 0 ]
  [[ "${output}" == "${VIRTUAL_ENV}/bin/python" ]]
  run ensure_dub_wheels
  [ "${status}" -eq 0 ]
  grep -q 'faster-whisper' "${DUB_PIP_LOG}"
  unset VIRTUAL_ENV
}

@test "ensure_user_custom_node_stub writes empty pack and keeps operator init" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  local dest="${TEST_TMP_DIR}/custom_nodes/_user"
  run ensure_user_custom_node_stub "${dest}"
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/__init__.py ]]
  grep -q 'NODE_CLASS_MAPPINGS' "${dest}/__init__.py"
  echo 'keep = True' >"${dest}/__init__.py"
  run ensure_user_custom_node_stub "${dest}"
  [ "${status}" -eq 0 ]
  grep -q 'keep = True' "${dest}/__init__.py"
}

@test "configure_nunchaku_pack disables when engine missing and re-enables" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export COMFY_HOME="${TEST_TMP_DIR}/nunchaku_home"
  mkdir -p "${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku" "${COMFY_HOME}/.venv/bin"
  echo pack >"${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku/__init__.py"
  cat >"${COMFY_HOME}/.venv/bin/python" <<'PY'
#!/usr/bin/env bash
if [[ ${1} == -c && ${2} == *nunchaku* ]]; then
  exit "${NUNCHAKU_IMPORT_RC:-1}"
fi
exit 0
PY
  chmod +x "${COMFY_HOME}/.venv/bin/python"
  export NUNCHAKU_IMPORT_RC=1
  run nunchaku_engine_importable "${COMFY_HOME}/.venv/bin/python"
  [ "${status}" -ne 0 ]
  run configure_nunchaku_pack
  [ "${status}" -eq 0 ]
  [[ -d ${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku.disabled ]]
  [[ ! -d ${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku ]]
  [[ "${output}" == *"disabled"* ]]
  run configure_nunchaku_pack
  [ "${status}" -eq 0 ]
  export NUNCHAKU_IMPORT_RC=0
  run configure_nunchaku_pack
  [ "${status}" -eq 0 ]
  [[ -d ${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku ]]
  [[ ! -d ${COMFY_HOME}/custom_nodes/ComfyUI-nunchaku.disabled ]]
  [[ "${output}" == *"enabled"* ]]
}

@test "seed_clay_inputs_if_missing writes plates via LAB_SEED_CLAY_PY" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  export LAB_SEED_CLAY_PY="${REPO_ROOT}/docker/seed_clay_inputs.py"
  export LAB_INPUTS_MOUNT="${TEST_TMP_DIR}/clay_inputs"
  run seed_clay_inputs_if_missing
  [ "${status}" -eq 0 ]
  [[ -f ${LAB_INPUTS_MOUNT}/ez_house_clay_01.png ]]
  [[ -f ${LAB_INPUTS_MOUNT}/ez_house_clay_10.png ]]
  export LAB_SEED_CLAY_PY="${TEST_TMP_DIR}/missing_seed.py"
  run seed_clay_inputs_if_missing
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"missing"* ]]
}

@test "entrypoint main writes _user stub" {
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/docker/entrypoint.sh"
  mkdir -p "${VENV}/bin"
  printf '#!/usr/bin/env bash\necho ok\n' >"${VENV}/bin/python"
  chmod +x "${VENV}/bin/python"
  printf 'export VIRTUAL_ENV=1\n' >"${VENV}/bin/activate"
  : >"${STAMP}"
  export LAB_ENTRYPOINT_INSTALL_CMD="true"
  export LAB_ENTRYPOINT_NO_EXEC=1
  export LAB_OUTPUTS_MOUNT="${TEST_TMP_DIR}/outputs_stub"
  run main
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_HOME}/custom_nodes/_user/__init__.py ]]
  grep -q 'NODE_CLASS_MAPPINGS' "${COMFY_HOME}/custom_nodes/_user/__init__.py"
}
