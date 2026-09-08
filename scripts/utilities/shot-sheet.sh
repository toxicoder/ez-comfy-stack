#!/usr/bin/env bash
#
# ## shot-sheet
#
# Write films/<slug>/shots.yaml from a lab bible with shot-card defaults.
# Does not mutate workflows/shorts/*.shots.yaml unless --lab-example.
#
# Usage:
#   ./scripts/utilities/shot-sheet.sh status [--json] [--film SLUG]
#   ./scripts/utilities/shot-sheet.sh run --film SLUG [--from PATH] [--out PATH] [--lab-example]
#
# Safety:
#   Host only. Does not start Docker. No GPU.
#
# Exit codes:
#   0 success; 1 usage / parse / write failure.
#
# @command shot-sheet

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

CMD="status"
JSON_FLAG=""
FILM=""
FROM_PATH=""
OUT_PATH=""
LAB_EXAMPLE=0

#######################################
# Map film id to jobstore slug.
# Arguments:
#   $1  go-see|still-here|switchyard
# Outputs:
#   slug on stdout
# Returns:
#   0 known; 1 unknown
#######################################
sheet_film_slug() {
  case "${1}" in
    go-see) echo gosee ;;
    still-here) echo stillhere ;;
    switchyard) echo switchyard ;;
    *) return 1 ;;
  esac
}

#######################################
# Print usage.
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: shot-sheet.sh status|run --film SLUG [--from PATH] [--out PATH] [--lab-example]" >&2
  echo "  Write films/<slug>/shots.yaml with shot-card defaults (audio_policy, clay, …)." >&2
  echo "  Does not start Docker. Does not copy YAML into Comfy." >&2
  echo "  --lab-example writes workflows/shorts/<film>.shots.yaml (refused otherwise)." >&2
  return 0
}

#######################################
# Parse CLI into globals.
# Globals:
#   CMD, JSON_FLAG, FILM, FROM_PATH, OUT_PATH, LAB_EXAMPLE
# Arguments:
#   $@
# Returns:
#   0; exits 0 on help
#######################################
parse_args() {
  CMD="status"
  JSON_FLAG=""
  FILM=""
  FROM_PATH=""
  OUT_PATH=""
  LAB_EXAMPLE=0
  if [[ $# -gt 0 && ${1} != -* ]]; then
    CMD="${1}"
    shift
  fi
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      status | run)
        CMD="${1}"
        ;;
      --film)
        FILM="${2:?}"
        shift
        ;;
      --from)
        FROM_PATH="${2:?}"
        shift
        ;;
      --out)
        OUT_PATH="${2:?}"
        shift
        ;;
      --lab-example)
        LAB_EXAMPLE=1
        ;;
      --json)
        JSON_FLAG="--json"
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
# Default source bible path.
# Globals:
#   REPO_ROOT, FILM, FROM_PATH
# Outputs:
#   Path on stdout
#######################################
source_yaml() {
  if [[ -n ${FROM_PATH} ]]; then
    echo "${FROM_PATH}"
    return 0
  fi
  echo "${REPO_ROOT}/workflows/shorts/${FILM}.shots.yaml"
}

#######################################
# Default destination path.
# Globals:
#   FILM, OUT_PATH, LAB_EXAMPLE, COMFY_OUTPUT_DIR, REPO_ROOT
# Outputs:
#   Path on stdout
# Returns:
#   1 unknown film
#######################################
dest_yaml() {
  local slug
  if [[ -n ${OUT_PATH} ]]; then
    echo "${OUT_PATH}"
    return 0
  fi
  if [[ ${LAB_EXAMPLE} -eq 1 ]]; then
    echo "${REPO_ROOT}/workflows/shorts/${FILM}.shots.yaml"
    return 0
  fi
  slug="$(sheet_film_slug "${FILM}")" || return 1
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}/shots.yaml"
}

#######################################
# Read-only status.
# Globals:
#   FILM, JSON_FLAG
# Outputs:
#   Human or JSON on stdout
# Returns:
#   0
#######################################
cmd_status() {
  local src dest have_src have_dest slug
  src=""
  dest=""
  have_src=0
  have_dest=0
  slug=""
  if [[ -n ${FILM} ]]; then
    src="$(source_yaml)"
    dest="$(dest_yaml)" || true
    [[ -f ${src} ]] && have_src=1
    [[ -n ${dest} && -f ${dest} ]] && have_dest=1
    slug="$(sheet_film_slug "${FILM}" 2>/dev/null || true)"
  fi
  if [[ -n ${JSON_FLAG} ]]; then
    printf '{"film":"%s","slug":"%s","source":"%s","dest":"%s","source_exists":%s,"dest_exists":%s}\n' \
      "${FILM}" "${slug}" "${src}" "${dest}" \
      "$([[ ${have_src} -eq 1 ]] && echo true || echo false)" \
      "$([[ ${have_dest} -eq 1 ]] && echo true || echo false)"
    return 0
  fi
  log "shot-sheet film=${FILM:-unset} dest=${dest:-unset} dest_exists=${have_dest}"
}

#######################################
# Scaffold shot-card YAML.
# Globals:
#   FILM, FROM_PATH, OUT_PATH, LAB_EXAMPLE, REPO_ROOT
# Returns:
#   0 write ok; 1 fail
#######################################
cmd_run() {
  local src dest slug
  if [[ -z ${FILM} ]]; then
    err "shot-sheet run requires --film"
    return 1
  fi
  slug="$(sheet_film_slug "${FILM}")" || {
    err "Unknown film: ${FILM}"
    return 1
  }
  src="$(source_yaml)"
  dest="$(dest_yaml)"
  if [[ ${LAB_EXAMPLE} -eq 0 && ${dest} == "${REPO_ROOT}/workflows/shorts/"* ]]; then
    err "refusing to overwrite lab YAML without --lab-example"
    return 1
  fi
  if [[ ! -f ${src} ]]; then
    err "missing source ${src}"
    return 1
  fi
  mkdir -p "$(dirname "${dest}")"
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -c '
import sys
from pathlib import Path
from ez_film.shots import scaffold_shot_sheet
src, dest = Path(sys.argv[1]), Path(sys.argv[2])
dest.write_text(scaffold_shot_sheet(src.read_text(encoding="utf-8")), encoding="utf-8")
print(str(dest))
' "${src}" "${dest}"
  log "wrote ${dest} (slug=${slug})"
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@
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
