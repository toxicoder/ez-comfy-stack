#!/usr/bin/env bats
#
# Hermetic tests for scripts/setup-host.sh (host bootstrap for the Bazel lint
# gate). curl, apt-get, brew, python3 and uname are mocked, and PATH is
# scrubbed per test: the suite never touches the network, sudo, or a host
# package manager.

load 'test_helper'

# Every binary the Bazel targets shell out to; must match REQUIRED_TOOLS in
# scripts/setup-host.sh and the --help text.
EXPECTED_TOOLS=(bazelisk shellcheck shfmt buildifier pyright mypy node git python3)

# Helper functions scripts/setup-host.sh declares. tests/shell_inventory.sh
# requires each name to appear under tests/, so this list is the gate.
EXPECTED_FUNCS=(
  setup_host_arch
  setup_host_fetch
  setup_host_hint
  setup_host_install_all
  setup_host_install_binary
  setup_host_install_node
  setup_host_install_plan
  setup_host_install_python_tools
  setup_host_install_release
  setup_host_load_pins
  setup_host_node_is_new_enough
  setup_host_pick_bin_dir
  setup_host_probe
  setup_host_report
  setup_host_run_root
  setup_host_sha256
  setup_host_usage
  setup_host_url
  setup_host_verify_sha256
)

# The six pins setup-host.sh must read from .devcontainer/tool-versions.env.
EXPECTED_PINS=(
  BAZELISK_VERSION
  BUILDIFIER_VERSION
  SHFMT_ASSET_VERSION
  NODE_VERSION
  NODE_SHA256_X64
  NODE_SHA256_ARM64
)

setup() {
  setup_repo_env
  export SCRIPT="${REPO_ROOT}/scripts/setup-host.sh"
  export VERSIONS_FILE="${REPO_ROOT}/.devcontainer/tool-versions.env"
  export BASH_BIN
  BASH_BIN="$(command -v bash)"
  export BIN_DIR="${TEST_TMP_DIR}/hostbin"
  export NODE_PREFIX="${TEST_TMP_DIR}/node-prefix"
  export SETUP_HOST_BIN_DIR="${BIN_DIR}"
  export SETUP_HOST_NODE_PREFIX="${NODE_PREFIX}"
  export LAB_NO_SUDO=1
  export TEST_ARCH
  TEST_ARCH="$(uname -m)"
  # A private coreutils dir: the install tests get a PATH with the package
  # managers and dev tools removed, but still resolve tar, install and friends.
  export CORE_BIN="${TEST_TMP_DIR}/core"
  mkdir -p "${CORE_BIN}"
  local need b
  need=(chmod cp env install ln mkdir mktemp rm rmdir tar sha256sum)
  for b in "${need[@]}"; do
    ln -s "$(command -v "${b}")" "${CORE_BIN}/${b}"
  done
  : >"${TEST_TMP_DIR}/curl_calls.log"
  : >"${TEST_TMP_DIR}/apt_calls.log"
  : >"${TEST_TMP_DIR}/brew_calls.log"
  : >"${TEST_TMP_DIR}/pip_calls.log"
}

teardown() {
  teardown_repo_env
}

# Read one pin value without exporting it into the test environment.
repo_pin() {
  sed -n "s/^${1}=//p" "${VERSIONS_FILE}" | head -1
}

# Like test_helper's install_mock_bin, but with an absolute shebang: these
# mocks are executed while PATH is scrubbed, so "#!/usr/bin/env bash" could
# not resolve bash itself.
install_mock() {
  local name="${1}"
  local body="${2}"
  cat >"${TEST_TMP_DIR}/bin/${name}" <<EOF
#!/bin/bash
${body}
EOF
  chmod +x "${TEST_TMP_DIR}/bin/${name}"
}

