#!/usr/bin/env bash
#
# ## run_pytest
#
# Hermetic pytest + 100% coverage gate on Spark patches.
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

export PYTHONPATH="${ROOT}/docker:${ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}"

if python3 -c 'import pytest, pytest_cov' 2>/dev/null; then
  python3 -m pytest tests/python -q \
    --cov=patch_get_free_memory \
    --cov=patch_unified_memory_copy \
    --cov=patch_magcache_compat \
    --cov=patch_vhs_widget_inputs \
    --cov=seed_clay_inputs \
    --cov=ez_ltx_spatial \
    --cov-report=term-missing \
    --cov-fail-under=100
else
  python3 -m pytest tests/python -q
fi
