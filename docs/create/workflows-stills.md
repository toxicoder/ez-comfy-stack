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

**Who this is for:** studio users after the first still-draft Queue. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Occupancy **klein**. Outputs under `${COMFY_OUTPUT_DIR}`.

---

## Still (Klein 4B)

| Workflow | What it does |
| --- | --- |
| **[klein/still-draft](../generated/workflows/klein/still-draft.md)** | Apache Klein 4B distilled, **768×432**, **4** steps, batch 2, prefix `ez_still_draft` |
| **[klein/still-hero](../generated/workflows/klein/still-hero.md)** | Same prompt + seed, **1280×704** (LTX VAE grid), more steps, prefix `ez_still_hero`. Enhance **on**. |
| **[klein/identity-sheet](../generated/workflows/klein/identity-sheet.md)** | 3-angle sheet (front / three-quarter / profile) of the identity you type. Seed **42**, Enhance **on** (identity mode), **1280×704** |
| **[klein/character-draft](../generated/workflows/klein/character-draft.md)** | Character still 1024×1280, style dropdown, prefix `ez_character` |
| **[klein/character-tweak](../generated/workflows/klein/character-tweak.md)** | Klein-edit that still (LoadImage + ReferenceLatent), prefix `ez_character_tweak` |
| **[klein/talking-head](../generated/workflows/klein/talking-head.md)** | Klein still → LTX I2V talking smoke. Real freeze: **[ltx/audio-to-video-5s](../generated/workflows/ltx/audio-to-video-5s.md)**. Qwen3-TTS / Wan S2V opt-in. No banned lip-sync OSS |

Lane B Klein stills (same occupancy **klein**):

| Workflow | Occupancy | What it does |
| --- | --- | --- |
| **[klein/still-daily](../generated/workflows/klein/still-daily.md)** | klein | Daily still. Click UNET to swap distilled / NVFP4 / base. Prefix `ez_still_app` |
| **[klein/platform-pack](../generated/workflows/klein/platform-pack.md)** | klein | Six plates, one identity (`ez_pack_*`). Independent T2I; Ctrl+B unused groups |

---

## Apps Lane A — Klein stills

App Mode (frontend **1.41.13+**) is a widget surface on the same lab JSON. Occupancy and handoff: [ComfyUI Apps](../studio-apps.md). Inspire (no UNET) stays on the [catalog index](../studio-workflows.md#inspire-lane-a).

| Workflow | What it does |
| --- | --- |
| **[klein/still-draft](../generated/workflows/klein/still-draft.md)** | Spark Still. 768×432, Enhance on. Prefix `ez_still_draft` |
| **[klein/identity-sheet](../generated/workflows/klein/identity-sheet.md)** | 3-angle sheet of the identity you type, seed **42**, **1280×704** |
| **[klein/storyboard-6up](../generated/workflows/klein/storyboard-6up.md)** | Six new cameras of one scene (`ez_board_01`…`06`) |
| **[klein/dream-house](../generated/workflows/klein/dream-house.md)** | World bible. Ten Instagram 4:5 stills: virtual tour of one place, each a different room or view (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study) |
| **[klein/dream-house-clay](../generated/workflows/klein/dream-house-clay.md)** | Same tour as Klein **edit** of clay (`ez_house_clay_01`…`10`). `start` seeds plates; optional `house-views` dump. Prefix `ez_dream_house_clay_*` |
| **[klein/character-draft](../generated/workflows/klein/character-draft.md)** | Character still, 1024×1280, style dropdown, prefix `ez_character` |
| **[klein/character-tweak](../generated/workflows/klein/character-tweak.md)** | Edit `ez_character_*.png` with a change prompt (ReferenceLatent) |
| **[klein/hook-still](../generated/workflows/klein/hook-still.md)** | Vertical 9:16 hook still |

---

## Creator toolkit — stills and plates

Pack 1 stills (motion/AV companions: [Motion catalog](workflows-motion.md)):

| Workflow | What it does |
| --- | --- |
| **[klein/shorts-still](../generated/workflows/klein/shorts-still.md)** | Vertical 9:16 Shorts still (`ez_shorts_still`) |
| **[klein/thumbnail](../generated/workflows/klein/thumbnail.md)** | YouTube thumbnail still 1280×720 |
| **[klein/product-packshot](../generated/workflows/klein/product-packshot.md)** | Clean product packshot 1:1 |
| **[klein/before-after](../generated/workflows/klein/before-after.md)** | Before plate, after Klein-edit of the same mug |
| **[klein/style-lock](../generated/workflows/klein/style-lock.md)** | One penthouse, four cameras, locked inventory |
| **[klein/storyboard-6up](../generated/workflows/klein/storyboard-6up.md)** | Six storyboard frames of one rooftop from new cameras |

Pack 2 — stills and plates:

| Workflow | What it does |
| --- | --- |
| **[klein/endcard-cta](../generated/workflows/klein/endcard-cta.md)** | End-card / CTA plate 16:9 |
| **[klein/quote-bg](../generated/workflows/klein/quote-bg.md)** | Quote-card background 1:1 |
| **[klein/open-graph](../generated/workflows/klein/open-graph.md)** | Blog / Open Graph hero |
| **[klein/podcast-cover](../generated/workflows/klein/podcast-cover.md)** | Podcast cover 1:1 |
| **[klein/banner-wide](../generated/workflows/klein/banner-wide.md)** | Channel / LinkedIn banner ~3:1 |
| **[klein/instagram-square](../generated/workflows/klein/instagram-square.md)** | Instagram 1:1 still |
| **[klein/hook-still](../generated/workflows/klein/hook-still.md)** | 9:16 first-frame hook |
| **[klein/lower-third-bg](../generated/workflows/klein/lower-third-bg.md)** | Lower-third-safe 16:9 plate |
| **[klein/food-tabletop](../generated/workflows/klein/food-tabletop.md)** | Food / tabletop 4:5 |
| **[klein/lighting-trio](../generated/workflows/klein/lighting-trio.md)** | Same subject, three lights (SHOT KEY is the identity plate) |
| **[klein/time-of-day](../generated/workflows/klein/time-of-day.md)** | Dusk plate, then dawn / noon / night edits |
| **[klein/camera-angles](../generated/workflows/klein/camera-angles.md)** | Wide / medium / close of one subject, new cameras |
| **[klein/color-moods](../generated/workflows/klein/color-moods.md)** | Warm plate, then three grade edits |

Klein stills may use 1280×720; LTX feeders stay **1280×704**. See [Troubleshooting](../troubleshooting.md).
