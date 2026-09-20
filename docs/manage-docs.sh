#!/usr/bin/env bash
#
# ## manage-docs
#
# Bazel / local interface for the Fumadocs (Next.js) documentation site.
#
# Usage:
#   bazelisk run //docs:docs     # generate + static export
#   bazelisk run //docs:serve
#   ./docs/manage-docs.sh build|serve|status|clean|preview
#
# Safety: Writes generated markdown and docs-site/out only. No Compose or GPU.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  REPO_ROOT="${BUILD_WORKSPACE_DIRECTORY}"
  SCRIPT_DIR="${REPO_ROOT}/docs"
else
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"
SITE_DIR="${REPO_ROOT}/docs-site"
DEFAULT_PORT=3005
PORT=${PORT:-${DEFAULT_PORT}}
AUTO_OPEN_BROWSER=true
: "${AUTO_SETUP_DOCS:=true}"

CMD="${1:-build}"
shift || true

#######################################
# Ensure Node 22+ and docs-site dependencies.
# Globals:
#   SITE_DIR, AUTO_SETUP_DOCS, SCRIPT_DIR
# Arguments:
#   None
# Outputs:
#   Error lines when the toolchain is missing
# Returns:
#   Exits 1 when Node/npm cannot satisfy the build
#######################################
docs_node_is_ready() {
  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "docs: Node.js 22+ and npm are required for the documentation site." >&2
    echo "docs: On a host: brew install node@22" >&2
    exit 1
  fi
  local node_major
  node_major="$(node -p 'Number.parseInt(process.versions.node.split(".")[0], 10)' 2>/dev/null || echo 0)"
  if [[ ! ${node_major:-0} =~ ^[0-9]+$ ]] || [[ ${node_major:-0} -lt 22 ]]; then
    echo "docs: Node is too old for Next 16 (need 22+)." >&2
    exit 1
  fi
  if [[ ! -x ${SITE_DIR}/node_modules/.bin/next ]]; then
    if [[ ${AUTO_SETUP_DOCS} == "true" ]]; then
      QUIET=true "${SCRIPT_DIR}/setup-docs.sh" || {
        echo "docs: failed to prepare the docs site via docs/setup-docs.sh" >&2
        exit 1
      }
    else
      echo "docs: docs-site/node_modules is missing. Run ./docs/setup-docs.sh first." >&2
      exit 1
    fi
  fi
}

#######################################
# Run the Python generators that fill docs/generated/.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   Generator logs
# Returns:
#   0; generator failures are fatal
#######################################
generate_code_docs() {
  python3 "${REPO_ROOT}/docs/generate_shell_docs.py"
  python3 "${REPO_ROOT}/docs/generate_workflow_docs.py"
  python3 "${REPO_ROOT}/docs/generate_cinema_docs.py"
  python3 "${REPO_ROOT}/docs/generate_audio_docs.py"
}

#######################################
# Copy cinema/media assets into the Next public tree.
# Globals:
#   REPO_ROOT, SITE_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
sync_public_assets() {
  mkdir -p "${SITE_DIR}/public"
  if [[ -d ${REPO_ROOT}/docs/assets ]]; then
    rm -rf "${SITE_DIR}/public/assets"
    cp -R "${REPO_ROOT}/docs/assets" "${SITE_DIR}/public/assets"
  fi
}

#######################################
# Generate + static export.
# Globals:
#   REPO_ROOT, SITE_DIR, NODE_OPTIONS, NEXT_TELEMETRY_DISABLED
# Arguments:
#   Optional --version latest|development
# Outputs:
#   Build logs
# Returns:
#   next build status
#######################################
docs_build() {
  local version=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --strict) shift ;;
      --no-strict) shift ;;
      --version)
        version="$2"
        shift 2
        ;;
      *)
        echo "docs/manage-docs.sh: unknown build option: $1" >&2
        exit 2
        ;;
    esac
  done
  docs_node_is_ready
  generate_code_docs
  sync_public_assets
  export NEXT_TELEMETRY_DISABLED="${NEXT_TELEMETRY_DISABLED:-1}"
  if [[ -z ${NODE_OPTIONS:-} ]]; then
    export NODE_OPTIONS="--max-old-space-size=6144"
  fi
  local build_script="build"
  case "${version}" in
    "") ;;
    latest) build_script="build:latest" ;;
    development) build_script="build:development" ;;
    *)
      echo "docs: --version must be latest or development, got ${version}" >&2
      exit 1
      ;;
  esac
  (cd "${SITE_DIR}" && npm run "${build_script}")
  echo "Build complete. Output is in docs-site/out/"
}

