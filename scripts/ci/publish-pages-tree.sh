#!/usr/bin/env bash
#
# ## CI GitHub Pages publisher
#
# Push a pre-assembled Fumadocs Pages tree onto origin/gh-pages from a
# separate git worktree. Next.js rewrites tracked docs-site/next-env.d.ts
# during `next build`; checking out gh-pages in that dirty source tree
# aborts the deploy job.
#
# Safety:
# - Pushes only gh-pages (never development or main).
# - Does not switch the source worktree off its branch.
# - Does not change Docker, Compose, restart policy, or download-limit.
#
# Usage:
#   ./scripts/ci/publish-pages-tree.sh _site

set -euo pipefail

PAGES_WORKTREE=""
# GitHub rejects blobs at 100 MiB. The Fumadocs /api/search export was 379 MiB.
PAGES_MAX_FILE_BYTES="${PAGES_MAX_FILE_BYTES:-104857600}"

#######################################
# Fail unless the assembled tree has root files and at least one alias.
# Globals:
#   None
# Arguments:
#   $1 - assembled Pages directory
# Outputs:
#   Error on stderr
# Returns:
#   0 when valid, 1 otherwise
#######################################
assert_assembled_pages_tree() {
  local root="${1}"
  if [[ ! -d ${root} ]]; then
    echo "publish-pages-tree: missing assembled dir ${root}" >&2
    return 1
  fi
  if [[ ! -f "${root}/index.html" ]]; then
    echo "publish-pages-tree: assembled tree needs index.html" >&2
    return 1
  fi
  if [[ ! -f "${root}/.nojekyll" ]]; then
    echo "publish-pages-tree: assembled tree needs .nojekyll" >&2
    return 1
  fi
  if [[ ! -d "${root}/latest" && ! -d "${root}/development" ]]; then
    echo "publish-pages-tree: assembled tree needs latest/ or development/" >&2
    return 1
  fi
}

#######################################
# Fail if any file is at or over GitHub's blob size limit.
# Globals:
#   PAGES_MAX_FILE_BYTES (read)
# Arguments:
#   $1 - assembled Pages directory
# Outputs:
#   Oversize paths on stderr
# Returns:
#   0 when every file is under the limit, 1 otherwise
#######################################
assert_pages_tree_file_sizes() {
  local root="${1}"
  local max_bytes="${PAGES_MAX_FILE_BYTES}"
  local too_big=0
  local f sz rel
  while IFS= read -r -d '' f; do
    sz="$(wc -c <"${f}" | tr -d '[:space:]')"
    if [[ ${sz} -ge ${max_bytes} ]]; then
      rel="${f#"${root}"/}"
      echo "publish-pages-tree: ${rel} is ${sz} bytes (GitHub limit ${max_bytes})" >&2
      too_big=1
    fi
  done < <(find "${root}" -type f -print0)
  if [[ ${too_big} -eq 1 ]]; then
    return 1
  fi
}

#######################################
# Set the github-actions bot identity on the current repository.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
configure_pages_git_identity() {
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
}

#######################################
# Remove the Pages worktree if add_pages_worktree created one.
# Globals:
#   PAGES_WORKTREE (read/write)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0
#######################################
cleanup_pages_worktree() {
  local wt="${PAGES_WORKTREE:-}"
  PAGES_WORKTREE=""
  if [[ -z ${wt} ]]; then
    return 0
  fi
  git worktree remove --force "${wt}" >/dev/null 2>&1 || rm -rf "${wt}" || true
}

#######################################
# Check origin/gh-pages out into a new worktree (orphan if missing).
# Globals:
#   PAGES_WORKTREE (write), RUNNER_TEMP, TMPDIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 on success
#######################################
add_pages_worktree() {
  local tmpdir tmp
  tmpdir="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
  mkdir -p "${tmpdir}"
  tmp="$(mktemp -d "${tmpdir}/ez-comfy-pages.XXXXXX")"
  rmdir "${tmp}"
  PAGES_WORKTREE="${tmp}"

  git fetch origin gh-pages || true
  if git show-ref --verify --quiet refs/remotes/origin/gh-pages; then
    git worktree add -B gh-pages "${PAGES_WORKTREE}" origin/gh-pages
  else
    git worktree add --orphan -b gh-pages "${PAGES_WORKTREE}"
  fi
}

#######################################
# Replace origin/gh-pages with the assembled tree via a worktree.
# Globals:
#   PAGES_WORKTREE, GITHUB_REF_NAME, GITHUB_SHA, RUNNER_TEMP, TMPDIR
# Arguments:
#   $1 - assembled Pages directory
# Outputs:
#   Git fetch/commit/push chatter
# Returns:
#   0 on success, non-zero on validation or git errors
#######################################
publish_pages_tree() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: publish-pages-tree.sh <assembled-dir>" >&2
    return 2
  fi
  local assembled repo_root
  assembled="$(cd "${1}" && pwd)"
  assert_assembled_pages_tree "${assembled}"
  assert_pages_tree_file_sizes "${assembled}"
  repo_root="$(git rev-parse --show-toplevel)"
  cd "${repo_root}"

  PAGES_WORKTREE=""
  trap cleanup_pages_worktree EXIT

  configure_pages_git_identity
  add_pages_worktree

  git -C "${PAGES_WORKTREE}" rm -rf --quiet . 2>/dev/null || true
  cp -a "${assembled}/." "${PAGES_WORKTREE}/"
  cat >"${PAGES_WORKTREE}/.gitignore" <<'GITIGNORE'
/*
!/latest
!/development
!/index.html
!/.nojekyll
GITIGNORE

  git -C "${PAGES_WORKTREE}" add -A
  git -C "${PAGES_WORKTREE}" commit \
    --allow-empty \
    -m "docs: publish ${GITHUB_REF_NAME:-unknown} from ${GITHUB_SHA:-unknown}"
  git -C "${PAGES_WORKTREE}" push origin HEAD:gh-pages
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  publish_pages_tree "$@"
fi
