---
title: Model licenses
description: US self-host license policy for Klein 4B, Wan 2.2, and LTX-2.5. Not legal advice.
tags: [license, apache, ltx, wan, klein, youtube, us]
---

# Model licenses

**What's on this page**

- Who this policy is for (US casual commercial, local weights only)
- Canonical table (same rows as repo-root `LICENSE-MODELS.md`)
- What we download by default vs omit
- LTX $10M company-revenue cap vs Wan Apache silent video
- How 90s shorts split still / silent motion / AV print
- What is banned (MiniMax H3, Klein 9B, FLUX.2-dev, API-only)

**What this enables**

- A grep-able policy CI can test
- Honest copy: LTX is the audio model and is **not Apache**; Wan is the legally cleanest motion model and has **no native audio**
- Operators can Queue the lab graphs without pulling US-excluded or non-commercial defaults

!!! warning "Not legal advice"

    This page encodes the stack’s **download and workflow policy**. It is not legal advice. Read each Hugging Face model card and license before you monetize. Company-revenue caps (LTX) count **affiliates**.

## Audience

US-based casual content creators: YouTube, client shorts, ads under a **small LLC**. Run **only locally hosted** models. No fal / Comfy Cloud / MiniMax API / Kling / Seedance / Veo partner nodes in lab graphs.

## Canonical table

Columns: model | HF repo | license name | US self-host OK? | monetized YouTube OK? | $ threshold | attribution | distillation ban | default download?

| model | HF repo | license name | US self-host OK? | monetized YouTube OK? | $ threshold | attribution | distillation ban | default download? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FLUX.2 Klein 4B distilled FP8 | black-forest-labs/FLUX.2-klein-4b-fp8 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| FLUX.2 Klein 4B base FP8 | black-forest-labs/FLUX.2-klein-base-4b-fp8 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| FLUX.2 Klein 4B NVFP4 | black-forest-labs/FLUX.2-klein-4b-nvfp4 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Qwen3-4B text encoder (Klein 4B companion) | Comfy-Org/flux2-klein-4B | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| FLUX.2 VAE | Comfy-Org/flux2-dev (split_files/vae) | Apache 2.0 companion | Yes | Yes | none | follow card | No extra ban beyond card | Yes |
| Z-Image Turbo | Comfy-Org/z_image_turbo | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Wan 2.2 TI2V-5B | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| Wan 2.2 A14B T2V/I2V | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| UMT5-XXL text encoder (Wan companion) | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| LTX-2.5 distilled INT8-convrot | Lightricks/LTX-2.5 | LTX Community License | Yes | Yes if company under cap | $10M COMPANY annual revenue (affiliates count) | disclose AI-generated media; do not strip provenance | Yes — do not distill into a competing model | Yes |
| LTX-2.3 distilled FP8 | Kijai/LTX2.3_comfy | LTX Community License | Yes | Yes if company under cap | $10M COMPANY annual revenue (affiliates count) | disclose AI-generated media; do not strip provenance | Yes — do not distill into a competing model | No |
| FLUX.2 Klein 9B | black-forest-labs/FLUX.2-klein-9b-nvfp4 | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| FLUX.2 [dev] | black-forest-labs/FLUX.2-dev | FLUX.2-dev / Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| MiniMax H3 | Comfy-Org/MiniMax-H3 | MiniMax H3 Community License | No — US Excluded Territory for weights AND outputs | No | n/a | n/a | n/a | No |
| Wan 2.5 / 2.6 / 2.7 / 3.0 | (API / partner) | API-only / partner | No (not local weights) | No as a lab default | n/a | n/a | n/a | No |
| Seedance / Kling / Veo / fal / Comfy Cloud | (API / partner) | API-only / partner | No (not local weights) | No as a lab default | n/a | n/a | n/a | No |
| HunyuanVideo 1.5 | Tencent Hunyuan | territorial clause (not EU/UK/KR) | Yes | Yes in the US | card | card | card | No |
| LongCat-Video | Meituan LongCat | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT | No |

