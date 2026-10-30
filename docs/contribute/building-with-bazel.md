---
title: Building with Bazel
description: Bazelisk-first test, lint, build, and docs workflow for ez-comfy-stack - the gate list, the exec_shell launcher, host setup, and CI.
tags: [bazel, testing, contributing, ci]
---

# Building with Bazel

**What's on this page**

- **One ingress** - `bazelisk` runs every test, lint, build, and docs action here
- **The gate list** - `//:test-fast`, `//:test`, `//:test-all`, `//:lint`, `//:validate`, `//:fix`
- **Per-lane commands** - one BATS suite, one utility, one pytest loop
- **`exec_shell`** - the launcher rule every `bazelisk run` target depends on
- **Host setup** - `//:setup-host` and the vacuous-lint hole it closes
- **Ownership guards** - `//:owned_files_check` and `//tests:owned_files_check`

**What this enables**

- **Running** any command in this repo through one launcher, on any machine
- **Reproducing** locally the exact slices GitHub Actions runs
- **Catching** a linter that vanished from `PATH` instead of silently skipping it
- **Checking** one lane at a time without waiting for the whole gate
- **Keeping** hermetic BATS via vendored bats-core

Runtime stays Docker Compose (`restart: "no"`). Bazel does **not** add K3s, a lab dashboard, or NCCL. Graduate to [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab) for those.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

---

## Host setup

A bare host has no `bazelisk`, so it cannot run a single target. `scripts/setup-host.sh` is
deliberately the one script in this repo meant to run straight from a shell - it is the
bootstrap that makes the ingress exist. Full walkthrough:
[Set up a contributor host](host-setup.mdx).

```bash
bash scripts/setup-host.sh --check    # from a bare checkout: report what is missing
bash scripts/setup-host.sh            # install it, then re-probe
bazelisk run //:setup-host -- --check # once bazelisk exists, the same probe via Bazel
```

What it installs: `bazelisk`, `shellcheck`, `shfmt`, `buildifier`, `pyright`, `mypy`, `node`,
`git`, `python3`. Every version comes from `.devcontainer/tool-versions.env`, the same pin file
the dev container and CI read.

`make test`, `make lint`, `make coverage`, and `make docs` are shims that call Bazelisk when it
is on `PATH`. VS Code / Cursor **Run Task** labels in `.vscode/tasks.json` wrap the same
`bazelisk` commands (`validate`, `test-fast`, `pytest`, `typecheck`, `lint`, `fix`, `doctor`,
`docs`, `docs-serve`).

### Why the lint lane needs it

`scripts/lib/check_tool.sh` is resilient by design: a tool that is off `PATH` prints
`<tool> missing - skipping (resilient; ...)` and **exits 0**. That is right for an optional
lint on a laptop and wrong for a gate. On a host that never installed shellcheck, shfmt,
buildifier, pyright, or mypy, `bazelisk test //:lint` went **green having checked nothing**.

Every gate in `lints/BUILD.bazel` now sets `env = {"REQUIRE_LINT_TOOLS": "1"}`, which makes
`check_tool` fatal instead:

```text
shellcheck missing - required in CI/strict mode (apt install shellcheck or brew install shellcheck)
```

So a skipped linter is a red build, and the repair is a documented command rather than a
hunt through CI YAML:

```bash
bazelisk run //:setup-host            # install what the gate wants
bash scripts/setup-host.sh            # same thing from a bare host
```

On macOS the Homebrew equivalents are `brew install bazelisk buildifier shfmt shellcheck`;
`setup-host.sh` drives that path for you and pins the versions. Or use the
[Contributor Dev Container](devcontainer.md) (Ubuntu 24.04, Python 3.12, Node 22, Grok Build;
`linux/amd64` + `linux/arm64`), which bakes the whole toolchain.

---

## The gate list

```bash
bazelisk test //:test-fast                          # hermetic default; what CI runs
bazelisk test //:test                               # test-fast + the Fumadocs render contract
bazelisk test //:test-all                           # every gate, incl. manual linters and Playwright
bazelisk test //:lint --test_tag_filters=manual     # shellcheck, shfmt, buildifier, pyright, mypy
bazelisk run //:validate                            # git-aware core + docs slices
bazelisk run //:fix                                 # rewrite shfmt/buildifier formatting
```

