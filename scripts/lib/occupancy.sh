#!/usr/bin/env bash
# ## occupancy
#
# Mode machine for one heavy GPU job on GB10.
# Source after scripts/lib/compose.sh. Not executable.
#
# Safety:
#   One heavy GPU job: klein / trellis / wan / ltx, or host NVENC, or llm-desk.
#   blender-desk is Workbench after POST /free (parked Comfy), not a second CUDA job.
#   llm-desk is host llama-server after POST /free, XOR with blender-desk and visual.
#   Does not weaken restart: "no", mem_limit 90g, or headroom.

OCCUPANCY_MODE_LIST=(idle blender-desk llm-desk klein trellis wan ltx)
_OCCUPANCY_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Path to the occupancy state file (outputs tree, never MODELS_DIR).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
occupancy_state_path() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/.occupancy.json"
}

#######################################
# Default occupancy JSON when the state file is missing or invalid.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   JSON on stdout
# Returns:
#   0
#######################################
occupancy_default_json() {
  printf '%s\n' '{"version":1,"mode":"idle","compose":false,"parked":false,"blender_pid":0,"mcp_pid":0,"llm_pid":0,"updated":""}'
}

#######################################
# Read occupancy state JSON (default when missing or invalid).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   JSON on stdout
# Returns:
#   0
#######################################
occupancy_read() {
  local path json
  path="$(occupancy_state_path)"
  if [[ -f ${path} ]]; then
    json="$(cat "${path}" 2>/dev/null || true)"
    if [[ -n ${json} ]] && printf '%s' "${json}" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
      printf '%s\n' "${json}"
      return 0
    fi
  fi
  occupancy_default_json
}

#######################################
# Read one occupancy field (booleans as true/false).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  field name
# Outputs:
#   Field value on stdout
# Returns:
#   0
#######################################
occupancy_field() {
  local key="${1}"
  occupancy_read | python3 -c 'import json, sys
d = json.load(sys.stdin)
key = sys.argv[1]
val = d.get(key, "")
if val is True:
    print("true")
elif val is False:
    print("false")
elif val is None:
    print("")
else:
    print(val)
' "${key}"
}

