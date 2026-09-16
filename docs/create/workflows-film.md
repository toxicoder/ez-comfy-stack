---
title: Film and DCC catalog
description: One-click 90s shorts graphs and clay → print DCC envelopes on the US-safe local studio.
tags: [comfyui, workflows, shorts, dcc, ltx, catalog]
---

# Film and DCC catalog

**What's on this page**

- **90s shorts** one-click films (go-see, still-here, switchyard)
- **DCC (clay → print)** Klein-from-clay, IC-LoRA envelopes, in-canvas loaders

**What this enables**

- **Queuing one file per film** instead of 18 separate 5 s graphs
- **Printing a Blender clay** through Klein look-dev and an LTX 5.00 s envelope

**Who this is for:** studio users who already Queued a 5 s LTX clip. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Full loop: [90s shorts](../shorts.md). Outputs under `${COMFY_OUTPUT_DIR}`.

---

## 90s shorts

| Workflow | What it does |
| --- | --- |
| **[shorts/go-see](../generated/workflows/shorts/go-see.md)** | **One-click** first-person parkour 90s: Klein identity + 18 LTX 5.00s AV prints + stitch |
| **[shorts/still-here](../generated/workflows/shorts/still-here.md)** | **One-click** household morning 90s (same shape) |
| **[shorts/switchyard](../generated/workflows/shorts/switchyard.md)** | **One-click** night freight-yard 90s (same shape) |
| **[wan/i2v-shot](../generated/workflows/wan/i2v-shot.md)** | Optional silent rehearsal / six-shot concat demo |
| **[ltx/i2v-shot](../generated/workflows/ltx/i2v-shot.md)** | Generic 5.00 s AV print (non-film) |

Full loop: [90s shorts](../shorts.md). One file per film — Queue once. Leave LTX **1280×704**. Do **not** set 241+ frames.

---

## DCC (clay → print)

| Workflow | What it does |
| --- | --- |
| **[dcc/klein/from-clay](../generated/workflows/dcc/klein/from-clay.md)** | Klein 4B edit of a guide-pack `first.png`. Enhance **on**, seed **42**, **1280×704**. Prefix `ez_clay_hero`. Then `overlay-qc`. Occupancy: dump while Comfy is **down**. |
| **[dcc/klein/from-clay-plates](../generated/workflows/dcc/klein/from-clay-plates.md)** | One clay still → four plates (hero 704, packshot 1:1, IG 4:5, shorts 9:16). Prefix `ez_clay_pack_*`. |
| **[dcc/klein/from-canny](../generated/workflows/dcc/klein/from-canny.md)** | Klein 4B edit of `canny.png`. Prefix `ez_canny_hero`. Handoff: `ltx-iclora-canny`. |
| **[klein/dream-house-clay](../generated/workflows/klein/dream-house-clay.md)** | Instagram 4:5 Path B: ten Klein edits of `house-views` clay (1024×1280). Not an LTX pack. |
| **[dcc/ltx/iclora-depth-5s](../generated/workflows/dcc/ltx/iclora-depth-5s.md)** | Lab envelope for a 5.00s depth-guided LTX print. Official Union Control graph is **Templates → LTX-2.5**. Opt-in `download-ltx --tier iclora`. MagCache off. Distilled-only. Joint AV is a world bed. |
| **[dcc/ltx/iclora-canny-5s](../generated/workflows/dcc/ltx/iclora-canny-5s.md)** | Same envelope; wire `canny.mp4`. |
| **[dcc/ltx/iclora-depth-shorts](../generated/workflows/dcc/ltx/iclora-depth-shorts.md)** | Depth envelope at **768×1280**. Dump with `export-guides --width 768 --height 1280`. |
| **[dcc/wan/flf-from-guide](../generated/workflows/dcc/wan/flf-from-guide.md)** | Fun InP first+last from the pack. Opt-in `download-wan --tier fun-inp`. MagCache off. |
| **[dcc/klein/from-guide-loader](../generated/workflows/dcc/klein/from-guide-loader.md)** | Stay on `:8188`. `EZDCCLoadGuideStill` + occupancy gate. Prefix `ez_guide_hero`. |
| **[dcc/ltx/iclora-from-guide-loader](../generated/workflows/dcc/ltx/iclora-from-guide-loader.md)** | Envelope from loaders + `depth.mp4` path. MagCache off. Distilled-only. Prefix `ez_iclora_guide`. |
| **[dcc/trellis/from-klein-still](../generated/workflows/dcc/trellis/from-klein-still.md)** | Still pack `plate=mug` → native TRELLIS.2 INT8. Output `assets/objects/_lab-mug/`. Occupancy **trellis**. |
| **[audio/finish](../generated/workflows/audio/finish.md)** | Picture-lock stem mix desk. Occupancy **audio**. Host `stem-mix.sh` (duck −15 dB, YouTube loudnorm). |

Operator loop: [DCC guide pack](../dcc-workflows.md). Stay on `:8188`: [Stay in Comfy after a Blender dump](../learn/comfy-first-blender.md). Playbook: [Clay to finish](../learn/clay-to-finish.md). Stills: [Blender creator suite](../learn/blender-creator.md).
