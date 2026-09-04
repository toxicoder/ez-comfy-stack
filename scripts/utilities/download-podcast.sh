#!/usr/bin/env bash
#
# ## download-podcast
#
# Opt-in Hugging Face pull for US-safe local podcast weights.
#
# Purpose:
#   Selective download of Kokoro ONNX (analog), native ACE-Step 1.5 beds,
#   and optional Chatterbox / Qwen3-TTS extras. Never part of download-models.
#
# Audience:
#   Operators on the Spark host. Prefer manage.sh download-podcast.
#
# Usage:
#   ./scripts/utilities/download-podcast.sh status|run|cleanup [--tier analog|acestep|chatterbox|qwen3tts|all] [--json]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   Opt-in only. Use download-limit wrap on remote SSH.
#   Refuses F5-TTS, XTTS, Fish, MiniMax H3, Music 3, TTS-Audio-Suite, OldTimeRadio.
#
# Exit codes:
#   0 success; 1 usage/tier/CLI errors.
#
# @command download-podcast

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="analog"
JSON_FLAG=""
CMD="status"
CLEANUP_YES=0

#######################################
# Hugging Face repo id for a podcast tier.
# Globals:
#   None
# Arguments:
#   $1  Tier id (analog|acestep|chatterbox|qwen3tts)
# Outputs:
#   Repo id on stdout (empty if unknown)
# Returns:
#   0
#######################################
tier_repo() {
  case "${1}" in
    analog) echo "fastrtc/kokoro-onnx" ;;
    acestep) echo "Comfy-Org/ace_step_1.5_ComfyUI_files" ;;
    chatterbox) echo "ResembleAI/chatterbox-turbo" ;;
    qwen3tts) echo "Qwen/Qwen3-TTS-12Hz-0.6B-Base" ;;
    *) echo "" ;;
  esac
}

#######################################
# Minimum ready size in GB for a tier (selective payload).
# Globals:
#   None
# Arguments:
#   $1  Tier id
# Outputs:
#   Integer GB on stdout
# Returns:
#   0
#######################################
tier_min_gb() {
  case "${1}" in
    analog) echo 0 ;;
    acestep) echo 2 ;;
    chatterbox) echo 1 ;;
    qwen3tts) echo 1 ;;
    *) echo 0 ;;
  esac
}

#######################################
# Glob patterns for selective hf download of a tier (one line each).
# Globals:
#   None
# Arguments:
#   $1  Tier id
# Outputs:
#   Include globs on stdout
# Returns:
#   0
#######################################
tier_include_patterns() {
  case "${1}" in
    analog)
      printf '%s\n' "kokoro-v1.0.onnx" "voices-v1.0.bin"
      ;;
    acestep)
      printf '%s\n' "checkpoints/ace_step_1.5_turbo_aio.safetensors"
      ;;
    chatterbox)
      printf '%s\n' "t3_turbo_v1.safetensors"
      ;;
    qwen3tts)
      printf '%s\n' "model.safetensors"
      ;;
    *)
      return 0
      ;;
  esac
}

#######################################
# Absolute local-dir for a tier snapshot.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id
# Outputs:
#   Directory path on stdout
# Returns:
#   0
#######################################
tier_dir() {
  local repo
  repo=$(tier_repo "${1}")
  echo "${MODELS_DIR}/${repo//\//__}_${1}"
}

#######################################
# Approximate on-disk size of a directory in GB.
# Globals:
#   None
# Arguments:
#   $1  Directory path
# Outputs:
#   Size with one decimal on stdout
# Returns:
#   0
#######################################
tier_size_gb() {
  local dir="${1}"
  if [[ ! -d ${dir} ]]; then
    echo 0
    return
  fi
  du -sk "${dir}" 2>/dev/null | awk '{printf "%.1f", $1/1024/1024}'
}

