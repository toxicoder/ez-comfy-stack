---
title: "audio/albums/drive-through/hour-1"
description: "Album graphs under audio/albums/drive-through/hour-1 (tracks, cover, album pack)."
tags: [workflows, generated, comfyui, audio, album]
---

# audio/albums/drive-through/hour-1

**What's on this page**

- **Every track, cover, and album-pack graph** in this folder
- **Shared ACE-Step topology** (one printer, unique widgets per take)
- **Node parameter reference** for the types on these graphs

**What this enables**

- **Queuing one numbered take** or `album-render`
- **Reading tags, lyrics, seed, BPM** without opening raw JSON

**Who this is for:** studio users after `download-music`. Occupancy **audio** (cover stills are **klein** — separate session).

> Generated from `workflows/_lab/audio/albums/drive-through/hour-1/`. Do not hand-edit this file.

## Purpose

Numbered takes under `audio/albums/drive-through/hour-1/`. Queue one track, or `./scripts/manage.sh album-render --album drive-through/hour-1`.

```text
## 01-night-window

US-safe EDM **180 s** take: **night window**. Fictional act **Drive-through** (hardcore, pure of heart). Native ACE-Step 1.5 turbo AIO. Live bass-set take. Instrumental score is empty-body ACE markers (`[drop - cues]`, `[inst - cues]`, `[outro]`) so ACE does not sing production notes. Drop-first warped hybrid-trap, trap drums, no quiet dips. Vocals are a rare DJ treat on other graphs, not here. Queue this graph **on its own** — draft-first is the generic rap lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and `[drop]` / `[inst]` / `[outro]` stay as written. Turn Enhance on only if you want the 4B rewriter.
3. Tags vs score: tags are genre/instrument hints; lyrics are the arrangement. Keep App **Vocal / instrumental** on instrumental so ACE does not sing. Encoder language is `unknown`. Free-text lines under a marker are lyrics — keep cues inside the brackets.
4. Original arrangements only. No “in the style of <living artist>”. No living-DJ names. No famous-hook paraphrases.
5. ACE-Step timbre is **invented**, not a cloned act.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration 180 s, bpm 145, language unknown, timesignature 4, generate_audio_codes true. Seed 193.
7. Saves: `01 - Night Window` FLAC master + 320 kbps MP3 under `${COMFY_OUTPUT_DIR}`.
8. Cover separately: Queue **stills/thumbnail.json** or **stills/podcast-cover.json**. Do not embed Klein here.
9. Human selection and edit before any release. Prompts are not authorship (USCO Part 2 / Thaler).
10. Do not co-resident with LTX / Wan / Klein on this Spark.

Occupancy: audio — stop Klein / Wan / LTX session. One GB10 job.
```

## Shared graph

```mermaid
flowchart LR
  N1["ACE-Step 1.5 turbo AIO"]
  N2["AuraFlow sampling"]
  N3["Song Duration"]
  N4["Latent length (seconds)"]
  N5["ez_edm_prompt"]
  N6["ACE tags + lyrics"]
  N7["Negative (zero)"]
  N8["ACE sampler"]
  N9["ACE decode"]
  N10["FLAC master"]
  N11["MP3 320k"]
  N12["Operator note"]
  N13["Cover image"]
  N14["Album metadata"]
  N15["Quality"]
  N1 --> N2
  N1 --> N6
  N1 --> N9
  N2 --> N8
  N3 --> N4
  N3 --> N6
  N4 --> N8
  N5 --> N6
  N6 --> N8
  N6 --> N7
  N7 --> N8
  N8 --> N9
  N9 --> N10
  N9 --> N11
  N9 --> N14
```

## Graphs in this album

| Graph | Nodes | Occupancy |
| --- | --- | --- |
| `audio/albums/drive-through/hour-1/01-night-window` | 15 | audio |
| `audio/albums/drive-through/hour-1/02-open-lane` | 15 | audio |
| `audio/albums/drive-through/hour-1/03-exit-seven` | 15 | audio |
| `audio/albums/drive-through/hour-1/04-skyline-pass` | 15 | audio |
| `audio/albums/drive-through/hour-1/05-on-ramp` | 15 | audio |
| `audio/albums/drive-through/hour-1/06-tunnel-bass` | 15 | audio |
| `audio/albums/drive-through/hour-1/07-wide-open` | 15 | audio |
| `audio/albums/drive-through/hour-1/08-overpass` | 15 | audio |
| `audio/albums/drive-through/hour-1/09-second-wave` | 15 | audio |
| `audio/albums/drive-through/hour-1/10-freight-pulse` | 15 | audio |
| `audio/albums/drive-through/hour-1/11-keep-going` | 15 | audio |
| `audio/albums/drive-through/hour-1/12-horizon-kick` | 15 | audio |
| `audio/albums/drive-through/hour-1/13-clean-wreckage` | 15 | audio |
| `audio/albums/drive-through/hour-1/14-heart-lane` | 15 | audio |
| `audio/albums/drive-through/hour-1/15-dawn-receipt` | 15 | audio |
| `audio/albums/drive-through/hour-1/album` | 3 | none |
| `audio/albums/drive-through/hour-1/cover` | 14 | klein |

## `01-night-window`

Catalog id `audio/albums/drive-through/hour-1/01-night-window`.

US-safe EDM 180s: Drive-through night-window hybrid trap warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, wa…` |
| 2 | `[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, g…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/01-night-window` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, warped bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, grid 193 0]

[inst - rapid hi-hats roll, 808 slide, grid 193 1]

[drop - harder growl drop, chest-sub warp, stacked reese, grid 193 2]

[inst - snare roll, chest-sub 808 punch, grid 193 3]

[drop - full send drop, warped 808 wall, low rumble wreck, grid 193 4]

[outro - kick holds, rapid hi-hats roll, warp bass ride, grid 193 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, wa…` |
| 1 | `[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, g…` |
| 2 | `193` |
| 3 | `fixed` |
| 4 | `145` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, warped bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, grid 193 0]

[inst - rapid hi-hats roll, 808 slide, grid 193 1]

[drop - harder growl drop, chest-sub warp, stacked reese, grid 193 2]

[inst - snare roll, chest-sub 808 punch, grid 193 3]

[drop - full send drop, warped 808 wall, low rumble wreck, grid 193 4]

[outro - kick holds, rapid hi-hats roll, warp bass ride, grid 193 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `193` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `01 - Night Window` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `01 - Night Window` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Night Window` |
| 3 | `1` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `01 - Night Window` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `02-open-lane`

Catalog id `audio/albums/drive-through/hour-1/02-open-lane`.

US-safe EDM 180s: Drive-through open-lane riddim warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 8…` |
| 2 | `[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0] [drop - har…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/02-open-lane` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 152 bpm, instrumental, no vocals
```

```text
[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0]

[drop - harder stacked drop, growl 808 punch, warped wall, grid 191 1]

[inst - rapid hi-hats denser, wobble sustain, grid 191 2]

[drop - heavy warped drop, low sub wobble, chest-sub 808 wreck, grid 191 3]

[outro - kick holds, hats denser, wobble ride, grid 191 4]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 8…` |
| 1 | `[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0] [drop - har…` |
| 2 | `191` |
| 3 | `fixed` |
| 4 | `152` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 152 bpm, instrumental, no vocals
```

```text
[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0]

[drop - harder stacked drop, growl 808 punch, warped wall, grid 191 1]

[inst - rapid hi-hats denser, wobble sustain, grid 191 2]

[drop - heavy warped drop, low sub wobble, chest-sub 808 wreck, grid 191 3]

[outro - kick holds, hats denser, wobble ride, grid 191 4]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `191` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `02 - Open Lane` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `02 - Open Lane` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Open Lane` |
| 3 | `2` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `02 - Open Lane` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `03-exit-seven`

Catalog id `audio/albums/drive-through/hour-1/03-exit-seven`.

US-safe EDM 180s: Drive-through exit-seven tearout warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| 2 | `[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0] [inst - me…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/03-exit-seven` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 142 bpm, instrumental, no vocals
```

```text
[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0]

[inst - metal hats roll, 808 grind hold, grid 233 1]

[drop - harder warped drop, sub crush 808, chest growl, grid 233 2]

[inst - snare roll, tearout 808 sustain, grid 233 3]

[drop - full send drop, stacked growl wreck, low rumble, grid 233 4]

[inst - rapid hi-hats denser, mid growl hold, grid 233 5]

[drop - harder growl drop, chest-sub 808 warp, tearout wreck, grid 233 6]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 233 7]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| 1 | `[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0] [inst - me…` |
| 2 | `233` |
| 3 | `fixed` |
| 4 | `142` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 142 bpm, instrumental, no vocals
```

```text
[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0]

[inst - metal hats roll, 808 grind hold, grid 233 1]

[drop - harder warped drop, sub crush 808, chest growl, grid 233 2]

[inst - snare roll, tearout 808 sustain, grid 233 3]

[drop - full send drop, stacked growl wreck, low rumble, grid 233 4]

[inst - rapid hi-hats denser, mid growl hold, grid 233 5]

[drop - harder growl drop, chest-sub 808 warp, tearout wreck, grid 233 6]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 233 7]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `233` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `03 - Exit Seven` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `03 - Exit Seven` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Exit Seven` |
| 3 | `3` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `03 - Exit Seven` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `04-skyline-pass`

Catalog id `audio/albums/drive-through/hour-1/04-skyline-pass`.

US-safe EDM 180s: Drive-through skyline-pass brostep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped b…` |
| 2 | `[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0] [inst - ra…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/04-skyline-pass` |

