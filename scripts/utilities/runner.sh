#!/usr/bin/env bash
#
# ## Utility runner (Bazel entry)
#
# Dispatches to `scripts/utilities/<name>.sh`.
#
# @command run-utility
# Usage:
#   bazelisk run //scripts:run-utility -- download-limit status
#   bazelisk run //scripts:run-utility -- occupancy status
#
# Safety:
#   Only invokes scripts under scripts/utilities/; each utility keeps its
#   own confirmations and download-limit clear-on-exit.

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(lab_script_dir 1 utilities)"
UTIL="${1:-}"
if [[ -z ${UTIL} ]]; then
  echo "run-utility: missing utility name" >&2
  echo "Usage: bazelisk run //scripts:run-utility -- <name> [args...]" >&2
  exit 2
fi
shift
exec "${SCRIPT_DIR}/${UTIL}.sh" "$@"
