#!/usr/bin/env bash
#
# ## house-views
#
# Occupancy-gated Blender dump of an ez.house.views.v1 pack (ten Instagram
# 4:5 Workbench clay + depth stills + greybox GLB). Never in docker/Dockerfile.
#
# Usage:
#   ./scripts/utilities/house-views.sh --slug lab-penthouse
#   ./scripts/utilities/house-views.sh --slug lab-penthouse --layout FILE
#
# Safety:
#   Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
#   Do not weaken restart: "no", headroom, or download-limit clear-on-exit.
#
# Exit codes:
#   0 success; 1 usage / missing blender / QC fail; 2 compose running
#
# @command house-views

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/occupancy.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/occupancy.sh"

ENGINE="blender"
SLUG=""
LAYOUT=""
OUT_DIR=""
INPUT_DIR=""
INSTALL_INPUTS=0
SEED_INPUTS=0
WIDTH=1024
HEIGHT=1280

#######################################
# Print usage.
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: house-views.sh --slug SLUG [--layout FILE] [--out DIR] [--input-dir DIR]" >&2
  echo "       house-views.sh --slug SLUG --install-inputs [--out DIR] [--input-dir DIR]" >&2
  echo "       house-views.sh [--slug SLUG] --seed-inputs [--out DIR] [--input-dir DIR] [--layout FILE]" >&2
  echo "  Host Blender dump of a 1024x1280 Instagram 4:5 clay tour (ten cameras)." >&2
  echo "  Clay copies go to COMFY_OUTPUT_DIR/input (container /inputs) for LoadImage." >&2
  echo "  --install-inputs copies an existing dump into input/ (no Blender; compose may stay up)." >&2
  echo "  --seed-inputs copies a pack when present, else renders the layout (no Blender;" >&2
  echo "  compose may stay up). Does not overwrite valid existing ez_house_clay_NN.png." >&2
  echo "  Dump refuses if compose is up (exit 2). Never in docker/Dockerfile." >&2
  echo "  Godot is P2. Default layout: schemas/house_layout.yaml" >&2
  echo "  See docs/learn/dream-house.md" >&2
  return 0
}

#######################################
# Parse CLI into globals.
# Globals:
#   ENGINE, SLUG, LAYOUT, OUT_DIR, INPUT_DIR, INSTALL_INPUTS, SEED_INPUTS, WIDTH, HEIGHT
# Arguments:
#   $@
# Outputs:
#   Help; errors on unknown args
# Returns:
#   0; exits 0 on help
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --engine)
        ENGINE="${2:?}"
        shift
        ;;
      --slug)
        SLUG="${2:?}"
        shift
        ;;
      --layout)
        LAYOUT="${2:?}"
        shift
        ;;
      --out)
        OUT_DIR="${2:?}"
        shift
        ;;
      --input-dir)
        INPUT_DIR="${2:?}"
        shift
        ;;
      --install-inputs)
        INSTALL_INPUTS=1
        ;;
      --seed-inputs)
        SEED_INPUTS=1
        ;;
      --width)
        WIDTH="${2:?}"
        shift
        ;;
      --height)
        HEIGHT="${2:?}"
        shift
        ;;
      -h | --help)
        cmd_help
        exit 0
        ;;
      --)
        shift
        break
        ;;
      *)
        err "Unknown arg: $1"
        cmd_help
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# Default dump directory under COMFY_OUTPUT_DIR/assets/sets/<slug>.
# Globals:
#   COMFY_OUTPUT_DIR, SLUG
# Arguments:
#   None
# Outputs:
#   Absolute directory
# Returns:
#   0
#######################################
default_out_dir() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/assets/sets/${SLUG}"
}

#######################################
# Default LoadImage directory (COMFY_OUTPUT_DIR/input → /inputs).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Absolute directory
# Returns:
#   0
#######################################
default_input_dir() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/input"
}

#######################################
# Copy pack ez_house_clay_NN.png into the LoadImage input directory.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  pack directory
#   $2  input directory
# Outputs:
#   helper text on stdout/stderr
# Returns:
#   copy-inputs status
#######################################
copy_clay_inputs() {
  local pack="${1}"
  local input="${2}"
  python3 "${REPO_ROOT}/scripts/lib/house_layout.py" copy-inputs "${pack}" "${input}"
}

#######################################
# Copy an existing dump into LoadImage input/ (no Blender, no occupancy XOR).
# Globals:
#   SLUG, OUT_DIR, INPUT_DIR
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 missing pack or copy fail
#######################################
cmd_install_inputs() {
  local dest input
  if [[ -z ${OUT_DIR} && -z ${SLUG} ]]; then
    err "Usage: house-views.sh --slug SLUG --install-inputs"
    return 1
  fi
  dest="${OUT_DIR:-$(default_out_dir)}"
  input="${INPUT_DIR:-$(default_input_dir)}"
  copy_clay_inputs "${dest}" "${input}" || {
    err "failed to copy clay into LoadImage input dir ${input}"
    return 1
  }
  log "installed clay into ${input}"
  return 0
}

