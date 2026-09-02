#!/usr/bin/env bash
# ## common
#
# Shared logging, fatal helpers, and environment loading for ez-comfy-stack.
#
# Purpose:
#   Keep operator diagnostics consistent (prefixed; always on stderr) so stdout
#   remains free for machine-readable data such as --json payloads.
#
# Audience:
#   Sourced by manage.sh and utilities after paths.sh. Not executable alone.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#   All error/status messages go to STDERR (Google S3).
#

# ANSI-C quotes so colors are real ESC bytes (printf %s and echo -e both work).
# Single-quoted '\033…' stays literal and breaks hf_progress_emit TTY lines.
# shellcheck disable=SC2034
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
RED=$'\033[0;31m'
NC=$'\033[0m'

# Used by signal helpers to track child PIDs for Ctrl+C cleanup.
_RWSF_CHILD_PID=""
_RWSF_EXTRA_PIDS=""

#######################################
# Kill a PID and its process group (INT → TERM → KILL). Never hangs forever.
# Globals:
#   None
# Arguments:
#   $1 - PID
#   $2 - Optional label for logs
# Outputs:
#   Optional log lines
# Returns:
#   0
#######################################
kill_pid_tree() {
  local pid="${1:-}"
  local label="${2:-process}"
  local i
  [[ -n ${pid} && ${pid} =~ ^[0-9]+$ ]] || return 0
  if ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi
  # Disable job-control notifications ([1]+ Terminated …)
  set +m 2>/dev/null || true
  log "Stopping ${label} (PID ${pid})…"
  kill -INT -- "-${pid}" 2>/dev/null || kill -INT "${pid}" 2>/dev/null || true
  for i in 1 2 3 4 5; do
    kill -0 "${pid}" 2>/dev/null || return 0
    sleep 0.2
  done
  kill -TERM -- "-${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
  for i in 1 2 3; do
    kill -0 "${pid}" 2>/dev/null || return 0
    sleep 0.2
  done
  kill -KILL -- "-${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
  wait "${pid}" 2>/dev/null || true
  return 0
}

#######################################
# Run a command with Ctrl+C killing the whole process group (not just the shell).
# Uses job control so children (hf workers) die; returns 130 on interrupt.
# Globals:
#   _RWSF_CHILD_PID
# Arguments:
#   $@ - Command and arguments to run
# Outputs:
#   Command's stdout/stderr (live when TTY)
# Returns:
#   Command exit status; 130 if interrupted
#######################################
run_with_signal_forwarding() {
  local child rc=0
  set -m 2>/dev/null || true
  "$@" &
  child=$!
  _RWSF_CHILD_PID="${child}"
  # Trap-only handler: SC2329/SC2317 — ShellCheck does not see string trap refs as calls
  # shellcheck disable=SC2317,SC2329
  _rwsf_on_signal() {
    log "Interrupted — stopping download process tree…"
    kill_pid_tree "${_RWSF_CHILD_PID}" "download"
    local extra
    for extra in ${_RWSF_EXTRA_PIDS:-}; do
      kill_pid_tree "${extra}" "helper"
    done
    _RWSF_CHILD_PID=""
    _RWSF_EXTRA_PIDS=""
    exit 130
  }
  trap '_rwsf_on_signal' INT TERM
  set +e
  wait "${child}"
  rc=$?
  set -e
  trap - INT TERM
  _RWSF_CHILD_PID=""
  if [[ ${rc} -gt 128 ]]; then
    return 130
  fi
  return "${rc}"
}

#######################################
# Emit an informational diagnostic to stderr with [ez-comfy] prefix.
# Globals:
#   GREEN, NC
# Arguments:
#   $@ - Message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0
#######################################
log() {
  echo -e "${GREEN}[ez-comfy]${NC} $*" >&2
}

#######################################
# Emit a non-fatal warning to stderr with [ez-comfy][WARN] prefix.
# Globals:
#   YELLOW, NC
# Arguments:
#   $@ - Warning message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0
#######################################
warn() {
  echo -e "${YELLOW}[ez-comfy][WARN]${NC} $*" >&2
}

#######################################
# Emit an error diagnostic to stderr with [ez-comfy][ERROR] prefix.
# Does not exit; pair with return/exit or die.
# Globals:
#   RED, NC
# Arguments:
#   $@ - Error message fragments
# Outputs:
#   Writes to stderr only
# Returns:
#   0 (caller controls process exit)
#######################################
err() {
  echo -e "${RED}[ez-comfy][ERROR]${NC} $*" >&2
}

#######################################
# Log an error and terminate the process with status 1.
# Globals:
#   None
# Arguments:
#   $@ - Error message fragments passed to err
# Outputs:
#   Writes to stderr via err
# Returns:
#   Does not return; exits 1
#######################################
die() {
  err "$@"
  exit 1
}

