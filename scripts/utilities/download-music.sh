#!/usr/bin/env bash
#
# ## download-music
#
# Opt-in Hugging Face pull for US-safe local ACE-Step music weights.
#
# Purpose:
#   Selective download of ACE-Step 1.5 turbo AIO (default) and optional XL
#   split files. Never part of download-models. Turbo reuses the podcast
#   acestep snapshot so the ~10 GB AIO is not pulled twice.
#
# Audience:
#   Operators on the Spark host. Prefer manage.sh download-music.
#
# Usage:
#   ./scripts/utilities/download-music.sh status|run|cleanup [--tier turbo|xl|all] [--json]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   Opt-in only. Use download-limit wrap on remote SSH.
#   Refuses MiniMax Music 3, MiniMax H3, Suno, Udio, Stable Audio partner.
#
# Exit codes:
#   0 success; 1 usage/tier/CLI errors.
#
# @command download-music

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="turbo"
JSON_FLAG=""
CMD="status"
CLEANUP_YES=0
readonly MUSIC_REPO="Comfy-Org/ace_step_1.5_ComfyUI_files"
readonly AIO_FILE="ace_step_1.5_turbo_aio.safetensors"
# Same local-dir as scripts/utilities/download-podcast.sh --tier acestep.
readonly TURBO_SNAPSHOT_SUFFIX="Comfy-Org__ace_step_1.5_ComfyUI_files_acestep"

#######################################
# Hugging Face repo id for a music tier.
# Globals:
#   MUSIC_REPO
# Arguments:
#   $1  Tier id (turbo|xl)
# Outputs:
#   Repo id on stdout (empty if unknown)
# Returns:
#   0
#######################################
tier_repo() {
  case "${1}" in
    turbo | xl) echo "${MUSIC_REPO}" ;;
    *) echo "" ;;
  esac
}

#######################################
# Basename of the turbo AIO checkpoint.
# Globals:
#   AIO_FILE
# Arguments:
#   None
# Outputs:
#   Filename on stdout
# Returns:
#   0
#######################################
aio_basename() {
  printf '%s\n' "${AIO_FILE}"
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
    turbo) echo 9 ;;
    xl) echo 14 ;;
    *) echo 0 ;;
  esac
}

#######################################
# Glob patterns for selective hf download of a tier (one line each).
# Globals:
#   AIO_FILE
# Arguments:
#   $1  Tier id
# Outputs:
#   Include globs on stdout
# Returns:
#   0
#######################################
tier_include_patterns() {
  case "${1}" in
    turbo)
      printf '%s\n' "checkpoints/${AIO_FILE}"
      ;;
    xl)
      printf '%s\n' \
        "split_files/diffusion_models/acestep_v1.5_xl_turbo_bf16.safetensors" \
        "split_files/vae/ace_1.5_vae.safetensors" \
        "split_files/text_encoders/qwen_0.6b_ace15.safetensors" \
        "split_files/text_encoders/qwen_1.7b_ace15.safetensors"
      ;;
    *)
      return 0
      ;;
  esac
}

#######################################
# Absolute local-dir for a tier snapshot.
# turbo uses the podcast acestep dest so the 10 GB AIO is shared.
# Globals:
#   MODELS_DIR, TURBO_SNAPSHOT_SUFFIX
# Arguments:
#   $1  Tier id
# Outputs:
#   Directory path on stdout
# Returns:
#   0
#######################################
tier_dir() {
  local repo
  case "${1}" in
    turbo)
      echo "${MODELS_DIR}/${TURBO_SNAPSHOT_SUFFIX}"
      ;;
    *)
      repo=$(tier_repo "${1}")
      echo "${MODELS_DIR}/${repo//\//__}_${1}"
      ;;
  esac
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
    all) echo "turbo xl" ;;
    turbo | xl) echo "${TIER}" ;;
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
comfy_dest_subdir() {
  local base="${1}"
  case "${base}" in
    ace_step*.safetensors) echo "checkpoints" ;;
    *vae*.safetensors) echo "vae" ;;
    qwen_*ace*.safetensors) echo "text_encoders" ;;
    acestep_v1.5_xl*.safetensors) echo "diffusion_models" ;;
    *) echo "checkpoints" ;;
  esac
}

