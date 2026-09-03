#!/usr/bin/env bats
#
# ## safety.bats
#
# Purpose:
#   Static and runtime safety invariants: compose restart no, mem_limit, MODELS_DIR default, heavy confirm, resource-policy.
#
# Hermetic:
#   Uses test_helper mocks; no GPU, sudo, or network required.
#

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "compose restart is no" {
  run grep -E 'restart:.*"no"' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
}

@test "Dockerfile defaults to public Docker Hub CUDA base not nvcr" {
  run grep -E 'ARG CUDA_BASE_IMAGE=nvidia/cuda:.*devel' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  run grep -E 'ARG CUDA_RUNTIME_IMAGE=nvidia/cuda:.*runtime' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  run grep -E 'FROM \$\{CUDA_BASE_IMAGE\}' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  run grep -E 'FROM \$\{CUDA_RUNTIME_IMAGE\}' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  # Multi-stage: builder prebuilds, runtime is the published stage
  run grep -E 'AS builder|AS runtime' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  # Hardcoded FROM nvcr.io as sole base would re-break unauthenticated builds
  run grep -E '^FROM nvcr\.io/' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -ne 0 ]
  run grep -E 'CUDA_BASE_IMAGE' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
  run grep -E 'CUDA_RUNTIME_IMAGE' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
}

@test "Dockerfile runtime installs gcc g++ for Triton JIT" {
  local df="${REPO_ROOT}/docker/Dockerfile"
  # Runtime stage must ship CC + Python.h (Torch 2.13 Triton cuda_utils JIT)
  run awk '
    /^FROM .* AS runtime/ { in_rt=1; next }
    in_rt && /^FROM / { in_rt=0 }
    in_rt { print }
  ' "${df}"
  [ "$status" -eq 0 ]
  [[ "${output}" == *gcc* ]]
  [[ "${output}" == *g++* || "${output}" == *g\+\+* || "${output}" == *"g++"* ]]
  [[ "${output}" == *python3-dev* ]]
  [[ "${output}" == *pythonpath* ]]
  # Guard against re-slimming away the compiler/headers without replacement
  run grep -E 'Triton|C compiler|Failed to find C compiler|Python\.h' "${df}"
  [ "$status" -eq 0 ]
}

@test "dockerignore allowlists pythonpath for runtime COPY" {
  local di="${REPO_ROOT}/docker/.dockerignore"
  [[ -f ${di} ]]
  # Whitelist-only context: without these lines, COPY pythonpath/ fails at build
  run grep -E '^!pythonpath/' "${di}"
  [ "$status" -eq 0 ]
  run grep -E '^!pythonpath/\*\*' "${di}"
  [ "$status" -eq 0 ]
  [[ -f ${REPO_ROOT}/docker/pythonpath/sitecustomize.py ]]
}

