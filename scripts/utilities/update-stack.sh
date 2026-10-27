#!/usr/bin/env bash
#
# ## update-stack
#
# Redeploy the Compose stack from the branch you are actually standing on.
#
# The published image lane comes from the git branch (scripts/lib/compose.sh):
# main publishes us-safe-studio and every other branch publishes
# us-safe-studio-development. This flow pins that pairing. It resolves the
# checked-out branch, refuses an explicit image from the other lane,
# fast-forwards the checkout, and redeploys through manage.sh.
#
# Sequence (the order is the contract; tests pin it):
#   1. update_stack_usage / parse_args
#   2. prove_repo_root           - BUILD_WORKSPACE_DIRECTORY, else script path
#   3. update_stack_preflight    - git present, docker usable
#   4. resolve_update_branch     - detached HEAD refuses without --branch
#   5. check_image_lane          - branch lane must match the image tag
#   6. check_dirty_tree          - dirty worktree refuses without --allow-dirty
#   7. guard_interactive_confirm - non-TTY start needs --yes
#   8. sync_checkout             - optional switch, fetch, pull --ff-only
#   9. changed_deploy_paths      - none | scripts | compose | image
#  10. reconcile_env_file        - warn on keys .env lacks; never write it
#  11. plan_redeploy             - none | restart | recreate
#  12. pull_stack_image          - docker pull; failure is only a warning
#  13. redeploy_stack            - manage.sh restart, or stop then start
#  14. verify_stack              - manage.sh doctor
#  15. promotion_note            - informational, never fails
#  16. report_summary            - branch/lane/plan/actions table on stderr
#
# What this script never does:
#   - Never merges, rebases, or resets. The pull is --ff-only only.
#   - Never calls docker or docker compose for start/stop. It delegates to
#     ./scripts/manage.sh so the heavy confirm, the headroom preflight, and
#     the restart: "no" policy all stay in one place.
#   - Never removes volumes and never runs cleanup.
#   - Never writes the operator's .env file; it only reports missing keys.
#
# Usage:
#   ./scripts/manage.sh update-stack
#   ./scripts/manage.sh update-stack --yes
#   ./scripts/manage.sh update-stack --dry-run
#   ./scripts/utilities/update-stack.sh --branch development --yes
#   bazelisk run //scripts:update-stack -- --dry-run
#
# Options:
#   -h, --help               Print usage and exit 0.
#   --dry-run                Print what would run; mutate nothing. Guardrails
#                            still execute and read-only git probes still run,
#                            so the plan is the real plan.
#   --branch NAME            Checkout and update NAME first; also the only way
#                            to run on a detached HEAD.
#   --allow-dirty            Proceed with a dirty worktree.
#   --skip-fetch             Skip git fetch and git pull --ff-only.
#   --skip-image-pull        Skip the docker pull.
#   --no-restart             Update checkout and image; leave the running
#                            stack alone.
#   --force-recreate         Always stop+start, even for a scripts-only change.
#   --force-build            Export LAB_STACK_FORCE_BUILD=1 for the delegated
#                            start.
#   --image REF              Explicit image ref; must match the branch lane
#                            unless --allow-lane-mismatch.
#   --allow-lane-mismatch    Permit an explicit image from another lane.
#   --yes                    Automation: exports LAB_NON_INTERACTIVE=1 and
#                            LAB_CONFIRM_TOKEN=yes (the supported confirm pair).
#
# Environment:
#   EZ_COMFY_IMAGE         Explicit image ref (same effect as --image).
#   LAB_GIT_BRANCH         Hermetic branch override read by stack_git_branch.
#   LAB_STACK_SKIP_PULL    1 = stack_pull_image declines the pull.
#   LAB_STACK_FORCE_BUILD  1 = compose up --build (set by --force-build).
#   LAB_NON_INTERACTIVE    1 with LAB_CONFIRM_TOKEN=yes is the automation
#   LAB_CONFIRM_TOKEN      confirm path require_heavy_confirm accepts.
#   BUILD_WORKSPACE_DIRECTORY  Set by bazel run; preferred repo root.
#
# Exit codes:
#   0 success, or nothing to do
#   1 failure
#   2 usage error
#   3 guardrail refusal (dirty tree, detached HEAD without --branch, lane
#     mismatch, non-TTY start without --yes)
#   5 repo root could not be proven
#
# @command update-stack

set -euo pipefail

# shellcheck source=../lib/paths.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/../lib/paths.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/common.sh"
# shellcheck source=../lib/compose.sh disable=SC1091
source "${REPO_ROOT}/scripts/lib/compose.sh"

# Operator-facing entry point this flow is allowed to delegate to. Never docker
# or docker compose directly (AGENTS.md: prefer manage.sh over raw docker compose).
MANAGE_SH="${REPO_ROOT}/scripts/manage.sh"
UPDATE_STACK_PHASE_TOTAL=16

