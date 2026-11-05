#!/usr/bin/env bats
#
# ## everything.bats
#
# Purpose:
#   Gate scripts/everything.sh, the one target that runs every Bazel gate. It
#   must run the gates in dependency order, name the failing target when one
#   fails, keep going so the report lists every failure, and never shell out to
#   anything but the Bazel binary.
#
# Hermetic:
#   No Bazel, no Docker, no GPU, no network. Every gate is driven through a stub
#   BAZEL script under TMPDIR that records its argv and exits on command, so the
#   suite asserts on the invocations rather than on a real build.

load 'test_helper'

setup() {
  setup_repo_env
  SCRIPT="${REPO_ROOT}/scripts/everything.sh"
  SCRATCH="$(mktemp -d)"
  mkdir -p "${SCRATCH}/bin" "${SCRATCH}/empty"
  # Stub Bazel: one argv line per call, exit code consumed per call from
  # STUB_EXIT (comma-separated) so a test can fail exactly one gate.
  cat >"${SCRATCH}/bin/bazelisk" <<'STUB'
#!/usr/bin/env bash
echo "bazelisk $*" >>"${STUB_LOG}"
n=$(($(wc -l <"${STUB_LOG}") - 1))
IFS=',' read -r -a codes <<<"${STUB_EXIT:-0}"
code="${codes[${n}]:-${codes[-1]:-0}}"
exit "${code}"
STUB
  chmod +x "${SCRATCH}/bin/bazelisk"
  # Stub Docker: the visual lane probes the daemon, so the suite controls the
  # answer with STUB_DOCKER instead of touching a real one. The default is
  # unreachable, which keeps every other test off the container path.
  cat >"${SCRATCH}/bin/docker" <<'STUB'
#!/usr/bin/env bash
exit "${STUB_DOCKER:-1}"
STUB
  chmod +x "${SCRATCH}/bin/docker"
  export STUB_DOCKER="${STUB_DOCKER:-1}"
  export STUB_LOG="${SCRATCH}/calls.txt"
  : >"${STUB_LOG}"
}

teardown() {
  teardown_repo_env
  rm -rf "${SCRATCH}"
}

# Source the script with a stub Bazel on PATH and an optional flag.
# Globals:
#   SCRIPT, SCRATCH
# Arguments:
#   $1 - optional flag to parse before sourcing
# Outputs:
#   Nothing; leaves the script's functions defined in the test shell
# Returns:
#   0
_load_script() {
  PATH="${SCRATCH}/bin:${PATH}"
  BAZEL="${SCRATCH}/bin/bazelisk"
  SKIP_BOOTSTRAP=0
  # shellcheck source=../../scripts/everything.sh disable=SC1091
  source "${SCRIPT}" ${1-}
}

# Decide what the stubbed Docker daemon answers to the visual-lane probe.
# Globals:
#   STUB_DOCKER
# Arguments:
#   $1 - exit code the stub 'docker info' should return (0 = daemon reachable)
# Outputs:
#   Nothing
# Returns:
#   0
_stub_docker() {
  export STUB_DOCKER="$1"
}

# Point the lane at a goldens directory holding one baseline, as a real
# checkout would after a capture.
# Globals:
#   SCRATCH, GOLDENS_DIR
# Arguments:
#   None
# Outputs:
#   A goldens directory containing one PNG
# Returns:
#   0
_place_baseline() {
  GOLDENS_DIR="${SCRATCH}/goldens"
  mkdir -p "${GOLDENS_DIR}"
  : >"${GOLDENS_DIR}/index.png"
}

@test "everything: usage names both flags and the default sweep" {
  run bash "${SCRIPT}" --help
  [ "$status" -eq 0 ]
  [[ "${output}" == *"--skip-bootstrap"* ]]
  [[ "${output}" == *":test-all"* ]]
  [[ "${output}" == *"render-check"* ]]
}

@test "everything: an unknown argument is exit 2, not a silent pass" {
  run bash "${SCRIPT}" --nope
  [ "$status" -eq 2 ]
  [[ "${output}" == *"unknown argument"* ]]
}

