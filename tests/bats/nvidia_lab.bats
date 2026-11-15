#!/usr/bin/env bats
#
# ## nvidia_lab.bats
#
# Purpose:
#   Cover every function in scripts/utilities/nvidia-lab.sh (strict inventory)
#   and the refusal rules of the opt-in NVIDIA lab tier: only an opt-in row can
#   be installed, uninstalled, or run; install and run pass the heavy confirm,
#   the headroom preflight, and the one-heavy-GPU-job occupancy XOR; run prints
#   its command and executes it only under EZ_NVIDIA_LAB_EXECUTE=1.
#
# Hermetic:
#   The catalog reader (scripts/lib/nvidia_lab.py) is a separate deliverable, so
#   this suite fakes python3 on PATH: it intercepts only the reader invocation
#   and answers from a flat fixture, and passes every other python3 call to the
#   real interpreter (occupancy reads its state through python3). docker and git
#   are mocked; headroom mocks come from setup_repo_env. No network, no GPU.
#

load 'test_helper'

#######################################
# Write the flat fixture the fake reader answers from.
# Globals:
#   NL_STUB_CATALOG
# Arguments:
#   None
# Outputs:
#   Fixture file
# Returns:
#   0
#######################################
write_nvidia_lab_fixture() {
  cat >"${NL_STUB_CATALOG}" <<'EOF'
ROW artifixer opt-in ArtiFixer
FIELD artifixer install docker-pull
FIELD artifixer artifact_ref ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939
FIELD artifixer cmd docker pull ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939
FIELD artifixer vram_gb 40
FIELD artifixer disk_gb 120
FIELD artifixer gate_notes Apache-2.0 code, ungated weights, and a published linux/arm64 CUDA 13 image
FIELD artifixer reopen n/a - this row is installable.
ROW 3dgrut opt-in 3DGRUT (3DGRT + 3DGUT)
FIELD 3dgrut install git-clone
FIELD 3dgrut artifact_ref https://github.com/nv-tlabs/3dgrut.git
FIELD 3dgrut cmd
FIELD 3dgrut vram_gb 24
FIELD 3dgrut disk_gb 20
FIELD 3dgrut gate_notes CUDA kernels compile at install and no aarch64 build is documented
FIELD 3dgrut reopen n/a - the first GB10 build has to be proven on the host.
ROW fake-pip opt-in Fake Pip Tool
FIELD fake-pip install pip-install
FIELD fake-pip artifact_ref
FIELD fake-pip cmd pip install fake-pip
FIELD fake-pip gate_notes upstream ships only a pip package
FIELD fake-pip reopen publish a linux_aarch64 wheel
ROW fake-none opt-in Fake None Tool
FIELD fake-none install none
FIELD fake-none artifact_ref
FIELD fake-none cmd
FIELD fake-none gate_notes nothing to place on this host
FIELD fake-none reopen upstream publishes an artifact
ROW lyra-2 blocked-license Project Lyra 2.0
FIELD lyra-2 install none
FIELD lyra-2 artifact_ref https://github.com/nv-tlabs/lyra.git
FIELD lyra-2 cmd
FIELD lyra-2 gate_notes The weight terms bar deployment and production use
FIELD lyra-2 reopen NVIDIA relicenses the Lyra 2.0 checkpoints so deployment and production use are permitted.
ROW cosmos-drive-dreams blocked-platform Cosmos Drive Dreams
FIELD cosmos-drive-dreams install none
FIELD cosmos-drive-dreams artifact_ref nvcr.io/nvidia/cosmos
FIELD cosmos-drive-dreams cmd
FIELD cosmos-drive-dreams gate_notes the Cosmos upstream ships x86_64 NGC images only
FIELD cosmos-drive-dreams reopen Upstream Cosmos publishes linux_aarch64 wheels or an arm64 container that runs on GB10.
ROW pixelumm deferred PixelUMM
FIELD pixelumm install none
FIELD pixelumm artifact_ref https://github.com/nv-tlabs/PixelUMM.git
FIELD pixelumm cmd
FIELD pixelumm gate_notes 121.6 GB of weights and a seven GPU training path
FIELD pixelumm reopen A quantized single-GPU inference checkpoint with a readable permissive weight license.
EOF
}

