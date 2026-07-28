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
    "${REPO_ROOT}/scripts/utilities/download-flux.sh" \
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

@test "resource policy documents flux-to-ltx" {
  run grep -E 'flux-to-ltx|90g' "${REPO_ROOT}/config/resource-policy.yaml"
  [ "$status" -eq 0 ]
}
