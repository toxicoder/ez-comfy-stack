#!/usr/bin/env bash
#
# ## nvidia-lab
#
# Operator CLI for the opt-in NVIDIA lab tier (one Spark, GB10 unverified).
#
# Purpose:
#   The tier is a catalog of NVIDIA lab rows (ArtiFixer, 3DGRUT, Lyra, GEN3C,
#   NuRec, ...) that are off by default and download nothing at boot. This CLI
#   is the only host door for that catalog: it lists rows, prints the verdict
#   for a row, plans the artifact fetch, and installs or runs a row the operator
#   opted into. Every catalog read goes through the Python reader in
#   scripts/lib/nvidia_lab.py, which owns schema validation; this script never
#   parses the catalog JSON itself.
#
# Audience:
#   Operators of a remotely managed DGX Spark. Wired into manage.sh as the
#   nvidia-lab verb; also sourced by tests/bats/nvidia_lab.bats.
#
# Usage:
#   bazelisk run //:manage -- nvidia-lab list
#   bazelisk run //:manage -- nvidia-lab status ID
#   bazelisk run //:manage -- nvidia-lab plan ID
#   bazelisk run //:manage -- nvidia-lab install ID
#   bazelisk run //:manage -- nvidia-lab uninstall ID
#   bazelisk run //:manage -- nvidia-lab run ID --input PATH [--params JSON]
#   bazelisk run //:manage -- nvidia-lab check
#
# Invariants:
#   - install / uninstall / run refuse any row whose status is not opt-in, and
#     print that row's status, gate_notes, and reopen sentence.
#   - install and run require the heavy confirm (require_heavy_confirm) and the
#     host headroom preflight (check_host_headroom), and refuse while occupancy
#     holds a heavy GPU mode or a live desk sidecar. These rows put work on the
#     same GB10 outside the Comfy process, so the one-heavy-GPU-job XOR holds.
#   - install runs only the row's own cmd when it is non-empty; otherwise it
#     pulls artifact_ref (docker-pull) or clones artifact_ref into the lab home
#     (git-clone). pip-install and none rows refuse with a stated reason.
#   - Artifacts land under ${EZ_NVIDIA_LAB_HOME:-$HOME/.ez-comfy/nvidia-lab}/ID:
#     never in the repo, never in a Comfy bind.
#   - run prints the exact command it would execute and executes it only when
#     EZ_NVIDIA_LAB_EXECUTE=1. The tier is unverified on GB10 and stays honest
#     about that.
#   - Nothing here touches docker-compose, the restart policy, mem_limit, the
#     headroom thresholds, or the download-limit trap.
#
# Test hooks:
#   EZ_NVIDIA_LAB_CATALOG - catalog JSON path handed to the reader as --catalog
#   EZ_NVIDIA_LAB_EXECUTE - 1 lets run execute the command it printed
#   EZ_NVIDIA_LAB_HOME    - clone root (default $HOME/.ez-comfy/nvidia-lab)
#
# Exit codes:
#   0 ok; 1 usage or reader failure; 2 refuse (unknown or non-opt-in row,
#   occupancy busy, headroom short, install kind this CLI will not run);
#   5 heavy confirm declined.
#
# @command nvidia-lab

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/occupancy.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/occupancy.sh"
# shellcheck source=../lib/safety.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/safety.sh"

# Single door to the catalog reader; the reader owns schema validation.
readonly NL_READER_REL="scripts/lib/nvidia_lab.py"
# Occupancy modes that own the GPU. llm-desk is covered by the live-sidecar
# check in nl_refuse_heavy_occupancy, which is what actually holds memory.
readonly -a NL_HEAVY_MODES=(klein trellis wan ltx)
# Exit codes (documented in the file header).
readonly NL_E_USAGE=1
readonly NL_E_REFUSE=2
readonly NL_E_DECLINED=5

CMD=""
TOOL_ID=""
RUN_INPUT=""
RUN_PARAMS=""
# Command argv the verb would execute; built by nl_install_argv / nl_run_argv.
NL_ARGV=()
# install kind and artifact target of the row those argvs act on.
NL_KIND=""
NL_TARGET=""

