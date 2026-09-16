---
title: shorts/tide-table/act-03
description: One-click dawn skiff · Fog and spit: 18 LTX 5.00s AV shots + stitch Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots
tags: [workflows, generated, comfyui, shorts]
---

# shorts/tide-table/act-03

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `shorts/tide-table/act-03` from Apps or Workflows.

> Generated from `workflows/_lab/shorts/tide-table/act-03.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **film**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## shorts/tide-table/act-03

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/outputs`) as a faststart H.264 master, plus an HTML sidecar. After Queue, a **Film ready** overlay offers play and download. Per-shot VHS nodes remain for inspection. Optional board: studio-ui `/watch/<slug>`.

One-click 90s unit (dawn skiff · Fog and spit): Klein identity still + 18 sequential LTX 5.00s AV prints + in-graph stitch.
Models: Klein 4B distilled FP8 (identity still, 4-step, Enhance **off**, t2i mode) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

1. Queue **once**. Klein runs first; models unload; then 18 × 5.00s LTX prints chain last-frame → next start.
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) — expected, not a hang.
3. The MP4 is already on disk at `${COMFY_OUTPUT_DIR}/ez_tidetable_90s.mp4` (act graphs write `ez_tidetable_actN_90s.mp4`). A **Film ready** overlay plays it. Copy off the Spark with scp.
4. Optional single-shot iterate: **ltx/i2v-shot**. Optional silent rehearsal: **wan/i2v-shot**.
5. Spark-farm / host stitch fallback: `./scripts/utilities/concat-shots.sh --film tide-table --yes`

Do not Queue a 90s denoise (keep 121-frame / 1+8n widgets). US-safe local pack only. No score.
Prompt enhance is **off** so the pinned identity and each baked LTX I2V paragraph are encoded as written. The identity STRING is wired into each shot enhance as context (used only if you turn Enhance on).

This graph is **act 3/5** of a 7.5 min film (90 × 5.00s). Act 3 LoadImage should be the previous act last frame (ez_tidetable_b12_s3_last_*.png). In-graph stitch writes `ez_tidetable_act3_90s.mp4`. After all five acts: `concat-shots.sh --film tide-table --yes` → `ez_tidetable_450s.mp4`.

