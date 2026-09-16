---
title: Motion and AV catalog
description: Seeded Wan 2.2 silent ~5 s graphs, LTX-2.5 AV heroes, GIF/bumper loops, and creator motion plates.
tags: [comfyui, workflows, wan, ltx, motion, catalog]
---

# Motion and AV catalog

**What's on this page**

- **Motion (Wan 2.2 5B)** silent I2V / T2V, FLF, VACE, A14B, TRELLIS
- **AV hero (LTX-2.5)** I2V / T2V and the ÷32 size warning
- **Showcase (LTX-2.5)** dialogue, native multishot, product hero, first-last-frame, A2V freeze
- **Creator toolkit** motion and AV plates (orbit, bumper, B-roll, hook)

**What this enables**

- **Queuing a silent ~5 s clip** or an AV ~5 s hero from a seeded filename
- **Keeping LTX widgets** on the native VAE grid so prints do not snap-and-crop

**Who this is for:** studio users after a Klein still. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Unload the previous family before Queue. Outputs under `${COMFY_OUTPUT_DIR}`.

---

## Motion (Wan 2.2 5B)

| Workflow | What it does |
| --- | --- |
| **[wan/still-to-video-5s](../generated/workflows/wan/still-to-video-5s.md)** | Silent I2V smoke, 832×480, **121** frames @ 24 fps. MagCache **draft-only** (`extra.lab_magcache`) |
| **[wan/first-last-5s](../generated/workflows/wan/first-last-5s.md)** | Fun InP first-last-frame 5 s (opt-in `download-wan --tier fun-inp`). MagCache off |
| **[wan/vace-join](../generated/workflows/wan/vace-join.md)** | Wan 2.1 VACE 1.3B 17-frame join (`1+8n`). Opt-in `download-wan --tier vace`. MagCache off |
| **[optional/wan/still-to-video-a14b](../generated/workflows/optional/wan/still-to-video-a14b.md)** | Optional A14B FP8: high+low UNET on canvas, Queue on high-noise 8-step (`download-wan --tier a14b`). MagCache off. Unload 5B first. Under `_lab/optional/` |
| **[optional/klein/trellis2](../generated/workflows/optional/klein/trellis2.md)** | Klein still → native TRELLIS.2 INT8 mesh (512). `download-3d --tier trellis2`. `occupancy enter trellis`. Under `_lab/optional/` |
| **[optional/longcat-video](../generated/workflows/optional/longcat-video.md)** | LongCat-Video MIT stub (note, not a 90s default). `download-longcat --tier video`. No NCCL. Under `_lab/optional/` |
| **[wan/text-to-video-5s](../generated/workflows/wan/text-to-video-5s.md)** | Silent T2V smoke, 121 frames (LoadImage bypassed) |
| **[wan/still-to-shot](../generated/workflows/wan/still-to-shot.md)** | Concat-safe **120** frames + last-frame SaveImage. 90s shots, or prefix `ez_shot_01..06` |
| **[wan/gif-loop](../generated/workflows/wan/gif-loop.md)** | Wan 5B I2V GIF (49 frames @ 12 fps, ping-pong). Prefix `ez_gif_loop`. Occupancy **wan** |

---

## AV hero (LTX-2.5)

| Workflow | What it does |
| --- | --- |
| **[ltx/still-to-video-5s](../generated/workflows/ltx/still-to-video-5s.md)** | ~5 s I2V, **1280×704**, native audio (Community License, $10M cap) |
| **[ltx/text-to-video-5s](../generated/workflows/ltx/text-to-video-5s.md)** | ~5 s T2V AV, **1280×704** |

---

## Showcase (LTX-2.5)

Authored recipes. Prompt Enhance **off**. Occupancy **ltx**. Same 5.00 s / 121 / **1280×704** printer as the heroes. Two-stage DFR stays in Comfy **Templates → LTX-2.5**.

