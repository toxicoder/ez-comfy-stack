#!/usr/bin/env bats
#
# Cover scripts/utilities/blender-guide.sh (occupancy, size snap, missing blender).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export BG="${UTILITIES_DIR}/blender-guide.sh"
  chmod +x "${BG}"
  # shellcheck disable=SC1090
  source "${BG}"
}

teardown() {
  teardown_repo_env
}

@test "blender-guide help and occupancy refuse" {
  run bash "${BG}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"1280x704"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  run refuse_if_comfy_running "guide pack dump (occupancy)"
  [ "${status}" -eq 2 ]
  FILM=go-see
  SHOT_ID=12
  run cmd_run
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"occupancy"* ]]
}

@test "blender-guide missing blender and size refuse" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  export PATH="${TEST_TMP_DIR}/bin:/usr/bin:/bin"
  FILM=go-see
  SHOT_ID=12
  WIDTH=1280
  HEIGHT=720
  run require_ltx_size
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"704"* ]]
  WIDTH=1280
  HEIGHT=704
  run require_ltx_size
  [ "${status}" -eq 0 ]
  run require_blender
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
}

@test "blender-guide parse_args normalize_shot_id default_out_dir" {
  parse_args --engine blender --film go-see --shot 12 --frames 120 --width 1280 --height 704
  [ "${FILM}" = "go-see" ]
  [ "${SHOT_ID}" = "12" ]
  [ "${ENGINE}" = "blender" ]
  run normalize_shot_id 12
  [ "${output}" = "12" ]
  run normalize_shot_id 3
  [ "${output}" = "03" ]
  FILM=go-see
  SHOT_ID=12
  run default_out_dir
  [[ "${output}" == *"/guides/go-see/12" ]]
  run parse_args --nope
  [ "${status}" -ne 0 ]
}

@test "blender-guide mock blender copies fixture then QC" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  local dest
  dest="${TEST_TMP_DIR}/guides/go-see/12"
  mkdir -p "${dest}"
  install_mock_bin blender "dest=\"${dest}\"; fixture=\"${REPO_ROOT}/tests/fixtures/dcc/suzanne-12\"; mkdir -p \"\${dest}\"; cp \"\${fixture}/shot.yaml\" \"\${fixture}/first.png\" \"\${fixture}/last.png\" \"\${dest}/\"; : >\"\${dest}/clay.mp4\"; : >\"\${dest}/depth.mp4\"; echo blender-ok; exit 0"
  FILM=go-see
  SHOT_ID=12
  OUT_DIR="${dest}"
  WIDTH=1280
  HEIGHT=704
  FRAMES=120
  ENGINE=blender
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"guide pack ok"* ]]
  run validate_pack_dir "${dest}" --fixture
  [ "${status}" -eq 0 ]
}

@test "blender-guide godot engine refused in P0" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  FILM=go-see
  SHOT_ID=12
  ENGINE=godot
  WIDTH=1280
  HEIGHT=704
  FRAMES=120
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"blender"* ]]
}
