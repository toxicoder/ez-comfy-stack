---
title: Download tiers
description: What --tier actually selects on each download command — pack ids, not a global quality ladder.
tags: [download, tier, models, klein, wan, ltx, podcast, dub, music]
---

# Download tiers

**What's on this page**

- **Chooser** — which command to run for the graph you will Queue
- **`--tier` vs `--limit`** — pack id versus Mbps
- **Default pack** — `download-models` (no `--tier`)
- **Per-family packs** — image, Wan, LTX, audio, 3D, extras
- **Banned names** — `quality` as an image `--tier` alias, Nunchaku, DA3-LARGE, DreamX-World, MiniMax H3. Klein 9B / FLUX.2-dev are **opt-in NC**, not defaults.

**What this enables**

- **Picking** the flag that matches the graph you will Queue
- **Avoiding** a ~47 GB Fun InP pull when you wanted Wan 2.2 5B
- **Copying** a command with **your** `--tier` and `--limit` already filled in

The **Your Spark** panel at the top of every docs page stores `SPARK_HOST` and friends in this browser. Highlighted chips in copyable commands are the same fields — click to edit. Copy buttons use those values. `--limit` defaults follow `DOWNLOAD_LIMIT` unless you override it on the widget.

Basenames on disk: [Download packs](operate/models-packs.md). Mbps throttle: [Download limit](download-limit.md).

---

## Choose a pack

<div class="grid cards" markdown>