@test "Dockerfile layer order keeps multi-GB prebuild cache stable" {
  local df="${REPO_ROOT}/docker/Dockerfile"
  # BuildKit syntax for COPY --chmod and cache mounts
  run grep -E '^# syntax=docker/dockerfile' "${df}"
  [ "$status" -eq 0 ]
  run grep -E 'mount=type=cache,target=/root/\.cache/pip' "${df}"
  [ "$status" -eq 0 ]
  # Phased module sources (not monolithic install-comfy.sh before torch)
  run grep -E 'phase-venv-torch\.sh|phase_venv|phase_torch' "${df}"
  [ "$status" -eq 0 ]
  run grep -E 'phase-comfy\.sh|phase_comfy' "${df}"
  [ "$status" -eq 0 ]
  run grep -E 'phase-nodes\.sh|phase_nodes' "${df}"
  [ "$status" -eq 0 ]

  # Builder: first COPY is phase modules only (not entrypoint/patch/orchestrator)
  run awk '/^COPY /{print; exit}' "${df}"
  [ "$status" -eq 0 ]
  [[ "${output}" == *phase-venv-torch* || "${output}" == *install-comfy/common* ]]
  [[ "${output}" != *entrypoint* ]]
  [[ "${output}" != *patch_get_free_memory* ]]
  [[ "${output}" != *install-comfy.sh* ]]

  # Runtime: split parts COPY (venv then app) before entrypoint
  local venv_line app_line entry_line
  venv_line="$(grep -n 'COPY --from=builder /opt/parts/venv' "${df}" | head -1 | cut -d: -f1)"
  app_line="$(grep -n 'COPY --from=builder /opt/parts/app' "${df}" | head -1 | cut -d: -f1)"
  entry_line="$(grep -n 'COPY.*entrypoint\.sh' "${df}" | head -1 | cut -d: -f1)"
  [ -n "${venv_line}" ]
  [ -n "${app_line}" ]
  [ -n "${entry_line}" ]
  [ "${venv_line}" -lt "${app_line}" ]
  [ "${app_line}" -lt "${entry_line}" ]

  # Validated non-empty default pins
  run grep -E 'ARG COMFYUI_REF=v0\.' "${df}"
  [ "$status" -eq 0 ]
  run grep -E 'ARG COMFYUI_MANAGER_REF=' "${df}"
  [ "$status" -eq 0 ]
  run grep -E 'ARG COMFYUI_NUNCHAKU_NODE_REF=v' "${df}"
  [ "$status" -eq 0 ]
  # VideoHelperSuite pin surface + runtime ffmpeg for VHS
  run grep -E 'ARG COMFYUI_VHS_REF=' "${df}"
  [ "$status" -eq 0 ]
  run grep -E '^\s*ffmpeg\s*$|ffmpeg \\' "${df}"
  [ "$status" -eq 0 ]
}

@test "compose bind-mounts ops scripts for zero-rebuild iteration" {
  local compose="${REPO_ROOT}/docker/docker-compose.yml"
  local ref_count
  run grep -E 'entrypoint\.sh:/opt/ez-comfy/entrypoint\.sh' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'install-comfy\.sh:/opt/ez-comfy/install-comfy\.sh' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'install-comfy:/opt/ez-comfy/install-comfy' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'patch_get_free_memory\.py:/opt/ez-comfy/patch_get_free_memory\.py' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'pythonpath:/opt/ez-comfy/pythonpath' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'LAB_DISABLE_TORCH_NATIVE_TRITON' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'cache_from:' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'COMFYUI_REF:.*v0\.' "${compose}"
  [ "$status" -eq 0 ]
  # Build-arg AND runtime env (stamp-present pin refresh on the named volume)
  ref_count="$(grep -cE 'COMFYUI_REF:' "${compose}" || true)"
  [ "${ref_count}" -ge 2 ]
}

@test "workflow mount is outside COMFY_HOME tree" {
  # Host workflows/ tree → image path (not under comfy-state volume)
  run grep -E 'workflows:/opt/ez-comfy/workflows' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
  run grep -E 'workflows:.*/comfy-state/ComfyUI/' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -ne 0 ]
}

@test "prompt-enhance nodes mount outside COMFY_HOME and no xAI key" {
  local compose="${REPO_ROOT}/docker/docker-compose.yml"
  run grep -E 'custom_nodes:/opt/ez-comfy/custom_nodes' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'custom_nodes:.*/comfy-state/ComfyUI/' "${compose}"
  [ "$status" -ne 0 ]
  run grep -E 'XAI_API_KEY:' "${compose}"
  [ "$status" -ne 0 ]
  run grep -E 'EZ_LLM_GGUF:' "${compose}"
  [ "$status" -eq 0 ]
  run grep -iE '^(ENV|ARG).*XAI_API_KEY' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -ne 0 ]
}

@test "compose bind-mounts generated media to host COMFY_OUTPUT_DIR" {
  local compose="${REPO_ROOT}/docker/docker-compose.yml"
  run grep -F 'COMFY_OUTPUT_DIR:-/mnt/comfy-output}:/outputs' "${compose}"
  [ "$status" -eq 0 ]
  run grep -E 'output-directory|/outputs' "${REPO_ROOT}/docker/entrypoint.sh"
  [ "$status" -eq 0 ]
  run grep -E 'down -v' "${REPO_ROOT}/scripts/lib/compose.sh"
  [ "$status" -eq 0 ]
  run grep -E 'COMFY_OUTPUT_DIR are NOT deleted' "${REPO_ROOT}/scripts/lib/compose.sh"
  [ "$status" -eq 0 ]
}

