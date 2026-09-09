#!/usr/bin/env bash
#
# ## download-dub
#
# Opt-in Hugging Face pull for US-safe dub (ASR + multilingual clone) weights.
#
# Purpose:
#   Selective download of Silero VAD, faster-whisper large-v3, and Chatterbox
#   Multilingual V3. Never part of download-models. Missing pack is not a
#   doctor failure.
#
# Audience:
#   Operators on the Spark host. Prefer manage.sh download-dub.
#
# Usage:
#   ./scripts/utilities/download-dub.sh status|run|cleanup [--tier asr|clone|all] [--json]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   Opt-in only. Use download-limit wrap on remote SSH.
#   Refuses F5-TTS, XTTS, Fish, MiniMax H3, NLLB, SeamlessM4T, Wav2Lip,
#   TTS-Audio-Suite, celebrity clone flags.
#
# Exit codes:
#   0 success; 1 usage/tier/CLI errors.
#
# @command download-dub

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="asr"
JSON_FLAG=""
CMD="status"
CLEANUP_YES=0

#######################################
# Hugging Face repo id for a dub pack.
# Globals:
#   None
# Arguments:
#   $1  Pack id (vad|whisper|clone)
# Outputs:
#   Repo id on stdout (empty if unknown)
# Returns:
#   0
#######################################
dub_tier_repo() {
  case "${1}" in
    vad) echo "snakers4/silero-vad" ;;
    whisper) echo "Systran/faster-whisper-large-v3" ;;
    clone) echo "ResembleAI/chatterbox" ;;
    *) echo "" ;;
  esac
}

#######################################
# Minimum ready size in GB for a pack.
# Globals:
#   None
# Arguments:
#   $1  Pack id
# Outputs:
#   Integer GB on stdout
# Returns:
#   0
#######################################
dub_tier_min_gb() {
  case "${1}" in
    vad) echo 0 ;;
    whisper) echo 2 ;;
    clone) echo 1 ;;
    *) echo 0 ;;
  esac
}

#######################################
# Glob patterns for selective hf download (one line each).
# Globals:
#   None
# Arguments:
#   $1  Pack id
# Outputs:
#   Include globs on stdout
# Returns:
#   0
#######################################
dub_tier_include_patterns() {
  case "${1}" in
    vad)
      printf '%s\n' "src/silero_vad/data/silero_vad.onnx"
      ;;
    whisper)
      printf '%s\n' "model.bin"
      ;;
    clone)
      printf '%s\n' "t3_mtl23ls_v2.safetensors" "s3gen.safetensors"
      ;;
    *)
      return 0
      ;;
  esac
}

#######################################
# Absolute local-dir for a pack snapshot.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Pack id
# Outputs:
#   Directory path on stdout
# Returns:
#   0
#######################################
dub_tier_dir() {
  local repo
  repo=$(dub_tier_repo "${1}")
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
dub_tier_size_gb() {
  local dir="${1}"
  if [[ ! -d ${dir} ]]; then
    echo 0
    return
  fi
  du -sk "${dir}" 2>/dev/null | awk '{printf "%.1f", $1/1024/1024}'
}

#######################################
# Expand a user-facing tier into concrete packs.
# Globals:
#   TIER
# Arguments:
#   None
# Outputs:
#   Space-separated pack ids on stdout
# Returns:
#   0
#######################################
dub_tiers_to_process() {
  case "${TIER}" in
    all) echo "vad whisper clone" ;;
    asr) echo "vad whisper" ;;
    clone) echo "clone" ;;
    vad | whisper) echo "${TIER}" ;;
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
#   Subfolder name on stdout
# Returns:
#   0
#######################################
dub_comfy_dest_subdir() {
  local base="${1}"
  case "${base}" in
    *.onnx) echo "onnx" ;;
    model.bin) echo "whisper" ;;
    *) echo "tts" ;;
  esac
}