#######################################
# Fake the catalog reader CLI contract over the fixture.
# Globals:
#   NL_STUB_READER, NL_STUB_LOG
# Arguments:
#   None
# Outputs:
#   Executable stub + argv log
# Returns:
#   0
#######################################
install_nvidia_lab_reader_stub() {
  cat >"${NL_STUB_READER}" <<'EOF'
#!/usr/bin/env bash
# Fake scripts/lib/nvidia_lab.py reader: same verbs, same shapes, flat fixture.
set -euo pipefail
catalog="${NL_STUB_CATALOG:-}"
printf '%s\n' "$*" >>"${NL_STUB_LOG}"
if [[ "${1:-}" == "--catalog" ]]; then
  catalog="${2:-}"
  shift 2
fi
verb="${1:-}"
if [[ $# -gt 0 ]]; then
  shift
fi

row_exists() {
  awk -v id="${1}" '$1=="ROW" && $2==id {found=1} END{exit !found}' "${catalog}"
}

case "${verb}" in
  list)
    awk -v OFS='\t' '$1=="ROW" {t=""; for (i=4; i<=NF; i++) t=(t=="" ? $i : t " " $i); print $2, $3, t}' "${catalog}"
    ;;
  ids)
    awk '$1=="ROW" {print $2}' "${catalog}"
    ;;
  status)
    id="${1:-}"
    row_exists "${id}" || {
      echo "unknown id: ${id}" >&2
      exit 1
    }
    awk -v id="${id}" '$1=="ROW" && $2==id {print $3; exit}' "${catalog}"
    ;;
  fields)
    id="${1:-}"
    keys="${2:-}"
    row_exists "${id}" || {
      echo "unknown id: ${id}" >&2
      exit 1
    }
    IFS=',' read -r -a want <<<"${keys}"
    for key in "${want[@]}"; do
      value="$(awk -v id="${id}" -v key="${key}" '$1=="FIELD" && $2==id && $3==key {
        v = ""
        for (i = 4; i <= NF; i++) v = (v == "" ? $i : v " " $i)
        print v
        exit
      }' "${catalog}")"
      printf '%s=%s\n' "${key}" "${value}"
    done
    ;;
  check)
    if [[ "${NL_STUB_CHECK_RC:-0}" == "1" ]]; then
      echo "catalog rejected: unknown key" >&2
      exit 1
    fi
    count="$(awk '$1=="ROW" {c++} END{print c+0}' "${catalog}")"
    echo "ok ${count} tools"
    ;;
  *)
    echo "fake reader: unknown verb ${verb}" >&2
    exit 2
    ;;
esac
EOF
  chmod +x "${NL_STUB_READER}"
  : >"${NL_STUB_LOG}"
}

#######################################
# Shadow python3: intercept only the nvidia-lab reader, pass the rest through.
# Globals:
#   NL_REAL_PYTHON, NL_STUB_READER, TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Executable fake python3 on PATH
# Returns:
#   0
#######################################
install_nvidia_lab_python_mock() {
  cat >"${TEST_TMP_DIR}/bin/python3" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == */scripts/lib/nvidia_lab.py ]]; then
  shift
  exec bash "${NL_STUB_READER}" "$@"
fi
exec "${NL_REAL_PYTHON}" "$@"
EOF
  chmod +x "${TEST_TMP_DIR}/bin/python3"
}

#######################################
# Log git argv and honour a clone by creating the target directory.
# Globals:
#   TEST_TMP_DIR
# Arguments:
#   None
# Outputs:
#   Executable git mock + git_calls.log
# Returns:
#   0
#######################################
install_git_mock() {
  cat >"${TEST_TMP_DIR}/bin/git" <<'EOF'
#!/usr/bin/env bash
echo "git $*" >>"${TEST_TMP_DIR}/git_calls.log"
if [[ "${1:-}" == "clone" ]]; then
  target=""
  for arg in "$@"; do
    target="${arg}"
  done
  mkdir -p "${target}"
fi
exit 0
EOF
  chmod +x "${TEST_TMP_DIR}/bin/git"
  : >"${TEST_TMP_DIR}/git_calls.log"
}

