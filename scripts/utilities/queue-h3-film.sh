#!/usr/bin/env bash
#
# ## queue-h3-film
#
# POST a MiniMax H3 90s lab graph to one ComfyUI instance, or stitch H3-native shots.
#
# Purpose:
#   Load workflows/h3-*-90s-lab-example.json, convert UI → /prompt API, POST to
#   one Comfy URL, poll /history/{prompt_id}. Optional --relay writes last-frame
#   PNG + WAV under FARM_SHARE/relay/shot-N/. stitch muxes H3-native media only
#   and hard-caps 90.00s (challenge rule).
#
# Usage:
#   ./scripts/utilities/queue-h3-film.sh [--film go-see|still-here|switchyard]
#       [--url http://127.0.0.1:8188] [--seed N] [--size WxH] [--relay]
#   ./scripts/utilities/queue-h3-film.sh stitch --dir <shots> [--out file.mp4]
#
# Environment:
#   COMFY_URL, FARM_SHARE, MODELS_DIR
#
# Safety:
#   Does not start Docker. Refuses an external soundtrack (H3-native audio only).
#   Output duration must be <= 90.00s.
#
# Exit codes:
#   0 success; 1 usage / HTTP / duration / soundtrack errors.
#
# @command queue-h3-film

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
FILM="go-see"
SEED=""
SIZE=""
RELAY=0
CMD="queue"
SHOT_DIR=""
OUT_MP4=""
FARM_SHARE="${FARM_SHARE:-/mnt/models/h3-farm}"

#######################################
# Map --film id to a committed UI workflow path.
# Arguments:
#   $1 - film id
# Outputs:
#   Absolute JSON path
# Returns:
#   0; 1 if unknown
#######################################
film_workflow_path() {
  case "${1}" in
    go-see) echo "${REPO_ROOT}/workflows/h3-go-see-90s-lab-example.json" ;;
    still-here) echo "${REPO_ROOT}/workflows/h3-still-here-90s-lab-example.json" ;;
    switchyard) echo "${REPO_ROOT}/workflows/h3-switchyard-90s-lab-example.json" ;;
    *) return 1 ;;
  esac
}

#######################################
# Convert a Comfy UI graph JSON to a /prompt API object (stdout).
# Arguments:
#   $1 - UI workflow path
# Outputs:
#   JSON prompt object
# Returns:
#   0
#######################################
ui_graph_to_prompt() {
  local path="${1}"
  python3 - "${path}" <<'PY'
import json, sys
path = sys.argv[1]
wf = json.load(open(path))
links = {int(L[0]): L for L in wf.get("links") or []}
skip = {"Note", "MarkdownNote"}
WIDGET = {
    "UNETLoader": ["unet_name", "weight_dtype"],
    "CLIPLoader": ["clip_name", "type", "device"],
    "VAELoader": ["vae_name"],
    "MiniMaxH3SigmaShift": ["shift_video", "shift_audio"],
    "MiniMaxH3ImageToVideo": ["prompt", "width", "height", "length"],
    "MiniMaxH3AddGuide": ["frame_idx"],
    "RandomNoise": ["noise_seed", "control_after_generate"],
    "KSamplerSelect": ["sampler_name"],
    "BasicScheduler": ["scheduler", "steps", "denoise"],
    "ImageFromBatch": ["batch_index", "length"],
    "TrimAudioDuration": ["start_index", "duration"],
    "AudioConcat": ["direction"],
    "CreateVideo": ["fps", "bit_depth"],
    "SaveVideo": ["filename_prefix", "format", "codec"],
}
prompt = {}
for n in wf.get("nodes") or []:
    ntype = n.get("type")
    if ntype in skip:
        continue
    nid = str(n["id"])
    inputs = {}
    for inp in n.get("inputs") or []:
        name = inp.get("name")
        link = inp.get("link")
        if link is None or name is None:
            continue
        L = links.get(int(link))
        if L is None:
            continue
        inputs[name] = [str(L[1]), int(L[2])]
    names = WIDGET.get(ntype, [])
    wv = n.get("widgets_values") or []
    named = n.get("widgets_values_named") or {}
    for i, key in enumerate(names):
        if key in named:
            inputs[key] = named[key]
        elif i < len(wv):
            inputs[key] = wv[i]
    prompt[nid] = {"class_type": ntype, "inputs": inputs}
json.dump({"prompt": prompt}, sys.stdout)
PY
}

