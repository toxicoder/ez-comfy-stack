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
| **[stills/still-draft](../generated/workflows/stills/still-draft.md)** | Apache Klein 4B distilled. Default **768×432**, **4** steps, batch 2, prefix `ez_still_draft`. **Format / platform** retargets |
| **[stills/still-hero](../generated/workflows/stills/still-hero.md)** | Same prompt + seed, **1280×704** (LTX VAE grid), more steps, prefix `ez_still_hero`. Enhance **on**. |
| **[stills/still-studio](../generated/workflows/stills/still-studio.md)** | Still desk. Format / platform (aspect or named job), Style, Rewrite prompt, Look recipe. Default **1280×704**. Prefix follows Format. |
| **[stills/image-studio](../generated/workflows/stills/image-studio.md)** | Universal still desk. 100 creator modes (background swap, change text, change ratio, …), Format / platform, optional reference still. **Iterate** does text-to-image then edit. **This run** shows the values Queue will send. Default **1280×704**. Prefix follows Creator mode unless Iterate is on (`ez_iterate`). |
| **[stills/identity-sheet](../generated/workflows/stills/identity-sheet.md)** | 3-angle sheet (front / three-quarter / profile) of the identity you type. Seed **42**, Enhance **on** (identity mode), **1280×704** |
| **[stills/character-draft](../generated/workflows/stills/character-draft.md)** | Character still 1024×1280, style dropdown, prefix `ez_character` |
| **[stills/character-tweak](../generated/workflows/stills/character-tweak.md)** | Klein-edit that still (LoadImage + ReferenceLatent), prefix `ez_character_tweak` |
| **[stills/talking-head](../generated/workflows/stills/talking-head.md)** | Klein still → LTX I2V talking smoke. Real freeze: **[motion/av/audio-to-video-8s](../generated/workflows/motion/av/audio-to-video-8s.md)**. Qwen3-TTS / Wan S2V opt-in. No banned lip-sync OSS |

Lane B Klein stills (same occupancy **klein**):

| Workflow | Occupancy | What it does |
| --- | --- | --- |
| **[stills/still-daily](../generated/workflows/stills/still-daily.md)** | klein | Daily still. Format / platform + click UNET to swap distilled / NVFP4 / base. Prefix `ez_still_app` |
| **[stills/still-studio](../generated/workflows/stills/still-studio.md)** | klein | Still desk. Format / platform sets pixels + prefix + framing; Style + Rewrite prompt + Look recipe. Prefix follows Format (`ez_still_studio` when Custom) |
| **[stills/image-studio](../generated/workflows/stills/image-studio.md)** | klein | Universal still desk. 100 creator modes + Format / platform + optional reference. **Iterate** / **This run**. Prefix follows Creator mode (`ez_gen_photoreal` default; `ez_iterate` while Iterate is on) |
| **[stills/platform-pack](../generated/workflows/stills/platform-pack.md)** | klein | Six plates, one identity (`ez_pack_*`). Independent T2I; Ctrl+B unused groups |
| **[stills/text-swap](../generated/workflows/stills/text-swap.md)** | klein | Lettering swap. Load a still, type only the new lettering, output matches source size. Prefix `ez_text_swap` |
| **[stills/background-swap](../generated/workflows/stills/background-swap.md)** | klein | Background swap. Load a still, pick a sample place or type a custom background. Replaces backdrop, ground, and nearby set dressing (empty Flux.2 canvas + ReferenceLatent). Toggles for other/background characters. Prefix `ez_bg_swap` |
| **[stills/background-edit](../generated/workflows/stills/background-edit.md)** | klein | Background edit. Load a still, restyle the environment in place (cartoon, add/remove, weather). Toggles for other/background characters. Prefix `ez_bg_edit` |

---

## Apps Lane A — Klein stills

