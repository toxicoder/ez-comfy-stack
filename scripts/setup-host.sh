#!/usr/bin/env bash
#
# ## setup-host - one-time host bootstrap: Bazelisk + the lint toolchain.
#
# The only script in this repo meant to run straight from a shell, and the one
# that has to: Bazel is the ingress for every other entry point, and a host
# with no bazelisk cannot run a single target.
#
# The lint gate is the reason it exists. scripts/lib/check_tool.sh prints
# "<tool> missing - skipping (resilient; ...)" and exits 0 when a linter is
# off PATH, so on a host that never installed shellcheck, shfmt, buildifier,
# pyright or mypy, `bazelisk test //:lint` goes GREEN having checked nothing.
# One command that installs those binaries is what makes that gate mean
# something; after it runs, a skipped linter is a real defect.
#
# What it probes for is the set of binaries the Bazel targets shell out to:
#
# - bazelisk: every entry point (bazelisk test|run ...); without it nothing runs
# - shellcheck: //lints:shell, and //:fix
# - shfmt: //lints:shfmt, and //:fix
# - buildifier: //lints:buildifier, and //:fix
# - pyright + mypy: //lints:pyright, //lints:mypy, and //tests:typecheck
# - node: //tests:js (tests/run_js.sh needs Node 22+) and the docs-site targets
# - git + python3: the checkout itself, and the interpreter the pip tools live in
#
# Every version comes from .devcontainer/tool-versions.env, the repo's declared
# single source of truth, sourced the way .github/actions/setup-bazel/action.yml
# sources it (set -a / source / set +a). Nothing in this script names a
# version: a bump there moves the devcontainer, CI and this bootstrap together.
# A required pin that is absent is a hard error, and the Node tarball is
# checked against its sha256 pin before anything is installed, so a swapped or
# truncated download cannot land on the host.
#
# Linux takes shellcheck, git and python3 from apt (the tools that have a
# package) and fetches the pinned upstream release for bazelisk, shfmt and
# buildifier; macOS takes all of them from Homebrew. Both paths install into
# the first writable candidate of /usr/local/bin, ${HOME}/bin, and print which
# one was chosen. The Python lane is always pip from tests/requirements.txt,
# which is what //tests:typecheck and //tests:pytest read.
#
# Usage (both forms work from any directory):
#   bash scripts/setup-host.sh            # install what is missing, then re-probe
#   bash scripts/setup-host.sh --check    # report only; exit 1 when something is missing
#   bash scripts/setup-host.sh --dry-run  # print the plan; touch nothing
#
# Options:
#   --check     probe and report only; writes nothing and exits 1 listing every
#               missing tool with the source it would come from
#   --dry-run   print what would be installed and from where; touch nothing
#   -h, --help  print this help and exit 0
#
# Environment (also the hooks tests/bats/setup_host.bats drives this script with):
#   SETUP_HOST_ROOT            checkout root (default: this script's parent)
#   SETUP_HOST_VERSIONS_FILE   pin file (default: <root>/.devcontainer/tool-versions.env)
#   SETUP_HOST_BIN_DIR         where binaries land (default: first writable of
#                              /usr/local/bin, ${HOME}/bin)
#   SETUP_HOST_NODE_PREFIX     prefix the pinned Node tarball is extracted into
#                              (default: ${HOME}/.local)
#   LAB_NO_SUDO=1              never call sudo (hermetic tests / restricted hosts)
#
# Exit codes: 0 when every tool is present (--check, --dry-run, or a completed
# install); 1 when a pin is missing, the pin file cannot be read, an install was
# asked for and something stayed missing after the re-probe, or --check found a
# tool missing.
#
# Safety: installs pinned release binaries, apt packages and pip packages only.
# It starts no stack, pulls no model weights, touches no model directory and
# runs no GPU job. sudo is used only for apt, and only when it is available.
#
# @command setup-host
# @description Install the host binaries the Bazel targets shell out to: bazelisk, shellcheck, shfmt, buildifier, pyright, mypy, node, git, python3.
# Usage: bash scripts/setup-host.sh [--check | --dry-run]
# Safety: Installs pinned releases and pip packages; starts nothing, downloads
#   no models, and runs no GPU job.

