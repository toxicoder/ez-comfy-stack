---
title: Visual Generative AI
description: Architecture of the unified Flux → LTX ComfyUI stack on DGX Spark unified memory.
tags: [comfyui, flux, ltx, visual, nvfp4]
---

# Visual Generative AI

**What's on this page**

- Architecture and resource profile (with diagrams)
- Flux → LTX pipeline
- Spark unified-memory patch and entrypoint sequence
- Operator commands

**What this enables**

- Running image + video generation tools in **one** Docker Compose stack
- Understanding why memory headroom and the free-memory patch matter on GB10

!!! tip "First run?"

    For install and first UI open, use [Getting Started](getting-started.md). This page explains **how the stack is wired**.

---

## Architecture

Host operator path, container lifecycle, mounts, and UI:

```mermaid
flowchart TB
  subgraph Host["DGX Spark host"]
    CLI["manage.sh"]
    Compose["Docker Compose<br/>project: ez-comfy<br/>restart: no"]
    Models["MODELS_DIR<br/>/mnt/models"]
    Policy["config/resource-policy.yaml<br/>headroom · mem limits"]
  end

  subgraph Ctr["Container: ez-comfy-studio"]
    EP["entrypoint.sh"]
    Install["install-comfy.sh"]
    Patch["patch_get_free_memory.py"]
    Comfy["ComfyUI"]
    EP --> Install --> Patch --> Comfy
  end

  Vol["named volume<br/>comfy-state"]
  WF["workflows/*.json + shorts/<br/>lab examples"]
  GPU["GPU · all · 1× GB10"]
  UI["UI :8188"]

  CLI --> Compose
  Compose --> EP
  Models -.->|bind /models| Ctr
  Vol -.->|/comfy-state| Ctr
  WF -.->|ro workflows| Ctr
  GPU --> Comfy
  Comfy --> UI
  Policy -.->|mirrored defaults| CLI
```

| Setting | Value |
| --- | --- |
| Profile | `us-safe-studio` |
| Memory limit / reservation | 90g / 80g |
| GPU | all (1× GB10) |
| restart | `"no"` |
| Flux | Klein 9B NVFP4 + Nunchaku |
| LTX | distilled FP8 balanced + Gemma DualCLIP |

---

## Combined pipeline (Flux → LTX)

Text → image → **video frames** in one ComfyUI stack. Lab graphs use `SaveImage` for frames. LTX-2.3 is a **joint audio/video** transformer: seeded LTX graphs load the **audio VAE**, create matching empty audio latents, and concat them with video latents before `KSampler` (audio is not saved). LTX text conditioning uses **DualCLIPLoader** (`gemma_3_12B_it_fp4_mixed` + `ltx-2.3_text_projection_bf16`, type **`ltxv`**) — not the projection file alone.

MiniMax H3 is **not** in this stack (US Excluded Territory). See [Model licenses](licenses.md).

```mermaid
flowchart LR
  Prompt["Text prompt"] --> Flux["Flux T2I<br/>fast · Klein 9B NVFP4"]
  Flux --> Image["Still image"]
  Image --> LTX["LTX I2V<br/>balanced · distilled FP8"]
  LTX --> Frames["Video frames<br/>SaveImage"]
  LTX --> Mp4["MP4 preview<br/>VHS_VideoCombine"]
```

**Handoff:** load **still-draft-lab-example** → Queue → set **wan-i2v-draft-lab-example** LoadImage to `ez_still_draft_*.png` → Queue 5 s silent → optional **ltx-i2v-hero-lab-example** for native audio. I2V graphs also Queue on Comfy’s default **example.png**. See [Getting Started — iteration loop](getting-started.md#iteration-loop-youtube-169).

!!! example "Pipeline tips"

    1. Download **flux fast** + **ltx balanced** first
    2. Prefer keeping both model sets loaded between T2I and I2V
    3. Avoid concurrent large LLM containers on the same Spark
    4. LTX lab graphs emit **MP4** via **VideoHelperSuite** (`VHS_VideoCombine`, 24 fps) plus optional PNG frames — see [Getting Started → Watch the video](getting-started.md#watch-the-video-ltx)
    5. Prompting: Klein wants Qwen-style prose (subject → light → camera); Wan wants motion + one camera move (no audio); LTX wants a present-tense paragraph with sound interleaved. See [Prompting](prompting.md). Every **\*-lab-example** canvas has an operator **Note**

---

## Memory and headroom budget

GB10 unified memory is shared by OS, SSH, Docker, and the ComfyUI container. Policy defaults leave free host RAM so remote access stays usable.

```mermaid
flowchart TB
  subgraph UM["~128 GiB unified memory (GB10)"]
    direction TB
    OS["OS + Docker daemon + interactive SSH"]
    Free["min_host_free_gib ≥ 28<br/>required before start"]
    Cont["Container mem_limit 90g<br/>mem_reservation 80g"]
  end
  Free --> Gate{"doctor / start<br/>headroom OK?"}
  Gate -->|yes| Cont
  Gate -->|no| Refuse["start refused"]
```

---

## Spark optimizations

| Setting | Purpose |
| --- | --- |
| `patch_get_free_memory.py` | Use host free RAM instead of under-reporting `cudaMemGetInfo` |
| `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | Less allocator fragmentation |
| `LAB_VISUAL_ENABLE_NVFP4=1` | Hint for NVFP4 / Nunchaku paths |
| Fail-soft Nunchaku / SageAttention | aarch64 wheels may be missing |

### Container entrypoint sequence

```mermaid
sequenceDiagram
  participant C as compose up
  participant E as entrypoint.sh
  participant I as install-comfy.sh
  participant P as patch_get_free_memory.py
  participant U as ComfyUI

  C->>E: start container
  E->>I: idempotent install / refresh
  I-->>E: COMFY_HOME + venv ready
  E->>P: re-apply Spark free-memory patch
  P-->>E: patched (fail-soft)
  E->>U: exec listen 0.0.0.0:8188
  Note over U: First cold start can take 10–30+ minutes
```

---

## Commands

| Step | Command |
| --- | --- |
| 1. Preflight | `./scripts/manage.sh doctor` |
| 2. Weights | `./scripts/manage.sh download-models` |
| 3. Start | `./scripts/manage.sh start` (type `yes`) |
| 4. Observe | `./scripts/manage.sh status` · `logs` |
| 5. Stop | `./scripts/manage.sh stop` |

```bash
./scripts/manage.sh doctor
./scripts/manage.sh download-models
./scripts/manage.sh start
./scripts/manage.sh status
./scripts/manage.sh logs
./scripts/manage.sh stop
```

```mermaid
flowchart LR
  Doctor["doctor"] --> Download["download-models"]
  Download --> Start["start"]
  Start --> Status["status"]
  Status --> Logs["logs"]
  Logs --> Stop["stop"]
  Start --> Cleanup["cleanup<br/>DELETE volume only"]
```

---

## Safety

!!! warning "Do not weaken"

    - Manual start only (`restart: "no"`)
    - Headroom preflight before start
    - Exclusive use of the GPU for this demo stack
    - Always `stop` before reboot — [Reboot Safety](reboot-safety.md)
