#!/usr/bin/env bash
#
# ## compress-cinema-clip
#
# Re-encode a Cinema Rack illustration MP4 to muted 854x480 H.264 and
# write a JPEG poster. Host ffmpeg. Does not start Docker.
#
# Purpose:
#   Keep encyclopedia clips small enough for Git LFS (target <=512KiB).
#
# Usage:
#   ./scripts/utilities/compress-cinema-clip.sh --in FILE --out FILE
#       [--poster FILE] [--crf 28] [--max-bytes 524288] [--dry-run]
#
# Safety:
#   Does not start Docker. CPU encode; compose may stay up. Fails if
#   ffmpeg is missing.
#
# Exit codes:
#   0 success or dry-run; 1 usage / missing ffmpeg / size cap.
#
# @command compress-cinema-clip

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

IN_MP4=""
OUT_MP4=""
POSTER=""
STILL=""
MOVE="hold"
CRF=28
CRF_RETRY=32
MAX_BYTES=524288
DRY_RUN=0
WIDTH=854
HEIGHT=480
FPS=24

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
  echo "Usage: compress-cinema-clip.sh --in FILE --out FILE [--poster FILE] [--crf 28] [--max-bytes 524288] [--dry-run]" >&2
  echo "   or: compress-cinema-clip.sh --still FILE --move KIND --out FILE [--poster FILE] [--dry-run]" >&2
  echo "  Mute and scale to 854x480 24fps H.264 CRF, +faststart. JPEG poster from frame 0." >&2
  echo "  --still animates a lock still with zoompan (hold|zoom_in|zoom_out|pan_left|pan_right|tilt_up|tilt_down|rise|drop|orbit|jitter|whip_left|whip_right)." >&2
  echo "  Does not start Docker. Fails if ffmpeg is missing or the file stays over the byte cap." >&2
  return 0
}

#######################################
# Parse CLI flags.
# Globals:
#   IN_MP4, OUT_MP4, POSTER, CRF, MAX_BYTES, DRY_RUN
# Arguments:
#   $@
# Outputs:
#   Usage on --help
# Returns:
#   0; exits 0 on help, 1 on unknown args
#######################################
parse_args() {
  IN_MP4=""
  OUT_MP4=""
  POSTER=""
  STILL=""
  MOVE="hold"
  CRF=28
  MAX_BYTES=524288
  DRY_RUN=0
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --in)
        IN_MP4="${2:?}"
        shift
        ;;
      --still)
        STILL="${2:?}"
        shift
        ;;
      --move)
        MOVE="${2:?}"
        shift
        ;;
      --out)
        OUT_MP4="${2:?}"
        shift
        ;;
      --poster)
        POSTER="${2:?}"
        shift
        ;;
      --crf)
        CRF="${2:?}"
        shift
        ;;
      --max-bytes)
        MAX_BYTES="${2:?}"
        shift
        ;;
      --dry-run)
        DRY_RUN=1
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
  err "ffmpeg is required for compress-cinema-clip (do not skip). Install ffmpeg and retry."
  return 1
}

#######################################
# Scale/pad/fps filter graph.
# Globals:
#   WIDTH, HEIGHT, FPS
# Arguments:
#   None
# Outputs:
#   Filter string
# Returns:
#   0
#######################################
video_filter() {
  printf '%s' "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps=${FPS}"
}

