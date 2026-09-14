---
title: Multi-stack model sharing
description: Share one MODELS_DIR between ez-comfy-stack Docker and nvidia-dgx-spark-lab hostPath.
tags: [models, cache, sharing, spark-lab, huggingface]
---

# Multi-stack model sharing

**What's on this page**

- **One `MODELS_DIR`** shared by this Docker stack and nvidia-dgx-spark-lab
- **Download path** (`download-models` → Klein / Wan / LTX, limit clears on exit)
- **Readiness check** (`status --json` and `doctor`)

**What this enables**

- **Downloading weights once** and reusing them across stacks
- **Checking readiness** without network access

**Who this is for:** operators who also run nvidia-dgx-spark-lab. Layout: [Models and cache](../models-and-cache.md). This sample stack does not pull in K3s or multi-node NCCL.

---

## Multi-stack sharing

```mermaid
flowchart LR
  EZ["ez-comfy-stack<br/>Docker bind mount"]
  Cache["MODELS_DIR<br/>shared host path"]
  Lab["nvidia-dgx-spark-lab<br/>K8s hostPath"]
  EZ <--> Cache
  Lab <--> Cache
```

Independent Sparks share `MODELS_DIR`; still no in-tree NCCL. Graduate to nvidia-dgx-spark-lab for K8s / multi-node work.

### Download path

```mermaid
sequenceDiagram
  actor Op as Operator
  participant M as manage.sh
  participant W as download-limit wrap
  participant I as download-image.sh
  participant Wa as download-wan.sh
  participant L as download-ltx.sh
  participant HF as Hugging Face
  participant Disk as MODELS_DIR

  Op->>M: download-models
  M->>W: --limit auto (default)
  W->>I: run --tier fast
  I->>HF: pull Klein 4B + TE + VAE
  HF-->>Disk: still weights + symlinks
  W->>Wa: run --tier 5b
  Wa->>HF: pull Wan 5B
  HF-->>Disk: wan weights + symlinks
  W->>L: run --tier 2.5
  L->>HF: pull LTX-2.5
  HF-->>Disk: ltx weights + symlinks
  W-->>M: clear limit on EXIT/INT/TERM
```

Throttle details: [Download limit](../download-limit.md). Pack ids: [Download tiers](../download-tiers.md).

### Readiness check

```mermaid
flowchart TB
  Status["download-image / download-wan / download-ltx<br/>status --json"]
  Doctor["manage.sh doctor"]
  Status --> Check{"lab files present<br/>under MODELS_DIR/comfy?"}
  Doctor --> Check
  Check -->|yes| Ready["Ready for start"]
  Check -->|no| Missing["Run download-models<br/>or fix MODELS_DIR mount"]
```
