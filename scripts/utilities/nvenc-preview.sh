#!/usr/bin/env bash
#
# ## nvenc-preview
#
# Host h264_nvenc preview encode. Never rewrite film masters.
#
# Purpose:
#   Encode a preview MP4 with the Spark NVENC engine when ComfyUI is stopped
#   so preview encode does not fight LTX/Wan denoise for the encoder.
#
# Usage:
#   ./scripts/utilities/nvenc-preview.sh --in MASTER.mp4 --out PREVIEW.mp4 [--yes]
#
# Safety:
#   Refuses if compose comfyui is running. Dry-run by default.
#   Does not start Docker. Does not delete inputs.
#
# Exit codes:
#   0 success / dry-run; 1 usage or refuse; 2 compose running
#
# @command nvenc-preview

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

IN_MP4=""
OUT_MP4=""
DRY_RUN=1

#######################################
# Parse CLI flags.
# Globals:
#   IN_MP4, OUT_MP4, DRY_RUN
# Arguments:
#   $@
# Outputs:
#   Usage on --help
# Returns:
#   0; exits 0 on help, 1 on unknown args
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --in)
        IN_MP4="${2:?}"
        shift
        ;;
      --out)
        OUT_MP4="${2:?}"
        shift
        ;;
      --dry-run) DRY_RUN=1 ;;
      --yes | -y) DRY_RUN=0 ;;
      -h | --help)
        echo "Usage: $0 --in MASTER.mp4 --out PREVIEW.mp4 [--dry-run|--yes]" >&2
        echo "  Refuses while ComfyUI compose is running (NVENC contention)." >&2
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
# Encode preview (dry-run prints the command).
# Globals:
#   IN_MP4, OUT_MP4, DRY_RUN
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 dry-run or success; 1 missing args/ffmpeg; 2 compose running
#######################################
cmd_run() {
  if [[ -z ${IN_MP4} || -z ${OUT_MP4} ]]; then
    err "Usage: nvenc-preview.sh --in MASTER.mp4 --out PREVIEW.mp4 [--yes]"
    return 1
  fi
  refuse_if_comfy_running "NVENC preview (encoder contention)" || return $?
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "dry-run: ffmpeg -y -i ${IN_MP4} -c:v h264_nvenc -preset p4 ${OUT_MP4}"
    return 0
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    err "ffmpeg not on PATH"
    return 1
  fi
  run_ffmpeg_logged "NVENC preview → ${OUT_MP4}" -- ffmpeg -y -i "${IN_MP4}" -c:v h264_nvenc -preset p4 -c:a aac -ar 48000 -ac 2 \
    -b:a 128k "${OUT_MP4}"
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