#######################################
# Write an occupancy state record for the XOR gate.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   $1  mode
#   $2  optional llm_pid (default 0)
# Outputs:
#   .occupancy.json
# Returns:
#   0
#######################################
set_occupancy_state() {
  local mode="${1}" llm_pid="${2:-0}"
  cat >"${COMFY_OUTPUT_DIR}/.occupancy.json" <<EOF
{"version":1,"mode":"${mode}","compose":false,"parked":false,"blender_pid":0,"mcp_pid":0,"llm_pid":${llm_pid},"pids_alive":{"blender_pid":false,"mcp_pid":false,"llm_pid":false},"updated":"2026-11-15T00:00:00Z"}
EOF
}

setup() {
  setup_repo_env
  NL_REAL_PYTHON="$(command -v python3)"
  export NL_REAL_PYTHON
  export NL_STUB_CATALOG="${TEST_TMP_DIR}/catalog.rows"
  export NL_STUB_READER="${TEST_TMP_DIR}/fake-nvidia-lab-reader.sh"
  export NL_STUB_LOG="${TEST_TMP_DIR}/reader_calls.log"
  write_nvidia_lab_fixture
  install_nvidia_lab_reader_stub
  install_nvidia_lab_python_mock
  install_git_mock
  install_docker_mocks
  export EZ_NVIDIA_LAB_CATALOG="${NL_STUB_CATALOG}"
  export EZ_NVIDIA_LAB_HOME="${TEST_TMP_DIR}/nvidia-lab"
  export LAB_NON_INTERACTIVE=1
  export LAB_CONFIRM_TOKEN=yes
  set_occupancy_state idle
  export DLS="${UTILITIES_DIR}/nvidia-lab.sh"
  chmod +x "${DLS}"
  # shellcheck disable=SC1090
  source "${DLS}"
}

teardown() {
  teardown_repo_env
}

@test "nvidia-lab list prints id status title from the reader" {
  run bash "${DLS}" list
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"artifixer	opt-in	ArtiFixer"* ]]
  [[ "${output}" == *"lyra-2	blocked-license	Project Lyra 2.0"* ]]
  [[ "${output}" == *"pixelumm	deferred	PixelUMM"* ]]
  run bash "${DLS}" list extra-arg
  [ "${status}" -eq 1 ]
}

@test "every catalog read goes through the python reader with --catalog" {
  : >"${NL_STUB_LOG}"
  run bash "${DLS}" list
  [ "${status}" -eq 0 ]
  grep -q -- "--catalog ${EZ_NVIDIA_LAB_CATALOG} list" "${NL_STUB_LOG}"
  : >"${NL_STUB_LOG}"
  run bash "${DLS}" status artifixer
  [ "${status}" -eq 0 ]
  grep -q -- "--catalog ${EZ_NVIDIA_LAB_CATALOG} status artifixer" "${NL_STUB_LOG}"
  # Without the override the reader picks its own catalog path.
  : >"${NL_STUB_LOG}"
  run bash -c "unset EZ_NVIDIA_LAB_CATALOG; bash '${DLS}' check"
  [ "${status}" -eq 0 ]
  ! grep -q -- "--catalog" "${NL_STUB_LOG}"
}

@test "an id the catalog does not publish is refused everywhere" {
  run bash "${DLS}" status nosuchtool
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"unknown nvidia-lab id: nosuchtool"* ]]
  run bash "${DLS}" plan nosuchtool
  [ "${status}" -ne 0 ]
  run bash "${DLS}" install nosuchtool
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"unknown nvidia-lab id: nosuchtool"* ]]
  run bash "${DLS}" uninstall nosuchtool
  [ "${status}" -eq 2 ]
  run bash "${DLS}" run nosuchtool --input /tmp/does-not-matter
  [ "${status}" -eq 2 ]
}

