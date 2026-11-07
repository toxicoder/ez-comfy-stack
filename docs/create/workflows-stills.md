---
title: Stills graphs
description: Reference table of every seeded Klein 4B still, identity sheet, character desk, and creator plate graph.
tags: [comfyui, workflows, klein, stills, catalog]
---

# Stills graphs

Pick a still graph. This catalog covers one-frame jobs on Klein 4B: a first
draft, a hero print, an identity sheet, a character, an environment edit, and
every single-plate deliverable that ships empty of lettering. Motion graphs
are on [Motion graphs](workflows-motion.md) and platform-size jobs are on
[Creator pack](workflows-creator.md).

**What's on this page**

- **Still (Klein 4B)** - draft, hero, studio desks, identity, character, reframe, plus the Lane B plate graphs
- **FLUX 3 Klein stills** - the gated opt-in twins
- **Apps Lane A - Klein stills** - the same graphs on the App Mode surface
- **Creator toolkit** - pack 1 and pack 2 stills and plates
- **Related** - what to load once the still is right

**What this enables**

- **Queuing a Klein still** from a seeded filename instead of a blank canvas
- **Locking identity and plates** before Wan / LTX motion
- **Choosing a still desk** - draft, studio, or the universal image studio
- **Reading one table per group** so you can find a row in seconds

**Who this is for:** studio users after the first still-draft Queue. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md).

