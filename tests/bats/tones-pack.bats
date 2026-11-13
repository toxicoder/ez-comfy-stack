#!/usr/bin/env bats
#
# Cover scripts/utilities/tones-pack.sh (help, ffmpeg gate, argv forwarding). Hermetic mocks.

load 'test_helper'

setup() {
  setup_repo_env
  export TP="${UTILITIES_DIR}/tones-pack.sh"
  chmod +x "${TP}"
  install_mock_bin ffmpeg "echo \"ffmpeg \$*\" >>\"\${TEST_TMP_DIR}/ffmpeg.log\"; exit 0"
  # shellcheck disable=SC1090,SC1091
  source "${TP}"
}

teardown() {
  teardown_repo_env
}

#######################################
# Install a python3 stub that records argv and the inherited PYTHONPATH.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   $1 - exit status the stub returns (default 0)
# Outputs:
#   Writes ${TEST_TMP_DIR}/bin/python3 and ${TEST_TMP_DIR}/python.log
# Returns:
#   0
#######################################
install_python_stub() {
  local status="${1:-0}"
  install_mock_bin python3 "
echo \"python \$*\" >>\"\${TEST_TMP_DIR}/python.log\"
echo \"argv: \$*\"
echo \"pythonpath: \${PYTHONPATH:-}\"
exit ${status}
"
}

@test "tones-pack cmd_help prints usage and every flag" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tones-pack.sh"* ]]
  [[ "${output}" == *"--out DIR"* ]]
  [[ "${output}" == *"--sample-rate 44100|48000"* ]]
  [[ "${output}" == *"--dry-run"* ]]
  [[ "${output}" == *"ffmpeg"* ]]
  run bash "${TP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  [[ "${output}" == *"--catalog FILE"* ]]
  run bash "${TP}" -h
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tone pack"* ]]
  run bash "${TP}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
}

@test "tones-pack help path returns before the ffmpeg gate" {
  mock_path_hide ffmpeg
  run command -v ffmpeg
  [ "${status}" -ne 0 ]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  [[ "${output}" != *"ffmpeg is required"* ]]
  run cmd_run help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  mock_path_restore
}

@test "tones-pack require_ffmpeg passes with ffmpeg and fails without" {
  run require_ffmpeg
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
  mock_path_hide ffmpeg
  run require_ffmpeg
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  [[ "${output}" == *"tones-pack"* ]]
  run cmd_run --out "${TEST_TMP_DIR}/pack"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  mock_path_restore
  install_mock_bin ffmpeg 'exit 0'
  require_ffmpeg
}

@test "tones-pack cmd_run forwards argv to ez_tones.pack" {
  install_python_stub 0
  run cmd_run --out "${TEST_TMP_DIR}/pack" --kind notification --tone glass-two-note \
    --pack-name "Shop Tones" --version 1.2.0 --sample-rate 48000 --dry-run
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"argv: -m ez_tones.pack"* ]]
  [[ "${output}" == *"--out ${TEST_TMP_DIR}/pack"* ]]
  [[ "${output}" == *"--kind notification"* ]]
  [[ "${output}" == *"--tone glass-two-note"* ]]
  [[ "${output}" == *"--sample-rate 48000"* ]]
  [[ "${output}" == *"--dry-run"* ]]
  [[ "${output}" == *"pythonpath: ${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib"* ]]
  grep -Fq -- '-m ez_tones.pack' "${TEST_TMP_DIR}/python.log"
  [ ! -e "${TEST_TMP_DIR}/ffmpeg.log" ]
}

@test "tones-pack forwards unknown flags and the module exit code" {
  install_python_stub 2
  run cmd_run --bogus-flag
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"--bogus-flag"* ]]
  grep -Fq -- '--bogus-flag' "${TEST_TMP_DIR}/python.log"
  install_python_stub 1
  run cmd_run --sample-rate nope --out "${TEST_TMP_DIR}/pack"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"--sample-rate nope"* ]]
}

@test "tones-pack parses cleanly and never starts docker" {
  run bash -n "${TP}"
  [ "${status}" -eq 0 ]
  run grep -q 'compose up' "${TP}"
  [ "${status}" -ne 0 ]
  run grep -Eq 'docker (start|run|compose)' "${TP}"
  [ "${status}" -ne 0 ]
  run grep -q '^# @command tones-pack$' "${TP}"
  [ "${status}" -eq 0 ]
}
