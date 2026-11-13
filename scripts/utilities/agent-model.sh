#!/usr/bin/env bash
#
# ## agent-model
#
# Host launcher for the optional Qwen3.8-Flash-Next editing agent: the
# MiaAI-Lab TensorFold recipe pinned to one commit lane, run on a single
# DGX Spark as a unified-memory co-tenant beside ComfyUI.
#
# This utility owns the operator path only: preflight, consent, the pinned
# clone/update, the co-tenant profile env, and the recipe's own start.sh /
# stop.sh. The recipe owns the container and the weights.
#
# Usage:
#   bazelisk run //scripts:run-utility -- agent-model status [--json]
#   bazelisk run //scripts:run-utility -- agent-model run
#   bazelisk run //scripts:run-utility -- agent-model stop
#
# Environment:
#   AGENT_MODEL_HOME, AGENT_MODEL_REPO, AGENT_MODEL_REF, AGENT_MODEL_PORT,
#   AGENT_MODEL_HOST (or HOST), AGENT_MODEL_READY_S, AGENT_MODEL_MIN_DISK_GB,
#   AGENT_MODEL_MIN_MEM_GIB, AGENT_MODEL_MEMINFO_FILE, AGENT_MODEL_ASSUME_YES,
#   AGENT_MODEL_POLL_INTERVAL_S, AGENT_MODEL_CURL_MAX_TIME_S, HF_HOME,
#   COMFY_OUTPUT_DIR, LAB_NON_INTERACTIVE, LAB_CONFIRM_TOKEN, and the external
#   command indirections AGENT_MODEL_{GIT,DOCKER,CURL,DF}_BIN.
#
# Safety:
#   Bind 127.0.0.1 only - a non-loopback HOST is refused. Heavy confirm before
#   the ~160 GB download. Refuses while a heavy GPU occupancy mode (wan / ltx /
#   trellis / klein) holds the Spark. Does not start Compose. Does not touch
#   restart: "no", mem_limit, or the headroom preflight.
#
# Exit codes:
#   0 ok; 1 usage or general error; 2 occupancy refuse; 4 preflight refuse
#   (tool, bind, disk, memory); 5 the operator declined the heavy confirm.
#
# @command agent-model

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/occupancy.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/occupancy.sh"
# shellcheck source=../lib/safety.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/safety.sh"

JSON_FLAG=""
CMD="status"

# Pinned recipe identity (do not drift; docs/agent-model.md quotes these).
readonly AGENT_MODEL_REPO_DEFAULT="https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Single-DGX-Spark-TensorFold"
readonly AGENT_MODEL_HOME_NAME_DEFAULT="qwen38-flash-next-tf"
readonly AGENT_MODEL_REF_DEFAULT="main"
readonly AGENT_MODEL_BIND_DEFAULT="127.0.0.1"
readonly AGENT_MODEL_PORT_DEFAULT="30001"
readonly AGENT_MODEL_READY_S_DEFAULT="900"
readonly AGENT_MODEL_MIN_DISK_GB_DEFAULT="160"
readonly AGENT_MODEL_MIN_MEM_GIB_DEFAULT="110"
readonly AGENT_MODEL_POLL_INTERVAL_S_DEFAULT="1"
readonly AGENT_MODEL_CURL_MAX_TIME_S_DEFAULT="5"
# Pinned single-Spark co-tenant profile (authors measured ~81 GiB weights).
readonly AGENT_MODEL_SERVED_NAME_DEFAULT="Qwen3.8-Flash-Next"
readonly AGENT_MODEL_PARALLEL_DEFAULT="2"
readonly AGENT_MODEL_CONTEXT_DEFAULT="32768"
readonly AGENT_MODEL_MAX_TOKENS_DEFAULT="4096"
readonly AGENT_MODEL_KV_DTYPE_DEFAULT="fp8"
readonly AGENT_MODEL_VISION_DEFAULT="0"
readonly AGENT_MODEL_THINKING_DEFAULT="1"
readonly AGENT_MODEL_CONTAINER_DEFAULT="ez-agent-model"
readonly AGENT_MODEL_MEM_FLOOR_GIB_DEFAULT="9"
# Occupancy modes that hold the GPU: the agent is refused while any is live.
readonly -a AGENT_MODEL_HEAVY_MODES=(klein trellis wan ltx)
# Exit codes (documented in the file header).
readonly AGENT_MODEL_E_USAGE=1
readonly AGENT_MODEL_E_OCCUPANCY=2
readonly AGENT_MODEL_E_PREFLIGHT=4
readonly AGENT_MODEL_E_DECLINED=5

