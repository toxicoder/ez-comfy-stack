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

@test "bazel-core path filters include vscode workspace files" {
  grep -qF '.vscode/*' "${REPO_ROOT}/scripts/validate.sh"
  grep -qF '.vscode/**' "${REPO_ROOT}/.github/workflows/ci.yml"
}

@test "bazel-core path filters include the whole devcontainer tree" {
  grep -qF '.devcontainer/*' "${REPO_ROOT}/scripts/validate.sh"
  grep -qF '.devcontainer/**' "${REPO_ROOT}/.github/workflows/ci.yml"
}

@test "bazel-core path filters include schemas" {
  grep -qF 'schemas/*' "${REPO_ROOT}/scripts/validate.sh"
  grep -qF 'schemas/**' "${REPO_ROOT}/.github/workflows/ci.yml"
}

@test "ci-graph path filters include bazelignore" {
  grep -qF '.bazelignore' "${REPO_ROOT}/scripts/validate.sh"
  grep -qF '.bazelignore' "${REPO_ROOT}/.github/workflows/ci.yml"
}

@test "shellcheck and fix skip nested node_modules" {
  grep -qF "*/node_modules/*" "${REPO_ROOT}/lints/run_shellcheck.sh"
  grep -qF "*/node_modules/*" "${REPO_ROOT}/fix.sh"
  grep -qF "*/node_modules/*" "${REPO_ROOT}/lints/buildifier_check.sh"
  run grep -F "./node_modules/*" "${REPO_ROOT}/lints/run_shellcheck.sh"
  [ "$status" -ne 0 ]
}

@test "JS type lane prefers the pinned tsc and falls back to the PATH" {
  local js="${REPO_ROOT}/lints/run_js_types.sh"
  grep -qF 'TSC="docs-site/node_modules/.bin/tsc"' "${js}"
  grep -qF 'command -v tsc' "${js}"
  # A missing compiler stays fatal under CI and strict mode, never a silent pass.
  grep -qF 'tsc missing - required in CI/strict mode' "${js}"
  # Order matters: the checkout's pinned compiler has to be tried first, or a
  # stray global TypeScript would move the counts the ratchet records.
  local pinned_at path_at
  pinned_at="$(grep -n 'docs-site/node_modules/.bin/tsc' "${js}" | head -1 | cut -d: -f1)"
  path_at="$(grep -n 'command -v tsc' "${js}" | head -1 | cut -d: -f1)"
  [ -n "${pinned_at}" ] && [ -n "${path_at}" ]
  [ "${pinned_at}" -lt "${path_at}" ]
}

