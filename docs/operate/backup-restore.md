---
title: Backup and restore
description: What to back up (MODELS_DIR, comfy-state, COMFY_OUTPUT_DIR, occupancy JSON) and what not to treat as a secret dump. Restore order.
tags: [backup, restore, cleanup, disk-wizard, safety]
---

# Backup and restore

**What's on this page**

- **What to back up** — `${MODELS_DIR}`, `comfy-state`, `${COMFY_OUTPUT_DIR}`, occupancy JSON
- **What not to back up as secrets** — `.env` / `HF_TOKEN`
- **Restore order**
- **`cleanup` vs a cache wipe**
- **disk-wizard quarantine restore**

**What this enables**

- **Recovering** a Spark without deleting Klein / Wan / LTX weights
- **Knowing** that type **DELETE** is the Comfy volume only
- **Moving** quarantined leftovers back after `disk-wizard --apply`

Stores: [Architecture](../learn/architecture.md) · [Models and cache](../models-and-cache.md).

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

!!! danger "cleanup vs wipe"

    `./scripts/manage.sh cleanup` (type **DELETE**) removes named volume **`ez-comfy-state`** only — Comfy install, venv, lab `ez_*` copies. It does **not** delete `${MODELS_DIR}` or `${COMFY_OUTPUT_DIR}`. Do **not** run `docker system prune -a --volumes`. Do **not** `rm -rf` `${MODELS_DIR}` unless you intend to re-download tens of GB (throttled wrap). `reap-models` and `disk-wizard` default to **`--plan`**.

---

## What to back up

| Tree | Holds | Notes |
| --- | --- | --- |
| **`${MODELS_DIR}`** (default `/mnt/models`) | Klein / Wan / LTX / GGUF weights + `comfy/` relative symlinks | Largest. Shareable across Sparks. **Not** deleted by `cleanup` |
| **`ez-comfy-state` volume** | Comfy install, venv, lab `ez_*` packs | `cleanup` **DELETE** removes this. After a wipe, `start` reseeds from the GHCR prebuilt |
| **`${COMFY_OUTPUT_DIR}`** (default `/mnt/comfy-output`) | PNG/MP4/audio, `input/` LoadImage, `comfy-user/` graphs, `custom-nodes-user/`, `films/`, `guides/`, `assets/`, `research/` | Survives `stop` and `cleanup` |
| **`${COMFY_OUTPUT_DIR}/.occupancy.json`** | Occupancy desk state | Outputs tree, never `${MODELS_DIR}` |

Three stores (image / weights / volume) are the mental model: the GHCR image is re-pullable; back up **weights** and **outputs**. The volume is optional — `start` can rebuild the install from the image.

---

## What not to back up as secrets

| Item | Why |
| --- | --- |
| **`.env`** | May contain `HF_TOKEN`. Recreate from `.env.example` + `setup` |
| **`HF_TOKEN`** | Gated LTX (and any gated HF). Store in the operator's secret manager, not a media tarball |
| **Filled `spark-farm.example.env`** | Real hostnames stay off git. Placeholders only in-tree |

Session vars in this browser (**Your Spark**) are localStorage, not a Spark backup.

---

## Restore order

1. **Host dirs** — writable `${MODELS_DIR}` and `${COMFY_OUTPUT_DIR}` (`./scripts/manage.sh setup`).
2. **Weights** — restore `${MODELS_DIR}` (or remount NFS). Then `./scripts/manage.sh doctor`. Missing files: `download-models` (throttled; `${DOWNLOAD_LIMIT}`).
3. **Outputs** — restore `${COMFY_OUTPUT_DIR}` (media, `comfy-user/`, occupancy JSON, films, guides).
4. **Secrets** — put `HF_TOKEN` in `.env` or `hf auth login`. Do not unpack a token from a public backup.
5. **Compose** — `./scripts/manage.sh start` (type **yes**). Headroom preflight still runs. `restart: "no"` unchanged. If you did **not** restore `ez-comfy-state`, the entrypoint seeds from `/opt/comfy-prebuilt`.
6. **Occupancy** — optional: keep `.occupancy.json` or `occupancy enter idle` and start clean.
7. **Farm** — each Spark still types **yes** locally. Never remote `compose up`. [Spark farm](../spark-farm.md).

```bash
./scripts/manage.sh setup
./scripts/manage.sh doctor
./scripts/manage.sh download-models    # only if weights missing
./scripts/manage.sh start              # type: yes
```

---

## disk-wizard quarantine restore

`disk-wizard --apply --yes` **quarantines** review-class leftovers. Dest: `${MODELS_DIR}/.disk-quarantine/<utc>/` when the path is under `${MODELS_DIR}`, else `${COMFY_OUTPUT_DIR}/.disk-quarantine/<utc>/`. Manifest is JSONL.

```bash
./scripts/manage.sh disk-wizard --plan
./scripts/manage.sh disk-wizard restore --from .disk-quarantine/<utc>
```

`--from` is absolute, or relative to `${MODELS_DIR}`. Restore `mv`s files back (skips `MANIFEST.jsonl`). Keep-set weights and `ez-comfy-state` were never offered for delete. [Disk wizard](../disk-wizard.md).
