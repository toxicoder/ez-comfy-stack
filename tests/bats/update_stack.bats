#!/usr/bin/env bats
#
# ## update_stack.bats
#
# Cover scripts/utilities/update-stack.sh. This suite pins the deploy
# contract: the phase ORDER, the branch/lane pairing, the redeploy DECISION,
# the REFUSALS, and the manage.sh entry point.
#
# Hermetic: stub binaries only (git + docker via install_mock_bin), a fake
# checkout whose manage.sh just records argv, LAB_HERMETIC=1. No daemon, no
# remote, no network, no volume.

bats_require_minimum_version 1.5.0

load 'test_helper'

setup() {
  setup_repo_env
  export LAB_HERMETIC=1
  # setup_repo_env forces this for compose up; the flow owns it.
  export LAB_STACK_FORCE_BUILD=0
  SCRIPT_UNDER_TEST="${UTILITIES_DIR}/update-stack.sh"
  chmod +x "${SCRIPT_UNDER_TEST}"
  # shellcheck disable=SC1090
  source "${SCRIPT_UNDER_TEST}"
  make_fake_root "${TEST_TMP_DIR}/root"
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  install_docker_mocks
  install_git_stub
  DOCKER_CALLS_LOG="${TEST_TMP_DIR}/docker_calls.log"
  export DOCKER_CALLS_LOG
  : >"${DOCKER_CALLS_LOG}"
  : >"${GIT_CALLS_LOG}"
  : >"${MANAGE_LOG}"
  unset EZ_COMFY_IMAGE
}

teardown() {
  teardown_repo_env
}

#######################################
# Build a proven-but-fake checkout: markers present, libs symlinked to the
# real tree, manage.sh reduced to a recorder.
# Globals:
#   TEST_TMP_DIR, SCRIPT_UNDER_TEST, REPO_ROOT
# Arguments:
#   $1  Root path (default ${TEST_TMP_DIR}/root)
# Outputs:
#   Creates the tree; exports FAKE_ROOT / CLI_SCRIPT / MANAGE_LOG
# Returns:
#   0
#######################################
make_fake_root() {
  local root="${1:-${TEST_TMP_DIR}/root}"
  mkdir -p "${root}/scripts/utilities" "${root}/docker"
  cp -a "${SCRIPT_UNDER_TEST}" "${root}/scripts/utilities/update-stack.sh"
  ln -s "${REPO_ROOT}/scripts/lib" "${root}/scripts/lib"
  : >"${root}/docker/docker-compose.yml"
  cat >"${root}/scripts/manage.sh" <<'MANAGE_STUB'
#!/usr/bin/env bash
echo "manage | $* | ni=${LAB_NON_INTERACTIVE:-} tok=${LAB_CONFIRM_TOKEN:-} frc=${LAB_STACK_FORCE_BUILD:-}" >>"${MANAGE_LOG}"
exit "${STUB_MANAGE_RC:-0}"
MANAGE_STUB
  chmod +x "${root}/scripts/manage.sh"
  FAKE_ROOT="${root}"
  CLI_SCRIPT="${root}/scripts/utilities/update-stack.sh"
  MANAGE_LOG="${TEST_TMP_DIR}/manage_calls.log"
  export FAKE_ROOT CLI_SCRIPT MANAGE_LOG
  : >"${MANAGE_LOG}"
  export STUB_MANAGE_RC=0
  export STUB_GIT_BRANCH=development
  export STUB_GIT_STATUS=''
  export STUB_GIT_DIFF=''
  export STUB_GIT_HEAD_BEFORE=''
  export STUB_GIT_HEAD_AFTER=''
  export STUB_GIT_PULL_RC=0
  export STUB_GIT_PULL_OUT=''
  export STUB_GIT_FETCH_RC=0
  export STUB_GIT_SWITCH_RC=0
  export STUB_GIT_VERIFY_RC=0
  export STUB_GIT_COUNT=3
}

#######################################
# Recording git stub. Answer keys are test-settable STUB_GIT_* variables; the
# HEAD answer moves exactly once so a pull looks like a pull.
# Globals:
#   TEST_TMP_DIR, GIT_CALLS_LOG
# Arguments:
#   None
# Outputs:
#   Mock binary + git_calls.log
# Returns:
#   0
#######################################
install_git_stub() {
  GIT_CALLS_LOG="${TEST_TMP_DIR}/git_calls.log"
  export GIT_CALLS_LOG
  install_mock_bin git '
echo "git $*" >> "${GIT_CALLS_LOG}"
case " $* " in
  *"--verify --quiet"*)
    exit "${STUB_GIT_VERIFY_RC:-0}"
    ;;
  *"rev-parse --abbrev-ref HEAD"*)
    echo "${STUB_GIT_BRANCH:-development}"
    exit 0
    ;;
  *"rev-parse HEAD"*)
    if [[ -n ${STUB_GIT_HEAD_AFTER:-} && ! -f "${TEST_TMP_DIR}/head_moved" ]]; then
      touch "${TEST_TMP_DIR}/head_moved"
      echo "${STUB_GIT_HEAD_BEFORE:-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}"
    else
      echo "${STUB_GIT_HEAD_AFTER:-${STUB_GIT_HEAD_BEFORE:-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb}}"
    fi
    exit 0
    ;;
  *"status --porcelain"*)
    printf "%s\n" "${STUB_GIT_STATUS:-}"
    exit 0
    ;;
  *"diff --name-only"*)
    printf "%s\n" "${STUB_GIT_DIFF:-}"
    exit 0
    ;;
  *"pull --ff-only"*)
    if [[ -n ${STUB_GIT_PULL_OUT:-} ]]; then
      echo "${STUB_GIT_PULL_OUT}"
    fi
    exit "${STUB_GIT_PULL_RC:-0}"
    ;;
  *"fetch --prune"*)
    exit "${STUB_GIT_FETCH_RC:-0}"
    ;;
  *"switch "*)
    exit "${STUB_GIT_SWITCH_RC:-0}"
    ;;
  *"rev-list --count"*)
    echo "${STUB_GIT_COUNT:-3}"
    exit 0
    ;;
esac
exit 0
'
}

