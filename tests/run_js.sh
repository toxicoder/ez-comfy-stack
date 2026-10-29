#!/usr/bin/env bash
#
# ## run_js
#
# Hermetic node:test gate for the first-party custom-node browser JS.
#
# Purpose:
#   Run the dependency-free node:test suite under tests/js/ so the
#   custom_nodes/ez_quality overlay and the custom_nodes/ez_image mode
#   registry fail here instead of only in a live ComfyUI tab. Does not
#   require npm, GPU, ComfyUI, or Docker.
#
# Usage:
#   bash tests/run_js.sh
#   bazelisk test //tests:js
#
# Safety: No Docker daemon, GPU, or network. Read-only over the repo; the
#   runner writes only to its own mkdtemp scratch under TMPDIR.
#
# Requirements:
#   node 22+ (built-in node:test runner). No package.json, no install step.
#
# Exit codes:
#   0 if the suite passes.
#   1 if node is missing or the suite fails.
#
set -euo pipefail

# shellcheck source=repo_root.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_root.sh"
ROOT="$(tests_repo_root)"
cd "${ROOT}"

# Absolute path to the node binary, set by require_node.
NODE_BIN=""

#######################################
# Resolve the node binary from PATH.
# Globals:
#   NODE_BIN
# Arguments:
#   None
# Outputs:
#   Missing-prerequisite hint on stderr when node is absent
# Returns:
#   0 if node is on PATH; 1 otherwise
#######################################
require_node() {
  NODE_BIN="$(command -v node 2>/dev/null || true)"
  if [[ -n ${NODE_BIN} ]]; then
    return 0
  fi
  echo "run_js: node is required for the JS gate and was not found on PATH." >&2
  echo "Install Node.js 22 or newer; the suite uses the built-in node:test" >&2
  echo "runner and needs no npm install." >&2
  return 1
}

#######################################
# Run the node:test suite from the repo root.
# Globals:
#   NODE_BIN
# Arguments:
#   $@ - node --test flags, placed before the file glob
# Outputs:
#   node:test reporter output on stdout/stderr
# Returns:
#   node --test exit status
#######################################
run_node_tests() {
  # The glob is quoted so node expands it, not bash. Passing the bare
  # directory (node --test tests/js/) fails with MODULE_NOT_FOUND on Node 24.
  # Extra args go before the glob: node treats anything after a positional
  # file pattern as another pattern, so a flag after the glob is ignored.
  "${NODE_BIN}" --test "$@" "tests/js/*.test.mjs"
}

#######################################
# JS test entrypoint.
# Globals:
#   NODE_BIN (set through require_node)
# Arguments:
#   $@ - extra args forwarded to node --test
# Outputs:
#   Status line plus runner output
# Returns:
#   0 on success; 1 if node is missing or the suite fails
#######################################
main() {
  echo "=== node:test (tests/js) ==="
  if ! require_node; then
    return 1
  fi
  run_node_tests "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
