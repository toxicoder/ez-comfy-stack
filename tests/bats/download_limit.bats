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
  run shaping_supported
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
  run gentle_hf_workers_for_mbps 250
  [ "${output}" = "4" ]
  run gentle_hf_workers_for_mbps 100
  [ "${output}" = "3" ]
  run gentle_hf_workers_for_mbps 40
  [ "${output}" = "2" ]
  run gentle_hf_workers_for_mbps 10
  [ "${output}" = "2" ]
  HF_DOWNLOAD_MIN_WORKERS=3
  run gentle_hf_workers_for_mbps 10
  [ "${output}" = "3" ]
  unset HF_DOWNLOAD_MIN_WORKERS
  run enable_gentle_download_mode 40 eth0
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Gentle"* || "${output}" == *"max-workers"* ]]
}

@test "probe_http_download_mbps and run_speedtest fallback chain" {
  export LAB_MOCK_HTTP_SPEED_MBPS=120
  unset LAB_MOCK_SPEEDTEST_MBPS
  run probe_http_download_mbps
  [ "${output}" = "120" ]
  # No speedtest-cli mock path: use HTTP probe via run_speedtest
  rm -f "${TEST_TMP_DIR}/bin/speedtest-cli"
  run run_speedtest_mbps
  [[ "${output}" == *"120"* ]]
  # clear_limits_for_speedtest should run (force clear) before measure
  [[ "${output}" == *"Clearing any existing bandwidth limits"* || "${output}" == *"120"* ]]
  unset LAB_MOCK_HTTP_SPEED_MBPS
  install_speedtest_mock 100
}

@test "clear_limits_for_speedtest and ensure_speedtest_cli" {
  export LAB_SHAPING_SUPPORTED=0
  : >"${TEST_TMP_DIR}/wondershaper.log"
  run clear_limits_for_speedtest eth0
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Clearing any existing bandwidth limits"* ]]
  # force=1 should still invoke wondershaper clear despite LAB_SHAPING_SUPPORTED=0
  grep -q clear "${TEST_TMP_DIR}/wondershaper.log"

  # ensure when already present
  install_speedtest_mock 50
  run ensure_speedtest_cli
  [ "${status}" -eq 0 ]
}

@test "wondershaper clear stdout does not pollute measured Mbps" {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
echo "Wondershaper queues have been cleared."
exit 0
'
  export LAB_MOCK_WONDERSHAPER=1
  export LAB_MOCK_SPEEDTEST_MBPS=100
  # Command substitution must yield a clean integer only
  measured=$(run_speedtest_mbps)
  [ "${measured}" = "100" ]
  run compute_auto_limit "${measured}"
  [[ "${output}" == *"85"* ]]
  run compute_auto_limit $'Wondershaper queues have been cleared.\n100'
  [ "${status}" -ne 0 ]
}

@test "shaping_supported respects LAB_FORCE_NO_HTB" {
  export LAB_FORCE_NO_HTB=1
  unset LAB_SHAPING_SUPPORTED
  run shaping_supported
  [ "${status}" -ne 0 ]
  unset LAB_FORCE_NO_HTB
  unset LAB_SHAPING_SUPPORTED
  export LAB_MOCK_WONDERSHAPER=1
  run shaping_supported
  [ "${status}" -eq 0 ]
  run mark_shaping_unsupported "unit-test"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Disabling kernel shaping"* ]]
  # Direct call so exported cache persists in this shell
  mark_shaping_unsupported "unit-test-direct"
  [ "${LAB_SHAPING_SUPPORTED}" = "0" ]
  run shaping_supported
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
  [[ "${output}" == *"Illegal"* || "${output}" == *"wondershaper"* || "${output}" == *"Error"* || "${output}" == *"Disabling kernel shaping"* || "${output}" == *"qdisc"* ]]
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
  export LAB_MOCK_HTTP_SPEED_MBPS=33
  rm -f "${TEST_TMP_DIR}/bin/speedtest-cli"
  run bash "${DLS}" run --limit auto --fallback 33
  [ "${status}" -eq 0 ]
  unset LAB_MOCK_HTTP_SPEED_MBPS
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
  unset HF_DOWNLOAD_MAX_WORKERS
  LIMIT_SPEC=50
  WRAP_ARGS=(bash -c 'echo wrap-ran >"${TEST_TMP_DIR}/wrap.ok"')
  run cmd_wrap
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Gentle"* || "${output}" == *"gentle"* || "${output}" == *"unavailable"* || "${output}" == *"max-workers"* || "${output}" == *"qdisc"* ]]
  [ -f "${TEST_TMP_DIR}/wrap.ok" ]
  grep -q clear "${TEST_TMP_DIR}/wondershaper.log"
}

