---
title: Hardware, memory, and safety
description: GB10 unified memory, occupancy, three stores (image / weights / volume), and why restart: no exists.
tags: [learn, gb10, unified-memory, safety, docker, spark]
---

# Hardware, memory, and safety

**What's on this page**

- Why SSH recoverability shapes every default
- Unified memory, 90g limit, headroom preflight
- Image vs weights vs comfy-state
- Occupancy, Kitchen attention, and the entrypoint

**What this enables**

- Operating a remote Spark without locking yourself out
- Knowing what `cleanup`, `stop`, and `download-models` each delete or keep

**Who this is for:** operators, and studio users who just hit OOM or a slow Queue.

!!! warning "Do not weaken"

    `restart: "no"`, type **yes** on start, headroom preflight, and download-limit **clear-on-exit** are the SSH-safe defaults. Demos do not get a pass.

---

## The constraint is SSH, not the demo

DGX Spark nodes are often driven over the internet with no KVM. A 90g GPU job that auto-starts on boot, or a full-rate Hugging Face pull, is how you lose the box.

```mermaid
flowchart LR
  S1["restart: no"] --> S2["type yes on start"]
  S2 --> S3["RAM/disk headroom"]
  S3 --> S4["download-limit auto 85%"]
  S4 --> Safe["SSH stays usable"]
```

Details: [Reboot safety](../reboot-safety.md) · [Download limit](../download-limit.md).

---

## Unified memory on GB10

GB10 shares **~128 GiB** among OS, SSH, Docker, and Comfy. There is no separate giant VRAM island.

```mermaid
flowchart TB
  subgraph UM["~128 GiB unified memory"]
    OS["OS + Docker + interactive SSH"]
    Free["min_host_free_gib ≥ 28 · required before start"]
    Cont["Container mem_limit 90g · mem_reservation 80g"]
  end
  Free --> Gate{"doctor / start OK?"}
  Gate -->|yes| Cont
  Gate -->|no| Refuse["start refused"]
```

Lab flags (do not “optimize” these away):

| Setting | Why |
| --- | --- |
| Default VRAM + offload flags | Unified memory. Omit `--highvram` / `--gpu-only`. ComfyUI dropped `--normalvram` |
| `patch_unified_memory_copy.py` | `copy=False` so UM does not double weights |
| `patch_get_free_memory.py` | Host free RAM instead of under-reporting `cudaMemGetInfo` |
| `--use-ck-attention` | Comfy Kitchen. XOR Sage — never both |
| `TORCH_COMPILE_DISABLE=1` | Triton compile off by default on sm_121 |
| Occupancy | One heavy GPU job |

`doctor` must **not** print `attention: pytorch-fallback` on a running Spark (10–20× slow). spark-timing is measured on a real Spark after Kitchen is live — CI does not invent seconds.

```bash
./scripts/manage.sh doctor
# Queue klein-still-draft, wan-i2v-5s, ltx-i2v-5s
./scripts/manage.sh spark-timing record --klein N --wan N --ltx N
```

---

## Three stores

| Store | What it is | Destroyed by |
| --- | --- | --- |
| **GHCR image** | ComfyUI + PyTorch (`us-safe-studio` / `-development`) | Re-pull / rebuild. **No weights** |
| **MODELS_DIR** | Klein / Wan / LTX / GGUF on the host (default `/mnt/models`) | You, or `reap-models`. **Not** `cleanup` |
| **comfy-state volume** | Comfy install, custom nodes, seeded workflows | `cleanup` (type `DELETE`) |

Outputs live in **COMFY_OUTPUT_DIR** (default `/mnt/comfy-output`). `cleanup` does not delete them.

```mermaid
flowchart TB
  Image["GHCR image · Comfy + torch"] --> Vol["comfy-state volume"]
  Weights["MODELS_DIR · bind /models"] -.-> Comfy["ComfyUI process"]
  Vol --> Comfy
  Out["COMFY_OUTPUT_DIR · bind /outputs"] -.-> Comfy
```

---

## Occupancy

GB10 is **one** GPU.

```mermaid
flowchart TB
  G["GB10"] --> X{"One heavy job"}
  X --> C["Comfy visual or ACE-Step"]
  X --> B["Host Blender"]
  X --> S["SuperSplat / NLE / NVENC"]
```

`manage.sh blender`, `film-proxies`, and NVENC preview **die if compose is up**. Cover art is a separate Klein session from podcast/rap.

---

## What happens on start

```mermaid
sequenceDiagram
  participant C as compose up
  participant E as entrypoint.sh
  participant I as install-comfy.sh
  participant P as UM patches
  participant U as ComfyUI

  C->>E: start container
  E->>I: idempotent install / seed prebuilt
  I-->>E: COMFY_HOME + venv
  E->>P: free-memory + copy=False
  P-->>E: patched (fail-soft)
  E->>U: Kitchen + UM flags on :8188
```

First start usually **seeds** from `/opt/comfy-prebuilt`. Without that image, cold pip is **10–30+ minutes**. Ops scripts are bind-mounted — edit them on the host and restart; do not rebuild for an entrypoint typo.

Operator first run: [Getting Started](../getting-started.md). Command catalog: [manage.sh reference](../manage-cli.md).
