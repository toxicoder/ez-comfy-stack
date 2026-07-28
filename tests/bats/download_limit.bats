#!/usr/bin/env bats
#
# ## download_limit.bats
#
# Purpose:
#   Cover every function in scripts/utilities/download-limit.sh (strict inventory).
#
# Hermetic:
#   Mocks for wondershaper, speedtest, iface; LAB_NO_SUDO=1.
#

load 'test_helper'

setup() {
  setup_repo_env
  install_wondershaper_mock
  install_speedtest_mock 100
  export DLS="${UTILITIES_DIR}/download-limit.sh"
  chmod +x "${DLS}"
  # shellcheck disable=SC1090
  source "${DLS}"
}

teardown() {
  teardown_repo_env
}

@test "download-limit CLI help status text json errors" {
  run bash "${DLS}" --help
  [ "${status}" -eq 0 ]
  run bash "${DLS}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"interface"* ]]
  run bash "${DLS}" status
  [ "${status}" -eq 0 ]
  run bash "${DLS}" run
  [ "${status}" -ne 0 ]
  run bash "${DLS}" run --limit nope
  [ "${status}" -ne 0 ]
  run bash "${DLS}" wrap --limit 10
  [ "${status}" -ne 0 ]
  run bash "${DLS}" status --bogus
  [ "${status}" -ne 0 ]
}

@test "download-limit helpers iface wondershaper limits speedtest auto" {
  run dl_log "x"
  [ "${status}" -eq 0 ]
  run dl_warn "y"
  [ "${status}" -eq 0 ]
  run dl_err "z"
  [ "${status}" -eq 0 ]

  run get_active_interface
  [ "${output}" = "eth0" ]
  run check_wondershaper
  [ "${status}" -eq 0 ]
  run ensure_wondershaper
  [ "${status}" -eq 0 ]
  run sudo_wondershaper clear eth0
  [ "${status}" -eq 0 ]
  run clear_limits eth0
  [ "${status}" -eq 0 ]
  run load_shaping_modules
  [ "${status}" -eq 0 ]
  run apply_limits eth0 40
  [ "${status}" -eq 0 ]

  export LAB_MOCK_SPEEDTEST_MBPS=100
  run run_speedtest_mbps
  # bats $output merges stderr (log lines) with stdout
  [[ "${output}" == *"100"* ]]
  run compute_auto_limit 200
  [[ "${output}" == *"170"* ]]
  run resolve_limit_mbps auto
  [[ "${output}" == *"85"* ]]
  run resolve_limit_mbps 50
  [[ "${output}" == *"50"* ]]
  run resolve_limit_mbps bad
  [ "${status}" -ne 0 ]
}

@test "clamp_rate_kbps clamps min max and passthrough" {
  run clamp_rate_kbps 4
  [ "${output}" = "8" ]
  run clamp_rate_kbps 100000000
  [ "${output}" = "10000000" ]
  run clamp_rate_kbps 50000
  [ "${output}" = "50000" ]
}

@test "limits_active respects LAB_MOCK_LIMITS_ACTIVE and mock wondershaper" {
  export LAB_MOCK_LIMITS_ACTIVE=0
  run limits_active eth0
  [ "${status}" -ne 0 ]
  export LAB_MOCK_LIMITS_ACTIVE=1
  run limits_active eth0
  [ "${status}" -eq 0 ]
  unset LAB_MOCK_LIMITS_ACTIVE
  export LAB_MOCK_WONDERSHAPER=1
  run limits_active eth0
  [ "${status}" -eq 0 ]
  run limits_active ""
  [ "${status}" -ne 0 ]
}

@test "apply_limits fails when wondershaper prints Illegal rate" {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
if [[ "$*" == clear* ]]; then exit 0; fi
echo "Error: Specified qdisc kind is unknown."
echo "Illegal \"rate\""
exit 0
'
  unset LAB_MOCK_LIMITS_ACTIVE
  # Force real verification path off mock-always-active when output has errors
  export LAB_MOCK_WONDERSHAPER=1
  run apply_limits eth0 50
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Illegal"* || "${output}" == *"wondershaper reported"* || "${output}" == *"Error"* ]]
}

@test "apply_limits fails when limits_active is false after apply" {
  install_wondershaper_mock
  export LAB_MOCK_WONDERSHAPER=1
  export LAB_MOCK_LIMITS_ACTIVE=0
  run apply_limits eth0 50
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"not active"* || "${output}" == *"Bandwidth limit"* ]]
  unset LAB_MOCK_LIMITS_ACTIVE
}

@test "download-limit parse_args cmd_status cmd_run cmd_clear cmd_wrap" {
  parse_args status --json
  [ "${CMD}" = "status" ]
  [ "${JSON_FLAG}" -eq 1 ]
  parse_args run --limit 40 --fallback 10
  [ "${LIMIT_SPEC}" = "40" ]
  [ "${FALLBACK_MBPS}" = "10" ]

  run cmd_status
  [ "${status}" -eq 0 ]
  LIMIT_SPEC=40
  run cmd_run
  [ "${status}" -eq 0 ]
  run cmd_clear
  [ "${status}" -eq 0 ]

  LIMIT_SPEC=auto
  export LAB_MOCK_SPEEDTEST_MBPS=80
  WRAP_ARGS=(true)
  run cmd_wrap
  [ "${status}" -eq 0 ]
  grep -q clear "${TEST_TMP_DIR}/wondershaper.log"

  run bash "${DLS}" run --limit 40
  [ "${status}" -eq 0 ]
  run bash "${DLS}" clear
  [ "${status}" -eq 0 ]
  unset LAB_MOCK_SPEEDTEST_MBPS
  rm -f "${TEST_TMP_DIR}/bin/speedtest-cli"
  run bash "${DLS}" run --limit auto --fallback 33
  [ "${status}" -eq 0 ]
}

@test "cmd_wrap soft-fails and still runs command when apply fails" {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
if [[ "$*" == clear* ]]; then exit 0; fi
echo "Error: Specified qdisc kind is unknown."
exit 0
'
  export LAB_MOCK_WONDERSHAPER=1
  unset DOWNLOAD_LIMIT_REQUIRE
  LIMIT_SPEC=50
  WRAP_ARGS=(bash -c 'echo wrap-ran >"${TEST_TMP_DIR}/wrap.ok"')
  run cmd_wrap
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"unthrottled"* || "${output}" == *"Could not apply"* ]]
  [ -f "${TEST_TMP_DIR}/wrap.ok" ]
  grep -q clear "${TEST_TMP_DIR}/wondershaper.log"
}

@test "cmd_wrap hard-fails when DOWNLOAD_LIMIT_REQUIRE=1 and apply fails" {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
if [[ "$*" == clear* ]]; then exit 0; fi
echo "Error: Specified qdisc kind is unknown."
exit 0
'
  export LAB_MOCK_WONDERSHAPER=1
  export DOWNLOAD_LIMIT_REQUIRE=1
  LIMIT_SPEC=50
  WRAP_ARGS=(true)
  run cmd_wrap
  [ "${status}" -ne 0 ]
  unset DOWNLOAD_LIMIT_REQUIRE
}

@test "cmd_run hard-fails when apply fails" {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
if [[ "$*" == clear* ]]; then exit 0; fi
echo "Illegal \"rate\""
exit 0
'
  export LAB_MOCK_WONDERSHAPER=1
  LIMIT_SPEC=50
  run cmd_run
  [ "${status}" -ne 0 ]
}