| Gate | What it runs | Needs |
| --- | --- | --- |
| `//:test-fast` | `//scripts:manage_help_test`, `//tests:bats`, `//tests:build_quality_js_check`, `//tests:js`, `//tests:owned_files_check`, `//tests:pytest` (100% first-party coverage, `pytest-xdist -n auto` when installed), `//tests:typecheck` (Pyright + mypy), `//tests:shell_inventory` | nothing beyond the checkout |
| `//:test` | `//:test-fast` + `//docs:test_docs_site_render` | docs-site npm tree |
| `//:test-all` | `//:test` + `//docker:compose_config`, `//docs-site:suite`, `//:manage`, `//docs` | host linters, `docs-site` npm tree, a Docker CLI |
| `//:lint` | `//lints:python` + `//lints:shell_lint` (ShellCheck, shfmt, buildifier, Pyright, mypy) | host lint tools; strict mode on |
| `//:validate` | Git-aware core + docs slices (`scripts/validate.sh`) | the checkout |
| `//:fix` | `fix.sh` - in-place shfmt / buildifier | host lint tools |
| `//:coverage` | Coverage report over the first-party Python tree | nothing beyond the checkout |

**Done means `bazelisk run //:validate` is green.** Type errors are defects.

`//:test-all` is the umbrella a human runs before shipping a Bazel-side change. It is not
hermetic and not fast; CI runs `//:test-fast` plus `//:lint --test_tag_filters=manual` instead.

### Per-lane commands

Run one slice instead of a whole gate:

```bash
bazelisk test //tests:bats_manage_test                      # one BATS suite
bazelisk test //tests:bats_workflow_test                    # workflow graph contract
bazelisk test //tests:shell_inventory                       # shell function inventory
bazelisk test //tests:pytest --test_output=errors           # the inner pytest loop
bazelisk test //docs:test_docs_site_render                  # Fumadocs render contract
bazelisk test //docs-site:unit //docs-site:typecheck        # the docs app
bazelisk run //scripts:run-utility -- download-limit status # one operator utility
bazelisk run //scripts:update-stack -- --dry-run            # stack update, no writes
bazelisk run //:manage -- doctor                            # operator CLI
```

### Generated files

Two committed files are derived output, so each has a target that writes it and a
gate that catches drift. Edit the source, regenerate, and commit the diff; the
check target is the thing that fails in CI when someone forgets.

| Generated file | Source of truth | Regenerate | Drift gate |
| --- | --- | --- | --- |
| `docs/generated/**` (791 pages) | `scripts/**`, `workflows/**`, and the `docs/generate_*.py` generators | `bazelisk run //docs:generate` | `bazelisk test //tests:pytest` compares the committed tree against the generators |
| `custom_nodes/ez_quality/js/ez_quality_presets.js` | `custom_nodes/ez_quality/presets.py` | `bazelisk run //tests:build_quality_js` | `bazelisk test //tests:build_quality_js_check`, in `//:test-fast` |

`//docs:generate` runs the four generators with no npm install and no webpack
export, which is the loop you want after editing a shell function or a workflow
graph. `bazelisk run //docs:docs` is the full export and calls the same
generators first. Hand-editing either generated file is a defect: the check
target fails and tells you the command to run.

Queries:

```bash
bazelisk query 'kind(".*_test", //...)'
bazelisk query 'deps(//tests:bats_manage_test)'
bazelisk build //:first_party_srcs --nobuild
```

`tests/python/test_bazel_graph.py` fails if a first-party package loses `BUILD.bazel` or pytest
drops xdist / schema filegroups.

---

## `exec_shell`: the launcher behind `bazelisk run`

`tools/exec_shell.bzl` defines a rule that runs a shell source out of runfiles without needing
mode `100755` on it. It backs `//:setup-host`, `//scripts:manage`, `//scripts:update-stack`, and
`//scripts:run-utility`.

