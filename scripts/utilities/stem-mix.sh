#!/usr/bin/env bash
#
# ## stem-mix
#
# Picture-lock stem mix (DX / BG / FX / MX). Duck −15 dB under DX, YouTube loudnorm.
# Occupancy: operator must already have stopped Klein/Wan/LTX. This script is CPU ffmpeg.
#
# Usage:
#   ./scripts/utilities/stem-mix.sh --film SLUG --shot ID [--dx PATH] --bg PATH [--fx PATH] [--mx PATH] [--video PATH]
#
# Exit codes:
#   0 mix written; 1 usage / missing ffmpeg / mix fail.
#
# @command stem-mix

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

FILM=""
SHOT_ID=""
DX=""
BG=""
FX=""
MX=""
VIDEO=""

#######################################
# Map film id to slug.
#######################################
mix_film_slug() {
  case "${1}" in
    go-see) echo gosee ;;
    still-here) echo stillhere ;;
    switchyard) echo switchyard ;;
    *) return 1 ;;
  esac
}

#######################################
# Print usage.
#######################################
cmd_help() {
  echo "Usage: stem-mix.sh --film SLUG --shot ID --bg PATH [--dx PATH] [--fx PATH] [--mx PATH] [--video PATH]" >&2
  echo "  Duck beds −15 dB under DX. YouTube loudnorm I=-14. Host ffmpeg." >&2
  echo "  Writes films/<slug>/stems/<id>/mix.m4a (or mix.mp4 with --video)." >&2
  echo "  Stop Klein/Wan/LTX first (occupancy audio). Does not start Docker." >&2
  return 0
}

#######################################
# Parse CLI.
#######################################
parse_args() {
  FILM=""
  SHOT_ID=""
  DX=""
  BG=""
  FX=""
  MX=""
  VIDEO=""
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --film)
        FILM="${2:?}"
        shift
        ;;
      --shot)
        SHOT_ID="${2:?}"
        shift
        ;;
      --dx)
        DX="${2:?}"
        shift
        ;;
      --bg)
        BG="${2:?}"
        shift
        ;;
      --fx)
        FX="${2:?}"
        shift
        ;;
      --mx)
        MX="${2:?}"
        shift
        ;;
      --video)
        VIDEO="${2:?}"
        shift
        ;;
      -h | --help | help)
        cmd_help
        exit 0
        ;;
      *)
        err "Unknown argument: ${1}"
        cmd_help
        return 1
        ;;
    esac
    shift
  done
}

#######################################
# Mix stems.
#######################################
cmd_run() {
  local slug dest extra
  extra=()
  if [[ -z ${FILM} || -z ${SHOT_ID} ]]; then
    err "stem-mix requires --film --shot"
    return 1
  fi
  slug="$(mix_film_slug "${FILM}")" || {
    err "Unknown film: ${FILM}"
    return 1
  }
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}/stems/${SHOT_ID}"
  [[ -n ${DX} ]] && extra+=(--dx "${DX}")
  [[ -n ${BG} ]] && extra+=(--bg "${BG}")
  [[ -n ${FX} ]] && extra+=(--fx "${FX}")
  [[ -n ${MX} ]] && extra+=(--mx "${MX}")
  [[ -n ${VIDEO} ]] && extra+=(--video "${VIDEO}")
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.stems --dest "${dest}" "${extra[@]}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  parse_args "$@" || exit 1
  cmd_run
fi