# CLI state (parse_args)
US_HELP=0
US_DRY_RUN=0
US_BRANCH=""
US_ALLOW_DIRTY=0
US_SKIP_FETCH=0
US_SKIP_IMAGE_PULL=0
US_NO_RESTART=0
US_FORCE_RECREATE=0
US_IMAGE=""
US_ALLOW_LANE_MISMATCH=0
US_YES=0

# Run state (filled by the phases, read by report_summary)
UPDATE_BRANCH=""
IMAGE_REF=""
IMAGE_LANE_NAME=""
DEPLOY_CLASS="none"
REDEPLOY_PLAN="none"
CHANGED_PATHS=""
US_ACTIONS=""

#######################################
# Print usage on stdout.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage text on stdout
# Returns:
#   0
#######################################
update_stack_usage() {
  cat <<'USAGE'
usage: update-stack [--dry-run] [--branch NAME] [--allow-dirty]
                    [--skip-fetch] [--skip-image-pull]
                    [--no-restart | --force-recreate] [--force-build]
                    [--image REF [--allow-lane-mismatch]] [--yes]

  Redeploy the Compose stack from the branch currently checked out: resolve
  the branch, prove the image lane matches it, fast-forward the checkout,
  refresh the image, then restart or recreate through manage.sh.

  Options: --dry-run (plan only), --branch NAME, --allow-dirty, --skip-fetch,
  --skip-image-pull, --no-restart, --force-recreate, --force-build,
  --image REF, --allow-lane-mismatch, --yes (automation confirm), -h/--help.

  Refused without an opt-in: a dirty worktree, a detached HEAD, an image from
  another lane, and a start with no terminal. It never merges, rebases, resets,
  removes volumes, or writes your .env file.
USAGE
}

#######################################
# Parse argv into the US_* globals. Flags only: a bare word is a usage error.
# Globals:
#   US_HELP, US_DRY_RUN, US_BRANCH, US_ALLOW_DIRTY, US_SKIP_FETCH,
#   US_SKIP_IMAGE_PULL, US_NO_RESTART, US_FORCE_RECREATE, US_IMAGE,
#   US_ALLOW_LANE_MISMATCH, US_YES.
#   Exports LAB_NON_INTERACTIVE / LAB_CONFIRM_TOKEN under --yes and
#   LAB_STACK_FORCE_BUILD under --force-build.
# Arguments:
#   $@  Flags (see update_stack_usage)
# Outputs:
#   Usage plus the cause on stderr for a usage error
# Returns:
#   0 ok; 2 usage error
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "${1}" in
      -h | --help)
        US_HELP=1
        return 0
        ;;
      --dry-run)
        US_DRY_RUN=1
        ;;
      --branch)
        [[ $# -ge 2 && -n ${2:-} && ${2} != -* ]] || {
          err "--branch needs a branch name"
          update_stack_usage >&2
          return 2
        }
        US_BRANCH="${2}"
        shift 2
        continue
        ;;
      --allow-dirty)
        US_ALLOW_DIRTY=1
        ;;
      --skip-fetch)
        US_SKIP_FETCH=1
        ;;
      --skip-image-pull)
        US_SKIP_IMAGE_PULL=1
        ;;
      --no-restart)
        US_NO_RESTART=1
        ;;
      --force-recreate)
        US_FORCE_RECREATE=1
        ;;
      --force-build)
        export LAB_STACK_FORCE_BUILD=1
        ;;
      --image)
        [[ $# -ge 2 && -n ${2:-} && ${2} != -* ]] || {
          err "--image needs a ref"
          update_stack_usage >&2
          return 2
        }
        US_IMAGE="${2}"
        shift 2
        continue
        ;;
      --allow-lane-mismatch)
        US_ALLOW_LANE_MISMATCH=1
        ;;
      --yes)
        US_YES=1
        export LAB_NON_INTERACTIVE=1
        export LAB_CONFIRM_TOKEN=yes
        ;;
      -*)
        err "unknown option: ${1} (try --help)"
        update_stack_usage >&2
        return 2
        ;;
      *)
        err "'${1}' is not an option; this CLI takes flags only (try --help)"
        update_stack_usage >&2
        return 2
        ;;
    esac
    shift
  done
  return 0
}

