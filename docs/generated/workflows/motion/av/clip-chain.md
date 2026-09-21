---
title: "motion/av/clip-chain"
description: "Four LTX AV beats with last-frame continuity, 8.00 s / 193 each"
tags: [workflows, generated, comfyui, motion]
---

# motion/av/clip-chain

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `motion/av/clip-chain` from Apps or Workflows.

> Generated from `workflows/_lab/motion/av/clip-chain.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **ltx**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## motion/av/clip-chain

Format / platform sets pixels (Custom uses Width × Height). Quality does not change size.

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

Four LTX AV beats share one UNET / video VAE / audio VAE / CLIP. Last frame of beat N starts beat N+1. EZClipConcat stitches the four MP4s (hard cut). Primary output: `${COMFY_OUTPUT_DIR}/ez_clip_chain.mp4` plus per-beat VHS (`ez_clip_b0N_ltx_video`) and last-frame PNG (`ez_clip_b0N_last`). No full-batch SaveImage.

**8 seconds, 24 fps** (193 frames = 1+8n) chain-wide. Duration combo stays 5/8/10/12; mixed per-beat lengths are unsupported. Four × 8 s sequential prints are tens of minutes on GB10 — not a hang. Headroom preflight still applies at `start`.

Occupancy: ltx — stop Wan, podcast, music, other LTX. One GB10 job. Occupancy ltx XOR. `occupancy enter ltx` before Queue. No Klein identity on this canvas.

Duplicate Beat groups on canvas for beats 5–24:

1. Duplicate the last Beat group.
2. Set `VHS_VideoCombine.filename_prefix` to `ez_clip_b05_ltx_video` (then b06…).
3. Set last-frame SaveImage prefix to `ez_clip_b05_last`.
4. Wire previous `EZClipLastFrame.last_frame` → new `LTXVImgToVideo.image`.
5. Wire new `VHS_VideoCombine.Filenames` → the next free `EZClipConcat.clip_0N` (`clip_05` for the fifth beat).
6. Keep the shared UNET / VAE / CLIP / Format / Seed / Rewrite / Audio notes wires (do not duplicate loaders).
7. Save under `_user/` if you want a personal App; shipped `_lab` stays 4 beats.

Past 24 stems: host `./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 --cap-seconds <sum> --yes` (default `--files` cap is 90 s).

LTX-2.5 distilled AV. LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown is hidden on I2V.

LoadImage default example.png; after a still set ez_still_hero_*.png. Match input Format. MagCache off.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **motion/av/clip-chain** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart TB
  GNOTE["NOTE"]
  GQUALITY["QUALITY"]
  G1__LTX_models["1. LTX models"]
  G2__Start___occupancy___format["2. Start / occupancy / format"]
  G3__Beat_1__8_00s_LTX_["3. Beat 1 (8.00s LTX)"]
  G4__Beat_2__8_00s_LTX_["4. Beat 2 (8.00s LTX)"]
  G5__Beat_3__8_00s_LTX_["5. Beat 3 (8.00s LTX)"]
  G6__Beat_4__8_00s_LTX_["6. Beat 4 (8.00s LTX)"]
  G7__Publish_clip_chain["7. Publish clip chain"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | LTX-2.5 distilled INT8-convrot | `UNETLoader` | 1. LTX models |
| 2 | LTX-2.5 video VAE | `VAELoader` | 1. LTX models |
| 3 | Gemma4-with-proj (ltxv) | `CLIPLoader` | 1. LTX models |
| 4 | Start image | `LoadImage` | 2. Start / occupancy / format |
| 13 | LTX-2.5 audio VAE | `VAELoader` | 1. LTX models |
| 14 | Empty LTX audio latent | `LTXVEmptyLatentAudio` | 1. LTX models |
| 17 | Operator note — clip chain | `Note` | NOTE |
| 22 | Quality | `EZQuality` | QUALITY |
| 23 | Format / platform | `EZVideoFormat` | 2. Start / occupancy / format |
| 24 | Describe image | `EZImageDescribe` | 2. Start / occupancy / format |
| 30 | Occupancy gate (ltx) | `EZDCCOccupancyGate` | 2. Start / occupancy / format |
| 31 | Seed | `PrimitiveNode` | 2. Start / occupancy / format |
| 32 | Rewrite prompt | `PrimitiveNode` | 2. Start / occupancy / format |
| 33 | Audio notes | `PrimitiveNode` | 2. Start / occupancy / format |
| 34 | Logline / context | `PrimitiveNode` | 2. Start / occupancy / format |
| 40 | Save clip chain (MP4) — play / download | `EZClipConcat` | 7. Publish clip chain |
| 41 | LTX AI-media disclosure (end-card) | `EZFilmDisclosure` | 7. Publish clip chain |
| 109 | Beat 1 | `EZLTXPromptEnhance` | 3. Beat 1 (8.00s LTX) |
| 100 | Beat 1 prompt | `CLIPTextEncode` | 3. Beat 1 (8.00s LTX) |
| 111 | Beat 1 negative enhance | `EZNegativePromptEnhance` | 3. Beat 1 (8.00s LTX) |
| 101 | Beat 1 negative | `CLIPTextEncode` | 3. Beat 1 (8.00s LTX) |
| 102 | LTX Img→Video condition | `LTXVImgToVideo` | 3. Beat 1 (8.00s LTX) |
| 103 | LTX frame rate cond | `LTXVConditioning` | 3. Beat 1 (8.00s LTX) |
| 106 | Concat AV latents | `LTXVConcatAVLatent` | 3. Beat 1 (8.00s LTX) |
| 104 | Beat 1 KSampler | `KSampler` | 3. Beat 1 (8.00s LTX) |
| 107 | Separate AV latents | `LTXVSeparateAVLatent` | 3. Beat 1 (8.00s LTX) |
| 105 | VAE Decode | `VAEDecode` | 3. Beat 1 (8.00s LTX) |
| 110 | Audio VAE Decode | `LTXVAudioVAEDecode` | 3. Beat 1 (8.00s LTX) |
| 108 | Beat 1 video (MP4) — open node for prev… | `VHS_VideoCombine` | 3. Beat 1 (8.00s LTX) |
| 112 | Beat 1 last frame | `EZClipLastFrame` | 3. Beat 1 (8.00s LTX) |
| 113 | Save beat 1 last frame | `SaveImage` | 3. Beat 1 (8.00s LTX) |
| 149 | Beat 2 | `EZLTXPromptEnhance` | 4. Beat 2 (8.00s LTX) |
| 140 | Beat 2 prompt | `CLIPTextEncode` | 4. Beat 2 (8.00s LTX) |
| 151 | Beat 2 negative enhance | `EZNegativePromptEnhance` | 4. Beat 2 (8.00s LTX) |
| 141 | Beat 2 negative | `CLIPTextEncode` | 4. Beat 2 (8.00s LTX) |
| 142 | LTX Img→Video condition | `LTXVImgToVideo` | 4. Beat 2 (8.00s LTX) |
| 143 | LTX frame rate cond | `LTXVConditioning` | 4. Beat 2 (8.00s LTX) |
| 146 | Concat AV latents | `LTXVConcatAVLatent` | 4. Beat 2 (8.00s LTX) |
| 144 | Beat 2 KSampler | `KSampler` | 4. Beat 2 (8.00s LTX) |
| 147 | Separate AV latents | `LTXVSeparateAVLatent` | 4. Beat 2 (8.00s LTX) |
| 145 | VAE Decode | `VAEDecode` | 4. Beat 2 (8.00s LTX) |
| 150 | Audio VAE Decode | `LTXVAudioVAEDecode` | 4. Beat 2 (8.00s LTX) |
| 148 | Beat 2 video (MP4) — open node for prev… | `VHS_VideoCombine` | 4. Beat 2 (8.00s LTX) |
| 152 | Beat 2 last frame | `EZClipLastFrame` | 4. Beat 2 (8.00s LTX) |
| 153 | Save beat 2 last frame | `SaveImage` | 4. Beat 2 (8.00s LTX) |
| 189 | Beat 3 | `EZLTXPromptEnhance` | 5. Beat 3 (8.00s LTX) |
| 180 | Beat 3 prompt | `CLIPTextEncode` | 5. Beat 3 (8.00s LTX) |
| 191 | Beat 3 negative enhance | `EZNegativePromptEnhance` | 5. Beat 3 (8.00s LTX) |
| 181 | Beat 3 negative | `CLIPTextEncode` | 5. Beat 3 (8.00s LTX) |
| 182 | LTX Img→Video condition | `LTXVImgToVideo` | 5. Beat 3 (8.00s LTX) |
| 183 | LTX frame rate cond | `LTXVConditioning` | 5. Beat 3 (8.00s LTX) |
| 186 | Concat AV latents | `LTXVConcatAVLatent` | 5. Beat 3 (8.00s LTX) |
| 184 | Beat 3 KSampler | `KSampler` | 5. Beat 3 (8.00s LTX) |
| 187 | Separate AV latents | `LTXVSeparateAVLatent` | 5. Beat 3 (8.00s LTX) |
| 185 | VAE Decode | `VAEDecode` | 5. Beat 3 (8.00s LTX) |
| 190 | Audio VAE Decode | `LTXVAudioVAEDecode` | 5. Beat 3 (8.00s LTX) |
| 188 | Beat 3 video (MP4) — open node for prev… | `VHS_VideoCombine` | 5. Beat 3 (8.00s LTX) |
| 192 | Beat 3 last frame | `EZClipLastFrame` | 5. Beat 3 (8.00s LTX) |
| 193 | Save beat 3 last frame | `SaveImage` | 5. Beat 3 (8.00s LTX) |
| 229 | Beat 4 | `EZLTXPromptEnhance` | 6. Beat 4 (8.00s LTX) |
| 220 | Beat 4 prompt | `CLIPTextEncode` | 6. Beat 4 (8.00s LTX) |
| 231 | Beat 4 negative enhance | `EZNegativePromptEnhance` | 6. Beat 4 (8.00s LTX) |
| 221 | Beat 4 negative | `CLIPTextEncode` | 6. Beat 4 (8.00s LTX) |
| 222 | LTX Img→Video condition | `LTXVImgToVideo` | 6. Beat 4 (8.00s LTX) |
| 223 | LTX frame rate cond | `LTXVConditioning` | 6. Beat 4 (8.00s LTX) |
| 226 | Concat AV latents | `LTXVConcatAVLatent` | 6. Beat 4 (8.00s LTX) |
| 224 | Beat 4 KSampler | `KSampler` | 6. Beat 4 (8.00s LTX) |
| 227 | Separate AV latents | `LTXVSeparateAVLatent` | 6. Beat 4 (8.00s LTX) |
| 225 | VAE Decode | `VAEDecode` | 6. Beat 4 (8.00s LTX) |
| 230 | Audio VAE Decode | `LTXVAudioVAEDecode` | 6. Beat 4 (8.00s LTX) |
| 228 | Beat 4 video (MP4) — open node for prev… | `VHS_VideoCombine` | 6. Beat 4 (8.00s LTX) |
| 232 | Beat 4 last frame | `EZClipLastFrame` | 6. Beat 4 (8.00s LTX) |
| 233 | Save beat 4 last frame | `SaveImage` | 6. Beat 4 (8.00s LTX) |
| 234 | Check models | `EZModelCheck` | QUALITY |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.37.0 / lab `INPUT_TYPES` — not SD1.5 folklore.

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

**How it affects generation:** Wrong family = Queue error or a melted picture. Lab pins Apache Klein 4B. Klein 9B / FLUX.2-dev are opt-in NC. MiniMax is banned.

**This graph:** `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`

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

| Instance | Value |
| --- | --- |
| LTX-2.5 video VAE | `ltx-2.5-video-vae-bf16.safetensors` |
| LTX-2.5 audio VAE | `ltx-2.5-audio-vae-bf16.safetensors` |

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

**This graph:** `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`

#### `type`

Type `COMBO`.

CLIPType enum. Picks tokenizer + template.

**How it affects generation:** flux2 wraps Klein strings in a Qwen chat template — do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.

**This graph:** `ltxv`

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

### `LoadImage` — Load Image

Load a still from Comfy input/ (or upload).

!!! warning "Lab notes"

    I2V / edit graphs default example.png until you pick ez_still_*.png. App Mode shows Start image only when this node is wired.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `IMAGE` | out | `IMAGE` | RGB still. |
| `MASK` | out | `MASK` | Alpha if present. |

#### `image`

Type `STRING`.

Filename in input/.

**How it affects generation:** Point at the Klein still you just saved (ez_still_draft_*.png, ez_character_*.png, first.png).

**This graph:** `example.png`

#### `upload`

Type `COMBO`. Range / default: image.

Upload widget type.

**How it affects generation:** Leave image. This is the choose-file control, not a generation knob.

**This graph:** `image`

### `LTXVEmptyLatentAudio` — Empty LTX Audio Latent

Allocate a silent/world-audio latent matching video length.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio_vae` | in | `VAE` | Audio VAE (sets latent channels). |
| `Latent` | out | `LATENT` | Empty audio latent. |

