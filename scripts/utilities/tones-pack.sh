#!/usr/bin/env bash
#
# ## tones-pack
#
# Render the in-tree tone catalog and package a sellable Android ringtone,
# notification, and alarm pack: WAV masters plus M4A and OGG per tone, the
# manifest a launcher imports, and the store listing copy.
#
# Purpose:
#   A tone pack that sells is a catalog, three codecs per tone, and the loudness
#   discipline that keeps a notification from blowing an ear out. The catalog
#   owns the motifs; this verb owns the encoding and the bundle.
#
# Usage:
#   bazelisk run //scripts:run-utility -- tones-pack --out DIR
#   bazelisk run //scripts:run-utility -- tones-pack --out DIR --kind notification
#   bazelisk run //scripts:run-utility -- tones-pack --out DIR --tone glass-two-note
#   bazelisk run //scripts:run-utility -- tones-pack --template FILE
#   bazelisk run //scripts:run-utility -- tones-pack --out DIR --dry-run
#
# Flags:
#   --out DIR             pack directory to write
#   --kind KIND           build only this kind; repeatable
#   --tone SLUG           build only this tone; repeatable
#   --catalog FILE        operator catalog JSON merged over the shipped pack
#   --template FILE       write the operator catalog template here and exit
#   --pack-name NAME      name stamped on the pack
#   --version VER         version stamped on the pack
#   --sample-rate HZ      44100 or 48000 for every file
#   --dry-run             print the plan, write nothing
#
# Environment:
#   COMFY_OUTPUT_DIR   suggested parent for --out when the operator passes none
#
# Safety:
#   Does not start Docker, does not queue ComfyUI, does not touch occupancy or
#   the headroom preflight. Writes only inside --out. ffmpeg is required on
#   PATH and is the only external command.
#
# Exit codes:
#   0 pack written or plan printed; 1 usage error or an encoding failure.
#
# @command tones-pack

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"
# Dispatch against the git checkout so --out lands where the operator expects.
REPO_ROOT="$(bazel_checkout_root)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Print tones-pack usage.
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
  echo "Usage: tones-pack.sh [--out DIR] [--kind KIND] [--tone SLUG] [--catalog FILE]" >&2
  echo "                   [--template FILE] [--pack-name NAME] [--version VER]" >&2
  echo "                   [--sample-rate 44100|48000] [--dry-run]" >&2
  echo "  Render the tone catalog and package an Android tone pack." >&2
  echo "  Needs ffmpeg on PATH; writes WAV, M4A, and OGG per tone." >&2
}

#######################################
# Require ffmpeg on PATH.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Failure reason on stderr when ffmpeg is missing
# Returns:
#   0 when ffmpeg is present; 1 otherwise
#######################################
require_ffmpeg() {
  if ! command -v ffmpeg >/dev/null 2>&1; then
    err "ffmpeg is required for tones-pack (do not skip). Install ffmpeg and retry."
    return 1
  fi
  return 0
}

#######################################
# Run the tone pack generator.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  flags forwarded to ez_tones.pack.main
# Outputs:
#   Build report on stdout
# Returns:
#   python status; 1 on a usage error or a failed encode
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  require_ffmpeg || return 1
  REPO_ROOT="$(bazel_checkout_root)"
  export PYTHONPATH="${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${REPO_ROOT}"
  exec python3 -m ez_tones.pack "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