@test "shfmt allowlist includes docs-site and setup-docs shell" {
  local shfmt="${REPO_ROOT}/lints/run_shfmt.sh"
  grep -qF 'docs/setup-docs.sh' "${shfmt}"
  grep -qF 'docs-site/run_npm.sh' "${shfmt}"
  grep -qF 'docs-site/scripts/visual_linux.sh' "${shfmt}"
  grep -qF 'docs-site/scripts/visual_linux_in_container.sh' "${shfmt}"
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
  grep -qF 'max-old-space-size=5120' "${gh}"
  grep -qF 'max-old-space-size=5120' "${REPO_ROOT}/docs/manage-docs.sh"
  grep -qF 'bazelisk shutdown' "${gh}"
  grep -qF './docs/manage-docs.sh build' "${gh}"
  grep -qF 'next build --webpack' "${REPO_ROOT}/docs-site/package.json"
  grep -qF 'dynamic: true' "${REPO_ROOT}/docs-site/source.config.ts"
  grep -qF 'enablePrerenderSourceMaps: false' "${REPO_ROOT}/docs-site/next.config.ts"
  grep -qF '.source/dynamic' "${REPO_ROOT}/docs-site/lib/source.ts"
  grep -qF '.load(' "${REPO_ROOT}/docs-site/app/[[...slug]]/page.tsx"
  run grep -E 'from ["'"'"']fumadocs-mdx/macro["'"'"']' "${REPO_ROOT}/docs-site/lib/content.ts"
  [ "$status" -ne 0 ]
  run grep -E 'from ["'"'"']fumadocs-mdx/macro["'"'"']' "${REPO_ROOT}/docs-site/source.config.ts"
  [ "$status" -ne 0 ]
  grep -qF 'docs-site/.next/cache' "${gh}"
  run grep -F 'bazelisk run //docs:docs' "${gh}"
  [ "$status" -ne 0 ]
  run grep -F 'max-old-space-size=6144' "${gh}"
  [ "$status" -ne 0 ]
  run grep -F 'max-old-space-size=4096' "${gh}"
  [ "$status" -ne 0 ]
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

@test "deploy-docs.yml builds one Pages alias per run" {
  local deploy="${REPO_ROOT}/.github/workflows/deploy-docs.yml"
  [ -f "${deploy}" ]
  grep -qF 'DOCS_ALIAS' "${deploy}"
  grep -qF 'pages-root-index.html' "${deploy}"
  grep -qF 'max-old-space-size=5120' "${deploy}"
  grep -qF 'npm run "build:${alias}"' "${deploy}"
  run grep -F 'max-old-space-size=6144' "${deploy}"
  [ "$status" -ne 0 ]
  run grep -F 'max-old-space-size=4096' "${deploy}"
  [ "$status" -ne 0 ]
  run grep -F 'docs-site:build-' "${deploy}"
  [ "$status" -ne 0 ]
  grep -qF 'docs-site/.next/cache' "${deploy}"
  grep -qF 'scripts/ci/publish-pages-tree.sh' "${deploy}"
  run grep -E 'bazelisk run //docs-site:build-latest' "${deploy}"
  [ "$status" -ne 0 ]
  run grep -E 'bazelisk run //docs-site:build-development' "${deploy}"
  [ "$status" -ne 0 ]
  run grep -E 'git checkout -B gh-pages' "${deploy}"
  [ "$status" -ne 0 ]
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
  grep -qF 'timeout = "moderate" if src in _MEDIUM else "short"' "${REPO_ROOT}/tests/bats.bzl"
  grep -qF 'bats/lib_unit.bats' "${REPO_ROOT}/tests/bats.bzl"
}

@test "first-party packages including schemas are in the Bazel graph" {
  [ -f "${REPO_ROOT}/schemas/BUILD.bazel" ]
  grep -qF 'name = "schemas"' "${REPO_ROOT}/schemas/BUILD.bazel"
  grep -qF 'name = "first_party_srcs"' "${REPO_ROOT}/BUILD.bazel"
  grep -qF 'name = "python_tests"' "${REPO_ROOT}/tests/BUILD.bazel"
  grep -qF 'name = "fixtures"' "${REPO_ROOT}/tests/BUILD.bazel"
  grep -qF '//schemas' "${REPO_ROOT}/tests/BUILD.bazel"
  grep -qF 'pytest-xdist==' "${REPO_ROOT}/tests/requirements.txt"
  grep -qF -- '-n auto' "${REPO_ROOT}/tests/run_pytest.sh"
  grep -qF -- '--dist worksteal' "${REPO_ROOT}/tests/run_pytest.sh"
  run grep -E 'rules_python|rules_js' "${REPO_ROOT}/MODULE.bazel"
  [ "$status" -ne 0 ]
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

@test "validate.sh --ci forwards each slice line and reads the CI true/false words" {
  local stub="${BATS_TEST_TMPDIR}/fake-bazel"
  printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "${STUB_LOG}"\n' >"${stub}"
  chmod +x "${stub}"

  # The workflow hands RUN_BAZEL_CORE / RUN_DOCS over as the words a GitHub
  # Actions boolean renders to; `false` used to reach an -eq test and die
  # under set -u instead of skipping the slice.
  run env STUB_LOG="${BATS_TEST_TMPDIR}/calls" BAZEL="${stub}" \
    RUN_BAZEL_CORE=true RUN_DOCS=false bash "${REPO_ROOT}/scripts/validate.sh" --ci
  [ "$status" -eq 0 ]
  grep -qF 'build //... --nobuild' "${BATS_TEST_TMPDIR}/calls"
  grep -qF 'test //:test-fast' "${BATS_TEST_TMPDIR}/calls"
  grep -qF 'test //:lint --test_tag_filters=manual' "${BATS_TEST_TMPDIR}/calls"
  grep -qF 'build //:manage //:all' "${BATS_TEST_TMPDIR}/calls"
  ! grep -qF 'run //docs:docs' "${BATS_TEST_TMPDIR}/calls"

  run env STUB_LOG="${BATS_TEST_TMPDIR}/calls-none" BAZEL="${stub}" \
    RUN_BAZEL_CORE=false RUN_DOCS=false bash "${REPO_ROOT}/scripts/validate.sh" --ci
  [ "$status" -eq 0 ]
  [[ ${output} == *"skip core"* ]]
  [ ! -s "${BATS_TEST_TMPDIR}/calls-none" ]
}

@test "validate.sh hands a failing slice to the bug template once" {
  grep -qE '^run_bazel\(\)' "${REPO_ROOT}/scripts/validate.sh"
  grep -qE '^_ez_validate_exit_trap\(\)' "${REPO_ROOT}/scripts/validate.sh"
  grep -qF "trap '_ez_validate_exit_trap \$?' EXIT" "${REPO_ROOT}/scripts/validate.sh"

  local stub="${BATS_TEST_TMPDIR}/failing-bazel"
  printf '#!/usr/bin/env bash\necho "ERROR: analysis of target failed" >&2\nexit 1\n' >"${stub}"
  chmod +x "${stub}"
  run env BAZEL="${stub}" RUN_BAZEL_CORE=true RUN_DOCS=false EZ_BUG_HINT=1 \
    EZ_BUG_REPORT_DIR="${BATS_TEST_TMPDIR}/reports" \
    bash "${REPO_ROOT}/scripts/validate.sh" --ci
  [ "$status" -ne 0 ]
  [[ ${output} == *'[ez-comfy][BUG] Template saved:'* ]]
  # The trap reports the slice that died, so the template names that line.
  local saved hints
  saved="$(printf '%s\n' "${output}" | sed -n 's/.*Template saved: //p' | head -n 1)"
  hints="$(printf '%s\n' "${output}" | grep -c '^\[ez-comfy\]\[BUG\] Template saved:' || true)"
  [ -f "${saved}" ]
  run cat "${saved}"
  [[ ${output} == *'build //... --nobuild'* ]]
  [[ ${output} == *'exited with status 1'* ]]
  [ "${hints}" -eq 1 ]
}

# A Bazel sh_test names $0 after the target and passes the npm script as $1, so the runner
# has to resolve the script from the argument whenever the target name is not itself a
# command. //docs-site:visual-test was unreachable for exactly this reason: it ran "npm
# visual" and npm answered "Unknown command".
_make_npm_stub() {
  local pkg="$1"
  mkdir -p "${pkg}/bin" "${pkg}/node_modules/.bin"
  cat >"${pkg}/bin/npm" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$@"
STUB
  chmod +x "${pkg}/bin/npm"
  : >"${pkg}/node_modules/.bin/next"
  : >"${pkg}/node_modules/.bin/vitest"
  chmod +x "${pkg}/node_modules/.bin/next" "${pkg}/node_modules/.bin/vitest"
}

@test "npm runner maps a gate target onto its npm script" {
  local pkg
  pkg="$(mktemp -d)"
  _make_npm_stub "${pkg}"
  cp "${REPO_ROOT}/docs-site/run_npm.sh" "${pkg}/visual-test"
  run env PATH="${pkg}/bin:${PATH}" bash "${pkg}/visual-test" visual
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]
  [ "${lines[0]}" = "run" ]
  [ "${lines[1]}" = "visual" ]
  rm -f "${pkg}/bin/npm" "${pkg}/visual-test" "${pkg}/node_modules/.bin/next" "${pkg}/node_modules/.bin/vitest"
  rmdir "${pkg}/node_modules/.bin" "${pkg}/node_modules" "${pkg}/bin" "${pkg}"
}

@test "npm runner still resolves a target named after its script" {
  local pkg
  pkg="$(mktemp -d)"
  _make_npm_stub "${pkg}"
  cp "${REPO_ROOT}/docs-site/run_npm.sh" "${pkg}/typecheck"
  run env PATH="${pkg}/bin:${PATH}" bash "${pkg}/typecheck" typecheck
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]
  [ "${lines[0]}" = "run" ]
  [ "${lines[1]}" = "typecheck" ]
  rm -f "${pkg}/bin/npm" "${pkg}/typecheck" "${pkg}/node_modules/.bin/next" "${pkg}/node_modules/.bin/vitest"
  rmdir "${pkg}/node_modules/.bin" "${pkg}/node_modules" "${pkg}/bin" "${pkg}"
}