The same table is in repo-root `LICENSE-MODELS.md` so tests can grep either file.

## Before `download-models`

LTX-2.5 is gated. Klein 4B and Wan 5B are Apache and do not need a license click.

1. Create or edit `.env` with `HF_TOKEN=hf_...` (or `hf auth login`)
2. In a browser, as **that same user**, open https://huggingface.co/Lightricks/LTX-2.5 and click **Agree**
3. Fine-grained tokens need **gated repo** read
4. `hf auth whoami` then `./scripts/manage.sh download-models`

A token in `.env` is **not** the same as accepting the Lightricks license. First-run path: [Getting Started](getting-started.md).

## Why these defaults

**Still (Apache 2.0):** FLUX.2 Klein **4B distilled FP8** is the official ComfyUI Klein 4B path (`flux-2-klein-4b-fp8.safetensors`, `qwen_3_4b.safetensors`, `flux2-vae.safetensors`). Distilled = 4 steps, CFG 1.0. Klein **9B** is FLUX Non-Commercial — **not** fine for monetized YouTube as a lab default. FLUX.2 [dev] is not a casual-commercial default.

**Runner-up still:** Z-Image Turbo (Apache 2.0, native Comfy templates). Optional `download-image --tier zimage` if Klein 4B quality disappoints. Qwen-Image is the slower quality sibling — documented only, not a default download.

**Silent motion (Apache 2.0):** Wan 2.2 TI2V-5B is the daily driver (T2V + I2V, official Comfy templates). **No native audio.** Wan 2.2 A14B is an optional hero (`download-wan --tier a14b`), not the first download.

**Audio + video (not Apache):** LTX-2.5 distilled INT8-convrot is the AV hero. **LTX Community License**: free commercial under **$10M COMPANY annual revenue (affiliates count)**; **no US geo-ban**; disclose AI-generated media; do not strip provenance; do not distill into a competing model. Hugging Face repo is **gated** — accept the license and set `HF_TOKEN` before `download-models`. Lab download is the **small distilled set**, not the 400 GB monorepo.

**LTX-2.3:** optional fallback (`download-ltx --tier 2.3`) if 2.5 access or INT8-convrot fails. Not advertised as 30 s / 60 s films.

**90s films:** Klein identity still + Wan 5.00s silent rehearsal + LTX 5.00s print (world audio, no score), concat with a 90s cap. Do not Queue 90s in one graph. See [90s shorts](shorts.md).

**Omitted:** LongCat-Video (custom-node risk). HunyuanVideo 1.5 (US-legal but territorial clause for other countries — not the one-stack default).

## Banned

Do not download, do not reference in lab graphs, do not pin Comfy for them:

- MiniMax H3 (US Excluded Territory for **weights and outputs**)
- FLUX.2 [dev] as any default or “quality” tier
- FLUX.2 Klein 9B as the default image model
- API-only models (Wan 2.5/2.6/2.7/3.0, Seedance, Kling, Veo, fal, Comfy Cloud, MiniMax API)

`./scripts/manage.sh download-models` **refuses** MiniMax H3.

## Default `download-models` pack

Apache still: `flux-2-klein-4b-fp8.safetensors` + `qwen_3_4b.safetensors` + `flux2-vae.safetensors`

Apache silent motion: `wan2.2_ti2v_5B_fp16.safetensors` + `wan2.2_vae.safetensors` + `umt5_xxl_fp8_e4m3fn_scaled.safetensors`

LTX AV (not Apache): `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` + `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` + `ltx-2.5-video-vae-bf16.safetensors` + `ltx-2.5-audio-vae-bf16.safetensors`

## Doctor one-liner

`manage.sh doctor` prints:

`License policy: Apache Klein 4B still + Apache Wan 2.2 5B silent + LTX-2.5 AV (Community, under 10M company USD). Not legal advice. See docs/licenses.md`
