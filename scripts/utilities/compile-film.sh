#!/usr/bin/env bash
#
# ## compile-film
#
# Compile workflows/shorts/{film}.shots.yaml into films/<slug>/ jobstore.
#
# Purpose:
#   Emit film.yaml, state.json (18 pending shots), and shots/NN.json stubs
#   from the YAML bible. Does not Queue Comfy. Does not start Docker.
#
# Usage:
#   ./scripts/utilities/compile-film.sh FILM
#
# Environment:
#   COMFY_OUTPUT_DIR — default /mnt/comfy-output
#
# Exit codes:
#   0 success; 1 usage / parse error
#
# @command compile-film

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/films.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/films.sh"

#######################################
# Map film id to jobstore slug.
# Arguments:
#   $1  film id
# Outputs:
#   slug on stdout
# Returns:
#   0 known; 1 unknown
#######################################
compile_film_slug() {
  film_slug "${1:-}"
}

#######################################
# Run the Python compiler (parse_shots_yaml, no second YAML subset).
# Globals:
#   REPO_ROOT, COMFY_OUTPUT_DIR
# Arguments:
#   $1  film id
# Outputs:
#   log/err
# Returns:
#   0; 1 on unknown film or python error
#######################################
compile_film_run() {
  local film="${1:-}"
  local slug yaml dest
  if [[ -z ${film} ]]; then
    err "Usage: compile-film.sh FILM"
    return 1
  fi
  slug="$(compile_film_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  yaml="${REPO_ROOT}/workflows/shorts/${film}.shots.yaml"
  if [[ ! -f ${yaml} ]]; then
    err "missing ${yaml}"
    return 1
  fi
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.jobstore init --yaml "${yaml}" --dest "${dest}"
  log "compiled ${film} → ${dest}"
}

#######################################
# CLI.
# Arguments:
#   $@
#######################################
main() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
    echo "Usage: $0 FILM" >&2
    exit 0
  fi
  compile_film_run "${1:-}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