Occupancy: film — stop everything else on that Spark. One GB10 job.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **shorts/tide-table/act-03** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart TB
  G1__Identity__Klein_["1. Identity (Klein)"]
  G2__LTX_models["2. LTX models"]
  G3__Beat_1__3___5_00s_LTX_["3. Beat 1 (3 × 5.00s LTX)"]
  G4__Beat_2__3___5_00s_LTX_["4. Beat 2 (3 × 5.00s LTX)"]
  G5__Beat_3__3___5_00s_LTX_["5. Beat 3 (3 × 5.00s LTX)"]
  G6__Beat_4__3___5_00s_LTX_["6. Beat 4 (3 × 5.00s LTX)"]
  G7__Beat_5__3___5_00s_LTX_["7. Beat 5 (3 × 5.00s LTX)"]
  G8__Beat_6__3___5_00s_LTX_["8. Beat 6 (3 × 5.00s LTX)"]
  G9__Publish_90s_MP4["9. Publish 90s MP4"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Klein 4B distilled FP8 | `UNETLoader` | 1. Identity (Klein) |
| 2 | Qwen3-4B TE | `CLIPLoader` | 1. Identity (Klein) |
| 3 | Flux2 VAE | `VAELoader` | 1. Identity (Klein) |
| 4 | Positive | `CLIPTextEncode` | 1. Identity (Klein) |
| 5 | Negative | `CLIPTextEncode` | 1. Identity (Klein) |
| 6 | Latent 1280x704 batch 1 | `EmptyFlux2LatentImage` | 1. Identity (Klein) |
| 7 | KSampler | `KSampler` | 1. Identity (Klein) |
| 8 | VAE Decode | `VAEDecode` | 1. Identity (Klein) |
| 9 | Save identity PNG | `SaveImage` | 1. Identity (Klein) |
| 10 | Operator note — one-click film | `Note` | 1. Identity (Klein) |
| 11 | Klein Prompt Enhance | `EZKleinPromptEnhance` | 1. Identity (Klein) |
| 12 | Negative Prompt Enhance | `EZNegativePromptEnhance` | 1. Identity (Klein) |
| 13 | Quality | `EZQuality` | Ungrouped |
| 52 | tide-table 90s shot map | `MarkdownNote` | Ungrouped |
| 50 | Unload models (pass IMAGE) | `EZUnloadModels` | 1. Identity (Klein) |
| 100 | LTX-2.5 distilled INT8-convrot | `UNETLoader` | 2. LTX models |
| 101 | LTX-2.5 video VAE | `VAELoader` | 2. LTX models |
| 102 | Gemma4-with-proj (ltxv) | `CLIPLoader` | 2. LTX models |
| 103 | LTX-2.5 audio VAE | `VAELoader` | 2. LTX models |
| 104 | Negative | `CLIPTextEncode` | 2. LTX models |
| 105 | Empty LTX audio latent | `LTXVEmptyLatentAudio` | 2. LTX models |
| 900 | Save act 3 (90s MP4) — play / download | `EZFilmConcat` | 9. Publish 90s MP4 |
| 211 | b1 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 3. Beat 1 (3 × 5.00s LTX) |
| 200 | b1 s1 LTX I2V | `CLIPTextEncode` | 3. Beat 1 (3 × 5.00s LTX) |
| 201 | LTX Img→Video condition | `LTXVImgToVideo` | 3. Beat 1 (3 × 5.00s LTX) |
| 202 | LTX frame rate cond | `LTXVConditioning` | 3. Beat 1 (3 × 5.00s LTX) |
| 203 | Concat AV latents | `LTXVConcatAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 204 | KSampler | `KSampler` | 3. Beat 1 (3 × 5.00s LTX) |
| 205 | Separate AV latents | `LTXVSeparateAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 206 | VAE Decode | `VAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 207 | Audio VAE Decode | `LTXVAudioVAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 208 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 3. Beat 1 (3 × 5.00s LTX) |
| 209 | Last frame | `ImageFromBatch` | 3. Beat 1 (3 × 5.00s LTX) |
| 210 | Save last frame | `SaveImage` | 3. Beat 1 (3 × 5.00s LTX) |
| 231 | b1 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 3. Beat 1 (3 × 5.00s LTX) |
| 220 | b1 s2 LTX I2V | `CLIPTextEncode` | 3. Beat 1 (3 × 5.00s LTX) |
| 221 | LTX Img→Video condition | `LTXVImgToVideo` | 3. Beat 1 (3 × 5.00s LTX) |
| 222 | LTX frame rate cond | `LTXVConditioning` | 3. Beat 1 (3 × 5.00s LTX) |
| 223 | Concat AV latents | `LTXVConcatAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 224 | KSampler | `KSampler` | 3. Beat 1 (3 × 5.00s LTX) |
| 225 | Separate AV latents | `LTXVSeparateAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 226 | VAE Decode | `VAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 227 | Audio VAE Decode | `LTXVAudioVAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 228 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 3. Beat 1 (3 × 5.00s LTX) |
| 229 | Last frame | `ImageFromBatch` | 3. Beat 1 (3 × 5.00s LTX) |
| 230 | Save last frame | `SaveImage` | 3. Beat 1 (3 × 5.00s LTX) |
| 251 | b1 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 3. Beat 1 (3 × 5.00s LTX) |
| 240 | b1 s3 LTX I2V | `CLIPTextEncode` | 3. Beat 1 (3 × 5.00s LTX) |
| 241 | LTX Img→Video condition | `LTXVImgToVideo` | 3. Beat 1 (3 × 5.00s LTX) |
| 242 | LTX frame rate cond | `LTXVConditioning` | 3. Beat 1 (3 × 5.00s LTX) |
| 243 | Concat AV latents | `LTXVConcatAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 244 | KSampler | `KSampler` | 3. Beat 1 (3 × 5.00s LTX) |
| 245 | Separate AV latents | `LTXVSeparateAVLatent` | 3. Beat 1 (3 × 5.00s LTX) |
| 246 | VAE Decode | `VAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 247 | Audio VAE Decode | `LTXVAudioVAEDecode` | 3. Beat 1 (3 × 5.00s LTX) |
| 248 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 3. Beat 1 (3 × 5.00s LTX) |
| 249 | Last frame | `ImageFromBatch` | 3. Beat 1 (3 × 5.00s LTX) |
| 250 | Save last frame | `SaveImage` | 3. Beat 1 (3 × 5.00s LTX) |
| 271 | b2 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 4. Beat 2 (3 × 5.00s LTX) |
| 260 | b2 s1 LTX I2V | `CLIPTextEncode` | 4. Beat 2 (3 × 5.00s LTX) |
| 261 | LTX Img→Video condition | `LTXVImgToVideo` | 4. Beat 2 (3 × 5.00s LTX) |
| 262 | LTX frame rate cond | `LTXVConditioning` | 4. Beat 2 (3 × 5.00s LTX) |
| 263 | Concat AV latents | `LTXVConcatAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 264 | KSampler | `KSampler` | 4. Beat 2 (3 × 5.00s LTX) |
| 265 | Separate AV latents | `LTXVSeparateAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 266 | VAE Decode | `VAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 267 | Audio VAE Decode | `LTXVAudioVAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 268 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 4. Beat 2 (3 × 5.00s LTX) |
| 269 | Last frame | `ImageFromBatch` | 4. Beat 2 (3 × 5.00s LTX) |
| 270 | Save last frame | `SaveImage` | 4. Beat 2 (3 × 5.00s LTX) |
| 291 | b2 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 4. Beat 2 (3 × 5.00s LTX) |
| 280 | b2 s2 LTX I2V | `CLIPTextEncode` | 4. Beat 2 (3 × 5.00s LTX) |
| 281 | LTX Img→Video condition | `LTXVImgToVideo` | 4. Beat 2 (3 × 5.00s LTX) |
| 282 | LTX frame rate cond | `LTXVConditioning` | 4. Beat 2 (3 × 5.00s LTX) |
| 283 | Concat AV latents | `LTXVConcatAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 284 | KSampler | `KSampler` | 4. Beat 2 (3 × 5.00s LTX) |
| 285 | Separate AV latents | `LTXVSeparateAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 286 | VAE Decode | `VAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 287 | Audio VAE Decode | `LTXVAudioVAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 288 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 4. Beat 2 (3 × 5.00s LTX) |
| 289 | Last frame | `ImageFromBatch` | 4. Beat 2 (3 × 5.00s LTX) |
| 290 | Save last frame | `SaveImage` | 4. Beat 2 (3 × 5.00s LTX) |
| 311 | b2 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 4. Beat 2 (3 × 5.00s LTX) |
| 300 | b2 s3 LTX I2V | `CLIPTextEncode` | 4. Beat 2 (3 × 5.00s LTX) |
| 301 | LTX Img→Video condition | `LTXVImgToVideo` | 4. Beat 2 (3 × 5.00s LTX) |
| 302 | LTX frame rate cond | `LTXVConditioning` | 4. Beat 2 (3 × 5.00s LTX) |
| 303 | Concat AV latents | `LTXVConcatAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 304 | KSampler | `KSampler` | 4. Beat 2 (3 × 5.00s LTX) |
| 305 | Separate AV latents | `LTXVSeparateAVLatent` | 4. Beat 2 (3 × 5.00s LTX) |
| 306 | VAE Decode | `VAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 307 | Audio VAE Decode | `LTXVAudioVAEDecode` | 4. Beat 2 (3 × 5.00s LTX) |
| 308 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 4. Beat 2 (3 × 5.00s LTX) |
| 309 | Last frame | `ImageFromBatch` | 4. Beat 2 (3 × 5.00s LTX) |
| 310 | Save last frame | `SaveImage` | 4. Beat 2 (3 × 5.00s LTX) |
| 331 | b3 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 5. Beat 3 (3 × 5.00s LTX) |
| 320 | b3 s1 LTX I2V | `CLIPTextEncode` | 5. Beat 3 (3 × 5.00s LTX) |
| 321 | LTX Img→Video condition | `LTXVImgToVideo` | 5. Beat 3 (3 × 5.00s LTX) |
| 322 | LTX frame rate cond | `LTXVConditioning` | 5. Beat 3 (3 × 5.00s LTX) |
| 323 | Concat AV latents | `LTXVConcatAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 324 | KSampler | `KSampler` | 5. Beat 3 (3 × 5.00s LTX) |
| 325 | Separate AV latents | `LTXVSeparateAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 326 | VAE Decode | `VAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 327 | Audio VAE Decode | `LTXVAudioVAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 328 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 5. Beat 3 (3 × 5.00s LTX) |
| 329 | Last frame | `ImageFromBatch` | 5. Beat 3 (3 × 5.00s LTX) |
| 330 | Save last frame | `SaveImage` | 5. Beat 3 (3 × 5.00s LTX) |
| 351 | b3 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 5. Beat 3 (3 × 5.00s LTX) |
| 340 | b3 s2 LTX I2V | `CLIPTextEncode` | 5. Beat 3 (3 × 5.00s LTX) |
| 341 | LTX Img→Video condition | `LTXVImgToVideo` | 5. Beat 3 (3 × 5.00s LTX) |
| 342 | LTX frame rate cond | `LTXVConditioning` | 5. Beat 3 (3 × 5.00s LTX) |
| 343 | Concat AV latents | `LTXVConcatAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 344 | KSampler | `KSampler` | 5. Beat 3 (3 × 5.00s LTX) |
| 345 | Separate AV latents | `LTXVSeparateAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 346 | VAE Decode | `VAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 347 | Audio VAE Decode | `LTXVAudioVAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 348 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 5. Beat 3 (3 × 5.00s LTX) |
| 349 | Last frame | `ImageFromBatch` | 5. Beat 3 (3 × 5.00s LTX) |
| 350 | Save last frame | `SaveImage` | 5. Beat 3 (3 × 5.00s LTX) |
| 371 | b3 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 5. Beat 3 (3 × 5.00s LTX) |
| 360 | b3 s3 LTX I2V | `CLIPTextEncode` | 5. Beat 3 (3 × 5.00s LTX) |
| 361 | LTX Img→Video condition | `LTXVImgToVideo` | 5. Beat 3 (3 × 5.00s LTX) |
| 362 | LTX frame rate cond | `LTXVConditioning` | 5. Beat 3 (3 × 5.00s LTX) |
| 363 | Concat AV latents | `LTXVConcatAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 364 | KSampler | `KSampler` | 5. Beat 3 (3 × 5.00s LTX) |
| 365 | Separate AV latents | `LTXVSeparateAVLatent` | 5. Beat 3 (3 × 5.00s LTX) |
| 366 | VAE Decode | `VAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 367 | Audio VAE Decode | `LTXVAudioVAEDecode` | 5. Beat 3 (3 × 5.00s LTX) |
| 368 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 5. Beat 3 (3 × 5.00s LTX) |
| 369 | Last frame | `ImageFromBatch` | 5. Beat 3 (3 × 5.00s LTX) |
| 370 | Save last frame | `SaveImage` | 5. Beat 3 (3 × 5.00s LTX) |
| 391 | b4 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 6. Beat 4 (3 × 5.00s LTX) |
| 380 | b4 s1 LTX I2V | `CLIPTextEncode` | 6. Beat 4 (3 × 5.00s LTX) |
| 381 | LTX Img→Video condition | `LTXVImgToVideo` | 6. Beat 4 (3 × 5.00s LTX) |
| 382 | LTX frame rate cond | `LTXVConditioning` | 6. Beat 4 (3 × 5.00s LTX) |
| 383 | Concat AV latents | `LTXVConcatAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 384 | KSampler | `KSampler` | 6. Beat 4 (3 × 5.00s LTX) |
| 385 | Separate AV latents | `LTXVSeparateAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 386 | VAE Decode | `VAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 387 | Audio VAE Decode | `LTXVAudioVAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 388 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 6. Beat 4 (3 × 5.00s LTX) |
| 389 | Last frame | `ImageFromBatch` | 6. Beat 4 (3 × 5.00s LTX) |
| 390 | Save last frame | `SaveImage` | 6. Beat 4 (3 × 5.00s LTX) |
| 411 | b4 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 6. Beat 4 (3 × 5.00s LTX) |
| 400 | b4 s2 LTX I2V | `CLIPTextEncode` | 6. Beat 4 (3 × 5.00s LTX) |
| 401 | LTX Img→Video condition | `LTXVImgToVideo` | 6. Beat 4 (3 × 5.00s LTX) |
| 402 | LTX frame rate cond | `LTXVConditioning` | 6. Beat 4 (3 × 5.00s LTX) |
| 403 | Concat AV latents | `LTXVConcatAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 404 | KSampler | `KSampler` | 6. Beat 4 (3 × 5.00s LTX) |
| 405 | Separate AV latents | `LTXVSeparateAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 406 | VAE Decode | `VAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 407 | Audio VAE Decode | `LTXVAudioVAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 408 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 6. Beat 4 (3 × 5.00s LTX) |
| 409 | Last frame | `ImageFromBatch` | 6. Beat 4 (3 × 5.00s LTX) |
| 410 | Save last frame | `SaveImage` | 6. Beat 4 (3 × 5.00s LTX) |
| 431 | b4 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 6. Beat 4 (3 × 5.00s LTX) |
| 420 | b4 s3 LTX I2V | `CLIPTextEncode` | 6. Beat 4 (3 × 5.00s LTX) |
| 421 | LTX Img→Video condition | `LTXVImgToVideo` | 6. Beat 4 (3 × 5.00s LTX) |
| 422 | LTX frame rate cond | `LTXVConditioning` | 6. Beat 4 (3 × 5.00s LTX) |
| 423 | Concat AV latents | `LTXVConcatAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 424 | KSampler | `KSampler` | 6. Beat 4 (3 × 5.00s LTX) |
| 425 | Separate AV latents | `LTXVSeparateAVLatent` | 6. Beat 4 (3 × 5.00s LTX) |
| 426 | VAE Decode | `VAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 427 | Audio VAE Decode | `LTXVAudioVAEDecode` | 6. Beat 4 (3 × 5.00s LTX) |
| 428 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 6. Beat 4 (3 × 5.00s LTX) |
| 429 | Last frame | `ImageFromBatch` | 6. Beat 4 (3 × 5.00s LTX) |
| 430 | Save last frame | `SaveImage` | 6. Beat 4 (3 × 5.00s LTX) |
| 451 | b5 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 7. Beat 5 (3 × 5.00s LTX) |
| 440 | b5 s1 LTX I2V | `CLIPTextEncode` | 7. Beat 5 (3 × 5.00s LTX) |
| 441 | LTX Img→Video condition | `LTXVImgToVideo` | 7. Beat 5 (3 × 5.00s LTX) |
| 442 | LTX frame rate cond | `LTXVConditioning` | 7. Beat 5 (3 × 5.00s LTX) |
| 443 | Concat AV latents | `LTXVConcatAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 444 | KSampler | `KSampler` | 7. Beat 5 (3 × 5.00s LTX) |
| 445 | Separate AV latents | `LTXVSeparateAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 446 | VAE Decode | `VAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 447 | Audio VAE Decode | `LTXVAudioVAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 448 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 7. Beat 5 (3 × 5.00s LTX) |
| 449 | Last frame | `ImageFromBatch` | 7. Beat 5 (3 × 5.00s LTX) |
| 450 | Save last frame | `SaveImage` | 7. Beat 5 (3 × 5.00s LTX) |
| 471 | b5 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 7. Beat 5 (3 × 5.00s LTX) |
| 460 | b5 s2 LTX I2V | `CLIPTextEncode` | 7. Beat 5 (3 × 5.00s LTX) |
| 461 | LTX Img→Video condition | `LTXVImgToVideo` | 7. Beat 5 (3 × 5.00s LTX) |
| 462 | LTX frame rate cond | `LTXVConditioning` | 7. Beat 5 (3 × 5.00s LTX) |
| 463 | Concat AV latents | `LTXVConcatAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 464 | KSampler | `KSampler` | 7. Beat 5 (3 × 5.00s LTX) |
| 465 | Separate AV latents | `LTXVSeparateAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 466 | VAE Decode | `VAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 467 | Audio VAE Decode | `LTXVAudioVAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 468 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 7. Beat 5 (3 × 5.00s LTX) |
| 469 | Last frame | `ImageFromBatch` | 7. Beat 5 (3 × 5.00s LTX) |
| 470 | Save last frame | `SaveImage` | 7. Beat 5 (3 × 5.00s LTX) |
| 491 | b5 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 7. Beat 5 (3 × 5.00s LTX) |
| 480 | b5 s3 LTX I2V | `CLIPTextEncode` | 7. Beat 5 (3 × 5.00s LTX) |
| 481 | LTX Img→Video condition | `LTXVImgToVideo` | 7. Beat 5 (3 × 5.00s LTX) |
| 482 | LTX frame rate cond | `LTXVConditioning` | 7. Beat 5 (3 × 5.00s LTX) |
| 483 | Concat AV latents | `LTXVConcatAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 484 | KSampler | `KSampler` | 7. Beat 5 (3 × 5.00s LTX) |
| 485 | Separate AV latents | `LTXVSeparateAVLatent` | 7. Beat 5 (3 × 5.00s LTX) |
| 486 | VAE Decode | `VAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 487 | Audio VAE Decode | `LTXVAudioVAEDecode` | 7. Beat 5 (3 × 5.00s LTX) |
| 488 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 7. Beat 5 (3 × 5.00s LTX) |
| 489 | Last frame | `ImageFromBatch` | 7. Beat 5 (3 × 5.00s LTX) |
| 490 | Save last frame | `SaveImage` | 7. Beat 5 (3 × 5.00s LTX) |
| 511 | b6 s1 LTX I2V enhance | `EZLTXPromptEnhance` | 8. Beat 6 (3 × 5.00s LTX) |
| 500 | b6 s1 LTX I2V | `CLIPTextEncode` | 8. Beat 6 (3 × 5.00s LTX) |
| 501 | LTX Img→Video condition | `LTXVImgToVideo` | 8. Beat 6 (3 × 5.00s LTX) |
| 502 | LTX frame rate cond | `LTXVConditioning` | 8. Beat 6 (3 × 5.00s LTX) |
| 503 | Concat AV latents | `LTXVConcatAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 504 | KSampler | `KSampler` | 8. Beat 6 (3 × 5.00s LTX) |
| 505 | Separate AV latents | `LTXVSeparateAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 506 | VAE Decode | `VAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 507 | Audio VAE Decode | `LTXVAudioVAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 508 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 8. Beat 6 (3 × 5.00s LTX) |
| 509 | Last frame | `ImageFromBatch` | 8. Beat 6 (3 × 5.00s LTX) |
| 510 | Save last frame | `SaveImage` | 8. Beat 6 (3 × 5.00s LTX) |
| 531 | b6 s2 LTX I2V enhance | `EZLTXPromptEnhance` | 8. Beat 6 (3 × 5.00s LTX) |
| 520 | b6 s2 LTX I2V | `CLIPTextEncode` | 8. Beat 6 (3 × 5.00s LTX) |
| 521 | LTX Img→Video condition | `LTXVImgToVideo` | 8. Beat 6 (3 × 5.00s LTX) |
| 522 | LTX frame rate cond | `LTXVConditioning` | 8. Beat 6 (3 × 5.00s LTX) |
| 523 | Concat AV latents | `LTXVConcatAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 524 | KSampler | `KSampler` | 8. Beat 6 (3 × 5.00s LTX) |
| 525 | Separate AV latents | `LTXVSeparateAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 526 | VAE Decode | `VAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 527 | Audio VAE Decode | `LTXVAudioVAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 528 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 8. Beat 6 (3 × 5.00s LTX) |
| 529 | Last frame | `ImageFromBatch` | 8. Beat 6 (3 × 5.00s LTX) |
| 530 | Save last frame | `SaveImage` | 8. Beat 6 (3 × 5.00s LTX) |
| 551 | b6 s3 LTX I2V enhance | `EZLTXPromptEnhance` | 8. Beat 6 (3 × 5.00s LTX) |
| 540 | b6 s3 LTX I2V | `CLIPTextEncode` | 8. Beat 6 (3 × 5.00s LTX) |
| 541 | LTX Img→Video condition | `LTXVImgToVideo` | 8. Beat 6 (3 × 5.00s LTX) |
| 542 | LTX frame rate cond | `LTXVConditioning` | 8. Beat 6 (3 × 5.00s LTX) |
| 543 | Concat AV latents | `LTXVConcatAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 544 | KSampler | `KSampler` | 8. Beat 6 (3 × 5.00s LTX) |
| 545 | Separate AV latents | `LTXVSeparateAVLatent` | 8. Beat 6 (3 × 5.00s LTX) |
| 546 | VAE Decode | `VAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 547 | Audio VAE Decode | `LTXVAudioVAEDecode` | 8. Beat 6 (3 × 5.00s LTX) |
| 548 | Save video (MP4) — open node for preview | `VHS_VideoCombine` | 8. Beat 6 (3 × 5.00s LTX) |
| 549 | Last frame | `ImageFromBatch` | 8. Beat 6 (3 × 5.00s LTX) |
| 550 | Save last frame | `SaveImage` | 8. Beat 6 (3 × 5.00s LTX) |
| 901 | LTX AI-media disclosure (end-card) | `EZFilmDisclosure` | 9. Publish 90s MP4 |
| 51 | Load previous act last frame | `LoadImage` | 1. Identity (Klein) |
| 902 | Negative Prompt Enhance | `EZNegativePromptEnhance` | Ungrouped |

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

| Instance | Value |
| --- | --- |
| Klein 4B distilled FP8 | `flux-2-klein-4b-fp8.safetensors` |
| LTX-2.5 distilled INT8-convrot | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` |

#### `weight_dtype`

Type `COMBO`. Range / default: default.

Cast at load.

**How it affects generation:** default keeps the file's dtype (Klein FP8, LTX INT8-convrot, Wan FP16).

**This graph (all 2 instances):** `default`

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

| Instance | Value |
| --- | --- |
| Qwen3-4B TE | `qwen_3_4b.safetensors` |
| Gemma4-with-proj (ltxv) | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` |

#### `type`

Type `COMBO`.

CLIPType enum. Picks tokenizer + template.

**How it affects generation:** flux2 wraps Klein strings in a Qwen chat template — do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.

| Instance | Value |
| --- | --- |
| Qwen3-4B TE | `flux2` |
| Gemma4-with-proj (ltxv) | `ltxv` |

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

**This graph (all 2 instances):** `default`

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

| Instance | Value |
| --- | --- |
| Flux2 VAE | `flux2-vae.safetensors` |
| LTX-2.5 video VAE | `ltx-2.5-video-vae-bf16.safetensors` |
| LTX-2.5 audio VAE | `ltx-2.5-audio-vae-bf16.safetensors` |

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
| Positive | `A photoreal third-person dawn still. A weathered unmarked wooden skiff bow fill…` |
| Negative | `plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, …` |
| Negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |
| b1 s1 LTX I2V | `The start image holds as the first frame. Piles return as pale marks wind, wate…` |
| b1 s2 LTX I2V | `The start image holds as the first frame. The pile slides past hull scrape, spl…` |
| b1 s3 LTX I2V | `The start image holds as the first frame. The cut narrows creak, grit The camer…` |
| b2 s1 LTX I2V | `The start image holds as the first frame. The hard is a grey bar ahead wind, sp…` |
| b2 s2 LTX I2V | `The start image holds as the first frame. The bow aims at the ring hull tick, c…` |
| b2 s3 LTX I2V | `The start image holds as the first frame. The hull kisses stone gravel scrape, …` |
| b3 s1 LTX I2V | `The start image holds as the first frame. Hands take the painter rope ticks, cl…` |
| b3 s2 LTX I2V | `The start image holds as the first frame. The hitch is made metal click, wood c…` |
| b3 s3 LTX I2V | `The start image holds as the first frame. The thwart holds still water tick, wi…` |
| b4 s1 LTX I2V | `The start image holds as the first frame. The skiff rests against stone hull kn…` |
| b4 s2 LTX I2V | `The start image holds as the first frame. A last look down the cut wind, splash…` |
| b4 s3 LTX I2V | `The start image holds as the first frame. Hands leave the thwart cloth, creak T…` |
| b5 s1 LTX I2V | `The start image holds as the first frame. The unmarked bow sits in first real s…` |
| b5 s2 LTX I2V | `The start image holds as the first frame. Steam lifts off wet wood steam, cloth…` |
| b5 s3 LTX I2V | `The start image holds as the first frame. The camera holds the bow hull tick, g…` |
| b6 s1 LTX I2V | `The start image holds as the first frame. Ripples die against stone splash, win…` |
| b6 s2 LTX I2V | `The start image holds as the first frame. A gull-less empty sky wind, cloth The…` |
| b6 s3 LTX I2V | `The start image holds as the first frame. The bow and the hard together wood cr…` |

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

**This graph:** `1280`

#### `height`

Type `INT`.

Latent pixel height.

**How it affects generation:** 1280×704 is the LTX VAE grid (÷32). 1280×720 is not.

**This graph:** `704`

#### `batch_size`

Type `INT`. Range / default: draft 2; others 1.

How many stills in one Queue.

**How it affects generation:** Draft uses 2 for a cheap fork. Heroes stay 1.

**This graph:** `1`

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

| Instance | Value |
| --- | --- |
| KSampler | `42` |
| KSampler | `78` |
| KSampler | `79` |
| KSampler | `80` |
| KSampler | `81` |
| KSampler | `82` |
| KSampler | `83` |
| KSampler | `84` |
| KSampler | `85` |
| KSampler | `86` |
| KSampler | `87` |
| KSampler | `88` |
| KSampler | `89` |
| KSampler | `90` |
| KSampler | `91` |
| KSampler | `92` |
| KSampler | `93` |
| KSampler | `94` |
| KSampler | `95` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed (lab).

What happens to seed after Queue.

**How it affects generation:** fixed keeps iteration honest while you change the prompt.

**This graph (all 19 instances):** `fixed`

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

| Instance | Value |
| --- | --- |
| KSampler | `4` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |
| KSampler | `20` |

#### `cfg`

Type `FLOAT`. Range / default: 0–100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5.

Classifier-free guidance scale.

**How it affects generation:** Distilled Klein is CFG 1.0 — raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.

**This graph (all 19 instances):** `1.0`

#### `sampler_name`

Type `COMBO`. Range / default: euler (most lab); uni_pc (Wan).

ODE / SDE algorithm that removes noise.

**How it affects generation:** euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.

**This graph (all 19 instances):** `euler`

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

**This graph (all 19 instances):** `simple`

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

**This graph (all 19 instances):** `1.0`

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
| Save identity PNG | `ez_tidetable_identity` |
| Save last frame | `ez_tidetable_b13_s1_last` |
| Save last frame | `ez_tidetable_b13_s2_last` |
| Save last frame | `ez_tidetable_b13_s3_last` |
| Save last frame | `ez_tidetable_b14_s1_last` |
| Save last frame | `ez_tidetable_b14_s2_last` |
| Save last frame | `ez_tidetable_b14_s3_last` |
| Save last frame | `ez_tidetable_b15_s1_last` |
| Save last frame | `ez_tidetable_b15_s2_last` |
| Save last frame | `ez_tidetable_b15_s3_last` |
| Save last frame | `ez_tidetable_b16_s1_last` |
| Save last frame | `ez_tidetable_b16_s2_last` |
| Save last frame | `ez_tidetable_b16_s3_last` |
| Save last frame | `ez_tidetable_b17_s1_last` |
| Save last frame | `ez_tidetable_b17_s2_last` |
| Save last frame | `ez_tidetable_b17_s3_last` |
| Save last frame | `ez_tidetable_b18_s1_last` |
| Save last frame | `ez_tidetable_b18_s2_last` |
| Save last frame | `ez_tidetable_b18_s3_last` |

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## shorts/tide-table/act-03 LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid). The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/outpu…`

```text
## shorts/tide-table/act-03

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/outputs`) as a faststart H.264 master, plus an HTML sidecar. After Queue, a **Film ready** overlay offers play and download. Per-shot VHS nodes remain for inspection. Optional board: studio-ui `/watch/<slug>`.

