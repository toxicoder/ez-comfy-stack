#!/usr/bin/env bats
#
# Hermetic tests for scripts/ci/publish-pages-tree.sh.
# Reproduces the Deploy Documentation failure: next build dirties
# docs-site/next-env.d.ts and an in-place gh-pages checkout aborts.

load 'test_helper'

setup() {
  setup_repo_env
  export GIT_CONFIG_GLOBAL=/dev/null
  export GIT_CONFIG_SYSTEM=/dev/null
  export RUNNER_TEMP="${TEST_TMP_DIR}/runner-temp"
  mkdir -p "${RUNNER_TEMP}"
  SCRIPT="${REPO_ROOT}/scripts/ci/publish-pages-tree.sh"
}

teardown() {
  teardown_repo_env
}

#######################################
# Point a repo at a local identity so commits do not use the host gitconfig.
# Globals:
#   None
# Arguments:
#   $1 - repository path
# Outputs:
#   None
# Returns:
#   0
#######################################
init_test_git_identity() {
  local repo="${1}"
  git -C "${repo}" config user.name "ez-comfy-test"
  git -C "${repo}" config user.email "test@example.com"
  git -C "${repo}" config commit.gpgsign false
}

#######################################
# Create a bare origin whose only branch is gh-pages with a latest/ tree.
# Globals:
#   TEST_TMP_DIR, ORIGIN
# Arguments:
#   None
# Outputs:
#   Sets ORIGIN
# Returns:
#   0
#######################################
setup_origin_with_latest() {
  ORIGIN="${TEST_TMP_DIR}/origin.git"
  git init --bare -b gh-pages "${ORIGIN}"
  local seed="${TEST_TMP_DIR}/seed"
  git clone "${ORIGIN}" "${seed}"
  init_test_git_identity "${seed}"
  mkdir -p "${seed}/latest"
  echo "kept-latest" >"${seed}/latest/index.html"
  git -C "${seed}" add latest
  git -C "${seed}" commit -m "seed latest"
  git -C "${seed}" push origin HEAD:gh-pages
}

#######################################
# Clone origin, switch to orphan development, dirty next-env.d.ts.
# Globals:
#   ORIGIN, TEST_TMP_DIR, CLONE
# Arguments:
#   None
# Outputs:
#   Sets CLONE
# Returns:
#   0
#######################################
setup_dirty_source_clone() {
  CLONE="${TEST_TMP_DIR}/clone"
  git clone "${ORIGIN}" "${CLONE}"
  init_test_git_identity "${CLONE}"
  git -C "${CLONE}" checkout --orphan development
  git -C "${CLONE}" rm -rf --quiet . 2>/dev/null || true
  mkdir -p "${CLONE}/docs-site"
  printf '%s\n' '/// <reference types="next" />' >"${CLONE}/docs-site/next-env.d.ts"
  git -C "${CLONE}" add docs-site/next-env.d.ts
  git -C "${CLONE}" commit -m "source"
  echo "DIRTY-FROM-NEXT-BUILD" >>"${CLONE}/docs-site/next-env.d.ts"
}

#######################################
# Write an assembled Pages tree with both aliases plus root files.
# Globals:
#   TEST_TMP_DIR, ASSEMBLED
# Arguments:
#   None
# Outputs:
#   Sets ASSEMBLED
# Returns:
#   0
#######################################
write_assembled_pages_tree() {
  ASSEMBLED="${TEST_TMP_DIR}/_site"
  mkdir -p "${ASSEMBLED}/development" "${ASSEMBLED}/latest"
  echo "new-development" >"${ASSEMBLED}/development/index.html"
  echo "kept-latest" >"${ASSEMBLED}/latest/index.html"
  echo "redirect" >"${ASSEMBLED}/index.html"
  touch "${ASSEMBLED}/.nojekyll"
}

@test "publish-pages-tree.sh names inventory functions" {
  [ -f "${SCRIPT}" ]
  for fn in assert_assembled_pages_tree assert_pages_tree_file_sizes configure_pages_git_identity add_pages_worktree cleanup_pages_worktree publish_pages_tree; do
    grep -qE "^${fn}\\(\\)" "${SCRIPT}"
  done
}

@test "assert_pages_tree_file_sizes rejects a blob at the GitHub limit" {
  write_assembled_pages_tree
  mkdir -p "${ASSEMBLED}/development/api"
  head -c 200 /dev/zero >"${ASSEMBLED}/development/api/search"
  export PAGES_MAX_FILE_BYTES=100
  run bash "${SCRIPT}" "${ASSEMBLED}"
  [ "$status" -ne 0 ]
  [[ ${output} == *"api/search"* ]]
  [[ ${output} == *"GitHub limit"* ]]
}

@test "assert_assembled_pages_tree rejects a tree without .nojekyll" {
  write_assembled_pages_tree
  rm -f "${ASSEMBLED}/.nojekyll"
  run bash "${SCRIPT}" "${ASSEMBLED}"
  [ "$status" -ne 0 ]
  [[ ${output} == *".nojekyll"* ]]
}

@test "publish_pages_tree keeps a dirty next-env.d.ts and pushes both aliases" {
  setup_origin_with_latest
  setup_dirty_source_clone
  write_assembled_pages_tree
  export GITHUB_REF_NAME=development
  export GITHUB_SHA
  GITHUB_SHA="$(git -C "${CLONE}" rev-parse HEAD)"

  run bash -c "cd \"${CLONE}\" && bash \"${SCRIPT}\" \"${ASSEMBLED}\""
  echo "$output"
  [ "$status" -eq 0 ]

  [ "$(git -C "${CLONE}" branch --show-current)" = "development" ]
  grep -qF "DIRTY-FROM-NEXT-BUILD" "${CLONE}/docs-site/next-env.d.ts"

  [ "$(git --git-dir="${ORIGIN}" show gh-pages:development/index.html)" = "new-development" ]
  [ "$(git --git-dir="${ORIGIN}" show gh-pages:latest/index.html)" = "kept-latest" ]
  git --git-dir="${ORIGIN}" show gh-pages:.nojekyll >/dev/null
  git --git-dir="${ORIGIN}" show gh-pages:index.html >/dev/null
}

@test "publish_pages_tree creates gh-pages when origin has no such branch" {
  ORIGIN="${TEST_TMP_DIR}/origin.git"
  git init --bare -b development "${ORIGIN}"
  CLONE="${TEST_TMP_DIR}/clone"
  git clone "${ORIGIN}" "${CLONE}"
  init_test_git_identity "${CLONE}"
  echo "seed" >"${CLONE}/README"
  git -C "${CLONE}" add README
  git -C "${CLONE}" commit -m "seed development"
  git -C "${CLONE}" push origin HEAD:development
  mkdir -p "${CLONE}/docs-site"
  echo "DIRTY-FROM-NEXT-BUILD" >"${CLONE}/docs-site/next-env.d.ts"

  write_assembled_pages_tree
  export GITHUB_REF_NAME=development
  export GITHUB_SHA
  GITHUB_SHA="$(git -C "${CLONE}" rev-parse HEAD)"

  run bash -c "cd \"${CLONE}\" && bash \"${SCRIPT}\" \"${ASSEMBLED}\""
  echo "$output"
  [ "$status" -eq 0 ]
  [ "$(git --git-dir="${ORIGIN}" show gh-pages:development/index.html)" = "new-development" ]
}