#######################################
# Run the CLI hermetically: every root candidate and confirm pair is scrubbed,
# stdin is not a TTY, stdout and stderr are split. Each call starts from clean
# recording logs and a fresh HEAD-move counter, so one test can plan several
# runs and still assert "nothing ran".
# Globals:
#   CLI_SCRIPT, MANAGE_LOG, GIT_CALLS_LOG, DOCKER_CALLS_LOG, TEST_TMP_DIR
# Arguments:
#   $@  Flags for update-stack.sh
# Outputs:
#   Sets status / output / stderr (bats run); truncates the recording logs
# Returns:
#   run status
#######################################
run_cli() {
  : >"${MANAGE_LOG}"
  : >"${GIT_CALLS_LOG}"
  : >"${DOCKER_CALLS_LOG}"
  rm -f "${TEST_TMP_DIR}/head_moved"
  run --separate-stderr env \
    REPO_ROOT= BUILD_WORKSPACE_DIRECTORY= EZ_COMFY_IMAGE= LAB_GIT_BRANCH= \
    LAB_NON_INTERACTIVE= LAB_CONFIRM_TOKEN= \
    bash "${CLI_SCRIPT}" "$@" </dev/null
}

# First line number of a pattern in the captured stderr (empty when absent).
stderr_line_of() {
  local n
  n="$(grep -n -- "$1" <<<"${stderr}" | head -1 | cut -d: -f1 || true)"
  printf '%s\n' "${n}"
}

# --- Pure decisions -------------------------------------------------------

@test "update_stack image_lane maps tags to lanes" {
  run image_lane "ghcr.io/toxicoder/ez-comfy:us-safe-studio"
  [ "${output}" = "production" ]
  run image_lane "ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  [ "${output}" = "development" ]
  run image_lane "ghcr.io/toxicoder/ez-comfy:latest"
  [ "${output}" = "custom" ]
  run image_lane "no-tag-at-all"
  [ "${output}" = "custom" ]
  run image_lane ""
  [ "${output}" = "custom" ]
}

@test "update_stack deploy_class_for_path covers every class" {
  run deploy_class_for_path "docker/docker-compose.yml"
  [ "${output}" = "compose" ]
  run deploy_class_for_path "docker/Dockerfile"
  [ "${output}" = "image" ]
  run deploy_class_for_path "config/policy.json"
  [ "${output}" = "image" ]
  run deploy_class_for_path ".env"
  [ "${output}" = "image" ]
  run deploy_class_for_path "scripts/manage.sh"
  [ "${output}" = "scripts" ]
  run deploy_class_for_path "studio-ui/app.js"
  [ "${output}" = "scripts" ]
  run deploy_class_for_path "docs/readme.md"
  [ "${output}" = "none" ]
  run deploy_class_for_path ""
  [ "${output}" = "none" ]
}

@test "update_stack changed_deploy_paths picks the strongest class" {
  run changed_deploy_paths
  [ "${output}" = "none" ]
  run changed_deploy_paths "docs/a.md" "README.md"
  [ "${output}" = "none" ]
  run changed_deploy_paths "scripts/lib/compose.sh" "workflows/_lab/stills/x.json"
  [ "${output}" = "scripts" ]
  run changed_deploy_paths "docker/docker-compose.yml" "scripts/manage.sh"
  [ "${output}" = "compose" ]
  run changed_deploy_paths "scripts/manage.sh" "docker/Dockerfile"
  [ "${output}" = "image" ]
  run changed_deploy_paths ".env"
  [ "${output}" = "image" ]
}

@test "update_stack plan_redeploy running branches" {
  US_FORCE_RECREATE=0
  run plan_redeploy "scripts" "running"
  [ "${output}" = "restart" ]
  run plan_redeploy "image" "running"
  [ "${output}" = "recreate" ]
  run plan_redeploy "compose" "running"
  [ "${output}" = "recreate" ]
  run plan_redeploy "none" "running"
  [ "${output}" = "none" ]
  # also: update_stack plan_redeploy stopped and forced branches
  US_FORCE_RECREATE=0
  run plan_redeploy "none" "stopped"
  [ "${output}" = "none" ]
  run plan_redeploy "scripts" "stopped"
  [ "${output}" = "recreate" ]
  run plan_redeploy "image"
  [ "${output}" = "recreate" ]
  run plan_redeploy
  [ "${output}" = "none" ]
  US_FORCE_RECREATE=1
  run plan_redeploy "none" "running"
  [ "${output}" = "recreate" ]
  run plan_redeploy "none" "stopped"
  [ "${output}" = "recreate" ]
  US_FORCE_RECREATE=0
  # also: update_stack plan_redeploy is pure stdout only
  [ "$(plan_redeploy "scripts" "running")" = "restart" ]
  [ "${REDEPLOY_PLAN}" = "none" ]
  [ "$(changed_deploy_paths "docker/Dockerfile")" = "image" ]
  [ "${DEPLOY_CLASS}" = "none" ]
}
@test "update_stack env_missing_keys lists only absent keys" {
  local tpl live
  tpl="${TEST_TMP_DIR}/.env.example"
  live="${TEST_TMP_DIR}/.env"
  cat >"${tpl}" <<'TPL'
# comment
MODELS_DIR=/mnt/models
COMFY_OUTPUT_DIR=/mnt/comfy-output
# HF_TOKEN=ignored
EZ_LLM_TIMEOUT_S=60
TPL
  printf '%s\n' 'MODELS_DIR=/tmp/m' 'export EZ_LLM_TIMEOUT_S=5' >"${live}"
  run env_missing_keys "${tpl}" "${live}"
  [ "${output}" = "COMFY_OUTPUT_DIR" ]
  printf '%s\n' 'MODELS_DIR=/tmp/m' 'EZ_LLM_TIMEOUT_S=5' 'COMFY_OUTPUT_DIR=/tmp/o' >"${live}"
  run env_missing_keys "${tpl}" "${live}"
  [ -z "${output}" ]
  run env_missing_keys "${TEST_TMP_DIR}/nope.example" "${live}"
  [ -z "${output}" ]
  # also: update_stack reconcile_env_file warns without writing the env file
  REPO_ROOT="${FAKE_ROOT}"
  run reconcile_env_file
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"no env template"* ]]
  printf '%s\n' 'MODELS_DIR=/mnt/models' 'COMFY_OUTPUT_DIR=/mnt/comfy-output' >"${FAKE_ROOT}/.env.example"
  run reconcile_env_file
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"no live env file"* ]]
  printf '%s\n' 'MODELS_DIR=/mnt/models' >"${FAKE_ROOT}/.env"
  run reconcile_env_file
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"COMFY_OUTPUT_DIR"* ]]
  [[ "${output}" == *"never writes"* ]]
  [ "$(cat "${FAKE_ROOT}/.env")" = "MODELS_DIR=/mnt/models" ]
  printf '%s\n' 'MODELS_DIR=/mnt/models' 'COMFY_OUTPUT_DIR=/mnt/comfy-output' >"${FAKE_ROOT}/.env"
  run reconcile_env_file
  [[ "${output}" == *"every key"* ]]
}
@test "update_stack usage names the flags and exits 0" {
  run update_stack_usage
  [ "${status}" -eq 0 ]
  [[ "${output}" == usage:* ]]
  [[ "${output}" == *"--allow-lane-mismatch"* ]]
  [[ "${output}" == *"--force-recreate"* ]]
}

