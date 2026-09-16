#!/usr/bin/env bats
#
# Hermetic tests for the slim contributor devcontainer (Bazel + lint pins).

load 'test_helper'

setup() {
  setup_repo_env
  export DEVCONTAINER_DIR="${REPO_ROOT}/.devcontainer"
}

teardown() {
  teardown_repo_env
}

@test "tool-versions.env exists and is bash-sourceable" {
  [[ -f "${DEVCONTAINER_DIR}/tool-versions.env" ]]
  run bash -c "set -a; source '${DEVCONTAINER_DIR}/tool-versions.env'; set +a; test -n \"\${BAZELISK_VERSION}\" && test -n \"\${BUILDIFIER_VERSION}\" && test -n \"\${SHFMT_ASSET_VERSION}\""
  [ "$status" -eq 0 ]
}

@test "Dockerfile does not download unpinned releases/latest for CLIs" {
  run grep -E 'https://.*/releases/latest/' "${DEVCONTAINER_DIR}/Dockerfile"
  [ "$status" -ne 0 ]
}

@test "Dockerfile is multi-arch (amd64 and arm64)" {
  grep -q 'amd64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'arm64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'TARGETARCH' "${DEVCONTAINER_DIR}/Dockerfile"
}

@test "Dockerfile RUN shell supports pipefail (bash SHELL, not dash)" {
  grep -Eq '^SHELL[[:space:]]*\[.*bash' "${DEVCONTAINER_DIR}/Dockerfile"
}

@test "Dockerfile does not hardcode TARGETARCH default to amd64" {
  run grep -E '^ARG[[:space:]]+TARGETARCH=' "${DEVCONTAINER_DIR}/Dockerfile"
  [ "$status" -ne 0 ]
  grep -Eq '^ARG[[:space:]]+TARGETARCH([[:space:]]|$)' "${DEVCONTAINER_DIR}/Dockerfile"
}

@test "Dockerfile and install-lint-tools pin match tool-versions.env" {
  # shellcheck disable=SC1091
  source "${DEVCONTAINER_DIR}/tool-versions.env"
  grep -q "${BAZELISK_VERSION}" "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q "${BUILDIFIER_VERSION}" "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q "${SHFMT_ASSET_VERSION}" "${DEVCONTAINER_DIR}/Dockerfile"
  local installer="${REPO_ROOT}/scripts/ci/install-lint-tools.sh"
  [[ -f ${installer} ]]
  grep -q "tool-versions.env" "${installer}"
}

@test "Dockerfile does not install k8s or ansible CLIs" {
  run grep -Ei 'kubeconform|kubectl|helm|ansible' "${DEVCONTAINER_DIR}/Dockerfile"
  [ "$status" -ne 0 ]
}

@test "doctor.sh --help prints usage" {
  run bash "${DEVCONTAINER_DIR}/doctor.sh" --help
  [ "$status" -eq 0 ]
  [[ ${output} == *"Usage:"* ]]
  [[ ${output} == *"bazelisk"* ]] || [[ ${output} == *"//:validate"* ]]
}

@test "doctor.sh fails when required tools are missing from PATH" {
  run env PATH="/usr/bin:/bin" DEVCONTAINER_DOCTOR_STRICT=1 \
    bash "${DEVCONTAINER_DIR}/doctor.sh" --quiet
  [ "$status" -eq 1 ]
}

@test "doctor.sh strict=0 exits 0 even when tools missing" {
  run env PATH="/usr/bin:/bin" DEVCONTAINER_DOCTOR_STRICT=0 \
    bash "${DEVCONTAINER_DIR}/doctor.sh" --quiet
  [ "$status" -eq 0 ]
}

@test "devcontainer.json points Bazel at bazelisk" {
  grep -q 'bazel.executable' "${DEVCONTAINER_DIR}/devcontainer.json"
  grep -q 'bazelisk' "${DEVCONTAINER_DIR}/devcontainer.json"
  run grep -E 'docker-in-docker' "${DEVCONTAINER_DIR}/devcontainer.json"
  [ "$status" -ne 0 ]
}

@test "post-create.sh prewarms bazelisk" {
  [[ -f "${DEVCONTAINER_DIR}/post-create.sh" ]]
  grep -Eq 'bazelisk (version|info)' "${DEVCONTAINER_DIR}/post-create.sh"
}
