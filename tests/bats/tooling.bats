#!/usr/bin/env bats
#
# Hermetic tests for Bazel-first tooling (validate, CI graph, Makefile shim).

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "validate.sh --help prints usage" {
  run bash "${REPO_ROOT}/scripts/validate.sh" --help
  [ "$status" -eq 0 ]
  [[ ${output} == *"Usage:"* ]]
  [[ ${output} == *"--all"* ]]
  [[ ${output} == *"--ci"* ]]
  [[ ${output} == *"--check-only"* ]]
}

@test "validate.sh names path filter helpers" {
  local script="${REPO_ROOT}/scripts/validate.sh"
  [ -f "${script}" ]
  for fn in usage need_bazel path_matches_bazel_core path_matches_docs path_matches_ci_graph path_matches_ci_workflow classify_path detect_changed_slices resolve_slices run_core_slice run_docs_slice check_generated_artifacts; do
    grep -qE "^${fn}\\(\\)" "${script}"
  done
}

@test "MODULE.bazel is Bzlmod with rules_shell and hermetic bats-core" {
  local mod="${REPO_ROOT}/MODULE.bazel"
  [ -f "${mod}" ]
  grep -q 'module(' "${mod}"
  grep -q 'rules_shell' "${mod}"
  grep -q 'bats-core-1.11.0' "${mod}"
  grep -q 'http_archive' "${mod}"
  run grep -E 'shadcn|rules_python|rules_oci|rules_js' "${mod}"
  [ "$status" -ne 0 ]
}

@test "Bazel version pin and bzlmod rc" {
  grep -qx '8.4.1' "${REPO_ROOT}/.bazelversion"
  grep -q -- '--enable_bzlmod' "${REPO_ROOT}/.bazelrc"
  grep -q -- '--noenable_workspace' "${REPO_ROOT}/.bazelrc"
  grep -q 'bazel-disk' "${REPO_ROOT}/.bazelrc"
  grep -q -- '--config=ci' "${REPO_ROOT}/.bazelrc" || grep -q 'build:ci' "${REPO_ROOT}/.bazelrc"
}

@test "root BUILD.bazel exposes primary aliases" {
  local build="${REPO_ROOT}/BUILD.bazel"
  [ -f "${build}" ]
  for name in 'name = "test-fast"' 'name = "test"' 'name = "lint"' 'name = "validate"' 'name = "manage"' 'name = "fix"'; do
    grep -qF "${name}" "${build}"
  done
}

@test "Makefile help lists Bazel primary and make shims" {
  run make -C "${REPO_ROOT}" help
  [ "$status" -eq 0 ]
  [[ ${output} == *"bazelisk"* ]]
  [[ ${output} == *"make test"* ]]
  [[ ${output} == *"make lint"* ]]
  [[ ${output} == *"make docs"* ]]
}

@test "GitHub CI has path-filtered bazel jobs" {
  local gh="${REPO_ROOT}/.github/workflows/ci.yml"
  [ -f "${gh}" ]
  for job in changes bazel-core docs-and-render validate-gate; do
    grep -qE "^  ${job}:" "${gh}"
  done
  for filter in bazel-core docs ci-graph ci-workflow; do
    grep -qE "^[[:space:]]+${filter}:" "${gh}"
  done
  grep -qF '//:test-fast' "${gh}"
  grep -qF '//:lint' "${gh}"
  grep -qF -- '--test_tag_filters=manual' "${gh}"
  grep -qF './.github/actions/setup-bazel' "${gh}"
  run grep -E 'dashboard-unit|dashboard-hermetic|//dashboard:' "${gh}"
  [ "$status" -ne 0 ]
}

@test "setup-bazel uses modern actions/cache and pinned bazelisk" {
  local setup="${REPO_ROOT}/.github/actions/setup-bazel/action.yml"
  [ -f "${setup}" ]
  grep -qE 'actions/cache@v[56]([^0-9]|$)' "${setup}"
  run grep -E 'actions/cache@v4([^0-9]|$)' "${setup}"
  [ "$status" -ne 0 ]
  grep -q 'bazelisk' "${setup}"
  grep -q 'bazel-disk' "${setup}"
}

@test "deploy-docs.yml publishes only after merge" {
  local deploy="${REPO_ROOT}/.github/workflows/deploy-docs.yml"
  [ -f "${deploy}" ]
  if grep -qE '^[[:space:]]*pull_request:' "${deploy}"; then
    echo "deploy-docs.yml must not trigger on pull_request" >&2
    return 1
  fi
  grep -qE '^[[:space:]]*push:' "${deploy}"
  grep -qF 'workflow_dispatch' "${deploy}"
}

@test "AGENTS.md is Bazel-first and still forbids K3s dashboard NCCL" {
  local agents="${REPO_ROOT}/AGENTS.md"
  grep -qF 'bazelisk run //:validate' "${agents}"
  grep -qE 'K3s|k3s' "${agents}"
  grep -qi 'NCCL' "${agents}"
  grep -qi 'dashboard' "${agents}"
  run grep -E 'Do not pull in K3s, Bazel' "${agents}"
  [ "$status" -ne 0 ]
}

@test "ci_check_only.sh gates bazel-core and docs only" {
  local gate="${REPO_ROOT}/scripts/ci_check_only.sh"
  [ -f "${gate}" ]
  grep -qE '^check_job\(\)' "${gate}"
  grep -q 'bazel-core' "${gate}"
  grep -q 'docs-and-render' "${gate}"
  run grep -E 'dashboard-unit|dashboard-hermetic' "${gate}"
  [ "$status" -ne 0 ]
}

@test "tests/bats.bzl declares bats_file_tests helper" {
  [ -f "${REPO_ROOT}/tests/bats.bzl" ]
  grep -q 'bats_file_tests' "${REPO_ROOT}/tests/bats.bzl"
  grep -q 'bats_runner.sh' "${REPO_ROOT}/tests/BUILD.bazel"
}

@test "install-lint-tools names run_root detect_arch install_release_bins" {
  local installer="${REPO_ROOT}/scripts/ci/install-lint-tools.sh"
  [ -f "${installer}" ]
  grep -qE '^run_root\(\)' "${installer}"
  grep -qE '^detect_arch\(\)' "${installer}"
  grep -qE '^install_release_bins\(\)' "${installer}"
  grep -q 'tool-versions.env' "${installer}"
  grep -q 'amd64' "${installer}"
  grep -q 'arm64' "${installer}"
  run grep -E 'kubeconform|ansible-lint' "${installer}"
  [ "$status" -ne 0 ]
}