@test "everything: a host with no bazelisk is exit 2 naming the repair" {
  # Absolute bash: command -v is a builtin, so an empty PATH really does have
  # no bazelisk, which is the state the script has to survive.
  run env PATH="${SCRATCH}/empty" BAZEL= /bin/bash "${SCRIPT}"
  [ "$status" -eq 2 ]
  [[ "${output}" == *"bazelisk or bazel not found"* ]]
  [[ "${output}" == *"setup-host"* ]]
}

@test "everything: run_bootstrap_gate probes the host toolchain" {
  _load_script
  run run_bootstrap_gate
  [ "$status" -eq 0 ]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk run //:setup-host -- --check" ]
}

@test "everything: run_bootstrap_gate prints the repair when the probe fails" {
  export STUB_EXIT=1
  _load_script
  run run_bootstrap_gate
  [ "$status" -eq 1 ]
  [[ "${output}" == *"install the pinned toolchain"* ]]
  [[ "${output}" == *"bash scripts/setup-host.sh"* ]]
}

@test "everything: --skip-bootstrap drops only the toolchain probe" {
  _load_script "--skip-bootstrap"
  run run_bootstrap_gate
  [ "$status" -eq 0 ]
  [[ "${output}" == *"skipping the //:setup-host probe"* ]]
  [ ! -s "${STUB_LOG}" ]
}

@test "everything: run_graph_gate loads and analyses without building" {
  _load_script
  run run_graph_gate
  [ "$status" -eq 0 ]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk build //... --nobuild" ]
}

@test "everything: run_test_gate runs the whole test lane minus the container lane" {
  _load_script
  run run_test_gate
  [ "$status" -eq 0 ]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk test //:test-all --test_tag_filters=-visual" ]
}

@test "everything: run_docs_gate builds then render-checks" {
  _load_script
  run run_docs_gate
  [ "$status" -eq 0 ]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk run //docs:docs" ]
  [ "${lines[1]}" = "bazelisk run //docs:render-check" ]
}

@test "everything: the happy path calls every gate in order" {
  _load_script
  # Pin the container lane to a skip so the ordering below does not depend on
  # whether the host running the suite has a Docker daemon.
  _stub_docker 1
  GOLDENS_DIR="${SCRATCH}/no-goldens"
  run main
  [ "$status" -eq 0 ]
  [[ "${output}" == *"all gates passed"* ]]
  [[ "${output}" == *"1 skipped: docs-site visual lane"* ]]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk run //:setup-host -- --check" ]
  [ "${lines[1]}" = "bazelisk build //... --nobuild" ]
  [ "${lines[2]}" = "bazelisk test //:test-all --test_tag_filters=-visual" ]
  [ "${lines[3]}" = "bazelisk run //docs:docs" ]
  [ "${lines[4]}" = "bazelisk run //docs:render-check" ]
}

@test "everything: a failing gate is reported by its target name" {
  export STUB_EXIT="0,1,0,0,0,0"
  _load_script
  run main
  [ "$status" -eq 1 ]
  [[ "${output}" == *"gate //... (load and analysis) failed"* ]]
  [[ "${output}" == *"1 gate(s) failed"* ]]
}

@test "everything: one failure does not stop the later gates" {
  export STUB_EXIT="1,0,0,0,0,0"
  _load_script
  run main
  [ "$status" -eq 1 ]
  # The probe failed, yet the test lane and both docs gates still ran.
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk run //:setup-host -- --check" ]
  [ "${lines[2]}" = "bazelisk test //:test-all --test_tag_filters=-visual" ]
  [ "${lines[3]}" = "bazelisk run //docs:docs" ]
  [ "${lines[4]}" = "bazelisk run //docs:render-check" ]
}