set -euo pipefail

# Builtins only: this script must still probe a host whose PATH is broken.
SELF_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
# shellcheck source=lib/common.sh disable=SC1091
source "${SELF_DIR}/lib/common.sh"

# The checkout this script lives in; overridable so the Bats suite can point
# the pin file and the install dir at a scratch tree.
SETUP_HOST_ROOT="${SETUP_HOST_ROOT:-$(cd "${SELF_DIR}/.." && pwd)}"
SETUP_HOST_VERSIONS_FILE="${SETUP_HOST_VERSIONS_FILE:-${SETUP_HOST_ROOT}/.devcontainer/tool-versions.env}"
SETUP_HOST_BIN_DIR="${SETUP_HOST_BIN_DIR:-}"
SETUP_HOST_NODE_PREFIX="${SETUP_HOST_NODE_PREFIX:-${HOME}/.local}"

# The Python lane is pip from this file, the same one //tests:pytest consumes.
SETUP_HOST_REQUIREMENTS="tests/requirements.txt"

# Binaries the Bazel targets shell out to. The re-probe after an install is
# over this list, so a tool that silently failed to install still fails here.
REQUIRED_TOOLS=(bazelisk shellcheck shfmt buildifier pyright mypy node git python3)

# Pins this script refuses to run without.
REQUIRED_PINS=(
  BAZELISK_VERSION
  BUILDIFIER_VERSION
  SHFMT_ASSET_VERSION
  NODE_VERSION
  NODE_SHA256_X64
  NODE_SHA256_ARM64
)

# Tools apt owns on Linux; the rest of the Linux set is a pinned release fetch.
APT_TOOLS=(shellcheck git python3)

# Tools fetched as raw release binaries (node is a tarball, handled apart).
RELEASE_TOOLS=(bazelisk shfmt buildifier)

# Filled by setup_host_arch; amd64 or arm64.
SETUP_HOST_ARCH=""
# "sudo" when apt needs a prefix, empty when it does not.
SETUP_HOST_SUDO=""
# Resolved by setup_host_pick_bin_dir.
BIN_DIR=""
PRESENT_TOOLS=()
MISSING_TOOLS=()

#######################################
# Print setup-host usage and the tool set.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help text on stdout
# Returns:
#   0
#######################################
setup_host_usage() {
  cat <<'HELP'
Usage: bash scripts/setup-host.sh [--check|--dry-run]

Install the host binaries the Bazel targets shell out to, so a lint gate that
skips a missing linter cannot pass on a host that never installed it:

  bazelisk    every entry point (bazelisk test|run ...); without it nothing runs
  shellcheck  //lints:shell, and //:fix
  shfmt       //lints:shfmt, and //:fix
  buildifier  //lints:buildifier, and //:fix
  pyright     //lints:pyright, and //tests:typecheck
  mypy        //lints:mypy, and //tests:typecheck
  node        //tests:js (Node 22+) and the docs-site targets
  git         the checkout, and the fetches the docs pins rely on
  python3     the interpreter the pip tools (pyright, mypy) install into

Versions come from .devcontainer/tool-versions.env; this script names none of
them. Linux uses apt for shellcheck, git and python3 and fetches the pinned
upstream release for bazelisk, shfmt, buildifier and node; macOS uses
Homebrew. pyright and mypy always come from tests/requirements.txt through pip.

  --check     probe only; write nothing; exit 1 listing every missing tool
  --dry-run   print what would be installed and from where; touch nothing
  -h, --help  this help

  bash scripts/setup-host.sh            # install what is missing, then re-probe
  bash scripts/setup-host.sh --check    # what is missing right now
  bash scripts/setup-host.sh --dry-run  # the plan, with no writes
HELP
}