@test "update_stack parse_args sets flags and exports the confirm pair" {
  local rc=0
  parse_args --dry-run --branch development --allow-dirty --skip-fetch \
    --skip-image-pull --force-recreate --allow-lane-mismatch --yes --force-build || rc=$?
  [ "${rc}" -eq 0 ]
  [ "${US_DRY_RUN}" -eq 1 ]
  [ "${US_BRANCH}" = "development" ]
  [ "${US_ALLOW_DIRTY}" -eq 1 ]
  [ "${US_SKIP_FETCH}" -eq 1 ]
  [ "${US_SKIP_IMAGE_PULL}" -eq 1 ]
  [ "${US_FORCE_RECREATE}" -eq 1 ]
  [ "${US_ALLOW_LANE_MISMATCH}" -eq 1 ]
  [ "${US_YES}" -eq 1 ]
  [ "${LAB_NON_INTERACTIVE}" = "1" ]
  [ "${LAB_CONFIRM_TOKEN}" = "yes" ]
  [ "${LAB_STACK_FORCE_BUILD}" = "1" ]
  rc=0
  parse_args --image ghcr.io/x/y:tag || rc=$?
  [ "${rc}" -eq 0 ]
  [ "${US_IMAGE}" = "ghcr.io/x/y:tag" ]
}

@test "update_stack parse_args rejects bad argv with 2" {
  local rc=0
  parse_args --bogus || rc=$?
  [ "${rc}" -eq 2 ]
  rc=0
  parse_args update-stack || rc=$?
  [ "${rc}" -eq 2 ]
  rc=0
  parse_args --branch || rc=$?
  [ "${rc}" -eq 2 ]
  rc=0
  parse_args --image || rc=$?
  [ "${rc}" -eq 2 ]
}

@test "update_stack every phase function exists as a named function" {
  local fns=(
    update_stack_usage parse_args prove_repo_root update_stack_preflight
    resolve_update_branch image_lane check_image_lane dirty_paths
    check_dirty_tree git_at_root sync_checkout classify_pull_failure
    deploy_class_for_path changed_deploy_paths env_missing_keys
    reconcile_env_file stack_is_running plan_redeploy pull_stack_image
    guard_interactive_confirm redeploy_stack run_manage verify_stack
    promotion_note report_summary
  )
  local f
  for f in "${fns[@]}"; do
    grep -Eq "^${f}[[:space:]]*\(\)[[:space:]]*\{" "${SCRIPT_UNDER_TEST}"
    [ "$(type -t "${f}")" = "function" ]
  done
}

# --- Repo root and preflight ---------------------------------------------

@test "update_stack prove_repo_root honours BUILD_WORKSPACE_DIRECTORY" {
  BUILD_WORKSPACE_DIRECTORY="${FAKE_ROOT}" prove_repo_root
  [ "${REPO_ROOT}" = "${FAKE_ROOT}" ]
  # also: update_stack prove_repo_root falls back to the script location
  local saved="${SCRIPT_DIR}"
  SCRIPT_DIR="${FAKE_ROOT}/scripts/utilities"
  BUILD_WORKSPACE_DIRECTORY= prove_repo_root
  [ "${REPO_ROOT}" = "${FAKE_ROOT}" ]
  SCRIPT_DIR="${saved}"
}
@test "update_stack unprovable repo root exits 5 before any step" {
  local broken="${TEST_TMP_DIR}/broken"
  mkdir -p "${broken}/scripts/utilities" "${broken}/docker"
  cp -a "${SCRIPT_UNDER_TEST}" "${broken}/scripts/utilities/update-stack.sh"
  ln -s "${REPO_ROOT}/scripts/lib" "${broken}/scripts/lib"
  : >"${broken}/docker/docker-compose.yml"
  run --separate-stderr env REPO_ROOT= BUILD_WORKSPACE_DIRECTORY= EZ_COMFY_IMAGE= \
    LAB_GIT_BRANCH= bash "${broken}/scripts/utilities/update-stack.sh" --yes </dev/null
  [ "${status}" -eq 5 ]
  [[ "${stderr}" == *"cannot prove a repo root"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  [ ! -s "${GIT_CALLS_LOG}" ]
  [ ! -s "${DOCKER_CALLS_LOG}" ]
}

@test "update_stack preflight passes with git and docker present" {
  US_DRY_RUN=0
  run update_stack_preflight
  [ "${status}" -eq 0 ]
  # also: update_stack preflight needs git unless skip-fetch
  local empty="${TEST_TMP_DIR}/emptybin"
  mkdir -p "${empty}"
  US_SKIP_FETCH=0
  US_DRY_RUN=1
  local rc=0
  (PATH="${empty}" update_stack_preflight) || rc=$?
  [ "${rc}" -eq 1 ]
  rc=0
  US_SKIP_FETCH=1
  (PATH="${empty}" update_stack_preflight) || rc=$?
  [ "${rc}" -eq 0 ]
  # also: update_stack preflight skips the docker probe in dry run
  local empty="${TEST_TMP_DIR}/emptybin2"
  mkdir -p "${empty}"
  US_DRY_RUN=1
  US_SKIP_FETCH=1
  local rc=0
  (PATH="${empty}" update_stack_preflight) || rc=$?
  [ "${rc}" -eq 0 ]
}
# --- Branch and lane guardrails ------------------------------------------

@test "update_stack resolve_update_branch prints the checked-out branch" {
  unset LAB_GIT_BRANCH
  STUB_GIT_BRANCH=feature/lane-pairing
  run resolve_update_branch
  [ "${status}" -eq 0 ]
  [ "${output}" = "feature/lane-pairing" ]
  # also: update_stack resolve_update_branch honours a different branch
  export LAB_GIT_BRANCH=development
  US_BRANCH=main
  run resolve_update_branch
  [ "${status}" -eq 0 ]
  [ "${output}" = "main" ]
  US_BRANCH=development
  run resolve_update_branch
  [ "${output}" = "development" ]
}
@test "update_stack resolve_update_branch refuses detached HEAD without branch" {
  unset LAB_GIT_BRANCH
  STUB_GIT_BRANCH=HEAD
  US_BRANCH=""
  run resolve_update_branch
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"detached HEAD"* ]]
  [[ "${output}" == *"--branch"* ]]
  US_BRANCH=development
  run resolve_update_branch
  [ "${status}" -eq 0 ]
  [ "${output}" = "development" ]
}

