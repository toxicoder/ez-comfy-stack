#!/usr/bin/env bash
#
# ## download-llm
#
# Download on-box GGUF packs: default prompt-enhance 4B, optional 35B desk.
#
# Purpose:
#   Selective Hugging Face pull. Apache 2.0. File-level include — not the
#   full Unsloth GGUF tree. Default enhance pack is part of download-models.
#   Opt-in qwen36-35b-a3b is occupancy llm-desk only (not download-models).
#
# Audience:
#   Operators on the Spark host. Prefer manage.sh download-llm / download-models.
#
# Usage:
#   ./scripts/utilities/download-llm.sh status|run|cleanup|link [--tier enhance|qwen36-35b-a3b|all] [--json]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   enhance ~3 GB (in download-models). 35B ~23 GB opt-in. Use download-limit
#   wrap on remote SSH. Does not weaken restart: "no", headroom, or
#   download-limit clear-on-exit.
#
# Exit codes:
#   0 success; 1 usage/tier/CLI errors.
#
# @command download-llm

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

MODELS_DIR=${MODELS_DIR:-"/mnt/models"}
TIER="enhance"
JSON_FLAG=""
CMD="status"
CLEANUP_YES=0
readonly LLM_REPO="unsloth/Qwen3-4B-Instruct-2507-GGUF"
readonly LLM_FILE="Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
readonly LLM_MIN_GB=3
readonly LLM_TIER="llm"
readonly LLM35_REPO="unsloth/Qwen3.6-35B-A3B-MTP-GGUF"
readonly LLM35_FILE="Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
readonly LLM35_MIN_GB=23
readonly LLM35_TIER="llm-35b"

#######################################
# Hugging Face repo id for the prompt-enhance GGUF.
# Globals:
#   LLM_REPO
# Arguments:
#   None
# Outputs:
#   Repo id on stdout
# Returns:
#   0
#######################################
llm_repo() {
  printf '%s\n' "${LLM_REPO}"
}

#######################################
# Basename of the default GGUF file.
# Globals:
#   LLM_FILE
# Arguments:
#   None
# Outputs:
#   Filename on stdout
# Returns:
#   0
#######################################
llm_filename() {
  printf '%s\n' "${LLM_FILE}"
}

#######################################
# Minimum ready size in GB for the GGUF pack.
# Globals:
#   LLM_MIN_GB
# Arguments:
#   None
# Outputs:
#   Integer GB on stdout
# Returns:
#   0
#######################################
llm_min_gb() {
  printf '%s\n' "${LLM_MIN_GB}"
}

#######################################
# Absolute local-dir for the GGUF snapshot.
# Globals:
#   MODELS_DIR, LLM_REPO, LLM_TIER
# Arguments:
#   None
# Outputs:
#   Directory path on stdout
# Returns:
#   0
#######################################
llm_dir() {
  echo "${MODELS_DIR}/${LLM_REPO//\//__}_${LLM_TIER}"
}

#######################################
# Include glob for hf download (one file).
# Globals:
#   LLM_FILE
# Arguments:
#   None
# Outputs:
#   Include pattern on stdout
# Returns:
#   0
#######################################
llm_include_pattern() {
  printf '%s\n' "${LLM_FILE}"
}

#######################################
# Hugging Face repo id for the opt-in 35B GGUF.
# Globals:
#   LLM35_REPO
# Arguments:
#   None
# Outputs:
#   Repo id on stdout
# Returns:
#   0
#######################################
llm35_repo() {
  printf '%s\n' "${LLM35_REPO}"
}

#######################################
# Basename of the 35B UD-Q4_K_XL GGUF (pinned).
# Globals:
#   LLM35_FILE
# Arguments:
#   None
# Outputs:
#   Filename on stdout
# Returns:
#   0
#######################################
llm35_filename() {
  printf '%s\n' "${LLM35_FILE}"
}

#######################################
# Minimum ready size in GB for the 35B pack.
# Globals:
#   LLM35_MIN_GB
# Arguments:
#   None
# Outputs:
#   Integer GB on stdout
# Returns:
#   0
#######################################
llm35_min_gb() {
  printf '%s\n' "${LLM35_MIN_GB}"
}

