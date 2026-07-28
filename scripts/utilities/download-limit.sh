#!/usr/bin/env bash
#
# ## download-limit
#
# Limit host download bandwidth so multi‑GB model pulls cannot starve remote SSH.
#
# Purpose:
#   Apply kernel traffic shaping via wondershaper on the default-route interface.
#   Supports fixed Mbps caps and an **auto** mode that runs a speedtest and applies
#   floor(0.85 × measured_download_mbps). Apply is verified via tc qdisc (or mocks).
#   The wrap subcommand always clears limits on EXIT/INT/TERM so a killed download
#   cannot leave the host permanently throttled. If apply fails, wrap soft-fails
#   (warn + continue unthrottled) unless DOWNLOAD_LIMIT_REQUIRE=1.
#
# Audience:
#   Operators on remotely managed DGX Spark nodes; also invoked by manage.sh
#   download-models.
#
# Usage:
#   download-limit.sh status [--json]
#   download-limit.sh run --limit auto|N [--fallback N]
#   download-limit.sh clear
#   download-limit.sh wrap --limit auto|N -- <command...>
#
# Requirements:
#   - sudo (unless LAB_NO_SUDO=1 for mocks)
#   - wondershaper (best-effort auto-install on apt/dnf/pacman)
#   - HTB/sch_* kernel modules for real shaping
#   - speedtest-cli or Ookla speedtest for auto mode (optional with fallback)
#
# Test hooks:
#   LAB_MOCK_IFACE, LAB_MOCK_WONDERSHAPER, LAB_MOCK_SPEEDTEST_MBPS,
#   LAB_MOCK_LIMITS_ACTIVE, LAB_NO_SUDO, DOWNLOAD_LIMIT_REQUIRE
#
# Units:
#   Limits are megabits per second (Mbps), not MB/s. 40 Mbps ≈ 5 MB/s.
#   Wondershaper rates are clamped to a legal HTB kbps range.
#
# Exit codes:
#   0 success (or wrap soft-fail with command success); 1 invalid args,
#   missing interface, or hard apply failure (run / REQUIRE wrap).
#
# @command download-limit

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

readonly AUTO_FRACTION="0.85"
readonly BANDWIDTH_UNIT_MULTIPLIER=1000
# High-but-legal "uncapped" upload for HTB (Mbps → ×1000 = kbps for wondershaper).
# Values near 100000 Mbps produce Illegal "rate" on common kernels.
readonly DEFAULT_UPLOAD_MBPS=10000
# Clamp wondershaper kbps arguments to a range HTB typically accepts.
readonly MIN_RATE_KBPS=8
readonly MAX_RATE_KBPS=10000000

CMD="status"
LIMIT_SPEC=""
FALLBACK_MBPS="${DOWNLOAD_LIMIT_FALLBACK:-50}"
JSON_FLAG=0
WRAP_ARGS=()

#######################################
# dl_log helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
dl_log() { log "[download-limit] $*"; }
#######################################
# dl_warn helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
dl_warn() { warn "[download-limit] $*"; }
#######################################
# dl_err helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
dl_err() { err "[download-limit] $*"; }

#######################################
# Detect default-route interface.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
get_active_interface() {
  if [[ -n ${LAB_MOCK_IFACE:-} ]]; then
    echo "${LAB_MOCK_IFACE}"
    return 0
  fi
  if command -v ip >/dev/null 2>&1; then
    ip route get 1.1.1.1 2>/dev/null | awk '{print $5; exit}'
    return 0
  fi
  route get 1.1.1.1 2>/dev/null | awk '/interface:/{print $2; exit}'
}

#######################################
# check_wondershaper helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
check_wondershaper() {
  command -v wondershaper >/dev/null 2>&1
}

