#!/usr/bin/env bash
#
# ## ci_check_only — lightweight CI validate-gate
#
# Verifies path-filtered GitHub jobs reported success (or were correctly
# skipped). No Bazel cold start — intended for the validate-gate job only.
#
# Env (set by CI):
#   BAZEL_CORE_RESULT, DOCS_RESULT
#   RUN_BAZEL_CORE, RUN_DOCS  (true/false or 1/0)
#
# Safety: Read-only orchestration. Does not start Compose.

set -euo pipefail

fail=0

#######################################
# Fail when a required CI job did not succeed.
# Globals:
#   fail
# Arguments:
#   $1 - job name
#   $2 - should run (1/true or 0/false)
#   $3 - GitHub job result
# Outputs:
#   skip/ok/FAIL lines
# Returns:
#   0 (accumulates failures in fail)
#######################################
check_job() {
  local name="$1"
  local should_run="$2"
  local result="$3"
  if [[ ${should_run} != "1" && ${should_run} != "true" ]]; then
    echo "skip ${name} (unchanged paths)"
    return 0
  fi
  if [[ ${result} != "success" ]]; then
    echo "FAIL ${name} result=${result}"
    fail=1
  else
    echo "ok ${name}"
  fi
}

check_job bazel-core "${RUN_BAZEL_CORE:-0}" "${BAZEL_CORE_RESULT:-skipped}"
check_job docs-and-render "${RUN_DOCS:-0}" "${DOCS_RESULT:-skipped}"

exit "${fail}"
