#!/usr/bin/env bash
#
# ## manage
#
# Operator CLI for the ez-comfy-stack unified Visual Generative AI demo
# (ComfyUI flux-to-ltx on a single NVIDIA DGX Spark).
#
# Purpose:
#   Single entrypoint for day-to-day stack lifecycle: preflight (doctor), status,
#   start/stop/restart, logs, model downloads (bandwidth-limited by default), and
#   cleanup of the Comfy state volume. Keeps heavy GPU work explicit and safe for
#   remote-SSH operation.
#
# Usage:
#   ./scripts/manage.sh help|setup|doctor|status|start|stop|restart|logs|download-models|cleanup
#   ./scripts/manage.sh download-limit status|run|clear|wrap ...
#
# Safety:
#   - Manual start only (compose restart: "no")
#   - Heavy confirmation for start/restart
#   - Host free-memory/disk headroom checks before start
#   - Model downloads default to bandwidth-limited (download-limit auto @ 85%)
#   - Always stop before node reboot
#   - setup may use sudo only to create/chown MODELS_DIR#
# Environment:
#   See .env.example — MODELS_DIR, HF_TOKEN, MEM_LIMIT, DOWNLOAD_LIMIT,
#   LAB_NON_INTERACTIVE, LAB_CONFIRM_TOKEN, MIN_HOST_FREE_GIB, etc.
#
# Exit codes:
#   0 — success or interactive user abort on confirm
#   1 — hard failure (preflight, docker, missing confirm token, unknown command)
#
# @command manage

set -euo pipefail

# shellcheck source=lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export REPO_ROOT

# shellcheck source=lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=lib/safety.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/safety.sh"
# shellcheck source=lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"

load_dotenv "${REPO_ROOT}"
MODELS_DIR=${MODELS_DIR:-/mnt/models}
export MODELS_DIR
DOWNLOAD_LIMIT=${DOWNLOAD_LIMIT:-auto}

#######################################
# Print the human-facing command list and environment pointer to stdout.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Always 0.
#######################################
cmd_help() {
  cat <<'EOF'
ez-comfy-stack manage — unified Visual Generative AI (Flux → LTX via ComfyUI)

Commands:
  help              Show this help
  setup [--install-docker] [--yes]
                    Host bootstrap: .env, MODELS_DIR (sudo), Docker CE install, doctor
  doctor            Preflight: docker, GPU, free RAM/disk, models
  status [--json]   Stack status
  start             Start flux-to-ltx (requires yes)
  stop              Stop stack (keep models + comfy volume)
  restart           stop + start
  logs              Follow compose logs
  download-models   Download flux-fast + ltx-balanced (bandwidth limited)
                    --with-h3 also pulls MiniMax H3 pruned INT8 (~40 GB)
  download-h3       Download MiniMax H3 only (opt-in; bandwidth limited)
                    Then open :8188 and Queue h3-go-see-90s-lab-example in the UI
  queue-h3          Optional: POST that same lab graph to local :8188 (not the contest UX)
  farm-h3           Optional: POST the same graphs across SPARK_COMFY_URLS
  stitch-h3         Optional ffmpeg mux of H3-native shots; hard-cap 90.00s
  download-limit    Proxy to utilities/download-limit.sh
  clear-hf-locks    Remove stale Hugging Face .lock files under MODELS_DIR
  cleanup           Remove comfy-state volume (type DELETE)

Environment: see .env.example (MODELS_DIR, HF_TOKEN, MEM_LIMIT, DOWNLOAD_LIMIT)
EOF
}

#######################################
# Bootstrap host prerequisites for doctor/download/start.
# Creates .env from example if missing; prepares MODELS_DIR (sudo mkdir/chown);
# installs Docker CE when missing (confirm / --install-docker); soft-checks GPU;
# then runs doctor.
# Side effects: May write .env; may sudo for MODELS_DIR and package install.
# Globals:
#   REPO_ROOT, MODELS_DIR, LAB_NO_SUDO, SETUP_INSTALL_DOCKER, SETUP_YES
# Arguments:
#   Optional: --install-docker  force docker install path
#             --yes             skip install confirmation
# Outputs:
#   Status via log/warn/err on stderr
# Returns:
#   0 when doctor passes; 1 when host still not ready
#######################################
cmd_setup() {
  log "Host setup / bootstrap"
  local ok=0
  local force_docker=0
  local arg

  for arg in "$@"; do
    case "${arg}" in
      --install-docker)
        force_docker=1
        SETUP_INSTALL_DOCKER=1
        export SETUP_INSTALL_DOCKER
        ;;
      --yes | -y)
        SETUP_YES=1
        export SETUP_YES
        force_docker=1
        ;;
      -h | --help)
        cat <<'EOF' >&2