#######################################
# Prove the repository root: BUILD_WORKSPACE_DIRECTORY first (that is how
# bazel run hands over the real source tree), else this script's own path.
# Side effects: assigns and exports REPO_ROOT on success only.
# Globals:
#   BUILD_WORKSPACE_DIRECTORY, SCRIPT_DIR, REPO_ROOT (written)
# Arguments:
#   None
# Outputs:
#   err on stderr when the root cannot be proven
# Returns:
#   0 proven; 5 unprovable
#######################################
prove_repo_root() {
  local candidate
  if [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
    candidate="${BUILD_WORKSPACE_DIRECTORY}"
  else
    candidate="$(cd "${SCRIPT_DIR}/../.." && pwd)"
  fi
  if [[ ! -f ${candidate}/scripts/manage.sh || ! -f ${candidate}/docker/docker-compose.yml ]]; then
    err "cannot prove a repo root at ${candidate} (need scripts/manage.sh and docker/docker-compose.yml)"
    return 5
  fi
  REPO_ROOT="$(cd "${candidate}" && pwd)"
  export REPO_ROOT
  return 0
}

#######################################
# Preflight: git on PATH and a usable docker client. Read-only probes only, so
# they run under --dry-run too. The docker probe is skipped for a dry run
# because a plan needs no daemon.
# Globals:
#   US_SKIP_FETCH, US_DRY_RUN
# Arguments:
#   None
# Outputs:
#   log/warn/err on stderr
# Returns:
#   0 ok; 1 missing prerequisite
#######################################
update_stack_preflight() {
  if ! command -v git >/dev/null 2>&1; then
    if [[ ${US_SKIP_FETCH} == 1 ]]; then
      warn "git is not on PATH; --skip-fetch given, so the tree deploys as it stands"
    else
      err "git is not on PATH; re-run with --skip-fetch to deploy the tree as it stands"
      return 1
    fi
  fi
  if [[ ${US_DRY_RUN} == 1 ]]; then
    log "dry run: skipping the docker probe (a plan needs no daemon)"
    return 0
  fi
  if ! resolve_docker_on_path; then
    err "docker is not usable; install it with: ./scripts/manage.sh setup --install-docker"
    return 1
  fi
  return 0
}

#######################################
# Print the branch this run updates. A detached HEAD (stack_git_branch prints
# unknown) is a refusal unless --branch named the branch to stand on.
# Globals:
#   US_BRANCH
# Arguments:
#   None
# Outputs:
#   Branch name on stdout; err on stderr when refused
# Returns:
#   0 ok; 3 detached HEAD without --branch
#######################################
resolve_update_branch() {
  local branch
  branch="$(stack_git_branch)"
  if [[ ${branch} == "unknown" || -z ${branch} ]]; then
    if [[ -n ${US_BRANCH} ]]; then
      echo "${US_BRANCH}"
      return 0
    fi
    err "detached HEAD: there is no branch to fast-forward"
    err "name one: update-stack --branch development (or --branch main)"
    return 3
  fi
  if [[ -n ${US_BRANCH} && ${US_BRANCH} != "${branch}" ]]; then
    echo "${US_BRANCH}"
    return 0
  fi
  echo "${branch}"
}

#######################################
# Map an image ref to its publication lane by tag. Pure: stdout answer only.
# Globals:
#   None
# Arguments:
#   $1  Image ref (registry/name:tag)
# Outputs:
#   production | development | custom on stdout
# Returns:
#   0
#######################################
image_lane() {
  local ref="${1:-}"
  local tag="${ref##*:}"
  case "${tag}" in
    us-safe-studio)
      echo "production"
      ;;
    us-safe-studio-development)
      echo "development"
      ;;
    *)
      echo "custom"
      ;;
  esac
}

#######################################
# Prove the image matches the branch lane: main -> production, anything else
# -> development. An explicit --image / EZ_COMFY_IMAGE from the other lane is a
# refusal unless --allow-lane-mismatch.
# Globals:
#   US_IMAGE, US_ALLOW_LANE_MISMATCH, EZ_COMFY_IMAGE, UPDATE_BRANCH
# Arguments:
#   None
# Outputs:
#   Chosen image ref on stdout; log/warn/err on stderr
# Returns:
#   0 ok; 3 lane mismatch
#######################################
check_image_lane() {
  local explicit="" want_ref want_lane have have_lane
  if [[ -n ${US_IMAGE} ]]; then
    EZ_COMFY_IMAGE="${US_IMAGE}"
    export EZ_COMFY_IMAGE
    explicit="--image"
  elif [[ -n ${EZ_COMFY_IMAGE:-} ]]; then
    explicit="EZ_COMFY_IMAGE"
  fi
  want_ref="ghcr.io/toxicoder/ez-comfy:$(stack_image_tag_for_branch "${UPDATE_BRANCH}")"
  want_lane="$(image_lane "${want_ref}")"
  have="$(stack_default_image)"
  have_lane="$(image_lane "${have}")"
  if [[ ${have_lane} == "${want_lane}" ]]; then
    log "lane ok: ${UPDATE_BRANCH} -> ${have_lane} (${have})"
    echo "${have}"
    return 0
  fi
  if [[ ${US_ALLOW_LANE_MISMATCH} == 1 ]]; then
    warn "lane mismatch accepted by --allow-lane-mismatch: ${have} (${have_lane}) on ${UPDATE_BRANCH} (${want_lane})"
    echo "${have}"
    return 0
  fi
  err "image lane mismatch: ${have} is ${have_lane}, but branch ${UPDATE_BRANCH} publishes ${want_lane}"
  if [[ -n ${explicit} ]]; then
    err "drop ${explicit}, or accept it with --allow-lane-mismatch"
  else
    err "the branch default should be lane-aligned; clear EZ_COMFY_IMAGE or accept with --allow-lane-mismatch"
  fi
  return 3
}

