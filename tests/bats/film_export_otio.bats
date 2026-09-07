#!/usr/bin/env bats
#
# Cover film-export-otio.sh.

load 'test_helper'

setup() {
  setup_repo_env
  export FE="${UTILITIES_DIR}/film-export-otio.sh"
  chmod +x "${FE}"
  # shellcheck disable=SC1090
  source "${FE}"
}

teardown() {
  teardown_repo_env
}

@test "film-export-otio slug and missing jobstore" {
  run film_slug go-see
  [ "${output}" = "gosee" ]
  run film_slug nope
  [ "${status}" -ne 0 ]
  run export_otio
  [ "${status}" -ne 0 ]
  run export_otio go-see
  [ "${status}" -ne 0 ]
}

@test "film-export-otio writes otio from compiled film" {
  run bash "${UTILITIES_DIR}/compile-film.sh" go-see
  [ "${status}" -eq 0 ]
  mkdir -p "${COMFY_OUTPUT_DIR}/films/gosee/shots"
  echo x >"${COMFY_OUTPUT_DIR}/films/gosee/shots/01.mp4"
  PYTHONPATH="${REPO_ROOT}/custom_nodes" python3 - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "${REPO_ROOT}/custom_nodes")
from ez_film.jobstore import load_state, mark_shot, save_state
dest = Path("${COMFY_OUTPUT_DIR}/films/gosee")
state = load_state(dest)
mark_shot(state, "01", "ok", mp4="shots/01.mp4")
save_state(dest, state)
PY
  run export_otio go-see
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/films/gosee/publish/gosee.otio ]]
}