#######################################
# Load a .env file from a directory if present (best-effort).
# Only assigns keys that are not already set in the environment so operator
# exports and hermetic tests (e.g. MODELS_DIR) take precedence over .env.
# Globals:
#   REPO_ROOT (read, optional default root)
# Arguments:
#   $1 - Directory containing .env (default REPO_ROOT or .)
# Outputs:
#   None
# Returns:
#   0 always (missing file is not an error)
#######################################
load_dotenv() {
  local root="${1:-${REPO_ROOT:-.}}"
  local env_file="${root}/.env"
  local line key val
  if [[ ! -f ${env_file} ]]; then
    return 0
  fi
  while IFS= read -r line || [[ -n ${line} ]]; do
    line="${line//$'\r'/}"
    [[ ${line} =~ ^[[:space:]]*$ ]] && continue
    [[ ${line} =~ ^[[:space:]]*# ]] && continue
    if [[ ${line} =~ ^[[:space:]]*export[[:space:]]+(.*)$ ]]; then
      line="${BASH_REMATCH[1]}"
    fi
    [[ ${line} == *"="* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    # trim whitespace around key
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ ${key} =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    # Do not clobber variables already present in the environment
    if [[ -n ${!key+x} ]]; then
      continue
    fi
    if [[ ${val} =~ ^\"(.*)\"$ ]]; then
      val="${BASH_REMATCH[1]}"
    elif [[ ${val} =~ ^\'(.*)\'$ ]]; then
      val="${BASH_REMATCH[1]}"
    fi
    export "${key}=${val}"
  done <"${env_file}"
}

#######################################
# Fail fatally if a required executable is not on PATH.
# Globals:
#   None
# Arguments:
#   $1 - Command name
# Outputs:
#   Error on stderr if missing
# Returns:
#   0 if found; otherwise exits 1 via die
#######################################
require_cmd() {
  local name="${1}"
  if ! command -v "${name}" >/dev/null 2>&1; then
    die "Required command not found: ${name}"
  fi
}

#######################################
# Locate a docker client binary (PATH first, then common absolute paths).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Absolute or PATH-resolved docker path on stdout when found
# Returns:
#   0 when found; 1 when missing
#######################################
find_docker_bin() {
  local candidate
  if candidate=$(command -v docker 2>/dev/null); then
    echo "${candidate}"
    return 0
  fi
  for candidate in /usr/bin/docker /usr/local/bin/docker; do
    if [[ -x ${candidate} ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

#######################################
# Ensure docker is available as the bare command "docker" on PATH.
# If only an absolute path exists, prepends its directory to PATH.
# Globals:
#   PATH (may be modified)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when docker is invocable; 1 otherwise
#######################################
resolve_docker_on_path() {
  local bin dir
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  if ! bin=$(find_docker_bin); then
    return 1
  fi
  dir="$(dirname "${bin}")"
  export PATH="${dir}:${PATH}"
  command -v docker >/dev/null 2>&1
}

#######################################
# Print copy-pasteable Docker CE install + docker group guidance.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Hints on stderr via err
# Returns:
#   0
#######################################
print_docker_install_hints() {
  local user
  user="$(id -un)"
  err "docker missing — install Docker CE (not snap) on DGX Spark:"
  err "  ./scripts/manage.sh setup --install-docker"
  err "  # or non-interactive:"
  err "  LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes SETUP_INSTALL_DOCKER=1 ./scripts/manage.sh setup"
  err "Manual:"
  err "  sudo apt-get update"
  err "  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
  err "  sudo usermod -aG docker ${user}"
  err "  newgrp docker   # or disconnect/reconnect SSH"
  err "Then: ./scripts/manage.sh doctor"
}

#######################################
# Return 0 when docker CLI + compose plugin respond successfully.
# Globals:
#   PATH (via resolve_docker_on_path)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when usable; 1 otherwise
#######################################
docker_cli_ok() {
  resolve_docker_on_path || return 1
  docker compose version >/dev/null 2>&1
}

#######################################
# Probe docker daemon access (docker info). Distinguishes permission errors.
# Under TEST_TMP_DIR or LAB_MOCK_DOCKER_INSTALL, compose OK is enough (hermetic).
# Globals:
#   TEST_TMP_DIR, LAB_MOCK_DOCKER_INSTALL
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 daemon OK; 1 permission denied; 2 other failure; 3 cli missing
#######################################
docker_daemon_status() {
  local out
  if ! resolve_docker_on_path; then
    return 3
  fi
  if [[ -n ${TEST_TMP_DIR:-} || ${LAB_MOCK_DOCKER_INSTALL:-} == "1" ]]; then
    if docker compose version >/dev/null 2>&1; then
      return 0
    fi
    return 2
  fi
  if out=$(docker info 2>&1); then
    return 0
  fi
  if [[ ${out} =~ [Pp]ermission\ denied|connect:\ permission ]]; then
    return 1
  fi
  return 2
}

#######################################
# Confirm whether setup may install Docker CE (interactive or env flags).
# Globals:
#   LAB_NON_INTERACTIVE, LAB_CONFIRM_TOKEN, SETUP_INSTALL_DOCKER, SETUP_YES
# Arguments:
#   $1 - Force yes when "1" (--install-docker or --yes on CLI)
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 proceed; 1 decline / missing token; 2 interactive abort
#######################################
confirm_docker_install() {
  local force="${1:-0}"
  if [[ ${force} == "1" || ${SETUP_YES:-} == "1" ]]; then
    log "Docker install confirmed"
    return 0
  fi
  if [[ ${SETUP_INSTALL_DOCKER:-} == "1" ]]; then
    if [[ ${LAB_NON_INTERACTIVE:-} == "1" && ${LAB_CONFIRM_TOKEN:-} != "yes" ]]; then
      err "SETUP_INSTALL_DOCKER=1 non-interactive needs LAB_CONFIRM_TOKEN=yes or --yes"
      return 1
    fi
    log "Docker install confirmed (SETUP_INSTALL_DOCKER)"
    return 0
  fi
  if [[ ${LAB_NON_INTERACTIVE:-} == "1" ]]; then
    err "Docker missing. Re-run: ./scripts/manage.sh setup --install-docker"
    return 1
  fi
  echo >&2
  local response
  read -r -p "Install Docker CE now (sudo apt)? Type yes to continue: " response
  if [[ ${response} =~ ^[Yy][Ee][Ss]$ ]]; then
    return 0
  fi
  log "Skipped Docker install."
  return 2
}

#######################################
# Install Docker CE + compose plugin and add current user to docker group.
# Prefer apt packages; fall back to get.docker.com. Hermetic: LAB_MOCK_DOCKER_INSTALL=1.
# Globals:
#   LAB_NO_SUDO, LAB_MOCK_DOCKER_INSTALL, LAB_MOCK_DOCKER_BIN_DIR, PATH
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when docker CLI+compose available afterward; 1 on failure
#######################################
install_docker_engine() {
  local user
  user="$(id -un)"

  # Hermetic tests first: always materialize mock docker even if host has docker
  # (GitHub Actions runners often ship docker; tests assert LAB_MOCK_DOCKER_BIN_DIR).
  if [[ ${LAB_MOCK_DOCKER_INSTALL:-} == "1" ]]; then
    local bindir="${LAB_MOCK_DOCKER_BIN_DIR:-${TEST_TMP_DIR:-/tmp}/ez-comfy-docker-bin}"
    mkdir -p "${bindir}"
    cat >"${bindir}/docker" <<'EOF'
#!/usr/bin/env bash
echo "docker $*" >>"${LAB_MOCK_DOCKER_BIN_DIR:-/tmp}/docker_install_calls.log" 2>/dev/null || true
if [[ "${1:-}" == "--version" ]]; then
  echo "Docker version 27.0.0"
  exit 0
fi
if [[ "${1:-}" == "compose" ]]; then
  echo "Docker Compose version v2.0.0"
  exit 0
fi
if [[ "${1:-}" == "info" ]]; then
  echo "Server Version: mock"
  exit 0
fi
exit 0
EOF
    chmod +x "${bindir}/docker"
    export PATH="${bindir}:${PATH}"
    log "LAB_MOCK_DOCKER_INSTALL: mock docker installed at ${bindir}/docker"
    docker_cli_ok
    return $?
  fi

  if docker_cli_ok; then
    log "docker already available: $(docker --version 2>/dev/null | head -1)"
    return 0
  fi

  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    err "Cannot install docker (LAB_NO_SUDO=1)"
    print_docker_install_hints
    return 1
  fi

  log "Installing Docker CE (apt preferred; may take a few minutes)..."

  # Snap docker breaks GPU tooling — remove if present
  if command -v snap >/dev/null 2>&1 && snap list docker >/dev/null 2>&1; then
    warn "Removing snap docker (prefer apt docker-ce for NVIDIA)"
    sudo snap remove docker 2>/dev/null || true
  fi

  local apt_ok=0
  if command -v apt-get >/dev/null 2>&1; then
    if sudo apt-get update -qq &&
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
        docker-ce docker-ce-cli containerd.io docker-compose-plugin; then
      apt_ok=1
    else
      warn "apt docker-ce install failed; trying get.docker.com"
    fi
  fi

  if [[ ${apt_ok} -ne 1 ]]; then
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL https://get.docker.com | sudo sh || {
        err "get.docker.com install failed"
        print_docker_install_hints
        return 1
      }
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y docker-compose-plugin 2>/dev/null || true
    else
      err "Neither apt docker-ce nor curl/get.docker.com available"
      print_docker_install_hints
      return 1
    fi
  fi

  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl enable --now docker 2>/dev/null || sudo service docker start 2>/dev/null || true
  fi

  sudo usermod -aG docker "${user}" 2>/dev/null || warn "usermod -aG docker failed (group may already include you)"

  if command -v nvidia-ctk >/dev/null 2>&1; then
    log "Configuring NVIDIA Container Toolkit for docker..."
    sudo nvidia-ctk runtime configure --runtime=docker 2>/dev/null || warn "nvidia-ctk configure failed"
    if command -v systemctl >/dev/null 2>&1; then
      sudo systemctl restart docker 2>/dev/null || true
    fi
  elif command -v nvidia-smi >/dev/null 2>&1; then
    warn "nvidia-smi present but nvidia-ctk missing — install nvidia-container-toolkit for GPU containers"
  fi

  # Refresh PATH for common install locations
  export PATH="/usr/bin:/usr/local/bin:${PATH}"
  hash -r 2>/dev/null || true

  if ! resolve_docker_on_path; then
    err "Docker install finished but docker binary still not found"
    print_docker_install_hints
    return 1
  fi

  log "docker installed: $(docker --version 2>/dev/null | head -1)"
  if docker compose version >/dev/null 2>&1; then
    log "docker compose: ok"
  else
    err "docker compose plugin still missing after install"
    return 1
  fi

  if ! id -nG 2>/dev/null | grep -qw docker; then
    warn "docker group not active in this shell yet — run: newgrp docker   (or re-login SSH)"
  fi
  return 0
}

#######################################
# Doctor-oriented docker preflight: CLI, compose, daemon/group.
# Globals:
#   See resolve_docker_on_path / docker_daemon_status
# Arguments:
#   None
# Outputs:
#   log/err/warn diagnostics
# Returns:
#   0 ready; 1 not ready
#######################################
#######################################
# Next-step string after a docker_daemon_status code.
# Arguments:
#   $1 - status from docker_daemon_status (0/1/2/3)
# Outputs:
#   Operator command on stdout
# Returns:
#   0
#######################################
doctor_next_step_hint() {
  case "${1:-0}" in
    1) echo "newgrp docker   # or disconnect/reconnect SSH" ;;
    2) echo "sudo systemctl start docker" ;;
    *) echo "./scripts/manage.sh setup --install-docker" ;;
  esac
}

check_docker_preflight() {
  if ! resolve_docker_on_path; then
    print_docker_install_hints
    return 1
  fi
  log "docker: $(docker --version 2>/dev/null | head -1)"
  if ! docker compose version >/dev/null 2>&1; then
    err "docker compose plugin missing"
    err "  ./scripts/manage.sh setup --install-docker"
    err "  # or: sudo apt-get install -y docker-compose-plugin"
    return 1
  fi
  log "docker compose: ok"

  local st=0
  docker_daemon_status || st=$?
  case "${st}" in
    0)
      return 0
      ;;
    1)
      err "docker permission denied — user not active in docker group for this session"
      err "  newgrp docker   # or disconnect/reconnect SSH"
      err "  # ensure: sudo usermod -aG docker $(id -un)"
      return 1
      ;;
    2)
      err "docker daemon not reachable — is the service running?"
      err "  sudo systemctl status docker"
      err "  sudo systemctl start docker"
      return 1
      ;;
    *)
      print_docker_install_hints
      return 1
      ;;
  esac
}

#######################################
# Ensure a host directory exists and is writable (mkdir as current user, no sudo).
# Globals:
#   None
# Arguments:
#   $1 - Label for errors (e.g. MODELS_DIR)
#   $2 - Directory path
# Outputs:
#   Actionable error text on stderr when not writable
# Returns:
#   0 when the directory exists and is writable; 1 otherwise
#######################################
ensure_writable_host_dir() {
  local label="${1:?ensure_writable_host_dir requires label}"
  local dir="${2:?ensure_writable_host_dir requires directory}"
  local user group
  user="$(id -un)"
  group="$(id -gn)"
  if [[ ! -d ${dir} ]]; then
    mkdir -p "${dir}" 2>/dev/null || true
  fi
  if [[ -d ${dir} && -w ${dir} ]]; then
    return 0
  fi
  err "${label}=${dir} is not writable."
  err "  ./scripts/manage.sh setup"
  err "  # or: sudo mkdir -p '${dir}' && sudo chown ${user}:${group} '${dir}'"
  return 1
}

#######################################
# Ensure MODELS_DIR exists and is writable by the current user.
# Tries mkdir -p as the current user; never uses sudo.
# Globals:
#   MODELS_DIR (read when $1 omitted)
# Arguments:
#   $1 - Directory path (default MODELS_DIR or /mnt/models)
# Outputs:
#   Actionable error text on stderr when not writable
# Returns:
#   0 when the directory exists and is writable; 1 otherwise
#######################################
ensure_models_dir() {
  local dir="${1:-${MODELS_DIR:-/mnt/models}}"
  ensure_writable_host_dir MODELS_DIR "${dir}"
}

#######################################
# Ensure COMFY_OUTPUT_DIR exists and is writable (generated PNG/MP4).
# Globals:
#   COMFY_OUTPUT_DIR (read when $1 omitted)
# Arguments:
#   $1 - Directory path (default COMFY_OUTPUT_DIR or /mnt/comfy-output)
# Outputs:
#   Actionable error text on stderr when not writable
# Returns:
#   0 when writable; 1 otherwise
#######################################
ensure_comfy_output_dir() {
  local dir="${1:-${COMFY_OUTPUT_DIR:-/mnt/comfy-output}}"
  ensure_writable_host_dir COMFY_OUTPUT_DIR "${dir}"
}

#######################################
# Create a host directory with sudo and chown when needed.
# Skips sudo when LAB_NO_SUDO=1 (tests / restricted environments).
# Globals:
#   LAB_NO_SUDO
# Arguments:
#   $1 - Label for logs/errors
#   $2 - Directory path
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when writable afterward; 1 on failure
#######################################
prepare_writable_host_dir() {
  local label="${1:?prepare_writable_host_dir requires label}"
  local dir="${2:?prepare_writable_host_dir requires directory}"
  if ensure_writable_host_dir "${label}" "${dir}" 2>/dev/null; then
    return 0
  fi
  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    err "${label}=${dir} not writable and LAB_NO_SUDO=1 (cannot sudo)"
    return 1
  fi
  log "Creating ${label} with sudo: ${dir}"
  if ! sudo mkdir -p "${dir}"; then
    err "sudo mkdir -p '${dir}' failed"
    return 1
  fi
  if ! sudo chown "$(id -u):$(id -g)" "${dir}"; then
    err "sudo chown failed for '${dir}'"
    return 1
  fi
  ensure_writable_host_dir "${label}" "${dir}"
}

#######################################
# Create MODELS_DIR with sudo and chown to the current user when needed.
# Skips sudo when LAB_NO_SUDO=1 (tests / restricted environments).
# Globals:
#   LAB_NO_SUDO, MODELS_DIR
# Arguments:
#   $1 - Directory path (default MODELS_DIR or /mnt/models)
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when writable afterward; 1 on failure
#######################################
prepare_models_dir() {
  prepare_writable_host_dir MODELS_DIR "${1:-${MODELS_DIR:-/mnt/models}}"
}

#######################################
# Create COMFY_OUTPUT_DIR with sudo/chown when needed.
# Globals:
#   LAB_NO_SUDO, COMFY_OUTPUT_DIR
# Arguments:
#   $1 - Directory path (default COMFY_OUTPUT_DIR or /mnt/comfy-output)
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when writable afterward; 1 on failure
#######################################
prepare_comfy_output_dir() {
  prepare_writable_host_dir COMFY_OUTPUT_DIR "${1:-${COMFY_OUTPUT_DIR:-/mnt/comfy-output}}"
}

#######################################
# Ensure Hugging Face CLI is available (prefer modern `hf`).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Error on stderr when missing
# Returns:
#   0 when hf or huggingface-cli is on PATH; exits 1 via die when missing
#######################################
check_hf_cli() {
  if command -v hf >/dev/null 2>&1 || command -v huggingface-cli >/dev/null 2>&1; then
    return 0
  fi
  die "Required tool missing: hf (pipx install huggingface_hub  OR  pip install -U 'huggingface_hub[cli]')"
}

#######################################
# Return 0 if PID must not be killed by lock cleanup (self / active download).
# Globals:
#   _HF_PROTECTED_PIDS, _RWSF_CHILD_PID, _RWSF_EXTRA_PIDS
# Arguments:
#   $1 - PID
# Returns:
#   0 if protected; 1 if may kill
#######################################
_hf_pid_is_protected() {
  local pid="${1:-}"
  local p
  [[ -n ${pid} ]] || return 0
  [[ ${pid} == "$$" || ${pid} == "${PPID}" ]] && return 0
  for p in ${_HF_PROTECTED_PIDS:-} ${_RWSF_CHILD_PID:-} ${_RWSF_EXTRA_PIDS:-}; do
    [[ ${pid} == "${p}" ]] && return 0
  done
  # Protect descendants of this shell (current hf children)
  if [[ -r /proc/${pid}/stat ]]; then
    local ppid
    ppid="$(awk '{print $4}' "/proc/${pid}/stat" 2>/dev/null || true)"
    [[ ${ppid} == "$$" ]] && return 0
  fi
  return 1
}

#######################################
# Clear stale Hugging Face download locks under a models root.
# By default may stop *orphan* hf PIDs (never the active download PIDs).
# locks_only=1 (mid-download): remove unheld .lock files only — never pkill.
# Globals:
#   HF_LOCK_CLEAR, HF_LOCK_CLEAR_FORCE, _HF_PROTECTED_PIDS, MODELS_DIR
# Arguments:
#   $1 - Root directory (default MODELS_DIR)
#   $2 - Optional "locks_only" to skip process kill entirely
# Outputs:
#   Status via log/warn
# Returns:
#   0 always
#######################################
clear_stale_hf_locks() {
  local root="${1:-${MODELS_DIR:-/mnt/models}}"
  local mode="${2:-}"
  local force="${HF_LOCK_CLEAR_FORCE:-0}"
  local lock removed=0 active=0 pid pids=""
  local locks_only=0
  [[ ${mode} == "locks_only" ]] && locks_only=1

  if [[ ${HF_LOCK_CLEAR:-1} == "0" ]]; then
    log "HF lock clear skipped (HF_LOCK_CLEAR=0)"
    return 0
  fi
  if [[ ! -d ${root} ]]; then
    return 0
  fi

  log "Checking for stale Hugging Face download locks under ${root} …"

  # Never kill our own active download (mid-download cleanup = locks only).
  # Skip process sweep under LAB_HERMETIC=1: parallel BATS files share a host PID
  # namespace and pgrep -f 'hf download' would kill sibling test processes.
  if [[ ${locks_only} -eq 0 && ${LAB_HERMETIC:-0} != "1" ]] &&
    command -v pgrep >/dev/null 2>&1; then
    set +m 2>/dev/null || true
    while read -r pid; do
      [[ -z ${pid} || ! ${pid} =~ ^[0-9]+$ ]] && continue
      if _hf_pid_is_protected "${pid}"; then
        continue
      fi
      if kill -0 "${pid}" 2>/dev/null; then
        log "Stopping orphan download PID ${pid}"
        kill -TERM "${pid}" 2>/dev/null || true
        pids="${pids} ${pid}"
      fi
    done < <(pgrep -f 'hf download|huggingface-cli download' 2>/dev/null || true)
    if [[ -n ${pids// /} ]]; then
      sleep 1
      for pid in ${pids}; do
        if kill -0 "${pid}" 2>/dev/null && ! _hf_pid_is_protected "${pid}"; then
          warn "Force-killing orphan download PID ${pid}"
          kill -KILL "${pid}" 2>/dev/null || true
        fi
      done
      sleep 1
    fi
  fi

  # Collect lock files
  local -a locks=()
  while IFS= read -r -d '' lock; do
    locks+=("${lock}")
  done < <(find "${root}" -type f \( -name '*.lock' -o -name '*.lock.*' \) -print0 2>/dev/null || true)

  if [[ ${#locks[@]} -eq 0 ]]; then
    log "No HF .lock files found under ${root}"
    return 0
  fi

  if [[ ${force} == "1" ]]; then
    for lock in "${locks[@]}"; do
      if rm -f "${lock}" 2>/dev/null; then
        removed=$((removed + 1))
      fi
    done
    log "HF_LOCK_CLEAR_FORCE=1: removed ${removed} lock file(s) under ${root}"
    return 0
  fi

  for lock in "${locks[@]}"; do
    local held=0
    if command -v fuser >/dev/null 2>&1; then
      if fuser "${lock}" >/dev/null 2>&1; then
        held=1
      fi
    elif command -v lsof >/dev/null 2>&1; then
      if lsof "${lock}" >/dev/null 2>&1; then
        held=1
      fi
    fi
    # Without fuser/lsof, treat as stale after optional process sweep
    if [[ ${held} -eq 1 ]]; then
      active=$((active + 1))
      continue
    fi
    if rm -f "${lock}" 2>/dev/null; then
      removed=$((removed + 1))
    fi
  done

  if [[ ${removed} -gt 0 ]]; then
    log "Removed ${removed} stale HF lock file(s) under ${root}"
  fi
  if [[ ${active} -gt 0 ]]; then
    warn "${active} lock(s) still held by live processes — wait or HF_LOCK_CLEAR_FORCE=1"
  fi
  if [[ ${removed} -eq 0 && ${active} -eq 0 ]]; then
    log "HF lock check clean under ${root}"
  fi
  return 0
}

#######################################
# Print plain-language guidance for a failed Hugging Face download.
# Suppresses stack-trace noise unless LAB_DEBUG or HF_DOWNLOAD_DEBUG is set.
# Globals:
#   LAB_DEBUG, HF_DOWNLOAD_DEBUG
# Arguments:
#   $1 - Path to a log file, or raw error text
#   $2 - Optional repo id (org/name)
# Outputs:
#   Short err/warn lines on stderr
# Returns:
#   0 always
#######################################
explain_hf_download_error() {
  local source="${1:-}"
  local repo="${2:-}"
  local text="" extracted
  if [[ -n ${source} && -f ${source} ]]; then
    text="$(cat "${source}" 2>/dev/null || true)"
  else
    text="${source}"
  fi
  if [[ -z ${repo} ]]; then
    extracted="$(printf '%s\n' "${text}" |
      sed -n 's|.*huggingface\.co/\([A-Za-z0-9_.-]\+/[A-Za-z0-9_.-]\+\).*|\1|p' |
      head -1)"
    if [[ -n ${extracted} ]]; then
      repo="${extracted}"
    fi
  fi
  if [[ -z ${repo} ]]; then
    repo="(unknown repo)"
  fi

  if [[ ${text} =~ GatedRepoError|not\ in\ the\ authorized\ list|restricted\ and\ you\ are\ not|Cannot\ access\ gated\ repo ]]; then
    err "Hugging Face gated model — access not granted for: ${repo}"
    err "  1. Open https://huggingface.co/${repo}"
    err "  2. Log in as the SAME account that owns HF_TOKEN and click Agree / accept the license"
    err "  3. Token needs gated-repo read: https://huggingface.co/settings/tokens"
    err "  4. Check identity: hf auth whoami"
    err "  5. Re-run download after access is approved"
  elif [[ ${text} =~ Invalid\ user\ token|401\ Unauthorized|401\ Client\ Error|Unauthorized ]]; then
    err "Hugging Face auth failed for: ${repo}"
    err "  Set a valid token in .env (HF_TOKEN=hf_...) or run: hf auth login"
    err "  Create tokens at: https://huggingface.co/settings/tokens"
  elif [[ ${text} =~ 429|rate\ limit|Rate\ limit ]]; then
    err "Hugging Face rate limit while downloading: ${repo}"
    err "  Wait a few minutes and re-run download-models"
  elif [[ ${text} =~ Could\ not\ connect|Name\ or\ service\ not\ known|Network\ is\ unreachable|Temporary\ failure\ in\ name\ resolution|Connection\ refused ]]; then
    err "Network error while downloading: ${repo}"
    err "  Check internet/DNS on this host and retry"
  elif [[ ${text} =~ 403|Forbidden ]]; then
    err "Hugging Face access denied (403) for: ${repo}"
    err "  Accept the model license on the repo page and ensure HF_TOKEN has read access"
    err "  https://huggingface.co/${repo}"
  else
    err "Hugging Face download failed for: ${repo}"
    err "  Re-run with LAB_DEBUG=1 for the raw CLI log"
  fi

  if [[ ${LAB_DEBUG:-} == "1" || ${HF_DOWNLOAD_DEBUG:-} == "1" ]]; then
    warn "--- raw hf download log (last 40 lines) ---"
    if [[ -n ${source} && -f ${source} ]]; then
      tail -n 40 "${source}" >&2 || true
    else
      printf '%s\n' "${text}" | tail -n 40 >&2 || true
    fi
    warn "--- end raw log ---"
  fi
}

#######################################
# Create or replace a symlink using a path relative to the link's directory.
# Absolute targets break inside Docker when host MODELS_DIR is mounted at a
# different path (/mnt/models on host vs /models in the container).
# Globals:
#   None
# Arguments:
#   $1  Target path (must exist; may be absolute)
#   $2  Link path to create or retarget
# Outputs:
#   warn on missing target or fallback to absolute
# Returns:
#   0 on success; 1 if target missing or link creation fails
#######################################
ln_sfn_relative() {
  local target="${1:?ln_sfn_relative requires target}"
  local linkpath="${2:?ln_sfn_relative requires link path}"
  local linkdir rel
  linkdir="$(dirname "${linkpath}")"
  mkdir -p "${linkdir}" || return 1
  if [[ ! -e ${target} ]]; then
    warn "ln_sfn_relative: target missing: ${target}"
    return 1
  fi
  # Prefer GNU realpath; fall back to python3 (macOS / minimal hosts)
  if rel="$(realpath --relative-to="${linkdir}" "${target}" 2>/dev/null)" && [[ -n ${rel} ]]; then
    :
  elif command -v python3 >/dev/null 2>&1; then
    rel="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' \
      "${target}" "${linkdir}")" || return 1
  else
    rel="${target}"
    warn "ln_sfn_relative: no relpath support; using absolute target (container-fragile)"
  fi
  ln -sfn "${rel}" "${linkpath}"
}

#######################################
# Lab workflow model basenames expected under MODELS_DIR/comfy after download-models.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Lines: subdir/filename
# Returns:
#   0
#######################################
lab_expected_model_relpaths() {
  cat <<'EOF'
diffusion_models/flux-2-klein-9b-nvfp4.safetensors
diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors
text_encoders/qwen_3_8b_fp4mixed.safetensors
text_encoders/gemma_3_12B_it_fp4_mixed.safetensors
text_encoders/ltx-2.3_text_projection_bf16.safetensors
vae/flux2-vae.safetensors
vae/LTX23_video_vae_bf16.safetensors
vae/LTX23_audio_vae_bf16.safetensors
EOF
}

#######################################
# MiniMax H3 lab basenames (opt-in; not part of default download-models).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Lines: subdir/filename
# Returns:
#   0
#######################################
h3_expected_model_relpaths() {
  cat <<'EOF'
diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
vae/minimax_h3_video_vae_fp16.safetensors
vae/minimax_h3_audio_vae_fp32.safetensors
EOF
}

#######################################
# Check host MODELS_DIR/comfy for lab workflow weights; warn on missing.
# Requires resolvable paths (broken symlinks count as missing). Absolute
# symlinks under comfy/ are container-fragile and produce a warn.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Optional models root (default MODELS_DIR)
# Outputs:
#   log/warn lines; list of missing files
# Returns:
#   0 if all present; 1 if any missing
#######################################
check_lab_models_ready() {
  local root="${1:-${MODELS_DIR:-/mnt/models}}"
  local rel path missing=0 link_tgt
  local comfy="${root}/comfy"
  if [[ ! -d ${comfy} ]]; then
    warn "lab models: ${comfy} missing — run ./scripts/manage.sh download-models"
    return 1
  fi
  while IFS= read -r rel; do
    [[ -z ${rel} ]] && continue
    path="${comfy}/${rel}"
    # -e follows symlinks; broken links must not count as ready
    if [[ -e ${path} ]]; then
      if [[ -L ${path} ]]; then
        link_tgt="$(readlink "${path}" 2>/dev/null || true)"
        if [[ ${link_tgt} == /* ]]; then
          warn "lab model absolute symlink (container-fragile): ${rel} → ${link_tgt}"
          warn "  Re-run ./scripts/manage.sh download-models to rewrite relative links"
        fi
      fi
      log "lab model ok: ${rel}"
    else
      if [[ -L ${path} ]]; then
        warn "lab model BROKEN symlink: ${rel} → $(readlink "${path}" 2>/dev/null || echo '?')"
      else
        warn "lab model MISSING: ${rel}"
      fi
      missing=$((missing + 1))
    fi
  done < <(lab_expected_model_relpaths)
  if [[ ${missing} -gt 0 ]]; then
    warn "Missing ${missing} lab model(s) under ${comfy} — run ./scripts/manage.sh download-models"
    warn "Then restart so Comfy models/* re-link to /models/comfy/*"
    return 1
  fi
  log "lab models: all expected files present under ${comfy}"
  return 0
}

#######################################
# Check host MODELS_DIR/comfy for MiniMax H3 lab weights.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Optional models root (default MODELS_DIR)
# Outputs:
#   log/warn lines
# Returns:
#   0 if all present; 1 if any missing
#######################################
check_h3_models_ready() {
  local root="${1:-${MODELS_DIR:-/mnt/models}}"
  local rel path missing=0 link_tgt
  local comfy="${root}/comfy"
  if [[ ! -d ${comfy} ]]; then
    warn "H3 models: ${comfy} missing — run ./scripts/manage.sh download-h3"
    return 1
  fi
  while IFS= read -r rel; do
    [[ -z ${rel} ]] && continue
    path="${comfy}/${rel}"
    if [[ -e ${path} ]]; then
      if [[ -L ${path} ]]; then
        link_tgt="$(readlink "${path}" 2>/dev/null || true)"
        if [[ ${link_tgt} == /* ]]; then
          warn "H3 model absolute symlink (container-fragile): ${rel} → ${link_tgt}"
          warn "  Re-run ./scripts/manage.sh download-h3 to rewrite relative links"
        fi
      fi
      log "H3 model ok: ${rel}"
    else
      if [[ -L ${path} ]]; then
        warn "H3 model BROKEN symlink: ${rel} → $(readlink "${path}" 2>/dev/null || echo '?')"
      else
        warn "H3 model MISSING: ${rel}"
      fi
      missing=$((missing + 1))
    fi
  done < <(h3_expected_model_relpaths)
  if [[ ${missing} -gt 0 ]]; then
    warn "Missing ${missing} H3 model(s) under ${comfy} — run ./scripts/manage.sh download-h3"
    return 1
  fi
  log "H3 models: all expected files present under ${comfy}"
  return 0
}

#######################################
# Count HF *.incomplete partials under a local-dir (resume state).
# Globals:
#   None
# Arguments:
#   $1  Destination directory path
# Outputs:
#   Integer count on stdout
# Returns:
#   0
#######################################
count_hf_incomplete() {
  local dest="${1:-}"
  local n=0
  if [[ -z ${dest} || ! -d ${dest} ]]; then
    echo 0
    return 0
  fi
  n="$(find "${dest}" -type f -name '*.incomplete' 2>/dev/null | wc -l | tr -d ' ')"
  echo "${n:-0}"
}

#######################################
# Short label for a download dest (basename of local-dir).
# Globals:
#   None
# Arguments:
#   $1  Destination directory path
# Outputs:
#   Basename on stdout
# Returns:
#   0
#######################################
hf_progress_label() {
  local dest="${1:-}"
  if [[ -z ${dest} ]]; then
    echo "download"
    return 0
  fi
  basename "${dest}"
}

#######################################
# Format kibibytes as a human size (MiB or GiB).
# Globals:
#   None
# Arguments:
#   $1  Size in KiB (integer)
# Outputs:
#   e.g. "179 MiB" or "28.4 GiB" on stdout
# Returns:
#   0
#######################################
hf_format_mib() {
  local kib="${1:-0}"
  if [[ ${kib} -lt 0 ]]; then
    kib=0
  fi
  if [[ ${kib} -ge 1048576 ]]; then
    awk -v k="${kib}" 'BEGIN { printf "%.1f GiB", k / 1048576 }'
  else
    awk -v k="${kib}" 'BEGIN { printf "%d MiB", int(k / 1024) }'
  fi
}

#######################################
# Format a transfer rate from KiB delta over seconds.
# Globals:
#   None
# Arguments:
#   $1  Delta KiB (integer; may be 0)
#   $2  Interval seconds (positive integer)
# Outputs:
#   e.g. "13.7 MiB/s" on stdout
# Returns:
#   0
#######################################
hf_format_rate() {
  local delta_kib="${1:-0}"
  local interval_s="${2:-10}"
  if [[ ${interval_s} -le 0 ]]; then
    interval_s=1
  fi
  if [[ ${delta_kib} -le 0 ]]; then
    echo "0 MiB/s"
    return 0
  fi
  awk -v d="${delta_kib}" -v s="${interval_s}" 'BEGIN {
    mibs = (d / 1024) / s
    if (mibs >= 100) printf "%.0f MiB/s", mibs
    else if (mibs >= 10) printf "%.1f MiB/s", mibs
    else printf "%.2f MiB/s", mibs
  }'
}

#######################################
# Format elapsed seconds as m:ss or h:mm:ss.
# Globals:
#   None
# Arguments:
#   $1  Elapsed seconds
# Outputs:
#   Time string on stdout
# Returns:
#   0
#######################################
hf_format_elapsed() {
  local secs="${1:-0}"
  local h m s
  if [[ ${secs} -lt 0 ]]; then
    secs=0
  fi
  h=$((secs / 3600))
  m=$(((secs % 3600) / 60))
  s=$((secs % 60))
  if [[ ${h} -gt 0 ]]; then
    printf '%d:%02d:%02d' "${h}" "${m}" "${s}"
  else
    printf '%d:%02d' "${m}" "${s}"
  fi
}

#######################################
# Build progress body (no [ez-comfy] prefix).
# Globals:
#   None
# Arguments:
#   $1  Label
#   $2  Size string
#   $3  Rate string
#   $4  Elapsed string
# Outputs:
#   Progress body on stdout
# Returns:
#   0
#######################################
hf_progress_line() {
  local label="${1:-download}"
  local size="${2:-0 MiB}"
  local rate="${3:-0 MiB/s}"
  local elapsed="${4:-0:00}"
  printf '↓ %s  %s  %s  elapsed %s' "${label}" "${size}" "${rate}" "${elapsed}"
}

#######################################
# Emit a progress line: rewrite on TTY stderr, log newline otherwise.
# Globals:
#   GREEN, NC, _HF_PROGRESS_ON_TTY (set to 1 after TTY emit)
# Arguments:
#   $1  Body line (without prefix)
# Outputs:
#   Progress to stderr
# Returns:
#   0
#######################################
hf_progress_emit() {
  local body="${1:-}"
  if [[ -t 2 ]]; then
    # Clear line + rewrite so we never smash with prior content
    printf '\r\033[K%s[ez-comfy]%s %s' "${GREEN}" "${NC}" "${body}" >&2
    _HF_PROGRESS_ON_TTY=1
  else
    log "${body}"
  fi
}

#######################################
# End a TTY progress rewrite so the next log starts on a new line.
# Globals:
#   _HF_PROGRESS_ON_TTY
# Arguments:
#   None
# Outputs:
#   Optional newline on stderr
# Returns:
#   0
#######################################
hf_progress_newline() {
  if [[ ${_HF_PROGRESS_ON_TTY:-0} == "1" ]]; then
    printf '\n' >&2
    _HF_PROGRESS_ON_TTY=0
  fi
}

#######################################
# Download a Hugging Face repo snapshot into --local-dir (or mock in tests).
# Prefers `hf download` over deprecated `huggingface-cli download` (the latter
# is a non-working stub on recent huggingface_hub installs and may prompt).
# On failure, prints plain-language guidance (not a full Python traceback)
# unless LAB_DEBUG=1 / HF_DOWNLOAD_DEBUG=1.
# Progress UI: disables hub/tqdm bars and shows disk growth (size, MiB/s,
# elapsed) on one rewriting TTY line or periodic non-TTY logs.
# Globals:
#   LAB_MOCK_HF_DOWNLOAD, HF_TOKEN (read by hub), HF_HOME (caller may set),
#   LAB_DEBUG, HF_DOWNLOAD_DEBUG, CI, HF_HUB_DISABLE_TELEMETRY,
#   HF_DOWNLOAD_MAX_WORKERS, HF_PROGRESS (0 disables progress lines),
#   HF_PROGRESS_INTERVAL (seconds, default 10), HF_LOCK_CLEAR_MID
# Arguments:
#   $@ - Passed to `hf download` / `huggingface-cli download`
#        (typically REPO --local-dir PATH)
# Outputs:
#   Progress via controlled UI; friendly errors on failure; mock writes .mock
# Returns:
#   0 on success; non-zero when the CLI fails
#######################################
hf_download() {
  local dest="" prev="" a repo="" hf_log rc=0
  repo="${1:-}"
  if [[ -n ${LAB_MOCK_HF_DOWNLOAD:-} ]]; then
    for a in "$@"; do
      if [[ ${prev} == "--local-dir" ]]; then
        dest="${a}"
      fi
      prev="${a}"
    done
    if [[ -z ${dest} ]]; then
      err "hf_download mock requires --local-dir"
      return 1
    fi
    if [[ ${LAB_MOCK_HF_DOWNLOAD} == "fail" ]]; then
      err "LAB_MOCK_HF_DOWNLOAD=fail"
      return 1
    fi
    if [[ ${LAB_MOCK_HF_DOWNLOAD} == "fail-gated" ]]; then
      explain_hf_download_error \
        "GatedRepoError: Cannot access gated repo. not in the authorized list. https://huggingface.co/${repo}/resolve/main/x" \
        "${repo}"
      return 1
    fi
    if [[ ${LAB_MOCK_HF_DOWNLOAD} == "fail-auth" ]]; then
      explain_hf_download_error "401 Client Error Unauthorized Invalid user token" "${repo}"
      return 1
    fi
    mkdir -p "${dest}"
    echo "mock" >"${dest}/.mock"
    # Honor --include paths so selective tier_files_ready works under mock
    local prev_m="" a_m rel_m has_inc=0
    for a_m in "$@"; do
      if [[ ${prev_m} == "--include" ]]; then
        has_inc=1
        rel_m="${a_m}"
        mkdir -p "${dest}/$(dirname "${rel_m}")"
        echo "mock" >"${dest}/${rel_m}"
      fi
      prev_m="${a_m}"
    done
    # Full-repo mock: drop a weight basename matching lab UNET when known
    if [[ ${has_inc} -eq 0 ]]; then
      case "${repo}" in
        *FLUX.2-klein-9b-nvfp4* | *FLUX.2-klein-9B-nvfp4*)
          echo "mock" >"${dest}/flux-2-klein-9b-nvfp4.safetensors"
          ;;
        *Nunchaku* | *nunchaku*)
          echo "mock" >"${dest}/flux-klein-nunchaku.safetensors"
          ;;
        *)
          echo "mock" >"${dest}/mock-weight.safetensors"
          ;;
      esac
    fi
    return 0
  fi

  # Durable cache root on MODELS_DIR when callers did not set HF_HOME
  if [[ -z ${HF_HOME:-} && -n ${MODELS_DIR:-} ]]; then
    export HF_HOME="${MODELS_DIR}"
  fi
  # Non-interactive hub; we own progress UI (disable tqdm smash with heartbeat)
  # Do not set force-download — hub resumes *.incomplete and skips up-to-date files.
  export CI="${CI:-1}"
  export HF_HUB_DISABLE_TELEMETRY="${HF_HUB_DISABLE_TELEMETRY:-1}"
  export PYTHONUNBUFFERED=1
  export TQDM_DISABLE="${TQDM_DISABLE:-1}"
  export HF_HUB_DISABLE_PROGRESS_BARS="${HF_HUB_DISABLE_PROGRESS_BARS:-1}"
  if [[ -n ${HF_TOKEN:-} ]]; then
    log "HF_TOKEN is set (using for gated repos)"
  fi

  hf_log="$(mktemp)"
  local -a hf_args=("$@")
  local dest_dir="" prev_a="" a
  local progress_label="" progress_interval start_ts final_kib final_elapsed
  local incomplete_n=0
  for a in "$@"; do
    if [[ ${prev_a} == "--local-dir" ]]; then
      dest_dir="${a}"
    fi
    prev_a="${a}"
  done
  progress_label="$(hf_progress_label "${dest_dir}")"
  progress_interval="${HF_PROGRESS_INTERVAL:-10}"
  if [[ ${progress_interval} -lt 1 ]]; then
    progress_interval=10
  fi
  # Gentle mode / operator override: limit parallel HF connections when set
  if [[ -n ${HF_DOWNLOAD_MAX_WORKERS:-} ]]; then
    if command -v hf >/dev/null 2>&1 && hf download --help 2>&1 | grep -q -- '--max-workers'; then
      hf_args+=(--max-workers "${HF_DOWNLOAD_MAX_WORKERS}")
      log "hf download  max-workers=${HF_DOWNLOAD_MAX_WORKERS}"
    fi
  fi
  if [[ -n ${dest_dir} ]]; then
    mkdir -p "${dest_dir}" 2>/dev/null || true
    incomplete_n="$(count_hf_incomplete "${dest_dir}")"
    log "downloading → ${dest_dir}  (resume-capable; re-run continues partials)"
    if [[ ${incomplete_n} -gt 0 ]]; then
      log "found ${incomplete_n} incomplete file(s) — resuming"
    fi
  fi

  local hb_pid="" hpid="" zero_streak=0
  _HF_PROGRESS_ON_TTY=0
  # Trap-only handler: SC2329/SC2317 — ShellCheck does not see string trap refs as calls
  # shellcheck disable=SC2317,SC2329
  _hf_dl_signal() {
    hf_progress_newline
    log "Interrupted — stopping hf download and progress monitor…"
    [[ -n ${hb_pid} ]] && kill_pid_tree "${hb_pid}" "progress monitor"
    [[ -n ${hpid} ]] && kill_pid_tree "${hpid}" "hf download"
    if [[ -n ${dest_dir} ]]; then
      log "partial download kept under ${dest_dir}; re-run the same command to resume"
    fi
    rm -f "${hf_log}"
    exit 130
  }
  trap '_hf_dl_signal' INT TERM

  # Heartbeat: disk growth is the truth for multi-GB files (not file-count tqdm)
  # set +m + disown: avoid bash "[1]+ Terminated" dumps on stop
  set +m 2>/dev/null || true
  start_ts="$(date +%s)"
  if [[ -n ${dest_dir} && ${HF_PROGRESS:-1} != "0" ]]; then
    mkdir -p "${dest_dir}" 2>/dev/null || true
    (
      local prev=0 cur delta elapsed body
      prev=$(du -sk "${dest_dir}" 2>/dev/null | awk '{print $1}') || prev=0
      zero_streak=0
      while true; do
        sleep "${progress_interval}"
        cur=$(du -sk "${dest_dir}" 2>/dev/null | awk '{print $1}') || cur=0
        delta=$((cur - prev))
        prev=${cur}
        elapsed=$(($(date +%s) - start_ts))
        body="$(hf_progress_line \
          "${progress_label}" \
          "$(hf_format_mib "${cur}")" \
          "$(hf_format_rate "${delta}" "${progress_interval}")" \
          "$(hf_format_elapsed "${elapsed}")")"
        hf_progress_emit "${body}"
        if [[ ${delta} -le 0 ]]; then
          zero_streak=$((zero_streak + 1))
          if [[ ${zero_streak} -ge 3 && ${HF_LOCK_CLEAR_MID:-1} == "1" ]]; then
            # locks_only: NEVER pkill — that was killing the active hf download
            hf_progress_newline
            warn "no disk growth for $((progress_interval * 3))s — clearing unheld HF locks (download still running)"
            clear_stale_hf_locks "${MODELS_DIR:-$(dirname "${dest_dir}")}" "locks_only" || true
            zero_streak=0
          fi
        else
          zero_streak=0
        fi
      done
    ) &
    hb_pid=$!
    disown "${hb_pid}" 2>/dev/null || true
    _RWSF_EXTRA_PIDS="${hb_pid}"
  fi

  set -m 2>/dev/null || true
  if command -v hf >/dev/null 2>&1; then
    set +e
    # Always capture CLI output for error explain; bars disabled above so no smash
    (
      set -o pipefail
      hf download "${hf_args[@]}" > >(tee -a "${hf_log}" >/dev/null) 2> >(tee -a "${hf_log}" >&2)
      exit "${PIPESTATUS[0]}"
    ) &
    hpid=$!
    # Protect active download from clear_stale_hf_locks process sweep
    _HF_PROTECTED_PIDS="${hpid} ${hb_pid}"
    export _HF_PROTECTED_PIDS
    wait "${hpid}"
    rc=$?
    set -e
  elif command -v huggingface-cli >/dev/null 2>&1; then
    warn "Using deprecated huggingface-cli; install modern hf: pipx install huggingface_hub"
    set +e
    (
      set -o pipefail
      huggingface-cli download "$@" 2>&1 | tee "${hf_log}"
      exit "${PIPESTATUS[0]}"
    ) &
    hpid=$!
    _HF_PROTECTED_PIDS="${hpid} ${hb_pid}"
    export _HF_PROTECTED_PIDS
    wait "${hpid}"
    rc=$?
    set -e
  else
    [[ -n ${hb_pid} ]] && kill_pid_tree "${hb_pid}" "progress monitor"
    hf_progress_newline
    trap - INT TERM
    unset _HF_PROTECTED_PIDS
    rm -f "${hf_log}"
    err "No hf or huggingface-cli on PATH"
    return 1
  fi
  set +m 2>/dev/null || true
  [[ -n ${hb_pid} ]] && kill_pid_tree "${hb_pid}" "progress monitor"
  _RWSF_EXTRA_PIDS=""
  unset _HF_PROTECTED_PIDS
  # Progress subshell may have left a \r line; always break TTY before final logs
  if [[ -t 2 ]]; then
    printf '\n' >&2
  fi
  _HF_PROGRESS_ON_TTY=0
  trap - INT TERM

  if [[ ${rc} -eq 0 ]]; then
    if [[ -n ${dest_dir} ]]; then
      final_kib=$(du -sk "${dest_dir}" 2>/dev/null | awk '{print $1}') || final_kib=0
      final_elapsed=$(($(date +%s) - start_ts))
      log "✓ ${progress_label}  $(hf_format_mib "${final_kib}")  in $(hf_format_elapsed "${final_elapsed}")"
    fi
    rm -f "${hf_log}"
    return 0
  fi
  if [[ ${rc} -eq 130 || ${rc} -gt 128 ]]; then
    rm -f "${hf_log}"
    return 130
  fi
  # Replace traceback noise with a short checklist
  explain_hf_download_error "${hf_log}" "${repo}"
  rm -f "${hf_log}"
  return 1
}
