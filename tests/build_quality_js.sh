#!/usr/bin/env bash
#
# ## build_quality_js
#
# Bazel entry point for the Quality tier codegen.
#
# Purpose:
#   Drive tests/python/_build_quality_js.py from Bazel so the frontend tier
#   table (custom_nodes/ez_quality/js/ez_quality_presets.js) is regenerated
#   through a build target. presets.py stays the single definition; the JS
#   file is derived output. Without this target the only way to regenerate was
#   a raw python3 invocation, which no BUILD file mapped.
#
# Usage:
#   bazelisk run //tests:build_quality_js
#   bazelisk test //tests:build_quality_js_check
#   bash tests/build_quality_js.sh [--check]
#
# Safety: No Docker daemon, GPU, network, or npm. Writes only the one
#   generated JS file inside the checkout, and only without --check.
#
# Requirements:
#   python3 on PATH. Imports custom_nodes/ez_quality/presets.py directly.
#
# Exit codes:
#   0 on a successful write, or when --check finds no drift.
#   1 when --check finds the generated file stale.
#
set -euo pipefail

# shellcheck source=repo_root.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_root.sh"

# Absolute path of the generator inside the checkout, set by main.
GENERATOR=""

#######################################
# Run the generator against the checkout.
# Globals:
#   GENERATOR
# Arguments:
#   "$@" - flags forwarded to the generator (pass --check to verify only).
# Outputs:
#   The generator's own stdout line naming the file it wrote or checked.
# Returns:
#   0 on success; 1 when --check reports drift or python3 is missing.
#######################################
run_generator() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "build_quality_js: python3 is not on PATH" >&2
    return 1
  fi
  python3 "${GENERATOR}" "$@"
}

#######################################
# Resolve the checkout and dispatch.
# Globals:
#   GENERATOR
# Arguments:
#   "$@" - flags forwarded to run_generator.
# Outputs:
#   Whatever run_generator prints.
# Returns:
#   The exit status of run_generator.
#######################################
main() {
  local root
  root="$(tests_repo_root)"
  cd "${root}"
  GENERATOR="${root}/tests/python/_build_quality_js.py"
  run_generator "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
