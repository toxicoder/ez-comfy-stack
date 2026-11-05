---
title: Building with Bazel
description: Run every test, lint, build, and docs action through bazelisk, with the gate list and the per-lane commands.
tags: [bazel, testing, contributing, ci]
---

# Building with Bazel

**What's on this page**

- **The one command** - `//:everything`, in **The gate list**: its six gates, two flags, exit codes
- **Host setup** - `//:setup-host` and the vacuous-lint hole it closes
- **The gate list** - `//:test-fast`, `//:test`, `//:test-all`, `//:lint`, `//:validate`, `//:fix`
- **Per-lane commands** - one BATS suite, one utility, one pytest loop
- **Generated files** - the two derived outputs, their targets, and the per-generator loops
- **`exec_shell`** - the launcher rule every `bazelisk run` target depends on
- **Ownership guards** - the four filemap checks, the glob policy, and `//tests:bazel_docs_check`
- **CI** - the path-filtered jobs and the one script with no Bazel label

**What this enables**

- **Running** any command in this repo through one launcher, on any machine
- **Reproducing** locally the exact slices GitHub Actions runs
- **Catching** a linter that vanished from `PATH` instead of silently skipping it
- **Checking** one lane at a time without waiting for the whole gate
- **Keeping** hermetic BATS via vendored bats-core

Fourth page in Contribute, after [Contributing](contributing.md), [Conventions](../project-conventions.md),
and [How we land changes](../learn/merges.md). Next: [Testing docs](testing-docs.md), which is
what those gates check on a docs PR.

Open this page when you need a command, not a concept. Start at **The gate list**, and drop to
**Per-lane commands** when a whole gate is too slow for the one file you changed.

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
bazelisk run //:everything                          # the whole sweep; stops at the first failure
bazelisk test //:test-fast                          # hermetic default; what CI runs
bazelisk test //:test                               # test-fast + the Fumadocs render contract
bazelisk test //:test-all                           # every gate, incl. manual linters and Playwright
bazelisk test //:lint --test_tag_filters=manual     # shellcheck, shfmt, buildifier, pyright, mypy
bazelisk run //:validate                            # git-aware core + docs slices
bazelisk run //:fix                                 # rewrite shfmt/buildifier formatting
```

| Gate | What it runs | Needs |
| --- | --- | --- |
| `//:everything` | the six gates in order: `//:setup-host -- --check`, `bazelisk build //... --nobuild`, `//:test-all` (visual lane held back), the `docs-site` visual lane, `//docs:docs`, `//docs:render-check` | bazelisk, plus everything `//:test-all` needs; Docker and committed baselines for gate 4 |
| `//:test-fast` | `//scripts:manage_help_test`, `//tests:bats`, `//tests:bazel_docs_check`, `//tests:build_quality_js_check`, `//tests:js`, `//tests:owned_files_check`, `//tests:pytest` (100% first-party coverage, `pytest-xdist -n auto` when installed), `//tests:typecheck` (Pyright + mypy), `//tests:shell_inventory` | nothing beyond the checkout |
| `//:test` | `//:test-fast` + `//docs:test_docs_site_render` | docs-site npm tree |
| `//:test-all` | `//:test` + `//docker:compose_config`, `//docs-site:suite`, `//:manage`, `//docs` | host linters, `docs-site` npm tree, a Docker CLI |
| `//:lint` | `//lints:python` + `//lints:shell_lint` (ShellCheck, shfmt, buildifier, Pyright, mypy) | host lint tools; strict mode on |
| `//:validate` | Git-aware core + docs slices (`scripts/validate.sh`) | the checkout |
| `//:fix` | `fix.sh` - in-place shfmt / buildifier | host lint tools |
| `//:coverage` | Coverage report over the first-party Python tree | nothing beyond the checkout |

**Done means `bazelisk run //:validate` is green.** Type errors are defects.

`//:test-all` is the umbrella a human runs before shipping a Bazel-side change. It is not
hermetic and not fast; CI runs `//:test-fast` plus `//:lint --test_tag_filters=manual` instead.

### The one command: `//:everything`

`//:everything` is the ingress for "is this checkout healthy?". It runs six gates in order and
stops at the first failure, printing the Bazel target name that failed. It is read-only
orchestration: it shells out to `bazelisk` only and touches no `sudo`, the GPU, or `$HOME`, so
it bypasses no confirmation, restart policy, headroom preflight, or download-limit
clear-on-exit.

```bash
bazelisk run //:everything                      # probe, graph, every gate, docs
bazelisk run //:everything -- --skip-bootstrap  # same, without the toolchain probe
```

| # | Gate | What it proves |
| --- | --- | --- |
| 1 | `//:setup-host -- --check` | the host toolchain the lint and docs gates shell out to is installed |
| 2 | `bazelisk build //... --nobuild` | every package loads and every target analyzes |
| 3 | `bazelisk test //:test-all --test_tag_filters=-visual` | every test gate a plain host can run, manual linters and compose config included |
| 4 | `bazelisk test //docs-site:visual-test //docs-site:visual_tooling_test` | the docs-site screenshots match the committed baselines, rendered in the pinned container |
| 5 | `bazelisk run //docs:docs` | the generators plus the full static export build |
| 6 | `bazelisk run //docs:render-check` | the built docs-site tree satisfies the render contract |

Gate 4 is the one gate that needs a container runtime, so it is probed before it is attempted:
with no reachable Docker daemon, or with no `.png` committed under
`docs-site/tests/visual/goldens/`, the sweep prints
`SKIP docs-site visual lane (<reason>)`, names the refresh command, counts the skip in its
summary, and carries on. An environment the host cannot provide is reported as a skip; a
baseline that actually differs fails gate 4 by name. `bazelisk test //:test-all` stays the
unfiltered form that runs both visual targets whatever the host looks like, and
`//:test-fast` leaves them out entirely.

