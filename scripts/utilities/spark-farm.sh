#!/usr/bin/env bash
#
# ## spark-farm
#
# Coordinate MiniMax H3 90s films across independent Comfy workers (no NCCL).
#
# Purpose:
#   status: SSH each SPARK_HOSTS entry (docker ps, disk, nvidia-smi, fabric ping).
#   sync-models: rsync H3 weights over SPARK_FABRIC_IPS only (not mgmt NIC).
#   run: assign one (film, seed) per SPARK_COMFY_URLS entry; queue-h3-film.sh.
#   Never starts compose on a remote node — prints the local manage.sh start.
#
# Usage:
#   ./scripts/utilities/spark-farm.sh status [--json]
#   ./scripts/utilities/spark-farm.sh sync-models
#   ./scripts/utilities/spark-farm.sh run [--film go-see] [--seeds 509201,509211,509221]
#
# Environment:
#   SPARK_HOSTS, SPARK_USER, SPARK_COMFY_URLS, SPARK_FABRIC_IPS, MODELS_DIR, FARM_SHARE
#   See config/spark-farm.example.env
#
# Safety:
#   Does not compose up remotely (heavy confirm stays local).
#   rsync uses fabric IPs. restart: "no" unchanged.
#
# Exit codes:
#   0 success; 1 usage / SSH / rsync / queue errors.
#
# @command spark-farm

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"

SPARK_HOSTS="${SPARK_HOSTS:-}"
SPARK_USER="${SPARK_USER:-nvidia}"
SPARK_COMFY_URLS="${SPARK_COMFY_URLS:-}"
SPARK_FABRIC_IPS="${SPARK_FABRIC_IPS:-}"
MODELS_DIR="${MODELS_DIR:-/mnt/models}"
FARM_SHARE="${FARM_SHARE:-/mnt/models/h3-farm}"
JSON_FLAG=""
CMD="status"
FILM="go-see"
SEEDS="509201,509211,509221"

