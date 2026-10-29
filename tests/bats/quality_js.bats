#!/usr/bin/env bats
#
# ## quality_js.bats
#
# Purpose:
#   Gate the EZQuality combo client contract. Runs the node:test suite under
#   tests/js/, which loads custom_nodes/ez_quality/js/ez_quality.js against an
#   in-repo frontend stub and asserts that picking a tier writes every affected
#   widget and that a breaking edit flips the combo to custom.
#
# Hermetic:
#   No browser, no npm install, no network. The frontend shim lives in
#   tests/js/ez_frontend_stub.mjs. Skips when node is not installed.

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "quality js: node --test suite over tests/js passes" {
  if ! command -v node >/dev/null 2>&1; then
    skip "node not installed"
  fi
  [ -f "${REPO_ROOT}/custom_nodes/ez_quality/js/ez_quality.js" ]
  [ -f "${REPO_ROOT}/custom_nodes/ez_quality/js/ez_quality_presets.js" ]
  ls "${REPO_ROOT}"/tests/js/*.test.mjs >/dev/null

  cd "${REPO_ROOT}" || return 1
  # node --test takes globs, not bare directories, on this node build.
  run node --test "tests/js/*.test.mjs"
  if [ "${status}" -ne 0 ]; then
    printf '%s\n' "${output}" >&2
  fi
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"fail 0"* ]]
  [[ "${output}" =~ pass\ [1-9] ]]
}
