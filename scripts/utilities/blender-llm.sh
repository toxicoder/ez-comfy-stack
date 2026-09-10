#!/usr/bin/env bash
#
# ## blender-llm
#
# Optional on-box Qwen3-4B CPU client for blender-mcp. Fail-soft: if host
# llama.cpp is missing, print the Path D hint (laptop MCP client).
# Never GPU-offload. Never in docker/Dockerfile.
#
# Usage:
#   ./scripts/utilities/blender-llm.sh "greybox mug on a table"
#
# @command blender-llm

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"
# shellcheck source=../lib/occupancy.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/occupancy.sh"

#######################################
# Print blender-llm help.
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
  echo "Usage: blender-llm.sh PROMPT" >&2
  echo "  Optional host llama.cpp + existing Qwen3-4B GGUF → blender-mcp." >&2
  echo "  CPU only. Path D if llama-cli is missing. Never in Dockerfile." >&2
}

#######################################
# Default GGUF path (same file as prompt-enhance).
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   Path on stdout
# Returns:
#   0
#######################################
llm_gguf_path() {
  echo "${MODELS_DIR:-/mnt/models}/comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
}

#######################################
# Path D hint when host llama.cpp is missing.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Hint on stderr
# Returns:
#   0
#######################################
print_path_d_hint() {
  err "host llama.cpp not found (llama-cli / llama_cpp)."
  err "Path D: laptop Grok/Cursor MCP client → SSH tunnel to blender-mcp."
  err "  ./scripts/manage.sh occupancy enter blender-desk"
  err "  ./scripts/manage.sh blender-mcp --stdio"
}

#######################################
# True when a host llama binary or python module exists.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 present; 1 missing
#######################################
host_llama_available() {
  if command -v llama-cli >/dev/null 2>&1; then
    return 0
  fi
  if command -v llama-cpp-python >/dev/null 2>&1; then
    return 0
  fi
  python3 -c 'import llama_cpp' 2>/dev/null
}

#######################################
# Run one prompt through llama-cli (or mock) then blender-mcp --call.
# Globals:
#   MODELS_DIR, LAB_MOCK_LLAMA
# Arguments:
#   $@  prompt words
# Outputs:
#   Tool result JSON on stdout
# Returns:
#   0; 1 missing llama / occupancy / tool failure
#######################################
cmd_run() {
  if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "help" ]]; then
    cmd_help
    return 0
  fi
  if [[ $# -eq 0 ]]; then
    err "blender-llm.sh requires a prompt"
    cmd_help
    return 1
  fi
  local prompt="$*"
  if [[ -n ${LAB_MOCK_LLAMA:-} ]]; then
    python3 "${REPO_ROOT}/scripts/lib/blender_mcp.py" --call occupancy_status
    return $?
  fi
  if ! host_llama_available; then
    print_path_d_hint
    return 1
  fi
  refuse_if_heavy_gpu "Blender LLM (occupancy)" || return $?
  local gguf
  gguf="$(llm_gguf_path)"
  if [[ ! -f ${gguf} ]]; then
    err "GGUF missing: ${gguf} (download-llm / download-models)"
    return 1
  fi
  log "llama-cli CPU only (do not GPU-offload next to Comfy)"
  local out
  out="$(llama-cli -m "${gguf}" -ngl 0 -p "${prompt}" --no-display-prompt 2>/dev/null || true)"
  if [[ ${out} == *create_primitive* ]]; then
    python3 "${REPO_ROOT}/scripts/lib/blender_mcp.py" --call create_primitive '{"kind":"cube","name":"llm-cube"}'
    return $?
  fi
  python3 "${REPO_ROOT}/scripts/lib/blender_mcp.py" --call occupancy_status
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  cmd_run "$@"
fi