@test "update_stack check_image_lane pairs development with the dev tag" {
  unset EZ_COMFY_IMAGE
  US_IMAGE=""
  US_ALLOW_LANE_MISMATCH=0
  UPDATE_BRANCH=development
  run --separate-stderr check_image_lane
  [ "${status}" -eq 0 ]
  [ "${output}" = "ghcr.io/toxicoder/ez-comfy:us-safe-studio-development" ]
  # also: update_stack check_image_lane pairs main with the production tag
  unset EZ_COMFY_IMAGE
  export LAB_GIT_BRANCH=main
  US_IMAGE=""
  US_ALLOW_LANE_MISMATCH=0
  UPDATE_BRANCH=main
  run --separate-stderr check_image_lane
  [ "${status}" -eq 0 ]
  [ "${output}" = "ghcr.io/toxicoder/ez-comfy:us-safe-studio" ]
  unset LAB_GIT_BRANCH
}
@test "update_stack check_image_lane refuses the other lane" {
  US_IMAGE=""
  US_ALLOW_LANE_MISMATCH=0
  EZ_COMFY_IMAGE="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  export EZ_COMFY_IMAGE
  UPDATE_BRANCH=main
  run check_image_lane
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"image lane mismatch"* ]]
  [[ "${output}" == *"--allow-lane-mismatch"* ]]
  unset EZ_COMFY_IMAGE
  # also: update_stack check_image_lane accepts a mismatch when opted in
  UPDATE_BRANCH=main
  US_IMAGE="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  US_ALLOW_LANE_MISMATCH=1
  run --separate-stderr check_image_lane
  [ "${status}" -eq 0 ]
  [ "${output}" = "ghcr.io/toxicoder/ez-comfy:us-safe-studio-development" ]
  [[ "${stderr}" == *"lane mismatch accepted"* ]]
  US_ALLOW_LANE_MISMATCH=0
  US_IMAGE="registry.example.com/team/ez-comfy:nightly"
  run check_image_lane
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"custom"* ]]
}
@test "update_stack dirty_paths and check_dirty_tree refuse a dirty tree" {
  REPO_ROOT="${FAKE_ROOT}"
  STUB_GIT_STATUS=' M scripts/manage.sh
?? docker/Dockerfile'
  US_ALLOW_DIRTY=0
  run dirty_paths
  [[ "${output}" == *"scripts/manage.sh"* ]]
  run check_dirty_tree
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"refusing to update a dirty worktree"* ]]
  [[ "${output}" == *"dirty:  M scripts/manage.sh"* ]]
  [[ "${output}" == *"--allow-dirty"* ]]
  # also: update_stack check_dirty_tree passes clean or with allow-dirty
  REPO_ROOT="${FAKE_ROOT}"
  STUB_GIT_STATUS=''
  run check_dirty_tree
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"worktree clean"* ]]
  STUB_GIT_STATUS=' M scripts/manage.sh'
  US_ALLOW_DIRTY=1
  run check_dirty_tree
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--allow-dirty"* ]]
  US_ALLOW_DIRTY=0
}
@test "update_stack check_dirty_tree caps the path list at 20" {
  REPO_ROOT="${FAKE_ROOT}"
  local i paths=''
  for i in $(seq 1 25); do
    paths="${paths} M file${i}.txt
"
  done
  STUB_GIT_STATUS="${paths}"
  US_ALLOW_DIRTY=0
  run check_dirty_tree
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"... and more"* ]]
  [ "$(grep -c '  dirty: ' <<<"${output}")" -eq 20 ]
}

@test "update_stack guard_interactive_confirm fails closed without a TTY" {
  US_YES=0
  US_NO_RESTART=0
  US_DRY_RUN=0
  run guard_interactive_confirm </dev/null
  [ "${status}" -eq 3 ]
  [[ "${output}" == *"no terminal"* ]]
  [[ "${output}" == *"--yes"* ]]
  US_YES=1
  run guard_interactive_confirm </dev/null
  [ "${status}" -eq 0 ]
  US_YES=0
  US_NO_RESTART=1
  run guard_interactive_confirm </dev/null
  [ "${status}" -eq 0 ]
  US_NO_RESTART=0
  US_DRY_RUN=1
  run guard_interactive_confirm </dev/null
  [ "${status}" -eq 0 ]
  US_DRY_RUN=0
}

# --- Checkout sync -------------------------------------------------------

@test "update_stack git_at_root addresses the proven root" {
  REPO_ROOT="${FAKE_ROOT}"
  : >"${GIT_CALLS_LOG}"
  run git_at_root status --porcelain
  [ "${status}" -eq 0 ]
  [[ "$(cat "${GIT_CALLS_LOG}")" == *"git -C ${FAKE_ROOT} status --porcelain"* ]]
}

@test "update_stack sync_checkout skip-fetch pulls nothing" {
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  US_SKIP_FETCH=1
  US_DRY_RUN=0
  CHANGED_PATHS='stale'
  : >"${GIT_CALLS_LOG}"
  sync_checkout >"${TEST_TMP_DIR}/out.log" 2>&1
  grep -q 'skipping the pull' "${TEST_TMP_DIR}/out.log"
  [ -z "${CHANGED_PATHS}" ]
  ! grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
}

@test "update_stack sync_checkout dry run plans git and runs nothing" {
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  US_SKIP_FETCH=0
  US_DRY_RUN=1
  US_FORCE_RECREATE=0
  : >"${GIT_CALLS_LOG}"
  sync_checkout >"${TEST_TMP_DIR}/out.log" 2>&1
  grep -q 'dry run: would run git fetch --prune origin' "${TEST_TMP_DIR}/out.log"
  grep -q 'dry run: would run git pull --ff-only' "${TEST_TMP_DIR}/out.log"
  ! grep -qE 'pull --ff-only|fetch --prune' "${GIT_CALLS_LOG}"
  STUB_GIT_DIFF='docker/Dockerfile'
  CHANGED_PATHS=''
  sync_checkout >"${TEST_TMP_DIR}/forecast.log" 2>&1
  grep -q 'change forecast from @{upstream}' "${TEST_TMP_DIR}/forecast.log"
  [[ "${CHANGED_PATHS}" == *"docker/Dockerfile"* ]]
  ! grep -qE 'pull --ff-only|fetch --prune' "${GIT_CALLS_LOG}"
  STUB_GIT_DIFF=''
  US_DRY_RUN=0
}

