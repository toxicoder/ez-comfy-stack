#!/usr/bin/env bash
#
# ## repo_root
#
# Resolve the checkout root from bazel run, bazel test runfiles, or script path.
#
# Purpose:
#   Shared helper sourced by hermetic test runners so Bazel run/test and
#   local bash invoke the same source tree (not bazel-bin).
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#

#######################################
# Print the repository root (source tree, not bazel-bin).
# Globals:
#   BUILD_WORKSPACE_DIRECTORY, TEST_SRCDIR
# Arguments:
#   None
# Outputs:
#   Absolute repo root
# Returns:
#   0 or exits 1
#######################################
tests_repo_root() {
  local marker real
  if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} && -f ${BUILD_WORKSPACE_DIRECTORY}/MODULE.bazel ]]; then
    echo "${BUILD_WORKSPACE_DIRECTORY}"
    return 0
  fi
  if [[ -n ${TEST_SRCDIR:-} && -f ${TEST_SRCDIR}/_main/scripts/manage.sh ]]; then
    marker="${TEST_SRCDIR}/_main/scripts/manage.sh"
    real="$(readlink -f "${marker}" 2>/dev/null || realpath "${marker}" 2>/dev/null || echo "${marker}")"
    echo "$(cd "$(dirname "${real}")/.." && pwd)"
    return 0
  fi
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
  if [[ -f ${here}/../MODULE.bazel ]]; then
    echo "$(cd "${here}/.." && pwd)"
    return 0
  fi
  echo "tests_repo_root: cannot locate MODULE.bazel" >&2
  return 1
}
