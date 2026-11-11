# Model licenses (US self-host policy)

This file is the **grep-able** license table for ez-comfy-stack. Operator prose lives in [docs/licenses.md](docs/licenses.md). **Not legal advice.** Confirm each Hugging Face card before commercial use.

Policy: US-based casual creators (YouTube, client shorts, ads under a small LLC) may run **only locally hosted** weights whose licenses allow ordinary commercial use of self-hosted outputs. No cloud partner nodes. No API-only models. No weights whose license excludes the United States.

| model | HF repo | license name | US self-host OK? | monetized YouTube OK? | $ threshold | attribution | distillation ban | default download? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FLUX.2 Klein 4B distilled FP8 | black-forest-labs/FLUX.2-klein-4b-fp8 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| FLUX.2 Klein 4B base FP8 | black-forest-labs/FLUX.2-klein-base-4b-fp8 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| FLUX.2 Klein 4B NVFP4 | black-forest-labs/FLUX.2-klein-4b-nvfp4 | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Qwen3-4B text encoder (Klein 4B companion) | Comfy-Org/flux2-klein-4B | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| FLUX.2 VAE | Comfy-Org/flux2-dev (split_files/vae) | Apache 2.0 companion | Yes | Yes | none | follow card | No extra ban beyond card | Yes |
| FLUX.2 small decoder VAE | black-forest-labs/FLUX.2-small-decoder | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Z-Image Turbo | Comfy-Org/z_image_turbo | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Wan 2.2 TI2V-5B | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| Wan 2.2 A14B T2V/I2V | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Wan 2.2 Fun InP A14B | alibaba-pai/Wan2.2-Fun-A14B-InP | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| SeedVR2-3B | ByteDance-Seed/SeedVR2-3B | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| TRELLIS.2 native | Comfy-Org/TRELLIS.2 | MIT | Yes | Yes | none | MIT NOTICE | No extra ban beyond MIT. No nvdiffrast/nvdiffrec | No |
| DINOv3 ViT-L (TRELLIS companion) | Comfy-Org/TRELLIS.2 (clip_vision) | DINOv3 License | Yes | Yes if you comply with the DINOv3 license | none | DINOv3 LICENSE with the pack | card | No |
| DA3-BASE | depth-anything/DA3-BASE | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| DeepLabV3 ResNet50 person mask | pytorch/vision (deeplabv3_resnet50 COCO-with-VOC) | BSD-3 | Yes | Yes | none | BSD NOTICE if you redistribute weights | No extra ban beyond BSD | No |
| BiRefNet matte (EZCutout input prep) | ZhengPeng7/BiRefNet | MIT | Yes | Yes | none | MIT NOTICE if you redistribute weights | No extra ban beyond MIT | No |
| Wan 2.1 VACE 1.3B | Wan-AI/Wan2.1-VACE-1.3B | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Wan 2.2 S2V 14B | Wan-AI/Wan2.2-S2V-14B | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| SuperSplat | playcanvas/supersplat | MIT | Yes | Yes | none | MIT | Host static viewer. Not in Dockerfile | No |
| UMT5-XXL text encoder (Wan companion) | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| LTX-2.5 distilled INT8-convrot | Lightricks/LTX-2.5 | LTX Community License | Yes | Yes if company under cap | $10M COMPANY annual revenue (affiliates count) | disclose AI-generated media; do not strip provenance | Yes - do not distill into a competing model | Yes |
| LTX-2.5 IC-LoRA Union Control | Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control | LTX Community License | Yes | Yes if company under cap | $10M COMPANY annual revenue (affiliates count) | disclose AI-generated media; do not strip provenance | Yes - do not distill into a competing model. Distilled-only. Official 2.5 graph widgets `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors`. Refuse 19B Union. | No |
| LTX-2.3 distilled FP8 | Kijai/LTX2.3_comfy | LTX Community License | Yes | Yes if company under cap | $10M COMPANY annual revenue (affiliates count) | disclose AI-generated media; do not strip provenance | Yes - do not distill into a competing model | No |
| FLUX.2 Klein 9B | black-forest-labs/FLUX.2-klein-9b-fp8 | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| FLUX.2 Klein 9B base FP8 | black-forest-labs/FLUX.2-klein-base-9b-fp8 | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| FLUX.2 Klein 9B NVFP4 | black-forest-labs/FLUX.2-klein-9b-nvfp4 | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| Qwen3-8B text encoder (Klein 9B companion) | Comfy-Org/flux2-klein-9B | follow card | Yes (with 9B) | No | follow card | card | card | No |
| FLUX.2 [dev] | black-forest-labs/FLUX.2-dev | FLUX.2-dev / Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| FLUX.2 [dev] FP8 Comfy pack | Comfy-Org/flux2-dev | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| Mistral Small Flux2 text encoder | Comfy-Org/flux2-dev (split_files/text_encoders) | FLUX Non-Commercial | Yes (non-commercial only) | No | paid BFL commercial license | card | card | No |
| FLUX 3 Image Klein distilled INT8-convrot | black-forest-labs/flux-3-image-klein-comfy | FLUX Kommunity License (v1.0) | Yes | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| FLUX 3 Image Klein base INT8 | black-forest-labs/flux-3-image-klein-comfy | FLUX Kommunity License (v1.0) | Yes | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| FLUX 3 Image Klein base NVFP4 | black-forest-labs/flux-3-image-klein-comfy | FLUX Kommunity License (v1.0) | Yes | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| FLUX 3 Image Klein base BF16 | black-forest-labs/flux-3-image-klein-comfy | FLUX Kommunity License (v1.0) | Yes | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| Qwen3VL-4B text encoder (FLUX 3 companion) | black-forest-labs/flux-3-image-klein-comfy (text_encoders) | FLUX Kommunity License (v1.0) | Yes (with FLUX 3) | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| Qwen3.5-9B prompt upsampler (FLUX 3 companion) | black-forest-labs/flux-3-image-klein-comfy (text_encoders) | FLUX Kommunity License (v1.0) | Yes (with FLUX 3) | Yes if a qualifying user under the cap | $5M gross annualized revenue (qualifying users) | card | card | No |
| Qwen-Image 2.1 INT8-convrot | Comfy-Org/Qwen-Image-2.1 (upstream: Qwen/Qwen-Image-2.1) | Qwen RESEARCH LICENSE AGREEMENT | Yes (research and personal use only) | No | paid Qwen commercial license | ship the Qwen RESEARCH LICENSE AGREEMENT and the NOTICE; show "Built with Qwen" in product docs | none stated. Section 4.b wants "Improved using Qwen" on any model you ship; 4.c bars Qwen as the primary product name | No |
| Qwen-Image 2.1 Turbo INT8-convrot | Comfy-Org/Qwen-Image-2.1 (upstream: Qwen/Qwen-Image-2.1-Turbo) | Qwen RESEARCH LICENSE AGREEMENT | Yes (research and personal use only) | No | paid Qwen commercial license | ship the Qwen RESEARCH LICENSE AGREEMENT and the NOTICE; show "Built with Qwen" in product docs | none stated. Section 4.b wants "Improved using Qwen" on any model you ship; 4.c bars Qwen as the primary product name | No |
| Qwen-Image 2.1 NVFP4 | BennyDaBall/Qwen-Image-2.1-NVFP4 (converts Comfy-Org/Qwen-Image-2.1) | Qwen RESEARCH LICENSE AGREEMENT | Yes (research and personal use only) | No | paid Qwen commercial license | BennyDaBall NOTICE plus the Qwen attribution line; show "Built with Qwen" in product docs | none stated. Section 4.b wants "Improved using Qwen" on any model you ship; 4.c bars Qwen as the primary product name | No |
| Qwen-Image 2.1 Turbo NVFP4 | BennyDaBall/Qwen-Image-2.1-Turbo-NVFP4 (converts Comfy-Org/Qwen-Image-2.1-Turbo) | Qwen RESEARCH LICENSE AGREEMENT | Yes (research and personal use only) | No | paid Qwen commercial license | BennyDaBall NOTICE plus the Qwen attribution line; show "Built with Qwen" in product docs | none stated. Section 4.b wants "Improved using Qwen" on any model you ship; 4.c bars Qwen as the primary product name | No |
| Qwen3VL-8B text encoder (Qwen-Image 2.1 companion) | Comfy-Org/Qwen-Image-2.1 (text_encoders) and both BennyDaBall packs | Qwen RESEARCH LICENSE AGREEMENT | Yes (with Qwen-Image 2.1) | No | paid Qwen commercial license | ship the Qwen RESEARCH LICENSE AGREEMENT and the NOTICE | none stated. Section 4.c bars Qwen as the primary product name | No |
| Qwen-Image 2.1 VAE BF16 | Comfy-Org/Qwen-Image-2.1 (vae), redistributed by both BennyDaBall packs | Qwen RESEARCH LICENSE AGREEMENT | Yes (with Qwen-Image 2.1) | No | paid Qwen commercial license | ship the Qwen RESEARCH LICENSE AGREEMENT and the NOTICE | none stated | No |
| MiniMax H3 | Comfy-Org/MiniMax-H3 | MiniMax H3 Community License | No - US Excluded Territory for weights AND outputs | No | n/a | n/a | n/a | No |
| Wan 2.5 / 2.6 / 2.7 / 3.0 | (API / partner) | API-only / partner | No (not local weights) | No as a lab default | n/a | n/a | n/a | No |
| Seedance / Kling / Veo / fal / Comfy Cloud | (API / partner) | API-only / partner | No (not local weights) | No as a lab default | n/a | n/a | n/a | No |
| HunyuanVideo 1.5 | Tencent Hunyuan | territorial clause (not EU/UK/KR) | Yes | Yes in the US | card | card | card | No |
| LongCat-Video | meituan-longcat/LongCat-Video | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT. No NCCL | No |
| DreamX-Creator 1.0 | GD-ML/DreamX-Creator | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache. Not DreamX-World | No |
| Qwen3-4B-Instruct-2507 Q4_K_M GGUF | unsloth/Qwen3-4B-Instruct-2507-GGUF | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| Qwen2.5-VL-3B-Instruct Q4_K_M GGUF | ggml-org/Qwen2.5-VL-3B-Instruct-GGUF | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Qwen3.6-35B-A3B UD-Q4_K_XL GGUF | unsloth/Qwen3.6-35B-A3B-MTP-GGUF | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| Qwen3.8-Flash-Next FP4 (editing agent sidecar, opt-in host recipe) | nvidia/Qwen3.8-Flash-Next-FP4-Local | NVIDIA Open Model License (base: Qwen Community License 1.0) | Yes (card: commercial use OK) | Yes per card | none per card | follow card | card | No |
| TensorFold engine (agent sidecar runtime, opt-in host checkout) | github.com/ashhart/TensorFold | Apache 2.0 | Yes | Yes | none | Apache NOTICE | No extra ban beyond Apache | No |
| Kokoro-82M | hexgrad/Kokoro-82M (ONNX pack: fastrtc/kokoro-onnx) | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| ACE-Step 1.5 turbo AIO | Comfy-Org/ace_step_1.5_ComfyUI_files | MIT upstream / Apache companion pack | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| ACE-Step 1.5 XL | Comfy-Org/ace_step_1.5_ComfyUI_files | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| MiniMax Music 3 | (partner / not lab default) | MiniMax Music 3 | No - not a lab default | No | n/a | n/a | n/a | No |
| Suno / Udio | (partner) | API-only / partner | No (not local weights) | No | n/a | n/a | n/a | No |
| Chatterbox / Multilingual v3 / Turbo | ResembleAI/chatterbox | MIT | Yes | Yes | none | MIT; PerTh watermark stays on | No extra ban beyond MIT | No |
| Qwen3-TTS 0.6B | Qwen/Qwen3-TTS-12Hz-0.6B-Base | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| faster-whisper large-v3 | Systran/faster-whisper-large-v3 | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| Silero VAD | snakers4/silero-vad | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| F5-TTS official weights | SWivid/F5-TTS | CC-BY-NC-4.0 | No | No | n/a | n/a | n/a | No |
| Coqui XTTS v2 | coqui/XTTS-v2 | CPML | No | No | n/a | n/a | n/a | No |
| Echo-TTS | (Echo-TTS card) | CC-BY-NC-SA | No | No | n/a | n/a | n/a | No |
| Fish Audio S2 | Fish Audio S2 | research/NC | No | No | n/a | n/a | n/a | No |
| Higgs Boson | Higgs v2/v3 | community/commercial traps | No | No | n/a | n/a | n/a | No |
| TTS-Audio-Suite | diodiogod/TTS-Audio-Suite | mixed NC / research pack | No | No | n/a | n/a | n/a | No |
| OldTimeRadio | jbrick2070/ComfyUI-OldTimeRadio | H3 / FLUX-dev / NC opt-in lanes | No | No | n/a | n/a | n/a | No |

