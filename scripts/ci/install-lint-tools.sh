#!/usr/bin/env bash
#
# ## CI lint tool installer
#
# Install host lint and formatter binaries on Ubuntu GitHub runners
# (and optionally other Linux hosts). Shared by setup-bazel and local bootstrap.
#
# Versions come from .devcontainer/tool-versions.env (single source of truth).
# Supports linux/amd64 and linux/arm64 (DGX Spark Grace, Apple Silicon).
#
# Installs:
#   - shellcheck, bats (apt)
#   - pytest, pyright, mypy (pip via tests/requirements.txt)
#   - buildifier, shfmt (release binaries, arch-aware)
#
# Safety:
# - Installs to system paths only; does not modify repo sources or Compose.
# - Requires sudo for apt and /usr/local/bin when not root.
#
# Usage:
#   bash scripts/ci/install-lint-tools.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VERSIONS_FILE="${REPO_ROOT}/.devcontainer/tool-versions.env"

if [[ ! -f ${VERSIONS_FILE} ]]; then
  echo "install-lint-tools: missing ${VERSIONS_FILE}" >&2
  exit 1
fi

set -a
# shellcheck source=../../.devcontainer/tool-versions.env disable=SC1091
source "${VERSIONS_FILE}"
set +a

: "${BUILDIFIER_VERSION:?}"
: "${SHFMT_ASSET_VERSION:?}"

echo "Installing lint tools (pins from tool-versions.env)..."

#######################################
# Run a command as root when needed.
# Globals:
#   None
# Arguments:
#   $@ - command
# Outputs:
#   Command output
# Returns:
#   Command status
#######################################
run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

#######################################
# Map uname -m to release asset arch (amd64|arm64).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   amd64 or arm64
# Returns:
#   0 or 1
#######################################
detect_arch() {
  local m
  m="$(uname -m)"
  case "${m}" in
    x86_64 | amd64) echo "amd64" ;;
    aarch64 | arm64) echo "arm64" ;;
    *)
      echo "install-lint-tools: unsupported arch ${m} (need x86_64 or aarch64)" >&2
      return 1
      ;;
  esac
}

#######################################
# Download buildifier and shfmt for the host arch.
# Globals:
#   BUILDIFIER_VERSION, SHFMT_ASSET_VERSION
# Arguments:
#   None
# Outputs:
#   Install progress
# Returns:
#   0 on success
#######################################
install_release_bins() {
  local arch
  arch="$(detect_arch)"

  curl -fsSL "https://github.com/bazelbuild/buildtools/releases/download/${BUILDIFIER_VERSION}/buildifier-linux-${arch}" \
    -o /tmp/buildifier
  run_root install /tmp/buildifier /usr/local/bin/buildifier
  buildifier --version || buildifier -version || true

  curl -fsSL "https://github.com/mvdan/sh/releases/download/v${SHFMT_ASSET_VERSION}/shfmt_v${SHFMT_ASSET_VERSION}_linux_${arch}" \
    -o /tmp/shfmt
  run_root install /tmp/shfmt /usr/local/bin/shfmt
  shfmt --version
}

run_root apt-get update -qq
run_root apt-get install -y -qq shellcheck curl ca-certificates python3-pip

pip install -r "${REPO_ROOT}/tests/requirements.txt"

if [[ ${LINT_BINS_CACHE_HIT:-} == "true" ]] &&
  command -v buildifier >/dev/null 2>&1 &&
  command -v shfmt >/dev/null 2>&1; then
  echo "Lint release binaries restored from cache."
  run_root chmod +x /usr/local/bin/buildifier /usr/local/bin/shfmt || true
else
  install_release_bins
fi

echo "Lint + formatter tools installed (buildifier ${BUILDIFIER_VERSION}, shfmt v${SHFMT_ASSET_VERSION})."
