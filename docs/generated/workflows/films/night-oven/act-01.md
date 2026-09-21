---
title: "films/night-oven/act-01"
description: "One-click overnight bakery · Tie the apron: 18 LTX 5.00s AV shots + stitch Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or fil"
tags: [workflows, generated, comfyui, films]
---

# films/night-oven/act-01

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `films/night-oven/act-01` from Apps or Workflows.

> Generated from `workflows/_lab/films/night-oven/act-01.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **film**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## films/night-oven/act-01

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/outputs`) as a faststart H.264 master, plus an HTML sidecar. After Queue, a **Film ready** overlay offers play and download. Per-shot VHS nodes remain for inspection. Optional board: studio-ui `/watch/<slug>`.

One-click 90s unit (overnight bakery · Tie the apron): Klein identity still + 18 sequential LTX 5.00s AV prints + in-graph stitch.
Models: Klein 4B distilled FP8 (identity still, 4-step, Enhance **off**, t2i mode) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

1. Queue **once**. Klein runs first; models unload; then 18 × 5.00s LTX prints chain last-frame → next start.
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) — expected, not a hang.
3. The MP4 is already on disk at `${COMFY_OUTPUT_DIR}/ez_nightoven_90s.mp4` (act graphs write `ez_nightoven_actN_90s.mp4`). A **Film ready** overlay plays it. Copy off the Spark with scp.
4. Optional single-shot iterate: **motion/av/still-to-shot**. Optional silent rehearsal: **motion/silent/still-to-shot**.
5. Spark-farm / host stitch fallback: `./scripts/utilities/concat-shots.sh --film night-oven --yes`

Do not Queue a 90s denoise (keep 121-frame / 1+8n widgets). US-safe local pack only. No score.
Prompt enhance is **off** so the pinned identity and each baked LTX I2V paragraph are encoded as written. The identity STRING is wired into each shot enhance as context (used only if you turn Enhance on).

This graph is **act 1/5** of a 7.5 min film (90 × 5.00s). Act 1 starts from Klein identity. In-graph stitch writes `ez_nightoven_act1_90s.mp4`. After all five acts: `concat-shots.sh --film night-oven --yes` → `ez_nightoven_450s.mp4`.

