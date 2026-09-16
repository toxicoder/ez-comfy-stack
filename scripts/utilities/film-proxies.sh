#!/usr/bin/env bash
#
# ## film-proxies
#
# Host h264_nvenc proxies for a film jobstore. Never rewrite masters.
#
# Usage:
#   ./scripts/utilities/film-proxies.sh go-see|still-here|switchyard [--yes]
#
# Safety:
#   Refuses if compose comfyui is running. Dry-run by default.
#   Proxies are 960×528 ~2 Mbps under films/<slug>/proxies/.
#
# @command film-proxies

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/films.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/films.sh"

FILM=""
DRY_RUN=1

#######################################
# Parse flags.
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --dry-run) DRY_RUN=1 ;;
      --yes | -y) DRY_RUN=0 ;;
      -h | --help)
        echo "Usage: $0 FILM [--dry-run|--yes]" >&2
        echo "  Writes 960x528 h264 ~2 Mbps proxies. Never rewrites masters." >&2
        echo "  Refuses while ComfyUI compose is running." >&2
        exit 0
        ;;
      *)
        if film_slug "${1}" >/dev/null 2>&1; then
          FILM="${1}"
        else
          err "Unknown arg: $1"
          exit 1
        fi
        ;;
    esac
    shift
  done
}

#######################################
# Proxy encode or dry-run.
#######################################
cmd_run() {
  local slug dest src out
  if [[ -z ${FILM} ]]; then
    err "Usage: film-proxies.sh FILM [--yes]"
    return 1
  fi
  slug="$(film_slug "${FILM}")" || return 1
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  if compose_is_running; then
    err "ComfyUI is running — stop it before film-proxies (NVENC contention)"
    return 2
  fi
  if [[ ! -d ${dest}/shots ]]; then
    err "missing ${dest}/shots"
    return 1
  fi
  mkdir -p "${dest}/proxies"
  local f
  shopt -s nullglob
  local -a shots=()
  local shot
  for shot in "${dest}/shots/"*.mp4; do
    shots+=("${shot}")
  done
  shopt -u nullglob
  if [[ ${#shots[@]} -eq 0 ]]; then
    err "no shots/*.mp4 under ${dest}"
    return 1
  fi
  for src in "${shots[@]}"; do
    f="$(basename "${src}")"
    out="${dest}/proxies/${f}"
    if [[ ${DRY_RUN} -eq 1 ]]; then
      log "dry-run: ffmpeg -y -i ${src} -vf scale=960:528 -c:v h264_nvenc -b:v 2M ${out}"
      continue
    fi
    if ! command -v ffmpeg >/dev/null 2>&1; then
      err "ffmpeg not on PATH"
      return 1
    fi
    run_ffmpeg_logged "NVENC proxy → ${out}" -- ffmpeg -y -i "${src}" -vf scale=960:528 -c:v h264_nvenc -preset p4 \
      -b:v 2M -maxrate 2M -bufsize 4M -an "${out}"
    log "wrote ${out}"
  done
}

#######################################
# CLI dispatcher.
# Globals:
#   FILM, DRY_RUN
# Arguments:
#   $@  Film id (go-see|still-here|switchyard) and --yes/--dry-run
# Outputs:
#   Status via log/warn/err on stderr
# Returns:
#   Exit status of cmd_run
#######################################
main() {
  parse_args "$@"
  cmd_run
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
