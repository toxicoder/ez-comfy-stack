#!/usr/bin/env bash
#
# ## promote-workflow
#
# Copy one live operator graph into the repo lab tree. Does not commit.
#
# Usage:
#   ./scripts/utilities/promote-workflow.sh \
#     --from PATH --lane LANE --id STEM [--subdir REL]
#
# Environment:
#   REPO_ROOT (optional)
#
# Safety:
#   Never copies _lab into _user. Refuses banned model strings and a
#   missing id.
#
# Exit codes:
#   0 success; 1 usage / refuse
#
# @command promote-workflow

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

readonly PROMOTE_LANES=(stills motion creator services films dcc optional audio inspire)
readonly PROMOTE_BANNED=(
  MiniMax
  Seedance
  Kling
  z_image_turbo
)
readonly PROMOTE_BANNED_UNET=(
  klein-9b
  flux-2-klein-9b
  FLUX.2-dev
  flux2_dev
  flux2-dev
  flux-2-dev
)

#######################################
# Print usage to stderr.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage text on stderr
# Returns:
#   0
#######################################
promote_usage() {
  err "Usage: promote-workflow.sh --from PATH --lane LANE --id STEM [--subdir REL]"
}

#######################################
# True when lane is an allowed _lab folder.
# Globals:
#   PROMOTE_LANES
# Arguments:
#   $1  lane
# Outputs:
#   None
# Returns:
#   0 when allowed
#######################################
promote_lane_ok() {
  local lane="${1:-}"
  local item
  for item in "${PROMOTE_LANES[@]}"; do
    if [[ ${item} == "${lane}" ]]; then
      return 0
    fi
  done
  return 1
}

#######################################
# Refuse graphs that contain banned model strings.
# Globals:
#   PROMOTE_BANNED
# Arguments:
#   $1  source file
# Outputs:
#   err on hit
# Returns:
#   0 when clean; 1 when banned
#######################################
promote_refuse_banned() {
  local src="${1:?}"
  local needle
  for needle in "${PROMOTE_BANNED[@]}"; do
    if grep -F -- "${needle}" "${src}" >/dev/null 2>&1; then
      err "refusing banned string ${needle} in ${src}"
      return 1
    fi
  done
  python3 - "${src}" "${PROMOTE_BANNED_UNET[@]}" <<'PY'
import json
import sys

path = sys.argv[1]
needles = [n.lower() for n in sys.argv[2:]]
try:
    data = json.loads(open(path, encoding="utf-8").read())
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)
for node in data.get("nodes") or []:
    if str(node.get("type") or "") != "UNETLoader":
        continue
    blob = " ".join(str(v) for v in (node.get("widgets_values") or [])).lower()
    for needle in needles:
        if needle in blob:
            raise SystemExit(f"pinned banned UNET {needle}")
raise SystemExit(0)
PY
  local pin_rc=$?
  if [[ ${pin_rc} -ne 0 ]]; then
    err "refusing banned UNET pin in ${src}"
    return 1
  fi
  return 0
}

#######################################
# Copy a live user graph into workflows/_lab/<lane>/<id>.json.
# Globals:
#   REPO_ROOT
# Arguments:
#   --from PATH --lane LANE --id STEM
# Outputs:
#   log/err
# Returns:
#   0 on copy; 1 on refuse
#######################################
promote_run() {
  local from="" lane="" id="" subdir="" dest dest_dir
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --from)
        from="${2:-}"
        shift 2
        ;;
      --lane)
        lane="${2:-}"
        shift 2
        ;;
      --id)
        id="${2:-}"
        shift 2
        ;;
      --subdir)
        subdir="${2:-}"
        shift 2
        ;;
      -h | --help)
        promote_usage
        return 1
        ;;
      *)
        err "unknown argument: ${1}"
        promote_usage
        return 1
        ;;
    esac
  done
  if [[ -z ${from} || -z ${lane} || -z ${id} ]]; then
    promote_usage
    return 1
  fi
  id="${id%.json}"
  id="${id##*/}"
  if [[ -z ${id} || ${id} == *..* ]]; then
    err "id must be a filename stem (got ${id})"
    return 1
  fi
  promote_lane_ok "${lane}" || {
    err "unknown lane ${lane} (stills|motion|creator|services|films|dcc|optional|audio|inspire)"
    return 1
  }
  if [[ ! -f ${from} ]]; then
    err "missing source ${from}"
    return 1
  fi
  if [[ ${from} == *"/_lab/"* || ${from} == *"/workflows/_lab/"* ]]; then
    err "never copy _lab into the lab tree from _lab (promote is user -> lab only)"
    return 1
  fi
  promote_refuse_banned "${from}" || return 1
  dest_dir="${REPO_ROOT}/workflows/_lab/${lane}"
  if [[ -n ${subdir} ]]; then
    if [[ ${subdir} == /* || ${subdir} == *..* ]]; then
      err "invalid --subdir ${subdir}"
      return 1
    fi
    dest_dir="${dest_dir}/${subdir}"
  fi
  dest="${dest_dir}/${id}.json"
  mkdir -p "$(dirname "${dest}")"
  cp -a "${from}" "${dest}"
  log "copied ${from} -> ${dest}"
  log "next: stamp App Mode, add/adjust tests/python/_build_*.py, run make test"
  log "do not copy _lab graphs into _user"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  promote_run "$@"
fi