# PATH scrubbed to the mock dir: the probe needs no host binary beyond the
# two coreutils the shared logger resolves its siblings with.
install_core_mocks() {
  install_mock dirname '
if [[ ${1:-} == */* ]]; then
  echo "${1%/*}"
else
  echo "."
fi
exit 0
'
  install_mock uname "
if [[ \${1:-} == '-m' ]]; then
  echo '${TEST_ARCH}'
  exit 0
fi
echo 'Linux'
exit 0
"
}

# Mocks for every external the install path can reach. Each records its argv.
install_pkg_mocks() {
  install_core_mocks
  install_mock curl '
args=("$@")
target=""
url=""
i=0
while [[ ${i} -lt ${#args[@]} ]]; do
  case "${args[i]}" in
    -o) target="${args[i + 1]:-}" ;;
    http*) url="${args[i]}" ;;
  esac
  i=$((i + 1))
done
echo "curl ${url} -o ${target}" >>"${TEST_TMP_DIR}/curl_calls.log"
if [[ ${SETUP_HOST_TEST_CURL_FAIL:-0} == 1 ]]; then
  exit 22
fi
if [[ -z ${target} ]]; then
  exit 0
fi
if [[ ${url} == *.tar.xz && -n ${SETUP_HOST_TEST_TARBALL:-} ]]; then
  cp "${SETUP_HOST_TEST_TARBALL}" "${target}"
  exit 0
fi
printf "#!/bin/bash\nexit 0\n" >"${target}"
chmod 755 "${target}"
exit 0
'
  install_mock apt-get '
echo "apt-get $*" >>"${TEST_TMP_DIR}/apt_calls.log"
if [[ ${1:-} == install ]]; then
  shift
  for pkg in "$@"; do
    [[ ${pkg} == -y || ${pkg} == -qq ]] && continue
    # Never shadow a binary another mock already owns.
    [[ -e "${TEST_TMP_DIR}/bin/${pkg}" ]] && continue
    printf "#!/bin/bash\nexit 0\n" >"${SETUP_HOST_BIN_DIR}/${pkg}"
    chmod 755 "${SETUP_HOST_BIN_DIR}/${pkg}"
  done
fi
exit 0
'
  install_mock brew '
echo "brew $*" >>"${TEST_TMP_DIR}/brew_calls.log"
exit 0
'
  install_mock python3 '
echo "python3 $*" >>"${TEST_TMP_DIR}/pip_calls.log"
if [[ ${2:-} == pip ]]; then
  for tool in pyright mypy; do
    printf "#!/bin/bash\nexit 0\n" >"${TEST_TMP_DIR}/bin/${tool}"
    chmod 755 "${TEST_TMP_DIR}/bin/${tool}"
  done
fi
exit 0
'
}

# Scratch pin file so a test controls the checksums.
# $1 - node x64 sha256, $2 - node arm64 sha256
write_versions_file() {
  cat >"${TEST_TMP_DIR}/tool-versions.env" <<EOF
BAZELISK_VERSION=v1.25.0
BUILDIFIER_VERSION=v8.2.1
SHFMT_ASSET_VERSION=3.10.0
NODE_VERSION=$(repo_pin NODE_VERSION)
NODE_SHA256_X64=${1}
NODE_SHA256_ARM64=${2}
EOF
  printf '%s\n' "${TEST_TMP_DIR}/tool-versions.env"
}

# Stage a node distro tarball plus the pin file that matches its checksum.
# Sets TARBALL and PINS for the calling test.
stage_node() {
  local narch=x64 node_ver stage tarball
  [[ ${TEST_ARCH} == aarch64 || ${TEST_ARCH} == arm64 ]] && narch=arm64
  node_ver="$(repo_pin NODE_VERSION)"
  stage="${TEST_TMP_DIR}/node-stage/node-v${node_ver}-linux-${narch}"
  mkdir -p "${stage}/bin" "${stage}/lib/node_modules/npm/bin"
  printf '#!/bin/bash\necho "v%s"\n' "${node_ver}" >"${stage}/bin/node"
  chmod 755 "${stage}/bin/node"
  printf '#!/bin/bash\nexit 0\n' >"${stage}/lib/node_modules/npm/bin/npm-cli.js"
  chmod 755 "${stage}/lib/node_modules/npm/bin/npm-cli.js"
  ln -s ../lib/node_modules/npm/bin/npm-cli.js "${stage}/bin/npm"
  tarball="${TEST_TMP_DIR}/node-fake.tar"
  tar -cf "${tarball}" -C "${TEST_TMP_DIR}/node-stage" "node-v${node_ver}-linux-${narch}"
  TARBALL="${tarball}"
  PINS="$(write_versions_file "$(sha256sum "${tarball}" | awk '{print $1}')" "$(printf '0%.0s' {1..64})")"
  export SETUP_HOST_TEST_TARBALL="${tarball}"
  export SETUP_HOST_VERSIONS_FILE="${PINS}"
}

zeros64() {
  printf '0%.0s' {1..64}
}

@test "setup-host.sh exists and parses" {
  [[ -f ${SCRIPT} ]]
  run bash -n "${SCRIPT}"
  [ "$status" -eq 0 ]
}

@test "--help exits 0 and names every tool the Bazel targets need" {
  run "${BASH_BIN}" "${SCRIPT}" --help
  [ "$status" -eq 0 ]
  [[ ${output} == *"Usage:"* ]]
  [[ ${output} == *"tool-versions.env"* ]]
  local tool
  for tool in "${EXPECTED_TOOLS[@]}"; do
    [[ ${output} == *"${tool}"* ]]
  done
  [[ ${output} == *"--check"* ]]
  [[ ${output} == *"--dry-run"* ]]
}

@test "unknown argument is a hard error" {
  run "${BASH_BIN}" "${SCRIPT}" --install-everything
  [ "$status" -ne 0 ]
  [[ ${output} == *"--help"* ]]
}

@test "--check on a scrubbed PATH exits 1 and names every missing tool" {
  install_core_mocks
  install_mock git 'exit 0'
  install_mock python3 'exit 0'
  run env PATH="${TEST_TMP_DIR}/bin" "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 1 ]
  local tool
  for tool in bazelisk shellcheck shfmt buildifier pyright mypy node; do
    [[ ${output} == *"missing: ${tool}"* ]]
  done
  [[ ${output} == *"setup-host.sh"* ]]
}

@test "--check writes nothing" {
  install_core_mocks
  run env PATH="${TEST_TMP_DIR}/bin" "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 1 ]
  [[ ! -e ${BIN_DIR} ]]
  [[ ! -e ${NODE_PREFIX} ]]
  [ ! -s "${TEST_TMP_DIR}/curl_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/apt_calls.log" ]
}

@test "--check exits 0 when every tool is on PATH" {
  install_core_mocks
  local tool
  for tool in "${EXPECTED_TOOLS[@]}"; do
    install_mock "${tool}" "
if [[ \${1:-} == '--version' ]]; then
  echo 'v$(repo_pin NODE_VERSION)'
fi
exit 0
"
  done
  run env PATH="${TEST_TMP_DIR}/bin" "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 0 ]
  [[ ${output} == *"every tool"* ]]
}

@test "--check flags a node older than the pinned major" {
  install_core_mocks
  local old_major
  old_major=$(( $(repo_pin NODE_VERSION | cut -d. -f1) - 5 ))
  install_mock node "echo 'v${old_major}.0.0'; exit 0"
  run env PATH="${TEST_TMP_DIR}/bin" "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 1 ]
  [[ ${output} == *"missing: node"* ]]
}

@test "--dry-run prints the plan and touches nothing" {
  install_pkg_mocks
  local before after
  before="$(find "${TEST_TMP_DIR}" -mindepth 1 | sort)"
  run env PATH="${TEST_TMP_DIR}/bin" "${BASH_BIN}" "${SCRIPT}" --dry-run
  [ "$status" -eq 0 ]
  [[ ${output} == *"would install"* ]]
  [[ ${output} == *"bazelbuild/bazelisk/releases/download"* ]]
  [[ ${output} == *"mvdan/sh/releases/download"* ]]
  [[ ${output} == *"bazelbuild/buildtools/releases/download"* ]]
  [[ ${output} == *"nodejs.org/dist/"* ]]
  [[ ${output} == *"tests/requirements.txt"* ]]
  [[ ${output} == *"apt-get install"* ]]
  [[ ${output} == *"${BIN_DIR}"* ]]
  after="$(find "${TEST_TMP_DIR}" -mindepth 1 | sort)"
  [ "${before}" = "${after}" ]
  [ ! -s "${TEST_TMP_DIR}/curl_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/apt_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/brew_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/pip_calls.log" ]
}

@test "the script names no version literal and reads every pin" {
  run grep -nE '[0-9]+\.[0-9]+\.[0-9]+' "${SCRIPT}"
  [ "$status" -ne 0 ]
  grep -qF '.devcontainer/tool-versions.env' "${SCRIPT}"
  grep -qE 'set -a' "${SCRIPT}"
  grep -qE 'set \+a' "${SCRIPT}"
  local key
  for key in "${EXPECTED_PINS[@]}"; do
    grep -qF "${key}" "${SCRIPT}"
  done
}

@test "the script does not touch docker, models, or GPU paths" {
  run grep -nE '(^|[^#])(docker|compose|nvidia-smi|MODELS_DIR)' "${SCRIPT}"
  [ "$status" -ne 0 ]
}

@test "a missing pin is a hard error naming the key" {
  install_core_mocks
  local pins
  pins="$(write_versions_file "$(zeros64)" "$(zeros64)")"
  grep -v '^NODE_SHA256_ARM64=' "${pins}" >"${pins}.trimmed"
  run env PATH="${TEST_TMP_DIR}/bin" SETUP_HOST_VERSIONS_FILE="${pins}.trimmed" \
    "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 1 ]
  [[ ${output} == *"NODE_SHA256_ARM64"* ]]
}

@test "a missing pin file is a hard error naming the path" {
  install_core_mocks
  run env PATH="${TEST_TMP_DIR}/bin" \
    SETUP_HOST_VERSIONS_FILE="${TEST_TMP_DIR}/nope/tool-versions.env" \
    "${BASH_BIN}" "${SCRIPT}" --check
  [ "$status" -eq 1 ]
  [[ ${output} == *"tool-versions.env"* ]]
}

@test "default run installs with apt, the pinned releases, and pip" {
  install_pkg_mocks
  stage_node
  run env PATH="${BIN_DIR}:${TEST_TMP_DIR}/bin:${CORE_BIN}" "${BASH_BIN}" "${SCRIPT}"
  [ "$status" -eq 0 ]
  [[ ${output} == *"${BIN_DIR}"* ]]
  [[ -x "${BIN_DIR}/bazelisk" ]]
  [[ -x "${BIN_DIR}/shfmt" ]]
  [[ -x "${BIN_DIR}/buildifier" ]]
  grep -qE 'install .*shellcheck' "${TEST_TMP_DIR}/apt_calls.log"
  grep -qF 'bazelbuild/bazelisk/releases/download' "${TEST_TMP_DIR}/curl_calls.log"
  grep -qF 'mvdan/sh/releases/download' "${TEST_TMP_DIR}/curl_calls.log"
  grep -qF 'bazelbuild/buildtools/releases/download' "${TEST_TMP_DIR}/curl_calls.log"
  grep -qF 'tests/requirements.txt' "${TEST_TMP_DIR}/pip_calls.log"
}

@test "a failed download still fails the re-probe" {
  install_pkg_mocks
  stage_node
  run env PATH="${BIN_DIR}:${TEST_TMP_DIR}/bin:${CORE_BIN}" \
    SETUP_HOST_TEST_CURL_FAIL=1 "${BASH_BIN}" "${SCRIPT}"
  [ "$status" -eq 1 ]
  [[ ${output} == *"still missing"* ]]
  [[ ${output} == *"bazelisk"* ]]
  [[ ! -e ${BIN_DIR}/bazelisk ]]
}

@test "node is installed only when its sha256 matches the pin" {
  install_pkg_mocks
  stage_node
  run env PATH="${BIN_DIR}:${TEST_TMP_DIR}/bin:${CORE_BIN}" "${BASH_BIN}" "${SCRIPT}"
  [ "$status" -eq 0 ]
  [[ -x "${NODE_PREFIX}/bin/node" ]]
  [[ -e "${BIN_DIR}/node" ]]
  [[ -e "${BIN_DIR}/npm" ]]
}

@test "a node tarball that fails the checksum is refused" {
  install_pkg_mocks
  stage_node
  local bad
  bad="$(write_versions_file "$(printf 'a%.0s' {1..64})" "$(zeros64)")"
  run env PATH="${BIN_DIR}:${TEST_TMP_DIR}/bin:${CORE_BIN}" \
    SETUP_HOST_VERSIONS_FILE="${bad}" "${BASH_BIN}" "${SCRIPT}"
  [ "$status" -eq 1 ]
  [[ ${output} == *"missing: node"* ]]
  [[ ${output} == *"sha256"* ]]
  [[ ! -e ${BIN_DIR}/node ]]
}

@test "setup-host declares every helper the test suite names" {
  local fn
  for fn in "${EXPECTED_FUNCS[@]}"; do
    grep -qE "^${fn}\(\) \{$" "${SCRIPT}"
  done
}

@test "setup-host is reachable as a Make shim" {
  grep -qE '^setup-host:' "${REPO_ROOT}/Makefile"
  run make -C "${REPO_ROOT}" -n setup-host
  [ "$status" -eq 0 ]
  [[ ${output} == *"scripts/setup-host.sh"* ]]
}
