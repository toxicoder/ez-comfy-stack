---
title: Film graphs
description: Reference table of one-click 90s shorts, five-act films, and the clay-to-print DCC envelope graphs.
tags: [comfyui, workflows, shorts, dcc, ltx, catalog]
---

# Film graphs

Pick a film graph. This catalog covers long-form jobs: a one-click 90s short, a
five-act 7.5 min film, and the DCC envelopes that print a Blender clay study
through Klein look-dev into an LTX take. Single clips are on
[Motion graphs](workflows-motion.md) and the stills they start from are on
[Stills graphs](workflows-stills.md).

**What's on this page**

- **90s shorts** - the three one-title pairs (go-see, still-here, switchyard), the five-act series, and the plate -> print queue order
- **DCC (clay -> print)** - Klein-from-clay, IC-LoRA envelopes, in-canvas loaders, and the ten `_lab/3d/` mesh Apps
- **Related** - what to load after the film lands

**What this enables**

- **Queuing one file per film** instead of 18 separate 5 s graphs
- **Printing a Blender clay** through Klein look-dev and an LTX 8.00 s App envelope
- **Reading one table per group** so you can pick a slug in seconds

**Who this is for:** studio users who already Queued a 5 s LTX clip. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Full loop: [Short films](../shorts.md).