#######################################
# Write occupancy state JSON.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  mode
#   $2  parked (true|false|1|0)
#   $3  blender_pid (optional, default 0)
#   $4  mcp_pid (optional, default 0)
#   $5  llm_pid (optional; when omitted, preserve current llm_pid)
# Outputs:
#   None
# Returns:
#   0 on write; 1 on mkdir/python failure
#######################################
occupancy_write() {
  local mode="${1}"
  local parked="${2}"
  local blender_pid="${3:-0}"
  local mcp_pid="${4:-0}"
  local llm_pid="0"
  [[ -n ${blender_pid} ]] || blender_pid="0"
  [[ -n ${mcp_pid} ]] || mcp_pid="0"
  if [[ $# -ge 5 ]]; then
    llm_pid="${5:-0}"
    [[ -n ${llm_pid} ]] || llm_pid="0"
  else
    llm_pid="$(occupancy_field llm_pid)"
    if [[ -z ${llm_pid} ]]; then
      llm_pid="0"
    fi
  fi
  local path parked_json compose_flag
  path="$(occupancy_state_path)"
  mkdir -p "$(dirname "${path}")" || return 1
  parked_json="false"
  if [[ ${parked} == "true" || ${parked} == "1" ]]; then
    parked_json="true"
  fi
  compose_flag="false"
  if compose_is_running; then
    compose_flag="true"
  fi
  python3 -c 'import json, sys, datetime
path, mode, parked, blender_pid, mcp_pid, llm_pid, compose_flag = sys.argv[1:8]
payload = {
    "version": 1,
    "mode": mode,
    "compose": compose_flag == "true",
    "parked": parked == "true",
    "blender_pid": int(blender_pid or 0),
    "mcp_pid": int(mcp_pid or 0),
    "llm_pid": int(llm_pid or 0),
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")
' "${path}" "${mode}" "${parked_json}" "${blender_pid}" "${mcp_pid}" "${llm_pid}" "${compose_flag}"
}

#######################################
# Current occupancy mode (idle when unset).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Mode id on stdout
# Returns:
#   0
#######################################
occupancy_mode() {
  local mode
  mode="$(occupancy_field mode)"
  if [[ -z ${mode} ]]; then
    echo "idle"
    return 0
  fi
  printf '%s\n' "${mode}"
}

#######################################
# True when Comfy is parked (models unloaded for blender-desk).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 parked; 1 not parked
#######################################
occupancy_is_parked() {
  [[ $(occupancy_field parked) == "true" ]]
}

#######################################
# Print valid occupancy mode ids.
# Globals:
#   OCCUPANCY_MODE_LIST
# Arguments:
#   None
# Outputs:
#   Space-separated modes on stdout
# Returns:
#   0
#######################################
occupancy_modes() {
  printf '%s\n' "${OCCUPANCY_MODE_LIST[*]}"
}

#######################################
# True when $1 is a valid occupancy mode.
# Globals:
#   OCCUPANCY_MODE_LIST
# Arguments:
#   $1  mode id
# Outputs:
#   Error on stderr when invalid
# Returns:
#   0 valid; 1 invalid
#######################################
occupancy_valid_mode() {
  local mode="${1:-}"
  local item
  for item in "${OCCUPANCY_MODE_LIST[@]}"; do
    if [[ ${item} == "${mode}" ]]; then
      return 0
    fi
  done
  err "Unknown occupancy mode: ${mode} (want: ${OCCUPANCY_MODE_LIST[*]})"
  return 1
}

#######################################
# Comfy HTTP origin for occupancy probes.
# Globals:
#   COMFY_PORT
# Arguments:
#   None
# Outputs:
#   URL on stdout
# Returns:
#   0
#######################################
occupancy_comfy_url() {
  echo "http://127.0.0.1:${COMFY_PORT:-8188}"
}

#######################################
# Hermetic Comfy HTTP mock (LAB_HERMETIC=1).
# Globals:
#   LAB_MOCK_COMFY_QUEUE, LAB_MOCK_COMFY_FREE, LAB_MOCK_COMFY_STATS
# Arguments:
#   $1  method (GET|POST)
#   $2  path (/queue|/free|/system_stats)
# Outputs:
#   Mock body on stdout
# Returns:
#   0; 1 when LAB_MOCK_COMFY_FREE=fail on /free
#######################################
occupancy_http_mock() {
  local path="${2}"
  case "${path}" in
    /queue)
      if [[ ${LAB_MOCK_COMFY_QUEUE:-idle} == "busy" ]]; then
        printf '%s\n' '{"queue_running":[[1]],"queue_pending":[]}'
      else
        printf '%s\n' '{"queue_running":[],"queue_pending":[]}'
      fi
      ;;
    /free)
      if [[ ${LAB_MOCK_COMFY_FREE:-ok} == "fail" ]]; then
        return 1
      fi
      printf '%s\n' '{}'
      ;;
    /system_stats)
      printf '%s\n' "${LAB_MOCK_COMFY_STATS:-{\"system\":{\"ram_free\":40000000000},\"devices\":[{\"vram_free\":40000000000,\"vram_total\":128000000000}]}}"
      ;;
    *)
      return 1
      ;;
  esac
  return 0
}

#######################################
# GET/POST Comfy occupancy routes. Hermetic tests never hit the network.
# Globals:
#   LAB_HERMETIC, COMFY_PORT
# Arguments:
#   $1  method
#   $2  path
#   $3  optional JSON body for POST
# Outputs:
#   Response body on stdout
# Returns:
#   0 on success; 1 on curl/mock failure
#######################################
occupancy_http() {
  local method="${1}"
  local path="${2}"
  local body="${3:-}"
  local url
  if [[ ${LAB_HERMETIC:-0} == "1" ]]; then
    occupancy_http_mock "${method}" "${path}" "${body}"
    return $?
  fi
  url="$(occupancy_comfy_url)${path}"
  if [[ ${method} == "POST" ]]; then
    curl -sf --max-time 5 -X POST "${url}" -H 'Content-Type: application/json' \
      --data "${body:-{}}"
    return $?
  fi
  curl -sf --max-time 5 "${url}"
}

#######################################
# True when Comfy has a running or pending queue item.
# Fail closed (busy) when compose is up and /queue cannot be read.
# Globals:
#   LAB_HERMETIC, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 busy; 1 idle
#######################################
comfy_queue_busy() {
  local body
  if ! compose_is_running; then
    return 1
  fi
  body="$(occupancy_http GET /queue)" || return 0
  printf '%s' "${body}" | python3 -c 'import json, sys
d = json.load(sys.stdin)
run = d.get("queue_running") or []
pend = d.get("queue_pending") or []
sys.exit(0 if (run or pend) else 1)
'
}

