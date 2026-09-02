#!/usr/bin/env bash
#
# ## concat-shots
#
# Concatenate approved 5 s lab MP4s with ffmpeg after the operator Queues each shot.
#
# Purpose:
#   Concatenate approved 5.00 s lab MP4s. Default glob is six ez_shot_01..06
#   files. --film joins the 18-shot US-safe 90s shorts (go-see / still-here /
#   switchyard) in beat/shot order and caps the result at 90 s.
#
# Usage:
#   ./scripts/utilities/concat-shots.sh [--dir DIR] [--out FILE] [--dry-run|--yes]
#   ./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 [--out FILE]
#   ./scripts/utilities/concat-shots.sh --film go-see|still-here|switchyard [--yes]
#
# Environment:
#   COMFY_OUTPUT_DIR — default /mnt/comfy-output
#   Default glob: ez_shot_0{1..6}*.mp4
#   --film: ez_<slug>_b{1..6}_s{1..3}_ltx_video*.mp4 (fallback _wan_video)
#   --cap-seconds: publish cap (default 90)
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
FILM=""
CAP_SECONDS="90"

#######################################
# Parse CLI flags.
# Globals:
#   SHOT_DIR, OUT_MP4, DRY_RUN, FILE_CSV, FILM, CAP_SECONDS
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
      --film)
        FILM="${2:?}"
        shift
        ;;
      --cap-seconds)
        CAP_SECONDS="${2:?}"
        shift
        ;;
      --dry-run) DRY_RUN=1 ;;
      --yes | -y) DRY_RUN=0 ;;
      -h | --help)
        echo "Usage: $0 [--dir DIR] [--out FILE] [--files a.mp4,b.mp4] [--film go-see|still-here|switchyard] [--cap-seconds N] [--dry-run|--yes]" >&2
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
# Map --film name to prefix slug.
# Arguments:
#   $1  go-see|still-here|switchyard
# Outputs:
#   slug on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_slug() {
  case "${1}" in
    go-see) echo gosee ;;
    still-here) echo stillhere ;;
    switchyard) echo switchyard ;;
    *) return 1 ;;
  esac
}

#######################################
# First glob match or empty.
# Arguments:
#   $1  glob
# Outputs:
#   path or nothing
# Returns:
#   0
#######################################
first_glob() {
  local pattern="${1}"
  local dir name f
  dir="$(dirname "${pattern}")"
  name="$(basename "${pattern}")"
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    printf '%s\n' "${f}"
    return 0
  done < <(find "${dir}" -maxdepth 1 -type f -name "${name}" 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Collect 18 US-safe short MP4s in beat/shot order.
# Prefers LTX print; falls back to Wan rehearsal.
# Globals:
#   SHOT_DIR, FILM
# Outputs:
#   Absolute paths on stdout
# Returns:
#   0
#######################################
list_film_shot_files() {
  local slug b s ltx wan
  slug="$(film_slug "${FILM}")" || return 1
  for b in 1 2 3 4 5 6; do
    for s in 1 2 3; do
      ltx="$(first_glob "${SHOT_DIR}/ez_${slug}_b${b}_s${s}_ltx_video"*.mp4)"
      wan="$(first_glob "${SHOT_DIR}/ez_${slug}_b${b}_s${s}_wan_video"*.mp4)"
      if [[ -n ${ltx} ]]; then
        printf '%s\n' "${ltx}"
      elif [[ -n ${wan} ]]; then
        printf '%s\n' "${wan}"
      fi
    done
  done
}

#######################################
# Collect shot MP4s from --files, --film, or ez_shot_01..06 glob.
# Globals:
#   SHOT_DIR, FILE_CSV, FILM
# Arguments:
#   None
# Outputs:
#   Absolute paths on stdout
# Returns:
#   0; 1 if --film is unknown
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
  if [[ -n ${FILM} ]]; then
    list_film_shot_files
    return $?
  fi
  local n
  for n in 01 02 03 04 05 06; do
    f="$(first_glob "${SHOT_DIR}/ez_shot_${n}"*.mp4)"
    [[ -n ${f} ]] && printf '%s\n' "${f}"
  done
}

#######################################
# Probe duration seconds of an MP4 (ffprobe). Empty if unavailable.
# Arguments:
#   $1  path
# Outputs:
#   seconds on stdout
# Returns:
#   0
#######################################
probe_mp4_seconds() {
  local path="${1}"
  if ! command -v ffprobe >/dev/null 2>&1; then
    return 0
  fi
  ffprobe -v error -show_entries format=duration -of csv=p=0 "${path}" 2>/dev/null || true
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
#   SHOT_DIR, OUT_MP4, DRY_RUN, FILM, CAP_SECONDS
# Arguments:
#   None
# Outputs:
#   log/warn/err
# Returns:
#   0 dry-run or success; 1 if no files, wrong film count, or ffmpeg missing/fails
#######################################
cmd_run() {
  local -a files=()
  local line slug
  if [[ -n ${FILM} ]] && ! slug="$(film_slug "${FILM}")"; then
    err "Unknown film: ${FILM} (go-see|still-here|switchyard)"
    return 1
  fi
  while IFS= read -r line; do
    [[ -n ${line} ]] && files+=("${line}")
  done < <(list_shot_files)
  if [[ ${#files[@]} -eq 0 ]]; then
    err "No shot MP4s found under ${SHOT_DIR} (expected ez_shot_01*.mp4 or --film prefixes) and --files is empty"
    return 1
  fi
  if [[ -n ${FILM} ]] && [[ ${#files[@]} -ne 18 ]]; then
    err "film ${FILM} expected 18 shots, found ${#files[@]}"
    return 1
  fi
  if [[ -z ${OUT_MP4} ]]; then
    if [[ -n ${slug} ]]; then
      OUT_MP4="${SHOT_DIR}/ez_${slug}_90s.mp4"
    else
      OUT_MP4="${SHOT_DIR}/ez_concat_shots.mp4"
    fi
  fi
  log "shots (${#files[@]}):"
  local f
  for f in "${files[@]}"; do
    log "  ${f}"
  done
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "dry-run: would concat → ${OUT_MP4} cap ${CAP_SECONDS}s (pass --yes to run ffmpeg)"
    return 0
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    err "ffmpeg not on PATH"
    return 1
  fi
  local list
  list="$(mktemp)"
  write_concat_list "${list}" "${files[@]}"
  ffmpeg -y -f concat -safe 0 -i "${list}" -t "${CAP_SECONDS}" -c copy "${OUT_MP4}"
  rm -f "${list}"
  local dur
  dur="$(probe_mp4_seconds "${OUT_MP4}")"
  if [[ -n ${dur} ]] && awk "BEGIN {exit !(${dur} > ${CAP_SECONDS} + 0.05)}"; then
    err "concat duration ${dur}s exceeds cap ${CAP_SECONDS}s"
    return 1
  fi
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
