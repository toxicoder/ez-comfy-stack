---
title: ez-comfy-stack
description: Lean Visual Generative AI demo stack (ComfyUI US-safe local studio) for a single NVIDIA DGX Spark.
tags: [comfyui, klein, wan, ltx, dgx-spark, docker]
---

# ez-comfy-stack

**What's on this page**

- What this project is (and is not)
- Default stack and safety principles
- How pieces connect
- Where to read next

**What this enables**

- Spinning up a **US-safe local studio** (Klein 4B + Wan 2.2 + LTX-2.5) on one Spark quickly
- Sharing model weights with other stacks via `${MODELS_DIR}` (default `/mnt/models`)
- Operating the stack safely over SSH without locking yourself out

!!! tip "Start here"

    New to this repo? Follow **[Getting Started](getting-started.md)** for setup → doctor → download → start → first still → stop.

    Then: [Prompting](prompting.md) · [Model licenses](licenses.md) · studio playbook [Visual Generative AI](visual-generative-ai.md) · opt-in [Local podcast](podcast.md) · opt-in [Local music](music.md).

    Contributors: [Conventions](project-conventions.md).

---

## Purpose

This is a **sample / demo** repository for **Visual Generative AI** on a **single NVIDIA DGX Spark (GB10)**. It is deliberately smaller than [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab): Docker Compose instead of K3s, one unified profile instead of a full lab.

Long-term multi-workload operations should use the full lab project. Use **ez-comfy-stack** when you want faster experimentation.

### This stack vs the full lab

```mermaid
flowchart TB
  subgraph EZ["ez-comfy-stack"]
    direction TB
    E1["Docker Compose"]
    E2["One profile: us-safe-studio"]
    E3["manage.sh operator CLI"]
    E4["Shared MODELS_DIR"]
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

---

## Default stack

| Item | Value |
| --- | --- |
| Runtime | ComfyUI (Docker) |
| Pipeline | **studio** — Klein 4B still → Wan 2.2 5 s silent → LTX-2.5 AV ([licenses](licenses.md)) |
| Image tier | **fast** — FLUX.2 Klein 4B distilled FP8 (Apache) |
| Wan tier | **5b** — Wan 2.2 TI2V-5B (Apache, silent) |
| LTX tier | **2.5** — LTX-2.5 distilled INT8-convrot (Community License, gated) |
| Models | host `${MODELS_DIR}` (default `/mnt/models`) |
| Outputs | host `${COMFY_OUTPUT_DIR}` (default `/mnt/comfy-output`) |
| UI | port **`${COMFY_PORT}`** (default **8188**) |
| Memory limit | **90g** (host headroom reserved for SSH) |

Klein 9B, FLUX.2-dev, Nunchaku 9B, and MiniMax H3 are **not** defaults. Optional fallbacks (Z-Image, Wan A14B, LTX-2.3) are documented on [Models & Cache](models-and-cache.md). Opt-in audio: [Local podcast](podcast.md) (Kokoro + native ACE-Step) and [Local music](music.md) (rap-first ACE-Step; not part of `download-models`).

---

## Session variables

Set these once per SSH session (defaults match `.env.example`). Getting Started repeats them in the copy-paste path.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"          # LAN IP or DNS of this Spark
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"        # auto | off | integer Mbps
```

UI: `http://${SPARK_HOST}:${COMFY_PORT}`. From a laptop, port-forward first (see [Getting Started](getting-started.md)).

---

## Safety first

!!! warning "Remote Spark rules"

    These defaults protect SSH recoverability on a remotely managed host. Do not weaken them for demos.

| Guard | Behavior |
| --- | --- |
| **No auto-start** | Compose `restart: "no"` after reboot |
| **Heavy confirmation** | Type `yes` on `start` |
| **Headroom preflight** | Free host RAM/disk checked before start |
| **Download throttle** | `download-limit auto` = **85%** of speedtest (when HTB works) |

```mermaid
flowchart LR
  S1["restart: no"] --> S2["type yes on start"]
  S2 --> S3["RAM/disk headroom"]
  S3 --> S4["download-limit auto 85%"]
  S4 --> Safe["SSH stays usable"]
```

Details: [Reboot Safety](reboot-safety.md) · [Download Limit](download-limit.md).

---

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
    Models["MODELS_DIR<br/>shared cache"]
    Out["COMFY_OUTPUT_DIR<br/>PNG / MP4"]
  end
  UI["Browser · SPARK_HOST:COMFY_PORT"]

  Op --> SSH --> Manage
  Manage --> Compose --> Comfy
  Models -.->|bind mount| Comfy
  Out -.->|bind /outputs| Comfy
  Comfy --> UI
  Op --> UI
```

---

## Documentation path

| When | Read |
| --- | --- |
| **First run** | [Getting Started](getting-started.md) |
| **How to prompt Klein / Wan / LTX** | [Prompting](prompting.md) |
| **Licenses before a 30 GB pull** | [Model licenses](licenses.md) |
| **Still → silent 5 s → AV 5 s** | [Visual Generative AI](visual-generative-ai.md) |
| **90s films (first-person running go-see / still-here / switchyard)** | [90s shorts](shorts.md) |
| **Three Sparks, one weight copy** | [Spark farm](spark-farm.md) |
| **Weights, cache, image pins** | [Models & Cache](models-and-cache.md) |
| **Throttled downloads** | [Download Limit](download-limit.md) |
| **Before reboot** | [Reboot Safety](reboot-safety.md) |
| **Something broke** | [Troubleshooting](troubleshooting.md) |
| **Contributing** | [Conventions](project-conventions.md) |

```mermaid
flowchart TB
  Home["Home"] --> GS["Getting Started"]
  GS --> Prompt["Prompting"]
  GS --> Lic["Licenses"]
  GS --> Vis["Visual Generative AI"]
  Vis --> Shorts["90s shorts"]
  Shorts --> Farm["Spark farm"]
  GS --> Mod["Models & Cache"]
  Mod --> DL["Download Limit"]
  GS --> RS["Reboot Safety"]
  Vis --> TS["Troubleshooting"]
  DL --> TS
  RS --> TS
  Home --> Conv["Conventions"]
```