#######################################
# Install wondershaper if missing (best-effort); skip if LAB_MOCK_WONDERSHAPER=1.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
ensure_wondershaper() {
  if [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
    return 0
  fi
  if check_wondershaper; then
    return 0
  fi
  dl_warn "wondershaper not found; attempting install..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y wondershaper
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y wondershaper
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm wondershaper
  else
    dl_err "Install wondershaper manually (or set PATH to a mock for tests)"
    return 1
  fi
  check_wondershaper
}

#######################################
# Invoke wondershaper (via sudo unless LAB_NO_SUDO=1).
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
sudo_wondershaper() {
  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    wondershaper "$@"
  else
    sudo wondershaper "$@"
  fi
}

#######################################
# Clamp a wondershaper rate (kbps) to MIN_RATE_KBPS..MAX_RATE_KBPS.
# Globals:
#   MIN_RATE_KBPS, MAX_RATE_KBPS
# Arguments:
#   $1  Rate in kbps (integer)
# Outputs:
#   Clamped integer rate on stdout
# Returns:
#   0
#######################################
clamp_rate_kbps() {
  local rate="${1}"
  if [[ ${rate} -lt ${MIN_RATE_KBPS} ]]; then
    echo "${MIN_RATE_KBPS}"
    return 0
  fi
  if [[ ${rate} -gt ${MAX_RATE_KBPS} ]]; then
    echo "${MAX_RATE_KBPS}"
    return 0
  fi
  echo "${rate}"
}

#######################################
# Best-effort load of kernel qdisc modules used by wondershaper/HTB.
# Skipped under LAB_MOCK_WONDERSHAPER or LAB_NO_SUDO.
# Globals:
#   LAB_MOCK_WONDERSHAPER, LAB_NO_SUDO
# Arguments:
#   None
# Outputs:
#   None (errors suppressed)
# Returns:
#   0 always
#######################################
load_shaping_modules() {
  if [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" || ${LAB_NO_SUDO:-} == "1" ]]; then
    return 0
  fi
  if command -v modprobe >/dev/null 2>&1; then
    sudo modprobe sch_htb 2>/dev/null || true
    sudo modprobe sch_ingress 2>/dev/null || true
    sudo modprobe sch_sfq 2>/dev/null || true
    sudo modprobe ifb 2>/dev/null || true
  fi
  return 0
}

#######################################
# Return 0 when kernel HTB-based shaping is likely available.
# DGX Spark / NVIDIA OFED kernels often lack sch_htb — detect and skip wondershaper spam.
# Globals:
#   LAB_MOCK_WONDERSHAPER, LAB_FORCE_NO_HTB, LAB_SHAPING_SUPPORTED (cache 0|1)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if shaping looks available; 1 otherwise
#######################################
shaping_supported() {
  if [[ -n ${LAB_SHAPING_SUPPORTED:-} ]]; then
    [[ ${LAB_SHAPING_SUPPORTED} == "1" ]]
    return $?
  fi
  if [[ ${LAB_FORCE_NO_HTB:-} == "1" ]]; then
    LAB_SHAPING_SUPPORTED=0
    export LAB_SHAPING_SUPPORTED
    return 1
  fi
  if [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
    LAB_SHAPING_SUPPORTED=1
    export LAB_SHAPING_SUPPORTED
    return 0
  fi
  load_shaping_modules
  if command -v modinfo >/dev/null 2>&1 && modinfo sch_htb >/dev/null 2>&1; then
    LAB_SHAPING_SUPPORTED=1
    export LAB_SHAPING_SUPPORTED
    return 0
  fi
  local kver
  kver="$(uname -r 2>/dev/null || true)"
  if [[ -n ${kver} ]] && compgen -G "/lib/modules/${kver}/kernel/net/sched/sch_htb*" >/dev/null 2>&1; then
    LAB_SHAPING_SUPPORTED=1
    export LAB_SHAPING_SUPPORTED
    return 0
  fi
  # Built-in HTB sometimes only appears via tc
  if command -v tc >/dev/null 2>&1 && tc qdisc add help 2>&1 | grep -qi htb; then
    LAB_SHAPING_SUPPORTED=1
    export LAB_SHAPING_SUPPORTED
    return 0
  fi
  LAB_SHAPING_SUPPORTED=0
  export LAB_SHAPING_SUPPORTED
  return 1
}

#######################################
# Map measured/target Mbps to HF download worker count for gentle mode.
# Globals:
#   None
# Arguments:
#   $1  Mbps (integer)
# Outputs:
#   Worker count on stdout
# Returns:
#   0
#######################################
gentle_hf_workers_for_mbps() {
  local mbps="${1:-50}"
  if [[ ${mbps} -ge 200 ]]; then
    echo 4
  elif [[ ${mbps} -ge 80 ]]; then
    echo 3
  elif [[ ${mbps} -ge 30 ]]; then
    echo 2
  else
    echo 1
  fi
}

#######################################
# Export HF env for reduced parallel saturation when kernel shaping is unavailable.
# Globals:
#   HF_DOWNLOAD_MAX_WORKERS, HF_HUB_ENABLE_HF_TRANSFER (export)
# Arguments:
#   $1  Target/measured Mbps
#   $2  Optional interface name (for log text)
# Outputs:
#   Warnings via dl_warn
# Returns:
#   0
#######################################
enable_gentle_download_mode() {
  local mbps="${1:-50}"
  local iface="${2:-}"
  local workers
  workers="$(gentle_hf_workers_for_mbps "${mbps}")"
  export HF_HUB_ENABLE_HF_TRANSFER=0
  if [[ -z ${HF_DOWNLOAD_MAX_WORKERS:-} ]]; then
    export HF_DOWNLOAD_MAX_WORKERS="${workers}"
  fi
  dl_warn "Kernel traffic shaping unavailable${iface:+ on ${iface}} (no HTB/IFB — common on DGX Spark)"
  dl_warn "Gentle HF mode: max-workers=${HF_DOWNLOAD_MAX_WORKERS} (target ~${mbps} Mbps). Not a hard Mbps cap."
  dl_warn "To skip limit machinery entirely: DOWNLOAD_LIMIT=off"
}

#######################################
# Return 0 when traffic shaping qdiscs appear active on the interface.
# Under LAB_MOCK_WONDERSHAPER=1, treats limits as active (hermetic tests).
# Globals:
#   LAB_MOCK_WONDERSHAPER, LAB_MOCK_LIMITS_ACTIVE
# Arguments:
#   $1  Interface name
# Outputs:
#   None
# Returns:
#   0 if shaping looks active; 1 otherwise
#######################################
limits_active() {
  local iface="${1:-}"
  if [[ -z ${iface} ]]; then
    return 1
  fi
  if [[ -n ${LAB_MOCK_LIMITS_ACTIVE:-} ]]; then
    [[ ${LAB_MOCK_LIMITS_ACTIVE} == "1" ]]
    return $?
  fi
  if [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" && ${LAB_FORCE_NO_HTB:-} != "1" ]]; then
    return 0
  fi
  local out=""
  if command -v tc >/dev/null 2>&1; then
    out=$(tc qdisc show dev "${iface}" 2>/dev/null || true)
    if [[ ${out} =~ htb|tbf|ingress|sfq ]]; then
      return 0
    fi
  fi
  return 1
}

#######################################
# Clear wondershaper on interface.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Interface
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
clear_limits() {
  local iface="${1:-}"
  if [[ -z ${iface} ]]; then
    iface=$(get_active_interface)
  fi
  if [[ -z ${iface} ]]; then
    dl_warn "No interface for clear"
    return 0
  fi
  dl_log "Clearing bandwidth limits on ${iface}"
  if check_wondershaper || [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
    sudo_wondershaper clear "${iface}" 2>/dev/null || true
  fi
  return 0
}

#######################################
# Apply download (and optional upload) Mbps caps and verify qdiscs are active.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Interface
#   $2  Download Mbps
#   $3  Upload Mbps (optional; default high legal "uncapped")
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 when apply succeeds and limits appear active; 1 otherwise
#######################################
apply_limits() {
  local iface="${1}"
  local down_mbps="${2}"
  local up_mbps="${3:-$DEFAULT_UPLOAD_MBPS}"
  local down_kbps up_kbps ws_out
  if ! shaping_supported; then
    dl_warn "Skipping wondershaper: kernel HTB not available"
    return 1
  fi
  down_kbps=$(clamp_rate_kbps $((down_mbps * BANDWIDTH_UNIT_MULTIPLIER)))
  up_kbps=$(clamp_rate_kbps $((up_mbps * BANDWIDTH_UNIT_MULTIPLIER)))
  ensure_wondershaper || return 1
  load_shaping_modules
  clear_limits "${iface}"
  dl_log "Applying limits on ${iface}: down=${down_mbps} Mbps up=${up_mbps} Mbps"
  # Capture tc/wondershaper noise; surface a single diagnostic on failure.
  if ! ws_out=$(sudo_wondershaper "${iface}" "${down_kbps}" "${up_kbps}" 2>&1); then
    dl_warn "wondershaper apply failed (see LAB_DEBUG=1 for details)"
    if [[ ${LAB_DEBUG:-} == "1" ]]; then
      dl_warn "${ws_out}"
    fi
    clear_limits "${iface}"
    return 1
  fi
  if [[ -n ${ws_out} ]] && [[ ${ws_out} =~ [Ee]rror|Illegal|unknown ]]; then
    dl_warn "wondershaper reported errors without hard Mbps cap"
    if [[ ${LAB_DEBUG:-} == "1" ]]; then
      dl_warn "${ws_out}"
    fi
    clear_limits "${iface}"
    return 1
  fi
  if ! limits_active "${iface}"; then
    dl_warn "Bandwidth limit not active on ${iface} after wondershaper (kernel qdisc missing?)"
    clear_limits "${iface}"
    return 1
  fi
  return 0
}

#######################################
# HTTP download probe → approximate download Mbps (no sudo).
# Uses Cloudflare speed endpoint by default; override with SPEEDTEST_HTTP_URL.
# Globals:
#   LAB_MOCK_HTTP_SPEED_MBPS, SPEEDTEST_HTTP_URL, SPEEDTEST_HTTP_BYTES
# Arguments:
#   None
# Outputs:
#   Integer Mbps on stdout
# Returns:
#   0 on success; 1 on failure
#######################################
probe_http_download_mbps() {
  if [[ -n ${LAB_MOCK_HTTP_SPEED_MBPS:-} ]]; then
    echo "${LAB_MOCK_HTTP_SPEED_MBPS}"
    return 0
  fi
  if ! command -v curl >/dev/null 2>&1; then
    return 1
  fi
  local bytes url bps mbps
  bytes="${SPEEDTEST_HTTP_BYTES:-15000000}"
  url="${SPEEDTEST_HTTP_URL:-https://speed.cloudflare.com/__down?bytes=${bytes}}"
  bps="$(curl -fsSL --max-time 30 -o /dev/null -w '%{speed_download}' "${url}" 2>/dev/null)" || return 1
  if [[ -z ${bps} || ! ${bps} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    return 1
  fi
  # bytes/s → Mbps; require at least ~0.5 Mbps of signal
  mbps="$(python3 -c "print(max(1, int(float('${bps}') * 8 / 1e6)))" 2>/dev/null)" || return 1
  if [[ ${mbps} -lt 1 ]]; then
    return 1
  fi
  echo "${mbps}"
  return 0
}

#######################################
# Return measured download Mbps as integer, or empty on failure.
# Tries speedtest-cli, Ookla speedtest, then HTTP probe (Cloudflare).
# Globals:
#   LAB_MOCK_SPEEDTEST_MBPS, LAB_MOCK_HTTP_SPEED_MBPS, SPEEDTEST_HTTP_*
# Arguments:
#   None
# Outputs:
#   Integer Mbps on stdout (no log noise on stdout)
# Returns:
#   0 on success; 1 on failure
#######################################
run_speedtest_mbps() {
  if [[ -n ${LAB_MOCK_SPEEDTEST_MBPS:-} ]]; then
    echo "${LAB_MOCK_SPEEDTEST_MBPS}"
    return 0
  fi
  local out=""
  if command -v speedtest-cli >/dev/null 2>&1; then
    out=$(speedtest-cli --simple 2>/dev/null | awk '/Download:/{print $2; exit}') || true
    if [[ -n ${out} && ${out} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      printf '%d\n' "${out%.*}"
      return 0
    fi
  fi
  if command -v speedtest >/dev/null 2>&1; then
    # Ookla CLI: --format=json or progress text
    out=$(speedtest --accept-license --accept-gdpr -f json 2>/dev/null |
      python3 -c 'import json,sys; d=json.load(sys.stdin); print(int(d.get("download",{}).get("bandwidth",0)*8/1e6))' 2>/dev/null) || true
    if [[ -z ${out} ]]; then
      out=$(speedtest --accept-license --accept-gdpr --simple 2>/dev/null |
        awk '/Download/{print int($2); exit}') || true
    fi
    if [[ -n ${out} && ${out} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      printf '%d\n' "${out%.*}"
      return 0
    fi
  fi
  if out=$(probe_http_download_mbps); then
    echo "${out}"
    return 0
  fi
  return 1
}

#######################################
# floor(speed * 0.85); minimum 1.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Measured Mbps
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
compute_auto_limit() {
  local measured="${1}"
  python3 -c "print(max(1, int(float('${measured}') * ${AUTO_FRACTION})))"
}

#######################################
# Resolve --limit auto|N to integer Mbps.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Limit spec
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
resolve_limit_mbps() {
  local spec="${1}"
  if [[ ${spec} == "auto" ]]; then
    local measured
    if measured=$(run_speedtest_mbps 2>/dev/null); then
      local auto
      auto=$(compute_auto_limit "${measured}")
      # Heuristic label: mock/http vs classic speedtest
      if [[ -n ${LAB_MOCK_HTTP_SPEED_MBPS:-} || -z ${LAB_MOCK_SPEEDTEST_MBPS:-} ]]; then
        dl_log "Measured download ≈ ${measured} Mbps → auto limit ${auto} Mbps (85%)"
      else
        dl_log "Measured download ≈ ${measured} Mbps → auto limit ${auto} Mbps (85%)"
      fi
      echo "${auto}"
      return 0
    fi
    dl_warn "Could not measure download speed; using fallback ${FALLBACK_MBPS} Mbps"
    echo "${FALLBACK_MBPS}"
    return 0
  fi
  if [[ ${spec} =~ ^[0-9]+$ && ${spec} -gt 0 ]]; then
    echo "${spec}"
    return 0
  fi
  dl_err "Invalid --limit '${spec}' (use auto or positive integer Mbps)"
  return 1
}

#######################################
# cmd_status helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
cmd_status() {
  local iface shaping="no"
  iface=$(get_active_interface)
  iface=${iface:-unknown}
  if shaping_supported; then
    shaping="yes"
  fi
  if [[ ${JSON_FLAG} -eq 1 ]]; then
    printf '{"interface":"%s","tool":"wondershaper","auto_fraction":%s,"shaping_supported":%s}\n' \
      "${iface}" "${AUTO_FRACTION}" "$([[ ${shaping} == yes ]] && echo true || echo false)"
  else
    dl_log "Interface: ${iface}"
    dl_log "auto fraction: ${AUTO_FRACTION} (85%)"
    dl_log "kernel HTB shaping: ${shaping}"
    if check_wondershaper; then
      dl_log "wondershaper: present"
    else
      dl_warn "wondershaper: missing"
    fi
  fi
}

#######################################
# cmd_run helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
cmd_run() {
  local mbps iface
  [[ -n ${LIMIT_SPEC} ]] || die "run requires --limit auto|N"
  mbps=$(resolve_limit_mbps "${LIMIT_SPEC}")
  iface=$(get_active_interface)
  [[ -n ${iface} ]] || die "Could not detect network interface"
  if ! apply_limits "${iface}" "${mbps}"; then
    die "Failed to apply bandwidth limit on ${iface} (qdisc/HTB unavailable or rate rejected)"
  fi
  dl_log "Limit applied. Use: $0 clear   to remove."
}

#######################################
# cmd_clear helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
cmd_clear() {
  local iface
  iface=$(get_active_interface)
  clear_limits "${iface}"
}

#######################################
# Apply limit, run remaining args, always clear.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
cmd_wrap() {
  local mbps iface
  [[ -n ${LIMIT_SPEC} ]] || die "wrap requires --limit auto|N"
  [[ ${#WRAP_ARGS[@]} -gt 0 ]] || die "wrap requires a command after --"
  mbps=$(resolve_limit_mbps "${LIMIT_SPEC}")
  iface=$(get_active_interface)
  [[ -n ${iface} ]] || die "Could not detect network interface"
  # shellcheck disable=SC2064
  trap 'clear_limits "'"${iface}"'"' EXIT INT TERM HUP
  if shaping_supported && apply_limits "${iface}" "${mbps}"; then
    dl_log "Kernel bandwidth limit active (~${mbps} Mbps down)"
  else
    if [[ ${DOWNLOAD_LIMIT_REQUIRE:-} == "1" ]]; then
      die "Failed to apply bandwidth limit on ${iface} (set DOWNLOAD_LIMIT=off to skip, or fix wondershaper/qdisc)"
    fi
    # Clear-on-exit still registered. Soft path: gentle HF workers, not a hard Mbps cap.
    enable_gentle_download_mode "${mbps}" "${iface}"
  fi
  dl_log "Running: ${WRAP_ARGS[*]}"
  "${WRAP_ARGS[@]}"
}

#######################################
# parse_args helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      status | run | clear | wrap)
        CMD="${1}"
        shift
        ;;
      --limit)
        LIMIT_SPEC="${2:-}"
        shift 2
        ;;
      --fallback)
        FALLBACK_MBPS="${2:-}"
        shift 2
        ;;
      --json)
        JSON_FLAG=1
        shift
        ;;
      --)
        shift
        WRAP_ARGS=("$@")
        break
        ;;
      -h | --help)
        cat <<'EOF' >&2
Usage:
  download-limit.sh status [--json]
  download-limit.sh run --limit auto|N [--fallback N]
  download-limit.sh clear
  download-limit.sh wrap --limit auto|N -- <command...>
EOF
        exit 0
        ;;
      *)
        die "Unknown arg: $1"
        ;;
    esac
  done
}

#######################################
# main helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    clear) cmd_clear ;;
    wrap) cmd_wrap ;;
    *) die "Unknown command: ${CMD}" ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