#######################################
# Print agent-model help.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: agent-model.sh status [--json] | run | stop" >&2
  echo "  Host launcher for the optional Qwen3.8-Flash-Next agent (TensorFold recipe)." >&2
  echo "  Bind 127.0.0.1 only. Heavy confirm (~160 GB download + GPU)." >&2
  echo "  Refused while occupancy is wan / ltx / trellis / klein, or a desk sidecar is live." >&2
  echo "  An orphaned desk record (sidecar gone) does not refuse. See docs/occupancy.md." >&2
  echo "  Exit: 2 occupancy refuse, 4 preflight refuse, 5 confirm declined." >&2
}

#######################################
# Absolute clone target for the pinned recipe checkout.
# Globals:
#   AGENT_MODEL_HOME, HOME
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
agent_home() {
  printf '%s\n' "${AGENT_MODEL_HOME:-${HOME:-/root}/${AGENT_MODEL_HOME_NAME_DEFAULT}}"
}

#######################################
# Upstream recipe URL.
# Globals:
#   AGENT_MODEL_REPO
# Arguments:
#   None
# Outputs:
#   URL on stdout
# Returns:
#   0
#######################################
agent_repo() {
  printf '%s\n' "${AGENT_MODEL_REPO:-${AGENT_MODEL_REPO_DEFAULT}}"
}

#######################################
# Pinned recipe ref (branch or tag name). Falls back to the pin when empty.
# Globals:
#   AGENT_MODEL_REF
# Arguments:
#   None
# Outputs:
#   Ref on stdout
# Returns:
#   0
#######################################
agent_ref() {
  local ref="${AGENT_MODEL_REF:-${AGENT_MODEL_REF_DEFAULT}}"
  if [[ -z ${ref} ]]; then
    ref="${AGENT_MODEL_REF_DEFAULT}"
  fi
  printf '%s\n' "${ref}"
}

#######################################
# Serve port, digits only.
# Globals:
#   AGENT_MODEL_PORT
# Arguments:
#   None
# Outputs:
#   Port on stdout
# Returns:
#   0
#######################################
agent_port() {
  local port="${AGENT_MODEL_PORT:-${AGENT_MODEL_PORT_DEFAULT}}"
  if [[ ! ${port} =~ ^[1-9][0-9]*$ ]]; then
    port="${AGENT_MODEL_PORT_DEFAULT}"
  fi
  printf '%s\n' "${port}"
}

#######################################
# Loopback bind host (refuse 0.0.0.0 and any other non-localhost bind).
# Globals:
#   AGENT_MODEL_HOST, HOST
# Arguments:
#   None
# Outputs:
#   Host on stdout; error on stderr when the bind is not loopback
# Returns:
#   0; 1 when the bind host is not loopback
#######################################
agent_bind_host() {
  local host="${AGENT_MODEL_HOST:-${HOST:-${AGENT_MODEL_BIND_DEFAULT}}}"
  case "${host}" in
    "" | 127.0.0.1 | localhost)
      printf '%s\n' "127.0.0.1"
      return 0
      ;;
    *)
      err "agent-model bind host must be 127.0.0.1 (got ${host})"
      return 1
      ;;
  esac
}

#######################################
# Container name the recipe runs under (status probes this).
# Globals:
#   CONTAINER_NAME
# Arguments:
#   None
# Outputs:
#   Container name on stdout
# Returns:
#   0
#######################################
agent_container_name() {
  printf '%s\n' "${CONTAINER_NAME:-${AGENT_MODEL_CONTAINER_DEFAULT}}"
}

