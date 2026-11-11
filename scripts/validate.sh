#!/usr/bin/env bash
#
# ## validate - unified build / test / lint orchestrator
#
# Single entry point for local and CI validation. Mirrors path filters from
# `.github/workflows/ci.yml` so developers run the same slices CI would run.
#
# **Behavior**: the core slice (build --nobuild, test-fast, lint) always runs;
# the docs slice is gated by changed paths, `--all`, or CI env vars.
#
# **Safety**: delegates to existing Bazel targets. Does not bypass manage.sh
# confirmations or weaken Compose restart / headroom / download-limit.
#
# Usage:
#   bazelisk run //:validate
#   bazelisk run //:validate -- --all
#   bazelisk run //:validate -- --ci --check-only
#
# @command validate
# @description Run build, test, lint, and conditional docs checks based on changed paths.
# Usage: bazelisk run //:validate [-- --all | --ci [--check-only]]
# Safety: Read-only orchestration; calls existing hermetic test targets only.

set -euo pipefail

if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  ROOT="${BUILD_WORKSPACE_DIRECTORY}"
  # shellcheck source=lib/paths.sh disable=SC1091
  source "${ROOT}/scripts/lib/paths.sh"
else
  # shellcheck source=lib/paths.sh disable=SC1091
  source "$(cd "$(dirname "${0}")" && pwd)/lib/paths.sh"
  ROOT="$(cd "$(lab_script_dir 0 scripts)/.." && pwd)"
fi
cd "${ROOT}"

# The slice traps below hand a failing bazelisk run to the same bug-report
# template the operator CLI prints, so a gate failure names the command and
# leaves a filed-ready markdown behind.
# shellcheck source=lib/bug_report.sh disable=SC1091
source "${ROOT}/scripts/lib/bug_report.sh"

BAZEL="${BAZEL:-$(command -v bazelisk 2>/dev/null || command -v bazel 2>/dev/null || true)}"
# The bazelisk line the failing slice last ran, read by the EXIT trap.
LAST_BAZEL_CMD=""

RUN_ALL=0
RUN_CI=0
CHECK_ONLY=0

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
Usage: validate.sh [--all] [--ci] [--check-only]

  (default)   Git-aware: run slices matching changed paths vs merge-base.
  --all       Run every slice regardless of changes.
  --ci        Use RUN_BAZEL_CORE / RUN_DOCS env (CI paths-filter).
  --check-only  With --ci: verify parallel job results only (no heavy re-run).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      RUN_ALL=1
      shift
      ;;
    --ci)
      RUN_CI=1
      shift
      ;;
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "validate: unknown argument: $1" >&2
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
#   Error on stderr when missing
# Returns:
#   0 or exits 1
#######################################
need_bazel() {
  if [[ -z ${BAZEL} ]]; then
    echo "validate: bazelisk or bazel not found in PATH" >&2
    EZ_BUG_HINT_SHOWN=1
    exit 1
  fi
}

