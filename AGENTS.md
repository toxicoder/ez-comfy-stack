# ez-comfy-stack

Single-Spark ComfyUI Compose demo. US-safe local studio. Not a cluster product.
Do not add K3s, a dashboard, multi-node NCCL, or extra model families.

Style: [docs/project-conventions.md](docs/project-conventions.md).
Shell: [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
(deviations only as documented there).

## Punctuation

Keep committed text files free of confusable Unicode punctuation (the
editor "could be confused with an ASCII character" warnings): en/em/minus
dashes (U+2010-U+2015, U+2212) become `-`, curly quotes U+2018-U+201D become
straight quotes, ellipsis U+2026 becomes `...`, arrows U+2190-U+2194 become
`<-` / `->` / `<->`, U+00D7 becomes `x`, U+00F7 becomes `div`, U+00B1 becomes
`+/-`, U+2248 becomes `~`, U+2260/U+2264/U+2265 become `!=`/`<=`/`>=`,
superscripts U+00B2/U+00B3 become `^2`/`^3`, middle dot U+00B7 and bullet
U+2022 become `-`, and narrow/no-break spaces become plain spaces. Content letters (accents in dub sample strings, CJK
punctuation in fixtures) and functional glyphs (progress-bar cells,
box-drawing banners, U+2713 check marks) are exempt. Enforced by
`tests/python/test_unicode_confusables.py` in validate.

## Commands

Prefer Bazelisk. Make targets are shims.

- validate: `bazelisk run //:validate`
- test (fast): `bazelisk test //:test-fast`
- one bats suite: `bazelisk test //tests:bats_<suite>_test`
- lint: `bazelisk test //:lint --test_tag_filters=manual`
- fmt: `bazelisk run //:fix`  (`make fmt` / `make lint` are shims)
- types: `make typecheck` (Pyright + mypy; `disallow_untyped_defs`)
- docs serve: `bazelisk run //docs:serve` or `./docs/manage-docs.sh serve`
- docs export: `bazelisk run //docs:docs`
- doctor: `./scripts/manage.sh doctor` or `make doctor`
- stack: `./scripts/manage.sh setup|download-models|start|stop`
- Python tools: `pip install -r tests/requirements.txt`

Done means `bazelisk run //:validate` is green. Type errors are defects.

## Structure

- `scripts/manage.sh` - operator CLI. Prefer this over raw docker compose.
- `scripts/lib/*.sh` - shared shell. Tests: `tests/bats/lib_unit.bats`
- `scripts/utilities/<name>.sh` - tests: `tests/bats/<name>.bats`
- `docker/` - Compose + `patch_*.py`. Tests: `tests/python/*`, `tests/bats/safety.bats`
- `workflows/` - graphs. Lab: `workflows/_lab/<lane>/<id>.json`. Never copy `_lab` into `_user`.
- `custom_nodes/`, `config/`, `studio-ui/`
- `docs/`, `docs-site/` - Fumadocs. `main` publishes `/latest/`, `development` publishes `/development/`
- `tests/bats/`, `tests/python/`

Prefer relative paths. Operator actions go through `./scripts/manage.sh`.

## Branching

- Integrate on `development`. `main` is production promotion only.
- Every change: fetch, checkout `development`, `git pull --ff-only`, then `feature/...` `fix/...` `chore/...` `docs/...`
- PR into `development`. Do not commit on `development` or `main`.
- Do not base work on `main` except an explicit production hotfix (say so in the PR).
- No force-push on `development` or `main`.
- Commits: `feat:|fix:|docs:|test:|chore:|ci:|refactor:` + imperative summary.

## Tests

TDD for non-trivial work: red (failing bats/pytest) -> green (minimum change) -> refactor.
Ship tests in the **same commit** as the production files they cover.

- New shell functions must be named and exercised under `tests/` in that commit.
- First-party Python: 100% coverage fail-under, Pyright clean, mypy clean.
- No `eval` or aliases in scripts. Prefer `"${var}"`, `[[ ]]`, `$(...)`.
- Document new shell functions: Globals / Arguments / Outputs / Returns.

## Safety

Do not weaken, and state impact if you touch any of:

- `restart: "no"`
- heavy confirm on start
- headroom preflight
- download-limit clear-on-exit for wrap

`download-limit auto` = 85% of measured Mbps. Occupancy is XOR: one heavy GPU job.
Models stay US-safe: Klein 4B stills, Wan 2.2 silent motion, LTX-2.5 distilled AV.
Do not pin MiniMax, Seedance, or other non-catalog models in promoted workflows.

Promote a live graph with `./scripts/manage.sh promote-workflow` into
`workflows/_lab/<lane>/<id>.json`, then update `_build_*.py` + tests. Never copy `_lab` -> `_user`.

## Docs

If operator behavior, CLI, env vars, safety, or failure modes change, update docs in
the **same change**. Keep YAML frontmatter (`title`, `description`, `tags`).
Add symptoms to [docs/troubleshooting.mdx](docs/troubleshooting.mdx).
Relative in-repo links only.

# Parent vs children
- Parent is the dispatcher. No bulk Grep/Read/Edit on the parent once children exist.
- One child per disjoint file cluster. At most four at once.
- Child return: <=20 lines. Files, command, result. No source dumps.
- Parent verifies with one targeted test or diff, not by re-reading every file.
- If the task is one file or one function, do not spawn. A child is overhead.