#######################################
# Split a comma-separated list into lines.
# Arguments:
#   $1 - csv
# Outputs:
#   One item per line
# Returns:
#   0
#######################################
csv_lines() {
  local csv="${1}"
  local IFS=','
  local -a items
  read -r -a items <<<"${csv}"
  local it
  for it in "${items[@]}"; do
    it="${it#"${it%%[![:space:]]*}"}"
    it="${it%"${it##*[![:space:]]}"}"
    [[ -n ${it} ]] && printf '%s\n' "${it}"
  done
}

#######################################
# SSH helper (mgmt network).
# Globals:
#   SPARK_USER
# Arguments:
#   $1 - host
#   $@ - remote command
# Returns:
#   ssh status
#######################################
ssh_host() {
  local host="${1}"
  shift
  ssh -o BatchMode=yes -o ConnectTimeout=5 "${SPARK_USER}@${host}" "$@"
}

#######################################
# Print the exact local start command operators must run on each node.
# Outputs:
#   Command on stderr via log
# Returns:
#   0
#######################################
print_remote_start_hint() {
  log "Never starting compose remotely. On each Spark, with confirm:"
  log "  ./scripts/manage.sh start"
}

#######################################
# status: probe each host (hermetic-friendly: SSH may be mocked).
# Globals:
#   SPARK_HOSTS, SPARK_FABRIC_IPS, JSON_FLAG, MODELS_DIR
# Returns:
#   0
#######################################
cmd_status() {
  local hosts host results=() fabric_ips ip
  hosts="$(csv_lines "${SPARK_HOSTS}")"
  fabric_ips="$(csv_lines "${SPARK_FABRIC_IPS}")"
  if [[ -z ${hosts} ]]; then
    err "SPARK_HOSTS is empty — source config/spark-farm.example.env"
    return 1
  fi
  while IFS= read -r host; do
    [[ -z ${host} ]] && continue
    local docker_ps disk smi ping_ok="false"
    docker_ps="$(ssh_host "${host}" "docker ps -a --filter name=ez-comfy-flux-to-ltx --format '{{.Status}}'" 2>/dev/null || echo "ssh-failed")"
    disk="$(ssh_host "${host}" "df -h ${MODELS_DIR}" 2>/dev/null || echo "n/a")"
    smi="$(ssh_host "${host}" "nvidia-smi -L" 2>/dev/null || echo "n/a")"
    ping_ok="false"
    while IFS= read -r ip; do
      [[ -z ${ip} ]] && continue
      if ping -c 1 -W 1 "${ip}" >/dev/null 2>&1; then
        ping_ok="true"
        break
      fi
    done <<<"${fabric_ips}"
    log "${host}: docker=${docker_ps} fabric_ping=${ping_ok}"
    log "  disk: ${disk}"
    log "  gpu: ${smi}"
    results+=("{\"host\":\"${host}\",\"docker\":\"${docker_ps//\"/}\",\"fabric_ping\":${ping_ok}}")
  done <<<"${hosts}"
  print_remote_start_hint
  if [[ ${JSON_FLAG} == "--json" ]]; then
    local joined
    joined=$(
      IFS=,
      echo "${results[*]}"
    )
    printf '{"hosts":[%s],"models_dir":"%s","farm_share":"%s"}\n' \
      "${joined}" "${MODELS_DIR}" "${FARM_SHARE}"
  fi
}

#######################################
# rsync H3 tree from fabric IP 0 to 1..n (not the mgmt NIC).
# Globals:
#   SPARK_FABRIC_IPS, SPARK_USER, MODELS_DIR
# Returns:
#   0; 1 if no fabric IPs
#######################################
cmd_sync_models() {
  local -a ips=()
  local line
  while IFS= read -r line; do
    [[ -n ${line} ]] && ips+=("${line}")
  done < <(csv_lines "${SPARK_FABRIC_IPS}")
  if [[ ${#ips[@]} -lt 2 ]]; then
    err "SPARK_FABRIC_IPS needs at least two fabric addresses"
    return 1
  fi
  local src="${ips[0]}"
  local h3_tree="${MODELS_DIR}/Comfy-Org__MiniMax-H3_pruned"
  local dest
  for dest in "${ips[@]:1}"; do
    log "rsync H3 weights ${src} → ${dest} over fabric (not mgmt NIC)"
    rsync -a --inplace -e "ssh -o BatchMode=yes" \
      "${SPARK_USER}@${src}:${h3_tree}/" \
      "${SPARK_USER}@${dest}:${h3_tree}/"
  done
}

#######################################
# Assign (film, seed) per Comfy URL and queue.
# Globals:
#   SPARK_COMFY_URLS, FILM, SEEDS, FARM_SHARE
# Returns:
#   0; 1 if a queue fails
#######################################
cmd_run() {
  local -a urls=() seeds=()
  local line
  while IFS= read -r line; do
    [[ -n ${line} ]] && urls+=("${line}")
  done < <(csv_lines "${SPARK_COMFY_URLS}")
  while IFS= read -r line; do
    [[ -n ${line} ]] && seeds+=("${line}")
  done < <(csv_lines "${SEEDS}")
  if [[ ${#urls[@]} -eq 0 ]]; then
    err "SPARK_COMFY_URLS is empty"
    return 1
  fi
  print_remote_start_hint
  mkdir -p "${FARM_SHARE}/out"
  local i url seed rc=0
  for i in "${!urls[@]}"; do
    url="${urls[$i]}"
    seed="${seeds[$i]:-${seeds[0]:-509201}}"
    log "farm ${FILM} seed=${seed} → ${url}"
    FARM_SHARE="${FARM_SHARE}" bash "${REPO_ROOT}/scripts/utilities/queue-h3-film.sh" \
      --film "${FILM}" --url "${url}" --seed "${seed}" || rc=$?
  done
  return "${rc}"
}

#######################################
# Parse CLI.
# Arguments:
#   $@
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      --json) JSON_FLAG="--json" ;;
      --film)
        FILM="${2:?}"
        shift
        ;;
      --seeds)
        SEEDS="${2:?}"
        shift
        ;;
      status | sync-models | run) CMD="${1}" ;;
      -h | --help)
        echo "Usage: $0 status [--json] | sync-models | run [--film go-see] [--seeds a,b,c]" >&2
        exit 0
        ;;
      *)
        err "Unknown arg: $1"
        exit 1
        ;;
    esac
    shift
  done
}

#######################################
# CLI dispatcher.
# Arguments:
#   $@
#######################################
main() {
  parse_args "$@"
  case "${CMD}" in
    status) cmd_status ;;
    sync-models) cmd_sync_models ;;
    run) cmd_run ;;
    *)
      err "Usage: $0 status|sync-models|run"
      exit 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
