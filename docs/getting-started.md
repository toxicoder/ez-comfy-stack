---
title: Getting Started
description: Install prerequisites, download models, and start the unified ComfyUI flux-to-ltx stack on DGX Spark.
tags: [getting-started, docker, comfyui]
---

# Getting Started

**What's on this page**

- Prerequisites on the Spark host
- Environment setup
- Download models (throttled)
- Start / status / stop

**What this enables**

- A first successful open of ComfyUI at port 8188
- Safe downloads that leave bandwidth for SSH

## Prerequisites

- NVIDIA DGX Spark (or compatible GB10 host) with drivers + **NVIDIA Container Toolkit**
- Docker with Compose v2 plugin
- `git`, `python3`, `pip` (`huggingface_hub` for downloads)
- Optional: `wondershaper`, `speedtest-cli` (auto-installed / used by download-limit)
- Hugging Face account with licenses accepted for FLUX / LTX models; `HF_TOKEN` if gated

## Setup

```bash
git clone https://github.com/toxicoder/ez-comfy-stack.git
cd ez-comfy-stack
git checkout development   # or your feature branch
cp .env.example .env
# edit .env: HF_TOKEN, MODELS_DIR=/mnt/models
```

## Doctor

```bash
./scripts/manage.sh doctor
```

Fix any errors before downloading multi-GB models.

## Download models (shared cache)

```bash
./scripts/manage.sh download-models
```

This runs **flux-fast** + **ltx-balanced** under `download-limit wrap --limit auto` (speedtest → **85%** cap). Weights land under `MODELS_DIR` (default `/mnt/models`) in a layout compatible with nvidia-dgx-spark-lab.

## Start the stack

```bash
./scripts/manage.sh start
# type: yes
./scripts/manage.sh status
```

Open `http://<spark-ip>:8188` (or port-forward if needed).

!!! warning "Cold start"
    First container start installs ComfyUI into the `comfy-state` volume and can take **10–30+ minutes**.

## Stop (always before reboot)

```bash
./scripts/manage.sh stop
```

## Development tests

```bash
make test
make coverage
make docs
```