#######################################
# Serve the Next dev server.
# Globals:
#   SITE_DIR, PORT, AUTO_OPEN_BROWSER
# Arguments:
#   --port N, --no-browser
# Outputs:
#   Dev server
# Returns:
#   next dev status
#######################################
docs_serve() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --port)
        PORT="$2"
        shift 2
        ;;
      --no-browser)
        AUTO_OPEN_BROWSER=false
        shift
        ;;
      *)
        echo "docs/manage-docs.sh: unknown serve option: $1" >&2
        exit 2
        ;;
    esac
  done
  docs_node_is_ready
  generate_code_docs
  sync_public_assets
  if [[ ${AUTO_OPEN_BROWSER} == "true" ]] && command -v python3 >/dev/null 2>&1; then
    python3 -m webbrowser "http://localhost:${PORT}" 2>/dev/null || true
  fi
  (cd "${SITE_DIR}" && exec npm run dev -- --port "${PORT}" --hostname localhost)
}

#######################################
# Print docs tool status.
# Globals:
#   REPO_ROOT, SITE_DIR
# Arguments:
#   None
# Outputs:
#   Status lines
# Returns:
#   0
#######################################
docs_status() {
  echo "REPO_ROOT=${REPO_ROOT}"
  echo "Content root:          $([ -d ${REPO_ROOT}/docs ] && echo 'docs/' || echo 'MISSING')"
  echo "Navigation tree:       $([ -f ${SITE_DIR}/lib/nav.json ] && echo 'docs-site/lib/nav.json' || echo 'MISSING')"
  echo "source.config.ts:      $([ -f ${SITE_DIR}/source.config.ts ] && echo 'present' || echo 'MISSING')"
  if command -v node >/dev/null 2>&1; then
    echo "Node:                  $(node --version)"
  else
    echo "Node:                  not in PATH"
  fi
  if [[ -x ${SITE_DIR}/node_modules/.bin/next ]]; then
    echo "Dependencies:          installed"
  else
    echo "Dependencies:          not installed (run ./docs/setup-docs.sh)"
  fi
  echo "Static export:         $([ -f ${SITE_DIR}/out/index.html ] && echo 'docs-site/out/' || echo 'not built')"
}

#######################################
# Remove local Next build artifacts.
# Globals:
#   SITE_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
docs_clean() {
  rm -rf "${SITE_DIR}/out" "${SITE_DIR}/out-linux" "${SITE_DIR}/.next" "${SITE_DIR}/.source" \
    "${SITE_DIR}/public/assets"
}

#######################################
# Export then serve the static tree.
# Globals:
#   SITE_DIR, PORT
# Arguments:
#   None
# Outputs:
#   Build + serve logs
# Returns:
#   0 on success
#######################################
docs_preview() {
  docs_build
  echo "Serving the static export from docs-site/out/ on port ${PORT}..."
  (cd "${SITE_DIR}" && npm run serve -- "${PORT}" out)
}

case "${CMD}" in
  build | docs) docs_build "$@" ;;
  serve) docs_serve "$@" ;;
  status) docs_status ;;
  clean) docs_clean ;;
  preview) docs_preview ;;
  typecheck)
    docs_node_is_ready
    (cd "${SITE_DIR}" && npm run typecheck)
    ;;
  test)
    docs_node_is_ready
    (cd "${SITE_DIR}" && npm run unit)
    ;;
  -h | --help | help)
    echo "Usage: docs/manage-docs.sh build|serve|status|clean|preview|typecheck|test"
    ;;
  *)
    echo "docs/manage-docs.sh: unknown command: ${CMD}" >&2
    exit 2
    ;;
esac