@test "update_stack sync_checkout records the pull diff" {
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  US_SKIP_FETCH=0
  US_DRY_RUN=0
  STUB_GIT_HEAD_BEFORE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='scripts/lib/compose.sh
docker/docker-compose.yml'
  CHANGED_PATHS=''
  sync_checkout >"${TEST_TMP_DIR}/out.log" 2>&1
  grep -q 'updated aaaaaaa -> bbbbbbb' "${TEST_TMP_DIR}/out.log"
  [[ "${CHANGED_PATHS}" == *"docker/docker-compose.yml"* ]]
  [[ "${CHANGED_PATHS}" == *"scripts/lib/compose.sh"* ]]
  STUB_GIT_HEAD_AFTER=''
  STUB_GIT_HEAD_BEFORE=''
  # also: update_stack sync_checkout reports already up to date
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  US_SKIP_FETCH=0
  US_DRY_RUN=0
  STUB_GIT_DIFF='scripts/manage.sh'
  CHANGED_PATHS='stale'
  sync_checkout >"${TEST_TMP_DIR}/out.log" 2>&1
  grep -q 'already up to date' "${TEST_TMP_DIR}/out.log"
  [ -z "${CHANGED_PATHS}" ]
  STUB_GIT_DIFF=''
}
@test "update_stack sync_checkout switches only for another branch" {
  REPO_ROOT="${FAKE_ROOT}"
  export LAB_GIT_BRANCH=development
  UPDATE_BRANCH=development
  : >"${GIT_CALLS_LOG}"
  run sync_checkout
  [[ "${output}" != *"switched to"* ]]
  ! grep -q ' switch ' "${GIT_CALLS_LOG}"
  UPDATE_BRANCH=main
  run sync_checkout
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"switched to main"* ]]
  grep -q 'switch main' "${GIT_CALLS_LOG}"
  UPDATE_BRANCH=development
  unset LAB_GIT_BRANCH
}

@test "update_stack sync_checkout switch failure is a hard failure" {
  REPO_ROOT="${FAKE_ROOT}"
  export LAB_GIT_BRANCH=development
  UPDATE_BRANCH=main
  STUB_GIT_SWITCH_RC=1
  run sync_checkout
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"git switch main failed"* ]]
  STUB_GIT_SWITCH_RC=0
  UPDATE_BRANCH=development
  unset LAB_GIT_BRANCH
  # also: update_stack sync_checkout warns and continues when fetch fails
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  STUB_GIT_FETCH_RC=1
  run sync_checkout
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"git fetch --prune origin failed"* ]]
  STUB_GIT_FETCH_RC=0
}
@test "update_stack sync_checkout classifies a fast-forward failure" {
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  STUB_GIT_PULL_RC=1
  STUB_GIT_PULL_OUT='fatal: Not possible to fast-forward, aborting.'
  run sync_checkout
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"reconcile it by hand"* ]]
  [[ "${output}" == *"| fatal: Not possible to fast-forward"* ]]
  STUB_GIT_PULL_RC=0
  STUB_GIT_PULL_OUT=''
  # also: update_stack classify_pull_failure names a pasteable repair
  run classify_pull_failure "fatal: unable to access: Could not resolve host: github.com" development
  [[ "${output}" == *"network looks broken"* ]]
  run classify_pull_failure "fatal: no upstream (no tracked branch)" development
  [[ "${output}" == *"--set-upstream-to=origin/development"* ]]
  run classify_pull_failure "something else entirely" main
  [[ "${output}" == *"git pull --ff-only failed on main"* ]]
  [[ "${output}" == *"resolve the checkout by hand"* ]]
}
# --- Env reconcile and running probe -------------------------------------

@test "update_stack stack_is_running reads compose state" {
  REPO_ROOT="${FAKE_ROOT}"
  rm -f "${TEST_TMP_DIR}/compose_running"
  run stack_is_running
  [ "${status}" -eq 1 ]
  touch "${TEST_TMP_DIR}/compose_running"
  run stack_is_running
  [ "${status}" -eq 0 ]
}

# --- Image pull, redeploy, verify ----------------------------------------

