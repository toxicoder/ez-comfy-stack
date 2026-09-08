---
title: Download tiers
description: What --tier actually selects on each download command — pack ids, not a global quality ladder.
tags: [download, tier, models, klein, wan, ltx, podcast, dub, music]
---

# Download tiers

**What's on this page**

- `--tier` is a **pack id**, not a quality ladder for the whole studio
- `--limit` is **bandwidth** (Mbps), not a model
- Default pack vs opt-in packs
- One live command builder per downloader

**What this enables**

- Picking the flag that matches the graph you will Queue
- Avoiding a 40 GB Fun InP pull when you wanted Wan 5B
- Copying a command with **your** `--tier` and `--limit` already filled in

The **Your Spark** panel at the top of every docs page stores `SPARK_HOST` and friends in this browser. Copy buttons use those values. `--limit` defaults follow `DOWNLOAD_LIMIT` unless you override it on the widget.

---

## Read this first

| Flag | Means | Does not mean |
| --- | --- | --- |
| **`--tier NAME`** | Which **pack** that one utility pulls | A studio-wide quality ladder |
| **`--limit auto\|N\|off`** | Hugging Face **bandwidth** cap | Smaller / faster weights |
| **`download-models`** | Klein 4B + Wan 5B + LTX-2.5 + GGUF | Podcast, music, 3D, LongCat, DreamX, SeedVR2 |

`download-models` has **no** `--tier`. Image `fast`, Wan `5b`, and LTX `2.5` are three different pack ids that happen to be the lab defaults.

`--tier all` is **per utility**. Wan `all` is `5b + a14b + fun-inp` and **does not include** `vace` or `s2v`.

Banned names (`quality` on image, Klein 9B, FLUX.2-dev, DA3-LARGE, DreamX-World, MiniMax H3) stay refused — see [Model licenses](licenses.md).

Occupancy: unload LTX before Fun InP / TRELLIS / VACE / S2V / ACE-Step. One heavy GPU job.

---

## Map

| Command | `--tier` values | Default | What you get | ~size | In `download-models`? |
| --- | --- | --- | --- | --- | --- |
| `download-models` | *(none)* | n/a | Klein 4B FP8 + TE + flux2-vae + Wan 2.2 5B + LTX-2.5 distilled + Qwen3-4B GGUF | tens of GB | itself |
| `download-image` | `fast` `nvfp4` `base` `zimage` `all` | `fast` | Still UNET **variant**. `fast` also pulls companions `te` + `vae` | 3–4 GB + companions | `fast` only |
| `download-wan` | `5b` `a14b` `fun-inp` `vace` `s2v` | `5b` | **Different Wan graphs**. `all` = 5b+a14b+fun-inp (**not** vace/s2v) | 12 / 20 / 40 / 6 / 20 GB | `5b` only |
| `download-ltx` | `2.5` `2.3` `iclora` `gemma` | `2.5` | **Generation** of LTX, not “better”. `2.3` is retired | ~30 GB distilled | `2.5` only |
| `download-podcast` | `analog` `acestep` `chatterbox` `qwen3tts` `all` | `analog` | **Different audio packs**. Missing pack is not a doctor failure | analog tiny; acestep ~10 GB shared | no |
| `download-dub` | `asr` `clone` `all` | `asr` | Silero VAD + faster-whisper; Chatterbox Multilingual V3. Missing pack is not a doctor failure | asr ~3 GB; clone ~2 GB | no |
| `download-music` | `turbo` `xl` `all` | `turbo` | Size ladder. `turbo` **shares dest** with `download-podcast --tier acestep` | ~10 GB AIO | no |
| `download-3d` | `trellis2` `da3-base` `all` | `trellis2` | Opt-in 3D. `da3-large` refused | ~8 / ~1 GB | no |
| `download-longcat` | `video` `avatar` `all` | `video` | Opt-in MIT LongCat; no NCCL | large | no |
| `download-dreamx` | `creator` | `creator` | Apache Creator only; World refused | ~8 GB | no |
| `download-restore` | `seedvr2-3b` | `seedvr2-3b` | Post-concat restore only | ~15 GB | no |
| `download-llm` | *(none)* | n/a | Prompt-enhance GGUF | ~3 GB | yes |

Cache layout and relative symlinks: [Models and cache](models-and-cache.md). Throttle details: [Download limit](download-limit.md).

---

## Default pack (`download-models`)

Use this unless you know you need an opt-in pack. `--limit` is Mbps.

```ezcmd
id: download-models
```

Stuck resume (`0 MiB/s`, `*.incomplete`): check **Delete stuck \*.incomplete** on the widget, or pass `--drop-incomplete`.

---

## Image — still UNET variant

`--tier fast` is Klein 4B distilled FP8 **and** the Qwen TE + flux2-vae companions. `nvfp4` / `base` / `zimage` are other stills, not “better video”.

```ezcmd
id: download-image
```

The manage.sh default pack calls `download-image.sh run --tier fast`. There is no `quality` image tier (FLUX.2-dev is banned).

---

## Wan — different graphs, not a ladder

`5b` is the silent daily driver (in `download-models`). `a14b`, Fun InP, VACE, and S2V are other models. **`--tier all` does not include `vace` or `s2v`.**

```ezcmd
id: download-wan
```

Unload LTX before Fun InP / VACE / S2V.

---

## LTX — generation, not “better”

`2.5` is the lab AV default. `2.3` is a retired fallback you should [reap](models-and-cache.md) after moving up. `balanced` / `quality` on the LTX utility are **2.3 aliases**, not a 2.5 quality knob.

```ezcmd
id: download-ltx
```

---

## Podcast — different audio packs

`analog` is Kokoro only (tiny). `acestep` is the same ~10 GB AIO as music `turbo`. Chatterbox / Qwen3-TTS are optional. Doctor does **not** fail when these are missing.

```ezcmd
id: download-podcast
```

---

## Dub — ASR + multilingual clone

`asr` is Silero VAD + faster-whisper large-v3. `clone` is Chatterbox Multilingual V3 (MIT, PerTh on). Doctor does **not** fail when these are missing. Occupancy **audio**. Playbook: [Local dub](dub.md).

```ezcmd
id: download-dub
```

---

## Music — the one size ladder

`turbo` vs `xl` is the closest thing this repo has to a quality/size flag. `turbo` **reuses** the podcast acestep snapshot — do not pull the AIO twice. Stop Klein/Wan/LTX first.

```ezcmd
id: download-music
```

---

## Opt-in extras

Not part of `download-models`. Each `--tier` is still a pack id.

### 3D

```ezcmd
id: download-3d
```

### LongCat (MIT, no NCCL)

```ezcmd
id: download-longcat
```

### DreamX-Creator

```ezcmd
id: download-dreamx
```

### SeedVR2 restore (after concat)

```ezcmd
id: download-restore
```

### Prompt-enhance GGUF (already in `download-models`)

```ezcmd
id: download-llm
```

---

## Related

| Need | Page |
| --- | --- |
| First install | [Getting Started](getting-started.md) |
| Cache layout / reap | [Models and cache](models-and-cache.md) |
| Mbps throttle | [Download limit](download-limit.md) |
| Verb catalog | [manage.sh reference](manage-cli.md) |
| Host leftovers | [Disk wizard](disk-wizard.md) |
