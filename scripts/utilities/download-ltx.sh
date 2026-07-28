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
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status depends on command path; see implementation.
#######################################
tier_min_gb() {
  case "${1}" in
    balanced) echo 20 ;;
    quality) echo 35 ;;
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
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
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
  local tier repo
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    log "Downloading ${repo} (tier: ${tier})..."
    HF_HOME="${MODELS_DIR}" hf_download "$repo" --local-dir "$(tier_dir "$tier")" || {
      warn "Download failed for ${repo} (${tier}). Continue."
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
      err "Usage: $0 status|run [--tier balanced|quality|all] [--json]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
