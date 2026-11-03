#!/usr/bin/env bats
#
# ## agent_model.bats
#
# Cover scripts/utilities/agent-model.sh (strict inventory). Host launcher for
# the optional Qwen3.8-Flash-Next agent: pinned clone/update, preflight,
# heavy confirm, co-tenant profile env, health poll, status --json.
#
# Hermetic: git, docker, curl, and df are PATH stubs that record argv; HOME,
# HF_HOME, AGENT_MODEL_HOME, the meminfo file, and the occupancy file are all
# under TEST_TMP_DIR. No network, no docker daemon, no GPU, no real sleep
# (AGENT_MODEL_POLL_INTERVAL_S=0).

bats_require_minimum_version 1.5.0

load 'test_helper'

setup() {
  setup_repo_env
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/paths.sh"
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib/common.sh"
  AM="${UTILITIES_DIR}/agent-model.sh"
  chmod +x "${AM}"
  # shellcheck disable=SC1090
  source "${AM}"

  export AGENT_MODEL_HOME="${TEST_TMP_DIR}/agent-home"
  export HF_HOME="${TEST_TMP_DIR}/hf"
  mkdir -p "${HF_HOME}"
  export AGENT_MODEL_MEMINFO_FILE="${TEST_TMP_DIR}/meminfo"
  export AGENT_MODEL_ASSUME_YES=1
  export AGENT_MODEL_POLL_INTERVAL_S=0
  export AGENT_MODEL_CURL_MAX_TIME_S=1
  unset LAB_NON_INTERACTIVE LAB_CONFIRM_TOKEN HOST AGENT_MODEL_HOST
  unset PARALLEL CONTEXT MAX_TOKENS KV_DTYPE VISION THINKING SERVED_NAME
  unset CONTAINER_NAME MEM_FLOOR_GIB TENSORFOLD_NO_UPDATE_CHECK

  GIT_CALLS_LOG="${TEST_TMP_DIR}/git_calls.log"
  DOCKER_CALLS_LOG="${TEST_TMP_DIR}/docker_calls.log"
  CURL_CALLS_LOG="${TEST_TMP_DIR}/curl_calls.log"
  DF_CALLS_LOG="${TEST_TMP_DIR}/df_calls.log"
  START_CALLS_LOG="${TEST_TMP_DIR}/start_calls.log"
  STOP_CALLS_LOG="${TEST_TMP_DIR}/stop_calls.log"
  RECIPE_FIXTURE_DIR="${TEST_TMP_DIR}/recipe-fixture"
  export GIT_CALLS_LOG DOCKER_CALLS_LOG CURL_CALLS_LOG DF_CALLS_LOG
  export START_CALLS_LOG STOP_CALLS_LOG RECIPE_FIXTURE_DIR
  : >"${GIT_CALLS_LOG}"
  : >"${DOCKER_CALLS_LOG}"
  : >"${CURL_CALLS_LOG}"
  : >"${DF_CALLS_LOG}"
  : >"${START_CALLS_LOG}"
  : >"${STOP_CALLS_LOG}"

  install_agent_command_stubs
  write_meminfo 125829120
  occupancy_write idle false 0 0 0
}

teardown() {
  teardown_repo_env
}