@test "update_stack pull_stack_image warns and continues on a failed pull" {
  IMAGE_REF="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  US_SKIP_IMAGE_PULL=0
  US_DRY_RUN=0
  export LAB_STACK_SKIP_PULL=1
  run pull_stack_image
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"did not succeed"* ]]
  [[ "${output}" == *"manage.sh start can still build locally"* ]]
  # also: update_stack pull_stack_image honours skip flags and dry run
  IMAGE_REF="ghcr.io/toxicoder/ez-comfy:us-safe-studio"
  US_SKIP_IMAGE_PULL=1
  run pull_stack_image
  [[ "${output}" == *"--skip-image-pull"* ]]
  US_SKIP_IMAGE_PULL=0
  US_DRY_RUN=1
  run pull_stack_image
  [[ "${output}" == *"dry run: would run docker pull ghcr.io/toxicoder/ez-comfy:us-safe-studio"* ]]
  IMAGE_REF=""
  run pull_stack_image
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"no image ref"* ]]
  US_DRY_RUN=0
  # also: update_stack pull_stack_image issues docker pull when allowed
  IMAGE_REF="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  US_SKIP_IMAGE_PULL=0
  US_DRY_RUN=0
  export LAB_STACK_SKIP_PULL=0
  run pull_stack_image
  [ "${status}" -eq 0 ]
  grep -q 'docker pull' "${DOCKER_CALLS_LOG}"
  export LAB_STACK_SKIP_PULL=1
}
@test "update_stack run_manage delegates to manage.sh only" {
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=0
  : >"${MANAGE_LOG}"
  run run_manage status
  [ "${status}" -eq 0 ]
  [ "$(cat "${MANAGE_LOG}")" = "manage | status | ni= tok= frc=0" ]
  run run_manage
  [ "${status}" -eq 1 ]
  # also: update_stack run_manage prints the literal command in dry run
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=1
  : >"${MANAGE_LOG}"
  run run_manage start
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"dry run: would run bash ${FAKE_ROOT}/scripts/manage.sh start"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  US_DRY_RUN=0
}
@test "update_stack redeploy_stack dry run mutates nothing" {
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=1
  US_NO_RESTART=0
  : >"${MANAGE_LOG}"
  run redeploy_stack recreate
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"would run bash ${FAKE_ROOT}/scripts/manage.sh stop"* ]]
  [[ "${output}" == *"would run bash ${FAKE_ROOT}/scripts/manage.sh start"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  run redeploy_stack restart
  [[ "${output}" == *"would run bash ${FAKE_ROOT}/scripts/manage.sh restart"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  US_DRY_RUN=0
}

@test "update_stack redeploy_stack recreate stops before it starts" {
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=0
  US_NO_RESTART=0
  : >"${MANAGE_LOG}"
  US_ACTIONS=''
  redeploy_stack recreate >"${TEST_TMP_DIR}/out.log" 2>&1
  [ "$(sed -n '1p' "${MANAGE_LOG}")" = "manage | stop | ni= tok= frc=0" ]
  [ "$(sed -n '2p' "${MANAGE_LOG}")" = "manage | start | ni= tok= frc=0" ]
  [[ "${US_ACTIONS}" == *"stop start"* ]]
  # also: update_stack redeploy_stack restart and none call one verb
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=0
  US_NO_RESTART=0
  : >"${MANAGE_LOG}"
  run redeploy_stack restart
  [ "$(cat "${MANAGE_LOG}")" = "manage | restart | ni= tok= frc=0" ]
  : >"${MANAGE_LOG}"
  run redeploy_stack none
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"nothing to redeploy"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  run redeploy_stack nonsense
  [ "${status}" -eq 2 ]
  [[ "${output}" == *"unknown redeploy plan"* ]]
  # also: update_stack redeploy_stack no-restart performs no redeploy call
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_NO_RESTART=1
  US_DRY_RUN=0
  : >"${MANAGE_LOG}"
  run redeploy_stack recreate
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"--no-restart"* ]]
  [[ "${output}" == *"running stack is untouched"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  US_NO_RESTART=0
}
@test "update_stack verify_stack runs doctor and reports failure" {
  MANAGE_SH="${FAKE_ROOT}/scripts/manage.sh"
  US_DRY_RUN=0
  : >"${MANAGE_LOG}"
  run verify_stack
  [ "${status}" -eq 0 ]
  [ "$(cat "${MANAGE_LOG}")" = "manage | doctor | ni= tok= frc=0" ]
  STUB_MANAGE_RC=1
  run verify_stack
  [ "${status}" -eq 1 ]
  [[ "${output}" == *"doctor reported problems"* ]]
  STUB_MANAGE_RC=0
  US_DRY_RUN=1
  run verify_stack
  [[ "${output}" == *"dry run: would run bash ${FAKE_ROOT}/scripts/manage.sh doctor"* ]]
  US_DRY_RUN=0
}

@test "update_stack promotion_note is informational and never fails" {
  REPO_ROOT="${FAKE_ROOT}"
  UPDATE_BRANCH=development
  run promotion_note
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"development holds 3 commit(s) that origin/main lacks"* ]]
  UPDATE_BRANCH=main
  run promotion_note
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"origin/development holds 3 commit(s) that main lacks"* ]]
  UPDATE_BRANCH=feature/no-lane
  run promotion_note
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"no promotion lane"* ]]
  UPDATE_BRANCH=development
  STUB_GIT_VERIFY_RC=1
  run promotion_note
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"not in this checkout; skipped"* ]]
  STUB_GIT_VERIFY_RC=0
}

@test "update_stack report_summary prints one branch/lane/plan/actions table" {
  UPDATE_BRANCH=development
  IMAGE_LANE_NAME=development
  IMAGE_REF="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  DEPLOY_CLASS=scripts
  CHANGED_PATHS='scripts/manage.sh
docs/a.md'
  REDEPLOY_PLAN=restart
  US_ACTIONS=" restart doctor"
  US_DRY_RUN=0
  run report_summary
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"branch : development"* ]]
  [[ "${output}" == *"lane   : development (ghcr.io/toxicoder/ez-comfy:us-safe-studio-development)"* ]]
  [[ "${output}" == *"change : scripts (2 path(s))"* ]]
  [[ "${output}" == *"plan   : restart"* ]]
  [[ "${output}" == *"actions:  restart doctor"* ]]
  US_DRY_RUN=1
  run report_summary
  [[ "${output}" == *"actions: none (dry run)"* ]]
  US_DRY_RUN=0
  CHANGED_PATHS=''
  US_ACTIONS=''
}

# --- Sequence and CLI refusals -------------------------------------------

@test "update_stack CLI runs the phases in the contract order" {
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='scripts/lib/compose.sh'
  run_cli --yes
  [ "${status}" -eq 0 ]
  local a b c d e f g h i j k l m n
  a="$(stderr_line_of 'resolve_update_branch')"
  b="$(stderr_line_of 'check_image_lane')"
  c="$(stderr_line_of 'check_dirty_tree')"
  d="$(stderr_line_of 'guard_interactive_confirm')"
  e="$(stderr_line_of 'sync_checkout')"
  f="$(stderr_line_of 'changed_deploy_paths')"
  g="$(stderr_line_of 'reconcile_env_file')"
  h="$(stderr_line_of 'plan_redeploy')"
  i="$(stderr_line_of 'pull_stack_image')"
  j="$(stderr_line_of 'redeploy_stack')"
  k="$(stderr_line_of 'verify_stack')"
  l="$(stderr_line_of 'promotion_note')"
  m="$(stderr_line_of 'summary')"
  n="$(stderr_line_of 'parse_args')"
  [ -n "${a}" ] && [ -n "${m}" ] && [ -n "${n}" ]
  [ "${n}" -lt "${a}" ]
  [ "${a}" -lt "${b}" ]
  [ "${b}" -lt "${c}" ]
  [ "${c}" -lt "${d}" ]
  [ "${d}" -lt "${e}" ]
  [ "${e}" -lt "${f}" ]
  [ "${f}" -lt "${g}" ]
  [ "${g}" -lt "${h}" ]
  [ "${h}" -lt "${i}" ]
  [ "${i}" -lt "${j}" ]
  [ "${j}" -lt "${k}" ]
  [ "${k}" -lt "${l}" ]
  [ "${l}" -lt "${m}" ]
  [ "$(grep -c 'would run' <<<"${stderr}")" -eq 0 ]
  [ "$(sed -n '1p' "${MANAGE_LOG}")" = "manage | restart | ni=1 tok=yes frc=0" ]
  [ "$(sed -n '2p' "${MANAGE_LOG}")" = "manage | doctor | ni=1 tok=yes frc=0" ]
  [ "$(wc -l <"${MANAGE_LOG}" | tr -d ' ')" = "2" ]
}

