#!/usr/bin/env bash
# Purpose: buildifier -mode=check on BUILD / MODULE / .bzl files.
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
check_tool buildifier "install from https://github.com/bazelbuild/buildtools/releases"
cd "${ROOT}"

echo "Running buildifier -mode=check..."
find . -type f \( \
  -name 'BUILD' -o \
  -name 'BUILD.bazel' -o \
  -name 'MODULE.bazel' -o \
  -name '*.bzl' \
  \) \
  ! -path '*/bazel-*/*' \
  ! -path './site/*' \
  ! -path './.venv*' \
  ! -path '*/node_modules/*' \
  -exec buildifier -mode=check {} +
echo "buildifier check passed."
