# AGENTS.md

Guidelines for AI coding agents in **ez-comfy-stack**.

Shared style lives in [docs/project-conventions.md](docs/project-conventions.md). **Shell code follows the [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)** with documented deviations in that conventions page. This file is **agent workflow** only.

## Branching

| Branch | Role |
| --- | --- |
| `development` | Primary integration |
| `main` | Production-ready promotion only |

### Always branch from `development`

**Mandatory for every feature, fix, chore, or docs change:**

1. Update integration: `git fetch origin && git checkout development && git pull --ff-only origin development`
2. Create a topic branch: `feature/…`, `fix/…`, `chore/…`, or `docs/…`
3. Implement and open a PR **into `development`**

**Do not:**

- Commit feature/fix work directly on `development` or `main`
- Base a new branch on `main` (exception: explicit production hotfix only; state that in the PR)
- Force-push protected branches (`development`, `main`)

Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`

```mermaid
flowchart LR
  Base["checkout + update development"] --> Topic["feature/* · fix/* · chore/* · docs/*"]
  Topic --> PR["PR → development"]
  PR --> Dev["development"]
  Dev --> Main["main · production-ready only"]
```

## TDD

Default for non-trivial changes:

1. **Red** — failing BATS or pytest  
2. **Green** — minimum production change  
3. **Refactor** — keep green  

### Tests ship with production code

**Always commit tests in the same change as the files they cover.** Do not land a feature or fix and follow up with a separate “add tests” commit for that work.

| Production change | Same commit includes |
| --- | --- |
| `scripts/lib/*.sh` | `tests/bats/lib_unit.bats` (or a focused bats file) |
| `scripts/utilities/<name>.sh` | `tests/bats/<name>.bats` (or extend existing) |
| `scripts/manage.sh` | `tests/bats/manage.bats` |
| `docker/patch_*.py` / compose safety fields | `tests/python/*` and/or `tests/bats/safety.bats` |

```mermaid
flowchart TB
  subgraph SameCommit["Same commit"]
    P1["scripts/lib/*.sh"] --> T1["tests/bats/lib_unit.bats"]
    P2["scripts/utilities/name.sh"] --> T2["tests/bats/name.bats"]
    P3["scripts/manage.sh"] --> T3["tests/bats/manage.bats"]
    P4["docker/patch_*.py · safety"] --> T4["tests/python/* · safety.bats"]
  end
```

### Shell style (Google)

When adding or editing shell (including `tests/bats/*.bash` helpers and `tests/*.sh` runners):

- Prefer `"${var}"`, `[[ … ]]`, `$(…)`, process substitution over `find | while`
- Document functions with **Globals / Arguments / Outputs / Returns**
- Run `make fmt` and `make lint` (ShellCheck warnings are defects)
- Do not use `eval` or aliases in scripts
- See conventions for intentional deviations (`env bash`, modular script length)
- Coverage: new functions must be **named and exercised under `tests/`** in the same commit
Finish with:

```bash
make test
make coverage
make lint
```

## Safety callouts

Any change to Docker resources, restart policy, headroom, or download-limit must state **safety impact**. Do not weaken:

- `restart: "no"`  
- heavy confirm on start  
- headroom preflight  
- download-limit clear-on-exit for wrap  

```mermaid
flowchart TB
  S1["restart: no"] --> Keep["Do not weaken"]
  S2["heavy confirm on start"] --> Keep
  S3["headroom preflight"] --> Keep
  S4["download-limit clear-on-exit"] --> Keep
```

## Paths

Prefer relative paths. Prefer `./scripts/manage.sh` for operator actions.

## Docs

### Always keep documentation current with the change

**Mandatory:** when operator behavior, CLI surface, env vars, safety, or failure modes change, update docs in the **same change set** as the production code. Do not land behavior changes with a default “docs later” follow-up.

After code changes, agents must:

1. Update the relevant `docs/*.md` pages (and README if onboarding/commands change)
2. Keep MkDocs frontmatter + “What's on this page” / “What this enables”
3. Prefer **relative** in-repo doc links
4. Update [docs/troubleshooting.md](docs/troubleshooting.md) when new symptoms or fixes appear

Public site publishes after merge via `.github/workflows/deploy-docs.yml` (mike): `main` → `/latest/`, `development` → `/development/`.

## Scope

This is a **sample** stack. Do not pull in K3s, Bazel, full dashboard, or multi-node NCCL. Point long-term users at nvidia-dgx-spark-lab.
