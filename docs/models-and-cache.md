---
title: Models & Cache
description: Shared /mnt/models layout for FLUX and LTX weights, Hugging Face tokens, and multi-stack sharing.
tags: [models, huggingface, cache]
---

# Models & Cache

**What's on this page**

- Default cache location and layout
- Download utilities and readiness checks
- Sharing with nvidia-dgx-spark-lab

**What this enables**

- Downloading weights once and reusing them across stacks
- Checking readiness without network access

## Default location

```text
MODELS_DIR=/mnt/models
```

Override in `.env` if needed. Prefer a large, durable disk on the Spark.

### Permissions

`doctor`, `download-models`, and download utilities require `MODELS_DIR` to be **writable by the current user**.

Preferred:

```bash
./scripts/manage.sh setup
# sudo mkdir -p + chown for MODELS_DIR when needed
```

Manual:

```bash
sudo mkdir -p /mnt/models
sudo chown "$USER:$USER" /mnt/models
```

Or point at a home path:

```bash
# .env
MODELS_DIR=$HOME/models
```

## Layout

```text
/mnt/models/
  black-forest-labs__FLUX.2-klein-9b-nvfp4/
  tonera__FLUX.2-klein-9B-Nunchaku/
  Kijai__LTX2.3_comfy_balanced/
  comfy/
    diffusion_models/   # symlinks
    text_encoders/
    vae/
  hub/                  # HF cache (optional)
```

This matches the lab hostPath pattern so K8s and Docker demos can share weights.

```mermaid
flowchart TB
  Root["/mnt/models · MODELS_DIR"]
  Root --> Flux1["black-forest-labs__FLUX.2-klein-9b-nvfp4"]
  Root --> Flux2["tonera__FLUX.2-klein-9B-Nunchaku"]
  Root --> Ltx["Kijai__LTX2.3_comfy_balanced"]
  Root --> Comfy["comfy/"]
  Root --> Hub["hub/ · optional HF cache"]
  Comfy --> DM["diffusion_models/ · symlinks"]
  Comfy --> TE["text_encoders/"]
  Comfy --> VAE["vae/"]
```

## Utilities

```bash
./scripts/utilities/download-flux.sh status --tier fast --json
./scripts/utilities/download-ltx.sh status --tier balanced --json
./scripts/utilities/download-flux.sh run --tier fast
./scripts/utilities/download-ltx.sh run --tier balanced
```

Or:

```bash
./scripts/manage.sh download-models
```

Downloads use the modern **`hf download`** CLI (not deprecated `huggingface-cli`). Install:

```bash
command -v hf || pipx install huggingface_hub
# or: pip install -U 'huggingface_hub[cli]'
```

### LTX selective download (not the full monorepo)

`Kijai/LTX2.3_comfy` is a multi-variant hub repo (~**400 GB** if you pull everything). This stack defaults to a **selective** subset via `hf download --include`:

| Tier | Transformer (approx) | Plus | Total (approx) |
| --- | --- | --- | --- |
| **balanced** | distilled FP8 `…fp8_input_scaled_v3` (~25 GB) | text projection + video/audio VAE | ~28–30 GB |
| **quality** | distilled BF16 (~42 GB) | same TE + VAEs | ~45–48 GB |

`status --json` readiness uses `min_gb` 20 (balanced) / 35 (quality) as a floor, not the full monorepo size.

Escape hatch (operators who really want every precision/lora):

```bash
LTX_FULL_REPO=1 ./scripts/utilities/download-ltx.sh run --tier balanced
```

### Gated models / HF_TOKEN

FLUX and some LTX assets may require accepting the license on Hugging Face and a token:

```bash
# .env
HF_TOKEN=hf_...
# or: hf auth login
```

### Download path

```mermaid
sequenceDiagram
  actor Op as Operator
  participant M as manage.sh
  participant W as download-limit wrap
  participant F as download-flux.sh
  participant L as download-ltx.sh
  participant HF as Hugging Face
  participant Disk as MODELS_DIR

  Op->>M: download-models
  M->>W: --limit auto (default)
  W->>F: run --tier fast
  F->>HF: pull FLUX repos
  HF-->>Disk: flux weights + symlinks
  W->>L: run --tier balanced
  L->>HF: pull LTX repos
  HF-->>Disk: ltx weights + symlinks
  W-->>M: clear limit on EXIT/INT/TERM
```

### Multi-stack sharing

```mermaid
flowchart LR
  EZ["ez-comfy-stack<br/>Docker bind mount"]
  Cache["/mnt/models<br/>shared host path"]
  Lab["nvidia-dgx-spark-lab<br/>K8s hostPath"]
  EZ <--> Cache
  Lab <--> Cache
```

### Readiness check

```mermaid
flowchart TB
  Status["download-flux / download-ltx<br/>status --json"]
  Doctor["manage.sh doctor"]
  Status --> Check{"tiers present<br/>under MODELS_DIR?"}
  Doctor --> Check
  Check -->|yes| Ready["Ready for start"]
  Check -->|no| Missing["Run download-models<br/>or fix MODELS_DIR mount"]
```

## Licenses & tokens

Accept model licenses on Hugging Face. Set `HF_TOKEN` in `.env` when downloads are gated.

## Disk headroom

`manage.sh doctor` / `start` require free disk ≥ `MIN_DISK_FREE_GIB` (default 40).