#######################################
# Print the porcelain status of the checkout (empty when clean). Pure: stdout
# answer only; a missing git or a non-repo simply prints nothing.
# Globals:
#   REPO_ROOT
# Arguments:
#   None
# Outputs:
#   One path per line on stdout
# Returns:
#   0
#######################################
dirty_paths() {
  git_at_root status --porcelain 2>/dev/null || true
}

#######################################
# Refuse to pull on top of unpublished work. Prints up to 20 dirty paths.
# Globals:
#   US_ALLOW_DIRTY
# Arguments:
#   None
# Outputs:
#   log/warn/err on stderr
# Returns:
#   0 clean or --allow-dirty; 3 refused
#######################################
check_dirty_tree() {
  local paths
  paths="$(dirty_paths)"
  if [[ -z ${paths} ]]; then
    log "worktree clean"
    return 0
  fi
  local count=0 line
  while IFS= read -r line; do
    if [[ -n ${line} ]]; then
      count=$((count + 1))
    fi
  done <<<"${paths}"
  if [[ ${US_ALLOW_DIRTY} == 1 ]]; then
    warn "worktree dirty (${count} path(s)); proceeding because of --allow-dirty"
    return 0
  fi
  err "refusing to update a dirty worktree (${count} path(s) changed)"
  local shown=0
  while IFS= read -r line; do
    [[ -n ${line} ]] || continue
    shown=$((shown + 1))
    if [[ ${shown} -gt 20 ]]; then
      err "  ... and more"
      break
    fi
    err "  dirty: ${line}"
  done <<<"${paths}"
  err "commit or stash them first, or re-run with --allow-dirty"
  return 3
}

#######################################
# Run git against the proven repo root. Single choke point so every git verb in
# this flow addresses the same checkout.
# Globals:
#   REPO_ROOT
# Arguments:
#   $@  git arguments (no leading "git")
# Outputs:
#   Whatever git prints
# Returns:
#   git status
#######################################
git_at_root() {
  git -C "${REPO_ROOT}" "$@"
}

#######################################
# Turn a failing git pull into a repair the operator can paste.
# Globals:
#   UPDATE_BRANCH
# Arguments:
#   $1  Captured pull output
#   $2  Target branch
# Outputs:
#   err cause + remedy on stderr
# Returns:
#   0
#######################################
classify_pull_failure() {
  local out="${1:-}" branch="${2:-${UPDATE_BRANCH:-}}"
  err "git pull --ff-only failed on ${branch}"
  local shown=0 line
  while IFS= read -r line; do
    [[ -n ${line} ]] || continue
    shown=$((shown + 1))
    if [[ ${shown} -gt 10 ]]; then
      break
    fi
    err "  | ${line}"
  done <<<"${out}"
  case "${out,,}" in
    *"could not resolve host"* | *"unable to access"* | *"connection timed out"*)
      err "network looks broken: check DNS/link, then re-run (or --skip-fetch to deploy as-is)"
      ;;
    *"not possible to fast-forward"* | *"need to specify how to reconcile"*)
      err "the branch diverged from upstream: reconcile it by hand, then re-run"
      ;;
    *"no tracked branch"* | *"has no upstream"*)
      err "no upstream set: git -C ${REPO_ROOT} branch --set-upstream-to=origin/${branch} ${branch}"
      ;;
    *)
      err "resolve the checkout by hand, then re-run this command"
      ;;
  esac
  return 0
}

