---
title: Config and schemas
description: Purpose, consumers, and safety for disk-catalog, model-manifest, resource-policy, farm env, .env.example, and schemas/.
tags: [config, schemas, safety, models, farm]
---

# Config and schemas

**What's on this page**

- **Operator config** — disk catalog, model manifest, resource policy, farm example env, `.env.example`
- **Handshake schemas** — asset, guide packs, house layout, scene, shot card
- **Who consumes each file** (`manage.sh` verb or library)
- **Safety** — keep-set, headroom, no secrets in git

**What this enables**

- **Knowing** which YAML is a disk bible vs a DCC pack vs a farm placeholder
- **Avoiding** committing `${HF_TOKEN}` or real Spark hostnames
- **Leaving** keys and values to the files themselves (this page does not dump them)

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

!!! danger "Do not commit secrets"

    Never put `HF_TOKEN`, a filled `.env`, or production hostnames into git. Farm hosts in `config/spark-farm.example.env` are **placeholders** (`spark-0.local`, fabric `10.0.0.1`…). Do not treat those as a real cluster.

!!! warning "Do not weaken headroom"

    `config/resource-policy.yaml` documents `min_host_free_gib: 28` and `memory_limit: 90g`. `manage.sh start` mirrors those via `MIN_HOST_FREE_GIB` / `MEM_LIMIT`. Demos do not get a pass.

---

## Operator config

| File | Purpose | Who consumes it | Safety |
| --- | --- | --- | --- |
| `config/disk-catalog.yaml` | Leftover signatures for disk-wizard (`risk` / `reclaim`) | `./scripts/manage.sh disk-wizard` → `scripts/lib/disk_catalog.py` | Keep-set weights and volume `ez-comfy-state` are **dangerous / none**. Never `docker system prune -a --volumes` |
| `config/model-manifest.yaml` | Disk bible for `${MODELS_DIR}`: keep-set packs + **refuse** list | `reap-models`, `models-status`, `scripts/lib/model_manifest.py` / `models.sh`. License bible stays `LICENSE-MODELS.md` | Refuse includes MiniMax-H3, DA3-LARGE, … Klein 9B / FLUX.2-dev are opt-in packs (`default: false`) |
| `config/resource-policy.yaml` | Human-readable GB10 headroom, mem 90g/80g, occupancy mode table, default model tiers | Operators; **mirrored** by `manage.sh` defaults (`MIN_HOST_FREE_GIB`, `MEM_LIMIT`, stack ports) | Do not lower `min_host_free_gib` without measuring SSH under load |
| `config/spark-farm.example.env` | Copy-and-fill farm variables | `./scripts/utilities/spark-farm.sh` after `set -a; source …` | Placeholders only. Management SSH is **not** the 200 GbE fabric. MiniMax H3 banned. [Spark farm](../spark-farm.md) |
| `.env.example` | Template `setup` copies to `.env` | `./scripts/manage.sh setup` / Compose interpolation | `HF_TOKEN=` stays commented. Do not commit a filled `.env` |

`.env.example` session keys used in docs: `MODELS_DIR`, `COMFY_OUTPUT_DIR`, `COMFY_PORT`, `DOWNLOAD_LIMIT`, plus `MEM_LIMIT` / `MEM_RESERVATION` / `MIN_HOST_FREE_GIB`. `SPARK_HOST` / `SPARK_USER` are docs/session (browser **Your Spark** panel and SSH), not required Compose keys.

Farm placeholders (from the example file — not a real rack):

```bash
# After you copy and fill — do not commit real names
SPARK_HOSTS=spark-0.local,spark-1.local,spark-2.local
SPARK_USER=nvidia
SPARK_COMFY_URLS=http://spark-0.local:8188,http://spark-1.local:8188,http://spark-2.local:8188
SPARK_FABRIC_IPS=10.0.0.1,10.0.0.2,10.0.0.3
MODELS_DIR=/mnt/models
```

---

## Schemas

Restricted YAML (stdlib parsers; no PyYAML). `scene.json` is JSON.

| File | Purpose | Who consumes it | Safety |
| --- | --- | --- | --- |
| `schemas/asset.yaml` | `ez.asset.v1` Asset Bible record (outputs under `${COMFY_OUTPUT_DIR}/assets`) | `./scripts/manage.sh asset-ls` → `scripts/lib/asset_bible.py` | **Never** `${MODELS_DIR}`. `license: operator-output` on the example |
| `schemas/guide_pack.shot.yaml` | `ez.guide.shot.v1` DCC ↔ Comfy print handshake (120 frames @ 24 fps) | `export-guides` / `scripts/lib/guide_pack.py` | Size is LTX VAE grid **1280×704** or **768×1280**. Never 1280×720 |
| `schemas/guide_pack.still.yaml` | `ez.guide.still.v1` single-frame clay/depth/canny plates | `blender-stills` | Allowed sizes: 1280×704, 768×1280, 1024×1280, 1024×1024, 1280×720 (**Klein thumb only**, never LTX) |
| `schemas/house_layout.yaml` | `ez.house.layout.v1` greybox for Instagram 4:5 clay stills | `house-views`, `start` seed-inputs → `scripts/lib/house_layout.py` | Y-up meters. Occupancy: dump dies if Comfy is a heavy job |
| `schemas/scene.json` | Instance list (`ref` + transform) — no embedded meshes | `asset_bible.py` `validate` / `load_scene` | Refuses data-URI / huge strings (meshes do not belong here) |
| `schemas/shot_card.yaml` | `ez.shot.card.v1` film bible extras on `workflows/shorts/*.shots.yaml` | `shot-sheet`; lab YAML on the host (not copied by entrypoint) | Optional keys default fail-closed. Does **not** replace `ez.guide.shot.v1` |

---

## Related

| Need | Page |
| --- | --- |
| `--tier` pack map | [Download tiers](../download-tiers.md) |
| Keep-set vs `cleanup` | [Models and cache](../models-and-cache.md) |
| Disk leftovers | [Disk wizard](../disk-wizard.md) |
| Occupancy modes in resource-policy | [Occupancy matrix](../operate/occupancy-matrix.md) |
