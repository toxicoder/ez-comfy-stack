#!/usr/bin/env bash
#
# ## download-dreamx
#
# Opt-in DreamX-Creator 1.0 (Apache joint AV). Never DreamX-World.
# Not download-models. Unload LTX first.
#
# Usage:
#   ./scripts/utilities/download-dreamx.sh status|run [--tier creator|all] [--json]
#
# @command download-dreamx

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="creator"
JSON_FLAG=""
CMD="status"

#######################################
# HF repo for a DreamX tier.
# Arguments:
#   $1  creator
#######################################
tier_repo() {
  case "${1}" in
    creator) echo "GD-ML/DreamX-Creator" ;;
    *) echo "" ;;
  esac
}

#######################################
# Selective includes (Creator 1.0 only).
# Arguments:
#   $1  Tier
#######################################
tier_include_patterns() {
  case "${1}" in
    creator)
      printf '%s\n' "creator/cross_attn_weights.safetensors" "README.md"
      ;;
  esac
}

#######################################
# Snapshot directory.
# Arguments:
#   $1  Tier
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

#######################################
# Tiers to process.
# Globals:
#   TIER
#######################################
tiers_to_process() {
  case "${TIER}" in
    all | creator) echo "creator" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Refuse DreamX-World and unknown packs.
# Arguments:
#   $1  Tier
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_dreamx_world() {
  local lower
  lower="$(printf '%s' "${1}" | tr '[:upper:]' '[:lower:]')"
  case "${lower}" in
    world | dreamx-world | dreamx_world)
      err "DreamX-World is refused; DreamX-Creator 1.0 Apache only"
      return 1
      ;;
  esac
  return 0
}

#######################################
# Parse CLI.
# Globals:
#   TIER, CMD, JSON_FLAG
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --tier)
        TIER="${2:?}"
        shift
        ;;
      status | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run [--tier creator] [--json]" >&2
        echo "  DreamX-Creator 1.0 Apache joint AV (~54 GB full). Not download-models." >&2
        echo "  DreamX-World is refused. Unload LTX first." >&2
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
  refuse_dreamx_world "${TIER}" || exit 1
  if [[ -z $(tier_repo "${TIER}") && ${TIER} != "all" ]]; then
    err "Unknown DreamX tier: ${TIER} (DreamX-World is refused)"
    exit 1
  fi
}

#######################################
# Ready when keep files exist.
# Arguments:
#   $1  Tier
#######################################
tier_files_ready() {
  local tier="${1}"
  local dir f pat
  dir="$(tier_dir "${tier}")"
  [[ -d ${dir} ]] || return 1
  while IFS= read -r pat; do
    [[ -z ${pat} || ${pat} == "README.md" ]] && continue
    f="${dir}/${pat}"
    if [[ ! -f ${f} || ! -s ${f} ]]; then
      return 1
    fi
  done < <(tier_include_patterns "${tier}")
  return 0
}

#######################################
# Link into comfy/diffusion_models.
# Arguments:
#   $1  Tier
#######################################
link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy/diffusion_models"
  prepare_comfy_layout "${MODELS_DIR}" || return 1
  local dir f base dest
  dir=$(tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    dest="${src}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base}"
    fi
  done < <(find "${dir}" -type f \( -name '*.safetensors' -o -name '*.pt' \) 2>/dev/null)
}

#######################################
# Status.
#######################################
cmd_status() {
  local tier repo ready
  local -a results=()
  for tier in $(tiers_to_process); do
    refuse_dreamx_world "${tier}" || exit 1
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown DreamX tier: ${tier}"
      exit 1
    fi
    ready="false"
    if tier_files_ready "${tier}"; then
      ready="true"
    fi
    results+=("{\"tier\":\"${tier}\",\"repo\":\"${repo}\",\"ready\":${ready}}")
    log "${tier}: ${repo} ready=${ready}"
  done
  if [[ ${JSON_FLAG} == "--json" ]]; then
    local joined
    joined=$(
      IFS=,
      echo "${results[*]}"
    )
    printf '{"tiers":[%s]}\n' "${joined}"
  fi
}

#######################################
# Download.
#######################################
cmd_run() {
  local tier repo dir
  check_hf_cli
  prepare_comfy_layout "${MODELS_DIR}" || exit 1
  for tier in $(tiers_to_process); do
    refuse_dreamx_world "${tier}" || exit 1
    repo=$(tier_repo "${tier}")
    dir="$(tier_dir "${tier}")"
    if tier_files_ready "${tier}"; then
      log "skip ${tier}: already present"
      link_into_comfy "${tier}"
      continue
    fi
    local -a include_args=()
    local pat
    while IFS= read -r pat; do
      [[ -z ${pat} ]] && continue
      include_args+=(--include "${pat}")
    done < <(tier_include_patterns "${tier}")
    HF_HOME="${MODELS_DIR}" hf_download "${repo}" --local-dir "${dir}" \
      "${include_args[@]}"
    link_into_comfy "${tier}"
  done
  cmd_status
}

#######################################
# Dispatcher.
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    *)
      err "Unknown command: ${CMD}"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