Occupancy: film — stop everything else on that Spark. One GB10 job.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **films/night-oven/act-01** from **Apps** or **Workflows**
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
| 52 | night-oven 90s shot map | `MarkdownNote` | Ungrouped |
| 50 | Unload models (pass IMAGE) | `EZUnloadModels` | 1. Identity (Klein) |
| 100 | LTX-2.5 distilled INT8-convrot | `UNETLoader` | 2. LTX models |
| 101 | LTX-2.5 video VAE | `VAELoader` | 2. LTX models |
| 102 | Gemma4-with-proj (ltxv) | `CLIPLoader` | 2. LTX models |
| 103 | LTX-2.5 audio VAE | `VAELoader` | 2. LTX models |
| 104 | Negative | `CLIPTextEncode` | 2. LTX models |
| 105 | Empty LTX audio latent | `LTXVEmptyLatentAudio` | 2. LTX models |
| 900 | Save act 1 (90s MP4) — play / download | `EZFilmConcat` | 9. Publish 90s MP4 |
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
| 902 | Negative Prompt Enhance | `EZNegativePromptEnhance` | 9. Publish 90s MP4 |
| 903 | Check models | `EZModelCheck` | Ungrouped |

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
| Positive | `A photoreal third-person bakery still at 2 a.m. A flour-dusted linen apron hang…` |
| Negative | `plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, …` |
| Negative | `morphing, identity drift, warping objects, face melting, flicker, jitter, frame…` |
| b1 s1 LTX I2V | `The start image holds as the first frame. The apron hangs still in tungsten clo…` |
| b1 s2 LTX I2V | `The start image holds as the first frame. A hand lifts the apron cloth, metal t…` |
| b1 s3 LTX I2V | `The start image holds as the first frame. The apron is tied fabric, click The c…` |
| b2 s1 LTX I2V | `The start image holds as the first frame. The knot sits at the waist cloth, hum…` |
| b2 s2 LTX I2V | `The start image holds as the first frame. Flour dust lifts grit, steam The came…` |
| b2 s3 LTX I2V | `The start image holds as the first frame. The bench is empty metal scrape, tick…` |
| b3 s1 LTX I2V | `The start image holds as the first frame. Bowls wait unmarked metal tick, hum T…` |
| b3 s2 LTX I2V | `The start image holds as the first frame. A pour of water pour, splash The came…` |
| b3 s3 LTX I2V | `The start image holds as the first frame. A mixer starts hum, metal The camera …` |
| b4 s1 LTX I2V | `The start image holds as the first frame. The bowl turns slow hum, scrape The c…` |
| b4 s2 LTX I2V | `The start image holds as the first frame. A scrape of the hook metal scrape, ti…` |
| b4 s3 LTX I2V | `The start image holds as the first frame. The mixer stops click, hum The camera…` |
| b5 s1 LTX I2V | `The start image holds as the first frame. Hands fold the dough cloth, scrape Th…` |
| b5 s2 LTX I2V | `The start image holds as the first frame. A dust of flour grit, cloth The camer…` |
| b5 s3 LTX I2V | `The start image holds as the first frame. The dough rests hum, tick The camera …` |
| b6 s1 LTX I2V | `The start image holds as the first frame. The oven mouth is dark hum, metal tic…` |
| b6 s2 LTX I2V | `The start image holds as the first frame. A match of warmth steam, click The ca…` |
| b6 s3 LTX I2V | `The start image holds as the first frame. The door opens metal scrape, steam Th…` |

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
| KSampler | `42` |
| KSampler | `43` |
| KSampler | `44` |
| KSampler | `45` |
| KSampler | `46` |
| KSampler | `47` |
| KSampler | `48` |
| KSampler | `49` |
| KSampler | `50` |
| KSampler | `51` |
| KSampler | `52` |
| KSampler | `53` |
| KSampler | `54` |
| KSampler | `55` |
| KSampler | `56` |
| KSampler | `57` |
| KSampler | `58` |
| KSampler | `59` |

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
| Save identity PNG | `ez_nightoven_identity` |
| Save last frame | `ez_nightoven_b1_s1_last` |
| Save last frame | `ez_nightoven_b1_s2_last` |
| Save last frame | `ez_nightoven_b1_s3_last` |
| Save last frame | `ez_nightoven_b2_s1_last` |
| Save last frame | `ez_nightoven_b2_s2_last` |
| Save last frame | `ez_nightoven_b2_s3_last` |
| Save last frame | `ez_nightoven_b3_s1_last` |
| Save last frame | `ez_nightoven_b3_s2_last` |
| Save last frame | `ez_nightoven_b3_s3_last` |
| Save last frame | `ez_nightoven_b4_s1_last` |
| Save last frame | `ez_nightoven_b4_s2_last` |
| Save last frame | `ez_nightoven_b4_s3_last` |
| Save last frame | `ez_nightoven_b5_s1_last` |
| Save last frame | `ez_nightoven_b5_s2_last` |
| Save last frame | `ez_nightoven_b5_s3_last` |
| Save last frame | `ez_nightoven_b6_s1_last` |
| Save last frame | `ez_nightoven_b6_s2_last` |
| Save last frame | `ez_nightoven_b6_s3_last` |

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## films/night-oven/act-01 LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid). The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/output…`

```text
## films/night-oven/act-01

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` (container `/outputs`) as a faststart H.264 master, plus an HTML sidecar. After Queue, a **Film ready** overlay offers play and download. Per-shot VHS nodes remain for inspection. Optional board: studio-ui `/watch/<slug>`.

One-click 90s unit (overnight bakery · Tie the apron): Klein identity still + 18 sequential LTX 5.00s AV prints + in-graph stitch.
Models: Klein 4B distilled FP8 (identity still, 4-step, Enhance **off**, t2i mode) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

1. Queue **once**. Klein runs first; models unload; then 18 × 5.00s LTX prints chain last-frame → next start.
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) — expected, not a hang.
3. The MP4 is already on disk at `${COMFY_OUTPUT_DIR}/ez_nightoven_90s.mp4` (act graphs write `ez_nightoven_actN_90s.mp4`). A **Film ready** overlay plays it. Copy off the Spark with scp.
4. Optional single-shot iterate: **motion/av/still-to-shot**. Optional silent rehearsal: **motion/silent/still-to-shot**.
5. Spark-farm / host stitch fallback: `./scripts/utilities/concat-shots.sh --film night-oven --yes`

Do not Queue a 90s denoise (keep 121-frame / 1+8n widgets). US-safe local pack only. No score.
Prompt enhance is **off** so the pinned identity and each baked LTX I2V paragraph are encoded as written. The identity STRING is wired into each shot enhance as context (used only if you turn Enhance on).

This graph is **act 1/5** of a 7.5 min film (90 × 5.00s). Act 1 starts from Klein identity. In-graph stitch writes `ez_nightoven_act1_90s.mp4`. After all five acts: `concat-shots.sh --film night-oven --yes` → `ez_nightoven_450s.mp4`.

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
| `image_desc` | in | `STRING` | Optional still caption from EZImageDescribe. |
| `background_cast` | in | `STRING` | Optional compact token from EZBackgroundCast. |
| `prompt` | out | `STRING` | String CLIP actually encodes. |

