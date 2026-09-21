#!/usr/bin/env bash
# Purpose: ShellCheck all first-party shell at warning severity.
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
check_tool shellcheck "apt install shellcheck or brew install shellcheck"
cd "${ROOT}"

echo "Running shellcheck..."
shellcheck --version
find . -name '*.sh' \
  -not -path './.git/*' \
  -not -path './site/*' \
  -not -path './bazel-*/*' \
  -not -path './.venv*/*' \
  -not -path '*/node_modules/*' \
  -print0 | xargs -0 shellcheck -x --severity=warning
echo "Shell lint step finished."
