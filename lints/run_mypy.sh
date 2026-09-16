#!/usr/bin/env bash
# Purpose: mypy using mypy.ini on first-party Python.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n ${TEST_SRCDIR:-} && -f ${TEST_SRCDIR}/_main/scripts/lib/check_tool.sh ]]; then
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${TEST_SRCDIR}/_main/scripts/lib/check_tool.sh"
elif [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${BUILD_WORKSPACE_DIRECTORY}/scripts/lib/check_tool.sh"
else
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${SCRIPT_DIR}/../scripts/lib/check_tool.sh"
fi
ROOT="$(bazel_checkout_root)"
check_tool python3 "install Python 3"
cd "${ROOT}"
if ! python3 -m mypy --version >/dev/null 2>&1; then
  if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
    echo "mypy missing - required in CI/strict mode (pip install -r tests/requirements.txt)" >&2
    exit 1
  fi
  echo "mypy missing - skipping (resilient; pip install -r tests/requirements.txt)"
  exit 0
fi
echo "Running mypy..."
python3 -m mypy
echo "mypy passed."