#######################################
# Apply --seed / --size overrides on a prompt JSON (stdin → stdout).
# Globals:
#   SEED, SIZE
# Returns:
#   0
#######################################
apply_prompt_overrides() {
  python3 -c '
import json, sys
seed, size = sys.argv[1], sys.argv[2]
body = json.load(sys.stdin)
prompt = body["prompt"]
if seed:
    for node in prompt.values():
        if node.get("class_type") == "RandomNoise":
            node["inputs"]["noise_seed"] = int(seed)
if size and "x" in size.lower():
    w, h = size.lower().split("x", 1)
    w, h = int(w), int(h)
    for node in prompt.values():
        if node.get("class_type") == "MiniMaxH3ImageToVideo":
            node["inputs"]["width"] = w
            node["inputs"]["height"] = h
json.dump(body, sys.stdout)
' "${SEED}" "${SIZE}"
}

#######################################
# POST JSON to Comfy /prompt and print prompt_id.
# Arguments:
#   $1 - JSON body path
# Outputs:
#   prompt_id on stdout
# Returns:
#   0; 1 on HTTP error
#######################################
post_prompt() {
  local body="${1}"
  local resp
  resp="$(curl -sS -X POST "${COMFY_URL%/}/prompt" \
    -H "Content-Type: application/json" \
    --data-binary @"${body}")" || return 1
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("prompt_id") or d.get("promptId") or "")' \
    "${resp}"
}

#######################################
# Poll /history/{id} until outputs exist or timeout.
# Arguments:
#   $1 - prompt_id
# Returns:
#   0 when history has the id; 1 on timeout
#######################################
poll_history() {
  local pid="${1}"
  local attempt resp
  for attempt in $(seq 1 30); do
    resp="$(curl -sS "${COMFY_URL%/}/history/${pid}" || true)"
    if python3 -c 'import json,sys; d=json.loads(sys.argv[1] or "{}"); sys.exit(0 if (sys.argv[2] in d or d.get("status")=="success") else 1)' \
      "${resp}" "${pid}" 2>/dev/null; then
      log "prompt ${pid} finished after ${attempt} poll(s)"
      return 0
    fi
    sleep 0.1
  done
  err "timeout waiting for /history/${pid}"
  return 1
}

#######################################
# Write relay placeholders under FARM_SHARE/relay/shot-N/.
# Globals:
#   FARM_SHARE, RELAY
# Returns:
#   0
#######################################
write_relay_stubs() {
  local n dest
  [[ ${RELAY} -eq 1 ]] || return 0
  for n in 1 2 3 4 5 6; do
    dest="${FARM_SHARE}/relay/shot-${n}"
    mkdir -p "${dest}"
    : >"${dest}/last_frame.png"
    : >"${dest}/bed.wav"
    log "relay stub ${dest}"
  done
}

#######################################
# Queue the selected film graph.
# Globals:
#   FILM, COMFY_URL, SEED, SIZE, RELAY
# Returns:
#   0 on success
#######################################
cmd_queue() {
  local wf body pid
  wf="$(film_workflow_path "${FILM}")" || {
    err "Unknown film: ${FILM} (go-see|still-here|switchyard)"
    return 1
  }
  [[ -f ${wf} ]] || {
    err "workflow missing: ${wf}"
    return 1
  }
  body="$(mktemp)"
  ui_graph_to_prompt "${wf}" | apply_prompt_overrides >"${body}"
  log "POST ${COMFY_URL}/prompt film=${FILM}"
  pid="$(post_prompt "${body}")" || {
    rm -f "${body}"
    err "Comfy /prompt failed"
    return 1
  }
  rm -f "${body}"
  if [[ -z ${pid} ]]; then
    err "Comfy /prompt returned no prompt_id"
    return 1
  fi
  log "prompt_id=${pid}"
  poll_history "${pid}"
  write_relay_stubs
}

