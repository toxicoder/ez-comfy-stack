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
  dl_warn "wondershaper not found; attempting non-interactive install..."
  if [[ ${LAB_NO_SUDO:-} == "1" ]] || ! command -v sudo >/dev/null 2>&1 || ! sudo -n true 2>/dev/null; then
    dl_err "wondershaper missing and cannot install without interactive sudo"
    return 1
  fi
  if command -v apt-get >/dev/null 2>&1; then
    sudo -n apt-get update -qq && sudo -n apt-get install -y wondershaper
  elif command -v dnf >/dev/null 2>&1; then
    sudo -n dnf install -y wondershaper
  elif command -v pacman >/dev/null 2>&1; then
    sudo -n pacman -S --noconfirm wondershaper
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
  # Silence "queues have been cleared" on clear — that line pollutes
  # measured=$(run_speedtest_mbps) if left on stdout. Keep apply output for error checks.
  local quiet=0
  if [[ ${1:-} == "clear" ]]; then
    quiet=1
  fi
  if [[ ${LAB_NO_SUDO:-} == "1" || ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
    if [[ ${quiet} -eq 1 ]]; then
      wondershaper "$@" >/dev/null 2>&1
    else
      wondershaper "$@"
    fi
    return $?
  fi
  # Never prompt interactively during download-models
  if ! sudo -n true 2>/dev/null; then
    return 1
  fi
  if [[ ${quiet} -eq 1 ]]; then
    sudo -n wondershaper "$@" >/dev/null 2>&1
  else
    sudo -n wondershaper "$@"
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
  # Non-interactive only — never prompt mid-download
  if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true 2>/dev/null; then
    return 0
  fi
  if command -v modprobe >/dev/null 2>&1; then
    sudo -n modprobe sch_htb 2>/dev/null || true
    sudo -n modprobe sch_ingress 2>/dev/null || true
    sudo -n modprobe sch_sfq 2>/dev/null || true
    sudo -n modprobe ifb 2>/dev/null || true
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
  # Detection only — no interactive sudo (load_shaping_modules is -n only)
  load_shaping_modules
  # Require non-interactive sudo for any real apply path
  if command -v sudo >/dev/null 2>&1 && ! sudo -n true 2>/dev/null; then
    LAB_SHAPING_SUPPORTED=0
    export LAB_SHAPING_SUPPORTED
    return 1
  fi
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
  local min_w workers
  # Floor ≥2: short HTTP probes often under-read line rate; workers=1 looks "hung" on multi-GB files
  min_w="${HF_DOWNLOAD_MIN_WORKERS:-2}"
  if [[ ${mbps} -ge 200 ]]; then
    workers=4
  elif [[ ${mbps} -ge 80 ]]; then
    workers=3
  elif [[ ${mbps} -ge 30 ]]; then
    workers=2
  else
    workers=${min_w}
  fi
  if [[ ${workers} -lt ${min_w} ]]; then
    workers=${min_w}
  fi
  echo "${workers}"
}

#######################################
# Default workers when speed sample is untrusted (idle NIC / failed probe).
# Globals:
#   HF_DOWNLOAD_DEFAULT_WORKERS
# Arguments:
#   None
# Outputs:
#   Integer workers on stdout
# Returns:
#   0
#######################################
default_hf_workers_untrusted() {
  echo "${HF_DOWNLOAD_DEFAULT_WORKERS:-4}"
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
  dl_log "Kernel Mbps cap unavailable${iface:+ on ${iface}} (common on DGX Spark) — gentle HF mode: max-workers=${HF_DOWNLOAD_MAX_WORKERS} (target ~${mbps} Mbps)"
  dl_log "Tip: DOWNLOAD_LIMIT=off skips limit machinery entirely"
}

#######################################
# Mark kernel shaping as unavailable for the rest of this process (no more sudo/ws).
# Globals:
#   LAB_SHAPING_SUPPORTED
# Arguments:
#   $1  Optional reason string
# Outputs:
#   One log line
# Returns:
#   0
#######################################
mark_shaping_unsupported() {
  local reason="${1:-runtime apply failed}"
  LAB_SHAPING_SUPPORTED=0
  export LAB_SHAPING_SUPPORTED
  dl_log "Disabling kernel shaping for this run (${reason})"
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
  local force="${2:-0}"
  if [[ -z ${iface} ]]; then
    iface=$(get_active_interface)
  fi
  if [[ -z ${iface} ]]; then
    return 0
  fi
  # Normal path: skip if shaping marked off (unless force for speed tests)
  if [[ ${force} != "1" && ${LAB_SHAPING_SUPPORTED:-} == "0" ]]; then
    return 0
  fi
  if [[ ${force} != "1" && ${LAB_NO_SUDO:-} != "1" && ${LAB_MOCK_WONDERSHAPER:-} != "1" ]]; then
    if command -v sudo >/dev/null 2>&1 && ! sudo -n true 2>/dev/null; then
      return 0
    fi
  fi
  if check_wondershaper || [[ ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
    dl_log "Clearing bandwidth limits on ${iface}"
    sudo_wondershaper clear "${iface}" 2>/dev/null || true
  fi
  # Best-effort raw tc clear (leftover qdiscs without wondershaper)
  if [[ ${force} == "1" ]] && command -v tc >/dev/null 2>&1; then
    if [[ ${LAB_NO_SUDO:-} == "1" || ${LAB_MOCK_WONDERSHAPER:-} == "1" ]]; then
      tc qdisc del dev "${iface}" root 2>/dev/null || true
      tc qdisc del dev "${iface}" ingress 2>/dev/null || true
    elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      sudo -n tc qdisc del dev "${iface}" root 2>/dev/null || true
      sudo -n tc qdisc del dev "${iface}" ingress 2>/dev/null || true
    fi
  fi
  return 0
}

#######################################
# Force-clear any shaping before speed measurement (ignore LAB_SHAPING_SUPPORTED=0).
# Globals:
#   See clear_limits
# Arguments:
#   $1  Optional interface
# Outputs:
#   Status logs
# Returns:
#   0
#######################################
clear_limits_for_speedtest() {
  local iface="${1:-}"
  if [[ -z ${iface} ]]; then
    iface=$(get_active_interface)
  fi
  if [[ -z ${iface} ]]; then
    return 0
  fi
  dl_log "Clearing any existing bandwidth limits before speed measure on ${iface}"
  clear_limits "${iface}" 1
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
    return 1
  fi
  # Avoid interactive sudo mid-download when ticket is cold
  if [[ ${LAB_NO_SUDO:-} != "1" && ${LAB_MOCK_WONDERSHAPER:-} != "1" ]]; then
    if command -v sudo >/dev/null 2>&1 && ! sudo -n true 2>/dev/null; then
      mark_shaping_unsupported "sudo not cached (would prompt mid-download)"
      return 1
    fi
  fi
  down_kbps=$(clamp_rate_kbps $((down_mbps * BANDWIDTH_UNIT_MULTIPLIER)))
  up_kbps=$(clamp_rate_kbps $((up_mbps * BANDWIDTH_UNIT_MULTIPLIER)))
  ensure_wondershaper || {
    mark_shaping_unsupported "wondershaper missing"
    return 1
  }
  load_shaping_modules
  clear_limits "${iface}"
  dl_log "Applying limits on ${iface}: down=${down_mbps} Mbps up=${up_mbps} Mbps"
  # Capture tc/wondershaper noise; one short diagnostic on failure.
  if ! ws_out=$(sudo_wondershaper "${iface}" "${down_kbps}" "${up_kbps}" 2>&1); then
    mark_shaping_unsupported "wondershaper apply failed"
    if [[ ${LAB_DEBUG:-} == "1" ]]; then
      dl_warn "${ws_out}"
    fi
    clear_limits "${iface}"
    return 1
  fi
  if [[ -n ${ws_out} ]] && [[ ${ws_out} =~ [Ee]rror|Illegal|unknown ]]; then
    mark_shaping_unsupported "qdisc/HTB/IFB unavailable at runtime"
    if [[ ${LAB_DEBUG:-} == "1" ]]; then
      dl_warn "${ws_out}"
    fi
    clear_limits "${iface}"
    return 1
  fi
  if ! limits_active "${iface}"; then
    mark_shaping_unsupported "qdisc not active after apply"
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
  local bytes bps mbps code url
  local -a urls=()
  bytes="${SPEEDTEST_HTTP_BYTES:-15000000}"
  if [[ -n ${SPEEDTEST_HTTP_URL:-} ]]; then
    urls+=("${SPEEDTEST_HTTP_URL}")
  fi
  urls+=(
    "https://speed.cloudflare.com/__down?bytes=${bytes}"
    "https://proof.ovh.net/files/10Mb.dat"
    "https://github.com/github/gitignore/archive/refs/heads/main.zip"
  )
  for url in "${urls[@]}"; do
    # -4 prefer IPv4; capture http_code + speed
    code="$(curl -4 -L --connect-timeout 5 --max-time 25 -o /dev/null \
      -w '%{http_code} %{speed_download}' "${url}" 2>/dev/null)" || continue
    bps="$(echo "${code}" | awk '{print $2}')"
    code="$(echo "${code}" | awk '{print $1}')"
    if [[ ! ${code} =~ ^2[0-9][0-9]$ ]]; then
      continue
    fi
    if [[ -z ${bps} || ! ${bps} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      continue
    fi
    mbps="$(python3 -c "print(max(1, int(float('${bps}') * 8 / 1e6)))" 2>/dev/null)" || continue
    if [[ ${mbps} -lt 1 ]]; then
      continue
    fi
    dl_log "HTTP probe OK via ${url%%\?*} ≈ ${mbps} Mbps"
    echo "${mbps}"
    return 0
  done
  return 1
}

#######################################
# Ensure speedtest-cli is available (pip --user preferred, then apt with sudo -n).
# Globals:
#   LAB_MOCK_SPEEDTEST_MBPS, LAB_NO_SUDO, PATH
# Arguments:
#   None
# Outputs:
#   Status logs
# Returns:
#   0 if speedtest-cli on PATH after attempt; 1 otherwise
#######################################
ensure_speedtest_cli() {
  local errf
  if command -v speedtest-cli >/dev/null 2>&1; then
    return 0
  fi
  if [[ -n ${LAB_MOCK_SPEEDTEST_MBPS:-} ]]; then
    return 0
  fi
  dl_log "speedtest-cli not found; attempting install (multiple strategies)…"
  if [[ -d ${HOME}/.local/bin ]]; then
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
  errf="$(mktemp)"

  _speedtest_try() {
    local desc="${1}"
    shift
    dl_log "  try: ${desc}"
    if "$@" >"${errf}" 2>&1; then
      return 0
    fi
    dl_warn "  failed: ${desc}: $(tail -n 2 "${errf}" | tr '\n' ' ')"
    return 1
  }

  if command -v python3 >/dev/null 2>&1; then
    _speedtest_try "pip --user" python3 -m pip install --user -q speedtest-cli || true
    if ! command -v speedtest-cli >/dev/null 2>&1; then
      _speedtest_try "pip --user --break-system-packages" \
        python3 -m pip install --user --break-system-packages -q speedtest-cli || true
    fi
  fi
  if ! command -v speedtest-cli >/dev/null 2>&1 && command -v pipx >/dev/null 2>&1; then
    _speedtest_try "pipx install" pipx install speedtest-cli || true
  fi
  if ! command -v speedtest-cli >/dev/null 2>&1 &&
    [[ ${LAB_NO_SUDO:-} != "1" ]] && command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    if command -v apt-get >/dev/null 2>&1; then
      _speedtest_try "apt speedtest-cli" sudo -n apt-get install -y speedtest-cli || true
      _speedtest_try "apt python3-speedtest-cli" sudo -n apt-get install -y python3-speedtest-cli || true
    elif command -v dnf >/dev/null 2>&1; then
      _speedtest_try "dnf speedtest-cli" sudo -n dnf install -y speedtest-cli || true
    fi
  fi
  rm -f "${errf}"

  # Refresh PATH and common locations
  export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:${PATH}"
  hash -r 2>/dev/null || true
  if command -v speedtest-cli >/dev/null 2>&1; then
    dl_log "speedtest-cli ready: $(command -v speedtest-cli)"
    return 0
  fi
  # Module-only install: wrap via python -m if import works
  if python3 -c 'import speedtest' 2>/dev/null; then
    dl_log "speedtest module importable; installing ~/.local/bin/speedtest-cli wrapper"
    mkdir -p "${HOME}/.local/bin"
    cat >"${HOME}/.local/bin/speedtest-cli" <<'EOF'
#!/usr/bin/env bash
exec python3 -m speedtest "$@"
EOF
    chmod +x "${HOME}/.local/bin/speedtest-cli"
    export PATH="${HOME}/.local/bin:${PATH}"
    hash -r 2>/dev/null || true
    if command -v speedtest-cli >/dev/null 2>&1; then
      return 0
    fi
  fi
  dl_warn "Could not install speedtest-cli after all strategies; will try HTTP probe / live RX"
  return 1
}

#######################################
# Return measured download Mbps as integer, or empty on failure.
# Clears any shaping first, ensures speedtest-cli, then CLI/Ookla/HTTP probes.
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
  if [[ ${LAB_FORCE_SPEEDTEST_FAIL:-} == "1" ]]; then
    dl_warn "Preflight speed: forced fail (test)"
    return 1
  fi
  if [[ -n ${LAB_MOCK_SPEEDTEST_MBPS:-} ]]; then
    echo "${LAB_MOCK_SPEEDTEST_MBPS}"
    return 0
  fi
  # Hermetic HTTP mock must win over host speedtest-cli (CI runners may have it)
  if [[ -n ${LAB_MOCK_HTTP_SPEED_MBPS:-} ]]; then
    echo "${LAB_MOCK_HTTP_SPEED_MBPS}"
    return 0
  fi

  # Unthrottle before any probe so residual wondershaper/tc does not skew results
  clear_limits_for_speedtest

  ensure_speedtest_cli || true

  local out="" reason=""
  if command -v speedtest-cli >/dev/null 2>&1; then
    out=$(speedtest-cli --simple 2>/dev/null | awk '/Download:/{print $2; exit}') || true
    if [[ -n ${out} && ${out} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      printf '%d\n' "${out%.*}"
      return 0
    fi
    reason="speedtest-cli gave no parseable result"
  else
    reason="speedtest-cli not available after install attempt"
  fi
  if command -v speedtest >/dev/null 2>&1; then
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
    reason="${reason}; ookla speedtest gave no parseable result"
  fi
  if out=$(probe_http_download_mbps); then
    echo "${out}"
    return 0
  fi
  reason="${reason}; HTTP speed probe failed (curl/Cloudflare)"
  # dl_warn is visible even under measured=$(run_speedtest_mbps) — stderr not captured
  dl_warn "Preflight speed: ${reason}"
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
  # Only accept a pure number (reject polluted multi-line / text stdout)
  if [[ ! ${measured} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    dl_err "compute_auto_limit: invalid measured Mbps '${measured//$'\n'/ }'"
    return 1
  fi
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
# Sample interface receive rate over a duration → Mbps integer.
# Globals:
#   LAB_MOCK_LIVE_RX_MBPS, LAB_MOCK_LIVE_SAMPLE_SLEEP
# Arguments:
#   $1  Interface name
#   $2  Sample duration seconds (default 15)
# Outputs:
#   Integer Mbps on stdout
# Returns:
#   0 on success; 1 on failure
#######################################
sample_iface_rx_mbps() {
  local iface="${1:-}"
  local sec="${2:-15}"
  local download_pid="${3:-}"
  if [[ -n ${LAB_MOCK_LIVE_RX_MBPS:-} ]]; then
    sleep "${LAB_MOCK_LIVE_SAMPLE_SLEEP:-0}" 2>/dev/null || true
    echo "${LAB_MOCK_LIVE_RX_MBPS}"
    return 0
  fi
  if [[ -z ${iface} || ${sec} -lt 1 ]]; then
    return 1
  fi
  local rx_path b1 b2 mbps elapsed chunk left
  rx_path="/sys/class/net/${iface}/statistics/rx_bytes"
  if [[ ! -r ${rx_path} ]]; then
    return 1
  fi
  b1="$(cat "${rx_path}" 2>/dev/null)" || return 1
  elapsed=0
  chunk=3
  while [[ ${elapsed} -lt ${sec} ]]; do
    left=$((sec - elapsed))
    if [[ ${left} -gt ${chunk} ]]; then
      left=${chunk}
    fi
    sleep "${left}"
    elapsed=$((elapsed + left))
    if [[ -n ${download_pid} ]] && kill -0 "${download_pid}" 2>/dev/null; then
      dl_log "Sampling live RX… ${elapsed}/${sec}s (download PID ${download_pid} still running)"
    else
      dl_log "Sampling live RX… ${elapsed}/${sec}s"
    fi
  done
  b2="$(cat "${rx_path}" 2>/dev/null)" || return 1
  if [[ -z ${b1} || -z ${b2} || ${b2} -lt ${b1} ]]; then
    return 1
  fi
  mbps="$(python3 -c "print(max(1, int((${b2} - ${b1}) * 8 / ${sec} / 1e6)))" 2>/dev/null)" || return 1
  echo "${mbps}"
  return 0
}

#######################################
# Apply kernel limit or gentle HF workers from a measured Mbps value.
# Globals:
#   DOWNLOAD_LIMIT_REQUIRE
# Arguments:
#   $1  Interface
#   $2  Measured raw Mbps (before 85% — this function applies auto fraction)
# Outputs:
#   Status logs
# Returns:
#   0 if kernel limit applied; 1 if gentle mode used instead
#######################################
apply_limit_from_measured() {
  local iface="${1}"
  local measured="${2}"
  local target
  target="$(compute_auto_limit "${measured}")"
  dl_log "Live sample done: ≈ ${measured} Mbps → target ${target} Mbps (85%)"
  if ! shaping_supported; then
    if [[ ${DOWNLOAD_LIMIT_REQUIRE:-} == "1" ]]; then
      die "Failed to apply bandwidth limit on ${iface}"
    fi
    enable_gentle_download_mode "${target}" "${iface}"
    return 1
  fi
  if apply_limits "${iface}" "${target}"; then
    dl_log "Kernel bandwidth limit active (~${target} Mbps down)"
    return 0
  fi
  if [[ ${DOWNLOAD_LIMIT_REQUIRE:-} == "1" ]]; then
    die "Failed to apply bandwidth limit on ${iface}"
  fi
  enable_gentle_download_mode "${target}" "${iface}"
  return 1
}

#######################################
# When preflight speed fails: measure live RX (HTTP traffic), then ONE foreground download.
# Does NOT start/kill a sample-phase model download (avoids HF locks and hang-on-wait).
# Globals:
#   WRAP_ARGS, LIVE_SPEED_SAMPLE_SEC, FALLBACK_MBPS, SPEEDTEST_HTTP_*
# Arguments:
#   $1  Interface
#   $2  Fallback Mbps if live sample fails
# Outputs:
#   Status logs; download progress
# Returns:
#   Download exit status (130 on Ctrl+C)
#######################################
wrap_with_live_speed_limit() {
  local iface="${1}"
  local live_mbps

  clear_limits_for_speedtest "${iface}"

  # Quick dry-run: if HTTP probe works, use it as preflight-quality measure (no 15s idle)
  if live_mbps=$(probe_http_download_mbps); then
    dl_log "Reliable HTTP probe ≈ ${live_mbps} Mbps — skipping idle RX sample"
    if shaping_supported; then
      apply_limit_from_measured "${iface}" "${live_mbps}" || true
    else
      enable_gentle_download_mode "$(compute_auto_limit "${live_mbps}")" "${iface}"
    fi
    dl_log "=== download-limit: download (foreground) ==="
    dl_log "Starting model download now — live progress should appear below"
    dl_log "Running: ${WRAP_ARGS[*]}"
    run_with_signal_forwarding "${WRAP_ARGS[@]}"
    return $?
  fi

  # No working probe URL: do NOT treat idle NIC RX as line rate
  dl_log "=== download-limit: no reliable speed probe ==="
  dl_log "HTTP/speedtest unavailable — using default max-workers=$(default_hf_workers_untrusted) (not idle RX)"
  export HF_HUB_ENABLE_HF_TRANSFER=0
  export HF_DOWNLOAD_MAX_WORKERS="${HF_DOWNLOAD_MAX_WORKERS:-$(default_hf_workers_untrusted)}"
  dl_log "Gentle HF mode: max-workers=${HF_DOWNLOAD_MAX_WORKERS} (untrusted/idle sample avoided)"
  dl_log "=== download-limit: download (foreground) ==="
  dl_log "Starting model download now — live progress should appear below"
  dl_log "Running: ${WRAP_ARGS[*]}"
  run_with_signal_forwarding "${WRAP_ARGS[@]}"
  return $?
}

#######################################
# Apply limit, run remaining args, always clear on exit; Ctrl+C kills children.
# If auto preflight speed fails, samples live RX during download then limits.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of wrapped command (130 on Ctrl+C)
#######################################
cmd_wrap() {
  local mbps iface measured preflight_ok=0
  [[ -n ${LIMIT_SPEC} ]] || die "wrap requires --limit auto|N"
  [[ ${#WRAP_ARGS[@]} -gt 0 ]] || die "wrap requires a command after --"
  iface=$(get_active_interface)
  [[ -n ${iface} ]] || die "Could not detect network interface"

  if [[ ${LIMIT_SPEC} == "auto" ]]; then
    if measured=$(run_speedtest_mbps); then
      mbps=$(compute_auto_limit "${measured}")
      preflight_ok=1
      dl_log "Preflight download ≈ ${measured} Mbps → auto limit ${mbps} Mbps (85%)"
    else
      preflight_ok=0
      mbps="${FALLBACK_MBPS}"
      dl_log "Preflight failed — next: live RX measure, then one foreground model download"
    fi
  else
    mbps=$(resolve_limit_mbps "${LIMIT_SPEC}")
    preflight_ok=1
  fi

  # shellcheck disable=SC2064
  trap 'clear_limits "'"${iface}"'"' EXIT

  if [[ ${preflight_ok} -eq 0 ]]; then
    wrap_with_live_speed_limit "${iface}" "${mbps}"
    return $?
  fi

  if shaping_supported && apply_limits "${iface}" "${mbps}"; then
    dl_log "Kernel bandwidth limit active (~${mbps} Mbps down)"
  else
    if [[ ${DOWNLOAD_LIMIT_REQUIRE:-} == "1" ]]; then
      die "Failed to apply bandwidth limit on ${iface} (set DOWNLOAD_LIMIT=off to skip, or fix wondershaper/qdisc)"
    fi
    enable_gentle_download_mode "${mbps}" "${iface}"
  fi
  dl_log "Running: ${WRAP_ARGS[*]}"
  run_with_signal_forwarding "${WRAP_ARGS[@]}"
  return $?
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