#######################################
# nl_log helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  message
# Outputs:
#   Status via log on stderr.
# Returns:
#   0
#######################################
nl_log() { log "[nvidia-lab] $*"; }
#######################################
# nl_warn helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  message
# Outputs:
#   Status via warn on stderr.
# Returns:
#   0
#######################################
nl_warn() { warn "[nvidia-lab] $*"; }
#######################################
# nl_err helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  message
# Outputs:
#   Status via err on stderr.
# Returns:
#   0
#######################################
nl_err() { err "[nvidia-lab] $*"; }

#######################################
# Absolute path of the catalog reader module.
# Globals:
#   REPO_ROOT, NL_READER_REL
# Arguments:
#   None
# Outputs:
#   Reader path on stdout
# Returns:
#   0
#######################################
nl_reader_path() {
  printf '%s\n' "${REPO_ROOT}/${NL_READER_REL}"
}

#######################################
# Run the catalog reader. The only place the catalog is ever read.
# Globals:
#   EZ_NVIDIA_LAB_CATALOG (optional --catalog override)
# Arguments:
#   $@  reader verb and its arguments
# Outputs:
#   Reader stdout on stdout; reader stderr on stderr
# Returns:
#   Reader exit status (a missing reader module is the reader's own error)
#######################################
nl_cli() {
  local reader rc=0
  reader="$(nl_reader_path)"
  if [[ -n ${EZ_NVIDIA_LAB_CATALOG:-} ]]; then
    python3 "${reader}" --catalog "${EZ_NVIDIA_LAB_CATALOG}" "$@" || rc=$?
    return "${rc}"
  fi
  python3 "${reader}" "$@" || rc=$?
  return "${rc}"
}

#######################################
# Fetch several catalog fields for one row as key=value lines.
# Globals:
#   None (reader via nl_cli)
# Arguments:
#   $1    row id
#   $2... field keys (one reader call for all of them)
# Outputs:
#   key=value lines on stdout
# Returns:
#   0; 1 when the reader refuses the id
#######################################
nl_row_fields() {
  local id="${1}"
  shift
  local keys="${*}"
  keys="${keys// /,}"
  nl_cli fields "${id}" "${keys}"
}

#######################################
# Pull one value out of a key=value blob.
# Globals:
#   None
# Arguments:
#   $1  blob of key=value lines
#   $2  key
# Outputs:
#   Value on stdout (empty when the key carried no value)
# Returns:
#   0 when the key was present; 1 when absent
#######################################
nl_field_value() {
  local blob="${1}" key="${2}" line
  while IFS= read -r line; do
    if [[ ${line} == "${key}="* ]]; then
      printf '%s\n' "${line#"${key}="}"
      return 0
    fi
  done <<<"${blob}"
  return 1
}

#######################################
# Status of one row, refusing an id the catalog does not publish.
# Globals:
#   None (reader via nl_cli)
# Arguments:
#   $1  row id
# Outputs:
#   Status on stdout; errors on stderr
# Returns:
#   0; NL_E_REFUSE when the id is unknown or unreadable
#######################################
nl_row_status() {
  local id="${1:-}" status=""
  if [[ -z ${id} ]]; then
    nl_err "nvidia-lab needs a row id"
    return "${NL_E_USAGE}"
  fi
  status="$(nl_cli status "${id}" 2>/dev/null)" || status=""
  status="${status//[[:space:]]/}"
  if [[ -z ${status} ]]; then
    nl_err "unknown nvidia-lab id: ${id}"
    nl_err "  bazelisk run //:manage -- nvidia-lab list"
    return "${NL_E_REFUSE}"
  fi
  printf '%s\n' "${status}"
}

#######################################
# Print why a row is not installable: status, gate_notes, reopen sentence.
# Globals:
#   None (reader via nl_row_fields)
# Arguments:
#   $1  row id
#   $2  row status
# Outputs:
#   Three error lines on stderr
# Returns:
#   0
#######################################
nl_print_verdict() {
  local id="${1}" status="${2}" blob notes reopen
  blob="$(nl_row_fields "${id}" gate_notes reopen)" || blob=""
  notes="$(nl_field_value "${blob}" gate_notes)" || notes=""
  reopen="$(nl_field_value "${blob}" reopen)" || reopen=""
  nl_err "row ${id} is ${status} - the tier keeps it as a card, not an install path"
  if [[ -n ${notes} ]]; then
    nl_err "  gate_notes: ${notes}"
  fi
  if [[ -n ${reopen} ]]; then
    nl_err "  reopen: ${reopen}"
  fi
  return 0
}

