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

# shellcheck disable=SC2034
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Used by signal helpers to track an optional background sample-phase PID.
_RWSF_CHILD_PID=""

#######################################
# Run a command in the foreground so progress bars (tqdm) keep a TTY.
# Ctrl+C/TERM aborts the command; returns 130 when interrupted.
# Globals:
#   None
# Arguments:
#   $@ - Command and arguments to run
# Outputs:
#   Command's stdout/stderr (live)
# Returns:
#   Command exit status; 130 if interrupted
#######################################
run_with_signal_forwarding() {
  local rc=0
  # shellcheck disable=SC2329
  _rwsf_fg_signal() {
    exit 130
  }
  trap '_rwsf_fg_signal' INT TERM
  set +e
  # Foreground: preserves TTY for hf/tqdm progress (background & wait hides it)
  "$@"
  rc=$?
  set -e
  trap - INT TERM
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

  if docker_cli_ok; then
    log "docker already available: $(docker --version 2>/dev/null | head -1)"
    return 0
  fi

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
  local user group
  user="$(id -un)"
  group="$(id -gn)"
  if [[ ! -d ${dir} ]]; then
    mkdir -p "${dir}" 2>/dev/null || true
  fi
  if [[ -d ${dir} && -w ${dir} ]]; then
    return 0
  fi
  err "MODELS_DIR=${dir} is not writable."
  err "  ./scripts/manage.sh setup"
  err "  # or: sudo mkdir -p '${dir}' && sudo chown ${user}:${group} '${dir}'"
  err "or set MODELS_DIR to a path you own in .env (e.g. ~/models)."
  return 1
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
  local dir="${1:-${MODELS_DIR:-/mnt/models}}"
  if ensure_models_dir "${dir}" 2>/dev/null; then
    return 0
  fi
  # ensure_models_dir already printed errors; clear intent for setup path
  if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
    err "MODELS_DIR=${dir} not writable and LAB_NO_SUDO=1 (cannot sudo)"
    return 1
  fi
  log "Creating MODELS_DIR with sudo: ${dir}"
  if ! sudo mkdir -p "${dir}"; then
    err "sudo mkdir -p '${dir}' failed"
    return 1
  fi
  if ! sudo chown "$(id -u):$(id -g)" "${dir}"; then
    err "sudo chown failed for '${dir}'"
    return 1
  fi
  ensure_models_dir "${dir}"
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
# Clear stale Hugging Face download locks under a models root.
# Stops orphan hf/huggingface download processes when safe; removes .lock files
# not held by a live process. FORCE deletes all locks after best-effort pkill.
# Globals:
#   HF_LOCK_CLEAR (0=skip), HF_LOCK_CLEAR_FORCE (1=force), MODELS_DIR
# Arguments:
#   $1 - Root directory (default MODELS_DIR or /mnt/models)
# Outputs:
#   Status via log/warn
# Returns:
#   0 always (best-effort; never aborts downloads solely for lock cleanup)
#######################################
clear_stale_hf_locks() {
  local root="${1:-${MODELS_DIR:-/mnt/models}}"
  local force="${HF_LOCK_CLEAR_FORCE:-0}"
  local lock removed=0 active=0 pid pids=""

  if [[ ${HF_LOCK_CLEAR:-1} == "0" ]]; then
    log "HF lock clear skipped (HF_LOCK_CLEAR=0)"
    return 0
  fi
  if [[ ! -d ${root} ]]; then
    return 0
  fi

  log "Checking for stale Hugging Face download locks under ${root} …"

  # Stop orphan downloaders that often leave locks after kill/restart experiments
  if command -v pgrep >/dev/null 2>&1; then
    while read -r pid; do
      [[ -z ${pid} || ! ${pid} =~ ^[0-9]+$ ]] && continue
      # Only target download-like command lines
      if [[ -r /proc/${pid}/cmdline ]] || kill -0 "${pid}" 2>/dev/null; then
        log "Stopping orphan download PID ${pid}"
        kill -TERM "${pid}" 2>/dev/null || true
        pids="${pids} ${pid}"
      fi
    done < <(pgrep -f 'hf download|huggingface-cli download|huggingface_hub' 2>/dev/null || true)
    if [[ -n ${pids// /} ]]; then
      sleep 2
      for pid in ${pids}; do
        if kill -0 "${pid}" 2>/dev/null; then
          warn "Force-killing download PID ${pid}"
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
      rm -f "${lock}" 2>/dev/null && removed=$((removed + 1)) || true
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
    # Without fuser/lsof, treat as stale after process sweep (common on minimal hosts)
    if [[ ${held} -eq 1 ]]; then
      active=$((active + 1))
      continue
    fi
    rm -f "${lock}" 2>/dev/null && removed=$((removed + 1)) || true
  done

  if [[ ${removed} -gt 0 ]]; then
    log "Removed ${removed} stale HF lock file(s) under ${root}"
  fi
  if [[ ${active} -gt 0 ]]; then
    warn "${active} lock(s) still held by live processes — wait for them or HF_LOCK_CLEAR_FORCE=1"
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
# Download a Hugging Face repo snapshot into --local-dir (or mock in tests).
# Prefers `hf download` over deprecated `huggingface-cli download` (the latter
# is a non-working stub on recent huggingface_hub installs and may prompt).
# On failure, prints plain-language guidance (not a full Python traceback)
# unless LAB_DEBUG=1 / HF_DOWNLOAD_DEBUG=1.
# Globals:
#   LAB_MOCK_HF_DOWNLOAD, HF_TOKEN (read by hub), HF_HOME (caller may set),
#   LAB_DEBUG, HF_DOWNLOAD_DEBUG, CI, HF_HUB_DISABLE_TELEMETRY
# Arguments:
#   $@ - Passed to `hf download` / `huggingface-cli download`
#        (typically REPO --local-dir PATH)
# Outputs:
#   Progress via tee; friendly errors on failure; mock writes .mock under local-dir
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
    return 0
  fi

  # Non-interactive hub updates, but keep progress bars when on a TTY
  export CI="${CI:-1}"
  export HF_HUB_DISABLE_TELEMETRY="${HF_HUB_DISABLE_TELEMETRY:-1}"
  export PYTHONUNBUFFERED=1
  export TQDM_MININTERVAL="${TQDM_MININTERVAL:-0.1}"
  if [[ -n ${HF_TOKEN:-} ]]; then
    log "HF_TOKEN is set (using for gated repos)"
  fi

  hf_log="$(mktemp)"
  local -a hf_args=("$@")
  local dest_dir="" prev_a="" a
  for a in "$@"; do
    if [[ ${prev_a} == "--local-dir" ]]; then
      dest_dir="${a}"
    fi
    prev_a="${a}"
  done
  # Gentle mode / operator override: limit parallel HF connections when set
  if [[ -n ${HF_DOWNLOAD_MAX_WORKERS:-} ]]; then
    if command -v hf >/dev/null 2>&1 && hf download --help 2>&1 | grep -q -- '--max-workers'; then
      hf_args+=(--max-workers "${HF_DOWNLOAD_MAX_WORKERS}")
      log "hf download using --max-workers=${HF_DOWNLOAD_MAX_WORKERS}"
    fi
  fi

  # shellcheck disable=SC2329
  _hf_dl_signal() {
    if [[ -n ${hb_pid:-} ]]; then
      kill "${hb_pid}" 2>/dev/null || true
    fi
    rm -f "${hf_log}"
    exit 130
  }
  trap '_hf_dl_signal' INT TERM

  # Heartbeat: prove progress even if hub UI is quiet (large single files)
  local hb_pid=""
  if [[ -n ${dest_dir} ]]; then
    mkdir -p "${dest_dir}" 2>/dev/null || true
    (
      local prev=0 cur delta
      prev=$(du -sk "${dest_dir}" 2>/dev/null | awk '{print $1}') || prev=0
      while true; do
        sleep 10
        cur=$(du -sk "${dest_dir}" 2>/dev/null | awk '{print $1}') || cur=0
        delta=$((cur - prev))
        prev=${cur}
        # KiB → MiB rough
        log "download progress: ${dest_dir} ≈ $((cur / 1024)) MiB (+$((delta / 1024)) MiB / 10s)"
      done
    ) &
    hb_pid=$!
  fi

  if command -v hf >/dev/null 2>&1; then
    set +e
    if [[ -t 2 ]]; then
      # Keep real TTY on stderr so tqdm shows live bars; still capture for errors
      # shellcheck disable=SC2094
      hf download "${hf_args[@]}" > >(tee -a "${hf_log}" >/dev/null) 2> >(tee -a "${hf_log}" >&2)
      rc=$?
    else
      set -o pipefail
      hf download "${hf_args[@]}" 2>&1 | tee "${hf_log}"
      rc=${PIPESTATUS[0]}
      set +o pipefail
    fi
    set -e
  elif command -v huggingface-cli >/dev/null 2>&1; then
    warn "Using deprecated huggingface-cli; install modern hf: pipx install huggingface_hub"
    set +e
    if [[ -t 2 ]]; then
      huggingface-cli download "$@" > >(tee -a "${hf_log}" >/dev/null) 2> >(tee -a "${hf_log}" >&2)
      rc=$?
    else
      set -o pipefail
      huggingface-cli download "$@" 2>&1 | tee "${hf_log}"
      rc=${PIPESTATUS[0]}
      set +o pipefail
    fi
    set -e
  else
    if [[ -n ${hb_pid} ]]; then
      kill "${hb_pid}" 2>/dev/null || true
      wait "${hb_pid}" 2>/dev/null || true
    fi
    trap - INT TERM
    rm -f "${hf_log}"
    err "No hf or huggingface-cli on PATH"
    return 1
  fi
  if [[ -n ${hb_pid} ]]; then
    kill "${hb_pid}" 2>/dev/null || true
    wait "${hb_pid}" 2>/dev/null || true
  fi
  trap - INT TERM

  if [[ ${rc} -eq 0 ]]; then
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