#######################################
# Health URL the launcher polls once the recipe is up.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   URL on stdout; error on stderr for a non-loopback bind
# Returns:
#   0; 1 when the bind host is not loopback
#######################################
agent_health_url() {
  local host port
  host="$(agent_bind_host)" || return 1
  port="$(agent_port)"
  printf 'http://%s:%s/health\n' "${host}" "${port}"
}

#######################################
# Whole-number seconds before the health poll gives up.
# Globals:
#   AGENT_MODEL_READY_S
# Arguments:
#   None
# Outputs:
#   Seconds on stdout
# Returns:
#   0
#######################################
agent_ready_s() {
  local secs="${AGENT_MODEL_READY_S:-${AGENT_MODEL_READY_S_DEFAULT}}"
  if [[ ! ${secs} =~ ^[1-9][0-9]*$ ]]; then
    secs="${AGENT_MODEL_READY_S_DEFAULT}"
  fi
  printf '%s\n' "${secs}"
}

#######################################
# Minimum free disk in GB required on the HF cache filesystem.
# Globals:
#   AGENT_MODEL_MIN_DISK_GB
# Arguments:
#   None
# Outputs:
#   GiB on stdout
# Returns:
#   0
#######################################
agent_min_disk_gb() {
  local want="${AGENT_MODEL_MIN_DISK_GB:-${AGENT_MODEL_MIN_DISK_GB_DEFAULT}}"
  if [[ ! ${want} =~ ^[0-9]+$ ]]; then
    want="${AGENT_MODEL_MIN_DISK_GB_DEFAULT}"
  fi
  printf '%s\n' "${want}"
}

#######################################
# Minimum MemAvailable in GiB required before the load (~81 GiB weights).
# Globals:
#   AGENT_MODEL_MIN_MEM_GIB
# Arguments:
#   None
# Outputs:
#   GiB on stdout
# Returns:
#   0
#######################################
agent_min_mem_gib() {
  local want="${AGENT_MODEL_MIN_MEM_GIB:-${AGENT_MODEL_MIN_MEM_GIB_DEFAULT}}"
  if [[ ! ${want} =~ ^[0-9]+$ ]]; then
    want="${AGENT_MODEL_MIN_MEM_GIB_DEFAULT}"
  fi
  printf '%s\n' "${want}"
}

#######################################
# meminfo file to read (overridable so bats can fake MemAvailable).
# Globals:
#   AGENT_MODEL_MEMINFO_FILE
# Arguments:
#   None
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
agent_meminfo_file() {
  printf '%s\n' "${AGENT_MODEL_MEMINFO_FILE:-/proc/meminfo}"
}

#######################################
# Filesystem the weights land on (probe target for the disk preflight).
# Globals:
#   HF_HOME, HOME
# Arguments:
#   None
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
agent_hf_home() {
  printf '%s\n' "${HF_HOME:-${HOME:-/root}/.cache/huggingface}"
}

#######################################
# Run git through the overridable indirection (bats stubs it).
# Globals:
#   AGENT_MODEL_GIT_BIN
# Arguments:
#   $@  git argv
# Outputs:
#   Whatever git prints
# Returns:
#   git status
#######################################
agent_run_git() {
  "${AGENT_MODEL_GIT_BIN:-git}" "$@"
}

#######################################
# Run docker through the overridable indirection (bats stubs it).
# Globals:
#   AGENT_MODEL_DOCKER_BIN
# Arguments:
#   $@  docker argv
# Outputs:
#   Whatever docker prints
# Returns:
#   docker status
#######################################
agent_run_docker() {
  "${AGENT_MODEL_DOCKER_BIN:-docker}" "$@"
}

#######################################
# Run curl through the overridable indirection (bats stubs it).
# Globals:
#   AGENT_MODEL_CURL_BIN
# Arguments:
#   $@  curl argv
# Outputs:
#   Whatever curl prints
# Returns:
#   curl status
#######################################
agent_run_curl() {
  "${AGENT_MODEL_CURL_BIN:-curl}" "$@"
}

#######################################
# Run df through the overridable indirection (bats stubs it).
# Globals:
#   AGENT_MODEL_DF_BIN
# Arguments:
#   $@  df argv
# Outputs:
#   Whatever df prints
# Returns:
#   df status
#######################################
agent_run_df() {
  "${AGENT_MODEL_DF_BIN:-df}" "$@"
}

