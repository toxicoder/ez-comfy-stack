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
# True if ComfyUI port accepts TCP connections on localhost.
# Globals:
#   COMFY_PORT
# Arguments:
#   $1  Optional port (default COMFY_PORT or 8188)
# Outputs:
#   None
# Returns:
#   0 if open; 1 otherwise
#######################################
stack_port_open() {
  local port="${1:-${COMFY_PORT:-8188}}"
  if command -v curl >/dev/null 2>&1; then
    curl -sf -o /dev/null --connect-timeout 1 "http://127.0.0.1:${port}/" 2>/dev/null && return 0
    # Comfy may not answer HTTP until fully up; TCP is enough
  fi
  if command -v nc >/dev/null 2>&1; then
    nc -z -w 1 127.0.0.1 "${port}" 2>/dev/null && return 0
  fi
  # Bash /dev/tcp fallback
  (echo >/dev/tcp/127.0.0.1/"${port}") >/dev/null 2>&1 && return 0
  return 1
}

#######################################
# True if ComfyUI /object_info lists MiniMaxH3AddGuide (native v0.34.0).
# Globals:
#   COMFY_PORT, LAB_MOCK_H3_OBJECT_INFO, LAB_HERMETIC
# Arguments:
#   $1  Optional port (default COMFY_PORT or 8188)
# Returns:
#   0 if registered; 1 if missing
#######################################
comfy_h3_object_info_ok() {
  local port="${1:-${COMFY_PORT:-8188}}"
  local url="http://127.0.0.1:${port}/object_info/MiniMaxH3AddGuide"
  case "${LAB_MOCK_H3_OBJECT_INFO:-}" in
    1 | ok | yes) return 0 ;;
    0 | missing | no) return 1 ;;
  esac
  if [[ ${LAB_HERMETIC:-0} == "1" ]]; then
    return 0
  fi
  curl -sf --connect-timeout 2 --max-time 8 "${url}" 2>/dev/null | grep -q 'MiniMaxH3AddGuide'
}

#######################################
# True if the image prebuilt tree will load MiniMaxH3 extras (nodes.py list).
# Globals:
#   None
# Returns:
#   0 if prebuilt has the loader
#######################################
comfy_prebuilt_has_h3_loader() {
  compose_run exec -T comfyui grep -q 'nodes_minimax_h3.py' /opt/comfy-prebuilt/nodes.py &&
    compose_run exec -T comfyui grep -q 'MiniMaxH3AddGuide' \
      /opt/comfy-prebuilt/comfy_extras/nodes_minimax_h3.py
}

#######################################
# Remove volume install stamp + pin so the next entrypoint reseeds Comfy.
# Globals:
#   None
# Returns:
#   0 (stamp removal is best-effort)
#######################################
comfy_volume_clear_install_stamp() {
  compose_run exec -T comfyui rm -f \
    /comfy-state/ComfyUI/.lab-install-complete \
    /comfy-state/ComfyUI/.lab-comfyui-ref || true
}

#######################################
# After the UI is up, confirm native MiniMaxH3 nodes are registered.
# If /object_info lacks MiniMaxH3AddGuide and the image has v0.34 extras,
# clear the volume stamp and restart once so entrypoint reseeds. Never
# suggests pip install comfyui-manager — these are core nodes.
# Globals:
#   COMFY_PORT, LAB_SKIP_H3_NODE_PROBE, LAB_STACK_FOLLOW, LAB_HERMETIC,
#   LAB_FORCE_H3_NODE_PROBE
# Returns:
#   0 if registered or probe skipped; 1 if still missing after one repair
#######################################
ensure_comfy_h3_native_nodes() {
  local waited=0
  if [[ ${LAB_SKIP_H3_NODE_PROBE:-0} == "1" ]]; then
    return 0
  fi
  if [[ ${LAB_FORCE_H3_NODE_PROBE:-0} != "1" ]]; then
    if [[ ${LAB_STACK_FOLLOW:-} == "0" || ${LAB_HERMETIC:-0} == "1" ]]; then
      return 0
    fi
  fi
  if ! stack_port_open "${COMFY_PORT:-8188}"; then
    warn "Comfy UI not up — skip MiniMaxH3 node probe"
    return 0
  fi
  if comfy_h3_object_info_ok; then
    log "Native MiniMaxH3AddGuide registered (core v0.34.0 — not a custom pack)"
    return 0
  fi
  warn "MiniMaxH3* missing from /object_info (volume Comfy is too old)"
  warn "These are core v0.34.0 nodes. Do not pip install comfyui-manager"
  warn "Do not restart with --enable-manager"
  if comfy_prebuilt_has_h3_loader; then
    log "Image has H3 extras — clearing volume stamp and restarting to reseed v0.34.0"
    comfy_volume_clear_install_stamp
    compose_run restart || {
      err "compose restart failed while reseeding native H3 nodes"
      return 1
    }
    while [[ ${waited} -lt 120 ]]; do
      if stack_port_open "${COMFY_PORT:-8188}"; then
        break
      fi
      sleep 2
      waited=$((waited + 2))
    done
    if comfy_h3_object_info_ok; then
      log "Native MiniMaxH3AddGuide registered after volume reseed"
      return 0
    fi
  fi
  err "MiniMaxH3AddGuide still not registered. git pull, stop, start."
  err "If GHCR is still 0.29: LAB_STACK_FORCE_BUILD=1 ./scripts/manage.sh start"
  err "Confirm: docker exec ez-comfy-flux-to-ltx grep nodes_minimax_h3.py /comfy-state/ComfyUI/nodes.py"
  err "Do not pip install comfyui-manager"
  return 1
}

