---
title: inspire/beat-sheet
description: Script desk: logline, audio policy, 18 shot cards → shot-sheet YAML
tags: [workflows, generated, comfyui, inspire]
---

# inspire/beat-sheet

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `inspire/beat-sheet` from Apps or Workflows.

> Generated from `workflows/_lab/inspire/beat-sheet.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **none**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## inspire/beat-sheet

Script desk — 6 beats × enter / traverse / exit. Occupancy: none — stop nothing GPU.

This graph does not print video. Fill Logline, Script, Audio policy, Score — those desk
fields are packed into Context Join and condition every card rewrite. Then fill the 18 cards
(`action | camera | world SFX | dialogue`). Audio policy also feeds LTX audio notes.
Write YAML on the host:

  ./scripts/manage.sh shot-sheet run --film <slug>

That writes `${COMFY_OUTPUT_DIR}/films/<slug>/shots.yaml`. The entrypoint does **not**
copy YAML. Do not overwrite `workflows/shorts/*.shots.yaml` unless `--lab-example`.

Next: stills/identity-sheet, or export-guides if clay is required, then
dcc/clay-hero.

Shot-card keys (defaults fail-closed):

  audio_policy: world-only | stems | a2v-lock
  score: none | acestep-instrumental
  clay: skip | required
  audio_lock: none | a2v
  camera: dolly in | tracking | fixed camera | …

Shot 1 of beat 1 load_from: identity. Later shots load_from: <prev_prefix>_last.

Do not type a 30/60/90 s denoise. One LTX print is 5.00 s (121 frames = 1+8n @ 24 fps).
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **inspire/beat-sheet** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart TB
  GNOTE["NOTE"]
  GDESK["DESK"]
  GBEAT_1["BEAT 1"]
  GBEAT_2["BEAT 2"]
  GBEAT_3["BEAT 3"]
  GBEAT_4["BEAT 4"]
  GBEAT_5["BEAT 5"]
  GBEAT_6["BEAT 6"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Operator note | `Note` | NOTE |
| 2 | Logline | `EZSamplePrompt` | DESK |
| 3 | Script | `PrimitiveNode` | DESK |
| 4 | Audio policy | `PrimitiveNode` | DESK |
| 5 | Score | `PrimitiveNode` | Ungrouped |
| 6 | Desk context | `EZContextJoin` | DESK |
| 7 | Beat 1 enter | `PrimitiveNode` | BEAT 1 |
| 8 | Beat 1 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 1 |
| 9 | Beat 1 traverse | `PrimitiveNode` | BEAT 1 |
| 10 | Beat 1 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 1 |
| 11 | Beat 1 exit | `PrimitiveNode` | BEAT 1 |
| 12 | Beat 1 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 1 |
| 13 | Beat 2 enter | `PrimitiveNode` | BEAT 2 |
| 14 | Beat 2 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 2 |
| 15 | Beat 2 traverse | `PrimitiveNode` | BEAT 2 |
| 16 | Beat 2 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 2 |
| 17 | Beat 2 exit | `PrimitiveNode` | BEAT 2 |
| 18 | Beat 2 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 2 |
| 19 | Beat 3 enter | `PrimitiveNode` | BEAT 3 |
| 20 | Beat 3 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 3 |
| 21 | Beat 3 traverse | `PrimitiveNode` | BEAT 3 |
| 22 | Beat 3 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 3 |
| 23 | Beat 3 exit | `PrimitiveNode` | BEAT 3 |
| 24 | Beat 3 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 3 |
| 25 | Beat 4 enter | `PrimitiveNode` | BEAT 4 |
| 26 | Beat 4 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 4 |
| 27 | Beat 4 traverse | `PrimitiveNode` | BEAT 4 |
| 28 | Beat 4 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 4 |
| 29 | Beat 4 exit | `PrimitiveNode` | BEAT 4 |
| 30 | Beat 4 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 4 |
| 31 | Beat 5 enter | `PrimitiveNode` | BEAT 5 |
| 32 | Beat 5 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 5 |
| 33 | Beat 5 traverse | `PrimitiveNode` | BEAT 5 |
| 34 | Beat 5 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 5 |
| 35 | Beat 5 exit | `PrimitiveNode` | BEAT 5 |
| 36 | Beat 5 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 5 |
| 37 | Beat 6 enter | `PrimitiveNode` | BEAT 6 |
| 38 | Beat 6 enter LTX enhance | `EZLTXPromptEnhance` | BEAT 6 |
| 39 | Beat 6 traverse | `PrimitiveNode` | BEAT 6 |
| 40 | Beat 6 traverse LTX enhance | `EZLTXPromptEnhance` | BEAT 6 |
| 41 | Beat 6 exit | `PrimitiveNode` | BEAT 6 |
| 42 | Beat 6 exit LTX enhance | `EZLTXPromptEnhance` | BEAT 6 |
| 43 | Quality | `EZQuality` | Ungrouped |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.34.6 / lab `INPUT_TYPES` — not SD1.5 folklore.

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## inspire/beat-sheet Script desk — 6 beats × enter / traverse / exit. Occupancy: none — stop nothing GPU. This graph does not print video. Fill Logline, Script, Audio policy, Score — those desk fiel…`

```text
## inspire/beat-sheet

Script desk — 6 beats × enter / traverse / exit. Occupancy: none — stop nothing GPU.

This graph does not print video. Fill Logline, Script, Audio policy, Score — those desk
fields are packed into Context Join and condition every card rewrite. Then fill the 18 cards
(`action | camera | world SFX | dialogue`). Audio policy also feeds LTX audio notes.
Write YAML on the host:

  ./scripts/manage.sh shot-sheet run --film <slug>

That writes `${COMFY_OUTPUT_DIR}/films/<slug>/shots.yaml`. The entrypoint does **not**
copy YAML. Do not overwrite `workflows/shorts/*.shots.yaml` unless `--lab-example`.

Next: stills/identity-sheet, or export-guides if clay is required, then
dcc/clay-hero.

Shot-card keys (defaults fail-closed):

  audio_policy: world-only | stems | a2v-lock
  score: none | acestep-instrumental
  clay: skip | required
  audio_lock: none | a2v
  camera: dolly in | tracking | fixed camera | …

Shot 1 of beat 1 load_from: identity. Later shots load_from: <prev_prefix>_last.

Do not type a 30/60/90 s denoise. One LTX print is 5.00 s (121 frames = 1+8n @ 24 fps).
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

### `EZSamplePrompt` — Sample Prompt

STRING source with a sample-prompt combo plus Custom textarea.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `prompt` | out | `STRING` | Resolved prompt. |

#### `sample`

Type `COMBO`. Range / default: custom.

Sample or Custom.

**How it affects generation:** Custom uses the textarea as typed.

**This graph:** `custom`

#### `prompt`

Type `STRING`.

Custom textarea.

**How it affects generation:** Ignored when a sample is selected.

**This graph:** `One-line premise. Approve before any UNET.`

#### `catalog`

Type `STRING`.

Catalog id (inspire/prompt-forge).

**How it affects generation:** Leave as stamped.

**This graph:** `inspire/beat-sheet`

### `PrimitiveNode` — Primitive

A typed constant (string or float) with seed-style control.

!!! warning "Lab notes"

    Music Duration (FLOAT) and Prompt Forge Context (STRING). widgets[1] is always control_after_generate.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `value` | out | `FLOAT\|STRING` | Wired into duration / context / lyrics. |

#### `value`

Type `FLOAT|STRING`.

The constant.

**How it affects generation:** FLOAT seconds drive ACE latent length. STRING context is bible/research for Enhance.

| Instance | Value |
| --- | --- |
| Script | `Spoken and visual beats. Words are cheap; prints are not.` |
| Audio policy | `world-only` |
| Score | `none` |
| Beat 1 enter | `enter beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 1 traverse | `traverse beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 1 exit | `exit beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 2 enter | `enter beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 2 traverse | `traverse beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 2 exit | `exit beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 3 enter | `enter beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 3 traverse | `traverse beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 3 exit | `exit beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 4 enter | `enter beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 4 traverse | `traverse beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 4 exit | `exit beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 5 enter | `enter beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 5 traverse | `traverse beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 5 exit | `exit beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 6 enter | `enter beat 6 — action \| camera \| world SFX \| dialogue` |
| Beat 6 traverse | `traverse beat 6 — action \| camera \| world SFX \| dialogue` |
| Beat 6 exit | `exit beat 6 — action \| camera \| world SFX \| dialogue` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Whether the primitive mutates after Queue.

**How it affects generation:** fixed keeps duration/context pinned.

**This graph (all 21 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

### `EZContextJoin` — Context Join

Pack labeled desk fields into one context STRING for rewriter nodes.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `a` | in | `STRING` | Logline. |
| `b` | in | `STRING` | Script. |
| `c` | in | `STRING` | Audio policy. |
| `d` | in | `STRING` | Score. |
| `context` | out | `STRING` | Labeled block for Enhance context. |

#### `label_a`

Type `STRING`. Range / default: Logline.

Label for field A.

**How it affects generation:** Empty values are omitted.

**This graph:** `Logline`

#### `label_b`

Type `STRING`. Range / default: Script.

Label for field B.

**How it affects generation:** Beat-sheet default Script.

**This graph:** `Script`

#### `label_c`

Type `STRING`. Range / default: Audio policy.

Label for field C.

**How it affects generation:** Keeps no-score / world-SFX policy in every card rewrite.

**This graph:** `Audio policy`

#### `label_d`

Type `STRING`. Range / default: Score.

Label for field D.

**How it affects generation:** Optional.

**This graph:** `Score`

### `EZLTXPromptEnhance` — LTX Prompt Enhance

Rewrite a lazy prompt for LTX-2.5 (present-tense paragraph, audio interleaved).

!!! warning "Lab notes"

    Off on 90s films, talking-head, authored showcase. On for generic 5 s printers.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `prompt` | out | `STRING` | Paragraph CLIP encodes. |

#### `sample`

Type `COMBO`. Range / default: custom.

Sample or Custom.

**How it affects generation:** Custom keeps the textarea.

**This graph (all 18 instances):** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored LTX paragraph.

**How it affects generation:** I2V: start image holds look; prompt is motion + world SFX. Dialogue belongs in "quotes" only if you asked for speech.

| Instance | Value |
| --- | --- |
| Beat 1 enter LTX enhance | `enter beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 1 traverse LTX enhance | `traverse beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 1 exit LTX enhance | `exit beat 1 — action \| camera \| world SFX \| dialogue` |
| Beat 2 enter LTX enhance | `enter beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 2 traverse LTX enhance | `traverse beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 2 exit LTX enhance | `exit beat 2 — action \| camera \| world SFX \| dialogue` |
| Beat 3 enter LTX enhance | `enter beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 3 traverse LTX enhance | `traverse beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 3 exit LTX enhance | `exit beat 3 — action \| camera \| world SFX \| dialogue` |
| Beat 4 enter LTX enhance | `enter beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 4 traverse LTX enhance | `traverse beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 4 exit LTX enhance | `exit beat 4 — action \| camera \| world SFX \| dialogue` |
| Beat 5 enter LTX enhance | `enter beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 5 traverse LTX enhance | `traverse beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 5 exit LTX enhance | `exit beat 5 — action \| camera \| world SFX \| dialogue` |
| Beat 6 enter LTX enhance | `enter beat 6 — action \| camera \| world SFX \| dialogue` |
| Beat 6 traverse LTX enhance | `traverse beat 6 — action \| camera \| world SFX \| dialogue` |
| Beat 6 exit LTX enhance | `exit beat 6 — action \| camera \| world SFX \| dialogue` |

#### `enhance`

Type `BOOLEAN`.

Run the rewriter.

**How it affects generation:** Off keeps authored film/shot text pinned.

**This graph (all 18 instances):** `true`

#### `mode`

Type `COMBO`.

t2v vs i2v vs iclora system prompt.

**How it affects generation:** i2v when a start still is wired. iclora describes look, not the control type.

**This graph (all 18 instances):** `i2v`

**Other choices**

| Choice | What it does |
| --- | --- |
| `t2v` | Text to AV. |
| `i2v` | Start still owns look. |
| `iclora` | Union Control look/materials; guide owns blocking. |

#### `duration_hint`

Type `STRING`. Range / default: 5 seconds, 24 fps.

Duration hint.

**How it affects generation:** Does not set 121 frames — LTXVImgToVideo does.

**This graph (all 18 instances):** `5 seconds, 24 fps`

#### `audio_notes`

Type `STRING`.

World SFX / no-score policy.

**How it affects generation:** Lab 5 s printers ask for world SFX matching the start image, no score.

#### `style`

Type `COMBO`. Range / default: none.

Look reference. Ignored on I2V.

**How it affects generation:** Start frame owns look.

**This graph (all 18 instances):** `none`

**Other choices**

| Choice | What it does |
| --- | --- |
| `none` | Off. Do not weave a look reference into the CLIP prompt. |
| `photorealistic` | Photoreal photograph, natural materials, physically plausible light. |
| `cinematic_film_still` | Cinematic feature-film still, widescreen, motivated practicals. |
| `documentary_photography` | Observational documentary photograph, available light. |
| `analog_35mm_film` | Analog 35mm color-negative film grain and organic color. |
| `analog_120_medium_format` | Medium-format 120 film, creamy tones, fine grain. |
| `polaroid_instant` | Instant Polaroid print look, soft contrast, creamy highlights. |
| `golden_hour_photography` | Golden-hour photograph, warm sidelight, long shadows. |
| `overcast_natural_light` | Overcast natural light, soft sky-fill, open shadows. |
| `studio_product_photography` | Studio product photograph, seamless backdrop, soft key. |
| `editorial_fashion_photography` | Editorial fashion photograph, precise styling, magazine light. |
| `street_photography` | Candid street photograph, mixed city light, layered depth. |
| `architectural_photography` | Architectural photograph, corrected verticals, material texture. |
| `anime` | Japanese anime still, clean cel color, sharp line. |
| `manga_screentone` | Black-and-white manga ink and screentone. |
| `cartoon` | Bold cartoon illustration, thick outline, flat color. |
| `western_comic_book` | Western comic-book inks, Ben-Day dots, saturated print color. |
| `saturday_morning_cartoon` | Saturday-morning cartoon cel, limited palette, painted background. |
| `storybook_illustration` | Storybook illustration, soft paint, narrative composition. |
| `watercolor_illustration` | Transparent watercolor on paper, wet-into-wet blooms. |
| `gouache_illustration` | Opaque gouache painting, matte pigment, graphic shapes. |
| `ink_and_wash` | Ink-and-wash drawing, black ink and grey washes. |
| `colored_pencil` | Colored-pencil drawing, layered strokes, paper grain. |
| `charcoal_sketch` | Charcoal sketch, vine blacks and kneaded-eraser lights. |
| `line_art` | Clean black line art, minimal fill. |
| `cel_shaded` | Cel-shaded illustration, hard shadow bands, graphic highlights. |
| `risograph_print` | Risograph print, limited spot inks, grainy stipple. |
| `3d_feature_animation` | 3D feature-animation still, rounded forms, physically based materials. |
| `pixar_like_3d` | Stylized feature 3D, appealing proportions, soft GI. |
| `claymation` | Claymation still, fingerprint clay, miniature set. |
| `stop_motion` | Stop-motion puppet still, practical miniature set. |
| `unreal_engine_cinematic` | Real-time cinematic 3D, sharp materials, cinematic camera. |
| `isometric_3d` | Isometric 3D diorama, even light, readable volumes. |
| `low_poly` | Low-poly 3D, faceted geometry, flat vertex color. |
| `voxel` | Voxel art, cubic voxels, limited palette. |
| `oil_painting` | Oil painting on canvas, visible brushwork, rich impasto. |
| `impressionist_painting` | Impressionist oil, broken color, outdoor light. |
| `cubist` | Cubist painting, faceted planes, simultaneous viewpoints. |
| `art_nouveau` | Art Nouveau illustration, whiplash curves, botanical ornament. |
| `ukiyo_e_woodblock` | Ukiyo-e woodblock print, mineral pigments, keyblock line. |
| `baroque_oil` | Baroque oil, dramatic chiaroscuro, theatrical spotlight. |
| `digital_matte_painting` | Digital matte painting, epic environment, atmospheric perspective. |
| `concept_art` | Production concept art, readable design, cinematic key light. |
| `cyberpunk` | Cyberpunk night, wet asphalt, neon magenta and cyan. |
| `solarpunk` | Solarpunk day, greenery on architecture, warm sun. |
| `film_noir` | Film-noir still, high-contrast black and white, hard key. |
| `1970s_grain` | 1970s film still, warm print, heavy grain. |
| `vaporwave` | Vaporwave still, pastel neon, chrome, VHS softness. |
| `pixel_art` | Pixel art, limited palette, visible pixels, cluster shading. |
| `papercraft` | Papercraft diorama, cut paper layers, studio light. |
| `blueprint_technical_drawing` | Blueprint technical drawing, white line on cyan ground. |
| `black_and_white_photography` | Black-and-white still photograph, silver-gelatin tonal scale. |
| `infrared_false_color` | False-color infrared still, pale foliage, dark sky. |
| `long_exposure_night` | Long-exposure night photograph, light trails, frozen ambient glow. |
| `underwater_photography` | Submerged still through water, cyan-green falloff, caustic rays. |
| `aerial_oblique` | Oblique aerial still from high altitude, wide ground coverage. |
| `tilt_shift_miniature` | Tilt-shift still, miniaturized real scene, razor plane of focus. |
| `double_exposure_film` | Double-exposure analog still, two scenes overlaid in one frame. |
| `wet_plate_collodion` | Wet-plate collodion still, silvered highlights, uneven edges. |
| `cyanotype_print` | Cyanotype print, Prussian-blue iron process on paper. |
| `platinum_print` | Platinum-palladium contact print, matte noble-metal tones. |
| `daguerreotype` | Daguerreotype plate, mirrored silver, razor-thin focal plane. |
| `tintype` | Tintype ferrotype on dark lacquered metal. |
| `pinhole_camera` | Pinhole-camera still, infinite depth, soft vignetting. |
| `large_format_view_camera` | Large-format view-camera still, extreme resolving power. |
| `macro_photography` | Macro still at life-size or greater, shallow plane on a tiny subject. |
| `astrophotography` | Astrophotograph of night sky, tracked stars, deep black sky. |
| `high_key_studio_portrait` | High-key studio sitter still, bright seamless, open shadows. |
| `low_key_studio_portrait` | Low-key studio sitter still, face emerging from deep black. |
| `newspaper_halftone` | Newspaper halftone photograph, coarse ink dots on newsprint. |
| `cctv_security_still` | Security-camera still, wide-angle compression, surveillance color. |
| `pastel_drawing` | Soft-pastel drawing on toned paper, chalk dust. |
| `oil_pastel` | Oil-pastel drawing, waxy dense sticks on paper. |
| `marker_illustration` | Alcohol-marker illustration, streaked fills on layout paper. |
| `ballpoint_pen` | Ballpoint-pen drawing on notebook paper, hatching density. |
| `crosshatch_pen_ink` | Crosshatched dip-pen and ink drawing on Bristol. |
| `linocut_print` | Linocut relief print, carved gouge marks on paper. |
| `woodcut_print` | Northern woodcut relief print, carved plank grain. |
| `etching_intaglio` | Copper-plate etching, bitten line and plate tone. |
| `stipple_illustration` | Stipple illustration built from ink dots only. |
| `graffiti_mural` | Spray-paint graffiti mural on brick or concrete. |
| `botanical_illustration` | Scientific botanical illustration on white vellum. |
| `medical_illustration` | Didactic medical illustration, cutaways, clean anatomy. |
| `fashion_croquis` | Fashion croquis, elongated figure, garment flats. |
| `retro_travel_poster` | Mid-century travel poster, flat lithograph color. |
| `pop_art_screenprint` | Pop-art screenprint, hard color flats, commercial-print dots. |
| `manhwa_webtoon` | Full-color Korean webtoon still, soft painterly cells. |
| `gongbi_meticulous` | Gongbi meticulous painting, fine-outline mineral color on silk. |
| `illuminated_manuscript` | Medieval illuminated-manuscript miniature on vellum, gold leaf. |
| `silhouette_cutout` | Black paper-cut silhouette on a pale field. |
| `cloisonne_enamel` | Cloisonné enamel, metal cloisons holding vitreous color. |
| `stained_glass` | Stained-glass window, lead cames, pot-metal color. |
| `mosaic_tile` | Secular tesserae mosaic of stone and glass tiles. |
| `pointillism` | Pointillist painting, discrete dots of pure pigment. |
| `fauvism` | Fauvist painting, violent unmixed color, wild brush. |
| `surrealism` | Surrealist painting, dream logic, precise impossible objects. |
| `expressionism` | Expressionist painting, distorted form, emotional color. |
| `abstract_expressionism` | Abstract-expressionist canvas, gestural drips, stained fields. |
| `rococo` | Rococo painting, pastel silk, ornamental lightness. |
| `neoclassical_oil` | Neoclassical oil, marble-smooth figures, civic clarity. |
| `romantic_landscape` | Romantic landscape oil, sublime weather, tiny figures. |
| `dutch_golden_age` | Dutch Golden Age oil, north-window light, quiet interior. |
| `fresco_buon` | Buon fresco on wet plaster, mineral pigment locked in lime. |
| `tempera_panel` | Egg-tempera on gessoed panel, fine hatch, matte finish. |
| `byzantine_mosaic_icon` | Byzantine gold-ground mosaic icon, frontal sacred geometry. |
| `art_deco` | Art Deco illustration, sunburst geometry, chrome and lacquer. |
| `constructivist_poster` | Constructivist poster, diagonal photomontage, block geometry. |
| `naive_folk_painting` | Naive folk painting, flat perspective, patterned interiors. |
| `encaustic_wax` | Encaustic painting, fused beeswax and pigment. |
| `photoreal_oil_painting` | Photoreal oil painting on canvas, brush and weave, not a camera capture. |
| `pre_raphaelite` | Pre-Raphaelite oil, jewel color, botanical minuteness. |
| `symbolism` | Symbolist painting, mythic hush, jeweled dusk. |
| `bauhaus_graphic` | Bauhaus graphic, primary geometry, spare workshop color. |
| `toon_shaded_3d` | Toon-shaded 3D, inked volume outlines on modeled forms. |
| `early_cgi_scanline` | Early-1990s scanline CGI, plastic shaders, visible aliasing. |
| `miniature_tabletop` | Painted tabletop wargame miniature on hobby basing. |
| `interlocking_brick` | Interlocking-brick diorama, studded plastic bricks. |
| `plush_toy` | Plush-toy still, stitched felt and pile fabric. |
| `felt_craft` | Needle-felted wool sculpture, fuzzy fibers standing off the form. |
| `origami` | Folded origami paper, visible crease pattern holding the form. |
| `sand_animation` | Sand-on-glass animation still, grains pushed into form. |
| `cutout_animation` | Hinged cutout-animation still, paper puppets on a painted board. |
| `rotoscope` | Rotoscoped still, traced live-action with graphic paint-over. |
| `porcelain_figurine` | Glazed porcelain figurine, kiln shine, collectible scale. |
| `wood_carving` | Carved wood sculpture, chisel facets and open grain. |
| `blown_glass` | Blown-glass sculpture, transparent color, furnace stretch. |
| `ice_sculpture` | Carved ice sculpture, internal fractures, cold speculars. |
| `neon_tube` | Bent neon-tube sculpture, glowing gas in glass. |
| `painted_resin_miniature` | Hand-painted display resin figure, garage-kit scale. |
| `inflatable_sculpture` | Inflatable vinyl sculpture, seams and gloss holding air. |
| `paper_theater_2_5d` | 2.5D paper theater, layered flats with shallow parallax. |
| `steampunk` | Brass-and-steam Victorian machine-age still. |
| `dieselpunk` | Interwar dieselpunk still, riveted steel, wartime chrome. |
| `cottagecore` | Cottagecore still, linen, wildflowers, hearth warmth. |
| `dark_academia` | Dark-academia still, oak libraries, wool, lamplight. |
| `synthwave` | Synthwave still, hot magenta-orange sunset grid. |
| `gothic_horror` | Gothic-horror still, candlelit stone, deep umber dread. |
| `high_fantasy` | High-fantasy painterly still, mythic armor, enchanted dusk. |
| `western_dust` | Dust-bowl western still, hard sun on adobe and sage. |
| `retrofuturism_1950s` | 1950s retrofuturist still, atomic-age chrome and aqua. |
| `brutalist` | Brutalist concrete still, board-formed mass, overcast civic light. |
| `memphis_design` | Memphis-Milano still, squiggle laminates, candy geometry. |
| `y2k_gloss` | Y2K gloss still, iridescent plastics, icy chrome orbs. |
| `vhs_tracking` | VHS tracking-error still, warped scanlines, chroma smear. |
| `crt_scanlines` | CRT monitor still, RGB phosphor, visible scanlines. |
| `glitch_art` | Datamosh glitch still, blocky codec tears across the frame. |
| `holographic` | Holographic-foil still, rainbow diffraction on chrome. |
| `bioluminescent` | Bioluminescent night still, living glow in deep-blue dark. |
| `post_apocalyptic` | Post-apocalyptic still, rust, dust, broken concrete, sickly sun. |
| `afrofuturism` | Afrofuturist still, diasporic ornament, cosmic metals, sunlit future. |
| `psychedelic_1960s` | 1960s psychedelic still, molten contour, vibrating complementary color. |

#### `catalog`

Type `STRING`.

Sample-catalog id.

**How it affects generation:** Leave as stamped.

**This graph (all 18 instances):** `inspire/beat-sheet`

### `EZQuality` — Quality

Workflow-global quality combo. JS overlays family-specific sampler, UNET, CLIP, and VAE widgets.

!!! warning "Lab notes"

    custom freezes the last overlay. lab restores authored widgets. ultra/max may select Klein 9B or FLUX.2-dev when those files are on disk (FLUX Non-Commercial, not YouTube-ok). Never changes size. Not --tier quality.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `quality` | out | `STRING` | Selected quality id. |

#### `quality`

Type `COMBO`. Range / default: lab.

custom freezes last overlay; lab restores graph defaults.

**How it affects generation:** Named qualities may swap UNET, CLIP, and VAE. Does not change size or length. ultra/max need download-image --tier 9b or flux2-dev.

**This graph:** `lab`

**Other choices**

| Choice | What it does |
| --- | --- |
| `custom` | Freeze current widgets. Queue does not overlay. |
| `draft` | Faster Apache Klein 4B (NVFP4 if on disk). |
| `lab` | Authored lab widgets. Default. |
| `standard` | Distilled 4B, 8 steps, CFG 1.0. |
| `high` | Klein base 4B + CFG 3.5 when on disk; else extra distilled steps at CFG 1.0. |
| `ultra` | Klein 9B distilled when on disk (FLUX Non-Commercial). Else high. |
| `max` | Klein 9B base or FLUX.2-dev when on disk (FLUX Non-Commercial). Else high. |
