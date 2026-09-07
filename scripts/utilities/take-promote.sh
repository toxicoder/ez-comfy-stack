#!/usr/bin/env bash
#
# ## take-promote
#
# Promote a take from films/<slug>/takes/<id>/tNNN.mp4 to shots/<id>.mp4.
#
# Usage:
#   ./scripts/utilities/take-promote.sh <film> <id> <take>
#
# Environment:
#   COMFY_OUTPUT_DIR
#
# @command take-promote

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Map film id to jobstore slug.
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
# Promote take N for shot id.
# Arguments:
#   $1  film
#   $2  shot id
#   $3  take number
#######################################
promote_run() {
  local film="${1:-}"
  local sid="${2:-}"
  local take="${3:-}"
  local slug dest
  if [[ -z ${film} || -z ${sid} || -z ${take} ]]; then
    err "Usage: take-promote.sh go-see|still-here|switchyard <id> <take>"
    return 1
  fi
  slug="$(film_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  if [[ ! -f ${dest}/state.json ]]; then
    err "missing jobstore ${dest}/state.json"
    return 1
  fi
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.jobstore promote --dest "${dest}" --id "${sid}" --take "${take}"
  log "promoted ${film} ${sid} take ${take} → ${dest}/shots/${sid}.mp4"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  promote_run "${1:-}" "${2:-}" "${3:-}"
fi
