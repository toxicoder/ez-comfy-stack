#!/usr/bin/env bats
#
# ## spark-farm.bats
#
# Cover scripts/utilities/spark-farm.sh. Hermetic SSH/rsync/ping/curl mocks.
#

load 'test_helper'

setup() {
  setup_repo_env
  export SF="${UTILITIES_DIR}/spark-farm.sh"
  chmod +x "${SF}"
  export SPARK_HOSTS="spark-0.local,spark-1.local"
  export SPARK_USER="nvidia"
  export SPARK_COMFY_URLS="http://spark-0.local:8188,http://spark-1.local:8188"
  export SPARK_FABRIC_IPS="10.0.0.1,10.0.0.2"
  export FARM_SHARE="${TEST_TMP_DIR}/farm"
  install_mock_bin ssh '
echo "ssh $*" >>"${TEST_TMP_DIR}/ssh_calls.log"
echo "Up 3 minutes"
exit 0
'
  install_mock_bin rsync '
echo "rsync $*" >>"${TEST_TMP_DIR}/rsync_calls.log"
exit 0
'
  install_mock_bin ping '
echo "ping $*" >>"${TEST_TMP_DIR}/ping_calls.log"
exit 0
'
  install_mock_bin curl '
echo "curl $*" >>"${TEST_TMP_DIR}/curl_calls.log"
if [[ "$*" == *"/prompt"* && "$*" != *"/history"* ]]; then
  echo "{\"prompt_id\":\"farm1\"}"
  exit 0
fi
echo "{\"farm1\":{\"status\":\"success\"}}"
exit 0
'
  # shellcheck disable=SC1090
  source "${SF}"
}

teardown() {
  teardown_repo_env
}

@test "spark-farm csv_lines parse_args help unknown" {
  run csv_lines "a, b,c"
  [[ "${output}" == *"a"* ]]
  [[ "${output}" == *"b"* ]]
  [[ "${output}" == *"c"* ]]
  parse_args status --json
  [ "${CMD}" = "status" ]
  [ "${JSON_FLAG}" = "--json" ]
  parse_args run --film still-here --seeds 1,2,3
  [ "${FILM}" = "still-here" ]
  [ "${SEEDS}" = "1,2,3" ]
  parse_args sync-models
  [ "${CMD}" = "sync-models" ]
  run bash "${SF}" --help
  [ "${status}" -eq 0 ]
  run bash "${SF}" --nope
  [ "${status}" -ne 0 ]
}

@test "spark-farm ssh_host hint status json sync run" {
  run ssh_host spark-0.local docker ps
  [ "${status}" -eq 0 ]
  grep -q 'spark-0.local' "${TEST_TMP_DIR}/ssh_calls.log"
  run print_remote_start_hint
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"manage.sh start"* ]]
  JSON_FLAG="--json"
  run cmd_status
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"hosts"* ]]
  [[ "${output}" == *"spark-0.local"* ]]
  run cmd_sync_models
  [ "${status}" -eq 0 ]
  grep -q 'rsync' "${TEST_TMP_DIR}/rsync_calls.log"
  grep -q '10.0.0.1' "${TEST_TMP_DIR}/rsync_calls.log"
  FILM=go-see
  SEEDS="509201,509211"
  run cmd_run
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"US Excluded Territory"* ]]
  FILM=wan-shot
  run cmd_run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"wan-shot"* || "${output}" == *"concat-shots"* || "${output}" == *"worker"* ]]
}

@test "spark-farm CLI status and empty hosts fail" {
  run bash -c "SPARK_HOSTS='spark-0.local' SPARK_USER=nvidia SPARK_FABRIC_IPS=10.0.0.1 bash '${SF}' status --json"
  [ "${status}" -eq 0 ]
  run bash -c "SPARK_HOSTS= bash '${SF}' status"
  [ "${status}" -ne 0 ]
}