#######################################
# zoompan recipe for a still illustration.
# Globals:
#   WIDTH, HEIGHT, FPS
# Arguments:
#   $1 motion kind
# Outputs:
#   zoompan filter
# Returns:
#   0 known; 1 unknown
#######################################
still_motion_filter() {
  local kind="${1:?}"
  local d=120
  local s="${WIDTH}x${HEIGHT}"
  case "${kind}" in
    hold)
      printf '%s' "zoompan=z=1.06:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    zoom_in)
      printf '%s' "zoompan=z='min(1.0+0.0035*on,1.42)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    zoom_out)
      printf '%s' "zoompan=z='if(eq(on,0),1.42,max(1.42-0.0035*on,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    pan_left)
      printf '%s' "zoompan=z=1.28:x='(iw-iw/zoom)*(1-on/119)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    pan_right)
      printf '%s' "zoompan=z=1.28:x='(iw-iw/zoom)*on/119':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    tilt_up)
      printf '%s' "zoompan=z=1.28:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/119)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    tilt_down)
      printf '%s' "zoompan=z=1.28:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/119':d=${d}:s=${s}:fps=${FPS}"
      ;;
    rise)
      printf '%s' "zoompan=z='min(1.08+0.002*on,1.32)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/119)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    drop)
      printf '%s' "zoompan=z='min(1.08+0.002*on,1.32)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/119':d=${d}:s=${s}:fps=${FPS}"
      ;;
    orbit)
      printf '%s' "zoompan=z=1.3:x='(iw-iw/zoom)*(0.5+0.5*sin(2*PI*on/120))':y='(ih-ih/zoom)*(0.5+0.5*cos(2*PI*on/120))':d=${d}:s=${s}:fps=${FPS}"
      ;;
    jitter)
      printf '%s' "zoompan=z=1.16:x='iw/2-(iw/zoom/2)+18*sin(on/3)':y='ih/2-(ih/zoom/2)+12*cos(on/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    whip_left)
      printf '%s' "zoompan=z=1.35:x='(iw-iw/zoom)*if(lt(on,14),1-on/14,0)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    whip_right)
      printf '%s' "zoompan=z=1.35:x='(iw-iw/zoom)*if(lt(on,14),on/14,1)':y='ih/2-(ih/zoom/2)':d=${d}:s=${s}:fps=${FPS}"
      ;;
    *)
      err "Unknown --move ${kind}"
      return 1
      ;;
  esac
}

#######################################
# Print ffmpeg compress argv for dry-run and tests.
# Globals:
#   IN_MP4, OUT_MP4
# Arguments:
#   $1 CRF
# Outputs:
#   One argv line
# Returns:
#   0
#######################################
compress_argv() {
  local crf="${1:?}"
  echo "ffmpeg -y -i ${IN_MP4} -an -vf $(video_filter) -c:v libx264 -pix_fmt yuv420p -profile:v high -crf ${crf} -preset slow -movflags +faststart -t 5 ${OUT_MP4}"
}

#######################################
# Print ffmpeg poster argv.
# Globals:
#   OUT_MP4, POSTER
# Arguments:
#   None
# Outputs:
#   One argv line
# Returns:
#   0
#######################################
poster_argv() {
  echo "ffmpeg -y -i ${OUT_MP4} -ss 0 -frames:v 1 -vf scale=640:-2 -q:v 4 ${POSTER}"
}

#######################################
# Print ffmpeg still-animation argv.
# Globals:
#   STILL, OUT_MP4, MOVE
# Arguments:
#   $1 CRF
# Outputs:
#   One argv line
# Returns:
#   0
#######################################
still_argv() {
  local crf="${1:?}"
  echo "ffmpeg -y -loop 1 -i ${STILL} -t 5 -vf $(still_motion_filter "${MOVE}") -an -c:v libx264 -pix_fmt yuv420p -profile:v high -crf ${crf} -preset slow -movflags +faststart ${OUT_MP4}"
}

#######################################
# Byte size of a file.
# Globals:
#   None
# Arguments:
#   $1 path
# Outputs:
#   Integer bytes
# Returns:
#   0
#######################################
file_size_bytes() {
  wc -c <"${1:?}" | tr -d ' '
}

#######################################
# True when path is larger than MAX_BYTES.
# Globals:
#   MAX_BYTES
# Arguments:
#   $1 path
# Outputs:
#   None
# Returns:
#   0 when over cap; 1 otherwise
#######################################
over_max_bytes() {
  local size
  size="$(file_size_bytes "${1:?}")"
  [[ ${size} -gt ${MAX_BYTES} ]]
}

