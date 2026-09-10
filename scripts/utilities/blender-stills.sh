#!/usr/bin/env bash
#
# ## blender-stills
#
# Occupancy-gated Blender dump of an ez.guide.still.v1 plate (single-frame
# clay / depth / canny at creator sizes). Never in docker/Dockerfile.
#
# Usage:
#   ./scripts/utilities/blender-stills.sh --film go-see --plate mug --blend FILE
#   ./scripts/utilities/blender-stills.sh --film go-see --plate mug --size 1024x1024
#
# Safety:
#   Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
#   --install-inputs copies first.png into COMFY_OUTPUT_DIR/input (compose may stay up).
#
# Exit codes:
#   0 success; 1 usage / missing blender / QC fail; 2 compose running
#
# @command blender-stills

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
FILM=""
PLATE=""
BLEND=""
OUT_DIR=""
INPUT_DIR=""
CAMERA=""
SIZE="1024x1024"
WIDTH=1024
HEIGHT=1024
PRINT_MODE="klein-from-clay"
INSTALL_INPUTS=0

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
  echo "Usage: blender-stills.sh --film SLUG --plate NAME [--blend FILE] [--size WxH]" >&2
  echo "       [--camera NAME] [--print klein-from-clay|klein-from-canny] [--out DIR]" >&2
  echo "       blender-stills.sh --film SLUG --plate NAME --install-inputs" >&2
  echo "  Host Blender dump of a single-frame clay/depth/canny still pack." >&2
  echo "  Sizes: 1280x704, 768x1280, 1024x1280, 1024x1024, 1280x720 (thumb, not LTX)." >&2
  echo "  Dump refuses if compose is up (exit 2). Never in docker/Dockerfile." >&2
  echo "  --install-inputs copies first.png into input/ (no Blender; compose may stay up)." >&2
  echo "  See docs/dcc-workflows.md" >&2
  return 0
}

#######################################
# Parse CLI into globals.
# Globals:
#   ENGINE, FILM, PLATE, BLEND, OUT_DIR, INPUT_DIR, CAMERA, SIZE, WIDTH, HEIGHT,
#   PRINT_MODE, INSTALL_INPUTS
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
      --film)
        FILM="${2:?}"
        shift
        ;;
      --plate)
        PLATE="${2:?}"
        shift
        ;;
      --blend)
        BLEND="${2:?}"
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
      --camera)
        CAMERA="${2:?}"
        shift
        ;;
      --size)
        SIZE="${2:?}"
        shift
        ;;
      --width)
        WIDTH="${2:?}"
        SIZE="${WIDTH}x${HEIGHT}"
        shift
        ;;
      --height)
        HEIGHT="${2:?}"
        SIZE="${WIDTH}x${HEIGHT}"
        shift
        ;;
      --print)
        PRINT_MODE="${2:?}"
        shift
        ;;
      --install-inputs)
        INSTALL_INPUTS=1
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
# Default still pack directory under COMFY_OUTPUT_DIR.
# Globals:
#   COMFY_OUTPUT_DIR, FILM, PLATE
# Arguments:
#   None
# Outputs:
#   Absolute directory
# Returns:
#   0
#######################################
default_out_dir() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/guides/${FILM}/stills/${PLATE}"
}

#######################################
# Default Comfy LoadImage input directory.
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
    err "See docs/blender-gb10-sidecar.md"
    return 1
  fi
  return 0
}

#######################################
# Snap operator size to the still contract.
# Globals:
#   SIZE, WIDTH, HEIGHT
# Arguments:
#   None
# Outputs:
#   Error when size is not allowed
# Returns:
#   0 ok; 1 refuse
#######################################
require_still_size() {
  local token="${SIZE}"
  token="${token//×/x}"
  case "${token}" in
    1280x704 | 768x1280 | 1024x1280 | 1024x1024 | 1280x720)
      WIDTH="${token%x*}"
      HEIGHT="${token#*x}"
      SIZE="${token}"
      return 0
      ;;
  esac
  err "Still size must be 1280x704, 768x1280, 1024x1280, 1024x1024, or 1280x720. Got ${SIZE} (1080p is not LTX-safe)."
  return 1
}

#######################################
# Run guide_pack.py validate-still on a dump directory.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  pack directory
# Outputs:
#   validator JSON on stdout
# Returns:
#   validator status
#######################################
validate_still_dir() {
  python3 "${REPO_ROOT}/scripts/lib/guide_pack.py" validate-still "${1}"
}

#######################################
# Copy first.png into LoadImage input/ (no Blender, no occupancy XOR).
# Globals:
#   FILM, PLATE, OUT_DIR, INPUT_DIR
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 missing pack
#######################################
cmd_install_inputs() {
  local dest input dest_png
  if [[ -z ${FILM} || -z ${PLATE} ]]; then
    err "Usage: blender-stills.sh --film SLUG --plate NAME --install-inputs"
    return 1
  fi
  dest="${OUT_DIR:-$(default_out_dir)}"
  input="${INPUT_DIR:-$(default_input_dir)}"
  dest_png="${dest}/first.png"
  if [[ ! -f ${dest_png} ]]; then
    err "missing ${dest_png}"
    return 1
  fi
  mkdir -p "${input}"
  cp "${dest_png}" "${input}/ez_clay_still_${PLATE}.png"
  if [[ -f ${dest}/canny.png ]]; then
    cp "${dest}/canny.png" "${input}/ez_canny_still_${PLATE}.png"
  fi
  log "installed still into ${input}"
  return 0
}

#######################################
# Dump a still pack with host Blender, then fail-closed QC.
# Globals:
#   ENGINE, FILM, PLATE, BLEND, OUT_DIR, CAMERA, SIZE, WIDTH, HEIGHT,
#   PRINT_MODE, INSTALL_INPUTS, INPUT_DIR, REPO_ROOT
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 usage/missing/QC; 2 occupancy
#######################################
cmd_run() {
  if [[ ${INSTALL_INPUTS} -eq 1 ]]; then
    cmd_install_inputs
    return $?
  fi
  refuse_if_comfy_running "Blender stills dump (occupancy)" || return $?
  if [[ -z ${FILM} || -z ${PLATE} ]]; then
    err "Usage: blender-stills.sh --film SLUG --plate NAME [--blend FILE] [--size WxH]"
    return 1
  fi
  if [[ ${ENGINE} != "blender" ]]; then
    err "P0 blender-stills engine is blender (godot is P2). Got ${ENGINE}"
    return 1
  fi
  require_still_size || return 1
  require_blender || return 1
  local dest input
  dest="${OUT_DIR:-$(default_out_dir)}"
  mkdir -p "${dest}"
  local -a bcmd=(blender)
  if [[ -n ${BLEND} ]]; then
    bcmd+=("${BLEND}")
  fi
  bcmd+=(--background --python "${REPO_ROOT}/tools/blender/export_still_pack.py" --)
  bcmd+=(--out "${dest}" --film "${FILM}" --plate "${PLATE}" --size "${SIZE}")
  bcmd+=(--print "${PRINT_MODE}")
  if [[ -n ${CAMERA} ]]; then
    bcmd+=(--camera "${CAMERA}")
  fi
  log "dumping still pack → ${dest}"
  "${bcmd[@]}" || {
    err "Blender still dump failed"
    return 1
  }
  validate_still_dir "${dest}" || {
    err "still pack QC failed (size/layers)"
    return 1
  }
  input="${INPUT_DIR:-$(default_input_dir)}"
  INPUT_DIR="${input}"
  cmd_install_inputs || return 1
  log "still pack ok: ${dest}"
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