```text
brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0]

[inst - rapid hi-hats roll, growl sustain, grid 199 1]

[drop - harder reese drop, stacked 808 wall, formant bend, grid 199 2]

[drop - full send drop, chest-sub growl, brostep wreck, grid 199 3]

[inst - snare roll, reese hold, grid 199 4]

[drop - harder warped drop, low rumble wreck, 808 punch, grid 199 5]

[outro - kick holds, hats denser, reese ride, grid 199 6]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped b…` |
| 1 | `[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0] [inst - ra…` |
| 2 | `199` |
| 3 | `fixed` |
| 4 | `145` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0]

[inst - rapid hi-hats roll, growl sustain, grid 199 1]

[drop - harder reese drop, stacked 808 wall, formant bend, grid 199 2]

[drop - full send drop, chest-sub growl, brostep wreck, grid 199 3]

[inst - snare roll, reese hold, grid 199 4]

[drop - harder warped drop, low rumble wreck, 808 punch, grid 199 5]

[outro - kick holds, hats denser, reese ride, grid 199 6]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `199` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `04 - Skyline Pass` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `04 - Skyline Pass` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Skyline Pass` |
| 3 | `4` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `04 - Skyline Pass` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `05-on-ramp`

Catalog id `audio/albums/drive-through/hour-1/05-on-ramp`.

US-safe EDM 180s: Drive-through on-ramp wave bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, r…` |
| 2 | `[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0] [inst - rapid…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/05-on-ramp` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 155 bpm, instrumental, no vocals
```

```text
[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0]

[inst - rapid hi-hats roll, wave 808 sustain, grid 197 1]

[drop - harder formant drop, double 808 split, chest warp, grid 197 2]

[inst - snare roll, 808 slide, grid 197 3]

[drop - full send drop, stacked wave wreck, warped sub, grid 197 4]