Usage: manage.sh setup [--install-docker] [--yes]
  --install-docker  Install Docker CE if missing (sudo)
  --yes             Skip install confirmation (still needs sudo)
EOF
        return 0
        ;;
      *)
        err "Unknown setup flag: ${arg}"
        return 1
        ;;
    esac
  done

  if [[ ! -f ${REPO_ROOT}/.env ]]; then
    if [[ -f ${REPO_ROOT}/.env.example ]]; then
      cp "${REPO_ROOT}/.env.example" "${REPO_ROOT}/.env"
      log "Created .env from .env.example (set HF_TOKEN if models are gated)"
    else
      warn ".env.example missing; skipping .env create"
    fi
  else
    log ".env already present"
  fi
  load_dotenv "${REPO_ROOT}"
  MODELS_DIR=${MODELS_DIR:-/mnt/models}
  export MODELS_DIR

  log "MODELS_DIR=${MODELS_DIR}"
  if prepare_models_dir "${MODELS_DIR}"; then
    log "models dir ready: ${MODELS_DIR}"
  else
    ok=1
  fi

  # Run install path when docker is missing, --install-docker/--yes, or hermetic mock.
  # (CI has host docker; tests still need LAB_MOCK_DOCKER_INSTALL to create bindir.)
  local need_docker_install=0
  if ! check_docker_preflight; then
    need_docker_install=1
  elif [[ ${force_docker} -eq 1 || ${LAB_MOCK_DOCKER_INSTALL:-} == "1" ]]; then
    need_docker_install=1
    log "docker preflight: ok — still running install path (--install-docker or mock)"
  else
    log "docker preflight: ok"
  fi

  if [[ ${need_docker_install} -eq 1 ]]; then
    local conf_rc=0
    confirm_docker_install "${force_docker}" || conf_rc=$?
    if [[ ${conf_rc} -eq 0 ]]; then
      if install_docker_engine; then
        if check_docker_preflight; then
          log "docker preflight: ok after install"
        else
          warn "Docker installed but preflight still failing — try: newgrp docker"
          ok=1
        fi
      else
        ok=1
      fi
    else
      print_docker_install_hints
      ok=1
    fi
  fi

  if command -v nvidia-smi >/dev/null 2>&1; then
    log "nvidia-smi: present"
  else
    warn "nvidia-smi not found (required on Spark for GPU workloads)"
  fi
  if command -v wondershaper >/dev/null 2>&1; then
    log "wondershaper: present"
  else
    warn "wondershaper not found (download-limit will try to install or soft-fail)"
  fi

  log "Re-running doctor..."
  if ! cmd_doctor; then
    ok=1
  fi
  if [[ ${ok} -ne 0 ]]; then
    local st=0
    docker_daemon_status || st=$?
    if [[ ${st} -eq 1 ]]; then
      err "Setup incomplete — run: newgrp docker   # then ./scripts/manage.sh doctor"
      return 1
    fi
    err "Setup incomplete — fix errors above, then re-run: ./scripts/manage.sh setup --install-docker"
    return 1
  fi
  log "Setup OK — next: ./scripts/manage.sh download-models"
  return 0
}