#######################################
# Absolute local-dir for the 35B snapshot.
# Globals:
#   MODELS_DIR, LLM35_REPO, LLM35_TIER
# Arguments:
#   None
# Outputs:
#   Directory path on stdout
# Returns:
#   0
#######################################
llm35_dir() {
  echo "${MODELS_DIR}/${LLM35_REPO//\//__}_${LLM35_TIER}"
}

#######################################
# Include glob for the 35B hf download (one file).
# Globals:
#   LLM35_FILE
# Arguments:
#   None
# Outputs:
#   Include pattern on stdout
# Returns:
#   0
#######################################
llm35_include_pattern() {
  printf '%s\n' "${LLM35_FILE}"
}

#######################################
# Approximate on-disk size of the GGUF local-dir in GB.
# Globals:
#   None
# Arguments:
#   $1  Directory path
# Outputs:
#   Size with one decimal on stdout
# Returns:
#   0
#######################################
llm_size_gb() {
  local dir="${1}"
  if [[ ! -d ${dir} ]]; then
    echo 0
    return
  fi
  du -sk "${dir}" 2>/dev/null | awk '{printf "%.1f", $1/1024/1024}'
}

#######################################
# True if the enhance GGUF file is present and non-empty.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 ready; 1 not ready
#######################################
llm_files_ready() {
  local dir f
  dir="$(llm_dir)"
  f="${dir}/$(llm_filename)"
  if [[ -f ${f} && -s ${f} ]]; then
    return 0
  fi
  return 1
}

#######################################
# True if the 35B GGUF file is present and non-empty.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 ready; 1 not ready
#######################################
llm35_files_ready() {
  local dir f
  dir="$(llm35_dir)"
  f="${dir}/$(llm35_filename)"
  if [[ -f ${f} && -s ${f} ]]; then
    return 0
  fi
  return 1
}

#######################################
# Relative symlink the enhance GGUF into MODELS_DIR/comfy/llm/.
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
link_llm_into_comfy() {
  local src dest dir f
  dir="$(llm_dir)"
  f="${dir}/$(llm_filename)"
  src="${MODELS_DIR}/comfy/llm"
  dest="${src}/$(llm_filename)"
  [[ -f ${f} ]] || return 0
  if ! prepare_writable_layout_dir "${src}"; then
    if [[ -e ${dest} ]]; then
      return 0
    fi
    return 1
  fi
  if ln_sfn_relative "${f}" "${dest}"; then
    log "linked $(llm_filename) → comfy/llm/"
    return 0
  fi
  warn "failed to link $(llm_filename) → comfy/llm/"
  return 1
}

#######################################
# Relative symlink the 35B GGUF into MODELS_DIR/comfy/llm/.
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
link_llm35_into_comfy() {
  local src dest dir f
  dir="$(llm35_dir)"
  f="${dir}/$(llm35_filename)"
  src="${MODELS_DIR}/comfy/llm"
  dest="${src}/$(llm35_filename)"
  [[ -f ${f} ]] || return 0
  if ! prepare_writable_layout_dir "${src}"; then
    if [[ -e ${dest} ]]; then
      return 0
    fi
    return 1
  fi
  if ln_sfn_relative "${f}" "${dest}"; then
    log "linked $(llm35_filename) → comfy/llm/"
    return 0
  fi
  warn "failed to link $(llm35_filename) → comfy/llm/"
  return 1
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
    all) echo "enhance qwen36-35b-a3b" ;;
    enhance | qwen36-35b-a3b) echo "${TIER}" ;;
    *) echo "${TIER}" ;;
  esac
}

