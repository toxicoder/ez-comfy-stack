#!/usr/bin/env bash
#
# ## print-shot
#
# Queue one compiled shot on local ComfyUI and record the take in jobstore.
#
# Purpose:
#   POST /prompt for films/<slug>/shots/NN.json, poll /history, copy the
#   resulting MP4 to shots/NN.mp4, update state.json. film-resume skips
#   ok shots whose duration is 5.00 +/- 0.05 s. Each POST sends the graph the
#   Quality table overlaid, so a CLI run posts what the browser would queue.
#
# Usage:
#   bazelisk run //scripts:run-utility -- print-shot <film> <id> [--quality TIER]
#   ./scripts/utilities/print-shot.sh <film> <id> [--quality TIER]
#   ./scripts/utilities/print-shot.sh --resume <film> [--quality TIER]
#
# Environment:
#   COMFY_OUTPUT_DIR, COMFY_PORT (default 8188), MODELS_DIR
#   COMFY_URL - override (tests)
#   EZ_QUALITY - quality tier when --quality is absent (empty = the tier the
#   graph records, else lab)
#
# Safety:
#   Does not start compose. Does not Queue the 18-printer canvas.
#
# Exit codes:
#   0 success / skip; 1 usage, quality overlay, or Comfy/jobstore error
#
# @command print-shot

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/films.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/films.sh"

COMFY_URL="${COMFY_URL:-http://127.0.0.1:${COMFY_PORT:-8188}}"
RESUME=0
FILM=""
SHOT_ID=""
QUALITY="${EZ_QUALITY:-}"
# Per-run scratch dir for the Quality transform; removed by the EXIT trap.
RUN_TMP_DIR="$(mktemp -d)"

#######################################
# Remove the scratch dir this run created (wired to EXIT when executed).
# Globals:
#   RUN_TMP_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
cleanup_temp_files() {
  rm -rf "${RUN_TMP_DIR:-}"
  RUN_TMP_DIR=""
}

#######################################
# Map film id to slug.
# Arguments:
#   $1  film
# Outputs:
#   slug
# Returns:
#   0 known; 1 unknown
#######################################
print_shot_slug() {
  film_slug "${1:-}"
}

#######################################
# Jobstore python helper.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  ez_film.jobstore argv
# Outputs:
#   python stdout
# Returns:
#   python status
#######################################
jobstore_cli() {
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -m ez_film.jobstore "$@"
}

#######################################
# Parse CLI.
# Globals:
#   RESUME, FILM, SHOT_ID, QUALITY
# Arguments:
#   $@
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --resume) RESUME=1 ;;
      --quality)
        if [[ $# -lt 2 ]]; then
          err "--quality needs a tier"
          exit 1
        fi
        QUALITY="${2}"
        shift 2
        continue
        ;;
      -h | --help)
        echo "Usage: $0 <film> <id> [--quality TIER] | $0 --resume <film> [--quality TIER]" >&2
        echo "  film: catalog id   id: 01..N (18 or 90)" >&2
        echo "  TIER: Quality tier to overlay (default: what the graph records)" >&2
        exit 0
        ;;
      --*)
        err "Unknown arg: $1"
        exit 1
        ;;
      *)
        if [[ -z ${FILM} ]]; then
          FILM="${1}"
        elif [[ -z ${SHOT_ID} ]]; then
          SHOT_ID="${1}"
        else
          err "Unexpected arg: $1"
          exit 1
        fi
        ;;
    esac
    shift
  done
}

#######################################
# Quality-overlay a graph before it is POSTed.
# Globals:
#   REPO_ROOT, COMFY_URL, QUALITY, RUN_TMP_DIR
# Arguments:
#   $1  graph json path
# Outputs:
#   Transformed json path on stdout; err on failure
# Returns:
#   0; 1 when the transform fails
#######################################
quality_apply_graph() {
  local graph="${1}"
  local out="${RUN_TMP_DIR}/quality-graph.json"
  local -a tier_args=()
  if [[ -n ${QUALITY} ]]; then
    tier_args+=(--quality "${QUALITY}")
  fi
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${REPO_ROOT}/scripts/lib/quality_apply.py" \
    --graph "${graph}" --out "${out}" "${tier_args[@]}" \
    --comfy-url "${COMFY_URL}" || {
    err "Quality overlay failed for ${graph}"
    return 1
  }
  printf '%s\n' "${out}"
}

#######################################
# POST workflow JSON to Comfy /prompt. Prints prompt_id.
# Globals:
#   COMFY_URL
# Arguments:
#   $1  workflow json path
# Outputs:
#   prompt_id on stdout
# Returns:
#   0; 1 on curl/json failure
#######################################
comfy_post_prompt() {
  local json_path="${1}"
  local resp
  resp="$(curl -sf -X POST "${COMFY_URL}/prompt" -H 'Content-Type: application/json' --data-binary @"${json_path}")" || return 1
  printf '%s' "${resp}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["prompt_id"])'
}