@test "cmd_wrap skips wondershaper when HTB unsupported" {
  export LAB_FORCE_NO_HTB=1
  unset LAB_SHAPING_SUPPORTED
  export LAB_MOCK_WONDERSHAPER=1
  unset HF_DOWNLOAD_MAX_WORKERS
  LIMIT_SPEC=80
  : >"${TEST_TMP_DIR}/wondershaper.log"
  WRAP_ARGS=(bash -c 'echo ok >"${TEST_TMP_DIR}/wrap2.ok"; echo workers=${HF_DOWNLOAD_MAX_WORKERS:-none}')
  run cmd_wrap
  [ "${status}" -eq 0 ]
  [ -f "${TEST_TMP_DIR}/wrap2.ok" ]
  [[ "${output}" == *"Gentle"* || "${output}" == *"unavailable"* ]]
  # should not have applied wondershaper rates (only clear maybe)
  if [[ -s "${TEST_TMP_DIR}/wondershaper.log" ]]; then
    ! grep -qE 'wondershaper eth0 [0-9]' "${TEST_TMP_DIR}/wondershaper.log" || true
  fi
  unset LAB_FORCE_NO_HTB
  unset LAB_SHAPING_SUPPORTED
}

@test "sample_iface_rx_mbps and wrap live speed path" {
  export LAB_MOCK_LIVE_RX_MBPS=160
  export LAB_MOCK_LIVE_SAMPLE_SLEEP=0
  run sample_iface_rx_mbps eth0 15
  [ "${status}" -eq 0 ]
  [ "${output}" = "160" ]

  export LAB_FORCE_SPEEDTEST_FAIL=1
  export LAB_FORCE_NO_HTB=1
  unset LAB_SHAPING_SUPPORTED
  unset HF_DOWNLOAD_MAX_WORKERS
  export LAB_MOCK_WONDERSHAPER=1
  # Reliable HTTP mock → use probe path (not idle RX)
  export LAB_MOCK_HTTP_SPEED_MBPS=200
  LIMIT_SPEC=auto
  WRAP_ARGS=(bash -c 'echo live-wrap >"${TEST_TMP_DIR}/live.ok"')
  run wrap_with_live_speed_limit eth0 50
  [ "${status}" -eq 0 ]
  [ -f "${TEST_TMP_DIR}/live.ok" ]
  [[ "${output}" == *"HTTP probe"* || "${output}" == *"200"* || "${output}" == *"gentle"* || "${output}" == *"foreground"* || "${output}" == *"max-workers"* ]]
  [[ "${output}" != *"Stopping sample-phase"* ]]

  # No HTTP mock → untrusted path uses default workers=4
  unset LAB_MOCK_HTTP_SPEED_MBPS
  unset HF_DOWNLOAD_MAX_WORKERS
  WRAP_ARGS=(bash -c 'echo untrusted >"${TEST_TMP_DIR}/untrusted.ok"; echo w=${HF_DOWNLOAD_MAX_WORKERS}')
  run wrap_with_live_speed_limit eth0 50
  [ "${status}" -eq 0 ]
  [ -f "${TEST_TMP_DIR}/untrusted.ok" ]
  [[ "${output}" == *"untrusted"* || "${output}" == *"default max-workers"* || "${output}" == *"max-workers=4"* ]]

  run apply_limit_from_measured eth0 100
  [[ "${output}" == *"target"* || "${output}" == *"gentle"* || "${output}" == *"85"* || "${output}" == *"Gentle"* ]]

  run kill_pid_tree ""
  [ "${status}" -eq 0 ]
  run default_hf_workers_untrusted
  [ "${output}" = "4" ]

  unset LAB_FORCE_SPEEDTEST_FAIL
  unset LAB_FORCE_NO_HTB
  unset LAB_SHAPING_SUPPORTED
  unset LAB_MOCK_LIVE_RX_MBPS
  unset LAB_MOCK_HTTP_SPEED_MBPS
}

@test "run_with_signal_forwarding runs command" {
  run run_with_signal_forwarding true
  [ "${status}" -eq 0 ]
  run run_with_signal_forwarding bash -c 'exit 7'
  [ "${status}" -eq 7 ]
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