@test "a blocked-license row refuses install uninstall and run" {
  run bash "${DLS}" install lyra-2
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"status is blocked-license"* ]]
  [[ "${output}" == *"gate_notes: The weight terms bar deployment and production use"* ]]
  [[ "${output}" == *"reopen: NVIDIA relicenses the Lyra 2.0 checkpoints so deployment and production use are permitted."* ]]
  run bash "${DLS}" uninstall lyra-2
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"blocked-license"* ]]
  run bash "${DLS}" run lyra-2 --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"blocked-license"* ]]
  # The verdict is still readable without an install path.
  run bash "${DLS}" plan lyra-2
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"status: blocked-license"* ]]
  [[ "${output}" == *"target: none"* ]]
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/git_calls.log" ]
}

@test "a blocked-platform row refuses install and run" {
  run bash "${DLS}" install cosmos-drive-dreams
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"status is blocked-platform"* ]]
  [[ "${output}" == *"gate_notes: the Cosmos upstream ships x86_64 NGC images only"* ]]
  [[ "${output}" == *"reopen: Upstream Cosmos publishes linux_aarch64 wheels or an arm64 container that runs on GB10."* ]]
  run bash "${DLS}" run cosmos-drive-dreams --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 2 ]
}

@test "a deferred row refuses install uninstall and run" {
  run bash "${DLS}" install pixelumm
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"status is deferred"* ]]
  [[ "${output}" == *"gate_notes: 121.6 GB of weights and a seven GPU training path"* ]]
  [[ "${output}" == *"reopen: A quantized single-GPU inference checkpoint with a readable permissive weight license."* ]]
  run bash "${DLS}" uninstall pixelumm
  [ "${status}" -eq 2 ]
  run bash "${DLS}" run pixelumm --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 2 ]
}

@test "install and run refuse while occupancy holds the GPU" {
  touch "${TEST_TMP_DIR}/in.png"
  for mode in klein trellis wan ltx; do
    set_occupancy_state "${mode}"
    run bash "${DLS}" install artifixer
    [ "${status}" -eq 2 ]
    [[ "${output}" == *"occupancy is ${mode}"* ]]
    run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/in.png"
    [ "${status}" -eq 2 ]
    [[ "${output}" == *"occupancy is ${mode}"* ]]
  done
  # A live llm-desk sidecar holds unified memory too.
  set_occupancy_state llm-desk "$$"
  run bash "${DLS}" install artifixer
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"occupancy is llm-desk with a live sidecar"* ]]
  # idle releases both verbs.
  set_occupancy_state idle
  run bash "${DLS}" install artifixer
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"installing artifixer: docker pull ghcr.io"* ]]
}

@test "install and run refuse without the heavy confirm" {
  touch "${TEST_TMP_DIR}/in.png"
  unset LAB_CONFIRM_TOKEN
  run bash "${DLS}" install artifixer
  [ "${status}" -eq 5 ]
  [[ "${output}" == *"HEAVY WORKLOAD"* ]]
  [[ "${output}" == *"LAB_CONFIRM_TOKEN=yes"* ]]
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]
  run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 5 ]
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]
}

@test "install refuses when host headroom is short" {
  export LAB_MOCK_FREE_MEM_GIB=1
  run bash "${DLS}" install artifixer
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"Insufficient free memory"* ]]
  [[ "${output}" == *"headroom preflight failed"* ]]
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]
}

@test "plan prints the pull target and the command for a docker-pull row" {
  run bash "${DLS}" plan artifixer
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"id: artifixer"* ]]
  [[ "${output}" == *"status: opt-in"* ]]
  [[ "${output}" == *"install: docker-pull"* ]]
  [[ "${output}" == *"target: ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939"* ]]
  [[ "${output}" == *"command: docker pull ghcr.io/nv-tlabs/artifixer:cuda13"* ]]
  [[ "${output}" == *"vram_gb: 40"* ]]
  [[ "${output}" == *"disk_gb: 120"* ]]
  # plan fetches nothing.
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]
  [ ! -s "${TEST_TMP_DIR}/git_calls.log" ]
  [ ! -d "${EZ_NVIDIA_LAB_HOME}" ]
}

