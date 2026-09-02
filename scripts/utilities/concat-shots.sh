#!/usr/bin/env bash
#
# ## concat-shots
#
# Concatenate approved 5 s lab MP4s with ffmpeg after the operator Queues each shot.
#
# Purpose:
#   Replace 90 s six-column graphs. The user Queues wan-shot-lab-example (or LTX
#   hero) six times with prefixes ez_shot_01..06, then runs this utility.
#
# Usage:
#   ./scripts/utilities/concat-shots.sh [--dir DIR] [--out FILE] [--dry-run] [--yes]
#   ./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 [--out FILE]
#
# Environment:
#   COMFY_OUTPUT_DIR — default /mnt/comfy-output (shot glob ez_shot_0{1..6}*.mp4)
#
# Safety:
#   Does not start Docker. Dry-run by default unless --yes.
#
# Exit codes:
#   0 success / dry-run; 1 usage or ffmpeg failure.
#
# @command concat-shots

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

SHOT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
OUT_MP4=""
DRY_RUN=1
FILE_CSV=""

#######################################
# Parse CLI flags.
# Globals:
#   SHOT_DIR, OUT_MP4, DRY_RUN, FILE_CSV
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
      --dir)
        SHOT_DIR="${2:?}"
        shift
        ;;
      --out)
        OUT_MP4="${2:?}"
        shift
        ;;
      --files)
        FILE_CSV="${2:?}"
        shift
        ;;
      --dry-run) DRY_RUN=1 ;;
      --yes | -y) DRY_RUN=0 ;;
      -h | --help)
        echo "Usage: $0 [--dir DIR] [--out FILE] [--files a.mp4,b.mp4] [--dry-run|--yes]" >&2
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
# Collect shot MP4s from --files or ez_shot_01..06 glob.
# Globals:
#   SHOT_DIR, FILE_CSV
# Arguments:
#   None
# Outputs:
#   Absolute paths on stdout
# Returns:
#   0
#######################################
list_shot_files() {
  local f
  if [[ -n ${FILE_CSV} ]]; then
    local IFS=','
    local -a items
    read -r -a items <<<"${FILE_CSV}"
    for f in "${items[@]}"; do
      f="${f#"${f%%[![:space:]]*}"}"
      f="${f%"${f##*[![:space:]]}"}"
      [[ -n ${f} ]] && printf '%s\n' "${f}"
    done
    return 0
  fi
  local n
  for n in 01 02 03 04 05 06; do
    shopt -s nullglob
    local -a matches=("${SHOT_DIR}"/ez_shot_"${n}"*.mp4)
    shopt -u nullglob
    if [[ ${#matches[@]} -gt 0 ]]; then
      printf '%s\n' "${matches[0]}"
    fi
  done
}

#######################################
# Write an ffmpeg concat demuxer list.
# Globals:
#   None
# Arguments:
#   $1  list file path
#   remaining: mp4 paths
# Outputs:
#   None
# Returns:
#   0
#######################################
write_concat_list() {
  local list="${1}"
  shift
  local f
  : >"${list}"
  for f in "$@"; do
    printf "file '%s'\n" "${f}" >>"${list}"
  done
}

#######################################
# Concatenate shots (dry-run prints the list).
# Globals:
#   SHOT_DIR, OUT_MP4, DRY_RUN
# Arguments:
#   None
# Outputs:
#   log/warn/err
# Returns:
#   0 dry-run or success; 1 if no files or ffmpeg missing/fails
#######################################
cmd_run() {
  local -a files=()
  local line
  while IFS= read -r line; do
    [[ -n ${line} ]] && files+=("${line}")
  done < <(list_shot_files)
  if [[ ${#files[@]} -eq 0 ]]; then
    err "No shot MP4s found under ${SHOT_DIR} (expected ez_shot_01*.mp4 …) and --files is empty"
    return 1
  fi
  if [[ -z ${OUT_MP4} ]]; then
    OUT_MP4="${SHOT_DIR}/ez_concat_shots.mp4"
  fi
  log "shots (${#files[@]}):"
  local f
  for f in "${files[@]}"; do
    log "  ${f}"
  done
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "dry-run: would concat → ${OUT_MP4} (pass --yes to run ffmpeg)"
    return 0
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    err "ffmpeg not on PATH"
    return 1
  fi
  local list
  list="$(mktemp)"
  write_concat_list "${list}" "${files[@]}"
  ffmpeg -y -f concat -safe 0 -i "${list}" -c copy "${OUT_MP4}"
  rm -f "${list}"
  log "wrote ${OUT_MP4}"
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