-   :material-package-down:{ .lg .middle } **First install**

    ---

    Klein 4B + Wan 5B + LTX-2.5 + prompt-enhance GGUF. No `--tier`.

    [:octicons-arrow-right-24: Default pack](#default-pack-download-models)

-   :material-image:{ .lg .middle } **A different still**

    ---

    Klein NVFP4 / base, or Z-Image Turbo. Not “better video”.

    [:octicons-arrow-right-24: Image](#image-still-unet)

-   :material-movie-open:{ .lg .middle } **A different Wan graph**

    ---

    A14B, Fun InP, VACE, or S2V. `--tier all` skips VACE and S2V.

    [:octicons-arrow-right-24: Wan](#wan-different-graphs)

-   :material-volume-high:{ .lg .middle } **LTX or IC-LoRA**

    ---

    Lab default is 2.5. `balanced` / `quality` are 2.3 aliases.

    [:octicons-arrow-right-24: LTX](#ltx-generation-not-better)

-   :material-microphone:{ .lg .middle } **Podcast, dub, music**

    ---

    Opt-in audio. ACE-Step turbo is shared. Occupancy audio.

    [:octicons-arrow-right-24: Audio](#audio-podcast-dub-music)

-   :material-cube-outline:{ .lg .middle } **3D or extras**

    ---

    TRELLIS.2, LongCat, DreamX-Creator, SeedVR2, 35B llm-desk.

    [:octicons-arrow-right-24: Opt-in extras](#opt-in-extras)

</div>

---

## `--tier` vs `--limit`

| Flag | Means | Does not mean |
| --- | --- | --- |
| **`--tier NAME`** | Which **pack** that one utility pulls | A studio-wide quality ladder |
| **`--limit auto\|N\|off`** | Hugging Face **bandwidth** cap (Mbps) | Smaller / faster weights |
| **`download-models`** | Klein 4B + Wan 5B + LTX-2.5 + GGUF | Podcast, music, 3D, LongCat, DreamX, SeedVR2 |

`download-models` has **no** `--tier`. Image `fast`, Wan `5b`, and LTX `2.5` are three different pack ids that happen to be the lab defaults.

`--tier all` is **per utility**:

| Utility | `--tier all` includes | Does not include |
| --- | --- | --- |
| Image | `fast` + `nvfp4` + `base` + `zimage` (and TE/VAE companions) | `9b`, `9b-base`, `9b-nvfp4`, `flux2-dev` (FLUX Non-Commercial; pick those flags on purpose) |
| Wan | `5b` + `a14b` + `fun-inp` | `vace`, `s2v` |
| LTX | `2.5` + `2.3` + `gemma` | `iclora` (and not `quality`; quality is a 2.3 alias you pick on purpose) |
| Podcast | `analog` + `acestep` + `chatterbox` + `qwen3tts` | — |
| Dub | `asr` + `clone` | — |
| Music | `turbo` + `xl` | — |
| 3D | `trellis2` + `da3-base` | `da3-large` (refused) |
| LongCat | `video` + `avatar` | NCCL |
| LLM | `enhance` + `qwen36-35b-a3b` | putting 35B into `download-models` |
| DreamX | same as `creator` | DreamX-World (refused) |

Banned names (`quality` as an image `--tier` alias, Nunchaku, DA3-LARGE, DreamX-World, MiniMax H3) stay refused. Klein 9B and FLUX.2-dev are gated **opt-in** packs (`--tier 9b` / `flux2-dev`), not lab defaults — [Model licenses](licenses.md).

Occupancy: one heavy GPU job. `occupancy enter trellis` (unload LTX/Wan, stop Blender) before TRELLIS. Same rule for Fun InP / VACE / S2V / ACE-Step / llm-desk.

---

## Queue this → pull this

| You will Queue | Pull |
| --- | --- |
| `_lab/stills/still-draft` (and most Klein stills) | `download-models` or `download-image --tier fast` |
| Klein daily UNET swap NVFP4 / base | `download-image --tier nvfp4` or `base` |
| Z-Image Turbo graph | `download-image --tier zimage` |
| `_lab/motion/silent/still-to-video-5s`, `text-to-video-5s`, shot / GIF / bumper | `download-models` or `download-wan --tier 5b` |
| Wan A14B silent hero | `download-wan --tier a14b` |
| `motion/silent/first-last-5s` first-last-frame | `download-wan --tier fun-inp` (~47 GB, floor 40) |
| VACE join | `download-wan --tier vace` (not in Wan `all`) |
| Wan S2V talking-head | `download-wan --tier s2v` (not in Wan `all`) |
| `_lab/motion/av/*` lab AV printers | `download-models` or `download-ltx --tier 2.5` |
| LTX IC-LoRA control graphs | `download-ltx --tier iclora` (not in LTX `all`) |
| Retired LTX-2.3 DualCLIP fallback | `download-ltx --tier 2.3` (auto-includes `gemma`) |
| Podcast Kokoro | `download-podcast --tier analog` |
| Podcast beds / rap ACE-Step | `download-podcast --tier acestep` **or** `download-music --tier turbo` (same file) |
| `audio/dub/clone-translate` | `download-dub --tier asr` then `--tier clone` (or `all`) |
| TRELLIS.2 / DA3-BASE | `download-3d --tier trellis2` / `da3-base` |
| Occupancy `llm-desk` 35B | `download-llm --tier qwen36-35b-a3b` (not `download-models`) |
| Prompt Enhance 4B GGUF | already in `download-models` (`download-llm --tier enhance`) |

---

## Default pack (`download-models`)

Use this unless you know you need an opt-in pack. Four steps: Klein → Wan → LTX → prompt-enhance GGUF. `--limit` is Mbps.

**Does not pull:** podcast, dub, music, 3D, LongCat, DreamX, SeedVR2, Wan A14B / Fun InP / VACE / S2V, LTX 2.3 / IC-LoRA, Klein NVFP4 / Z-Image, or the 35B llm-desk GGUF.

```ezcmd
id: download-models
```

Stuck resume (`0 MiB/s`, `*.incomplete`): check **Delete stuck \*.incomplete** on the widget, or pass `--drop-incomplete`.

---

## Image — still UNET

`--tier fast` is Klein 4B distilled FP8 **and** the Qwen TE + flux2-vae companions. `nvfp4` / `base` also pull those companions. `zimage` is a different still runner (no Klein TE/VAE). None of these are “better Wan”.

| Pack | Default? | In `download-models`? | ~size | Occupancy | Notes |
| --- | --- | --- | --- | --- | --- |
| `fast` | yes | yes | 3–4 GB + companions (floors 3 / 2 / 0) | klein | Distilled FP8 daily still |
| `nvfp4` | no | no | ~2 GB + companions | klein | Optional Klein 4B NVFP4 |
| `base` | no | no | ~3 GB + companions | klein | Optional Klein 4B base FP8 |
| `zimage` | no | no | ~4 GB | klein | Z-Image Turbo; no TE/VAE companions |
| `all` | no | no | sum of the four | klein | `fast` + `nvfp4` + `base` + `zimage` (Apache only; not 9B/dev) |
| `9b` | no | no | ~8 GB + 8B TE + small VAE | klein | FLUX Non-Commercial Klein 9B distilled. Gated. Not YouTube-ok |
| `9b-base` | no | no | ~8 GB + companions | klein | FLUX Non-Commercial 9B base |
| `9b-nvfp4` | no | no | ~5 GB + companions | klein | FLUX Non-Commercial 9B NVFP4 |
| `small-vae` | no | no | small | klein | Apache `full_encoder_small_decoder.safetensors` (official 9B Comfy VAE) |
| `flux2-dev` | no | no | ~20 GB+ | klein | FLUX Non-Commercial 32B FP8 + Mistral TE. Gated. Not YouTube-ok |
| `te` / `vae` | companions | with `fast` | — | — | Not a public first-run flag; `fast`/`nvfp4`/`base` pull them |

```ezcmd
id: download-image
```

The manage.sh default pack calls `download-image.sh run --tier fast`. There is no `quality` image `--tier` alias. FLUX.2-dev is the opt-in `--tier flux2-dev` (FLUX Non-Commercial).

---

## Wan — different graphs

`5b` is the silent daily driver (in `download-models`). `a14b`, Fun InP, VACE, and S2V are other models. **`--tier all` does not include `vace` or `s2v`.**

| Pack | Default? | In `download-models`? | ~size | Occupancy | Notes |
| --- | --- | --- | --- | --- | --- |
| `5b` | yes | yes | ~12 GB (floor 12) | wan | TI2V-5B silent smoke + shots |
| `a14b` | no | no | ~20 GB (floor 20) | wan | I2V 14B FP8; unload 5B first |
| `fun-inp` | no | no | **~47 GB** (status floor 40) | wan; unload LTX | First-last-frame; `motion/silent/first-last-5s` |
| `vace` | no | no | ~6 GB (floor 6) | wan; unload LTX | **Not in `all`**. 17-frame join |
| `s2v` | no | no | ~20 GB (floor 20) | wan; unload LTX | **Not in `all`**. Talking-head opt-in |
| `all` | no | no | 5b+a14b+fun-inp | — | Explicitly **not** vace/s2v |

```ezcmd
id: download-wan
```

Unload LTX before Fun InP / VACE / S2V.

---

## LTX — generation, not “better”

`2.5` is the lab AV default. `2.3` is a retired fallback you should [reap](models-and-cache.md) after moving up. `balanced` / `quality` on this utility are **2.3 aliases**, not a 2.5 quality knob. `2.3` / `balanced` / `quality` auto-include `gemma` (Gemma 3 DualCLIP). **`--tier all` is `2.5` + `2.3` + `gemma` and does not include `iclora`.**

| Pack | Default? | In `download-models`? | ~size | Occupancy | Notes |
| --- | --- | --- | --- | --- | --- |
| `2.5` | yes | yes | ~30 GB (floor 30) | ltx | Distilled INT8-convrot + Gemma4 + VAEs. Gated |
| `2.3` / `balanced` | no | no | floor 20; ~28–30 GB + TE | ltx | Retired FP8 fallback; auto-includes `gemma` |
| `quality` | no | no | floor 35; ~45–48 GB + TE | ltx | 2.3 **BF16** alias, not 2.5. Auto-includes `gemma` |
| `gemma` | companion | with 2.3 | ~8–9.5 GB (floor 8) | — | Gemma 3 DualCLIP; lab 2.5 uses Gemma 4 instead |
| `iclora` | no | no | ~1 GB (floor 1) | ltx | Union Control LoRA. **Not in `all`** |
| `all` | no | no | 2.5+2.3+gemma | — | **Does not include `iclora`** |

```ezcmd
id: download-ltx
```

LTX-2.5 needs the Hugging Face license click plus `HF_TOKEN` as the **same** user. A token is not that click.

---

## Audio — podcast, dub, music

Opt-in. Missing packs are **not** doctor failures. Occupancy **audio**: stop Klein / Wan / LTX first.

### Podcast

`analog` is Kokoro only (tiny). `acestep` is the same ~10 GB AIO as music `turbo`. Chatterbox / Qwen3-TTS are optional. `qwen3tts` keeps `model.safetensors`, `config.json`, text tokenizer files, and nested `speech_tokenizer/` (~3 GB).

| Pack | Default? | ~size | What you get |
| --- | --- | --- | --- |
| `analog` | yes | tiny | Kokoro-82M ONNX + voices |
| `acestep` | no | ~10 GB | ACE-Step 1.5 turbo AIO (shared dest with music `turbo`) |
| `chatterbox` | no | small | Optional MIT GPU TTS (PerTh on) |
| `qwen3tts` | no | ~3 GB | Optional Qwen3-TTS 0.6B Base snapshot |
| `all` | no | sum | analog + acestep + chatterbox + qwen3tts |

```ezcmd
id: download-podcast
```

### Dub

`asr` is Silero VAD + faster-whisper large-v3 (`model.bin`, `config.json`, **and** `tokenizer.json`). `clone` is Chatterbox Multilingual V3 plus `MODELS_DIR/pkuseg`. Playbook: [Local dub](dub.md).

| Pack | Default? | ~size | What you get |
| --- | --- | --- | --- |
| `asr` | yes | ~3 GB | Silero VAD + faster-whisper large-v3 |
| `clone` | no | ~4 GB + small pkuseg zip | Chatterbox Multilingual V3 (MIT, PerTh on) |
| `all` | no | asr + clone | Both packs |

```ezcmd
id: download-dub
```

??? tip "Wheels when Compose is up (clone)"

    `download-dub` pip-installs `faster-whisper`, the `llama-cpp-python` CPU wheel, `setuptools<82` (PerTh / `pkg_resources`), then the Chatterbox GitHub zip at `CHATTERBOX_TTS_REF` with `--upgrade --force-reinstall --no-deps` (does not pin torch 2.6; PyPI 0.1.7 has no `t3_model=v3`). Restart also heals PerTh when `PerthImplicitWatermarker` is not callable. Queue also self-heals a missing llama.cpp wheel. A llama.cpp / GGUF miss is a **blocking** Dub status when Rewrite translation is on.

### Music — the one size ladder

`turbo` vs `xl` is the closest thing this repo has to a quality/size flag. `turbo` **reuses** the podcast acestep snapshot — do not pull the AIO twice.

| Pack | Default? | ~size | Notes |
| --- | --- | --- | --- |
| `turbo` | yes | ~10 GB AIO | Shared dest with `download-podcast --tier acestep` |
| `xl` | no | larger split files | Optional; not the default rap/podcast bed |
| `all` | no | turbo + xl | — |

```ezcmd
id: download-music
```

---

## Opt-in extras

Not part of `download-models`. Each `--tier` is still a pack id.

### 3D

Native Comfy-Org TRELLIS.2 INT8 + DINOv3. `da3-base` is Apache depth. `da3-large` is refused. SuperSplat is a host viewer, not this downloader. Occupancy: `occupancy enter trellis` first.

| Pack | Default? | ~size | Notes |
| --- | --- | --- | --- |
| `trellis2` | yes | ~12 GB | No nvdiffrast |
| `da3-base` | no | ~1 GB | Apache. DA3-LARGE refused |
| `all` | no | both | — |

```ezcmd
id: download-3d
```

### LongCat (MIT, no NCCL)

Independent Sparks still share `MODELS_DIR`. This sample stack does not ship in-tree NCCL.

| Pack | Default? | Notes |
| --- | --- | --- |
| `video` | yes | LongCat-Video |
| `avatar` | no | LongCat-Video-Avatar |
| `all` | no | video + avatar |

```ezcmd
id: download-longcat
```

### DreamX-Creator

Apache Creator only. DreamX-World is refused. Unload LTX first. Selective payload is `cross_attn_weights.safetensors` (~**8 GB**, `min_gb` 8). The **full** hub repo is ~**54 GB** — do not pull the whole tree.

```ezcmd
id: download-dreamx
```

### SeedVR2 restore (still polish or after concat)

Opt-in Apache. `--tier seedvr2-3b` (~15 GB). Optional polish on a Klein 4B PNG for **Free Commercial Use (<$10M)** quality (add detail, do not jump to 4K) or post-concat restore on a film master (conservative 1.3–1.5×). Occupancy: stop Comfy first if you restore on GPU. Not part of `download-models`.

```ezcmd
id: download-restore
```

### Prompt-enhance GGUF (already in `download-models`)

Default `--tier enhance` is the 4B Q4_K_M already pulled by `download-models`. `--tier qwen36-35b-a3b` is opt-in (~23 GB) for `occupancy enter llm-desk`. `--tier all` is enhance + 35B. Do not add the 35B pack to `download-models`.

```ezcmd
id: download-llm
```

---

## Banned names

| Name | What happens |
| --- | --- |
| Image `quality` as a `--tier` | Refused (use `flux2-dev` for the NC 32B pack) |
| Klein 9B as a lab default / pinned UNET | Not the default. Opt-in `--tier 9b` (FLUX Non-Commercial) |
| Nunchaku 9B | Refused |
| `--tier da3-large` | Refused |
| DreamX-World | Refused |
| MiniMax H3 / `download-h3` | Refused |

Read [Model licenses](licenses.md) before a 30 GB pull.

---

## Related

| Need | Page |
| --- | --- |
| First install | [Getting Started](getting-started.md) |
| Cache layout / reap | [Models and cache](models-and-cache.md) |
| Basenames on disk | [Download packs](operate/models-packs.md) |
| Mbps throttle | [Download limit](download-limit.md) |
| Verb catalog | [manage.sh reference](manage-cli.md) |
| Host leftovers | [Disk wizard](disk-wizard.md) |
| Hung resume / HTB | [Downloads troubleshooting](operate/troubleshooting-downloads.md) |
