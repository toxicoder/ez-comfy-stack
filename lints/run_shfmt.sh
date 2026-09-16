#!/usr/bin/env bash
# Purpose: shfmt -d (diff / check) on first-party shell.
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
check_tool shfmt "brew install shfmt or see https://github.com/mvdan/sh"
cd "${ROOT}"

echo "Running shfmt -d..."
shfmt -d -s -i 2 -ci \
  scripts docker/install-comfy.sh docker/install-comfy docker/entrypoint.sh \
  tests/coverage.sh tests/run_all.sh tests/run_pytest.sh tests/shell_inventory.sh \
  tests/typecheck.sh tests/bats_runner.sh \
  lints docs/manage-docs.sh fix.sh \
  .devcontainer/doctor.sh .devcontainer/post-create.sh
echo "shfmt check passed."
