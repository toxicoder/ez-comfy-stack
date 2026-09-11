#!/usr/bin/env bash
#
# ## reap-models
#
# Plan/apply/restore model cache cleanup. Never overloaded as manage.sh cleanup.
#
# Usage:
#   ./scripts/utilities/reap-models.sh --plan
#   ./scripts/utilities/reap-models.sh --apply --class junk --yes
#   ./scripts/utilities/reap-models.sh --apply --class superseded --quarantine --yes
#   ./scripts/utilities/reap-models.sh --drop-pack triposplat --quarantine --yes
#   ./scripts/utilities/reap-models.sh restore --from .reap-quarantine/<utc>
#   ./scripts/utilities/reap-models.sh drop-quarantine --older-than 14d --yes
#
# Safety:
#   --plan is default. --apply requires --yes.
#   Refuses unsafe MODELS_DIR, path escape, compose-up (except junk), hf PID.
#   Does not delete shared keep-set files (flux2-vae, ACE-Step AIO).
#
# @command reap-models

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

MODE="${MODE:-plan}"
CLASS="junk,superseded,banned"
YES=0
QUARANTINE=0
I_FOREIGN=0
I_SHARED=0
DROP_PACK=""
RESTORE_FROM=""
OLDER_THAN=""
FORCE=0

#######################################
# Parse CLI.
# Globals:
#   MODE, CLASS, YES, QUARANTINE, I_FOREIGN, DROP_PACK, RESTORE_FROM, OLDER_THAN, FORCE
# Arguments:
#   $@
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --plan) MODE="plan" ;;
      --apply) MODE="apply" ;;
      --class)
        CLASS="${2:?}"
        shift
        ;;
      --yes | -y) YES=1 ;;
      --quarantine) QUARANTINE=1 ;;
      --i-foreign) I_FOREIGN=1 ;;
      --i-shared-cache) I_SHARED=1 ;;
      --drop-pack)
        MODE="drop-pack"
        DROP_PACK="${2:?}"
        shift
        ;;
      restore)
        MODE="restore"
        ;;
      --from)
        RESTORE_FROM="${2:?}"
        shift
        ;;
      drop-quarantine)
        MODE="drop-quarantine"
        ;;
      --older-than)
        OLDER_THAN="${2:?}"
        shift
        ;;
      --force) FORCE=1 ;;
      -h | --help)
        echo "Usage: $0 --plan | --apply --class junk|superseded|banned [--quarantine] --yes" >&2
        echo "       $0 --drop-pack NAME [--quarantine] --yes" >&2
        echo "       $0 restore --from .reap-quarantine/<utc>" >&2
        echo "       $0 drop-quarantine --older-than 14d --yes" >&2
        echo "Default is --plan (no delete). cleanup (manage.sh) does not delete weights." >&2
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# True if CLASS csv contains a token.
# Arguments:
#   $1  token
# Returns:
#   0 if selected
#######################################
class_selected() {
  local tok="${1}"
  [[ ,${CLASS}, == *",${tok},"* ]]
}

#######################################
# Log a reap action.
# Globals:
#   MODELS_DIR, COMFY_OUTPUT_DIR
# Arguments:
#   $@  message
#######################################
reap_log() {
  local line msg
  msg="$*"
  mkdir -p "${MODELS_DIR}"
  line="$(date -u +%Y-%m-%dT%H:%M:%SZ) ${msg}"
  printf '%s\n' "${line}" >>"${MODELS_DIR}/.reap-log"
  if [[ -n ${COMFY_OUTPUT_DIR:-} && -d ${COMFY_OUTPUT_DIR} ]]; then
    printf '%s\n' "${line}" >>"${COMFY_OUTPUT_DIR}/.reap-models.log"
  fi
  log "${msg}"
}

