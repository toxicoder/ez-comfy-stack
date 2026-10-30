#!/usr/bin/env bats
#
# ## runfiles.bats
#
# Purpose:
#   Cover path resolution for the Bazel ingress: manage.sh and
#   scripts/utilities/runner.sh may be exec'd from a runfiles tree, but
#   REPO_ROOT, the compose file, and every utility dispatch must resolve to the
#   git checkout. lib/ is still sourced from the tree the script lives in.
#
# Hermetic:
#   Builds a throwaway checkout and a throwaway runfiles tree (symlinks into the
#   throwaway checkout) under TEST_TMP_DIR, so neither the developer .env nor
#   bazel-out can satisfy an assertion. Docker/wondershaper/speedtest/hf mocks
#   come from test_helper.

load 'test_helper'

#######################################
# Build a throwaway git checkout under the given root: the sources manage.sh
# and the utilities need, as real copies (readlink cannot escape to the real
# repo), plus a stub MODULE.bazel and no .env.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1 - Absolute target directory for the fake checkout
# Outputs:
#   Creates files under $1
# Returns:
#   0 on success; non-zero if the copy fails
#######################################
make_fake_checkout() {
  local root="${1}"
  mkdir -p "${root}/scripts/lib" "${root}/docker"
  cp "${REPO_ROOT}/scripts/manage.sh" "${root}/scripts/manage.sh"
  # shellcheck disable=SC2046  # glob expansion is the point here
  cp "${REPO_ROOT}"/scripts/lib/*.sh "${root}/scripts/lib/"
  # shellcheck disable=SC2046  # glob expansion is the point here
  cp "${REPO_ROOT}"/scripts/lib/*.py "${root}/scripts/lib/" 2>/dev/null || true
  cp -r "${REPO_ROOT}/scripts/utilities" "${root}/scripts/utilities"
  cp "${REPO_ROOT}/docker/docker-compose.yml" "${root}/docker/docker-compose.yml"
  cp -r "${REPO_ROOT}/docker/install-comfy" "${root}/docker/install-comfy"
  : >"${root}/MODULE.bazel"
}

#######################################
# Build a throwaway runfiles tree whose entries symlink back into the fake
# checkout, mirroring what bazel run lays down. Deliberately has no docker/
# directory: a runfiles REPO_ROOT cannot satisfy the compose check.
# Globals:
#   None
# Arguments:
#   $1 - Absolute target directory for the runfiles tree (the _main level)
#   $2 - Absolute fake checkout the entries symlink into
# Outputs:
#   Creates symlinks under $1
# Returns:
#   0 on success
#######################################
make_fake_runfiles() {
  local rf="${1}"
  local root="${2}"
  local f
  mkdir -p "${rf}/scripts/lib" "${rf}/scripts/utilities"
  ln -s "${root}/scripts/manage.sh" "${rf}/scripts/manage.sh"
  # shellcheck disable=SC2046  # glob expansion is the point here
  for f in "${root}"/scripts/lib/*.sh; do
    ln -s "${f}" "${rf}/scripts/lib/$(basename "${f}")"
  done
  # shellcheck disable=SC2046  # glob expansion is the point here
  for f in "${root}"/scripts/utilities/*.sh; do
    ln -s "${f}" "${rf}/scripts/utilities/$(basename "${f}")"
  done
}

setup() {
  setup_repo_env
  install_docker_mocks
  install_wondershaper_mock
  install_speedtest_mock 100
  install_hf_mock
  CHECKOUT="${TEST_TMP_DIR}/checkout"
  RUNFILES="${TEST_TMP_DIR}/rf/_main"
  make_fake_checkout "${CHECKOUT}"
  make_fake_runfiles "${RUNFILES}" "${CHECKOUT}"
}

teardown() {
  teardown_repo_env
}

@test "manage.sh exec'd from runfiles reports the checkout compose file" {
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/manage.sh" doctor
  [[ "${output}" == *"compose file: ${CHECKOUT}/docker/docker-compose.yml"* ]]
  [[ "${output}" != *"${RUNFILES}"* ]]
  [[ "${output}" != *"bazel-out"* ]]
  [ "${status}" -eq 0 ]
}

@test "manage.sh exec'd from runfiles falls back to the symlinked checkout" {
  run env -u REPO_ROOT -u BUILD_WORKSPACE_DIRECTORY \
    bash "${RUNFILES}/scripts/manage.sh" doctor
  [[ "${output}" == *"compose file: ${CHECKOUT}/docker/docker-compose.yml"* ]]
  [[ "${output}" != *"${RUNFILES}"* ]]
  [ "${status}" -eq 0 ]
}

@test "manage.sh still sources lib from the tree it was exec'd from" {
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/manage.sh" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ez-comfy-stack manage"* ]]
  [ -e "${RUNFILES}/scripts/lib/common.sh" ]
  grep -F 'source "${SCRIPT_DIR}/lib/common.sh"' "${RUNFILES}/scripts/manage.sh"
}

@test "runner.sh dispatches by name from the source tree" {
  run bash "${REPO_ROOT}/scripts/utilities/runner.sh" download-limit status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"interface"'* ]]
}

@test "runner.sh prefers the checkout copy over the runfiles copy" {
  cat >"${CHECKOUT}/scripts/utilities/probe-marker.sh" <<'PROBE'
#!/usr/bin/env bash
printf 'source=checkout\nREPO_ROOT=%s\n' "${REPO_ROOT:-}"
PROBE
  cat >"${RUNFILES}/scripts/utilities/probe-marker.sh" <<'PROBE'
#!/usr/bin/env bash
printf 'source=runfiles\nREPO_ROOT=%s\n' "${REPO_ROOT:-}"
PROBE
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/utilities/runner.sh" probe-marker
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"source=checkout"* ]]
  [[ "${output}" != *"source=runfiles"* ]]
  [[ "${output}" == *"REPO_ROOT=${CHECKOUT}"* ]]
}

@test "runner.sh exports REPO_ROOT of the checkout to a runfiles-only utility" {
  cat >"${RUNFILES}/scripts/utilities/probe-only.sh" <<'PROBE'
#!/usr/bin/env bash
printf 'REPO_ROOT=%s\n' "${REPO_ROOT:-}"
PROBE
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/utilities/runner.sh" probe-only
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"REPO_ROOT=${CHECKOUT}"* ]]
}

@test "runner.sh reports an unknown utility instead of exec'ing a miss" {
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/utilities/runner.sh" no-such-utility-xyz
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"no-such-utility-xyz"* ]]
  [[ "${output}" != *"No such file or directory"* ]]
}

@test "runner.sh refuses a utility name that escapes scripts/utilities" {
  cat >"${CHECKOUT}/scripts/probe-escape.sh" <<'PROBE'
#!/usr/bin/env bash
printf 'ESCAPED\n'
PROBE
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/utilities/runner.sh" ../probe-escape
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"bare name"* ]]
  [[ "${output}" != *"ESCAPED"* ]]
}

@test "runner.sh usage exits 2 without a utility name" {
  run env -u REPO_ROOT BUILD_WORKSPACE_DIRECTORY="${CHECKOUT}" \
    bash "${RUNFILES}/scripts/utilities/runner.sh"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"missing utility name"* ]]
}
