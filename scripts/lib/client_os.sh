#!/usr/bin/env bash
# Operator-laptop helpers: OS detect, SSH config, key, package hints.
# Sourced by utilities/setup-client.sh. Not executable.
# @function detect_client_os

#######################################
# Classify this machine for client bootstrap.
# Globals:
#   EZ_CLIENT_OS (optional override)
# Arguments:
#   None
# Outputs:
#   One of darwin, linux, wsl, windows, unknown on stdout
# Returns:
#   0
#######################################
detect_client_os() {
  if [[ -n ${EZ_CLIENT_OS:-} ]]; then
    echo "${EZ_CLIENT_OS}"
    return 0
  fi
  local uname_s
  uname_s="$(uname -s 2>/dev/null || echo unknown)"
  case "${uname_s}" in
    Darwin) echo darwin ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        echo wsl
      else
        echo linux
      fi
      ;;
    MINGW* | MSYS* | CYGWIN*) echo windows ;;
    *) echo unknown ;;
  esac
}

#######################################
# True when this host should run Spark setup instead of laptop client setup.
# Globals:
#   EZ_ONBOARD_ROLE (spark|laptop override)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when this looks like the Spark
#######################################
client_is_spark_host() {
  if [[ ${EZ_ONBOARD_ROLE:-} == "spark" ]]; then
    return 0
  fi
  if [[ ${EZ_ONBOARD_ROLE:-} == "laptop" ]]; then
    return 1
  fi
  if [[ -f /etc/nv_tegra_release ]]; then
    return 0
  fi
  if command -v nvidia-smi >/dev/null 2>&1 && [[ -d /mnt/models || -d /mnt/comfy-output ]]; then
    return 0
  fi
  return 1
}

#######################################
# Path of the SSH config file we may edit.
# Globals:
#   EZ_SSH_CONFIG, HOME
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
ssh_config_path() {
  echo "${EZ_SSH_CONFIG:-${HOME}/.ssh/config}"
}

#######################################
# Write or replace the ez-spark Host block in the SSH config.
# Globals:
#   HOME
# Arguments:
#   $1 - Spark hostname or IP
#   $2 - SSH user
#   $3 - ComfyUI port (LocalForward)
# Outputs:
#   Status via log
# Returns:
#   0 on success, 1 if path is not writable
#######################################
write_ez_spark_ssh_config() {
  local host="${1:?host}"
  local user="${2:?user}"
  local port="${3:?port}"
  local cfg dir tmp
  cfg="$(ssh_config_path)"
  dir="$(dirname "${cfg}")"
  mkdir -p "${dir}"
  chmod 700 "${dir}" 2>/dev/null || true
  tmp="${cfg}.ez-comfy.$$"
  if [[ -f ${cfg} ]]; then
    awk '
      BEGIN { skip=0 }
      /^# BEGIN ez-comfy-stack ez-spark$/ { skip=1; next }
      /^# END ez-comfy-stack ez-spark$/ { skip=0; next }
      skip==0 { print }
    ' "${cfg}" >"${tmp}"
  else
    : >"${tmp}"
  fi
  {
    echo ""
    echo "# BEGIN ez-comfy-stack ez-spark"
    echo "Host ez-spark"
    echo "  HostName ${host}"
    echo "  User ${user}"
    echo "  LocalForward ${port} 127.0.0.1:${port}"
    echo "  ControlMaster auto"
    echo "  ControlPath ~/.ssh/cm-%r@%h:%p"
    echo "  ControlPersist 10m"
    echo "# END ez-comfy-stack ez-spark"
  } >>"${tmp}"
  mv "${tmp}" "${cfg}"
  chmod 600 "${cfg}" 2>/dev/null || true
  log "SSH config Host ez-spark -> ${user}@${host} LocalForward ${port} (${cfg})"
}

#######################################
# Ensure an ed25519 key exists under the SSH home.
# Globals:
#   HOME, EZ_SSH_KEY, LAB_MOCK_SSH
# Arguments:
#   None
# Outputs:
#   Status via log
# Returns:
#   0 when a key exists or was created
#######################################
ensure_ssh_key() {
  local key="${EZ_SSH_KEY:-${HOME}/.ssh/id_ed25519}"
  if [[ -f ${key} ]]; then
    log "SSH key present: ${key}"
    return 0
  fi
  mkdir -p "$(dirname "${key}")"
  if [[ ${LAB_MOCK_SSH:-} == "1" ]]; then
    printf 'mock-key\n' >"${key}"
    printf 'mock-key.pub\n' >"${key}.pub"
    log "LAB_MOCK_SSH: wrote ${key}"
    return 0
  fi
  if ! command -v ssh-keygen >/dev/null 2>&1; then
    err "ssh-keygen missing - install OpenSSH, then re-run setup-client"
    return 1
  fi
  ssh-keygen -t ed25519 -N "" -f "${key}" >/dev/null
  log "Created SSH key ${key}"
}

#######################################
# List missing client tools (space-separated) on stdout.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Tool names that are not on PATH
# Returns:
#   0
#######################################
client_missing_tools() {
  local tool
  local -a missing=()
  for tool in git ssh python3; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      missing+=("${tool}")
    fi
  done
  if ((${#missing[@]})); then
    printf '%s\n' "${missing[*]}"
  fi
}

#######################################
# Install missing client packages, or log the mock path.
# Globals:
#   LAB_MOCK_CLIENT_INSTALL, LAB_NO_SUDO
# Arguments:
#   $1 - OS id from detect_client_os
# Outputs:
#   Status via log/warn/err
# Returns:
#   0 when tools are present or mock-installed; 1 on hard fail
#######################################
install_client_packages() {
  local os="${1:?os}"
  local missing
  missing="$(client_missing_tools || true)"
  if [[ -z ${missing} ]]; then
    log "client tools: git ssh python3 present"
    return 0
  fi
  log "missing client tools: ${missing}"
  if [[ ${LAB_MOCK_CLIENT_INSTALL:-} == "1" ]]; then
    log "LAB_MOCK_CLIENT_INSTALL: skipping real package install (${os})"
    return 0
  fi
  local -a pkgs=()
  read -r -a pkgs <<<"${missing}"
  case "${os}" in
    darwin)
      if command -v brew >/dev/null 2>&1; then
        brew install "${pkgs[@]}" || return 1
      else
        err "Homebrew missing. Install from https://brew.sh then re-run setup-client"
        return 1
      fi
      ;;
    linux | wsl)
      if [[ ${LAB_NO_SUDO:-} == "1" ]]; then
        err "Cannot install packages (LAB_NO_SUDO=1). Install: ${missing}"
        return 1
      fi
      if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}" openssh-client
      elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y "${pkgs[@]}" openssh-clients
      else
        err "No apt-get/dnf. Install: ${missing}"
        return 1
      fi
      ;;
    windows)
      err "Use scripts/utilities/setup-client.ps1 (WSL2) or Git for Windows + OpenSSH"
      return 1
      ;;
    *)
      err "Unknown OS ${os}. Install git, OpenSSH, and python3, then re-run"
      return 1
      ;;
  esac
}
