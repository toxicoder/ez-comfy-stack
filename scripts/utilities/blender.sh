#!/usr/bin/env bash
#
# ## blender
#
# Host Blender sidecar. Dies if compose is up (occupancy). Never in
# docker/Dockerfile — GB10 DCC stays on the host. See docs/blender-gb10-sidecar.md.
#
# Usage:
#   ./scripts/utilities/blender.sh [--] [blender args]
#
# @command blender

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"

#######################################
# Refuse when studio compose is running.
# Globals:
#   None (compose_is_running uses compose project env)
# Arguments:
#   None
# Outputs:
#   Error on stderr when compose is up
# Returns:
#   0 idle; 2 when ComfyUI is running
#######################################
refuse_if_comfy_running() {
  if compose_is_running; then
    err "ComfyUI is running — stop it before Blender (occupancy)"
    return 2
  fi
  return 0
}

#######################################
# Launch host blender or print install hint.
# Globals:
#   PATH
# Arguments:
#   $@  blender args; optional leading --
# Outputs:
#   Help or install hint on stderr; exec blender on stdout
# Returns:
#   blender exit; 1 missing binary; 2 compose running
#######################################
cmd_run() {
  refuse_if_comfy_running || return $?
  if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
    echo "Usage: blender.sh [--] [args]  (host Blender; refuses if compose is up)" >&2
    echo "  Never in docker/Dockerfile. See docs/blender-gb10-sidecar.md" >&2
    return 0
  fi
  if [[ ${1:-} == "--" ]]; then
    shift
  fi
  if ! command -v blender >/dev/null 2>&1; then
    err "blender not on PATH. Host install only — never in docker/Dockerfile."
    err "See docs/blender-gb10-sidecar.md"
    return 1
  fi
  exec blender "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
