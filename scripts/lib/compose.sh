#!/usr/bin/env bash
# ## compose
#
# Docker Compose wrappers for the unified ComfyUI flux-to-ltx stack.
#
# Purpose:
#   Isolate every docker/compose invocation behind helpers that pin the project
#   file (`docker/docker-compose.yml`) and project name (`ez-comfy`). This keeps
#   manage.sh thin and makes hermetic tests able to inject COMPOSE_BIN mocks.
#
# Audience:
#   Sourced by manage.sh after paths.sh and common.sh.
#
# Environment:
#   MODELS_DIR, COMFY_PORT, MEM_LIMIT, MEM_RESERVATION — exported into compose
#   COMPOSE_BIN — optional full command override for tests (space-separated ok)
#
# Safety:
#   stack_start does not ask for confirmation (caller must require_heavy_confirm).
#   stack_cleanup_state removes named volumes but never deletes host MODELS_DIR.
#

#######################################
# Print the base docker compose argv as separate words (for debugging/docs).
# Does not execute Docker. Useful when showing operators the equivalent command.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Prints words on stdout: docker compose -f <file> --project-name ez-comfy
#######################################
compose_cmd() {
  local file
  file="$(lab_compose_file)"
  echo "docker" "compose" "-f" "${file}" "--project-name" "ez-comfy"
}

#######################################
# Invoke `docker compose` against this repo's compose file with project name ez-comfy.
# If COMPOSE_BIN is set, that command is used instead (BATS installs a mock).
# All remaining arguments are forwarded as compose subcommands/flags.
# Side effects: May start/stop containers, build images, stream logs.
# shellcheck disable=SC2086
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  Compose arguments (e.g. `ps`, `up -d --build`, `down --remove-orphans`).
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of the compose process.
#######################################
compose_run() {
  if [[ -n ${COMPOSE_BIN:-} ]]; then
    # shellcheck disable=SC2086
    ${COMPOSE_BIN} "$@"
    return $?
  fi
  local file
  file="$(lab_compose_file)"
  docker compose -f "${file}" --project-name ez-comfy "$@"
}

#######################################
# Ensure the Docker CLI and Compose v2 plugin are available, or die.
# Side effects: May terminate the process.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 when both work; otherwise dies (exit 1).
#######################################
require_docker() {
  if ! check_docker_preflight; then
    die "Docker preflight failed (install with: ./scripts/manage.sh setup --install-docker)"
  fi
}

#######################################
# Emit a minimal JSON object describing the flux-to-ltx stack state on stdout.
# State values:
#   stopped  — no containers / empty ps output
#   running  — ps JSON mentions running
#   present  — containers exist but not clearly running
#   unknown  — compose ps failed (Docker down, etc.)
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Always 0 after printing one JSON line to stdout.
#######################################
compose_status_json() {
  local ps_out state="unknown"
  if ps_out=$(compose_run ps --format json 2>/dev/null); then
    if [[ -z ${ps_out} || ${ps_out} == "[]" ]]; then
      state="stopped"
    elif echo "${ps_out}" | grep -q '"running"\|"Running"\|running'; then
      state="running"
    else
      state="present"
    fi
  else
    state="unknown"
  fi
  printf '{"stack":"flux-to-ltx","state":"%s"}\n' "${state}"
}

#######################################
# Predicate: true if the comfyui service is listed among running compose services.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 when running; 1 otherwise.
#######################################
compose_is_running() {
  local out
  out=$(compose_run ps --status running --services 2>/dev/null || true)
  [[ ${out} == *comfyui* ]]
}

#######################################
# After compose up, fail if comfyui is not running; print ps -a and recent logs.
# Globals:
#   None (uses compose_run)
# Arguments:
#   $1  Optional settle seconds (default 3)
# Outputs:
#   Status/errors on stderr; compose ps/logs on failure
# Returns:
#   0 if running; 1 if not
#######################################
stack_verify_running() {
  local settle="${1:-3}"
  local i retries=3
  if [[ ${settle} -gt 0 ]]; then
    sleep "${settle}"
  else
    retries=1
  fi
  i=0
  while [[ ${i} -lt ${retries} ]]; do
    i=$((i + 1))
    if compose_is_running; then
      return 0
    fi
    if [[ ${i} -lt ${retries} ]]; then
      sleep 1
    fi
  done
  err "Container is not running after start (restart: no → exits stay stopped)."
  warn "compose ps -a:"
  compose_run ps -a 2>/dev/null || true
  warn "Recent comfyui logs:"
  compose_run logs --tail 80 comfyui 2>/dev/null || true
  err "Tips: ./scripts/manage.sh logs — if volume was poisoned by a failed first start:"
  err "  ./scripts/manage.sh stop && docker volume rm ez-comfy-state  # then start again"
  err "  Stop other GPU containers if nvidia runtime fails; check free RAM vs MEM_RESERVATION"
  return 1
}

#######################################
# Build images if needed and start the unified stack detached (`up -d --build`).
# Exports default env for compose interpolation, ensures MODELS_DIR/comfy exists,
# and logs cold-start expectations. Does not confirm with the user.
# Side effects: Network/image pulls, container create/start, mkdir under MODELS_DIR.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 when up and container running; non-zero on compose or verify failure.
#######################################
stack_start() {
  require_docker
  export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
  export COMFY_PORT="${COMFY_PORT:-8188}"
  export MEM_LIMIT="${MEM_LIMIT:-90g}"
  export MEM_RESERVATION="${MEM_RESERVATION:-80g}"
  ensure_models_dir "${MODELS_DIR}" || return 1
  mkdir -p "${MODELS_DIR}/comfy"
  log "Starting unified flux-to-ltx stack (mem_limit=${MEM_LIMIT})..."
  if ! compose_run up -d --build; then
    err "compose up failed"
    compose_run ps -a 2>/dev/null || true
    compose_run logs --tail 80 comfyui 2>/dev/null || true
    return 1
  fi
  # LAB_STACK_VERIFY_SETTLE=0 skips sleep in hermetic tests
  if ! stack_verify_running "${LAB_STACK_VERIFY_SETTLE:-3}"; then
    return 1
  fi
  log "Stack starting. UI: http://localhost:${COMFY_PORT}"
  log "Cold start (first install) may take 10–30+ minutes — follow: ./scripts/manage.sh logs"
}

#######################################
# Stop and remove stack containers while retaining named volumes and host models.
# Uses `compose down --remove-orphans` without `-v` so comfy-state survives for
# faster subsequent starts.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of compose down.
#######################################
stack_stop() {
  require_docker
  log "Stopping stack (volumes retained)..."
  compose_run down --remove-orphans
  log "Stopped."
}

#######################################
# Follow compose logs for the project (default: all services).
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  Extra args forwarded to `compose logs -f` (service names, --tail, etc.).
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of compose logs (often interrupted by Ctrl-C).
#######################################
stack_logs() {
  require_docker
  compose_run logs -f "$@"
}

#######################################
# Stop the stack and delete Compose-managed volumes (Comfy install state).
# Does **not** delete host MODELS_DIR. Caller must obtain DELETE confirmation first.
# Side effects: Irreversible removal of the ez-comfy-state volume contents.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of `compose down -v`.
#######################################
stack_cleanup_state() {
  require_docker
  log "Removing project volumes (models host path is NOT deleted)..."
  compose_run down -v --remove-orphans
  log "Comfy state volume removed."
}