#######################################
# Refuse any row whose status is not opt-in.
# Globals:
#   NL_E_REFUSE
# Arguments:
#   $1  row id
#   $2  verb label for the error line
# Outputs:
#   Errors on stderr via nl_print_verdict
# Returns:
#   0 opt-in; NL_E_REFUSE otherwise (also for an unknown id)
#######################################
nl_require_opt_in() {
  local id="${1}" verb="${2:-this verb}" status=""
  status="$(nl_row_status "${id}")" || return "${NL_E_REFUSE}"
  if [[ ${status} != "opt-in" ]]; then
    nl_err "refusing to ${verb}: status is ${status}"
    nl_print_verdict "${id}" "${status}"
    return "${NL_E_REFUSE}"
  fi
  return 0
}

#######################################
# Reject an id that could escape the lab home or is not kebab-case.
# Globals:
#   None
# Arguments:
#   $1  row id
# Outputs:
#   Error on stderr
# Returns:
#   0 valid; 1 invalid
#######################################
nl_valid_id() {
  local id="${1:-}"
  if [[ ! ${id} =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    nl_err "invalid nvidia-lab id: ${id:-<empty>} (want kebab-case a-z 0-9 -)"
    return 1
  fi
  return 0
}

#######################################
# Root the tier installs its artifacts under (never the repo, never a bind).
# Globals:
#   EZ_NVIDIA_LAB_HOME, HOME
# Arguments:
#   None
# Outputs:
#   Absolute directory on stdout
# Returns:
#   0
#######################################
nl_lab_home() {
  printf '%s\n' "${EZ_NVIDIA_LAB_HOME:-${HOME:-/root}/.ez-comfy/nvidia-lab}"
}

#######################################
# Absolute clone target for one git-clone row.
# Globals:
#   EZ_NVIDIA_LAB_HOME, HOME
# Arguments:
#   $1  row id
# Outputs:
#   Absolute directory on stdout
# Returns:
#   0
#######################################
nl_clone_dir() {
  local id="${1}"
  printf '%s/%s\n' "$(nl_lab_home)" "${id}"
}

#######################################
# Build the install argv for a row and record its kind and target.
# A published cmd always wins; otherwise docker-pull pulls artifact_ref and
# git-clone clones it into the lab home. pip-install and none refuse.
# Globals:
#   NL_ARGV (rewritten), NL_KIND, NL_TARGET
# Arguments:
#   $1  row id (must already be opt-in)
# Outputs:
#   Errors on stderr for a kind this CLI will not run
# Returns:
#   0; NL_E_REFUSE when the kind or the ref is unusable
#######################################
nl_install_argv() {
  local id="${1}" blob cmd ref
  NL_ARGV=()
  NL_KIND=""
  NL_TARGET=""
  blob="$(nl_row_fields "${id}" install artifact_ref cmd)" || blob=""
  NL_KIND="$(nl_field_value "${blob}" install)" || NL_KIND=""
  ref="$(nl_field_value "${blob}" artifact_ref)" || ref=""
  cmd="$(nl_field_value "${blob}" cmd)" || cmd=""
  case "${NL_KIND}" in
    docker-pull | git-clone) ;;
    pip-install)
      nl_err "row ${id} is install=pip-install - this CLI will not pip-install into the Comfy image env"
      nl_err "  build it in its own venv by hand; the reason is in gate_notes"
      return "${NL_E_REFUSE}"
      ;;
    none)
      nl_err "row ${id} is install=none - there is no artifact to place on this host"
      return "${NL_E_REFUSE}"
      ;;
    *)
      nl_err "row ${id} has an unusable install kind: ${NL_KIND:-<empty>}"
      return "${NL_E_REFUSE}"
      ;;
  esac
  if [[ -n ${cmd} ]]; then
    read -r -a NL_ARGV <<<"${cmd}" || true
  elif [[ -z ${ref} ]]; then
    nl_err "row ${id} is ${NL_KIND} with no artifact_ref - nothing to place on this host"
    return "${NL_E_REFUSE}"
  elif [[ ${NL_KIND} == "docker-pull" ]]; then
    NL_ARGV=(docker pull "${ref}")
  else
    NL_ARGV=(git clone "${ref}" "$(nl_clone_dir "${id}")")
  fi
  if [[ ${#NL_ARGV[@]} -eq 0 ]]; then
    nl_err "row ${id} publishes a cmd that resolves to no argv"
    return "${NL_E_REFUSE}"
  fi
  if [[ ${NL_KIND} == "git-clone" ]]; then
    NL_TARGET="$(nl_clone_dir "${id}")"
  else
    NL_TARGET="${ref}"
  fi
  return 0
}

#######################################
# Build the run argv for a row: its published cmd plus the input and params.
# Globals:
#   NL_ARGV (rewritten), NL_KIND, NL_TARGET
# Arguments:
#   $1  row id (must already be opt-in)
#   $2  input path (must exist)
#   $3  params JSON (may be empty)
# Outputs:
#   Errors on stderr when the row publishes no cmd or the input is missing
# Returns:
#   0; NL_E_USAGE for a missing input; NL_E_REFUSE for a row with no cmd
#######################################
nl_run_argv() {
  local id="${1}" input="${2:-}" params="${3:-}" blob cmd
  NL_ARGV=()
  if [[ -z ${input} ]]; then
    nl_err "run needs --input PATH"
    return "${NL_E_USAGE}"
  fi
  if [[ ! -e ${input} ]]; then
    nl_err "input not found: ${input}"
    return "${NL_E_USAGE}"
  fi
  blob="$(nl_row_fields "${id}" cmd install)" || blob=""
  cmd="$(nl_field_value "${blob}" cmd)" || cmd=""
  NL_KIND="$(nl_field_value "${blob}" install)" || NL_KIND=""
  NL_TARGET=""
  if [[ -z ${cmd} ]]; then
    nl_err "row ${id} publishes no cmd - run refuses until upstream documents one"
    nl_err "  bazelisk run //:manage -- nvidia-lab plan ${id}"
    return "${NL_E_REFUSE}"
  fi
  read -r -a NL_ARGV <<<"${cmd}" || true
  if [[ ${#NL_ARGV[@]} -eq 0 ]]; then
    nl_err "row ${id} publishes a cmd that resolves to no argv"
    return "${NL_E_REFUSE}"
  fi
  NL_ARGV+=(--input "${input}")
  if [[ -n ${params} ]]; then
    NL_ARGV+=(--params "${params}")
  fi
  return 0
}

#######################################
# Join the built argv into the one line the operator sees.
# Globals:
#   NL_ARGV
# Arguments:
#   None
# Outputs:
#   Command line on stdout (nothing when argv is empty)
# Returns:
#   0
#######################################
nl_print_argv() {
  local out="" arg
  if [[ ${#NL_ARGV[@]} -eq 0 ]]; then
    return 0
  fi
  for arg in "${NL_ARGV[@]}"; do
    if [[ -n ${out} ]]; then
      out="${out} ${arg}"
    else
      out="${arg}"
    fi
  done
  printf '%s\n' "${out}"
}

#######################################
# Execute the built argv as-is: no shell, no eval, no globbing.
# Globals:
#   NL_ARGV
# Arguments:
#   None
# Outputs:
#   Child output
# Returns:
#   Child status; NL_E_USAGE when argv is empty
#######################################
nl_exec_argv() {
  if [[ ${#NL_ARGV[@]} -eq 0 ]]; then
    nl_err "nothing to execute"
    return "${NL_E_USAGE}"
  fi
  "${NL_ARGV[@]}"
}

#######################################
# Refuse while occupancy holds the one heavy GPU job.
# A heavy mode is a claim on its own; a desk mode claims only while its sidecar
# lives, which occupancy_desk_held decides from the recorded PIDs.
# Globals:
#   NL_HEAVY_MODES, occupancy_mode, occupancy_desk_held (scripts/lib/occupancy.sh)
# Arguments:
#   $1  verb label for the error line
# Outputs:
#   Errors on stderr when refused
# Returns:
#   0 allowed; NL_E_REFUSE refused
#######################################
nl_refuse_heavy_occupancy() {
  local verb="${1:-this verb}" mode heavy
  mode="$(occupancy_mode)"
  for heavy in "${NL_HEAVY_MODES[@]}"; do
    if [[ ${mode} == "${heavy}" ]]; then
      nl_err "occupancy is ${mode} - one heavy GPU job at a time; finish it before ${verb}"
      nl_err "  bazelisk run //:manage -- occupancy enter idle --yes"
      return "${NL_E_REFUSE}"
    fi
  done
  if declare -F occupancy_desk_held >/dev/null 2>&1 && occupancy_desk_held "${mode}"; then
    nl_err "occupancy is ${mode} with a live sidecar - unified memory is busy before ${verb}"
    nl_err "  bazelisk run //:manage -- occupancy enter idle --yes"
    return "${NL_E_REFUSE}"
  fi
  return 0
}

#######################################
# The three gates a GPU job outside the Comfy process has to pass.
# Heavy confirm, then the host headroom preflight, then the occupancy XOR.
# Globals:
#   NL_E_DECLINED, NL_E_REFUSE, require_heavy_confirm, check_host_headroom
# Arguments:
#   $1  label for the confirm banner
# Outputs:
#   Confirm banner and errors on stderr
# Returns:
#   0; NL_E_DECLINED confirm refused; NL_E_REFUSE headroom or occupancy
#######################################
nl_gate_heavy_work() {
  local label="${1:-nvidia-lab workload}"
  if ! require_heavy_confirm "${label}" \
    "These rows run on the same GB10 outside the Comfy process."; then
    return "${NL_E_DECLINED}"
  fi
  if ! check_host_headroom; then
    nl_err "host headroom preflight failed - not starting ${label}"
    return "${NL_E_REFUSE}"
  fi
  nl_refuse_heavy_occupancy "${label}" || return "${NL_E_REFUSE}"
  return 0
}

#######################################
# Print usage.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  cat >&2 <<'EOF'
Usage:
  bazelisk run //:manage -- nvidia-lab list
  bazelisk run //:manage -- nvidia-lab status ID
  bazelisk run //:manage -- nvidia-lab plan ID
  bazelisk run //:manage -- nvidia-lab install ID
  bazelisk run //:manage -- nvidia-lab uninstall ID
  bazelisk run //:manage -- nvidia-lab run ID --input PATH [--params JSON]
  bazelisk run //:manage -- nvidia-lab check

  Opt-in NVIDIA lab tier. Nothing downloads until you install an opt-in row.
  install and run ask the heavy confirm, check host headroom, and refuse while
  a heavy occupancy mode holds the GPU. run prints its command and only
  executes it with EZ_NVIDIA_LAB_EXECUTE=1: the tier is unverified on GB10.
  Artifacts land under ~/.ez-comfy/nvidia-lab/ID, never in the repo.
  Exit: 2 refuse, 5 heavy confirm declined.
EOF
  return 0
}

#######################################
# List every catalog row as id, status, title.
# Globals:
#   NL_E_USAGE
# Arguments:
#   None
# Outputs:
#   Reader list on stdout
# Returns:
#   0; NL_E_USAGE when the reader fails
#######################################
cmd_list() {
  local rc=0
  nl_cli list || rc=$?
  if [[ ${rc} -ne 0 ]]; then
    nl_err "could not read the nvidia-lab catalog (rc ${rc})"
    return "${NL_E_USAGE}"
  fi
  return 0
}

#######################################
# Print one row's status.
# Globals:
#   None
# Arguments:
#   $1  row id
# Outputs:
#   status ID: STATUS on stdout
# Returns:
#   0; NL_E_REFUSE unknown id
#######################################
cmd_status() {
  local id="${1:-}" status=""
  status="$(nl_row_status "${id}")" || return "${NL_E_REFUSE}"
  printf 'status %s: %s\n' "${id}" "${status}"
  return 0
}

#######################################
# Print what install would fetch, without fetching or confirming anything.
# Globals:
#   NL_ARGV, NL_KIND, NL_TARGET
# Arguments:
#   $1  row id
# Outputs:
#   Plan lines on stdout; the verdict on stderr for a non-opt-in row
# Returns:
#   0; NL_E_REFUSE unknown id
#######################################
cmd_plan() {
  local id="${1:-}" status="" blob install ref vram disk
  status="$(nl_row_status "${id}")" || return "${NL_E_REFUSE}"
  blob="$(nl_row_fields "${id}" install artifact_ref vram_gb disk_gb)" || blob=""
  install="$(nl_field_value "${blob}" install)" || install=""
  ref="$(nl_field_value "${blob}" artifact_ref)" || ref=""
  vram="$(nl_field_value "${blob}" vram_gb)" || vram=""
  disk="$(nl_field_value "${blob}" disk_gb)" || disk=""
  printf 'id: %s\n' "${id}"
  printf 'status: %s\n' "${status}"
  printf 'install: %s\n' "${install:-none}"
  case "${install}" in
    docker-pull)
      printf 'target: %s\n' "${ref}"
      ;;
    git-clone)
      printf 'source: %s\n' "${ref}"
      printf 'target: %s\n' "$(nl_clone_dir "${id}")"
      ;;
    *)
      printf 'target: none - this row places nothing on this host\n'
      ;;
  esac
  printf 'vram_gb: %s\n' "${vram:-0}"
  printf 'disk_gb: %s\n' "${disk:-0}"
  if [[ ${status} != "opt-in" ]]; then
    nl_print_verdict "${id}" "${status}"
    return 0
  fi
  if nl_install_argv "${id}"; then
    printf 'command: %s\n' "$(nl_print_argv)"
  fi
  return 0
}

#######################################
# Place one opt-in row's artifact on the host.
# Globals:
#   NL_ARGV, NL_KIND, NL_TARGET
# Arguments:
#   $1  row id
# Outputs:
#   Progress on stderr; child output
# Returns:
#   0; NL_E_REFUSE refused; NL_E_DECLINED confirm declined; child status otherwise
#######################################
cmd_install() {
  local id="${1:-}" dir
  nl_require_opt_in "${id}" "install ${id}" || return "${NL_E_REFUSE}"
  nl_gate_heavy_work "nvidia-lab install ${id}" || return $?
  nl_install_argv "${id}" || return "${NL_E_REFUSE}"
  if [[ ${NL_KIND} == "git-clone" ]]; then
    dir="$(dirname "${NL_TARGET}")"
    if [[ ! -d ${NL_TARGET} ]]; then
      mkdir -p "${dir}" || return 1
    fi
  fi
  nl_log "installing ${id}: $(nl_print_argv)"
  nl_exec_argv
}

#######################################
# Remove one opt-in row's host artifact.
# Only a git-clone checkout under the lab home is ever deleted: a pulled image
# is shared, so the operator removes it themselves.
# Globals:
#   NL_E_REFUSE
# Arguments:
#   $1  row id
# Outputs:
#   Progress on stderr
# Returns:
#   0; NL_E_REFUSE refused or refused to delete a shared image
#######################################
cmd_uninstall() {
  local id="${1:-}" kind="" target home
  nl_require_opt_in "${id}" "uninstall ${id}" || return "${NL_E_REFUSE}"
  target="$(nl_clone_dir "${id}")"
  home="$(nl_lab_home)"
  kind="$(nl_row_fields "${id}" install)" || kind=""
  kind="$(nl_field_value "${kind}" install)" || kind=""
  if [[ ${target} != "${home%/}/${id}" ]]; then
    nl_err "refusing to remove ${target}: it is not the lab-home checkout of ${id}"
    return "${NL_E_REFUSE}"
  fi
  case "${kind}" in
    git-clone)
      if [[ ! -d ${target} ]]; then
        nl_log "nothing installed for ${id} at ${target}"
        return 0
      fi
      nl_log "removing ${target}"
      rm -rf -- "${target}"
      return 0
      ;;
    docker-pull)
      nl_err "refusing to uninstall ${id}: a pulled image is shared on this host"
      nl_err "  remove it yourself with docker rmi when you are sure nothing else uses it"
      return "${NL_E_REFUSE}"
      ;;
    *)
      nl_err "refusing to uninstall ${id}: install kind ${kind:-<empty>} placed nothing here"
      return "${NL_E_REFUSE}"
      ;;
  esac
}

#######################################
# Print the command a row would run; execute it only on an explicit opt-in.
# Globals:
#   NL_ARGV, EZ_NVIDIA_LAB_EXECUTE
# Arguments:
#   $1  row id
#   $2  input path
#   $3  params JSON (may be empty)
# Outputs:
#   The exact command on stdout; child output in execute mode
# Returns:
#   0; NL_E_REFUSE refused; NL_E_DECLINED confirm declined; NL_E_USAGE input;
#   child status in execute mode
#######################################
cmd_run() {
  local id="${1:-}" input="${2:-}" params="${3:-}" line
  nl_require_opt_in "${id}" "run ${id}" || return "${NL_E_REFUSE}"
  if [[ ! -e ${input} ]]; then
    nl_err "input not found: ${input}"
    return "${NL_E_USAGE}"
  fi
  nl_gate_heavy_work "nvidia-lab run ${id}" || return $?
  nl_run_argv "${id}" "${input}" "${params}" || return $?
  line="$(nl_print_argv)"
  if [[ ${EZ_NVIDIA_LAB_EXECUTE:-0} != "1" ]]; then
    nl_log "unverified on GB10 - printing the command without running it"
    printf 'would run: %s\n' "${line}"
    printf 'set EZ_NVIDIA_LAB_EXECUTE=1 to execute it\n'
    return 0
  fi
  nl_log "executing ${id}: ${line}"
  nl_exec_argv
}

#######################################
# Validate the catalog through the reader.
# Globals:
#   NL_E_USAGE
# Arguments:
#   None
# Outputs:
#   Reader verdict on stdout; errors on stderr
# Returns:
#   0 when the reader reports ok; NL_E_USAGE otherwise
#######################################
cmd_check() {
  local rc=0
  nl_cli check || rc=$?
  if [[ ${rc} -ne 0 ]]; then
    nl_err "nvidia-lab catalog check failed (rc ${rc})"
    return "${NL_E_USAGE}"
  fi
  return 0
}

#######################################
# Parse argv into globals; the verb always comes first.
# Globals:
#   CMD, TOOL_ID, RUN_INPUT, RUN_PARAMS
# Arguments:
#   $@  CLI arguments
# Outputs:
#   Help or errors on stderr
# Returns:
#   0; NL_E_USAGE on a bad verb, a missing id, or a bad flag
#######################################
parse_args() {
  if [[ $# -eq 0 ]]; then
    cmd_help
    return "${NL_E_USAGE}"
  fi
  CMD="${1}"
  shift
  case "${CMD}" in
    list | check)
      if [[ $# -gt 0 ]]; then
        nl_err "nvidia-lab ${CMD} takes no arguments"
        return "${NL_E_USAGE}"
      fi
      return 0
      ;;
    help | -h | --help)
      CMD="help"
      return 0
      ;;
    status | plan | install | uninstall | run) ;;
    *)
      nl_err "unknown nvidia-lab verb: ${CMD}"
      cmd_help
      return "${NL_E_USAGE}"
      ;;
  esac
  if [[ $# -eq 0 ]]; then
    nl_err "nvidia-lab ${CMD} needs a row id"
    return "${NL_E_USAGE}"
  fi
  TOOL_ID="${1}"
  shift
  nl_valid_id "${TOOL_ID}" || return "${NL_E_USAGE}"
  if [[ ${CMD} == "run" ]]; then
    while [[ $# -gt 0 ]]; do
      case "${1}" in
        --input)
          if [[ $# -lt 2 || -z ${2:-} ]]; then
            nl_err "--input needs a path"
            return "${NL_E_USAGE}"
          fi
          RUN_INPUT="${2}"
          shift 2
          ;;
        --params)
          if [[ $# -lt 2 ]]; then
            nl_err "--params needs a JSON string"
            return "${NL_E_USAGE}"
          fi
          RUN_PARAMS="${2}"
          shift 2
          ;;
        -h | --help)
          CMD="help"
          return 0
          ;;
        *)
          nl_err "unknown nvidia-lab argument: ${1}"
          return "${NL_E_USAGE}"
          ;;
      esac
    done
    if [[ -z ${RUN_INPUT} ]]; then
      nl_err "nvidia-lab run ${TOOL_ID} needs --input PATH"
      return "${NL_E_USAGE}"
    fi
  elif [[ $# -gt 0 ]]; then
    nl_err "nvidia-lab ${CMD} takes only a row id"
    return "${NL_E_USAGE}"
  fi
  return 0
}

#######################################
# main helper.
# Globals:
#   CMD, TOOL_ID, RUN_INPUT, RUN_PARAMS
# Arguments:
#   $@  CLI arguments
# Outputs:
#   Verb output
# Returns:
#   Verb status
#######################################
main() {
  parse_args "$@" || return $?
  case "${CMD}" in
    help) cmd_help ;;
    list) cmd_list ;;
    status) cmd_status "${TOOL_ID}" ;;
    plan) cmd_plan "${TOOL_ID}" ;;
    install) cmd_install "${TOOL_ID}" ;;
    uninstall) cmd_uninstall "${TOOL_ID}" ;;
    run) cmd_run "${TOOL_ID}" "${RUN_INPUT}" "${RUN_PARAMS}" ;;
    check) cmd_check ;;
    *)
      nl_err "unknown nvidia-lab verb: ${CMD}"
      return "${NL_E_USAGE}"
      ;;
  esac
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
