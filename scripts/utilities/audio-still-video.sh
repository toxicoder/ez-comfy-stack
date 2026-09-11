#!/usr/bin/env bash
#
# ## audio-still-video
#
# Mux a user-supplied still with an audio master into a YouTube-ready MP4.
# Host ffmpeg (libx264 stillimage + AAC). Does not change audio lab graphs.
#
# Purpose:
#   After Queue, turn FLAC/MP3 + a cover/thumbnail into H.264+AAC with
#   +faststart so YouTube ingest accepts a still-image video.
#
# Usage:
#   ./scripts/utilities/audio-still-video.sh status [--json]
#   ./scripts/utilities/audio-still-video.sh run --audio FILE --image FILE [--out FILE]
#       [--size 1920x1080|1280x720|1080x1920] [--fit letterbox|crop|stretch]
#       [--loudnorm off|youtube] [--dry-run]
#
# Environment:
#   COMFY_OUTPUT_DIR (not required; default --out is next to --audio)
#
# Safety:
#   Does not start Docker. CPU encode; compose may stay up. Fails if ffmpeg
#   is missing. Does not load ACE-Step / Klein / Wan / LTX.
#
# Exit codes:
#   0 success or dry-run; 1 usage / missing ffmpeg / mux failure.
#
# @command audio-still-video

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

CMD="run"
JSON_FLAG=""
AUDIO_FILE=""
IMAGE_FILE=""
OUT_FILE=""
SIZE="1920x1080"
SIZE_W=1920
SIZE_H=1080
FIT="letterbox"
LOUDNORM="off"
DRY_RUN=0
FFMPEG_ARGV=()

#######################################
# Print usage.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: audio-still-video.sh status|run --audio FILE --image FILE [--out FILE] [--size 1920x1080|1280x720|1080x1920] [--fit letterbox|crop|stretch] [--loudnorm off|youtube] [--dry-run] [--json]" >&2
  echo "  Mux a still + audio master to H.264+AAC MP4 for YouTube. Host ffmpeg. Compose may stay up." >&2
  echo "  Default 1920x1080 letterbox. Graphs still save FLAC + MP3. Does not start Docker." >&2
  echo "  Fails if ffmpeg is missing (do not skip)." >&2
  return 0
}

#######################################
# Require ffmpeg on PATH.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   err when missing
# Returns:
#   0 if present; 1 otherwise
#######################################
require_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1; then
    return 0
  fi
  err "ffmpeg is required for audio-still-video (do not skip). Install ffmpeg and retry."
  return 1
}

#######################################
# Parse an allowed canvas size into SIZE / SIZE_W / SIZE_H.
# Globals:
#   SIZE, SIZE_W, SIZE_H
# Arguments:
#   $1  1920x1080|1280x720|1080x1920
# Outputs:
#   err on unknown size
# Returns:
#   0 known; 1 unknown
#######################################
parse_size() {
  case "${1}" in
    1920x1080)
      SIZE_W=1920
      SIZE_H=1080
      ;;
    1280x720)
      SIZE_W=1280
      SIZE_H=720
      ;;
    1080x1920)
      SIZE_W=1080
      SIZE_H=1920
      ;;
    *)
      err "Unknown --size ${1} (use 1920x1080|1280x720|1080x1920)"
      return 1
      ;;
  esac
  SIZE="${1}"
  return 0
}

#######################################
# Build the -vf chain for the current fit and canvas.
# Globals:
#   FIT, SIZE_W, SIZE_H
# Arguments:
#   None
# Outputs:
#   Filter on stdout
# Returns:
#   0 known fit; 1 unknown
#######################################
scale_filter() {
  local w h
  w="${SIZE_W}"
  h="${SIZE_H}"
  case "${FIT}" in
    letterbox)
      printf 'scale=%s:%s:force_original_aspect_ratio=decrease,pad=%s:%s:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p\n' \
        "${w}" "${h}" "${w}" "${h}"
      ;;
    crop)
      printf 'scale=%s:%s:force_original_aspect_ratio=increase,crop=%s:%s,fps=30,format=yuv420p\n' \
        "${w}" "${h}" "${w}" "${h}"
      ;;
    stretch)
      printf 'scale=%s:%s,fps=30,format=yuv420p\n' "${w}" "${h}"
      ;;
    *)
      err "Unknown --fit ${FIT} (use letterbox|crop|stretch)"
      return 1
      ;;
  esac
}

#######################################
# Default MP4 path: same stem as --audio, .mp4 suffix.
# Globals:
#   AUDIO_FILE
# Arguments:
#   None
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
default_out_path() {
  local stem
  stem="${AUDIO_FILE%.*}"
  if [[ ${stem} == "${AUDIO_FILE}" ]]; then
    stem="${AUDIO_FILE}"
  fi
  printf '%s.mp4\n' "${stem}"
}