#######################################
# Ensure LoadImage plates exist (copy pack or render layout).
# No Blender, no occupancy XOR. Does not overwrite valid plates.
# Globals:
#   SLUG, OUT_DIR, INPUT_DIR, LAYOUT, REPO_ROOT
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 seed fail
#######################################
cmd_seed_inputs() {
  local dest input layout slug
  slug="${SLUG:-lab-penthouse}"
  SLUG="${slug}"
  dest="${OUT_DIR:-$(default_out_dir)}"
  input="${INPUT_DIR:-$(default_input_dir)}"
  layout="${LAYOUT:-$(default_layout)}"
  local -a argv=(
    python3 "${REPO_ROOT}/scripts/lib/house_layout.py" seed-inputs "${input}"
    --slug "${slug}"
    --layout "${layout}"
  )
  if [[ -d ${dest} ]]; then
    argv+=(--pack "${dest}")
  fi
  "${argv[@]}" || {
    err "failed to seed clay into LoadImage input dir ${input}"
    return 1
  }
  log "seeded clay into ${input}"
  return 0
}

#######################################
# Default layout YAML (shipped penthouse).
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Absolute path
# Returns:
#   0
#######################################
default_layout() {
  echo "${REPO_ROOT}/schemas/house_layout.yaml"
}

#######################################
# Fail unless host blender is on PATH.
# Globals:
#   PATH
# Arguments:
#   None
# Outputs:
#   Install hint on stderr when missing
# Returns:
#   0 present; 1 missing
#######################################
require_blender() {
  if ! command -v blender >/dev/null 2>&1; then
    err "blender not on PATH. Host install only — never in docker/Dockerfile."
    err "No Blender → use klein-dream-house-lab-example (T2I). See docs/blender-gb10-sidecar.md"
    return 1
  fi
  return 0
}

#######################################
# Instagram 4:5 still size (not the LTX 1280x704 pack).
# Globals:
#   WIDTH, HEIGHT
# Arguments:
#   None
# Outputs:
#   Error when not 1024x1280
# Returns:
#   0 ok; 1 refuse
#######################################
require_ig_size() {
  if [[ ${WIDTH} -eq 1024 && ${HEIGHT} -eq 1280 ]]; then
    return 0
  fi
  err "House views size must be 1024x1280 (Instagram 4:5). Got ${WIDTH}x${HEIGHT} (do not use 1280x704/720)."
  return 1
}

#######################################
# Run house_layout.py validate-views on a dump directory.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  pack directory
#   $2  optional --fixture
# Outputs:
#   validator text on stdout
# Returns:
#   validator status
#######################################
validate_pack_dir() {
  local pack="${1}"
  local extra="${2:-}"
  local -a argv=(python3 "${REPO_ROOT}/scripts/lib/house_layout.py" validate-views "${pack}")
  if [[ ${extra} == "--fixture" ]]; then
    argv+=(--fixture)
  fi
  "${argv[@]}"
}

#######################################
# Dump a pack with host Blender, then fail-closed QC.
# Globals:
#   ENGINE, SLUG, LAYOUT, OUT_DIR, INPUT_DIR, INSTALL_INPUTS, SEED_INPUTS, WIDTH, HEIGHT, REPO_ROOT
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 usage/missing/QC; 2 occupancy
#######################################
cmd_run() {
  if [[ ${SEED_INPUTS} -eq 1 ]]; then
    cmd_seed_inputs
    return $?
  fi
  if [[ ${INSTALL_INPUTS} -eq 1 ]]; then
    cmd_install_inputs
    return $?
  fi
  refuse_if_heavy_gpu "house views dump (occupancy)" || return $?
  if [[ -z ${SLUG} ]]; then
    err "Usage: house-views.sh --slug SLUG [--layout FILE]"
    return 1
  fi
  if [[ ${ENGINE} != "blender" ]]; then
    err "P0 house-views engine is blender (godot is P2). Got ${ENGINE}"
    return 1
  fi
  require_ig_size || return 1
  require_blender || return 1
  local dest layout input
  dest="${OUT_DIR:-$(default_out_dir)}"
  layout="${LAYOUT:-$(default_layout)}"
  if [[ ! -f ${layout} ]]; then
    err "layout not found: ${layout}"
    return 1
  fi
  mkdir -p "${dest}"
  input="${INPUT_DIR:-$(default_input_dir)}"
  local -a bcmd=(blender --background --python "${REPO_ROOT}/tools/blender/export_house_views.py" --)
  bcmd+=(--out "${dest}" --layout "${layout}" --slug "${SLUG}" --engine "${ENGINE}")
  bcmd+=(--width "${WIDTH}" --height "${HEIGHT}" --input-dir "${input}")
  log "dumping house views → ${dest}"
  "${bcmd[@]}" || {
    err "Blender house-views dump failed"
    return 1
  }
  validate_pack_dir "${dest}" || {
    err "house views QC failed (size/cameras/layers)"
    return 1
  }
  copy_clay_inputs "${dest}" "${input}" || {
    err "failed to copy clay into LoadImage input dir ${input}"
    return 1
  }
  log "house views ok: ${dest}"
  return 0
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@
#######################################
main() {
  parse_args "$@"
  cmd_run
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