One-click 90s unit (dawn skiff · Fog and spit): Klein identity still + 18 sequential LTX 5.00s AV prints + in-graph stitch.
Models: Klein 4B distilled FP8 (identity still, 4-step, Enhance **off**, t2i mode) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

1. Queue **once**. Klein runs first; models unload; then 18 × 5.00s LTX prints chain last-frame → next start.
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) — expected, not a hang.
3. The MP4 is already on disk at `${COMFY_OUTPUT_DIR}/ez_tidetable_90s.mp4` (act graphs write `ez_tidetable_actN_90s.mp4`). A **Film ready** overlay plays it. Copy off the Spark with scp.
4. Optional single-shot iterate: **ltx/i2v-shot**. Optional silent rehearsal: **wan/i2v-shot**.
5. Spark-farm / host stitch fallback: `./scripts/utilities/concat-shots.sh --film tide-table --yes`

Do not Queue a 90s denoise (keep 121-frame / 1+8n widgets). US-safe local pack only. No score.
Prompt enhance is **off** so the pinned identity and each baked LTX I2V paragraph are encoded as written. The identity STRING is wired into each shot enhance as context (used only if you turn Enhance on).

This graph is **act 3/5** of a 7.5 min film (90 × 5.00s). Act 3 LoadImage should be the previous act last frame (ez_tidetable_b12_s3_last_*.png). In-graph stitch writes `ez_tidetable_act3_90s.mp4`. After all five acts: `concat-shots.sh --film tide-table --yes` → `ez_tidetable_450s.mp4`.

