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
  [[ "${output}" == *"/inputs"* ]]
  [[ "${output}" == *"--install-inputs"* ]]
  [[ "${output}" == *"--seed-inputs"* ]]
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
  [ "${INSTALL_INPUTS}" -eq 0 ]
  [ "${SEED_INPUTS}" -eq 0 ]
  run default_out_dir
  [[ "${output}" == *"/assets/sets/lab-penthouse" ]]
  run default_input_dir
  [[ "${output}" == *"/input" ]]
  [[ "${output}" != *"/input/input" ]]
  run default_layout
  [[ "${output}" == *"house_layout.yaml" ]]
  parse_args --slug lab-penthouse --install-inputs
  [ "${INSTALL_INPUTS}" -eq 1 ]
  parse_args --slug lab-penthouse --seed-inputs
  [ "${SEED_INPUTS}" -eq 1 ]
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
  [ -f "${COMFY_OUTPUT_DIR}/input/ez_house_clay_01.png" ]
  [ -f "${COMFY_OUTPUT_DIR}/input/ez_house_clay_10.png" ]
}

@test "house-views --install-inputs copies without blender while compose is up" {
  touch "${TEST_TMP_DIR}/compose_running"
  local dest input
  dest="${TEST_TMP_DIR}/assets/sets/lab-penthouse"
  input="${COMFY_OUTPUT_DIR}/input"
  python3 "${REPO_ROOT}/scripts/lib/house_layout.py" fixture "${dest}" --slug lab-penthouse
  SLUG=lab-penthouse
  OUT_DIR="${dest}"
  INPUT_DIR="${input}"
  INSTALL_INPUTS=1
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"installed clay"* ]]
  [ -f "${input}/ez_house_clay_01.png" ]
  [ -f "${input}/ez_house_clay_10.png" ]
  run copy_clay_inputs "${dest}" "${input}"
  [ "${status}" -eq 0 ]
}

@test "house-views --seed-inputs renders without blender while compose is up" {
  touch "${TEST_TMP_DIR}/compose_running"
  local input
  input="${COMFY_OUTPUT_DIR}/input"
  SLUG=lab-penthouse
  INPUT_DIR="${input}"
  LAYOUT="${REPO_ROOT}/schemas/house_layout.yaml"
  SEED_INPUTS=1
  INSTALL_INPUTS=0
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"seeded clay"* ]]
  [ -f "${input}/ez_house_clay_01.png" ]
  [ -f "${input}/ez_house_clay_10.png" ]
  run cmd_seed_inputs
  [ "${status}" -eq 0 ]
}

@test "house-views --install-inputs fails closed when pack clay is missing" {
  touch "${TEST_TMP_DIR}/compose_running"
  SLUG=lab-penthouse
  OUT_DIR="${TEST_TMP_DIR}/missing-pack"
  INSTALL_INPUTS=1
  run cmd_install_inputs
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"failed to copy clay"* ]] || [[ "${output}" == *"missing clay"* ]]
}
