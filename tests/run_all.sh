#!/usr/bin/env bash
#
# ## run_all
#
# Hermetic full-suite entrypoint for local developers and `make test`.
#
# Purpose:
#   Run BATS for all suites under tests/bats, then Python tests for the Spark
#   free-memory patch (preferring pytest-cov when installed).
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#
# Requirements:
#   bats, python3, pytest (optional pytest-cov). GNU parallel recommended for
#   bats --jobs. No GPU or Hugging Face network.
#
# Environment:
#   BATS_JOBS — parallel BATS file jobs (default: nproc or 4)
#
# Exit codes:
#   Non-zero if any stage fails (set -e).
#
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
cd "${ROOT}"

#######################################
# Resolve parallel job count for bats --jobs.
# Globals:
#   BATS_JOBS
# Arguments:
#   None
# Outputs:
#   Integer jobs on stdout
# Returns:
#   0
#######################################
bats_job_count() {
  if [[ -n ${BATS_JOBS:-} ]]; then
    echo "${BATS_JOBS}"
    return 0
  fi
  if command -v nproc >/dev/null 2>&1; then
    nproc
    return 0
  fi
  if command -v sysctl >/dev/null 2>&1; then
    sysctl -n hw.ncpu 2>/dev/null && return 0
  fi
  echo 4
}

echo "==> BATS"
JOBS="$(bats_job_count)"
if bats --help 2>&1 | grep -q -- '--jobs'; then
  # Parallel across files; serialize within file (safer for shared setup patterns).
  if command -v parallel >/dev/null 2>&1 || command -v rush >/dev/null 2>&1; then
    echo "bats --jobs ${JOBS} --no-parallelize-within-files"
    bats --jobs "${JOBS}" --no-parallelize-within-files tests/bats
  else
    echo "GNU parallel/rush not found; running bats serially (install parallel for speed)"
    bats tests/bats
  fi
else
  bats tests/bats
fi

echo "==> Python"
export PYTHONPATH="${ROOT}/docker${PYTHONPATH:+:${PYTHONPATH}}"
if python3 -c 'import pytest, pytest_cov' 2>/dev/null; then
  python3 -m pytest tests/python -q --cov=patch_get_free_memory \
    --cov-report=term-missing --cov-fail-under=100
else
  python3 -m pytest tests/python -q
fi

echo "==> All tests passed"
