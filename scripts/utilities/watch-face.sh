#!/usr/bin/env bash
#
# ## watch-face
#
# Emit submittable Wear OS watch face projects in the Watch Face Format: the
# `res/raw/watchface.xml` scene, the ambient variant that meets the
# illuminated-area rule, previews, the metadata and settings XML, and the
# store listing copy.
#
# Purpose:
#   A sellable Wear face is a strict XML dialect plus a compliance checklist.
#   This verb generates the project and runs the gate over it, so an operator
#   ships a folder that the Play console accepts instead of hand-writing XML.
#
# Usage:
#   bazelisk run //scripts:run-utility -- watch-face --out DIR
#   bazelisk run //scripts:run-utility -- watch-face --out DIR --face SLUG
#   bazelisk run //scripts:run-utility -- watch-face --out DIR --style analog
#   bazelisk run //scripts:run-utility -- watch-face --validate-only --out DIR
#
# Flags:
#   --out DIR            folder the projects are written into (required)
#   --face SLUG          build one face; repeatable
#   --style NAME         build one style only
#   --catalog FILE       JSON override merged over the shipped catalog
#   --wff-version N      Watch Face Format version to declare, 1 to 4
#   --preview-edge PX    square preview edge, at least the catalog minimum
#   --size-variants      also write the round small and large shapes file
#   --validate-only      build into scratch, run the compliance gate, report
#   --dry-run            compute and report, write nothing
#
# Environment:
#   COMFY_OUTPUT_DIR   suggested parent for --out when the operator passes none
#
# Safety:
#   Does not start Docker, does not queue ComfyUI, does not touch occupancy or
#   the headroom preflight. Writes only inside --out. The compliance gate is
#   fail-closed: a face that misses the ambient, size, or slot limits exits 1.
#
# Exit codes:
#   0 projects written or gate clean; 1 usage error or a compliance failure.
#
# @command watch-face

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"
# Dispatch against the git checkout so --out lands where the operator expects.
REPO_ROOT="$(bazel_checkout_root)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Print watch-face usage.
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
  echo "Usage: watch-face.sh --out DIR [--face SLUG] [--style NAME] [--catalog FILE]" >&2
  echo "                   [--wff-version N] [--preview-edge PX] [--size-variants]" >&2
  echo "                   [--validate-only] [--dry-run]" >&2
  echo "  Emit a submittable Wear OS Watch Face Format project and gate it." >&2
}

#######################################
# Run the watch face generator.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  flags forwarded to ez_watch.project.main
# Outputs:
#   One line per face plus every compliance finding on stdout
# Returns:
#   python status; 1 on a usage error or any error-severity finding
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  REPO_ROOT="$(bazel_checkout_root)"
  export PYTHONPATH="${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${REPO_ROOT}"
  exec python3 -m ez_watch.project "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