@test "plan prints the clone target under the lab home, never the repo" {
  run bash "${DLS}" plan 3dgrut
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"source: https://github.com/nv-tlabs/3dgrut.git"* ]]
  [[ "${output}" == *"target: ${EZ_NVIDIA_LAB_HOME}/3dgrut"* ]]
  [[ "${output}" == *"command: git clone https://github.com/nv-tlabs/3dgrut.git"* ]]
  [[ "${output}" != *"${REPO_ROOT}/"* ]]
  [[ "${output}" != *"${COMFY_OUTPUT_DIR}/"* ]]
}

@test "install pulls the artifact of a docker-pull row" {
  run bash "${DLS}" install artifixer
  [ "${status}" -eq 0 ]
  grep -q "docker pull ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939" \
    "${TEST_TMP_DIR}/docker_calls.log"
}

@test "install clones a git-clone row into the lab home" {
  run bash "${DLS}" install 3dgrut
  [ "${status}" -eq 0 ]
  grep -q "git clone https://github.com/nv-tlabs/3dgrut.git ${EZ_NVIDIA_LAB_HOME}/3dgrut" \
    "${TEST_TMP_DIR}/git_calls.log"
  [ -d "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  [[ "${EZ_NVIDIA_LAB_HOME}/3dgrut" != "${REPO_ROOT}"* ]]
  [[ "${EZ_NVIDIA_LAB_HOME}/3dgrut" != "${COMFY_OUTPUT_DIR}"* ]]
  [ ! -e "${REPO_ROOT}/3dgrut" ]
}

@test "install refuses pip-install and none rows with a stated reason" {
  run bash "${DLS}" install fake-pip
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"install=pip-install"* ]]
  [[ "${output}" == *"will not pip-install"* ]]
  [ ! -s "${TEST_TMP_DIR}/git_calls.log" ]
  run bash "${DLS}" install fake-none
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"install=none"* ]]
}

@test "run prints the command and executes only with EZ_NVIDIA_LAB_EXECUTE=1" {
  printf 'pixels\n' >"${TEST_TMP_DIR}/in.png"
  run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/in.png" --params '{"steps":8}'
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"would run: docker pull ghcr.io/nv-tlabs/artifixer:cuda13"* ]]
  [[ "${output}" == *"--input ${TEST_TMP_DIR}/in.png"* ]]
  [[ "${output}" == *"--params {\"steps\":8}"* ]]
  [[ "${output}" == *"EZ_NVIDIA_LAB_EXECUTE=1"* ]]
  [[ "${output}" == *"unverified on GB10"* ]]
  [ ! -s "${TEST_TMP_DIR}/docker_calls.log" ]

  export EZ_NVIDIA_LAB_EXECUTE=1
  run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"executing artifixer:"* ]]
  grep -q "docker pull ghcr.io/nv-tlabs/artifixer:cuda13" "${TEST_TMP_DIR}/docker_calls.log"
}

@test "run refuses a missing input, a missing flag, and a row with no cmd" {
  run bash "${DLS}" run artifixer
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"needs --input PATH"* ]]
  run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/absent.png"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"input not found"* ]]
  run bash "${DLS}" run artifixer --input
  [ "${status}" -eq 1 ]
  run bash "${DLS}" run artifixer --input "${TEST_TMP_DIR}/x" --bogus
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"unknown nvidia-lab argument"* ]]
  # 3dgrut publishes no cmd, so run refuses rather than guessing an entrypoint.
  touch "${TEST_TMP_DIR}/in.png"
  run bash "${DLS}" run 3dgrut --input "${TEST_TMP_DIR}/in.png"
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"publishes no cmd"* ]]
}