#######################################
# Encode OUT_MP4 at CRF.
# Globals:
#   IN_MP4, OUT_MP4
# Arguments:
#   $1 CRF
# Outputs:
#   log
# Returns:
#   ffmpeg status
#######################################
compress_once() {
  local crf="${1:?}"
  local vf
  vf="$(video_filter)"
  mkdir -p "$(dirname "${OUT_MP4}")"
  run_ffmpeg_logged "cinema clip CRF ${crf}" -- ffmpeg -y -i "${IN_MP4}" -an \
    -vf "${vf}" -c:v libx264 -pix_fmt yuv420p -profile:v high \
    -crf "${crf}" -preset slow -movflags +faststart -t 5 "${OUT_MP4}"
}

#######################################
# Extract JPEG poster from OUT_MP4.
# Globals:
#   OUT_MP4, POSTER
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   ffmpeg status
#######################################
extract_poster() {
  mkdir -p "$(dirname "${POSTER}")"
  run_ffmpeg_logged "cinema poster" -- ffmpeg -y -i "${OUT_MP4}" -ss 0 \
    -frames:v 1 -vf scale=640:-2 -q:v 4 "${POSTER}"
}

#######################################
# Animate STILL into OUT_MP4 at CRF.
# Globals:
#   STILL, OUT_MP4, MOVE
# Arguments:
#   $1 CRF
# Outputs:
#   log
# Returns:
#   ffmpeg status
#######################################
compress_still_once() {
  local crf="${1:?}"
  local vf
  vf="$(still_motion_filter "${MOVE}")" || return 1
  mkdir -p "$(dirname "${OUT_MP4}")"
  run_ffmpeg_logged "cinema still ${MOVE} CRF ${crf}" -- ffmpeg -y -loop 1 \
    -i "${STILL}" -t 5 -vf "${vf}" -an -c:v libx264 -pix_fmt yuv420p \
    -profile:v high -crf "${crf}" -preset slow -movflags +faststart "${OUT_MP4}"
}

#######################################
# Compress, retry CRF, write poster.
# Globals:
#   IN_MP4, OUT_MP4, POSTER, CRF, CRF_RETRY, DRY_RUN
# Arguments:
#   None
# Outputs:
#   log / dry-run argv
# Returns:
#   0 success; 1 usage / ffmpeg / size
#######################################
cmd_run() {
  if [[ -z ${OUT_MP4} ]]; then
    err "Usage: compress-cinema-clip.sh --in FILE --out FILE  OR  --still FILE --move KIND --out FILE"
    return 1
  fi
  if [[ -z ${IN_MP4} && -z ${STILL} ]]; then
    err "Usage: compress-cinema-clip.sh --in FILE --out FILE  OR  --still FILE --move KIND --out FILE"
    return 1
  fi
  if [[ -z ${POSTER} ]]; then
    POSTER="${OUT_MP4%.*}.jpg"
  fi
  if [[ ${DRY_RUN} -eq 1 ]]; then
    if [[ -n ${STILL} ]]; then
      still_argv "${CRF}"
    else
      compress_argv "${CRF}"
    fi
    poster_argv
    return 0
  fi
  if [[ -n ${STILL} ]]; then
    if [[ ! -f ${STILL} ]]; then
      err "missing still ${STILL}"
      return 1
    fi
  elif [[ ! -f ${IN_MP4} ]]; then
    err "missing input ${IN_MP4}"
    return 1
  fi
  require_ffmpeg || return 1
  if [[ -n ${STILL} ]]; then
    compress_still_once "${CRF}" || return 1
  else
    compress_once "${CRF}" || return 1
  fi
  if over_max_bytes "${OUT_MP4}"; then
    log "retry cinema clip CRF ${CRF_RETRY} (over ${MAX_BYTES} bytes)"
    if [[ -n ${STILL} ]]; then
      compress_still_once "${CRF_RETRY}" || return 1
    else
      compress_once "${CRF_RETRY}" || return 1
    fi
  fi
  if over_max_bytes "${OUT_MP4}"; then
    err "compressed clip still over ${MAX_BYTES} bytes: ${OUT_MP4}"
    return 1
  fi
  extract_poster || return 1
  log "wrote ${OUT_MP4} and ${POSTER}"
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@
# Outputs:
#   See cmd_run
# Returns:
#   cmd_run status
#######################################
main() {
  parse_args "$@"
  cmd_run
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
