#!/usr/bin/env bash
#
# ## post-create
#
# Install Python test/docs deps and prewarm bazelisk so the first IDE query
# does not race the Bazel download.
#
# Usage:
#   bash .devcontainer/post-create.sh
#   bash .devcontainer/post-create.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  echo "Usage: post-create.sh"
  echo "Installs tests/requirements.txt and prewarms bazelisk version."
  exit 0
fi

cd "${REPO_ROOT}"
python3 -m pip install --user -r tests/requirements.txt
if [[ -f docs/requirements.txt ]]; then
  python3 -m pip install --user -r docs/requirements.txt || true
fi
if command -v npm >/dev/null 2>&1 && [[ -f docs-site/package.json ]]; then
  (cd docs-site && npm ci --legacy-peer-deps)
fi
bazelisk version
echo "post-create: ready — bazelisk run //:validate"
