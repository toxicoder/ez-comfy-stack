---
title: MiniMax H3 90s films
description: GO SEE, STILL HERE, and SWITCHYARD MiniMax H3 lab graphs — 2160 frames / 90.00s, native audio, challenge rules.
tags: [h3, minimax, comfyui, video, challenge]
---

# MiniMax H3 90s films

**What's on this page**

- Challenge duration cap (90.00s, never 90.17s)
- GO SEE / STILL HERE / SWITCHYARD theses and shot maps
- Native node graph, weights, and opt-in download
- Missing Node Packs / Unknown pack (core v0.34.0 — not Manager)
- License warning (geo / Community License)

**What this enables**

- The same ComfyUI UX as Flux/LTX: open `:8188`, load a `*-lab-example` graph, **Queue**
- A Sync Sound–legal mux: native H3 audio, **2160 frames @ 24 fps = 90.00s**
- The workflow JSON you Queue is the file the challenge asks you to submit

!!! warning "Comfy H3 Sync Sound — 90 seconds maximum"

    [Challenge rules](https://blog.comfy.org/p/comfy-h3-sync-sound-community-challenge): **90 seconds maximum length**, H3-native synced audio (no post-H3 soundtrack), SFW, no unlicensed IP or likenesses, one submission per user. Submit **GO SEE** plus its workflow JSON. STILL HERE and SWITCHYARD are extra lab films with the same hard cap.

## Duration math

H3 cannot quality-sample 90s in one denoise. Do **not** set `length=2164` or `length=2160` on a single `MiniMaxH3ImageToVideo`.

| Stage | Frames | Seconds @ 24 fps |
| --- | --- | --- |
| Six FL2VA columns | `6 × 379` | — |
| Overlap trim (shots 2–6) | `− 5 × 22` | — |
| Unique generated | 2164 | 90.166…s (internal) |
| **Challenge cap (drop last 4 of the hold)** | **2160** | **90.00s — the file** |

`CreateVideo` fps=24. `TrimAudioDuration` to **90.00s**. `stitch-h3` applies `ffmpeg -t 90` and **fails** if probed duration `> 90`.

## Operator path (ComfyUI, like Flux / LTX)

```bash
./scripts/manage.sh download-h3          # opt-in; default download-models stays flux+ltx
./scripts/manage.sh start                # type yes; volume pin syncs to v0.34.0 (native H3 nodes)
# open http://<spark-ip>:8188
```

In the UI: **Workflows** → `h3-go-see-90s-lab-example` (seeded from host `workflows/` into `user/default/workflows/`). Drag-drop of the same JSON still works. Review the six shot prompts, **Queue**, watch **SaveVideo**. That MP4 plus this JSON are the contest submission.

!!! warning "Missing Node Packs / Unknown pack for MiniMaxH3*"

    `MiniMaxH3AddGuide`, `MiniMaxH3ImageToVideo`, and `MiniMaxH3SigmaShift` are **native ComfyUI v0.34.0** nodes (`comfy_extras/nodes_minimax_h3.py`, listed in `nodes.py`, `cnr_id: comfy-core`) — not a custom pack. Do **not** `pip install comfyui-manager` and do **not** restart with `--enable-manager`. After `git pull`, `./scripts/manage.sh stop` then `start` so the volume pin (`.lab-comfyui-ref`) and extras loader sync to `v0.34.0`. Hard-refresh the browser. Details: [Troubleshooting](troubleshooting.md).

OOM at 1344×768×379: on each `MiniMaxH3ImageToVideo` set width/height to **864×480** (0.4 MP table). Do **not** raise `MEM_LIMIT`.

??? note "Optional: POST the same graph (not the contest UX)"

    `./scripts/manage.sh queue-h3 --film go-see` posts the lab-example JSON to local `:8188`. Use it for automation; generating the film for the challenge is still **Queue in ComfyUI**. `--size 864x480` is the CLI equivalent of the UI resize.

## Weights (CLIP type `minimax`)

| File | `MODELS_DIR/comfy/` |
| --- | --- |
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `diffusion_models/` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `text_encoders/` |
| `minimax_h3_video_vae_fp16.safetensors` | `vae/` |
| `minimax_h3_audio_vae_fp32.safetensors` | `vae/` |

Source: [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3). Optional `--tier ref2va` / `--tier turbo` are documented only; quality path does not use turbo LoRAs.

The brief’s CLIP type `qwen_image` is outdated on ComfyUI 0.34+; lab graphs use **`minimax`**.

## Graph (native nodes only)

Shared: `UNETLoader` → `MiniMaxH3SigmaShift` (12 / 3) → `BasicScheduler` simple 20; `CLIPLoader` type `minimax`; two `VAELoader`s.

Per shot: `MiniMaxH3ImageToVideo` 1344×768 length **379**; shots 2–6 `MiniMaxH3AddGuide` at `frame_idx=0` (prev last frame + prev H3 audio bed); `RandomNoise` fixed seed; `BasicGuider` (CFG 1.0); `KSamplerSelect` `res_multistep`; `SamplerCustomAdvanced`; `VAEDecode` + `VAEDecodeAudio`; last-frame `ImageFromBatch`; shots 2–6 `ImageFromBatch` start 22 / length 357 and `TrimAudioDuration` 22/24 s.

Fold: `ImageBatch` + `AudioConcat` → keep **2160** frames + audio **90.00s** → `CreateVideo` 24 fps → `SaveVideo`.

Optional canvas note: [NikoDemon80/ComfyUI-H3-Motion-Context](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context) (`context_length=22`, `audio_context_length=24`, `match_tail=true`). **Default graph does not depend on that pack.**

## Films

**GO SEE** (default farm / intended contest entry): first-person only, Hardcore Henry camera, **zero violence**, olive windbreaker + worn black gloves in frame on every plant. Parkour is transportation. Native audio: breath + world objects. **No score.**

1. Rooftop dawn → barrel roll through sky → warehouse roof
2. Ladder drop, market pallet vault → under awning → river
3. Stones → through bridge arch → beech forest, creek jump
4. Trees thin → boulder front flip → headland / generic lighthouse
5. Granite steps → through stone-wall gap → mountain meadow
6. Ridge stop. Hands on wooden rail. Look. Quiet laugh. Hold.

**STILL HERE**: third-person household morning. Mug + invented child-hum motif. SFW; no real-child likeness as a first frame.

**SWITCHYARD**: night freight yard. Generic cars; no railroad marks.

Prefixes: `video/GO_SEE_90s_H3`, `video/STILL_HERE_90s_H3`, `video/SWITCHYARD_90s_H3`.

!!! warning "MiniMax H3 Community License (geo)"

    Open weights and their outputs treat the US / EU / UK / South Korea as **excluded territories** unless MiniMax grants a formal authorization. Hosted API / Comfy Cloud is global. This stack downloads **local** weights and does **not** geo-block the downloader. Read MiniMax’s license Q&A on the [MiniMax-H3 model card](https://huggingface.co/MiniMaxAI/MiniMax-H3) before generating. No license bypass in this repo.
