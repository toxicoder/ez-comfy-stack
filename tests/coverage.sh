#!/usr/bin/env bash
#
# ## coverage
#
# Enforce project coverage gates for CI (`make coverage`) and local pre-merge.
#
# Gates:
#   1. Python — pytest-cov on Spark patches + seed_clay_inputs + ez_ltx_spatial with --cov-fail-under=100
#   2. Pyright (Pylance) + mypy — first-party Python typecheck (tests/typecheck.sh)
#   3. Shell function inventory — every function under scripts/ and docker/**/*.sh
#      must be named under tests/ (strict; production-only refs do not count)
#   4. Full BATS suite
#   5. Optional kcov when available (non-fatal on hosts without kcov)
#
# Hermetic: no Docker daemon, GPU, sudo, or network required.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
cd "${ROOT}"
FAIL=0

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
  bash tests/run_pytest.sh || FAIL=1

  bash tests/typecheck.sh || FAIL=1

  bash tests/shell_inventory.sh || FAIL=1

  echo "=== BATS suite ==="
  JOBS="${BATS_JOBS:-}"
  if [[ -z ${JOBS} ]]; then
    if command -v nproc >/dev/null 2>&1; then
      JOBS="$(nproc)"
    elif command -v sysctl >/dev/null 2>&1; then
      JOBS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
    else
      JOBS=4
    fi
  fi
  if bats --help 2>&1 | grep -q -- '--jobs' &&
    { command -v parallel >/dev/null 2>&1 || command -v rush >/dev/null 2>&1; }; then
    echo "bats --jobs ${JOBS} --no-parallelize-within-files"
    bats --jobs "${JOBS}" --no-parallelize-within-files tests/bats || FAIL=1
  else
    bats tests/bats || FAIL=1
  fi

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
  echo "Coverage gate PASSED (100% Python + Pyright + mypy + strict shell inventory + BATS)"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