#######################################
# Stream compose logs and poll until UI port is open (or timeout / detach).
# Ctrl+C detaches follower only — container keeps running.
# Globals:
#   COMFY_PORT, LAB_STACK_FOLLOW, LAB_STACK_READY_TIMEOUT, LAB_STACK_HEARTBEAT
# Arguments:
#   None
# Outputs:
#   Progress logs; compose log stream to stderr
# Returns:
#   0 always (timeout warns but leaves container running)
#######################################
stack_follow_until_ready() {
  local port="${COMFY_PORT:-8188}"
  local timeout_s="${LAB_STACK_READY_TIMEOUT:-2700}"
  local heartbeat_s="${LAB_STACK_HEARTBEAT:-30}"
  local t0 now elapsed log_pid=""
  local follow="${LAB_STACK_FOLLOW:-}"

  if [[ -z ${follow} ]]; then
    if [[ -t 1 || -t 2 ]]; then
      follow=1
    else
      follow=0
    fi
  fi
  if [[ ${follow} == "0" ]]; then
    log "LAB_STACK_FOLLOW=0 — not streaming logs; use: ./scripts/manage.sh logs"
    return 0
  fi

  if stack_port_open "${port}"; then
    log "ComfyUI already responding on http://localhost:${port}"
    ensure_comfy_h3_native_nodes || return 1
    return 0
  fi

  log "Streaming container logs until UI is ready on :${port} (timeout ${timeout_s}s)"
  log "Ctrl+C detaches this view only — container keeps installing/running"
  log "Re-attach anytime: ./scripts/manage.sh logs"

  t0="$(date +%s)"
  local last_hb=0 aborted=0
  set +m 2>/dev/null || true
  (
    compose_run logs -f --tail 50 2>&1
  ) &
  log_pid=$!
  disown "${log_pid}" 2>/dev/null || true

  # shellcheck disable=SC2329
  _stack_follow_cleanup() {
    if [[ -n ${log_pid} ]] && kill -0 "${log_pid}" 2>/dev/null; then
      kill "${log_pid}" 2>/dev/null || true
      wait "${log_pid}" 2>/dev/null || true
    fi
  }
  trap 'aborted=1' INT TERM

  while true; do
    if [[ ${aborted} -eq 1 ]]; then
      _stack_follow_cleanup
      trap - INT TERM
      log "Detached from log stream (container still running). ./scripts/manage.sh logs"
      return 0
    fi
    if stack_port_open "${port}"; then
      _stack_follow_cleanup
      trap - INT TERM
      log "✓ ComfyUI is up — http://localhost:${port}"
      ensure_comfy_h3_native_nodes || return 1
      return 0
    fi
    if ! compose_is_running; then
      _stack_follow_cleanup
      trap - INT TERM
      err "Container exited during install — see logs above"
      compose_run ps -a 2>/dev/null || true
      return 1
    fi
    now="$(date +%s)"
    elapsed=$((now - t0))
    if [[ ${elapsed} -ge ${timeout_s} ]]; then
      _stack_follow_cleanup
      trap - INT TERM
      warn "Timed out after ${elapsed}s waiting for :${port} (install may still be running)"
      warn "Continue with: ./scripts/manage.sh logs"
      return 0
    fi
    if [[ $((elapsed - last_hb)) -ge ${heartbeat_s} ]]; then
      log "… still waiting for ComfyUI on :${port} (elapsed ${elapsed}s; container running)"
      last_hb=${elapsed}
    fi
    sleep 2
  done
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
#######################################
# Resolve the current git branch for GHCR image channel selection.
# Prefers LAB_GIT_BRANCH (tests / hermetic override); else git rev-parse.
# Globals:
#   LAB_GIT_BRANCH (optional)
# Arguments:
#   None
# Outputs:
#   Branch name on stdout (or "unknown")
# Returns:
#   0
#######################################
stack_git_branch() {
  if [[ -n ${LAB_GIT_BRANCH:-} ]]; then
    echo "${LAB_GIT_BRANCH}"
    return 0
  fi
  local root branch
  root="$(lab_repo_root)"
  branch="$(git -C "${root}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ -z ${branch} || ${branch} == "HEAD" ]]; then
    echo "unknown"
    return 0
  fi
  echo "${branch}"
}

