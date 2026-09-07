#!/usr/bin/env bash
#
# ## film-accept
#
# Fail-closed accept gate before 90s concat (duration, 1280×704, LTX audio).
#
# Usage:
#   ./scripts/utilities/film-accept.sh go-see|still-here|switchyard
#
# Environment:
#   COMFY_OUTPUT_DIR
#
# @command film-accept

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
#   $1  go-see|still-here|switchyard
# Outputs:
#   slug on stdout
# Returns:
#   0 known; 1 unknown
#######################################
accept_film_slug() {
  case "${1}" in
    go-see) echo gosee ;;
    still-here) echo stillhere ;;
    switchyard) echo switchyard ;;
    *) return 1 ;;
  esac
}

#######################################
# Run the Python accept gate.
# Globals:
#   REPO_ROOT, COMFY_OUTPUT_DIR
# Arguments:
#   $1  film id
# Outputs:
#   JSON report on stdout; defects on stderr
# Returns:
#   0 all shots pass; 1 fail closed
#######################################
cmd_run() {
  local film="${1:-}"
  local slug dest
  if [[ ${film} == "-h" || ${film} == "--help" || -z ${film} ]]; then
    echo "Usage: film-accept.sh go-see|still-here|switchyard" >&2
    echo "  Fail closed: 18 ok shots, 5.00±0.05s, 1280x704, LTX audio present." >&2
    [[ -n ${film} ]] && return 0
    return 1
  fi
  slug="$(accept_film_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.accept --dest "${dest}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