#######################################
# Refuse banned LLM packs (H3, 120B default, Flash-Next, DeepSeek-V4).
# Globals:
#   None
# Arguments:
#   $1  Tier or flag string
# Outputs:
#   Error on stderr when banned
# Returns:
#   0 allowed; 1 banned
#######################################
refuse_banned_llm_tier() {
  local raw="${1:-}"
  local lowered
  lowered="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]')"
  case "${lowered}" in
    *h3* | *minimax* | *120b* | *flash-next* | *flashnext* | *deepseek-v4* | \
      *deepseekv4* | *deepseek_v4*)
      err "Banned LLM tier: ${raw}. See docs/licenses.md"
      return 1
      ;;
  esac
  return 0
}

#######################################
# Parse CLI flags.
# Globals:
#   JSON_FLAG, CMD, CLEANUP_YES, TIER
# Arguments:
#   $@  CLI args
# Outputs:
#   Usage on stderr
# Returns:
#   0; exits 1 on unknown args
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --tier)
        TIER="${2:?}"
        if ! refuse_banned_llm_tier "${TIER}"; then
          exit 1
        fi
        shift
        ;;
      --tier=*)
        TIER="${1#--tier=}"
        if ! refuse_banned_llm_tier "${TIER}"; then
          exit 1
        fi
        ;;
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup | link) CMD="${1}" ;;
      enhance | qwen36-35b-a3b | all)
        TIER="${1}"
        ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup|link [--tier enhance|qwen36-35b-a3b|all] [--json] [--yes]" >&2
        echo "  Default enhance = ${LLM_FILE} from ${LLM_REPO} (Apache 2.0, download-models)" >&2
        echo "  qwen36-35b-a3b = ${LLM35_FILE} (~23 GB, occupancy llm-desk, not download-models)" >&2
        echo "  cleanup options: --dry-run (default) | --yes" >&2
        exit 0
        ;;
      *)
        if ! refuse_banned_llm_tier "${1}"; then
          exit 1
        fi
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
  case "${TIER}" in
    enhance | qwen36-35b-a3b | all) ;;
    *)
      err "Unknown tier: ${TIER} (want: enhance|qwen36-35b-a3b|all)"
      exit 1
      ;;
  esac
}

#######################################
# One JSON object for a concrete pack.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id (enhance|qwen36-35b-a3b)
# Outputs:
#   JSON object on stdout
# Returns:
#   0; 1 unknown tier
#######################################
tier_status_json() {
  local tier="${1}"
  local repo dir size min ready
  case "${tier}" in
    enhance)
      repo="$(llm_repo)"
      dir="$(llm_dir)"
      min="$(llm_min_gb)"
      ready="false"
      if llm_files_ready; then
        ready="true"
      fi
      ;;
    qwen36-35b-a3b)
      repo="$(llm35_repo)"
      dir="$(llm35_dir)"
      min="$(llm35_min_gb)"
      ready="false"
      if llm35_files_ready; then
        ready="true"
      fi
      ;;
    *)
      return 1
      ;;
  esac
  size="$(llm_size_gb "${dir}")"
  printf '{"tier":"%s","repo":"%s","path":"%s","size_gb":%s,"min_gb":%s,"ready":%s}' \
    "${tier}" "${repo}" "${dir}" "${size}" "${min}" "${ready}"
}

#######################################
# Read-only readiness report.
# Globals:
#   MODELS_DIR, JSON_FLAG, TIER
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; status on stderr otherwise
# Returns:
#   0; exits 1 on unknown tier
#######################################
cmd_status() {
  local results=()
  local tier json
  for tier in $(tiers_to_process); do
    json="$(tier_status_json "${tier}")" || {
      err "Unknown tier: ${tier}"
      exit 1
    }
    results+=("${json}")
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
      json="$(tier_status_json "${tier}")"
      log "$(printf '%s' "${json}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("%s: %s — %s GB at %s (ready=%s)" % (d["tier"], d["repo"], d["size_gb"], d["path"], d["ready"]))')"
    done
  fi
}

