#!/usr/bin/env bash
# ## progress
#
# Shared operator progress (bars, heartbeats, ffmpeg) for ez-comfy-stack.
# Sourced from common.sh after log/warn/err. Not executable alone.
#
# Contract: live updates on stderr only. Stdout stays --json / data.
# TTY rewrites one line; non-TTY (CI, pipes) emits periodic newlines.
#

if [[ -n ${_EZ_COMFY_PROGRESS_LOADED:-} ]]; then
  return 0
fi
_EZ_COMFY_PROGRESS_LOADED=1

_PROGRESS_ON_TTY=0

#######################################
# True when bars and heartbeats are enabled.
# Globals:
#   EZ_COMFY_PROGRESS
# Returns:
#   0 when enabled; 1 when EZ_COMFY_PROGRESS=0
#######################################
progress_enabled() {
  [[ ${EZ_COMFY_PROGRESS:-1} != "0" ]]
}

#######################################
# True when ANSI color is allowed on stderr.
# Globals:
#   NO_COLOR
# Returns:
#   0 when stderr is a TTY and NO_COLOR is unset
#######################################
progress_use_color() {
  [[ -z ${NO_COLOR:-} && -t 2 ]]
}

#######################################
# Heartbeat / bar interval in seconds (0 disables ticks).
# Globals:
#   EZ_COMFY_PROGRESS_INTERVAL
# Outputs:
#   Number on stdout (default 2)
# Returns:
#   0
#######################################
progress_interval_s() {
  local raw="${EZ_COMFY_PROGRESS_INTERVAL:-2}"
  if [[ ${raw} =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    printf '%s\n' "${raw}"
    return 0
  fi
  printf '%s\n' "2"
}

#######################################
# Numbered phase banner.
# Arguments:
#   $1  Step number
#   $2  Total steps
#   $3+ Message
# Outputs:
#   log line on stderr
# Returns:
#   0
#######################################
log_step() {
  local n="${1:?log_step requires n}"
  local total="${2:?log_step requires total}"
  shift 2
  log "══ ${n}/${total} ══ $*"
}

#######################################
# Success line (same [ez-comfy] prefix).
# Arguments:
#   $@  Message
# Outputs:
#   log line on stderr
# Returns:
#   0
#######################################
log_ok() {
  log "✓ $*"
}

#######################################
# Debug line; silent unless LAB_DEBUG=1 or EZ_COMFY_LOG_LEVEL=debug.
# Globals:
#   LAB_DEBUG, EZ_COMFY_LOG_LEVEL
# Arguments:
#   $@  Message
# Outputs:
#   log line on stderr when debug is on
# Returns:
#   0
#######################################
log_debug() {
  if [[ ${LAB_DEBUG:-} == "1" || ${EZ_COMFY_LOG_LEVEL:-info} == "debug" ]]; then
    log "[debug] $*"
  fi
}

#######################################
# Format kibibytes as a human size (MiB or GiB).
# Arguments:
#   $1  Size in KiB (integer)
# Outputs:
#   e.g. "179 MiB" or "28.4 GiB" on stdout
# Returns:
#   0
#######################################
progress_format_mib() {
  local kib="${1:-0}"
  if [[ ${kib} -lt 0 ]]; then
    kib=0
  fi
  if [[ ${kib} -ge 1048576 ]]; then
    awk -v k="${kib}" 'BEGIN { printf "%.1f GiB", k / 1048576 }'
  else
    awk -v k="${kib}" 'BEGIN { printf "%d MiB", int(k / 1024) }'
  fi
}

#######################################
# Format a transfer rate from KiB delta over seconds.
# Arguments:
#   $1  Delta KiB (integer; may be 0)
#   $2  Interval seconds (positive)
# Outputs:
#   e.g. "13.7 MiB/s" on stdout
# Returns:
#   0
#######################################
progress_format_rate() {
  local delta_kib="${1:-0}"
  local interval_s="${2:-10}"
  if [[ ${interval_s} -le 0 ]]; then
    interval_s=1
  fi
  if [[ ${delta_kib} -le 0 ]]; then
    echo "0 MiB/s"
    return 0
  fi
  awk -v d="${delta_kib}" -v s="${interval_s}" 'BEGIN {
    mibs = (d / 1024) / s
    if (mibs >= 100) printf "%.0f MiB/s", mibs
    else if (mibs >= 10) printf "%.1f MiB/s", mibs
    else printf "%.2f MiB/s", mibs
  }'
}

#######################################
# Format elapsed seconds as m:ss or h:mm:ss.
# Arguments:
#   $1  Elapsed seconds
# Outputs:
#   Time string on stdout
# Returns:
#   0
#######################################
progress_format_elapsed() {
  local secs="${1:-0}"
  local h m s
  if [[ ${secs} -lt 0 ]]; then
    secs=0
  fi
  h=$((secs / 3600))
  m=$(((secs % 3600) / 60))
  s=$((secs % 60))
  if [[ ${h} -gt 0 ]]; then
    printf '%d:%02d:%02d' "${h}" "${m}" "${s}"
  else
    printf '%d:%02d' "${m}" "${s}"
  fi
}

#######################################
# Remaining seconds from elapsed/current/total, or empty if unknown.
# Arguments:
#   $1  Elapsed seconds
#   $2  Current units
#   $3  Total units
# Outputs:
#   Integer seconds or empty
# Returns:
#   0
#######################################
progress_eta_s() {
  local elapsed="${1:-0}"
  local cur="${2:-0}"
  local total="${3:-0}"
  if [[ ${cur} -le 0 || ${total} -le ${cur} || ${elapsed} -le 0 ]]; then
    printf ''
    return 0
  fi
  printf '%s' $((elapsed * (total - cur) / cur))
}

#######################################
# Unicode bar fill (▓ done, ░ rest).
# Arguments:
#   $1  Filled cells
#   $2  Width (default 20)
# Outputs:
#   Bar on stdout
# Returns:
#   0
#######################################
progress_bar_fill() {
  local filled="${1:-0}"
  local width="${2:-20}"
  local i s=""
  if [[ ${filled} -lt 0 ]]; then
    filled=0
  fi
  if [[ ${width} -le 0 ]]; then
    width=20
  fi
  if [[ ${filled} -gt ${width} ]]; then
    filled="${width}"
  fi
  for ((i = 0; i < filled; i++)); do
    s+="▓"
  done
  for ((i = filled; i < width; i++)); do
    s+="░"
  done
  printf '%s' "${s}"
}

#######################################
# Emit a percent bar line via progress_emit.
# Arguments:
#   $1  Current
#   $2  Total
#   $3  Label
#   $4  Extra (optional)
# Outputs:
#   Progress on stderr
# Returns:
#   0
#######################################
progress_bar() {
  local cur="${1:-0}"
  local total="${2:-0}"
  local label="${3:-}"
  local extra="${4:-}"
  local pct=0 filled=0 width=20 body
  if [[ ${total} -gt 0 ]]; then
    pct=$((cur * 100 / total))
    filled=$((cur * width / total))
  fi
  body="$(progress_bar_fill "${filled}" "${width}") ${pct}%  ${cur}/${total}"
  if [[ -n ${label} ]]; then
    body+="  ${label}"
  fi
  if [[ -n ${extra} ]]; then
    body+="  ${extra}"
  fi
  progress_emit "${body}"
}

#######################################
# Emit a progress line: rewrite on TTY stderr, log newline otherwise.
# Globals:
#   GREEN, NC, _PROGRESS_ON_TTY
# Arguments:
#   $1  Body line (without prefix)
# Outputs:
#   Progress to stderr
# Returns:
#   0
#######################################
progress_emit() {
  local body="${1:-}"
  if [[ -t 2 ]] && progress_enabled; then
    if progress_use_color; then
      printf '\r\033[K%s[ez-comfy]%s %s' "${GREEN}" "${NC}" "${body}" >&2
    else
      printf '\r\033[K[ez-comfy] %s' "${body}" >&2
    fi
    _PROGRESS_ON_TTY=1
  else
    log "${body}"
  fi
}

#######################################
# End a TTY progress rewrite so the next log starts on a new line.
# Globals:
#   _PROGRESS_ON_TTY
# Outputs:
#   Optional newline on stderr
# Returns:
#   0
#######################################
progress_newline() {
  if [[ ${_PROGRESS_ON_TTY:-0} == "1" ]]; then
    printf '\n' >&2
    _PROGRESS_ON_TTY=0
  fi
}

#######################################
# Heartbeat body: label + elapsed.
# Arguments:
#   $1  Label
#   $2  Start unix timestamp
# Outputs:
#   Newline log (never rewrites — command may also use stderr)
# Returns:
#   0
#######################################
progress_heartbeat() {
  local label="${1:-}"
  local start_ts="${2:-0}"
  local now elapsed
  now="$(date +%s)"
  elapsed=$((now - start_ts))
  if [[ ${elapsed} -lt 0 ]]; then
    elapsed=0
  fi
  log "… ${label}  elapsed $(progress_format_elapsed "${elapsed}")  (still running)"
}

#######################################
# Run a command with periodic stderr heartbeats. Does not steal stdout.
# Heartbeats are newlines so they do not smash the command's own TTY output.
# Globals:
#   EZ_COMFY_PROGRESS, EZ_COMFY_PROGRESS_INTERVAL
# Arguments:
#   $1  Label
#   $2  Optional --
#   $@  Command
# Outputs:
#   Start/heartbeat/end on stderr; command stdout/stderr
# Returns:
#   Command exit status
#######################################
run_with_heartbeat() {
  local label="${1:?run_with_heartbeat requires label}"
  shift
  if [[ ${1:-} == "--" ]]; then
    shift
  fi
  local start_ts hb_pid="" rc=0 interval
  start_ts="$(date +%s)"
  log "${label}…"
  interval="$(progress_interval_s)"
  if progress_enabled && [[ ${interval} != "0" && ${interval} != "0.0" ]]; then
    (
      while true; do
        sleep "${interval}"
        progress_heartbeat "${label}" "${start_ts}"
      done
    ) &
    hb_pid=$!
    disown "${hb_pid}" 2>/dev/null || true
  fi
  set +e
  "$@"
  rc=$?
  set -e
  if [[ -n ${hb_pid} ]]; then
    kill "${hb_pid}" 2>/dev/null || true
    wait "${hb_pid}" 2>/dev/null || true
  fi
  progress_newline
  if [[ ${rc} -eq 0 ]]; then
    log_ok "${label} ($(progress_format_elapsed $(($(date +%s) - start_ts))))"
  else
    err "${label} failed (elapsed $(progress_format_elapsed $(($(date +%s) - start_ts))))"
  fi
  return "${rc}"
}

#######################################
# First -t duration token from an ffmpeg argv (seconds), or empty.
# Arguments:
#   $@  ffmpeg args (with or without leading ffmpeg)
# Outputs:
#   Duration string on stdout when present
# Returns:
#   0
#######################################
ffmpeg_duration_from_args() {
  local prev="" a
  for a in "$@"; do
    if [[ ${prev} == "-t" ]]; then
      printf '%s\n' "${a}"
      return 0
    fi
    prev="${a}"
  done
  printf ''
}

#######################################
# Last out_time from an ffmpeg -progress file, in seconds.
# Arguments:
#   $1  Progress file path
# Outputs:
#   Seconds (float) on stdout
# Returns:
#   0
#######################################
progress_ffmpeg_out_time_s() {
  local file="${1:-}"
  local ms=0 us=0
  if [[ -z ${file} || ! -f ${file} ]]; then
    echo 0
    return 0
  fi
  ms="$(awk -F= '/^out_time_ms=/ { v=$2 } END { print v+0 }' "${file}")"
  if [[ ${ms} -gt 0 ]]; then
    awk -v m="${ms}" 'BEGIN { printf "%.1f", m / 1000 }'
    return 0
  fi
  us="$(awk -F= '/^out_time_us=/ { v=$2 } END { print v+0 }' "${file}")"
  awk -v u="${us}" 'BEGIN { printf "%.1f", u / 1000000 }'
}

#######################################
# True when ffmpeg wrote progress=end.
# Arguments:
#   $1  Progress file path
# Returns:
#   0 when ended; 1 otherwise
#######################################
progress_ffmpeg_ended() {
  local file="${1:-}"
  [[ -n ${file} && -f ${file} ]] || return 1
  grep -q '^progress=end' "${file}"
}

#######################################
# Run ffmpeg with a start/end banner. When progress is on, parse -progress file.
# When EZ_COMFY_PROGRESS=0 the argv is unchanged (hermetic ffmpeg mocks).
# Globals:
#   EZ_COMFY_PROGRESS, EZ_COMFY_PROGRESS_INTERVAL
# Arguments:
#   $1  Label
#   $2  Optional --
#   $@  ffmpeg command (ffmpeg must be argv0)
# Outputs:
#   Progress on stderr; ffmpeg writes the output file
# Returns:
#   ffmpeg exit status
#######################################
run_ffmpeg_logged() {
  local label="${1:?run_ffmpeg_logged requires label}"
  shift
  if [[ ${1:-} == "--" ]]; then
    shift
  fi
  local start_ts rc=0 interval prog="" fpid="" dur="" now elapsed body tsec
  start_ts="$(date +%s)"
  log "${label}…"
  interval="$(progress_interval_s)"
  dur="$(ffmpeg_duration_from_args "$@")"

  if ! progress_enabled || [[ ${interval} == "0" || ${interval} == "0.0" ]]; then
    set +e
    "$@"
    rc=$?
    set -e
    if [[ ${rc} -eq 0 ]]; then
      log_ok "${label} ($(progress_format_elapsed $(($(date +%s) - start_ts))))"
    else
      err "${label} failed (elapsed $(progress_format_elapsed $(($(date +%s) - start_ts))))"
    fi
    return "${rc}"
  fi

  prog="$(mktemp)"
  local -a cmd=("$@")
  if [[ ${cmd[0]} == "ffmpeg" ]]; then
    cmd=(
      ffmpeg -nostats -hide_banner -loglevel error
      -progress "file:${prog}"
      "${cmd[@]:1}"
    )
  fi

  set +e
  "${cmd[@]}" &
  fpid=$!
  while kill -0 "${fpid}" 2>/dev/null; do
    sleep "${interval}"
    tsec="$(progress_ffmpeg_out_time_s "${prog}")"
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ -n ${dur} && ${dur} != "0" ]]; then
      body="$(printf 'encoding %s  %ss / %ss  elapsed %s' \
        "${label}" "${tsec}" "${dur}" "$(progress_format_elapsed "${elapsed}")")"
    else
      body="$(printf 'encoding %s  t=%ss  elapsed %s' \
        "${label}" "${tsec}" "$(progress_format_elapsed "${elapsed}")")"
    fi
    progress_emit "${body}"
  done
  wait "${fpid}"
  rc=$?
  set -e
  progress_newline
  rm -f "${prog}"
  if [[ ${rc} -eq 0 ]]; then
    log_ok "${label} ($(progress_format_elapsed $(($(date +%s) - start_ts))))"
  else
    err "${label} failed (elapsed $(progress_format_elapsed $(($(date +%s) - start_ts))))"
  fi
  return "${rc}"
}

# Hugging Face helpers kept as names so existing BATS stay green.
hf_format_mib() { progress_format_mib "$@"; }
hf_format_rate() { progress_format_rate "$@"; }
hf_format_elapsed() { progress_format_elapsed "$@"; }
hf_progress_emit() { progress_emit "$@"; }
hf_progress_newline() { progress_newline "$@"; }
