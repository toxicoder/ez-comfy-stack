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
#   (one transformer + text projection + VAEs) plus the Gemma 3 TE companion
#   from Comfy-Org/ltx-2 (DualCLIP with type ltxv). Not the full monorepo
#   (~400 GB of every precision/variant). Set LTX_FULL_REPO=1 to pull everything.
#
# Audience:
#   Operators preparing a Spark host for manage.sh start. Prefer
#   manage.sh download-models for throttled sequential flux+ltx pulls.
#
# Usage:
#   ./scripts/utilities/download-ltx.sh status [--tier balanced|quality|gemma|all] [--json]
#   ./scripts/utilities/download-ltx.sh run [--tier ...]
#   ./scripts/utilities/download-ltx.sh cleanup [--tier ...] [--dry-run|--yes]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD — same semantics as download-flux.
#   LTX_FULL_REPO=1 — download entire Kijai/LTX2.3_comfy snapshot (all variants).
#
# Safety:
#   Multi‑GB transfer — use download-limit when on remote SSH.
#   cleanup defaults to --dry-run; --yes deletes only non-selective files under
#   the tier local-dir (never other MODELS_DIR trees like FLUX).
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
# cleanup: dry-run unless --yes (explicit delete)
CLEANUP_YES=0

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
    # Gemma 3 TE for DualCLIPLoader type=ltxv (required with text_projection)
    gemma) echo "Comfy-Org/ltx-2" ;;
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
    # distilled fp8 transformer (~25 GB) + projection + VAEs ≈ 28–30 GB
    balanced) echo 20 ;;
    # distilled bf16 transformer (~42 GB) + projection + VAEs ≈ 45–48 GB
    quality) echo 35 ;;
    # gemma_3_12B_it_fp4_mixed ≈ 9.45 GB
    gemma) echo 8 ;;
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
  # Shared projection + VAEs for Comfy split loaders (not full monorepo).
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
    gemma)
      # Official Comfy-Org LTX-2 Gemma 3 TE (DualCLIP pair with Kijai text_projection).
      printf '%s\n' \
        "split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"
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
    # Gemma TE is required for runnable LTX lab graphs (DualCLIP type ltxv)
    all) echo "balanced quality gemma" ;;
    balanced) echo "balanced gemma" ;;
    quality) echo "quality gemma" ;;
    gemma) echo "gemma" ;;
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
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup [--tier balanced|quality|gemma|all] [--json]" >&2
        echo "  cleanup options: --dry-run (default) | --yes  delete non-selective weights" >&2
        echo "  balanced/quality auto-include gemma (Comfy-Org/ltx-2 TE for DualCLIP)" >&2
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
# Return 0 if relative path is kept for a selective tier (or tiny meta).
# Globals:
#   None
# Arguments:
#   $1  Tier name
#   $2  Path relative to tier local-dir
# Outputs:
#   None
# Returns:
#   0 keep; 1 extra (candidate for cleanup)
#######################################
is_ltx_keep_relpath() {
  local tier="${1}"
  local rel="${2}"
  local pat
  case "${rel}" in
    .gitattributes | LICENSE | README.md) return 0 ;;
    # HF local-dir resume/cache metadata + partials (never wipe for cleanup)
    .cache | .cache/*) return 0 ;;
    *.incomplete) return 0 ;;
    *.lock | *.lock.*) return 0 ;;
  esac
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    if [[ ${rel} == "${pat}" ]]; then
      return 0
    fi
  done < <(tier_include_patterns "${tier}")
  return 1
}

#######################################
# True if selective tier files are already on disk (skip re-download).
# Globals:
#   MODELS_DIR, LTX_FULL_REPO
# Arguments:
#   $1  Tier name
# Outputs:
#   None
# Returns:
#   0 ready; 1 not ready
#######################################
tier_files_ready() {
  local tier="${1}"
  local dir pat f size min
  dir="$(tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 1
  fi
  # Full monorepo mode: size floor only (no fixed include list); never for gemma
  if [[ ${LTX_FULL_REPO:-0} == "1" && ${tier} != "gemma" ]]; then
    size="$(tier_size_gb "${dir}")"
    min="$(tier_min_gb "${tier}")"
    awk "BEGIN {exit !($size >= $min)}"
    return $?
  fi
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    f="${dir}/${pat}"
    if [[ ! -f ${f} || ! -s ${f} ]]; then
      return 1
    fi
  done < <(tier_include_patterns "${tier}")
  return 0
}

#######################################
# List files under a tier dir that are outside the selective keep set.
# Globals:
#   MODELS_DIR (via tier_dir)
# Arguments:
#   $1  Tier name
# Outputs:
#   Absolute paths of extra files on stdout (one per line)
# Returns:
#   0
#######################################
list_extra_ltx_files() {
  local tier="${1}"
  local dir rel f
  dir="$(tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 0
  fi
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    rel="${f#"${dir}"/}"
    if ! is_ltx_keep_relpath "${tier}" "${rel}"; then
      printf '%s\n' "${f}"
    fi
  done < <(find "${dir}" -type f 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Remove empty directories under a tier local-dir (post-delete).
# Globals:
#   None
# Arguments:
#   $1  Absolute directory path
# Outputs:
#   None
# Returns:
#   0
#######################################
prune_empty_dirs() {
  local root="${1}"
  [[ -d ${root} ]] || return 0
  # deepest-first so parents empty after children are removed
  find "${root}" -depth -type d -empty -delete 2>/dev/null || true
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
  local dir base dest_sub dest rel
  dir=$(tier_dir "$tier")
  [[ -d ${dir} ]] || return 0
  while read -r f; do
    base="$(basename "${f}")"
    rel="${f#"${dir}"/}"
    dest_sub="diffusion_models"
    # Prefer HF layout path (vae/…, text_encoders/…); never match *te* against
    # ".safetensors" (that mis-routed every weight into text_encoders).
    case "${rel}" in
      text_encoders/* | */text_encoders/*) dest_sub="text_encoders" ;;
      vae/* | */vae/*) dest_sub="vae" ;;
      diffusion_models/* | */diffusion_models/*) dest_sub="diffusion_models" ;;
      *)
        case "${base}" in
          *text_projection* | *text_encoder* | *gemma*) dest_sub="text_encoders" ;;
          *vae* | *audio*) dest_sub="vae" ;;
          *) dest_sub="diffusion_models" ;;
        esac
        ;;
    esac
    dest="${src}/${dest_sub}/${base}"
    # Relative targets so bind-mount path (/mnt/models vs /models) does not break
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/${dest_sub}/"
    else
      warn "failed to link ${base} → comfy/${dest_sub}/"
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
  local tier repo ok=0 fail=0 pat dir
  local -a include_args=()
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "$tier")
    dir="$(tier_dir "$tier")"
    if tier_files_ready "${tier}"; then
      log "skip ${tier}: already present at ${dir} (cache hit)"
      link_into_comfy "$tier"
      ok=$((ok + 1))
      continue
    fi
    include_args=()
    # Full monorepo escape hatch is only for Kijai/LTX2.3_comfy, not Gemma companion
    if [[ ${LTX_FULL_REPO:-0} == "1" && ${tier} != "gemma" ]]; then
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
      if [[ ${tier} != "gemma" ]]; then
        log "Tip: LTX_FULL_REPO=1 pulls the entire ~400 GB Kijai monorepo (not recommended)"
      fi
    fi
    # Empty include_args must not expand under set -u (bash unbound array).
    local dl_rc=0
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
    err "No LTX tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial LTX download: ${ok} ok, ${fail} failed"
  fi
}

#######################################
# Remove non-selective weight files from tier local-dirs (dry-run by default).
# Globals:
#   MODELS_DIR, TIER, CLEANUP_YES
# Arguments:
#   None
# Outputs:
#   Logs kept/removed paths and size after
# Returns:
#   0; 1 on unknown tier
#######################################
cmd_cleanup() {
  local tier dir f rel n_extra n_del size_before size_after total_extra=0
  for tier in $(tiers_to_process); do
    if [[ -z $(tier_repo "${tier}") ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir="$(tier_dir "${tier}")"
    if [[ ! -d ${dir} ]]; then
      log "cleanup ${tier}: no directory at ${dir} (nothing to do)"
      continue
    fi
    n_extra=0
    n_del=0
    size_before="$(tier_size_gb "${dir}")"
    log "cleanup ${tier}: scanning ${dir} (current ≈ ${size_before} GB)"
    log "cleanup ${tier}: keeping selective files from tier_include_patterns + LICENSE/README/.gitattributes"
    while IFS= read -r f; do
      [[ -z ${f} ]] && continue
      n_extra=$((n_extra + 1))
      rel="${f#"${dir}"/}"
      if [[ ${CLEANUP_YES} -eq 1 ]]; then
        rm -f "${f}" || warn "Failed to remove ${f}"
        n_del=$((n_del + 1))
        log "  removed: ${rel}"
      else
        log "  would remove: ${rel}"
      fi
    done < <(list_extra_ltx_files "${tier}")
    total_extra=$((total_extra + n_extra))
    if [[ ${CLEANUP_YES} -eq 1 ]]; then
      prune_empty_dirs "${dir}"
      size_after="$(tier_size_gb "${dir}")"
      log "cleanup ${tier}: deleted ${n_del} extra file(s); size ${size_before} → ${size_after} GB"
    else
      log "cleanup ${tier}: ${n_extra} extra file(s) (dry-run). Re-run with --yes to delete."
    fi
  done
  if [[ ${CLEANUP_YES} -ne 1 && ${total_extra} -gt 0 ]]; then
    log "Tip: MODELS_DIR=${MODELS_DIR} $0 cleanup --tier ${TIER} --yes"
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
    cleanup) cmd_cleanup ;;
    *)
      err "Usage: $0 status|run|cleanup [--tier balanced|quality|all] [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
