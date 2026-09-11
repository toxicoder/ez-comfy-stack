#!/usr/bin/env bash
#
# ## download-3d
#
# Opt-in 3D packs: native Comfy-Org TRELLIS.2 INT8 (MIT, no nvdiffrast) and
# DA3-BASE (Apache). Never part of download-models. occupancy enter trellis
# first (unload LTX). SuperSplat is a host viewer (docs/splat-sidecar.md).
#
# Usage:
#   ./scripts/utilities/download-3d.sh status|run [--tier trellis2|da3-base|all] [--json]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   Occupancy: do not coreside with LTX/Wan denoise. DA3-LARGE is refused.
#
# @command download-3d

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="trellis2"
JSON_FLAG=""
CMD="status"

#######################################
# HF repo for a 3D tier.
# Globals:
#   None
# Arguments:
#   $1  Tier name (trellis2|da3-base)
# Outputs:
#   Repo id or empty
# Returns:
#   0
#######################################
tier_repo() {
  case "${1}" in
    trellis2) echo "Comfy-Org/TRELLIS.2" ;;
    da3-base) echo "depth-anything/DA3-BASE" ;;
    *) echo "" ;;
  esac
}

#######################################
# Selective includes (one path per line).
# Globals:
#   None
# Arguments:
#   $1  Tier name
# Outputs:
#   Include paths on stdout
# Returns:
#   0
#######################################
tier_include_patterns() {
  case "${1}" in
    trellis2)
      printf '%s\n' \
        "diffusion_models/trellis_2_int8_convrot.safetensors" \
        "vae/trellis_2_shape_vae_bf16.safetensors" \
        "vae/trellis_2_texture_vae_bf16.safetensors" \
        "clip_vision/dino_v3_vit_l.safetensors" \
        "README.md"
      ;;
    da3-base)
      printf '%s\n' "model.safetensors" "README.md"
      ;;
  esac
}

#######################################
# Snapshot directory for a tier.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier name
# Outputs:
#   Absolute local-dir path
# Returns:
#   0
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

#######################################
# Tiers to process for the current TIER flag.
# Globals:
#   TIER
# Arguments:
#   None
# Outputs:
#   Space-separated tier names
# Returns:
#   0
#######################################
tiers_to_process() {
  case "${TIER}" in
    all) echo "trellis2 da3-base" ;;
    trellis2 | da3-base) echo "${TIER}" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Refuse banned 3D packs (DA3-LARGE, nvdiffrast, Inria 3DGS, Pixal3D default).
# Globals:
#   None
# Arguments:
#   $1  Tier name
# Outputs:
#   Error on stderr when banned
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_banned_3d_tier() {
  local tier="${1}"
  local lower
  lower="$(printf '%s' "${tier}" | tr '[:upper:]' '[:lower:]')"
  case "${lower}" in
    da3-large | nvdiffrast | nvdiffrec | inria-3dgs | pixal3d | pixal3d-as-default)
      err "Banned 3D pack: ${tier} (DA3-LARGE / nvdiffrast / Inria 3DGS / Pixal3D-as-default)"
      return 1
      ;;
  esac
  return 0
}

#######################################
# Parse CLI into TIER / CMD / JSON_FLAG.
# Globals:
#   TIER, CMD, JSON_FLAG
# Arguments:
#   $@  CLI args
# Outputs:
#   Help on stderr; errors on unknown/banned
# Returns:
#   0; exits 0 on --help; exits 1 on bad args
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
        echo "Usage: $0 status|run [--tier trellis2|da3-base|all] [--json]" >&2
        echo "  Native Comfy-Org TRELLIS.2 INT8 (MIT, no nvdiffrast). DA3-BASE Apache." >&2
        echo "  occupancy enter trellis first. DA3-LARGE / Pixal3D-as-default refused." >&2
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
  refuse_banned_3d_tier "${TIER}" || exit 1
  if [[ ${TIER} != "all" && -z $(tier_repo "${TIER}") ]]; then
    err "Unknown 3D tier: ${TIER} (DA3-LARGE is refused)"
    exit 1
  fi
}

#######################################
# Ready when keep files exist (skip README).
# Globals:
#   MODELS_DIR (via tier_dir)
# Arguments:
#   $1  Tier name
# Outputs:
#   None
# Returns:
#   0 ready; 1 missing
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
# Comfy dest path for a TRELLIS.2 native basename.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  basename
# Outputs:
#   Absolute dest on stdout
# Returns:
#   0
#######################################
trellis_comfy_dest() {
  local base="${1}"
  local src="${MODELS_DIR}/comfy"
  case "${base}" in
    trellis_2_int8_convrot.safetensors | trellis_2_bf16.safetensors)
      echo "${src}/diffusion_models/${base}"
      ;;
    trellis_2_*vae*.safetensors)
      echo "${src}/vae/${base}"
      ;;
    dino_v3*.safetensors)
      echo "${src}/clip_vision/${base}"
      ;;
    *)
      echo "${src}/3d/${base}"
      ;;
  esac
}

#######################################
# Link weights into native Comfy folders (TRELLIS) or diffusion_models (DA3).
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier name
# Outputs:
#   log lines on stderr
# Returns:
#   0
#######################################
link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy"
  prepare_comfy_layout "${MODELS_DIR}" || return 1
  local dir f base dest
  dir=$(tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    dest="${src}/3d/${base}"
    if [[ ${tier} == "da3-base" ]]; then
      dest="${src}/diffusion_models/${base}"
    elif [[ ${tier} == "trellis2" ]]; then
      dest="$(trellis_comfy_dest "${base}")"
    fi
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base}"
    fi
  done < <(find "${dir}" -type f \( -name '*.safetensors' -o -name '*.pth' -o -name '*.pt' \) 2>/dev/null)
}

#######################################
# Print ready status (optional JSON).
# Globals:
#   TIER, JSON_FLAG, MODELS_DIR
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; logs on stderr
# Returns:
#   0; 1 unknown tier
#######################################
cmd_status() {
  local tier repo dir ready
  local -a results=()
  for tier in $(tiers_to_process); do
    refuse_banned_3d_tier "${tier}" || exit 1
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown 3D tier: ${tier} (DA3-LARGE is refused)"
      exit 1
    fi
    dir=$(tier_dir "${tier}")
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
# Download selected 3D tiers and link into comfy/.
# Globals:
#   TIER, MODELS_DIR
# Arguments:
#   None
# Outputs:
#   Status via cmd_status
# Returns:
#   0; 1 on unknown tier / hf failure
#######################################
cmd_run() {
  local tier repo dir i=0 n=0
  local -a tiers=()
  check_hf_cli
  prepare_comfy_layout "${MODELS_DIR}" || exit 1
  read -r -a tiers <<<"$(tiers_to_process)"
  n="${#tiers[@]}"
  for tier in "${tiers[@]}"; do
    i=$((i + 1))
    log_step "${i}" "${n}" "3d ${tier}"
    refuse_banned_3d_tier "${tier}" || exit 1
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown 3D tier: ${tier}"
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
# Globals:
#   CMD
# Arguments:
#   $@  CLI args
# Outputs:
#   Command output
# Returns:
#   Command status
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