#### `frames`

Type `INT`. Range / default: 193 Apps / 121 film.

Must match video length.

**How it affects generation:** Mismatch with LTXVImgToVideo length breaks concat.

**This graph:** `193`

#### `frame_rate`

Type `FLOAT`. Range / default: 24.0.

Audio timeline fps.

**How it affects generation:** Keep 24 with the rest of the printer.

**This graph:** `24.0`

#### `batch_size`

Type `INT`. Range / default: 1.

Clips per Queue.

**How it affects generation:** Stay 1.

**This graph:** `1`

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## motion/av/clip-chain Format / platform sets pixels (Custom uses Width × Height). Quality does not change size. LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).…`

```text
## motion/av/clip-chain

Format / platform sets pixels (Custom uses Width × Height). Quality does not change size.

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

Four LTX AV beats share one UNET / video VAE / audio VAE / CLIP. Last frame of beat N starts beat N+1. EZClipConcat stitches the four MP4s (hard cut). Primary output: `${COMFY_OUTPUT_DIR}/ez_clip_chain.mp4` plus per-beat VHS (`ez_clip_b0N_ltx_video`) and last-frame PNG (`ez_clip_b0N_last`). No full-batch SaveImage.

**8 seconds, 24 fps** (193 frames = 1+8n) chain-wide. Duration combo stays 5/8/10/12; mixed per-beat lengths are unsupported. Four × 8 s sequential prints are tens of minutes on GB10 — not a hang. Headroom preflight still applies at `start`.

Occupancy: ltx — stop Wan, podcast, music, other LTX. One GB10 job. Occupancy ltx XOR. `occupancy enter ltx` before Queue. No Klein identity on this canvas.

Duplicate Beat groups on canvas for beats 5–24:

1. Duplicate the last Beat group.
2. Set `VHS_VideoCombine.filename_prefix` to `ez_clip_b05_ltx_video` (then b06…).
3. Set last-frame SaveImage prefix to `ez_clip_b05_last`.
4. Wire previous `EZClipLastFrame.last_frame` → new `LTXVImgToVideo.image`.
5. Wire new `VHS_VideoCombine.Filenames` → the next free `EZClipConcat.clip_0N` (`clip_05` for the fifth beat).
6. Keep the shared UNET / VAE / CLIP / Format / Seed / Rewrite / Audio notes wires (do not duplicate loaders).
7. Save under `_user/` if you want a personal App; shipped `_lab` stays 4 beats.

Past 24 stems: host `./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 --cap-seconds <sum> --yes` (default `--files` cap is 90 s).

LTX-2.5 distilled AV. LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown is hidden on I2V.

LoadImage default example.png; after a still set ez_still_hero_*.png. Match input Format. MagCache off.
```