**How to read these tables.** The **Workflow** column is the lab id you load from
`_lab/film/`, `_lab/guides/`, or `_lab/3d/`, and it links to the generated node page for that
graph. **What it does** names the story or the guide input, the printer size, the
seed, the Enhance state, the output prefix, and any opt-in download. Seeds,
occupancy, and Queue rules are shared with every other catalog:
[Workflow catalog](../studio-workflows.md#shared-lab-graph-rules).

---

## 90s shorts

| Workflow | What it does |
| --- | --- |
| **[film/go-see/00-plate](../generated/workflows/film/go-see/00-plate.md)** | **Queue first.** Klein 4B identity still for the first-person parkour 90s. Prefix `ez_gosee_plate` |
| **[film/go-see/feature](../generated/workflows/film/go-see/feature.md)** | **One-click** first-person parkour 90s: 18 LTX 5.00s AV prints + stitch, from `ez_gosee_plate.png` |
| **[film/still-here/00-plate](../generated/workflows/film/still-here/00-plate.md)** | **Queue first.** Klein 4B identity still for the household morning 90s. Prefix `ez_stillhere_plate` |
| **[film/still-here/feature](../generated/workflows/film/still-here/feature.md)** | **One-click** household morning 90s (same shape) |
| **[film/switchyard/00-plate](../generated/workflows/film/switchyard/00-plate.md)** | **Queue first.** Klein 4B identity still for the night freight-yard 90s. Prefix `ez_switchyard_plate` |
| **[film/switchyard/feature](../generated/workflows/film/switchyard/feature.md)** | **One-click** night freight-yard 90s (same shape) |
| **[film/tide-table/00-plate](../generated/workflows/film/tide-table/00-plate.md)** | **Queue first.** Klein 4B identity still for the dawn skiff film. Prefix `ez_tidetable_plate` |
| **[film/tide-table/act-01](../generated/workflows/film/tide-table/act-01.md)** | Dawn skiff 7.5 min, act 1 of 5 (then act-02...05; concat 450s) |
| **[film/night-oven/00-plate](../generated/workflows/film/night-oven/00-plate.md)** | **Queue first.** Klein 4B identity still for the overnight bakery film. Prefix `ez_nightoven_plate` |
| **[film/night-oven/act-01](../generated/workflows/film/night-oven/act-01.md)** | Overnight bakery 7.5 min, act 1 of 5 |
| **[film/glasshouse/00-plate](../generated/workflows/film/glasshouse/00-plate.md)** | **Queue first.** Klein 4B identity still for the storm glasshouse film. Prefix `ez_glasshouse_plate` |
| **[film/glasshouse/act-01](../generated/workflows/film/glasshouse/act-01.md)** | Storm glasshouse 7.5 min, act 1 of 5 |
| **[film/last-lane/00-plate](../generated/workflows/film/last-lane/00-plate.md)** | **Queue first.** Klein 4B identity still for the night two-lane film. Prefix `ez_lastlane_plate` |
| **[film/last-lane/act-01](../generated/workflows/film/last-lane/act-01.md)** | Night two-lane 7.5 min, act 1 of 5 |
| **[film/breakwater/00-plate](../generated/workflows/film/breakwater/00-plate.md)** | **Queue first.** Klein 4B identity still for the storm-wall walk film. Prefix `ez_breakwater_plate` |
| **[film/breakwater/act-01](../generated/workflows/film/breakwater/act-01.md)** | Storm-wall walk 7.5 min, act 1 of 5 |
| **[video/silent/still-to-shot](../generated/workflows/video/silent/still-to-shot.md)** | Optional silent rehearsal / six-shot concat demo |
| **[video/av/still-to-shot](../generated/workflows/video/av/still-to-shot.md)** | Generic 5.00 s AV print (non-film) |

Plate graphs (Queue one first - its `SaveImage` writes `ez_<slug>_plate.png`, which the act-01 / feature app's `LoadImage` reads): `film/tide-table/00-plate` `film/night-oven/00-plate` `film/glasshouse/00-plate` `film/last-lane/00-plate` `film/breakwater/00-plate` `film/go-see/00-plate` `film/still-here/00-plate` `film/switchyard/00-plate`.

Act graphs (Queue in order, then `concat-shots.sh --film`): `film/tide-table/act-01` `film/tide-table/act-02` `film/tide-table/act-03` `film/tide-table/act-04` `film/tide-table/act-05` - `film/night-oven/act-01` `film/night-oven/act-02` `film/night-oven/act-03` `film/night-oven/act-04` `film/night-oven/act-05` - `film/glasshouse/act-01` `film/glasshouse/act-02` `film/glasshouse/act-03` `film/glasshouse/act-04` `film/glasshouse/act-05` - `film/last-lane/act-01` `film/last-lane/act-02` `film/last-lane/act-03` `film/last-lane/act-04` `film/last-lane/act-05` - `film/breakwater/act-01` `film/breakwater/act-02` `film/breakwater/act-03` `film/breakwater/act-04` `film/breakwater/act-05`.

Full loop: [Short films](../shorts.md). Two apps per film - Queue the **plate**, then the act / feature app. Leave LTX **1280x704**. Film printers stay **121 frames**. Do **not** Queue a 30/60/90 s latent.

---

## DCC (clay -> print)

| Workflow | What it does |
| --- | --- |
| **[guides/clay-hero](../generated/workflows/guides/clay-hero.md)** | Klein 4B edit of a guide-pack `first.png`. Enhance **on**, seed **42**, **1280x704**. Prefix `ez_clay_hero`. Then `overlay-qc`. Occupancy: dump while Comfy is **down**. |
| **[guides/clay-plates](../generated/workflows/guides/clay-plates.md)** | One clay still -> four plates (hero 704, packshot 1:1, IG 4:5, shorts 9:16). Prefix `ez_clay_pack_*`. |
| **[guides/canny-hero](../generated/workflows/guides/canny-hero.md)** | Klein 4B edit of `canny.png`. Prefix `ez_canny_hero`. Handoff: `ltx-iclora-canny`. |
| **[photos/dream-house-clay](../generated/workflows/photos/dream-house-clay.md)** | Instagram 4:5 Path B: ten Klein edits of `house-views` clay (1024x1280). Not an LTX pack. |
| **[guides/depth-control-8s](../generated/workflows/guides/depth-control-8s.md)** | Lab envelope for an 8.00s depth-guided LTX print. Official Union Control graph is **Templates -> LTX-2.5**. Opt-in `download-ltx --tier iclora`. MagCache off. Distilled-only. Joint AV is a world bed. |
| **[guides/canny-control-8s](../generated/workflows/guides/canny-control-8s.md)** | Same envelope; wire `canny.mp4`. |
| **[guides/depth-control-shorts](../generated/workflows/guides/depth-control-shorts.md)** | Depth envelope at **768x1280**. Dump with `export-guides --width 768 --height 1280`. |
| **[guides/first-last-from-guide](../generated/workflows/guides/first-last-from-guide.md)** | Fun InP first+last from the pack. Opt-in `download-wan --tier fun-inp`. MagCache off. |
| **[guides/guide-still](../generated/workflows/guides/guide-still.md)** | Stay on `:8188`. `EZDCCLoadGuideStill` + occupancy gate. Prefix `ez_guide_hero`. |
| **[guides/depth-from-loader](../generated/workflows/guides/depth-from-loader.md)** | Envelope from loaders + `depth.mp4` path. MagCache off. Distilled-only. Prefix `ez_iclora_guide`. |
| **[3d/trellis2](../generated/workflows/3d/trellis2.md)** | Klein still via `LoadImage` -> native TRELLIS.2 INT8 textured mesh. `SaveGLB` writes `assets/objects/_lab-trellis2/mesh`. Opt-in `download-3d --tier trellis2`. Occupancy **trellis**. |
| **[3d/still-to-mesh](../generated/workflows/3d/still-to-mesh.md)** | Still pack `plate=mug` via `EZDCCLoadStillPack` -> native TRELLIS.2 INT8 textured mesh. `SaveGLB` writes `assets/objects/_lab-mug/mesh`. Occupancy **trellis**. |
| **[3d/blockout-mesh](../generated/workflows/3d/blockout-mesh.md)** | Still pack via `EZDCCLoadStillPack` -> **untextured gray-box blockout**: structure + shape stages only, no upsample, no texture VAE, no `PaintMesh` - the fast layout proxy. `SaveGLB` writes `assets/objects/_lab-blockout/blockout`. Occupancy **trellis**. |
| **[3d/shot-to-prop](../generated/workflows/3d/shot-to-prop.md)** | DCC guide still via `EZDCCLoadGuideStill` (`slug=go-see`, `shot_id=12`, `layer=first`) -> textured mesh of one hero object, for re-compositing that object into other shots. `SaveGLB` writes `assets/objects/_lab-shot-prop/prop`. Occupancy **trellis**. |
| **[3d/prop-variants](../generated/workflows/3d/prop-variants.md)** | Klein still via `LoadImage` with `EmptyTrellis2LatentStructure` `batch_size=4` -> four candidate meshes from one still in a single occupancy session. `SaveGLB` writes `assets/objects/_lab-variants/prop`. Occupancy **trellis**. |
| **[3d/hero-from-photos](../generated/workflows/3d/hero-from-photos.md)** | One clean plate via `LoadImage` -> one textured hero `.glb` through the full chain at the 1024 upsample floor: the pick-one-take App. App rows: **Hero still**, **Quality**, **Upsample resolution**, **Texture pass**, **Save prefix**. `SaveGLB` writes `assets/objects/_lab-hero/hero`. Occupancy **trellis**. Handoff: `3d/multi-image-asset`. |
| **[3d/multi-image-asset](../generated/workflows/3d/multi-image-asset.md)** | **Four** views of one subject - **Front view** / **Side view** / **Back view** / **Top-down view**, each its own `LoadImage`, gate, and `Trellis2Conditioning` - fused into one mesh: the front conditions structure, the side the shape stage, the back the upsample, the top-down the texture pass. `SaveGLB` writes `assets/objects/_lab-multiview/asset`. Occupancy **trellis**. Build the plate with `photos/multi-view`. |
| **[3d/character-batch](../generated/workflows/3d/character-batch.md)** | Character sheet via `LoadImage` with `EmptyTrellis2LatentStructure` `batch_size=4` -> four candidate characters off one plate and one occupancy session, one `.glb` per item straight off `PaintMesh`. `SaveGLB` writes `assets/objects/_lab-characters/character`. Occupancy **trellis**. |
| **[3d/world-elements](../generated/workflows/3d/world-elements.md)** | Prop source **plus** a ground plate (two `LoadImage`, two `Trellis2Conditioning`) -> one textured `.glb` painted against the surface it will sit on, **and** the `scene.json` for it from the `EZSceneLayout` node in the same graph: one Queue, two files. `SaveGLB` writes `assets/objects/_lab-world/element`; the layout writes `scenes/world-elements_NNNNN.json`. Occupancy **trellis**. Handoff: `3d/set-dressing`. |
| **[3d/set-dressing](../generated/workflows/3d/set-dressing.md)** | The world half with no GPU: `EZSceneLayout` alone takes Asset Bible slugs (one per line), one camera, and an HDRI and writes `scenes/set-dressing_NNNNN.json` against [`schemas/scene.json`](../../schemas/scene.json). Prints no mesh and loads no model, so it queues beside a running take. Occupancy **none**. |
| **[audio/stem-mix](../generated/workflows/audio/stem-mix.md)** | Picture-lock stem mix desk. Occupancy **audio**. Host `stem-mix.sh` (duck -15 dB, YouTube loudnorm). |

---

## Related

Run the full loop first: [Short films](../shorts.md). Then:

- Operator loop for the guide pack: [DCC guide pack](../dcc-workflows.md)
- Stay on `:8188` after a Blender dump: [Stay in Comfy after a Blender dump](../learn/comfy-first-blender.md)
- Look-dev path from clay to finished clip: [Clay blockout to finished clip](../learn/clay-to-finish.md)
- Stills in Blender: [Blender creator suite](../learn/blender-creator.md)
- Pick the graph for a different job: [Workflow catalog](../studio-workflows.md)