TRELLIS.2 footnote: download `Comfy-Org/TRELLIS.2` (`trellis_2_int8_convrot` + shape/texture VAEs + `dino_v3_vit_l`). Original research weights: microsoft/TRELLIS.2. Companion encoder DINOv3 (Meta custom license, commercial-friendly) is not a default download - it ships inside opt-in `download-3d --tier trellis2`. Native TRELLIS Comfy basenames such as `trellis_2_int8_convrot` are opt-in via `download-3d` only - do not treat them as `download-models`.

## Banned from this stack (do not download, do not pin lab graphs)

- MiniMax H3 and MiniMaxH3* nodes/workflows
- MiniMax Music 3 as a lab default
- Suno / Udio partner APIs
- FLUX.2 [dev] as any default or "quality" image `--tier` alias (opt-in is `download-image --tier flux2-dev`)
- FLUX.2 Klein 9B (`flux-2-klein-9b-fp8`, `FLUX.2-klein-9b-nvfp4`, Nunchaku 9B) as the **default** image model or a pinned lab UNET (opt-in is `download-image --tier 9b`)
- FLUX 3 Image Klein (`flux3`, `flux3-base`, `flux3-nvfp4`, `flux3-bf16`, `flux3-te`, `flux3-pup`) as the **default** image model or promoted into the `photos/` lane - FLUX Kommunity License (v1.0), opt-in only via `download-image --tier flux3`; the opt-in `labs/opt-in/still-flux3-*` lab graphs are allowed and never default
- Qwen-Image 2.1 (`qwen-image`, `qwen-image-turbo`, `qwen-image-nvfp4`, `qwen-image-turbo-nvfp4`, plus the `qwen-image-te` / `qwen-image-vae` companions) as the **default** image model, a pinned lab UNET, or a monetized-output pick - Qwen RESEARCH LICENSE AGREEMENT bars commercial use until you hold a separate paid Qwen license; opt-in only via `download-image --tier qwen-image*`, and **Klein 4B stays the Apache default still**
- The raw `Qwen/Qwen-Image-2.1` and `Qwen/Qwen-Image-2.1-Turbo` diffusers folders as a download source - ComfyUI cannot load a diffusers tree in this stack; pull `Comfy-Org/Qwen-Image-2.1` instead
- Nunchaku 9B packs
- API-only / US-excluded / paid-self-host-required models (Wan 2.5+, Seedance, Kling, Veo, fal, Comfy Cloud, MiniMax API)
- F5-TTS official weights (CC-BY-NC-4.0), Coqui XTTS v2 (CPML), Echo-TTS (CC-BY-NC-SA)
- Fish Audio S2 (research/NC), Higgs Boson (community/commercial traps)
- TTS-Audio-Suite as a pack; OldTimeRadio as a pack
- nvdiffrast / nvdiffrec TRELLIS, DA3-LARGE, Inria 3DGS, Pixal3D-as-default
- DreamX-World (Creator 1.0 Apache only)
- Wav2Lip OSS
- LTX-2 19B IC-LoRA Union Control (`Lightricks/LTX-2-19b-IC-LoRA-Union-Control`)