### `EZQuality` — Quality

Workflow-global quality combo. JS overlays family-specific sampler, UNET, CLIP, and VAE widgets.

!!! warning "Lab notes"

    custom freezes the last overlay. lab restores authored widgets. Free Commercial Use (<$10M) pins Apache Klein 4B (never 9B / FLUX.2-dev) and LTX-2.5 steps; Wan / audio / trellis are no-ops. ultra/max may select Klein 9B or FLUX.2-dev when those files are on disk (FLUX Non-Commercial, not YouTube-ok). Never changes size. Not --tier quality.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `quality` | out | `STRING` | Selected quality id. |

#### `quality`

Type `COMBO`. Range / default: lab.

custom freezes last overlay; lab restores graph defaults.

**How it affects generation:** Named qualities may swap UNET, CLIP, and VAE. Does not change size or length. Free Commercial Use (<$10M) is Klein 4B + LTX (never 9B / FLUX.2-dev). ultra/max need download-image --tier 9b or flux2-dev.

**This graph:** `lab`

**Other choices**

| Choice | What it does |
| --- | --- |
| `custom` | Freeze current widgets. Queue does not overlay. |
| `draft` | Faster Apache Klein 4B (NVFP4 if on disk). |
| `lab` | Authored lab widgets. Default. |
| `standard` | Distilled 4B, 8 steps, CFG 1.0. |
| `high` | Klein base 4B + CFG 3.5 when on disk; else extra distilled steps at CFG 1.0. |
| `Free Commercial Use (<$10M)` | Klein 4B stills (never 9B / FLUX.2-dev) + LTX-2.5 steps. Optional SeedVR2 polish on the PNG, not 4K. Wan / audio / trellis are no-ops. |
| `ultra` | Klein 9B distilled when on disk (FLUX Non-Commercial). Else high. |
| `max` | Klein 9B base or FLUX.2-dev when on disk (FLUX Non-Commercial). Else high. |

### `EZVideoFormat` — Format / platform (video)

Pick a Wan or LTX clip canvas (aspect or named platform).

!!! warning "Lab notes"

    Wan and LTX printers wire width/height into Wan22ImageToVideoLatent, LTXVImgToVideo, or EmptyLTXVLatentVideo. Hint feeds Enhance duration_hint on non-loop graphs. Duration writes LTX length (default 8 s). Quality does not change size. Match input snaps aspect to a loaded still.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Optional still used when Output size is Match input. |
| `width` | out | `INT` | Latent width (Wan ÷16, LTX ÷32). |
| `height` | out | `INT` | Latent height (Wan ÷16, LTX ÷32). |
| `hint` | out | `STRING` | Enhance duration / framing line. |
| `prefix` | out | `STRING` | Optional filename prefix (often unwired). |

#### `family`

Type `COMBO`. Range / default: Wan 5B / LTX-2.5.

Which VAE grid to use.

**How it affects generation:** Wan snaps ÷16 (max 1024). LTX snaps ÷32 (max 1280). App Mode hides this — occupancy already picks the model.

**This graph:** `LTX-2.5`

**Other choices**

| Choice | What it does |
| --- | --- |
| `Wan 5B` | wan VAE grid ÷16. |
| `LTX-2.5` | ltx VAE grid ÷32. |

#### `format`

Type `COMBO`. Range / default: 16:9 YouTube / 9:16 Shorts / Custom.

Aspect or named platform job.

**How it affects generation:** Preset writes pixels and Rewrite prompt framing. Custom uses Width × Height. Does not change Quality, length, CLIP, or VAE.

