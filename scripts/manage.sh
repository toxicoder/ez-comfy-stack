#!/usr/bin/env bash
#
# ## manage
#
# Operator CLI for the ez-comfy-stack unified Visual Generative AI demo
# (ComfyUI US-safe local studio on a single NVIDIA DGX Spark).
#
# Purpose:
#   Single entrypoint for day-to-day stack lifecycle: preflight (doctor), status,
#   start/stop/restart, logs, model downloads (bandwidth-limited by default), and
#   cleanup of the Comfy state volume. Keeps heavy GPU work explicit and safe for
#   remote-SSH operation.
#
# Usage:
#   ./scripts/manage.sh help|setup|doctor|status|start|stop|restart|logs|download-models [--limit auto|N|off]|cleanup
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
COMFY_OUTPUT_DIR=${COMFY_OUTPUT_DIR:-/mnt/comfy-output}
export COMFY_OUTPUT_DIR
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
ez-comfy-stack manage — unified Visual Generative AI (local US-safe studio via ComfyUI)

Commands:
  help              Show this help
  setup [--install-docker] [--yes]
                    Host bootstrap: .env, MODELS_DIR + COMFY_OUTPUT_DIR (sudo), Docker CE install, doctor
  doctor            Preflight: docker, GPU, free RAM/disk, models, output dir, license policy
  status [--json]   Stack status
  start             Start studio stack (requires yes)
  stop              Stop stack (keep models, outputs, and comfy volume)
  restart           stop + start
  logs              Follow compose logs
  download-models [--limit auto|N|off]
                    Download Apache still + Wan 2.2 5B + LTX distilled (bandwidth limited)
                    --limit N is a fixed Mbps cap (overrides DOWNLOAD_LIMIT for this run)
                    Refuses MiniMax H3 (US Excluded Territory)
  download-limit    Proxy to utilities/download-limit.sh
  clear-hf-locks    Remove stale Hugging Face .lock files under MODELS_DIR
  cleanup           Remove comfy-state volume only (type DELETE; keeps COMFY_OUTPUT_DIR)

Environment: see .env.example (MODELS_DIR, COMFY_OUTPUT_DIR, HF_TOKEN, MEM_LIMIT, DOWNLOAD_LIMIT)
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
  COMFY_OUTPUT_DIR=${COMFY_OUTPUT_DIR:-/mnt/comfy-output}
  export COMFY_OUTPUT_DIR
  log "COMFY_OUTPUT_DIR=${COMFY_OUTPUT_DIR}"
  if prepare_comfy_output_dir "${COMFY_OUTPUT_DIR}"; then
    log "output dir ready: ${COMFY_OUTPUT_DIR}"
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
  log "COMFY_OUTPUT_DIR=${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
  if ensure_comfy_output_dir "${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"; then
    log "output dir exists and is writable"
  else
    ok=1
  fi
  local image_json wan_json ltx_json
  image_json=$(MODELS_DIR="${MODELS_DIR}" bash "${REPO_ROOT}/scripts/utilities/download-image.sh" status --tier fast --json 2>/dev/null || echo '{}')
  wan_json=$(MODELS_DIR="${MODELS_DIR}" bash "${REPO_ROOT}/scripts/utilities/download-wan.sh" status --tier 5b --json 2>/dev/null || echo '{}')
  ltx_json=$(MODELS_DIR="${MODELS_DIR}" bash "${REPO_ROOT}/scripts/utilities/download-ltx.sh" status --tier 2.5 --json 2>/dev/null || echo '{}')
  log "image status: ${image_json}"
  log "wan status: ${wan_json}"
  log "ltx status: ${ltx_json}"
  # Soft: missing lab weights do not fail doctor (download may be intentional later)
  check_lab_models_ready "${MODELS_DIR}" || warn "lab workflow models incomplete (not a hard doctor failure)"
  log "License policy: Apache Klein 4B still + Apache Wan 2.2 5B silent + LTX-2.5 AV (Community, under 10M company USD). Not legal advice. See docs/licenses.md"
  if [[ ! -f $(lab_compose_file) ]]; then
    err "compose file missing: $(lab_compose_file)"
    ok=1
  else
    log "compose file: $(lab_compose_file)"
  fi
  # Soft: show which GHCR channel start would pull (branch-aligned; no network)
  log "default image: $(stack_default_image) (branch=$(stack_git_branch))"
  if [[ ${ok} -ne 0 ]]; then
    if [[ ${docker_failed} -eq 1 ]]; then
      err "Doctor found problems — try: $(doctor_next_step_hint "${docker_st}")"
    else
      err "Doctor found problems — see errors above (headroom, MODELS_DIR, COMFY_OUTPUT_DIR, or compose)"
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
    fi
  else
    warn "docker not available"
  fi
  log "MODELS_DIR=${MODELS_DIR} COMFY_OUTPUT_DIR=${COMFY_OUTPUT_DIR:-/mnt/comfy-output} COMFY_PORT=${COMFY_PORT:-8188} MEM_LIMIT=${MEM_LIMIT:-90g}"
}

