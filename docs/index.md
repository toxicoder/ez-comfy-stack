---
title: ez-comfy-stack
description: Lean Visual Generative AI demo stack (ComfyUI flux-to-ltx) for a single NVIDIA DGX Spark.
tags: [comfyui, flux, ltx, dgx-spark, docker]
---

# ez-comfy-stack

**What's on this page**

- What this project is (and is not)
- System context and how pieces connect
- Safety principles for remote DGX Spark access
- High-level layout and next links

**What this enables**

- Spinning up a **unified Flux → LTX** ComfyUI demo on one Spark quickly
- Sharing model weights with other stacks via `/mnt/models`
- Operating the stack safely over SSH without locking yourself out

## Purpose

This is a **sample / demo** repository for **Visual Generative AI** on a **single NVIDIA DGX Spark (GB10)**. It is deliberately smaller than [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab): Docker Compose instead of K3s, one unified profile instead of a full lab.

Long-term multi-workload operations should use the full lab project. Use **ez-comfy-stack** when you want faster experimentation.

### This stack vs the full lab

```mermaid
flowchart TB
  subgraph EZ["ez-comfy-stack"]
    direction TB
    E1["Docker Compose"]
    E2["One profile: flux-to-ltx"]
    E3["manage.sh operator CLI"]
    E4["Shared /mnt/models"]
    E1 --> E2 --> E3
    E2 --> E4
  end
  subgraph LAB["nvidia-dgx-spark-lab"]
    direction TB
    L1["K3s / multi-workload"]
    L2["Many stacks + dashboard"]
    L3["Long-term ops"]
    L1 --> L2 --> L3
  end
  EZ -->|"graduate when you outgrow demos"| LAB
```

## System context

How an operator reaches ComfyUI on a remotely managed Spark:

```mermaid
flowchart TB
  Op["Operator workstation"]
  SSH["SSH / port-forward"]
  subgraph Spark["DGX Spark host"]
    direction TB
    Manage["./scripts/manage.sh"]
    Compose["Docker Compose<br/>restart: no · mem_limit 90g"]
    subgraph Ctr["comfyui container"]
      Comfy["ComfyUI"]
    end
    Models["/mnt/models<br/>shared cache"]
  end
  UI["Browser · http://spark:8188"]

  Op --> SSH --> Manage
  Manage --> Compose --> Comfy
  Models -.->|bind mount| Comfy
  Comfy --> UI
  Op --> UI
```

## Default stack

| Item | Value |
| --- | --- |
| Runtime | ComfyUI (Docker) |
| Pipeline | **flux-to-ltx** (text → image → video frames; audio VAE available) |
| Flux tier | fast — FLUX.2 Klein 9B NVFP4 + Nunchaku |
| LTX tier | balanced — LTX-2.3 distilled FP8 |
| Models | host `/mnt/models` |
| UI | port **8188** |
| Memory limit | **90g** (host headroom reserved for SSH) |

## Safety first

- **No auto-start** after reboot (`restart: "no"`)
- **Heavy confirmation** on `start`
- **Host free-memory headroom** checks
- **Bandwidth-limited** model downloads (`download-limit auto` = 85% of speedtest)

```mermaid
flowchart LR
  S1["restart: no"] --> S2["type yes on start"]
  S2 --> S3["RAM/disk headroom"]
  S3 --> S4["download-limit auto 85%"]
  S4 --> Safe["SSH stays usable"]
```

See [Reboot Safety](reboot-safety.md).

## Documentation map

```mermaid
flowchart LR
  Home["Home"] --> GS["Getting Started"]
  GS --> Vis["Visual Generative AI"]
  Vis --> Mod["Models & Cache"]
  Mod --> DL["Download Limit"]
  GS --> RS["Reboot Safety"]
  Vis --> TS["Troubleshooting"]
  DL --> TS
  RS --> TS
  Home --> Conv["Conventions"]
```

## Quick links

- [Getting Started](getting-started.md)
- [Visual Generative AI](visual-generative-ai.md)
- [Download Limit](download-limit.md)
- [Troubleshooting](troubleshooting.md)