**This graph:** `LTX · 16:9 YouTube (1280×704)`

**Other choices**

| Choice | What it does |
| --- | --- |
| `Custom` | Width × Height widgets, snapped to the Family VAE grid. |
| `Wan · 16:9 YouTube (832×480)` | 832×480. wan. |
| `Wan · 16:9 mid (1024×576)` | 1024×576. wan. |
| `Wan · 9:16 Shorts (480×832)` | 480×832. wan. |
| `Wan · 1:1 square (768×768)` | 768×768. wan. |
| `LTX · 16:9 YouTube (1280×704)` | 1280×704. ltx. |
| `LTX · 9:16 Shorts (768×1280)` | 768×1280. ltx. |
| `LTX · 1:1 square (768×768)` | 768×768. ltx. |
| `LTX · 4:5 portrait (1024×1280)` | 1024×1280. ltx. |

#### `width`

Type `INT`. Range / default: 16–1280.

Custom width.

**How it affects generation:** Used when Format is Custom. Presets ignore this widget at Queue. LTX Custom snaps 720→704.

**This graph:** `1280`

#### `height`

Type `INT`. Range / default: 16–1280.

Custom height.

**How it affects generation:** Used when Format is Custom. Presets ignore this widget at Queue.

**This graph:** `704`

#### `size_mode`

Type `COMBO`. Range / default: Match input / Force format.

Match a loaded still's aspect, or keep Format / platform.

**How it affects generation:** Match input (default) picks the nearest family aspect row when a still is loaded. Force format keeps the Format pick. Quality does not change size.

**This graph:** `Match input`

#### `duration_s`

Type `COMBO`. Range / default: 5 / 8 / 10 / 12 seconds.

LTX clip length.

**How it affects generation:** Default 8 seconds (193 frames, 1+8n). Frontend writes latent length. Wan 5B stays 5 seconds. Film printers stay 5 seconds / 121.

**This graph:** `8 seconds`

### `EZImageDescribe` — Describe image

Caption a source still so Prompt Enhance can name inventory and lettering.

!!! warning "Lab notes"

    Off (default) returns empty and does not load the describe GGUF. Opt-in: download-llm --tier describe (Qwen2.5-VL-3B Apache).

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Source still. Lazy — skipped when enable is off. |
| `caption` | out | `STRING` | Short caption, or empty. |

#### `enable`

Type `BOOLEAN`. Range / default: off.

Run the captioner.

**How it affects generation:** Off skips the VLM. On needs download-llm --tier describe.

**This graph:** `false`

### `EZDCCOccupancyGate` — Occupancy gate

Pass-through IMAGE that fail-closes on occupancy XOR. Does not start Compose.

!!! warning "Lab notes"

    Missing .occupancy.json passes. idle / blender-desk / llm-desk / mismatch fail.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Still to gate. |
| `image` | out | `IMAGE` | Same still if occupancy matches. |

#### `required_mode`

Type `COMBO`.

Heavy GPU mode that must already be entered.

**How it affects generation:** klein / wan / ltx / trellis. Pick the family you are about to Queue.

**This graph:** `ltx`

**Other choices**

| Choice | What it does |
| --- | --- |
| `klein` | Klein 4B stills. |
| `trellis` | TRELLIS.2. |
| `wan` | Wan 5B. |
| `ltx` | LTX-2.5. |

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
| Seed | `42` |
| Rewrite prompt | `true` |
| Audio notes | `world SFX matching the start image, no score` |
| Logline / context | `—` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Whether the primitive mutates after Queue.

**How it affects generation:** fixed keeps duration/context pinned.