**How to read these tables.** The **Workflow** column is the lab id you load from
`_lab/`, and it links to the generated node page for that graph. **What it does**
names the job, the default pixels, the Enhance state, and the output prefix. The
**Occupancy** column, where a table has one, is the GB10 job the graph claims;
every graph on this page is occupancy **klein**.
Size values are widget defaults; **Format / platform** retargets the same graph.
Rules every lab graph shares (seeds, occupancy, sizes, Queue) are on
[Workflow catalog](../studio-workflows.md#shared-lab-graph-rules).

---

## Still (Klein 4B)

| Workflow | What it does |
| --- | --- |
| **[photos/still-draft](../generated/workflows/photos/still-draft.md)** | Apache Klein 4B distilled. Default **768x432**, **4** steps, batch 2, prefix `ez_still_draft`. **Format / platform** retargets |
| **[photos/still-hero](../generated/workflows/photos/still-hero.md)** | Same prompt + seed, **1280x704** (LTX VAE grid), more steps, prefix `ez_still_hero`. Enhance **on**. |
| **[photos/still-studio](../generated/workflows/photos/still-studio.md)** | Still desk. Format / platform (aspect or named job), Style, Rewrite prompt, Look recipe. Default **1280x704**. Prefix follows Format. |
| **[photos/image-studio](../generated/workflows/photos/image-studio.md)** | Universal still desk. 100 creator modes (background swap, change text, change ratio, ...), Format / platform, optional reference still. **Iterate** does text-to-image then edit. **This run** shows the values Queue will send. Default **1280x704**. Prefix follows Creator mode unless Iterate is on (`ez_iterate`). |
| **[photos/identity-sheet](../generated/workflows/photos/identity-sheet.md)** | 3-angle sheet (front / three-quarter / profile) of the identity you type. Seed **42**, Enhance **on** (identity mode), **1280x704** |
| **[photos/character-draft](../generated/workflows/photos/character-draft.md)** | Character still 1024x1280, style dropdown, prefix `ez_character` |
| **[photos/character-tweak](../generated/workflows/photos/character-tweak.md)** | Klein-edit that still (LoadImage + ReferenceLatent), prefix `ez_character_tweak` |
| **[video/av/talking-head](../generated/workflows/video/av/talking-head.md)** | Klein still -> LTX I2V talking smoke. Real freeze: **[video/av/audio-to-video-8s](../generated/workflows/video/av/audio-to-video-8s.md)**. Qwen3-TTS / Wan S2V opt-in. No banned lip-sync OSS |
| **[photos/upscale-reframe](../generated/workflows/photos/upscale-reframe.md)** | Upscale + reframe desk. Load a still, pick **Upscale** (none / 2x / 4x / 4K) and a **Format / platform** aspect (or Custom Width x Height); the missing frame area is generated to fill the new aspect, and the source plate is encoded as the reference. Format defaults to Custom (1280x704). Handoff: **[video/silent/still-to-video-5s](../generated/workflows/video/silent/still-to-video-5s.md)** |

Lane B Klein stills (same occupancy **klein**):

| Workflow | Occupancy | What it does |
| --- | --- | --- |
| **[photos/still-daily](../generated/workflows/photos/still-daily.md)** | klein | Daily still. Format / platform + click UNET to swap distilled / NVFP4 / base. Prefix `ez_still_app` |
| **[photos/still-studio](../generated/workflows/photos/still-studio.md)** | klein | Still desk. Format / platform sets pixels + prefix + framing; Style + Rewrite prompt + Look recipe. Prefix follows Format (`ez_still_studio` when Custom) |
| **[photos/image-studio](../generated/workflows/photos/image-studio.md)** | klein | Universal still desk. 100 creator modes + Format / platform + optional reference. **Iterate** / **This run**. Prefix follows Creator mode (`ez_gen_photoreal` default; `ez_iterate` while Iterate is on) |
| **[photos/platform-pack](../generated/workflows/photos/platform-pack.md)** | klein | Six plates, one identity (`ez_pack_*`). Independent T2I; Ctrl+B unused groups |
| **[photos/text-swap](../generated/workflows/photos/text-swap.md)** | klein | Lettering swap. Load a still, type only the new lettering, output matches source size. Prefix `ez_text_swap` |
| **[photos/background-swap](../generated/workflows/photos/background-swap.md)** | klein | Background swap. Load a still, pick a sample place or type a custom background. Replaces backdrop, ground, and nearby set dressing (empty Flux.2 canvas + ReferenceLatent). Toggles for other/background characters. Prefix `ez_bg_swap` |
| **[photos/background-edit](../generated/workflows/photos/background-edit.md)** | klein | Background edit. Load a still, restyle the environment in place (cartoon, add/remove, weather). Toggles for other/background characters. Prefix `ez_bg_edit` |

---

## FLUX 3 Klein stills (opt-in, gated)

Same Klein desk on **FLUX 3 Image Klein** weights: gated Hugging Face, **FLUX Kommunity License (v1.0)**, not Apache, and **not** in `download-models`. Accept the license on `black-forest-labs/flux-3-image-klein-comfy` with the **same HF account as `HF_TOKEN`**, then pull `bazelisk run //scripts:run-utility -- download-image run --tier flux3` (or `--tier flux3-base`) - each tier auto-includes the `flux3-te` text encoder. Monetized output only for qualifying users under **$5M gross annualized revenue**: [Model licenses](../licenses.md). Klein 4B above stays the Apache default still.

| Workflow | Occupancy | What it does |
| --- | --- | --- |
| **[labs/opt-in/still-flux3-fast](../generated/workflows/labs/opt-in/still-flux3-fast.md)** | klein | FLUX 3 Klein distilled INT8 (`flux3-image-klein-int8-convrot.safetensors`), **16** steps, CFG **1.0** - the graph ships the Quality `flux3-fast` values. Qwen3VL TE (type `flux2`) + `flux2-vae`. Prefix `ez_still_flux3_fast` |
| **[labs/opt-in/still-flux3-quality](../generated/workflows/labs/opt-in/still-flux3-quality.md)** | klein | FLUX 3 Klein base INT8 (`flux3-image-klein-base-int8-convrot.safetensors`), **50** steps, CFG **3.5** - the graph ships the Quality `flux3-quality` values. Same gated TE + VAE. Prefix `ez_still_flux3_quality` |

Weights missing: **Check models** names the command and Queue keeps the authored loaders (nothing swaps in weights you have not accepted). Both graphs pin `qwen3vl_4b_int8_convrot.safetensors` + `flux2-vae.safetensors`; Format / platform still sets pixels (16:9 mid 1024x576 by default).

---

## Apps Lane A - Klein stills

Same graphs, opened from Comfy's **Apps** sidebar. Widgets and handoff:
[ComfyUI Apps](../studio-apps.md). Inspire (no UNET) stays on the
[catalog index](../studio-workflows.md#labs-lane-a).

| Workflow | What it does |
| --- | --- |
| **[photos/image-studio](../generated/workflows/photos/image-studio.md)** | Universal still desk. 100 creator modes, Format / platform, optional reference. **Iterate** (text, then edit the saved still) and **This run** (values Queue will send). Prefix follows Creator mode |
| **[photos/still-draft](../generated/workflows/photos/still-draft.md)** | Spark Still. Default 768x432; **Format / platform** retargets. Enhance on. Prefix `ez_still_draft` |
| **[photos/identity-sheet](../generated/workflows/photos/identity-sheet.md)** | 3-angle sheet of the identity you type, seed **42**, **1280x704** |
| **[photos/storyboard-6up](../generated/workflows/photos/storyboard-6up.md)** | Six new cameras of one scene (`ez_board_01`...`06`) |
| **[photos/dream-house](../generated/workflows/photos/dream-house.md)** | World bible. Ten Instagram 4:5 stills: virtual tour of one place, each a different room or view (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study) |
| **[photos/dream-house-clay](../generated/workflows/photos/dream-house-clay.md)** | Same tour as Klein **edit** of clay (`ez_house_clay_01`...`10`). `start` seeds plates; optional `house-views` dump. Prefix `ez_dream_house_clay_*` |
| **[photos/character-draft](../generated/workflows/photos/character-draft.md)** | Character still, 1024x1280, style dropdown, prefix `ez_character` |
| **[photos/character-tweak](../generated/workflows/photos/character-tweak.md)** | Edit `ez_character_*.png` with a change prompt (ReferenceLatent) |
| **[photos/background-swap](../generated/workflows/photos/background-swap.md)** | Keep the subject; replace backdrop, ground, and nearby set dressing. 100 sample places + Custom. Cubic block world rebuilds this place as cubes from a block study, then pastes the original people; when the person mask cannot run it keeps the people photoreal on a photo-anchored rebuild. Other/background character toggles. Prefix `ez_bg_swap` |
| **[photos/background-edit](../generated/workflows/photos/background-edit.md)** | Keep the subject; restyle the environment in place (cartoon, add/remove, weather). 30 samples + Custom. Other/background character toggles. Prefix `ez_bg_edit` |
| **[photos/hook-still](../generated/workflows/photos/hook-still.md)** | Vertical 9:16 hook still |
| **[photos/upscale-reframe](../generated/workflows/photos/upscale-reframe.md)** | Upscale + reframe desk: 2x / 4x / 4K upscale and aspect reframe of a loaded still, or a new plate at the chosen format. **Format / platform** defaults to Custom (1280x704); the new frame area is generated, not stretched |

---

## Creator toolkit - stills and plates

Pack 1 stills (video/AV companions: [Motion graphs](workflows-motion.md)):

| Workflow | What it does |
| --- | --- |
| **[photos/shorts-still](../generated/workflows/photos/shorts-still.md)** | Vertical 9:16 Shorts still (`ez_shorts_still`) |
| **[photos/thumbnail](../generated/workflows/photos/thumbnail.md)** | YouTube thumbnail still 1280x720 |
| **[photos/product-packshot](../generated/workflows/photos/product-packshot.md)** | Clean product packshot 1:1 |
| **[photos/before-after](../generated/workflows/photos/before-after.md)** | Before plate, after Klein-edit of the same mug |
| **[photos/style-lock](../generated/workflows/photos/style-lock.md)** | One penthouse, four cameras, locked inventory |
| **[photos/storyboard-6up](../generated/workflows/photos/storyboard-6up.md)** | Six storyboard frames of one rooftop from new cameras |

Pack 2 - stills and plates:

| Workflow | What it does |
| --- | --- |
| **[photos/endcard-cta](../generated/workflows/photos/endcard-cta.md)** | End-card / CTA plate 16:9 |
| **[photos/quote-bg](../generated/workflows/photos/quote-bg.md)** | Quote-card background 1:1 |
| **[photos/open-graph](../generated/workflows/photos/open-graph.md)** | Blog / Open Graph hero |
| **[photos/podcast-cover](../generated/workflows/photos/podcast-cover.md)** | Podcast cover 1:1 |
| **[photos/banner-wide](../generated/workflows/photos/banner-wide.md)** | Channel / LinkedIn banner ~3:1 |
| **[photos/instagram-square](../generated/workflows/photos/instagram-square.md)** | Instagram 1:1 still |
| **[photos/hook-still](../generated/workflows/photos/hook-still.md)** | 9:16 first-frame hook |
| **[photos/lower-third-bg](../generated/workflows/photos/lower-third-bg.md)** | Lower-third-safe 16:9 plate |
| **[photos/food-tabletop](../generated/workflows/photos/food-tabletop.md)** | Food / tabletop 4:5 |
| **[photos/lighting-trio](../generated/workflows/photos/lighting-trio.md)** | Same subject, three lights (SHOT KEY is the identity plate) |
| **[photos/time-of-day](../generated/workflows/photos/time-of-day.md)** | Dusk plate, then dawn / noon / night edits |
| **[photos/camera-angles](../generated/workflows/photos/camera-angles.md)** | Wide / medium / close of one subject, new cameras |
| **[photos/color-moods](../generated/workflows/photos/color-moods.md)** | Warm plate, then three grade edits |

Klein stills may use 1280x720; LTX feeders stay **1280x704** - sizes:
[shared lab-graph rules](../studio-workflows.md#shared-lab-graph-rules). A
still that will not load or looks wrong: [Troubleshooting](../troubleshooting.md).

---

## Related

1. Move the still: [Motion graphs](workflows-motion.md)
2. Run the loop it belongs to: [The still-to-motion-to-AV pipeline](../visual-generative-ai.md)
3. Pick the graph for a different job: [Workflow catalog](../studio-workflows.md)
4. Write the prompt: [Prompting](../prompting.md)
5. Ship a platform size: [Creator pack](workflows-creator.md)
