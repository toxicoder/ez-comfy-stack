---
title: Project Conventions
description: Conventions for shell (Google Shell Style Guide), Docker, docs, testing, and safety in ez-comfy-stack.
tags: [conventions, contributing, safety, shell, google-style]
---

# Project Conventions

**What's on this page**

- Core principles
- Repo layout and ownership
- Shell style (Google Shell Style Guide + project deviations)
- Docker, testing, coverage gate, and branching rules

**What this enables**

- Consistent, reviewable contributions without the full lab Bazel/K8s surface
- Shell that matches industry practice while staying safe on remote DGX Spark hosts

## Principles

| Principle | Meaning |
| --- | --- |
| Stability first | SSH stays usable under load |
| Explicit resources | Docker mem limits always set |
| No auto-start | `restart: "no"` |
| Hermetic tests | BATS/pytest without real Spark |
| Docs as code | MkDocs pages with required sections |
| Keep it small | No K8s/Ansible/dashboard/Bazel |
| Style as gate | ShellCheck + shfmt on every change |

## Repo layout

```mermaid
flowchart TB
  Root["ez-comfy-stack"]
  Root --> Manage["scripts/manage.sh<br/>operator CLI"]
  Root --> Lib["scripts/lib/*<br/>common · compose · paths · safety"]
  Root --> Util["scripts/utilities/*<br/>download-flux · download-ltx · download-limit"]
  Root --> Docker["docker/*<br/>compose · Dockerfile · entrypoint · patch"]
  Root --> Cfg["config/resource-policy.yaml"]
  Root --> Docs["docs/ · MkDocs"]
  Root --> Tests["tests/bats · tests/python"]
  Manage --> Lib
  Manage --> Util
  Manage --> Docker
```

## Shell style

**Primary reference:** [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html).

This project follows that guide for executables and libraries, with the **intentional deviations** below. When the guide and this page conflict, this page wins for the listed deviations only.

### Rules we follow (summary)

| Area | Rule |
| --- | --- |
| Language | Bash only for executables |
| STDERR | `log` / `warn` / `err` → stderr; data/JSON → stdout |
| Comments | File overview header; every library function documented |
| Function docs | Google-style **Globals / Arguments / Outputs / Returns** blocks |
| Indent | 2 spaces; no tabs (`shfmt -i 2 -ci`) |
| Control flow | `; then` / `; do` on same line as `if` / `for` / `while` |
| Tests | Prefer `[[ … ]]`; use `-z` / `-n` for empty strings; `==` for equality |
| Command subst | `$(…)` only (never backticks) |
| Quoting | Quote expansions: `"${var}"`, `"${array[@]}"`, `"$@"` |
| Arrays | Use arrays for argument lists; expand with `"${arr[@]}"` |
| Arithmetic | `$((…))` / `((…))`; not `let` / `expr` / `$[…]` |
| Eval / aliases | Forbidden in scripts |
| Pipes to while | Prefer process substitution: `while read; do …; done < <(cmd)` |
| Locals | `local` in functions; split `local x` / `x="$(cmd)"` when exit status of `cmd` matters |
| Constants | `UPPER_SNAKE`; prefer `readonly` when set once |
| Naming | Functions/vars `lower_snake_case`; `name()` without `function` keyword |
| Structure | Helpers grouped; multi-function scripts use `main` + source guard |
| Libraries | `scripts/lib/*.sh` — `.sh` extension, **not** executable |
| Entry scripts | `*.sh`, executable, `set -euo pipefail` |
| ShellCheck | Clean at warning level (`make lint`) |
| SUID/SGID | Forbidden |

### Intentional deviations from Google

| Google guide | This project | Why |
| --- | --- | --- |
| Shebang `#!/bin/bash` | `#!/usr/bin/env bash` | Works on macOS (Homebrew bash) and Linux Spark without assuming `/bin/bash` is modern |
| Prefer scripts ≤ ~100 lines or rewrite | Modular multi-file shell ops surface | Operator tooling is intentionally Bash; split by domain (`lib/*`, utilities) |
| Function banner style only | Globals/Arguments/Outputs/Returns labels (Google fields) | Clearer API docs; optional `# @command` on CLI entrypoints for help discoverability |
| Hard 80-column lines | Prefer ≤80; soft max ~100 | Long HF repo ids and one-line JSON status payloads |
| Package functions with `::` | Flat `verb_noun` names | Single small repository |

### Function comment template

```bash
#######################################
# One-line summary of behavior.
# Longer notes if needed for non-obvious safety or side effects.
# Globals:
#   MODELS_DIR (read)
# Arguments:
#   $1 - tier id (fast|quality|…)
# Outputs:
#   Writes human status to stderr; JSON to stdout when --json
# Returns:
#   0 on success, 1 on error
#######################################
some_func() {
  local tier="${1}"
  …
}
```