@test "uninstall removes only the lab-home checkout" {
  run bash "${DLS}" install 3dgrut
  [ "${status}" -eq 0 ]
  [ -d "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  run bash "${DLS}" uninstall 3dgrut
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"removing ${EZ_NVIDIA_LAB_HOME}/3dgrut"* ]]
  [ ! -d "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  # A missing checkout is not an error.
  run bash "${DLS}" uninstall 3dgrut
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"nothing installed for 3dgrut"* ]]
  # A pulled image is shared, so the CLI never deletes it.
  run bash "${DLS}" uninstall artifixer
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"shared on this host"* ]]
  # A path that is not the row's own checkout is never removed.
  run bash "${DLS}" uninstall ../etc
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"invalid nvidia-lab id"* ]]
}

@test "check passes and fails with the reader" {
  run bash "${DLS}" check
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ok 7 tools"* ]]
  export NL_STUB_CHECK_RC=1
  run bash "${DLS}" check
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"catalog check failed"* ]]
}

@test "usage and unknown verbs fail closed" {
  run bash "${DLS}"
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"nvidia-lab list"* ]]
  [[ "${output}" == *"EZ_NVIDIA_LAB_EXECUTE=1"* ]]
  run bash "${DLS}" bogus-verb
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"unknown nvidia-lab verb: bogus-verb"* ]]
  run bash "${DLS}" status
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"needs a row id"* ]]
  run bash "${DLS}" status artifixer extra
  [ "${status}" -eq 1 ]
  run bash "${DLS}" status 3DGRUT
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"invalid nvidia-lab id"* ]]
}

@test "manage.sh wires the nvidia-lab verb to this CLI" {
  # Names the manage.sh dispatcher (strict shell inventory) and pins the seam:
  # manage.sh must keep routing the verb to this script.
  grep -q 'cmd_nvidia_lab()' "${REPO_ROOT}/scripts/manage.sh"
  grep -q 'nvidia-lab) cmd_nvidia_lab "$@" ;;' "${REPO_ROOT}/scripts/manage.sh"
  grep -q 'scripts/utilities/nvidia-lab.sh' "${REPO_ROOT}/scripts/manage.sh"
}

@test "nvidia-lab script text is ASCII only" {
  local stray
  LC_ALL=C
  stray="$(tr -d '\011\012\040-\176' <"${DLS}" | wc -c | tr -d ' ')"
  [ "${stray}" = "0" ]
}

@test "reader seam and id helpers behave" {
  run nl_log "planned"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"[nvidia-lab] planned"* ]]
  run nl_warn "soft"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"WARN"* && "${output}" == *"[nvidia-lab] soft"* ]]
  run nl_err "hard"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ERROR"* && "${output}" == *"[nvidia-lab] hard"* ]]
  run nl_reader_path
  [ "${status}" -eq 0 ]
  [[ "${output}" == */scripts/lib/nvidia_lab.py ]]
  run nl_lab_home
  [ "${output}" = "${EZ_NVIDIA_LAB_HOME}" ]
  run nl_clone_dir 3dgrut
  [ "${output}" = "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  run nl_valid_id 3dgrut-artifixer-fork
  [ "${status}" -eq 0 ]
  run nl_valid_id ../etc
  [ "${status}" -eq 1 ]
  run nl_valid_id ""
  [ "${status}" -eq 1 ]
  run nl_cli list
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"artifixer"* ]]
  run nl_row_fields artifixer install cmd
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"install=docker-pull"* ]]
  [[ "${output}" == *"cmd=docker pull ghcr.io"* ]]
  run nl_field_value "install=docker-pull
cmd=" install
  [ "${output}" = "docker-pull" ]
  run nl_field_value "install=docker-pull" cmd
  [ "${status}" -eq 1 ]
}

@test "row verdict helpers behave in process" {
  run nl_row_status artifixer
  [ "${status}" -eq 0 ]
  [ "${output}" = "opt-in" ]
  run nl_row_status nosuchtool
  [ "${status}" -eq 2 ]
  run nl_row_status ""
  [ "${status}" -eq 1 ]
  run nl_print_verdict lyra-2 blocked-license
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"row lyra-2 is blocked-license"* ]]
  [[ "${output}" == *"reopen: NVIDIA relicenses"* ]]
  run nl_require_opt_in artifixer "install artifixer"
  [ "${status}" -eq 0 ]
  run nl_require_opt_in lyra-2 "install lyra-2"
  [ "${status}" -eq 2 ]
}