#######################################
# Source the version pins and require the ones this script needs.
# Globals:
#   BAZELISK_VERSION, BUILDIFIER_VERSION, SHFMT_ASSET_VERSION, NODE_VERSION,
#   NODE_SHA256_X64, NODE_SHA256_ARM64 (exported by set -a)
# Arguments:
#   $1 - path to the pin file
# Outputs:
#   Error on stderr naming the missing file or key
# Returns:
#   0 when every REQUIRED_PINS key is non-empty; 1 otherwise
#######################################
setup_host_load_pins() {
  local file="${1:-}"
  if [[ ! -f ${file} ]]; then
    err "setup-host: pin file not found: ${file}"
    err "  .devcontainer/tool-versions.env is the single source of truth for these"
    err "  versions; restore it and re-run this script."
    return 1
  fi
  set -a
  # shellcheck source=../.devcontainer/tool-versions.env disable=SC1091
  source "${file}"
  set +a
  local key
  for key in "${REQUIRED_PINS[@]}"; do
    if [[ -z ${!key:-} ]]; then
      err "setup-host: ${key} is not set in ${file}"
      err "  this script installs only pinned releases, so it refuses to guess a"
      err "  version. Add ${key} to the pin file and re-run."
      return 1
    fi
  done
  return 0
}

#######################################
# Map the host machine to the Go-style release asset arch.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   amd64 or arm64 on stdout
# Returns:
#   0 when the arch is supported; 1 when uname is unavailable or unsupported
#######################################
setup_host_arch() {
  local machine
  machine="$(uname -m 2>/dev/null || true)"
  case "${machine}" in
    x86_64 | amd64) printf 'amd64\n' ;;
    aarch64 | arm64) printf 'arm64\n' ;;
    *)
      err "setup-host: unsupported arch '${machine}' (need x86_64 or aarch64)"
      return 1
      ;;
  esac
}

#######################################
# Report whether the node on PATH is new enough for the JS and docs lanes.
# The floor is the major the repo pins, so the script names no version itself.
# Globals:
#   NODE_VERSION
# Arguments:
#   None
# Outputs:
#   Nothing
# Returns:
#   0 when node is on PATH and its major is at least the pinned major; 1 otherwise
#######################################
setup_host_node_is_new_enough() {
  local out major want
  command -v node >/dev/null 2>&1 || return 1
  out="$(node --version 2>/dev/null || true)"
  [[ ${out} =~ ^v?([0-9]+) ]] || return 1
  major="${BASH_REMATCH[1]}"
  want="${NODE_VERSION%%.*}"
  [[ ${major} =~ ^[0-9]+$ ]] || return 1
  [[ ${major} -ge ${want} ]]
}

#######################################
# Probe every required tool once, filling the present and missing lists.
# Globals:
#   REQUIRED_TOOLS, PRESENT_TOOLS (written), MISSING_TOOLS (written)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
setup_host_probe() {
  local tool
  PRESENT_TOOLS=()
  MISSING_TOOLS=()
  for tool in "${REQUIRED_TOOLS[@]}"; do
    if [[ ${tool} == node ]]; then
      if setup_host_node_is_new_enough; then
        PRESENT_TOOLS+=("${tool}")
      else
        MISSING_TOOLS+=("${tool}")
      fi
      continue
    fi
    if command -v "${tool}" >/dev/null 2>&1; then
      PRESENT_TOOLS+=("${tool}")
    else
      MISSING_TOOLS+=("${tool}")
    fi
  done
  return 0
}