#######################################
# Run a recipe script (./start.sh, ./stop.sh) from the pinned checkout.
# Globals:
#   AGENT_MODEL_SHELL_BIN
# Arguments:
#   $1  Script file name inside the checkout
# Outputs:
#   Recipe output; error on stderr when the file is missing
# Returns:
#   0; 1 when the script is missing or exits non-zero
#######################################
agent_run_recipe_script() {
  local name="${1:?agent_run_recipe_script needs a script name}"
  local script
  script="$(agent_home)/${name}"
  if [[ ! -f ${script} ]]; then
    err "recipe script missing: ${script} - re-run: agent-model.sh run"
    return 1
  fi
  run_with_heartbeat "agent-model ${name}" -- "${AGENT_MODEL_SHELL_BIN:-bash}" "${script}"
}

#######################################
# Export an env var only when the operator has not set it.
# Globals:
#   named by $1
# Arguments:
#   $1  Variable name
#   $2  Pinned default value
# Outputs:
#   None
# Returns:
#   0
#######################################
agent_env_default() {
  local key="${1}" value="${2}"
  if [[ -z ${!key+x} ]]; then
    export "${key}=${value}"
  fi
}

#######################################
# Export the pinned single-Spark co-tenant profile for the recipe.
# HOST/PORT come from the validated loopback bind + port; every value keeps an
# operator override that was already in the environment.
# Globals:
#   HOST, PORT, SERVED_NAME, PARALLEL, CONTEXT, MAX_TOKENS, KV_DTYPE, VISION,
#   THINKING, TENSORFOLD_NO_UPDATE_CHECK, CONTAINER_NAME, MEM_FLOOR_GIB
# Arguments:
#   None
# Outputs:
#   Exported environment; log of the resolved profile
# Returns:
#   0; 1 when the bind host is not loopback
#######################################
agent_export_profile() {
  local host port
  host="$(agent_bind_host)" || return 1
  port="$(agent_port)"
  agent_env_default HOST "${host}"
  agent_env_default PORT "${port}"
  agent_env_default SERVED_NAME "${AGENT_MODEL_SERVED_NAME_DEFAULT}"
  agent_env_default PARALLEL "${AGENT_MODEL_PARALLEL_DEFAULT}"
  agent_env_default CONTEXT "${AGENT_MODEL_CONTEXT_DEFAULT}"
  agent_env_default MAX_TOKENS "${AGENT_MODEL_MAX_TOKENS_DEFAULT}"
  agent_env_default KV_DTYPE "${AGENT_MODEL_KV_DTYPE_DEFAULT}"
  agent_env_default VISION "${AGENT_MODEL_VISION_DEFAULT}"
  agent_env_default THINKING "${AGENT_MODEL_THINKING_DEFAULT}"
  agent_env_default TENSORFOLD_NO_UPDATE_CHECK "1"
  agent_env_default CONTAINER_NAME "${AGENT_MODEL_CONTAINER_DEFAULT}"
  agent_env_default MEM_FLOOR_GIB "${AGENT_MODEL_MEM_FLOOR_GIB_DEFAULT}"
  log "co-tenant profile host=${HOST} port=${PORT} served=${SERVED_NAME} parallel=${PARALLEL} context=${CONTEXT} max_tokens=${MAX_TOKENS} kv=${KV_DTYPE} vision=${VISION} thinking=${THINKING}"
}

#######################################
# Require the external CLIs the launcher shells out to.
# Globals:
#   AGENT_MODEL_GIT_BIN, AGENT_MODEL_DOCKER_BIN, AGENT_MODEL_CURL_BIN
# Arguments:
#   None
# Outputs:
#   Errors on stderr naming each missing tool
# Returns:
#   0; 4 when a tool is absent
#######################################
agent_require_tools() {
  local name bin rc=0
  for name in git docker curl; do
    case "${name}" in
      git) bin="${AGENT_MODEL_GIT_BIN:-git}" ;;
      docker) bin="${AGENT_MODEL_DOCKER_BIN:-docker}" ;;
      curl) bin="${AGENT_MODEL_CURL_BIN:-curl}" ;;
    esac
    if ! command -v "${bin}" >/dev/null 2>&1; then
      err "agent-model needs ${name} (${bin} not found on PATH)"
      rc="${AGENT_MODEL_E_PREFLIGHT}"
    fi
  done
  return "${rc}"
}

