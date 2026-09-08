---
title: Local podcast
description: US-safe audio-first episode and radio-drama lanes on one DGX Spark (Kokoro + native ACE-Step).
tags: [podcast, kokoro, ace-step, tts, disclosure, us-safe]
---

# Local podcast

**What's on this page**

- Option A (audio-first commercial episode) vs Option B (one-graph radio drama)
- App Mode: script, bed/sting tags, length, Kokoro stock voices (refs stay graph-only)
- Why TTS-Audio-Suite and OldTimeRadio are not vendored
- Kokoro default on Spark; Chatterbox / Qwen3-TTS optional
- Native ACE-Step instrumental beds
- Voice consent, platform rules, and authorship
- `download-podcast` usage, sequential Queue, and loudnorm
- Clone-and-translate of a recorded show is a different lane: [Local dub](dub.md)

**What this enables**

- Queue a local two-host episode without cloud TTS or rented music
- Keep the visual studio bootable when podcast extras are missing
- Disclose synthetic voices in the mix, not only in a description box

!!! warning "Not legal advice"

    Platform rules and copyright change. Read the current Apple, YouTube, Spotify, FTC, and USCO pages before you monetize.

---

## Two operator paths

Do **not** load Klein + Wan + LTX + ACE-Step + TTS in one session. Cover art is a separate graph.

### Option A — audio-first commercial episode

Graph: **podcast-audio-first-lab-example** (`extra.lab_profile` `us-safe-podcast`).

| Stage | What runs | Prefix |
| --- | --- | --- |
| SCRIPT | App **Script** + **Rewrite script**. In-tree `EZPodcastScript` (enhance **on**). Missing GGUF passes the widget through | `ez_podcast_script` |
| DISCLOSURE | `EZPodcastDisclosure` prepends the spoken bumper | (string) |
| VOICES | App **Speaker A / B**, **Include announcer**, **Speaking speed**. `EZKokoroTTS` Kokoro-82M ONNX/CPU built-ins. Voice-clone refs stay graph-only | `ez_podcast_voice` |
| BEDS | App **Bed tags**, **Rewrite bed**, **Bed length (seconds)**. Native Comfy ACE-Step 1.5, instrumental (lyrics hidden) | `ez_podcast_bed` |
| MIX | Duck −15 dB + overlay. FLAC master + 320 kbps MP3 | `ez_podcast_ep` / `ez_podcast_mix` |
| COVER | Queue **klein-podcast-cover-lab-example** separately (1024², `ez_podcast`) | `ez_podcast` |

First spoken line is always:

> Voices and music on this show are synthesized. The hosts are original characters, not recordings of real people.

Do not type that line yourself. The disclosure node prepends it.

### Option B — one-graph radio drama

Graph: **podcast-radio-drama-lab-example** (`us-safe-radio`). Same legal engines. Writer prompt is lab-original fiction (`radio_drama.txt`), not a news rewrite. App Mode: **Script**, **Sting tags** / **Bed tags**, sting and bed length, **Speaker A / B / Announcer**, **Include announcer**, **Speaking speed**. ACE-Step sting + bed stay instrumental (lyrics hidden). One master mix (`ez_radio_ep` / `ez_radio_mix`).

Optional Wan silent bumper / LTX 5s hook **groups default off** (node mode never). Queue **wan-bumper-loop-lab-example** or **ltx-hook-av-lab-example** in a later session. Not a one-graph film.

---

## Why those packs are not vendored

This lab does **not** git-clone, pip-require, or default to:

- **TTS-Audio-Suite** — many engines, including F5-TTS CC-BY-NC, Fish NC, Higgs commercial traps, VibeVoice research-only, and ARM wheel pain on GB10
- **ComfyUI-OldTimeRadio** — optional lanes that pull US-excluded or non-commercial video models
- Cloud ACE-Step forks, MiniMax Music, F5-TTS official weights, Coqui XTTS v2, Echo-TTS, Fish Audio S2, celebrity reference WAVs, ElevenLabs, or xAI TTS

Native ACE-Step 1.5 already ships in `COMFYUI_REF=v0.34.0` (`TextEncodeAceStepAudio1.5`, `EmptyAceStep1.5LatentAudio`). Beds stay **instrumental** (`instrumental`, `no vocals` in tags; empty lyrics). Rap vocals with original lyrics live on [Local music](music.md) and reuse this same AIO dest — do not download it twice.

---

## Engines on Spark

