#!/usr/bin/env bash
#
# ## coverage
#
# Enforce project coverage gates for CI (`make coverage`) and local pre-merge.
#
# Gates:
#   1. Python — pytest-cov on patch_get_free_memory with --cov-fail-under=100
#   2. Shell function inventory — every function under scripts/ and docker/*.sh
#      must be named under tests/ (strict; production-only refs do not count)
#   3. Full BATS suite
#   4. Optional kcov when available (non-fatal on hosts without kcov)
#
# Hermetic: no Docker daemon, GPU, sudo, or network required.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
cd "${ROOT}"
FAIL=0

#######################################
# Collect production function names from scripts/ and docker/*.sh.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes sorted unique function names to stdout (one per line)
# Returns:
#   0
#######################################
list_production_functions() {
  {
    grep -RhoE '^[a-zA-Z_][a-zA-Z0-9_]*\(\)' scripts --include='*.sh' 2>/dev/null || true
    grep -RhoE '^[a-zA-Z_][a-zA-Z0-9_]*\(\)' docker --include='*.sh' 2>/dev/null || true
  } | sed 's/()//' | sort -u
}

#######################################
# Coverage gate entrypoint.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Gate results on stdout/stderr
# Returns:
#   0 if all gates pass; 1 otherwise
#######################################
main() {
  echo "=== Python coverage (100%) ==="
  if ! python3 -c 'import pytest, pytest_cov' 2>/dev/null; then
    echo "Install pytest-cov: pip install pytest pytest-cov" >&2
    FAIL=1
  else
    PYTHONPATH="${ROOT}/docker" python3 -m pytest tests/python -q \
      --cov=patch_get_free_memory \
      --cov-report=term-missing \
      --cov-fail-under=100 || FAIL=1
  fi

  echo "=== Shell function inventory (strict: must appear under tests/) ==="
  FUNCS="$(list_production_functions)"
  TEST_BLOB="$(cat tests/bats/*.bats tests/bats/*.bash tests/python/*.py tests/*.sh 2>/dev/null || true)"

  MISSING=""
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    # Entrypoints are exercised by executing the script; skip inventory.
    case "${f}" in
      main) continue ;;
    esac
    if ! grep -qE "\\b${f}\\b" <<<"${TEST_BLOB}"; then
      MISSING="${MISSING}${f}"$'\n'
    fi
  done <<<"${FUNCS}"

  if [[ -n ${MISSING} ]]; then
    echo "Untested shell functions (not referenced under tests/):" >&2
    printf '%s' "${MISSING}" >&2
    FAIL=1
  else
    count="$(echo "${FUNCS}" | grep -c . || true)"
    echo "All ${count} production shell functions referenced under tests/."
  fi

  echo "=== BATS suite ==="
  bats tests/bats/*.bats || FAIL=1

  # Optional kcov — never fail the gate (CI/mac may lack paths kcov expects)
  if command -v kcov >/dev/null 2>&1; then
    echo "=== kcov line coverage (optional; non-fatal) ==="
    rm -rf coverage/kcov
    mkdir -p coverage/kcov
    if kcov --bash-dont-parse-binary-dir coverage/kcov \
      bash scripts/manage.sh help 2>/dev/null; then
      echo "kcov report: coverage/kcov"
    else
      echo "kcov skipped or failed (non-fatal)"
    fi
  fi

  if [[ ${FAIL} -ne 0 ]]; then
    echo "Coverage gate FAILED" >&2
    exit 1
  fi
  echo "Coverage gate PASSED (100% Python + strict shell inventory + BATS)"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
