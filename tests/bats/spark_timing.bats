#!/usr/bin/env bats
#
# Cover scripts/utilities/spark-timing.sh (Kitchen wall-clock table).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export ST="${UTILITIES_DIR}/spark-timing.sh"
  chmod +x "${ST}"
  # shellcheck disable=SC1090
  source "${ST}"
}

teardown() {
  teardown_repo_env
}

@test "spark-timing help show empty record validation" {
  run bash "${ST}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"kitchen"* ]]
  [[ "${output}" == *"not kitchen"* ]]
  run cmd_show
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"none"* ]]
  JSON_FLAG="--json"
  run cmd_show
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"recorded\":false"* ]]
  JSON_FLAG=""
  run timing_path
  [[ "${output}" == *spark-timing.json ]]
  run is_positive_seconds 12.5
  [ "${status}" -eq 0 ]
  run is_positive_seconds 0
  [ "${status}" -ne 0 ]
  run is_positive_seconds nope
  [ "${status}" -ne 0 ]
  parse_args record --klein 10 --wan 20 --ltx 30 --json
  [ "${CMD}" = "record" ]
  run cmd_record
  [ "${status}" -eq 0 ]
  [[ -f ${COMFY_OUTPUT_DIR}/spark-timing.json ]]
  grep -q '"klein_s":10' "${COMFY_OUTPUT_DIR}/spark-timing.json"
  JSON_FLAG="--json"
  run cmd_show
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"klein_s"* ]]
  KLEIN_S=""
  run cmd_record
  [ "${status}" -ne 0 ]
  run bash "${ST}" record --klein 0 --wan 1 --ltx 1
  [ "${status}" -ne 0 ]
  run bash "${ST}" nope
  [ "${status}" -ne 0 ]
}

@test "spark-timing record requires kitchen when compose is up" {
  parse_args record --klein 10 --wan 20 --ltx 30
  run cmd_record
  [ "${status}" -eq 0 ]
  grep -q '"attention":"unknown"' "${COMFY_OUTPUT_DIR}/spark-timing.json"
  touch "${TEST_TMP_DIR}/compose_running"
  export LAB_MOCK_DOCKER_LOGS="Starting server"
  run cmd_record
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"pytorch-fallback"* ]]
  export LAB_MOCK_DOCKER_LOGS="Using sage attention on sm_121"
  run cmd_record
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"sage"* ]]
  export LAB_MOCK_DOCKER_LOGS="Using Comfy Kitchen attention"
  run cmd_record
  [ "${status}" -eq 0 ]
  grep -q '"attention":"kitchen"' "${COMFY_OUTPUT_DIR}/spark-timing.json"
  grep -q '"klein_s":10' "${COMFY_OUTPUT_DIR}/spark-timing.json"
}