#######################################
# Confirm, check headroom, then start the unified studio Compose stack.
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
  require_heavy_confirm "us-safe-studio (ComfyUI unified stack)" \
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

#######################################
# Download lab weights under MODELS_DIR with bandwidth limits.
# DOWNLOAD_LIMIT (auto|N|off) is the default; --limit overrides for this run.
# wrap always clears shaping on exit. off|0 skips throttle (SSH risk).
# Globals:
#   DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
# Arguments:
#   Optional: --limit auto|N|off
# Outputs:
#   Status via log/warn/err on stderr
# Returns:
#   0 when lab files are ready; 1 on usage error or incomplete weights
#######################################
cmd_download_models() {
  local limit="${DOWNLOAD_LIMIT}"
  local rc=0
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --with-h3)
        refuse_minimax_h3
        return 1
        ;;
      --limit)
        if [[ $# -lt 2 || -z ${2} || ${2} == -* ]]; then
          err "download-models --limit requires auto|N|off"
          return 1
        fi
        limit="${2}"
        shift 2
        ;;
      --limit=*)
        limit="${1#--limit=}"
        if [[ -z ${limit} ]]; then
          err "download-models --limit requires auto|N|off"
          return 1
        fi
        shift
        ;;
      -h | --help)
        cat <<'EOF' >&2
Usage: manage.sh download-models [--limit auto|N|off]
  Default: Apache still (Klein 4B) + Wan 2.2 5B + LTX distilled AV.
  --limit auto  speedtest then 85% (default, or DOWNLOAD_LIMIT in .env)
  --limit N     fixed cap in Mbps (e.g. 40 ≈ 5 MB/s); overrides DOWNLOAD_LIMIT
  --limit off   no throttle (not recommended over remote SSH)
  MiniMax H3 is banned (US Excluded Territory). See docs/licenses.md
EOF
        return 0
        ;;
      *)
        err "Unknown download-models flag: ${1}"
        return 1
        ;;
    esac
  done
  case "${limit}" in
    auto | off | 0) ;;
    *)
      if [[ ! ${limit} =~ ^[0-9]+$ || ${limit} -le 0 ]]; then
        err "Invalid --limit '${limit}' (use auto, off, or a positive integer Mbps)"
        return 1
      fi
      ;;
  esac
  ensure_models_dir "${MODELS_DIR}" || return 1
  clear_stale_hf_locks "${MODELS_DIR}"
  local image_cmd wan_cmd ltx_cmd
  image_cmd=(bash "${REPO_ROOT}/scripts/utilities/download-image.sh" run --tier fast)
  wan_cmd=(bash "${REPO_ROOT}/scripts/utilities/download-wan.sh" run --tier 5b)
  ltx_cmd=(bash "${REPO_ROOT}/scripts/utilities/download-ltx.sh" run --tier 2.5)
  if [[ ${limit} == "off" || ${limit} == "0" ]]; then
    warn "DOWNLOAD_LIMIT=off — saturating the link may lock remote SSH"
    "${image_cmd[@]}" || rc=$?
    if [[ ${rc} -eq 0 ]]; then
      "${wan_cmd[@]}" || rc=$?
    fi
    if [[ ${rc} -eq 0 ]]; then
      "${ltx_cmd[@]}" || rc=$?
    fi
  else
    local dl="${REPO_ROOT}/scripts/utilities/download-limit.sh"
    local inner
    inner="MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-image.sh' run --tier fast && \
       MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-wan.sh' run --tier 5b && \
       MODELS_DIR='${MODELS_DIR}' bash '${REPO_ROOT}/scripts/utilities/download-ltx.sh' run --tier 2.5"
    bash "${dl}" wrap --limit "${limit}" -- bash -c "${inner}" ||
      rc=$?
  fi
  # Lab workflows need the full basename set under MODELS_DIR/comfy (not size-only tiers)
  if ! check_lab_models_ready "${MODELS_DIR}"; then
    err "download-models: lab workflow weights incomplete under ${MODELS_DIR}/comfy"
    err "Re-run after fixing HF_TOKEN / network, or download tiers individually."
    return 1
  fi
  if [[ ${rc} -ne 0 ]]; then
    warn "download-models: download reported errors (rc=${rc}) but lab files are present"
  fi
  log "download-models: lab workflow weights ready under ${MODELS_DIR}/comfy"
  return 0
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
    download-h3 | queue-h3 | farm-h3 | stitch-h3)
      refuse_minimax_h3
      exit 1
      ;;
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
