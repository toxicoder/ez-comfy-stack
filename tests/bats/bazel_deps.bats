#!/usr/bin/env bats
#
# Hermetic tests for tests/bazel_deps.py, the "every tracked file is owned by a
# BUILD target" guard.
#
# Purpose:
#   Prove the guard runs from a shell, passes on this checkout, and - the part
#   that matters - fails on the three drift classes it exists to catch: a
#   tracked file no BUILD file names, a payload the contract requires but the
#   BUILD data dropped, and a test target no suite claims.
#
# Safety: no Bazel invocation (a nested bazel call would contend with the
#   output-base lock of the //tests:bats_* action running this suite), no
#   Docker, no GPU, no network. The failing cases run against throwaway
#   `git init` trees under TMPDIR, never against this checkout.

load 'test_helper'

setup() {
  setup_repo_env
  GUARD="${REPO_ROOT}/tests/bazel_deps.py"
  SCRATCH="$(mktemp -d)"
  git -C "${SCRATCH}" init -q
  git -C "${SCRATCH}" config user.email bats@example.com
  git -C "${SCRATCH}" config user.name bats
  printf 'module(name = "scratch")\n' > "${SCRATCH}/MODULE.bazel"
}

teardown() {
  teardown_repo_env
  rm -rf "${SCRATCH}"
}

# Write a scratch checkout: one package, the given BUILD body, the given files.
# Globals:
#   SCRATCH
# Arguments:
#   $1 - BUILD.bazel body
#   $2.. - newline-separated tracked paths
# Outputs:
#   Creates and commits the tree under SCRATCH
# Returns:
#   0
scratch_repo() {
  local body="$1"
  shift
  printf '%s\n' "${body}" > "${SCRATCH}/BUILD.bazel"
  local path
  for path in "$@"; do
    mkdir -p "${SCRATCH}/$(dirname "${path}")"
    : > "${SCRATCH}/${path}"
  done
  git -C "${SCRATCH}" add -A
}

@test "guard passes on this checkout" {
  run python3 "${GUARD}" --root "${REPO_ROOT}"
  [ "$status" -eq 0 ]
  [[ "${output}" == *"0 violation(s)"* ]]
}

@test "guard selects one check at a time" {
  run python3 "${GUARD}" --root "${REPO_ROOT}" --check-ownership
  [ "$status" -eq 0 ]
  run python3 "${GUARD}" --root "${REPO_ROOT}" --check-payloads
  [ "$status" -eq 0 ]
  run python3 "${GUARD}" --root "${REPO_ROOT}" --check-suites
  [ "$status" -eq 0 ]
}

@test "a tracked file no BUILD file names fails the guard" {
  scratch_repo 'filegroup(name = "srcs", srcs = ["a.py"])' a.py orphan.md
  run python3 "${GUARD}" --root "${SCRATCH}" --check-ownership
  [ "$status" -eq 1 ]
  [[ "${output}" == *"orphan.md: named by no BUILD file"* ]]
}

@test "a BUILD file and a .bazelignore entry both exempt a file" {
  scratch_repo 'filegroup(name = "srcs", srcs = ["a.py"])' a.py
  run python3 "${GUARD}" --root "${SCRATCH}" --check-ownership
  [ "$status" -eq 0 ]

  printf 'scratch/\n' > "${SCRATCH}/.bazelignore"
  scratch_repo 'filegroup(name = "srcs", srcs = ["a.py"])' a.py scratch/private.md
  run python3 "${GUARD}" --root "${SCRATCH}" --check-ownership
  [ "$status" -eq 0 ]
}

@test "a dropped payload fails the guard" {
  mkdir -p "${SCRATCH}/lints"
  cp "${REPO_ROOT}/lints/buildifier_check.sh" "${SCRATCH}/lints/buildifier_check.sh"
  cat > "${SCRATCH}/lints/BUILD.bazel" <<'EOF'
sh_test(
    name = "buildifier",
    srcs = ["buildifier_check.sh"],
    data = ["//scripts:lib/check_tool.sh"],
)
EOF
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-payloads
  # The scratch tree holds only one contracted target, so the others are
  # reported as missing; what matters is that buildifier itself is clean here.
  [[ "${output}" != *"//lints:buildifier: undeclared payload"* ]]

  printf 'sh_test(\n    name = "buildifier",\n    srcs = ["buildifier_check.sh"],\n)\n' \
    > "${SCRATCH}/lints/BUILD.bazel"
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-payloads
  [ "$status" -eq 1 ]
  [[ "${output}" == *"//lints:buildifier: undeclared payload //scripts:lib/check_tool.sh"* ]]
}

