---
title: Disk wizard
description: Guided, plan-first reclaim for leftover AI experiment files on a DGX Spark that also runs other inference backends.
tags: [disk, wizard, docker, huggingface, ollama, safety]
---

# Disk wizard

**What's on this page**

- What the wizard will and will not touch
- How it differs from `cleanup` and `reap-models`
- Plan → explain → apply
- Restore from quarantine

**What this enables**

- Freeing tens of GB of leftover HF blobs, Docker build cache, Ollama pulls, and superseded Comfy packs **without** deleting the lab keep-set
- Understanding *what a file is*, *why you might have it*, and *the risk of removing it*
- Keeping `cleanup` as volume-only and `reap-models` as the MODELS_DIR specialist

**Safety impact:** additive. Default is read-only `--plan`. Does not change `restart: "no"`, start `yes`, headroom, or download-limit clear-on-exit.

---

## When to use this

You run this studio **and** other experiments on the same Spark (vLLM, Ollama, llama.cpp, extra Compose stacks, ad-hoc `hf download`). Disk fills with residue that `reap-models` cannot see because it only walks `MODELS_DIR`.

```ezcmd
id: disk-wizard-plan
```

TTY with no flags starts a numbered guide, then still writes a plan. Non-interactive (CI, pipes) is `--plan`. `--apply` requires `--yes`.

---

## Three tools (do not mix them up)

| Tool | Scope | Default | Deletes weights? |
| --- | --- | --- | --- |
| `cleanup` | Named volume `ez-comfy-state` only | type `DELETE` | **No** |
| `reap-models` | `MODELS_DIR` classes (junk / superseded / banned / drop-pack) | `--plan` | Only after `--apply --yes` |
| `disk-wizard` | Host leftovers (HF hub, Docker cache, Ollama, tmp dumps, MODELS_DIR junk) | `--plan` | Safe junk after `--apply --yes`; review-class **quarantines** |

Never offered: `docker system prune -a --volumes`. That would eat other stacks' volumes.

---

## Wizard steps

1. **Survey** (always read-only) — `df`, Docker `system df` when available, catalog matches, top files under allowed roots.
2. **Explain + rank** — largest *likely leftover* first. Each row: what / why / risk / reclaim / whether something is running.
3. **Guide in three steps**
    - **A — Safe junk** — `*.incomplete`, dangling Comfy symlinks, unused Docker **build cache**, detached HF revisions, core dumps. Default accept on `--apply`.
    - **B — Review leftovers** — unused named images, HF hub repos that are not the lab keep-set, Ollama blobs, opt-in Comfy packs, large MP4s under `COMFY_OUTPUT_DIR`. Default **skip**. Set `DISK_WIZARD_STEP_B=1` to quarantine those when applying.
    - **C — Will not touch** — default keep-set weights, `ez-comfy-state` (use `cleanup`), images of running containers, path escape, other users' homes.
4. **Confirm** — `--apply --yes`. Log: `${MODELS_DIR}/.disk-wizard.log`.

```bash
./scripts/manage.sh disk-wizard --plan
./scripts/manage.sh disk-wizard --json
./scripts/manage.sh disk-wizard --apply --yes
./scripts/manage.sh disk-wizard restore --from .disk-quarantine/<utc>
```

---

## What a row means

| Field | Meaning |
| --- | --- |
| **what** | What this file or Docker object is |
| **why** | Why it exists on a Spark used for mixed inference experiments |
| **risk** | `safe` (junk) / `review` (maybe still wanted) / `dangerous` (refused) |
| **reclaim** | `delete` / `quarantine` / `hf-prune` / `reap-models` / `none` |

Quarantine dest: `${MODELS_DIR}/.disk-quarantine/<utc>/` when the path is under `MODELS_DIR`, else `${COMFY_OUTPUT_DIR}/.disk-quarantine/<utc>/`. Manifest is JSONL. Restore moves files back.

---

## Allowed roots

Default: `MODELS_DIR`, `COMFY_OUTPUT_DIR`, `$HOME/.cache`, `$HOME/.ollama`, `/tmp`, `/var/tmp`. Extra colon-separated roots: `DISK_WIZARD_ROOTS`. Paths are realpath-jailed (no `/`, `/boot`, other homes).

`--i-system` is **not** implemented in v1 (apt/journal stay off).

---

## Hard refuses

- Default keep-set basenames (Klein / Wan 5B / LTX-2.5 / GGUF)
- Docker image **in use**
- Named volume `ez-comfy-state`
- `docker system prune -a --volumes` as one shot
- HF pid / `.hf-download.pid` (override `--force`, not the happy path)
- Path escape after `realpath`
- Drive-by `rm -rf ~/.cache/huggingface`

MODELS_DIR class work still belongs to `reap-models` for superseded LTX-2.3 / drop-pack; the wizard **explains** those rows and quarantines on apply rather than reimplementing keep-set.

---

## Related

| Need | Page |
| --- | --- |
| MODELS_DIR classes only | [Models and cache](models-and-cache.md) |
| `--tier` pack map | [Download tiers](download-tiers.md) |
| Verb catalog | [manage.sh reference](manage-cli.md) |
| Disk-full symptom | [Troubleshooting](troubleshooting.md) |
