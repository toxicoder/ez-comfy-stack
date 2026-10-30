#!/usr/bin/env bash
#
# ## post-create
#
# Install Python test/docs deps into ~/.venv and prewarm bazelisk/grok so the
# first IDE query does not race the Bazel download. The docs-site install
# (bazelisk run //docs-site:install) is opt-in via DEVCONTAINER_INSTALL_DOCS_SITE=1
# (use ./docs/setup-docs.sh otherwise).
#
# Usage:
#   bash .devcontainer/post-create.sh
#   bash .devcontainer/post-create.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  echo "Usage: post-create.sh"
  echo "Creates ~/.venv, installs tests/requirements.txt, prewarms bazelisk and grok."
  echo "Set DEVCONTAINER_INSTALL_DOCS_SITE=1 to also run docs-site npm ci."
  exit 0
fi

cd "${REPO_ROOT}"
python3 -m venv "${HOME}/.venv"
# shellcheck disable=SC1091
source "${HOME}/.venv/bin/activate"
# Bootstrap-only pip installs: they put pytest, pyright and mypy on PATH, which is
# what the Bazel lint/typecheck targets shell out for, so they cannot themselves
# run through bazelisk. They stay raw for that reason alone.
python -m pip install -r tests/requirements.txt
if [[ -f docs/requirements.txt ]]; then
  python -m pip install -r docs/requirements.txt || true
fi
if [[ ${DEVCONTAINER_INSTALL_DOCS_SITE:-0} == "1" ]] &&
  command -v npm >/dev/null 2>&1 &&
  [[ -f docs-site/package.json ]]; then
  # `run`, not `build`: //docs-site:install is an sh_binary and build would only
  # stage it. The runner cd's into the real docs-site/ tree for npm ci.
  bazelisk run //docs-site:install
fi
bazelisk version
grok --version
echo "post-create: ready - bazelisk run //:validate"
