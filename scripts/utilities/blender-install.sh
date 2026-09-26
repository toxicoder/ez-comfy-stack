#!/usr/bin/env bash
#
# ## blender-install
#
# Host apt install of Ubuntu blender for Workbench dumps. Never in
# docker/Dockerfile. Occupancy does not install Blender.
#
# Usage:
#   ./scripts/utilities/blender-install.sh
#   ./scripts/manage.sh blender-install
#
# Safety:
#   Host package only. Does not start Compose. Does not weaken restart: "no",
#   headroom, or download-limit clear-on-exit. Does not fetch unofficial
#   aarch64 CUDA tarballs.
#
# Environment:
#   BLENDER_BIN, LAB_MOCK_BLENDER_INSTALL, LAB_MOCK_BLENDER_BIN_DIR, LAB_NO_SUDO
#
# @command blender-install

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/blender_host.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/blender_host.sh"

#######################################
# Print blender-install help.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: blender-install.sh" >&2
  echo "  Host apt install of Ubuntu blender (universe). Never in docker/Dockerfile." >&2
  echo "  occupancy enter blender-desk does not install Blender." >&2
  echo "  Prefer: ./scripts/manage.sh blender-install" >&2
  echo "  See docs/blender-gb10-sidecar.md" >&2
}

#######################################
# Hermetic mock blender on PATH (never apt).
# Globals:
#   LAB_MOCK_BLENDER_BIN_DIR, TEST_TMP_DIR, PATH
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0 when the mock binary is executable
#######################################
mock_blender_install() {
  local bindir
  bindir="${LAB_MOCK_BLENDER_BIN_DIR:-${TEST_TMP_DIR:-/tmp}/bin}"
  mkdir -p "${bindir}"
  cat >"${bindir}/blender" <<'EOF'
#!/usr/bin/env bash
echo "mock-blender $*"
exit 0
EOF
  chmod +x "${bindir}/blender"
  export PATH="${bindir}:${PATH}"
  log "LAB_MOCK_BLENDER_INSTALL: mock blender at ${bindir}/blender"
}

#######################################
# Install host blender via apt, or no-op when already resolved.
# Globals:
#   BLENDER_BIN, LAB_MOCK_BLENDER_INSTALL, LAB_NO_SUDO, PATH
# Arguments:
#   $@  optional -h/--help
# Outputs:
#   Help or install hint on stderr
# Returns:
#   0 present or installed; 1 missing/sudo/apt refuse
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
    cmd_help
    return 0
  fi
  if [[ $# -gt 0 ]]; then
    err "Usage: blender-install.sh"
    cmd_help
    return 1
  fi
  local existing=""
  if existing="$(blender_host_bin)"; then
    log "host Blender already present: ${existing}"
    return 0
  fi
  if [[ ${LAB_MOCK_BLENDER_INSTALL:-} == "1" ]]; then
    mock_blender_install
    return 0
  fi
  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    err "Cannot install blender (LAB_NO_SUDO=1)"
    print_blender_host_hint
    return 1
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    err "apt-get not found. Install Ubuntu aarch64 blender on the host, or use Path D."
    print_blender_host_hint
    return 1
  fi
  log "Installing host blender (apt universe; never in docker/Dockerfile)..."
  if ! sudo apt-get update -qq ||
    ! run_with_heartbeat "apt-get install blender" -- \
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y blender; then
    err "apt-get install blender failed"
    print_blender_host_hint
    return 1
  fi
  export PATH="/usr/bin:/usr/local/bin:${PATH}"
  hash -r 2>/dev/null || true
  if existing="$(blender_host_bin)"; then
    log "host Blender installed: ${existing}"
    return 0
  fi
  err "blender still missing after apt-get"
  print_blender_host_hint
  return 1
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
