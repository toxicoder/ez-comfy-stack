#!/usr/bin/env bash
#
# ## download-limit
#
# Limit host download bandwidth so multi‑GB model pulls cannot starve remote SSH.
#
# Purpose:
#   Apply kernel traffic shaping via wondershaper on the default-route interface.
#   Supports fixed Mbps caps and an **auto** mode that runs a speedtest and applies
#   floor(0.85 × measured_download_mbps). The wrap subcommand always clears limits
#   on EXIT/INT/TERM so a killed download cannot leave the host permanently throttled.
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
#   - speedtest-cli or Ookla speedtest for auto mode (optional with fallback)
#
# Test hooks:
#   LAB_MOCK_IFACE, LAB_MOCK_WONDERSHAPER, LAB_MOCK_SPEEDTEST_MBPS, LAB_NO_SUDO
#
# Units:
#   Limits are megabits per second (Mbps), not MB/s. 40 Mbps ≈ 5 MB/s.
#
# Exit codes:
#   0 success; 1 invalid args, missing interface, or apply failure.
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
readonly DEFAULT_UPLOAD_MBPS=100000

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
# Apply download (and optional upload) Mbps caps.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Interface
#   $2  Download Mbps
#   $3  Upload Mbps (optional; default uncapped)
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
apply_limits() {
  local iface="${1}"
  local down_mbps="${2}"
  local up_mbps="${3:-$DEFAULT_UPLOAD_MBPS}"
  local down_kbps up_kbps
  down_kbps=$((down_mbps * BANDWIDTH_UNIT_MULTIPLIER))
  up_kbps=$((up_mbps * BANDWIDTH_UNIT_MULTIPLIER))
  ensure_wondershaper || return 1
  clear_limits "${iface}"
  dl_log "Applying limits on ${iface}: down=${down_mbps} Mbps up=${up_mbps} Mbps"
  sudo_wondershaper "${iface}" "${down_kbps}" "${up_kbps}"
}

#######################################
# Return measured download Mbps as integer, or empty on failure.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
run_speedtest_mbps() {
  if [[ -n ${LAB_MOCK_SPEEDTEST_MBPS:-} ]]; then
    echo "${LAB_MOCK_SPEEDTEST_MBPS}"
    return 0
  fi
  local out=""
  if command -v speedtest-cli >/dev/null 2>&1; then
    out=$(speedtest-cli --simple 2>/dev/null | awk '/Download:/{print $2; exit}') || true
  elif command -v speedtest >/dev/null 2>&1; then
    # Ookla CLI: --format=json or progress text
    out=$(speedtest --accept-license --accept-gdpr -f json 2>/dev/null |
      python3 -c 'import json,sys; d=json.load(sys.stdin); print(int(d.get("download",{}).get("bandwidth",0)*8/1e6))' 2>/dev/null) || true
    if [[ -z ${out} ]]; then
      out=$(speedtest --accept-license --accept-gdpr --simple 2>/dev/null |
        awk '/Download/{print int($2); exit}') || true
    fi
  fi
  if [[ -n ${out} && ${out} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    printf '%d\n' "${out%.*}"
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
    if measured=$(run_speedtest_mbps); then
      local auto
      auto=$(compute_auto_limit "${measured}")
      dl_log "Speedtest download ≈ ${measured} Mbps → auto limit ${auto} Mbps (85%)"
      echo "${auto}"
      return 0
    fi
    dl_warn "Speedtest failed; using fallback ${FALLBACK_MBPS} Mbps"
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
  local iface
  iface=$(get_active_interface)
  iface=${iface:-unknown}
  if [[ ${JSON_FLAG} -eq 1 ]]; then
    printf '{"interface":"%s","tool":"wondershaper","auto_fraction":%s}\n' \
      "${iface}" "${AUTO_FRACTION}"
  else
    dl_log "Interface: ${iface}"
    dl_log "auto fraction: ${AUTO_FRACTION} (85%)"
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
  apply_limits "${iface}" "${mbps}"
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
  apply_limits "${iface}" "${mbps}"
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