#######################################
# True when path belongs to the bazel-core CI slice.
# Globals:
#   None
# Arguments:
#   $1 - repo-relative path
# Returns:
#   0 when matched
#######################################
path_matches_bazel_core() {
  local path="$1"
  [[ ${path} == scripts/* ]] && return 0
  [[ ${path} == tests/* ]] && return 0
  [[ ${path} == lints/* ]] && return 0
  [[ ${path} == docker/* ]] && return 0
  [[ ${path} == custom_nodes/* ]] && return 0
  [[ ${path} == config/* ]] && return 0
  [[ ${path} == tools/* ]] && return 0
  [[ ${path} == studio-ui/* ]] && return 0
  [[ ${path} == workflows/* ]] && return 0
  [[ ${path} == schemas/* ]] && return 0
  [[ ${path} == docs/*.py ]] && return 0
  [[ ${path} == mypy.ini ]] && return 0
  [[ ${path} == pyrightconfig.json ]] && return 0
  [[ ${path} == .devcontainer/* ]] && return 0
  [[ ${path} == .vscode/* ]] && return 0
  return 1
}

#######################################
# True when path belongs to the docs CI slice.
# Globals:
#   None
# Arguments:
#   $1 - repo-relative path
# Returns:
#   0 when matched
#######################################
path_matches_docs() {
  local path="$1"
  [[ ${path} == docs/* ]] && return 0
  [[ ${path} == docs-site/* ]] && return 0
  [[ ${path} == includes/* ]] && return 0
  [[ ${path} == scripts/manage.sh ]] && return 0
  [[ ${path} == scripts/lib/* ]] && return 0
  [[ ${path} == scripts/utilities/* ]] && return 0
  return 1
}

#######################################
# True when path is the Bazel graph / orchestrator.
# Globals:
#   None
# Arguments:
#   $1 - repo-relative path
# Returns:
#   0 when matched
#######################################
path_matches_ci_graph() {
  local path="$1"
  [[ ${path} == BUILD.bazel ]] && return 0
  [[ ${path} == MODULE.bazel ]] && return 0
  [[ ${path} == MODULE.bazel.lock ]] && return 0
  [[ ${path} == .bazelrc ]] && return 0
  [[ ${path} == .bazelversion ]] && return 0
  [[ ${path} == .bazelignore ]] && return 0
  [[ ${path} == fix.sh ]] && return 0
  [[ ${path} == scripts/validate.sh ]] && return 0
  return 1
}

#######################################
# True when path is GitHub workflow/action YAML.
# Globals:
#   None
# Arguments:
#   $1 - repo-relative path
# Returns:
#   0 when matched
#######################################
path_matches_ci_workflow() {
  local path="$1"
  [[ ${path} == .github/* ]] && return 0
  return 1
}

#######################################
# Classify a path into zero or more slice labels.
# Globals:
#   None
# Arguments:
#   $1 - repo-relative path
# Outputs:
#   Slice names on stdout (one per line)
# Returns:
#   0
#######################################
classify_path() {
  local path="$1"
  path_matches_bazel_core "${path}" && echo bazel-core
  path_matches_docs "${path}" && echo docs
  path_matches_ci_graph "${path}" && echo ci-graph
  path_matches_ci_workflow "${path}" && echo ci-workflow
}

#######################################
# Set RUN_BAZEL_CORE / RUN_DOCS from git diffs.
# Globals:
#   RUN_BAZEL_CORE, RUN_DOCS
# Arguments:
#   None
# Outputs:
#   Warning when no git history
# Returns:
#   0 when any slice matched, 1 otherwise
#######################################
detect_changed_slices() {
  local slices=()
  local base=""
  local path class

  if git rev-parse --verify development >/dev/null 2>&1; then
    base="$(git merge-base HEAD development 2>/dev/null || echo HEAD)"
  elif git rev-parse --verify main >/dev/null 2>&1; then
    base="$(git merge-base HEAD main 2>/dev/null || echo HEAD)"
  elif git rev-parse --verify HEAD >/dev/null 2>&1; then
    base="HEAD"
  else
    echo "validate: no git history; use --all for first commit" >&2
    return 1
  fi

  while IFS= read -r path; do
    [[ -z ${path} ]] && continue
    class="$(classify_path "${path}" || true)"
    [[ -z ${class} ]] && continue
    slices+=("${class}")
  done < <(
    git diff --name-only "${base}" HEAD 2>/dev/null
    git diff --name-only --cached
    git diff --name-only
  )

  if [[ ${#slices[@]} -eq 0 ]]; then
    return 1
  fi

  local want_bazel=0 want_docs=0
  for class in "${slices[@]}"; do
    case "${class}" in
      bazel-core) want_bazel=1 ;;
      docs) want_docs=1 ;;
      ci-graph)
        want_bazel=1
        want_docs=1
        ;;
      ci-workflow) want_bazel=1 ;;
    esac
  done

  RUN_BAZEL_CORE=${want_bazel}
  RUN_DOCS=${want_docs}
}

#######################################
# Resolve which slices to run.
# Globals:
#   RUN_ALL, RUN_CI, RUN_BAZEL_CORE, RUN_DOCS
# Arguments:
#   None
# Outputs:
#   Status when falling back to core
# Returns:
#   0
#######################################
resolve_slices() {
  if [[ ${RUN_ALL} -eq 1 ]]; then
    RUN_BAZEL_CORE=1
    RUN_DOCS=1
    return 0
  fi

  if [[ ${RUN_CI} -eq 1 ]]; then
    RUN_BAZEL_CORE="${RUN_BAZEL_CORE:-0}"
    RUN_DOCS="${RUN_DOCS:-0}"
    if [[ ${RUN_CI_GRAPH:-0} == "1" || ${RUN_CI_GRAPH:-} == "true" ]]; then
      RUN_BAZEL_CORE=1
      RUN_DOCS=1
    fi
    [[ ${RUN_BAZEL_CORE} == "true" ]] && RUN_BAZEL_CORE=1
    [[ ${RUN_DOCS} == "true" ]] && RUN_DOCS=1
    return 0
  fi

  RUN_BAZEL_CORE=0
  RUN_DOCS=0
  if detect_changed_slices; then
    :
  else
    echo "validate: no matching path changes detected; running core only"
    RUN_BAZEL_CORE=1
  fi
}

#######################################
# Fail if generated shell reference is dirty.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Error when dirty
# Returns:
#   0 or exits 1
#######################################
check_generated_artifacts() {
  local dirty=0
  if ! git diff --quiet -- docs/generated/shell/reference.md 2>/dev/null; then
    echo "validate: docs/generated/shell/reference.md is dirty - run: bazelisk run //docs:generate, then commit docs/generated/" >&2
    dirty=1
  fi
  if [[ ${dirty} -ne 0 ]]; then
    exit 1
  fi
  echo "validate: generated docs artifacts are committed"
}

#######################################
# Run build --nobuild, test-fast, lint, key builds.
# Globals:
#   BAZEL, RUN_ALL
# Arguments:
#   None
# Outputs:
#   Bazel logs
# Returns:
#   Bazel exit status
#######################################
run_core_slice() {
  echo "==> validate: core (build --nobuild, test-fast, lint, key builds)"
  need_bazel
  run_bazel build //... --nobuild
  run_bazel test //:test-fast
  run_bazel test //:lint --test_tag_filters=manual
  run_bazel build //:manage //:all
}

#######################################
# Run docs generation and the Fumadocs export.
# Globals:
#   BAZEL
# Arguments:
#   None
# Outputs:
#   Bazel logs
# Returns:
#   Bazel exit status
#######################################
run_docs_slice() {
  need_bazel
  echo "==> validate: docs (Fumadocs gates + generate + export + render-check)"
  run_bazel test \
    //docs:test_docs_site_render \
    //docs-site:suite \
    --test_tag_filters=-visual
  run_bazel run //docs:docs
  run_bazel run //docs:render-check
}

#######################################
# Run one Bazel invocation and remember it for the failure handoff.
# Globals:
#   BAZEL, LAST_BAZEL_CMD (written)
# Arguments:
#   $@ - the bazelisk arguments
# Outputs:
#   Bazel output
# Returns:
#   The Bazel exit status
#######################################
run_bazel() {
  LAST_BAZEL_CMD="${BAZEL} $*"
  "${BAZEL}" "$@"
}

#######################################
# EXIT trap: hand a failing slice to the bug-report template once.
# Globals:
#   LAST_BAZEL_CMD, EZ_BUG_HINT_SHOWN
# Arguments:
#   $1 - the status the script is exiting with
# Outputs:
#   The hint on stderr, when a human is watching
# Returns:
#   0 always; the script's exit status is left alone
#######################################
_ez_validate_exit_trap() {
  local rc="${1:-0}"
  if [[ ${rc} == "0" || -n ${EZ_BUG_HINT_SHOWN:-} ]]; then
    return 0
  fi
  if ! declare -f bug_report_hint >/dev/null 2>&1; then
    return 0
  fi
  EZ_BUG_HINT_SHOWN=1
  bug_report_hint "bazel" "${LAST_BAZEL_CMD:-}" "${rc}"
  return 0
}

#######################################
# CLI dispatcher.
# Globals:
#   RUN_ALL, RUN_CI, CHECK_ONLY, RUN_BAZEL_CORE, RUN_DOCS
# Arguments:
#   None
# Outputs:
#   Slice status
# Returns:
#   First failing slice
#######################################
main() {
  if [[ ${RUN_CI} -eq 1 && ${CHECK_ONLY} -eq 1 ]]; then
    exec bash "${ROOT}/scripts/ci_check_only.sh"
  fi

  resolve_slices
  if [[ ${RUN_BAZEL_CORE} -eq 1 || ${RUN_BAZEL_CORE} == "true" ]]; then
    run_core_slice
  else
    echo "validate: skip core (unchanged bazel-core paths)"
  fi
  if [[ ${RUN_DOCS} -eq 1 || ${RUN_DOCS} == "true" || ${RUN_ALL} -eq 1 ]]; then
    run_docs_slice
    check_generated_artifacts
  fi
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  trap '_ez_validate_exit_trap $?' EXIT
  main "$@"
fi
