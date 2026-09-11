#!/usr/bin/env bash
#
# ## llm-sidecar
#
# Host llama-server for the opt-in Qwen3.6-35B-A3B writing desk.
# Occupancy llm-desk is the public path. Never in docker/Dockerfile.
#
# Usage:
#   ./scripts/utilities/llm-sidecar.sh status [--json]
#   ./scripts/utilities/llm-sidecar.sh start
#   ./scripts/utilities/llm-sidecar.sh stop
#
# Environment:
#   MODELS_DIR, COMFY_OUTPUT_DIR, EZ_LLM_SIDECAR_PORT, EZ_LLM_SIDECAR_CTX,
#   EZ_LLM_SIDECAR_HOST, LAB_MOCK_LLAMA_SERVER, LAB_HERMETIC
#
# Safety:
#   Bind 127.0.0.1 only. GPU-offload is allowed here (llm-desk XOR).
#   Does not start Compose. Does not GPU-offload the in-canvas 4B.
#
# @command llm-sidecar

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
# shellcheck source=download-llm.sh disable=SC1091
source "${REPO_ROOT}/scripts/utilities/download-llm.sh"

JSON_FLAG=""
CMD="status"
readonly LLM_SIDECAR_BIND_DEFAULT="127.0.0.1"
readonly LLM_SIDECAR_PORT_DEFAULT="30000"
readonly LLM_SIDECAR_CTX_DEFAULT="8192"

#######################################
# Print llm-sidecar help.
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
  echo "Usage: llm-sidecar.sh status [--json] | start | stop" >&2
  echo "  Host llama-server for occupancy llm-desk. Bind 127.0.0.1 only." >&2
  echo "  Prefer: ./scripts/manage.sh occupancy enter llm-desk --yes" >&2
  echo "  Never in docker/Dockerfile. See docs/occupancy.md." >&2
}

#######################################
# Loopback bind host (refuse 0.0.0.0 / non-localhost).
# Globals:
#   EZ_LLM_SIDECAR_HOST
# Arguments:
#   None
# Outputs:
#   Host on stdout
# Returns:
#   0; 1 when bind host is not loopback
#######################################
sidecar_bind_host() {
  local host="${EZ_LLM_SIDECAR_HOST:-${LLM_SIDECAR_BIND_DEFAULT}}"
  if [[ -z ${host} ]]; then
    host="${LLM_SIDECAR_BIND_DEFAULT}"
  fi
  case "${host}" in
    127.0.0.1 | localhost)
      printf '%s\n' "127.0.0.1"
      return 0
      ;;
    *)
      err "llm-sidecar bind host must be 127.0.0.1 (got ${host})"
      return 1
      ;;
  esac
}

#######################################
# Sidecar TCP port.
# Globals:
#   EZ_LLM_SIDECAR_PORT
# Arguments:
#   None
# Outputs:
#   Port on stdout
# Returns:
#   0
#######################################
sidecar_port() {
  local port="${EZ_LLM_SIDECAR_PORT:-${LLM_SIDECAR_PORT_DEFAULT}}"
  if [[ ! ${port} =~ ^[0-9]+$ ]]; then
    port="${LLM_SIDECAR_PORT_DEFAULT}"
  fi
  printf '%s\n' "${port}"
}

#######################################
# Sidecar context size.
# Globals:
#   EZ_LLM_SIDECAR_CTX
# Arguments:
#   None
# Outputs:
#   Context tokens on stdout
# Returns:
#   0
#######################################
sidecar_ctx() {
  local ctx="${EZ_LLM_SIDECAR_CTX:-${LLM_SIDECAR_CTX_DEFAULT}}"
  if [[ ! ${ctx} =~ ^[1-9][0-9]*$ ]]; then
    ctx="${LLM_SIDECAR_CTX_DEFAULT}"
  fi
  printf '%s\n' "${ctx}"
}

