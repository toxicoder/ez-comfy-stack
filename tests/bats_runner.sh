#!/usr/bin/env bash
#
# ## bats_runner
#
# Hermetic BATS runner for use inside Bazel sh_test.
#
# Purpose:
#   Locate the hermetic bats binary and the test sources via runfiles,
#   compute REPO_ROOT so existing tests/bats/*.bats keep relative paths,
#   then exec bats.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#

set -euo pipefail

if [[ -n ${TEST_SRCDIR:-} ]]; then
  RUNFILES="${TEST_SRCDIR}"
else
  RUNFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

#######################################
# Locate a runfiles path by name across Bazel candidate roots.
# Globals:
#   RUNFILES
# Arguments:
#   $1 - relative path to find
# Outputs:
#   Absolute path on stdout
# Returns:
#   0 on success; exits 1 otherwise
#######################################
find_file() {
  local name="$1"
  local candidates=(
    "${RUNFILES}/_main/${name}"
    "${RUNFILES}/${name}"
    "${RUNFILES}/external/${name}"
    "${RUNFILES}/bats_core/${name}"
    "${RUNFILES}/_main/external/bats_core/${name}"
    "${RUNFILES}/+_repo_rules+bats_core/${name}"
    "${RUNFILES}/+_repo_rules+bats_core/bin/bats"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -e ${c} ]]; then
      echo "${c}"
      return 0
    fi
  done
  echo "ERROR: Could not locate ${name} in runfiles" >&2
  echo "RUNFILES=${RUNFILES}" >&2
  # shellcheck disable=SC2012
  ls -l "${RUNFILES}" 2>/dev/null | head -30 >&2 || true
  find "${RUNFILES}" -path '*bats*' -type f 2>/dev/null | head -10 >&2 || true
  exit 1
}

#######################################
# Derive repository root from a known marker file path.
# Globals:
#   None
# Arguments:
#   $1 - absolute marker file path
# Outputs:
#   Absolute repo root
# Returns:
#   0
#######################################
repo_root_from_marker() {
  local marker="$1"
  local dir
  dir="$(dirname "${marker}")"
  case "${marker}" in
    */scripts/manage.sh)
      (cd "${dir}/.." && pwd)
      ;;
    */README.md)
      (cd "${dir}" && pwd)
      ;;
    *)
      (cd "${dir}/.." && pwd)
      ;;
  esac
}

BATS_BIN="$(find_file +_repo_rules+bats_core/bin/bats 2>/dev/null || find_file bats_core/bin/bats)"

REPO_ROOT_MARKER="$(
  find_file _main/scripts/manage.sh 2>/dev/null ||
    find_file _main/README.md 2>/dev/null ||
    find_file scripts/manage.sh 2>/dev/null || true
)"

if [[ -n ${REPO_ROOT_MARKER} && -f ${REPO_ROOT_MARKER} ]]; then
  REPO_ROOT="$(repo_root_from_marker "${REPO_ROOT_MARKER}")"
else
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [[ -f "${REPO_ROOT}/scripts/manage.sh" ]]; then
  _manage_real="$(readlink -f "${REPO_ROOT}/scripts/manage.sh" 2>/dev/null || realpath "${REPO_ROOT}/scripts/manage.sh" 2>/dev/null || echo "${REPO_ROOT}/scripts/manage.sh")"
  REPO_ROOT="$(dirname "$(dirname "${_manage_real}")")"
else
  REPO_ROOT="$(cd "${REPO_ROOT}" && pwd -P)"
fi

export REPO_ROOT
echo "[bats_runner] REPO_ROOT=${REPO_ROOT}" >&2
echo "[bats_runner] BATS_BIN=${BATS_BIN}" >&2

BATS_HELPER="$(
  find_file _main/tests/bats/test_helper.bash 2>/dev/null ||
    find_file tests/bats/test_helper.bash 2>/dev/null || true
)"
if [[ -z ${BATS_HELPER} || ! -f ${BATS_HELPER} ]]; then
  echo "ERROR: Could not locate tests/bats/test_helper.bash in runfiles" >&2
  exit 1
fi
BATS_TEST_DIR="$(dirname "${BATS_HELPER}")"

BATS_TEST_FILES=()
if [[ $# -gt 0 ]]; then
  for name in "$@"; do
    case "${name}" in
      *.bats) BATS_TEST_FILES+=("${BATS_TEST_DIR}/${name}") ;;
      *) BATS_TEST_FILES+=("${BATS_TEST_DIR}/${name}.bats") ;;
    esac
  done
else
  BATS_TEST_FILES=("${BATS_TEST_DIR}"/*.bats)
fi

if [[ ! -e ${BATS_TEST_FILES[0]} ]]; then
  echo "ERROR: No .bats files found under ${BATS_TEST_DIR} (args: $*)" >&2
  exit 1
fi

echo "[bats_runner] BATS_TEST_DIR=${BATS_TEST_DIR}" >&2
echo "[bats_runner] Running ${#BATS_TEST_FILES[@]} test file(s)" >&2

exec "${BATS_BIN}" "${BATS_TEST_FILES[@]}"
