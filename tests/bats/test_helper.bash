#!/usr/bin/env bash
# ## test_helper
#
# Shared BATS helpers for ez-comfy-stack hermetic tests.
#
# Purpose:
#   Provide a consistent temporary environment (REPO_ROOT, MODELS_DIR, mock PATH)
#   and install fake binaries for docker, wondershaper, speedtest-cli, and
#   huggingface-cli so suites never touch a real GPU, sudo, or network.
#
# Style:
#   Google Shell Style Guide where applicable (sourced library; not executable).
#   Diagnostics from production code under test still use project log helpers.
#
# Usage:
#   load 'test_helper'
#   setup() { setup_repo_env; install_docker_mocks; }
#   teardown() { teardown_repo_env; }
#

#######################################
# Resolve absolute repository root from the current BATS test file location.
# Globals:
#   BATS_TEST_FILENAME
# Arguments:
#   None
# Outputs:
#   Writes absolute path to stdout
# Returns:
#   0 on success
#######################################
bats_canonical_repo_root() {
  local here
  here="$(cd "$(dirname "${BATS_TEST_FILENAME}")" && pwd)"
  cd "${here}/../.." && pwd
}

#######################################
# Create temp dir, export paths, and set safe mock defaults for headroom.
# Globals:
#   Many TEST_*/LAB_*/PATH/MODELS_DIR exports
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when mktemp succeeds
#######################################
setup_repo_env() {
  export REPO_ROOT
  REPO_ROOT="$(bats_canonical_repo_root)"
  export SCRIPT_DIR="${REPO_ROOT}/scripts"
  export MANAGE_SH="${REPO_ROOT}/scripts/manage.sh"
  export UTILITIES_DIR="${REPO_ROOT}/scripts/utilities"
  export TEST_TMP_DIR
  TEST_TMP_DIR="$(mktemp -d)"
  export PATH="${TEST_TMP_DIR}/bin:${PATH}"
  mkdir -p "${TEST_TMP_DIR}/bin" "${TEST_TMP_DIR}/models"
  export MODELS_DIR="${TEST_TMP_DIR}/models"
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export LAB_MOCK_IFACE=eth0
  export LAB_MOCK_WONDERSHAPER=1
  export LAB_NO_SUDO=1
  export LAB_MOCK_HF_DOWNLOAD=1
  export MIN_HOST_FREE_GIB=28
  export MIN_DISK_FREE_GIB=40
  export MEM_LIMIT=90g
}

#######################################
# Remove TEST_TMP_DIR (idempotent cleanup for BATS teardown).
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
teardown_repo_env() {
  rm -rf "${TEST_TMP_DIR:-}" || true
}

#######################################
# Write an executable mock script into $TEST_TMP_DIR/bin/$name.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   $1 - Command name on PATH
#   $2 - Shell body (no shebang)
# Outputs:
#   Creates file under TEST_TMP_DIR/bin
# Returns:
#   0
#######################################
install_mock_bin() {
  local name="${1}"
  local body="${2}"
  cat >"${TEST_TMP_DIR}/bin/${name}" <<EOF
#!/usr/bin/env bash
${body}
EOF
  chmod +x "${TEST_TMP_DIR}/bin/${name}"
}

#######################################
# Install a docker CLI mock for compose flags and up/down/ps/logs.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Mock binary + docker_calls.log
# Returns:
#   0
#######################################
install_docker_mocks() {
  install_mock_bin docker '
echo "docker $*" >> "${TEST_TMP_DIR}/docker_calls.log"
if [[ "${1}" != "compose" ]]; then
  if [[ "${1}" == "--version" ]]; then
    echo "Docker version 27.0.0"
    exit 0
  fi
  exit 0
fi
shift
while [[ $# -gt 0 ]]; do
  case "${1}" in
    -f|--file|--project-name|-p)
      shift 2 || true
      ;;
    version)
      echo "Docker Compose version v2.0.0"
      exit 0
      ;;
    ps)
      if [[ " $* " == *" --format json"* ]]; then
        if [[ -f "${TEST_TMP_DIR}/compose_running" ]]; then
          echo "{\"Service\":\"comfyui\",\"State\":\"running\"}"
        fi
        exit 0
      fi
      if [[ " $* " == *" --status running"* ]]; then
        if [[ -f "${TEST_TMP_DIR}/compose_running" ]]; then
          echo "comfyui"
        fi
        exit 0
      fi
      echo "NAME STATUS"
      exit 0
      ;;
    up)
      touch "${TEST_TMP_DIR}/compose_running"
      echo "ok"
      exit 0
      ;;
    down)
      rm -f "${TEST_TMP_DIR}/compose_running"
      echo "ok"
      exit 0
      ;;
    logs)
      echo "ok"
      exit 0
      ;;
    *)
      shift || true
      ;;
  esac
done
exit 0
'
  : >"${TEST_TMP_DIR}/docker_calls.log"
}

#######################################
# Install wondershaper mock that logs argv.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Mock binary + wondershaper.log
# Returns:
#   0
#######################################
install_wondershaper_mock() {
  install_mock_bin wondershaper '
echo "wondershaper $*" >> "${TEST_TMP_DIR}/wondershaper.log"
exit 0
'
  : >"${TEST_TMP_DIR}/wondershaper.log"
}

#######################################
# Install speedtest-cli mock reporting fixed download Mbps.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   $1 - Download Mbps integer (default 100)
# Outputs:
#   Mock binary
# Returns:
#   0
#######################################
install_speedtest_mock() {
  local mbps="${1:-100}"
  install_mock_bin speedtest-cli "
echo \"Download: ${mbps} Mbit/s\"
echo \"Upload: 20 Mbit/s\"
exit 0
"
}

#######################################
# Install no-op hf and huggingface-cli mocks for CLI presence checks.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Mock binaries
# Returns:
#   0
#######################################
install_hf_mock() {
  install_mock_bin hf '
echo "hf $*" >>"${TEST_TMP_DIR}/hf_calls.log"
echo "hf $*"
exit 0
'
  install_mock_bin huggingface-cli '
echo "huggingface-cli $*" >>"${TEST_TMP_DIR}/hf_calls.log"
echo "huggingface-cli $*"
# Simulate modern stub that refuses download
if [[ "${1:-}" == "download" ]]; then
  echo "Warning: huggingface-cli is deprecated and no longer works. Use hf instead." >&2
  exit 1
fi
exit 0
'
  : >"${TEST_TMP_DIR}/hf_calls.log"
}
