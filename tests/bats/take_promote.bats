#!/usr/bin/env bats
#
# Cover take-promote.sh.

load 'test_helper'

setup() {
  setup_repo_env
  export TP="${UTILITIES_DIR}/take-promote.sh"
  chmod +x "${TP}"
  # shellcheck disable=SC1090
  source "${TP}"
}

teardown() {
  teardown_repo_env
}

@test "take-promote slug usage and missing jobstore" {
  run film_slug go-see
  [ "${output}" = "gosee" ]
  run promote_run
  [ "${status}" -ne 0 ]
  run promote_run go-see 12 1
  [ "${status}" -ne 0 ]
}

@test "take-promote copies take to shots" {
  run bash "${UTILITIES_DIR}/compile-film.sh" go-see
  [ "${status}" -eq 0 ]
  local dest take
  dest="${COMFY_OUTPUT_DIR}/films/gosee"
  mkdir -p "${dest}/takes/12"
  take="${dest}/takes/12/t001.mp4"
  echo take >"${take}"
  PYTHONPATH="${REPO_ROOT}/custom_nodes" python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "${REPO_ROOT}/custom_nodes")
from ez_film.jobstore import load_state, mark_shot, save_state
dest = Path("${dest}")
state = load_state(dest)
mark_shot(state, "12", "running")
save_state(dest, state)
PY
  run promote_run go-see 12 1
  [ "${status}" -eq 0 ]
  [[ -f ${dest}/shots/12.mp4 ]]
  [[ $(cat "${dest}/shots/12.mp4") == "take" ]]
}