App Mode (frontend **1.41.13+**) is a widget surface on the same lab JSON. Occupancy and handoff: [ComfyUI Apps](../studio-apps.md). Inspire (no UNET) stays on the [catalog index](../studio-workflows.md#inspire-lane-a).

| Workflow | What it does |
| --- | --- |
| **[stills/image-studio](../generated/workflows/stills/image-studio.md)** | Universal still desk. 100 creator modes, Format / platform, optional reference. **Iterate** (text, then edit the saved still) and **This run** (values Queue will send). Prefix follows Creator mode |
| **[stills/still-draft](../generated/workflows/stills/still-draft.md)** | Spark Still. Default 768×432; **Format / platform** retargets. Enhance on. Prefix `ez_still_draft` |
| **[stills/identity-sheet](../generated/workflows/stills/identity-sheet.md)** | 3-angle sheet of the identity you type, seed **42**, **1280×704** |
| **[stills/storyboard-6up](../generated/workflows/stills/storyboard-6up.md)** | Six new cameras of one scene (`ez_board_01`…`06`) |
| **[stills/dream-house](../generated/workflows/stills/dream-house.md)** | World bible. Ten Instagram 4:5 stills: virtual tour of one place, each a different room or view (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study) |
| **[stills/dream-house-clay](../generated/workflows/stills/dream-house-clay.md)** | Same tour as Klein **edit** of clay (`ez_house_clay_01`…`10`). `start` seeds plates; optional `house-views` dump. Prefix `ez_dream_house_clay_*` |
| **[stills/character-draft](../generated/workflows/stills/character-draft.md)** | Character still, 1024×1280, style dropdown, prefix `ez_character` |
| **[stills/character-tweak](../generated/workflows/stills/character-tweak.md)** | Edit `ez_character_*.png` with a change prompt (ReferenceLatent) |
| **[stills/background-swap](../generated/workflows/stills/background-swap.md)** | Keep the subject; replace backdrop, ground, and nearby set dressing. 100 sample places + Custom (Cubic block world rebuilds this place as cubes). Other/background character toggles. Prefix `ez_bg_swap` |
| **[stills/background-edit](../generated/workflows/stills/background-edit.md)** | Keep the subject; restyle the environment in place (cartoon, add/remove, weather). 30 samples + Custom. Other/background character toggles. Prefix `ez_bg_edit` |
| **[stills/hook-still](../generated/workflows/stills/hook-still.md)** | Vertical 9:16 hook still |

---

## Creator toolkit — stills and plates

Pack 1 stills (motion/AV companions: [Motion catalog](workflows-motion.md)):

| Workflow | What it does |
| --- | --- |
| **[stills/shorts-still](../generated/workflows/stills/shorts-still.md)** | Vertical 9:16 Shorts still (`ez_shorts_still`) |
| **[stills/thumbnail](../generated/workflows/stills/thumbnail.md)** | YouTube thumbnail still 1280×720 |
| **[stills/product-packshot](../generated/workflows/stills/product-packshot.md)** | Clean product packshot 1:1 |
| **[stills/before-after](../generated/workflows/stills/before-after.md)** | Before plate, after Klein-edit of the same mug |
| **[stills/style-lock](../generated/workflows/stills/style-lock.md)** | One penthouse, four cameras, locked inventory |
| **[stills/storyboard-6up](../generated/workflows/stills/storyboard-6up.md)** | Six storyboard frames of one rooftop from new cameras |

Pack 2 — stills and plates:

| Workflow | What it does |
| --- | --- |
| **[stills/endcard-cta](../generated/workflows/stills/endcard-cta.md)** | End-card / CTA plate 16:9 |
| **[stills/quote-bg](../generated/workflows/stills/quote-bg.md)** | Quote-card background 1:1 |
| **[stills/open-graph](../generated/workflows/stills/open-graph.md)** | Blog / Open Graph hero |
| **[stills/podcast-cover](../generated/workflows/stills/podcast-cover.md)** | Podcast cover 1:1 |
| **[stills/banner-wide](../generated/workflows/stills/banner-wide.md)** | Channel / LinkedIn banner ~3:1 |
| **[stills/instagram-square](../generated/workflows/stills/instagram-square.md)** | Instagram 1:1 still |
| **[stills/hook-still](../generated/workflows/stills/hook-still.md)** | 9:16 first-frame hook |
| **[stills/lower-third-bg](../generated/workflows/stills/lower-third-bg.md)** | Lower-third-safe 16:9 plate |
| **[stills/food-tabletop](../generated/workflows/stills/food-tabletop.md)** | Food / tabletop 4:5 |
| **[stills/lighting-trio](../generated/workflows/stills/lighting-trio.md)** | Same subject, three lights (SHOT KEY is the identity plate) |
| **[stills/time-of-day](../generated/workflows/stills/time-of-day.md)** | Dusk plate, then dawn / noon / night edits |
| **[stills/camera-angles](../generated/workflows/stills/camera-angles.md)** | Wide / medium / close of one subject, new cameras |
| **[stills/color-moods](../generated/workflows/stills/color-moods.md)** | Warm plate, then three grade edits |

Klein stills may use 1280×720; LTX feeders stay **1280×704**. See [Troubleshooting](../troubleshooting.md).