#######################################
# Free space in whole GiB on the weights filesystem (falls back to / when the
# HF cache path does not exist yet, which is the first-run case).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   GiB on stdout; error on stderr when df fails
# Returns:
#   0; 1 when df cannot read the path
#######################################
agent_disk_free_gb() {
  local path out=""
  path="$(agent_hf_home)"
  [[ -d ${path} ]] || path="/"
  if ! out="$(agent_run_df -Pk "${path}" 2>/dev/null)"; then
    err "agent-model cannot read free disk on ${path}"
    return 1
  fi
  printf '%s\n' "${out}" | awk 'NR==2 {printf "%d", $4/1024/1024}'
}

#######################################
# MemAvailable in whole GiB, read straight from the meminfo file so hermetic
# tests can point AGENT_MODEL_MEMINFO_FILE at a fixture (no LAB_MOCK_* path).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   GiB on stdout (0 when unknown); error on stderr when unreadable
# Returns:
#   0; 1 when the meminfo file is not readable
#######################################
agent_mem_available_gib() {
  local file out
  file="$(agent_meminfo_file)"
  if [[ ! -r ${file} ]]; then
    err "agent-model cannot read ${file} for MemAvailable"
    return 1
  fi
  out="$(awk '/^MemAvailable:/ {printf "%d", $2/1024/1024; found=1; exit} END {if (!found) printf "0"}' "${file}")"
  printf '%s\n' "${out:-0}"
}

#######################################
# Current occupancy mode (lib helper when sourced, file fallback otherwise).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Mode on stdout (idle when unknown)
# Returns:
#   0
#######################################
agent_occupancy_mode() {
  local mode=""
  if declare -F occupancy_mode >/dev/null 2>&1; then
    mode="$(occupancy_mode)"
  else
    mode="$(agent_occupancy_mode_file)"
  fi
  printf '%s\n' "${mode:-idle}"
}

#######################################
# Read the mode field out of .occupancy.json without the occupancy lib.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Mode on stdout (idle when missing or unparsable)
# Returns:
#   0
#######################################
agent_occupancy_mode_file() {
  local path mode
  path="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/.occupancy.json"
  mode=""
  if [[ -f ${path} ]]; then
    mode="$(python3 -c 'import json,sys
try:
    print(json.load(open(sys.argv[1])).get("mode") or "")
except Exception:
    print("")' "${path}" 2>/dev/null || true)"
  fi
  printf '%s\n' "${mode:-idle}"
}

#######################################
# Refuse the agent while a live GPU claim owns the Spark.
# A heavy mode is a claim on its own; a desk mode is one only while its
# sidecar process lives, which occupancy_desk_held decides from the recorded
# PIDs. A desk the operator never shut down (sidecar killed, host rebooted)
# therefore does not hold agent-model run down forever.
# Globals:
#   AGENT_MODEL_HEAVY_MODES
#   occupancy_desk_held (scripts/lib/occupancy.sh, when sourced)
# Arguments:
#   None
# Outputs:
#   Errors on stderr when refused
# Returns:
#   0 allowed; 2 refused
#######################################
agent_refuse_heavy_occupancy() {
  local mode heavy
  mode="$(agent_occupancy_mode)"
  for heavy in "${AGENT_MODEL_HEAVY_MODES[@]}"; do
    if [[ ${mode} == "${heavy}" ]]; then
      err "occupancy is ${mode} - stop the visual job before agent-model run"
      err "  bazelisk run //:manage -- occupancy enter idle --yes"
      return "${AGENT_MODEL_E_OCCUPANCY}"
    fi
  done
  if declare -F occupancy_desk_held >/dev/null 2>&1 && occupancy_desk_held "${mode}"; then
    err "occupancy is ${mode} with a live sidecar - release the desk before agent-model run"
    err "  bazelisk run //:manage -- occupancy enter idle --yes"
    return "${AGENT_MODEL_E_OCCUPANCY}"
  fi
  return 0
}

