#!/usr/bin/env bash
#
# ## manage-docs
#
# Bazel / local interface for the MkDocs Material site.
#
# Usage:
#   bazelisk run //docs:docs     # generate + strict build
#   bazelisk run //docs:serve
#   ./docs/manage-docs.sh build|serve|status|clean|preview
#
# Safety: Writes generated markdown and site/ only. No Compose or GPU.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  REPO_ROOT="${BUILD_WORKSPACE_DIRECTORY}"
  SCRIPT_DIR="${REPO_ROOT}/docs"
else
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"

CMD="${1:-build}"

#######################################
# Generate shell + workflow references then strict MkDocs build.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Generator and mkdocs logs
# Returns:
#   0 on success
#######################################
docs_build() {
  python3 "${REPO_ROOT}/docs/generate_shell_docs.py"
  python3 "${REPO_ROOT}/docs/generate_workflow_docs.py"
  python3 "${REPO_ROOT}/docs/generate_cinema_docs.py"
  NO_MKDOCS_2_WARNING=1 python3 -m mkdocs build --strict
  touch "${REPO_ROOT}/site/.nojekyll"
}

#######################################
# Serve MkDocs locally.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Dev server
# Returns:
#   mkdocs serve status
#######################################
docs_serve() {
  python3 "${REPO_ROOT}/docs/generate_shell_docs.py"
  python3 "${REPO_ROOT}/docs/generate_workflow_docs.py"
  python3 "${REPO_ROOT}/docs/generate_cinema_docs.py"
  NO_MKDOCS_2_WARNING=1 python3 -m mkdocs serve
}

#######################################
# Print docs tool status.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Status lines
# Returns:
#   0
#######################################
docs_status() {
  echo "REPO_ROOT=${REPO_ROOT}"
  python3 -m mkdocs --version
  [[ -f ${REPO_ROOT}/mkdocs.yml ]]
}

#######################################
# Remove the local site/ directory.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
docs_clean() {
  rm -rf "${REPO_ROOT}/site"
}

#######################################
# Strict build then a one-shot static hint.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Build logs
# Returns:
#   0 on success
#######################################
docs_preview() {
  docs_build
  echo "Built site/ — open site/index.html or: bazelisk run //docs:serve"
}

case "${CMD}" in
  build | docs) docs_build ;;
  serve) docs_serve ;;
  status) docs_status ;;
  clean) docs_clean ;;
  preview) docs_preview ;;
  -h | --help | help)
    echo "Usage: docs/manage-docs.sh build|serve|status|clean|preview"
    ;;
  *)
    echo "docs/manage-docs.sh: unknown command: ${CMD}" >&2
    exit 2
    ;;
esac