[outro - kick holds, rapid hi-hats roll, wave ride, grid 197 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, r…` |
| 1 | `[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0] [inst - rapid…` |
| 2 | `197` |
| 3 | `fixed` |
| 4 | `155` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 155 bpm, instrumental, no vocals
```

```text
[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0]

[inst - rapid hi-hats roll, wave 808 sustain, grid 197 1]

[drop - harder formant drop, double 808 split, chest warp, grid 197 2]

[inst - snare roll, 808 slide, grid 197 3]

[drop - full send drop, stacked wave wreck, warped sub, grid 197 4]

[outro - kick holds, rapid hi-hats roll, wave ride, grid 197 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `197` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `05 - On-Ramp` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `05 - On-Ramp` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `On-Ramp` |
| 3 | `5` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `05 - On-Ramp` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `06-tunnel-bass`

Catalog id `audio/albums/drive-through/hour-1/06-tunnel-bass`.

US-safe EDM 180s: Drive-through tunnel-bass dirty warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda…` |
| 2 | `[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0] [drop…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/06-tunnel-bass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0]

[drop - harder growl drop, dual-action pedal bass, chest punch, grid 257 1]

[inst - rapid hi-hats roll, pedal 808 hold, grid 257 2]

[drop - full send drop, chest-sub wreck, warped rumble, grid 257 3]

[outro - kick holds, hats denser, pedal ride, grid 257 4]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda…` |
| 1 | `[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0] [drop…` |
| 2 | `257` |
| 3 | `fixed` |
| 4 | `150` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0]

[drop - harder growl drop, dual-action pedal bass, chest punch, grid 257 1]

[inst - rapid hi-hats roll, pedal 808 hold, grid 257 2]

[drop - full send drop, chest-sub wreck, warped rumble, grid 257 3]

[outro - kick holds, hats denser, pedal ride, grid 257 4]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `257` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `06 - Tunnel Bass` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `06 - Tunnel Bass` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Tunnel Bass` |
| 3 | `6` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `06 - Tunnel Bass` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `07-wide-open`

Catalog id `audio/albums/drive-through/hour-1/07-wide-open`.

US-safe EDM 180s: Drive-through wide-open color bass DJ shout, ACE-Step 1.5 turbo AIO, sparse DJ vocal chop, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, wa…` |
| 2 | `[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0] [chorus]…` |
| 3 | `false` |
| 4 | `vocal` |
| 5 | `audio/albums/drive-through/hour-1/07-wide-open` |

```text
color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, sparse vocal chop, DJ shout, no rap, rave, 808, original composition, riser, drop first, 150 bpm
```

```text
[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0]

[chorus]
hey

[drop - harder growl drop, chest-sub warp, color bass wreck, grid 239 2]

[inst - rapid hi-hats roll, 808 slide, grid 239 3]

[drop - full send drop, low 808 wall, warped color, grid 239 4]

[outro - kick holds, rapid hi-hats roll, color ride, grid 239 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, wa…` |
| 1 | `[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0] [chorus]…` |
| 2 | `239` |
| 3 | `fixed` |
| 4 | `150` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `en` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, sparse vocal chop, DJ shout, no rap, rave, 808, original composition, riser, drop first, 150 bpm
```

```text
[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0]

[chorus]
hey

[drop - harder growl drop, chest-sub warp, color bass wreck, grid 239 2]

[inst - rapid hi-hats roll, 808 slide, grid 239 3]

[drop - full send drop, low 808 wall, warped color, grid 239 4]

[outro - kick holds, rapid hi-hats roll, color ride, grid 239 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `239` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `07 - Wide Open` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `07 - Wide Open` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Wide Open` |
| 3 | `7` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `07 - Wide Open` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `08-overpass`

Catalog id `audio/albums/drive-through/hour-1/08-overpass`.

US-safe EDM 180s: Drive-through overpass dirty dubstep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, …` |
| 2 | `[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0] [inst - …` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/08-overpass` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0]

[inst - metal hats roll, wobble sustain, grid 227 1]

[drop - harder growl drop, stacked 808 warp, chest rumble, grid 227 2]

[inst - rapid hi-hats denser, 808 punch hold, grid 227 3]

[drop - full send drop, warped wobble wreck, low sub, grid 227 4]

[inst - snare roll, growl hold, grid 227 5]

[drop - harder warped drop, chest-sub 808 wreck, dubstep grind, grid 227 6]

[outro - kick holds, hats denser, wobble ride, grid 227 7]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, …` |
| 1 | `[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0] [inst - …` |
| 2 | `227` |
| 3 | `fixed` |
| 4 | `150` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0]

[inst - metal hats roll, wobble sustain, grid 227 1]

[drop - harder growl drop, stacked 808 warp, chest rumble, grid 227 2]

[inst - rapid hi-hats denser, 808 punch hold, grid 227 3]

[drop - full send drop, warped wobble wreck, low sub, grid 227 4]

[inst - snare roll, growl hold, grid 227 5]

[drop - harder warped drop, chest-sub 808 wreck, dubstep grind, grid 227 6]

[outro - kick holds, hats denser, wobble ride, grid 227 7]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `227` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `08 - Overpass` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `08 - Overpass` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Overpass` |
| 3 | `8` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `08 - Overpass` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `09-second-wave`

Catalog id `audio/albums/drive-through/hour-1/09-second-wave`.

US-safe EDM 180s: Drive-through second-wave hybrid trap chop, ACE-Step 1.5 turbo AIO, sparse DJ vocal chop, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warp…` |
| 2 | `[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 …` |
| 3 | `false` |
| 4 | `vocal` |
| 5 | `audio/albums/drive-through/hour-1/09-second-wave` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warped bass, sparse vocal chop, DJ shout, no rap, rave, original composition, riser, drop first, 150 bpm
```

```text
[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 0]

[inst - rapid hi-hats roll, 808 slide, grid 241 1]

[chorus]
go

[drop - harder double drop, full send bass warp, formant wreck, grid 241 3]

[drop - full send drop, chest-sub 808 wreck, warped trap, grid 241 4]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 241 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warp…` |
| 1 | `[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 …` |
| 2 | `241` |
| 3 | `fixed` |
| 4 | `150` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `en` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warped bass, sparse vocal chop, DJ shout, no rap, rave, original composition, riser, drop first, 150 bpm
```

```text
[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 0]

[inst - rapid hi-hats roll, 808 slide, grid 241 1]

[chorus]
go

[drop - harder double drop, full send bass warp, formant wreck, grid 241 3]

[drop - full send drop, chest-sub 808 wreck, warped trap, grid 241 4]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 241 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `241` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `09 - Second Wave` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `09 - Second Wave` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Second Wave` |
| 3 | `9` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `09 - Second Wave` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `10-freight-pulse`

Catalog id `audio/albums/drive-through/hour-1/10-freight-pulse`.

US-safe EDM 180s: Drive-through freight-pulse drumstep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808…` |
| 2 | `[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0] [inst - ame…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/10-freight-pulse` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 176 bpm, instrumental, no vocals
```

```text
[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0]

[inst - amen break, rapid hi-hats 808 freight, grid 211 1]

[drop - harder growl drop, double amen wreck, formant grind, grid 211 2]

[inst - hats denser, reese hold, grid 211 3]

[drop - full send drop, stacked amen wreck, warped chest-sub, grid 211 4]

[inst - snare roll, 808 punch, grid 211 5]

[drop - harder warped drop, chest-sub 808 wreck, reese wall, grid 211 6]

[outro - kick holds, amen break, reese ride, grid 211 7]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808…` |
| 1 | `[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0] [inst - ame…` |
| 2 | `211` |
| 3 | `fixed` |
| 4 | `176` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 176 bpm, instrumental, no vocals
```

```text
[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0]

[inst - amen break, rapid hi-hats 808 freight, grid 211 1]

[drop - harder growl drop, double amen wreck, formant grind, grid 211 2]

[inst - hats denser, reese hold, grid 211 3]

[drop - full send drop, stacked amen wreck, warped chest-sub, grid 211 4]

[inst - snare roll, 808 punch, grid 211 5]

[drop - harder warped drop, chest-sub 808 wreck, reese wall, grid 211 6]

[outro - kick holds, amen break, reese ride, grid 211 7]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `211` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `10 - Freight Pulse` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `10 - Freight Pulse` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Freight Pulse` |
| 3 | `10` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `10 - Freight Pulse` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `11-keep-going`

Catalog id `audio/albums/drive-through/hour-1/11-keep-going`.

US-safe EDM 180s: Drive-through keep-going neuro warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave…` |
| 2 | `[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0] [inst - rap…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/11-keep-going` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 170 bpm, instrumental, no vocals
```

```text
[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0]

[inst - rapid hi-hats denser, reese sustain, grid 251 1]

[drop - harder formant drop, full send 170 wreck, chest-sub, grid 251 2]

[inst - snare roll, 808 slide, grid 251 3]

[drop - full send drop, chest-sub wreck, neuro warp, grid 251 4]

[outro - kick holds, hats denser, reese ride, grid 251 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave…` |
| 1 | `[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0] [inst - rap…` |
| 2 | `251` |
| 3 | `fixed` |
| 4 | `170` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 170 bpm, instrumental, no vocals
```

```text
[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0]

[inst - rapid hi-hats denser, reese sustain, grid 251 1]

[drop - harder formant drop, full send 170 wreck, chest-sub, grid 251 2]

[inst - snare roll, 808 slide, grid 251 3]

[drop - full send drop, chest-sub wreck, neuro warp, grid 251 4]

[outro - kick holds, hats denser, reese ride, grid 251 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `251` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `11 - Keep Going` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `11 - Keep Going` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Keep Going` |
| 3 | `11` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `11 - Keep Going` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `12-horizon-kick`

Catalog id `audio/albums/drive-through/hour-1/12-horizon-kick`.

US-safe EDM 180s: Drive-through horizon-kick tearout warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| 2 | `[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0] [inst -…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/12-horizon-kick` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, rave, no singing, no choir, no vocal chops, original composition, kick split, drop first, 165 bpm, instrumental, no vocals
```

```text
[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0]

[inst - rapid hi-hats roll, growl sustain, grid 263 1]

[drop - harder stacked drop, formant reverse wreck, chest-sub 808, grid 263 2]

[inst - 808 triplets, hats denser, grid 263 3]

[drop - full send drop, chest-sub wreck, tearout warp, grid 263 4]

[drop - harder growl drop, low rumble wreck, 808 punch, grid 263 5]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 263 6]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| 1 | `[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0] [inst -…` |
| 2 | `263` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, rave, no singing, no choir, no vocal chops, original composition, kick split, drop first, 165 bpm, instrumental, no vocals
```

```text
[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0]

[inst - rapid hi-hats roll, growl sustain, grid 263 1]

[drop - harder stacked drop, formant reverse wreck, chest-sub 808, grid 263 2]

[inst - 808 triplets, hats denser, grid 263 3]

[drop - full send drop, chest-sub wreck, tearout warp, grid 263 4]

[drop - harder growl drop, low rumble wreck, 808 punch, grid 263 5]

[outro - kick holds, rapid hi-hats roll, growl ride, grid 263 6]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `263` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `12 - Horizon Kick` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `12 - Horizon Kick` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Horizon Kick` |
| 3 | `12` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `12 - Horizon Kick` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `13-clean-wreckage`

Catalog id `audio/albums/drive-through/hour-1/13-clean-wreckage`.

US-safe EDM 180s: Drive-through clean-wreckage brostep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warp…` |
| 2 | `[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0] [drop - …` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/13-clean-wreckage` |

```text
brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0]

[drop - harder reese drop, kick stack wreck, chest formant, grid 269 1]

[inst - rapid hi-hats roll, 808 punch hold, grid 269 2]

[drop - full send drop, mid growl crash, warped wall, grid 269 3]

[outro - kick holds, hats denser, brostep ride, grid 269 4]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warp…` |
| 1 | `[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0] [drop - …` |
| 2 | `269` |
| 3 | `fixed` |
| 4 | `150` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warped bass, rave, 808, no singing, no choir, no vocal chops, original composition, riser, drop first, 150 bpm, instrumental, no vocals
```

```text
[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0]

[drop - harder reese drop, kick stack wreck, chest formant, grid 269 1]

[inst - rapid hi-hats roll, 808 punch hold, grid 269 2]

[drop - full send drop, mid growl crash, warped wall, grid 269 3]

[outro - kick holds, hats denser, brostep ride, grid 269 4]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `269` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `13 - Clean Wreckage` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `13 - Clean Wreckage` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Clean Wreckage` |
| 3 | `13` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `13 - Clean Wreckage` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `14-heart-lane`

Catalog id `audio/albums/drive-through/hour-1/14-heart-lane`.

US-safe EDM 180s: Drive-through heart-lane wave bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, n…` |
| 2 | `[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0] [inst - ra…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/14-heart-lane` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0]

[inst - rapid hi-hats roll, wave 808 sustain lane, grid 223 1]

[drop - harder formant drop, full send kick wreck, 808 slide, grid 223 2]

[inst - snare roll, chest-sub 808, grid 223 3]

[drop - full send drop, stacked wave bass, warped rumble, grid 223 4]

[outro - kick holds, rapid hi-hats roll, wave ride, grid 223 5]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, n…` |
| 1 | `[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0] [inst - ra…` |
| 2 | `223` |
| 3 | `fixed` |
| 4 | `145` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 145 bpm, instrumental, no vocals
```

```text
[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0]

[inst - rapid hi-hats roll, wave 808 sustain lane, grid 223 1]

[drop - harder formant drop, full send kick wreck, 808 slide, grid 223 2]

[inst - snare roll, chest-sub 808, grid 223 3]

[drop - full send drop, stacked wave bass, warped rumble, grid 223 4]

[outro - kick holds, rapid hi-hats roll, wave ride, grid 223 5]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `223` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `14 - Heart Lane` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `14 - Heart Lane` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Heart Lane` |
| 3 | `14` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `14 - Heart Lane` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `15-dawn-receipt`

Catalog id `audio/albums/drive-through/hour-1/15-dawn-receipt`.

US-safe EDM 180s: Drive-through dawn-receipt chest bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**ACE-Step 1.5 turbo AIO** (`CheckpointLoaderSimple`)

| Slot | Value |
| --- | --- |
| 0 | `ace_step_1.5_turbo_aio.safetensors` |

**AuraFlow sampling** (`ModelSamplingAuraFlow`)

| Slot | Value |
| --- | --- |
| 0 | `3` |

**Song Duration** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `180.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, …` |
| 2 | `[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0] [inst - rapi…` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-1/15-dawn-receipt` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 140 bpm, instrumental, no vocals
```

```text
[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0]

[inst - rapid hi-hats denser, 808 hold, grid 229 1]

[drop - harder growl drop, chest wall wreck, formant punch, grid 229 2]

[drop - full send drop, low sub wreck, warped 808, grid 229 3]

[outro - kick holds, hats denser, chest ride, grid 229 4]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, …` |
| 1 | `[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0] [inst - rapi…` |
| 2 | `229` |
| 3 | `fixed` |
| 4 | `140` |
| 5 | `180.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, rave, no singing, no choir, no vocal chops, original composition, riser, drop first, 140 bpm, instrumental, no vocals
```

```text
[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0]

[inst - rapid hi-hats denser, 808 hold, grid 229 1]

[drop - harder growl drop, chest wall wreck, formant punch, grid 229 2]

[drop - full send drop, low sub wreck, warped 808, grid 229 3]

[outro - kick holds, hats denser, chest ride, grid 229 4]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `229` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `15 - Dawn Receipt` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `15 - Dawn Receipt` |
| 1 | `320k` |

**Cover image** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `cover.png` |
| 1 | `image` |

**Album metadata** (`EZAudioMetadata`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |
| 2 | `Dawn Receipt` |
| 3 | `15` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `15 - Dawn Receipt` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `album`

Catalog id `audio/albums/drive-through/hour-1/album`.

Pack Hour 1 zip + m3u
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**Pack album zip** (`EZAlbumPack`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 1` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## `cover`

Catalog id `audio/albums/drive-through/hour-1/cover`.

Album cover still for Drive-through / Hour 1

**Klein 4B distilled FP8** (`UNETLoader`)

| Slot | Value |
| --- | --- |
| 0 | `flux-2-klein-4b-fp8.safetensors` |
| 1 | `default` |

**Qwen3-4B TE** (`CLIPLoader`)

| Slot | Value |
| --- | --- |
| 0 | `qwen_3_4b.safetensors` |
| 1 | `flux2` |
| 2 | `default` |

**Flux2 VAE** (`VAELoader`)

| Slot | Value |
| --- | --- |
| 0 | `flux2-vae.safetensors` |

**Positive** (`CLIPTextEncode`)

| Slot | Value |
| --- | --- |
| 0 | `square album cover, graphic print, night highway overpass, warped neon bass, we…` |

```text
square album cover, graphic print, night highway overpass, warped neon bass, wet asphalt, fictional act Drive-through, album Hour 1, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

**Negative** (`CLIPTextEncode`)

| Slot | Value |
| --- | --- |
| 0 | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt…` |

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

**Size 1:1 Instagram** (`EmptyFlux2LatentImage`)

| Slot | Value |
| --- | --- |
| 0 | `1024` |
| 1 | `1024` |
| 2 | `1` |

**KSampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `42` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Save PNG** (`SaveImage`)

| Slot | Value |
| --- | --- |
| 0 | `albums/Drive-through/Hour 1/cover` |

**Draft still (set to ez_still_draft_00001_.png)** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `example.png` |
| 1 | `image` |

**Klein Prompt Enhance** (`EZKleinPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `square album cover, graphic print, night highway overpass, warped neon bass, we…` |
| 2 | `true` |
| 3 | `t2i` |
| 4 | `YouTube 16:9 still` |
| 5 | `none` |
| 6 | `audio/albums/drive-through/hour-1/cover` |

```text
square album cover, graphic print, night highway overpass, warped neon bass, wet asphalt, fictional act Drive-through, album Hour 1, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

**Negative Prompt Enhance** (`EZNegativePromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt…` |
| 1 | `true` |
| 2 | `klein` |

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.34.6 / lab `INPUT_TYPES` — not SD1.5 folklore.

### `CheckpointLoaderSimple` — Load Checkpoint

Load a single-file checkpoint that bundles MODEL + CLIP + VAE.

!!! warning "Lab notes"

    ACE-Step 1.5 turbo AIO (ace_step_1.5_turbo_aio.safetensors) on every music graph.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `MODEL` | out | `MODEL` | ACE denoiser (then ModelSamplingAuraFlow). |
| `CLIP` | out | `CLIP` | ACE text encoder. |
| `VAE` | out | `VAE` | ACE audio VAE. |

#### `ckpt_name`

Type `STRING`.

Filename under checkpoints/.

**How it affects generation:** Lab music is the turbo AIO. XL is opt-in via download-music --tier xl — swap only if you meant to.

**This graph (all 15 instances):** `ace_step_1.5_turbo_aio.safetensors`

### `ModelSamplingAuraFlow` — ModelSamplingAuraFlow

Patch ACE-Step with AuraFlow sampling shift.

!!! warning "Lab notes"

    Every ACE graph uses shift 3.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `model` | in | `MODEL` | ACE checkpoint MODEL. |
| `MODEL` | out | `MODEL` | Shifted ACE denoiser. |

#### `shift`

Type `FLOAT`. Range / default: 3 (lab ACE).

AuraFlow shift.

**How it affects generation:** 3 is the ACE-Step 1.5 lab value. Higher shift changes timing/attack of the beat.

**This graph (all 15 instances):** `3`

### `PrimitiveNode` — Primitive

A typed constant (string or float) with seed-style control.

!!! warning "Lab notes"

    Music Duration (FLOAT) and Prompt Forge Context (STRING). widgets[1] is always control_after_generate.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `value` | out | `FLOAT\|STRING` | Wired into duration / context / lyrics. |

#### `value`

Type `FLOAT|STRING`.

The constant.

**How it affects generation:** FLOAT seconds drive ACE latent length. STRING context is bible/research for Enhance.

**This graph (all 15 instances):** `180.0`

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Whether the primitive mutates after Queue.

**How it affects generation:** fixed keeps duration/context pinned.

**This graph (all 15 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

### `EmptyAceStep1.5LatentAudio` — Empty ACE-Step 1.5 Latent Audio

Allocate an ACE-Step audio latent for N seconds.

!!! warning "Lab notes"

    Draft 32 s, full 96 s, album takes 180 s. seconds is also a socket from PrimitiveNode so App Duration stays in one place.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `seconds` | in | `FLOAT` | Wired from Song Duration primitive on music graphs. |
| `LATENT` | out | `LATENT` | Audio latent for KSampler. |

#### `seconds`

Type `FLOAT`. Range / default: 32 / 96 / 180 lab.

Duration in seconds.

**How it affects generation:** Longer latents cost RAM/time linearly. Stay at the seeded length unless you have headroom.

**This graph (all 15 instances):** `180.0`

#### `batch_size`

Type `INT`. Range / default: 1.

Takes per Queue.

**How it affects generation:** Stay 1.

**This graph (all 15 instances):** `1`

### `EZAceStepPromptEnhance` — ACE-Step Prompt Enhance

Rewrite ACE tags (genre first) and lyrics. Instrumental mode forces [inst].

!!! warning "Lab notes"

    Enhance off on authored album takes. Instrumental sanitizes lyrics into bracket cues.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `lyrics` | in | `STRING` | Optional lyrics override (EZRapLyrics). |
| `tags` | out | `STRING` | Tags for the ACE encoder. |
| `lyrics` | out | `STRING` | Lyrics / [inst] for the ACE encoder. |

#### `sample`

Type `COMBO`. Range / default: custom.

Sample or Custom.

**How it affects generation:** Custom keeps authored tags/lyrics.

**This graph (all 15 instances):** `custom`

#### `tags`

Type `STRING`.

Genre-first tags.

**How it affects generation:** Keep vocal identity tags stable across an album. Drive-through is not rap-over-club.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, wa…` |
| ez_edm_prompt | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 8…` |
| ez_edm_prompt | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| ez_edm_prompt | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped b…` |
| ez_edm_prompt | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, r…` |
| ez_edm_prompt | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda…` |
| ez_edm_prompt | `color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, wa…` |
| ez_edm_prompt | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, …` |
| ez_edm_prompt | `warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warp…` |
| ez_edm_prompt | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808…` |
| ez_edm_prompt | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave…` |
| ez_edm_prompt | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| ez_edm_prompt | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warp…` |
| ez_edm_prompt | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, n…` |
| ez_edm_prompt | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, …` |

#### `lyrics`

Type `STRING`.

Sectioned lyrics.

**How it affects generation:** Enhance off on catalog takes so exclusive verses stay pinned.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, g…` |
| ez_edm_prompt | `[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0] [drop - har…` |
| ez_edm_prompt | `[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0] [inst - me…` |
| ez_edm_prompt | `[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0] [inst - ra…` |
| ez_edm_prompt | `[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0] [inst - rapid…` |
| ez_edm_prompt | `[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0] [drop…` |
| ez_edm_prompt | `[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0] [chorus]…` |
| ez_edm_prompt | `[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0] [inst - …` |
| ez_edm_prompt | `[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 …` |
| ez_edm_prompt | `[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0] [inst - ame…` |
| ez_edm_prompt | `[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0] [inst - rap…` |
| ez_edm_prompt | `[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0] [inst -…` |
| ez_edm_prompt | `[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0] [drop - …` |
| ez_edm_prompt | `[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0] [inst - ra…` |
| ez_edm_prompt | `[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0] [inst - rapi…` |

#### `enhance`

Type `BOOLEAN`. Range / default: false on albums.

Run the rewriter.

**How it affects generation:** On only when you typed a lazy hook and want the GGUF to expand it.

**This graph (all 15 instances):** `false`

#### `mode`

Type `COMBO`.

Vocal vs instrumental sanitizer.

**How it affects generation:** instrumental forces no-vocals tags and [inst] lyrics.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `vocal` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `vocal` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |
| ez_edm_prompt | `instrumental` |

**Other choices**

| Choice | What it does |
| --- | --- |
| `vocal` | Nill Bye / rap-draft / rap-full. |
| `instrumental` | Drive-through EDM. |

#### `catalog`

Type `STRING`.

Sample-catalog id.

**How it affects generation:** Leave as stamped.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/01-night-window` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/02-open-lane` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/03-exit-seven` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/04-skyline-pass` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/05-on-ramp` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/06-tunnel-bass` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/07-wide-open` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/08-overpass` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/09-second-wave` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/10-freight-pulse` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/11-keep-going` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/12-horizon-kick` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/13-clean-wreckage` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/14-heart-lane` |
| ez_edm_prompt | `audio/albums/drive-through/hour-1/15-dawn-receipt` |

### `TextEncodeAceStepAudio1.5` — ACE-Step 1.5 Text Encode

Pack tags, lyrics, BPM, key, and duration into ACE conditioning.

!!! warning "Lab notes"

    15 widgets including control_after_generate after seed (see _ace_widgets_contract.py). Vocal graphs language=en; instrumental unknown. generate_audio_codes stays true.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `clip` | in | `CLIP` | ACE CLIP from the AIO checkpoint. |
| `tags` | in | `STRING` | Often wired from EZAceStepPromptEnhance. |
| `lyrics` | in | `STRING` | Wired lyrics / [inst]. |
| `duration` | in | `FLOAT` | Same seconds as the empty latent. |
| `CONDITIONING` | out | `CONDITIONING` | Positive for KSampler. |

#### `tags`

Type `STRING`.

Genre-first tags, BPM last.

**How it affects generation:** ACE reads tags as the arrangement. Keep dry-booth vocal tags on Nill Bye; Drive-through is warped bass, no rap vocal.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `warped hybrid-trap, trap drums, rapid hi-hats, formant bass, chest-sub, 808, wa…` |
| ACE tags + lyrics | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, rave, 8…` |
| ACE tags + lyrics | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| ACE tags + lyrics | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, reese bass, warped b…` |
| ACE tags + lyrics | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, r…` |
| ACE tags + lyrics | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda…` |
| ACE tags + lyrics | `color bass, formant bass, chest-sub, rapid hi-hats, trap drums, stacked 808, wa…` |
| ACE tags + lyrics | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, warped bass, …` |
| ACE tags + lyrics | `warped hybrid-trap, trap drums, rapid hi-hats, growl bass, chest-sub, 808, warp…` |
| ACE tags + lyrics | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, rave, 808…` |
| ACE tags + lyrics | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, warped bass, rave…` |
| ACE tags + lyrics | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, ra…` |
| ACE tags + lyrics | `brostep, growl bass, chest-sub, rapid hi-hats, trap drums, chest-sub bass, warp…` |
| ACE tags + lyrics | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, rave, n…` |
| ACE tags + lyrics | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, body bass, warped bass, …` |

#### `lyrics`

Type `STRING`.

Sectioned lyrics or [inst] cues.

**How it affects generation:** Non-empty lines under a section are sung. Instrumental graphs must keep cues inside [brackets].

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `[drop - heavy warped drop, warped hybrid-trap drums 808 wreck, formant grind, g…` |
| ACE tags + lyrics | `[drop - full send drop, riddim wobble wreck, sub crush, grid 191 0] [drop - har…` |
| ACE tags + lyrics | `[drop - heavy tearout drop, growl wreck, formant scrape, grid 233 0] [inst - me…` |
| ACE tags + lyrics | `[drop - heavy brostep drop, mid growl wreck, warped 808, grid 199 0] [inst - ra…` |
| ACE tags + lyrics | `[drop - heavy wave drop, warped 808 wreck, fold bass, grid 197 0] [inst - rapid…` |
| ACE tags + lyrics | `[drop - heavy dirty drop, industrial 808 warp, formant wreck, grid 257 0] [drop…` |
| ACE tags + lyrics | `[drop - heavy color drop, warped 808 wreck, formant stack, grid 239 0] [chorus]…` |
| ACE tags + lyrics | `[drop - heavy wobble drop, dirty dubstep wreck, sub crush, grid 227 0] [inst - …` |
| ACE tags + lyrics | `[drop - heavy warped drop, warped hybrid-trap growl wreck, 808 stack, grid 241 …` |
| ACE tags + lyrics | `[drop - heavy amen drop, reese stack wreck, warped 808, grid 211 0] [inst - ame…` |
| ACE tags + lyrics | `[drop - heavy neuro drop, reese 808 wreck, warped coil, grid 251 0] [inst - rap…` |
| ACE tags + lyrics | `[drop - heavy tearout drop, kick split wreck, warped growl, grid 263 0] [inst -…` |
| ACE tags + lyrics | `[drop - heavy brostep drop, stacked 808 warp, growl wreck, grid 269 0] [drop - …` |
| ACE tags + lyrics | `[drop - heavy wave drop, chest-sub 808 warp, fold wreck, grid 223 0] [inst - ra…` |
| ACE tags + lyrics | `[drop - heavy chest drop, warped 808 wreck, sub grind, grid 229 0] [inst - rapi…` |

#### `seed`

Type `INT`.

ACE encoder seed (audio-codes LLM).

**How it affects generation:** Independent from KSampler seed. Lab locks it with the take.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `193` |
| ACE tags + lyrics | `191` |
| ACE tags + lyrics | `233` |
| ACE tags + lyrics | `199` |
| ACE tags + lyrics | `197` |
| ACE tags + lyrics | `257` |
| ACE tags + lyrics | `239` |
| ACE tags + lyrics | `227` |
| ACE tags + lyrics | `241` |
| ACE tags + lyrics | `211` |
| ACE tags + lyrics | `251` |
| ACE tags + lyrics | `263` |
| ACE tags + lyrics | `269` |
| ACE tags + lyrics | `223` |
| ACE tags + lyrics | `229` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Seed control.

**How it affects generation:** fixed on every lab take.

**This graph (all 15 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

#### `bpm`

Type `INT`. Range / default: 10–300.

Tempo written into the codes.

**How it affects generation:** Must match the tags' BPM. Mismatch makes the vocal drift the grid.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `145` |
| ACE tags + lyrics | `152` |
| ACE tags + lyrics | `142` |
| ACE tags + lyrics | `145` |
| ACE tags + lyrics | `155` |
| ACE tags + lyrics | `150` |
| ACE tags + lyrics | `150` |
| ACE tags + lyrics | `150` |
| ACE tags + lyrics | `150` |
| ACE tags + lyrics | `176` |
| ACE tags + lyrics | `170` |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics | `150` |
| ACE tags + lyrics | `145` |
| ACE tags + lyrics | `140` |

#### `duration`

Type `FLOAT`.

Seconds (duplicated on the latent).

**How it affects generation:** Keep in lockstep with EmptyAceStep1.5LatentAudio / Primitive.

**This graph (all 15 instances):** `180.0`

#### `timesignature`

Type `COMBO`. Range / default: 4.

Beats per bar.

**How it affects generation:** 4 is lab 4/4. 3 is waltz; 6 is 6/8.

**This graph (all 15 instances):** `4`

**Other choices**

| Choice | What it does |
| --- | --- |
| `2` | 2/4. |
| `3` | 3/4. |
| `4` | Lab 4/4. |
| `6` | 6/8. |

#### `language`

Type `COMBO`. Range / default: en / unknown.

Lyric language.

**How it affects generation:** en for sung English. unknown for instrumental (do not leave en on a no-vocal take).

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `en` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `en` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |
| ACE tags + lyrics | `unknown` |

**Other choices**

| Choice | What it does |
| --- | --- |
| `en` | English lyrics. Lab vocal graphs. |
| `unknown` | No lyric language. Lab instrumental / Drive-through graphs. |
| `ja` | Japanese. |
| `zh` | Chinese. |
| `yue` | Cantonese. |
| `es` | Spanish. |
| `de` | German. |
| `fr` | French. |
| `pt` | Portuguese. |
| `ru` | Russian. |
| `it` | Italian. |
| `ko` | Korean. |
| `ar` | Arabic. |
| `hi` | Hindi. |
| `id` | Indonesian. |
| `vi` | Vietnamese. |
| `th` | Thai. |
| `tr` | Turkish. |
| `pl` | Polish. |
| `nl` | Dutch. |
| `sv` | Swedish. |
| `uk` | Ukrainian. |
| `he` | Hebrew. |
| `fa` | Persian. |
| `cs` | Czech. |
| `el` | Greek. |
| `hu` | Hungarian. |
| `ro` | Romanian. |
| `fi` | Finnish. |
| `da` | Danish. |
| `no` | Norwegian. |
| `ms` | Malay. |
| `ta` | Tamil. |
| `te` | Telugu. |
| `bn` | Bengali. |
| `ur` | Urdu. |
| `pa` | Punjabi. |
| `tl` | Tagalog. |
| `sw` | Swahili. |
| `az` | Azerbaijani. |
| `bg` | Bulgarian. |
| `ca` | Catalan. |
| `hr` | Croatian. |
| `ht` | Haitian Creole. |
| `is` | Icelandic. |
| `la` | Latin. |
| `lt` | Lithuanian. |
| `ne` | Nepali. |
| `sa` | Sanskrit. |
| `sk` | Slovak. |
| `sr` | Serbian. |

#### `keyscale`

Type `COMBO`. Range / default: C minor.

Musical key.

**How it affects generation:** Lab C minor. Changing key is a new arrangement, not a mix tweak.

**This graph (all 15 instances):** `C minor`

**Other choices**

| Choice | What it does |
| --- | --- |
| `C major` | Major key of C. |
| `C# major` | Major key of C#. |
| `Db major` | Major key of Db. |
| `D major` | Major key of D. |
| `D# major` | Major key of D#. |
| `Eb major` | Major key of Eb. |
| `E major` | Major key of E. |
| `F major` | Major key of F. |
| `F# major` | Major key of F#. |
| `Gb major` | Major key of Gb. |
| `G major` | Major key of G. |
| `G# major` | Major key of G#. |
| `Ab major` | Major key of Ab. |
| `A major` | Major key of A. |
| `A# major` | Major key of A#. |
| `Bb major` | Major key of Bb. |
| `B major` | Major key of B. |
| `C minor` | Lab ships C minor on ACE graphs. Changing key reshapes harmony; keep vocal graphs in one key per album unless you mean a new arrangement. |
| `C# minor` | Minor key of C#. |
| `Db minor` | Minor key of Db. |
| `D minor` | Minor key of D. |
| `D# minor` | Minor key of D#. |
| `Eb minor` | Minor key of Eb. |
| `E minor` | Minor key of E. |
| `F minor` | Minor key of F. |
| `F# minor` | Minor key of F#. |
| `Gb minor` | Minor key of Gb. |
| `G minor` | Minor key of G. |
| `G# minor` | Minor key of G#. |
| `Ab minor` | Minor key of Ab. |
| `A minor` | Minor key of A. |
| `A# minor` | Minor key of A#. |
| `Bb minor` | Minor key of Bb. |
| `B minor` | Minor key of B. |

#### `generate_audio_codes`

Type `BOOLEAN`. Range / default: true.

Run the ACE LLM that drafts audio codes.

**How it affects generation:** true = higher quality, slower. Off only if you pass a reference timbre (lab graphs do not).

**This graph (all 15 instances):** `true`

#### `cfg_scale`

Type `FLOAT`. Range / default: 2.0.

Guidance inside audio-code generation.

**How it affects generation:** 2.0 is the ACE default. Higher follows tags/lyrics more tightly and can sound rigid.

**This graph (all 15 instances):** `2.0`

#### `temperature`

Type `FLOAT`. Range / default: 0.85.

Sampling temperature for audio codes.

**How it affects generation:** Lower = more deterministic. Higher = wilder fills.

**This graph (all 15 instances):** `0.85`

#### `top_p`

Type `FLOAT`. Range / default: 0.9.

Nucleus sampling.

**How it affects generation:** 0.9 is the lab default.

**This graph (all 15 instances):** `0.9`

#### `top_k`

Type `INT`. Range / default: 0 = off.

Top-k token cap.

**How it affects generation:** 0 disables top-k (lab).

**This graph (all 15 instances):** `0`

#### `min_p`

Type `FLOAT`. Range / default: 0.0.

Minimum probability floor.

**How it affects generation:** 0.0 disables min-p (lab).

**This graph (all 15 instances):** `0.0`

### `ConditioningZeroOut` — Conditioning Zero Out

Replace a conditioning with zeros (unconditional / empty negative).

!!! warning "Lab notes"

    ACE graphs zero the negative so CFG 1.0 stays a true uncond skip.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `conditioning` | in | `CONDITIONING` | Usually an unused negative encode. |
| `CONDITIONING` | out | `CONDITIONING` | Zeroed cond for KSampler.negative. |

No widgets. Sockets only.

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
| ACE sampler | `193` |
| ACE sampler | `191` |
| ACE sampler | `233` |
| ACE sampler | `199` |
| ACE sampler | `197` |
| ACE sampler | `257` |
| ACE sampler | `239` |
| ACE sampler | `227` |
| ACE sampler | `241` |
| ACE sampler | `211` |
| ACE sampler | `251` |
| ACE sampler | `263` |
| ACE sampler | `269` |
| ACE sampler | `223` |
| ACE sampler | `229` |
| KSampler | `42` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed (lab).

What happens to seed after Queue.

**How it affects generation:** fixed keeps iteration honest while you change the prompt.

**This graph (all 16 instances):** `fixed`

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

**This graph (all 16 instances):** `8`

#### `cfg`

Type `FLOAT`. Range / default: 0–100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5.

Classifier-free guidance scale.

**How it affects generation:** Distilled Klein is CFG 1.0 — raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.

**This graph (all 16 instances):** `1.0`

#### `sampler_name`

Type `COMBO`. Range / default: euler (most lab); uni_pc (Wan).

ODE / SDE algorithm that removes noise.

**How it affects generation:** euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.

**This graph (all 16 instances):** `euler`

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

**This graph (all 16 instances):** `simple`

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

**This graph (all 16 instances):** `1.0`

### `VAEDecodeAudio` — VAE Decode Audio

Decode an ACE audio latent to AUDIO.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | ACE KSampler output. |
| `vae` | in | `VAE` | ACE VAE from the AIO checkpoint. |
| `AUDIO` | out | `AUDIO` | Waveform for SaveAudio. |

No widgets. Sockets only.

### `SaveAudio` — Save Audio

Write a FLAC/wav master.

!!! warning "Lab notes"

    Music graphs pair this with SaveAudioMP3 and EZAudioMetadata. Stem mix uses ez_stem_mix.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio` | in | `AUDIO` | Decoded ACE or mix. |

#### `filename_prefix`

Type `STRING`.

Save stem.

**How it affects generation:** Album tracks use NN - Song Title. Tags come from EZAudioMetadata.

| Instance | Value |
| --- | --- |
| FLAC master | `01 - Night Window` |
| FLAC master | `02 - Open Lane` |
| FLAC master | `03 - Exit Seven` |
| FLAC master | `04 - Skyline Pass` |
| FLAC master | `05 - On-Ramp` |
| FLAC master | `06 - Tunnel Bass` |
| FLAC master | `07 - Wide Open` |
| FLAC master | `08 - Overpass` |
| FLAC master | `09 - Second Wave` |
| FLAC master | `10 - Freight Pulse` |
| FLAC master | `11 - Keep Going` |
| FLAC master | `12 - Horizon Kick` |
| FLAC master | `13 - Clean Wreckage` |
| FLAC master | `14 - Heart Lane` |
| FLAC master | `15 - Dawn Receipt` |

### `SaveAudioMP3` — Save Audio (MP3)

Write an MP3 copy of the same take.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio` | in | `AUDIO` | Same AUDIO as SaveAudio. |

#### `filename_prefix`

Type `STRING`.

Save stem (match FLAC).

**How it affects generation:** Same NN - Song Title as the FLAC.

| Instance | Value |
| --- | --- |
| MP3 320k | `01 - Night Window` |
| MP3 320k | `02 - Open Lane` |
| MP3 320k | `03 - Exit Seven` |
| MP3 320k | `04 - Skyline Pass` |
| MP3 320k | `05 - On-Ramp` |
| MP3 320k | `06 - Tunnel Bass` |
| MP3 320k | `07 - Wide Open` |
| MP3 320k | `08 - Overpass` |
| MP3 320k | `09 - Second Wave` |
| MP3 320k | `10 - Freight Pulse` |
| MP3 320k | `11 - Keep Going` |
| MP3 320k | `12 - Horizon Kick` |
| MP3 320k | `13 - Clean Wreckage` |
| MP3 320k | `14 - Heart Lane` |
| MP3 320k | `15 - Dawn Receipt` |

#### `quality`

Type `COMBO`. Range / default: 320k.

Bitrate preset.

**How it affects generation:** 320k is the lab master. Lower bitrates are smaller and harsher on hats.

**This graph (all 15 instances):** `320k`

**Other choices**

| Choice | What it does |
| --- | --- |
| `320k` | Lab default. |
| `192k` | Smaller, more artifacts. |
| `128k` | Preview only. |

### `Note` — Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

| Instance | Value |
| --- | --- |
| Operator note | `## 01-night-window US-safe EDM **180 s** take: **night window**. Fictional act …` |
| Operator note | `## 02-open-lane US-safe EDM **180 s** take: **open lane**. Fictional act **Driv…` |
| Operator note | `## 03-exit-seven US-safe EDM **180 s** take: **exit seven**. Fictional act **Dr…` |
| Operator note | `## 04-skyline-pass US-safe EDM **180 s** take: **skyline pass**. Fictional act …` |
| Operator note | `## 05-on-ramp US-safe EDM **180 s** take: **on-ramp**. Fictional act **Drive-th…` |
| Operator note | `## 06-tunnel-bass US-safe EDM **180 s** take: **tunnel bass**. Fictional act **…` |
| Operator note | `## 07-wide-open US-safe EDM **180 s** take: **wide open**. Fictional act **Driv…` |
| Operator note | `## 08-overpass US-safe EDM **180 s** take: **overpass**. Fictional act **Drive-…` |
| Operator note | `## 09-second-wave US-safe EDM **180 s** take: **second wave**. Fictional act **…` |
| Operator note | `## 10-freight-pulse US-safe EDM **180 s** take: **freight pulse**. Fictional ac…` |
| Operator note | `## 11-keep-going US-safe EDM **180 s** take: **keep going**. Fictional act **Dr…` |
| Operator note | `## 12-horizon-kick US-safe EDM **180 s** take: **horizon kick**. Fictional act …` |
| Operator note | `## 13-clean-wreckage US-safe EDM **180 s** take: **clean wreckage**. Fictional …` |
| Operator note | `## 14-heart-lane US-safe EDM **180 s** take: **heart lane**. Fictional act **Dr…` |
| Operator note | `## 15-dawn-receipt US-safe EDM **180 s** take: **dawn receipt**. Fictional act …` |
| Operator note | `## audio/albums/drive-through/hour-1/album Album **Hour 1** by **Drive-through*…` |
| Operator note | `## audio/albums/drive-through/hour-1/cover Album cover for **Drive-through — Ho…` |

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

| Instance | Value |
| --- | --- |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Cover image | `cover.png` |
| Draft still (set to ez_still_draft_0000… | `example.png` |

#### `upload`

Type `COMBO`. Range / default: image.

Upload widget type.

**How it affects generation:** Leave image. This is the choose-file control, not a generation knob.

**This graph (all 16 instances):** `image`

### `EZAudioMetadata` — Audio Metadata

Stamp artist/album/title tags and optional cover on saved audio.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio` | in | `AUDIO` | Pass-through AUDIO. |
| `cover` | in | `IMAGE` | Optional. Unwired so App Queue does not require a file. |
| `audio` | out | `AUDIO` | Same AUDIO; files on disk get tags. |

#### `artist`

Type `STRING`.

ID3/Vorbis artist.

**How it affects generation:** Nill Bye vs Drive-through.

**This graph (all 15 instances):** `Drive-through`

#### `album`

Type `STRING`.

Album title.

**How it affects generation:** Must match the folder album-slug display name.

**This graph (all 15 instances):** `Hour 1`

#### `title`

Type `STRING`.

Track title.

**How it affects generation:** Pairs with SaveAudio stem NN - Song Title.

| Instance | Value |
| --- | --- |
| Album metadata | `Night Window` |
| Album metadata | `Open Lane` |
| Album metadata | `Exit Seven` |
| Album metadata | `Skyline Pass` |
| Album metadata | `On-Ramp` |
| Album metadata | `Tunnel Bass` |
| Album metadata | `Wide Open` |
| Album metadata | `Overpass` |
| Album metadata | `Second Wave` |
| Album metadata | `Freight Pulse` |
| Album metadata | `Keep Going` |
| Album metadata | `Horizon Kick` |
| Album metadata | `Clean Wreckage` |
| Album metadata | `Heart Lane` |
| Album metadata | `Dawn Receipt` |

#### `track`

Type `INT`. Range / default: 1–99.

Track number.

**How it affects generation:** Numbered takes 01–20.

| Instance | Value |
| --- | --- |
| Album metadata | `1` |
| Album metadata | `2` |
| Album metadata | `3` |
| Album metadata | `4` |
| Album metadata | `5` |
| Album metadata | `6` |
| Album metadata | `7` |
| Album metadata | `8` |
| Album metadata | `9` |
| Album metadata | `10` |
| Album metadata | `11` |
| Album metadata | `12` |
| Album metadata | `13` |
| Album metadata | `14` |
| Album metadata | `15` |

#### `tracktotal`

Type `INT`.

Album track count.

**How it affects generation:** 15 or 20 depending on the album.

**This graph (all 15 instances):** `15`

#### `year`

Type `INT`. Range / default: 2026.

Tag year.

**How it affects generation:** Does not affect audio.

**This graph (all 15 instances):** `2026`

#### `art_mode`

Type `COMBO`. Range / default: skip.

Cover art policy.

**How it affects generation:** skip on every audio Queue (Cover LoadImage is bypassed). generate is klein occupancy — later session. upload: graph view, Ctrl+B Cover image, then wire.

**This graph (all 15 instances):** `skip`

**Other choices**

| Choice | What it does |
| --- | --- |
| `skip` | Lab default. No cover required. |
| `upload` | Un-bypass Cover image and wire the socket. |
| `generate` | Use cover.jpg from the album folder (klein session). |

#### `prefix`

Type `STRING`.

SaveAudio stem to stamp.

**How it affects generation:** Must match SaveAudio / SaveAudioMP3.

| Instance | Value |
| --- | --- |
| Album metadata | `01 - Night Window` |
| Album metadata | `02 - Open Lane` |
| Album metadata | `03 - Exit Seven` |
| Album metadata | `04 - Skyline Pass` |
| Album metadata | `05 - On-Ramp` |
| Album metadata | `06 - Tunnel Bass` |
| Album metadata | `07 - Wide Open` |
| Album metadata | `08 - Overpass` |
| Album metadata | `09 - Second Wave` |
| Album metadata | `10 - Freight Pulse` |
| Album metadata | `11 - Keep Going` |
| Album metadata | `12 - Horizon Kick` |
| Album metadata | `13 - Clean Wreckage` |
| Album metadata | `14 - Heart Lane` |
| Album metadata | `15 - Dawn Receipt` |

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

**This graph (all 17 instances):** `lab`

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

### `EZAlbumPack` — Album Pack

Write <Album>.m3u and <Album>.zip under albums/<Artist>/<Album>/.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `zip_path` | out | `STRING` | Zip path or empty on failure. |

#### `artist`

Type `STRING`.

Artist folder.

**How it affects generation:** Drive-through or Nill Bye.

**This graph:** `Drive-through`

#### `album`

Type `STRING`.

Album folder display name.

**How it affects generation:** Queue tracks first (or album-render). CPU only.

**This graph:** `Hour 1`

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

**This graph:** `flux-2-klein-4b-fp8.safetensors`

#### `weight_dtype`

Type `COMBO`. Range / default: default.

Cast at load.

**How it affects generation:** default keeps the file's dtype (Klein FP8, LTX INT8-convrot, Wan FP16).

**This graph:** `default`

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

**This graph:** `qwen_3_4b.safetensors`

#### `type`

Type `COMBO`.

CLIPType enum. Picks tokenizer + template.

**How it affects generation:** flux2 wraps Klein strings in a Qwen chat template — do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.

**This graph:** `flux2`

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

**This graph:** `default`

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

**This graph:** `flux2-vae.safetensors`

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
| Positive | `square album cover, graphic print, night highway overpass, warped neon bass, we…` |
| Negative | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt…` |

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

**This graph:** `1024`

#### `height`

Type `INT`.

Latent pixel height.

**How it affects generation:** 1280×704 is the LTX VAE grid (÷32). 1280×720 is not.

**This graph:** `1024`

#### `batch_size`

Type `INT`. Range / default: draft 2; others 1.

How many stills in one Queue.

**How it affects generation:** Draft uses 2 for a cheap fork. Heroes stay 1.

**This graph:** `1`

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

**This graph:** `albums/Drive-through/Hour 1/cover`

### `EZKleinPromptEnhance` — Klein Prompt Enhance

Rewrite a lazy still/edit prompt for Klein 4B with on-box Qwen3-4B-Instruct.

!!! warning "Lab notes"

    Enhance on for lazy CLIP printers; off for authored recipes. Style ignored when it would fight an I2V start frame (not used here). Occupancy llm for the GGUF, then klein for the UNET.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `prompt` | in | `STRING` | Optional override of the widget (usually unwired). |
| `context` | in | `STRING` | Bible/research. Ignored when Enhance is off. |
| `image_desc` | in | `STRING` | Optional still caption from EZImageDescribe. |
| `prompt` | out | `STRING` | String CLIP actually encodes. |

#### `sample`

Type `COMBO`. Range / default: custom.

Lab sample prompt or Custom.

**How it affects generation:** Custom keeps the textarea. Picking a sample fills and locks the Prompt. The App dropdown lists this graph's 20 recipes plus Custom (place recipes such as Cliff villa on stills/dream-house).

**This graph:** `custom`

#### `prompt`

Type `STRING`.

Lazy sentence or authored still prompt.

**How it affects generation:** When Enhance is on, the GGUF expands this into Klein-native sentences.

**This graph:** `square album cover, graphic print, night highway overpass, warped neon bass, wet asphalt, fictional act Drive-through, album Hour 1, no text, no letters, no logos, no living person likeness, no celeb…`

```text
square album cover, graphic print, night highway overpass, warped neon bass, wet asphalt, fictional act Drive-through, album Hour 1, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

#### `enhance`

Type `BOOLEAN`. Range / default: on for lazy printers.

Run the rewriter.

**How it affects generation:** Off = encode the widget as-is (plus style suffix if set).

**This graph:** `true`

#### `mode`

Type `COMBO`. Range / default: t2i / edit / identity / text_swap.

System prompt flavor.

**How it affects generation:** t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet). text_swap = glyph-lock lettering on a source still.

**This graph:** `t2i`

**Other choices**

| Choice | What it does |
| --- | --- |
| `t2i` | New still. |
| `edit` | Klein-edit / clay / tweak. |
| `identity` | Camera-free identity bible. |
| `text_swap` | Replace lettering; source still owns look and size. |

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

#### `catalog`

Type `STRING`.

Sample-catalog id (graph stem).

**How it affects generation:** Internal. Leave as stamped so sample dropdowns resolve.

**This graph:** `audio/albums/drive-through/hour-1/cover`

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

**This graph:** `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks`

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

#### `enhance`

Type `BOOLEAN`.

Rewrite using the positive as context.

**How it affects generation:** Stops canned 'illustration / Pixar' terms from fighting a cartoon-positive.

**This graph:** `true`

#### `family`

Type `COMBO`.

Which negative family.

**How it affects generation:** Must match the UNET on the canvas.

**This graph:** `klein`

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