#######################################
# Print the probe result: present, missing, and where each missing tool comes from.
# Globals:
#   PRESENT_TOOLS, MISSING_TOOLS, SETUP_HOST_ROOT
# Arguments:
#   None
# Outputs:
#   Report on stdout, one "missing: <tool> - <source>" line per absent tool
# Returns:
#   0
#######################################
setup_host_report() {
  local tool
  printf 'setup-host: host tool report (checkout %s)\n' "${SETUP_HOST_ROOT}"
  if [[ ${#PRESENT_TOOLS[@]} -gt 0 ]]; then
    printf '  present: %s\n' "${PRESENT_TOOLS[*]}"
  fi
  if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
    printf '  tools missing (%d): %s\n' "${#MISSING_TOOLS[@]}" "${MISSING_TOOLS[*]}"
    for tool in "${MISSING_TOOLS[@]}"; do
      printf '  missing: %s - %s\n' "${tool}" "$(setup_host_hint "${tool}")"
    done
  fi
  return 0
}

#######################################
# Print where one tool comes from (a release URL, an apt line, or a brew line).
# Globals:
#   SETUP_HOST_ARCH
# Arguments:
#   $1 - tool name from REQUIRED_TOOLS
# Outputs:
#   One install source on stdout
# Returns:
#   0
#######################################
setup_host_hint() {
  local tool="${1:-}" url="" pip_cmd="python3 -m pip install" brew=0
  if [[ "$(uname -s 2>/dev/null || true)" == Darwin ]]; then
    brew=1
  fi
  [[ -n ${VIRTUAL_ENV:-} ]] || pip_cmd="${pip_cmd} --user"
  pip_cmd="${pip_cmd} -r ${SETUP_HOST_REQUIREMENTS}"
  case "${tool}" in
    pyright | mypy)
      printf '%s\n' "${pip_cmd}"
      ;;
    shellcheck | git | python3)
      if [[ ${brew} == 1 ]]; then
        printf '%s\n' "brew install ${tool}"
      else
        printf '%s\n' "apt-get install -y ${tool}"
      fi
      ;;
    *)
      if [[ ${brew} == 1 ]]; then
        printf '%s\n' "brew install ${tool}"
      elif url="$(setup_host_url "${tool}")"; then
        printf '%s\n' "${url}"
      else
        printf '%s\n' "no pinned release for this arch; install ${tool} by hand"
      fi
      ;;
  esac
  return 0
}

#######################################
# Build the pinned release URL for one tool.
# Globals:
#   SETUP_HOST_ARCH, BAZELISK_VERSION, BUILDIFIER_VERSION, SHFMT_ASSET_VERSION,
#   NODE_VERSION
# Arguments:
#   $1 - tool: bazelisk, shfmt, buildifier, or node
# Outputs:
#   One HTTPS URL on stdout; node's ends in .tar.xz and is checksum-verified
# Returns:
#   0 when the tool and arch resolve; 1 for an unknown tool or arch
#######################################
setup_host_url() {
  local tool="${1:-}" arch="${SETUP_HOST_ARCH}" narch=x64
  [[ -n ${arch} ]] || return 1
  case "${arch}" in
    amd64) narch=x64 ;;
    arm64) narch=arm64 ;;
    *) return 1 ;;
  esac
  case "${tool}" in
    bazelisk)
      printf '%s\n' "https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-${arch}"
      ;;
    shfmt)
      printf '%s\n' "https://github.com/mvdan/sh/releases/download/v${SHFMT_ASSET_VERSION}/shfmt_v${SHFMT_ASSET_VERSION}_linux_${arch}"
      ;;
    buildifier)
      printf '%s\n' "https://github.com/bazelbuild/buildtools/releases/download/${BUILDIFIER_VERSION}/buildifier-linux-${arch}"
      ;;
    node)
      printf '%s\n' "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${narch}.tar.xz"
      ;;
    *)
      return 1
      ;;
  esac
  return 0
}

#######################################
# Echo the sha256 pin for the Node tarball of this arch.
# Globals:
#   SETUP_HOST_ARCH, NODE_SHA256_X64, NODE_SHA256_ARM64
# Arguments:
#   None
# Outputs:
#   64 hex characters on stdout
# Returns:
#   0 when a pin exists for this arch; 1 otherwise
#######################################
setup_host_sha256() {
  local var=""
  case "${SETUP_HOST_ARCH}" in
    amd64) var=NODE_SHA256_X64 ;;
    arm64) var=NODE_SHA256_ARM64 ;;
    *) return 1 ;;
  esac
  printf '%s\n' "${!var}"
  return 0
}

