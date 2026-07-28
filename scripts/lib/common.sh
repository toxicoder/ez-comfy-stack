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
