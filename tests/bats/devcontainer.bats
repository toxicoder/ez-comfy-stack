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
  run bash -c "set -a; source '${DEVCONTAINER_DIR}/tool-versions.env'; set +a; test -n \"\${BAZELISK_VERSION}\" && test -n \"\${BUILDIFIER_VERSION}\" && test -n \"\${SHFMT_ASSET_VERSION}\" && test -n \"\${GROK_VERSION}\" && test -n \"\${NODE_VERSION}\" && test -n \"\${NODE_SHA256_X64}\" && test -n \"\${NODE_SHA256_ARM64}\""
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
  grep -q "${GROK_VERSION}" "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q "${NODE_VERSION}" "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q "${NODE_SHA256_X64}" "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q "${NODE_SHA256_ARM64}" "${DEVCONTAINER_DIR}/Dockerfile"
  local installer="${REPO_ROOT}/scripts/ci/install-lint-tools.sh"
  [[ -f ${installer} ]]
  grep -q "tool-versions.env" "${installer}"
}

@test "Dockerfile uses Ubuntu 24.04 noble and BuildKit cache mounts" {
  grep -Eq 'FROM .*devcontainers/base:noble' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q '# syntax=docker/dockerfile:1' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q -- '--mount=type=cache,target=/var/cache/apt' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'bubblewrap' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'python3-venv' "${DEVCONTAINER_DIR}/Dockerfile"
}

@test "Dockerfile does not COPY pin files before apt" {
  run grep -E '^COPY[[:space:]]+tool-versions\.env' "${DEVCONTAINER_DIR}/Dockerfile"
  [ "$status" -ne 0 ]
}

@test "Dockerfile layer order keeps Grok after Node" {
  local df="${DEVCONTAINER_DIR}/Dockerfile"
  local node_line grok_line
  node_line="$(grep -nE '^ARG[[:space:]]+NODE_VERSION=' "${df}" | head -1 | cut -d: -f1)"
  grok_line="$(grep -nE '^ARG[[:space:]]+GROK_VERSION=' "${df}" | head -1 | cut -d: -f1)"
  [[ -n ${node_line} && -n ${grok_line} ]]
  [[ ${grok_line} -gt ${node_line} ]]
}

@test "Dockerfile uses official Node tarball and Grok linux artifacts" {
  grep -q 'linux-x64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'linux-arm64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'linux-x86_64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'linux-aarch64' "${DEVCONTAINER_DIR}/Dockerfile"
  grep -q 'x.ai/cli/grok-' "${DEVCONTAINER_DIR}/Dockerfile"
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

@test "devcontainer.json reaches host LLM without host networking" {
  local json="${DEVCONTAINER_DIR}/devcontainer.json"
  grep -q 'host.docker.internal' "${json}"
  grep -q 'host-gateway' "${json}"
  grep -q 'GROK_SANDBOX' "${json}"
  grep -q 'XAI_API_KEY' "${json}"
  grep -q 'ez-comfy-devcontainer' "${json}"
  grep -q 'docker-outside-of-docker:1.10.1' "${json}"
  run grep -E 'devcontainers/features/python' "${json}"
  [ "$status" -ne 0 ]
  run grep -E 'devcontainers/features/node' "${json}"
  [ "$status" -ne 0 ]
  run grep -E 'network=host|--network=host' "${json}"
  [ "$status" -ne 0 ]
  run grep -E '"privileged"[[:space:]]*:[[:space:]]*true' "${json}"
  [ "$status" -ne 0 ]
}

@test "devcontainer grok config sandboxes docker.sock" {
  [[ -f "${DEVCONTAINER_DIR}/grok/sandbox.toml" ]]
  [[ -f "${DEVCONTAINER_DIR}/grok/config.toml" ]]
  grep -q 'docker.sock' "${DEVCONTAINER_DIR}/grok/sandbox.toml"
  grep -q 'host.docker.internal' "${DEVCONTAINER_DIR}/grok/config.toml"
  grep -q 'inherit = "core"' "${DEVCONTAINER_DIR}/grok/config.toml"
  grep -q 'auto_update = false' "${DEVCONTAINER_DIR}/grok/config.toml"
}

@test "post-create.sh prewarms bazelisk and skips docs-site npm by default" {
  [[ -f "${DEVCONTAINER_DIR}/post-create.sh" ]]
  grep -Eq 'bazelisk (version|info)' "${DEVCONTAINER_DIR}/post-create.sh"
  grep -q 'grok --version' "${DEVCONTAINER_DIR}/post-create.sh"
  grep -q 'DEVCONTAINER_INSTALL_DOCS_SITE' "${DEVCONTAINER_DIR}/post-create.sh"
  grep -q 'python3 -m venv' "${DEVCONTAINER_DIR}/post-create.sh"
}

@test "devcontainer dockerignore is whitelist-only" {
  local di="${DEVCONTAINER_DIR}/.dockerignore"
  [[ -f ${di} ]]
  grep -qx '\*' "${di}"
  grep -q '!Dockerfile' "${di}"
  grep -q '!grok/' "${di}"
}

@test "publish-devcontainer workflow is native multi-arch GHCR only" {
  local wf="${REPO_ROOT}/.github/workflows/publish-devcontainer.yml"
  [[ -f ${wf} ]]
  grep -q 'linux/amd64' "${wf}"
  grep -q 'linux/arm64' "${wf}"
  grep -q 'ubuntu-24.04-arm' "${wf}"
  grep -q 'ez-comfy-devcontainer' "${wf}"
  grep -q 'packages: write' "${wf}"
  run grep -iE 'dockerhub|setup-qemu' "${wf}"
  [ "$status" -ne 0 ]
  run grep -E 'HF_TOKEN|API_KEY' "${wf}"
  [ "$status" -ne 0 ]
}