#### `sample`

Type `COMBO`. Range / default: custom.

Lab sample prompt or Custom.

**How it affects generation:** Custom keeps the textarea. Picking a sample fills and locks the Prompt. The App dropdown lists this graph's 30 recipes plus Custom (place recipes such as Cliff villa on stills/dream-house).

**This graph:** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored still prompt.

**How it affects generation:** When Enhance is on, the GGUF expands this into Klein-native sentences.

**This graph:** `A photoreal third-person bakery still at 2 a.m. A flour-dusted linen apron hangs on a steel bench in the foreground, unmarked mixer bowls and a dark oven mouth behind. Warm tungsten versus a sodium a…`

```text
A photoreal third-person bakery still at 2 a.m. A flour-dusted linen apron hangs on a steel bench in the foreground, unmarked mixer bowls and a dark oven mouth behind. Warm tungsten versus a sodium alley through one high window. Match a standing eyeline. 35mm-equivalent classic, framed for YouTube 16:9, empty of lettering, mild film grain, clean unmarked lens.
```

#### `enhance`

Type `BOOLEAN`. Range / default: on for lazy printers.

Run the rewriter.

**How it affects generation:** Off = encode the widget as-is (plus style suffix if set).

**This graph:** `false`

#### `mode`

Type `COMBO`. Range / default: t2i / edit / identity / text_swap / background_swap / background_edit.

System prompt flavor.

**How it affects generation:** t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet). text_swap = glyph-lock lettering on a source still. background_swap = replace environment including ground. background_edit = restyle the environment in place.

**This graph:** `identity`

**Other choices**

| Choice | What it does |
| --- | --- |
| `t2i` | New still. |
| `edit` | Klein-edit / clay / tweak. |
| `identity` | Camera-free identity bible. |
| `text_swap` | Replace lettering; source still owns look and size. |
| `background_swap` | Replace backdrop, ground, and nearby set dressing. |
| `background_edit` | Restyle or rewrite the environment; keep the subject. |

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

Sample-catalog id (graph stem).

**How it affects generation:** Internal. Leave as stamped so sample dropdowns resolve.

**This graph:** `films/night-oven/act-01`

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

### `MarkdownNote` — Markdown Note

Rendered markdown note (90s shot maps).

#### `text`

Type `STRING`.

Markdown body.

**How it affects generation:** Does not affect pixels. 90s films put the beat table here.

**This graph:** `## night-oven (overnight bakery · Tie the apron) Queue **once**. Klein identity still → 18 × 5.00s LTX AV prints (last-frame continuity) → **Save 90s film (MP4)**. Do not Queue a 90s denoise (121 fra…`

