#!/usr/bin/env bash
#
# ## everything - one target that runs every gate
#
# The ingress for "is this checkout healthy?". It runs the host bootstrap
# probe, the load/analysis graph, every test gate in //:test-all, the
# container visual lane, and the docs build, in that order, and stops at the
# first failure with the name of the Bazel target that failed.
#
# **Behavior**: no path filtering. //:validate is the fast, git-aware slice for
# a working day; this is the full sweep you run before shipping a Bazel-side
# change or promoting a graph. It shells out to `bazelisk` only and never
# touches sudo, the GPU, or $HOME. The visual lane is the one gate that needs
# a container runtime, so it is probed first and reported as a skip when this
# host cannot support it; `bazelisk test //:test-all` remains the unfiltered
# form that runs it regardless.
#
# **Safety**: read-only orchestration. It delegates to existing Bazel targets
# and bypasses no manage.sh confirmation, no Compose restart policy, no
# headroom preflight, and no download-limit clear-on-exit.
#
# Requirements:
#   bazelisk (or bazel) on PATH. When it is absent, //:setup-host is the
#   repair, and that is the one thing this script cannot run for itself.
#
# Usage:
#   bazelisk run //:everything
#   bazelisk run //:everything -- --skip-bootstrap
#
# Exit codes:
#   0 every gate passed.
#   1 a gate failed (its target name is printed).
#   2 bad argument, or bazelisk is missing.
#
# @command everything
# @description Run every Bazel gate: bootstrap probe, graph load, //:test-all, the visual lane, and the docs build.
# Safety: Read-only orchestration; invokes existing Bazel targets only.

set -euo pipefail

BAZEL="${BAZEL:-$(command -v bazelisk 2>/dev/null || command -v bazel 2>/dev/null || true)}"
SKIP_BOOTSTRAP=0

# The gate() hook below is the filing handoff for a failing bazelisk run. The
# //:everything target ships it in runfiles, so sourcing beside the script
# works the same way under `bazelisk run` and from a plain checkout.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bug_report.sh disable=SC1091
source "${SCRIPT_DIR}/lib/bug_report.sh"
# Committed screenshot baselines for the docs-site visual lane. The lane needs
# them plus a container runtime, so their absence is an environment gap the
# sweep reports as a skip rather than as a failing gate.
GOLDENS_DIR="docs-site/tests/visual/goldens"

#######################################
# Print usage and exit 0.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage on stdout
# Returns:
#   0
#######################################
usage() {
  cat <<'EOF'
Usage: everything.sh [--skip-bootstrap]

  (default)        Probe the host toolchain, load the graph, run //:test-all,
                   then build and render-check the docs.
  --skip-bootstrap Skip the //:setup-host --check probe (CI, or a host you
                   already know is provisioned).
  -h, --help       Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-bootstrap)
      SKIP_BOOTSTRAP=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "everything: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

#######################################
# Require bazelisk/bazel on PATH.
#
# A missing toolchain is a named environment gap with a stated repair, so it
# claims the one-shot bug-handoff flag instead of offering a defect report.
# Globals:
#   BAZEL, EZ_BUG_HINT_SHOWN (set to 1 to suppress the handoff)
# Arguments:
#   None
# Outputs:
#   The repair command on stderr when missing
# Returns:
#   0 or exits 2
#######################################
need_bazel() {
  if [[ -z ${BAZEL} ]]; then
    echo "everything: bazelisk or bazel not found in PATH" >&2
    echo "everything: bootstrap the host with 'bash scripts/setup-host.sh', then re-run" >&2
    echo "everything:   bazelisk run //:setup-host -- --check" >&2
    EZ_BUG_HINT_SHOWN=1
    exit 2
  fi
}

#######################################
# Run one gate and report it by its Bazel target name.
# Globals:
#   BAZEL
# Arguments:
#   $1 - label to print, e.g. //:test-all
#   $@ - the bazelisk invocation after the binary
# Outputs:
#   The gate header and the Bazel output
# Returns:
#   The gate's exit status, 1 when it failed
#######################################
gate() {
  local label="$1"
  shift
  echo "==> //:everything: ${label}"
  if ! "${BAZEL}" "$@"; then
    echo "everything: gate ${label} failed" >&2
    if [[ -z ${EZ_BUG_HINT_SHOWN:-} ]] && declare -f bug_report_hint >/dev/null 2>&1; then
      EZ_BUG_HINT_SHOWN=1
      bug_report_hint "bazel" "${BAZEL} $*" 1
    fi
    return 1
  fi
}