| Engine | License | Role | Default download? |
| --- | --- | --- | --- |
| Kokoro-82M ONNX | Apache 2.0 | Default TTS, built-in voices, CPU/aarch64-safe | No — `download-podcast --tier analog` |
| ACE-Step 1.5 turbo AIO | MIT | Instrumental beds | No — `--tier acestep` |
| Chatterbox Turbo | MIT | Optional GPU TTS; PerTh watermark stays on | No — `--tier chatterbox` |
| Qwen3-TTS 0.6B | Apache 2.0 | Optional TTS + voice design | No — `--tier qwen3tts` |
| Qwen3-4B-Instruct GGUF | Apache 2.0 | Script draft, fail-soft | Already in `download-models` |

Empty Chatterbox/Qwen3 refs fall back to Kokoro built-ins. Never drop celebrity WAVs into the graph.

`kokoro-onnx` / `onnxruntime` are **optional runtime** installs inside the container venv. They are **not** baked in `phase-nodes.sh` (a new pip would invalidate **venv-extra**, not the multi‑GB torch layer). Analog graphs still load if the wheel is missing; Queue fail-softs until you install it and `download-podcast --tier analog`.

---

## Voice consent and invented characters

Hosts are **original characters**, not recordings of real people. Operator-owned reference clips are allowed only when you have rights. Do not clone living people. Do not ship Rogan/Ramsay-style refs in this repo. Translating a recorded podcast while keeping the original speakers is [Local dub](dub.md) (`dub-localize-lab-example`), with a rights attestation on every Queue.

---

## Platform and US rules (operator checklist)

- **Apple Podcasts 1.11** — disclose material AI audio in the **content** and in **metadata**
- **YouTube** — use the synthetic/altered content toggle; July 2026 inauthentic-content rules (no template slop, no AI doctor / lawyer / finance-advisor persona)
- **Spotify** — allowed if you own the rights, disclose, and do not use unconsented clones
- **FTC** — spoken sponsor reads; synthetic persona endorsements need both a paid-connection disclosure and “this voice is AI”
- **USCO Part 2 / Thaler** — prompts are not authorship. A human-edited script plus selection, arrangement, and mix **can** be. Raw generations are not registrable

---

## Download

Podcast weights are **opt-in**. `./scripts/manage.sh download-models` does **not** pull them. `doctor` prints analog JSON and still exits 0 when the pack is absent.

```bash
./scripts/manage.sh download-podcast --tier analog      # Kokoro ONNX + voices
./scripts/manage.sh download-podcast --tier acestep     # ace_step_1.5_turbo_aio.safetensors
# same AIO dest as: ./scripts/manage.sh download-music --tier turbo
./scripts/manage.sh download-podcast --tier all         # analog + ACE + optional TTS
# same --limit auto|N|off wrap as download-models (always clears on exit)
```

Layout after analog + acestep:

```text
${MODELS_DIR}/comfy/
  onnx/kokoro-v1.0.onnx
  tts/voices-v1.0.bin
  checkpoints/ace_step_1.5_turbo_aio.safetensors
```

Relative symlinks only (host `/mnt/models` vs container `/models`).

---

## What runs on Queue

```mermaid
sequenceDiagram
  participant U as Studio user
  participant S as EZPodcastScript
  participant D as Disclosure
  participant K as Kokoro TTS
  participant A as ACE-Step beds
  participant M as Mix

  U->>S: Queue (Enhance on)
  S->>D: script string
  D->>K: bumper + lines
  D->>A: instrumental tags
  K->>M: voice stems
  A->>M: beds
  M->>U: FLAC + MP3 under COMFY_OUTPUT_DIR
```

Cover art is a **later** Klein session. Occupancy: do not load LTX + ACE-Step together.

## Sequential Queue

1. `download-podcast --tier analog` (and `--tier acestep` for beds)
2. Optional: `pip install kokoro-onnx onnxruntime` in the Comfy venv (runtime; see troubleshooting)
3. `./scripts/manage.sh start` — type **yes**
4. Load **podcast-audio-first-lab-example**. Enhance on. Queue. Files under `${COMFY_OUTPUT_DIR}` as `ez_podcast_ep_*.flac` / `ez_podcast_mix_*.mp3`
5. Load **klein-podcast-cover-lab-example** in a **later** session. Queue `ez_podcast_*.png`
6. Loudness (ffmpeg; Comfy cannot LUFS):

```bash
./scripts/utilities/podcast-loudnorm.sh run --in "${COMFY_OUTPUT_DIR}/ez_podcast_ep_00001_.flac"
# --target youtube  → −14 LUFS; default podcast → −16 LUFS
```

Start still requires typing `yes`. Compose `restart: "no"` is unchanged.