**This graph (all 4 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

### `EZClipConcat` — Save clip chain (MP4)

Concat 1–24 duration-head MP4s. Cap is a ceiling, not a pad-to-runtime.

!!! warning "Lab notes"

    clip_01 required; clip_02…24 optional. Collect-until-gap (a hole refuses). v1 hard-cut only (xfade_cs=0). Master ≈ sum(stems); default cap 600 s, max 1800. No films/<slug>/publish copy.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `clip_01` | in | `VHS_FILENAMES` | First clip MP4. |
| `clip_02` | in | `VHS_FILENAMES` | Clip 02 MP4 (optional). |
| `clip_03` | in | `VHS_FILENAMES` | Clip 03 MP4 (optional). |
| `clip_04` | in | `VHS_FILENAMES` | Clip 04 MP4 (optional). |
| `clip_05` | in | `VHS_FILENAMES` | Clip 05 MP4 (optional). |
| `clip_06` | in | `VHS_FILENAMES` | Clip 06 MP4 (optional). |
| `clip_07` | in | `VHS_FILENAMES` | Clip 07 MP4 (optional). |
| `clip_08` | in | `VHS_FILENAMES` | Clip 08 MP4 (optional). |
| `clip_09` | in | `VHS_FILENAMES` | Clip 09 MP4 (optional). |
| `clip_10` | in | `VHS_FILENAMES` | Clip 10 MP4 (optional). |
| `clip_11` | in | `VHS_FILENAMES` | Clip 11 MP4 (optional). |
| `clip_12` | in | `VHS_FILENAMES` | Clip 12 MP4 (optional). |
| `clip_13` | in | `VHS_FILENAMES` | Clip 13 MP4 (optional). |
| `clip_14` | in | `VHS_FILENAMES` | Clip 14 MP4 (optional). |
| `clip_15` | in | `VHS_FILENAMES` | Clip 15 MP4 (optional). |
| `clip_16` | in | `VHS_FILENAMES` | Clip 16 MP4 (optional). |
| `clip_17` | in | `VHS_FILENAMES` | Clip 17 MP4 (optional). |
| `clip_18` | in | `VHS_FILENAMES` | Clip 18 MP4 (optional). |
| `clip_19` | in | `VHS_FILENAMES` | Clip 19 MP4 (optional). |
| `clip_20` | in | `VHS_FILENAMES` | Clip 20 MP4 (optional). |
| `clip_21` | in | `VHS_FILENAMES` | Clip 21 MP4 (optional). |
| `clip_22` | in | `VHS_FILENAMES` | Clip 22 MP4 (optional). |
| `clip_23` | in | `VHS_FILENAMES` | Clip 23 MP4 (optional). |
| `clip_24` | in | `VHS_FILENAMES` | Clip 24 MP4 (optional). |
| `disclosure` | in | `STRING` | EZFilmDisclosure text. |
| `path` | out | `STRING` | Published MP4 path. |

#### `prefix`

Type `STRING`. Range / default: ez_clip_chain.

Output filename stem.

**How it affects generation:** Writes ez_clip_chain.mp4 under Comfy output. Rename if you Queue more than one chain.

**This graph:** `ez_clip_chain`

#### `cap_seconds`

Type `FLOAT`. Range / default: 600 default, 1800 max.

Fail-closed duration ceiling.

**How it affects generation:** Not a pad target. 4×8 s is ~32 s. Past 24 stems use concat-shots.sh --files … --cap-seconds.

**This graph:** `600.0`

#### `xfade_cs`

Type `INT`. Range / default: 0–50; v1 must be 0.

Audio acrossfade in centiseconds.

**How it affects generation:** v1 raises unless 0 (hard cut). Widget stays for a later overlap-off acrossfade.

**This graph:** `0`

### `EZFilmDisclosure` — LTX AI-media disclosure

Prepend the LTX Community License AI-media disclosure. Idempotent. Not legal advice.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `text` | out | `STRING` | Disclosure (+ optional extra). |

#### `text`

Type `STRING`.

Optional extra line after the stock disclosure.

**How it affects generation:** Empty = stock sentence only. Do not strip provenance.

### `EZLTXPromptEnhance` — LTX Prompt Enhance

Rewrite a lazy prompt for LTX-2.5 (present-tense paragraph, audio interleaved).

!!! warning "Lab notes"

    Off on 90s films, talking-head, authored showcase. On for generic 8 s printers.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `prompt` | out | `STRING` | Paragraph CLIP encodes. |

#### `sample`

Type `COMBO`. Range / default: custom.

Sample or Custom.

**How it affects generation:** Custom keeps the textarea.

**This graph (all 4 instances):** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored LTX paragraph.

**How it affects generation:** I2V: start image holds look; prompt is motion + world SFX. Dialogue belongs in "quotes" only if you asked for speech.

| Instance | Value |
| --- | --- |
| Beat 1 | `The start image holds as the first frame. The camera dollies in slowly toward t…` |
| Beat 2 | `The start image holds as the first frame. The camera continues the slow dolly, …` |
| Beat 3 | `The start image holds as the first frame. The subject continues the same action…` |
| Beat 4 | `The start image holds as the first frame. Motion settles: the camera eases to a…` |

#### `enhance`

Type `BOOLEAN`.

Run the rewriter.

**How it affects generation:** Off keeps authored film/shot text pinned.

**This graph (all 4 instances):** `true`

#### `mode`

Type `COMBO`.

t2v vs i2v vs iclora system prompt.

**How it affects generation:** i2v when a start still is wired. iclora describes look, not the control type.

**This graph (all 4 instances):** `i2v`

**Other choices**

| Choice | What it does |
| --- | --- |
| `t2v` | Text to AV. |
| `i2v` | Start still owns look. |
| `iclora` | Union Control look/materials; guide owns blocking. |

#### `duration_hint`

Type `STRING`. Range / default: 8 seconds, 24 fps.

Duration hint.

**How it affects generation:** Does not set 193 frames — LTXVImgToVideo does. Film printers stay 5 seconds / 121.

**This graph (all 4 instances):** `8 seconds, 24 fps`

#### `audio_notes`

Type `STRING`.

World SFX / no-score policy.

**How it affects generation:** Lab 8 s Apps ask for world SFX matching the start image, no score.

**This graph (all 4 instances):** `world SFX matching the start image, no score`

#### `style`

Type `COMBO`. Range / default: none.

Look reference. Ignored on I2V.

**How it affects generation:** Start frame owns look.

**This graph (all 4 instances):** `none`

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
| `webtoon_color_hold` | Webtoon color hold, hard flats. |
| `ova_paint_nineties` | 1990s OVA paint, acetate cel. |
| `late_night_cel_city` | Late-night cel city, neon planes. |
| `watercolor_layout_bg` | Watercolor layout background, paper tooth. |
| `thick_ink_action_still` | Thick-ink action still, speedlines. |
| `soft_pastel_romance_still` | Soft pastel romance still, airbrush blush. |
| `analog_acetate_cel` | Analog acetate cel, pegbar. |
| `digital_paint_anime_still` | Digital-paint anime still, soft blends. |
| `limited_tv_color_hold` | Limited TV color hold, small palette. |
| `sparkle_highlight_anime` | Sparkle-highlight anime, catchlights. |
| `heavy_screentone_color` | Heavy screentone color, tone sheets. |
| `school_rooftop_cel` | School-rooftop cel, chain-link sky. |
| `train_window_anime_bg` | Train-window anime background, BG streaks. |
| `festival_lantern_cel` | Festival-lantern cel, paper glow. |
| `rain_reflection_anime` | Rain-reflection anime, wet cel. |
| `winter_breath_cel` | Winter-breath cel, vapor clouds. |
| `summer_heat_cel` | Summer-heat cel, heat haze. |
| `mecha_cockpit_cel` | Mecha-cockpit cel, instrument glow. |
| `magic_circle_cel` | Magic-circle cel, glyph glow. |
| `food_steam_anime` | Food-steam anime, steam curls. |
| `sports_speedline_cel` | Sports-speedline cel, radial lines. |
| `horror_shadow_cel` | Horror-shadow cel, graphic bands. |
| `slice_of_life_flat` | Slice-of-life flat cel, household props. |
| `historical_ink_anime` | Historical ink anime, ink-wash architecture. |
| `stage_spotlight_cel` | Stage-spotlight cel, cone key. |
| `beach_sparkle_cel` | Beach-sparkle cel, water glitter. |
| `shrine_steps_cel` | Shrine-steps cel, dawn mist. |
| `subway_rush_cel` | Subway-rush cel, packed car. |
| `library_dust_cel` | Library-dust cel, sunshaft motes. |
| `rooftop_laundry_cel` | Rooftop-laundry cel, sheet lines. |
| `convenience_night_cel` | Convenience-night cel, interior glow. |
| `petal_fall_cel` | Petal-fall cel, blossom ticks. |
| `maple_path_cel` | Maple-path cel, fallen leaves. |
| `snow_footprint_cel` | Snow-footprint cel, trail of prints. |
| `cat_alley_cel` | Cat-alley cel, watching cat. |
| `bicycle_slope_cel` | Bicycle-slope cel, sky rim. |
| `river_firefly_cel` | River-firefly cel, firefly ticks. |
| `clock_tower_cel` | Clock-tower cel, unmarked face. |
| `greenhouse_cel_still` | Greenhouse cel still, glass dapples. |
| `bakery_dawn_cel` | Bakery-dawn cel, oven glow. |
| `radio_booth_cel` | Radio-booth cel, foam wedges. |
| `observatory_cel_still` | Observatory cel still, dome and stars. |
| `fishing_pier_cel` | Fishing-pier cel, wet planks. |
| `desert_bus_cel` | Desert-bus cel, heat haze. |
| `island_ferry_cel` | Island-ferry cel, wake water. |
| `attic_window_cel` | Attic-window cel, dust shaft. |
| `rooftop_pool_cel` | Rooftop-pool cel, water caustics. |
| `night_market_cel` | Night-market cel, stall glow. |
| `dawn_switchback_cel` | Dawn-switchback cel, raking dawn. |
| `clockwork_festival_cel` | Clockwork-festival cel, decorative gears. |
| `rubber_hose_ink` | Rubber-hose ink, looping limbs. |
| `sunday_funnies_halftone` | Sunday-funnies halftone, newsprint primaries. |
| `editorial_gag_panel` | Editorial gag panel, brush contour. |
| `limited_tv_paint` | Limited TV paint, tiny paint set. |
| `crayon_saturday_still` | Crayon Saturday still, wax stroke. |
| `marker_comp_toon` | Marker-comp toon, felt-tip bleed. |
| `flat_shape_toon` | Flat-shape toon, simple geometry. |
| `clay_outline_toon` | Clay-outline toon, rounded contour. |
| `newsprint_comic_color` | Newsprint comic color, off-register primaries. |
| `brush_pen_toon` | Brush-pen toon, dry-brush contour. |
| `chalkboard_toon` | Chalkboard toon, chalk dust. |
| `felt_board_toon` | Felt-board toon, cut-cloth shapes. |
| `sticker_sheet_toon` | Sticker-sheet toon, die-cut gloss. |
| `balloon_animal_toon` | Balloon-animal toon, inflated gloss. |
| `woodcut_toon` | Woodcut toon, gouge marks. |
| `linocut_toon` | Linocut toon, rolled-ink flats. |
| `collage_cutout_toon` | Collage-cutout toon, scissor edges. |
| `puppet_show_toon` | Puppet-show toon, cloth and rods. |
| `matchstick_toon` | Matchstick toon, stick limbs. |
| `doodle_margin_toon` | Doodle-margin toon, ruled paper. |
| `cereal_box_toon` | Cereal-box toon, loud pack art. |
| `birthday_card_toon` | Birthday-card toon, foil balloons. |
| `sidewalk_chalk_toon` | Sidewalk-chalk toon, pavement tooth. |
| `window_paint_toon` | Window-paint toon, tempera on glass. |
| `yarn_outline_toon` | Yarn-outline toon, stitched contour. |
| `button_eye_toon` | Button-eye toon, felt and buttons. |
| `paper_bag_toon` | Paper-bag toon, kraft crayon. |
| `sock_puppet_toon` | Sock-puppet toon, googly craft eyes. |
| `party_banner_toon` | Party-banner toon, bunting shapes. |
| `ice_cream_toon` | Ice-cream toon, drip scoops. |
| `circus_poster_toon` | Circus-poster toon, big-top shapes. |
| `toy_block_toon` | Toy-block toon, wooden cubes. |
| `marble_run_toon` | Marble-run toon, glass orbs. |
| `kaleidoscope_toon` | Kaleidoscope toon, mirrored shards. |
| `snow_globe_toon` | Snow-globe toon, glitter in glass. |
| `cookie_cutter_toon` | Cookie-cutter toon, cut dough. |
| `shadow_puppet_toon` | Shadow-puppet toon, backlit silhouettes. |
| `flipbook_toon` | Flipbook toon, page corners. |
| `stencil_spray_toon` | Stencil-spray toon, crisp masks. |
| `gag_balloon_toon` | Gag-balloon toon, empty speech shapes. |
| `pie_gag_toon` | Pie-gag toon, flying cream. |
| `anvil_gag_toon` | Anvil-gag toon, scale gag. |
| `spring_shoes_toon` | Spring-shoes toon, coiled bounce. |
| `cannon_gag_toon` | Cannon-gag toon, smoke puffs. |
| `trampoline_toon` | Trampoline toon, stretch bounce. |
| `whoopee_cushion_toon` | Whoopee-cushion toon, rubber disc. |
| `banana_peel_toon` | Banana-peel toon, slip setup. |
| `magnet_gag_toon` | Magnet-gag toon, flying metal. |
| `invisible_ink_toon` | Invisible-ink toon, UV glow doodle. |
| `jack_in_box_toon` | Jack-in-box toon, sprung lid. |
| `stop_motion_felt` | Stop-motion felt, felt nap. |
| `paper_cutout_two_five` | Paper cutout 2.5D, stacked card planes. |
| `paint_on_glass` | Paint-on-glass, wet pigment smears. |
| `toon_shaded_cgi` | Toon-shaded CGI, banded shadow. |
| `claymation_armature` | Claymation armature, thumbprints. |
| `sand_animation_still` | Sand animation still, poured grains. |
| `pinboard_animation` | Pinboard animation, raised pins. |
| `hinged_silhouette_sheet` | Hinged silhouette sheet, hinged black figures. |
| `pixilation_live` | Pixilation live, stepped pose. |
| `rotoscope_paint` | Rotoscope paint, traced contour. |
| `replacement_animation` | Replacement animation, swapped mouth card. |
| `cutout_multiplane` | Cutout multiplane, glass layers. |
| `object_animation_still` | Object animation still, posed household items. |
| `stratacut_clay` | Stratacut clay, sliced color loaf. |
| `time_lapse_animation` | Time-lapse animation still, stepped daylight. |
| `go_motion_still` | Go-motion still, smear tails. |
| `clay_morph_still` | Clay-morph still, mid-reshape. |
| `wire_puppet_still` | Wire-puppet still, visible armature. |
| `foam_latex_puppet` | Foam-latex puppet, painted foam skin. |
| `ball_and_socket_puppet` | Ball-and-socket puppet, machined joints. |
| `pixel_stop_motion` | Pixel stop-motion, physical beads. |
| `lego_brick_still` | Brick-built animation still, interlocking studs. |
| `wool_needle_felt` | Wool needle-felt, stab texture. |
| `origami_animation` | Origami animation still, fold creases. |
| `kirigami_still` | Kirigami still, cut-and-fold architecture. |
| `zoetrope_still` | Zoetrope still, sequential strip. |
| `phenakistoscope_still` | Phenakistoscope still, radial sequence. |
| `thaumatrope_still` | Thaumatrope still, two-sided hold. |
| `flipbook_stack_3d` | Flipbook stack 3D, page thickness. |
| `cymatics_animation` | Cymatics animation still, standing-wave powder. |
| `ferrofluid_still` | Ferrofluid still, spiked magnetic liquid. |
| `ink_in_water_still` | Ink-in-water still, blooming plumes. |
| `oil_on_water_still` | Oil-on-water still, swirling film. |
| `smoke_tank_still` | Smoke-tank still, volume wisps. |
| `sparkler_trails_still` | Sparkler-trails still, held light paths. |
| `light_painting_anim` | Light-painting animation still, drawn light path. |
| `diorama_tilt_band` | Diorama tilt-band still, diorama world. |
| `forced_perspective_set` | Forced-perspective set still, giant prop. |
| `rear_projection_still` | Rear-projection still, screen world. |
| `front_projection_still` | Front-projection still, reflected plate. |
| `motion_control_miniature` | Motion-control miniature still, repeatable rig. |
| `animatronic_still` | Animatronic still, mechanical brows. |
| `suitmation_still` | Suitmation still, built creature suit. |
| `prosthetic_creature_still` | Prosthetic creature still, foam appliances. |
| `stop_frame_city` | Stop-frame city still, block metropolis. |
| `garden_stop_motion` | Garden stop-motion still, posed plants. |
| `kitchen_stop_motion` | Kitchen stop-motion still, walking utensils. |
| `office_stop_motion` | Office stop-motion still, marching stationery. |
| `workshop_stop_motion` | Workshop stop-motion still, posed tools. |
| `harbor_stop_motion` | Harbor stop-motion still, tactile toy quay. |

#### `catalog`

Type `STRING`.

Sample-catalog id.

**How it affects generation:** Leave as stamped.

**This graph (all 4 instances):** `motion/av/clip-chain`

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
| Beat 1 prompt | `The start image holds as the first frame. The camera dollies in slowly toward t…` |
| Beat 1 negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |
| Beat 2 prompt | `The start image holds as the first frame. The camera continues the slow dolly, …` |
| Beat 2 negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |
| Beat 3 prompt | `The start image holds as the first frame. The subject continues the same action…` |
| Beat 3 negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |
| Beat 4 prompt | `The start image holds as the first frame. Motion settles: the camera eases to a…` |
| Beat 4 negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |

### `EZNegativePromptEnhance` — Negative Prompt Enhance

Rewrite a negative CLIP seed against the final positive. Stays on when Rewrite prompt is off.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `positive` | in | `STRING` | Final positive CLIP string (enhance output, Prompt Join, or shot bundle). |
| `prompt` | out | `STRING` | Negative string. |

#### `prompt`

Type `STRING`.

Negative seed (artifacts, not style).

**How it affects generation:** FLUX-family models do not use negatives well. Keep this short; put constraints in the positive.

**This graph (all 4 instances):** `morphing, identity drift, warping objects, face melting, flicker, jitter, frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, watermark, burned-in text`

#### `enhance`

Type `BOOLEAN`.

Rewrite negative. App label: Rewrite negative.

**How it affects generation:** Stays on when Rewrite prompt is off. Off skips the LLM; the conflict filter still runs.

**This graph (all 4 instances):** `true`

#### `family`

Type `COMBO`.

Which negative family.

**How it affects generation:** Must match the UNET on the canvas.

**This graph (all 4 instances):** `ltx`

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

### `LTXVImgToVideo` — LTX Image to Video

Condition LTX on a start image and allocate the video latent.

!!! warning "Lab notes"

    ÷32 spatial, length 1+8n. Standalone Apps 1280×704×193. Film printers 1280×704×121. Shorts 768×1280. Some shot graphs still store 120 and rely on ez_ltx_spatial to snap.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `positive` | in | `CONDITIONING` | LTX prompt cond. |
| `negative` | in | `CONDITIONING` | Negative cond. |
| `vae` | in | `VAE` | ltx-2.5-video-vae. |
| `image` | in | `IMAGE` | Start still (Klein feeder). |
| `positive` | out | `CONDITIONING` | Image-conditioned positive. |
| `negative` | out | `CONDITIONING` | Image-conditioned negative. |
| `latent` | out | `LATENT` | Video latent. |

#### `width`

Type `INT`. Range / default: 1280 / 768.

Frame width.

**How it affects generation:** Must be ÷32. 720p width is fine; height 720 is not.

**This graph (all 4 instances):** `1280`

#### `height`

Type `INT`. Range / default: 704 / 1280.

Frame height.

**How it affects generation:** 704 not 720. Shorts 1280.

**This graph (all 4 instances):** `704`

#### `length`

Type `INT`. Range / default: 193 Apps / 121 film = 1+8n.

Frame count.

**How it affects generation:** Standalone Apps default 193 @ 24 fps ≈ 8.04 s. Film printers stay 121 (~5.04 s). Do not type a 90 s length.

**This graph (all 4 instances):** `193`

#### `batch_size`

Type `INT`. Range / default: 1.

Clips per Queue.

**How it affects generation:** Stay 1.

**This graph (all 4 instances):** `1`

### `LTXVConditioning` — LTX Conditioning

Stamp frame-rate onto LTX positive/negative cond.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `positive` | in | `CONDITIONING` | Prompt cond. |
| `negative` | in | `CONDITIONING` | Negative cond. |
| `positive` | out | `CONDITIONING` | FPS-stamped positive. |
| `negative` | out | `CONDITIONING` | FPS-stamped negative. |

#### `frame_rate`

Type `FLOAT`. Range / default: 24.0.

Frames per second written into cond.

**How it affects generation:** Must match VHS frame_rate (24). Mismatch makes motion too fast/slow.

**This graph (all 4 instances):** `24.0`

### `LTXVConcatAVLatent` — LTX Concat AV Latent

Join video + audio latents into one joint AV latent for the sampler.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `video_latent` | in | `LATENT` | Video latent. |
| `audio_latent` | in | `LATENT` | Empty or encoded audio latent. |
| `latent` | out | `LATENT` | Joint AV latent. |

No widgets. Sockets only.

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

**This graph (all 4 instances):** `42`

#### `control_after_generate`

Type `COMBO`. Range / default: fixed (lab).

What happens to seed after Queue.

**How it affects generation:** fixed keeps iteration honest while you change the prompt.

**This graph (all 4 instances):** `fixed`

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

**This graph (all 4 instances):** `20`

#### `cfg`

Type `FLOAT`. Range / default: 0–100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5.

Classifier-free guidance scale.

**How it affects generation:** Distilled Klein is CFG 1.0 — raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.

**This graph (all 4 instances):** `1.0`

#### `sampler_name`

Type `COMBO`. Range / default: euler (most lab); uni_pc (Wan).

ODE / SDE algorithm that removes noise.

**How it affects generation:** euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.

**This graph (all 4 instances):** `euler`

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
| `cfgpp_ud10_ab` | CFG++ UD10 AB. Added in ComfyUI 0.35; not a lab default. |
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

**This graph (all 4 instances):** `simple`

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

**This graph (all 4 instances):** `1.0`

### `LTXVSeparateAVLatent` — LTX Separate AV Latent

Split a joint AV latent after sampling.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `av_latent` | in | `LATENT` | KSampler output. |
| `video_latent` | out | `LATENT` | Picture latent → VAEDecode. |
| `audio_latent` | out | `LATENT` | Audio latent → LTXVAudioVAEDecode (not on a2v). |

No widgets. Sockets only.

### `VAEDecode` — VAE Decode

Decode image/video latents to pixels.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | KSampler output (video or still). |
| `vae` | in | `VAE` | Matching family VAE. |
| `IMAGE` | out | `IMAGE` | Frames or still. |

No widgets. Sockets only.

### `LTXVAudioVAEDecode` — LTX Audio VAE Decode

Decode LTX audio latent to AUDIO for the MP4 mux.

!!! warning "Lab notes"

    Skipped on motion/av/audio-to-video-8s (original wav is muxed).

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | Audio latent. |
| `audio_vae` | in | `VAE` | ltx-2.5-audio-vae-bf16. |
| `Audio` | out | `AUDIO` | World bed / dialogue stem. |

No widgets. Sockets only.

### `VHS_VideoCombine` — VHS Video Combine

Encode frames (and optional audio) to MP4 or GIF.

!!! warning "Lab notes"

    Lab clips set save_output true. After Queue open the node for preview. GIF graphs use image/gif + pingpong.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `images` | in | `IMAGE` | Decoded frames. |
| `audio` | in | `AUDIO` | LTX decoded audio or unused. |
| `meta_batch` | in | `VHS_BatchManager` | Optional batch manager (unwired). |
| `vae` | in | `VAE` | Optional (unwired). |
| `Filenames` | out | `VHS_FILENAMES` | Path list for EZFilmConcat. |

#### `frame_rate`

Type `FLOAT`. Range / default: lab 24 (GIF 12/16).

Output frames per second.

**How it affects generation:** 24 fps is the lab motion/AV printer. GIF loops use 12. Changing fps without changing frame count changes duration.

**This graph (all 4 instances):** `24`

#### `loop_count`

Type `INT`. Range / default: 0 = infinite in players that honor it.

How many times the file loops.

**How it affects generation:** 0 is the lab default (play once / player default).

**This graph (all 4 instances):** `0`

#### `filename_prefix`

Type `STRING`.

Save prefix under the output folder.

**How it affects generation:** Lab prefixes start with ez_. The host file is ${COMFY_OUTPUT_DIR}/<prefix>_*.mp4 (or .gif).

| Instance | Value |
| --- | --- |
| Beat 1 video (MP4) — open node for prev… | `ez_clip_b01_ltx_video` |
| Beat 2 video (MP4) — open node for prev… | `ez_clip_b02_ltx_video` |
| Beat 3 video (MP4) — open node for prev… | `ez_clip_b03_ltx_video` |
| Beat 4 video (MP4) — open node for prev… | `ez_clip_b04_ltx_video` |

#### `format`

Type `COMBO`.

Container / codec.

**How it affects generation:** video/h264-mp4 is every lab clip except motion/loops/gif-loop (image/gif).

**This graph (all 4 instances):** `video/h264-mp4`

**Other choices**

| Choice | What it does |
| --- | --- |
| `video/h264-mp4` | H.264 MP4. Lab default; save_output must stay true. |
| `image/gif` | Animated GIF. motion/loops/gif-loop only. |

#### `pix_fmt`

Type `COMBO`. Range / default: yuv420p.

Pixel format for H.264.

**How it affects generation:** yuv420p plays everywhere. Other formats can break QuickTime/YouTube.

**This graph (all 4 instances):** `yuv420p`

#### `crf`

Type `INT`. Range / default: lab 18.

H.264 constant-rate-factor. Lower is bigger/cleaner.

**How it affects generation:** 18 is the lab visually-lossless-ish setting. Raising CRF shrinks files and adds blockiness.

**This graph (all 4 instances):** `18`

#### `save_metadata`

Type `BOOLEAN`.

Embed workflow JSON in the file.

**How it affects generation:** true keeps provenance on the MP4.

**This graph (all 4 instances):** `true`

#### `trim_to_audio`

Type `BOOLEAN`.

Cut picture to audio length.

**How it affects generation:** Lab false except when you mean to lock to a bed. ltx/a2v muxes the original wav instead.

**This graph (all 4 instances):** `false`

#### `pingpong`

Type `BOOLEAN`.

Play frames forward then reverse.

**How it affects generation:** true on motion/loops/gif-loop, bumper-loop, sticker-loop. false on 5 s narrative prints.

**This graph (all 4 instances):** `false`

#### `save_output`

Type `BOOLEAN`.

Write the file to disk.

**How it affects generation:** Lab video graphs require true. After Queue, open the node for the inline preview.

**This graph (all 4 instances):** `true`

### `EZClipLastFrame` — Last frame (IMAGE)

Return the last frame of an IMAGE batch (index -1) as the next clip's I2V start.

!!! warning "Lab notes"

    Duration-safe. Do not hardcode ImageFromBatch 120 — legal last indices are 120 / 192 / 240 / 288.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Decoded video batch. |
| `last_frame` | out | `IMAGE` | Last frame (batch dim 1). |

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
| Save beat 1 last frame | `ez_clip_b01_last` |
| Save beat 2 last frame | `ez_clip_b02_last` |
| Save beat 3 last frame | `ez_clip_b03_last` |
| Save beat 4 last frame | `ez_clip_b04_last` |

### `EZModelCheck` — Check models

Manual disk check for occupancy + Quality weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph:** `Click Check models. Queue does not run this node.`
