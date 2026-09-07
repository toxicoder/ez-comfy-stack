#!/usr/bin/env bash
#
# ## film-export-otio
#
# Write films/<slug>/publish/<slug>.otio from jobstore state.json.
#
# Usage:
#   ./scripts/utilities/film-export-otio.sh go-see|still-here|switchyard
#
# Environment:
#   COMFY_OUTPUT_DIR
#
# @command film-export-otio

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Map film id to jobstore slug.
# Arguments:
#   $1  film id
# Outputs:
#   slug
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
# Export OTIO JSON.
# Arguments:
#   $1  film id
#######################################
export_otio() {
  local film="${1:-}"
  local slug dest
  if [[ -z ${film} ]]; then
    err "Usage: film-export-otio.sh go-see|still-here|switchyard"
    return 1
  fi
  slug="$(film_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  if [[ ! -f ${dest}/state.json ]]; then
    err "missing jobstore ${dest}/state.json — compile-film / print-shot first"
    return 1
  fi
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.otio_export --dest "${dest}"
  log "wrote ${dest}/publish/${slug}.otio"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  export_otio "${1:-}"
fi
