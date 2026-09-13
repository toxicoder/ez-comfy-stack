#!/usr/bin/env bash
#
# ## album-render
#
# Queue one shipped music album on local ComfyUI, then zip the folder.
#
# Purpose:
#   One-go album: optional Klein cover, then each ACE-Step track, then pack.
#   Sequential occupancy (klein XOR audio). Does not start compose.
#
# Usage:
#   ./scripts/utilities/album-render.sh status [--json]
#   ./scripts/utilities/album-render.sh run --album ARTIST/SLUG
#       [--art skip|upload|generate] [--image FILE] [--out DIR] [--dry-run]
#   ./scripts/utilities/album-render.sh pack --album ARTIST/SLUG [--out DIR]
#
# Environment:
#   COMFY_OUTPUT_DIR, COMFY_PORT (default 8188), COMFY_URL, REPO_ROOT
#
# Safety:
#   Does not start Docker. Does not change restart: "no". Sequential Queue.
#   generate unloads models (POST /free) between cover and tracks.
#
# Exit codes:
#   0 success / dry-run; 1 usage / missing compose / queue failure.
#
# @command album-render

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

COMFY_URL="${COMFY_URL:-http://127.0.0.1:${COMFY_PORT:-8188}}"
CMD="run"
JSON_FLAG=""
ALBUM_ID=""
ART_MODE="skip"
IMAGE_FILE=""
OUT_DIR=""
DRY_RUN=0

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
  echo "Usage: album-render.sh status|run|pack --album ARTIST/SLUG [--art skip|upload|generate] [--image FILE] [--out DIR] [--dry-run] [--json]" >&2
  echo "  Sequential album Queue on local Comfy. Does not start compose." >&2
  echo "  --art generate queues cover.json (klein) then POST /free then tracks." >&2
  return 0
}

#######################################
# Resolve a shipped album folder under workflows/_lab/audio/albums.
# Arguments:
#   $1  artist/slug
# Outputs:
#   Absolute album directory
# Returns:
#   0 when present
#######################################
album_dir() {
  local id="${1:?}"
  local dest
  dest="${REPO_ROOT}/workflows/_lab/audio/albums/${id}"
  if [[ ! -d ${dest} ]]; then
    err "unknown album ${id} (expected ${dest})"
    return 1
  fi
  printf '%s\n' "${dest}"
}

#######################################
# True when Comfy /system_stats answers.
# Globals:
#   COMFY_URL
# Returns:
#   0 when up
#######################################
comfy_up() {
  curl -sf "${COMFY_URL}/system_stats" >/dev/null 2>&1
}

#######################################
# POST /free to unload models (occupancy XOR).
# Globals:
#   COMFY_URL
# Returns:
#   0
#######################################
comfy_free() {
  curl -sf -X POST "${COMFY_URL}/free" \
    -H 'Content-Type: application/json' \
    --data '{"unload_models":true,"free_memory":true}' >/dev/null 2>&1 || true
}

#######################################
# POST a workflow JSON to /prompt.
# Globals:
#   COMFY_URL
# Arguments:
#   $1  workflow json path
# Outputs:
#   prompt_id
# Returns:
#   0; 1 on curl/json failure
#######################################
comfy_post_prompt() {
  local json_path="${1:?}"
  local resp
  resp="$(curl -sf -X POST "${COMFY_URL}/prompt" -H 'Content-Type: application/json' --data-binary @"${json_path}")" || return 1
  printf '%s' "${resp}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["prompt_id"])'
}

#######################################
# Poll /history until the prompt id appears or timeout.
# Globals:
#   COMFY_URL
# Arguments:
#   $1  prompt_id
# Returns:
#   0
#######################################
comfy_wait_history() {
  local pid="${1:?}"
  local attempt=0
  local max="${LAB_ALBUM_POLL_MAX:-3}"
  while [[ ${attempt} -lt ${max} ]]; do
    attempt=$((attempt + 1))
    if curl -sf "${COMFY_URL}/history/${pid}" 2>/dev/null | grep -q "${pid}"; then
      return 0
    fi
    sleep "${LAB_ALBUM_POLL:-0}"
  done
  return 0
}

#######################################
# Pack an already-rendered album folder.
# Globals:
#   COMFY_OUTPUT_DIR, REPO_ROOT
# Arguments:
#   $1  artist/slug
# Outputs:
#   zip path
# Returns:
#   0; 1 on missing audio
#######################################
pack_only() {
  local id="${1:?}"
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 - "${id}" "${COMFY_OUTPUT_DIR:-}" "${OUT_DIR:-}" <<'PY'
import json
import sys
from pathlib import Path

from ez_music.albums import shipped_albums
from ez_music.metadata import album_dir_from_env
from ez_music.pack import pack_album

album_id, output, override = sys.argv[1], sys.argv[2], sys.argv[3]
artist_slug, slug = album_id.split("/", 1)
info = next(
    row
    for row in shipped_albums()
    if row["artist_slug"] == artist_slug and row["slug"] == slug
)
root = Path(override) if override else None
dest = album_dir_from_env(info["artist"], info["title"], output_dir=root)
if output and root is None:
    dest = album_dir_from_env(info["artist"], info["title"], output_dir=Path(output))
zip_path = pack_album(dest, album=info["title"])
print(zip_path)
PY
}

