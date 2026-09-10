#!/usr/bin/env bash
#
# ## dub-fetch
#
# Optional URL ingest for the dub lane (yt-dlp). Writes into COMFY_OUTPUT_DIR/input.
#
# Purpose:
#   Pull operator-owned / licensed media into COMFY_OUTPUT_DIR/input so
#   EZDubIngest Source file can select it. YouTube ToS still applies.
#   Not baked into the Docker image.
#
# Audience:
#   Operators on the Spark host.
#
# Usage:
#   ./scripts/utilities/dub-fetch.sh status|run --url URL [--out DIR]
#
# Environment:
#   COMFY_OUTPUT_DIR, LAB_MOCK_YT_DLP
#
# Safety:
#   Opt-in. Does not start Docker. Refuses empty/non-http URLs.
#   Does not commit cookies. Occupancy unchanged.
#
# Exit codes:
#   0 success; 1 usage / missing yt-dlp / fetch failure.
#
# @command dub-fetch

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

CMD="status"
URL=""
OUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}/input"

#######################################
# True when the string is an http(s) URL.
# Globals:
#   None
# Arguments:
#   $1  Candidate
# Outputs:
#   None
# Returns:
#   0 if URL; 1 otherwise
#######################################
dub_is_http_url() {
  local raw="${1:-}"
  case "${raw}" in
    http://* | https://*) return 0 ;;
    *) return 1 ;;
  esac
}

#######################################
# Require yt-dlp or the hermetic mock.
# Globals:
#   LAB_MOCK_YT_DLP
# Arguments:
#   None
# Outputs:
#   Error on stderr when missing
# Returns:
#   0 ready; 1 missing
#######################################
dub_require_ytdlp() {
  if [[ ${LAB_MOCK_YT_DLP:-} == "1" ]]; then
    return 0
  fi
  if command -v yt-dlp >/dev/null 2>&1; then
    return 0
  fi
  err "yt-dlp is not on PATH. Install it for URL ingest, or pass a local file to EZDubIngest."
  return 1
}

#######################################
# Parse CLI flags.
# Globals:
#   CMD, URL, OUT_DIR
# Arguments:
#   $@  CLI args
# Outputs:
#   Usage on stderr
# Returns:
#   0; exits 1 on unknown args
#######################################
dub_fetch_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --url)
        URL="${2:?}"
        shift
        ;;
      --out)
        OUT_DIR="${2:?}"
        shift
        ;;
      status | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status|run --url URL [--out DIR]" >&2
        echo "  Writes into COMFY_OUTPUT_DIR/input (survives cleanup)." >&2
        echo "  Operator-owned or licensed URLs only. See docs/dub.md." >&2
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
# Read-only yt-dlp / output report.
# Globals:
#   OUT_DIR, LAB_MOCK_YT_DLP
# Arguments:
#   None
# Outputs:
#   Status on stderr
# Returns:
#   0 if yt-dlp or mock is available; 1 otherwise
#######################################
dub_fetch_cmd_status() {
  local has=0
  if [[ ${LAB_MOCK_YT_DLP:-} == "1" ]] || command -v yt-dlp >/dev/null 2>&1; then
    has=1
  fi
  log "dub-fetch out=${OUT_DIR} ytdlp=${has} mock=${LAB_MOCK_YT_DLP:-0}"
  if [[ ${has} -eq 1 ]]; then
    return 0
  fi
  err "yt-dlp missing — URL ingest will not silently skip"
  return 1
}

#######################################
# Fetch one URL into OUT_DIR.
# Globals:
#   URL, OUT_DIR, LAB_MOCK_YT_DLP
# Arguments:
#   None
# Outputs:
#   log/err; downloaded path on stderr
# Returns:
#   0 on success; 1 on missing url/tool/failure
#######################################
dub_fetch_cmd_run() {
  if ! dub_is_http_url "${URL}"; then
    err "dub-fetch --url must be http(s). Got: ${URL:-empty}"
    return 1
  fi
  dub_require_ytdlp || return 1
  mkdir -p "${OUT_DIR}"
  local dest="${OUT_DIR}/ez_dub_fetch.%(ext)s"
  if [[ ${LAB_MOCK_YT_DLP:-} == "1" ]]; then
    echo "mock" >"${OUT_DIR}/ez_dub_fetch.wav"
    log "dub-fetch mock → ${OUT_DIR}/ez_dub_fetch.wav"
    return 0
  fi
  if ! yt-dlp --no-playlist -f "bestaudio/best" -o "${dest}" "${URL}"; then
    err "yt-dlp failed for ${URL}"
    return 1
  fi
  log "dub-fetch wrote under ${OUT_DIR}"
  return 0
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@ - CLI args
#######################################
main() {
  dub_fetch_parse_args "$@"
  case "${CMD}" in
    status) dub_fetch_cmd_status ;;
    run) dub_fetch_cmd_run ;;
    *)
      err "Usage: $0 status|run --url URL [--out DIR]"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