#######################################
# Unload Comfy models and free cache (POST /free). No-op when compose is down.
# Globals:
#   LAB_HERMETIC, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   Warn on stderr when the call fails
# Returns:
#   0 success or compose down; 1 on HTTP failure
#######################################
comfy_free_memory() {
  if ! compose_is_running; then
    return 0
  fi
  occupancy_http POST /free '{"unload_models":true,"free_memory":true}' >/dev/null
}

#######################################
# Best-effort Comfy /system_stats JSON (empty object when unavailable).
# Globals:
#   LAB_HERMETIC, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   JSON on stdout
# Returns:
#   0
#######################################
comfy_system_stats() {
  local body
  if ! compose_is_running; then
    printf '%s\n' '{}'
    return 0
  fi
  body="$(occupancy_http GET /system_stats)" || {
    printf '%s\n' '{}'
    return 0
  }
  printf '%s\n' "${body}"
}

#######################################
# Refuse when studio compose (comfyui) is running.
# NVENC / film-proxies stay XOR with compose-up (encoder is a GPU job).
# Globals:
#   None (compose_is_running uses compose project env)
# Arguments:
#   $1  Optional job label (default: host GPU sidecar (occupancy))
# Outputs:
#   Error on stderr when compose is up
# Returns:
#   0 idle; 2 when ComfyUI is running
#######################################
refuse_if_comfy_running() {
  local job="${1:-host GPU sidecar (occupancy)}"
  if compose_is_running; then
    err "ComfyUI is running — stop it before ${job}"
    return 2
  fi
  return 0
}

#######################################
# Refuse a DCC dump when Comfy is a heavy job (up, not parked, or queue busy).
# Parked blender-desk after POST /free is allowed. Compose down is allowed.
# Globals:
#   COMFY_OUTPUT_DIR, LAB_HERMETIC
# Arguments:
#   $1  Optional job label
# Outputs:
#   Error on stderr when refused
# Returns:
#   0 allowed; 2 occupancy refuse
#######################################
refuse_if_heavy_gpu() {
  local job="${1:-host DCC dump (occupancy)}"
  refuse_if_llm_sidecar "${job}" || return $?
  if ! compose_is_running; then
    return 0
  fi
  if comfy_queue_busy; then
    err "Comfy queue is busy — wait or occupancy enter blender-desk before ${job}"
    return 2
  fi
  if occupancy_is_parked && [[ $(occupancy_mode) == "blender-desk" ]]; then
    return 0
  fi
  err "ComfyUI is running — occupancy enter blender-desk (or stop) before ${job}"
  return 2
}

#######################################
# Refuse Cycles/OptiX/CUDA Blender args while Compose is up.
# Globals:
#   CYCLES_DEVICE
# Arguments:
#   $@  blender argv
# Outputs:
#   Error on stderr when refused
# Returns:
#   0 allowed; 2 refused
#######################################
refuse_cycles_while_compose() {
  local arg
  if ! compose_is_running; then
    return 0
  fi
  if [[ ${CYCLES_DEVICE:-} == "CUDA" || ${CYCLES_DEVICE:-} == "OPTIX" ]]; then
    err "Cycles GPU while Comfy is up — occupancy idle first (Workbench only in blender-desk)"
    return 2
  fi
  for arg in "$@"; do
    case "${arg}" in
      *CYCLES* | *OPTIX* | *CUDA*)
        err "Cycles GPU while Comfy is up — occupancy idle first (Workbench only in blender-desk)"
        return 2
        ;;
    esac
  done
  return 0
}

#######################################
# True when a recorded occupancy PID is still alive.
# Globals:
#   None
# Arguments:
#   $1  pid
# Outputs:
#   None
# Returns:
#   0 alive; 1 dead/unset
#######################################
occupancy_pid_alive() {
  local pid="${1:-0}"
  [[ ${pid} =~ ^[1-9][0-9]*$ ]] || return 1
  kill -0 "${pid}" 2>/dev/null
}

#######################################
# True when the recorded blender sidecar PID is alive.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 alive; 1 dead
#######################################
blender_pid_alive() {
  occupancy_pid_alive "$(occupancy_field blender_pid)"
}

#######################################
# True when the recorded MCP PID is alive.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 alive; 1 dead
#######################################
mcp_pid_alive() {
  occupancy_pid_alive "$(occupancy_field mcp_pid)"
}

#######################################
# True when the recorded llm-sidecar PID is alive.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 alive; 1 dead
#######################################
llm_pid_alive() {
  occupancy_pid_alive "$(occupancy_field llm_pid)"
}