#######################################
# Fast-forward the checkout. Optional git switch first when --branch named
# another branch. Sets CHANGED_PATHS from the pull's diff; under --dry-run it
# forecasts that diff read-only from @{upstream} instead of pulling. Never
# merges, rebases, or resets.
# Globals:
#   US_BRANCH, US_SKIP_FETCH, US_DRY_RUN, UPDATE_BRANCH, CHANGED_PATHS (written)
# Arguments:
#   None
# Outputs:
#   log/warn/err on stderr
# Returns:
#   0 ok; 1 switch or pull failed
#######################################
sync_checkout() {
  CHANGED_PATHS=""
  if ! command -v git >/dev/null 2>&1; then
    log "no git: deploying the tree as it stands"
    return 0
  fi
  local target current
  target="${UPDATE_BRANCH}"
  current="$(stack_git_branch)"
  if [[ ${target} != "${current}" ]]; then
    if [[ ${US_DRY_RUN} == 1 ]]; then
      log "dry run: would run git switch ${target}"
    elif ! git_at_root switch "${target}"; then
      err "git switch ${target} failed; resolve the checkout by hand, then re-run"
      return 1
    else
      log_ok "switched to ${target}"
    fi
  fi
  if [[ ${US_SKIP_FETCH} == 1 ]]; then
    log "skipping the pull (--skip-fetch); deploying the tree as it stands"
    return 0
  fi
  if [[ ${US_DRY_RUN} == 1 ]]; then
    log "dry run: would run git fetch --prune origin"
    log "dry run: would run git pull --ff-only"
    # Read-only forecast so the plan is real without a pull: the change set the
    # fast-forward would bring in, from the upstream ref this checkout already
    # has. Stale refs are reported as-is; nothing here mutates the checkout.
    local forecast
    forecast="$(git_at_root diff --name-only HEAD "@{upstream}" 2>/dev/null || true)"
    if [[ -n ${forecast} ]]; then
      CHANGED_PATHS="${forecast}"
      log "dry run: change forecast from @{upstream} (no pull performed)"
    fi
    return 0
  fi
  if ! git_at_root fetch --prune origin; then
    warn "git fetch --prune origin failed; continuing with what the checkout has"
  fi
  local before after pull_out
  before="$(git_at_root rev-parse HEAD 2>/dev/null || true)"
  if ! pull_out="$(git_at_root pull --ff-only 2>&1)"; then
    classify_pull_failure "${pull_out}" "${target}"
    return 1
  fi
  after="$(git_at_root rev-parse HEAD 2>/dev/null || true)"
  if [[ -n ${before} && -n ${after} && ${before} != "${after}" ]]; then
    CHANGED_PATHS="$(git_at_root diff --name-only "${before}" "${after}" 2>/dev/null || true)"
    log_ok "updated ${before:0:7} -> ${after:0:7}"
  else
    log_ok "already up to date at ${after:0:7}"
  fi
  return 0
}

