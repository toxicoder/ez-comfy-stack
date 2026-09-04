#!/usr/bin/env bash
#
# ## podcast-loudnorm
#
# ffmpeg loudnorm for podcast / YouTube masters. Comfy cannot LUFS-normalize.
#
# Purpose:
#   Target −16 LUFS (podcast) or −14 LUFS (YouTube). Never silently skip.
#
# Usage:
#   ./scripts/utilities/podcast-loudnorm.sh status [--json]
#   ./scripts/utilities/podcast-loudnorm.sh run --in FILE [--out FILE] [--target podcast|youtube]
#
# Environment:
#   COMFY_OUTPUT_DIR
#
# Safety:
#   Does not start Docker. Fails if ffmpeg is missing or loudnorm fails.
#
# Exit codes:
#   0 success; 1 usage / missing ffmpeg / loudnorm failure.
#
# @command podcast-loudnorm

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

CMD="status"
JSON_FLAG=""
IN_FILE=""
OUT_FILE=""
TARGET="podcast"

#######################################
# Integrated loudness target in LUFS.
# Globals:
#   TARGET
# Arguments:
#   None
# Outputs:
#   Integer LUFS (negative) on stdout
# Returns:
#   0
#######################################
loudness_i() {
  case "${TARGET}" in
    youtube) echo -14 ;;
    *) echo -16 ;;
  esac
}

#######################################
# ffmpeg loudnorm filter string for the current target.
# Globals:
#   TARGET
# Arguments:
#   None
# Outputs:
#   Filter on stdout
# Returns:
#   0
#######################################
loudnorm_filter() {
  printf 'loudnorm=I=%s:LRA=11:TP=-1.5' "$(loudness_i)"
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
  err "ffmpeg is required for podcast-loudnorm (do not skip). Install ffmpeg and retry."
  return 1
}

#######################################
# Parse CLI flags.
# Globals:
#   CMD, JSON_FLAG, IN_FILE, OUT_FILE, TARGET
# Arguments:
#   $@  CLI args
# Outputs:
#   Usage on stderr
# Returns:
#   0; exits 1 on unknown args
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --in)
        IN_FILE="${2:?}"
        shift
        ;;
      --out)
        OUT_FILE="${2:?}"
        shift
        ;;
      --target)
        TARGET="${2:?}"
        case "${TARGET}" in
          podcast | youtube) ;;
          *)
            err "Unknown --target ${TARGET} (use podcast|youtube)"
            exit 1
            ;;
        esac
        shift
        ;;
      --youtube) TARGET="youtube" ;;
      status | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run [--in FILE] [--out FILE] [--target podcast|youtube] [--json]" >&2
        echo "  podcast = −16 LUFS; youtube = −14 LUFS. Fails if ffmpeg is missing." >&2
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
# Default output path next to the input with a -lufs suffix.
# Globals:
#   IN_FILE, TARGET
# Arguments:
#   None
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
default_out_path() {
  local stem ext
  stem="${IN_FILE%.*}"
  ext="${IN_FILE##*.}"
  if [[ ${stem} == "${IN_FILE}" ]]; then
    ext="flac"
  fi
  printf '%s-%s-lufs.%s\n' "${stem}" "${TARGET}" "${ext}"
}

#######################################
# Read-only ffmpeg / target report.
# Globals:
#   JSON_FLAG, TARGET
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; log otherwise
# Returns:
#   0 if ffmpeg is present; 1 otherwise
#######################################
cmd_status() {
  local has="false" i
  i="$(loudness_i)"
  if command -v ffmpeg >/dev/null 2>&1; then
    has="true"
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '{"ffmpeg":%s,"target":"%s","lufs":%s,"filter":"%s"}\n' \
      "${has}" "${TARGET}" "${i}" "$(loudnorm_filter)"
  else
    log "podcast-loudnorm target=${TARGET} I=${i} LUFS filter=$(loudnorm_filter) ffmpeg=${has}"
  fi
  if [[ ${has} != "true" ]]; then
    err "ffmpeg missing — loudnorm will not silently skip"
    return 1
  fi
  return 0
}

#######################################
# Run ffmpeg loudnorm. Never skip.
# Globals:
#   IN_FILE, OUT_FILE, TARGET
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0 on success; 1 on missing input/ffmpeg or ffmpeg failure
#######################################
cmd_run() {
  local out filter
  require_ffmpeg || return 1
  if [[ -z ${IN_FILE} ]]; then
    err "run requires --in FILE"
    return 1
  fi
  if [[ ! -f ${IN_FILE} ]]; then
    err "input missing: ${IN_FILE}"
    return 1
  fi
  out="${OUT_FILE}"
  if [[ -z ${out} ]]; then
    out="$(default_out_path)"
  fi
  filter="$(loudnorm_filter)"
  log "loudnorm ${IN_FILE} → ${out} (${filter})"
  if ! ffmpeg -y -i "${IN_FILE}" -af "${filter}" "${out}"; then
    err "ffmpeg loudnorm failed for ${IN_FILE} (not skipped)"
    return 1
  fi
  log "wrote ${out}"
  return 0
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@ - CLI args
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    *)
      err "Usage: $0 status|run [--in FILE] [--out FILE] [--target podcast|youtube] [--json]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
