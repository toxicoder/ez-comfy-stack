#!/usr/bin/env bash
#
# ## download-longcat
#
# Opt-in LongCat-Video (MIT). Second stack, not download-models.
# Context-parallel two-Spark only behind LAB_ALLOW_CONTEXT_PARALLEL=1.
# NCCL is out of this sample stack.
#
# Usage:
#   ./scripts/utilities/download-longcat.sh status|run [--tier video|avatar|all] [--json]
#
# @command download-longcat

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="video"
JSON_FLAG=""
CMD="status"

#######################################
# HF repo for a LongCat tier.
# Arguments:
#   $1  video|avatar
# Outputs:
#   Repo id or empty
#######################################
tier_repo() {
  case "${1}" in
    video) echo "meituan-longcat/LongCat-Video" ;;
    avatar) echo "meituan-longcat/LongCat-Video-Avatar" ;;
    *) echo "" ;;
  esac
}

#######################################
# Selective includes.
# Arguments:
#   $1  Tier
#######################################
tier_include_patterns() {
  case "${1}" in
    video | avatar)
      printf '%s\n' "README.md"
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
    all) echo "video avatar" ;;
    video | avatar) echo "${TIER}" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Refuse NCCL / context-parallel unless the lab flag is set.
# Globals:
#   LAB_ALLOW_CONTEXT_PARALLEL
# Arguments:
#   $1  optional flag name
# Returns:
#   0 allowed; 1 refused
#######################################
refuse_context_parallel() {
  if [[ ${LAB_ALLOW_CONTEXT_PARALLEL:-0} == "1" ]]; then
    log "LAB_ALLOW_CONTEXT_PARALLEL=1 (two-Spark continuation only; still no NCCL in this sample)"
    return 0
  fi
  if [[ ${1:-} == "--context-parallel" ]]; then
    err "context-parallel two-Spark only behind LAB_ALLOW_CONTEXT_PARALLEL=1; NCCL is out of this sample"
    return 1
  fi
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
      --context-parallel)
        refuse_context_parallel --context-parallel || exit 1
        ;;
      status | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run [--tier video|avatar|all] [--json]" >&2
        echo "  LongCat-Video MIT. Not download-models. No NCCL. No context-parallel default." >&2
        echo "  Two-Spark continuation only with LAB_ALLOW_CONTEXT_PARALLEL=1." >&2
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
  [[ -s ${dir}/README.md ]]
}

#######################################
# Link weights into comfy/diffusion_models.
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
  done < <(find "${dir}" -type f \( -name '*.safetensors' -o -name '*.pth' \) 2>/dev/null)
}

#######################################
# Status JSON/text.
#######################################
cmd_status() {
  local tier repo ready
  local -a results=()
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown LongCat tier: ${tier}"
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
  local tier repo dir i=0 n=0
  local -a tiers=()
  refuse_context_parallel || true
  check_hf_cli
  prepare_comfy_layout "${MODELS_DIR}" || exit 1
  read -r -a tiers <<<"$(tiers_to_process)"
  n="${#tiers[@]}"
  for tier in "${tiers[@]}"; do
    i=$((i + 1))
    log_step "${i}" "${n}" "longcat ${tier}"
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown LongCat tier: ${tier}"
      exit 1
    fi
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
