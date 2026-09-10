#!/usr/bin/env bash
#
# ## typecheck
#
# Hermetic Pyright (Pylance) + mypy gate for first-party Python.
#
# Purpose:
#   Run Pyright with pyrightconfig.json and mypy with mypy.ini so local
#   make test / coverage / lint and CI fail on type errors. Does not require
#   GPU, ComfyUI, or Docker.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#
# Requirements:
#   python3, pyright, mypy (pip install -r tests/requirements.txt).
#
# Exit codes:
#   0 if both checkers report no errors.
#   1 if either checker is missing or reports errors.
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
# Require the mypy CLI module.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Install hint on stderr when missing
# Returns:
#   0 if python3 -m mypy works; 1 otherwise
#######################################
require_mypy() {
  if python3 -m mypy --version >/dev/null 2>&1; then
    return 0
  fi
  echo "mypy is required for the typecheck gate." >&2
  echo "Install: pip install -r tests/requirements.txt" >&2
  return 1
}

#######################################
# Run mypy from the repo root using mypy.ini.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   mypy diagnostics on stdout/stderr
# Returns:
#   mypy exit status
#######################################
run_mypy() {
  python3 -m mypy
}

#######################################
# Typecheck entrypoint.
# Globals:
#   None
# Arguments:
#   $@ - extra args forwarded to pyright only
# Outputs:
#   Status and checker output
# Returns:
#   0 on success; 1 if either checker is missing or dirty
#######################################
main() {
  local fail=0

  echo "=== Pyright (Pylance) ==="
  if ! require_pyright; then
    fail=1
  elif ! run_pyright "$@"; then
    fail=1
  fi

  echo "=== mypy ==="
  if ! require_mypy; then
    fail=1
  elif ! run_mypy; then
    fail=1
  fi

  if [[ ${fail} -ne 0 ]]; then
    return 1
  fi
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