#######################################
# First existing turbo AIO path (comfy link or shared snapshot).
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   Absolute path on stdout when found
# Returns:
#   0 if a non-empty AIO file exists; 1 otherwise
#######################################
existing_aio_path() {
  local dest snap
  dest="${MODELS_DIR}/comfy/checkpoints/$(aio_basename)"
  if [[ -f ${dest} && -s ${dest} ]]; then
    printf '%s\n' "${dest}"
    return 0
  fi
  snap="$(tier_dir turbo)/checkpoints/$(aio_basename)"
  if [[ -f ${snap} && -s ${snap} ]]; then
    printf '%s\n' "${snap}"
    return 0
  fi
  return 1
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
# True if selective tier files are already on disk (basename for turbo).
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
  if [[ ${tier} == "turbo" ]]; then
    existing_aio_path >/dev/null
    return $?
  fi
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
# Relative-symlink selective files into MODELS_DIR/comfy/*.
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
  mkdir -p "${src}/checkpoints" "${src}/diffusion_models" "${src}/text_encoders" "${src}/vae"
  local dir base dest dest_sub f rel
  dir=$(tier_dir "${tier}")
  [[ -d ${dir} ]] || return 0
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    base="$(basename "${f}")"
    rel="${f#"${dir}"/}"
    dest_sub="$(comfy_dest_subdir "${base}")"
    case "${rel}" in
      checkpoints/*) dest_sub="checkpoints" ;;
      split_files/text_encoders/* | text_encoders/*) dest_sub="text_encoders" ;;
      split_files/vae/* | vae/*) dest_sub="vae" ;;
      split_files/diffusion_models/* | diffusion_models/*) dest_sub="diffusion_models" ;;
    esac
    dest="${src}/${dest_sub}/${base}"
    if ln_sfn_relative "${f}" "${dest}"; then
      log "linked ${base} → comfy/${dest_sub}/"
    else
      warn "failed to link ${base} → comfy/${dest_sub}/"
    fi
  done < <(
    find "${dir}" -type f -name '*.safetensors' 2>/dev/null
  )
}

#######################################
# Refuse banned music packs / partner APIs.
# Globals:
#   None
# Arguments:
#   $1  Tier or flag string
# Outputs:
#   Error on stderr when banned
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_banned_music_tier() {
  local raw="${1:-}"
  local lowered
  lowered="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]')"
  case "${lowered}" in
    *music3* | *minimax* | *suno* | *h3* | *stable-audio* | *stableaudio*)
      err "Banned music tier: ${raw}. See docs/licenses.md and docs/music.md"
      return 1
      ;;
    udio | udio-* | *-udio | *-udio-*)
      # Exact Udio partner ids — do not use *udio* (that matches "audio").
      err "Banned music tier: ${raw}. See docs/licenses.md and docs/music.md"
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
        if ! refuse_banned_music_tier "${TIER}"; then
          exit 1
        fi
        shift
        ;;
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup) CMD="${1}" ;;
      turbo | xl | all)
        TIER="${1}"
        ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup [--tier turbo|xl|all] [--json]" >&2
        echo "  turbo = ACE-Step 1.5 turbo AIO only (default; shared with download-podcast --tier acestep)." >&2
        echo "  xl = optional XL split files. Not part of download-models." >&2
        echo "  cleanup options: --dry-run (default) | --yes" >&2
        exit 0
        ;;
      *)
        if ! refuse_banned_music_tier "${1}"; then
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
      log "skip ${tier}: already present (cache hit; shared AIO dest with download-podcast --tier acestep)"
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
    err "No music tiers downloaded successfully (${fail} failed). Check hf CLI and HF_TOKEN."
    exit 1
  fi
  if [[ ${fail} -gt 0 ]]; then
    warn "Partial music download: ${ok} ok, ${fail} failed"
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
      err "Usage: $0 status|run|cleanup [--tier turbo|xl|all] [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
