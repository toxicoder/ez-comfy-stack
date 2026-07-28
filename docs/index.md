---
title: ez-comfy-stack
description: Lean Visual Generative AI demo stack (ComfyUI flux-to-ltx) for a single NVIDIA DGX Spark.
tags: [comfyui, flux, ltx, dgx-spark, docker]
---

# ez-comfy-stack

**What's on this page**

- What this project is (and is not)
- Safety principles for remote DGX Spark access
- High-level layout and next links

**What this enables**

- Spinning up a **unified Flux → LTX** ComfyUI demo on one Spark quickly
- Sharing model weights with other stacks via `/mnt/models`
- Operating the stack safely over SSH without locking yourself out

## Purpose

This is a **sample / demo** repository for **Visual Generative AI** on a **single NVIDIA DGX Spark (GB10)**. It is deliberately smaller than [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab): Docker Compose instead of K3s, one unified profile instead of a full lab.

Long-term multi-workload operations should use the full lab project. Use **ez-comfy-stack** when you want faster experimentation.

## Default stack

| Item | Value |
| --- | --- |
| Runtime | ComfyUI (Docker) |
| Pipeline | **flux-to-ltx** (text → image → video + audio) |
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

See [Reboot Safety](reboot-safety.md).

## Quick links

- [Getting Started](getting-started.md)
- [Visual Generative AI](visual-generative-ai.md)
- [Download Limit](download-limit.md)
- [Troubleshooting](troubleshooting.md)