@test "update_stack CLI recreates for an image-class change on main" {
  export STUB_GIT_BRANCH=main
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='docker/Dockerfile'
  run_cli --yes
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"lane ok: main -> production (ghcr.io/toxicoder/ez-comfy:us-safe-studio)"* ]]
  [[ "${stderr}" == *"stack running + change image -> plan recreate"* ]]
  [[ "${stderr}" == *"lane   : production (ghcr.io/toxicoder/ez-comfy:us-safe-studio)"* ]]
  [ "$(sed -n '1p' "${MANAGE_LOG}")" = "manage | stop | ni=1 tok=yes frc=0" ]
  [ "$(sed -n '2p' "${MANAGE_LOG}")" = "manage | start | ni=1 tok=yes frc=0" ]
  # also: update_stack CLI stops a stopped stack never and recreates on change
  export STUB_GIT_BRANCH=development
  rm -f "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='config/policy.json'
  run_cli --yes
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"stack stopped + change image -> plan recreate"* ]]
  [[ "$(grep -c 'manage | stop' "${MANAGE_LOG}")" -eq 1 ]]
  [[ "$(grep -c 'manage | start' "${MANAGE_LOG}")" -eq 1 ]]
}
@test "update_stack CLI force-recreate overrides a scripts-class restart" {
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='scripts/manage.sh'
  run_cli --yes --force-recreate
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"plan recreate"* ]]
  grep -q 'manage | stop' "${MANAGE_LOG}"
  ! grep -q 'manage | restart' "${MANAGE_LOG}"
  # also: update_stack CLI no-restart leaves the stack alone
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='docker/Dockerfile'
  run_cli --yes --no-restart
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"--no-restart"* ]]
  ! grep -qE 'manage \| (stop|start|restart)' "${MANAGE_LOG}"
  grep -q 'manage | doctor' "${MANAGE_LOG}"
  # also: update_stack CLI force-build exports the build flag to manage.sh
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='scripts/manage.sh'
  run_cli --yes --force-build
  [ "${status}" -eq 0 ]
  grep -q 'manage | restart | ni=1 tok=yes frc=1' "${MANAGE_LOG}"
}
@test "update_stack CLI dry run mutates nothing" {
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='docker/Dockerfile'
  run_cli --dry-run
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"dry run: would run git pull --ff-only"* ]]
  [[ "${stderr}" == *"change forecast from @{upstream}"* ]]
  [[ "${stderr}" == *"stack running + change image -> plan recreate"* ]]
  [[ "${stderr}" == *"dry run: would run docker pull"* ]]
  [[ "${stderr}" == *"dry run: would run bash ${FAKE_ROOT}/scripts/manage.sh stop"* ]]
  [[ "${stderr}" == *"dry run: would run bash ${FAKE_ROOT}/scripts/manage.sh start"* ]]
  [[ "${stderr}" == *"dry run: would run bash ${FAKE_ROOT}/scripts/manage.sh doctor"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  ! grep -qE 'docker pull|compose .*(up|down|restart|rmi|build)' "${DOCKER_CALLS_LOG}"
  ! grep -qE 'pull --ff-only|fetch --prune' "${GIT_CALLS_LOG}"
  # also: update_stack CLI dry run still refuses unsafe checkouts
  STUB_GIT_STATUS=' M scripts/manage.sh'
  run_cli --dry-run
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"refusing to update a dirty worktree"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  ! grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
}
@test "update_stack CLI refuses a dirty tree before mutating" {
  STUB_GIT_STATUS=' M scripts/manage.sh'
  run_cli --yes
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"refusing to update a dirty worktree"* ]]
  [[ "${stderr}" == *"--allow-dirty"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  ! grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
  # also: update_stack CLI proceeds with a dirty tree when opted in
  STUB_GIT_STATUS=' M scripts/manage.sh'
  run_cli --yes --allow-dirty
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"proceeding because of --allow-dirty"* ]]
  grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
}
@test "update_stack CLI refuses detached HEAD without branch" {
  STUB_GIT_BRANCH=HEAD
  run_cli --yes
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"detached HEAD"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  ! grep -qE 'pull --ff-only|fetch --prune| switch ' "${GIT_CALLS_LOG}"
  # also: update_stack CLI runs on detached HEAD with branch
  STUB_GIT_BRANCH=HEAD
  run_cli --yes --branch development
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"lane ok: development"* ]]
  grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
  grep -q 'manage | doctor' "${MANAGE_LOG}"
}
@test "update_stack CLI refuses the wrong image lane" {
  export STUB_GIT_BRANCH=main
  local dev_ref="ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  run_cli --yes --image "${dev_ref}"
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"image lane mismatch"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  run_cli --yes --allow-lane-mismatch --image "${dev_ref}"
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"lane mismatch accepted by --allow-lane-mismatch"* ]]
  [[ "${stderr}" == *"lane   : development (${dev_ref})"* ]]
  run --separate-stderr env REPO_ROOT= BUILD_WORKSPACE_DIRECTORY= LAB_GIT_BRANCH= \
    LAB_NON_INTERACTIVE= LAB_CONFIRM_TOKEN= EZ_COMFY_IMAGE="${dev_ref}" \
    bash "${CLI_SCRIPT}" --yes </dev/null
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"drop EZ_COMFY_IMAGE"* ]]
  # also: update_stack CLI honours the image flag
  export STUB_GIT_BRANCH=development
  run_cli --yes --image "ghcr.io/toxicoder/ez-comfy:us-safe-studio-development"
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"lane   : development"* ]]
  run_cli --yes --image "ghcr.io/toxicoder/ez-comfy:us-safe-studio"
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"image lane mismatch"* ]]
}
@test "update_stack CLI refuses a non-TTY start without yes" {
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='docker/Dockerfile'
  run_cli
  [ "${status}" -eq 3 ]
  [[ "${stderr}" == *"no terminal to confirm the heavy start through"* ]]
  [[ "${stderr}" == *"re-run with --yes"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  ! grep -q 'pull --ff-only' "${GIT_CALLS_LOG}"
}

@test "update_stack CLI rejects unknown flags and bare words with 2" {
  run_cli --nope
  [ "${status}" -eq 2 ]
  [[ "${stderr}" == *"unknown option: --nope"* ]]
  [[ "${stderr}" == *"usage: update-stack"* ]]
  run_cli development
  [ "${status}" -eq 2 ]
  [[ "${stderr}" == *"takes flags only"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  # also: update_stack CLI help exits 0 with usage on stdout
  run_cli --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"usage: update-stack"* ]]
  [[ "${output}" == *"--skip-image-pull"* ]]
}

@test "update_stack CLI help is a read request, not a deploy phase" {
  run_cli --help
  [ "${status}" -eq 0 ]
  # No phase progress banner when the operator only asked for usage.
  [[ "${output}" != *"parse_args"* ]]
  [[ "${stderr}" != *"1/"* ]]
  # Help answers even when it is not the first flag.
  run_cli --dry-run --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"usage: update-stack"* ]]
  [ ! -s "${MANAGE_LOG}" ]
}
@test "update_stack CLI skips fetch without touching the remote" {
  run_cli --yes --skip-fetch
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"skipping the pull"* ]]
  ! grep -qE 'pull --ff-only|fetch --prune' "${GIT_CALLS_LOG}"
  grep -q 'manage | doctor' "${MANAGE_LOG}"
  # also: update_stack CLI skips the image pull on request
  run_cli --yes --skip-image-pull
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"skipping the image pull"* ]]
  ! grep -q 'docker pull' "${DOCKER_CALLS_LOG}"
}
@test "update_stack CLI pull failure is a warning not a failure" {
  export LAB_STACK_SKIP_PULL=1
  run_cli --yes
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"image pull did not succeed"* ]]
  grep -q 'manage | doctor' "${MANAGE_LOG}"
  # also: update_stack CLI pull failure aborts before any container verb
  STUB_GIT_PULL_RC=1
  STUB_GIT_PULL_OUT='fatal: Not possible to fast-forward, aborting.'
  run_cli --yes
  [ "${status}" -eq 1 ]
  [[ "${stderr}" == *"reconcile it by hand"* ]]
  [ ! -s "${MANAGE_LOG}" ]
  # also: update_stack CLI reports a failed manage.sh verb with a retry
  STUB_GIT_PULL_RC=0
  STUB_GIT_PULL_OUT=''
  touch "${TEST_TMP_DIR}/compose_running"
  STUB_GIT_HEAD_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  STUB_GIT_DIFF='scripts/manage.sh'
  STUB_MANAGE_RC=1
  run_cli --yes
  [ "${status}" -eq 1 ]
  [[ "${stderr}" == *"manage.sh restart failed; retry with: bazelisk run //:manage -- restart"* ]]
}
@test "update_stack CLI honours BUILD_WORKSPACE_DIRECTORY as the root" {
  local other="${TEST_TMP_DIR}/other"
  make_fake_root "${other}"
  local first="${TEST_TMP_DIR}/root/scripts/utilities/update-stack.sh"
  run --separate-stderr env REPO_ROOT= EZ_COMFY_IMAGE= LAB_GIT_BRANCH= \
    LAB_NON_INTERACTIVE= LAB_CONFIRM_TOKEN= \
    BUILD_WORKSPACE_DIRECTORY="${other}" \
    bash "${first}" --yes </dev/null
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"running: bash ${other}/scripts/manage.sh doctor"* ]]
  [[ "${stderr}" != *"running: bash ${TEST_TMP_DIR}/root/scripts/manage.sh"* ]]
}

