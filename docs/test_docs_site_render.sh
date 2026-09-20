#!/usr/bin/env bash
# Wrapper for docs/test_docs_site_render.py (source contract + optional export checks).
set -euo pipefail

if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  cd "${BUILD_WORKSPACE_DIRECTORY}"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${SCRIPT_DIR}/.."
fi

exec python3 docs/test_docs_site_render.py "$@"