## Default `download-models` pack

Apache still: `flux-2-klein-4b-fp8.safetensors` + `qwen_3_4b.safetensors` + `flux2-vae.safetensors`

Opt-in NC still (not in `download-models`): `flux-2-klein-9b-fp8.safetensors` + `qwen_3_8b_fp8mixed.safetensors` + `full_encoder_small_decoder.safetensors` via `download-image --tier 9b`. FLUX Non-Commercial - not monetized YouTube. `flux2_dev_fp8mixed.safetensors` + `mistral_3_small_flux2_bf16.safetensors` via `--tier flux2-dev`.

Opt-in FLUX 3 Image Klein still (not in `download-models`, gated, HF revision-pinned at `feef60b0aaf63a4773ace96636ebbcf43b881312`): `flux3-image-klein-int8-convrot.safetensors` + `qwen3vl_4b_int8_convrot.safetensors` via `download-image --tier flux3`. Base variants `flux3-image-klein-base-int8-convrot.safetensors` (`--tier flux3-base`), `flux3-image-klein-base-nvfp4.safetensors` (`--tier flux3-nvfp4`), `flux3-image-klein-base-bf16.safetensors` (`--tier flux3-bf16`). Optional prompt upsampler `qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors` via `--tier flux3-pup`. All six are **FLUX Kommunity License (v1.0)** - monetized output is OK only for qualifying users under **$5M gross annualized revenue**. FLUX 3 is *not* Apache and is never a default; **Klein 4B remains the Apache default still**. Not legal advice.

