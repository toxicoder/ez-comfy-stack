#!/usr/bin/env bash
#
# ## download-flux
#
# Download FLUX.2 checkpoints for ComfyUI on DGX Spark into the shared model cache.
#
# Purpose:
#   Pull Hugging Face snapshots for the unified flux-to-ltx demo (default tier:
#   fast = Klein 9B NVFP4 + optional Nunchaku) and symlink safetensors into
#   $MODELS_DIR/comfy/diffusion_models for ComfyUI discovery.
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
    fast) echo 12 ;;
    quality) echo 30 ;;
    nunchaku) echo 4 ;;
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

#######################################
# check_hf_cli helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
check_hf_cli() {
  if command -v huggingface-cli >/dev/null 2>&1 || command -v hf >/dev/null 2>&1; then
    return 0
  fi
  err "Required tool missing: huggingface-cli or hf (pip install -U huggingface_hub)"
  exit 1
}

#######################################
# hf_download helper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
hf_download() {
  if [[ -n ${LAB_MOCK_HF_DOWNLOAD:-} ]]; then
    local dest=""
    local prev=""
    for a in "$@"; do
      if [[ ${prev} == "--local-dir" ]]; then
        dest="$a"
      fi
      prev="$a"
    done
    mkdir -p "${dest}"
    echo "mock" >"${dest}/.mock"
    return 0
  fi
  if command -v huggingface-cli >/dev/null 2>&1; then
    huggingface-cli download "$@"
  else
    hf download "$@"
  fi
}

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
    all)
      if [[ ${INCLUDE_NUNCHAKU} == "1" ]]; then
        echo "fast nunchaku quality"
      else
        echo "fast quality"
      fi
      ;;
    fast)
      if [[ ${INCLUDE_NUNCHAKU} == "1" ]]; then
        echo "fast nunchaku"
      else
        echo "fast"
      fi
      ;;
    quality) echo "quality" ;;
    nunchaku) echo "nunchaku" ;;
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
  local src dest
  src=$(tier_dir "$tier")
  dest=$(comfy_link_dir "$tier")
  mkdir -p "$dest"
  [[ -d ${src} ]] || return 0
  while read -r f; do
    local base
    base="$(basename "${f}")"
    if [[ ! -e "${dest}/${base}" ]]; then
      ln -sfn "${f}" "${dest}/${base}" || true
    fi
  done < <(find "${src}" -maxdepth 3 -type f \( -name '*.safetensors' -o -name '*.sft' \) 2>/dev/null)
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
  mkdir -p "${MODELS_DIR}/comfy/diffusion_models" \
    "${MODELS_DIR}/comfy/text_encoders" "${MODELS_DIR}/comfy/vae"
  local tier repo
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: $tier"
      exit 1
    fi
    log "Downloading ${repo} (tier: ${tier})..."
    HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "$(tier_dir "$tier")" || {
      warn "Download failed for ${repo} (gated license or network). Continue with other tiers."
      continue
    }
    link_into_comfy "$tier"
  done
  cmd_status
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
