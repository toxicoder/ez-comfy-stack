#!/usr/bin/env bash
#
# ## run_all
#
# Hermetic full-suite entrypoint for local developers and `make test`.
#
# Purpose:
#   Run BATS for all suites under tests/bats, then Python tests for the Spark
#   free-memory patch (preferring pytest-cov when installed), then re-run
#   safety.bats as an explicit safety grep pass.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#
# Requirements:
#   bats, python3, pytest (optional pytest-cov). No GPU or Hugging Face network.
#
# Exit codes:
#   Non-zero if any stage fails (set -e).
#
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
cd "${ROOT}"

echo "==> BATS"
bats tests/bats/*.bats

echo "==> Python"
python3 -m pytest tests/python -q --cov=docker/patch_get_free_memory \
  --cov-report=term-missing --cov-fail-under=100 2>/dev/null ||
  python3 -m pytest tests/python -q

echo "==> Safety greps"
bats tests/bats/safety.bats

echo "==> All tests passed"