#######################################
# Resolve the 35B GGUF path (comfy/llm link, then snapshot dir).
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout when present
# Returns:
#   0 when a non-empty file exists; 1 missing
#######################################
sidecar_gguf_path() {
  local name link snap
  name="$(llm35_filename)"
  link="${MODELS_DIR:-/mnt/models}/comfy/llm/${name}"
  snap="$(llm35_dir)/${name}"
  if [[ -f ${link} && -s ${link} ]]; then
    printf '%s\n' "${link}"
    return 0
  fi
  if [[ -f ${snap} && -s ${snap} ]]; then
    printf '%s\n' "${snap}"
    return 0
  fi
  printf '%s\n' "${link}"
  return 1
}

#######################################
# Path to the sidecar log (outputs tree, never MODELS_DIR).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
sidecar_log_path() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/llm-sidecar.log"
}

#######################################
# Path to the mock/real sidecar pid file.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
sidecar_pid_file() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/llm-sidecar.pid"
}

#######################################
# Host-install hint when llama-server is missing.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Hint on stderr
# Returns:
#   0
#######################################
print_llama_server_hint() {
  err "llama-server not found on PATH."
  err "Install host llama.cpp (aarch64). Do not apt/pip inside the Comfy container."
  err "Never add llama.cpp to docker/Dockerfile."
  err "Path D: ssh -L 30000:127.0.0.1:30000  (laptop client → Spark sidecar)"
  err "  ./scripts/manage.sh occupancy enter llm-desk --yes"
}

#######################################
# Parse llm-sidecar CLI.
# Globals:
#   JSON_FLAG, CMD
# Arguments:
#   $@  CLI args
# Outputs:
#   Help; errors on unknown args
# Returns:
#   0; exits 0 on help; 1 on bad args
#######################################
parse_args() {
  JSON_FLAG=""
  CMD="status"
  if [[ $# -eq 0 ]]; then
    CMD="status"
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
      start) CMD="start" ;;
      stop) CMD="stop" ;;
      --*)
        err "Unknown arg: ${1}"
        cmd_help
        exit 1
        ;;
      *)
        err "Unknown arg: ${1}"
        cmd_help
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# Print sidecar status (human or JSON).
# Globals:
#   JSON_FLAG, MODELS_DIR, COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; logs on stderr
# Returns:
#   0
#######################################
cmd_status() {
  local running="false" pid port bind gguf ready="false" occupancy live
  pid="$(occupancy_field llm_pid)"
  if [[ -z ${pid} ]]; then
    pid="0"
  fi
  live="false"
  if llm_pid_alive; then
    live="true"
    running="true"
  fi
  port="$(sidecar_port)"
  bind="127.0.0.1"
  occupancy="$(occupancy_mode)"
  gguf=""
  if sidecar_gguf_path >/dev/null; then
    gguf="$(sidecar_gguf_path)"
    ready="true"
  else
    gguf="$(sidecar_gguf_path || true)"
  fi
  if [[ ${LAB_MOCK_LLAMA_SERVER:-} == "1" && ${ready} == "true" ]]; then
    if [[ ${occupancy} == "llm-desk" ]]; then
      running="true"
    fi
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '{"running":%s,"pid":%s,"port":%s,"bind":"%s","gguf":"%s","ready":%s,"occupancy":"%s","llm_live":%s}\n' \
      "${running}" "${pid}" "${port}" "${bind}" "${gguf}" "${ready}" "${occupancy}" "${live}"
    return 0
  fi
  log "llm-sidecar running=${running} pid=${pid} port=${port} bind=${bind} ready=${ready} occupancy=${occupancy}"
}