#######################################
# Compare a download against its sha256 pin.
# Globals:
#   None
# Arguments:
#   $1 - path to the downloaded file
#   $2 - expected sha256
# Outputs:
#   Mismatch diagnostic on stderr
# Returns:
#   0 when they match; 1 on a mismatch or when no checksum tool exists
#######################################
setup_host_verify_sha256() {
  local file="${1:-}" expected="${2:-}" actual=""
  [[ -s ${file} ]] || return 1
  # Builtins after the digest: the hash is the first whitespace-delimited field.
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "${file}" 2>/dev/null || true)"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "${file}" 2>/dev/null || true)"
  else
    err "setup-host: no sha256sum or shasum on PATH; cannot verify ${file##*/}"
    return 1
  fi
  actual="${actual%% *}"
  if [[ -z ${actual} || ${actual} != "${expected}" ]]; then
    err "setup-host: sha256 mismatch for ${file##*/}"
    err "  expected ${expected}, got ${actual:-nothing}"
    return 1
  fi
  return 0
}

#######################################
# Fetch one URL to a path with curl.
# Globals:
#   None
# Arguments:
#   $1 - HTTPS URL
#   $2 - destination path
# Outputs:
#   The download at $2; failure note on stderr
# Returns:
#   0 when a non-empty file was fetched; 1 otherwise
#######################################
setup_host_fetch() {
  local url="${1:-}" dest="${2:-}"
  [[ -n ${url} && -n ${dest} ]] || return 1
  if ! curl -fsSL "${url}" -o "${dest}"; then
    err "setup-host: nothing was fetched from ${url} (no network, or no curl)"
    rm -f "${dest}" 2>/dev/null || true
    return 1
  fi
  [[ -s ${dest} ]]
}

#######################################
# Put one fetched binary in the install dir.
# Globals:
#   BIN_DIR, SETUP_HOST_SUDO
# Arguments:
#   $1 - path to the downloaded binary
#   $2 - name to install it as
# Outputs:
#   ${BIN_DIR}/$2; failure note on stderr
# Returns:
#   0 when the file is in place; 1 when the install dir refused it
#######################################
setup_host_install_binary() {
  local src="${1:-}" name="${2:-}"
  [[ -s ${src} ]] || return 1
  chmod 755 "${src}" || return 1
  if ! setup_host_run_root install -m 0755 "${src}" "${BIN_DIR}/${name}"; then
    err "setup-host: ${name} was fetched, but ${BIN_DIR} refused the install"
    return 1
  fi
  return 0
}

#######################################
# Install the pinned Node tarball and link node, npm and npx into the install dir.
# The checksum pin is the gate: an unverified tarball is never extracted.
# Globals:
#   SETUP_HOST_NODE_PREFIX, BIN_DIR, SETUP_HOST_ARCH
# Arguments:
#   $1 - scratch dir to download into
# Outputs:
#   Node distro under ${SETUP_HOST_NODE_PREFIX} and links in ${BIN_DIR}; notes on stderr
# Returns:
#   0 when node is linked; 1 on a failed fetch, checksum, or extract
#######################################
setup_host_install_node() {
  local tmp="${1:-}" url="" expected="" bin_name=""
  [[ -n ${tmp} ]] || return 1
  if ! url="$(setup_host_url node)"; then
    err "setup-host: node: no pinned release for this arch"
    return 1
  fi
  if ! expected="$(setup_host_sha256)"; then
    err "setup-host: node: no sha256 pin for this arch"
    return 1
  fi
  if ! setup_host_fetch "${url}" "${tmp}/node.tar.xz"; then
    return 1
  fi
  if ! setup_host_verify_sha256 "${tmp}/node.tar.xz" "${expected}"; then
    err "setup-host: node: refusing to install a tarball that fails its sha256 pin"
    return 1
  fi
  mkdir -p "${SETUP_HOST_NODE_PREFIX}" || return 1
  if ! tar -xf "${tmp}/node.tar.xz" -C "${SETUP_HOST_NODE_PREFIX}" --strip-components=1; then
    err "setup-host: node: the verified tarball could not be extracted into ${SETUP_HOST_NODE_PREFIX}"
    return 1
  fi
  for bin_name in node npm npx; do
    [[ -e ${SETUP_HOST_NODE_PREFIX}/bin/${bin_name} ]] || continue
    if ! setup_host_run_root ln -sfn "${SETUP_HOST_NODE_PREFIX}/bin/${bin_name}" "${BIN_DIR}/${bin_name}"; then
      err "setup-host: node: ${BIN_DIR} refused the ${bin_name} link"
      return 1
    fi
  done
  log "node installed from ${url}"
  return 0
}

