#!/usr/bin/env bash
# ## setup-docs
#
# Idempotent setup for the Fumadocs documentation site (npm packages).
#
# Usage:
#   ./docs/setup-docs.sh
#   QUIET=true ./docs/setup-docs.sh
#
# Safety: Installs into docs-site/node_modules. Never publishes.

set -euo pipefail

QUIET=${QUIET:-false}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  REPO_ROOT="${BUILD_WORKSPACE_DIRECTORY}"
else
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"
SITE_DIR="${REPO_ROOT}/docs-site"

if [[ ${QUIET} != "true" ]]; then
  echo "=== ez-comfy-stack documentation setup ==="
  echo "Repo root: ${REPO_ROOT}"
fi

#######################################
# Install Next.js app dependencies from the pinned lockfile.
# Globals:
#   SITE_DIR, QUIET
# Arguments:
#   None
# Outputs:
#   Status lines
# Returns:
#   0 when present or installed
#######################################
docs_install_site_deps() {
  if [[ ! -f ${SITE_DIR}/package.json ]]; then
    echo "setup-docs: docs-site/package.json not found" >&2
    return 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "setup-docs: npm is required (Node.js 22+)" >&2
    return 1
  fi
  if [[ -x ${SITE_DIR}/node_modules/.bin/next && -x ${SITE_DIR}/node_modules/.bin/vitest ]]; then
    if [[ ${QUIET} != "true" ]]; then
      echo "docs-site dependencies already installed."
    fi
    return 0
  fi
  if [[ ${QUIET} != "true" ]]; then
    echo "→ docs-site: npm ci"
  fi
  (cd "${SITE_DIR}" && npm ci --legacy-peer-deps)
}

docs_install_site_deps

if [[ ${QUIET} != "true" ]]; then
  echo ""
  echo "=== Setup complete ==="
  echo "  ./docs/manage-docs.sh serve"
  echo "  ./docs/manage-docs.sh build"
  echo "  bazelisk run //docs:serve"
fi