@test "prebuilt image defaults to GHCR and never bakes HF_TOKEN in Dockerfile" {
  run grep -E 'ghcr.io/.*/ez-comfy:us-safe-studio' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
  run grep -E 'comfy-prebuilt|EZ_COMFY_PREBUILD' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -eq 0 ]
  # Secrets must not appear as Dockerfile ENV/ARG assignments
  run grep -iE '^(ENV|ARG).*HF_TOKEN|^(ENV|ARG).*API_KEY|COPY.*\.env' "${REPO_ROOT}/docker/Dockerfile"
  [ "$status" -ne 0 ]
  run grep -E 'ghcr.io' "${REPO_ROOT}/.github/workflows/publish-image.yml"
  [ "$status" -eq 0 ]
  run grep -iE 'dockerhub|docker\.io/.*push|DOCKERHUB' "${REPO_ROOT}/.github/workflows/publish-image.yml"
  [ "$status" -ne 0 ]
  # Publish uses Buildx GHA cache (faster rebuilds)
  run grep -E 'cache-from:.*type=gha|cache-to:.*type=gha' "${REPO_ROOT}/.github/workflows/publish-image.yml"
  [ "$status" -eq 0 ]
}

@test "compose has mem_limit" {
  run grep -E 'mem_limit' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
}

@test "compose does not use restart always" {
  run grep -E 'restart:.*always' "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -ne 0 ]
}

@test "default MODELS_DIR is /mnt/models" {
  run grep -E '/mnt/models' "${REPO_ROOT}/.env.example"
  [ "$status" -eq 0 ]
  run grep -E 'MODELS_DIR:-/mnt/models|MODELS_DIR:-"/mnt/models"' \
    "${REPO_ROOT}/scripts/manage.sh" \
    "${REPO_ROOT}/scripts/utilities/download-image.sh" \
    "${REPO_ROOT}/docker/docker-compose.yml"
  [ "$status" -eq 0 ]
}

@test "heavy confirm present in manage start" {
  run grep -n 'require_heavy_confirm' "${REPO_ROOT}/scripts/manage.sh"
  [ "$status" -eq 0 ]
}

@test "parse_gib_from_mem_limit" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  run parse_gib_from_mem_limit 90g
  [ "$output" = "90" ]
  run parse_gib_from_mem_limit 2048m
  [ "$output" = "2" ]
}

@test "check_host_headroom fails when low" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  export LAB_MOCK_FREE_MEM_GIB=1
  export LAB_MOCK_DISK_FREE_GIB=100
  export MIN_HOST_FREE_GIB=28
  run check_host_headroom
  [ "$status" -ne 0 ]
}

@test "check_host_headroom ok when high" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export MIN_HOST_FREE_GIB=28
  run check_host_headroom
  [ "$status" -eq 0 ]
}

@test "require_heavy_confirm noninteractive" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/common.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/safety.sh"
  export LAB_NON_INTERACTIVE=1
  export LAB_CONFIRM_TOKEN=yes
  run require_heavy_confirm "test"
  [ "$status" -eq 0 ]
  export LAB_CONFIRM_TOKEN=
  run require_heavy_confirm "test"
  [ "$status" -eq 1 ]
}

@test "paths helpers" {
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  export REPO_ROOT
  run lab_repo_root
  [ "$status" -eq 0 ]
  [[ "$output" == *"ez-comfy-stack"* ]]
  run lab_models_dir
  [ "$status" -eq 0 ]
}

@test "resource policy documents studio memory limits" {
  run grep -E 'studio|flux-to-ltx|90g' "${REPO_ROOT}/config/resource-policy.yaml"
  [ "$status" -eq 0 ]
}
