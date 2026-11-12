#!/usr/bin/env bash
#
# ## icon-pack
#
# Build a sellable Android adaptive-icon pack from the in-tree catalog: one
# vector foreground plus density-rasterized PNGs per app, the launcher content
# provider JSON, the drawable sets Play requires, and a listing draft.
#
# Purpose:
#   Turning a set of app icons into a shippable pack is mostly compliance
#   work - adaptive layers, every launcher density, the appfilter XML, the
#   512 px store icon. This verb owns that structure; the catalog owns which
#   apps exist and how each glyph is drawn.
#
# Usage:
#   bazelisk run //scripts:run-utility -- icon-pack --out DIR
#   bazelisk run //scripts:run-utility -- icon-pack --out DIR --icon SLUG
#   bazelisk run //scripts:run-utility -- icon-pack --out DIR --category NAME
#   bazelisk run //scripts:run-utility -- icon-pack --catalog FILE --out DIR
#   bazelisk run //scripts:run-utility -- icon-pack --validate-only --out DIR
#   bazelisk run //scripts:run-utility -- icon-pack --scaffold new-app-slug
#
# Flags:
#   --out DIR           project directory to write
#   --catalog FILE      operator JSON merged over the shipped catalog
#   --icon SLUG         publish only this slug (repeatable)
#   --category NAME     publish only this category (repeatable)
#   --art-dir DIR       directory of <slug>.png master art to prefer
#   --pack-name NAME    pack name for the listing and strings
#   --pack-version VER  pack version for the manifest
#   --validate-only     run the compliance gate over a built pack and report
#   --scaffold SLUG     print the override row a new app needs, then exit
#   --name LABEL        human label used with --scaffold
#   --package ID        application id used with --scaffold
#   --glyph ID          recipe id used with --scaffold
#   --dry-run           report the file list, write nothing
#
# Environment:
#   COMFY_OUTPUT_DIR   suggested parent for --out when the operator passes none
#
# Safety:
#   Does not start Docker, does not queue ComfyUI, does not touch occupancy or
#   the headroom preflight. Writes only inside --out. Never embeds a trademarked
#   logo: the catalog holds generated geometric recipes only.
#
# Exit codes:
#   0 pack written or gate clean; 1 usage error or a compliance failure.
#
# @command icon-pack

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"
# Dispatch against the git checkout so --out lands where the operator expects.
REPO_ROOT="$(bazel_checkout_root)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Print icon-pack usage.
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
  echo "Usage: icon-pack.sh --out DIR [--catalog FILE] [--icon SLUG] [--category NAME]" >&2
  echo "                  [--art-dir DIR] [--pack-name NAME] [--pack-version VER]" >&2
  echo "                  [--dry-run] [--validate-only] [--scaffold SLUG]" >&2
  echo "                  [--name LABEL] [--package ID] [--glyph ID]" >&2
  echo "  Build a store-ready Android adaptive icon pack from the catalog." >&2
  echo "  --scaffold prints the override row for a newly released app." >&2
}

#######################################
# Run the icon pack generator.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  flags forwarded to ez_icons.pack.main
# Outputs:
#   Build report on stdout
# Returns:
#   python status; 1 on a usage error or a failed compliance gate
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  REPO_ROOT="$(bazel_checkout_root)"
  export PYTHONPATH="${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${REPO_ROOT}"
  exec python3 -m ez_icons.pack "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
