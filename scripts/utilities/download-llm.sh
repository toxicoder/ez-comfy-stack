#!/usr/bin/env bash
#
# ## download-llm
#
# Download the on-box prompt-enhance GGUF (Qwen3-4B-Instruct-2507 Q4_K_M).
#
# Purpose:
#   Selective Hugging Face pull for the Spark-local prompt rewriter.
#   Apache 2.0. File-level include — not the full Unsloth GGUF tree.
#
# Audience:
#   Operators on the Spark host. Prefer manage.sh download-models.
#
# Usage:
#   ./scripts/utilities/download-llm.sh status [--json]
#   ./scripts/utilities/download-llm.sh run
#   ./scripts/utilities/download-llm.sh link
#   ./scripts/utilities/download-llm.sh cleanup [--dry-run|--yes]
#
# Environment:
#   MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD
#
# Safety:
#   ~2.5 GB. Use download-limit wrap on remote SSH.
#
# Exit codes:
#   0 success; 1 usage/CLI errors.
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
JSON_FLAG=""
CMD="status"
CLEANUP_YES=0
readonly LLM_REPO="unsloth/Qwen3-4B-Instruct-2507-GGUF"
readonly LLM_FILE="Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
readonly LLM_MIN_GB=3
readonly LLM_TIER="llm"

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
# True if the GGUF file is present and non-empty.
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
# Relative symlink the GGUF into MODELS_DIR/comfy/llm/.
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
  mkdir -p "${src}"
  [[ -f ${f} ]] || return 0
  dest="${src}/$(llm_filename)"
  if ln_sfn_relative "${f}" "${dest}"; then
    log "linked $(llm_filename) → comfy/llm/"
  else
    warn "failed to link $(llm_filename) → comfy/llm/"
  fi
}

#######################################
# Parse CLI flags.
# Globals:
#   JSON_FLAG, CMD, CLEANUP_YES
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
      --dry-run) CLEANUP_YES=0 ;;
      --yes | -y) CLEANUP_YES=1 ;;
      status | run | cleanup | link) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run|cleanup|link [--json] [--yes]" >&2
        echo "  Default = ${LLM_FILE} from ${LLM_REPO} (Apache 2.0)" >&2
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
# Read-only readiness report.
# Globals:
#   MODELS_DIR, JSON_FLAG
# Arguments:
#   None
# Outputs:
#   JSON on stdout when --json; status on stderr otherwise
# Returns:
#   0
#######################################
cmd_status() {
  local dir size ready
  dir="$(llm_dir)"
  size="$(llm_size_gb "${dir}")"
  ready="false"
  if llm_files_ready; then
    ready="true"
  fi
  if [[ ${JSON_FLAG} == "--json" ]]; then
    printf '{"tiers":[{"tier":"llm","repo":"%s","path":"%s","size_gb":%s,"min_gb":%s,"ready":%s}],"models_dir":"%s"}\n' \
      "$(llm_repo)" "${dir}" "${size}" "$(llm_min_gb)" "${ready}" "${MODELS_DIR}"
  else
    log "llm: $(llm_repo) — ${size} GB at ${dir} (ready=${ready})"
  fi
}

#######################################
# Download the GGUF if missing and link into comfy/llm.
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   log/warn/err
# Returns:
#   0 on success; 1 if download failed
#######################################
cmd_run() {
  local dir
  check_hf_cli
  ensure_models_dir "${MODELS_DIR}" || exit 1
  clear_stale_hf_locks "${MODELS_DIR}"
  dir="$(llm_dir)"
  if llm_files_ready; then
    log "skip llm: already present at ${dir} (cache hit)"
    link_llm_into_comfy
    cmd_status
    return 0
  fi
  log "Downloading $(llm_repo) selective subset (tier: llm)…"
  log "  include: $(llm_include_pattern)"
  if HF_HOME="${MODELS_DIR}" hf_download "$(llm_repo)" --local-dir "${dir}" \
    --include "$(llm_include_pattern)"; then
    link_llm_into_comfy
    cmd_status
    return 0
  fi
  warn "Partials kept under ${dir}; re-run to resume."
  err "LLM GGUF download failed. Check hf CLI and network."
  exit 1
}

#######################################
# Relink the snapshot GGUF into MODELS_DIR/comfy/llm/ (no download).
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0
#######################################
cmd_link() {
  link_llm_into_comfy
}

#######################################
# Remove extra files in the GGUF local-dir (keep the Q4_K_M file).
# Globals:
#   CLEANUP_YES
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0
#######################################
cmd_cleanup() {
  local dir f rel keep
  dir="$(llm_dir)"
  keep="$(llm_filename)"
  if [[ ! -d ${dir} ]]; then
    log "cleanup llm: no directory at ${dir} (nothing to do)"
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
      err "Usage: $0 status|run|cleanup|link [--json] [--yes]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