#######################################
# Expand a user-facing tier into concrete download tiers.
# Globals:
#   TIER
# Arguments:
#   None
# Outputs:
#   Space-separated tier ids on stdout
# Returns:
#   0
#######################################
tiers_to_process() {
  case "${TIER}" in
    all) echo "analog acestep chatterbox qwen3tts" ;;
    analog | acestep | chatterbox | qwen3tts) echo "${TIER}" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Comfy subfolder for a downloaded basename.
# Globals:
#   None
# Arguments:
#   $1  Basename
# Outputs:
#   Subfolder name on stdout (onnx|tts|checkpoints)
# Returns:
#   0
#######################################
comfy_dest_subdir() {
  local base="${1}"
  case "${base}" in
    *.onnx) echo "onnx" ;;
    voices*.bin) echo "tts" ;;
    ace_step*.safetensors) echo "checkpoints" ;;
    *) echo "tts" ;;
  esac
}

#######################################
# True if a relative path is in the selective keep set (or tiny meta).
# Globals:
#   None
# Arguments:
#   $1  Tier id
#   $2  Path relative to tier local-dir
# Outputs:
#   None
# Returns:
#   0 keep; 1 extra
#######################################
is_keep_relpath() {
  local tier="${1}"
  local rel="${2}"
  local pat
  case "${rel}" in
    .gitattributes | LICENSE | README.md) return 0 ;;
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
# True if selective tier files are already on disk.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id
# Outputs:
#   None
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
# List files under a tier dir outside the selective keep set.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id
# Outputs:
#   Absolute extra paths on stdout
# Returns:
#   0
#######################################
list_extra_files() {
  local tier="${1}"
  local dir rel f
  dir="$(tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 0
  fi
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    rel="${f#"${dir}"/}"
    if ! is_keep_relpath "${tier}" "${rel}"; then
      printf '%s\n' "${f}"
    fi
  done < <(find "${dir}" -type f 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Remove empty directories under a root (post-delete).
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
  find "${root}" -depth -type d -empty -delete 2>/dev/null || true
}

#######################################
# Relative-symlink selective files into MODELS_DIR/comfy/{onnx,tts,checkpoints}.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy"
  mkdir -p "${src}/onnx" "${src}/tts" "${src}/checkpoints"
  local dir base dest dest_sub f
  dir=$(tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    dest_sub="$(comfy_dest_subdir "${base}")"
    dest="${src}/${dest_sub}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/${dest_sub}/"
    else
      warn "failed to link ${base} → comfy/${dest_sub}/"
    fi
  done < <(
    find "${dir}" -type f \( \
      -name '*.safetensors' -o -name '*.onnx' -o -name '*.bin' -o -name '*.pt' \
      \) 2>/dev/null
  )
}

#######################################
# Refuse banned podcast packs / celebrity clone flags.
# Globals:
#   None
# Arguments:
#   $1  Tier or flag string
# Outputs:
#   Error on stderr when banned
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_banned_podcast_tier() {
  local raw="${1:-}"
  local lowered
  lowered="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]')"
  case "${lowered}" in
    *f5* | *xtts* | *fish* | *h3* | *music3* | *oldtimeradio* | *old-time-radio* | \
      *tts-audio-suite* | *ttsaudiosuite* | *rogan* | *ramsay* | *higgs* | *echo-tts* | *vibevoice*)
      err "Banned podcast tier: ${raw}. See docs/licenses.md and docs/podcast.md"
      return 1
      ;;
  esac
  return 0
}

