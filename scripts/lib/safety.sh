#!/usr/bin/env bash
# ## safety
#
# Preflight checks, heavy confirmation, and host headroom for remote Spark safety.
#
# Purpose:
#   DGX Spark hosts are often operated over the internet without physical access.
#   Starting a 90 GiB-class ComfyUI stack without free RAM/disk headroom can make
#   SSH unresponsive. This library enforces explicit operator consent and minimum
#   free resources before heavy work begins.
#
# Invariants:
#   - Heavy workloads never auto-start (Compose restart policy is "no"; this lib
#     only gates explicit start paths).
#   - Interactive start requires typing "yes" (case-insensitive full word).
#   - Non-interactive automation requires LAB_NON_INTERACTIVE=1 and a matching
#     LAB_CONFIRM_TOKEN (yes for start, DELETE for cleanup).
#
# Audience:
#   Sourced by manage.sh (and tests). Depends on common.sh (log/warn/err) and
#   paths.sh (lab_models_dir) being available in the caller.
#
# Environment (defaults applied if unset):
#   MIN_HOST_FREE_GIB   — minimum free host RAM in GiB (default 28)
#   MIN_DISK_FREE_GIB   — minimum free disk on models path in GiB (default 40)
#   MEM_LIMIT           — Docker mem_limit string, e.g. 90g (default 90g)
#   LAB_MOCK_FREE_MEM_GIB / LAB_MOCK_DISK_FREE_GIB — hermetic test overrides
#   LAB_NON_INTERACTIVE / LAB_CONFIRM_TOKEN — automation confirm path
#

# Defaults (overridable via env / .env)
: "${MIN_HOST_FREE_GIB:=28}"
: "${MIN_DISK_FREE_GIB:=40}"
: "${MEM_LIMIT:=90g}"

#######################################
# Gate a heavy GPU/memory action behind explicit operator confirmation.
# Interactive mode prompts on the TTY and accepts only the word "yes"
# (case-insensitive). Non-interactive mode (LAB_NON_INTERACTIVE=1) requires
# LAB_CONFIRM_TOKEN=yes; any other token fails closed.
# Exit codes are intentional for manage.sh:
#   0 — confirmed, proceed
#   1 — hard failure (automation missing token)
#   2 — user aborted interactively (manage treats as soft exit 0)
# Side effects: Reads stdin when interactive; writes warnings to stderr.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Human-readable action label (default: "workload").
#   $2  Optional extra warning printed before the heavy banner.
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 confirm, 1 automation failure, 2 interactive abort.
#######################################
require_heavy_confirm() {
  local label="${1:-workload}"
  local extra="${2:-}"
  if [[ -n ${extra} ]]; then
    warn "${extra}"
  fi
  warn "=== HEAVY WORKLOAD: ${label} ==="
  warn "Uses large unified memory + GPU. Prefer remote headroom for SSH."
  if [[ ${LAB_NON_INTERACTIVE:-} == "1" ]]; then
    if [[ ${LAB_CONFIRM_TOKEN:-} == "yes" ]]; then
      log "Non-interactive confirm accepted for ${label}"
      return 0
    fi
    err "Non-interactive start requires LAB_CONFIRM_TOKEN=yes"
    return 1
  fi
  echo >&2
  local response
  read -r -p "Start ${label}? Type yes to continue: " response
  if [[ ${response} =~ ^[Yy][Ee][Ss]$ ]]; then
    return 0
  fi
  log "Aborted by user."
  return 2
}

#######################################
# Gate destructive cleanup (volume removal) behind an exact DELETE confirmation.
# Interactive mode requires typing DELETE exactly. Non-interactive mode requires
# LAB_NON_INTERACTIVE=1 and LAB_CONFIRM_TOKEN=DELETE.
# Side effects: Reads stdin when interactive; writes to stderr.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 confirm, 1 automation failure, 2 interactive abort.
#######################################
require_delete_confirm() {
  if [[ ${LAB_NON_INTERACTIVE:-} == "1" ]]; then
    if [[ ${LAB_CONFIRM_TOKEN:-} == "DELETE" ]]; then
      return 0
    fi
    err "Non-interactive cleanup requires LAB_CONFIRM_TOKEN=DELETE"
    return 1
  fi
  local response
  read -r -p "Type DELETE to remove Comfy state volume: " response
  if [[ ${response} == "DELETE" ]]; then
    return 0
  fi
  log "Aborted by user."
  return 2
}

#######################################
# Convert a Docker-style memory limit string into integer GiB (floor).
# Accepts forms used by Compose mem_limit / mem_reservation:
#   - NNg / NNG → N GiB
#   - NNm / NNM → floor(N/1024) GiB
#   - bare integer → treated as bytes, converted to GiB
# Unparseable input yields 0 so callers can skip soft checks.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Memory string (default "0").
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Prints integer GiB on stdout; always exit 0.
#######################################
parse_gib_from_mem_limit() {
  local raw="${1:-0}"
  local num unit
  if [[ ${raw} =~ ^([0-9]+)([gGmM])$ ]]; then
    num="${BASH_REMATCH[1]}"
    unit="${BASH_REMATCH[2]}"
    case "${unit}" in
      g | G) echo "${num}" ;;
      m | M) echo $((num / 1024)) ;;
      *) echo 0 ;;
    esac
    return 0
  fi
  if [[ ${raw} =~ ^([0-9]+)$ ]]; then
    # assume bytes
    echo $((raw / 1024 / 1024 / 1024))
    return 0
  fi
  echo 0
}

