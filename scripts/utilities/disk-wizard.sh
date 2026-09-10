#!/usr/bin/env bash
#
# ## disk-wizard
#
# Guided, plan-first reclaim for leftover AI experiment files on a DGX Spark.
# Does not overload manage.sh cleanup (volume-only) or reap-models (MODELS_DIR).
#
# Usage:
#   ./scripts/utilities/disk-wizard.sh --plan
#   ./scripts/utilities/disk-wizard.sh --json
#   ./scripts/utilities/disk-wizard.sh --apply --yes
#   ./scripts/utilities/disk-wizard.sh restore --from .disk-quarantine/<utc>
#
# Safety:
#   Default is --plan (read-only). --apply requires --yes.
#   Review-class items quarantine. Dangerous / keep-set / ez-comfy-state refused.
#   Never offers docker system prune -a --volumes.
#   Does not weaken restart: no, start confirm, headroom, or download-limit.
#
# @command disk-wizard

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/models.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/models.sh"
# shellcheck source=../lib/disk_scan.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/disk_scan.sh"

MODE="${MODE:-}"
YES=0
RESTORE_FROM=""
JSON_FLAG=0
FORCE=0

#######################################
# Print usage to stderr.
# Arguments:
#   None
# Returns:
#   0
#######################################
disk_wizard_usage() {
  echo "Usage: $0 --plan | --json | --apply --yes | restore --from DIR" >&2
  echo "Default without a TTY is --plan. cleanup does not delete weights." >&2
  echo "Never runs docker system prune -a --volumes." >&2
}

#######################################
# Parse CLI.
# Globals:
#   MODE, YES, RESTORE_FROM, JSON_FLAG, FORCE
# Arguments:
#   $@
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --plan) MODE="plan" ;;
      --json)
        JSON_FLAG=1
        MODE="${MODE:-plan}"
        ;;
      --apply) MODE="apply" ;;
      --yes | -y) YES=1 ;;
      restore) MODE="restore" ;;
      --from)
        RESTORE_FROM="${2:?}"
        shift
        ;;
      --force) FORCE=1 ;;
      -h | --help)
        disk_wizard_usage
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        disk_wizard_usage
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# True when stdin is a TTY.
# Returns:
#   0 tty
#######################################
disk_is_tty() {
  [[ -t 0 ]]
}

#######################################
# Append a log line to MODELS_DIR / COMFY_OUTPUT_DIR wizard logs.
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR
# Arguments:
#   $@  message
#######################################
disk_log() {
  local line msg dest
  msg="$*"
  line="$(date -u +%Y-%m-%dT%H:%M:%SZ) ${msg}"
  for dest in "${MODELS_DIR:-}/.disk-wizard.log" "${COMFY_OUTPUT_DIR:-}/.disk-wizard.log"; do
    if [[ -n ${dest} && ${dest} != /.disk-wizard.log && -d $(dirname "${dest}") ]]; then
      printf '%s\n' "${line}" >>"${dest}" 2>/dev/null || true
    fi
  done
  log "${msg}"
}

#######################################
# Path to the last written plan JSON.
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR
# Outputs:
#   path
# Returns:
#   0
#######################################
disk_plan_file() {
  if [[ -n ${MODELS_DIR:-} && -d ${MODELS_DIR} ]]; then
    echo "${MODELS_DIR}/.disk-wizard-plan.json"
    return 0
  fi
  echo "${COMFY_OUTPUT_DIR:-.}/.disk-wizard-plan.json"
}

#######################################
# Catalog / manifest paths.
# Outputs:
#   catalog path
#######################################
disk_catalog_path() {
  echo "${REPO_ROOT}/config/disk-catalog.yaml"
}

#######################################
# Rank file paths via disk_catalog.py.
# Globals:
#   REPO_ROOT, MODELS_DIR
# Arguments:
#   None (reads JSONL on stdin)
# Outputs:
#   JSON array
# Returns:
#   python status
#######################################
disk_rank_candidates() {
  python3 "${REPO_ROOT}/scripts/lib/disk_catalog.py" \
    --catalog "$(disk_catalog_path)" \
    --manifest "$(models_manifest_path)" \
    rank
}