@test "update_stack manage.sh cmd_update_stack delegates to this script" {
  local src="${REPO_ROOT}/scripts/manage.sh"
  grep -Eq '^cmd_update_stack\(\) \{' "${src}"
  grep -q 'update-stack) cmd_update_stack' "${src}"
  grep -q 'scripts/utilities/update-stack.sh' "${src}"
}

@test "update_stack CLI reports the promotion note and the summary table" {
  run_cli --yes
  [ "${status}" -eq 0 ]
  [[ "${stderr}" == *"development holds 3 commit(s) that origin/main lacks"* ]]
  [[ "${stderr}" == *"branch : development"* ]]
  [[ "${stderr}" == *"lane   : development (ghcr.io/toxicoder/ez-comfy:us-safe-studio-development)"* ]]
  [[ "${stderr}" == *"plan   : none"* ]]
  [[ "${stderr}" == *"actions:  doctor"* ]]
}

@test "update_stack resolves its libraries under bazel run" {
  # `bazel run` executes the built binary from Bazel's output tree, where the
  # sibling ../lib directory does not exist, so a script-relative source dies at
  # load. Reproduce that exact shape: the script alone in a fake output tree,
  # with BUILD_WORKSPACE_DIRECTORY naming the real checkout.
  local staged_dir="${TEST_TMP_DIR}/bazel-bin/scripts"
  mkdir -p "${staged_dir}"
  cp "${UTILITIES_DIR}/update-stack.sh" "${staged_dir}/update-stack"
  chmod +x "${staged_dir}/update-stack"
  [ ! -e "${staged_dir}/../lib" ]
  run env BUILD_WORKSPACE_DIRECTORY="${REPO_ROOT}" \
    bash "${staged_dir}/update-stack" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"usage: update-stack"* ]]
  [[ "${output}" != *"No such file or directory"* ]]
  [[ "${output}" != *"paths.sh"* ]]
}

@test "update_stack names a runnable entry point when no root resolves" {
  # The same output-tree shape, but without BUILD_WORKSPACE_DIRECTORY: fail with
  # an actionable message and the contract's exit 5, not a bare bash error.
  local staged_dir="${TEST_TMP_DIR}/orphan/scripts"
  mkdir -p "${staged_dir}"
  cp "${UTILITIES_DIR}/update-stack.sh" "${staged_dir}/update-stack"
  chmod +x "${staged_dir}/update-stack"
  run env -u BUILD_WORKSPACE_DIRECTORY bash "${staged_dir}/update-stack" --help
  [ "${status}" -eq 5 ]
  [[ "${output}" == *"cannot find scripts/lib/paths.sh"* ]]
  [[ "${output}" == *"bazelisk run //scripts:update-stack"* ]]
}
