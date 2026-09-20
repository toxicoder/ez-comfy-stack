#!/usr/bin/env bash
#
# ## run_pytest
#
# Hermetic pytest + 100% coverage gate on first-party production Python.
#
# Usage:
#   bash tests/run_pytest.sh
#   bazelisk test //tests:pytest
#
# Safety: No Docker daemon, GPU, or network.

set -euo pipefail

# shellcheck source=repo_root.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_root.sh"
ROOT="$(tests_repo_root)"
cd "${ROOT}"

export PYTHONPATH="${ROOT}/docker:${ROOT}/docker/pythonpath:${ROOT}/custom_nodes:${ROOT}/scripts/lib:${ROOT}/studio-ui:${ROOT}/docs:${ROOT}/tools:${ROOT}/tools/blender${PYTHONPATH:+:${PYTHONPATH}}"

# One pytest process so coverage stay combined; xdist only parallelizes tests.
PYTEST_ARGS=(tests/python -q)
if python3 -c 'import xdist' 2>/dev/null; then
  PYTEST_ARGS+=(-n auto --dist worksteal)
fi

if python3 -c 'import pytest, pytest_cov' 2>/dev/null; then
  python3 -m pytest "${PYTEST_ARGS[@]}" \
    --cov=custom_nodes \
    --cov=docker \
    --cov=docs \
    --cov=scripts/lib \
    --cov=studio-ui \
    --cov=tools \
    --cov-config=tests/.coveragerc \
    --cov-report=term-missing \
    --cov-fail-under=100
else
  python3 -m pytest "${PYTEST_ARGS[@]}"
fi