### Entry script skeleton

```bash
#!/usr/bin/env bash
#
# ## tool-name
#
# Overview, usage, safety, exit codes.

set -euo pipefail

# sources, constants (readonly where fixed)

#######################################
# …
#######################################
helper() { …; }

#######################################
# CLI dispatcher.
# Arguments:
#   $@ - CLI args
#######################################
main() {
  …
}

# shfmt -s may leave ${BASH_SOURCE[0]} unquoted inside [[ ]]; that is intentional.
if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi
```

### Utility contract

Utilities under `scripts/utilities/` implement at least:

| Subcommand | Contract |
| --- | --- |
| `status [--json]` | Read-only; exit 0 when reporting succeeds |
| `run` | Idempotent where practical |
| Extra | `clear` / `wrap` allowed for download-limit |

```mermaid
flowchart LR
  Status["status --json<br/>read-only"] --> Ready["Report readiness"]
  Run["run"] --> Work["Idempotent work"]
  Extra["clear / wrap<br/>download-limit only"] --> Safety["Always clear on exit"]
```

## Docker

- One compose service for the unified stack  
- Multi-stage image: **devel** builder + **runtime** final (no secrets/models)  
- GHCR channel by long-lived branch: publish tags `flux-to-ltx` (`main`) and `flux-to-ltx-development`; `manage.sh` pulls the tag for the current git branch (feature branches use the development channel)  
- Scripts as real files (not inline ConfigMap YAML)  
- Host model cache + named volume for Comfy state  
- Compose `restart: "no"`; explicit `mem_limit` / `mem_reservation`  

```mermaid
flowchart TB
  Compose["docker-compose.yml"] --> Svc["comfyui service"]
  Svc --> Restart["restart: no"]
  Svc --> Mem["mem_limit / mem_reservation"]
  Svc --> Models["bind MODELS_DIR"]
  Svc --> State["volume comfy-state"]
```

## Testing

- TDD for behavior changes  
- BATS for shell; pytest for Python  
- **Hermetic by default**: `test_helper.bash` sets `LAB_HERMETIC=1`, speed/probe mocks, and `HF_PROGRESS=0` (no real curl/speedtest, no progress-monitor sleeps)
- **Parallel BATS**: `bats --jobs` across files when GNU `parallel` is installed (`BATS_JOBS` override); serialize within files
- `make coverage` enforces:
  - **100% Python line coverage** on `patch_get_free_memory`
  - **Strict shell inventory**: every function in `scripts/**/*.sh` and `docker/**/*.sh` must be **named under `tests/`** (production-only references do not count)
  - Full BATS suite green  
- **Tests ship with production code** — same commit as the files under test  
- **Test shell style**: `tests/bats/*.bats`, `tests/bats/*.bash`, and `tests/*.sh` follow the Google Shell Style Guide where applicable (quoted `"${var}"`, `[[ … ]]`, Google-style helper comments in `test_helper.bash`, 2-space indent / shfmt for `.sh` runners)

```mermaid
flowchart LR
  Red["Red<br/>failing BATS / pytest"] --> Green["Green<br/>minimum production change"]
  Green --> Refactor["Refactor<br/>keep green"]
  Refactor --> Commit["Same commit<br/>tests + production"]
```

```mermaid
flowchart TB
  Cov["make coverage"] --> Py["100% line · patch_get_free_memory"]
  Cov --> Shell["Every scripts/** + docker/** function<br/>named under tests/"]
  Cov --> Bats["Full BATS suite green"]
  Lint["make lint"] --> SC["ShellCheck warnings = defects"]
  Lint --> Fmt["shfmt"]
```

## Branches

- Feature work from `development`: `feature/<short-description>`  
- Conventional commit titles  
- PR into `development` first  

```mermaid
flowchart LR
  Feat["feature/* · fix/* · chore/* · docs/*"] --> Dev["development"]
  Dev --> Main["main<br/>production-ready only"]
```

## Docs publish

- Local / PR: `make docs` (strict MkDocs Material build into `site/`)
- Public site (per long-lived branch) via **mike** on GitHub Pages:
  - `main` → [latest](https://toxicoder.github.io/ez-comfy-stack/latest/)
  - `development` → [development](https://toxicoder.github.io/ez-comfy-stack/development/)
- Workflow: `.github/workflows/deploy-docs.yml` (push to `main`/`development` with docs paths, or `workflow_dispatch`)
- Prefer **relative** links between pages and to in-repo paths so they stay correct on every git branch and under each published version prefix
- Branch-stamped Edit links: `docs/hooks.py` + `EZ_DOCS_VERSION` / `MIKE_DOCS_VERSION`
