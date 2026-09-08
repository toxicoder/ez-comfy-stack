#!/usr/bin/env bats
#
# Cover scripts/utilities/house-views.sh (occupancy, size, missing blender, godot).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export HV="${UTILITIES_DIR}/house-views.sh"
  chmod +x "${HV}"
  # shellcheck disable=SC1090
  source "${HV}"
}

teardown() {
  teardown_repo_env
}

@test "house-views help and occupancy refuse" {
  run bash "${HV}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"1024x1280"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  run refuse_if_comfy_running "house views dump (occupancy)"
  [ "${status}" -eq 2 ]
  SLUG=lab-penthouse
  run cmd_run
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"occupancy"* ]]
}

@test "house-views missing blender and size refuse" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  export PATH="${TEST_TMP_DIR}/bin:/usr/bin:/bin"
  SLUG=lab-penthouse
  WIDTH=1280
  HEIGHT=720
  run require_ig_size
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"1024"* ]]
  WIDTH=1280
  HEIGHT=704
  run require_ig_size
  [ "${status}" -eq 1 ]
  WIDTH=1024
  HEIGHT=1280
  run require_ig_size
  [ "${status}" -eq 0 ]
  run require_blender
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
}

@test "house-views parse_args default_out_dir" {
  parse_args --engine blender --slug lab-penthouse --width 1024 --height 1280
  [ "${SLUG}" = "lab-penthouse" ]
  [ "${ENGINE}" = "blender" ]
  run default_out_dir
  [[ "${output}" == *"/assets/sets/lab-penthouse" ]]
  run default_layout
  [[ "${output}" == *"house_layout.yaml" ]]
  run parse_args --nope
  [ "${status}" -ne 0 ]
}

@test "house-views godot engine refused in P0" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  SLUG=lab-penthouse
  ENGINE=godot
  WIDTH=1024
  HEIGHT=1280
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"blender"* ]]
}

@test "house-views mock blender copies fixture then QC" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  local dest
  dest="${TEST_TMP_DIR}/assets/sets/lab-penthouse"
  mkdir -p "${dest}"
  install_mock_bin blender "dest=\"${dest}\"; python3 \"${REPO_ROOT}/scripts/lib/house_layout.py\" fixture \"\${dest}\" --slug lab-penthouse >/dev/null; mkdir -p \"\${dest}/mesh\"; echo glTF >\"\${dest}/mesh/house.glb\"; cp \"${REPO_ROOT}/schemas/house_layout.yaml\" \"\${dest}/layout.yaml\"; echo blender-ok; exit 0"
  SLUG=lab-penthouse
  OUT_DIR="${dest}"
  WIDTH=1024
  HEIGHT=1280
  ENGINE=blender
  LAYOUT="${REPO_ROOT}/schemas/house_layout.yaml"
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"house views ok"* ]]
  run validate_pack_dir "${dest}"
  [ "${status}" -eq 0 ]
}