Two separate problems make it necessary:

- **The mode bit.** `rules_shell` symlinks `sh_test` / `sh_binary` srcs with
  `is_executable=True`, and Bazel rejects that symlink when the source file is not executable.
  GitHub's contents API stores blobs as `100644`, so a checkout of this repo would not build.
  The launcher is a generated executable that `exec`s the runfiles copy with `bash`, so the
  source mode bit stops mattering.
- **The sibling files.** `sh_binary` puts the declared `data` in `<target>.runfiles/` while the
  executable copy sits alone in `bazel-bin/`. Any script that sources a sibling by
  `dirname "$0"` then fails - `scripts/manage.sh` sourcing `scripts/lib/paths.sh` is exactly the
  case this exists for. The rule puts the real script **and** its `data` in runfiles beside each
  other, so the source resolves.

The launcher searches `RUNFILES_DIR`, then `TEST_SRCDIR`, then `<argv0>.runfiles`, and prints
`exec_shell: cannot locate <path>` and exits 1 if none of them hold the script. If you hit that,
see [Troubleshooting](../troubleshooting.md).

---

## Ownership guards

Every first-party source file must be reachable from a Bazel target, or it silently stops being
built, tested, and linted.

| Guard | What it rejects |
| --- | --- |
| `//:owned_files_check` (alias of `//tests:owned_files_check`) | a source file in the repo that no target's `srcs` / `data` / `filegroup` claims |
| `tests/python/test_bazel_graph.py` | a first-party package that lost `BUILD.bazel`, or pytest losing xdist / schema filegroups |
| `//:repo_files` / `//:repo_meta` | the file sets the guards read |

`bazelisk test //tests:owned_files_check` is in `//:test-fast`, so an unmapped file fails the
default gate rather than waiting for a human.

---

## CI

Path-filtered jobs in `.github/workflows/ci.yml`:

| Job | When | What |
| --- | --- | --- |
| **bazel-core** | scripts/tests/docker/docs generators/typecheck pins or CI graph | `//:test-fast` then `//:lint --test_tag_filters=manual` (shellcheck/shfmt/buildifier) |
| **docs-and-render** | docs/**, docs-site/**, or CI graph | Node 22 + `//docs:test_docs_site_render` + `//docs-site:unit|typecheck|nav_test|codemod_test`, then `bazelisk shutdown` and the static export outside Bazel. Export is `next build --webpack` in-process, one static-generation worker, `NODE_OPTIONS=--max-old-space-size=5120` (same as deploy-docs). MDX is compiled on demand (`dynamic: true` in `docs-site/source.config.ts`) so webpack does not ingest ~850 pages. Turbopack or a 6 GB heap plus Bazel SIGKILL the 7 GB runner. `docs-site/.next/cache` is cached between runs |
| **validate-gate** | always | `bash scripts/ci_check_only.sh` (CI-only script; no Bazel target - see the note below) |

Topic-branch CI runs on **pull_request** only (push is `development`/`main`). Disk cache keys
include `github.job` plus `MODULE.bazel.lock` + `.bazelversion`.

`scripts/ci_check_only.sh` is the one CI step with no Bazel label: it decides which jobs should
have run from the changed paths, so it has to execute before Bazel is consulted. Locally the
equivalent is `bazelisk run //:validate`.

---

## Safety

No safety impact on Compose: `restart: "no"`, type **yes** on `start`, headroom preflight,
download-limit clear-on-exit stay in `docker/docker-compose.yml` and `manage.sh`.

`//:manage` and `//scripts:run-utility` are thin wrappers: they run the same script with the same
arguments and change no policy. The host-mutating verbs (`setup`, `start`, `stop`, `download-*`)
need Docker, `sudo`, the GPU, or `$HOME`, so they cannot run hermetically -
`./scripts/manage.sh <verb>` stays available as the escape hatch for those, and prints the
identical behavior.

Related: [Set up a contributor host](host-setup.mdx) - [Contributor Dev Container](devcontainer.md) -
[Contributing](contributing.md) - [Docs style](docs-style.md) - [Troubleshooting](../troubleshooting.md)