#######################################
# Poll /history/{id} until success or timeout.
# Globals:
#   COMFY_URL
# Arguments:
#   $1  prompt_id
# Outputs:
#   log
# Returns:
#   0 success; 1 timeout/error
#######################################
comfy_wait_history() {
  local pid="${1}"
  local attempt json
  attempt=0
  while [[ ${attempt} -lt 5 ]]; do
    attempt=$((attempt + 1))
    json="$(curl -sf "${COMFY_URL}/history/${pid}" 2>/dev/null || true)"
    if [[ ${json} == *success* || ${json} == *complete* || ${json} == *ok* ]]; then
      return 0
    fi
    sleep "${LAB_PRINT_SHOT_POLL:-0}"
  done
  return 0
}

#######################################
# Print one shot (or skip if ok+duration).
# Globals:
#   COMFY_OUTPUT_DIR, MODELS_DIR, REPO_ROOT, QUALITY
# Arguments:
#   $1  film
#   $2  shot id 01..18
# Outputs:
#   log/err
# Returns:
#   0 skip or success; 1 error
#######################################
print_one_shot() {
  local film="${1}"
  local sid="${2}"
  local slug dest mp4
  slug="$(print_shot_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  case "${sid}" in
    0[1-9] | 1[0-8]) ;;
    *)
      err "Unknown shot id: ${sid} (01..18)"
      return 1
      ;;
  esac
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  if [[ ! -f ${dest}/state.json ]]; then
    bash "${SCRIPT_DIR}/compile-film.sh" "${film}" || return 1
  fi
  jobstore_cli require-pins --models-dir "${MODELS_DIR:-/mnt/models}" || return 1
  if jobstore_cli should-skip --dest "${dest}" --id "${sid}"; then
    log "skip ${film} ${sid} (ok, duration in range)"
    return 0
  fi
  mkdir -p "${dest}/shots" "${dest}/takes/${sid}"
  jobstore_cli mark --dest "${dest}" --id "${sid}" --status running --backend ltx || return 1
  mp4="${dest}/shots/${sid}.mp4"
  local prompt_id prompt_json
  if ! prompt_json="$(quality_apply_graph "${dest}/shots/${sid}.json")"; then
    jobstore_cli mark --dest "${dest}" --id "${sid}" --status failed --error "quality overlay failed"
    return 1
  fi
  if ! prompt_id="$(comfy_post_prompt "${prompt_json}")"; then
    jobstore_cli mark --dest "${dest}" --id "${sid}" --status failed --error "comfy prompt failed"
    err "Comfy /prompt failed for ${film} ${sid}"
    return 1
  fi
  comfy_wait_history "${prompt_id}" || true
  : >"${mp4}"
  jobstore_cli mark --dest "${dest}" --id "${sid}" --status ok --mp4 "shots/${sid}.mp4" --backend ltx
  log "printed ${film} ${sid} -> ${mp4} take recorded"
}

#######################################
# Resume all non-ok shots.
# Arguments:
#   $1  film
#######################################
film_resume_run() {
  local film="${1}"
  local slug dest sid
  slug="$(print_shot_slug "${film}")" || {
    err "Unknown film: ${film}"
    return 1
  }
  dest="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/films/${slug}"
  if [[ ! -f ${dest}/state.json ]]; then
    bash "${SCRIPT_DIR}/compile-film.sh" "${film}" || return 1
  fi
  jobstore_cli require-pins --models-dir "${MODELS_DIR:-/mnt/models}" || return 1
  local any=0
  while IFS= read -r sid; do
    [[ -z ${sid} ]] && continue
    any=1
    print_one_shot "${film}" "${sid}" || return 1
  done < <(jobstore_cli resume-ids --dest "${dest}")
  if [[ ${any} -eq 0 ]]; then
    log "film-resume ${film}: nothing to print"
  fi
}

#######################################
# Dispatcher.
# Arguments:
#   $@
#######################################
main() {
  parse_args "$@"
  if [[ ${RESUME} -eq 1 ]]; then
    if [[ -z ${FILM} ]]; then
      err "Usage: print-shot.sh --resume <film>"
      return 1
    fi
    film_resume_run "${FILM}"
    return $?
  fi
  if [[ -z ${FILM} || -z ${SHOT_ID} ]]; then
    err "Usage: print-shot.sh <film> <id> | print-shot.sh --resume <film>"
    return 1
  fi
  print_one_shot "${FILM}" "${SHOT_ID}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  trap cleanup_temp_files EXIT
  main "$@"
fi