#######################################
# Install argv-recording stubs for every external command the launcher calls.
# Behaviour is steered by STUB_* env vars; no stub touches the network.
# Globals:
#   TEST_TMP_DIR, GIT_CALLS_LOG, DOCKER_CALLS_LOG, CURL_CALLS_LOG, DF_CALLS_LOG
# Arguments:
#   None
# Outputs:
#   Mock binaries under ${TEST_TMP_DIR}/bin
# Returns:
#   0
#######################################
install_agent_command_stubs() {
  install_mock_bin git '
echo "git $*" >> "${GIT_CALLS_LOG}"
if [[ "${STUB_GIT_RC:-0}" != "0" ]]; then
  exit "${STUB_GIT_RC}"
fi
case " $* " in
  *" clone "*)
    target="${*: -1}"
    mkdir -p "${target}/.git"
    if [[ -d ${RECIPE_FIXTURE_DIR} ]]; then
      cp "${RECIPE_FIXTURE_DIR}"/*.sh "${target}/" 2>/dev/null || true
    fi
    ;;
esac
exit 0
'
  install_mock_bin docker '
echo "docker $*" >> "${DOCKER_CALLS_LOG}"
if [[ "${1:-}" == "inspect" ]]; then
  if [[ ! -f ${TEST_TMP_DIR}/container_exists ]]; then
    exit 1
  fi
  prev=""
  template=""
  for arg in "$@"; do
    if [[ ${prev} == "-f" ]]; then
      template="${arg}"
    fi
    prev="${arg}"
  done
  case "${template}" in
    *"Health"*) echo "${STUB_DOCKER_HEALTH:-}" ;;
    *"State.Status"*) echo "${STUB_DOCKER_STATUS:-running}" ;;
    *) echo "" ;;
  esac
  exit 0
fi
exit 0
'
  install_mock_bin curl '
echo "curl $*" >> "${CURL_CALLS_LOG}"
if [[ -n ${STUB_CURL_OK_AFTER:-} ]]; then
  n=0
  if [[ -f ${TEST_TMP_DIR}/curl_count ]]; then
    n="$(cat "${TEST_TMP_DIR}/curl_count")"
  fi
  n=$((n + 1))
  printf "%s\n" "${n}" >"${TEST_TMP_DIR}/curl_count"
  if ((n > STUB_CURL_OK_AFTER)); then
    exit 0
  fi
  exit 22
fi
exit "${STUB_CURL_RC:-0}"
'
  install_mock_bin df '
echo "df $*" >> "${DF_CALLS_LOG}"
if [[ "${STUB_DF_RC:-0}" != "0" ]]; then
  exit "${STUB_DF_RC}"
fi
echo "Filesystem     1024-blocks      Used Available Capacity Mounted on"
echo "/dev/fake 1000000000 100000000 ${STUB_DF_AVAIL_KIB:-209715200} 33% /fake"
exit 0
'
}

#######################################
# Write a fake /proc/meminfo fixture with the requested MemAvailable.
# Globals:
#   AGENT_MODEL_MEMINFO_FILE
# Arguments:
#   $1  MemAvailable in KiB
# Outputs:
#   Fixture file
# Returns:
#   0
#######################################
write_meminfo() {
  printf 'MemTotal:       132906208 kB\nMemAvailable:    %s kB\n' "${1}" >"${AGENT_MODEL_MEMINFO_FILE}"
}

#######################################
# Populate the recipe fixture that the git clone stub copies into the home.
# Globals:
#   RECIPE_FIXTURE_DIR
# Arguments:
#   None
# Outputs:
#   start.sh / stop.sh fixtures that record their argv and the profile env
# Returns:
#   0
#######################################
write_recipe_fixture() {
  mkdir -p "${RECIPE_FIXTURE_DIR}"
  cat >"${RECIPE_FIXTURE_DIR}/start.sh" <<'FIXTURE'
#!/usr/bin/env bash
echo "start $*" >>"${START_CALLS_LOG}"
echo "profile HOST=${HOST} PORT=${PORT} SERVED_NAME=${SERVED_NAME} PARALLEL=${PARALLEL} CONTEXT=${CONTEXT} MAX_TOKENS=${MAX_TOKENS} KV_DTYPE=${KV_DTYPE} VISION=${VISION} THINKING=${THINKING} NO_UPDATE=${TENSORFOLD_NO_UPDATE_CHECK} CONTAINER=${CONTAINER_NAME} MEM_FLOOR=${MEM_FLOOR_GIB}" >>"${START_CALLS_LOG}"
exit "${STUB_START_RC:-0}"
FIXTURE
  cat >"${RECIPE_FIXTURE_DIR}/stop.sh" <<'FIXTURE'
#!/usr/bin/env bash
echo "stop $*" >>"${STOP_CALLS_LOG}"
exit "${STUB_STOP_RC:-0}"
FIXTURE
  chmod +x "${RECIPE_FIXTURE_DIR}/start.sh" "${RECIPE_FIXTURE_DIR}/stop.sh"
}

#######################################
# Create the pinned checkout by hand (update path, no clone).
# Globals:
#   AGENT_MODEL_HOME
# Arguments:
#   None
# Outputs:
#   ${AGENT_MODEL_HOME}/.git plus the recipe scripts
# Returns:
#   0
#######################################
make_agent_home() {
  write_recipe_fixture
  mkdir -p "${AGENT_MODEL_HOME}/.git"
  cp "${RECIPE_FIXTURE_DIR}/start.sh" "${RECIPE_FIXTURE_DIR}/stop.sh" "${AGENT_MODEL_HOME}/"
}

@test "agent-model defines every function for the coverage inventory" {
  local -a fns=(
    cmd_help agent_home agent_repo agent_ref agent_port agent_bind_host
    agent_container_name agent_health_url agent_ready_s agent_min_disk_gb
    agent_min_mem_gib agent_meminfo_file agent_hf_home agent_run_git
    agent_run_docker agent_run_curl agent_run_df agent_run_recipe_script
    agent_env_default agent_export_profile agent_require_tools
    agent_disk_free_gb agent_mem_available_gib agent_occupancy_mode
    agent_occupancy_mode_file agent_refuse_heavy_occupancy agent_preflight
    agent_confirm_run agent_sync_repo agent_health_ok agent_poll_health
    agent_container_exists agent_container_field agent_resolve_state
    agent_status_json cmd_status cmd_run cmd_stop parse_args main
  )
  local fn
  [[ ${#fns[@]} -eq 40 ]]
  for fn in "${fns[@]}"; do
    run type "${fn}"
    [ "${status}" -eq 0 ] || return 1
  done
}

@test "agent-model pinned defaults resolve as contracted" {
  run agent_home
  [ "${output}" = "${TEST_TMP_DIR}/agent-home" ]
  run agent_repo
  [ "${output}" = "https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Single-DGX-Spark-TensorFold" ]
  run agent_ref
  [ "${output}" = "main" ]
  run agent_port
  [ "${output}" = "30001" ]
  run agent_bind_host
  [ "${output}" = "127.0.0.1" ]
  run agent_container_name
  [ "${output}" = "ez-agent-model" ]
  run agent_ready_s
  [ "${output}" = "900" ]
  run agent_min_disk_gb
  [ "${output}" = "160" ]
  run agent_min_mem_gib
  [ "${output}" = "110" ]
  run agent_hf_home
  [ "${output}" = "${HF_HOME}" ]
  run agent_meminfo_file
  [ "${output}" = "${AGENT_MODEL_MEMINFO_FILE}" ]
  run agent_health_url
  [ "${output}" = "http://127.0.0.1:30001/health" ]
}

@test "agent-model falls back to the pin for junk env values" {
  export AGENT_MODEL_PORT="not-a-port"
  run agent_port
  [ "${output}" = "30001" ]
  export AGENT_MODEL_REF=""
  run agent_ref
  [ "${output}" = "main" ]
  export AGENT_MODEL_READY_S="0"
  run agent_ready_s
  [ "${output}" = "900" ]
  export AGENT_MODEL_MIN_DISK_GB="abc"
  run agent_min_disk_gb
  [ "${output}" = "160" ]
  export AGENT_MODEL_MIN_MEM_GIB="-3"
  run agent_min_mem_gib
  [ "${output}" = "110" ]
}

@test "agent-model help, unknown arg, and bare status verb" {
  run bash "${AM}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Qwen3.8-Flash-Next"* ]]
  [[ "${output}" == *"127.0.0.1"* ]]
  run bash "${AM}" --nope
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"Unknown arg"* ]]
  run bash "${AM}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"state=stopped"* ]]
}

@test "agent-model status --json reports stopped with the contract shape" {
  run bash "${AM}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"state":"stopped"'* ]]
  [[ "${output}" == *'"url":"http://127.0.0.1:30001/health"'* ]]
  [[ "${output}" == *'"model":"Qwen3.8-Flash-Next"'* ]]
  [[ "${output}" == *'"port":30001'* ]]
  [[ "${output}" == *'"profile":{"parallel":2,"context":32768,"max_tokens":4096,"kv_dtype":"fp8","vision":0}'* ]]
  [[ "${output}" == *'"container":"ez-agent-model"'* ]]
}

@test "agent-model status --json maps running plus health to ready" {
  touch "${TEST_TMP_DIR}/container_exists"
  export STUB_CURL_RC=0
  run bash "${AM}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"state":"ready"'* ]]
  run grep -c 'curl -fsS' "${CURL_CALLS_LOG}"
  [ "${output}" = "1" ]
}

@test "agent-model status --json maps starting and unhealthy states" {
  touch "${TEST_TMP_DIR}/container_exists"
  export STUB_CURL_RC=22
  export STUB_DOCKER_STATUS=created
  run bash "${AM}" status --json
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'"state":"starting"'* ]]
  export STUB_DOCKER_STATUS=running STUB_DOCKER_HEALTH=starting
  run bash "${AM}" status --json
  [[ "${output}" == *'"state":"starting"'* ]]
  export STUB_DOCKER_STATUS=exited STUB_DOCKER_HEALTH=""
  run bash "${AM}" status --json
  [[ "${output}" == *'"state":"unhealthy"'* ]]
}

@test "agent-model status human line names state and container" {
  touch "${TEST_TMP_DIR}/container_exists"
  export STUB_CURL_RC=0
  run bash "${AM}" status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"state=ready"* ]]
  [[ "${output}" == *"container=ez-agent-model"* ]]
}

@test "agent-model probes container existence and inspect fields" {
  run agent_container_exists
  [ "${status}" -ne 0 ]
  touch "${TEST_TMP_DIR}/container_exists"
  export STUB_DOCKER_STATUS=restarting
  run agent_container_exists
  [ "${status}" -eq 0 ]
  run agent_container_field '{{.State.Status}}'
  [ "${output}" = "restarting" ]
  run agent_container_field '{{if .State.Health}}{{.State.Health.Status}}{{end}}'
  [ "${output}" = "" ]
  export STUB_DOCKER_HEALTH=healthy
  run agent_container_field '{{if .State.Health}}{{.State.Health.Status}}{{end}}'
  [ "${output}" = "healthy" ]
  run agent_resolve_state
  [ "${output}" = "ready" ]
}

@test "agent-model status json helper prints the pinned profile" {
  run agent_status_json unhealthy
  [ "${status}" -eq 0 ]
  [[ "${output}" == '{"state":"unhealthy"'* ]]
  [[ "${output}" == *'"kv_dtype":"fp8"'* ]]
  [[ "${output}" == *'"vision":0'* ]]
}

@test "agent-model preflight refuses a non-loopback bind host" {
  export AGENT_MODEL_HOST="0.0.0.0"
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"must be 127.0.0.1"* ]]
  run agent_health_url
  [ "${status}" -ne 0 ]
}

@test "agent-model preflight refuses when a tool is missing" {
  export AGENT_MODEL_CURL_BIN=agent-model-no-curl
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"needs curl"* ]]
  run agent_require_tools
  [ "${status}" -eq 4 ]
  unset AGENT_MODEL_CURL_BIN
  run agent_require_tools
  [ "${status}" -eq 0 ]
}

@test "agent-model preflight refuses when free disk is short" {
  export STUB_DF_AVAIL_KIB=104857600
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"free disk 100 GB < 160 GB"* ]]
  run grep -c 'df -Pk' "${DF_CALLS_LOG}"
  [ "${output}" = "1" ]
}

@test "agent-model preflight refuses when df cannot read the path" {
  export STUB_DF_RC=1
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"cannot measure free disk"* ]]
  run agent_disk_free_gb
  [ "${status}" -ne 0 ]
}

@test "agent-model preflight refuses when MemAvailable is short" {
  write_meminfo 41943040
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"MemAvailable 40 GiB < 110 GiB"* ]]
  run agent_mem_available_gib
  [ "${output}" = "40" ]
}

@test "agent-model preflight refuses when meminfo is unreadable" {
  export AGENT_MODEL_MEMINFO_FILE="${TEST_TMP_DIR}/nope-meminfo"
  run bash "${AM}" run
  [ "${status}" -eq 4 ]
  [[ "${output}" == *"cannot read"* ]]
  run agent_mem_available_gib
  [ "${status}" -ne 0 ]
}

@test "agent-model preflight refuses while a heavy GPU mode holds the spark" {
  local mode
  for mode in wan ltx trellis klein; do
    occupancy_write "${mode}" false 0 0 0
    run bash "${AM}" run
    [ "${status}" -eq 2 ] || return 1
    [[ "${output}" == *"occupancy is ${mode}"* ]] || return 1
  done
}

@test "agent-model allows idle and llm-desk occupancy" {
  occupancy_write llm-desk false 0 0 0
  run agent_refuse_heavy_occupancy
  [ "${status}" -eq 0 ]
  occupancy_write idle false 0 0 0
  run agent_refuse_heavy_occupancy
  [ "${status}" -eq 0 ]
}

@test "agent-model occupancy mode falls back to the state file" {
  printf '{"version":1,"mode":"ltx"}\n' >"${COMFY_OUTPUT_DIR}/.occupancy.json"
  unset -f occupancy_mode
  run agent_occupancy_mode
  [ "${output}" = "ltx" ]
  run agent_occupancy_mode_file
  [ "${output}" = "ltx" ]
  rm -f "${COMFY_OUTPUT_DIR}/.occupancy.json"
  run agent_occupancy_mode_file
  [ "${output}" = "idle" ]
  printf 'not json\n' >"${COMFY_OUTPUT_DIR}/.occupancy.json"
  run agent_occupancy_mode_file
  [ "${output}" = "idle" ]
}

@test "agent-model run declines without the typed yes" {
  run bash -c "printf '\n' | env -u AGENT_MODEL_ASSUME_YES bash '${AM}' run"
  [ "${status}" -eq 5 ]
  [[ "${output}" == *"Aborted by user"* ]]
  [ ! -d "${AGENT_MODEL_HOME}" ]
}

@test "agent-model run accepts the typed yes and reaches ready" {
  write_recipe_fixture
  touch "${TEST_TMP_DIR}/container_exists"
  export STUB_CURL_RC=0
  run bash -c "printf 'yes\n' | env -u AGENT_MODEL_ASSUME_YES bash '${AM}' run"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"HEAVY WORKLOAD"* ]]
  [[ "${output}" == *"agent-model ready"* ]]
  run grep 'start ' "${START_CALLS_LOG}"
  [ "${status}" -eq 0 ]
}

@test "agent-model run clones the pinned recipe and exports the profile" {
  write_recipe_fixture
  export STUB_CURL_RC=0
  run bash "${AM}" run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cloning pinned recipe"* ]]
  run grep -c 'clone --depth 1 --branch main' "${GIT_CALLS_LOG}"
  [ "${output}" = "1" ]
  run grep 'profile HOST=' "${START_CALLS_LOG}"
  [[ "${output}" == *"HOST=127.0.0.1"* ]]
  [[ "${output}" == *"PORT=30001"* ]]
  [[ "${output}" == *"SERVED_NAME=Qwen3.8-Flash-Next"* ]]
  [[ "${output}" == *"PARALLEL=2"* ]]
  [[ "${output}" == *"CONTEXT=32768"* ]]
  [[ "${output}" == *"MAX_TOKENS=4096"* ]]
  [[ "${output}" == *"KV_DTYPE=fp8"* ]]
  [[ "${output}" == *"VISION=0"* ]]
  [[ "${output}" == *"THINKING=1"* ]]
  [[ "${output}" == *"NO_UPDATE=1"* ]]
  [[ "${output}" == *"CONTAINER=ez-agent-model"* ]]
  [[ "${output}" == *"MEM_FLOOR=9"* ]]
  run grep -c 'curl -fsS' "${CURL_CALLS_LOG}"
  [ "${output}" = "1" ]
}

@test "agent-model run honors operator profile overrides" {
  write_recipe_fixture
  export PARALLEL=4 KV_DTYPE=bf16 CONTAINER_NAME=mine
  export STUB_CURL_RC=0
  run bash "${AM}" run
  [ "${status}" -eq 0 ]
  run grep 'profile HOST=' "${START_CALLS_LOG}"
  [[ "${output}" == *"PARALLEL=4"* ]]
  [[ "${output}" == *"KV_DTYPE=bf16"* ]]
  [[ "${output}" == *"CONTAINER=mine"* ]]
  run agent_container_name
  [ "${output}" = "mine" ]
}

@test "agent-model run updates an existing checkout without cloning" {
  make_agent_home
  export STUB_CURL_RC=0
  run bash "${AM}" run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"updating pinned recipe"* ]]
  run grep -c 'fetch --depth 1 origin main' "${GIT_CALLS_LOG}"
  [ "${output}" = "1" ]
  run grep -c 'reset --hard origin/main' "${GIT_CALLS_LOG}"
  [ "${output}" = "1" ]
  run grep -c 'checkout main' "${GIT_CALLS_LOG}"
  [ "${output}" = "1" ]
  run grep -c 'clone' "${GIT_CALLS_LOG}"
  [ "${output}" = "0" ]
}

@test "agent-model run fails when git fails" {
  write_recipe_fixture
  export STUB_GIT_RC=128
  run bash "${AM}" run
  [ "${status}" -eq 1 ]
}

@test "agent-model run refuses a checkout without start.sh" {
  mkdir -p "${RECIPE_FIXTURE_DIR}"
  export STUB_CURL_RC=0
  run bash "${AM}" run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"no start.sh"* ]]
}

@test "agent-model run fails when the recipe start.sh fails" {
  make_agent_home
  export STUB_START_RC=3
  run bash "${AM}" run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"start.sh failed"* ]]
}

@test "agent-model run reports a health timeout" {
  write_recipe_fixture
  export STUB_CURL_RC=22 AGENT_MODEL_READY_S=3
  run bash "${AM}" run
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"did not answer within 3s"* ]]
  run grep -c 'curl -fsS' "${CURL_CALLS_LOG}"
  [ "${output}" = "3" ]
}

@test "agent-model poll helper waits until health answers" {
  export STUB_CURL_OK_AFTER=2 AGENT_MODEL_READY_S=5
  run agent_poll_health
  [ "${status}" -eq 0 ]
  run agent_health_ok
  [ "${status}" -eq 0 ]
}

@test "agent-model health probe fails when curl fails" {
  export STUB_CURL_RC=7
  run agent_health_ok
  [ "${status}" -ne 0 ]
  export AGENT_MODEL_HOST=0.0.0.0
  run agent_health_ok
  [ "${status}" -ne 0 ]
}

@test "agent-model recipe script helper errors on a missing script" {
  mkdir -p "${AGENT_MODEL_HOME}"
  run agent_run_recipe_script stop.sh
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"recipe script missing"* ]]
}

@test "agent-model stop without a checkout reports an error" {
  run bash "${AM}" stop
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"nothing to stop"* ]]
  [ ! -d "${AGENT_MODEL_HOME}" ]
}

@test "agent-model stop runs the recipe stop.sh" {
  make_agent_home
  run bash "${AM}" stop
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"agent-model stopped"* ]]
  run grep 'stop ' "${STOP_CALLS_LOG}"
  [ "${status}" -eq 0 ]
}

@test "agent-model stop fails when the recipe stop.sh fails" {
  make_agent_home
  export STUB_STOP_RC=9
  run bash "${AM}" stop
  [ "${status}" -eq 1 ]
}

@test "agent-model stop fails when stop.sh is missing" {
  mkdir -p "${AGENT_MODEL_HOME}"
  run bash "${AM}" stop
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"recipe script missing"* ]]
}

@test "agent-model profile export keeps values already in the environment" {
  export PARALLEL=7
  agent_export_profile
  [ "${PARALLEL}" = "7" ]
  [ "${PORT}" = "30001" ]
  [ "${CONTEXT}" = "32768" ]
  [ "${TENSORFOLD_NO_UPDATE_CHECK}" = "1" ]
  agent_env_default PARALLEL "2"
  [ "${PARALLEL}" = "7" ]
  agent_env_default MEM_FLOOR_GIB "9"
  [ "${MEM_FLOOR_GIB}" = "9" ]
}

@test "agent-model profile export refuses a non-loopback bind" {
  export AGENT_MODEL_HOST="10.0.0.5"
  run agent_export_profile
  [ "${status}" -eq 1 ]
}

@test "agent-model external command indirections honour their env vars" {
  export AGENT_MODEL_GIT_BIN=git AGENT_MODEL_DOCKER_BIN=docker
  export AGENT_MODEL_CURL_BIN=curl AGENT_MODEL_DF_BIN=df
  run agent_run_git --version
  [ "${status}" -eq 0 ]
  run agent_run_docker --version
  [ "${status}" -eq 0 ]
  run agent_run_curl --version
  [ "${status}" -eq 0 ]
  run agent_run_df -Pk "${TEST_TMP_DIR}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"/dev/fake"* ]]
}

@test "agent-model disk probe falls back to root for a missing hf path" {
  export HF_HOME="${TEST_TMP_DIR}/does-not-exist"
  run agent_disk_free_gb
  [ "${status}" -eq 0 ]
  [ "${output}" = "200" ]
  run grep 'df -Pk /' "${DF_CALLS_LOG}"
  [ "${status}" -eq 0 ]
}

@test "agent-model preflight passes with a healthy host" {
  run agent_preflight
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"MemAvailable 120 GiB"* ]]
}

@test "agent-model parse_args maps verbs and flags" {
  parse_args status --json
  [ "${CMD}" = "status" ]
  [ "${JSON_FLAG}" = "--json" ]
  parse_args run
  [ "${CMD}" = "run" ]
  [ -z "${JSON_FLAG}" ]
  parse_args stop
  [ "${CMD}" = "stop" ]
  run parse_args bogus
  [ "${status}" -eq 1 ]
}
