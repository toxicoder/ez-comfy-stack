#!/usr/bin/env bash
#
# ## setup-client
#
# Operator laptop bootstrap: tools, SSH Host ez-spark, optional remote Spark
# setup. Never auto-starts Comfy (restart: "no", type yes on start).
#
# Usage:
#   ./scripts/utilities/setup-client.sh [--host H] [--user U] [--port N]
#   ./scripts/utilities/setup-client.sh --onboard [...]
#   ./scripts/utilities/setup-client.sh --ui
#
# @command setup-client

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/client_os.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/client_os.sh"

#######################################
# Print setup-client usage.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
setup_client_usage() {
  cat <<'EOF' >&2
Usage: setup-client.sh [--onboard] [--ui] [--host H] [--user U] [--port N] [--download]
  Default     Laptop: packages, SSH key, Host ez-spark LocalForward
  --onboard   Spark host: manage.sh setup. Laptop: client then remote doctor
  --ui        Print/open the forwarded ComfyUI URL (ssh -N -L unless mocked)
  --download  With --onboard from a laptop, also run remote download-models
Never starts the stack. Next: ssh ez-spark && ./scripts/manage.sh start  # type yes
EOF
}

#######################################
# SSH to the Spark and run clone + setup + doctor (no start).
# Globals:
#   LAB_MOCK_SSH, REPO_ROOT
# Arguments:
#   $1 - git ref to clone
#   $2 - 1 to also download-models
# Outputs:
#   Status via log
# Returns:
#   0 on success
#######################################
remote_spark_bootstrap() {
  local ref="${1:?ref}"
  local download="${2:-0}"
  if [[ ${LAB_MOCK_SSH:-} == "1" ]]; then
    log "LAB_MOCK_SSH: would clone -b ${ref}, setup --install-docker, doctor"
    if [[ ${download} -eq 1 ]]; then
      log "LAB_MOCK_SSH: would download-models (not start)"
    fi
    return 0
  fi
  local remote
  remote=$(
    cat <<EOF
set -euo pipefail
if [[ ! -d ez-comfy-stack/scripts ]]; then
  git clone -b ${ref} https://github.com/toxicoder/ez-comfy-stack.git
fi
cd ez-comfy-stack
./scripts/manage.sh setup --install-docker
./scripts/manage.sh doctor
EOF
  )
  if [[ ${download} -eq 1 ]]; then
    remote+=$'\n./scripts/manage.sh download-models\n'
  fi
  # Client-side ${ref} is intentional; the Spark has no EZ_DOCS_GIT_REF.
  # shellcheck disable=SC2029
  ssh ez-spark "${remote}"
}

#######################################
# Foreground port-forward helper, or print the URL when mocked.
# Globals:
#   COMFY_PORT, LAB_MOCK_SSH
# Arguments:
#   None
# Outputs:
#   Status via log; may exec ssh
# Returns:
#   ssh status
#######################################
spark_ui_tunnel() {
  local port="${COMFY_PORT:-8188}"
  log "Open http://127.0.0.1:${port} after the Spark stack is started (type yes)."
  if [[ ${LAB_MOCK_SSH:-} == "1" ]]; then
    log "LAB_MOCK_SSH: ssh -N -L ${port}:127.0.0.1:${port} ez-spark"
    return 0
  fi
  exec ssh -N -L "${port}:127.0.0.1:${port}" ez-spark
}

#######################################
# Laptop client bootstrap.
# Globals:
#   SPARK_HOST, SPARK_USER, COMFY_PORT
# Arguments:
#   None
# Outputs:
#   Status via log
# Returns:
#   0 when SSH config is written
#######################################
run_laptop_client() {
  local os host user port
  os="$(detect_client_os)"
  log "client OS: ${os}"
  install_client_packages "${os}" || return 1
  ensure_ssh_key || return 1
  host="${SPARK_HOST:-127.0.0.1}"
  user="${SPARK_USER:-${USER:-spark}}"
  port="${COMFY_PORT:-8188}"
  write_ez_spark_ssh_config "${host}" "${user}" "${port}"
  log "Next: ssh ez-spark"
  log "Then: ./scripts/manage.sh start   # type yes - never auto-started"
  log "UI:   http://127.0.0.1:${port} (after start + this LocalForward)"
}

#######################################
# Onboard: Spark setup locally, or laptop client + remote bootstrap.
# Globals:
#   SPARK_HOST, EZ_DOCS_GIT_REF
# Arguments:
#   $1 - 1 to download-models remotely
# Outputs:
#   Status via log
# Returns:
#   0 on success
#######################################
run_onboard() {
  local download="${1:-0}"
  if client_is_spark_host; then
    log "This host looks like the Spark - running manage.sh setup"
    bash "${REPO_ROOT}/scripts/manage.sh" setup --install-docker
    return $?
  fi
  run_laptop_client || return 1
  remote_spark_bootstrap "${EZ_DOCS_GIT_REF:-development}" "${download}"
  log "Remote bootstrap finished. Stack is NOT started."
  log "ssh ez-spark && ./scripts/manage.sh start   # type yes"
}

#######################################
# CLI for setup-client / onboard / spark-ui.
# Globals:
#   SPARK_HOST, SPARK_USER, COMFY_PORT
# Arguments:
#   flags
# Outputs:
#   Status via log
# Returns:
#   0 on success
#######################################
setup_client_main() {
  local mode="client"
  local download=0
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --onboard) mode="onboard" ;;
      --ui) mode="ui" ;;
      --download) download=1 ;;
      -h | --help)
        setup_client_usage
        return 0
        ;;
      --host)
        SPARK_HOST="${2:?--host needs a value}"
        export SPARK_HOST
        shift
        ;;
      --user)
        SPARK_USER="${2:?--user needs a value}"
        export SPARK_USER
        shift
        ;;
      --port)
        COMFY_PORT="${2:?--port needs a value}"
        export COMFY_PORT
        shift
        ;;
      --host=*)
        SPARK_HOST="${1#--host=}"
        export SPARK_HOST
        ;;
      --user=*)
        SPARK_USER="${1#--user=}"
        export SPARK_USER
        ;;
      --port=*)
        COMFY_PORT="${1#--port=}"
        export COMFY_PORT
        ;;
      *)
        err "Unknown flag: ${1}"
        setup_client_usage
        return 1
        ;;
    esac
    shift
  done
  case "${mode}" in
    client) run_laptop_client ;;
    onboard) run_onboard "${download}" ;;
    ui) spark_ui_tunnel ;;
    *)
      err "unknown mode ${mode}"
      return 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  setup_client_main "$@"
fi
