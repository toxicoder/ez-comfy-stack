---
title: manage.sh reference
description: Operator command catalog for ez-comfy-stack — what each manage.sh verb does and when not to run it.
tags: [manage, cli, operator, reference]
---

# manage.sh reference

**What's on this page**

- How to invoke the CLI
- Command catalog
- `--tier` is a pack id (not a quality ladder)
- What not to run (banned H3 aliases, occupancy)

**What this enables**

- Looking up a verb without scrolling the Getting Started tutorial
- Keeping first-run docs a tutorial, not a man page

**Who this is for:** operators who already cloned the repo. First install: [Getting Started](getting-started.md).

Run from the **repo root**. `manage.sh` loads `.env`. Session exports (`SPARK_HOST`, `MODELS_DIR`, …) are for *your* shell (browser URL, `ssh -L`, `ls`). The **Your Spark** panel on these docs fills the same keys when you copy a command.

```ezcmd
id: doctor
```

`--tier` on `download-podcast` / `download-music` / `download-3d` / … selects **which pack**, not a studio-wide quality level. `--limit` is Mbps. Full map: [Download tiers](download-tiers.md). `download-models` has no `--tier`.

---

## Catalog

| Command | Purpose | Do not |
| --- | --- | --- |
| `setup [--install-docker] [--yes]` | `.env`, dirs, optional Docker CE, then doctor | Skip doctor failures |
| `doctor` | Preflight (docker, GPU, RAM/disk, dirs, license one-liner, spark-timing) | Treat missing weights as a hard fail (they are a warning) |
| `status [--json]` | Compose project; prints `MODELS_DIR`, `COMFY_OUTPUT_DIR`, port | — |
| `start` | Type `yes`; headroom; compose up | Weaken confirm or `restart: "no"` |
| `stop` | Stop containers; keep models, outputs, volume | Reboot with the stack up |
| `restart` | `stop` + `start` (full confirm again) | — |
| `logs` | Follow compose logs (`logs --tail 100` works) | — |
| `download-models [--limit auto\|N\|off] [--drop-incomplete]` | Default pack, throttled wrap. **No `--tier`.** | Expect podcast/music weights (they are opt-in) |
| `download-podcast [--tier analog\|…] [--limit auto\|N\|off]` | Opt-in pack id (`analog` = Kokoro). [Tiers](download-tiers.md) | Co-resident with LTX/Wan/Klein |
| `download-dub [--tier asr\|clone\|all] [--limit auto\|N\|off]` | Opt-in ASR + Chatterbox Multilingual V3. [Local dub](dub.md) | Co-resident with LTX/Wan/Klein |
| `download-music [--tier turbo\|xl\|all] [--limit auto\|N\|off]` | Opt-in size ladder; `turbo` shares dest with `download-podcast --tier acestep` | Co-resident with the visual session |
| `download-limit …` | Proxy to `scripts/utilities/download-limit.sh` | Leave a wrap limit stuck; wrap **always clears on exit** |
| `clear-hf-locks` | Stale Hugging Face `.lock` files under `MODELS_DIR` | Force-clear while `hf` is still writing |
| `reset-hf-partials [--yes] [--force]` | Delete `*.incomplete` (finished weights kept) | — |
| `cleanup` | Type `DELETE`; remove `ez-comfy-state` only | Think this deletes weights or `COMFY_OUTPUT_DIR` |
| `print-shot` / `film-resume` / `film-export-otio` / `film-proxies` / `take-promote` | 90s jobstore ([90s shorts](shorts.md)) | `film-proxies` while compose is up |
| `download-restore` | Opt-in SeedVR2-3B | Treat as part of `download-models` |
| `download-3d` | Opt-in TRELLIS.2 + DA3-BASE (no nvdiffrast; DA3-LARGE refused) | `--tier da3-large` |
| `blender` | Host Blender sidecar; dies if compose is up | Run next to Comfy |
| `export-guides` | Dump a 1280×704 / 120f guide pack; dies if compose is up | 1280×720; dump while Comfy is up |
| `house-views` | Dump 1024×1280 Instagram 4:5 clay stills + GLB; dies if compose is up | Reuse `export-guides`; dump while Comfy is up; Godot |
| `shot-sheet` | Write `films/<slug>/shots.yaml` with shot-card defaults | Overwrite lab YAML without `--lab-example` |
| `overlay-qc` | 50% clay/look overlay (host ffmpeg; compose may stay up) | Skip size QC; auto-accept the score |
| `film-animatic` | Cheap 90s animatic from clay.mp4 or stills | Treat as a 90s denoise |
| `stem-mix` | Picture-lock stems; duck −15 dB; YouTube loudnorm | Mix ACE-Step next to LTX |
| `audio-still-video --audio FILE --image FILE` | Mux a still + audio master to YouTube MP4 (host ffmpeg; compose may stay up) | Treat as a denoise; use NVENC; edit audio lab graphs |
| `asset-ls` | Read-only [Asset Bible](asset-bible.md) catalog (`COMFY_OUTPUT_DIR/assets`) | Store assets in `MODELS_DIR` or `guides/` |
| `film-accept` | Fail-closed 90s gate (duration / 1280×704 / LTX audio; stems LUFS when `audio_policy: stems`) | `--skip-accept` as a habit |
| `download-longcat` / `download-dreamx` | Opt-in LongCat MIT / DreamX-Creator Apache | DreamX-World; NCCL |
| `spark-timing` | Kitchen wall-clock table (`record --klein N --wan N --ltx N`) | Record on `pytorch-fallback` |
| `models-status` / `reap-models` | Disk bible / MODELS_DIR cache cleanup (never `cleanup` weights) | `cleanup` when you meant reap |
| `disk-wizard` | Host-wide leftover survey (default `--plan`). [Disk wizard](disk-wizard.md) | `docker system prune -a --volumes`; confuse with `cleanup` |

`download-h3`, `queue-h3`, `farm-h3`, and `stitch-h3` are **banned** aliases (MiniMax H3). 3D DCC notes: [Studio sidecars](studio-sidecars.md).

Safety is unchanged: `restart: "no"`, heavy confirm on `start`, headroom preflight, download-limit clear-on-exit.

---

## Related

| Need | Page |
| --- | --- |
| First install | [Getting Started](getting-started.md) |
| Why start asks for `yes` | [Hardware, memory, and safety](learn/hardware.md) |
| Throttle details | [Download limit](download-limit.md) |
| Symptom → fix | [Troubleshooting](troubleshooting.md) |
