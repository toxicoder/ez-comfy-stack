---
title: Film and DCC catalog
description: One-click 90s shorts graphs and clay → print DCC envelopes on the US-safe local studio.
tags: [comfyui, workflows, shorts, dcc, ltx, catalog]
---

# Film and DCC catalog

**What's on this page**

- **90s shorts** one-click films (go-see, still-here, switchyard)
- **7.5 min shorts** five-act graphs (tide-table, night-oven, glasshouse, last-lane, breakwater)
- **DCC (clay → print)** Klein-from-clay, IC-LoRA envelopes, in-canvas loaders

**What this enables**

- **Queuing one file per film** instead of 18 separate 5 s graphs
- **Printing a Blender clay** through Klein look-dev and an LTX 5.00 s envelope

**Who this is for:** studio users who already Queued a 5 s LTX clip. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Full loop: [90s shorts](../shorts.md). Outputs under `${COMFY_OUTPUT_DIR}`.

---

## 90s shorts

| Workflow | What it does |
| --- | --- |
| **[films/go-see](../generated/workflows/films/go-see.md)** | **One-click** first-person parkour 90s: Klein identity + 18 LTX 5.00s AV prints + stitch |
| **[films/still-here](../generated/workflows/films/still-here.md)** | **One-click** household morning 90s (same shape) |
| **[films/switchyard](../generated/workflows/films/switchyard.md)** | **One-click** night freight-yard 90s (same shape) |
| **[films/tide-table/act-01](../generated/workflows/films/tide-table/act-01.md)** | Dawn skiff 7.5 min, act 1 of 5 (then act-02…05; concat 450s) |
| **[films/night-oven/act-01](../generated/workflows/films/night-oven/act-01.md)** | Overnight bakery 7.5 min, act 1 of 5 |
| **[films/glasshouse/act-01](../generated/workflows/films/glasshouse/act-01.md)** | Storm glasshouse 7.5 min, act 1 of 5 |
| **[films/last-lane/act-01](../generated/workflows/films/last-lane/act-01.md)** | Night two-lane 7.5 min, act 1 of 5 |
| **[films/breakwater/act-01](../generated/workflows/films/breakwater/act-01.md)** | Storm-wall walk 7.5 min, act 1 of 5 |
| **[motion/silent/still-to-shot](../generated/workflows/motion/silent/still-to-shot.md)** | Optional silent rehearsal / six-shot concat demo |
| **[motion/av/still-to-shot](../generated/workflows/motion/av/still-to-shot.md)** | Generic 5.00 s AV print (non-film) |

Act graphs (Queue in order, then `concat-shots.sh --film`): `films/tide-table/act-01` `films/tide-table/act-02` `films/tide-table/act-03` `films/tide-table/act-04` `films/tide-table/act-05` · `films/night-oven/act-01` `films/night-oven/act-02` `films/night-oven/act-03` `films/night-oven/act-04` `films/night-oven/act-05` · `films/glasshouse/act-01` `films/glasshouse/act-02` `films/glasshouse/act-03` `films/glasshouse/act-04` `films/glasshouse/act-05` · `films/last-lane/act-01` `films/last-lane/act-02` `films/last-lane/act-03` `films/last-lane/act-04` `films/last-lane/act-05` · `films/breakwater/act-01` `films/breakwater/act-02` `films/breakwater/act-03` `films/breakwater/act-04` `films/breakwater/act-05`.

Full loop: [90s shorts](../shorts.md). One file per film — Queue once. Leave LTX **1280×704**. Do **not** set 241+ frames.

---

## DCC (clay → print)

| Workflow | What it does |
| --- | --- |
| **[dcc/clay-hero](../generated/workflows/dcc/clay-hero.md)** | Klein 4B edit of a guide-pack `first.png`. Enhance **on**, seed **42**, **1280×704**. Prefix `ez_clay_hero`. Then `overlay-qc`. Occupancy: dump while Comfy is **down**. |
| **[dcc/clay-plates](../generated/workflows/dcc/clay-plates.md)** | One clay still → four plates (hero 704, packshot 1:1, IG 4:5, shorts 9:16). Prefix `ez_clay_pack_*`. |
| **[dcc/canny-hero](../generated/workflows/dcc/canny-hero.md)** | Klein 4B edit of `canny.png`. Prefix `ez_canny_hero`. Handoff: `ltx-iclora-canny`. |
| **[stills/dream-house-clay](../generated/workflows/stills/dream-house-clay.md)** | Instagram 4:5 Path B: ten Klein edits of `house-views` clay (1024×1280). Not an LTX pack. |
| **[dcc/depth-control-5s](../generated/workflows/dcc/depth-control-5s.md)** | Lab envelope for a 5.00s depth-guided LTX print. Official Union Control graph is **Templates → LTX-2.5**. Opt-in `download-ltx --tier iclora`. MagCache off. Distilled-only. Joint AV is a world bed. |
| **[dcc/canny-control-5s](../generated/workflows/dcc/canny-control-5s.md)** | Same envelope; wire `canny.mp4`. |
| **[dcc/depth-control-shorts](../generated/workflows/dcc/depth-control-shorts.md)** | Depth envelope at **768×1280**. Dump with `export-guides --width 768 --height 1280`. |
| **[dcc/first-last-from-guide](../generated/workflows/dcc/first-last-from-guide.md)** | Fun InP first+last from the pack. Opt-in `download-wan --tier fun-inp`. MagCache off. |
| **[dcc/guide-still](../generated/workflows/dcc/guide-still.md)** | Stay on `:8188`. `EZDCCLoadGuideStill` + occupancy gate. Prefix `ez_guide_hero`. |
| **[dcc/depth-from-loader](../generated/workflows/dcc/depth-from-loader.md)** | Envelope from loaders + `depth.mp4` path. MagCache off. Distilled-only. Prefix `ez_iclora_guide`. |
| **[dcc/still-to-mesh](../generated/workflows/dcc/still-to-mesh.md)** | Still pack `plate=mug` → native TRELLIS.2 INT8. Output `assets/objects/_lab-mug/`. Occupancy **trellis**. |
| **[audio/stem-mix](../generated/workflows/audio/stem-mix.md)** | Picture-lock stem mix desk. Occupancy **audio**. Host `stem-mix.sh` (duck −15 dB, YouTube loudnorm). |

Operator loop: [DCC guide pack](../dcc-workflows.md). Stay on `:8188`: [Stay in Comfy after a Blender dump](../learn/comfy-first-blender.md). Playbook: [Clay to finish](../learn/clay-to-finish.md). Stills: [Blender creator suite](../learn/blender-creator.md).