#######################################
# Record the llm-sidecar PID in occupancy state. Does not remap mode.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  pid
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
occupancy_set_llm_pid() {
  local pid="${1:-0}"
  local mode parked blender mcp
  mode="$(occupancy_mode)"
  parked="$(occupancy_field parked)"
  blender="$(occupancy_field blender_pid)"
  mcp="$(occupancy_field mcp_pid)"
  [[ -n ${mode} ]] || mode="idle"
  [[ -n ${parked} ]] || parked="false"
  [[ -n ${blender} ]] || blender="0"
  [[ -n ${mcp} ]] || mcp="0"
  occupancy_write "${mode}" "${parked}" "${blender}" "${mcp}" "${pid}"
}

#######################################
# SIGTERM then SIGKILL the recorded llm-sidecar PID and clear it.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
stop_llm_sidecar() {
  occupancy_stop_pid "$(occupancy_field llm_pid)"
  occupancy_set_llm_pid 0
  rm -f "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/llm-sidecar.pid" 2>/dev/null || true
}

#######################################
# Refuse when a live llm-sidecar PID is recorded (XOR with DCC / visual).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  Optional job label
# Outputs:
#   Error on stderr when refused
# Returns:
#   0 allowed; 2 sidecar live
#######################################
refuse_if_llm_sidecar() {
  local job="${1:-host GPU job (occupancy)}"
  if llm_pid_alive; then
    err "llm-desk sidecar is running — occupancy enter blender-desk or idle before ${job}"
    return 2
  fi
  return 0
}

#######################################
# Start the 35B sidecar (implementation detail of occupancy enter llm-desk).
# Globals:
#   COMFY_OUTPUT_DIR, LAB_MOCK_LLAMA_SERVER, _OCCUPANCY_LIB
# Arguments:
#   None
# Outputs:
#   sidecar logs on stderr
# Returns:
#   llm-sidecar.sh start status
#######################################
start_llm_sidecar() {
  local sidecar
  sidecar="${_OCCUPANCY_LIB}/../utilities/llm-sidecar.sh"
  EZ_LLM_SIDECAR_ENTERING=1 bash "${sidecar}" start
}

#######################################
# SIGTERM then SIGKILL a recorded occupancy PID. Ignores 0/self/init.
# Globals:
#   None
# Arguments:
#   $1  pid
# Outputs:
#   None
# Returns:
#   0
#######################################
occupancy_stop_pid() {
  local pid="${1:-0}"
  [[ ${pid} =~ ^[1-9][0-9]*$ ]] || return 0
  if [[ ${pid} == "$$" || ${pid} == "1" ]]; then
    return 0
  fi
  kill -TERM "${pid}" 2>/dev/null || true
  kill -KILL "${pid}" 2>/dev/null || true
}

#######################################
# Record the blender sidecar PID in occupancy state.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  pid
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
occupancy_set_blender_pid() {
  local pid="${1:-0}"
  local mode parked mcp
  mode="$(occupancy_mode)"
  parked="$(occupancy_field parked)"
  mcp="$(occupancy_field mcp_pid)"
  if [[ ${mode} == "idle" ]]; then
    mode="blender-desk"
  fi
  if [[ -z ${parked} ]]; then
    parked="false"
  fi
  if [[ -z ${mcp} ]]; then
    mcp="0"
  fi
  occupancy_write "${mode}" "${parked}" "${pid}" "${mcp}"
}

#######################################
# Record the MCP server PID in occupancy state.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  pid
# Outputs:
#   None
# Returns:
#   occupancy_write status
#######################################
occupancy_set_mcp_pid() {
  local pid="${1:-0}"
  local mode parked blender
  mode="$(occupancy_mode)"
  parked="$(occupancy_field parked)"
  blender="$(occupancy_field blender_pid)"
  if [[ ${mode} == "idle" ]]; then
    mode="blender-desk"
  fi
  if [[ -z ${parked} ]]; then
    parked="false"
  fi
  if [[ -z ${blender} ]]; then
    blender="0"
  fi
  occupancy_write "${mode}" "${parked}" "${blender}" "${pid}"
}

#######################################
# Stop recorded blender and MCP PIDs and clear them in state.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
stop_blender_desk() {
  occupancy_stop_pid "$(occupancy_field blender_pid)"
  occupancy_stop_pid "$(occupancy_field mcp_pid)"
  occupancy_write "$(occupancy_mode)" "$(occupancy_field parked)" 0 0
}

