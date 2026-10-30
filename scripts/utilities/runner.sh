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
#   bash scripts/utilities/runner.sh download-limit status
#
# Environment:
#   BUILD_WORKSPACE_DIRECTORY - set by `bazel run`; names the git checkout the
#   utility runs against. Exported as REPO_ROOT for the utility and its children.
#
# Safety:
#   Only invokes scripts under scripts/utilities/; each utility keeps its
#   own confirmations and download-limit clear-on-exit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"

UTIL="${1:-}"
if [[ -z ${UTIL} ]]; then
  echo "run-utility: missing utility name" >&2
  echo "Usage: bazelisk run //scripts:run-utility -- <name> [args...]" >&2
  exit 2
fi
shift

if [[ ${UTIL} == */* || ${UTIL} == .* ]]; then
  echo "run-utility: utility name must be a bare name under scripts/utilities/" >&2
  exit 2
fi

# Dispatch from the git checkout, not the runfiles tree: every utility derives
# its own REPO_ROOT from dirname "${BASH_SOURCE[0]}", so a runfiles path would
# make it read .env and offer bazel-out bind mounts to docker. A utility the
# checkout does not carry still resolves beside this script.
CHECKOUT_ROOT="$(bazel_checkout_root)"
TARGET="${CHECKOUT_ROOT}/scripts/utilities/${UTIL}.sh"
if [[ ! -f ${TARGET} ]]; then
  TARGET="${SCRIPT_DIR}/${UTIL}.sh"
fi
if [[ ! -f ${TARGET} ]]; then
  echo "run-utility: unknown utility '${UTIL}'" >&2
  echo "Expected ${CHECKOUT_ROOT}/scripts/utilities/${UTIL}.sh" >&2
  exit 2
fi
export REPO_ROOT="${CHECKOUT_ROOT}"
exec bash "${TARGET}" "$@"
