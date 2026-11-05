#!/usr/bin/env bash
#
# ## run_pytest
#
# Hermetic pytest + 100% coverage gate on first-party production Python.
#
# The gate is un-skippable on purpose. A host that never installed pytest or
# pytest-cov fails the target with the repair command instead of running the
# suite unmeasured and reporting green, and every tree the gate claims to
# measure must exist and hold production Python. tests/python/
# test_coverage_gate.py pins COV_SCOPE below against the tracked first-party
# packages, so a new package cannot join the tree without joining the gate.
#
# Usage:
#   bazelisk test //tests:pytest
#
# Safety: No Docker daemon, GPU, or network.

set -euo pipefail

# shellcheck source=repo_root.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_root.sh"
ROOT="$(tests_repo_root)"
cd "${ROOT}"

export PYTHONPATH="${ROOT}/docker:${ROOT}/docker/pythonpath:${ROOT}/custom_nodes:${ROOT}/scripts/lib:${ROOT}/studio-ui:${ROOT}/docs:${ROOT}/tools:${ROOT}/tools/blender${PYTHONPATH:+:${PYTHONPATH}}"

# First-party production trees the 100% floor measures, in report order. Keep
# this list and tests/.coveragerc honest through tests/python/
# test_coverage_gate.py: it walks the tracked tree and fails when a package
# with production Python is missing here, or when an omit rule would hide one.
COV_SCOPE=(
  custom_nodes
  docker
  docs
  scripts/lib
  studio-ui
  tools
)

#######################################
# Require a python module the coverage gate depends on.
# Globals:
#   None
# Arguments:
#   $1 - python module name to import
#   $2 - command that installs it
# Outputs:
#   Repair instructions on stderr when the module is missing
# Returns:
#   0 when python3 can import it; 1 otherwise
#######################################
require_module() {
  local module="${1}" installer="${2}"
  if ! python3 -c "import ${module}" >/dev/null 2>&1; then
    echo "run_pytest: python3 cannot import ${module}; refusing to run the suite unmeasured" >&2
    echo "run_pytest: repair with '${installer}', or 'bazelisk run //:setup-host'" >&2
    return 1
  fi
  return 0
}

#######################################
# Require a measured tree to exist and hold production Python.
# Globals:
#   None
# Arguments:
#   $1 - path relative to the repo root
# Outputs:
#   Failure reason on stderr when the tree is gone or holds nothing to measure
# Returns:
#   0 when the tree is measurable; 1 otherwise
#######################################
require_measurable() {
  local pkg="${1}" found=""
  if [[ ! -d ${pkg} ]]; then
    echo "run_pytest: ${pkg} is in COV_SCOPE but absent from the tree" >&2
    return 1
  fi
  found="$(find "${pkg}" -name '*.py' -not -name 'test_*' -not -path '*/__pycache__/*' -print -quit 2>/dev/null || true)"
  if [[ -z ${found} ]]; then
    echo "run_pytest: ${pkg} holds no first-party production Python to measure" >&2
    return 1
  fi
  return 0
}

REQUIREMENTS="tests/requirements.txt"
require_module pytest "python3 -m pip install -r ${REQUIREMENTS}" || exit 1
require_module pytest_cov "python3 -m pip install -r ${REQUIREMENTS}" || exit 1

for pkg in "${COV_SCOPE[@]}"; do
  require_measurable "${pkg}" || exit 1
done

# One pytest process so coverage stay combined; xdist only parallelizes tests.
PYTEST_ARGS=(tests/python -q)
if python3 -c 'import xdist' 2>/dev/null; then
  PYTEST_ARGS+=(-n auto --dist worksteal)
fi

for pkg in "${COV_SCOPE[@]}"; do
  PYTEST_ARGS+=(--cov="${pkg}")
done

PYTEST_ARGS+=(
  --cov-config=tests/.coveragerc
  --cov-report=term-missing
  --cov-fail-under=100
)

echo "=== pytest + 100% coverage gate over: ${COV_SCOPE[*]} ==="
python3 -m pytest "${PYTEST_ARGS[@]}"