#######################################
# Build JSONL of walked files plus docker mock objects.
# One Python walk for all roots (stderr progress); docker objects appended.
# Globals:
#   REPO_ROOT, DISK_WIZARD_MAX_DEPTH
# Outputs:
#   JSONL on stdout; scan progress on stderr
# Returns:
#   0
#######################################
disk_survey_jsonl() {
  local depth root docker_blob
  local -a roots=()
  depth="${DISK_WIZARD_MAX_DEPTH:-6}"
  while IFS= read -r root; do
    [[ -z ${root} ]] && continue
    roots+=("${root}")
  done < <(disk_allowed_roots)

  if [[ ${#roots[@]} -gt 0 ]]; then
    python3 "${REPO_ROOT}/scripts/lib/disk_catalog.py" \
      --catalog "$(disk_catalog_path)" \
      walk \
      --max-depth "${depth}" \
      -- "${roots[@]}"
  fi

  log "Querying Docker disk usage (docker system df; can take a while)…"
  docker_blob="$(disk_docker_df || true)"
  if [[ -n ${docker_blob} ]]; then
    python3 -c '
import json,sys
raw=sys.argv[1].strip()
if not raw:
    raise SystemExit(0)
for line in raw.splitlines():
    line=line.strip()
    if not line:
        continue
    try:
        obj=json.loads(line)
    except json.JSONDecodeError:
        continue
    dtype=str(obj.get("type") or obj.get("Type") or obj.get("docker_type") or "")
    ident=str(obj.get("id") or obj.get("ID") or obj.get("path") or dtype or "docker")
    size=int(obj.get("size_bytes") or obj.get("Size") or 0)
    if not dtype:
        dtype="build-cache"
    path="docker://"+dtype+"/"+ident
    print(json.dumps({"path": path, "size_bytes": size, "broken_symlink": False}))
' "${docker_blob}"
  fi
}

#######################################
# Run survey + rank; write plan file; print human or JSON.
# Globals:
#   JSON_FLAG
# Outputs:
#   Progress on stderr; human plan or JSON on stdout
# Returns:
#   0
#######################################
disk_survey() {
  local ranked dest jsonl n
  log "Starting read-only disk survey (can take a while on a full host; nothing is deleted)…"
  disk_df_report >&2 || true
  jsonl="$(disk_survey_jsonl)"
  n=0
  if [[ -n ${jsonl} ]]; then
    n="$(printf '%s\n' "${jsonl}" | grep -c . || true)"
  fi
  log "Ranking ${n} candidates…"
  ranked="$(printf '%s\n' "${jsonl}" | disk_rank_candidates)"
  dest="$(disk_plan_file)"
  printf '%s\n' "${ranked}" >"${dest}"
  log "Plan written to ${dest}"
  if [[ ${JSON_FLAG} -eq 1 ]]; then
    printf '%s\n' "${ranked}"
    return 0
  fi
  disk_print_plan "${ranked}"
}

#######################################
# Human plan: grouped A/B/C.
# Arguments:
#   $1  JSON array
#######################################
disk_print_plan() {
  local json="${1}"
  python3 -c '
import json, sys

rows = json.load(sys.stdin)

def gib(n):
    return "%.2f GiB" % (n / 1024 / 1024 / 1024)

steps = {
    "A": "Step A - safe junk (default accept on apply)",
    "B": "Step B - review leftovers (default skip; quarantine if selected)",
    "C": "Step C - will not touch (keep-set, volumes, in-use)",
}
for step in ("A", "B", "C"):
    group = [r for r in rows if r.get("step") == step]
    print("")
    print(steps[step])
    if not group:
        print("  (none)")
        continue
    for r in group:
        risk = r.get("risk")
        ident = r.get("id")
        path = r.get("path")
        what = r.get("what")
        why = r.get("why")
        when = r.get("leftover_when")
        reclaim = r.get("reclaim")
        size = gib(int(r.get("size_bytes") or 0))
        print("  [%s] %s  %s  %s" % (risk, size, ident, path))
        print("      what: %s" % what)
        print("      why:  %s" % why)
        print("      risk: %s  reclaim=%s" % (when, reclaim))
' <<<"${json}"
}

#######################################
# Interactive numbered wizard (TTY). Writes plan then prompts.
# Globals:
#   PLAN_JSON, YES
# Returns:
#   0; 1 abort
#######################################
disk_wizard_steps() {
  disk_survey
  if [[ ${JSON_FLAG} -eq 1 ]]; then
    return 0
  fi
  echo >&2
  echo "Step A items are safe junk. Step B is skipped unless you pass --apply after editing the plan." >&2
  echo "This invocation is guidance + plan only. Re-run with --apply --yes to act." >&2
}

#######################################
# Refuse apply when hf pid, unless --force.
# Globals:
#   FORCE
# Returns:
#   0 ok; 1 refuse
#######################################
disk_apply_guards() {
  if disk_hf_pid_present && [[ ${FORCE} -eq 0 ]]; then
    err "hf download appears to be running; refuse --apply (use --force to override)"
    return 1
  fi
  return 0
}

#######################################
# Quarantine destination for a path.
# Arguments:
#   $1  path
#   $2  utc stamp
# Outputs:
#   dest dir
#######################################
disk_quarantine_base() {
  local path="${1}"
  local stamp="${2}"
  local models real
  models="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${MODELS_DIR}")"
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${path}")"
  case "${real}/" in
    "${models}/"*)
      echo "${MODELS_DIR}/.disk-quarantine/${stamp}"
      return 0
      ;;
  esac
  if [[ -n ${COMFY_OUTPUT_DIR:-} && -d ${COMFY_OUTPUT_DIR} ]]; then
    echo "${COMFY_OUTPUT_DIR}/.disk-quarantine/${stamp}"
    return 0
  fi
  echo "${HOME}/.ez-comfy-disk-quarantine/${stamp}"
}

#######################################
# Move one path into quarantine.
# Arguments:
#   $1  class/id
#   $2  path
# Returns:
#   0
#######################################
disk_quarantine_one() {
  local class="${1}"
  local path="${2}"
  local stamp dest rel
  disk_realpath_under_any "${path}" >/dev/null || return 1
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dest="$(disk_quarantine_base "${path}" "${stamp}")"
  mkdir -p "${dest}"
  rel="$(basename "${path}")"
  mkdir -p "$(dirname "${dest}/${rel}")"
  mv "${path}" "${dest}/${rel}"
  printf '{"path":"%s","class":"%s"}\n' "${path}" "${class}" >>"${dest}/MANIFEST.jsonl"
  disk_log "quarantine ${class} ${path} -> ${dest}"
}

#######################################
# Delete one junk path.
# Arguments:
#   $1  class
#   $2  path
# Returns:
#   0
#######################################
disk_delete_one() {
  local class="${1}"
  local path="${2}"
  disk_realpath_under_any "${path}" >/dev/null || return 1
  if models_is_keep_file "$(basename "${path}")"; then
    log "keep-set, skip ${path}"
    return 0
  fi
  rm -f "${path}"
  disk_log "delete ${class} ${path}"
}

#######################################
# Apply one ranked row.
# Globals:
#   FORCE
# Arguments:
#   $1  JSON object
# Returns:
#   0; 1 skip/refuse
#######################################
disk_apply_one() {
  local row="${1}"
  local risk reclaim path id
  risk="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("risk",""))' "${row}")"
  reclaim="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("reclaim",""))' "${row}")"
  path="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("path",""))' "${row}")"
  id="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("id",""))' "${row}")"
  if [[ ${risk} == dangerous || ${reclaim} == none ]]; then
    log "skip ${id} ${path} (will not touch)"
    return 0
  fi
  if [[ ${path} == docker://* ]]; then
    log "skip docker object ${path} (plan-only in v1; prune manually after review)"
    return 0
  fi
  if models_is_keep_file "$(basename "${path}")" && [[ ${id} != hf-incomplete ]]; then
    log "keep-set, skip ${path}"
    return 0
  fi
  case "${reclaim}" in
    delete)
      disk_delete_one "${id}" "${path}"
      ;;
    quarantine | reap-models | hf-prune)
      disk_quarantine_one "${id}" "${path}"
      ;;
    docker-prune)
      log "skip docker-prune ${path} (not auto-applied)"
      ;;
    *)
      log "skip ${id} ${path}"
      ;;
  esac
}

