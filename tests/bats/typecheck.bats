#!/usr/bin/env bats
#
# ## typecheck.bats
#
# Purpose:
#   Contract for the hermetic Pyright (Pylance) + mypy gate: runner, Makefile,
#   test entrypoints, config include lists, pinned tools, and agent finish-with
#   docs.
#
# Hermetic:
#   File/content assertions only. Does not install or invoke Pyright or mypy.
#

load 'test_helper'

setup() {
  setup_repo_env
}

teardown() {
  teardown_repo_env
}

@test "typecheck runner exists and names Pyright" {
  local script="${REPO_ROOT}/tests/typecheck.sh"
  [ -f "${script}" ]
  run grep -F 'python3 -m pyright' "${script}"
  [ "${status}" -eq 0 ]
  run grep -i 'Pyright' "${script}"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/requirements.txt' "${script}"
  [ "${status}" -eq 0 ]
}

@test "typecheck runner names mypy helpers" {
  local script="${REPO_ROOT}/tests/typecheck.sh"
  [ -f "${script}" ]
  run grep -F 'python3 -m mypy' "${script}"
  [ "${status}" -eq 0 ]
  run grep -F 'require_mypy' "${script}"
  [ "${status}" -eq 0 ]
  run grep -F 'run_mypy' "${script}"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/requirements.txt' "${script}"
  [ "${status}" -eq 0 ]
}

@test "Makefile typecheck and lint invoke tests/typecheck.sh" {
  local mk="${REPO_ROOT}/Makefile"
  run grep -E '^typecheck:' "${mk}"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/typecheck.sh' "${mk}"
  [ "${status}" -eq 0 ]
  awk '/^lint:/{p=1; next} p && /^[^[:space:]#]/{exit} p' "${mk}" | grep -F 'tests/typecheck.sh'
}

@test "Makefile typecheck help names mypy" {
  local mk="${REPO_ROOT}/Makefile"
  run grep -i 'mypy' "${mk}"
  [ "${status}" -eq 0 ]
}

@test "run_all and coverage invoke typecheck" {
  run grep -F 'tests/typecheck.sh' "${REPO_ROOT}/tests/run_all.sh"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/typecheck.sh' "${REPO_ROOT}/tests/coverage.sh"
  [ "${status}" -eq 0 ]
  run grep -i 'mypy' "${REPO_ROOT}/tests/run_all.sh"
  [ "${status}" -eq 0 ]
  run grep -i 'mypy' "${REPO_ROOT}/tests/coverage.sh"
  [ "${status}" -eq 0 ]
}

@test "pyrightconfig includes first-party Python roots" {
  local cfg="${REPO_ROOT}/pyrightconfig.json"
  [ -f "${cfg}" ]
  run grep -F 'custom_nodes' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'docker' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'scripts/lib' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/python' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F '"typeCheckingMode": "standard"' "${cfg}"
  [ "${status}" -eq 0 ]
}

@test "mypy.ini includes first-party Python roots" {
  local cfg="${REPO_ROOT}/mypy.ini"
  [ -f "${cfg}" ]
  run grep -F 'custom_nodes' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'docker' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'scripts/lib' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'tests/python' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'studio-ui' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'ignore_missing_imports' "${cfg}"
  [ "${status}" -eq 0 ]
  run grep -F 'check_untyped_defs' "${cfg}"
  [ "${status}" -eq 0 ]
}

@test "requirements pin mypy" {
  run grep -E '^mypy==' "${REPO_ROOT}/tests/requirements.txt"
  [ "${status}" -eq 0 ]
}

@test "AGENTS.md finish-with requires Pyright (Pylance) and mypy" {
  local agents="${REPO_ROOT}/AGENTS.md"
  run grep -F 'make lint' "${agents}"
  [ "${status}" -eq 0 ]
  run grep -E 'Pyright|Pylance' "${agents}"
  [ "${status}" -eq 0 ]
  run grep -i 'mypy' "${agents}"
  [ "${status}" -eq 0 ]
}
