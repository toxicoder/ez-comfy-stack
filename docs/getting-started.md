---
title: Getting Started
description: Install prerequisites, download models, and start the unified ComfyUI flux-to-ltx stack on DGX Spark.
tags: [getting-started, docker, comfyui]
---

# Getting Started

**What's on this page**

- What success looks like
- Prerequisites checklist
- Setup, doctor, download, start, stop
- Optional: build the Docker image locally instead of pulling GHCR
- Example workflows and optional deep-dives

**What this enables**

- A first successful open of ComfyUI at port **8188**
- Safe model downloads that leave bandwidth for SSH
- Choosing prebuilt GHCR pull (default) or a local Dockerfile build

---

## You will end here

| Goal | Detail |
| --- | --- |
| **UI** | ComfyUI at `http://<spark-ip>:8188` |
| **Workflow** | A seeded **lab-*** graph (image and/or video frames) |
| **Weights** | Flux **fast** + LTX **balanced** under `MODELS_DIR` (default `/mnt/models`) |

**Expect** multi‑GB Hugging Face pulls (throttled by default). First start usually **seeds** from a prebuilt GHCR image; without that image, cold pip can take **10–30+ minutes**.

---

## Path at a glance

1. **Clone** this repo (branch that matches these docs)
2. **`setup`** — `.env`, model dir, Docker if needed
3. **`doctor`** — fix hard failures before multi‑GB downloads
4. **`download-models`** — flux-fast + ltx-balanced (throttled)
5. **`start`** — type `yes`, then open **:8188**
6. **`stop`** — always, before reboot

```bash
git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
cd ez-comfy-stack
./scripts/manage.sh setup --install-docker   # approve sudo; edit .env for HF_TOKEN if gated
./scripts/manage.sh doctor
./scripts/manage.sh download-models
./scripts/manage.sh start                    # type: yes
./scripts/manage.sh status
# open http://<spark-ip>:8188
./scripts/manage.sh stop                     # before reboot
```

Sections below unpack each step. Feature work still branches from `development` (see [Conventions](project-conventions.md)).

---

## Prerequisites

### Checklist

- [ ] **NVIDIA DGX Spark** (or compatible GB10) with drivers + **NVIDIA Container Toolkit**
- [ ] **Docker** with Compose v2 (prefer apt `docker-ce`, not snap; user in `docker` group)
- [ ] **Writable model cache** — default `/mnt/models`, or set `MODELS_DIR` in `.env`
- [ ] **git**, **python3**, **pip** / **pipx**
- [ ] **Hugging Face CLI** — modern `hf` from `huggingface_hub` (**not** the deprecated `huggingface-cli` stub)
- [ ] **HF account** — licenses accepted for FLUX / LTX; `HF_TOKEN` in `.env` or `hf auth login` if gated

### At a glance

| Kind | Items |
| --- | --- |
| **Required on host** | NVIDIA drivers, Container Toolkit, Docker + Compose v2, git, python3, pip/pipx |
| **Optional / auto** | `wondershaper`, `speedtest-cli` (used by download-limit; HTB/`sch_htb` when shaping is available) |
| **Accounts** | HF licenses + `HF_TOKEN` for gated models |
| **Image base** | Public Docker Hub `nvidia/cuda` — **no** NGC / `nvcr.io` login required |

```bash
# Model cache (or let setup create it)
sudo mkdir -p /mnt/models && sudo chown "$USER:$USER" /mnt/models

# HF CLI
command -v hf || pipx install huggingface_hub
# or: pip install -U 'huggingface_hub[cli]'
```

```mermaid
flowchart LR
  subgraph Required["Required on host"]
    Drv["NVIDIA drivers"]
    CTK["NVIDIA Container Toolkit"]
    Dock["Docker + Compose v2"]
    Git["git · python3 · pip"]
  end
  subgraph Optional["Optional / auto"]
    WS["wondershaper"]
    ST["speedtest-cli"]
  end
  subgraph Accounts["Accounts"]
    HF["HF licenses + HF_TOKEN"]
  end
  Required --> Ready["Ready for doctor"]
  Optional --> Ready
  Accounts --> Ready
```

---

## Setup