Two flags: `--skip-bootstrap` drops gate 1, which is what CI or a host you already provisioned
wants, and `-h` / `--help` prints the usage. Exit codes: `0` when every gate passed, `1` when a
gate failed (the failing target name is printed), `2` on a bad argument or when `bazelisk` is
missing. Gate 1 is the one thing this target cannot run for itself, so exit 2 means
`bazelisk run //:setup-host` is the repair.

Unlike `//:validate`, this sweep does no path filtering. Reach for `//:validate` during the day
and `//:everything` before you push a Bazel-side change or promote a graph.

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

When you touched one generator, run only that generator:

```bash
bazelisk run //docs:generate_shell     # shell CLI reference, from scripts/**
bazelisk run //docs:generate_workflow  # workflow pages, from the lab graph tree
bazelisk run //docs:generate_cinema    # Cinema Rack encyclopedia pages
bazelisk run //docs:generate_audio     # Audio Rack encyclopedia pages
```

Each writes only its own slice of the generated tree, so the loop stays short. The umbrella
`//docs:generate` stays the right call before a commit, because it is what the drift check
compares the committed tree against as a whole.

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
| `//tests:bazel_docs_check` | committed text that tells a reader to run a repo script directly while a Bazel target does that job |
| `tests/python/test_bazel_graph.py` | a first-party package that lost `BUILD.bazel`, or pytest losing xdist / schema filegroups |
| `//:repo_files` / `//:repo_meta` | the file sets the guards read |

`bazelisk test //tests:owned_files_check` and `bazelisk test //tests:bazel_docs_check` are both
in `//:test-fast`, so an unmapped file or a raw script in the docs fails the default gate rather
than waiting for a human.

### The four checks in `//tests:owned_files_check`

That target runs the static guard in `tests/bazel_deps.py`. It cannot ask Bazel (a nested query
deadlocks on the output-base lock of the outer invocation), so it parses every `BUILD.bazel` with
`ast` and re-derives four facts:

| Check | Fails when | What the person who broke it does |
| --- | --- | --- |
| ownership | a tracked file is named by no BUILD target | add the file to the target that uses it, or exempt it in the guard with the reason |
| payload | a script target's declared `data` does not match what its own source reads, in either direction | fix the `data` list; missing entries break at run time, stale entries mis-invalidate the cache |
| suites | a test target belongs to no suite | add it to the suite for its lane, so the gate actually runs it |
| explicit srcs | a `srcs` / `data` / `deps` list is not spelled out | list the files, or earn a sanctioned glob (below) |

A `BUILD.bazel` that gets cleverer than string lists, `+`, and `glob([...])` fails the parse
loudly instead of silently mapping nothing. That is the point: the guard is a guard, not a Bazel
reimplementation.

### Build targets list the files they reference

Every `srcs`, `data`, and `deps` list is explicit. `glob()` is allowed in exactly six sanctioned
clauses, each justified in a table inside `tests/bazel_deps.py`, and they are the generated-output,
committed-media, and per-file-test-generator cases:

| Sanctioned glob | Why the build cannot list it |
| --- | --- |
| `//docs:content` `generated/**` | pages `//docs:generate` writes; the set changes on every run, so it is derived, not authored |
| `//docs:content` `assets/**` | committed docs media; the payload is the tree and nothing reasons about one asset |
| `//docs-site:visual-goldens` `tests/visual/goldens/*.png` | screenshot baselines captured by the visual run, not written by hand |
| `//docs-site:visual-goldens` `tests/visual/goldens/**/*.png` | the same tree in the recursive form the capturer also writes |
| `//tests:bats_file_tests` `bats/*.bats` | the per-file generator derives one named test target plus the suite from each file |
| `//workflows:lab_graphs` `_lab/**/*.json` | graphs arrive one file at a time from `bazelisk run //:manage -- promote-workflow`; the tree is the payload |

A new glob fails the gate, and the fix is to list the files. Anything the build can name, it
should name: an explicit list is what makes a cached action invalidate when it should. If a
clause genuinely cannot be a list, add a reasoned entry to the guard's sanctioned table and say so
in the PR. The check runs both ways, so a sanctioned glob that no `BUILD.bazel` uses any more
fails too.

### What `//tests:bazel_docs_check` rejects

The doc-side twin of the filemap guard. It reads the checkout, plus the note fields ComfyUI graphs
carry, and fails when text a reader could copy - a fenced block or a backticked span - names a repo
script directly while a Bazel target does that job. The advice it prints is the copyable target,
so the repair is usually a cut and paste.

Two things are exempt by policy rather than by exception:

- the `manage.sh` verbs that need Docker, `sudo`, the GPU, or `$HOME` (`setup`,
  `setup-client`, `onboard`, `start`, `stop`, `restart`, `update-stack`, `blender-install`, and
  anything `download-*`), because they cannot run hermetically - see **Safety** below
- the one bootstrap that installs `bazelisk` itself, which no target can be the door for

Everything else is written as its target. A script with no target yet is added to the guard's
exemption table with the reason it has none; an entry without a reason is the failure the check
exists to catch. Run the whole checkout with `bazelisk test //tests:bazel_docs_check`.

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

## Related

| Need | Page |
| --- | --- |
| What each gate checks on a docs PR | [Testing docs](testing-docs.md) |
| Install the toolchain these targets shell out to | [Set up a contributor host](host-setup.mdx) |
| The same pins in a container | [Contributor Dev Container](devcontainer.md) |
| The PR checklist these gates feed | [Contributing](contributing.md) |
| A gate that fails for an unclear reason | [Troubleshooting](../troubleshooting.md) |