Opt-in Qwen-Image 2.1 still (not in `download-models`, public repos, HF revision-pinned): `qwen_image_2.1_int8_convrot.safetensors` via `download-image --tier qwen-image`, or the distilled sibling `qwen_image_2.1_turbo_int8_convrot.safetensors` via `--tier qwen-image-turbo` - both pull the shared `qwen3vl_8b_int8_convrot.safetensors` encoder (`--tier qwen-image-te`) and `qwen_image_2.1_vae_bf16.safetensors` (`--tier qwen-image-vae`) for you. BennyDaBall's native NVFP4 conversions: `qwen_image_2.1_nvfp4.safetensors` + `qwen3vl_8b_nvfp4.safetensors` via `--tier qwen-image-nvfp4`, and `qwen_image_2.1_turbo_nvfp4.safetensors` + `qwen3vl_8b_turbo_nvfp4.safetensors` via `--tier qwen-image-turbo-nvfp4`. All four are the **Qwen RESEARCH LICENSE AGREEMENT** (2026-09-20, Hangzhou Tongyi Laboratory) - section 2.b bars commercial use until you hold a separate paid Qwen license, so none is a default, none is in image `--tier all`, and **Klein 4B remains the Apache default still**. The official `Qwen/Qwen-Image-2.1` and `Qwen/Qwen-Image-2.1-Turbo` repos are diffusers trees that ComfyUI cannot load in this stack; the downloader always pulls the Comfy-Org repack `Comfy-Org/Qwen-Image-2.1` (pinned `aacf31a6d48e707f352ecba714cee0680da3479b`), with the BennyDaBall packs pinned at `b0e954a1ba86f00e30f76bac2494f45b0a221948` and `82226d8cadaf20a678338f8faf5e5a0cfc3e1dfd`. Not legal advice.

Apache silent motion: `wan2.2_ti2v_5B_fp16.safetensors` + `wan2.2_vae.safetensors` + `umt5_xxl_fp8_e4m3fn_scaled.safetensors`

LTX AV (not Apache): `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` + `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` + `ltx-2.5-video-vae-bf16.safetensors` + `ltx-2.5-audio-vae-bf16.safetensors`

Apache prompt-enhance GGUF: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