#######################################
# Map a git branch name to the published GHCR image tag channel.
# Aligns with publish-image.yml: main → flux-to-ltx; development →
# flux-to-ltx-development; feature/other → development channel.
# Globals:
#   None
# Arguments:
#   $1  Git branch name
# Outputs:
#   Image tag (without registry) on stdout
# Returns:
#   0
#######################################
stack_image_tag_for_branch() {
  local branch="${1:-unknown}"
  case "${branch}" in
    main)
      echo "flux-to-ltx"
      ;;
    *)
      # development, feature/*, detached/unknown → integration channel
      echo "flux-to-ltx-development"
      ;;
  esac
}

#######################################
# Resolve default GHCR image ref (public package; no credentials in repo).
# Uses EZ_COMFY_IMAGE when set; otherwise branch-aligned tag from
# stack_git_branch + stack_image_tag_for_branch (matches publish-image.yml).
# Globals:
#   EZ_COMFY_IMAGE, LAB_GIT_BRANCH
# Arguments:
#   None
# Outputs:
#   Image ref on stdout
# Returns:
#   0
#######################################
stack_default_image() {
  if [[ -n ${EZ_COMFY_IMAGE:-} ]]; then
    echo "${EZ_COMFY_IMAGE}"
    return 0
  fi
  local tag
  tag="$(stack_image_tag_for_branch "$(stack_git_branch)")"
  echo "ghcr.io/toxicoder/ez-comfy:${tag}"
}

#######################################
# Try docker pull of prebuilt image; return 0 if usable.
# Globals:
#   None
# Arguments:
#   $1  Image reference
# Outputs:
#   Status logs
# Returns:
#   0 if pull ok or image already local; 1 on failure
#######################################
stack_pull_image() {
  local img="${1:?}"
  if [[ ${LAB_STACK_SKIP_PULL:-0} == "1" ]]; then
    log "LAB_STACK_SKIP_PULL=1 — not pulling ${img}"
    return 1
  fi
  log "Pulling prebuilt image ${img} (GHCR; no model weights inside)…"
  if docker pull "${img}"; then
    log "Pull ok: ${img}"
    return 0
  fi
  warn "Pull failed for ${img} — will build locally if needed (long if prebuild enabled)"
  return 1
}

#######################################
# Build images if needed and start the unified stack detached.
# Prefers GHCR pull; falls back to compose build. Seeds volume from prebuilt.
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
  export EZ_COMFY_IMAGE
  local branch
  branch="$(stack_git_branch)"
  EZ_COMFY_IMAGE="$(stack_default_image)"
  ensure_models_dir "${MODELS_DIR}" || return 1
  mkdir -p "${MODELS_DIR}/comfy"
  log "══ start ══ unified flux-to-ltx (mem_limit=${MEM_LIMIT})"
  log "Image: ${EZ_COMFY_IMAGE} (branch=${branch})"

  local up_args=(up -d)
  if [[ ${LAB_STACK_FORCE_BUILD:-0} == "1" ]]; then
    log "LAB_STACK_FORCE_BUILD=1 — compose up --build (may take a long time)"
    up_args+=(--build)
  elif stack_pull_image "${EZ_COMFY_IMAGE}"; then
    log "Using pulled image (compose up without rebuild)"
  else
    log "Building image locally (Dockerfile prebuild installs torch — can take 30+ min)…"
    up_args+=(--build)
  fi

  if ! compose_run "${up_args[@]}"; then
    err "compose up failed"
    compose_run ps -a 2>/dev/null || true
    compose_run logs --tail 80 comfyui 2>/dev/null || true
    return 1
  fi
  log "Compose up finished — verifying container is running…"
  # LAB_STACK_VERIFY_SETTLE=0 skips sleep in hermetic tests
  if ! stack_verify_running "${LAB_STACK_VERIFY_SETTLE:-3}"; then
    return 1
  fi
  log "Container is running. UI target: http://localhost:${COMFY_PORT}"
  log "First start with prebuilt image: seeds volume from /opt/comfy-prebuilt (local copy)"
  log "Without prebuilt: cold pip install (multi-GB). LAB_FORCE_COLD_INSTALL=1 forces pip path."
  # Default FOLLOW on TTY; tests set LAB_STACK_FOLLOW=0
  stack_follow_until_ready || return 1
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