#######################################
# Run operator preflight checks without starting the stack.
# Validates Docker + Compose, optional nvidia-smi, MEM_LIMIT budget warning,
# host free RAM/disk headroom, MODELS_DIR presence, flux/ltx readiness JSON,
# and existence of the compose file.
# Side effects: May invoke docker, nvidia-smi, download-*-status (no network pull).
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 when all hard checks pass; 1 if any hard check fails.
#######################################
cmd_doctor() {
  log "Doctor / preflight"
  local ok=0
  local docker_failed=0 docker_st=0
  if ! check_docker_preflight; then
    docker_failed=1
    docker_daemon_status || docker_st=$?
    if command -v sudo >/dev/null 2>&1 && sudo -n docker --version >/dev/null 2>&1; then
      warn "sudo docker works — add your user to the docker group and re-login (newgrp docker)"
    fi
    ok=1
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    log "nvidia-smi: present"
    nvidia-smi -L 2>/dev/null | head -5 || true
  else
    warn "nvidia-smi not found (ok for offline tests; required on Spark)"
  fi
  check_mem_limit_vs_headroom || true
  if ! check_host_headroom; then
    ok=1
  fi
  log "MODELS_DIR=${MODELS_DIR}"
  if ensure_models_dir "${MODELS_DIR}"; then
    log "models dir exists and is writable"
  else
    ok=1
  fi
  local flux_json ltx_json
  flux_json=$(MODELS_DIR="${MODELS_DIR}" bash "${REPO_ROOT}/scripts/utilities/download-flux.sh" status --tier fast --json 2>/dev/null || echo '{}')
  ltx_json=$(MODELS_DIR="${MODELS_DIR}" bash "${REPO_ROOT}/scripts/utilities/download-ltx.sh" status --tier balanced --json 2>/dev/null || echo '{}')
  log "flux status: ${flux_json}"
  log "ltx status: ${ltx_json}"
  # Soft: missing lab weights do not fail doctor (download may be intentional later)
  check_lab_models_ready "${MODELS_DIR}" || warn "lab workflow models incomplete (not a hard doctor failure)"
  if [[ ${LAB_PIPELINE:-} == "h3" ]]; then
    check_h3_models_ready "${MODELS_DIR}" || warn "H3 workflow models incomplete (not a hard doctor failure)"
  fi
  if [[ ! -f $(lab_compose_file) ]]; then
    err "compose file missing: $(lab_compose_file)"
    ok=1
  else
    log "compose file: $(lab_compose_file)"
  fi
  # Soft: show which GHCR channel start would pull (branch-aligned; no network)
  log "default image: $(stack_default_image) (branch=$(stack_git_branch))"
  if stack_port_open "${COMFY_PORT:-8188}"; then
    if comfy_h3_object_info_ok; then
      log "Native MiniMaxH3AddGuide registered"
    else
      warn "MiniMaxH3* missing (core v0.34.0). Do not pip install comfyui-manager. git pull, stop, start"
    fi
  fi
  if [[ ${ok} -ne 0 ]]; then
    if [[ ${docker_failed} -eq 1 ]]; then
      err "Doctor found problems — try: $(doctor_next_step_hint "${docker_st}")"
    else
      err "Doctor found problems — see errors above (headroom, MODELS_DIR, or compose)"
    fi
    return 1
  fi
  log "Doctor OK"
  return 0
}

#######################################
# Show human-readable or JSON status of the Compose project.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Optional `--json` for machine-readable compose_status_json on stdout.
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 after printing; docker failures are warned, not always fatal.
#######################################
cmd_status() {
  local json=0
  if [[ ${1:-} == "--json" ]]; then
    json=1
  fi
  if [[ ${json} -eq 1 ]]; then
    compose_status_json
    return 0
  fi
  log "Stack status (project ez-comfy)"
  if resolve_docker_on_path; then
    # -a shows Exited containers (restart: no hides them from default ps)
    compose_run ps -a 2>/dev/null || warn "compose ps failed (stack may be stopped)"
    if ! compose_is_running; then
      warn "comfyui is not running. Logs: ./scripts/manage.sh logs --tail 100"
    elif ! stack_port_open "${COMFY_PORT:-8188}"; then
      warn "container running but :${COMFY_PORT:-8188} not open yet (cold install?). ./scripts/manage.sh logs"
    else
      log "ComfyUI port open — http://localhost:${COMFY_PORT:-8188}"
      if comfy_h3_object_info_ok; then
        log "Native MiniMaxH3AddGuide registered"
      else
        warn "MiniMaxH3* not in /object_info (core v0.34.0, not a pack). Do not pip install comfyui-manager. stop + start after git pull"
      fi
    fi
  else
    warn "docker not available"
  fi
  log "MODELS_DIR=${MODELS_DIR} COMFY_PORT=${COMFY_PORT:-8188} MEM_LIMIT=${MEM_LIMIT:-90g}"
}

#######################################
# Confirm, check headroom, then start the unified flux-to-ltx Compose stack.
# Side effects: May build/start containers; requires operator confirmation.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success or interactive abort; 1 on failed confirm/headroom/compose.
#######################################
cmd_start() {
  require_heavy_confirm "flux-to-ltx (ComfyUI unified stack)" \
    "90Gi-class memory limit; exclusive GPU; manual start only." || {
    local rc=$?
    if [[ ${rc} -eq 2 ]]; then
      exit 0
    fi
    exit 1
  }
  check_mem_limit_vs_headroom
  check_host_headroom || exit 1
  stack_start
}

