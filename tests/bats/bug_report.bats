#!/usr/bin/env bats
#
# Hermetic tests for scripts/lib/bug_report.sh: the CLI and bazelisk bug
# handoff. Nothing here touches the network, docker, or a GPU - the library
# only probes, writes one file under a temp dir, and builds a URL string.

load 'test_helper'

setup() {
  setup_repo_env
  BUG_LIB="${REPO_ROOT}/scripts/lib/bug_report.sh"
  REPORT_DIR="${BATS_TEST_TMPDIR}/bug-reports"
  # Probe timeouts would otherwise slow every case; the probes still run.
  export BUG_REPORT_PROBE_TIMEOUT=2
  export EZ_BUG_REPORT_DIR="${REPORT_DIR}"
}

teardown() {
  teardown_repo_env
}

# Source the library inside a fresh bash so set -u and function visibility
# match how manage.sh and common.sh actually load it.
lib_bash() {
  bash -c "source '${BUG_LIB}'; $1"
}

@test "bug_report_markdown carries every pack heading in pack order" {
  run lib_bash 'bug_report_markdown "t" "cli" "manage.sh start" 1'
  [ "${status}" -eq 0 ]
  local heading line prev=0
  for heading in '## What happened' '## Steps' '## Expected' '## Actual' '## Environment'; do
    line="$(printf '%s\n' "${output}" | grep -n -F -x -- "${heading}" | head -n 1 | cut -d: -f1)"
    [ -n "${line}" ]
    [ "${line}" -gt "${prev}" ]
    prev="${line}"
  done
}

@test "bug_report_markdown fills Steps with the command and Actual with the status" {
  run lib_bash 'bug_report_markdown "t" "bazel" "bazelisk test //:test-all" 7'
  [ "${status}" -eq 0 ]
  [[ ${output} == *'bazelisk test //:test-all'* ]]
  [[ ${output} == *'exited with status 7'* ]]
}

@test "bug_report_markdown leaves operator prose as the pack fill-in marker" {
  run lib_bash 'bug_report_markdown "t" "cli" "x" 1'
  [ "${status}" -eq 0 ]
  [[ ${output} == *'<!-- Replace this line. -->'* ]]
}

@test "bug_report_markdown omits Command output when no log was given" {
  run lib_bash 'bug_report_markdown "t" "cli" "x" 1'
  [ "${status}" -eq 0 ]
  [[ ${output} != *'## Command output'* ]]
}

@test "bug_report_markdown attaches a bounded, fenced log tail" {
  local log="${BATS_TEST_TMPDIR}/gate.log"
  local i
  : > "${log}"
  for i in $(seq 1 300); do
    printf 'line %s\n' "${i}" >> "${log}"
  done
  run lib_bash "BUG_REPORT_LOG_TAIL=5 bug_report_markdown 't' 'bazel' 'x' 1 '${log}'"
  [ "${status}" -eq 0 ]
  [[ ${output} == *'## Command output'* ]]
  [[ ${output} == *'line 300'* ]]
  [[ ${output} != *'line 294'* ]]
  [[ ${output} == *'```'* ]]
}

@test "bug_report_markdown skips an unreadable log instead of failing" {
  run lib_bash "bug_report_markdown 't' 'cli' 'x' 1 '${BATS_TEST_TMPDIR}/nope.log'"
  [ "${status}" -eq 0 ]
  [[ ${output} != *'## Command output'* ]]
}

@test "bug_report_env_block redacts tokens and the home directory" {
  run lib_bash 'HOME=/home/operator bug_report_env_block cli'
  [ "${status}" -eq 0 ]
  [[ ${output} == *'- surface: cli'* ]]
  [[ ${output} == *'os:'* ]]
  [[ ${output} != *'/home/operator'* ]]
}

@test "bug_report_redact hides token-shaped secrets from every provider" {
  run lib_bash "HOME=/home/operator bug_report_redact 'a ghp_ABCDEF123456 b github_pat_abcdefghijklmnop c hf_ZZZZZZZZZZZZZZ d /home/operator/models'"
  [ "${status}" -eq 0 ]
  [[ ${output} == *'ghp_'* ]] && return 1
  [[ ${output} == *'github_pat_'* ]] && return 1
  [[ ${output} == *'hf_ZZZZ'* ]] && return 1
  [[ ${output} == *'~/models'* ]]
  [[ ${output} == *'[redacted]'* ]]
}

@test "bug_report_title prefixes the surface and respects a supplied prefix" {
  run lib_bash 'bug_report_title "boom" "bazel"'
  [ "${status}" -eq 0 ]
  [ "${output}" = "[cli:bazel] boom" ]

  run lib_bash 'bug_report_title "[app:stills/x] boom" "cli"'
  [ "${status}" -eq 0 ]
  [ "${output}" = "[app:stills/x] boom" ]
}