#######################################
# Populate FFMPEG_ARGV for the current inputs and flags.
# Globals:
#   AUDIO_FILE, IMAGE_FILE, OUT_FILE, LOUDNORM, FIT, SIZE_W, SIZE_H, FFMPEG_ARGV
# Arguments:
#   None
# Outputs:
#   err when the fit is unknown
# Returns:
#   0; 1 when scale_filter fails
#######################################
build_ffmpeg_argv() {
  local vf out
  vf="$(scale_filter)" || return 1
  vf="${vf%$'\n'}"
  out="${OUT_FILE}"
  if [[ -z ${out} ]]; then
    out="$(default_out_path)"
  fi
  FFMPEG_ARGV=(
    ffmpeg
    -y
    -loop
    1
    -framerate
    1
    -i
    "${IMAGE_FILE}"
    -i
    "${AUDIO_FILE}"
    -vf
    "${vf}"
    -c:v
    libx264
    -tune
    stillimage
    -preset
    medium
    -crf
    18
    -c:a
    aac
    -b:a
    192k
    -ar
    48000
    -ac
    2
  )
  if [[ ${LOUDNORM} == "youtube" ]]; then
    FFMPEG_ARGV+=(-af "loudnorm=I=-14:LRA=11:TP=-1.5")
  fi
  FFMPEG_ARGV+=(-shortest -movflags +faststart "${out}")
  return 0
}

#######################################
# Parse CLI flags.
# Globals:
#   CMD, JSON_FLAG, AUDIO_FILE, IMAGE_FILE, OUT_FILE, SIZE, SIZE_W, SIZE_H,
#   FIT, LOUDNORM, DRY_RUN
# Arguments:
#   $@  CLI args
# Outputs:
#   Usage on stderr
# Returns:
#   0; 1 on unknown args
#######################################
parse_args() {
  CMD="run"
  JSON_FLAG=""
  AUDIO_FILE=""
  IMAGE_FILE=""
  OUT_FILE=""
  SIZE="1920x1080"
  SIZE_W=1920
  SIZE_H=1080
  FIT="letterbox"
  LOUDNORM="off"
  DRY_RUN=0
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --audio)
        AUDIO_FILE="${2:?}"
        shift
        ;;
      --image)
        IMAGE_FILE="${2:?}"
        shift
        ;;
      --out)
        OUT_FILE="${2:?}"
        shift
        ;;
      --size)
        parse_size "${2:?}" || return 1
        shift
        ;;
      --fit)
        FIT="${2:?}"
        case "${FIT}" in
          letterbox | crop | stretch) ;;
          *)
            err "Unknown --fit ${FIT} (use letterbox|crop|stretch)"
            return 1
            ;;
        esac
        shift
        ;;
      --loudnorm)
        LOUDNORM="${2:?}"
        case "${LOUDNORM}" in
          off | youtube) ;;
          *)
            err "Unknown --loudnorm ${LOUDNORM} (use off|youtube)"
            return 1
            ;;
        esac
        shift
        ;;
      --dry-run) DRY_RUN=1 ;;
      status | run) CMD="${1}" ;;
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
  return 0
}

#######################################
# Read-only ffmpeg / canvas report.
# Globals:
#   JSON_FLAG, SIZE, FIT, LOUDNORM
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; log otherwise
# Returns:
#   0 if ffmpeg is present; 1 otherwise
#######################################
cmd_status() {
  local has="false"
  if command -v ffmpeg >/dev/null 2>&1; then
    has="true"
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '{"ffmpeg":%s,"size":"%s","fit":"%s","loudnorm":"%s"}\n' \
      "${has}" "${SIZE}" "${FIT}" "${LOUDNORM}"
  else
    log "audio-still-video size=${SIZE} fit=${FIT} loudnorm=${LOUDNORM} ffmpeg=${has}"
  fi
  if [[ ${has} != "true" ]]; then
    err "ffmpeg missing — still-video will not silently skip"
    return 1
  fi
  return 0
}

#######################################
# Mux still + audio. Never skip ffmpeg.
# Globals:
#   AUDIO_FILE, IMAGE_FILE, OUT_FILE, SIZE, FIT, LOUDNORM, DRY_RUN, FFMPEG_ARGV
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 on success or dry-run; 1 on missing input/ffmpeg or ffmpeg failure
#######################################
cmd_run() {
  local parent
  require_ffmpeg || return 1
  if [[ -z ${AUDIO_FILE} ]]; then
    err "run requires --audio FILE"
    return 1
  fi
  if [[ -z ${IMAGE_FILE} ]]; then
    err "run requires --image FILE"
    return 1
  fi
  if [[ ! -f ${AUDIO_FILE} ]]; then
    err "audio missing: ${AUDIO_FILE}"
    return 1
  fi
  if [[ ! -f ${IMAGE_FILE} ]]; then
    err "image missing: ${IMAGE_FILE}"
    return 1
  fi
  parse_size "${SIZE}" || return 1
  if [[ -z ${OUT_FILE} ]]; then
    OUT_FILE="$(default_out_path)"
  fi
  build_ffmpeg_argv || return 1
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "dry-run: ${FFMPEG_ARGV[*]}"
    return 0
  fi
  parent="$(dirname "${OUT_FILE}")"
  mkdir -p "${parent}"
  log "mux ${IMAGE_FILE} + ${AUDIO_FILE} → ${OUT_FILE} (size=${SIZE} fit=${FIT})"
  if ! run_ffmpeg_logged "mux still+audio → ${OUT_FILE}" -- "${FFMPEG_ARGV[@]}"; then
    err "ffmpeg still-video failed for ${AUDIO_FILE} (not skipped)"
    return 1
  fi
  log "wrote ${OUT_FILE}"
  return 0
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@  CLI args
# Outputs:
#   Status via log/warn/err on stderr unless noted
# Returns:
#   Handler status; unknown command exits 1
#######################################
main() {
  parse_args "$@" || exit 1
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    *)
      err "Unknown command: ${CMD}"
      cmd_help
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