#######################################
# Parse CLI flags.
# Globals:
#   JSON_FLAG, TIER, CMD, CLEANUP_YES
# Arguments:
#   $@  CLI args
# Outputs:
#   Usage on stderr
# Returns:
#   0; exits 1 on unknown/banned args
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --tier)
        TIER="${2:?}"
        if ! refuse_banned_podcast_tier "${TIER}"; then
          exit 1
        fi
        shift
        ;;
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup) CMD="${1}" ;;
      analog | acestep | chatterbox | qwen3tts | all)
        TIER="${1}"
        ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup [--tier analog|acestep|chatterbox|qwen3tts|all] [--json]" >&2
        echo "  analog = Kokoro-82M ONNX only (smallest). Not part of download-models." >&2
        echo "  cleanup options: --dry-run (default) | --yes" >&2
        exit 0
        ;;
      *)
        if ! refuse_banned_podcast_tier "${1}"; then
          exit 1
        fi
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# Read-only readiness report.
# Globals:
#   MODELS_DIR, TIER, JSON_FLAG
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; status on stderr otherwise
# Returns:
#   0; exits 1 on unknown tier
#######################################
cmd_status() {
  local results=()
  local tier repo dir size min ready
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir=$(tier_dir "${tier}")
    size=$(tier_size_gb "${dir}")
    min=$(tier_min_gb "${tier}")
    ready="false"
    if tier_files_ready "${tier}"; then
      ready="true"
    fi
    results+=("{\"tier\":\"${tier}\",\"repo\":\"${repo}\",\"path\":\"${dir}\",\"size_gb\":${size},\"min_gb\":${min},\"ready\":${ready}}")
  done
  if [[ ${JSON_FLAG} == "--json" ]]; then
    local joined
    joined=$(
      IFS=,
      echo "${results[*]}"
    )
    printf '{"tiers":[%s],"models_dir":"%s"}\n' "${joined}" "${MODELS_DIR}"
  else
    for tier in $(tiers_to_process); do
      dir=$(tier_dir "${tier}")
      size=$(tier_size_gb "${dir}")
      log "${tier}: $(tier_repo "${tier}") — ${size} GB at ${dir}"
    done
  fi
}

#######################################
# Download missing selective files and link into comfy/.
# Globals:
#   MODELS_DIR, TIER
# Arguments:
#   None
# Outputs:
#   log/warn/err
# Returns:
#   0 on success; exits 1 if none downloaded
#######################################
cmd_run() {
  check_hf_cli
  ensure_models_dir "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  local tier repo ok=0 fail=0 pat dir
  local -a include_args=()
  for tier in $(tiers_to_process); do
    repo=$(tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir="$(tier_dir "${tier}")"
    if tier_files_ready "${tier}"; then
      log "skip ${tier}: already present at ${dir} (cache hit)"
      link_into_comfy "${tier}"
      ok=$((ok + 1))
      continue
    fi
    include_args=()
    log "Downloading ${repo} selective subset (tier: ${tier})…"
    while IFS= read -r pat; do
      [[ -z ${pat} ]] && continue
      include_args+=(--include "${pat}")
      log "  include: ${pat}"
    done < <(tier_include_patterns "${tier}")
    if [[ ${#include_args[@]} -eq 0 ]]; then
      err "No include patterns for tier ${tier}; refusing full-repo pull."
      fail=$((fail + 1))
      continue
    fi
    local dl_rc=0
    HF_HOME="${MODELS_DIR}" hf_download "${repo}" --local-dir "${dir}" \
      "${include_args[@]}" || dl_rc=$?
    if [[ ${dl_rc} -eq 0 ]]; then
      link_into_comfy "${tier}"
      ok=$((ok + 1))
    else
      warn "Skipping remaining setup for ${repo} (see short error above)."
      warn "Partials kept under ${dir}; re-run to resume."
      fail=$((fail + 1))
    fi
  done
  cmd_status
  if [[ ${ok} -eq 0 ]]; then
    err "No podcast tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial podcast download: ${ok} ok, ${fail} failed"
  fi
}

#######################################
# Remove non-selective files from tier local-dirs (dry-run by default).
# Globals:
#   MODELS_DIR, TIER, CLEANUP_YES
# Arguments:
#   None
# Outputs:
#   Logs kept/removed paths
# Returns:
#   0; exits 1 on unknown tier
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
    done < <(list_extra_files "${tier}")
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
# CLI dispatcher.
# Arguments:
#   $@ - CLI args
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    run) cmd_run ;;
    cleanup) cmd_cleanup ;;
    *)
      err "Usage: $0 status|run|cleanup [--tier analog|acestep|chatterbox|qwen3tts|all] [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