#######################################
# Probe the host toolchain the lint and docs gates shell out to.
# Globals:
#   BAZEL, SKIP_BOOTSTRAP
# Arguments:
#   None
# Outputs:
#   The probe output, or the repair command when a tool is missing
# Returns:
#   0 when provisioned or skipped, 1 otherwise
#######################################
run_bootstrap_gate() {
  if [[ ${SKIP_BOOTSTRAP} -eq 1 ]]; then
    echo "==> //:everything: skipping the //:setup-host probe"
    return 0
  fi
  gate "//:setup-host -- --check" run //:setup-host -- --check || {
    echo "everything: install the pinned toolchain with 'bazelisk run //:setup-host'" >&2
    echo "everything: on a bare host, where Bazel does not exist yet: 'bash scripts/setup-host.sh'" >&2
    return 1
  }
}

#######################################
# Load and analyse every target without building actions.
# Globals:
#   BAZEL
# Arguments:
#   None
# Outputs:
#   Bazel loading and analysis output
# Returns:
#   0 or 1
#######################################
run_graph_gate() {
  gate "//... (load and analysis)" build //... --nobuild
}

#######################################
# Run every test gate that a plain host can run.
# Globals:
#   BAZEL
# Arguments:
#   None
# Outputs:
#   Bazel test output
# Returns:
#   0 or 1
#######################################
run_test_gate() {
  # The visual lane is filtered out here and run by run_visual_gate below,
  # which can tell a missing container runtime apart from a broken checkout.
  # //:test-all still names both targets, so `bazelisk test //:test-all`
  # remains the unfiltered form.
  gate "//:test-all" test //:test-all --test_tag_filters=-visual
}

#######################################
# Report whether the container visual lane is runnable here.
# Globals:
#   GOLDENS_DIR
# Arguments:
#   None
# Outputs:
#   One reason line when the lane cannot run
# Returns:
#   0 when runnable, 1 with the reason printed
#######################################
visual_lane_ready() {
  if ! docker info >/dev/null 2>&1; then
    echo "the Docker daemon is not reachable"
    return 1
  fi
  if [[ ! -d ${GOLDENS_DIR} ]] ||
    [[ -z $(find "${GOLDENS_DIR}" -type f -name '*.png' -print -quit) ]]; then
    echo "no committed baselines under ${GOLDENS_DIR}"
    return 1
  fi
  return 0
}

#######################################
# Compare the docs-site screenshot baselines in the pinned container.
# Globals:
#   BAZEL, GOLDENS_DIR, SKIPPED
# Arguments:
#   None
# Outputs:
#   The container run, or the skip reason plus the repair command
# Returns:
#   0 when the lane ran clean or was skipped, 1 when it ran and failed
#######################################
run_visual_gate() {
  local reason=""
  if ! reason=$(visual_lane_ready); then
    echo "==> //:everything: SKIP docs-site visual lane (${reason})"
    echo "everything: refresh baselines with 'bazelisk run //docs-site:visual-linux -- --update'"
    SKIPPED+=("docs-site visual lane")
    return 0
  fi
  gate "//docs-site visual lane" test //docs-site:visual-test //docs-site:visual_tooling_test
}

#######################################
# Build the docs site and fail on broken links.
# Globals:
#   BAZEL
# Arguments:
#   None
# Outputs:
#   The Fumadocs export and render-check output
# Returns:
#   0 or 1
#######################################
run_docs_gate() {
  gate "//docs:docs" run //docs:docs || return 1
  gate "//docs:render-check" run //docs:render-check
}

#######################################
# Move to the real workspace before invoking Bazel again.
# Globals:
#   BUILD_WORKSPACE_DIRECTORY
# Arguments:
#   None
# Outputs:
#   Nothing
# Returns:
#   0
#######################################
enter_workspace() {
  # `bazel run` starts the binary with its working directory inside the output
  # base. Bazel then refuses a nested invocation ("bazel should not be called
  # from a bazel output directory"), so the gates would all report a failure
  # that means nothing. BUILD_WORKSPACE_DIRECTORY is Bazel's own name for the
  # checkout, and it is unset when the script is run directly.
  if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
    cd "${BUILD_WORKSPACE_DIRECTORY}"
  fi
}

#######################################
# Run the gates in dependency order.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   One header per gate plus the final summary
# Returns:
#   0 when all gates passed, 1 when any failed
#######################################
main() {
  need_bazel
  enter_workspace
  local -a failed=()
  local -a SKIPPED=()

  run_bootstrap_gate || failed+=("//:setup-host")
  run_graph_gate || failed+=("//... (load and analysis)")
  run_test_gate || failed+=("//:test-all")
  run_visual_gate || failed+=("//docs-site visual lane")
  run_docs_gate || failed+=("//docs:docs")

  if [[ ${#failed[@]} -gt 0 ]]; then
    echo "everything: ${#failed[@]} gate(s) failed: ${failed[*]}" >&2
    return 1
  fi
  local summary="everything: all gates passed"
  if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    summary+=" (${#SKIPPED[@]} skipped: ${SKIPPED[*]})"
  fi
  echo "${summary}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