Occupancy: film — stop everything else on that Spark. One GB10 job.
```

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

**This graph:** `A photoreal third-person dawn still. A weathered unmarked wooden skiff bow fills the lower third, wet grain and a blank painter coil on the thwart, looking out from a stone hard toward a cut of unmar…`

```text
A photoreal third-person dawn still. A weathered unmarked wooden skiff bow fills the lower third, wet grain and a blank painter coil on the thwart, looking out from a stone hard toward a cut of unmarked piles and grey-pink water. Eye-level 35mm lens, framed for YouTube 16:9, empty of lettering, mild film grain, clean unmarked lens.
```

#### `enhance`

Type `BOOLEAN`. Range / default: on for lazy printers.

Run the rewriter.

**How it affects generation:** Off = encode the widget as-is (plus style suffix if set).

**This graph:** `false`

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

**This graph:** `YouTube 16:9 still`

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

**This graph:** `shorts/tide-table/act-03`

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

| Instance | Value |
| --- | --- |
| Negative Prompt Enhance | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt…` |
| Negative Prompt Enhance | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |

#### `enhance`

Type `BOOLEAN`.

Rewrite using the positive as context.

**How it affects generation:** Stops canned 'illustration / Pixar' terms from fighting a cartoon-positive.

**This graph (all 2 instances):** `false`

