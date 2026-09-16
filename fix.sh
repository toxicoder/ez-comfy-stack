#!/usr/bin/env bash
#
# ## fix
#
# Run trusted formatters (buildifier + shfmt).
#
# Usage:
#   bazelisk run //:fix
#   ./fix.sh
#
# Safety: formatters only. Does not change Compose restart policy, headroom,
# or download-limit. Missing tools are skipped unless CI=true.
#
# @command fix
# @description Format BUILD files and shell sources with trusted tools.
# Usage: bazelisk run //:fix
# Safety: Write-only formatters; no cluster or GPU side effects.

set -euo pipefail

ROOT="${BUILD_WORKSPACE_DIRECTORY:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
cd "${ROOT}"

echo "→ Running trusted formatters (//:fix)"

if command -v buildifier >/dev/null 2>&1; then
  echo "   buildifier -mode=fix"
  find . -type f \( -name 'BUILD' -o -name 'BUILD.bazel' -o -name 'MODULE.bazel' -o -name '*.bzl' \) \
    ! -path '*/bazel-*/*' \
    ! -path './site/*' \
    ! -path './.venv*' \
    ! -path './node_modules/*' \
    -exec buildifier -mode=fix {} +
else
  echo "   (buildifier not in PATH - skipping)"
fi

if command -v shfmt >/dev/null 2>&1; then
  echo "   shfmt -w -s -i 2 -ci"
  find . -name '*.sh' \
    ! -path '*/bazel-*/*' \
    ! -path './site/*' \
    ! -path './.venv*' \
    ! -path './node_modules/*' \
    -exec shfmt -w -s -i 2 -ci {} +
else
  echo "   (shfmt not in PATH - skipping)"
fi

echo "✓ fix complete (run 'bazelisk test //:lint --test_tag_filters=manual' for checks)"