@test "npm runner generic escape hatch forwards every argument" {
  local pkg
  pkg="$(mktemp -d)"
  _make_npm_stub "${pkg}"
  cp "${REPO_ROOT}/docs-site/run_npm.sh" "${pkg}/npm"
  run env PATH="${pkg}/bin:${PATH}" bash "${pkg}/npm" ci --force
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]
  [ "${lines[0]}" = "ci" ]
  [ "${lines[1]}" = "--force" ]
  rm -f "${pkg}/bin/npm" "${pkg}/npm" "${pkg}/node_modules/.bin/next" "${pkg}/node_modules/.bin/vitest"
  rmdir "${pkg}/node_modules/.bin" "${pkg}/node_modules" "${pkg}/bin" "${pkg}"
}

# ---- docs-site visual launcher: the mount probe ------------------------------------------
#
# The lane renders inside a container that bind-mounts the checkout.  A daemon that lives
# elsewhere (a DinD sidecar, a remote context) accepts a --volume whose source it cannot see and
# mounts an empty /lab, and a daemon handed a stale copy of the path passes a presence check, so
# --update would rewrite the committed baselines from a rendering that is not the tree under
# review.  Only a started container discovers either, so the probe is driven here with a stubbed
# docker rather than a real daemon.

_make_docker_stub() {
  local dir="$1"
  mkdir -p "${dir}/bin"
  cat >"${dir}/bin/docker" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"${DOCKER_CALLS}"
local_entry=""
saw_entrypoint="false"
for a in "$@"; do
  if [[ ${saw_entrypoint} == "true" ]]; then
    local_entry="${a}"
    saw_entrypoint="false"
    continue
  fi
  [[ ${a} == "--entrypoint" ]] && saw_entrypoint="true"
done
case "${1:-}" in
  info | pull) exit 0 ;;
  run) ;;
  *) exit 0 ;;