#######################################
# Resource + tool preflight for a run (bind, tools, disk, memory, occupancy).
# Globals:
#   AGENT_MODEL_HEAVY_MODES
# Arguments:
#   None
# Outputs:
#   log_step/log progress; errors on stderr
# Returns:
#   0; 2 occupancy refuse; 4 tool, bind, disk, or memory refuse
#######################################
agent_preflight() {
  local free_gib avail_gib need_disk need_mem
  log_step 1 4 "loopback bind + host tools"
  agent_bind_host >/dev/null || return "${AGENT_MODEL_E_PREFLIGHT}"
  agent_require_tools || return "${AGENT_MODEL_E_PREFLIGHT}"
  need_disk="$(agent_min_disk_gb)"
  log_step 2 4 "free disk on $(agent_hf_home) (need >= ${need_disk} GB)"
  free_gib="$(agent_disk_free_gb || true)"
  if [[ ! ${free_gib} =~ ^[0-9]+$ ]]; then
    err "agent-model cannot measure free disk - refusing the download"
    return "${AGENT_MODEL_E_PREFLIGHT}"
  fi
  if [[ ${free_gib} -lt ${need_disk} ]]; then
    err "free disk ${free_gib} GB < ${need_disk} GB - the recipe download needs the room"
    return "${AGENT_MODEL_E_PREFLIGHT}"
  fi
  log_ok "free disk ${free_gib} GB"
  need_mem="$(agent_min_mem_gib)"
  log_step 3 4 "host MemAvailable (need >= ${need_mem} GiB)"
  avail_gib="$(agent_mem_available_gib || true)"
  if [[ ! ${avail_gib} =~ ^[0-9]+$ ]]; then
    err "agent-model cannot read MemAvailable - refusing the load"
    return "${AGENT_MODEL_E_PREFLIGHT}"
  fi
  if [[ ${avail_gib} -lt ${need_mem} ]]; then
    err "MemAvailable ${avail_gib} GiB < ${need_mem} GiB - free the desk (weights ~81 GiB + reserves)"
    return "${AGENT_MODEL_E_PREFLIGHT}"
  fi
  log_ok "MemAvailable ${avail_gib} GiB"
  log_step 4 4 "occupancy (one heavy GPU job at a time)"
  agent_refuse_heavy_occupancy || return "${AGENT_MODEL_E_OCCUPANCY}"
  return 0
}

#######################################
# Heavy confirm gate for the download + GPU load.
# Globals:
#   AGENT_MODEL_ASSUME_YES, LAB_NON_INTERACTIVE, LAB_CONFIRM_TOKEN
# Arguments:
#   None
# Outputs:
#   Warnings on stderr; reads stdin when interactive
# Returns:
#   0 confirmed; 1 automation failure; 5 operator declined
#######################################
agent_confirm_run() {
  if [[ ${AGENT_MODEL_ASSUME_YES:-} == "1" ]]; then
    warn "AGENT_MODEL_ASSUME_YES=1 - heavy confirm bypassed"
    return 0
  fi
  if ! require_heavy_confirm "agent-model run (Qwen3.8-Flash-Next, ~160 GB download + GPU)" \
    "One heavy GPU job at a time: finish wan / ltx / trellis / klein first."; then
    return "${AGENT_MODEL_E_DECLINED}"
  fi
  return 0
}

#######################################
# Clone the pinned recipe, or fetch + hard-reset an existing checkout.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/log_ok progress; git output; errors on stderr
# Returns:
#   0; 1 on any git failure or a checkout without start.sh
#######################################
agent_sync_repo() {
  local home repo ref parent
  home="$(agent_home)"
  repo="$(agent_repo)"
  ref="$(agent_ref)"
  if [[ -d ${home}/.git ]]; then
    log "updating pinned recipe ${home} at ${ref}"
    agent_run_git -C "${home}" fetch --depth 1 origin "${ref}" || return 1
    agent_run_git -C "${home}" -c advice.detachedHead=false checkout "${ref}" || return 1
    agent_run_git -C "${home}" reset --hard "origin/${ref}" || return 1
  else
    log "cloning pinned recipe ${repo} at ${ref}"
    parent="$(dirname "${home}")"
    mkdir -p "${parent}" || return 1
    agent_run_git -c advice.detachedHead=false clone --depth 1 --branch "${ref}" \
      "${repo}" "${home}" || return 1
  fi
  if [[ ! -f ${home}/start.sh ]]; then
    err "pinned recipe at ${home} has no start.sh - refusing to guess the entrypoint"
    return 1
  fi
  log_ok "recipe ready at ${home} (${ref})"
  return 0
}

