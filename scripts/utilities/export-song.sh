#!/usr/bin/env bash
#
# ## export-song
#
# Hand a generated or imported song over to a human sequencer: MIDI, MusicXML,
# the timeline JSON, per-lane MIDI and band-limited WAV stems, and an import
# guide, all in one bundle folder.
#
# Purpose:
#   The stack prototypes a track with AI. Finishing it needs the notes, not a
#   flattened mix, so this verb runs the stdlib transcriber over one master and
#   writes the whole DAW hand-off at once. CPU only; no GPU, no ComfyUI queue.
#
# Usage:
#   bazelisk run //scripts:run-utility -- export-song AUDIO OUT_DIR
#   bazelisk run //scripts:run-utility -- export-song AUDIO OUT_DIR --title NAME
#   bazelisk run //scripts:run-utility -- export-song AUDIO OUT_DIR --no-stems
#   bazelisk run //scripts:run-utility -- export-song AUDIO OUT_DIR --no-quantize
#
# Flags:
#   AUDIO              master audio file to convert (wav, flac, mp3, m4a)
#   OUT_DIR            folder the bundle is written into (created if missing)
#   --title NAME       song title, defaulting to the file's tag or filename
#   --beats-per-bar N  bar length used when engraving the MusicXML (default 4)
#   --no-stems         skip the band-limited WAV stems
#   --no-quantize      keep the transcriber's raw note timing
#
# Environment:
#   COMFY_OUTPUT_DIR   suggested parent for OUT_DIR when the operator passes none
#
# Outputs:
#   <OUT_DIR>/<slug>/ with <slug>.mid, <slug>.musicxml, timeline.json,
#   stems/NN-<lane>.{mid,wav}, audio/<master>, project.md, manifest.json.
#
# Safety:
#   Read-only on the input. Does not start Docker, does not queue ComfyUI, does
#   not touch occupancy, restart: "no", or the headroom preflight. ffmpeg and
#   ffprobe are required on PATH and are the only external commands.
#
# Exit codes:
#   0 bundle written; 1 bad arguments, missing master, or a failed probe.
#
# @command export-song

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"
# Run against the git checkout so the bundle lands where the operator expects
# it and the runfiles copy is only a fallback (same reasoning as runner.sh).
REPO_ROOT="$(bazel_checkout_root)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Print export-song usage.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Help on stderr
# Returns:
#   0
#######################################
cmd_help() {
  echo "Usage: export-song.sh AUDIO OUT_DIR [--title NAME] [--beats-per-bar N]" >&2
  echo "                                   [--no-stems] [--no-quantize]" >&2
  echo "  Convert one master into a DAW bundle: MIDI, MusicXML, timeline JSON," >&2
  echo "  per-lane MIDI and WAV stems, and a project.md import guide." >&2
  echo "  CPU only; needs ffmpeg and ffprobe on PATH." >&2
}

#######################################
# Require ffmpeg and ffprobe on PATH.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Failure reason on stderr when either tool is missing
# Returns:
#   0 when both are present; 1 otherwise
#######################################
require_ffmpeg_pair() {
  local tool
  for tool in ffmpeg ffprobe; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      err "${tool} is required for export-song (do not skip). Install ffmpeg and retry."
      return 1
    fi
  done
  return 0
}

#######################################
# Run the exporter.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  flags forwarded to ez_music.song_export.main
# Outputs:
#   Bundle summary on stdout
# Returns:
#   python status; 1 on a bad path or a failed probe
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  require_ffmpeg_pair || return 1
  REPO_ROOT="$(bazel_checkout_root)"
  export PYTHONPATH="${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${REPO_ROOT}"
  exec python3 -m ez_music.song_export "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
