---
title: Testing docs
description: make test, coverage, lint, docs, typecheck — 100% Python gate, shell inventory, mike aliases, generate_shell_docs.py.
tags: [testing, coverage, mkdocs, mike, contributing]
---

# Testing docs

**What's on this page**

- **Make targets** — `test` / `coverage` / `lint` / `docs` / `typecheck`
- **100% Python gate** — UM patches + `ez_ltx_spatial` (not the shell generator)
- **Shell function inventory**
- **`deploy-docs.yml` + mike** — `main` → `latest`, `development` → `development`
- **`make docs`** — `docs/generate_shell_docs.py` then `mkdocs build --strict`

**What this enables**

- **Running** the same gates CI uses before a docs PR
- **Knowing** the coverage number is **not** “every Python file in the repo”
- **Publishing** versioned docs without upgrading MkDocs 2.x

Style: [Docs style](docs-style.md). Root workflow: [Contributing](contributing.md).

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

Hermetic tests do not need a Spark. Docs JS session vars still use those names in fences.

---

## Make targets

| Target | What it runs |
| --- | --- |
| **`make test`** | `tests/run_all.sh` — BATS + Python + Pyright + mypy |
| **`make coverage`** | `tests/coverage.sh` — 100% pytest-cov gate + typecheck + shell inventory + full BATS |
| **`make lint`** | ShellCheck + `shfmt -d` + `tests/typecheck.sh` (Pyright + mypy) |
| **`make typecheck`** | Pyright (Pylance) + mypy |
| **`make docs`** | `python3 docs/generate_shell_docs.py` then `NO_MKDOCS_2_WARNING=1 python3 -m mkdocs build --strict` |
| **`make fmt`** | `shfmt -w` |
| **`make doctor`** | `./scripts/manage.sh doctor` (host; not hermetic) |

Install once: `pip install -r tests/requirements.txt` and `pip install -r docs/requirements.txt`.

Pyright errors and mypy errors are **defects**. Do not skip the gate.

---

## 100% Python gate

`make coverage` / `make python` fail-under **100** on:

- `patch_get_free_memory`
- `patch_unified_memory_copy`
- `patch_magcache_compat`
- `patch_vhs_widget_inputs`
- `seed_clay_inputs`
- **`ez_ltx_spatial`**

That is **UM / MagCache / VHS widgetInputs / clay seed / LTX spatial** — **not** `docs/generate_shell_docs.py` and not the rest of `custom_nodes/`. The shell generator is exercised by pytest (`tests/python/test_generate_shell_docs.py`) without a 100% line gate.

`PYTHONPATH=docker:custom_nodes`.

---

## Shell function inventory

Every function under `scripts/**/*.sh` and `docker/**/*.sh` must be **named under `tests/`** (strict; production-only refs do not count). Entrypoint `main` is skipped. New library functions ship with BATS/pytest in the **same commit**.

---

## make docs

```bash
python3 docs/generate_shell_docs.py
NO_MKDOCS_2_WARNING=1 python3 -m mkdocs build --strict
touch site/.nojekyll
```

`generate_shell_docs.py` writes `docs/generated/shell/reference.md` from `# ##`, `# @command`, and `# @function` comments. Do not hand-edit that file. `--strict` treats MkDocs warnings as errors.

Pins: MkDocs **1.x** + Material (`docs/requirements.txt`). Do **not** upgrade to MkDocs 2.x. Do **not** enable `header.autohide`. [Docs style](docs-style.md).

---

## deploy-docs.yml + mike

`.github/workflows/deploy-docs.yml` runs on push to **`main`** / **`development`** (docs paths) or `workflow_dispatch`.

| Git branch | mike alias |
| --- | --- |
| **`main`** | **`latest`** (default site) |
| **`development`** | **`development`** |

PR validation is `make docs` in CI only (no mike push). Deploy sets `EZ_DOCS_PUBLISHED_AT` for the last-published chip. `hooks.py` stamps `__DOCS_GIT_REF__` and GitHub blob/tree URLs to the long-lived ref.

Public URLs: [latest](https://toxicoder.github.io/ez-comfy-stack/latest/) · [development](https://toxicoder.github.io/ez-comfy-stack/development/).

!!! warning "AI-drafted docs still need a human pass"

    Green `make docs` does not prove the page matches the code. Read `nodes.py` / compose / occupancy before merge.