| Workflow | What it does |
| --- | --- |
| **[ltx/dialogue-5s](../generated/workflows/ltx/dialogue-5s.md)** | T2V with a quoted spoken line + interleaved foley. `LTXVModalityGuidance` (A/V coupling). Prefix `ez_ltx_dialogue`. Mouths will not match |
| **[ltx/multishot-5s](../generated/workflows/ltx/multishot-5s.md)** | Native multishot T2V: named hard cut + match cut in one 5 s clip. Prefix `ez_ltx_multishot` |
| **[ltx/product-hero](../generated/workflows/ltx/product-hero.md)** | I2V from **[klein/product-packshot](../generated/workflows/klein/product-packshot.md)** (`ez_packshot_*.png`). Slow orbit + table SFX. Prefix `ez_ltx_product` |
| **[ltx/first-last-5s](../generated/workflows/ltx/first-last-5s.md)** | First-last-frame AV. Two Klein stills pin start/end via `LTXVAddGuide` on the video latent (before audio concat). Prefix `ez_ltx_flf` |
| **[ltx/audio-to-video-5s](../generated/workflows/ltx/audio-to-video-5s.md)** | Audio freeze: `LoadAudio` → encode into the joint latent; MP4 muxes the **original** wav (no audio VAE decode). Prefix `ez_ltx_a2v`. Drop `ez_a2v_bed.wav` in `${COMFY_OUTPUT_DIR}/input` |

!!! warning "LTX width/height must be divisible by 32"

    Broadcast 720p (**1280×720**) and 1080p (**1920×1080**) are **not** native LTX VAE sizes (720/16=45, then the next `/2` patch fails). Lab landscape graphs use **1280×704**. Klein **I2V feeders** (`klein-still-hero`, 90s film identity) are **1280×704**. Thumbnails/end-cards may stay 1280×720. Typing 720 or 1080 on LTX widgets is **auto-snapped** (704 / 1056) by `ez_ltx_spatial` — prefer 704 so you skip the extra crop. Portrait shorts I2V is **768×1280**. See [Troubleshooting](../troubleshooting.md).

---

## Creator toolkit — motion / AV

Pack 1 motion / AV (stills companions: [Stills catalog](workflows-stills.md)):

| Workflow | What it does |
| --- | --- |
| **[wan/shorts-still-5s](../generated/workflows/wan/shorts-still-5s.md)** | Vertical silent I2V from that still |
| **[ltx/shorts-still-5s](../generated/workflows/ltx/shorts-still-5s.md)** | Vertical AV I2V (~5 s) with world audio |
| **[wan/bumper-loop](../generated/workflows/wan/bumper-loop.md)** | Loopable MP4 bumper (ping-pong) |
| **[ltx/broll-ambient](../generated/workflows/ltx/broll-ambient.md)** | Ambient B-roll AV plate (~5 s) |

Pack 2 — motion / AV:

| Workflow | What it does |
| --- | --- |
| **[wan/orbit-still-5s](../generated/workflows/wan/orbit-still-5s.md)** | Slow orbit I2V ~5 s |
| **[wan/push-in-still-5s](../generated/workflows/wan/push-in-still-5s.md)** | Hero push-in I2V ~5 s |
| **[wan/parallax-still-5s](../generated/workflows/wan/parallax-still-5s.md)** | Subtle parallax I2V ~5 s |
| **[wan/sticker-loop](../generated/workflows/wan/sticker-loop.md)** | Looping sticker MP4 |
| **[ltx/weather-broll](../generated/workflows/ltx/weather-broll.md)** | Rain / wind B-roll AV |
| **[ltx/interior-ambience](../generated/workflows/ltx/interior-ambience.md)** | Interior room-tone AV |
| **[ltx/hook-av](../generated/workflows/ltx/hook-av.md)** | ~5 s AV cold open |

90s shot printers (**[wan/still-to-shot](../generated/workflows/wan/still-to-shot.md)**, **[ltx/still-to-shot](../generated/workflows/ltx/still-to-shot.md)**) live with the films: [Film catalog](workflows-film.md).