#######################################
# Classify one repo-relative path by how it reaches the running stack. Pure:
# stdout answer only.
# Globals:
#   None
# Arguments:
#   $1  Repo-relative path
# Outputs:
#   none | scripts | compose | image on stdout
# Returns:
#   0
#######################################
deploy_class_for_path() {
  local path="${1:-}"
  case "${path}" in
    docker/docker-compose.yml | docker/*.yml | docker/*.yaml)
      echo "compose"
      ;;
    docker/* | config/* | .env)
      echo "image"
      ;;
    scripts/* | studio-ui/*)
      echo "scripts"
      ;;
    *)
      echo "none"
      ;;
  esac
}

#######################################
# Collapse a changed-path list into one deploy relevance class. Pure: stdout
# answer only. image beats compose beats scripts beats none.
# Globals:
#   None
# Arguments:
#   $@  Repo-relative paths (may be empty)
# Outputs:
#   none | scripts | compose | image on stdout
# Returns:
#   0
#######################################
changed_deploy_paths() {
  local path class best="none"
  for path in "$@"; do
    [[ -n ${path} ]] || continue
    class="$(deploy_class_for_path "${path}")"
    if [[ ${class} == "image" ]]; then
      best="image"
    elif [[ ${class} == "compose" && ${best} != "image" ]]; then
      best="compose"
    elif [[ ${class} == "scripts" && ${best} == "none" ]]; then
      best="scripts"
    fi
  done
  echo "${best}"
}

#######################################
# Print the template keys the live env file lacks, one per line. Pure: reads
# two files, writes nothing.
# Globals:
#   None
# Arguments:
#   $1  Template env file
#   $2  Live env file
# Outputs:
#   Missing key names on stdout
# Returns:
#   0
#######################################
env_missing_keys() {
  local template="${1:-}" live="${2:-}"
  [[ -f ${template} ]] || return 0
  local key line
  while IFS= read -r line; do
    [[ ${line} =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)= ]] || continue
    key="${BASH_REMATCH[1]}"
    if [[ ! -f ${live} ]] || ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?${key}=" "${live}" 2>/dev/null; then
      echo "${key}"
    fi
  done <"${template}"
  return 0
}

#######################################
# Report drift between the root env template and the live env file. Warns only;
# the operator's .env is never written.
# Globals:
#   REPO_ROOT, US_DRY_RUN
# Arguments:
#   None
# Outputs:
#   log/warn on stderr
# Returns:
#   0 always
#######################################
reconcile_env_file() {
  local template="${REPO_ROOT}/.env.example" live="${REPO_ROOT}/.env"
  if [[ ! -f ${template} ]]; then
    log "no env template at ${template}; nothing to reconcile"
    return 0
  fi
  if [[ ! -f ${live} ]]; then
    warn "no live env file at ${live}; copy ${template} to it before a real start"
    return 0
  fi
  local missing
  missing="$(env_missing_keys "${template}" "${live}")"
  if [[ -z ${missing} ]]; then
    log "env file has every key the template declares"
    return 0
  fi
  warn ".env is missing $(printf '%s\n' "${missing}" | grep -c .) key(s) from .env.example: $(tr '\n' ' ' <<<"${missing}")"
  warn "add them yourself if the stack needs them; this flow never writes ${live}"
  return 0
}

#######################################
# Predicate: is the stack running? Delegates to compose_is_running (read-only
# compose ps).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 running; 1 not running or unknown
#######################################
stack_is_running() {
  compose_is_running
}

#######################################
# Decide the redeploy action. PURE: stdout is exactly one of none|restart|recreate.
# Bind-mounted payload (scripts class) only needs a restart; image/compose
# classes need a fresh container.
# Globals:
#   US_FORCE_RECREATE
# Arguments:
#   $1  Changed-path class: none | scripts | compose | image
#   $2  Stack state: running | stopped
# Outputs:
#   none | restart | recreate on stdout
# Returns:
#   0
#######################################
plan_redeploy() {
  local class="${1:-none}" state="${2:-stopped}"
  if [[ ${US_FORCE_RECREATE} == 1 ]]; then
    echo "recreate"
    return 0
  fi
  if [[ ${state} == "running" ]]; then
    case "${class}" in
      scripts)
        echo "restart"
        ;;
      compose | image)
        echo "recreate"
        ;;
      *)
        echo "none"
        ;;
    esac
    return 0
  fi
  if [[ ${class} == "none" ]]; then
    echo "none"
  else
    echo "recreate"
  fi
  return 0
}

#######################################
# Pull the lane image. A failed pull is a warning, not a failure: a local build
# remains viable.
# Globals:
#   US_SKIP_IMAGE_PULL, US_DRY_RUN, IMAGE_REF
# Arguments:
#   None
# Outputs:
#   log/warn/err on stderr
# Returns:
#   0 always
#######################################
pull_stack_image() {
  if [[ ${US_SKIP_IMAGE_PULL} == 1 ]]; then
    log "skipping the image pull (--skip-image-pull)"
    return 0
  fi
  if [[ -z ${IMAGE_REF} ]]; then
    warn "no image ref resolved; skipping the pull"
    return 0
  fi
  if [[ ${US_DRY_RUN} == 1 ]]; then
    log "dry run: would run docker pull ${IMAGE_REF}"
    return 0
  fi
  if stack_pull_image "${IMAGE_REF}"; then
    return 0
  fi
  warn "image pull did not succeed for ${IMAGE_REF}; continuing - manage.sh start can still build locally"
  return 0
}

#######################################
# Fail closed when a heavy start would need a terminal we do not have. The
# supported automation path is --yes (LAB_NON_INTERACTIVE=1 +
# LAB_CONFIRM_TOKEN=yes); require_heavy_confirm in manage.sh stays in force.
# Globals:
#   US_YES, US_NO_RESTART, US_DRY_RUN
# Arguments:
#   None
# Outputs:
#   err on stderr when refused
# Returns:
#   0 ok; 3 refused
#######################################
guard_interactive_confirm() {
  if [[ ${US_YES} == 1 || ${US_NO_RESTART} == 1 || ${US_DRY_RUN} == 1 ]]; then
    return 0
  fi
  if [[ -t 0 ]]; then
    return 0
  fi
  err "no terminal to confirm the heavy start through"
  err "automation opt-in: re-run with --yes (sets LAB_NON_INTERACTIVE=1 + LAB_CONFIRM_TOKEN=yes)"
  return 3
}

#######################################
# Apply the plan. Delegates every container verb to manage.sh. --no-restart
# leaves the running stack alone.
# Globals:
#   US_NO_RESTART, US_DRY_RUN, MANAGE_SH, US_ACTIONS (appended)
# Arguments:
#   $1  Plan: none | restart | recreate
# Outputs:
#   log/err on stderr; manage.sh output when not a dry run
# Returns:
#   0 ok; 1 delegated verb failed; 2 unknown plan
#######################################
redeploy_stack() {
  local plan="${1:-${REDEPLOY_PLAN:-none}}"
  if [[ ${US_NO_RESTART} == 1 ]]; then
    log "--no-restart: checkout and image updated; the running stack is untouched"
    return 0
  fi
  case "${plan}" in
    none)
      log "nothing to redeploy; the stack is on the code it already had"
      ;;
    restart)
      if [[ ${US_DRY_RUN} == 1 ]]; then
        log "dry run: would run bash ${MANAGE_SH} restart"
      else
        US_ACTIONS="${US_ACTIONS} restart"
        run_manage restart || return 1
      fi
      ;;
    recreate)
      if [[ ${US_DRY_RUN} == 1 ]]; then
        log "dry run: would run bash ${MANAGE_SH} stop"
        log "dry run: would run bash ${MANAGE_SH} start"
      else
        US_ACTIONS="${US_ACTIONS} stop start"
        run_manage stop || return 1
        run_manage start || return 1
      fi
      ;;
    *)
      err "unknown redeploy plan: ${plan}"
      return 2
      ;;
  esac
  return 0
}

#######################################
# Single delegation point for manage.sh verbs. Never docker / docker compose.
# Globals:
#   US_DRY_RUN, MANAGE_SH
# Arguments:
#   $@  Verb and its flags (start | stop | restart | doctor ...)
# Outputs:
#   log/err on stderr; manage.sh stdout/stderr when not a dry run
# Returns:
#   0 ok or planned; 1 missing verb or failed verb
#######################################
run_manage() {
  local verb="${1:-}"
  if [[ -z ${verb} ]]; then
    err "run_manage: no verb given"
    return 1
  fi
  shift
  local cmd=(bash "${MANAGE_SH}" "${verb}")
  if [[ $# -gt 0 ]]; then
    cmd+=("$@")
  fi
  if [[ ${US_DRY_RUN} == 1 ]]; then
    log "dry run: would run ${cmd[*]}"
    return 0
  fi
  log "running: ${cmd[*]}"
  if ! "${cmd[@]}"; then
    err "manage.sh ${verb} failed; retry with: ./scripts/manage.sh ${verb}"
    return 1
  fi
  return 0
}

#######################################
# Verify the redeploy with the operator doctor. Read-only; never weakens what
# doctor checks.
# Globals:
#   US_DRY_RUN, MANAGE_SH, US_ACTIONS (appended)
# Arguments:
#   None
# Outputs:
#   log/err on stderr; manage.sh doctor output
# Returns:
#   0 ok; 1 doctor reported problems
#######################################
verify_stack() {
  if [[ ${US_DRY_RUN} == 1 ]]; then
    log "dry run: would run bash ${MANAGE_SH} doctor"
    return 0
  fi
  US_ACTIONS="${US_ACTIONS} doctor"
  if ! run_manage doctor; then
    err "doctor reported problems; look next with: ./scripts/manage.sh status"
    return 1
  fi
  return 0
}

#######################################
# Informational promotion note. On main, report how many commits
# origin/development holds that main lacks; on development, report commits in
# development not in origin/main. Missing refs are reported and skipped.
# Globals:
#   UPDATE_BRANCH
# Arguments:
#   None
# Outputs:
#   log on stderr
# Returns:
#   0 always (never fails the run)
#######################################
promotion_note() {
  if ! command -v git >/dev/null 2>&1; then
    log "promotion note: no git on PATH; skipped"
    return 0
  fi
  local range base head_ref count
  case "${UPDATE_BRANCH}" in
    main) range="main..origin/development" ;;
    development) range="origin/main..development" ;;
    *)
      log "promotion note: ${UPDATE_BRANCH} has no promotion lane (only main and development do)"
      return 0
      ;;
  esac
  base="${range%%..*}"
  head_ref="${range##*..}"
  if ! git_at_root rev-parse --verify --quiet "${base}" >/dev/null 2>&1 ||
    ! git_at_root rev-parse --verify --quiet "${head_ref}" >/dev/null 2>&1; then
    log "promotion note: ${base} or ${head_ref} is not in this checkout; skipped"
    return 0
  fi
  count="$(git_at_root rev-list --count "${range}" 2>/dev/null || true)"
  if [[ -z ${count} ]]; then
    log "promotion note: could not count ${range}; skipped"
    return 0
  fi
  if [[ ${UPDATE_BRANCH} == "main" ]]; then
    log "promotion note: origin/development holds ${count} commit(s) that main lacks (unpromoted work)"
  else
    log "promotion note: development holds ${count} commit(s) that origin/main lacks (unpromoted work)"
  fi
  return 0
}

#######################################
# One branch/lane/plan/actions table on stderr.
# Globals:
#   UPDATE_BRANCH, IMAGE_LANE_NAME, IMAGE_REF, DEPLOY_CLASS, CHANGED_PATHS,
#   REDEPLOY_PLAN, US_ACTIONS
# Arguments:
#   None
# Outputs:
#   Summary lines on stderr
# Returns:
#   0 always
#######################################
report_summary() {
  local actions="${US_ACTIONS:-}" changed=0 line
  [[ -n ${actions} ]] || actions="none"
  if [[ ${US_DRY_RUN} == 1 ]]; then
    actions="none (dry run)"
  fi
  if [[ -n ${CHANGED_PATHS} ]]; then
    while IFS= read -r line; do
      if [[ -n ${line} ]]; then
        changed=$((changed + 1))
      fi
    done <<<"${CHANGED_PATHS}"
  fi
  log_step 16 "${UPDATE_STACK_PHASE_TOTAL}" "summary"
  log "  branch : ${UPDATE_BRANCH:-unknown}"
  log "  lane   : ${IMAGE_LANE_NAME:-custom} (${IMAGE_REF:-none})"
  log "  change : ${DEPLOY_CLASS} (${changed} path(s))"
  log "  plan   : ${REDEPLOY_PLAN:-none}"
  log "  actions: ${actions}"
  return 0
}

#######################################
# Run the update-stack flow in the contract's phase order.
# Globals:
#   Every US_* global plus UPDATE_BRANCH / IMAGE_REF / DEPLOY_CLASS /
#   REDEPLOY_PLAN / CHANGED_PATHS / US_ACTIONS
# Arguments:
#   $@  Flags (see update_stack_usage)
# Outputs:
#   Usage on stdout for --help; progress and the summary table on stderr
# Returns:
#   0 ok; 1 failure; 2 usage; 3 guardrail refusal; 5 unprovable repo root
#######################################
main() {
  # Help is a read request, not a deploy: answer it before any phase banner so an
  # operator asking for usage never sees a "1/16" progress counter.
  local arg
  for arg in "$@"; do
    if [[ ${arg} == "-h" || ${arg} == "--help" ]]; then
      update_stack_usage
      return 0
    fi
  done

  log_step 1 "${UPDATE_STACK_PHASE_TOTAL}" "parse_args"
  parse_args "$@" || return $?
  if [[ ${US_HELP} == 1 ]]; then
    update_stack_usage
    return 0
  fi

  log_step 2 "${UPDATE_STACK_PHASE_TOTAL}" "prove_repo_root"
  prove_repo_root || return $?
  MANAGE_SH="${REPO_ROOT}/scripts/manage.sh"

  log_step 3 "${UPDATE_STACK_PHASE_TOTAL}" "update_stack_preflight"
  update_stack_preflight || return $?

  log_step 4 "${UPDATE_STACK_PHASE_TOTAL}" "resolve_update_branch"
  UPDATE_BRANCH="$(resolve_update_branch)" || return $?

  log_step 5 "${UPDATE_STACK_PHASE_TOTAL}" "check_image_lane"
  IMAGE_REF="$(check_image_lane)" || return $?
  IMAGE_LANE_NAME="$(image_lane "${IMAGE_REF}")"

  log_step 6 "${UPDATE_STACK_PHASE_TOTAL}" "check_dirty_tree"
  check_dirty_tree || return $?

  log_step 7 "${UPDATE_STACK_PHASE_TOTAL}" "guard_interactive_confirm"
  guard_interactive_confirm || return $?

  log_step 8 "${UPDATE_STACK_PHASE_TOTAL}" "sync_checkout"
  sync_checkout || return $?

  local -a changed=()
  if [[ -n ${CHANGED_PATHS} ]]; then
    mapfile -t changed <<<"${CHANGED_PATHS}"
  fi

  log_step 9 "${UPDATE_STACK_PHASE_TOTAL}" "changed_deploy_paths"
  DEPLOY_CLASS="$(changed_deploy_paths ${changed[@]+"${changed[@]}"})"

  log_step 10 "${UPDATE_STACK_PHASE_TOTAL}" "reconcile_env_file"
  reconcile_env_file || true

  log_step 11 "${UPDATE_STACK_PHASE_TOTAL}" "plan_redeploy"
  local state="stopped"
  if stack_is_running; then
    state="running"
  fi
  REDEPLOY_PLAN="$(plan_redeploy "${DEPLOY_CLASS}" "${state}")"
  log "stack ${state} + change ${DEPLOY_CLASS} -> plan ${REDEPLOY_PLAN}"

  log_step 12 "${UPDATE_STACK_PHASE_TOTAL}" "pull_stack_image"
  pull_stack_image

  log_step 13 "${UPDATE_STACK_PHASE_TOTAL}" "redeploy_stack"
  redeploy_stack "${REDEPLOY_PLAN}" || return $?

  log_step 14 "${UPDATE_STACK_PHASE_TOTAL}" "verify_stack"
  verify_stack || return $?

  log_step 15 "${UPDATE_STACK_PHASE_TOTAL}" "promotion_note"
  promotion_note || true

  report_summary || true
  return 0
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
