---
title: Spark farm
description: Three DGX Sparks as independent Comfy workers plus a shared model cache — farm and relay, no NCCL.
tags: [spark, farm, fabric, h3, comfyui]
---

# Spark farm

**What's on this page**

- How three Sparks are used (farm vs relay)
- Fabric NFS / rsync vs management SSH
- Operator commands (`farm-h3`, `sync-models`)
- What this sample stack refuses (NCCL, K3s)

**What this enables**

- Three concurrent 90.00s MiniMax H3 films with **one weight copy**
- Shot-relay copies on the 200 GbE fabric, not the 10 GbE mgmt NIC
- Unchanged `restart: "no"` and local heavy confirm on `start`

This remains a **per-node Comfy demo**. Tensor-parallel LLMs belong in [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab).

## Farm vs relay

| Mode | What the 3 Sparks do | When |
| --- | --- | --- |
| **Farm (default)** | Each Spark runs one full 6-shot film (different film / seed). Shared `/mnt/models`. | GO SEE + STILL HERE + SWITCHYARD, or 3 seeds of GO SEE |
| **Relay (optional)** | Spark-0 samples shot N, writes last-frame PNG + WAV to the share; Spark-1 samples shot N+1. | One film, if weight-load dominates wall-clock |
| **Do not implement** | NCCL split of a single H3 denoise across 3 GB10s | Out of scope |

GB10 128 GB unified memory holds INT8 FL2VA + NVFP4 Qwen3-VL-32B + both VAEs. Clustering is **throughput + one weight copy**, not slicing one sampler.

## Networking (docs only — no IaC)

Physical: 3 Sparks, high-bandwidth already up.

- **3-node ring:** 3× QSFP DAC, both CX-7 ports live. NVIDIA Sync → Cluster Assistant. No switch.
- **Star via QSFP switch:** each Spark one or two 200 GbE links.

Management SSH stays on 10 GbE / RJ45. Model sync and shot-relay use **`SPARK_FABRIC_IPS` only**. Do not rsync multi-gig weights over the management NIC.

Shared `MODELS_DIR` (pick one):

1. **NFS over the fabric subnet (preferred):** Spark-0 exports `/mnt/models`; Sparks 1–2 mount it. Compose already bind-mounts `${MODELS_DIR}:/models`.
2. **Replica:** `./scripts/utilities/spark-farm.sh sync-models` rsyncs the H3 tree over fabric IPs.

See `config/spark-farm.example.env`.

## Per-node process

On **each** Spark (operator, with confirm):

```bash
git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
cd ez-comfy-stack
./scripts/manage.sh setup
# set MODELS_DIR=/mnt/models and HF_TOKEN in .env
./scripts/manage.sh doctor
./scripts/manage.sh download-h3          # cache owner, or after NFS is up
./scripts/manage.sh start                # type yes
```

Three UIs: `http://spark-0:8188`, `http://spark-1:8188`, `http://spark-2:8188`.

`farm-h3` **never** starts compose remotely. It prints the exact `./scripts/manage.sh start` you must run locally (heavy confirm stays on that node). Three containers still use `restart: "no"`.

From a laptop or Spark-0:

```bash
export SPARK_COMFY_URLS=http://spark-0:8188,http://spark-1:8188,http://spark-2:8188
./scripts/manage.sh farm-h3 --film go-see --seeds 509201,509211,509221
```

Memory: keep `MEM_LIMIT=90g`, `MEM_RESERVATION=80g`, `MIN_HOST_FREE_GIB=28`, `shm_size: 16gb`. If a node OOMs at 1344×768×379, use `--size 864x480` rather than raising mem limits.

## Commands

```bash
./scripts/utilities/spark-farm.sh status [--json]
./scripts/utilities/spark-farm.sh sync-models
./scripts/manage.sh farm-h3 --film go-see
./scripts/manage.sh queue-h3 --film go-see --relay
./scripts/manage.sh stitch-h3 --dir <shots>   # H3-native concat only; -t 90
```