#######################################
# Download one pack if missing and link into comfy/llm.
# Globals:
#   MODELS_DIR
# Arguments:
#   $1  Tier id
# Outputs:
#   log/warn/err
# Returns:
#   0 on success; 1 if download failed
#######################################
run_one_tier() {
  local tier="${1}"
  local dir repo include ready_fn link_fn
  case "${tier}" in
    enhance)
      dir="$(llm_dir)"
      repo="$(llm_repo)"
      include="$(llm_include_pattern)"
      ready_fn=llm_files_ready
      link_fn=link_llm_into_comfy
      ;;
    qwen36-35b-a3b)
      dir="$(llm35_dir)"
      repo="$(llm35_repo)"
      include="$(llm35_include_pattern)"
      ready_fn=llm35_files_ready
      link_fn=link_llm35_into_comfy
      ;;
    *)
      err "Unknown tier: ${tier}"
      return 1
      ;;
  esac
  if "${ready_fn}"; then
    log "skip ${tier}: already present at ${dir} (cache hit)"
    "${link_fn}" || return 1
    return 0
  fi
  log "Downloading ${repo} selective subset (tier: ${tier})…"
  log "  include: ${include}"
  if HF_HOME="${MODELS_DIR}" hf_download "${repo}" --local-dir "${dir}" \
    --include "${include}"; then
    "${link_fn}" || return 1
    return 0
  fi
  warn "Partials kept under ${dir}; re-run to resume."
  err "LLM GGUF download failed (${tier}). Check hf CLI and network."
  return 1
}

#######################################
# Download selected GGUF pack(s) if missing and link into comfy/llm.
# Globals:
#   MODELS_DIR, TIER
# Arguments:
#   None
# Outputs:
#   log/warn/err
# Returns:
#   0 on success; 1 if download failed
#######################################
cmd_run() {
  local tier fail=0
  check_hf_cli
  prepare_comfy_layout "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  for tier in $(tiers_to_process); do
    if ! run_one_tier "${tier}"; then
      fail=1
    fi
  done
  cmd_status
  if [[ ${fail} -ne 0 ]]; then
    exit 1
  fi
  return 0
}

#######################################
# Relink snapshot GGUF(s) into MODELS_DIR/comfy/llm/ (no download).
# Globals:
#   MODELS_DIR, TIER
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
cmd_link() {
  local tier
  for tier in $(tiers_to_process); do
    case "${tier}" in
      enhance) link_llm_into_comfy ;;
      qwen36-35b-a3b) link_llm35_into_comfy ;;
    esac
  done
}

#######################################
# Remove extra files in the selected pack local-dir (keep the pinned GGUF).
# Globals:
#   CLEANUP_YES, TIER
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0
#######################################
cleanup_one_dir() {
  local dir="${1}"
  local keep="${2}"
  local label="${3}"
  local f rel
  if [[ ! -d ${dir} ]]; then
    log "cleanup ${label}: no directory at ${dir} (nothing to do)"
    return 0
  fi
  while IFS= read -r f; do
    [[ -z ${f} ]] && continue
    rel="${f#"${dir}"/}"
    case "${rel}" in
      "${keep}" | .gitattributes | LICENSE | README.md | .cache | .cache/* | *.incomplete | *.lock | *.lock.*)
        continue
        ;;
    esac
    if [[ ${CLEANUP_YES} -eq 1 ]]; then
      rm -f "${f}" || warn "Failed to remove ${f}"
      log "  removed: ${rel}"
    else
      log "  would remove: ${rel}"
    fi
  done < <(find "${dir}" -type f 2>/dev/null | LC_ALL=C sort)
}

#######################################
# Remove extra files in selected GGUF local-dir(s).
# Globals:
#   CLEANUP_YES, TIER
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0
#######################################
cmd_cleanup() {
  local tier
  for tier in $(tiers_to_process); do
    case "${tier}" in
      enhance)
        cleanup_one_dir "$(llm_dir)" "$(llm_filename)" "llm"
        ;;
      qwen36-35b-a3b)
        cleanup_one_dir "$(llm35_dir)" "$(llm35_filename)" "qwen36-35b-a3b"
        ;;
    esac
  done
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
    link) cmd_link ;;
    cleanup) cmd_cleanup ;;
    *)
      err "Usage: $0 status|run|cleanup|link [--tier enhance|qwen36-35b-a3b|all] [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
