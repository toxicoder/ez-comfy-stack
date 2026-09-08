#!/usr/bin/env bash
#
# ## film-animatic
#
# Cheap 90s animatic from clay.mp4 or held stills. Host ffmpeg, no GPU.
# May run while compose is up.
#
# Usage:
#   ./scripts/utilities/film-animatic.sh --film SLUG [--yaml PATH] [--guides DIR]
#
# Exit codes:
#   0 written; 1 usage / missing sources / ffmpeg fail.
#
# @command film-animatic

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

FILM=""
YAML=""
GUIDES=""

#######################################
# Map film id to slug.
#######################################
animatic_film_slug() {
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
  echo "Usage: film-animatic.sh --film SLUG [--yaml PATH] [--guides DIR]" >&2
  echo "  Concat clay.mp4 or 5.00s still holds. Cap 90s. Host ffmpeg." >&2
  echo "  Writes films/<slug>/publish/animatic.mp4. Compose may stay up." >&2
  return 0
}

#######################################
# Parse CLI.
#######################################
parse_args() {
  FILM=""
  YAML=""
  GUIDES=""
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --film)
        FILM="${2:?}"
        shift
        ;;
      --yaml)
        YAML="${2:?}"
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
# Build the animatic.
#######################################
cmd_run() {
  local slug dest out_root
  if [[ -z ${FILM} ]]; then
    err "film-animatic requires --film"
    return 1
  fi
  slug="$(animatic_film_slug "${FILM}")" || {
    err "Unknown film: ${FILM}"
    return 1
  }
  out_root="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
  dest="${out_root}/films/${slug}"
  if [[ -z ${YAML} ]]; then
    if [[ -f ${dest}/shots.yaml ]]; then
      YAML="${dest}/shots.yaml"
    else
      YAML="${REPO_ROOT}/workflows/shorts/${FILM}.shots.yaml"
    fi
  fi
  if [[ -z ${GUIDES} ]]; then
    GUIDES="${out_root}/guides/${slug}"
  fi
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.animatic --yaml "${YAML}" --dest "${dest}" --guides "${GUIDES}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  parse_args "$@" || exit 1
  cmd_run
fi
