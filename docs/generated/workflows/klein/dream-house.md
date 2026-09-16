---
title: klein/dream-house
description: Ten Instagram 4:5 Klein stills: virtual tour of one place (outside, rooms, terrace, drone)
tags: [workflows, generated, comfyui, klein]
---

# klein/dream-house

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `klein/dream-house` from Apps or Workflows.

> Generated from `workflows/_lab/klein/dream-house.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **klein**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## klein/dream-house

Ten Instagram 4:5 stills: a virtual tour of **one place** (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280). Type any place in HOUSE IDENTITY — the default placeholder is the lab penthouse.
HOUSE IDENTITY is a camera-free world bible (rooms, furniture, outdoor lamps, sky, surroundings, time of day). Enhance extracts only the rooms and furniture you named — name lounge, kitchen, dining, bath, bedroom, terrace, study, and outdoor lamps so the tour can enter them. Name each room’s backdrop in the bible (which wall or opening that room faces). Hidden SHOT cards are camera stations (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study): lens, camera height, a distinct room program (entrance hall, living hall, cook line, dining hall, sleep chamber, wet room, open-air terrace, writing room), near/far planes, and which room — not a penthouse template and not one volume restyled. They do not name dusk, materials, or architecture. Prompt Join lock=view front-loads the shot and closes with “this still is only the room and backdrop the shot names.” Shots 02–10 are independent T2I (empty latent, same seed 42); they do not ReferenceLatent the identity still.
Identity-mode enhance is **on**. Shot cards are not Klein-t2i-enhanced — a per-shot rewrite would mutate the bible. Optional style dropdown applies to the bible.
Queue writes ez_dream_house_01 through ez_dream_house_10. Unused SHOT groups may be bypassed (Ctrl+B). Dawn / noon / night of one camera belong on klein-time-of-day, not this tour.
If materials drift across rooms, swap the UNET to Klein base 4B and raise steps/CFG as on klein-still-daily.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **klein/dream-house** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart TB
  GMODEL["MODEL"]
  GHOUSE_IDENTITY["HOUSE IDENTITY"]
  GSHOT_01_tower["SHOT 01 tower"]
  GSHOT_02_foyer["SHOT 02 foyer"]
  GSHOT_03_lounge["SHOT 03 lounge"]
  GSHOT_04_kitchen["SHOT 04 kitchen"]
  GSHOT_05_dining["SHOT 05 dining"]
  GSHOT_06_bedroom["SHOT 06 bedroom"]
  GSHOT_07_bath["SHOT 07 bath"]
  GSHOT_08_terrace["SHOT 08 terrace"]
  GSHOT_09_drone["SHOT 09 drone"]
  GSHOT_10_study["SHOT 10 study"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Klein 4B distilled FP8 | `UNETLoader` | MODEL |
| 2 | Qwen3-4B TE | `CLIPLoader` | MODEL |
| 3 | Flux2 VAE | `VAELoader` | MODEL |
| 4 | HOUSE IDENTITY | `EZKleinPromptEnhance` | HOUSE IDENTITY |
| 5 | Negative | `CLIPTextEncode` | Ungrouped |
| 6 | Instagram 4:5 1024x1280 | `EmptyFlux2LatentImage` | Ungrouped |
| 7 | Operator note | `Note` | Ungrouped |
| 10 | SHOT 01 tower | `EZPromptJoin` | SHOT 01 tower |
| 11 | Positive 01 | `CLIPTextEncode` | SHOT 01 tower |
| 12 | Sampler 01 | `KSampler` | SHOT 01 tower |
| 13 | Decode 01 | `VAEDecode` | SHOT 01 tower |
| 14 | Save 01 | `SaveImage` | SHOT 01 tower |
| 15 | SHOT 02 foyer | `EZPromptJoin` | SHOT 02 foyer |
| 16 | Positive 02 | `CLIPTextEncode` | SHOT 02 foyer |
| 17 | Sampler 02 | `KSampler` | SHOT 02 foyer |
| 18 | Decode 02 | `VAEDecode` | SHOT 02 foyer |
| 19 | Save 02 | `SaveImage` | SHOT 02 foyer |
| 20 | SHOT 03 lounge | `EZPromptJoin` | SHOT 03 lounge |
| 21 | Positive 03 | `CLIPTextEncode` | SHOT 03 lounge |
| 22 | Sampler 03 | `KSampler` | SHOT 03 lounge |
| 23 | Decode 03 | `VAEDecode` | SHOT 03 lounge |
| 24 | Save 03 | `SaveImage` | SHOT 03 lounge |
| 25 | SHOT 04 kitchen | `EZPromptJoin` | SHOT 04 kitchen |
| 26 | Positive 04 | `CLIPTextEncode` | SHOT 04 kitchen |
| 27 | Sampler 04 | `KSampler` | SHOT 04 kitchen |
| 28 | Decode 04 | `VAEDecode` | SHOT 04 kitchen |
| 29 | Save 04 | `SaveImage` | SHOT 04 kitchen |
| 30 | SHOT 05 dining | `EZPromptJoin` | SHOT 05 dining |
| 31 | Positive 05 | `CLIPTextEncode` | SHOT 05 dining |
| 32 | Sampler 05 | `KSampler` | SHOT 05 dining |
| 33 | Decode 05 | `VAEDecode` | SHOT 05 dining |
| 34 | Save 05 | `SaveImage` | SHOT 05 dining |
| 35 | SHOT 06 bedroom | `EZPromptJoin` | SHOT 06 bedroom |
| 36 | Positive 06 | `CLIPTextEncode` | SHOT 06 bedroom |
| 37 | Sampler 06 | `KSampler` | SHOT 06 bedroom |
| 38 | Decode 06 | `VAEDecode` | SHOT 06 bedroom |
| 39 | Save 06 | `SaveImage` | SHOT 06 bedroom |
| 40 | SHOT 07 bath | `EZPromptJoin` | SHOT 07 bath |
| 41 | Positive 07 | `CLIPTextEncode` | SHOT 07 bath |
| 42 | Sampler 07 | `KSampler` | SHOT 07 bath |
| 43 | Decode 07 | `VAEDecode` | SHOT 07 bath |
| 44 | Save 07 | `SaveImage` | SHOT 07 bath |
| 45 | SHOT 08 terrace | `EZPromptJoin` | SHOT 08 terrace |
| 46 | Positive 08 | `CLIPTextEncode` | SHOT 08 terrace |
| 47 | Sampler 08 | `KSampler` | SHOT 08 terrace |
| 48 | Decode 08 | `VAEDecode` | SHOT 08 terrace |
| 49 | Save 08 | `SaveImage` | SHOT 08 terrace |
| 50 | SHOT 09 drone | `EZPromptJoin` | SHOT 09 drone |
| 51 | Positive 09 | `CLIPTextEncode` | SHOT 09 drone |
| 52 | Sampler 09 | `KSampler` | SHOT 09 drone |
| 53 | Decode 09 | `VAEDecode` | SHOT 09 drone |
| 54 | Save 09 | `SaveImage` | SHOT 09 drone |
| 55 | SHOT 10 study | `EZPromptJoin` | SHOT 10 study |
| 56 | Positive 10 | `CLIPTextEncode` | SHOT 10 study |
| 57 | Sampler 10 | `KSampler` | SHOT 10 study |
| 58 | Decode 10 | `VAEDecode` | SHOT 10 study |
| 59 | Save 10 | `SaveImage` | SHOT 10 study |
| 60 | Negative Prompt Enhance | `EZNegativePromptEnhance` | Ungrouped |
| 61 | Quality | `EZQuality` | Ungrouped |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.34.6 / lab `INPUT_TYPES` — not SD1.5 folklore.

### `UNETLoader` — Load Diffusion Model

Load a standalone transformer/UNET from diffusion_models/.

!!! warning "Lab notes"

    Lab files: flux-2-klein-4b-fp8.safetensors, wan2.2_ti2v_5B_fp16.safetensors, ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors. weight_dtype stays default.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `MODEL` | out | `MODEL` | Denoiser weights. |

#### `unet_name`

Type `STRING`.

Checkpoint filename under MODELS_DIR diffusion_models.

**How it affects generation:** Wrong family = Queue error or a melted picture. Do not swap Klein 9B / FLUX.2-dev / MiniMax.

**This graph:** `flux-2-klein-4b-fp8.safetensors`

#### `weight_dtype`

Type `COMBO`. Range / default: default.

Cast at load.

**How it affects generation:** default keeps the file's dtype (Klein FP8, LTX INT8-convrot, Wan FP16).

**This graph:** `default`

**Other choices**

| Choice | What it does |
| --- | --- |
| `default` | Load weights as stored. Lab UNETLoader always uses this. |
| `fp8_e4m3fn` | Cast to FP8 e4m3fn. Can save memory; may shift Klein/LTX quality. |
| `fp8_e4m3fn_fast` | FP8 e4m3fn with fast optimizations. |
| `fp8_e5m2` | Cast to FP8 e5m2. |

### `CLIPLoader` — Load CLIP

Load a text encoder. The type combo must match the UNET family.

!!! warning "Lab notes"

    Lab types: flux2 (Qwen3-4B), wan (UMT5), ltxv (Gemma4-with-proj). Wrong type is a Queue error, not a bad prompt. MiniMax type is banned.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `CLIP` | out | `CLIP` | Text encoder for CLIPTextEncode / ACE / LTX. |

#### `clip_name`

Type `STRING`.

Filename under text_encoders.

**How it affects generation:** Must match the family (qwen_3_4b, umt5_xxl, gemma4-12b-with-proj).

**This graph:** `qwen_3_4b.safetensors`

#### `type`

Type `COMBO`.

CLIPType enum. Picks tokenizer + template.

**How it affects generation:** flux2 wraps Klein strings in a Qwen chat template — do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.

**This graph:** `flux2`

**Other choices**

| Choice | What it does |
| --- | --- |
| `flux2` | Klein 4B / Qwen3-4B text encoder. Lab stills. |
| `wan` | Wan 2.2 UMT5-XXL. Lab silent motion. |
| `ltxv` | LTX-2.5 Gemma4-with-proj. Lab AV. |
| `ace` | ACE-Step text encoder. Music graphs use CheckpointLoaderSimple instead. |
| `stable_diffusion` | SD1.x CLIP. Not a lab default. |
| `stable_cascade` | Stable Cascade CLIP. |
| `sd3` | SD3 CLIP stack. |
| `stable_audio` | Stable Audio T5. |
| `mochi` | Mochi T5. |
| `pixart` | PixArt. |
| `cosmos` | Cosmos T5. |
| `lumina2` | Lumina-2 Gemma. |
| `hidream` | HiDream. |
| `chroma` | Chroma. |
| `omnigen2` | OmniGen2. |
| `qwen_image` | Qwen-Image. |
| `hunyuan_image` | Hunyuan image. |
| `ovis` | Ovis. |
| `longcat_image` | LongCat image. Optional stub only. |
| `cogvideox` | CogVideoX T5. |
| `lens` | Lens. |
| `pixeldit` | PixelDit. |
| `ideogram4` | Ideogram. |
| `boogu` | Boogu. |
| `krea2` | Krea. |
| `joyimage` | JoyImage Qwen3-VL. |
| `mage` | Mage. |
| `minimax` | MiniMax. Banned in this studio (US Excluded Territory). Do not pick. |

#### `device`

Type `COMBO`. Range / default: default.

Where to load the encoder.

**How it affects generation:** default uses GPU. cpu is a debug escape hatch.

**This graph:** `default`

**Other choices**

| Choice | What it does |
| --- | --- |
| `default` | Load on the Comfy compute device (GPU). Lab default. |
| `cpu` | Force CPU. Much slower; only for debugging a CLIP load. |

### `VAELoader` — Load VAE

Load the autoencoder that maps pixels ↔ latents (and LTX audio).

!!! warning "Lab notes"

    Do not mix families: flux2-vae, wan2.2_vae, ltx-2.5-video-vae-bf16, ltx-2.5-audio-vae-bf16.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `VAE` | out | `VAE` | Encoder/decoder. |

#### `vae_name`

Type `STRING`.

Filename under vae/.

**How it affects generation:** Wrong VAE = color trash or a shape error.

**This graph:** `flux2-vae.safetensors`

### `EZKleinPromptEnhance` — Klein Prompt Enhance

Rewrite a lazy still/edit prompt for Klein 4B with on-box Qwen3-4B-Instruct.

!!! warning "Lab notes"

    Enhance on for lazy CLIP printers; off for authored recipes. Style ignored when it would fight an I2V start frame (not used here). Occupancy llm for the GGUF, then klein for the UNET.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `prompt` | in | `STRING` | Optional override of the widget (usually unwired). |
| `context` | in | `STRING` | Bible/research. Ignored when Enhance is off. |
| `prompt` | out | `STRING` | String CLIP actually encodes. |

#### `sample`

Type `COMBO`. Range / default: custom.

Lab sample prompt or Custom.

**How it affects generation:** Custom keeps the textarea. Picking a sample fills and locks the Prompt. Python combo is the union of every catalog so Comfy accepts place recipes (Cliff villa on dream-house); JS still filters the App dropdown to this graph.

**This graph:** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored still prompt.

**How it affects generation:** When Enhance is on, the GGUF expands this into Klein-native sentences.

**This graph:** `A photoreal still of one full-floor warm-glass crown penthouse on a very tall unmarked tropical coastal tower in a dense city of unmarked glass skyscrapers, a bright bay only as a distant slot betwee…`

```text
A photoreal still of one full-floor warm-glass crown penthouse on a very tall unmarked tropical coastal tower in a dense city of unmarked glass skyscrapers, a bright bay only as a distant slot between towers. A wide wraparound terrace sits outside a three-bay black-framed glass wall. Teak floors, pale stone, coral-teal edge light. Lounge at the glass with one sand linen sofa facing the towers. Kitchen island faces a solid teak cook wall. Dining faces an interior stone wall. Master bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a teak shelf wall. Warm teak terrace lanterns and low path lights. Palms on the terrace. Unmarked home, empty of lettering.
```

#### `enhance`

Type `BOOLEAN`. Range / default: on for lazy printers.

Run the rewriter.

**How it affects generation:** Off = encode the widget as-is (plus style suffix if set).

**This graph:** `true`

#### `mode`

Type `COMBO`. Range / default: t2i / edit / identity.

System prompt flavor.

**How it affects generation:** t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet).

**This graph:** `identity`

**Other choices**

| Choice | What it does |
| --- | --- |
| `t2i` | New still. |
| `edit` | Klein-edit / clay / tweak. |
| `identity` | Camera-free identity bible. |

#### `duration_hint`

Type `STRING`.

Framing hint (YouTube 16:9 still, Instagram 4:5, …).

**How it affects generation:** Steers aspect language in the rewrite. Does not set the latent size — EmptyFlux2LatentImage does.

**This graph:** `Instagram 4:5 still`

#### `style`

Type `COMBO`. Range / default: none.

Look reference woven into the CLIP prompt.

**How it affects generation:** none = off. Dropdown wins over style words already in the source. Hidden on I2V graphs.

**This graph:** `none`

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

#### `catalog`

Type `STRING`.

Sample-catalog id (graph stem).

**How it affects generation:** Internal. Leave as stamped so sample dropdowns resolve.

**This graph:** `klein/dream-house`

### `CLIPTextEncode` — CLIP Text Encode

Turn a prompt string into CONDITIONING for the sampler.

!!! warning "Lab notes"

    The dim CLIP box after Queue is this string. Prompt Enhance nodes rewrite it when Enhance is on.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `clip` | in | `CLIP` | Matching family encoder. |
| `text` | in | `STRING` | Often wired from Prompt Enhance so the widget is a preview. |
| `CONDITIONING` | out | `CONDITIONING` | Positive or negative cond. |

#### `text`

Type `STRING`.

Prompt encoded by CLIP.

**How it affects generation:** Klein: sentences, subject → place → light → camera. Wan I2V: motion + one camera only. LTX: present-tense paragraph with audio interleaved. Distilled Klein quality lives here, not in CFG.

| Instance | Value |
| --- | --- |
| Negative | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt…` |
| Positive 01 | `Low exterior looking up at this place from outside, 24mm, Instagram 4:5. Arriva…` |
| Positive 02 | `A narrow unoccupied entrance hall at the way in, 24mm, Instagram 4:5, eye-level…` |
| Positive 03 | `A wide unoccupied living hall from the lounge the bible named; if none, the pri…` |
| Positive 04 | `An unoccupied kitchen the bible named; if none, a cook room. 35mm, Instagram 4:…` |
| Positive 05 | `An unoccupied dining hall from the dining interior the bible named; if none, a …` |
| Positive 06 | `An unoccupied sleep chamber from the bedroom the bible named; if none, a privat…` |
| Positive 07 | `An unoccupied small wet room from the bath the bible named; if none, a wet inte…` |
| Positive 08 | `An unoccupied open-air terrace from the outdoor living the bible named; if none…` |
| Positive 09 | `Overhead looking down at this same place, 24mm, Instagram 4:5. Straight-down pl…` |
| Positive 10 | `An unoccupied writing room from the study the bible named; if none, a small wri…` |