#######################################
# One health probe against the recipe /health endpoint.
# Globals:
#   AGENT_MODEL_CURL_MAX_TIME_S
# Arguments:
#   None
# Outputs:
#   None (probe output discarded)
# Returns:
#   0 when /health answers 2xx; 1 otherwise
#######################################
agent_health_ok() {
  local url
  url="$(agent_health_url)" || return 1
  agent_run_curl -fsS --max-time "${AGENT_MODEL_CURL_MAX_TIME_S:-${AGENT_MODEL_CURL_MAX_TIME_S_DEFAULT}}" \
    "${url}" >/dev/null 2>&1
}

#######################################
# Poll /health until it answers or the ready window is spent.
# Globals:
#   AGENT_MODEL_READY_S, AGENT_MODEL_POLL_INTERVAL_S
# Arguments:
#   None
# Outputs:
#   Progress on stderr
# Returns:
#   0 ready; 1 timed out
#######################################
agent_poll_health() {
  local ready_s interval iters i=0 url
  ready_s="$(agent_ready_s)"
  interval="${AGENT_MODEL_POLL_INTERVAL_S:-${AGENT_MODEL_POLL_INTERVAL_S_DEFAULT}}"
  if [[ ! ${interval} =~ ^[0-9]+$ ]] || [[ ${interval} == "0" ]]; then
    iters="${ready_s}"
  else
    iters=$(((ready_s + interval - 1) / interval))
  fi
  url="$(agent_health_url)" || return 1
  while ((i < iters)); do
    if agent_health_ok; then
      return 0
    fi
    i=$((i + 1))
    if ((i < iters)); then
      sleep "${interval}"
    fi
  done
  err "agent-model /health did not answer within ${ready_s}s - see ${url}"
  return 1
}

#######################################
# True when the agent container exists in docker.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None (docker output discarded)
# Returns:
#   0 when present; 1 when absent or docker failed
#######################################
agent_container_exists() {
  agent_run_docker inspect "$(agent_container_name)" >/dev/null 2>&1
}

#######################################
# One docker inspect template field for the agent container.
# Globals:
#   None
# Arguments:
#   $1  Go template (e.g. {{.State.Status}})
# Outputs:
#   Field value on stdout (empty when unavailable)
# Returns:
#   0 always
#######################################
agent_container_field() {
  local template="${1:-}"
  local out=""
  out="$(agent_run_docker inspect -f "${template}" "$(agent_container_name)" 2>/dev/null)" || out=""
  printf '%s\n' "${out}"
}

#######################################
# Resolve the agent state for status (stopped|starting|ready|unhealthy).
# Container absent -> stopped. /health answering -> ready. A container still
# coming up -> starting. Anything else that exists -> unhealthy.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   State token on stdout
# Returns:
#   0
#######################################
agent_resolve_state() {
  local status health
  if ! agent_container_exists; then
    printf 'stopped\n'
    return 0
  fi
  if agent_health_ok; then
    printf 'ready\n'
    return 0
  fi
  status="$(agent_container_field '{{.State.Status}}')"
  health="$(agent_container_field '{{if .State.Health}}{{.State.Health.Status}}{{end}}')"
  case "${status}" in
    created | restarting | paused)
      printf 'starting\n'
      return 0
      ;;
  esac
  if [[ ${health} == "starting" ]]; then
    printf 'starting\n'
    return 0
  fi
  printf 'unhealthy\n'
}