#######################################
# True when occupancy allows a sidecar start.
# Globals:
#   EZ_LLM_SIDECAR_ENTERING, COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Error on stderr when refused
# Returns:
#   0 allowed; 2 refused
#######################################
sidecar_start_allowed() {
  local mode
  mode="$(occupancy_mode)"
  case "${mode}" in
    klein | trellis | wan | ltx)
      err "occupancy is ${mode} — stop the visual job before llm-sidecar start"
      err "  ./scripts/manage.sh occupancy enter llm-desk --yes"
      return 2
      ;;
  esac
  if comfy_queue_busy; then
    err "Comfy queue is busy — wait before llm-sidecar start"
    return 2
  fi
  if [[ ${mode} == "llm-desk" ]]; then
    return 0
  fi
  if [[ ${EZ_LLM_SIDECAR_ENTERING:-} == "1" ]]; then
    return 0
  fi
  err "llm-sidecar start requires occupancy llm-desk"
  err "  ./scripts/manage.sh occupancy enter llm-desk --yes"
  return 2
}

#######################################
# Mock start: fake pid file, llm_pid 0, no binary.
# Globals:
#   COMFY_OUTPUT_DIR, LAB_MOCK_LLAMA_SERVER
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0
#######################################
mock_start() {
  local pidf
  pidf="$(sidecar_pid_file)"
  mkdir -p "$(dirname "${pidf}")"
  printf '0\n' >"${pidf}"
  occupancy_set_llm_pid 0
  log "llm-sidecar: LAB_MOCK_LLAMA_SERVER=1 (pid 0)"
  return 0
}

#######################################
# Start host llama-server (or mock).
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR, LAB_MOCK_LLAMA_SERVER, LAB_HERMETIC
# Arguments:
#   None
# Outputs:
#   log/err
# Returns:
#   0; 1 missing GGUF/binary; 2 occupancy refuse
#######################################
cmd_start() {
  local gguf host port ctx logf pidf ngl_args=() spec_args=() pid
  sidecar_start_allowed || return $?
  sidecar_bind_host >/dev/null || return 1
  if [[ ${LAB_MOCK_LLAMA_SERVER:-} == "1" ]]; then
    mock_start
    return 0
  fi
  if [[ ${LAB_HERMETIC:-0} == "1" ]]; then
    print_llama_server_hint
    return 1
  fi
  if ! sidecar_gguf_path >/dev/null; then
    err "35B GGUF missing. Download the opt-in pack:"
    err "  ./scripts/manage.sh download-llm --tier qwen36-35b-a3b"
    return 1
  fi
  gguf="$(sidecar_gguf_path)"
  if ! command -v llama-server >/dev/null 2>&1; then
    print_llama_server_hint
    return 1
  fi
  host="$(sidecar_bind_host)"
  port="$(sidecar_port)"
  ctx="$(sidecar_ctx)"
  logf="$(sidecar_log_path)"
  pidf="$(sidecar_pid_file)"
  mkdir -p "$(dirname "${logf}")"
  ngl_args=(-ngl 99)
  if llama-server --help 2>&1 | grep -q -- '--spec-type'; then
    spec_args=(--spec-type draft-mtp --spec-draft-n-max 2)
  else
    log "llama-server has no --spec-type; starting without MTP"
  fi
  nohup llama-server \
    -m "${gguf}" \
    --host "${host}" \
    --port "${port}" \
    --ctx-size "${ctx}" \
    --alias qwen36-35b-a3b \
    "${ngl_args[@]}" \
    "${spec_args[@]}" \
    >>"${logf}" 2>&1 &
  pid=$!
  occupancy_set_llm_pid "${pid}"
  printf '%s\n' "${pid}" >"${pidf}"
  log "llm-sidecar started pid=${pid} ${host}:${port} log=${logf}"
  return 0
}

#######################################
# Stop the sidecar (TERM then KILL) and clear occupancy llm_pid.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0
#######################################
cmd_stop() {
  stop_llm_sidecar
  rm -f "$(sidecar_pid_file)" 2>/dev/null || true
  log "llm-sidecar stopped"
  return 0
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@  CLI args
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
    *)
      err "Unknown command: ${CMD}"
      cmd_help
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
