#!/usr/bin/env bash
# ## paths
#
# Path resolution helpers for ez-comfy-stack operator scripts and utilities.
#
# Purpose:
#   Provide a single way to locate the repository root, Docker Compose file, and
#   shared model cache without hard-coding absolute paths.
#
# Audience:
#   Sourced by entry scripts under scripts/ and scripts/utilities/. Not executable.
#
# Style:
#   Follows the Google Shell Style Guide with project deviations documented in
#   docs/project-conventions.md (notably #!/usr/bin/env bash).
#
# Environment:
#   REPO_ROOT   — optional override for the repository root (must be a directory)
#   MODELS_DIR  — optional override for the shared model cache (default /mnt/models)
#

#######################################
# Resolve an absolute directory path relative to the calling script.
# Walks dirname of BASH_SOURCE[1] (the sourcer), then climbs N parents.
# Globals:
#   None
# Arguments:
#   $1 - Non-negative parent segments to climb (default 0)
#   $2 - Unused; reserved for lab API compatibility
# Outputs:
#   Writes absolute path to stdout
# Returns:
#   0 on success; non-zero if cd fails
#######################################
lab_script_dir() {
  local climb="${1:-0}"
  local dir
  dir="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
  local i
  for ((i = 0; i < climb; i++)); do
    dir="$(cd "${dir}/.." && pwd)"
  done
  echo "${dir}"
}

#######################################
# Resolve the absolute path of the ez-comfy-stack repository root.
# Prefers REPO_ROOT when set to an existing directory; otherwise two parents
# above this library file.
# Globals:
#   REPO_ROOT (read, optional)
# Arguments:
#   None
# Outputs:
#   Writes absolute repo root path to stdout
# Returns:
#   0 when resolution succeeds
#######################################
lab_repo_root() {
  local script_dir
  if [[ -n ${REPO_ROOT:-} && -d ${REPO_ROOT} ]]; then
    echo "${REPO_ROOT}"
    return 0
  fi
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${script_dir}/../.." && pwd
}

#######################################
# Absolute path to the unified stack Docker Compose file.
# Globals:
#   None (uses lab_repo_root)
# Arguments:
#   None
# Outputs:
#   Writes absolute path to stdout (does not check existence)
# Returns:
#   0
#######################################
lab_compose_file() {
  echo "$(lab_repo_root)/docker/docker-compose.yml"
}

#######################################
# Path for the shared Hugging Face / Comfy model cache.
# Globals:
#   MODELS_DIR (read, optional; default /mnt/models)
# Arguments:
#   None
# Outputs:
#   Writes models directory path to stdout
# Returns:
#   0
#######################################
lab_models_dir() {
  echo "${MODELS_DIR:-/mnt/models}"
}

#######################################
# Host directory for ComfyUI generated media (PNG, MP4).
# Globals:
#   COMFY_OUTPUT_DIR (read, optional; default /mnt/comfy-output)
# Arguments:
#   None
# Outputs:
#   Writes output directory path to stdout
# Returns:
#   0
#######################################
lab_comfy_output_dir() {
  echo "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
}