#######################################
# CLI dispatcher.
# Globals:
#   CMD, ALBUM_ID, ART_MODE, IMAGE_FILE, DRY_RUN, JSON_FLAG
# Arguments:
#   $@
# Returns:
#   0 or 1
#######################################
main() {
  local status
  if [[ $# -eq 0 ]]; then
    cmd_help
    return 1
  fi
  case "${1}" in
    status | run | pack | -h | --help)
      CMD="${1}"
      shift
      ;;
  esac
  if [[ ${CMD} == "-h" || ${CMD} == "--help" ]]; then
    cmd_help
    return 0
  fi
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --album)
        ALBUM_ID="${2:-}"
        shift 2
        ;;
      --art)
        ART_MODE="${2:-}"
        shift 2
        ;;
      --image)
        IMAGE_FILE="${2:-}"
        shift 2
        ;;
      --out)
        OUT_DIR="${2:-}"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      --json)
        JSON_FLAG=1
        shift
        ;;
      -h | --help)
        cmd_help
        return 0
        ;;
      *)
        err "unknown argument: ${1}"
        cmd_help
        return 1
        ;;
    esac
  done
  case "${ART_MODE}" in
    skip | upload | generate) ;;
    *)
      err "--art must be skip|upload|generate"
      return 1
      ;;
  esac
  if [[ ${CMD} == "status" ]]; then
    if [[ -n ${JSON_FLAG} ]]; then
      if comfy_up; then
        printf '{"comfy":"up","url":"%s"}\n' "${COMFY_URL}"
      else
        printf '{"comfy":"down","url":"%s"}\n' "${COMFY_URL}"
      fi
    else
      if comfy_up; then
        log "Comfy up at ${COMFY_URL}"
      else
        log "Comfy down (${COMFY_URL})"
      fi
    fi
    return 0
  fi
  if [[ -z ${ALBUM_ID} ]]; then
    err "--album ARTIST/SLUG is required"
    return 1
  fi
  album_dir "${ALBUM_ID}" >/dev/null || return 1
  if [[ ${CMD} == "pack" ]]; then
    pack_only "${ALBUM_ID}"
    return 0
  fi
  if [[ ${ART_MODE} == "upload" && -z ${IMAGE_FILE} ]]; then
    err "--art upload requires --image FILE"
    return 1
  fi
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "dry-run album ${ALBUM_ID} art=${ART_MODE}"
    return 0
  fi
  if ! comfy_up; then
    err "Comfy is not up at ${COMFY_URL} — start the stack first (does not auto-start)"
    return 1
  fi
  local dir cover track
  dir="$(album_dir "${ALBUM_ID}")"
  if [[ ${ART_MODE} == "generate" ]]; then
    cover="${dir}/cover.json"
    if [[ ! -f ${cover} ]]; then
      err "missing ${cover}"
      return 1
    fi
    log "queue cover (occupancy klein) ${cover}"
    status="$(comfy_post_prompt "${cover}")" || return 1
    comfy_wait_history "${status}"
    comfy_free
  fi
  if [[ ${ART_MODE} == "upload" ]]; then
    PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
      python3 - "${ALBUM_ID}" "${IMAGE_FILE}" "${COMFY_OUTPUT_DIR:-}" <<'PY'
import shutil
import sys
from pathlib import Path

from ez_music.albums import shipped_albums
from ez_music.metadata import album_dir_from_env

album_id, image, output = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
artist_slug, slug = album_id.split("/", 1)
info = next(
    row
    for row in shipped_albums()
    if row["artist_slug"] == artist_slug and row["slug"] == slug
)
dest = album_dir_from_env(
    info["artist"],
    info["title"],
    output_dir=Path(output) if output else None,
)
shutil.copy2(image, dest / "cover.jpg")
print(dest / "cover.jpg")
PY
  fi
  while IFS= read -r -d '' track; do
    log "queue track ${track##*/}"
    status="$(comfy_post_prompt "${track}")" || return 1
    comfy_wait_history "${status}"
  done < <(find "${dir}" -maxdepth 1 -type f -name '[0-9][0-9]-*.json' -print0 | sort -z)
  pack_only "${ALBUM_ID}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
