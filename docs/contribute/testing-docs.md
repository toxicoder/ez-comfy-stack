---
title: Testing docs
description: bazelisk test-fast, coverage, lint, docs, typecheck — 100% Python gate, shell inventory, mike aliases, generate_shell_docs.py.
tags: [testing, coverage, mkdocs, mike, contributing]
---

# Testing docs

**What's on this page**

- **Bazel / Make targets** — `//:test-fast` / `coverage` / `lint` / `docs` / `typecheck`
- **100% Python gate** — all first-party production Python (`custom_nodes`, `docker`, `docs/*.py`, `scripts/lib`, `studio-ui`, `tools`)
- **Shell function inventory** (invoked by a test, not only named)
- **`deploy-docs.yml` + mike** — `main` → `latest`, `development` → `development`
- **`bazelisk run //docs:docs`** — `docs/generate_shell_docs.py` + `docs/generate_workflow_docs.py` then `mkdocs build --strict`

**What this enables**

- **Running** the same gates CI uses before a docs PR
- **Knowing** the 100% gate is every first-party production Python module, with GPU/bpy/network branches covered by hermetic fakes
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

Makefile shims call Bazelisk when present. Canonical commands: [Building with Bazel](building-with-bazel.md).

| Target | What it runs |
| --- | --- |
| **`bazelisk test //:test-fast`** / **`make test`** | BATS + Python + Pyright + mypy |
| **`make coverage`** | Same as `//:test-fast` via Bazel, else `tests/coverage.sh` |
| **`bazelisk test //:lint --test_tag_filters=manual`** | ShellCheck + shfmt + buildifier (Pyright + mypy live in `//:test-fast`) |
| **`make typecheck`** | Pyright (Pylance) + mypy |
| **`bazelisk run //docs:docs`** | generators then `NO_MKDOCS_2_WARNING=1 mkdocs build --strict` |
| **`bazelisk run //:fix`** | buildifier + `shfmt -w` |
| **`make doctor`** | `bazelisk run //:manage -- doctor` (host; not hermetic) |

Install once: `pip install -r tests/requirements.txt` and `pip install -r docs/requirements.txt`.

Pyright errors and mypy errors are **defects**. Do not skip the gate.

---

## 100% Python gate

`make coverage` / `tests/run_pytest.sh` fail-under **100** on every first-party production package:

- `custom_nodes`
- `docker` (UM patches, `seed_clay_inputs`, `pythonpath/sitecustomize`)
- `docs` generators and hooks
- `scripts/lib`
- `studio-ui`
- `tools` (Blender exporters; `bpy` is faked)

Vendored `custom_nodes/ez_dcc/_guide_pack.py` is included (same tests as `scripts/lib/guide_pack.py`). GPU loaders, llama.cpp, and host Blender are exercised with `sys.modules` fakes — tests stay hermetic.

`PYTHONPATH=docker:docker/pythonpath:custom_nodes:scripts/lib:studio-ui:docs:tools`.

---

## Shell function inventory

Every function under `scripts/**/*.sh` and `docker/**/*.sh` must be **invoked by a test** under `tests/` (strict; a comment that only names the function does not count). Entrypoint `main` is skipped. New library functions ship with BATS/pytest in the **same commit**. kcov remains optional and non-fatal.

---

## make docs

```bash
python3 docs/generate_shell_docs.py
python3 docs/generate_workflow_docs.py
NO_MKDOCS_2_WARNING=1 python3 -m mkdocs build --strict
touch site/.nojekyll
```

`generate_shell_docs.py` writes `docs/generated/shell/reference.md` from `# ##`, `# @command`, and `# @function` comments. `generate_workflow_docs.py` writes `docs/generated/workflows/` and `docs/reference/workflow-nodes.md` from `_lab` JSON plus `docs/workflow_nodes.py`. Do not hand-edit those files. `--strict` treats MkDocs warnings as errors.

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
