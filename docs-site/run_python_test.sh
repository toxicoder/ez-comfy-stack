#!/usr/bin/env bash
#
# Bazel entry point for the python unittest suites that live beside the docs-site sources
# (the nav transcriber, the MkDocs->MDX codemod, the MDX hazard audit, and the golden
# pipeline guards).
#
# Usage (from a bazel run):
#   run_python_test.sh <test_module.py> [--cov=<module path>] [runner args...]
#
# Without --cov the module runs under unittest, exactly as it always has. With
# --cov=<module path> -- a python file relative to this directory, e.g.
# --cov=scripts/gen_nav.py -- the same suite runs under pytest + pytest-cov measuring that
# one production module at --cov-report=term-missing --cov-fail-under=100, so a statement no
# test reaches fails the Bazel target instead of riding along unmeasured. The remaining args
# are forwarded to whichever runner takes over.
#
# The measured path needs the host's pytest and pytest-cov (pip install -r
# tests/requirements.txt). A missing one is a hard failure on purpose: falling back to the
# unmeasured unittest run is the hole this gate exists to close.
set -euo pipefail

if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} && -d "${BUILD_WORKSPACE_DIRECTORY}/docs-site" ]]; then
  cd "${BUILD_WORKSPACE_DIRECTORY}/docs-site"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$SCRIPT_DIR"
fi

if [[ $# -eq 0 ]]; then
  echo "usage: $(basename "$0") <test_module.py> [--cov=<module path>] [runner args...]" >&2
  exit 2
fi

TEST_MODULE="$1"
shift

# --cov is an option of this wrapper, not of the test runner, so it is pulled out here.
COV_MODULE=""
RUNNER_ARGS=()
for arg in "$@"; do
  if [[ ${arg} == --cov=* ]]; then
    if [[ -n ${COV_MODULE} ]]; then
      echo "only one --cov= is supported, got ${COV_MODULE} and ${arg#--cov=}" >&2
      exit 2
    fi
    COV_MODULE="${arg#--cov=}"
    if [[ -z ${COV_MODULE} ]]; then
      echo "--cov= needs a python file relative to $(pwd)" >&2
      exit 2
    fi
    if [[ ! -f ${COV_MODULE} ]]; then
      echo "coverage target ${COV_MODULE} not found under $(pwd)" >&2
      exit 1
    fi
  else
    RUNNER_ARGS+=("${arg}")
  fi
done

if [[ ! -f ${TEST_MODULE} ]]; then
  echo "test module ${TEST_MODULE} not found in $(pwd)" >&2
  exit 1
fi

if [[ -n ${COV_MODULE} ]]; then
  if ! python3 -c 'import pytest, pytest_cov' >/dev/null 2>&1; then
    echo "coverage gate needs pytest and pytest-cov: pip install -r tests/requirements.txt" >&2
    exit 1
  fi
  # coverage resolves a --cov value that is not a directory as an importable module name, and
  # the suites put scripts/ on sys.path, so the file path the targets name becomes the module
  # it imports. Measuring one module is the point: --cov over a directory would score the
  # unimported siblings at 0% and report the wrong total.
  COV_TARGET="$(basename "${COV_MODULE}" .py)"
  # A bazel test sandbox is read-only outside TEST_TMPDIR, so neither the coverage data file
  # nor pytest's cache may land in the runfiles tree.
  export COVERAGE_FILE="${TEST_TMPDIR:-.}/.coverage"
  # The suites are unittest.TestCase-based, which pytest collects without changes.
  exec python3 -m pytest "${TEST_MODULE}" -q -p no:cacheprovider \
    --cov="${COV_TARGET}" --cov-report=term-missing --cov-fail-under=100 \
    "${RUNNER_ARGS[@]}"
fi

# discover keeps the package dir importable so the tests can `import gen_nav` etc.
# out of scripts/.
exec python3 -m unittest discover -s . -p "${TEST_MODULE}" -t . -v "${RUNNER_ARGS[@]}"