#######################################
# Emit the status JSON contract on stdout.
# Globals:
#   None
# Arguments:
#   $1  State token from agent_resolve_state
# Outputs:
#   JSON object on stdout
# Returns:
#   0
#######################################
agent_status_json() {
  local state="${1:-stopped}"
  printf '{"state":"%s","url":"%s","model":"%s","port":%s,"profile":{"parallel":%s,"context":%s,"max_tokens":%s,"kv_dtype":"%s","vision":%s},"container":"%s"}\n' \
    "${state}" \
    "$(agent_health_url)" \
    "${AGENT_MODEL_SERVED_NAME_DEFAULT}" \
    "$(agent_port)" \
    "${AGENT_MODEL_PARALLEL_DEFAULT}" \
    "${AGENT_MODEL_CONTEXT_DEFAULT}" \
    "${AGENT_MODEL_MAX_TOKENS_DEFAULT}" \
    "${AGENT_MODEL_KV_DTYPE_DEFAULT}" \
    "${AGENT_MODEL_VISION_DEFAULT}" \
    "$(agent_container_name)"
}

#######################################
# Print agent-model status (human or JSON).
# Globals:
#   JSON_FLAG
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; log line on stderr otherwise
# Returns:
#   0; 1 when the bind host is not loopback
#######################################
cmd_status() {
  local state url
  url="$(agent_health_url)" || return 1
  state="$(agent_resolve_state)"
  if [[ ${JSON_FLAG} == "--json" ]]; then
    agent_status_json "${state}"
    return 0
  fi
  log "agent-model state=${state} url=${url} model=${AGENT_MODEL_SERVED_NAME_DEFAULT} container=$(agent_container_name)"
}

#######################################
# Preflight, confirm, sync the pinned recipe, start it, wait for /health.
# Globals:
#   AGENT_MODEL_ASSUME_YES
# Arguments:
#   None
# Outputs:
#   log/log_step/log_ok/err on stderr; recipe output passthrough
# Returns:
#   0; 1 recipe/health failure; 2 occupancy refuse; 4 preflight refuse;
#   5 confirm declined
#######################################
cmd_run() {
  local home
  agent_confirm_run || return $?
  agent_preflight || return $?
  home="$(agent_home)"
  agent_sync_repo || return 1
  agent_export_profile || return 1
  agent_run_recipe_script start.sh || return 1
  run_with_heartbeat "waiting for agent-model on $(agent_health_url)" -- agent_poll_health || return 1
  log_ok "agent-model ready at $(agent_health_url) (model ${AGENT_MODEL_SERVED_NAME_DEFAULT}, container $(agent_container_name), home ${home})"
  return 0
}

#######################################
# Stop the agent container with the recipe's own stop.sh.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log / err on stderr
# Returns:
#   0; 1 when the checkout is missing or stop.sh fails
#######################################
cmd_stop() {
  local home
  home="$(agent_home)"
  if [[ ! -d ${home} ]]; then
    err "no agent-model checkout at ${home} - nothing to stop (run: agent-model.sh run)"
    return 1
  fi
  agent_run_recipe_script stop.sh || return 1
  log_ok "agent-model stopped (container $(agent_container_name))"
  return 0
}

#######################################
# Parse agent-model CLI.
# Globals:
#   JSON_FLAG, CMD
# Arguments:
#   $@  CLI args
# Outputs:
#   Help on stderr; errors on unknown args
# Returns:
#   0; exits 0 on help; 1 on bad args
#######################################
parse_args() {
  JSON_FLAG=""
  CMD="status"
  if [[ $# -eq 0 ]]; then
    return 0
  fi
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      -h | --help | help)
        cmd_help
        exit 0
        ;;
      --json) JSON_FLAG="--json" ;;
      status) CMD="status" ;;
      run) CMD="run" ;;
      stop) CMD="stop" ;;
      *)
        err "Unknown arg: ${1}"
        cmd_help
        return "${AGENT_MODEL_E_USAGE}"
        ;;
    esac
    shift
  done
  return 0
}

#######################################
# CLI dispatcher.
# Globals:
#   CMD
# Arguments:
#   $@  CLI args
# Outputs:
#   Verb output
# Returns:
#   Verb status
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    stop) cmd_stop ;;
    *)
      err "Unknown command: ${CMD}"
      cmd_help
      return "${AGENT_MODEL_E_USAGE}"
      ;;
  esac
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