#######################################
# Occupancy status JSON (state file plus live compose/queue).
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   JSON on stdout
# Returns:
#   0
#######################################
occupancy_status_json() {
  local compose_flag="false"
  local queue="idle"
  local llm_live="false"
  if compose_is_running; then
    compose_flag="true"
    if comfy_queue_busy; then
      queue="busy"
    fi
  fi
  if llm_pid_alive; then
    llm_live="true"
  fi
  occupancy_read | python3 -c 'import json, sys
d = json.load(sys.stdin)
d["compose_live"] = sys.argv[1] == "true"
d["queue"] = sys.argv[2]
try:
    d["llm_pid"] = int(d.get("llm_pid") or 0)
except (TypeError, ValueError):
    d["llm_pid"] = 0
d["llm_live"] = sys.argv[3] == "true"
json.dump(d, sys.stdout)
print()
' "${compose_flag}" "${queue}" "${llm_live}"
}

#######################################
# Enter an occupancy mode. Heavy modes do not start Compose (start still needs yes).
# Globals:
#   COMFY_OUTPUT_DIR, LAB_HERMETIC
# Arguments:
#   $1  mode
#   $2  optional --yes (1) to stop a live blender desk
# Outputs:
#   Status on stderr
# Returns:
#   0; 1 usage/compose-down; 2 busy/blender-alive without --yes
#######################################
occupancy_enter() {
  local target="${1:-}"
  local yes="${2:-0}"
  local parked="false"
  occupancy_valid_mode "${target}" || return 1
  case "${target}" in
    idle)
      stop_llm_sidecar
      stop_blender_desk
      if compose_is_running; then
        stack_stop || return 1
      fi
      occupancy_write "idle" "false" 0 0 0
      log "occupancy: idle"
      ;;
    blender-desk)
      stop_llm_sidecar
      if compose_is_running; then
        if comfy_queue_busy; then
          err "Comfy queue is busy — wait or interrupt before blender-desk"
          return 2
        fi
        if ! comfy_free_memory; then
          warn "POST /free failed; Workbench may still contend for unified memory"
        fi
        occupancy_write "blender-desk" "true" \
          "$(occupancy_field blender_pid)" "$(occupancy_field mcp_pid)" 0
        log "occupancy: blender-desk (Comfy parked via /free)"
      else
        occupancy_write "blender-desk" "false" \
          "$(occupancy_field blender_pid)" "$(occupancy_field mcp_pid)" 0
        log "occupancy: blender-desk (compose down)"
      fi
      ;;
    llm-desk)
      if compose_is_running; then
        if comfy_queue_busy; then
          err "Comfy queue is busy — wait or interrupt before llm-desk"
          return 2
        fi
      fi
      if blender_pid_alive || mcp_pid_alive; then
        if [[ ${yes} != "1" ]]; then
          err "Blender desk is running — occupancy enter llm-desk --yes to stop it"
          return 2
        fi
        stop_blender_desk
      fi
      parked="false"
      if compose_is_running; then
        if ! comfy_free_memory; then
          warn "POST /free failed; 35B sidecar may still contend for unified memory"
        fi
        parked="true"
      fi
      occupancy_write "llm-desk" "${parked}" 0 0 0
      if ! start_llm_sidecar; then
        err "llm-sidecar failed to start"
        return 1
      fi
      if [[ ${parked} == "true" ]]; then
        log "occupancy: llm-desk (Comfy parked via /free; 35B sidecar)"
      else
        log "occupancy: llm-desk (compose down; 35B sidecar)"
      fi
      ;;
    klein | trellis | wan | ltx)
      stop_llm_sidecar
      if blender_pid_alive || mcp_pid_alive; then
        if [[ ${yes} != "1" ]]; then
          err "Blender desk is running — occupancy enter ${target} --yes to stop it"
          return 2
        fi
        stop_blender_desk
      fi
      if ! compose_is_running; then
        err "ComfyUI is not running — ./scripts/manage.sh start (type yes)"
        return 1
      fi
      if comfy_queue_busy; then
        err "Comfy queue is busy — wait before occupancy enter ${target}"
        return 2
      fi
      if ! comfy_free_memory; then
        warn "POST /free failed before ${target}"
      fi
      occupancy_write "${target}" "false" 0 0 0
      log "occupancy: ${target} — one heavy GPU job. Queue the ${target} graph."
      ;;
  esac
  return 0
}
