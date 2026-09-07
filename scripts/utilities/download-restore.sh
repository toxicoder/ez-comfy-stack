#!/usr/bin/env bash
#
# ## download-restore
#
# Opt-in post-concat restore pack (SeedVR2-3B Apache). Never part of
# download-models. Unload Comfy denoise first (occupancy).
#
# Usage:
#   ./scripts/utilities/download-restore.sh status [--tier seedvr2-3b] [--json]
#   ./scripts/utilities/download-restore.sh run [--tier seedvr2-3b]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   ~15 GB. Not default. Do not coreside with LTX/Wan denoise.
#
# @command download-restore

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="seedvr2-3b"
JSON_FLAG=""
CMD="status"

#######################################
# Hugging Face repo for a restore tier.
# Arguments:
#   $1  Tier name
# Outputs:
#   Repo id or empty
# Returns:
#   0
#######################################
tier_repo() {
  case "${1}" in
    seedvr2-3b) echo "ByteDance-Seed/SeedVR2-3B" ;;
    *) echo "" ;;
  esac
}

#######################################
# Selective include paths (no x86_64 apex wheels).
# Arguments:
#   $1  Tier
# Outputs:
#   One path per line
#######################################
tier_include_patterns() {
  case "${1}" in
    seedvr2-3b)
      printf '%s\n' \
        "seedvr2_ema_3b.pth" \
        "ema_vae.pth" \
        "pos_emb.pt" \
        "neg_emb.pt" \
        "README.md"
      ;;
  esac
}

#######################################
# Local snapshot directory.
# Arguments:
#   $1  Tier
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

#######################################
# Parse CLI.
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
        echo "Usage: $0 status|run [--tier seedvr2-3b] [--json]" >&2
        echo "  seedvr2-3b = ByteDance SeedVR2-3B Apache 2.0 (~15 GB). Post-concat only." >&2
        echo "  Not part of download-models. Unload LTX/Wan first." >&2
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
# True when keep-set files exist.
#######################################
tier_files_ready() {
  local tier="${1}"
  local dir f
  dir="$(tier_dir "${tier}")"
  [[ -d ${dir} ]] || return 1
  local pat
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    [[ ${pat} == "README.md" ]] && continue
    f="${dir}/${pat}"
    if [[ ! -f ${f} || ! -s ${f} ]]; then
      return 1
    fi
  done < <(tier_include_patterns "${tier}")
  return 0
}

#######################################
# Link restore weights under comfy/upscale_models.
#######################################
link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy/upscale_models"
  mkdir -p "${src}"
  local dir f base dest
  dir=$(tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    dest="${src}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/upscale_models/"
    fi
  done < <(find "${dir}" -maxdepth 1 -type f \( -name '*.pth' -o -name '*.pt' -o -name '*.safetensors' \) 2>/dev/null)
}

#######################################
# Status.
#######################################
cmd_status() {
  local repo dir
  repo=$(tier_repo "${TIER}")
  if [[ -z ${repo} ]]; then
    err "Unknown restore tier: ${TIER}"
    exit 1
  fi
  dir=$(tier_dir "${TIER}")
  local ready="false"
  if tier_files_ready "${TIER}"; then
    ready="true"
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '{"tier":"%s","repo":"%s","path":"%s","ready":%s}\n' \
      "${TIER}" "${repo}" "${dir}" "${ready}"
  else
    log "${TIER}: ${repo} ready=${ready} at ${dir}"
  fi
}

#######################################
# Download selective subset.
#######################################
cmd_run() {
  local repo dir
  repo=$(tier_repo "${TIER}")
  if [[ -z ${repo} ]]; then
    err "Unknown restore tier: ${TIER}"
    exit 1
  fi
  check_hf_cli
  ensure_models_dir "${MODELS_DIR}" || exit 1
  dir="$(tier_dir "${TIER}")"
  if tier_files_ready "${TIER}"; then
    log "skip ${TIER}: already present"
    link_into_comfy "${TIER}"
    cmd_status
    return 0
  fi
  local -a include_args=()
  local pat
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    include_args+=(--include "${pat}")
  done < <(tier_include_patterns "${TIER}")
  HF_HOME="${MODELS_DIR}" hf_download "${repo}" --local-dir "${dir}" \
    "${include_args[@]}"
  link_into_comfy "${TIER}"
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
