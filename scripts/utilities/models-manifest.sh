#!/usr/bin/env bash
#
# ## models-manifest
#
# status | keep-set | render for config/model-manifest.yaml
#
# Usage:
#   ./scripts/utilities/models-manifest.sh status|keep-set|render
#
# @command models-manifest

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/models.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/models.sh"

CMD="${1:-status}"

#######################################
# Print keep-set.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   basenames
# Returns:
#   0
#######################################
cmd_keep_set() {
  models_keep_set
}

#######################################
# Print refuse list + pack JSON.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   human status
# Returns:
#   0
#######################################
cmd_status() {
  log "manifest $(models_manifest_path)"
  log "keep-set:"
  models_keep_set | while IFS= read -r f; do
    log "  ${f}"
  done
  log "refuse:"
  models_refuse_list | while IFS= read -r f; do
    log "  ${f}"
  done
}

#######################################
# Dump parsed JSON.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   JSON stdout
# Returns:
#   0
#######################################
cmd_render() {
  python3 "${REPO_ROOT}/scripts/lib/model_manifest.py" \
    --manifest "$(models_manifest_path)" json
}

#######################################
# CLI.
# Arguments:
#   $@
#######################################
main() {
  case "${CMD}" in
    status) cmd_status ;;
    keep-set) cmd_keep_set ;;
    render) cmd_render ;;
    -h | --help | help)
      echo "Usage: $0 status|keep-set|render" >&2
      exit 0
      ;;
    *)
      err "Usage: $0 status|keep-set|render"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
