#!/usr/bin/env bash
#
# ## overlay-qc
#
# 50% blend of clay first.png vs Klein look plate. Host ffmpeg, no GPU.
# May run while compose is up (unlike export-guides).
# Pack directory is guides/<film-id>/<shot>/ (go-see), the same directory
# blender-guide writes. Uses guides/<output-prefix>/ only when the film-id
# directory is absent.
#
# Usage:
#   ./scripts/utilities/overlay-qc.sh --film SLUG --shot ID --look PATH [--guides DIR]
#
# Safety:
#   Does not start Docker. Fail-closed on 1280x704 mismatch.
#
# Exit codes:
#   0 overlay written; 1 usage / QC fail.
#
# @command overlay-qc

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/films.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/films.sh"

FILM=""
SHOT_ID=""
LOOK=""
GUIDES=""

#######################################
# Map film id to slug.
# Arguments:
#   $1  film id
# Outputs:
#   slug
# Returns:
#   0 known; 1 unknown
#######################################
overlay_film_slug() {
  film_slug "${1:-}"
}

#######################################
# Guide-pack root. The film-id directory wins when it exists.
# Globals:
#   None
# Arguments:
#   $1  output root (COMFY_OUTPUT_DIR)
#   $2  film id (go-see)
#   $3  output prefix (gosee)
# Outputs:
#   Guide-pack directory on stdout
# Returns:
#   0
#######################################
overlay_guides_dir() {
  local root="${1:?}" film="${2:?}" slug="${3:-}"
  if [[ -d "${root}/guides/${film}" ]]; then
    printf '%s\n' "${root}/guides/${film}"
    return 0
  fi
  if [[ -n ${slug} && ${slug} != "${film}" && -d "${root}/guides/${slug}" ]]; then
    printf '%s\n' "${root}/guides/${slug}"
    return 0
  fi
  printf '%s\n' "${root}/guides/${film}"
}

#######################################
# Print usage.
#######################################
cmd_help() {
  echo "Usage: overlay-qc.sh --film SLUG --shot ID --look PATH [--guides DIR]" >&2
  echo "  50% clay/look overlay at 1280x704. Host ffmpeg. Compose may stay up." >&2
  echo "  Writes guides/<film-id>/<shot>/overlay.png and score.json." >&2
  echo "  That is the blender-guide directory (go-see, not the gosee prefix)." >&2
  return 0
}

#######################################
# Parse CLI.
# Globals:
#   FILM, SHOT_ID, LOOK, GUIDES
#######################################
parse_args() {
  FILM=""
  SHOT_ID=""
  LOOK=""
  GUIDES=""
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
      --look)
        LOOK="${2:?}"
        shift
        ;;
      --guides)
        GUIDES="${2:?}"
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
# Run overlay QC.
# Globals:
#   FILM, SHOT_ID, LOOK, GUIDES, COMFY_OUTPUT_DIR, REPO_ROOT
#######################################
cmd_run() {
  local slug dest clay
  if [[ -z ${FILM} || -z ${SHOT_ID} || -z ${LOOK} ]]; then
    err "overlay-qc requires --film --shot --look"
    return 1
  fi
  slug="$(overlay_film_slug "${FILM}")" || {
    err "Unknown film: ${FILM}"
    return 1
  }
  if [[ -z ${GUIDES} ]]; then
    GUIDES="$(overlay_guides_dir "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}" "${FILM}" "${slug}")"
  fi
  dest="${GUIDES}/${SHOT_ID}"
  clay="${dest}/first.png"
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.overlay --clay "${clay}" --look "${LOOK}" --dest "${dest}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  parse_args "$@" || exit 1
  cmd_run
fi