#######################################
# Apply Step A (safe) from the plan file. Step B only if DISK_WIZARD_STEP_B=1.
# Globals:
#   YES, DISK_WIZARD_STEP_B
# Returns:
#   0; 1 missing --yes
#######################################
disk_apply() {
  local dest row risk
  disk_apply_guards || return 1
  if [[ ${YES} -ne 1 ]]; then
    err "--apply requires --yes"
    return 1
  fi
  dest="$(disk_plan_file)"
  if [[ ! -s ${dest} ]]; then
    disk_survey >/dev/null
  fi
  dest="$(disk_plan_file)"
  python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "${dest}"
  while IFS= read -r row; do
    [[ -z ${row} ]] && continue
    risk="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("risk",""))' "${row}")"
    if [[ ${risk} == safe ]]; then
      disk_apply_one "${row}"
      continue
    fi
    if [[ ${risk} == review && ${DISK_WIZARD_STEP_B:-0} == "1" ]]; then
      disk_apply_one "${row}"
    fi
  done < <(python3 -c 'import json,sys
for r in json.load(open(sys.argv[1])):
    print(json.dumps(r))
' "${dest}")
}

#######################################
# Restore files from a quarantine tree.
# Globals:
#   RESTORE_FROM, MODELS_DIR
# Returns:
#   0; 1 missing
#######################################
disk_restore() {
  local src="${RESTORE_FROM}"
  [[ ${src} == /* ]] || src="${MODELS_DIR}/${src}"
  [[ -d ${src} ]] || {
    err "missing quarantine ${src}"
    return 1
  }
  local f rel
  while IFS= read -r f; do
    rel="$(basename "${f}")"
    [[ ${rel} == MANIFEST.jsonl ]] && continue
    mv "${f}" "${MODELS_DIR}/${rel}"
    disk_log "restore ${rel}"
  done < <(find "${src}" -type f ! -name MANIFEST.jsonl)
}

#######################################
# JSON report wrapper (same as --json plan).
# Returns:
#   0
#######################################
disk_json_report() {
  JSON_FLAG=1
  disk_survey
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@
#######################################
main() {
  parse_args "$@"
  MODELS_DIR="${MODELS_DIR:-/mnt/models}"
  export MODELS_DIR
  COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
  export COMFY_OUTPUT_DIR
  if [[ -z ${MODE} ]]; then
    if disk_is_tty; then
      MODE="wizard"
    else
      MODE="plan"
    fi
  fi
  case "${MODE}" in
    plan) disk_survey ;;
    wizard) disk_wizard_steps ;;
    apply) disk_apply ;;
    restore) disk_restore ;;
    *)
      err "Unknown mode ${MODE}"
      disk_wizard_usage
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