#######################################
# Stop stack containers while retaining volumes and the host model cache.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of stack_stop.
#######################################
cmd_stop() {
  stack_stop
}

#######################################
# Stop then start (re-runs full start confirmation and headroom checks).
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of the final start path.
#######################################
cmd_restart() {
  cmd_stop
  cmd_start
}

#######################################
# Follow Docker Compose logs for the stack.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  Extra args for `compose logs -f` (service filter, --tail, etc.).
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
cmd_logs() {
  stack_logs "$@"
}

#######################################
# Download flux-fast and ltx-balanced weights under MODELS_DIR with bandwidth limits.
# DOWNLOAD_LIMIT controls throttling:
#   auto | N  — wrap both downloads under download-limit (default auto)
#   off | 0   — no throttle (warns about remote SSH risk)
# Side effects: Network HF downloads; may require sudo for wondershaper.
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Exit status of the download pipeline.
#######################################
#######################################
# Clear stale Hugging Face download locks under MODELS_DIR.
# Globals:
#   MODELS_DIR
# Arguments:
#   None
# Outputs:
#   Status via log/warn
# Returns:
#   0
#######################################
cmd_clear_hf_locks() {
  ensure_models_dir "${MODELS_DIR}" || return 1
  clear_stale_hf_locks "${MODELS_DIR}"
}

cmd_download_models() {
  local limit="${DOWNLOAD_LIMIT}"
  local flux_cmd ltx_cmd rc=0 with_h3=0
  local arg
  for arg in "$@"; do
    case "${arg}" in
      --with-h3) with_h3=1 ;;
      -h | --help)
        cat <<'EOF' >&2
Usage: manage.sh download-models [--with-h3]
  Default: flux-fast + ltx-balanced (does not pull H3).
  --with-h3  also download MiniMax H3 pruned INT8 (~40 GB).
EOF
        return 0
        ;;
      *)
        err "Unknown download-models flag: ${arg}"
        return 1
        ;;
    esac
  done
  ensure_models_dir "${MODELS_DIR}" || return 1
  clear_stale_hf_locks "${MODELS_DIR}"
  flux_cmd=(bash "${REPO_ROOT}/scripts/utilities/download-flux.sh" run --tier fast)
  ltx_cmd=(bash "${REPO_ROOT}/scripts/utilities/download-ltx.sh" run --tier balanced)
  if [[ ${limit} == "off" || ${limit} == "0" ]]; then
    warn "DOWNLOAD_LIMIT=off — saturating the link may lock remote SSH"
    "${flux_cmd[@]}" || rc=$?
    if [[ ${rc} -eq 0 ]]; then
      "${ltx_cmd[@]}" || rc=$?
    fi
    if [[ ${rc} -eq 0 && ${with_h3} -eq 1 ]]; then
      bash "${REPO_ROOT}/scripts/utilities/download-h3.sh" run --tier pruned || rc=$?
    fi
  else
    local dl="${REPO_ROOT}/scripts/utilities/download-limit.sh"
    local inner
    inner="MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-flux.sh' run --tier fast && \
       MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-ltx.sh' run --tier balanced"
    if [[ ${with_h3} -eq 1 ]]; then
      inner="${inner} && MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-h3.sh' run --tier pruned"
    fi
    bash "${dl}" wrap --limit "${limit}" -- bash -c "${inner}" ||
      rc=$?
  fi
  # Lab workflows need the full basename set under MODELS_DIR/comfy (not size-only tiers)
  if ! check_lab_models_ready "${MODELS_DIR}"; then
    err "download-models: lab workflow weights incomplete under ${MODELS_DIR}/comfy"
    err "Re-run after fixing HF_TOKEN / network, or download tiers individually."
    return 1
  fi
  if [[ ${with_h3} -eq 1 ]] && ! check_h3_models_ready "${MODELS_DIR}"; then
    err "download-models --with-h3: H3 weights incomplete under ${MODELS_DIR}/comfy"
    return 1
  fi
  if [[ ${rc} -ne 0 ]]; then
    warn "download-models: download reported errors (rc=${rc}) but lab files are present"
  fi
  log "download-models: lab workflow weights ready under ${MODELS_DIR}/comfy"
  return 0
}