#######################################
# Estimate currently free host memory in whole GiB.
# Resolution order:
#   1. LAB_MOCK_FREE_MEM_GIB (hermetic tests)
#   2. Linux MemAvailable from /proc/meminfo
#   3. macOS vm_stat free+inactive+speculative pages
#   4. 0 if unknown (fail closed at check_host_headroom)
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Prints integer GiB on stdout; exit 0.
#######################################
host_free_mem_gib() {
  if [[ -n ${LAB_MOCK_FREE_MEM_GIB:-} ]]; then
    echo "${LAB_MOCK_FREE_MEM_GIB}"
    return 0
  fi
  if [[ -f /proc/meminfo ]]; then
    awk '/MemAvailable:/ {printf "%d", $2/1024/1024; exit}' /proc/meminfo
    return 0
  fi
  if command -v vm_stat >/dev/null 2>&1; then
    # macOS approximate free+inactive pages
    local page_size free inactive speculative
    page_size=$(pagesize 2>/dev/null || echo 4096)
    free=$(vm_stat | awk '/Pages free/ {gsub("\\.","",$3); print $3}')
    inactive=$(vm_stat | awk '/Pages inactive/ {gsub("\\.","",$3); print $3}')
    speculative=$(vm_stat | awk '/Pages speculative/ {gsub("\\.","",$3); print $3}')
    free=${free:-0}
    inactive=${inactive:-0}
    speculative=${speculative:-0}
    echo $(((free + inactive + speculative) * page_size / 1024 / 1024 / 1024))
    return 0
  fi
  echo 0
}

#######################################
# Report free disk space for a path in whole GiB using `df -Pk`.
#            If the path is missing, falls back to `/`.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Filesystem path to measure (default MODELS_DIR or `/`).
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Prints integer GiB on stdout. Honors LAB_MOCK_DISK_FREE_GIB in tests.
#######################################
host_disk_free_gib() {
  local path="${1:-${MODELS_DIR:-/}}"
  if [[ -n ${LAB_MOCK_DISK_FREE_GIB:-} ]]; then
    echo "${LAB_MOCK_DISK_FREE_GIB}"
    return 0
  fi
  if [[ ! -d ${path} ]]; then
    path="/"
  fi
  df -Pk "${path}" 2>/dev/null | awk 'NR==2 {printf "%d", $4/1024/1024}'
}

#######################################
# Fail if free host RAM or models-disk free space is below policy thresholds.
# Compares host_free_mem_gib / host_disk_free_gib against MIN_HOST_FREE_GIB and
# MIN_DISK_FREE_GIB. On failure, prints actionable errors about remote SSH risk.
# Side effects: Logs progress and errors to stderr. Requires lab_models_dir when available.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 if both thresholds satisfied; 1 if either is short.
#######################################
check_host_headroom() {
  local free_ram free_disk
  free_ram=$(host_free_mem_gib)
  free_disk=$(host_disk_free_gib "$(lab_models_dir 2>/dev/null || echo /mnt/models)")
  free_ram=${free_ram:-0}
  free_disk=${free_disk:-0}
  log "Host free RAM ≈ ${free_ram} GiB (need ≥ ${MIN_HOST_FREE_GIB})"
  log "Host free disk ≈ ${free_disk} GiB (need ≥ ${MIN_DISK_FREE_GIB})"
  if [[ ${free_ram} -lt ${MIN_HOST_FREE_GIB} ]]; then
    err "Insufficient free memory: ${free_ram} GiB < ${MIN_HOST_FREE_GIB} GiB headroom"
    err "Stop other GPU/memory workloads and retry. Do not risk locking out remote SSH."
    return 1
  fi
  if [[ ${free_disk} -lt ${MIN_DISK_FREE_GIB} ]]; then
    err "Insufficient free disk: ${free_disk} GiB < ${MIN_DISK_FREE_GIB} GiB"
    return 1
  fi
  return 0
}

#######################################
# Soft-warn when container MEM_LIMIT plus host headroom exceeds 128 GiB unified memory.
# DGX Spark GB10 has 128 GiB unified memory. If MEM_LIMIT + MIN_HOST_FREE_GIB is
# greater than 128, the configuration is likely to thrash under load. This check
# never fails the start path—only warns—so operators can still force a start after
# acknowledging the risk.
# Side effects: May warn on stderr.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Always 0.
#######################################
check_mem_limit_vs_headroom() {
  local limit_gib total=128
  limit_gib=$(parse_gib_from_mem_limit "${MEM_LIMIT}")
  if [[ ${limit_gib} -le 0 ]]; then
    warn "Could not parse MEM_LIMIT=${MEM_LIMIT}; skipping budget check"
    return 0
  fi
  if [[ $((limit_gib + MIN_HOST_FREE_GIB)) -gt ${total} ]]; then
    warn "MEM_LIMIT (${limit_gib} GiB) + headroom (${MIN_HOST_FREE_GIB}) exceeds ${total} GiB unified memory"
    warn "On DGX Spark this may thrash or freeze SSH under load."
  fi
  return 0
}
