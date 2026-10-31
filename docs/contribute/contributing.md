---
title: Contributing
description: "Start here to open a pull request: branch from development, write the test first, land it green."
tags: [contributing, pr, tdd, docs]
---

# Contributing

**What's on this page**

- **Workflow (from the root file)** - branch, TDD, commit tests with code, PR into `development`
- **Promote a live graph** - the one command that copies a `_user` graph into `_lab`
- **PR checklist** - gates, safety impact, and the docs pass
- **Related** - the rest of the Contribute tab, in reading order

**What this enables**

- **Opening** a PR into `development` without copying the root file into the docs site
- **Finding** style and test gates from the published docs
- **Keeping** MiniMax graphs out of `_lab`, and Klein 9B / FLUX.2-dev off authored lab UNET pins

This is the **entry** page of Contribute. Read it, then [Conventions](../project-conventions.md)
and [How we land changes](../learn/merges.md), then the build, test, and environment pages:
[Building with Bazel](building-with-bazel.md), [Testing docs](testing-docs.md),
[Contributor Dev Container](devcontainer.md), [Set up a contributor host](host-setup.mdx). Close
with [Docs style](docs-style.md) before you touch a page.

Open this page when you are about to make your first change in this repo. It is a summary of the
root file, not a second source of truth: the numbered workflow and the checklist are what a
reviewer holds you to.

Canonical source: [CONTRIBUTING.md on GitHub](https://github.com/toxicoder/ez-comfy-stack/blob/__DOCS_GIT_REF__/CONTRIBUTING.md). Do not treat this page as a second source of truth.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

Session vars are for operator fences. Contributors still branch from **`development`** (literal name).

---

## Workflow (from the root file)

Five steps, in order, for every change:

1. Branch from latest `development`
2. Prefer TDD (`bazelisk test //:test-fast`)
3. **Commit tests with the production files they cover** (same commit)
4. Run `bazelisk test //:lint --test_tag_filters=manual` and `bazelisk run //docs:docs`
5. Open a PR into `development`

How merge commits, squash, rebase, and stacked PRs work in this repo: [How we land changes](../learn/merges.md). Land each PR **into `development`**. A GitHub Merged badge on a PR whose base is another topic branch does not update `development`.

Install Python test tools once: `pip install -r tests/requirements.txt`.

VS Code / Cursor: open the repo root and **Run Task -> validate** (same as `bazelisk run //:validate`). Also `doctor` and `docs-serve`. Shared `.vscode/` files are generic - no `.env`, interpreter path, or host variables. Format-on-save is shell and Starlark only. Optional Linux toolchain: [Contributor Dev Container](devcontainer.md).

File watchers ignore local runtime dumps (`.models`, `comfy-state`, `output` / `outputs`, `input` / `inputs`, venvs, and Bazel `external/`). Pylance reports diagnostics for open files only; workspace-wide Pyright and mypy still run in `bazelisk test //:test-fast`. Bazel CodeLens and the Targets tree are off so the extension does not background-query (`bazel.commandLine.queriesShareServer` is false). Tailwind does not scan `docs/generated` or docs-site build output. If the editor is still heavy: Command Palette -> **Developer: Open Process Explorer** / **Extension Bisect**, starting with Bazel, Tailwind, and MDX.

```mermaid
flowchart TB
  A["Branch from development"] --> B["TDD: red -> green -> refactor"]
  B --> C["Commit tests + production together"]
  C --> D["bazelisk run //:validate"]
  D --> E["PR into development"]
```

Commit titles: `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`.

## Promote a live graph

Promote a live `_user` graph (does **not** commit):

```bash
bazelisk run //:manage -- promote-workflow \
  --from "${COMFY_OUTPUT_DIR}/comfy-user/default/workflows/_user/my-hook.json" \
  --lane stills \
  --id my-hook
```

Must not contain MiniMax / Seedance / Kling / z_image_turbo, and must not pin Klein 9B / FLUX.2-dev as the UNETLoader widget. Then stamp App Mode, add or adjust `_build_*.py` / tests, and `bazelisk test //:test-fast`. Never copy `_lab` into `_user`.

---

## PR checklist

Copy this into the PR body and tick every box before you ask for review:

- [ ] Tests updated in the same commits as the code they exercise
- [ ] `bazelisk test //:test-fast` (or `bazelisk test //:coverage`) passes (100% first-party Python + Pyright + mypy)
- [ ] `bazelisk test //:lint --test_tag_filters=manual` clean
- [ ] `bazelisk run //docs:docs` (Fumadocs static export)
- [ ] Safety impact called out if Docker/resources/download-limit changed
- [ ] Docs updated for operator-facing changes
- [ ] **AI-drafted docs still received a human pass**

Do not weaken `restart: "no"`, heavy confirm on `start`, headroom, or download-limit clear-on-exit.

---

## Related

| Need | Page |
| --- | --- |
| Shell / Docker / docs chrome behind every checkbox | [Conventions](../project-conventions.md) |
| Merge commit vs squash, rebase, and stacked PRs | [How we land changes](../learn/merges.md) |
| The gate list and one-lane-at-a-time commands | [Building with Bazel](building-with-bazel.md) |
| Docs gates and the Pages aliases | [Testing docs](testing-docs.md) |
| Vulnerability reporting | [Security](security.md) |
| Agent workflow | [AGENTS.md on GitHub](https://github.com/toxicoder/ez-comfy-stack/blob/__DOCS_GIT_REF__/AGENTS.md) |
