#!/usr/bin/env bash
#
# ## pack-frames
#
# Mux a PNG/EXR sequence to 24fps 1280x704 MP4 with software libx264.
# Not NVENC — may run while Comfy is up because it does not use the GPU.
#
# Usage:
#   ./scripts/utilities/pack-frames.sh --in DIR --out FILE [--fps 24] [--pattern '%04d.png']
#
# @command pack-frames

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

IN_DIR=""
OUT_MP4=""
FPS=24
PATTERN="%04d.png"
WIDTH=1280
HEIGHT=704

#######################################
# Parse CLI.
# Globals:
#   IN_DIR, OUT_MP4, FPS, PATTERN, WIDTH, HEIGHT
# Arguments:
#   $@
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --in)
        IN_DIR="${2:?}"
        shift
        ;;
      --out)
        OUT_MP4="${2:?}"
        shift
        ;;
      --fps)
        FPS="${2:?}"
        shift
        ;;
      --pattern)
        PATTERN="${2:?}"
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
        echo "Usage: pack-frames.sh --in DIR --out FILE [--fps 24] [--pattern %04d.png]" >&2
        echo "  Software libx264 mux (not NVENC). 1280x704 / 24fps lab default." >&2
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# Build ffmpeg argv (software encode).
# Globals:
#   IN_DIR, OUT_MP4, FPS, PATTERN, WIDTH, HEIGHT
# Arguments:
#   None
# Outputs:
#   Words on stdout
# Returns:
#   0
#######################################
ffmpeg_mux_argv() {
  printf '%s\n' ffmpeg -y -framerate "${FPS}" \
    -i "${IN_DIR}/${PATTERN}" \
    -an -c:v libx264 -pix_fmt yuv420p \
    -s "${WIDTH}x${HEIGHT}" \
    "${OUT_MP4}"
}

#######################################
# Mux the sequence.
# Globals:
#   IN_DIR, OUT_MP4, FPS
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 success; 1 usage/ffmpeg
#######################################
cmd_run() {
  if [[ -z ${IN_DIR} || -z ${OUT_MP4} ]]; then
    err "Usage: pack-frames.sh --in DIR --out FILE"
    return 1
  fi
  if [[ ! -d ${IN_DIR} ]]; then
    err "missing input dir ${IN_DIR}"
    return 1
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    err "ffmpeg not on PATH"
    return 1
  fi
  mkdir -p "$(dirname "${OUT_MP4}")"
  log "mux ${IN_DIR} → ${OUT_MP4} (${FPS} fps, libx264, not NVENC)"
  ffmpeg -y -framerate "${FPS}" -i "${IN_DIR}/${PATTERN}" \
    -an -c:v libx264 -pix_fmt yuv420p -s "${WIDTH}x${HEIGHT}" "${OUT_MP4}"
  log "wrote ${OUT_MP4}"
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
