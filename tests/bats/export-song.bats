#!/usr/bin/env bats
#
# Cover scripts/utilities/export-song.sh (help, ffmpeg pair gate, argv forwarding). Hermetic mocks.

load 'test_helper'

setup() {
  setup_repo_env
  export ES="${UTILITIES_DIR}/export-song.sh"
  chmod +x "${ES}"
  install_mock_bin ffmpeg "echo \"ffmpeg \$*\" >>\"\${TEST_TMP_DIR}/ffmpeg.log\"; exit 0"
  install_mock_bin ffprobe "echo \"ffprobe \$*\" >>\"\${TEST_TMP_DIR}/ffprobe.log\"; exit 0"
  # shellcheck disable=SC1090,SC1091
  source "${ES}"
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

@test "export-song cmd_help prints usage and every flag" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"export-song.sh"* ]]
  [[ "${output}" == *"AUDIO OUT_DIR"* ]]
  [[ "${output}" == *"--title NAME"* ]]
  [[ "${output}" == *"--beats-per-bar N"* ]]
  [[ "${output}" == *"--no-stems"* ]]
  [[ "${output}" == *"--no-quantize"* ]]
  [[ "${output}" == *"ffprobe"* ]]
  run bash "${ES}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  run bash "${ES}" -h
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"DAW bundle"* ]]
  run bash "${ES}" help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
}

@test "export-song help path returns before the ffmpeg pair gate" {
  mock_path_hide ffmpeg
  mock_path_hide ffprobe
  run command -v ffmpeg
  [ "${status}" -ne 0 ]
  run command -v ffprobe
  [ "${status}" -ne 0 ]
  run cmd_run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  [[ "${output}" != *"is required for export-song"* ]]
  run cmd_run help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"Usage:"* ]]
  mock_path_restore
}

@test "export-song require_ffmpeg_pair needs both ffmpeg and ffprobe" {
  run require_ffmpeg_pair
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
  mock_path_hide ffmpeg
  run require_ffmpeg_pair
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  [[ "${output}" == *"export-song"* ]]
  run cmd_run "${TEST_TMP_DIR}/master.wav" "${TEST_TMP_DIR}/bundle"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffmpeg"* ]]
  mock_path_restore
  install_mock_bin ffmpeg 'exit 0'
  mock_path_hide ffprobe
  run require_ffmpeg_pair
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffprobe"* ]]
  [[ "${output}" == *"export-song"* ]]
  run cmd_run "${TEST_TMP_DIR}/master.wav" "${TEST_TMP_DIR}/bundle"
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"ffprobe"* ]]
  mock_path_restore
  install_mock_bin ffprobe 'exit 0'
  require_ffmpeg_pair
}

@test "export-song cmd_run forwards argv to ez_music.song_export" {
  install_python_stub 0
  run cmd_run "${TEST_TMP_DIR}/master.wav" "${TEST_TMP_DIR}/bundle" \
    --title "Shop Tones" --beats-per-bar 3 --no-stems --no-quantize
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"argv: -m ez_music.song_export"* ]]
  [[ "${output}" == *"${TEST_TMP_DIR}/master.wav ${TEST_TMP_DIR}/bundle"* ]]
  [[ "${output}" == *"--title Shop Tones"* ]]
  [[ "${output}" == *"--beats-per-bar 3"* ]]
  [[ "${output}" == *"--no-stems"* ]]
  [[ "${output}" == *"--no-quantize"* ]]
  [[ "${output}" == *"pythonpath: ${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib"* ]]
  grep -Fq -- '-m ez_music.song_export' "${TEST_TMP_DIR}/python.log"
  [ ! -e "${TEST_TMP_DIR}/ffmpeg.log" ]
  [ ! -e "${TEST_TMP_DIR}/ffprobe.log" ]
}

@test "export-song forwards unknown flags and the module exit code" {
  install_python_stub 2
  run cmd_run "${TEST_TMP_DIR}/master.wav" "${TEST_TMP_DIR}/bundle" --bogus-flag
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"--bogus-flag"* ]]
  grep -Fq -- '--bogus-flag' "${TEST_TMP_DIR}/python.log"
  install_python_stub 1
  run cmd_run "${TEST_TMP_DIR}/nope.wav" "${TEST_TMP_DIR}/bundle"
  [ "${status}" -eq 1 ]
}

@test "export-song parses cleanly and never starts docker" {
  run bash -n "${ES}"
  [ "${status}" -eq 0 ]
  run grep -q 'compose up' "${ES}"
  [ "${status}" -ne 0 ]
  run grep -Eq 'docker (start|run|compose)' "${ES}"
  [ "${status}" -ne 0 ]
  run grep -q '^# @command export-song$' "${ES}"
  [ "${status}" -eq 0 ]
}
