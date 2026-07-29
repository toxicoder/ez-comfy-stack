#!/usr/bin/env bash
#
# ## download-flux
#
# Download FLUX.2 checkpoints for ComfyUI on DGX Spark into the shared model cache.
#
# Purpose:
#   Pull Hugging Face snapshots for the unified flux-to-ltx demo (default tier:
#   fast = Klein 9B NVFP4 + optional Nunchaku) and symlink safetensors into
#   $MODELS_DIR/comfy/{diffusion_models,text_encoders,vae} for ComfyUI discovery.
#   Companions (Comfy-Org TE + VAE) are pulled with the fast tier for runnable graphs.
#
# Audience:
#   Operators on the Spark host (or CI with LAB_MOCK_HF_DOWNLOAD). Prefer
#   manage.sh download-models which wraps this under bandwidth limits.
#
# Usage:
#   ./scripts/utilities/download-flux.sh status [--tier fast|quality|nunchaku|all] [--json]
#   ./scripts/utilities/download-flux.sh run [--tier ...] [--no-nunchaku]
#
# Environment:
#   MODELS_DIR          — cache root (default /mnt/models)
#   INCLUDE_NUNCHAKU    — 1 (default) includes nunchaku repo with fast/all
#   HF_TOKEN            — optional; required for gated BFL models
#   LAB_MOCK_HF_DOWNLOAD — if set, skip real HF network and write mock markers
#
# Safety:
#   Large downloads can saturate WAN links. Run under download-limit wrap when
#   accessing the host over the internet without out-of-band console access.
#
# Exit codes:
#   0 success; 1 unknown args/tiers or missing HF CLI on run.
#
# @command download-flux

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="fast"
JSON_FLAG=""
CMD="status"
INCLUDE_NUNCHAKU="${INCLUDE_NUNCHAKU:-1}"

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
    fast) echo "black-forest-labs/FLUX.2-klein-9b-nvfp4" ;;
    quality) echo "black-forest-labs/FLUX.2-dev" ;;
    nunchaku) echo "tonera/FLUX.2-klein-9B-Nunchaku" ;;
    # Comfy-Org split TE + VAE required for runnable Flux.2 Klein graphs
    companions) echo "Comfy-Org/flux2-klein-9B" ;;
    *) echo "" ;;
  esac
}

#######################################
# tier_min_gb helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
tier_min_gb() {
  case "${1}" in
    fast) echo 5 ;;
    quality) echo 30 ;;
    nunchaku) echo 4 ;;
    # qwen fp4mixed ~6.8G + flux2-vae ~0.3G
    companions) echo 6 ;;
    *) echo 0 ;;
  esac
}

#######################################
# tier_dir helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}"
}

#######################################
# comfy_link_dir helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
comfy_link_dir() {
  echo "${MODELS_DIR}/comfy/diffusion_models"
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
# True if tier local-dir already meets min size (skip re-download).
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier name
# Outputs:
#   None
# Returns:
#   0 ready; 1 not ready
#######################################
tier_files_ready() {
  local tier="${1}"
  local dir size min
  dir="$(tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 1
  fi
  # Require at least one weight-like file so empty dirs with junk don't skip
  local has_weight=0
  while IFS= read -r _; do
    has_weight=1
    break
  done < <(find "${dir}" -type f \( -name '*.safetensors' -o -name '*.sft' -o -name '*.gguf' -o -name '*.bin' \) 2>/dev/null)
  if [[ ${has_weight} -ne 1 ]]; then
    return 1
  fi
  size="$(tier_size_gb "${dir}")"
  min="$(tier_min_gb "${tier}")"
  awk "BEGIN {exit !($size >= $min)}"
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
    all)
      if [[ ${INCLUDE_NUNCHAKU} == "1" ]]; then
        echo "fast companions nunchaku quality"
      else
        echo "fast companions quality"
      fi
      ;;
    fast)
      # Companions (Qwen TE + flux2 VAE) required for lab image workflows
      if [[ ${INCLUDE_NUNCHAKU} == "1" ]]; then
        echo "fast companions nunchaku"
      else
        echo "fast companions"
      fi
      ;;
    quality) echo "quality" ;;
    nunchaku) echo "nunchaku" ;;
    companions) echo "companions" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# HF --include patterns for selective companion download (one line each).
# Globals:
#   FLUX_TE_VARIANT — fp4 (default) | full
# Arguments:
#   $1  Tier name
# Outputs:
#   Include globs on stdout
# Returns:
#   0
#######################################
tier_include_patterns() {
  case "${1}" in
    companions)
      if [[ ${FLUX_TE_VARIANT:-fp4} == "full" ]]; then
        echo "split_files/text_encoders/qwen_3_8b.safetensors"
      else
        echo "split_files/text_encoders/qwen_3_8b_fp4mixed.safetensors"
      fi
      echo "split_files/vae/flux2-vae.safetensors"
      ;;
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
      --no-nunchaku) INCLUDE_NUNCHAKU=0 ;;
      status | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run [--tier fast|quality|nunchaku|all] [--no-nunchaku] [--json]" >&2
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
  local src base dest_sub
  local comfy="${MODELS_DIR}/comfy"
  src=$(tier_dir "$tier")
  mkdir -p "${comfy}/diffusion_models" "${comfy}/text_encoders" "${comfy}/vae"
  [[ -d ${src} ]] || return 0
  while read -r f; do
    base="$(basename "${f}")"
    dest_sub="diffusion_models"
    case "${base}" in
      *vae*) dest_sub="vae" ;;
      *qwen* | *clip* | *t5* | *text*) dest_sub="text_encoders" ;;
    esac
    if [[ ! -e "${comfy}/${dest_sub}/${base}" ]]; then
      ln -sfn "${f}" "${comfy}/${dest_sub}/${base}" || true
      log "linked ${base} → comfy/${dest_sub}/"
    fi
  done < <(find "${src}" -type f \( -name '*.safetensors' -o -name '*.sft' \) 2>/dev/null)
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
  mkdir -p "${MODELS_DIR}/comfy/diffusion_models" \
    "${MODELS_DIR}/comfy/text_encoders" "${MODELS_DIR}/comfy/vae"
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
    if [[ ${#include_args[@]} -gt 0 ]]; then
      HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "${dir}" \
        "${include_args[@]}" || dl_rc=$?
    else
      HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "${dir}" || dl_rc=$?
    fi
    if [[ ${dl_rc} -eq 0 ]]; then
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
    err "No FLUX tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial FLUX download: ${ok} ok, ${fail} failed"
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
      err "Usage: $0 status|run [--tier fast|quality|nunchaku|all] [--no-nunchaku] [--json]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