#######################################
# True if a relative path is in the selective keep set (or tiny meta).
# Globals:
#   None
# Arguments:
#   $1  Pack id
#   $2  Path relative to pack local-dir
# Outputs:
#   None
# Returns:
#   0 keep; 1 extra
#######################################
dub_is_keep_relpath() {
  local tier="${1}"
  local rel="${2}"
  local pat
  case "${rel}" in
    .gitattributes | LICENSE | README.md | .mock) return 0 ;;
    .cache | .cache/*) return 0 ;;
    *.incomplete) return 0 ;;
    *.lock | *.lock.*) return 0 ;;
  esac
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    if [[ ${rel} == "${pat}" ]]; then
      return 0
    fi
  done < <(dub_tier_include_patterns "${tier}")
  return 1
}

#######################################
# True if selective pack files are already on disk.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Pack id
# Outputs:
#   None
# Returns:
#   0 ready; 1 not ready
#######################################
dub_tier_files_ready() {
  local tier="${1}"
  local dir pat f
  dir="$(dub_tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 1
  fi
  while IFS= read -r pat; do
    [[ -z ${pat} ]] && continue
    f="${dir}/${pat}"
    if [[ ! -f ${f} || ! -s ${f} ]]; then
      return 1
    fi
  done < <(dub_tier_include_patterns "${tier}")
  return 0
}

#######################################
# List files under a pack dir outside the selective keep set.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Pack id
# Outputs:
#   Absolute extra paths on stdout
# Returns:
#   0
#######################################
dub_list_extra_files() {
  local tier="${1}"
  local dir rel f
  dir="$(dub_tier_dir "${tier}")"
  if [[ ! -d ${dir} ]]; then
    return 0
  fi
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    rel="${f#"${dir}"/}"
    if ! dub_is_keep_relpath "${tier}" "${rel}"; then
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
dub_prune_empty_dirs() {
  local root="${1}"
  [[ -d ${root} ]] || return 0
  find "${root}" -depth -type d -empty -delete 2>/dev/null || true
}

#######################################
# Relative-symlink selective files into MODELS_DIR/comfy/{onnx,whisper,tts}.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Pack id
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
dub_link_into_comfy() {
  local tier="${1}"
  local src="${MODELS_DIR}/comfy"
  prepare_comfy_layout "${MODELS_DIR}" || return 1
  local dir base dest dest_sub f
  dir=$(dub_tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    dest_sub="$(dub_comfy_dest_subdir "${base}")"
    dest="${src}/${dest_sub}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/${dest_sub}/"
    else
      warn "failed to link ${base} → comfy/${dest_sub}/"
    fi
  done < <(
    find "${dir}" -type f \( \
      -name '*.safetensors' -o -name '*.onnx' -o -name 'model.bin' \
      \) 2>/dev/null
  )
}

#######################################
# Refuse banned dub packs / celebrity clone flags.
# Globals:
#   None
# Arguments:
#   $1  Tier or flag string
# Outputs:
#   Error on stderr when banned
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_banned_dub_tier() {
  local raw="${1:-}"
  local lowered
  lowered="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]')"
  case "${lowered}" in
    *f5* | *xtts* | *fish* | *h3* | *nllb* | *seamless* | *wav2lip* | \
      *oldtimeradio* | *tts-audio-suite* | *ttsaudiosuite* | *rogan* | *ramsay* | \
      *higgs* | *echo-tts* | *elevenlabs*)
      err "Banned dub tier: ${raw}. See docs/licenses.md and docs/dub.md"
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
dub_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --tier)
        TIER="${2:?}"
        if ! refuse_banned_dub_tier "${TIER}"; then
          exit 1
        fi
        shift
        ;;
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup) CMD="${1}" ;;
      asr | clone | all | vad | whisper)
        TIER="${1}"
        ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup [--tier asr|clone|all] [--json]" >&2
        echo "  asr = Silero VAD + faster-whisper large-v3. Not part of download-models." >&2
        echo "  clone = Chatterbox Multilingual V3 (MIT, PerTh on)." >&2
        echo "  cleanup options: --dry-run (default) | --yes" >&2
        exit 0
        ;;
      *)
        if ! refuse_banned_dub_tier "${1}"; then
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
dub_cmd_status() {
  local results=()
  local tier repo dir size min ready
  for tier in $(dub_tiers_to_process); do
    repo=$(dub_tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir=$(dub_tier_dir "${tier}")
    size=$(dub_tier_size_gb "${dir}")
    min=$(dub_tier_min_gb "${tier}")
    ready="false"
    if dub_tier_files_ready "${tier}"; then
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
    for tier in $(dub_tiers_to_process); do
      dir=$(dub_tier_dir "${tier}")
      size=$(dub_tier_size_gb "${dir}")
      log "${tier}: $(dub_tier_repo "${tier}") — ${size} GB at ${dir}"
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
dub_cmd_run() {
  check_hf_cli
  prepare_comfy_layout "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  local tier repo ok=0 fail=0 pat dir
  local -a include_args=()
  for tier in $(dub_tiers_to_process); do
    repo=$(dub_tier_repo "${tier}")
    if [[ -z ${repo} ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir="$(dub_tier_dir "${tier}")"
    if dub_tier_files_ready "${tier}"; then
      log "skip ${tier}: already present at ${dir} (cache hit)"
      dub_link_into_comfy "${tier}"
      ok=$((ok + 1))
      continue
    fi
    include_args=()
    log "Downloading ${repo} selective subset (tier: ${tier})…"
    while IFS= read -r pat; do
      [[ -z ${pat} ]] && continue
      include_args+=(--include "${pat}")
      log "  include: ${pat}"
    done < <(dub_tier_include_patterns "${tier}")
    if [[ ${#include_args[@]} -eq 0 ]]; then
      err "No include patterns for tier ${tier}; refusing full-repo pull."
      fail=$((fail + 1))
      continue
    fi
    local dl_rc=0
    HF_HOME="${MODELS_DIR}" hf_download "${repo}" --local-dir "${dir}" \
      "${include_args[@]}" || dl_rc=$?
    if [[ ${dl_rc} -eq 0 ]]; then
      dub_link_into_comfy "${tier}"
      ok=$((ok + 1))
    else
      warn "Skipping remaining setup for ${repo} (see short error above)."
      warn "Partials kept under ${dir}; re-run to resume."
      fail=$((fail + 1))
    fi
  done
  dub_cmd_status
  if [[ ${ok} -eq 0 ]]; then
    err "No dub tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial dub download: ${ok} ok, ${fail} failed"
  fi
}

#######################################
# Remove non-selective files from pack local-dirs (dry-run by default).
# Globals:
#   MODELS_DIR, TIER, CLEANUP_YES
# Arguments:
#   None
# Outputs:
#   Logs kept/removed paths
# Returns:
#   0; exits 1 on unknown tier
#######################################
dub_cmd_cleanup() {
  local tier dir f rel n_extra n_del size_before size_after total_extra=0
  for tier in $(dub_tiers_to_process); do
    if [[ -z $(dub_tier_repo "${tier}") ]]; then
      err "Unknown tier: ${tier}"
      exit 1
    fi
    dir="$(dub_tier_dir "${tier}")"
    if [[ ! -d ${dir} ]]; then
      log "cleanup ${tier}: no directory at ${dir} (nothing to do)"
      continue
    fi
    n_extra=0
    n_del=0
    size_before="$(dub_tier_size_gb "${dir}")"
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
    done < <(dub_list_extra_files "${tier}")
    total_extra=$((total_extra + n_extra))
    if [[ ${CLEANUP_YES} -eq 1 ]]; then
      dub_prune_empty_dirs "${dir}"
      size_after="$(dub_tier_size_gb "${dir}")"
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
  dub_parse_args "$@"
  case "${CMD}" in
    status) dub_cmd_status ;;
    run) dub_cmd_run ;;
    cleanup) dub_cmd_cleanup ;;
    *)
      err "Usage: $0 status|run|cleanup [--tier asr|clone|all] [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
