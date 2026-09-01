#!/usr/bin/env bash
#
# ## download-h3
#
# Download MiniMax H3 checkpoints for ComfyUI into the shared model cache.
#
# Purpose:
#   Selective Hugging Face pull from Comfy-Org/MiniMax-H3 (not the 433 GB tree)
#   and relative symlinks into $MODELS_DIR/comfy/{diffusion_models,text_encoders,vae}.
#   Default --tier pruned is the four lab basenames (~40 GB).
#
# Audience:
#   Operators on the Spark host (or CI with LAB_MOCK_HF_DOWNLOAD). Prefer
#   manage.sh download-h3 / download-models --with-h3 which wrap bandwidth limits.
#
# Usage:
#   ./scripts/utilities/download-h3.sh status [--tier pruned|ref2va|turbo|all] [--json]
#   ./scripts/utilities/download-h3.sh run [--tier ...]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD — same semantics as download-flux.
#
# Safety:
#   Large downloads can saturate WAN links. Run under download-limit wrap.
#   Does not geo-block; MiniMax H3 Community License is documented, not enforced here.
#
# Exit codes:
#   0 success; 1 unknown args/tiers or missing HF CLI on run.
#
# @command download-h3

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="pruned"
JSON_FLAG=""
CMD="status"

#######################################
# Map a tier name to the Hugging Face repo id.
# Arguments:
#   $1 - tier (pruned|ref2va|turbo)
# Outputs:
#   Repo id on stdout, or empty if unknown
# Returns:
#   0
#######################################
tier_repo() {
  case "${1}" in
    pruned | ref2va | turbo) echo "Comfy-Org/MiniMax-H3" ;;
    *) echo "" ;;
  esac
}

#######################################
# Minimum ready size floor in GB (selective payload, not the full hub tree).
# Arguments:
#   $1 - tier name
# Outputs:
#   Integer GB on stdout
# Returns:
#   0
#######################################
tier_min_gb() {
  case "${1}" in
    pruned) echo 35 ;;
    ref2va) echo 15 ;;
    turbo) echo 1 ;;
    *) echo 0 ;;
  esac
}

#######################################
# Local-dir under MODELS_DIR for a tier snapshot.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1 - tier name
# Outputs:
#   Absolute path on stdout
# Returns:
#   0
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

#######################################
# Default Comfy diffusion_models link dir.
# Globals:
#   MODELS_DIR
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
comfy_link_dir() {
  echo "${MODELS_DIR}/comfy/diffusion_models"
}

#######################################
# Directory size in GB (one decimal), or 0 if missing.
# Arguments:
#   $1 - directory
# Outputs:
#   Size on stdout
# Returns:
#   0
#######################################
tier_size_gb() {
  local dir="${1}"
  if [[ ! -d ${dir} ]]; then
    echo 0
    return
  fi
  du -sk "$dir" 2>/dev/null | awk '{printf "%.1f", $1/1024/1024}'
}

#######################################
# HF --include paths for a selective tier (one line each).
# Arguments:
#   $1 - tier name
# Outputs:
#   Include paths on stdout
# Returns:
#   0
#######################################
tier_include_patterns() {
  case "${1}" in
    pruned)
      echo "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"
      echo "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
      echo "vae/minimax_h3_video_vae_fp16.safetensors"
      echo "vae/minimax_h3_audio_vae_fp32.safetensors"
      ;;
    ref2va)
      echo "diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"
      ;;
    turbo)
      echo "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
      ;;
  esac
}

#######################################
# True if every include path exists and is non-empty.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1 - tier name
# Returns:
#   0 ready; 1 not ready
#######################################
tier_files_ready() {
  local tier="${1}"
  local dir pat f
  dir="$(tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 1
  fi
  local has=0
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    has=1
    f="${dir}/${pat}"
    if [[ ! -f ${f} || ! -s ${f} ]]; then
      return 1
    fi
  done < <(tier_include_patterns "${tier}")
  [[ ${has} -eq 1 ]]
}

#######################################
# Expand TIER into the list of tiers to process.
# Globals:
#   TIER
# Outputs:
#   Space-separated tier names
# Returns:
#   0
#######################################
tiers_to_process() {
  case "${TIER}" in
    all) echo "pruned ref2va turbo" ;;
    pruned | ref2va | turbo) echo "${TIER}" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Parse CLI arguments into CMD / TIER / JSON_FLAG.
