---
title: Spark farm
description: Three DGX Sparks as independent Comfy workers plus a shared model cache — no NCCL, no MiniMax H3.
tags: [spark, farm, fabric, comfyui]
---

# Spark farm

**What's on this page**

- How three Sparks are used (farm vs relay)
- Fabric NFS / rsync vs management SSH
- Three ComfyUI UIs (Queue lab-example graphs on each)
- Optional `sync-models` (rsync `MODELS_DIR/comfy` over fabric)
- What this sample stack refuses (NCCL, K3s, MiniMax H3)

**What this enables**

- Three concurrent 5 s Wan/LTX shots with **one weight copy**
- Copies on the 200 GbE fabric, not the 10 GbE mgmt NIC
- Unchanged `restart: "no"` and local heavy confirm on `start`

This remains a **per-node Comfy demo**. Tensor-parallel LLMs belong in [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab).

## Farm vs relay

| Mode | What the 3 Sparks do | When |
| --- | --- | --- |
| **Farm (default)** | Each Spark Queues an independent 5 s Wan or LTX shot. Shared `${MODELS_DIR}`. | Parallel shorts / concat-shots |
| **Do not implement** | NCCL split of a single denoise across 3 GB10s | Out of scope |

Clustering is **throughput + one weight copy**, not slicing one sampler. MiniMax H3 is banned — see [licenses](licenses.md).

## Networking (docs only — no IaC)

Physical: 3 Sparks, high-bandwidth already up.

- **3-node ring:** 3× QSFP DAC, both CX-7 ports live. NVIDIA Sync → Cluster Assistant. No switch.
- **Star via QSFP switch:** each Spark one or two 200 GbE links.

Management SSH stays on 10 GbE / RJ45. Model sync uses **`SPARK_FABRIC_IPS` only**. Do not rsync multi-gig weights over the management NIC.

Shared `MODELS_DIR` (pick one):

1. **NFS over the fabric subnet (preferred):** Spark-0 exports `${MODELS_DIR}` (default `/mnt/models`); Sparks 1–2 mount it. Compose already bind-mounts `${MODELS_DIR}:/models`.
2. **Replica:** `./scripts/utilities/spark-farm.sh sync-models` rsyncs `MODELS_DIR/comfy` over fabric IPs.

Copy `config/spark-farm.example.env`, edit hostnames/IPs, then:

```bash
set -a
source config/spark-farm.example.env   # after you filled in real hosts
set +a
```

## Per-node process

On **each** Spark (operator, with confirm):

```bash
git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
cd ez-comfy-stack
./scripts/manage.sh setup
# set MODELS_DIR and HF_TOKEN in .env (same MODELS_DIR on every node)
./scripts/manage.sh doctor
./scripts/manage.sh download-models      # cache owner, or after NFS is up
./scripts/manage.sh start                # type yes
```

Three UIs (replace hostnames from `SPARK_COMFY_URLS`):

```bash
# After sourcing spark-farm.example.env
# http://spark-0.local:8188  http://spark-1.local:8188  http://spark-2.local:8188
```

On each UI, load the unified **film-*-90s-*-lab-example** graph (or **ltx-i2v-shot-lab-example** / optional **wan-i2v-shot-lab-example**) and **Queue** independent **5 s** shots — different beats in parallel for the 90s films. Concat locally:

```bash
FILM=go-see   # or still-here | switchyard
./scripts/utilities/concat-shots.sh --film "${FILM}" --yes
```

See [90s shorts](shorts.md). MiniMax H3 films are banned (see [licenses](licenses.md)).

`spark-farm.sh` **never** starts compose remotely. It prints the exact `./scripts/manage.sh start` you must run locally (heavy confirm stays on that node). Containers still use `restart: "no"`.

The `run` subcommand prints a **film-*-90s / wan-i2v-shot / ltx-i2v-shot** Queue reminder for `--film go-see` (or still-here / switchyard). It does **not** POST graphs. It refuses MiniMax H3 names (`*h3*` / `*MiniMax*`).

Memory: keep `MEM_LIMIT=90g`, `MEM_RESERVATION=80g`, `MIN_HOST_FREE_GIB=28`, `shm_size: 16gb`.

## Commands

```bash
./scripts/utilities/spark-farm.sh status [--json]
./scripts/utilities/spark-farm.sh sync-models
./scripts/utilities/spark-farm.sh run --film go-see
```