@test "everything: a failing visual lane is reported by its own gate name" {
  export STUB_EXIT="0,0,0,1,0,0"
  _load_script
  _stub_docker 0
  _place_baseline
  run main
  [ "$status" -eq 1 ]
  [[ "${output}" == *"gate //docs-site visual lane failed"* ]]
  [[ "${output}" == *"1 gate(s) failed: //docs-site visual lane"* ]]
  run cat "${STUB_LOG}"
  [ "${lines[3]}" = "bazelisk test //docs-site:visual-test //docs-site:visual_tooling_test" ]
  # The docs gates still ran after the visual failure.
  [ "${lines[4]}" = "bazelisk run //docs:docs" ]
}

@test "everything: a broken docs render-check is reported separately" {
  export STUB_EXIT="0,0,0,0,1"
  _load_script
  run main
  [ "$status" -eq 1 ]
  [[ "${output}" == *"gate //docs:render-check failed"* ]]
}

@test "everything: gate forwards argv to bazelisk unchanged" {
  _load_script
  run gate "//:example" test //:example --test_output=errors
  [ "$status" -eq 0 ]
  [[ "${output}" == *"==> //:everything: //:example"* ]]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk test //:example --test_output=errors" ]
}

@test "everything: enter_workspace moves out of the Bazel output base" {
  # `bazel run` starts the binary inside the output base, where a nested Bazel
  # invocation is refused outright. This is what makes the target usable.
  _load_script
  local inside="${SCRATCH}/bazel-out/k8-fastbuild/bin"
  mkdir -p "${inside}"
  cd "${inside}"
  BUILD_WORKSPACE_DIRECTORY="${SCRATCH}" enter_workspace
  [ "$(pwd)" = "${SCRATCH}" ]
}

@test "everything: enter_workspace leaves a direct run alone" {
  _load_script
  local here="${SCRATCH}"
  cd "${here}"
  BUILD_WORKSPACE_DIRECTORY= enter_workspace
  [ "$(pwd)" = "${here}" ]
}

@test "everything: the visual lane skips when the daemon is unreachable" {
  _load_script
  _stub_docker 1
  _place_baseline
  run run_visual_gate
  [ "$status" -eq 0 ]
  [[ "${output}" == *"SKIP docs-site visual lane (the Docker daemon is not reachable)"* ]]
  [[ "${output}" == *"bazelisk run //docs-site:visual-linux -- --update"* ]]
  [ ! -s "${STUB_LOG}" ]
}

@test "everything: the visual lane skips when no baseline is committed" {
  _load_script
  _stub_docker 0
  GOLDENS_DIR="${SCRATCH}/missing-goldens"
  run run_visual_gate
  [ "$status" -eq 0 ]
  [[ "${output}" == *"SKIP docs-site visual lane (no committed baselines"* ]]
  [ ! -s "${STUB_LOG}" ]
}

@test "everything: an empty goldens directory is not a runnable lane" {
  _load_script
  _stub_docker 0
  GOLDENS_DIR="${SCRATCH}/goldens"
  mkdir -p "${GOLDENS_DIR}"
  run visual_lane_ready
  [ "$status" -eq 1 ]
  [[ "${output}" == *"no committed baselines"* ]]
}

@test "everything: visual_lane_ready is ready with a daemon and a baseline" {
  _load_script
  _stub_docker 0
  _place_baseline
  run visual_lane_ready
  [ "$status" -eq 0 ]
  [ -z "${output}" ]
}

@test "everything: the visual lane runs both targets when the host can support it" {
  _load_script
  _stub_docker 0
  _place_baseline
  run run_visual_gate
  [ "$status" -eq 0 ]
  run cat "${STUB_LOG}"
  [ "${lines[0]}" = "bazelisk test //docs-site:visual-test //docs-site:visual_tooling_test" ]
}

@test "everything: the sweep touches no host-mutating verb" {
  _load_script
  run main
  [ "$status" -eq 0 ]
  [[ "${output}" != *"sudo"* ]]
  local calls
  calls="$(cat "${STUB_LOG}")"
  [[ "${calls}" != *"docker"* ]]
  [[ "${calls}" != *"manage -- start"* ]]
  [[ "${calls}" != *"manage -- stop"* ]]
}