#### `family`

Type `COMBO`.

Which negative family.

**How it affects generation:** Must match the UNET on the canvas.

| Instance | Value |
| --- | --- |
| Negative Prompt Enhance | `klein` |
| Negative Prompt Enhance | `ltx` |

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

### `MarkdownNote` — Markdown Note

Rendered markdown note (90s shot maps).

#### `text`

Type `STRING`.

Markdown body.

**How it affects generation:** Does not affect pixels. 90s films put the beat table here.

**This graph:** `## tide-table (dawn skiff · Fog and spit) Queue **once**. Klein identity still → 18 × 5.00s LTX AV prints (last-frame continuity) → **Save 90s film (MP4)**. Do not Queue a 90s denoise (121 frames = 1…`

```text
## tide-table (dawn skiff · Fog and spit)

Queue **once**. Klein identity still → 18 × 5.00s LTX AV prints (last-frame continuity) → **Save 90s film (MP4)**. Do not Queue a 90s denoise (121 frames = 1+8n per shot). Optional silent rehearsal: **wan/i2v-shot**. Optional host stitch: `./scripts/utilities/concat-shots.sh --film tide-table --yes`.

18 × 121 frames @ 24 fps (LTX 1+8n) stitch under a 90.00s cap. US-safe local pack only. No score. Play/download: overlay, `ez_*_90s.html`, or studio-ui `/watch/<slug>`.

**Identity look:** A photoreal third-person dawn still. A weathered unmarked wooden skiff bow fills the lower third, wet grain and a blank painter coil on the thwart, looking out from a stone hard toward a cut of unmarked piles and grey-pink water. Eye-level 35mm lens, framed for YouTube 16:9, empty of lettering, mild film grain, clean unmarked lens.

| Beat | Place | s1 | s2 | s3 |
| --- | --- | --- | --- | --- |
| 1 | Lane | Piles return as pale marks | The pile slides past | The cut narrows |
| 2 | Piles | The hard is a grey bar ahead | The bow aims at the ring | The hull kisses stone |
| 3 | Tie | Hands take the painter | The hitch is made | The thwart holds still |
| 4 | Quiet | The skiff rests against stone | A last look down the cut | Hands leave the thwart |
| 5 | Hold | The unmarked bow sits in first real sun | Steam lifts off wet wood | The camera holds the bow |
| 6 | Still water | Ripples die against stone | A gull-less empty sky | The bow and the hard together |
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.
```