#######################################
# Download MiniMax H3 pruned weights only (opt-in; bandwidth-limited).
# Globals:
#   MODELS_DIR, DOWNLOAD_LIMIT
# Arguments:
#   $@  forwarded to download-h3.sh after `run` (e.g. --tier turbo)
# Returns:
#   0 when four H3 basenames are present
#######################################
cmd_download_h3() {
  local limit="${DOWNLOAD_LIMIT}"
  local rc=0
  ensure_models_dir "${MODELS_DIR}" || return 1
  clear_stale_hf_locks "${MODELS_DIR}"
  if [[ ${limit} == "off" || ${limit} == "0" ]]; then
    warn "DOWNLOAD_LIMIT=off — saturating the link may lock remote SSH"
    bash "${REPO_ROOT}/scripts/utilities/download-h3.sh" run "$@" || rc=$?
  else
    local dl="${REPO_ROOT}/scripts/utilities/download-limit.sh"
    bash "${dl}" wrap --limit "${limit}" -- bash -c \
      "MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-h3.sh' run $*" ||
      rc=$?
  fi
  if ! check_h3_models_ready "${MODELS_DIR}"; then
    err "download-h3: H3 weights incomplete under ${MODELS_DIR}/comfy"
    return 1
  fi
  if [[ ${rc} -ne 0 ]]; then
    warn "download-h3: download reported errors (rc=${rc}) but H3 files are present"
  fi
  log "download-h3: MiniMax H3 weights ready under ${MODELS_DIR}/comfy"
  return 0
}

#######################################
# POST an H3 90s film graph to one ComfyUI URL.
# Arguments:
#   $@  forwarded to queue-h3-film.sh
#######################################
cmd_queue_h3() {
  bash "${REPO_ROOT}/scripts/utilities/queue-h3-film.sh" "$@"
}

#######################################
# Farm H3 films across SPARK_COMFY_URLS (does not start compose).
# Arguments:
#   $@  forwarded to spark-farm.sh run
#######################################
cmd_farm_h3() {
  bash "${REPO_ROOT}/scripts/utilities/spark-farm.sh" run "$@"
}

#######################################
# ffmpeg mux of H3-native shot media; refuse soundtracks; cap 90s.
# Arguments:
#   $@  forwarded to queue-h3-film.sh stitch
#######################################
cmd_stitch_h3() {
  bash "${REPO_ROOT}/scripts/utilities/queue-h3-film.sh" stitch "$@"
}

#######################################
# Proxy remaining argv to scripts/utilities/download-limit.sh.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $@  Forwarded subcommand and flags (status|run|clear|wrap …).
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success; non-zero on failure where applicable.
#######################################
cmd_download_limit() {
  bash "${REPO_ROOT}/scripts/utilities/download-limit.sh" "$@"
}

#######################################
# After DELETE confirmation, remove Compose volumes (Comfy install state only).
# Globals:
#   See file header / caller environment.
# Arguments:
#   None
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   0 on success/abort; 1 on hard confirm failure.
#######################################
cmd_cleanup() {
  require_delete_confirm || {
    local rc=$?
    if [[ ${rc} -eq 2 ]]; then
      exit 0
    fi
    exit 1
  }
  stack_cleanup_state
}

#######################################
# Thin CLI dispatcher: first argument selects a cmd_* handler.
# Globals:
#   See file header / caller environment.
# Arguments:
#   $1  Subcommand (default help).
#   $@  Remaining args for the selected command.
# Outputs:
#   Status via log/warn/err on stderr unless noted.
# Returns:
#   Propagates handler status; unknown command exits 1 after help.
#######################################
main() {
  local cmd="${1:-help}"
  shift || true
  case "${cmd}" in
    help | -h | --help) cmd_help ;;
    setup) cmd_setup "$@" ;;
    doctor) cmd_doctor ;;
    status) cmd_status "$@" ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    logs) cmd_logs "$@" ;;
    download-models) cmd_download_models "$@" ;;
    download-h3) cmd_download_h3 "$@" ;;
    queue-h3) cmd_queue_h3 "$@" ;;
    farm-h3) cmd_farm_h3 "$@" ;;
    stitch-h3) cmd_stitch_h3 "$@" ;;
    download-limit) cmd_download_limit "$@" ;;
    clear-hf-locks) cmd_clear_hf_locks ;;
    cleanup) cmd_cleanup ;;
    *)
      err "Unknown command: ${cmd}"
      cmd_help
      exit 1
      ;;
  esac
}

# Source guard: allow tests to source this file without executing main.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