@test "bug_report_url percent-encodes and points at the repo issues form" {
  run lib_bash 'bug_report_url "[cli:cli] a title & more" "## What happened

body text" "bug"'
  [ "${status}" -eq 0 ]
  [[ ${output} == 'https://github.com/'*'/issues/new?'* ]]
  [[ ${output} == *'title=%5Bcli%3Acli%5D'* ]]
  [[ ${output} == *'labels=bug'* ]]
  [[ ${output} == *'%23%23+What+happened'* ]]
}

@test "bug_report_url clamps to BUG_REPORT_MAX_HREF on a line boundary" {
  local body
  body="$(lib_bash 'bug_report_markdown t cli x 1')"
  [ -n "${body}" ]
  [ "${#body}" -gt 400 ]
  export BODY="${body}"
  run bash -c "source '${BUG_LIB}'; BUG_REPORT_MAX_HREF=300 bug_report_url '[cli:cli] t' \"\${BODY}\" bug"
  [ "${status}" -eq 0 ]
  [[ ${output} == *'body='* ]]
  [ "${#output}" -le 300 ]
  [[ ${output} == *'shortened+to+fit+the+URL'* ]]
}

@test "bug_report_url keeps title and labels when python3 is unavailable" {
  run lib_bash 'command() { if [[ "${2:-}" == "python3" ]]; then return 1; fi; builtin command "$@"; }; bug_report_url "[cli:cli] plain" "ignored body" bug'
  [ "${status}" -eq 0 ]
  [[ ${output} == 'https://github.com/'*'/issues/new?title='* ]]
  [[ ${output} == *'labels=bug'* ]]
  [[ ${output} != *'body='* ]]
}

@test "bug_report_write saves a 0600 file with a slugged name" {
  run lib_bash 'bug_report_write "body text" "Disk Wizard: Docker Size Parse Broken!"'
  [ "${status}" -eq 0 ]
  local saved="${output}"
  [ -f "${saved}" ]
  [[ ${saved} == "${REPORT_DIR}/"* ]]
  [[ ${saved##*/} == *'-disk-wizard-docker-size-parse-broken'* ]]
  run stat -c '%a' "${saved}"
  [ "${output}" = "600" ]
}

@test "bug_report_write falls back to a plain slug for an empty title" {
  run lib_bash 'bug_report_write "body" ""'
  [ "${status}" -eq 0 ]
  [ -f "${output}" ]
  [[ ${output} == *'-bug-report.md' ]]
}

@test "bug_report_enabled is silent under bats even with stderr free" {
  run lib_bash 'BATS_TEST_FILENAME=/tmp/x.bats bug_report_enabled && echo ON || echo OFF'
  [ "${status}" -eq 0 ]
  [ "${output}" = "OFF" ]
}

@test "bug_report_enabled honours the explicit switch" {
  run env -u BATS_TEST_FILENAME -u BATS_RUN_TMPDIR EZ_BUG_HINT=1 \
    bash -c "source '${BUG_LIB}'; bug_report_enabled && echo ON || echo OFF"
  [ "${status}" -eq 0 ]
  [ "${output}" = "ON" ]

  run lib_bash 'EZ_BUG_HINT=0 bug_report_enabled && echo ON || echo OFF'
  [ "${status}" -eq 0 ]
  [ "${output}" = "OFF" ]
}

@test "bug_report_hint prints the four handoff lines when forced on" {
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint cli "manage.sh start" 1 2>&1 >/dev/null'
  [ "${status}" -eq 0 ]
  [[ ${output} == *'[ez-comfy][BUG] Template saved:'* ]]
  [[ ${output} == *'Open on GitHub:'* ]]
  [[ ${output} == *'bazelisk run //:manage -- report-bug'* ]]
}

@test "bug_report_hint prints nothing when EZ_BUG_HINT is off" {
  run lib_bash 'EZ_BUG_HINT=0 bug_report_hint cli "manage.sh start" 1 2>&1'
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "bug_report_hint never writes to stdout and always returns 0" {
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint "cli" "x" 1 2>/dev/null'
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
}

@test "bug_report_hint survives garbage arguments" {
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint "" "" 999 2>&1'
  [ "${status}" -eq 0 ]
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint 2>&1'
  [ "${status}" -eq 0 ]
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint cli "cmd" "not-a-number" 2>&1'
  [ "${status}" -eq 0 ]
}

@test "bug_report_hint works with set -e active in the caller" {
  run bash -c "set -euo pipefail; source '${BUG_LIB}'; EZ_BUG_HINT=1 bug_report_hint cli 'manage.sh start' 1 >/dev/null 2>&1; echo SURVIVED"
  [ "${status}" -eq 0 ]
  [ "${output}" = "SURVIVED" ]
}

@test "bug_report_hint writes the template it points at" {
  run lib_bash 'EZ_BUG_HINT=1 bug_report_hint bazel "bazelisk test //:validate" 1 2>&1 >/dev/null'
  [ "${status}" -eq 0 ]
  local saved
  saved="$(printf '%s\n' "${output}" | sed -n 's/.*Template saved: //p' | head -n 1)"
  [ -n "${saved}" ]
  [ -f "${saved}" ]
  run cat "${saved}"
  [[ ${output} == *'bazelisk test //:validate'* ]]
  [[ ${output} == *'## Environment'* ]]
}
