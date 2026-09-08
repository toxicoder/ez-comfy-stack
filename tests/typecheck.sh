#!/usr/bin/env bash
#
# ## typecheck
#
# Hermetic Pyright (Pylance) gate for first-party Python.
#
# Purpose:
#   Run Pyright with pyrightconfig.json so local make test / coverage / lint
#   and CI fail on type errors. Does not require GPU, ComfyUI, or Docker.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#
# Requirements:
#   python3, pyright (pip install -r tests/requirements.txt).
#
# Exit codes:
#   0 if Pyright reports no errors.
#   1 if Pyright is missing or reports errors.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
cd "${ROOT}"

#######################################
# Require the Pyright CLI module.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Install hint on stderr when missing
# Returns:
#   0 if python3 -m pyright works; 1 otherwise
#######################################
require_pyright() {
  if python3 -m pyright --version >/dev/null 2>&1; then
    return 0
  fi
  echo "Pyright is required for the typecheck gate." >&2
  echo "Install: pip install -r tests/requirements.txt" >&2
  return 1
}

#######################################
# Run Pyright from the repo root.
# Globals:
#   None
# Arguments:
#   $@ - extra args forwarded to pyright
# Outputs:
#   Pyright diagnostics on stdout/stderr
# Returns:
#   Pyright exit status
#######################################
run_pyright() {
  python3 -m pyright "$@"
}

#######################################
# Typecheck entrypoint.
# Globals:
#   None
# Arguments:
#   $@ - extra args forwarded to pyright
# Outputs:
#   Status and Pyright output
# Returns:
#   0 on success; 1 if Pyright missing or dirty
#######################################
main() {
  echo "=== Pyright (Pylance) ==="
  require_pyright
  run_pyright "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