Clone the **same long-lived branch these docs describe** (`main` for [latest](https://toxicoder.github.io/ez-comfy-stack/latest/), `development` for [development](https://toxicoder.github.io/ez-comfy-stack/development/)).

=== "Interactive"

    ```bash
    git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
    cd ez-comfy-stack

    # One-shot host bootstrap: .env, MODELS_DIR (sudo), Docker CE if missing, doctor
    ./scripts/manage.sh setup --install-docker
    # approve sudo + type yes if prompted; edit .env for HF_TOKEN if models are gated
    ```

=== "Non-interactive"

    ```bash
    git clone -b __DOCS_GIT_REF__ https://github.com/toxicoder/ez-comfy-stack.git
    cd ez-comfy-stack

    LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes SETUP_INSTALL_DOCKER=1 \
      ./scripts/manage.sh setup
    ```

`setup` will:

1. Create `.env` from `.env.example` if missing
2. Create and own `MODELS_DIR` (default `/mnt/models`) via sudo when needed
3. **Install Docker CE + compose plugin** when missing (`--install-docker` or interactive yes; apt preferred, not snap)
4. Add your user to the `docker` group; configure `nvidia-ctk` when present
5. Re-run `doctor`

??? tip "Docker group not active in this shell"

    After install, if `docker` permission is denied:

    ```bash
    newgrp docker   # or re-login SSH
    ./scripts/manage.sh doctor
    ```

---

## Doctor

```bash
./scripts/manage.sh doctor
```

Fix any errors **before** downloading multi‑GB models.

!!! warning "Hard failures to clear first"

    - **docker missing**
    - **docker compose missing**
    - **host headroom** (RAM/disk)
    - **MODELS_DIR not writable**

    Prefer `./scripts/manage.sh setup` first. Copy-paste fixes: [Troubleshooting](troubleshooting.md).

---

## Download models

```bash
# Ensure HF token for gated repos (FLUX):
# echo 'HF_TOKEN=hf_...' >> .env   # or: hf auth login

./scripts/manage.sh download-models
```

| What | Detail |
| --- | --- |
| **Tiers** | **flux-fast** + **ltx-balanced** |
| **Throttle** | `download-limit wrap --limit auto` → speedtest → **85%** cap (when HTB works) |
| **CLI** | Modern **`hf download`** |
| **Layout** | Weights under `MODELS_DIR` (default `/mnt/models`), compatible with nvidia-dgx-spark-lab |
| **LTX size** | Selective subset of `Kijai/LTX2.3_comfy` (~**30 GB**), not the full monorepo (~400 GB) |

`download-models` **exits non-zero** until every lab basename is present under `MODELS_DIR/comfy/` (Flux UNET + Qwen TE + `flux2-vae` + LTX distilled FP8 + text projection + video/audio VAEs).

!!! tip "Bandwidth shaping soft-fail"

    If kernel HTB is missing (common on DGX Spark), downloads continue with gentle HF workers and a warning. Use `DOWNLOAD_LIMIT=off` only when you accept SSH risk. See [Download Limit](download-limit.md).

If Comfy shows **Missing Models** on **lab-*** graphs, re-run download and `doctor`. Full basename table: [Models & Cache](models-and-cache.md).

---

## Start the stack

```bash
./scripts/manage.sh start
# type: yes
./scripts/manage.sh status
```

Open **`http://<spark-ip>:8188`** (or SSH port-forward if needed).

!!! success "Done when"

    Port **8188** responds and you can load a **lab-*** workflow without missing-weight errors.

### Build the image locally (optional)

By default, `manage.sh start` **pulls** a branch-aligned prebuilt image from GHCR (ComfyUI + PyTorch baked in; **not** FLUX/LTX weights). You can instead **build** `docker/Dockerfile` on the host and still use the same start path.

=== "One-shot env"

    ```bash
    LAB_STACK_FORCE_BUILD=1 ./scripts/manage.sh start
    # type: yes
    ```

=== "Persist in .env"

    ```bash
    # in .env (see .env.example)
    LAB_STACK_FORCE_BUILD=1

    ./scripts/manage.sh start
    # type: yes
    ```

| When to use local build | When to stick with GHCR pull |
| --- | --- |
| GHCR tag missing, private, or pull denied | Normal first install / fastest path |
| Rebaking `/opt/comfy-prebuilt` after pin or phase changes | Ops-script-only edits (entrypoint / install / patch) |
| Developing the image layers themselves | You only need Comfy + weights running |

**Still the same safety path:** type `yes`, host headroom preflight, `restart: "no"`, and weights via `download-models` / `MODELS_DIR`. Local build does **not** skip confirmation or put models inside the image.

!!! warning "Expect a long Docker build"

    With default `EZ_COMFY_PREBUILD=1`, local build installs torch and Comfy into the image and can take **30+ minutes** (multi‑GB wheels). Base layers come from public Docker Hub `nvidia/cuda` (no NGC login by default). Compose may use a previously pulled GHCR image as build cache (`cache_from`) when present.

After a successful prebuild image, first container start **seeds** the `comfy-state` volume from `/opt/comfy-prebuilt` (same as the GHCR path). A thin build (`EZ_COMFY_PREBUILD=0`) or `LAB_FORCE_COLD_INSTALL=1` falls back to cold multi‑GB pip at runtime.

| Variable | Role |
| --- | --- |
| `LAB_STACK_FORCE_BUILD=1` | Prefer local `compose up --build` (skip pull-first path) |
| `LAB_STACK_SKIP_PULL=1` | Do not `docker pull`; start falls through to local `compose --build` |
| `EZ_COMFY_PREBUILD=1` (default) | Bake Comfy + torch into the image during build |
| `EZ_COMFY_PREBUILD=0` | Thin image → cold pip at first container start |
| `EZ_COMFY_IMAGE` | Tag for the pulled or built image (branch default if unset) |

Pull failures already fall back to local build automatically. Force-build is for when you **want** a rebuild even if GHCR is available.

Layer invalidation and pin bumps: [Models & Cache](models-and-cache.md#prebuilt-container-image-ghcr). Recovery rows: [Troubleshooting](troubleshooting.md).

### Example workflows

After `download-models` + `start`, open ComfyUI and load from `user/default/workflows/` (seeded from host `workflows/`):

=== "Image (Flux)"

    | Workflow | What it does |
    | --- | --- |
    | **lab-flux-txt2img** | Text → image 1024² (Flux.2 Klein NVFP4 + Qwen TE + flux2 VAE) |
    | **lab-flux-txt2img-portrait** | Text → image **768×1024** portrait |
    | **lab-flux-txt2img-landscape** | Text → image **1280×720** landscape |
    | **lab-flux-txt2img-quick** | Smoke test: **768²**, **4** steps |
    | **lab-flux-img2img** | Image → image (set LoadImage input) |

=== "Video frames (LTX)"

    | Workflow | What it does |
    | --- | --- |
    | **lab-ltx-i2v** | Image → video frames (~97 @ 24 fps; set start frame) |
    | **lab-ltx-i2v-short** | Faster I2V: **33** frames @ 24 fps |
    | **lab-ltx-t2v** | Text → video frames (~97 @ 24 fps) |
    | **lab-ltx-t2v-short** | Faster T2V: **33** frames @ 24 fps |

=== "Combined"

    | Workflow | What it does |
    | --- | --- |
    | **lab-flux-to-ltx** | Flux txt2img + handoff notes → load **lab-ltx-i2v** for video frames |

??? abstract "Lab workflow details"

    - Flux CLIP loader type is **`flux2`** with `qwen_3_8b_fp4mixed` + `EmptyFlux2LatentImage` (simplified `KSampler`, not the full official advanced sampler subgraph)
    - LTX graphs save **frames** via `SaveImage` (no VideoHelperSuite / VHS required)
    - `download-models` also places `LTX23_audio_vae_bf16` for advanced AV experiments; **lab examples do not wire audio**
    - Lab graphs use **core** loaders only (not ComfyUI-nunchaku). Nunchaku import warnings on aarch64 are optional and do not block examples
    - **Not Z-Image.** Community Z-Image templates need different weights (`ae` / `qwen_3_4b` / `z_image_turbo_*`)

---

## Stop (always before reboot)

!!! danger "Golden rule"

    **Never reboot with the heavy ComfyUI stack still running.** Always stop first. See [Reboot Safety](reboot-safety.md).

```bash
./scripts/manage.sh stop
```

---

## Optional deep-dives

??? tip "Prebuilt image (GHCR)"

    `manage.sh start` pulls a **branch-aligned** arm64 image published by the `publish-image` workflow:

    | Git branch | Image tag |
    | --- | --- |
    | `main` | `ghcr.io/toxicoder/ez-comfy:flux-to-ltx` |
    | `development` (and feature branches) | `ghcr.io/toxicoder/ez-comfy:flux-to-ltx-development` |

    Override with `EZ_COMFY_IMAGE` in `.env` if needed.

    Multi-stage: **devel** builder installs Comfy+torch in **phased modules** (torch separate from custom nodes); final stage is **CUDA runtime** (no nvcc) with **split layers** (venv vs app) so pulls reuse multi‑GB torch when only app bits change.

    It includes ComfyUI + PyTorch (pinned refs — see [Models & Cache](models-and-cache.md#prebuild-version-pins-validated)); **not** FLUX/LTX weights (those stay on `MODELS_DIR`).

    First start **seeds** the volume from `/opt/comfy-prebuilt` (local copy) instead of multi‑GB pip.

    No tokens or host secrets are baked into the image. Pull is public for public packages.

    `./scripts/manage.sh doctor` prints the resolved default image before you start.

??? tip "Dev: edit scripts without rebuilding"

    Compose bind-mounts `docker/entrypoint.sh`, `docker/install-comfy.sh`, `docker/install-comfy/`, and `docker/patch_get_free_memory.py` into the container.

    Change those files on the host, then restart the stack — **no multi‑GB image rebuild**.

    Rebuild only when you need a new baked `/opt/comfy-prebuilt` tree (torch / Comfy / nodes): [build the image locally](getting-started.md#build-the-image-locally-optional) or publish.

    See [Models & Cache](models-and-cache.md#image-layer-cache-high-velocity-rebuilds-pulls) for what invalidates which layers.

??? warning "Cold start without prebuilt"

    If GHCR pull fails or you force a thin/local build without prebuild, first start can take **10–30+ minutes** of pip.

    `manage.sh start` streams logs until port 8188 responds (++ctrl+c++ detaches only).

    `LAB_STACK_FOLLOW=0` returns immediately after the container is up.

??? abstract "First-run journey (sequence)"

    ```mermaid
    sequenceDiagram
      actor Op as Operator
      participant M as manage.sh
      participant DL as download-limit
      participant HF as Hugging Face
      participant D as Docker / ComfyUI
      participant B as Browser

      Op->>M: clone + setup
      Op->>M: doctor
      M-->>Op: preflight OK
      Op->>M: download-models
      M->>DL: wrap --limit auto
      DL->>HF: throttled pull (flux-fast + ltx-balanced)
      HF-->>DL: weights → MODELS_DIR
      DL-->>M: clear limit on exit
      Op->>M: start
      M-->>Op: type yes
      Op->>M: yes
      M->>D: compose up -d
      D-->>Op: seed prebuilt or cold install
      Op->>B: open :8188
      Op->>M: stop (before reboot)
    ```

??? abstract "Cold-start phases (first start without prebuilt)"

    ```mermaid
    flowchart TB
      A["manage.sh start<br/>type yes"] --> B["Docker build image<br/>ez-comfy:flux-to-ltx"]
      B --> C["Create volume comfy-state"]
      C --> D["entrypoint: install-comfy.sh<br/>pip + git · 10–30+ min"]
      D --> E["patch_get_free_memory.py"]
      E --> F["Exec ComfyUI on 0.0.0.0:8188"]
      F --> G["UI ready"]
    ```

---

## Next steps

| Need | Page |
| --- | --- |
| Pipeline architecture & memory budget | [Visual Generative AI](visual-generative-ai.md) |
| Cache layout, basenames, layer pins | [Models & Cache](models-and-cache.md) |
| Bandwidth throttle details | [Download Limit](download-limit.md) |
| Reboot / recovery | [Reboot Safety](reboot-safety.md) |
| Symptom → fix | [Troubleshooting](troubleshooting.md) |
| Contributing / shell style | [Conventions](project-conventions.md) |
