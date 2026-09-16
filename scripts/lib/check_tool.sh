#!/usr/bin/env bash
#
# ## check_tool helper
#
# Resilient tool checker used by lints/run_*.sh and CI installers.
# By default, a missing tool prints a message and exits 0 so local runs can
# continue when optional linters are not installed.
#
# When CI=true or REQUIRE_LINT_TOOLS=1, a missing tool is fatal (exit 1).
#
# @function check_tool
# Usage:
#   source "$(dirname "$0")/../lib/check_tool.sh"
#   check_tool shellcheck "apt install shellcheck"
#
# Safety: Read-only PATH probe. No GPU, Docker, or network.

#######################################
# Require a CLI on PATH, or skip/fail based on CI strictness.
# Globals:
#   CI, REQUIRE_LINT_TOOLS
# Arguments:
#   $1 - tool name (command)
#   $2 - install hint
# Outputs:
#   Skip or error message on stderr/stdout
# Returns:
#   0 when present, or when missing and not strict; exits 1 when strict
#######################################
check_tool() {
  local tool="$1"
  local install_hint="${2:-pip install or apt install ${tool}}"
  if ! command -v "${tool}" >/dev/null 2>&1; then
    if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
      echo "${tool} missing - required in CI/strict mode (${install_hint})" >&2
      exit 1
    fi
    echo "${tool} missing - skipping (resilient; ${install_hint})"
    exit 0
  fi
}

#######################################
# Echo the git checkout root, following Bazel runfiles symlinks.
# Globals:
#   BUILD_WORKSPACE_DIRECTORY
# Arguments:
#   None
# Outputs:
#   Absolute checkout path
# Returns:
#   0
#######################################
bazel_checkout_root() {
  local real
  if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} && -d ${BUILD_WORKSPACE_DIRECTORY} ]]; then
    echo "${BUILD_WORKSPACE_DIRECTORY}"
    return 0
  fi
  real="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
  cd "$(dirname "${real}")/../.." && pwd
}