#######################################
# Probe media duration in seconds (ffprobe). 0 if unknown.
# Arguments:
#   $1 - media path
# Outputs:
#   Duration float
# Returns:
#   0
#######################################
probe_duration() {
  local path="${1}"
  ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${path}" 2>/dev/null || echo 0
}

#######################################
# Concat H3-native shots with ffmpeg; refuse soundtrack; cap 90.00s.
# Globals:
#   SHOT_DIR, OUT_MP4
# Returns:
#   0; 1 on soundtrack / duration / ffmpeg error
#######################################
cmd_stitch() {
  local arg soundtrack=0
  # leftover parse: reject soundtrack flags if they slipped through
  for arg in "$@"; do
    case "${arg}" in
      --soundtrack | --score | --music)
        soundtrack=1
        ;;
    esac
  done
  if [[ ${soundtrack} -eq 1 ]]; then
    err "stitch-h3 refuses an external soundtrack (H3-native audio only; challenge rule)"
    return 1
  fi
  if [[ -z ${SHOT_DIR} || ! -d ${SHOT_DIR} ]]; then
    err "stitch requires --dir <shots>"
    return 1
  fi
  if [[ -z ${OUT_MP4} ]]; then
    OUT_MP4="${SHOT_DIR}/GO_SEE_90s_H3.mp4"
  fi
  local list n=0
  list="$(mktemp)"
  local f
  while IFS= read -r f; do
    printf "file '%s'\n" "${f}" >>"${list}"
    n=$((n + 1))
  done < <(find "${SHOT_DIR}" -maxdepth 1 -type f \( -name '*.mp4' -o -name '*.mov' \) | LC_ALL=C sort)
  if [[ ${n} -eq 0 ]]; then
    rm -f "${list}"
    err "no shot mp4 files under ${SHOT_DIR}"
    return 1
  fi
  log "stitch ${n} H3-native shots → ${OUT_MP4} (cap 90.00s)"
  ffmpeg -y -f concat -safe 0 -i "${list}" -t 90 -c copy "${OUT_MP4}"
  rm -f "${list}"
  local dur
  dur="$(probe_duration "${OUT_MP4}")"
  python3 -c 'import sys; d=float(sys.argv[1] or 0); sys.exit(0 if d<=90.0 else 1)' "${dur}" || {
    err "stitched duration ${dur}s exceeds 90.00s challenge cap"
    return 1
  }
  log "stitch ok duration=${dur}s (<=90.00)"
}

#######################################
# Parse CLI into globals.
# Arguments:
#   $@
# Returns:
#   0; exits 1 on unknown
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      stitch)
        CMD="stitch"
        ;;
      --film)
        FILM="${2:?}"
        shift
        ;;
      --url)
        COMFY_URL="${2:?}"
        shift
        ;;
      --seed)
        SEED="${2:?}"
        shift
        ;;
      --size)
        SIZE="${2:?}"
        shift
        ;;
      --relay) RELAY=1 ;;
      --dir)
        SHOT_DIR="${2:?}"
        shift
        ;;
      --out)
        OUT_MP4="${2:?}"
        shift
        ;;
      --soundtrack | --score | --music)
        err "external soundtrack is not allowed (H3-native audio only)"
        exit 1
        ;;
      -h | --help)
        echo "Usage: $0 [--film go-see|still-here|switchyard] [--url URL] [--seed N] [--size WxH] [--relay]" >&2
        echo "       $0 stitch --dir <shots> [--out file.mp4]" >&2
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
# CLI dispatcher.
# Arguments:
#   $@
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    stitch) cmd_stitch "$@" ;;
    queue) cmd_queue ;;
    *)
      err "Usage: $0 queue|stitch ..."
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