@test "argv builders and executor behave in process" {
  # Direct calls (not run) so the globals these builders set are visible.
  nl_install_argv artifixer
  [ "${NL_KIND}" = "docker-pull" ]
  [ "${NL_TARGET}" = "ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939" ]
  nl_install_argv 3dgrut
  [ "${NL_KIND}" = "git-clone" ]
  [ "${NL_ARGV[0]}" = "git" ]
  [ "${NL_ARGV[2]}" = "https://github.com/nv-tlabs/3dgrut.git" ]
  [ "${NL_ARGV[3]}" = "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  run nl_install_argv fake-pip
  [ "${status}" -eq 2 ]
  run nl_install_argv fake-none
  [ "${status}" -eq 2 ]

  touch "${TEST_TMP_DIR}/in.png"
  nl_run_argv artifixer "${TEST_TMP_DIR}/in.png" '{"steps":8}'
  run nl_print_argv
  [[ "${output}" == "docker pull ghcr.io/nv-tlabs/artifixer:cuda13"* ]]
  [[ "${output}" == *"--input ${TEST_TMP_DIR}/in.png --params {\"steps\":8}" ]]
  run nl_run_argv artifixer "" ""
  [ "${status}" -eq 1 ]
  run nl_run_argv artifixer "${TEST_TMP_DIR}/missing.png" ""
  [ "${status}" -eq 1 ]
  run nl_run_argv 3dgrut "${TEST_TMP_DIR}/in.png" ""
  [ "${status}" -eq 2 ]

  NL_ARGV=(echo worked)
  run nl_exec_argv
  [ "${status}" -eq 0 ]
  [ "${output}" = "worked" ]
  NL_ARGV=()
  run nl_print_argv
  [ "${status}" -eq 0 ]
  [ -z "${output}" ]
  run nl_exec_argv
  [ "${status}" -eq 1 ]
}

@test "occupancy and confirm gates pass for an idle host" {
  run nl_refuse_heavy_occupancy "install artifixer"
  [ "${status}" -eq 0 ]
  set_occupancy_state wan
  run nl_refuse_heavy_occupancy "install artifixer"
  [ "${status}" -eq 2 ]
  set_occupancy_state idle
  run nl_gate_heavy_work "nvidia-lab install artifixer"
  [ "${status}" -eq 0 ]
  unset LAB_CONFIRM_TOKEN
  run nl_gate_heavy_work "nvidia-lab install artifixer"
  [ "${status}" -eq 5 ]
}

@test "verbs run in process through their own entry points" {
  run cmd_help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"nvidia-lab check"* ]]
  run cmd_list
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"3dgrut"* ]]
  run cmd_status artifixer
  [ "${status}" -eq 0 ]
  [ "${output}" = "status artifixer: opt-in" ]
  run cmd_plan artifixer
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"install: docker-pull"* ]]
  run cmd_check
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"ok 7 tools"* ]]
  run cmd_install 3dgrut
  [ "${status}" -eq 0 ]
  [ -d "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  run cmd_uninstall 3dgrut
  [ "${status}" -eq 0 ]
  [ ! -d "${EZ_NVIDIA_LAB_HOME}/3dgrut" ]
  touch "${TEST_TMP_DIR}/in.png"
  run cmd_run artifixer "${TEST_TMP_DIR}/in.png" ""
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"would run: docker pull"* ]]
  # parse_args writes the verb globals, so call it without run.
  parse_args run 3dgrut --input "${TEST_TMP_DIR}/in.png"
  [ "${CMD}" = "run" ]
  [ "${TOOL_ID}" = "3dgrut" ]
  [ "${RUN_INPUT}" = "${TEST_TMP_DIR}/in.png" ]
  parse_args install artifixer
  [ "${CMD}" = "install" ]
  run parse_args nope
  [ "${status}" -eq 1 ]
  run main list
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"artifixer"* ]]
}
