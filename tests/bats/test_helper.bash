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
  local here candidate manage_real
  here="$(cd "$(dirname "${BATS_TEST_FILENAME}")" && pwd)"
  candidate="$(cd "${here}/../.." && pwd)"
  if [[ -f "${candidate}/scripts/manage.sh" ]]; then
    manage_real="$(readlink -f "${candidate}/scripts/manage.sh" 2>/dev/null || realpath "${candidate}/scripts/manage.sh" 2>/dev/null || echo "${candidate}/scripts/manage.sh")"
    dirname "$(dirname "${manage_real}")"
    return 0
  fi
  (cd "${candidate}" && pwd -P)
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
  # Per-test PATH masking state (mock_path_hide); never inherit it from a prior test.
  unset EZ_MOCK_PATH_SAVED EZ_MOCK_PATH_HIDDEN
  export PATH="${TEST_TMP_DIR}/bin:${PATH}"
  mkdir -p "${TEST_TMP_DIR}/bin" "${TEST_TMP_DIR}/models"
  export MODELS_DIR="${TEST_TMP_DIR}/models"
  export COMFY_OUTPUT_DIR="${TEST_TMP_DIR}/comfy-output"
  mkdir -p "${COMFY_OUTPUT_DIR}"
  export LAB_MOCK_FREE_MEM_GIB=64
  export LAB_MOCK_DISK_FREE_GIB=100
  export LAB_MOCK_IFACE=eth0
  export LAB_MOCK_WONDERSHAPER=1
  export LAB_NO_SUDO=1
  # Host-local speed cache must not touch the developer ~/.cache (and stays per-test).
  export DOWNLOAD_LIMIT_CACHE_DIR="${TEST_TMP_DIR}/dl-speed-cache"
  mkdir -p "${DOWNLOAD_LIMIT_CACHE_DIR}"
  export LAB_MOCK_HF_DOWNLOAD=1
  # Default speed/probe mocks - tests must not hit real network (curl/speedtest).
  export LAB_MOCK_HTTP_SPEED_MBPS="${LAB_MOCK_HTTP_SPEED_MBPS:-100}"
  export LAB_MOCK_SPEEDTEST_MBPS="${LAB_MOCK_SPEEDTEST_MBPS:-100}"
  # Hermetic guard: probe_http_download_mbps / run_speedtest skip real I/O.
  export LAB_HERMETIC="${LAB_HERMETIC:-1}"
  # Skip hf_download progress subshell + kill_pid_tree cost (~1.5s per call).
  export HF_PROGRESS="${HF_PROGRESS:-0}"
  export EZ_COMFY_PROGRESS="${EZ_COMFY_PROGRESS:-0}"
  export EZ_COMFY_PROGRESS_INTERVAL="${EZ_COMFY_PROGRESS_INTERVAL:-0}"
  unset HF_TOKEN
  export MIN_HOST_FREE_GIB=28
  export MIN_DISK_FREE_GIB=40
  export MEM_LIMIT=90g
  # Do not stream compose logs or wait for UI port in hermetic tests
  export LAB_STACK_FOLLOW=0
  export LAB_STACK_VERIFY_SETTLE=0
  export LAB_STACK_SKIP_PULL=1
  export LAB_STACK_FORCE_BUILD=1
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
# Make a command genuinely unresolvable on PATH, host-independently.
#
# Deletes the mock copy and rebuilds PATH from the mock bin dir plus a symlink
# farm of every command reachable before the first mask, minus the named one.
# A host that ships the real binary (e.g. /usr/bin/ffmpeg inside a container)
# can therefore not undo a "tool missing" case, and a host that lacks the tool
# behaves the same way.
#
# Globals:
#   PATH, TEST_TMP_DIR, EZ_MOCK_PATH_SAVED, EZ_MOCK_PATH_HIDDEN
# Arguments:
#   $1 - Command name that must become unresolvable
# Outputs:
#   Writes ${TEST_TMP_DIR}/bin-masked-<n>; exports PATH; diagnostics on stderr
# Returns:
#   0 when the command is gone from PATH; 1 when the farm broke or the
#   command is still resolvable
#######################################
mock_path_hide() {
  local name="${1}"
  local masked_dir
  local dir entry hidden
  local -a dirs=() entries=() hidden_names=()
  if [[ -z ${EZ_MOCK_PATH_SAVED:-} ]]; then
    EZ_MOCK_PATH_SAVED="${PATH}"
    export EZ_MOCK_PATH_SAVED
  fi
  IFS=':' read -r -a hidden_names <<< "${EZ_MOCK_PATH_HIDDEN:-}"
  # Fresh farm per call: PATH still points at the previous farm, so the
  # rebuild never unlinks the binaries it is itself running.
  masked_dir="${TEST_TMP_DIR}/bin-masked-${#hidden_names[@]}"
  rm -f "${TEST_TMP_DIR}/bin/${name}"
  mkdir -p "${masked_dir}"
  IFS=':' read -r -a dirs <<< "${EZ_MOCK_PATH_SAVED}"
  for dir in "${dirs[@]}"; do
    [[ -d ${dir} ]] || continue
    entries=()
    for entry in "${dir}"/*; do
      [[ -f ${entry} && -x ${entry} ]] || continue
      entries+=("${entry}")
    done
    [[ ${#entries[@]} -gt 0 ]] || continue
    # First PATH dir wins: names already linked stay as they are.
    ln -s "${entries[@]}" "${masked_dir}/" 2>/dev/null || true
  done
  for hidden in "${name}" "${hidden_names[@]}"; do
    [[ -n ${hidden} ]] && rm -f "${masked_dir}/${hidden}"
  done
  EZ_MOCK_PATH_HIDDEN="${EZ_MOCK_PATH_HIDDEN:+${EZ_MOCK_PATH_HIDDEN}:}${name}"
  export EZ_MOCK_PATH_HIDDEN
  export PATH="${TEST_TMP_DIR}/bin:${masked_dir}"
  hash -r 2>/dev/null || true
  if ! command -v bash >/dev/null 2>&1; then
    printf 'mock_path_hide: farm %s is incomplete (bash not resolvable)\n' \
      "${masked_dir}" >&2
    return 1
  fi
  if command -v "${name}" >/dev/null 2>&1; then
    printf 'mock_path_hide: %s still resolvable at %s\n' \
      "${name}" "$(command -v "${name}")" >&2
    return 1
  fi
}

#######################################
# Undo mock_path_hide and restore the PATH captured before the first mask.
# Globals:
#   PATH, EZ_MOCK_PATH_SAVED, EZ_MOCK_PATH_HIDDEN
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
mock_path_restore() {
  if [[ -n ${EZ_MOCK_PATH_SAVED:-} ]]; then
    PATH="${EZ_MOCK_PATH_SAVED}"
    export PATH
    unset EZ_MOCK_PATH_SAVED EZ_MOCK_PATH_HIDDEN
    hash -r 2>/dev/null || true
  fi
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
  if [[ "${1}" == "pull" ]]; then
    echo "Pulled ${2:-}"
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
      echo "${LAB_MOCK_DOCKER_LOGS:-ok}"
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

#######################################
# Install a sudo mock that heals directory writability without real root.
# mkdir is passed through; chown becomes chmod -R u+w so hermetic tests can
# simulate prepare_comfy_layout's sudo path.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Mock binary + sudo_calls.log
# Returns:
#   0
#######################################
install_sudo_heal_mock() {
  install_mock_bin sudo '
echo "sudo $*" >>"${TEST_TMP_DIR}/sudo_calls.log"
if [[ ${1:-} == -n ]]; then
  shift
fi
case "${1:-}" in
  mkdir)
    shift
    mkdir "$@"
    ;;
  chown)
    shift
    if [[ ${1:-} == -R ]]; then
      shift
    fi
    shift
    chmod -R u+w "$@" 2>/dev/null || true
    ;;
  chmod)
    shift
    chmod "$@"
    ;;
  *)
    exit 0
    ;;
esac
'
  : >"${TEST_TMP_DIR}/sudo_calls.log"
}
