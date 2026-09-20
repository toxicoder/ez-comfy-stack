---
title: Building with Bazel
description: Bazel-first test, lint, and docs workflow for ez-comfy-stack — targets, Makefile shims, and CI.
tags: [bazel, testing, contributing, ci]
---

# Building with Bazel

**What's on this page**

- Why Bazelisk is the primary test/lint/docs launcher
- Daily commands and Makefile shims
- CI path filters
- What this repo still refuses (K3s, dashboard, NCCL)

**What this enables**

- Reproducible hermetic BATS via vendored bats-core
- One command (`bazelisk run //:validate`) before a PR
- The same slices GitHub Actions runs

Runtime stays Docker Compose (`restart: "no"`). Bazel does **not** add K3s, a lab dashboard, or NCCL. Graduate to [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab) for those.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

## Prerequisites

- Bazelisk (recommended) or Bazel 8.4.1 (`.bazelversion`)
- Host tools for lint: shellcheck, shfmt, buildifier, `pip install -r tests/requirements.txt`

```bash
# macOS
brew install bazelisk buildifier shfmt shellcheck
```

## Daily commands

```bash
bazelisk run //:validate
bazelisk run //:validate -- --all
bazelisk test //:test-fast
bazelisk test //:lint --test_tag_filters=manual
bazelisk run //:fix
bazelisk run //:manage -- doctor
bazelisk run //docs:docs
bazelisk run //docs:serve
bazelisk run //scripts:run-utility -- download-limit status
```

`make test`, `make lint`, `make coverage`, and `make docs` call Bazelisk when it is on `PATH`.

## Target map

| Target | What it runs |
| --- | --- |
| `//:test-fast` | Split BATS + pytest 100% (all first-party Python) + Pyright + mypy + shell inventory |
| `//:test` | test-fast + Fumadocs render contract (`//docs:test_docs_site_render`) |
| `//:lint` | ShellCheck, shfmt, buildifier, Pyright, mypy (manual / host tools) |
| `//:validate` | Git-aware core + docs slices |
| `//docs:docs` | generators + Fumadocs static export (`docs-site/out/`) |

Queries:

```bash
bazelisk query 'kind(".*_test", //...)'
bazelisk query 'deps(//tests:bats_manage_test)'
```

## CI

Path-filtered jobs in `.github/workflows/ci.yml`:

| Job | When | What |
| --- | --- | --- |
| **bazel-core** | scripts/tests/docker/docs generators/typecheck pins or CI graph | `//:test-fast` then `//:lint` (shellcheck/shfmt/buildifier) |
| **docs-and-render** | docs/**, docs-site/**, or CI graph | Node 22 + `//docs:test_docs_site_render` + `//docs-site:unit|typecheck|nav_test|codemod_test` then `bazelisk shutdown` and `//docs:docs`. Export is `next build --webpack` with one static-generation worker and `NODE_OPTIONS=--max-old-space-size=4096` (same as deploy-docs). A 6 GB heap plus Turbopack OOMs the 7 GB runner |
| **validate-gate** | always | `scripts/ci_check_only.sh` |

Topic-branch CI runs on **pull_request** only (push is `development`/`main`). Disk cache keys include `github.job` plus `MODULE.bazel.lock` + `.bazelversion`.

## Safety

No safety impact on Compose: `restart: "no"`, type **yes** on `start`, headroom preflight, download-limit clear-on-exit stay in `docker/docker-compose.yml` and `manage.sh`.