esac
case "${local_entry}" in
  test) exit 0 ;;
  sha256sum)
    files=()
    for a in "$@"; do
      [[ ${a} == docs-site/* ]] && files+=("${a}")
    done
    if [[ ${#files[@]} -eq 0 ]]; then
      exit 1
    fi
    if ! out="$(cd "${STUB_REPO_ROOT}" && sha256sum "${files[@]}")"; then
      exit 1
    fi
    if [[ "${DOCKER_MODE:-match}" != "match" ]]; then
      # A whole-hash swap: rewriting one hex digit would pass whenever that digit is already 0.
      out="$(printf '%s\n' "${out}" |
        sed '1s/^[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]/deadbeef/')"
    fi
    printf '%s\n' "${out}"
    exit 0
    ;;
  *) echo "x86_64"; exit 0 ;;
esac
STUB
  chmod +x "${dir}/bin/docker"
}

_cleanup_docker_stub() {
  rm -f "${LAUNCHER_STUB}/bin/docker" "${LAUNCHER_CALLS}"
  rmdir "${LAUNCHER_STUB}/bin" "${LAUNCHER_STUB}"
}

_run_visual_launcher() {
  local mode="$1"
  shift
  local stub calls
  stub="$(mktemp -d)"
  _make_docker_stub "${stub}"
  calls="${stub}/calls"
  : >"${calls}"
  run env -u BUILD_WORKSPACE_DIRECTORY \
    PATH="${stub}/bin:${PATH}" \
    DOCKER_CALLS="${calls}" \
    STUB_REPO_ROOT="${REPO_ROOT}" \
    DOCKER_MODE="${mode}" \
    bash "${REPO_ROOT}/docs-site/scripts/visual_linux.sh" "$@"
  LAUNCHER_CALLS="${calls}"
  LAUNCHER_STUB="${stub}"
  LAUNCHER_STATUS="${status}"
  LAUNCHER_OUTPUT="${output}"
}

# A leading `!` suppresses errexit in Bats, so `! grep -q ...` can never fail a test; run the
# lookup and assert on its status instead.
_assert_absent() {
  run grep -q -- "$1" "$2"
  [ "${status}" -ne 0 ]
}

@test "visual launcher blocks a capture whose mount is a stale copy of the checkout" {
  _run_visual_launcher stale
  [ "${LAUNCHER_STATUS}" -eq 1 ]
  [[ ${LAUNCHER_OUTPUT} == *"does not see this checkout at /lab"* ]]
  # The whole point: a capture started from a tree nobody reviewed must never start.
  _assert_absent 'bash /lab/docs-site/scripts/visual_linux_in_container.sh' "${LAUNCHER_CALLS}"
  _cleanup_docker_stub
}

@test "visual launcher probe runs on the capture path, not only under --check" {
  _run_visual_launcher stale
  [ "${LAUNCHER_STATUS}" -eq 1 ]
  run grep -q -- '--entrypoint sha256sum' "${LAUNCHER_CALLS}"
  [ "${status}" -eq 0 ]
  _cleanup_docker_stub
}

@test "visual launcher --check reports ready when the container sees this checkout" {
  _run_visual_launcher match --check
  [ "${LAUNCHER_STATUS}" -eq 0 ]
  [[ ${LAUNCHER_OUTPUT} == *"visual lane ready"* ]]
  _assert_absent 'bash /lab/docs-site/scripts/visual_linux_in_container.sh' "${LAUNCHER_CALLS}"
  _cleanup_docker_stub
}
