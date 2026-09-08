#!/usr/bin/env bash
#
# ## blender-guide
#
# Occupancy-gated Blender dump of an ez.guide.shot.v1 pack (clay / depth /
# first+last at 1280x704, 120 frames @ 24 fps). Never in docker/Dockerfile.
#
# Usage:
#   ./scripts/utilities/blender-guide.sh --film go-see --shot 12 [--blend FILE]
#   ./scripts/utilities/blender-guide.sh --engine blender --film go-see --shot 12
#
# Safety:
#   Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
#   Software ffmpeg mux (pack-frames.sh) — not NVENC.
#
# Exit codes:
#   0 success; 1 usage / missing blender / QC fail; 2 compose running
#
# @command export-guides

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
SHOT_ID=""
BLEND=""
OUT_DIR=""
CAMERA=""
FRAMES=120
WIDTH=1280
HEIGHT=704

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
  echo "Usage: blender-guide.sh --film SLUG --shot ID [--blend FILE] [--out DIR] [--camera NAME]" >&2
  echo "  Host Blender dump of a 1280x704 / 120f / 24fps guide pack." >&2
  echo "  Refuses if compose is up (exit 2). Never in docker/Dockerfile." >&2
  echo "  See docs/dcc-workflows.md" >&2
  return 0
}

#######################################
# Parse CLI into globals.
# Globals:
#   ENGINE, FILM, SHOT_ID, BLEND, OUT_DIR, CAMERA, FRAMES, WIDTH, HEIGHT
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
      --shot)
        SHOT_ID="${2:?}"
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
      --camera)
        CAMERA="${2:?}"
        shift
        ;;
      --frames)
        FRAMES="${2:?}"
        shift
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
# Normalize shot id to two digits (12 or 012 -> 12).
# Arguments:
#   $1  shot id
# Outputs:
#   NN on stdout
# Returns:
#   0 known pattern; 1 otherwise
#######################################
normalize_shot_id() {
  local raw="${1}"
  local n
  if [[ ${raw} =~ ^[0-9]+$ ]]; then
    n=$((10#${raw}))
    printf '%02d\n' "${n}"
    return 0
  fi
  return 1
}

#######################################
# Default pack directory under COMFY_OUTPUT_DIR.
# Globals:
#   COMFY_OUTPUT_DIR, FILM, SHOT_ID
# Arguments:
#   None
# Outputs:
#   Absolute directory
# Returns:
#   0
#######################################
default_out_dir() {
  local sid
  sid="$(normalize_shot_id "${SHOT_ID}")" || sid="${SHOT_ID}"
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/guides/${FILM}/${sid}"
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
# Snap operator size to the LTX VAE grid (refuse 720/1080 as-is).
# Globals:
#   WIDTH, HEIGHT
# Arguments:
#   None
# Outputs:
#   Error when not 1280x704 or 768x1280
# Returns:
#   0 ok; 1 refuse
#######################################
require_ltx_size() {
  if [[ ${WIDTH} -eq 1280 && ${HEIGHT} -eq 704 ]]; then
    return 0
  fi
  if [[ ${WIDTH} -eq 768 && ${HEIGHT} -eq 1280 ]]; then
    return 0
  fi
  err "Guide pack size must be 1280x704 (or 768x1280). Got ${WIDTH}x${HEIGHT} (720/1080 are not LTX-safe)."
  return 1
}

#######################################
# Run guide_pack.py validate on a dump directory.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  pack directory
#   $2  optional --fixture
# Outputs:
#   validator JSON on stdout
# Returns:
#   validator status
#######################################
validate_pack_dir() {
  local pack="${1}"
  local extra="${2:-}"
  local -a argv=(python3 "${REPO_ROOT}/scripts/lib/guide_pack.py" validate "${pack}")
  if [[ ${extra} == "--fixture" ]]; then
    argv+=(--fixture)
  fi
  "${argv[@]}"
}

#######################################
# Dump a pack with host Blender, then fail-closed QC.
# Globals:
#   ENGINE, FILM, SHOT_ID, BLEND, OUT_DIR, CAMERA, FRAMES, WIDTH, HEIGHT, REPO_ROOT
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 ok; 1 usage/missing/QC; 2 occupancy
#######################################
cmd_run() {
  refuse_if_comfy_running "guide pack dump (occupancy)" || return $?
  if [[ -z ${FILM} || -z ${SHOT_ID} ]]; then
    err "Usage: blender-guide.sh --film SLUG --shot ID [--blend FILE]"
    return 1
  fi
  if [[ ${ENGINE} != "blender" ]]; then
    err "P0 export-guides engine is blender (godot is P2). Got ${ENGINE}"
    return 1
  fi
  require_ltx_size || return 1
  if [[ ${FRAMES} -ne 120 ]]; then
    err "frames must be 120 (5.00s @ 24 fps), got ${FRAMES}"
    return 1
  fi
  require_blender || return 1
  local dest sid
  sid="$(normalize_shot_id "${SHOT_ID}")" || {
    err "shot id must be numeric (01-18)"
    return 1
  }
  dest="${OUT_DIR:-$(default_out_dir)}"
  mkdir -p "${dest}"
  local -a bcmd=(blender)
  if [[ -n ${BLEND} ]]; then
    bcmd+=("${BLEND}")
  fi
  bcmd+=(--background --python "${REPO_ROOT}/tools/blender/export_guide_pack.py" --)
  bcmd+=(--out "${dest}" --film "${FILM}" --shot "${sid}" --frames "${FRAMES}" --width "${WIDTH}" --height "${HEIGHT}")
  if [[ -n ${CAMERA} ]]; then
    bcmd+=(--camera "${CAMERA}")
  fi
  log "dumping guide pack → ${dest}"
  "${bcmd[@]}" || {
    err "Blender guide dump failed"
    return 1
  }
  validate_pack_dir "${dest}" || {
    err "guide pack QC failed (size/frames/layers)"
    return 1
  }
  log "guide pack ok: ${dest}"
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
