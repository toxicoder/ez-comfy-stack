---
title: ComfyUI Apps
description: App Mode surfaces for the US-safe studio — Lane A Inspire vs Lane B Produce, occupancy, and handoff chains.
tags: [comfyui, app-mode, workflows, occupancy, klein, wan, ltx]
---

# ComfyUI Apps

**What's on this page**

- How App Mode relates to the node graph
- Occupancy (one GB10 job)
- Lane A (Inspire) vs Lane B (Produce)
- Handoff chains (still → motion → AV)

**What this enables**

- Queueing a lab graph from creator widgets instead of hunting the canvas
- Knowing which App to stop before you load the next one
- Following Spark Still → Hero → Silent 5s → AV 5s without renaming files

**Who this is for:** studio users after `klein-still-draft-lab-example` has been loaded once.

Lab graphs are still the same `*-lab-example.json` files. [App Mode](learn/comfyui.md#graph-and-app) is a widget surface on that JSON (ComfyUI frontend **1.41.13+**). It is **not** a second frontend and not `studio-ui`.

```mermaid
flowchart LR
  Load["Load *-lab-example"] --> App["App Mode widgets"]
  App --> Queue["Queue"]
  Queue --> Out["PNG / MP4"]
  App --> Graph["Graph view to inspect"]
```

---

## Graph vs App

| Surface | What you edit | When |
| --- | --- | --- |
| **App** | Prompt, Enhance, style, seed, size, LoadImage | Daily Queue |
| **Graph** | Groups, bypass (Ctrl+B), VHS preview, UNET/CLIP/VAE | Debug, film one-click, unused plates |

Official persist is `extra.linearData` (`inputs` / `outputs`). The lab contract is `extra.lab_app_mode` (`lane`, `occupancy`, `handoff`, `frontend_min`). Do not require `extra.linearMode` — upstream does not write it.

90s film graphs stay `default_view: graph` (too many widgets) but App Mode is still **enabled**.

Filenames: [Workflow catalog](studio-workflows.md). Playbook: [Still to motion to AV](visual-generative-ai.md).

---

## Occupancy

One GB10 job. Cover art ≠ film ≠ podcast. Every App Note includes a one-line occupancy stanza.

| Occupancy | Allowed | Must be stopped |
| --- | --- | --- |
| `none` / `llm` | Prompt Forge, Beat Sheet | nothing GPU |
| `klein` | still Apps + Platform Pack | Wan, LTX, podcast, music |
| `wan` | silent 5 s / GIF / bumper | LTX, podcast, music |
| `ltx` | any AV 5 s | Wan, podcast, music, other LTX |
| `film` | 90 s one-click | everything else on that Spark |
| `audio` | podcast / rap | Klein / Wan / LTX session |

Prompt Enhance GGUF stays CPU-only (`n_gpu_layers=0`). Sidecar occupancy (Comfy XOR Blender) is unchanged: [Studio sidecars](studio-sidecars.md).

---

## Lane A — Inspire

Explore identity, cameras, and world bibles. Occupancy **klein** unless noted.

| App | What it does |
| --- | --- |
| **klein-still-draft-lab-example** | Spark Still. 768×432, seed 42, Enhance on. Prefix `ez_still_draft` |
| **klein-identity-sheet-lab-example** | Front / three-quarter / profile. 1280×704, Enhance on (identity mode) |
| **klein-storyboard-6up-lab-example** | Six new cameras of one rooftop (`ez_board_01`…`06`) |
| **klein-dream-house-lab-example** | World bible. Ten 4:5 stills of one wizard penthouse, independent T2I, identity-mode enhance on the bible |
| **klein-style-lock-lab-example** | One penthouse, four cameras, locked inventory |
| **klein-lighting-trio-lab-example** | Same subject, three lights |
| **klein-camera-angles-lab-example** | Wide / medium / close |
| **klein-color-moods-lab-example** | Warm plate plus three grades |
| **klein-time-of-day-lab-example** | Dusk plate, then dawn / noon / night |
| **klein-hook-still-lab-example** | Vertical 9:16 first-frame hook (`ez_hook_still`) |
| **prompt-forge-lab-example** | No UNET. Klein + Wan + LTX enhance preview. Occupancy **llm** (CPU GGUF) |
| **beat-sheet-lab-example** | No UNET. 6×3 STRING cards; paste into `workflows/shorts/<slug>.shots.yaml`. Occupancy **none** |

---

## Lane B — Produce

Ship plates and ~5 s clips. Hide UNET/CLIP/VAE except **klein-still-daily** (swap table).

| App | Occupancy | Prefix / output |
| --- | --- | --- |
| **klein-still-daily-lab-example** | klein | `ez_still_app` — click UNET to swap distilled / NVFP4 / base |
| **klein-still-hero-lab-example** | klein | `ez_still_hero` — 1280×704 LTX feeder |
| **klein-thumbnail-lab-example** | klein | `ez_thumbnail` 1280×720 |
| **klein-ig-square-lab-example** | klein | `ez_ig_square` 1:1 |
| **klein-og-blog-lab-example** | klein | `ez_og` 1216×640 |
| **klein-banner-wide-lab-example** | klein | `ez_banner` ~3:1 |
| **klein-shorts-still-lab-example** | klein | `ez_shorts_still` 432×768 |
| **wan-i2v-5s-lab-example** | wan | Silent 5 s, 121 frames, MagCache draft-only |
| **wan-gif-loop-lab-example** | wan | 49-frame ping-pong GIF |
| **ltx-i2v-5s-lab-example** | ltx | AV 5 s, 1280×704 |
| **ltx-hook-av-lab-example** | ltx | AV cold open |
| **klein-platform-pack-lab-example** | klein | Six plates from one identity (`ez_pack_thumb` / ig / portrait / shorts / og / banner). Ctrl+B unused groups |

Creator plates (packshot, end-card, quote, food, bumper, B-roll, orbit, …) stay in the [catalog](studio-workflows.md). Klein stills may use 1280×720; LTX feeders stay **1280×704**.

Audio Apps (`podcast-*`, `music-rap-*`) are occupancy **audio**. Film `film-*-90s-*-lab-example` is occupancy **film**. DCC: [DCC guide pack](dcc-workflows.md).

---

## Handoff chains

| From | To |
| --- | --- |
| Spark Still | Hero Still → Silent 5s (`wan-i2v-5s`) → AV 5s (`ltx-i2v-5s`) |
| Spark Still | Platform Pack (`klein-platform-pack`) → Silent 5s / Hook AV |
| Hook Still | `wan-shorts-i2v` → `ltx-shorts-i2v` |
| Storyboard 6-up | `wan-i2v-shot` / `ltx-i2v-shot` |
| World bible (dream-house) | Loop kit (GIF / bumper / sticker) |

Set I2V **LoadImage** to the still prefix you just saved (`ez_still_draft_*.png`, `ez_hook_still_*.png`, …). I2V graphs also Queue on Comfy’s `example.png`.

Do **not** Queue Wan and LTX in the same session. Stop the other occupancy first.

!!! warning "Do not weaken"

    `restart: "no"`, type **yes** on start, headroom, and download-limit are unchanged. Apps do not add `workflows/apps/` or seed `workflows/optional/`.
