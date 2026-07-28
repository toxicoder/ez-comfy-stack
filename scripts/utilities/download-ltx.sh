#!/usr/bin/env bash
#
# ## download-ltx
#
# Download LTX-2.3 ComfyUI components (Kijai split checkpoints) into MODELS_DIR.
#
# Purpose:
#   Fetch weights required for the balanced video tier of the unified flux-to-ltx
#   pipeline and link them into ComfyUI model subfolders (diffusion_models,
#   text_encoders, vae) under $MODELS_DIR/comfy.
#
#   By default each tier pulls a selective subset of Kijai/LTX2.3_comfy
#   (one transformer + text encoder + VAEs, ~25–50 GB), not the full monorepo
#   (~400 GB of every precision/variant). Set LTX_FULL_REPO=1 to pull everything.
#
# Audience:
#   Operators preparing a Spark host for manage.sh start. Prefer
#   manage.sh download-models for throttled sequential flux+ltx pulls.
#
# Usage:
#   ./scripts/utilities/download-ltx.sh status [--tier balanced|quality|all] [--json]
#   ./scripts/utilities/download-ltx.sh run [--tier ...]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD — same semantics as download-flux.
#   LTX_FULL_REPO=1 — download entire Kijai/LTX2.3_comfy snapshot (all variants).
#
# Safety:
#   Multi‑GB transfer — use download-limit when on remote SSH.
#
# Exit codes:
#   0 success; 1 usage/tier/CLI errors.
#
# @command download-ltx

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="balanced"
JSON_FLAG=""
CMD="status"

#######################################
# tier_repo helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
tier_repo() {
  case "${1}" in
    balanced | quality) echo "Kijai/LTX2.3_comfy" ;;
    *) echo "" ;;
  esac
}

#######################################
# tier_min_gb helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Tier name (balanced|quality|…)
# Outputs:
#   Minimum ready size in GB on stdout (selective payload, not full monorepo).
# Returns:
#   0
#######################################
tier_min_gb() {
  case "${1}" in
    # distilled fp8 transformer (~25 GB) + TE + VAEs ≈ 28–30 GB
    balanced) echo 20 ;;
    # distilled bf16 transformer (~42 GB) + TE + VAEs ≈ 45–48 GB
    quality) echo 35 ;;
    *) echo 0 ;;
  esac
}

#######################################
# Glob patterns for selective hf download of a tier (one line each).
# Globals:
#   None
# Arguments:
#   $1  Tier name (balanced|quality)
# Outputs:
#   Include globs on stdout (empty for unknown tier).
# Returns:
#   0
#######################################
tier_include_patterns() {
  # Shared TE + VAEs for Comfy split loaders (not full monorepo).
  local -a shared=(
    "text_encoders/ltx-2.3_text_projection_bf16.safetensors"
    "vae/LTX23_video_vae_bf16.safetensors"
    "vae/LTX23_audio_vae_bf16.safetensors"
  )
  case "${1}" in
    balanced)
      # Distilled FP8 with calibrated input scales (Spark / modern NVIDIA FP8 matmul).
      printf '%s\n' \
        "diffusion_models/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors" \
        "${shared[@]}"
      ;;
    quality)
      # Distilled BF16 transformer for higher fidelity (much larger).
      printf '%s\n' \
        "diffusion_models/ltx-2.3-22b-distilled_transformer_only_bf16.safetensors" \
        "${shared[@]}"
      ;;
    *)
      return 0
      ;;
  esac
}

#######################################
# tier_dir helper.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier name
# Outputs:
#   Absolute local-dir path for that tier on stdout.
# Returns:
#   0
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

# check_hf_cli / hf_download: provided by scripts/lib/common.sh (prefer `hf download`).

#######################################
# tier_size_gb helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
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
# tiers_to_process helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
tiers_to_process() {
  case "$TIER" in
    all) echo "balanced quality" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# parse_args helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
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
        echo "Usage: $0 status|run [--tier balanced|quality|all] [--json]" >&2
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
# link_into_comfy helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy"
  mkdir -p "${src}/diffusion_models" "${src}/text_encoders" "${src}/vae" "${src}/checkpoints"
  local dir
  dir=$(tier_dir "$tier")
  [[ -d ${dir} ]] || return 0
  while read -r f; do
    local base dest_sub
    base="$(basename "${f}")"
    dest_sub="diffusion_models"
    case "$base" in
      *text* | *gemma* | *te*) dest_sub="text_encoders" ;;
      *vae* | *audio*) dest_sub="vae" ;;
    esac
    if [[ ! -e "${src}/${dest_sub}/${base}" ]]; then
      ln -sfn "${f}" "${src}/${dest_sub}/${base}" || true
    fi
  done < <(find "${dir}" -type f \( -name '*.safetensors' -o -name '*.sft' -o -name '*.gguf' \) 2>/dev/null)
}

#######################################
# cmd_status helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
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
    if awk "BEGIN {exit !($size >= $min)}"; then
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
# cmd_run helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
cmd_run() {
  check_hf_cli
  ensure_models_dir "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  local tier repo ok=0 fail=0 pat
  local -a include_args=()
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    include_args=()
    if [[ ${LTX_FULL_REPO:-0} == "1" ]]; then
      log "Downloading full ${repo} snapshot (tier: ${tier}; LTX_FULL_REPO=1)…"
      log "Full monorepo is ~400 GB (every precision/variant). Prefer selective default."
    else
      log "Downloading ${repo} selective subset (tier: ${tier})…"
      while IFS= read -r pat; do
        [[ -z ${pat} ]] && continue
        include_args+=(--include "${pat}")
        log "  include: ${pat}"
      done < <(tier_include_patterns "${tier}")
      if [[ ${#include_args[@]} -eq 0 ]]; then
        err "No include patterns for tier ${tier}; refusing full monorepo pull."
        fail=$((fail + 1))
        continue
      fi
      log "Tip: LTX_FULL_REPO=1 pulls the entire ~400 GB repo (not recommended)"
    fi
    # Empty include_args must not expand under set -u (bash unbound array).
    local dl_rc=0
    if [[ ${#include_args[@]} -gt 0 ]]; then
      HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "$(tier_dir "$tier")" \
        "${include_args[@]}" || dl_rc=$?
    else
      HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "$(tier_dir "$tier")" || dl_rc=$?
    fi
    if [[ ${dl_rc} -eq 0 ]]; then
      link_into_comfy "$tier"
      ok=$((ok + 1))
    else
      warn "Skipping remaining setup for ${repo} (see short error above)."
      fail=$((fail + 1))
    fi
  done
  cmd_status
  if [[ ${ok} -eq 0 ]]; then
    err "No LTX tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial LTX download: ${ok} ok, ${fail} failed"
  fi
}

#######################################
# main helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
main() {
  parse_args "$@"
  case "$CMD" in
    status) cmd_status ;;
    run) cmd_run ;;
    *)
      err "Usage: $0 status|run [--tier balanced|quality|all] [--json]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