#######################################
# Install the Python lint lane from tests/requirements.txt (pyright + mypy).
# Globals:
#   SETUP_HOST_ROOT, SETUP_HOST_REQUIREMENTS, VIRTUAL_ENV
# Arguments:
#   None
# Outputs:
#   pip output on stdout/stderr; notes on stderr
# Returns:
#   0 when pip ran; 1 when the requirements file is missing or pip failed
#######################################
setup_host_install_python_tools() {
  local req="${SETUP_HOST_ROOT}/${SETUP_HOST_REQUIREMENTS}"
  local -a cmd=(python3 -m pip install)
  if [[ ! -f ${req} ]]; then
    err "setup-host: ${req} not found; pyright and mypy install from it"
    return 1
  fi
  [[ -n ${VIRTUAL_ENV:-} ]] || cmd+=(--user)
  cmd+=(-r "${req}")
  log "installing the Python lint lane from ${SETUP_HOST_REQUIREMENTS} ..."
  if ! env PIP_BREAK_SYSTEM_PACKAGES=1 "${cmd[@]}"; then
    err "setup-host: pip failed; pyright and mypy stay missing"
    return 1
  fi
  return 0
}

#######################################
# Choose the install dir: the override, /usr/local/bin when writable, else ~/bin.
# Globals:
#   SETUP_HOST_BIN_DIR, HOME, BIN_DIR (written)
# Arguments:
#   $1 - "1" to create the directory, "0" to only resolve it (check / dry-run)
# Outputs:
#   The chosen directory and whether PATH sees it, on stderr
# Returns:
#   0 when the directory is usable; 1 when it cannot be created
#######################################
setup_host_pick_bin_dir() {
  local create="${1:-0}"
  if [[ -n ${SETUP_HOST_BIN_DIR} ]]; then
    BIN_DIR="${SETUP_HOST_BIN_DIR}"
  elif [[ -w /usr/local/bin ]]; then
    BIN_DIR="/usr/local/bin"
  else
    BIN_DIR="${HOME}/bin"
  fi
  if [[ ${create} == 1 ]] && ! setup_host_run_root mkdir -p "${BIN_DIR}"; then
    err "setup-host: cannot create the install dir ${BIN_DIR}"
    return 1
  fi
  log "install dir: ${BIN_DIR}"
  if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
    warn "${BIN_DIR} is not on PATH; add it before the next 'bazelisk test //:lint'"
  fi
  return 0
}

#######################################
# Run a command as root when a prefix is available, else as the current user.
# Globals:
#   SETUP_HOST_SUDO
# Arguments:
#   $@ - command and its arguments
# Outputs:
#   Whatever the command prints
# Returns:
#   The command's status
#######################################
setup_host_run_root() {
  if [[ ${EUID} -eq 0 || -z ${SETUP_HOST_SUDO} ]]; then
    "$@"
  else
    "${SETUP_HOST_SUDO}" "$@"
  fi
}

