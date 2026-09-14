---
title: Stills catalog (Klein 4B)
description: Seeded Klein 4B stills, identity sheets, Apps Lane A Klein, and creator plates.
tags: [comfyui, workflows, klein, stills, catalog]
---

# Stills catalog (Klein 4B)

**What's on this page**

- **Still (Klein 4B)** draft, hero, identity, and character graphs
- **Creator toolkit** stills and plates
- **Apps Lane A** Klein stills (Spark Still, dream-house, hook, character)

**What this enables**

- **Queuing a Klein still** from a seeded filename instead of a blank canvas
- **Locking identity and plates** before Wan / LTX motion

**Who this is for:** studio users after the first still-draft Queue. Index: [Workflow catalog](../studio-workflows.md). Occupancy **klein**. Outputs under `${COMFY_OUTPUT_DIR}`.

---

## Still (Klein 4B)

| Workflow | What it does |
| --- | --- |
| **klein/still-draft** | Apache Klein 4B distilled, **768×432**, **4** steps, batch 2, prefix `ez_still_draft` |
| **klein/still-hero** | Same prompt + seed, **1280×704** (LTX VAE grid), more steps, prefix `ez_still_hero`. Enhance **on**. |
| **klein/identity-sheet** | 3-angle sheet (front / three-quarter / profile) of the identity you type. Seed **42**, Enhance **on** (identity mode), **1280×704** |
| **klein/character-draft** | Character still 1024×1280, style dropdown, prefix `ez_character` |
| **klein/character-tweak** | Klein-edit that still (LoadImage + ReferenceLatent), prefix `ez_character_tweak` |
| **klein/talking-head** | Klein still → LTX A2V freeze smoke. Qwen3-TTS / Wan S2V opt-in. No banned lip-sync OSS |

Lane B Klein stills (same occupancy **klein**):

| Workflow | Occupancy | What it does |
| --- | --- | --- |
| **klein/still-daily** | klein | Daily still. Click UNET to swap distilled / NVFP4 / base. Prefix `ez_still_app` |
| **klein/platform-pack** | klein | Six plates, one identity (`ez_pack_*`). Independent T2I; Ctrl+B unused groups |

---

## Apps Lane A — Klein stills

App Mode (frontend **1.41.13+**) is a widget surface on the same lab JSON. Occupancy and handoff: [ComfyUI Apps](../studio-apps.md). Inspire (no UNET) stays on the [catalog index](../studio-workflows.md#inspire-lane-a).

| Workflow | What it does |
| --- | --- |
| **klein/still-draft** | Spark Still. 768×432, Enhance on. Prefix `ez_still_draft` |
| **klein/identity-sheet** | 3-angle sheet of the identity you type, seed **42**, **1280×704** |
| **klein/storyboard-6up** | Six new cameras of one scene (`ez_board_01`…`06`) |
| **klein/dream-house** | World bible. Ten Instagram 4:5 stills: virtual tour of one place (tower, foyer, rooms, terrace, drone, study) |
| **klein/dream-house-clay** | Same tour as Klein **edit** of clay (`ez_house_clay_01`…`10`). `start` seeds plates; optional `house-views` dump. Prefix `ez_dream_house_clay_*` |
| **klein/character-draft** | Character still, 1024×1280, style dropdown, prefix `ez_character` |
| **klein/character-tweak** | Edit `ez_character_*.png` with a change prompt (ReferenceLatent) |
| **klein/hook-still** | Vertical 9:16 hook still |

---

## Creator toolkit — stills and plates

Pack 1 stills (motion/AV companions: [Motion catalog](workflows-motion.md)):

| Workflow | What it does |
| --- | --- |
| **klein/shorts-still** | Vertical 9:16 Shorts still (`ez_shorts_still`) |
| **klein/thumbnail** | YouTube thumbnail still 1280×720 |
| **klein/product-packshot** | Clean product packshot 1:1 |
| **klein/before-after** | Before plate, after Klein-edit of the same mug |
| **klein/style-lock** | One penthouse, four cameras, locked inventory |
| **klein/storyboard-6up** | Six storyboard frames of one rooftop from new cameras |

Pack 2 — stills and plates:

| Workflow | What it does |
| --- | --- |
| **klein/endcard-cta** | End-card / CTA plate 16:9 |
| **klein/quote-bg** | Quote-card background 1:1 |
| **klein/og-blog** | Blog / Open Graph hero |
| **klein/podcast-cover** | Podcast cover 1:1 |
| **klein/banner-wide** | Channel / LinkedIn banner ~3:1 |
| **klein/ig-square** | Instagram 1:1 still |
| **klein/hook-still** | 9:16 first-frame hook |
| **klein/lower-third-bg** | Lower-third-safe 16:9 plate |
| **klein/food-tabletop** | Food / tabletop 4:5 |
| **klein/lighting-trio** | Same subject, three lights (SHOT KEY is the identity plate) |
| **klein/time-of-day** | Dusk plate, then dawn / noon / night edits |
| **klein/camera-angles** | Wide / medium / close of one subject, new cameras |
| **klein/color-moods** | Warm plate, then three grade edits |

Klein stills may use 1280×720; LTX feeders stay **1280×704**. See [Troubleshooting](../troubleshooting.md).
