#!/usr/bin/env bash
#
# ## studio-tui
#
# Guarded full-screen operator console for the studio. One curses front end over
# every manage.sh verb and every unmanaged utility: stack lifecycle, model tier
# downloads, occupancy desk, sidecars, film and cut tools, disk reclaim, and the
# lab lane browser.
#
# The console dispatches to the existing scripts. It never builds a docker
# command, never writes .occupancy.json, and never sets LAB_NON_INTERACTIVE or
# LAB_CONFIRM_TOKEN, so require_heavy_confirm and require_delete_confirm still
# run in the child. Heavy actions stay behind the same 28 GiB RAM and 40 GiB
# disk floors that gate manage.sh start.
#
# Usage:
#   bazelisk run //:studio-tui
#   bazelisk run //:studio-tui -- --check
#   bazelisk run //scripts:run-utility -- studio-tui [flags]   (operator escape hatch)
#
# Flags:
#   --check            validate the catalog and guard wiring, print a report, exit
#   --json             with --check, emit the report as JSON
#   --dry-run          dispatch prints the argv and does not run it
#   --read-only        only observe-only actions may dispatch
#   --no-color         monochrome (also honoured via NO_COLOR)
#   --group NAME       open on one section instead of the dashboard
#   --timeout SECONDS  per-command cap, default 900
#
# Environment:
#   MODELS_DIR, COMFY_OUTPUT_DIR, COMFY_PORT, MEM_LIMIT, DOWNLOAD_LIMIT
#   NO_COLOR, TERM, TERMINFO
#
# Safety:
#   One console at a time: an flock on ${COMFY_OUTPUT_DIR}/.studio-tui.lock
#   refuses the second copy, which is the mutex the CLI itself never had.
#   Refuses to draw when stdout is not a TTY; --check is the headless path.
#
# @command studio-tui

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=../lib/check_tool.sh disable=SC1091
source "${SCRIPT_DIR}/../lib/check_tool.sh"
# Dispatch against the git checkout, never the runfiles tree: the console reads
# workflows/_lab and execs scripts/manage.sh, and a runfiles path would point it
# at a copy with no .env and no outputs (same reasoning as utilities/runner.sh).
REPO_ROOT="$(bazel_checkout_root)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

#######################################
# Print studio-tui usage.
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
  echo "Usage: studio-tui.sh [--check] [--json] [--dry-run] [--read-only]" >&2
  echo "                     [--no-color] [--group NAME] [--timeout SECONDS]" >&2
  echo "  Guarded operator console over the studio stack (curses, no new dependency)." >&2
  echo "  --check validates the catalog and the guard wiring without a TTY." >&2
  echo "  Heavy actions keep the CLI's typed confirmations and the headroom floors." >&2
  echo '  One console at a time: flock on ${COMFY_OUTPUT_DIR}/.studio-tui.lock.' >&2
}

#######################################
# Run the console, or the headless self-check.
# Globals:
#   REPO_ROOT, COMFY_OUTPUT_DIR, MODELS_DIR
# Arguments:
#   $@  flags forwarded to tui.cli
# Outputs:
#   TUI on the TTY; the --check report on stdout
# Returns:
#   python status; 3 when another console already holds the flock (owned by
#   tui.runner.ConsoleLock, which is the only lock implementation)
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  REPO_ROOT="$(bazel_checkout_root)"
  export PYTHONPATH="${REPO_ROOT}/custom_nodes:${REPO_ROOT}/scripts/lib${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${REPO_ROOT}"
  exec python3 -m tui.cli "$@"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