```text
## night-oven (overnight bakery · Tie the apron)

Queue **once**. Klein identity still → 18 × 5.00s LTX AV prints (last-frame continuity) → **Save 90s film (MP4)**. Do not Queue a 90s denoise (121 frames = 1+8n per shot). Optional silent rehearsal: **motion/silent/still-to-shot**. Optional host stitch: `./scripts/utilities/concat-shots.sh --film night-oven --yes`.

18 × 121 frames @ 24 fps (LTX 1+8n) stitch under a 90.00s cap. US-safe local pack only. No score. Play/download: overlay, `ez_*_90s.html`, or studio-ui `/watch/<slug>`.

**Identity look:** A photoreal third-person bakery still at 2 a.m. A flour-dusted linen apron hangs on a steel bench in the foreground, unmarked mixer bowls and a dark oven mouth behind. Warm tungsten versus a sodium alley through one high window. Match a standing eyeline. 35mm-equivalent classic, framed for YouTube 16:9, empty of lettering, mild film grain, clean unmarked lens.

| Beat | Place | s1 | s2 | s3 |
| --- | --- | --- | --- | --- |
| 1 | Bench | The apron hangs still in tungsten | A hand lifts the apron | The apron is tied |
| 2 | Tie | The knot sits at the waist | Flour dust lifts | The bench is empty |
| 3 | Empty steel | Bowls wait unmarked | A pour of water | A mixer starts |
| 4 | Mixer | The bowl turns slow | A scrape of the hook | The mixer stops |
| 5 | Dough | Hands fold the dough | A dust of flour | The dough rests |
| 6 | Rest | The oven mouth is dark | A match of warmth | The door opens |
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

Type `INT`. Range / default: 193 Apps / 121 film.

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

**This graph:** `night-oven`

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

**This graph:** `1`

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

**This graph (all 18 instances):** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored LTX paragraph.

**How it affects generation:** I2V: start image holds look; prompt is motion + world SFX. Dialogue belongs in "quotes" only if you asked for speech.

| Instance | Value |
| --- | --- |
| b1 s1 LTX I2V enhance | `The start image holds as the first frame. The apron hangs still in tungsten clo…` |
| b1 s2 LTX I2V enhance | `The start image holds as the first frame. A hand lifts the apron cloth, metal t…` |
| b1 s3 LTX I2V enhance | `The start image holds as the first frame. The apron is tied fabric, click The c…` |
| b2 s1 LTX I2V enhance | `The start image holds as the first frame. The knot sits at the waist cloth, hum…` |
| b2 s2 LTX I2V enhance | `The start image holds as the first frame. Flour dust lifts grit, steam The came…` |
| b2 s3 LTX I2V enhance | `The start image holds as the first frame. The bench is empty metal scrape, tick…` |
| b3 s1 LTX I2V enhance | `The start image holds as the first frame. Bowls wait unmarked metal tick, hum T…` |
| b3 s2 LTX I2V enhance | `The start image holds as the first frame. A pour of water pour, splash The came…` |
| b3 s3 LTX I2V enhance | `The start image holds as the first frame. A mixer starts hum, metal The camera …` |
| b4 s1 LTX I2V enhance | `The start image holds as the first frame. The bowl turns slow hum, scrape The c…` |
| b4 s2 LTX I2V enhance | `The start image holds as the first frame. A scrape of the hook metal scrape, ti…` |
| b4 s3 LTX I2V enhance | `The start image holds as the first frame. The mixer stops click, hum The camera…` |
| b5 s1 LTX I2V enhance | `The start image holds as the first frame. Hands fold the dough cloth, scrape Th…` |
| b5 s2 LTX I2V enhance | `The start image holds as the first frame. A dust of flour grit, cloth The camer…` |
| b5 s3 LTX I2V enhance | `The start image holds as the first frame. The dough rests hum, tick The camera …` |
| b6 s1 LTX I2V enhance | `The start image holds as the first frame. The oven mouth is dark hum, metal tic…` |
| b6 s2 LTX I2V enhance | `The start image holds as the first frame. A match of warmth steam, click The ca…` |
| b6 s3 LTX I2V enhance | `The start image holds as the first frame. The door opens metal scrape, steam Th…` |

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

Type `STRING`. Range / default: 8 seconds, 24 fps.

Duration hint.

**How it affects generation:** Does not set 193 frames — LTXVImgToVideo does. Film printers stay 5 seconds / 121.

**This graph (all 18 instances):** `5 seconds, 24 fps`

#### `audio_notes`

Type `STRING`.

World SFX / no-score policy.

**How it affects generation:** Lab 8 s Apps ask for world SFX matching the start image, no score.

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

**This graph (all 18 instances):** `films/night-oven/act-01`

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

**This graph (all 18 instances):** `1280`

#### `height`

Type `INT`. Range / default: 704 / 1280.

Frame height.

**How it affects generation:** 704 not 720. Shorts 1280.

**This graph (all 18 instances):** `704`

#### `length`

Type `INT`. Range / default: 193 Apps / 121 film = 1+8n.

Frame count.

**How it affects generation:** Standalone Apps default 193 @ 24 fps ≈ 8.04 s. Film printers stay 121 (~5.04 s). Do not type a 90 s length.

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
| Save video (MP4) — open node for preview | `ez_nightoven_b1_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b1_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b1_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b2_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b2_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b2_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b3_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b3_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b3_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b4_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b4_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b4_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b5_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b5_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b5_s3_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b6_s1_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b6_s2_ltx_video` |
| Save video (MP4) — open node for preview | `ez_nightoven_b6_s3_ltx_video` |

#### `format`

Type `COMBO`.

Container / codec.

**How it affects generation:** video/h264-mp4 is every lab clip except motion/loops/gif-loop (image/gif).

**This graph (all 18 instances):** `video/h264-mp4`

**Other choices**

| Choice | What it does |
| --- | --- |
| `video/h264-mp4` | H.264 MP4. Lab default; save_output must stay true. |
| `image/gif` | Animated GIF. motion/loops/gif-loop only. |

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

**How it affects generation:** true on motion/loops/gif-loop, bumper-loop, sticker-loop. false on 5 s narrative prints.

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

### `EZModelCheck` — Check models

Manual disk check for occupancy + Quality weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph:** `Click Check models. Queue does not run this node.`
