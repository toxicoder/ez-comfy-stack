---
title: Spark farm
description: Three DGX Sparks as independent Comfy workers plus a shared model cache — no NCCL, no MiniMax H3.
tags: [spark, farm, fabric, comfyui]
---

# Spark farm

**What's on this page**

- How three Sparks are used (farm vs relay)
- Fabric NFS / rsync vs management SSH
- Three ComfyUI UIs (Queue the lab-example graph on each)
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
| **Farm (default)** | Each Spark Queues an independent 5 s Wan or LTX shot. Shared `/mnt/models`. | Parallel shorts / concat-shots |
| **Do not implement** | NCCL split of a single denoise across 3 GB10s | Out of scope |

Clustering is **throughput + one weight copy**, not slicing one sampler. MiniMax H3 is banned — see [licenses](licenses.md).

## Networking (docs only — no IaC)

Physical: 3 Sparks, high-bandwidth already up.

- **3-node ring:** 3× QSFP DAC, both CX-7 ports live. NVIDIA Sync → Cluster Assistant. No switch.
- **Star via QSFP switch:** each Spark one or two 200 GbE links.

Management SSH stays on 10 GbE / RJ45. Model sync and shot-relay use **`SPARK_FABRIC_IPS` only**. Do not rsync multi-gig weights over the management NIC.

Shared `MODELS_DIR` (pick one):

1. **NFS over the fabric subnet (preferred):** Spark-0 exports `/mnt/models`; Sparks 1–2 mount it. Compose already bind-mounts `${MODELS_DIR}:/models`.
2. **Replica:** `./scripts/utilities/spark-farm.sh sync-models` rsyncs `MODELS_DIR/comfy` over fabric IPs.

See `config/spark-farm.example.env`.

## Per-node process

On **each** Spark (operator, with confirm):

```bash
git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
cd ez-comfy-stack
./scripts/manage.sh setup
# set MODELS_DIR=/mnt/models and HF_TOKEN in .env
./scripts/manage.sh doctor
./scripts/manage.sh download-models      # cache owner, or after NFS is up
./scripts/manage.sh start                # type yes
```

Three UIs: `http://spark-0:8188`, `http://spark-1:8188`, `http://spark-2:8188`. On each, load **wan-shot-lab-example** and **Queue** independently. Concat after approval — MiniMax H3 films are banned (see [licenses](licenses.md)).

`spark-farm.sh` **never** starts compose remotely. It prints the exact `./scripts/manage.sh start` you must run locally (heavy confirm stays on that node). Containers still use `restart: "no"`.

Memory: keep `MEM_LIMIT=90g`, `MEM_RESERVATION=80g`, `MIN_HOST_FREE_GIB=28`, `shm_size: 16gb`.

## Commands

```bash
./scripts/utilities/spark-farm.sh status [--json]
./scripts/utilities/spark-farm.sh sync-models
```
