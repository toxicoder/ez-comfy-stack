#!/usr/bin/env bats
#
# Cover scripts/utilities/blender-stills.sh (occupancy, size, missing blender).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export BS="${UTILITIES_DIR}/blender-stills.sh"
  chmod +x "${BS}"
  # shellcheck disable=SC1090
  source "${BS}"
}

teardown() {
  teardown_repo_env
}

@test "blender-stills help and occupancy refuse" {
  run bash "${BS}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"1024x1024"* ]]
  [[ "${output}" == *"Dockerfile"* ]]
  run cmd_help
  [ "${status}" -eq 0 ]
  touch "${TEST_TMP_DIR}/compose_running"
  FILM=go-see
  PLATE=mug
  run cmd_run
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"occupancy"* ]]
}

@test "blender-stills missing blender and size refuse" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  export PATH="${TEST_TMP_DIR}/bin:/usr/bin:/bin"
  FILM=go-see
  PLATE=mug
  SIZE=1920x1080
  run require_still_size
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"720"* ]] || [[ "${output}" == *"1080"* ]]
  SIZE=1024x1024
  run require_still_size
  [ "${status}" -eq 0 ]
  [ "${WIDTH}" -eq 1024 ]
  [ "${HEIGHT}" -eq 1024 ]
  run require_blender
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"not on PATH"* ]]
}

@test "blender-stills parse_args default_out_dir" {
  parse_args --engine blender --film go-see --plate mug --size 768x1280 --print klein-from-canny
  [ "${FILM}" = "go-see" ]
  [ "${PLATE}" = "mug" ]
  [ "${SIZE}" = "768x1280" ]
  [ "${PRINT_MODE}" = "klein-from-canny" ]
  run default_out_dir
  [[ "${output}" == *"/guides/go-see/stills/mug" ]]
  run parse_args --nope
  [ "${status}" -ne 0 ]
}

@test "blender-stills install-inputs copies first.png without blender" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  local dest input
  dest="${TEST_TMP_DIR}/guides/go-see/stills/mug"
  input="${TEST_TMP_DIR}/input"
  mkdir -p "${dest}" "${input}"
  python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "${REPO_ROOT}/scripts/lib")
import guide_pack as gp
dest = Path("${dest}")
gp.write_solid_png(dest / "first.png", 1024, 1024, (8, 8, 8))
gp.write_solid_png(dest / "canny.png", 1024, 1024, (1, 1, 1))
gp.write_still_yaml(dest / "still.yaml", {
    "schema": gp.STILL_SCHEMA,
    "slug": "go-see",
    "plate": "mug",
    "engine": "blender",
    "print": "klein-from-clay",
    "size": [1024, 1024],
    "layers": ["rgb", "canny", "first"],
})
PY
  FILM=go-see
  PLATE=mug
  OUT_DIR="${dest}"
  INPUT_DIR="${input}"
  INSTALL_INPUTS=1
  run cmd_run
  [ "${status}" -eq 0 ]
  [ -f "${input}/ez_clay_still_mug.png" ]
  [ -f "${input}/ez_canny_still_mug.png" ]
  run validate_still_dir "${dest}"
  [ "${status}" -eq 0 ]
}

@test "blender-stills godot engine refused in P0" {
  rm -f "${TEST_TMP_DIR}/compose_running"
  FILM=go-see
  PLATE=mug
  ENGINE=godot
  SIZE=1024x1024
  run cmd_run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"blender"* ]]
}
