#!/usr/bin/env bash
#
# ## spark-timing
#
# Record wall-clock seconds for the three Kitchen smokes on a real Spark.
# CI has no GPU — this file is the operator timing table. Do not invent seconds.
#
# Usage:
#   ./scripts/utilities/spark-timing.sh show [--json]
#   ./scripts/utilities/spark-timing.sh record --klein N --wan N --ltx N [--json]
#
# Environment:
#   COMFY_OUTPUT_DIR (JSON lands at spark-timing.json; not git)
#
# @command spark-timing

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"

JSON_FLAG=""
CMD="show"
KLEIN_S=""
WAN_S=""
LTX_S=""

#######################################
# Path of the operator timing JSON.
# Globals:
#   COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
timing_path() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/spark-timing.json"
}

#######################################
# True when a value is a positive number (seconds).
# Globals:
#   None
# Arguments:
#   $1  candidate
# Outputs:
#   None
# Returns:
#   0 valid; 1 otherwise
#######################################
is_positive_seconds() {
  [[ ${1} =~ ^[0-9]+([.][0-9]+)?$ ]] || return 1
  awk -v n="${1}" 'BEGIN {exit !(n > 0)}'
}

#######################################
# Parse CLI into globals.
# Globals:
#   CMD, JSON_FLAG, KLEIN_S, WAN_S, LTX_S
# Arguments:
#   $@  CLI tokens
# Outputs:
#   Help on stderr for -h/--help
# Returns:
#   0; exits 0 on help; exits 1 on unknown arg
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --klein)
        KLEIN_S="${2:?}"
        shift
        ;;
      --wan)
        WAN_S="${2:?}"
        shift
        ;;
      --ltx)
        LTX_S="${2:?}"
        shift
        ;;
      show | record) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 show|record --klein N --wan N --ltx N [--json]" >&2
        echo "  Wall-clock seconds after doctor prints attention: kitchen." >&2
        echo "  Writes ${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/spark-timing.json (not git)." >&2
        echo "  Refuses to record when compose is up and attention is not kitchen." >&2
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
# Print recorded timings (empty is a page, not a crash).
# Globals:
#   JSON_FLAG, COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Status on stderr; JSON on stdout with --json
# Returns:
#   0
#######################################
cmd_show() {
  local path attn
  path="$(timing_path)"
  attn="$(stack_attention_backend)"
  if [[ ! -f ${path} ]]; then
    log "spark-timing: none at ${path}"
    log "Queue klein-still-draft, wan-i2v-5s, ltx-i2v-5s with attention: kitchen, then:"
    log "  ./scripts/manage.sh spark-timing record --klein N --wan N --ltx N"
    log "live attention: ${attn}"
    if [[ ${JSON_FLAG} == "--json" ]]; then
      printf '{"recorded":false,"attention":"%s","path":"%s"}\n' "${attn}" "${path}"
    fi
    return 0
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    cat "${path}"
    return 0
  fi
  log "spark-timing ${path}"
  log "$(cat "${path}")"
}

#######################################
# Write timings. Refuse a non-Kitchen path while compose is up.
# Globals:
#   KLEIN_S, WAN_S, LTX_S, JSON_FLAG, COMFY_OUTPUT_DIR
# Arguments:
#   None
# Outputs:
#   Status on stderr; JSON on stdout with --json
# Returns:
#   0 wrote; 1 validation; 2 live attention is not kitchen
#######################################
cmd_record() {
  local path attn dest
  if [[ -z ${KLEIN_S} || -z ${WAN_S} || -z ${LTX_S} ]]; then
    err "record requires --klein N --wan N --ltx N (wall-clock seconds)"
    return 1
  fi
  is_positive_seconds "${KLEIN_S}" || {
    err "invalid --klein ${KLEIN_S}"
    return 1
  }
  is_positive_seconds "${WAN_S}" || {
    err "invalid --wan ${WAN_S}"
    return 1
  }
  is_positive_seconds "${LTX_S}" || {
    err "invalid --ltx ${LTX_S}"
    return 1
  }
  attn="$(stack_attention_backend)"
  if compose_is_running && [[ ${attn} != "kitchen" ]]; then
    err "live attention is ${attn}; record only with attention: kitchen (stack down after a Kitchen run is OK)"
    return 2
  fi
  path="$(timing_path)"
  dest="$(dirname "${path}")"
  mkdir -p "${dest}"
  printf '{"klein_s":%s,"wan_s":%s,"ltx_s":%s,"attention":"%s","smokes":{"klein":"klein-still-draft-lab-example","wan":"wan-i2v-5s-lab-example","ltx":"ltx-i2v-5s-lab-example"}}\n' \
    "${KLEIN_S}" "${WAN_S}" "${LTX_S}" "${attn}" >"${path}"
  log "wrote ${path} (attention=${attn})"
  if [[ ${JSON_FLAG} == "--json" ]]; then
    cat "${path}"
  fi
}

#######################################
# Dispatcher.
# Globals:
#   CMD
# Arguments:
#   $@  CLI tokens
# Outputs:
#   Delegates to cmd_show / cmd_record
# Returns:
#   Handler status; 1 unknown command
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    show) cmd_show ;;
    record) cmd_record ;;
    *)
      err "Unknown command: ${CMD}"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