### `EmptyFlux2LatentImage` — Empty Flux.2 Latent

Allocate a Klein / Flux.2 still latent (width × height × batch).

!!! warning "Lab notes"

    Draft 768×432 batch 2. Hero / LTX feeders 1280×704. Portrait 1024×1280 or 768×1280. 1280×720 is OK for thumbnails, not for LTX feeders.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `LATENT` | out | `LATENT` | Noise canvas for KSampler. |

#### `width`

Type `INT`. Range / default: lab 768 / 1280 / 1024 / 432….

Latent pixel width.

**How it affects generation:** Sets the still's width. Match the intended platform (16:9, 9:16, 1:1, 4:5).

**This graph:** `1024`

#### `height`

Type `INT`.

Latent pixel height.

**How it affects generation:** 1280×704 is the LTX VAE grid (÷32). 1280×720 is not.

**This graph:** `1280`

#### `batch_size`

Type `INT`. Range / default: draft 2; others 1.

How many stills in one Queue.

**How it affects generation:** Draft uses 2 for a cheap fork. Heroes stay 1.

**This graph:** `1`

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## klein/dream-house Ten Instagram 4:5 stills: a virtual tour of **one place** (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280). Type any place in HOUSE IDENTITY — the default placeholder is the lab…`

```text
## klein/dream-house

Ten Instagram 4:5 stills: a virtual tour of **one place** (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280). Type any place in HOUSE IDENTITY — the default placeholder is the lab penthouse.
HOUSE IDENTITY is a camera-free world bible (rooms, furniture, outdoor lamps, sky, surroundings, time of day). Enhance extracts only the rooms and furniture you named — name lounge, kitchen, dining, bath, bedroom, terrace, study, and outdoor lamps so the tour can enter them. Name each room’s backdrop in the bible (which wall or opening that room faces). Hidden SHOT cards are camera stations (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study): lens, camera height, a distinct room program (entrance hall, living hall, cook line, dining hall, sleep chamber, wet room, open-air terrace, writing room), near/far planes, and which room — not a penthouse template and not one volume restyled. They do not name dusk, materials, or architecture. Prompt Join lock=view front-loads the shot and closes with “this still is only the room and backdrop the shot names.” Shots 02–10 are independent T2I (empty latent, same seed 42); they do not ReferenceLatent the identity still.
Identity-mode enhance is **on**. Shot cards are not Klein-t2i-enhanced — a per-shot rewrite would mutate the bible. Optional style dropdown applies to the bible.
Queue writes ez_dream_house_01 through ez_dream_house_10. Unused SHOT groups may be bypassed (Ctrl+B). Dawn / noon / night of one camera belong on klein-time-of-day, not this tour.
If materials drift across rooms, swap the UNET to Klein base 4B and raise steps/CFG as on klein-still-daily.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

### `EZPromptJoin` — Prompt Join

Join a shared identity paragraph with a shot-specific camera line.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `identity` | in | `STRING` | World bible / character lock. |
| `prompt` | out | `STRING` | Joined prompt for CLIP / Enhance. |

#### `shot`

Type `STRING`.

Shot card (camera, room, action).

**How it affects generation:** lock=view front-loads this so Klein sees a new camera in the same place.

| Instance | Value |
| --- | --- |
| SHOT 01 tower | `Low exterior looking up at this place from outside, 24mm, Instagram 4:5. Arriva…` |
| SHOT 02 foyer | `A narrow unoccupied entrance hall at the way in, 24mm, Instagram 4:5, eye-level…` |
| SHOT 03 lounge | `A wide unoccupied living hall from the lounge the bible named; if none, the pri…` |
| SHOT 04 kitchen | `An unoccupied kitchen the bible named; if none, a cook room. 35mm, Instagram 4:…` |
| SHOT 05 dining | `An unoccupied dining hall from the dining interior the bible named; if none, a …` |
| SHOT 06 bedroom | `An unoccupied sleep chamber from the bedroom the bible named; if none, a privat…` |
| SHOT 07 bath | `An unoccupied small wet room from the bath the bible named; if none, a wet inte…` |
| SHOT 08 terrace | `An unoccupied open-air terrace from the outdoor living the bible named; if none…` |
| SHOT 09 drone | `Overhead looking down at this same place, 24mm, Instagram 4:5. Straight-down pl…` |
| SHOT 10 study | `An unoccupied writing room from the study the bible named; if none, a small wri…` |

#### `inventory`

Type `STRING`.

Locked object list.

**How it affects generation:** Keeps mugs/coats from mutating across a pack.

#### `lock`

Type `COMBO`. Range / default: view.

What stays pinned.

**How it affects generation:** view = new camera, same place (dream-house, storyboard). state = same camera, new light/grade (time-of-day, color-moods).

**This graph (all 10 instances):** `view`

**Other choices**

| Choice | What it does |
| --- | --- |
| `view` | New camera, same world. |
| `state` | Same framing, new light/grade/action. |

### `KSampler` — KSampler

Denoise a latent for N steps at a CFG, sampler, and scheduler.

!!! warning "Lab notes"

    Distilled Klein is CFG 1.0 / 4 steps / euler / simple. Raising CFG is not a quality knob. Wan 5B uses uni_pc and CFG 5. LTX distilled uses euler / simple / CFG 1.0 / 20 steps. ACE-Step uses 8 steps / CFG 1.0 / euler. TRELLIS uses 12 steps / CFG 7.5 / euler / normal.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `model` | in | `MODEL` | UNET / transformer after any ModelSampling* patch. |
| `positive` | in | `CONDITIONING` | What to include (CLIP / ACE / LTX prompt). |
| `negative` | in | `CONDITIONING` | What to avoid. Distilled Klein ignores this well — put constraints in the positive. |
| `latent_image` | in | `LATENT` | Noise canvas or encoded start image / video / audio latent. |
| `LATENT` | out | `LATENT` | Denoised latent for VAE decode. |

#### `seed`

Type `INT`. Range / default: 0 … 2^64-1; lab 42.

Random seed for the noise tensor.

**How it affects generation:** Same seed + same graph ≈ same picture or clip. Lab locks 42 on smokes so drafts are comparable.

**This graph (all 10 instances):** `42`

#### `control_after_generate`

Type `COMBO`. Range / default: fixed (lab).

What happens to seed after Queue.

**How it affects generation:** fixed keeps iteration honest while you change the prompt.

**This graph (all 10 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

#### `steps`

Type `INT`. Range / default: 1–10000; Klein distilled 4; LTX 20; Wan 20; ACE 8; TRELLIS 12.

Denoising iterations.

**How it affects generation:** More steps refine detail with diminishing returns. Distilled Klein is authored at 4 — raising steps is slower, not a quality knob. Do not raise LTX/Wan toward a 90 s denoise.

**This graph (all 10 instances):** `4`

#### `cfg`

Type `FLOAT`. Range / default: 0–100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5.

Classifier-free guidance scale.

**How it affects generation:** Distilled Klein is CFG 1.0 — raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.

**This graph (all 10 instances):** `1.0`

#### `sampler_name`

Type `COMBO`. Range / default: euler (most lab); uni_pc (Wan).

ODE / SDE algorithm that removes noise.

**How it affects generation:** euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.

**This graph (all 10 instances):** `euler`

**Other choices**

| Choice | What it does |
| --- | --- |
| `euler` | First-order ODE. Lab default for Klein, LTX, ACE, and most stills. Fast and stable at CFG 1.0. |
| `euler_cfg_pp` | Euler with CFG++. Rarely needed on distilled Klein (CFG is already 1.0). |
| `euler_ancestral` | Adds ancestral noise each step. More variation; weaker exact seed lock. |
| `euler_ancestral_cfg_pp` | Ancestral Euler with CFG++. |
| `heun` | Second-order Heun. Slower, sometimes smoother; not a lab default. |
| `heunpp2` | Higher-order Heun variant. |
| `exp_heun_2_x0` | Exponential Heun (x0 prediction). |
| `exp_heun_2_x0_sde` | Exponential Heun SDE. Extra stochasticity. |
| `dpm_2` | DPM-Solver-2. Two function evals per step. |
| `dpm_2_ancestral` | Ancestral DPM-2. |
| `lms` | Linear multistep. Older; keep for experiments only. |
| `dpm_fast` | Fast DPM. Coarse, good for previews. |
| `dpm_adaptive` | Adaptive DPM. Step count is a hint, not a hard budget. |
| `dpmpp_2s_ancestral` | DPM++ 2S ancestral. Common SD1.5 pick; not a Klein default. |
| `dpmpp_2s_ancestral_cfg_pp` | DPM++ 2S ancestral with CFG++. |
| `dpmpp_sde` | DPM++ SDE. Stochastic, slower. |
| `dpmpp_sde_gpu` | DPM++ SDE on GPU noise. |
| `dpmpp_2m` | DPM++ 2M. Smooth; often used on SD-family, not distilled Klein. |
| `dpmpp_2m_cfg_pp` | DPM++ 2M with CFG++. |
| `dpmpp_2m_sde` | DPM++ 2M SDE. |
| `dpmpp_2m_sde_gpu` | DPM++ 2M SDE GPU noise. |
| `dpmpp_2m_sde_heun` | DPM++ 2M SDE Heun. |
| `dpmpp_2m_sde_heun_gpu` | DPM++ 2M SDE Heun GPU. |
| `dpmpp_3m_sde` | DPM++ 3M SDE. |
| `dpmpp_3m_sde_gpu` | DPM++ 3M SDE GPU. |
| `ddpm` | Classic DDPM. Slow; do not use on 121-frame LTX. |
| `lcm` | Latent Consistency. Needs an LCM-tuned model; not lab Klein/Wan/LTX. |
| `ipndm` | iPNDM multistep. |
| `ipndm_v` | iPNDM (v-prediction). |
| `deis` | DEIS multistep. |
| `res_multistep` | Res multistep. Some turbo recipes. |
| `res_multistep_cfg_pp` | Res multistep CFG++. |
| `res_multistep_ancestral` | Ancestral res multistep. |
| `res_multistep_ancestral_cfg_pp` | Ancestral res multistep CFG++. |
| `gradient_estimation` | Gradient-estimation sampler. |
| `gradient_estimation_cfg_pp` | Gradient-estimation CFG++. |
| `er_sde` | ER-SDE sampler. |
| `seeds_2` | SEEDS-2. |
| `seeds_3` | SEEDS-3. |
| `sa_solver` | SA-Solver. |
| `sa_solver_pece` | SA-Solver PECE. |
| `ddim` | DDIM. Deterministic; not a lab default. |
| `uni_pc` | UniPC. Lab Wan 5B silent graphs use this with CFG 5. |
| `uni_pc_bh2` | UniPC BH2 variant. |

#### `scheduler`

Type `COMBO`. Range / default: simple (most lab); normal (TRELLIS).

How sigmas are spaced across steps.

**How it affects generation:** simple is even spacing and matches distilled Klein / LTX / ACE. normal is the TRELLIS pair. Do not copy karras from an SD1.5 recipe onto Klein.

**This graph (all 10 instances):** `simple`

**Other choices**

| Choice | What it does |
| --- | --- |
| `simple` | Even sigma spacing. Lab default for Klein, Wan, LTX, and ACE. |
| `normal` | Linear timestep schedule. TRELLIS structure/texture stages use this. |
| `karras` | Karras sigmas. Often sharper on SD-family; not the lab default. |
| `exponential` | Exponential sigma decay. |
| `sgm_uniform` | SGM uniform. SD3-family default; Wan uses ModelSamplingSD3 shift instead. |
| `ddim_uniform` | Uniform DDIM schedule. |
| `beta` | Beta-distribution timesteps. |
| `linear_quadratic` | Linear then quadratic (Mochi-style). |
| `kl_optimal` | KL-optimal sigma curve. |

#### `denoise`

Type `FLOAT`. Range / default: 0–1; lab 1.0.

Fraction of the latent to replace with denoised signal.

**How it affects generation:** 1.0 is full generation (T2I / T2V / ACE). Values below 1 keep structure from an encoded start image (Klein edit / clay). Lab I2V uses dedicated latent nodes, not denoise<1 on empty noise.

**This graph (all 10 instances):** `1.0`

### `VAEDecode` — VAE Decode

Decode image/video latents to pixels.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | KSampler output (video or still). |
| `vae` | in | `VAE` | Matching family VAE. |
| `IMAGE` | out | `IMAGE` | Frames or still. |

No widgets. Sockets only.

### `SaveImage` — Save Image

Write PNG stills under the output folder.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `images` | in | `IMAGE` | Decoded still or last-frame. |

#### `filename_prefix`

Type `STRING`.

Save prefix.

**How it affects generation:** Lab prefixes start with ez_. Last-frame savers on shot graphs feed concat-shots.

| Instance | Value |
| --- | --- |
| Save 01 | `ez_dream_house_01` |
| Save 02 | `ez_dream_house_02` |
| Save 03 | `ez_dream_house_03` |
| Save 04 | `ez_dream_house_04` |
| Save 05 | `ez_dream_house_05` |
| Save 06 | `ez_dream_house_06` |
| Save 07 | `ez_dream_house_07` |
| Save 08 | `ez_dream_house_08` |
| Save 09 | `ez_dream_house_09` |
| Save 10 | `ez_dream_house_10` |

### `EZNegativePromptEnhance` — Negative Prompt Enhance

Rewrite a negative CLIP seed so it does not fight the positive.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `positive` | in | `STRING` | Positive CLIP string as context. |
| `prompt` | out | `STRING` | Negative string. |

#### `prompt`

Type `STRING`.

Negative seed (artifacts, not style).

**How it affects generation:** FLUX-family models do not use negatives well. Keep this short; put constraints in the positive.

**This graph:** `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks`

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

#### `enhance`

Type `BOOLEAN`.

Rewrite using the positive as context.

**How it affects generation:** Stops canned 'illustration / Pixar' terms from fighting a cartoon-positive.

**This graph:** `true`

#### `family`

Type `COMBO`.

Which negative family.

**How it affects generation:** Must match the UNET on the canvas.

**This graph:** `klein`

**Other choices**

| Choice | What it does |
| --- | --- |
| `klein` | Klein stills. |
| `wan` | Wan silent. |
| `ltx` | LTX AV. |
| `zimage` | Z-Image Turbo (CFG 1; list is documentation). |
| `longcat` | LongCat-Video. |
| `dreamx` | DreamX-Creator AV. |
| `s2v` | Wan S2V; wav owns speech. |

### `EZQuality` — Quality

Workflow-global Lab / Draft / High combo. JS overlays family-specific sampler and Klein UNET widgets.

!!! warning "Lab notes"

    Default lab leaves authored widgets. Draft is faster. High is slower. Distilled Klein High without Klein base keeps CFG 1.0. Never selects banned weights. Not --tier quality.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `quality` | out | `STRING` | Selected quality id (lab, draft, high). |

#### `quality`

Type `COMBO`. Range / default: lab.

Lab default, Draft (faster), or High (slower).

**How it affects generation:** Family-specific overlays on steps, CFG, and Klein 4B UNET. Does not change size, length, CLIP, or VAE. Klein base High needs download-image --tier base.

**This graph:** `lab`

**Other choices**

| Choice | What it does |
| --- | --- |
| `lab` | Authored lab widgets. Default. |
| `draft` | Faster: fewer steps. Klein stays CFG 1.0 distilled when already distilled. |
| `high` | Slower: more steps. Klein base 4B + CFG 3.5 when that UNET is on disk; else extra distilled steps at CFG 1.0. |