### `EZUnloadModels` — Unload models

Pass-through IMAGE that unloads diffusion models first.

!!! warning "Lab notes"

    Keeps Klein 4B and LTX-2.5 from sitting in memory together on 90s one-click films.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Identity still. |
| `image` | out | `IMAGE` | Same still after unload. |

No widgets. Sockets only.

### `LTXVEmptyLatentAudio` — Empty LTX Audio Latent

Allocate a silent/world-audio latent matching video length.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio_vae` | in | `VAE` | Audio VAE (sets latent channels). |
| `Latent` | out | `LATENT` | Empty audio latent. |

#### `frames`

Type `INT`. Range / default: 121.

Must match video length.

**How it affects generation:** Mismatch with LTXVImgToVideo length breaks concat.

**This graph:** `121`

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

### `EZFilmConcat` — Save 90s film (MP4)

Concat 18 LTX 5.00 s MP4s, cap 90 s, H.264 CRF 18 + AAC + loudnorm + faststart.

!!! warning "Lab notes"

    Queue once. xfade_cs is audio-only acrossfade; 0 is a hard cut. go-see ships xfade_cs 8. act=0 is a 90s film master; act=1–5 writes ez_<slug>_actN_90s.mp4.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `shot_01` | in | `VHS_FILENAMES` | Shot 01 MP4. |
| `shot_02` | in | `VHS_FILENAMES` | Shot 02 MP4. |
| `shot_03` | in | `VHS_FILENAMES` | Shot 03 MP4. |
| `shot_04` | in | `VHS_FILENAMES` | Shot 04 MP4. |
| `shot_05` | in | `VHS_FILENAMES` | Shot 05 MP4. |
| `shot_06` | in | `VHS_FILENAMES` | Shot 06 MP4. |
| `shot_07` | in | `VHS_FILENAMES` | Shot 07 MP4. |
| `shot_08` | in | `VHS_FILENAMES` | Shot 08 MP4. |
| `shot_09` | in | `VHS_FILENAMES` | Shot 09 MP4. |
| `shot_10` | in | `VHS_FILENAMES` | Shot 10 MP4. |
| `shot_11` | in | `VHS_FILENAMES` | Shot 11 MP4. |
| `shot_12` | in | `VHS_FILENAMES` | Shot 12 MP4. |
| `shot_13` | in | `VHS_FILENAMES` | Shot 13 MP4. |
| `shot_14` | in | `VHS_FILENAMES` | Shot 14 MP4. |
| `shot_15` | in | `VHS_FILENAMES` | Shot 15 MP4. |
| `shot_16` | in | `VHS_FILENAMES` | Shot 16 MP4. |
| `shot_17` | in | `VHS_FILENAMES` | Shot 17 MP4. |
| `shot_18` | in | `VHS_FILENAMES` | Shot 18 MP4. |
| `disclosure` | in | `STRING` | EZFilmDisclosure text. |
| `path` | out | `STRING` | Published MP4 path. |

#### `film`

Type `COMBO`.

Film id.

**How it affects generation:** Picks output name and shot-map. Must match the graph.

**This graph:** `tide-table`

**Other choices**

| Choice | What it does |
| --- | --- |
| `go-see` | Parkour 90s. |
| `still-here` | Household morning 90s. |
| `switchyard` | Night freight-yard 90s. |
| `tide-table` | Dawn skiff 7.5 min. |
| `night-oven` | Bakery 7.5 min. |
| `glasshouse` | Storm glasshouse 7.5 min. |
| `last-lane` | Night two-lane 7.5 min. |
| `breakwater` | Storm-wall walk 7.5 min. |

#### `cap_seconds`

Type `FLOAT`. Range / default: 90.0 max.

Hard duration cap for this 18-shot stitch.

**How it affects generation:** Stay 90. This is a stitch cap, not a denoise length. 7.5 min masters are host concat of 90 stems.

**This graph:** `90.0`

#### `xfade_cs`

Type `INT`. Range / default: 0–50; 10 = 0.10 s.

Audio-only acrossfade in centiseconds.

**How it affects generation:** 0 = hard cut (still-here, switchyard). 8 = 0.08 s audio cross on go-see / last-lane / breakwater. Picture stays cut-only so duration stays on picture.

**This graph:** `0`

#### `act`

Type `INT`. Range / default: 0–5.

0 = 90s film master; 1–5 = act master for a 7.5 min film.

**How it affects generation:** Festival shorts Queue five act graphs, then concat-shots.sh writes ez_<slug>_450s.mp4.

**This graph:** `3`

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
| b1 s1 LTX I2V enhance | `The start image holds as the first frame. Piles return as pale marks wind, wate…` |
| b1 s2 LTX I2V enhance | `The start image holds as the first frame. The pile slides past hull scrape, spl…` |
| b1 s3 LTX I2V enhance | `The start image holds as the first frame. The cut narrows creak, grit The camer…` |
| b2 s1 LTX I2V enhance | `The start image holds as the first frame. The hard is a grey bar ahead wind, sp…` |
| b2 s2 LTX I2V enhance | `The start image holds as the first frame. The bow aims at the ring hull tick, c…` |
| b2 s3 LTX I2V enhance | `The start image holds as the first frame. The hull kisses stone gravel scrape, …` |
| b3 s1 LTX I2V enhance | `The start image holds as the first frame. Hands take the painter rope ticks, cl…` |
| b3 s2 LTX I2V enhance | `The start image holds as the first frame. The hitch is made metal click, wood c…` |
| b3 s3 LTX I2V enhance | `The start image holds as the first frame. The thwart holds still water tick, wi…` |
| b4 s1 LTX I2V enhance | `The start image holds as the first frame. The skiff rests against stone hull kn…` |
| b4 s2 LTX I2V enhance | `The start image holds as the first frame. A last look down the cut wind, splash…` |
| b4 s3 LTX I2V enhance | `The start image holds as the first frame. Hands leave the thwart cloth, creak T…` |
| b5 s1 LTX I2V enhance | `The start image holds as the first frame. The unmarked bow sits in first real s…` |
| b5 s2 LTX I2V enhance | `The start image holds as the first frame. Steam lifts off wet wood steam, cloth…` |
| b5 s3 LTX I2V enhance | `The start image holds as the first frame. The camera holds the bow hull tick, g…` |
| b6 s1 LTX I2V enhance | `The start image holds as the first frame. Ripples die against stone splash, win…` |
| b6 s2 LTX I2V enhance | `The start image holds as the first frame. A gull-less empty sky wind, cloth The…` |
| b6 s3 LTX I2V enhance | `The start image holds as the first frame. The bow and the hard together wood cr…` |

#### `enhance`

Type `BOOLEAN`.

Run the rewriter.

**How it affects generation:** Off keeps authored film/shot text pinned.

**This graph (all 18 instances):** `false`

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

#### `catalog`

Type `STRING`.

Sample-catalog id.

**How it affects generation:** Leave as stamped.

**This graph (all 18 instances):** `shorts/tide-table/act-03`

### `LTXVImgToVideo` — LTX Image to Video

Condition LTX on a start image and allocate the video latent.

!!! warning "Lab notes"

    ÷32 spatial, length 1+8n. 1280×704×121 is the lab printer. Shorts 768×1280. Some shot graphs still store 120 and rely on ez_ltx_spatial to snap.

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

**This graph (all 18 instances):** `1280`

#### `height`

Type `INT`. Range / default: 704 / 1280.

Frame height.

**How it affects generation:** 704 not 720. Shorts 1280.

**This graph (all 18 instances):** `704`

#### `length`

Type `INT`. Range / default: 121.

Frame count.

**How it affects generation:** 1+8n. 121 @ 24 fps ≈ 5.04 s. Do not type a 90 s length.

**This graph (all 18 instances):** `121`

#### `batch_size`

Type `INT`. Range / default: 1.

Clips per Queue.

**How it affects generation:** Stay 1.

**This graph (all 18 instances):** `1`

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

**This graph (all 18 instances):** `24.0`

### `LTXVConcatAVLatent` — LTX Concat AV Latent

Join video + audio latents into one joint AV latent for the sampler.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `video_latent` | in | `LATENT` | Video latent. |
| `audio_latent` | in | `LATENT` | Empty or encoded audio latent. |
| `latent` | out | `LATENT` | Joint AV latent. |

No widgets. Sockets only.

### `LTXVSeparateAVLatent` — LTX Separate AV Latent

Split a joint AV latent after sampling.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `av_latent` | in | `LATENT` | KSampler output. |
| `video_latent` | out | `LATENT` | Picture latent → VAEDecode. |
| `audio_latent` | out | `LATENT` | Audio latent → LTXVAudioVAEDecode (not on a2v). |

No widgets. Sockets only.

### `LTXVAudioVAEDecode` — LTX Audio VAE Decode

Decode LTX audio latent to AUDIO for the MP4 mux.

!!! warning "Lab notes"

    Skipped on ltx/a2v-5s (original wav is muxed).

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

**This graph (all 18 instances):** `24`

#### `loop_count`

Type `INT`. Range / default: 0 = infinite in players that honor it.

How many times the file loops.

**How it affects generation:** 0 is the lab default (play once / player default).

**This graph (all 18 instances):** `0`

#### `filename_prefix`

Type `STRING`.

Save prefix under the output folder.

**How it affects generation:** Lab prefixes start with ez_. The host file is ${COMFY_OUTPUT_DIR}/<prefix>_*.mp4 (or .gif).

| Instance | Value |
| --- | --- |
| Save video (MP4) — open node for preview | `ez_tidetable_b13_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b13_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b13_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b14_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b14_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b14_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b15_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b15_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b15_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b16_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b16_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b16_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b17_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b17_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b17_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b18_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b18_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_tidetable_b18_s3_ltx_video` |

#### `format`

Type `COMBO`.

Container / codec.

**How it affects generation:** video/h264-mp4 is every lab clip except wan/gif-loop (image/gif).

**This graph (all 18 instances):** `video/h264-mp4`

**Other choices**

| Choice | What it does |
| --- | --- |
| `video/h264-mp4` | H.264 MP4. Lab default; save_output must stay true. |
| `image/gif` | Animated GIF. wan/gif-loop only. |

#### `pix_fmt`

Type `COMBO`. Range / default: yuv420p.

Pixel format for H.264.

**How it affects generation:** yuv420p plays everywhere. Other formats can break QuickTime/YouTube.

**This graph (all 18 instances):** `yuv420p`

#### `crf`

Type `INT`. Range / default: lab 18.

H.264 constant-rate-factor. Lower is bigger/cleaner.

**How it affects generation:** 18 is the lab visually-lossless-ish setting. Raising CRF shrinks files and adds blockiness.

**This graph (all 18 instances):** `18`

#### `save_metadata`

Type `BOOLEAN`.

Embed workflow JSON in the file.

**How it affects generation:** true keeps provenance on the MP4.

**This graph (all 18 instances):** `true`

#### `trim_to_audio`

Type `BOOLEAN`.

Cut picture to audio length.

**How it affects generation:** Lab false except when you mean to lock to a bed. ltx/a2v muxes the original wav instead.

**This graph (all 18 instances):** `false`

#### `pingpong`

Type `BOOLEAN`.

Play frames forward then reverse.

**How it affects generation:** true on wan/gif-loop, bumper-loop, sticker-loop. false on 5 s narrative prints.

**This graph (all 18 instances):** `false`

#### `save_output`

Type `BOOLEAN`.

Write the file to disk.

**How it affects generation:** Lab video graphs require true. After Queue, open the node for the inline preview.

**This graph (all 18 instances):** `true`

### `ImageFromBatch` — Image From Batch

Pick one frame out of a decoded video batch.

!!! warning "Lab notes"

    Last-frame savers: index 120 on 121-frame LTX (0-based last), 119 on 120-frame Wan shots.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Decoded frame batch. |
| `IMAGE` | out | `IMAGE` | Single frame. |

#### `batch_index`

Type `INT`. Range / default: 120 (LTX 121) / 119 (Wan 120).

0-based frame index.

**How it affects generation:** Must be length-1 for the last frame. Off-by-one here breaks shot continuity.

**This graph (all 18 instances):** `120`

#### `length`

Type `INT`. Range / default: 1.

How many frames to take.

**How it affects generation:** Stay 1 (one still).

**This graph (all 18 instances):** `1`

### `EZFilmDisclosure` — LTX AI-media disclosure

Prepend the LTX Community License AI-media disclosure. Idempotent. Not legal advice.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `text` | out | `STRING` | Disclosure (+ optional extra). |

#### `text`

Type `STRING`.

Optional extra line after the stock disclosure.

**How it affects generation:** Empty = stock sentence only. Do not strip provenance.

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

**This graph:** `ez_tidetable_b12_s3_last.png`

#### `upload`

Type `COMBO`. Range / default: image.

Upload widget type.

**How it affects generation:** Leave image. This is the choose-file control, not a generation knob.

**This graph:** `image`