@test "a payload the script stopped reading fails the guard" {
  mkdir -p "${SCRATCH}/lints"
  printf '#!/usr/bin/env bash\necho no tools here\n' > "${SCRATCH}/lints/buildifier_check.sh"
  cat > "${SCRATCH}/lints/BUILD.bazel" <<'EOF'
sh_test(
    name = "buildifier",
    srcs = ["buildifier_check.sh"],
    data = ["//scripts:lib/check_tool.sh"],
)
EOF
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-payloads
  [ "$status" -eq 1 ]
  [[ "${output}" == *"//lints:buildifier: unsupported requirement"* ]]
}

@test "a test target no suite claims fails the guard" {
  mkdir -p "${SCRATCH}/tests"
  cat > "${SCRATCH}/BUILD.bazel" <<'EOF'
test_suite(
    name = "test-fast",
    tests = ["//tests:js"],
)
EOF
  cat > "${SCRATCH}/tests/BUILD.bazel" <<'EOF'
sh_test(
    name = "js",
    srcs = ["run_js.sh"],
)
EOF
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-suites
  [ "$status" -eq 0 ]

  # An orphan sh_test that no suite names.
  cat >> "${SCRATCH}/tests/BUILD.bazel" <<'EOF'

sh_test(
    name = "orphan",
    srcs = ["bats_runner.sh"],
)
EOF
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-suites
  [ "$status" -eq 1 ]
  [[ "${output}" == *"//tests:orphan"* ]]
}

@test "a BUILD file the guard cannot read is a finding, not a crash" {
  scratch_repo 'filegroup(name = "srcs", srcs = ["a.py",])' a.py
  printf 'filegroup(\n' >> "${SCRATCH}/BUILD.bazel"
  git -C "${SCRATCH}" add -A
  run python3 "${GUARD}" --root "${SCRATCH}" --check-ownership
  [ "$status" -eq 1 ]
  [[ "${output}" == *":BUILD.bazel: unparseable"* ]]
  [[ "${output}" != *"Traceback"* ]]
}

@test "this checkout declares no target named all" {
  run grep -rEn '^\s*name = "all",' "${REPO_ROOT}" --include=BUILD.bazel
  [ "$status" -eq 1 ]
}

@test "the js gate declares the mjs tree" {
  grep -q 'name = "js_files"' "${REPO_ROOT}/tests/BUILD.bazel"
  grep -q '":js_files"' "${REPO_ROOT}/tests/BUILD.bazel"
  grep -q '"js/\*\*"' "${REPO_ROOT}/tests/BUILD.bazel"
  [ "$(find "${REPO_ROOT}/tests/js" -name '*.mjs' | wc -l)" -eq 6 ]
}

@test "the css tree is owned by the custom_nodes filegroup" {
  grep -q '"\*\*/\*.css"' "${REPO_ROOT}/custom_nodes/BUILD.bazel"
  [ -f "${REPO_ROOT}/custom_nodes/ez_feedback/js/ez_feedback.css" ]
  [ -f "${REPO_ROOT}/custom_nodes/ez_outputs/js/ez_outputs.css" ]
}

@test "the lint gates fail loudly under bazel" {
  [ "$(grep -c 'REQUIRE_LINT_TOOLS": "1"' "${REPO_ROOT}/lints/BUILD.bazel")" -eq 5 ]
}

@test "every docs-site test belongs to the docs-site suite or test-all" {
  grep -q 'name = "suite"' "${REPO_ROOT}/docs-site/BUILD.bazel"
  grep -q ':visual_tooling_test' "${REPO_ROOT}/docs-site/BUILD.bazel"
  grep -q '//docs-site:visual-test' "${REPO_ROOT}/BUILD.bazel"
}

@test "an unmapped scratch file is caught by intent-to-add" {
  scratch_repo 'filegroup(name = "srcs", srcs = ["a.py"])' a.py
  : > "${SCRATCH}/notes.md"
  git -C "${SCRATCH}" add -N notes.md
  run python3 "${GUARD}" --root "${SCRATCH}" --check-ownership
  [ "$status" -eq 1 ]
  [[ "${output}" == *"notes.md"* ]]
}