#######################################
# Print the install plan for the missing tools without writing anything.
# Globals:
#   MISSING_TOOLS, BIN_DIR, SETUP_HOST_NODE_PREFIX
# Arguments:
#   None
# Outputs:
#   One "would install <tool> <- <source>" line per missing tool, on stdout
# Returns:
#   0
#######################################
setup_host_install_plan() {
  local tool
  printf 'setup-host: install plan (--dry-run writes nothing)\n'
  printf '  install dir: %s\n' "${BIN_DIR}"
  printf '  node prefix: %s\n' "${SETUP_HOST_NODE_PREFIX}"
  if [[ ${#MISSING_TOOLS[@]} -eq 0 ]]; then
    printf '  nothing to install: every tool is already on PATH.\n'
    return 0
  fi
  for tool in "${MISSING_TOOLS[@]}"; do
    printf '  would install %s <- %s\n' "${tool}" "$(setup_host_hint "${tool}")"
  done
  return 0
}

#######################################
# Install the missing tools: apt packages, pinned releases, then the pip lane.
# Failures are reported, not fatal: main re-probes and fails on anything absent.
# Globals:
#   MISSING_TOOLS, APT_TOOLS, RELEASE_TOOLS, SETUP_HOST_SUDO, BIN_DIR
# Arguments:
#   None
# Outputs:
#   Progress on stdout/stderr; installs into ${BIN_DIR} and ${SETUP_HOST_NODE_PREFIX}
# Returns:
#   0 always; the re-probe in main is what decides success
#######################################
setup_host_install_all() {
  local tool pkg failed=0 tmp=""
  local -a apt_pkgs=()
  if [[ "$(uname -s 2>/dev/null || true)" == Darwin ]]; then
    if ! command -v brew >/dev/null 2>&1; then
      err "setup-host: no Homebrew on this Mac; install it, then re-run this script"
      return 0
    fi
    for tool in "${MISSING_TOOLS[@]}"; do
      [[ ${tool} == pyright || ${tool} == mypy ]] && continue
      log "brew install ${tool} ..."
      if ! brew install "${tool}"; then
        warn "brew install ${tool} did not work; check that formula by hand"
        failed=1
      fi
    done
    setup_host_install_python_tools || failed=1
    [[ ${failed} == 0 ]] || log "some installs failed; the re-probe below lists what is left."
    return 0
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    err "setup-host: no apt-get and no Homebrew: the pinned releases below are all"
    err "  this script can fetch; install the apt packages by hand."
  fi

  for tool in "${MISSING_TOOLS[@]}"; do
    for pkg in "${APT_TOOLS[@]}"; do
      [[ ${tool} == "${pkg}" ]] && apt_pkgs+=("${tool}")
    done
  done
  if [[ ${#apt_pkgs[@]} -gt 0 ]] && command -v apt-get >/dev/null 2>&1; then
    log "apt-get install -y ${apt_pkgs[*]} ..."
    setup_host_run_root apt-get update -qq >/dev/null 2>&1 ||
      warn "apt-get update failed; continuing with the cached package list"
    if ! setup_host_run_root apt-get install -y "${apt_pkgs[@]}"; then
      warn "apt-get install ${apt_pkgs[*]} did not work; install those by hand"
      failed=1
    fi
  fi

  tmp="$(mktemp -d 2>/dev/null || true)"
  if [[ -z ${tmp} ]]; then
    err "setup-host: mktemp failed; cannot stage the release downloads"
    return 0
  fi
  if ! command -v curl >/dev/null 2>&1; then
    err "setup-host: no curl: the pinned releases cannot be fetched on this host"
    rm -rf "${tmp}"
    return 0
  fi
  for tool in "${RELEASE_TOOLS[@]}"; do
    [[ " ${MISSING_TOOLS[*]} " == *" ${tool} "* ]] || continue
    if ! setup_host_install_release "${tool}" "${tmp}"; then
      failed=1
    fi
  done
  if [[ " ${MISSING_TOOLS[*]} " == *" node "* ]]; then
    setup_host_install_node "${tmp}" || failed=1
  fi
  rm -rf "${tmp}"

  if [[ " ${MISSING_TOOLS[*]} " == *" pyright "* || " ${MISSING_TOOLS[*]} " == *" mypy "* ]]; then
    setup_host_install_python_tools || failed=1
  fi
  [[ ${failed} == 0 ]] || log "some installs failed; the re-probe below lists what is left."
  return 0
}

#######################################
# Fetch and install one raw release binary.
# Globals:
#   SETUP_HOST_ARCH
# Arguments:
#   $1 - tool from RELEASE_TOOLS
#   $2 - scratch dir to download into
# Outputs:
#   ${BIN_DIR}/$1; notes on stderr
# Returns:
#   0 when installed; 1 when the URL, fetch, or install failed
#######################################
setup_host_install_release() {
  local tool="${1:-}" tmp="${2:-}" url=""
  if ! url="$(setup_host_url "${tool}")"; then
    err "setup-host: ${tool}: no pinned Linux release in .devcontainer/tool-versions.env"
    return 1
  fi
  log "fetching ${tool} from ${url}"
  if ! setup_host_fetch "${url}" "${tmp}/${tool}"; then
    return 1
  fi
  setup_host_install_binary "${tmp}/${tool}" "${tool}"
}

#######################################
# setup-host entrypoint: parse args, load pins, probe, then check, plan or install.
# Globals:
#   everything above; SETUP_HOST_VERSIONS_FILE, SETUP_HOST_BIN_DIR
# Arguments:
#   $@ - optional --check, --dry-run, -h, --help
# Outputs:
#   Report, plan, or install progress on stdout/stderr
# Returns:
#   0 when every tool is present; 1 on a missing pin, an unknown argument, or a
#   tool that stayed missing
#######################################
main() {
  local arg mode=install tool
  for arg in "$@"; do
    case "${arg}" in
      --check) mode=check ;;
      --dry-run) mode=dry-run ;;
      -h | --help)
        setup_host_usage
        return 0
        ;;
      *)
        die "setup-host: unknown argument ${arg} (try --help)"
        ;;
    esac
  done

  setup_host_load_pins "${SETUP_HOST_VERSIONS_FILE}" ||
    die "setup-host: version pins are required; see --help"
  SETUP_HOST_ARCH="$(setup_host_arch || true)"
  SETUP_HOST_SUDO=""
  if [[ ${EUID} -ne 0 && ${LAB_NO_SUDO:-0} != 1 ]] && command -v sudo >/dev/null 2>&1; then
    SETUP_HOST_SUDO="sudo"
  fi

  setup_host_probe
  setup_host_report

  if [[ ${mode} == check ]]; then
    if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
      log "setup-host --check installed nothing and wrote nothing."
      log '  Run "bash scripts/setup-host.sh" (no flags) to install what is missing,'
      log '  or run "bazelisk test //:lint" knowing that the Bazel lint targets set'
      log '  REQUIRE_LINT_TOOLS=1, so a tool missing from PATH turns the gate red'
      log '  here. Running a lint script by hand on the host still skips what it'
      log '  cannot find.'
      return 1
    fi
    log "setup-host: every tool the Bazel targets need is on PATH."
    return 0
  fi

  if [[ ${mode} == dry-run ]]; then
    setup_host_pick_bin_dir 0 || return 1
    setup_host_install_plan
    return 0
  fi

  if [[ ${#MISSING_TOOLS[@]} -eq 0 ]]; then
    log "setup-host: every tool the Bazel targets need is on PATH."
    return 0
  fi

  setup_host_pick_bin_dir 1 || return 1
  setup_host_install_all

  # The re-probe is the point: a partial install must not look like a pass.
  setup_host_probe
  if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
    printf 'setup-host: still missing: %s\n' "${MISSING_TOOLS[*]}"
    for tool in "${MISSING_TOOLS[@]}"; do
      printf '  still missing: %s - %s\n' "${tool}" "$(setup_host_hint "${tool}")"
    done
    log "  //:lint will skip those checks instead of running them."
    return 1
  fi
  log "setup-host: every tool the Bazel targets need is on PATH."
  return 0
}

main "$@"