#######################################
# Guards before apply.
# Globals:
#   MODE, CLASS, FORCE, I_SHARED
# Returns:
#   0; 1 compose/hf; 2 farm
#######################################
reap_apply_guards() {
  models_dir_is_safe || return 1
  models_realpath_under "${MODELS_DIR}" >/dev/null || return 1
  if [[ -f ${MODELS_DIR}/.hf-download.pid ]]; then
    err "hf download pid file present; refuse --apply (use --force to override)"
    return 1
  fi
  if hf_download_pids_running && [[ ${FORCE} -eq 0 ]]; then
    err "hf download PID running; refuse --apply"
    return 1
  fi
  if compose_is_running && ! class_selected junk; then
    err "Comfy is up; refuse --apply for class other than junk"
    return 1
  fi
  if [[ ${I_SHARED} -eq 0 ]] && command -v bash >/dev/null; then
    :
  fi
  return 0
}

#######################################
# Classify a path relative to MODELS_DIR.
# Arguments:
#   $1  absolute path
# Outputs:
#   class token
# Returns:
#   0
#######################################
reap_classify_path() {
  local path="${1}"
  local base rel
  base="$(basename "${path}")"
  rel="${path#"${MODELS_DIR}"/}"
  if [[ ${rel} == foreign/* || ${rel} == foreign ]]; then
    echo foreign
    return 0
  fi
  local tok
  while IFS= read -r tok; do
    [[ -z ${tok} ]] && continue
    case "${base}" in
      *"${tok}"*)
        echo banned
        return 0
        ;;
    esac
    case "${rel}" in
      *"${tok}"*)
        echo banned
        return 0
        ;;
    esac
  done < <(models_refuse_list)
  case "${base}" in
    *.incomplete | *.lock)
      echo junk
      return 0
      ;;
  esac
  if [[ -L ${path} && ! -e ${path} ]]; then
    echo junk
    return 0
  fi
  if [[ ${rel} == Lightricks__LTX-2.3* || ${rel} == *LTX-2.3* ]]; then
    echo superseded
    return 0
  fi
  if models_is_keep_file "${base}"; then
    echo live
    return 0
  fi
  echo orphan
}

#######################################
# Plan: print class + path for matching files.
# Globals:
#   MODELS_DIR, CLASS, I_FOREIGN
#######################################
reap_plan() {
  local f class
  models_dir_is_safe || return 1
  [[ -d ${MODELS_DIR} ]] || {
    log "MODELS_DIR missing: ${MODELS_DIR}"
    return 0
  }
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    class="$(reap_classify_path "${f}")"
    if [[ ${class} == foreign && ${I_FOREIGN} -eq 0 ]]; then
      log "foreign skip: ${f}"
      continue
    fi
    if [[ ${class} == live ]]; then
      continue
    fi
    if class_selected "${class}"; then
      log "PLAN ${class} ${f}"
    fi
  done < <(find "${MODELS_DIR}" \( -type f -o -type l \) 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Quarantine or delete one path.
# Globals:
#   QUARANTINE, MODELS_DIR
# Arguments:
#   $1  class
#   $2  path
#######################################
reap_one() {
  local class="${1}"
  local path="${2}"
  local stamp dest
  models_realpath_under "${path}" >/dev/null || return 1
  if models_is_keep_file "$(basename "${path}")" && [[ ${class} != junk ]]; then
    log "keep-set, skip ${path}"
    return 0
  fi
  if [[ ${QUARANTINE} -eq 1 || ${class} != junk ]]; then
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    dest="${MODELS_DIR}/.reap-quarantine/${stamp}"
    mkdir -p "${dest}"
    mkdir -p "$(dirname "${dest}/${path#"${MODELS_DIR}"/}")"
    mv "${path}" "${dest}/${path#"${MODELS_DIR}"/}"
    printf '{"path":"%s","class":"%s","reason":"%s"}\n' \
      "${path}" "${class}" "${class}" >>"${dest}/MANIFEST.json"
    reap_log "quarantine ${class} ${path} -> ${dest}"
  else
    rm -f "${path}"
    reap_log "delete ${class} ${path}"
  fi
}

#######################################
# Apply selected classes.
#######################################
reap_apply() {
  local f class i=0
  reap_apply_guards || return $?
  if [[ ${YES} -ne 1 ]]; then
    err "--apply requires --yes"
    return 1
  fi
  log "reap apply class=${CLASS} under ${MODELS_DIR}"
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    i=$((i + 1))
    if ((i % 25 == 0)); then
      log "… reap apply scanned ${i} paths (still running)"
    fi
    class="$(reap_classify_path "${f}")"
    if [[ ${class} == foreign && ${I_FOREIGN} -eq 0 ]]; then
      continue
    fi
    if [[ ${class} == live ]]; then
      continue
    fi
    if class_selected "${class}"; then
      reap_one "${class}" "${f}"
    fi
  done < <(find "${MODELS_DIR}" \( -type f -o -type l \) 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Drop an opt-in pack's files except shared keep-set names.
# Globals:
#   DROP_PACK, YES, QUARANTINE
#######################################
reap_drop_pack() {
  local json files f
  reap_apply_guards || return $?
  if [[ ${YES} -ne 1 ]]; then
    err "--drop-pack requires --yes"
    return 1
  fi
  json="$(python3 "${REPO_ROOT}/scripts/lib/model_manifest.py" \
    --manifest "$(models_manifest_path)" pack "${DROP_PACK}")" || return 1
  files="$(python3 -c 'import json,sys; print("\n".join(json.loads(sys.argv[1]).get("files") or []))' "${json}")"
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    if models_is_keep_file "${f}" && python3 -c 'import json,sys
p=json.loads(sys.argv[1])
raise SystemExit(0 if p.get("shares") else 1)
' "${json}"; then
      log "drop-pack ${DROP_PACK}: keep shared ${f}"
      continue
    fi
    while IFS= read -r path; do
      [[ -z ${path} ]] && continue
      if [[ ${QUARANTINE} -eq 1 ]]; then
        reap_one orphan "${path}"
      else
        QUARANTINE=1
        reap_one orphan "${path}"
      fi
    done < <(find "${MODELS_DIR}" -name "${f}" 2>/dev/null)
  done <<<"${files}"
}

#######################################
# Restore a quarantine tree.
# Globals:
#   RESTORE_FROM, MODELS_DIR
#######################################
reap_restore() {
  local src="${RESTORE_FROM}"
  [[ ${src} == /* ]] || src="${MODELS_DIR}/${src}"
  [[ -d ${src} ]] || {
    err "missing quarantine ${src}"
    return 1
  }
  local f rel
  while IFS= read -r f; do
    rel="${f#"${src}"/}"
    [[ ${rel} == MANIFEST.json ]] && continue
    mkdir -p "$(dirname "${MODELS_DIR}/${rel}")"
    mv "${f}" "${MODELS_DIR}/${rel}"
    reap_log "restore ${rel}"
  done < <(find "${src}" -type f ! -name MANIFEST.json)
}

#######################################
# Drop old quarantine dirs (name is UTC stamp). --older-than 14d is documented.
# Globals:
#   OLDER_THAN, YES, MODELS_DIR
#######################################
reap_drop_quarantine() {
  if [[ ${YES} -ne 1 ]]; then
    err "drop-quarantine requires --yes"
    return 1
  fi
  log "drop-quarantine older-than=${OLDER_THAN:-any}"
  local d
  for d in "${MODELS_DIR}/.reap-quarantine"/*; do
    [[ -d ${d} ]] || continue
    rm -rf "${d}"
    reap_log "drop-quarantine ${d}"
  done
}

#######################################
# Dispatcher.
#######################################
main() {
  parse_args "$@"
  case "${MODE}" in
    plan) reap_plan ;;
    apply) reap_apply ;;
    drop-pack) reap_drop_pack ;;
    restore) reap_restore ;;
    drop-quarantine) reap_drop_quarantine ;;
    *)
      err "unknown mode ${MODE}"
      return 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