# Arguments:
#   $@ - CLI args
# Returns:
#   0; exits 0 on help, 1 on unknown args
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
        echo "Usage: $0 status|run [--tier pruned|ref2va|turbo|all] [--json]" >&2
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
# Symlink safetensors from a tier local-dir into MODELS_DIR/comfy/*.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1 - tier name
# Returns:
#   0
#######################################
link_into_comfy() {
  local tier="${1}"
  local src base dest_sub dest rel
  local comfy="${MODELS_DIR}/comfy"
  src=$(tier_dir "$tier")
  mkdir -p "${comfy}/diffusion_models" "${comfy}/text_encoders" "${comfy}/vae" "${comfy}/loras"
  [[ -d ${src} ]] || return 0
  while read -r f; do
    base="$(basename "${f}")"
    rel="${f#"${src}"/}"
    dest_sub="diffusion_models"
    case "${rel}" in
      text_encoders/* | */text_encoders/*) dest_sub="text_encoders" ;;
      vae/* | */vae/*) dest_sub="vae" ;;
      loras/* | */loras/*) dest_sub="loras" ;;
      diffusion_models/* | */diffusion_models/*) dest_sub="diffusion_models" ;;
      *)
        case "${base}" in
          *qwen* | *text_encoder*) dest_sub="text_encoders" ;;
          *vae* | *audio*) dest_sub="vae" ;;
          *lora* | *turbo*) dest_sub="loras" ;;
        esac
        ;;
    esac
    dest="${comfy}/${dest_sub}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/${dest_sub}/"
    else
      warn "failed to link ${base} → comfy/${dest_sub}/"
    fi
  done < <(find "${src}" -type f \( -name '*.safetensors' -o -name '*.sft' \) 2>/dev/null)
}

#######################################
# Read-only tier status (JSON on --json).
# Globals:
#   TIER, JSON_FLAG, MODELS_DIR
# Outputs:
#   JSON on stdout when --json; human lines on stderr otherwise
# Returns:
#   0; exits 1 on unknown tier
#######################################
cmd_status() {
  local results=()
  local tier repo dir size min ready
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: $tier"
      exit 1
    fi
    dir=$(tier_dir "$tier")
    size=$(tier_size_gb "$dir")
    min=$(tier_min_gb "$tier")
    ready="false"
    if tier_files_ready "${tier}"; then
      ready="true"
    fi
    results+=("{\"tier\":\"$tier\",\"repo\":\"$repo\",\"path\":\"$dir\",\"size_gb\":$size,\"min_gb\":$min,\"ready\":$ready}")
  done
  if [[ $JSON_FLAG == "--json" ]]; then
    local joined
    joined=$(
      IFS=,
      echo "${results[*]}"
    )
    printf '{"tiers":[%s],"models_dir":"%s"}\n' "$joined" "$MODELS_DIR"
  else
    for tier in $(tiers_to_process); do
      dir=$(tier_dir "$tier")
      size=$(tier_size_gb "$dir")
      log "${tier}: $(tier_repo "$tier") — ${size} GB at ${dir}"
    done
  fi
}

#######################################
# Idempotent selective download + symlink.
# Globals:
#   MODELS_DIR, TIER
# Returns:
#   0 on success; 1 if no tier succeeded
#######################################
cmd_run() {
  check_hf_cli
  ensure_models_dir "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  mkdir -p "${MODELS_DIR}/comfy/diffusion_models" \
    "${MODELS_DIR}/comfy/text_encoders" "${MODELS_DIR}/comfy/vae" \
    "${MODELS_DIR}/comfy/loras"
  local tier repo ok=0 fail=0 dir
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: $tier"
      exit 1
    fi
    dir="$(tier_dir "$tier")"
    if tier_files_ready "${tier}"; then
      log "skip ${tier}: already present at ${dir} (cache hit)"
      link_into_comfy "$tier"
      ok=$((ok + 1))
      continue
    fi
    log "Downloading ${repo} (tier: ${tier})..."
    local -a include_args=()
    local pat dl_rc=0
    while IFS= read -r pat; do
      [[ -z ${pat} ]] && continue
      include_args+=(--include "${pat}")
      log "  include: ${pat}"
    done < <(tier_include_patterns "${tier}")
    HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "${dir}" \
      "${include_args[@]}" || dl_rc=$?
    if [[ ${dl_rc} -eq 0 ]]; then
      if ! tier_files_ready "${tier}"; then
        warn "Download reported ok but required files missing for ${tier} under ${dir}"
        fail=$((fail + 1))
        continue
      fi
      link_into_comfy "$tier"
      ok=$((ok + 1))
    else
      warn "Skipping remaining setup for ${repo} (see short error above)."
      warn "Partials kept under ${dir}; re-run to resume."
      fail=$((fail + 1))
    fi
  done
  cmd_status
  if [[ ${ok} -eq 0 ]]; then
    err "No H3 tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial H3 download: ${ok} ok, ${fail} failed"
  fi
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@ - CLI args
#######################################
main() {
  parse_args "$@"
  case "$CMD" in
    status) cmd_status ;;
    run) cmd_run ;;
    *)
      err "Usage: $0 status|run [--tier pruned|ref2va|turbo|all] [--json]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
