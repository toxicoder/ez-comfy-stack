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
| Qwen3-4B-Instruct-2507 Q4_K_M GGUF | unsloth/Qwen3-4B-Instruct-2507-GGUF | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | Yes |
| Kokoro-82M | hexgrad/Kokoro-82M (ONNX pack: fastrtc/kokoro-onnx) | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| ACE-Step 1.5 turbo AIO | Comfy-Org/ace_step_1.5_ComfyUI_files | MIT upstream / Apache companion pack | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| ACE-Step 1.5 XL | Comfy-Org/ace_step_1.5_ComfyUI_files | MIT | Yes | Yes | none | MIT | No extra ban beyond MIT | No |
| MiniMax Music 3 | (partner / not lab default) | MiniMax Music 3 | No — not a lab default | No | n/a | n/a | n/a | No |
| Suno / Udio | (partner) | API-only / partner | No (not local weights) | No | n/a | n/a | n/a | No |
| Chatterbox / Multilingual v3 / Turbo | ResembleAI/chatterbox | MIT | Yes | Yes | none | MIT; PerTh watermark stays on | No extra ban beyond MIT | No |
| Qwen3-TTS 0.6B | Qwen/Qwen3-TTS-12Hz-0.6B-Base | Apache 2.0 | Yes | Yes | none | Apache NOTICE if you redistribute weights | No extra ban beyond Apache | No |
| F5-TTS official weights | SWivid/F5-TTS | CC-BY-NC-4.0 | No | No | n/a | n/a | n/a | No |
| Coqui XTTS v2 | coqui/XTTS-v2 | CPML | No | No | n/a | n/a | n/a | No |
| Echo-TTS | (Echo-TTS card) | CC-BY-NC-SA | No | No | n/a | n/a | n/a | No |
| Fish Audio S2 | Fish Audio S2 | research/NC | No | No | n/a | n/a | n/a | No |
| Higgs Boson | Higgs v2/v3 | community/commercial traps | No | No | n/a | n/a | n/a | No |
| TTS-Audio-Suite | diodiogod/TTS-Audio-Suite | mixed NC / research pack | No | No | n/a | n/a | n/a | No |
| OldTimeRadio | jbrick2070/ComfyUI-OldTimeRadio | H3 / FLUX-dev / NC optional lanes | No | No | n/a | n/a | n/a | No |

## Banned from this stack (do not download, do not pin lab graphs)

- MiniMax H3 and MiniMaxH3* nodes/workflows
- MiniMax Music 3 as a lab default
- Suno / Udio partner APIs
- FLUX.2 [dev] as any default or “quality” tier
- FLUX.2 Klein 9B (`flux-2-klein-9b`, `FLUX.2-klein-9b-nvfp4`, Nunchaku 9B) as the default image model
- API-only / US-excluded / paid-self-host-required models (Wan 2.5+, Seedance, Kling, Veo, fal, Comfy Cloud, MiniMax API)
- F5-TTS official weights (CC-BY-NC-4.0), Coqui XTTS v2 (CPML), Echo-TTS (CC-BY-NC-SA)
- Fish Audio S2 (research/NC), Higgs Boson (community/commercial traps)
- TTS-Audio-Suite as a pack; OldTimeRadio as a pack

## Default `download-models` pack

Apache still: `flux-2-klein-4b-fp8.safetensors` + `qwen_3_4b.safetensors` + `flux2-vae.safetensors`

Apache silent motion: `wan2.2_ti2v_5B_fp16.safetensors` + `wan2.2_vae.safetensors` + `umt5_xxl_fp8_e4m3fn_scaled.safetensors`

LTX AV (not Apache): `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` + `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` + `ltx-2.5-video-vae-bf16.safetensors` + `ltx-2.5-audio-vae-bf16.safetensors`

Apache prompt-enhance GGUF: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
