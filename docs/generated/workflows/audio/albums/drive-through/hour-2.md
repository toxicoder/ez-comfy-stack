---
title: "audio/albums/drive-through/hour-2"
description: "Album graphs under audio/albums/drive-through/hour-2 (tracks, cover, album pack)."
tags: [workflows, generated, comfyui, audio, album]
---

# audio/albums/drive-through/hour-2

**What's on this page**

- **Every track, cover, and album-pack graph** in this folder
- **Shared ACE-Step topology** (one printer, unique widgets per take)
- **Node parameter reference** for the types on these graphs

**What this enables**

- **Queuing one numbered take** or `album-render`
- **Reading tags, lyrics, seed, BPM** without opening raw JSON

**Who this is for:** studio users after `download-music`. Occupancy **audio** (cover stills are **klein** - separate session).

> Generated from `workflows/_lab/audio/albums/drive-through/hour-2/`. Do not hand-edit this file.

## Purpose

Numbered takes under `audio/albums/drive-through/hour-2/`. Queue one track, or `./scripts/manage.sh album-render --album drive-through/hour-2`.

```text
## 01-rumble-strip

US-safe EDM **325 s** take: **rumble strip**. Fictional act **Drive-through** (hardcore, pure of heart). Native ACE-Step 1.5 turbo AIO. Live bass-set take. Instrumental score is empty-body ACE markers (`[drop - cues]`, `[inst - cues]`, `[build-up]`, `[breakdown]`, `[outro]`) so ACE does not sing production notes. Form **drv-5d2d9ea518**. Short build, then the drop. Later stanzas switch layers. No section is a long loop. No brass and no high leads. Vocals are a rare DJ treat on other graphs, not here. The take is 5 sequential ACE-Step passes (67 s + 67 s + 67 s + 67 s + 67 s) joined in-graph on the bar grid by **Beat-join passes**: each seam overlaps 2 bar, 1 bar, 2 bar, 2 bar whole bars, the 808 hand-off never stacks or nulls, and the crossfade never clicks. SaveAudio, the MP3, and the metadata stamp carry the one joined master. Queue this graph **on its own** - draft-first is the generic rap lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and `[drop]` / `[inst]` / `[outro]` stay as written. Turn Enhance on only if you want the 4B rewriter.
3. Tags vs score: tags are genre/instrument hints; lyrics are the arrangement. Keep App **Vocal / instrumental** on instrumental so ACE does not sing. Encoder language is `unknown`. Free-text lines under a marker are lyrics - keep cues inside the brackets.
4. Original arrangements only. No "in the style of <living artist>". No living-DJ names. No famous-hook paraphrases.
5. ACE-Step timbre is **invented**, not a cloned act.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration 325 s across 5 passes, bpm 165, language unknown, timesignature 4, key D major, form drv-5d2d9ea518, generate_audio_codes true. Seed 271.
7. Saves: `01 - Rumble Strip` FLAC master + 320 kbps MP3 under `${COMFY_OUTPUT_DIR}`.
8. Cover separately: Queue **stills/thumbnail.json** or **stills/podcast-cover.json**. Do not embed Klein here.
9. Human selection and edit before any release. Prompts are not authorship (USCO Part 2 / Thaler).
10. Do not co-resident with LTX / Wan / Klein on this Spark.

Occupancy: audio - stop Klein / Wan / LTX session. One GB10 job.
```

## Shared graph

```mermaid
flowchart TB
  GNOTE["NOTE"]
  GQUALITY["QUALITY"]
  GMODEL["MODEL"]
  GDURATION["DURATION"]
  GPROMPT["PROMPT"]
  GOUTPUT["OUTPUT"]
  GPASS_2["PASS 2"]
  GPASS_3["PASS 3"]
  GPASS_4["PASS 4"]
  GPASS_5["PASS 5"]
  GJOIN["JOIN"]
  GINPUT["INPUT"]
  GSETTINGS["SETTINGS"]
```

## Graphs in this album

| Graph | Nodes | Occupancy |
| --- | --- | --- |
| `audio/albums/drive-through/hour-2/01-rumble-strip` | 45 | audio |
| `audio/albums/drive-through/hour-2/02-low-lane` | 38 | audio |
| `audio/albums/drive-through/hour-2/03-warm-merge` | 38 | audio |
| `audio/albums/drive-through/hour-2/04-colour-span` | 38 | audio |
| `audio/albums/drive-through/hour-2/05-garage-ticket` | 31 | audio |
| `audio/albums/drive-through/hour-2/06-liquid-grade` | 38 | audio |
| `audio/albums/drive-through/hour-2/07-jump-bay` | 38 | audio |
| `audio/albums/drive-through/hour-2/08-psy-median` | 31 | audio |
| `audio/albums/drive-through/hour-2/09-groove-mile` | 38 | audio |
| `audio/albums/drive-through/hour-2/10-donk-ramp` | 45 | audio |
| `audio/albums/drive-through/hour-2/11-bounce-booth` | 38 | audio |
| `audio/albums/drive-through/hour-2/12-toll-growl` | 31 | audio |
| `audio/albums/drive-through/hour-2/13-night-oil` | 31 | audio |
| `audio/albums/drive-through/hour-2/14-chest-pass` | 45 | audio |
| `audio/albums/drive-through/hour-2/15-sunrise-sub` | 45 | audio |
| `audio/albums/drive-through/hour-2/album` | 4 | none |
| `audio/albums/drive-through/hour-2/cover` | 18 | klein |

## `01-rumble-strip`

Catalog id `audio/albums/drive-through/hour-2/01-rumble-strip`.

US-safe EDM take: Drive-through rumble-strip hybrid trap warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `67.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 2 | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts, tempo push, dry hats, warped hybrid-trap drums 808 wreck, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, octave 808 stack, wreck warped drop, double-time feel, octave sub stack, low-mid bass melody, wobble FM voice, ghost snare, wide hat bed, warped hybrid-trap, dual-action pedal bass, heavy warped drop, 2 bars]

[inst - FM warp sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, layered sub stack, heavy reese drop, double-time feel, octave sub stack, low reese counterline, trap drums denser, side snare, rumble grind, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, kick pattern flip, rolling hats, rapid hi-hats roll, 2 bars]

[drop - chest-sub, low-mid orbits the sub, wide stereo layer, full send wobble drop, octave sub stack, low wobble answer, neuro wobble lead, offbeat hats, late snare, 808 slide, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, low-mid stack tightens, tempo push, early kick, dual-action pedal bass, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, rapid hi-hats, syncopated hats, stacked warp, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, layered sub stack, heavy wobble drop, body bass, wavy low-mid line, granular bass figure, trap drums denser, open hat, harder warped drop, 2 bars]

[inst - FM warp sub, low-mid from every angle, kick pattern flip, closed hat, pedal 808 hold, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, mono kick punch, rising energy, room snare, hats denser, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, wreck wobble drop, octave sub stack, low wobble answer, ghost snare, tight kick, full send drop, 2 bars]

[inst - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - wavy phase sub, layers surround the ear, layered sub stack, heavy warped drop, double-time feel, octave sub stack, low-mid bass melody, trap drums denser, pushed snare, low rumble wreck, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub energy lifts, accelerating hats, body bass, chopped hats, chest warped, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, wreck warped drop, body bass, body bass answer, ghost snare, kick opens, kick holds, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, low-end pressure builds, tempo push, body bass, snare answers, pedal ride, 2 bars]

[inst - chest-sub, low-mid from every angle, octave sub stack, kick pattern flip, offbeat push, 2 bars]

[drop - wavy phase sub, wide 3D bass field, wide stereo layer, full send wobble drop, double-time feel, body bass, wavy low-mid line, offbeat hats, straight hats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, octave sub stack, ghost snare, triplet hats, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, kick stomp, rising energy, body bass, backbeat shove, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 1 | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts...` |
| 2 | `271` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts, tempo push, dry hats, warped hybrid-trap drums 808 wreck, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, octave 808 stack, wreck warped drop, double-time feel, octave sub stack, low-mid bass melody, wobble FM voice, ghost snare, wide hat bed, warped hybrid-trap, dual-action pedal bass, heavy warped drop, 2 bars]

[inst - FM warp sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, layered sub stack, heavy reese drop, double-time feel, octave sub stack, low reese counterline, trap drums denser, side snare, rumble grind, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, kick pattern flip, rolling hats, rapid hi-hats roll, 2 bars]

[drop - chest-sub, low-mid orbits the sub, wide stereo layer, full send wobble drop, octave sub stack, low wobble answer, neuro wobble lead, offbeat hats, late snare, 808 slide, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, low-mid stack tightens, tempo push, early kick, dual-action pedal bass, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, rapid hi-hats, syncopated hats, stacked warp, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, layered sub stack, heavy wobble drop, body bass, wavy low-mid line, granular bass figure, trap drums denser, open hat, harder warped drop, 2 bars]

[inst - FM warp sub, low-mid from every angle, kick pattern flip, closed hat, pedal 808 hold, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, mono kick punch, rising energy, room snare, hats denser, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, wreck wobble drop, octave sub stack, low wobble answer, ghost snare, tight kick, full send drop, 2 bars]

[inst - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - wavy phase sub, layers surround the ear, layered sub stack, heavy warped drop, double-time feel, octave sub stack, low-mid bass melody, trap drums denser, pushed snare, low rumble wreck, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub energy lifts, accelerating hats, body bass, chopped hats, chest warped, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, wreck warped drop, body bass, body bass answer, ghost snare, kick opens, kick holds, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, low-end pressure builds, tempo push, body bass, snare answers, pedal ride, 2 bars]

[inst - chest-sub, low-mid from every angle, octave sub stack, kick pattern flip, offbeat push, 2 bars]

[drop - wavy phase sub, wide 3D bass field, wide stereo layer, full send wobble drop, double-time feel, body bass, wavy low-mid line, offbeat hats, straight hats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, octave sub stack, ghost snare, triplet hats, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, kick stomp, rising energy, body bass, backbeat shove, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `271` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `01 - Rumble Strip` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `01 - Rumble Strip` |
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
| 1 | `Hour 2` |
| 2 | `Rumble Strip` |
| 3 | `1` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `01 - Rumble Strip` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 2 | `[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, ris...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, rising energy, FM 808, side snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, layered sub stack, phase-charged heavy reese drop, response line, double-time feel, stacked 808, body bass answer, acid squelch line, staccato sub bursts, rolling hats, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, FM 808, fast bass triplets, late snare, 2 bars]

[build-up - chest-sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, octave 808 stack, laser electric wreck reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, distorted sub figure, driving sub pulse run, syncopated hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, downbeat kick, 2 bars]

[drop - octave sub pulse, wide 3D bass field, layered sub stack, laser electric heavy wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, staccato sub bursts, closed hat, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, stutter gate, accelerating hats, stacked 808, body bass answer, room snare, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, wide stereo layer, laser electric full send warped drop, counter-line, double-time feel, FM 808, low wobble answer, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, octave 808 stack, rising energy, stacked 808, chest-sub melody, acid squelch line, loose hats, 2 bars]

[inst - chest-sub, 3D low-mid orbit, FM 808, low-mid bass melody, neuro wobble lead, rolling 808 run, pushed snare, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick run, tempo push, stacked 808, wavy low-mid line, chopped hats, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, FM 808, low reese counterline, distorted sub figure, fast bass triplets, hat density up, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, wide stereo layer, phase-charged full send reese drop, response line, double-time feel, stacked 808, body bass answer, granular bass figure, double-time bass gallop, kick opens, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, FM 808, low wobble answer, wobble FM voice, driving sub pulse run, kick tightens, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, phase-charged stacked wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, phase-wavy synth line, rolling 808 run, snare answers, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, bass circles the low-mid, parallel low-mid layer, phase-charged harder warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, fast bass triplets, straight hats, 2 bars]

[inst - wavy phase sub, bass pans wide behind, wide stereo layer, FM 808, low reese counterline, double-time bass gallop, triplet hats, 2 bars]

[drop - bitcrushed 808, layers surround the ear, octave 808 stack, phase-charged wreck reese drop, response line, double-time feel, stacked 808, body bass answer, square-wave pulse figure, driving sub pulse run, backbeat shove, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, kick run, tempo push, panning bass layer, FM 808, low wobble answer, distorted sub figure, ghost notes, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, kick tightens, pre-impact hold, accelerating hats, parallel low-mid layer, FM 808, low-mid bass melody, wobble FM voice, wide hat bed, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 1 | `[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, ris...` |
| 2 | `271` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, rising energy, FM 808, side snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, layered sub stack, phase-charged heavy reese drop, response line, double-time feel, stacked 808, body bass answer, acid squelch line, staccato sub bursts, rolling hats, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, FM 808, fast bass triplets, late snare, 2 bars]

[build-up - chest-sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, octave 808 stack, laser electric wreck reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, distorted sub figure, driving sub pulse run, syncopated hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, downbeat kick, 2 bars]

[drop - octave sub pulse, wide 3D bass field, layered sub stack, laser electric heavy wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, staccato sub bursts, closed hat, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, stutter gate, accelerating hats, stacked 808, body bass answer, room snare, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, wide stereo layer, laser electric full send warped drop, counter-line, double-time feel, FM 808, low wobble answer, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, octave 808 stack, rising energy, stacked 808, chest-sub melody, acid squelch line, loose hats, 2 bars]

[inst - chest-sub, 3D low-mid orbit, FM 808, low-mid bass melody, neuro wobble lead, rolling 808 run, pushed snare, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick run, tempo push, stacked 808, wavy low-mid line, chopped hats, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, FM 808, low reese counterline, distorted sub figure, fast bass triplets, hat density up, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, wide stereo layer, phase-charged full send reese drop, response line, double-time feel, stacked 808, body bass answer, granular bass figure, double-time bass gallop, kick opens, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, FM 808, low wobble answer, wobble FM voice, driving sub pulse run, kick tightens, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, phase-charged stacked wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, phase-wavy synth line, rolling 808 run, snare answers, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, bass circles the low-mid, parallel low-mid layer, phase-charged harder warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, fast bass triplets, straight hats, 2 bars]

[inst - wavy phase sub, bass pans wide behind, wide stereo layer, FM 808, low reese counterline, double-time bass gallop, triplet hats, 2 bars]

[drop - bitcrushed 808, layers surround the ear, octave 808 stack, phase-charged wreck reese drop, response line, double-time feel, stacked 808, body bass answer, square-wave pulse figure, driving sub pulse run, backbeat shove, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, kick run, tempo push, panning bass layer, FM 808, low wobble answer, distorted sub figure, ghost notes, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, kick tightens, pre-impact hold, accelerating hats, parallel low-mid layer, FM 808, low-mid bass melody, wobble FM voice, wide hat bed, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `271` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 2 | `[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising energy, low chest-sub, mono kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, wide stereo layer, multi-stack heavy warped drop, response line, double-time feel, mono chest-sub, body bass answer, warped FM lead, driving sub pulse run, side snare, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, panning bass layer, wide laser full send wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, staccato sub bursts, kick opens, 2 bars]

[build-up - octave sub pulse, layers surround the ear, downbeat kick, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, parallel low-mid layer, multi-stack wreck wobble drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, phase-wavy synth line, fast bass triplets, backbeat shove, 2 bars]

[drop - chest-sub, bass circles the low-mid, wide stereo layer, multi-stack heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, driving sub pulse run, offbeat push, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, phase-charged wreck warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, square-wave pulse figure, fast bass triplets, dry hats, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, low-mid orbit widens, tempo push, low chest-sub, low wobble answer, room snare, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, layered sub stack, multi-stack wreck reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, warped FM lead, fast bass triplets, tight kick, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, wide laser heavy warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, granular bass figure, driving sub pulse run, dry hats, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, low-mid orbit widens, tempo push, mono chest-sub, wavy low-mid line, pushed snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, wide laser full send reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, staccato sub bursts, mono kick, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, beat stutter, accelerating hats, mono chest-sub, body bass answer, hat density up, 2 bars]

[inst - wavy phase sub, bass pans wide behind, FM 808, low wobble answer, acid squelch line, fast bass triplets, open hat, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, low chest-sub, low-mid bass melody, driving sub pulse run, snare answers, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, low-mid orbit widens, tempo push, octave 808 stack, mono chest-sub, wavy low-mid line, offbeat push, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, panning bass layer, low chest-sub, low reese counterline, acid squelch line, staccato sub bursts, straight hats, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, beat stutter, accelerating hats, layered sub stack, mono chest-sub, body bass answer, triplet hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, parallel low-mid layer, low chest-sub, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, rolling hats, rising energy, wide stereo layer, mono chest-sub, chest-sub melody, distorted sub figure, ghost notes, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, kick stomp, accelerating hats, octave 808 stack, low chest-sub, low-mid bass melody, granular bass figure, dry hats, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 1 | `[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising ...` |
| 2 | `271` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising energy, low chest-sub, mono kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, wide stereo layer, multi-stack heavy warped drop, response line, double-time feel, mono chest-sub, body bass answer, warped FM lead, driving sub pulse run, side snare, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, panning bass layer, wide laser full send wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, staccato sub bursts, kick opens, 2 bars]

[build-up - octave sub pulse, layers surround the ear, downbeat kick, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, parallel low-mid layer, multi-stack wreck wobble drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, phase-wavy synth line, fast bass triplets, backbeat shove, 2 bars]

[drop - chest-sub, bass circles the low-mid, wide stereo layer, multi-stack heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, driving sub pulse run, offbeat push, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, phase-charged wreck warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, square-wave pulse figure, fast bass triplets, dry hats, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, low-mid orbit widens, tempo push, low chest-sub, low wobble answer, room snare, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, layered sub stack, multi-stack wreck reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, warped FM lead, fast bass triplets, tight kick, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, wide laser heavy warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, granular bass figure, driving sub pulse run, dry hats, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, low-mid orbit widens, tempo push, mono chest-sub, wavy low-mid line, pushed snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, wide laser full send reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, staccato sub bursts, mono kick, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, beat stutter, accelerating hats, mono chest-sub, body bass answer, hat density up, 2 bars]

[inst - wavy phase sub, bass pans wide behind, FM 808, low wobble answer, acid squelch line, fast bass triplets, open hat, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, low chest-sub, low-mid bass melody, driving sub pulse run, snare answers, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, low-mid orbit widens, tempo push, octave 808 stack, mono chest-sub, wavy low-mid line, offbeat push, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, panning bass layer, low chest-sub, low reese counterline, acid squelch line, staccato sub bursts, straight hats, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, beat stutter, accelerating hats, layered sub stack, mono chest-sub, body bass answer, triplet hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, parallel low-mid layer, low chest-sub, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, rolling hats, rising energy, wide stereo layer, mono chest-sub, chest-sub melody, distorted sub figure, ghost notes, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, kick stomp, accelerating hats, octave 808 stack, low chest-sub, low-mid bass melody, granular bass figure, dry hats, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `271` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 2 | `[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising energy, low chest-sub, side snare, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, distorted sub figure, double-time bass gallop, rolling hats, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, stutter gate, tempo push, low chest-sub, late snare, 2 bars]

[inst - chest-sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, laser electric stacked warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, staccato sub bursts, syncopated hats, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, mono chest-sub, fast bass triplets, open hat, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run, rising energy, low chest-sub, closed hat, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, downbeat kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, octave 808 stack, laser electric wreck wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, rolling 808 run, tight kick, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, kick tightens, kick run, rising energy, mono chest-sub, body bass answer, distorted sub figure, loose hats, 2 bars]

[inst - chest-sub, panning low-mid sweep, low chest-sub, low wobble answer, fast bass triplets, pushed snare, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, wobble FM voice, double-time bass gallop, chopped hats, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, kick tightens, kick run, rising energy, low chest-sub, low-mid bass melody, phase-wavy synth line, hat density up, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, phase-charged wreck warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, rolling 808 run, kick opens, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, stutter gate, tempo push, low chest-sub, low reese counterline, acid squelch line, kick tightens, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged heavy reese drop, response line, double-time feel, mono chest-sub, body bass answer, neuro wobble lead, fast bass triplets, snare answers, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, low wobble answer, double-time bass gallop, offbeat push, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, phase-charged full send wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, distorted sub figure, driving sub pulse run, straight hats, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick run, rising energy, octave 808 stack, low chest-sub, low-mid bass melody, granular bass figure, triplet hats, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, downbeat kick, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, stutter gate, tempo push, layered sub stack, low chest-sub, low reese counterline, ghost notes, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder reese drop, response line, double-time feel, mono chest-sub, body bass answer, double-time bass gallop, dry hats, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, sub pickup, accelerating hats, wide stereo layer, low chest-sub, low wobble answer, acid squelch line, wide hat bed, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 1 | `[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising...` |
| 2 | `271` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising energy, low chest-sub, side snare, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, distorted sub figure, double-time bass gallop, rolling hats, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, stutter gate, tempo push, low chest-sub, late snare, 2 bars]

[inst - chest-sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, laser electric stacked warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, staccato sub bursts, syncopated hats, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, mono chest-sub, fast bass triplets, open hat, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run, rising energy, low chest-sub, closed hat, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, downbeat kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, octave 808 stack, laser electric wreck wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, rolling 808 run, tight kick, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, kick tightens, kick run, rising energy, mono chest-sub, body bass answer, distorted sub figure, loose hats, 2 bars]

[inst - chest-sub, panning low-mid sweep, low chest-sub, low wobble answer, fast bass triplets, pushed snare, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, wobble FM voice, double-time bass gallop, chopped hats, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, kick tightens, kick run, rising energy, low chest-sub, low-mid bass melody, phase-wavy synth line, hat density up, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, phase-charged wreck warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, rolling 808 run, kick opens, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, stutter gate, tempo push, low chest-sub, low reese counterline, acid squelch line, kick tightens, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged heavy reese drop, response line, double-time feel, mono chest-sub, body bass answer, neuro wobble lead, fast bass triplets, snare answers, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, low wobble answer, double-time bass gallop, offbeat push, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, phase-charged full send wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, distorted sub figure, driving sub pulse run, straight hats, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick run, rising energy, octave 808 stack, low chest-sub, low-mid bass melody, granular bass figure, triplet hats, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, downbeat kick, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, stutter gate, tempo push, layered sub stack, low chest-sub, low reese counterline, ghost notes, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder reese drop, response line, double-time feel, mono chest-sub, body bass answer, double-time bass gallop, dry hats, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, sub pickup, accelerating hats, wide stereo layer, low chest-sub, low wobble answer, acid squelch line, wide hat bed, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `271` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 5 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 5 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 5** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 2 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energy surge, tempo push, body bass, low reese counterline, early kick, 2 bars]

[drop - chest-sub, bass pans wide behind, wide stereo layer, full send laser heavy warped drop, response line, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, staccato sub bursts, syncopated hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave sub stack, chest-sub melody, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, laser electric tower wreck warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, driving sub pulse run, room snare, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, octave sub stack, wavy low-mid line, rolling 808 run, tight kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, laser electric tower heavy reese drop, second low-mid line, double-time feel, body bass, low reese counterline, distorted sub figure, staccato sub bursts, loose hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, parallel low-mid layer, rising energy, octave sub stack, body bass answer, pushed snare, 2 bars]

[drop - chest-sub, low-mid from every angle, panning bass layer, laser electric tower full send wobble drop, counter-line, double-time feel, body bass, low wobble answer, double-time bass gallop, chopped hats, 2 bars]

[inst - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - FM warp sub, low-mid from every angle, layered sub stack, laser electric tower harder wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, distorted sub figure, fast bass triplets, straight hats, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, parallel low-mid layer, rising energy, layered sub stack, FM 808, body bass answer, hat density up, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, full send laser heavy warped drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, staccato sub bursts, kick opens, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, parallel low-mid layer, rising energy, panning bass layer, octave sub stack, body bass answer, square-wave pulse figure, offbeat push, 2 bars]

[drop - chest-sub, low-mid from every angle, wide stereo layer, full send laser stacked warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, rolling 808 run, backbeat shove, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, bass melody climbs, accelerating hats, panning bass layer, FM 808, wavy low-mid line, phase-wavy synth line, offbeat push, 2 bars]

[inst - FM warp sub, wide 3D bass field, parallel low-mid layer, low chest-sub, wavy low-mid line, double-time bass gallop, triplet hats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, laser electric tower heavy reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, staccato sub bursts, triplet hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, laser electric tower full send wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, square-wave pulse figure, double-time bass gallop, ghost notes, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, parallel low-mid layer, body bass, low wobble answer, neuro wobble lead, rolling 808 run, mono kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, laser electric tower harder wobble drop, response line, double-time feel, low chest-sub, body bass answer, acid squelch line, fast bass triplets, late snare, 2 bars]

[outro - FM warp sub, panning low-mid sweep, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, rolling hats, 2 bars]
```

**ACE tags + lyrics (pass 5)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| 1 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| 2 | `271` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-sub, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energy surge, tempo push, body bass, low reese counterline, early kick, 2 bars]

[drop - chest-sub, bass pans wide behind, wide stereo layer, full send laser heavy warped drop, response line, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, staccato sub bursts, syncopated hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave sub stack, chest-sub melody, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, laser electric tower wreck warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, driving sub pulse run, room snare, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, octave sub stack, wavy low-mid line, rolling 808 run, tight kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, laser electric tower heavy reese drop, second low-mid line, double-time feel, body bass, low reese counterline, distorted sub figure, staccato sub bursts, loose hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, parallel low-mid layer, rising energy, octave sub stack, body bass answer, pushed snare, 2 bars]

[drop - chest-sub, low-mid from every angle, panning bass layer, laser electric tower full send wobble drop, counter-line, double-time feel, body bass, low wobble answer, double-time bass gallop, chopped hats, 2 bars]

[inst - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - FM warp sub, low-mid from every angle, layered sub stack, laser electric tower harder wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, distorted sub figure, fast bass triplets, straight hats, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, parallel low-mid layer, rising energy, layered sub stack, FM 808, body bass answer, hat density up, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, full send laser heavy warped drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, staccato sub bursts, kick opens, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, parallel low-mid layer, rising energy, panning bass layer, octave sub stack, body bass answer, square-wave pulse figure, offbeat push, 2 bars]

[drop - chest-sub, low-mid from every angle, wide stereo layer, full send laser stacked warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, rolling 808 run, backbeat shove, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, bass melody climbs, accelerating hats, panning bass layer, FM 808, wavy low-mid line, phase-wavy synth line, offbeat push, 2 bars]

[inst - FM warp sub, wide 3D bass field, parallel low-mid layer, low chest-sub, wavy low-mid line, double-time bass gallop, triplet hats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, laser electric tower heavy reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, staccato sub bursts, triplet hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, laser electric tower full send wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, square-wave pulse figure, double-time bass gallop, ghost notes, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, parallel low-mid layer, body bass, low wobble answer, neuro wobble lead, rolling 808 run, mono kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, laser electric tower harder wobble drop, response line, double-time feel, low chest-sub, body bass answer, acid squelch line, fast bass triplets, late snare, 2 bars]

[outro - FM warp sub, panning low-mid sweep, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, rolling hats, 2 bars]
```

**ACE sampler (pass 5)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `271` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `165` |
| 1 | `2, 1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `02-low-lane`

Catalog id `audio/albums/drive-through/hour-2/02-low-lane`.

US-safe EDM take: Drive-through low-lane riddim warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `89.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 2 | `[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bar...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/02-low-lane` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, laser-lit harder reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, trap drums denser, hat density up, wobble bass, heavy riddim drop, 2 bars]

[build-up - octave sub pulse, layers surround the ear, downbeat kick, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, layered sub stack, laser-lit wreck wobble drop, counter melody, octave sub stack, chest-sub melody, square-wave pulse figure, offbeat hats, kick tightens, chest-sub wobble, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub swell, rising energy, snare answers, warped wreck, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, wide stereo layer, laser-lit heavy warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, granular bass figure, rapid hi-hats, offbeat push, harder warped drop, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, layered sub stack, laser-lit full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, distorted sub figure, kick pattern flip, backbeat shove, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, wide 3D bass field, octave 808 stack, electric full send warped drop, low wobble answer, octave sub stack, wavy low-mid line, granular bass figure, kick pattern flip, wide hat bed, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, rapid hi-hats, dry hats, rapid hi-hats denser, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, sub swell, accelerating hats, octave sub stack, wide hat bed, wobble sustain, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, kick pattern flip, mono kick, kick tightens, 2 bars]

[drop - chest-sub, 3D low-mid orbit, layered sub stack, laser-lit wreck reese drop, response line, octave sub stack, body bass answer, offbeat hats, side snare, chest-sub 808, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, tom run, accelerating hats, body bass, rolling hats, 808 triplets, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, octave sub stack, rapid hi-hats, late snare, riddim warped hold, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, bass pressure builds, rising energy, body bass, early kick, warped sub stack, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, octave sub stack, kick pattern flip, syncopated hats, riddim wreck, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, laser-lit wreck wobble drop, second low-mid line, body bass, low reese counterline, neuro wobble lead, offbeat hats, open hat, full send drop, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - chest-sub, bass circles the low-mid, body bass, rapid hi-hats, room snare, kick holds, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, tom run, tempo push, octave sub stack, tight kick, hats denser, 2 bars]

[inst - bitcrushed 808, layers surround the ear, body bass, low-mid bass melody, kick pattern flip, loose hats, wobble ride, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick only on downbeats, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, body bass, low reese counterline, warped FM lead, ghost snare, chopped hats, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, laser-lit heavy reese drop, response line, octave sub stack, body bass answer, rapid hi-hats, hat density up, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, side snare, accelerating hats, body bass, low wobble answer, neuro wobble lead, kick opens, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, octave sub stack, chest-sub melody, square-wave pulse figure, kick pattern flip, kick tightens, 2 bars]

[drop - wavy phase sub, low-mid from every angle, layered sub stack, laser-lit wreck reese drop, counter-lead answers, body bass, low-mid bass melody, distorted sub figure, offbeat hats, snare answers, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick tightens, sub pickup, tempo push, body bass, low reese counterline, wobble FM voice, straight hats, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 1 | `[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bar...` |
| 2 | `277` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, laser-lit harder reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, trap drums denser, hat density up, wobble bass, heavy riddim drop, 2 bars]

[build-up - octave sub pulse, layers surround the ear, downbeat kick, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, layered sub stack, laser-lit wreck wobble drop, counter melody, octave sub stack, chest-sub melody, square-wave pulse figure, offbeat hats, kick tightens, chest-sub wobble, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub swell, rising energy, snare answers, warped wreck, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, wide stereo layer, laser-lit heavy warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, granular bass figure, rapid hi-hats, offbeat push, harder warped drop, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, layered sub stack, laser-lit full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, distorted sub figure, kick pattern flip, backbeat shove, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, wide 3D bass field, octave 808 stack, electric full send warped drop, low wobble answer, octave sub stack, wavy low-mid line, granular bass figure, kick pattern flip, wide hat bed, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, rapid hi-hats, dry hats, rapid hi-hats denser, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, sub swell, accelerating hats, octave sub stack, wide hat bed, wobble sustain, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, kick pattern flip, mono kick, kick tightens, 2 bars]

[drop - chest-sub, 3D low-mid orbit, layered sub stack, laser-lit wreck reese drop, response line, octave sub stack, body bass answer, offbeat hats, side snare, chest-sub 808, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, tom run, accelerating hats, body bass, rolling hats, 808 triplets, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, octave sub stack, rapid hi-hats, late snare, riddim warped hold, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, bass pressure builds, rising energy, body bass, early kick, warped sub stack, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, octave sub stack, kick pattern flip, syncopated hats, riddim wreck, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, laser-lit wreck wobble drop, second low-mid line, body bass, low reese counterline, neuro wobble lead, offbeat hats, open hat, full send drop, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - chest-sub, bass circles the low-mid, body bass, rapid hi-hats, room snare, kick holds, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, tom run, tempo push, octave sub stack, tight kick, hats denser, 2 bars]

[inst - bitcrushed 808, layers surround the ear, body bass, low-mid bass melody, kick pattern flip, loose hats, wobble ride, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick only on downbeats, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, body bass, low reese counterline, warped FM lead, ghost snare, chopped hats, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, laser-lit heavy reese drop, response line, octave sub stack, body bass answer, rapid hi-hats, hat density up, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, side snare, accelerating hats, body bass, low wobble answer, neuro wobble lead, kick opens, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, octave sub stack, chest-sub melody, square-wave pulse figure, kick pattern flip, kick tightens, 2 bars]

[drop - wavy phase sub, low-mid from every angle, layered sub stack, laser-lit wreck reese drop, counter-lead answers, body bass, low-mid bass melody, distorted sub figure, offbeat hats, snare answers, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick tightens, sub pickup, tempo push, body bass, low reese counterline, wobble FM voice, straight hats, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `277` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `02 - Low Lane` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `02 - Low Lane` |
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
| 1 | `Hour 2` |
| 2 | `Low Lane` |
| 3 | `2` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `02 - Low Lane` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 2 | `[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 b...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/02-low-lane` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, phase-charged stacked reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, wobble FM voice, rolling 808 run, kick opens, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, kick run, tempo push, body bass, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, phase-charged harder wobble drop, counter-line, double-time feel, octave sub stack, low wobble answer, fast bass triplets, snare answers, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, stutter gate, accelerating hats, body bass, offbeat push, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, wide stereo layer, laser electric stacked wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, rolling 808 run, triplet hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, stutter gate, accelerating hats, octave sub stack, backbeat shove, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, panning bass layer, laser electric harder warped drop, response line, double-time feel, body bass, body bass answer, fast bass triplets, ghost notes, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, octave 808 stack, rising energy, octave sub stack, low wobble answer, dry hats, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, parallel low-mid layer, laser electric wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, phase-wavy synth line, driving sub pulse run, wide hat bed, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick only on downbeats, 2 bars]

[inst - octave sub pulse, layers surround the ear, body bass, wavy low-mid line, acid squelch line, staccato sub bursts, side snare, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, phase-charged harder reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, neuro wobble lead, fast bass triplets, rolling hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, parallel low-mid layer, phase-charged wreck wobble drop, counter-line, double-time feel, octave sub stack, low wobble answer, distorted sub figure, driving sub pulse run, early kick, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, stutter gate, accelerating hats, body bass, chest-sub melody, syncopated hats, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, octave sub stack, low-mid bass melody, wobble FM voice, staccato sub bursts, open hat, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, laser electric harder wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, phase-wavy synth line, fast bass triplets, closed hat, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, stutter gate, accelerating hats, octave sub stack, low reese counterline, room snare, 2 bars]

[drop - FM warp sub, bass circles the low-mid, parallel low-mid layer, laser electric wreck warped drop, response line, double-time feel, body bass, body bass answer, driving sub pulse run, tight kick, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, octave sub stack, low wobble answer, rolling 808 run, loose hats, 2 bars]

[drop - phase-distorted sub, layers surround the ear, octave 808 stack, laser electric heavy reese drop, counter melody, double-time feel, body bass, chest-sub melody, square-wave pulse figure, staccato sub bursts, pushed snare, 2 bars]

[inst - chest-sub, 3D low-mid orbit, panning bass layer, octave sub stack, low-mid bass melody, distorted sub figure, fast bass triplets, chopped hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, layered sub stack, laser electric full send wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, double-time bass gallop, hat density up, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, stutter gate, accelerating hats, parallel low-mid layer, octave sub stack, low reese counterline, kick opens, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, wide stereo layer, laser electric stacked warped drop, response line, double-time feel, body bass, body bass answer, rolling 808 run, kick tightens, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, laser electric harder reese drop, counter melody, double-time feel, body bass, chest-sub melody, acid squelch line, fast bass triplets, offbeat push, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, downbeat impact, rising energy, parallel low-mid layer, body bass, wavy low-mid line, square-wave pulse figure, triplet hats, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 1 | `[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 b...` |
| 2 | `277` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, phase-charged stacked reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, wobble FM voice, rolling 808 run, kick opens, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, kick run, tempo push, body bass, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, phase-charged harder wobble drop, counter-line, double-time feel, octave sub stack, low wobble answer, fast bass triplets, snare answers, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, stutter gate, accelerating hats, body bass, offbeat push, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, wide stereo layer, laser electric stacked wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, rolling 808 run, triplet hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, stutter gate, accelerating hats, octave sub stack, backbeat shove, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, panning bass layer, laser electric harder warped drop, response line, double-time feel, body bass, body bass answer, fast bass triplets, ghost notes, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, octave 808 stack, rising energy, octave sub stack, low wobble answer, dry hats, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, parallel low-mid layer, laser electric wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, phase-wavy synth line, driving sub pulse run, wide hat bed, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick only on downbeats, 2 bars]

[inst - octave sub pulse, layers surround the ear, body bass, wavy low-mid line, acid squelch line, staccato sub bursts, side snare, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, phase-charged harder reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, neuro wobble lead, fast bass triplets, rolling hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, parallel low-mid layer, phase-charged wreck wobble drop, counter-line, double-time feel, octave sub stack, low wobble answer, distorted sub figure, driving sub pulse run, early kick, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, stutter gate, accelerating hats, body bass, chest-sub melody, syncopated hats, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, octave sub stack, low-mid bass melody, wobble FM voice, staccato sub bursts, open hat, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, laser electric harder wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, phase-wavy synth line, fast bass triplets, closed hat, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, stutter gate, accelerating hats, octave sub stack, low reese counterline, room snare, 2 bars]

[drop - FM warp sub, bass circles the low-mid, parallel low-mid layer, laser electric wreck warped drop, response line, double-time feel, body bass, body bass answer, driving sub pulse run, tight kick, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, octave sub stack, low wobble answer, rolling 808 run, loose hats, 2 bars]

[drop - phase-distorted sub, layers surround the ear, octave 808 stack, laser electric heavy reese drop, counter melody, double-time feel, body bass, chest-sub melody, square-wave pulse figure, staccato sub bursts, pushed snare, 2 bars]

[inst - chest-sub, 3D low-mid orbit, panning bass layer, octave sub stack, low-mid bass melody, distorted sub figure, fast bass triplets, chopped hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, layered sub stack, laser electric full send wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, double-time bass gallop, hat density up, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, stutter gate, accelerating hats, parallel low-mid layer, octave sub stack, low reese counterline, kick opens, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, wide stereo layer, laser electric stacked warped drop, response line, double-time feel, body bass, body bass answer, rolling 808 run, kick tightens, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, laser electric harder reese drop, counter melody, double-time feel, body bass, chest-sub melody, acid squelch line, fast bass triplets, offbeat push, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, downbeat impact, rising energy, parallel low-mid layer, body bass, wavy low-mid line, square-wave pulse figure, triplet hats, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `277` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 2 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, ki...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/02-low-lane` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, kick run, tempo push, body bass, kick opens, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, panning bass layer, laser electric harder wobble drop, counter-line, double-time feel, stacked 808, low wobble answer, acid squelch line, rolling 808 run, snare answers, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, body bass, double-time bass gallop, snare answers, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, phase-charged full send wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[inst - chest-sub, bass pans wide behind, body bass, rolling 808 run, straight hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, FM 808, rolling 808 run, ghost notes, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, wide laser stacked warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, double-time bass gallop, ghost notes, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, parallel low-mid layer, wide laser harder reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, rolling 808 run, wide hat bed, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - chest-sub, low-mid from every angle, octave sub stack, body bass answer, fast bass triplets, side snare, 2 bars]

[build-up - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, stacked 808, low wobble answer, granular bass figure, fast bass triplets, early kick, 2 bars]

[drop - octave sub pulse, bass pans wide behind, parallel low-mid layer, multi-stack harder wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, phase-wavy synth line, rolling 808 run, early kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, octave 808 stack, multi-stack wreck warped drop, second low-mid line, double-time feel, body bass, low reese counterline, acid squelch line, fast bass triplets, open hat, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, mono chest-sub, low wobble answer, square-wave pulse figure, rolling 808 run, open hat, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, phase-charged wreck warped drop, response line, double-time feel, FM 808, body bass answer, neuro wobble lead, fast bass triplets, tight kick, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, body bass, low reese counterline, chopped hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, mono chest-sub, low wobble answer, fast bass triplets, chopped hats, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, laser electric harder warped drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, granular bass figure, rolling 808 run, chopped hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, rolling hats, tempo push, FM 808, wavy low-mid line, hat density up, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser electric wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, neuro wobble lead, fast bass triplets, hat density up, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, low-mid orbit widens, accelerating hats, parallel low-mid layer, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick opens, 2 bars]

[drop - FM warp sub, panning low-mid sweep, wide stereo layer, laser electric heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, driving sub pulse run, kick tightens, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, layered sub stack, stacked 808, low-mid bass melody, square-wave pulse figure, straight hats, 2 bars]

[drop - chest-sub, layers surround the ear, parallel low-mid layer, phase-charged wreck wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, distorted sub figure, fast bass triplets, triplet hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, sub pickup, tempo push, wide stereo layer, body bass, low wobble answer, phase-wavy synth line, backbeat shove, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 1 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, ki...` |
| 2 | `277` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, kick run, tempo push, body bass, kick opens, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, panning bass layer, laser electric harder wobble drop, counter-line, double-time feel, stacked 808, low wobble answer, acid squelch line, rolling 808 run, snare answers, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, body bass, double-time bass gallop, snare answers, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, phase-charged full send wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[inst - chest-sub, bass pans wide behind, body bass, rolling 808 run, straight hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, FM 808, rolling 808 run, ghost notes, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, wide laser stacked warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, double-time bass gallop, ghost notes, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, parallel low-mid layer, wide laser harder reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, rolling 808 run, wide hat bed, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - chest-sub, low-mid from every angle, octave sub stack, body bass answer, fast bass triplets, side snare, 2 bars]

[build-up - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, stacked 808, low wobble answer, granular bass figure, fast bass triplets, early kick, 2 bars]

[drop - octave sub pulse, bass pans wide behind, parallel low-mid layer, multi-stack harder wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, phase-wavy synth line, rolling 808 run, early kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, octave 808 stack, multi-stack wreck warped drop, second low-mid line, double-time feel, body bass, low reese counterline, acid squelch line, fast bass triplets, open hat, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, mono chest-sub, low wobble answer, square-wave pulse figure, rolling 808 run, open hat, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, phase-charged wreck warped drop, response line, double-time feel, FM 808, body bass answer, neuro wobble lead, fast bass triplets, tight kick, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, body bass, low reese counterline, chopped hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, mono chest-sub, low wobble answer, fast bass triplets, chopped hats, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, laser electric harder warped drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, granular bass figure, rolling 808 run, chopped hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, rolling hats, tempo push, FM 808, wavy low-mid line, hat density up, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser electric wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, neuro wobble lead, fast bass triplets, hat density up, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, low-mid orbit widens, accelerating hats, parallel low-mid layer, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick opens, 2 bars]

[drop - FM warp sub, panning low-mid sweep, wide stereo layer, laser electric heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, driving sub pulse run, kick tightens, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, layered sub stack, stacked 808, low-mid bass melody, square-wave pulse figure, straight hats, 2 bars]

[drop - chest-sub, layers surround the ear, parallel low-mid layer, phase-charged wreck wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, distorted sub figure, fast bass triplets, triplet hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, sub pickup, tempo push, wide stereo layer, body bass, low wobble answer, phase-wavy synth line, backbeat shove, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `277` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 2 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wi...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/02-low-lane` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wide stereo layer, accelerating hats, low chest-sub, body bass answer, kick opens, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, panning bass layer, octave-stacked electric heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, fast bass triplets, straight hats, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser electric tower wreck wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, distorted sub figure, rolling 808 run, triplet hats, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - chest-sub, layers surround the ear, layered sub stack, laser electric tower heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, octave 808 stack, laser electric tower full send warped drop, response line, double-time feel, FM 808, body bass answer, phase-wavy synth line, driving sub pulse run, straight hats, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, octave sub stack, chest-sub melody, fast bass triplets, straight hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, low-mid climbs, tempo push, mono chest-sub, low wobble answer, wobble FM voice, ghost notes, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, layered sub stack, FM 808, body bass answer, granular bass figure, staccato sub bursts, mono kick, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, bass melody climbs, rising energy, parallel low-mid layer, body bass, low reese counterline, distorted sub figure, ghost notes, 2 bars]

[inst - chest-sub, bass pans wide behind, wide stereo layer, FM 808, chest-sub melody, phase-wavy synth line, double-time bass gallop, rolling hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, parallel low-mid layer, tempo push, wide stereo layer, octave sub stack, wavy low-mid line, acid squelch line, rolling hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, wide stereo layer, full send laser full send reese drop, response line, double-time feel, low chest-sub, body bass answer, square-wave pulse figure, driving sub pulse run, rolling hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, low-mid climbs, tempo push, octave 808 stack, mono chest-sub, low wobble answer, late snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, full send laser harder wobble drop, counter-line, double-time feel, stacked 808, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, FM 808, chest-sub melody, granular bass figure, driving sub pulse run, room snare, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, laser electric tower stacked reese drop, counter-line, double-time feel, body bass, low wobble answer, staccato sub bursts, pushed snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, parallel low-mid layer, stacked 808, low reese counterline, warped FM lead, fast bass triplets, pushed snare, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, laser electric tower harder warped drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, double-time bass gallop, chopped hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, low-mid climbs, tempo push, octave 808 stack, stacked 808, low wobble answer, hat density up, 2 bars]

[outro - neuro wobble sub, bass circles the low-mid, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, hat density up, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| 1 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wi...` |
| 2 | `277` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wide stereo layer, accelerating hats, low chest-sub, body bass answer, kick opens, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, panning bass layer, octave-stacked electric heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, fast bass triplets, straight hats, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser electric tower wreck wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, distorted sub figure, rolling 808 run, triplet hats, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - chest-sub, layers surround the ear, layered sub stack, laser electric tower heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, octave 808 stack, laser electric tower full send warped drop, response line, double-time feel, FM 808, body bass answer, phase-wavy synth line, driving sub pulse run, straight hats, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, octave sub stack, chest-sub melody, fast bass triplets, straight hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, low-mid climbs, tempo push, mono chest-sub, low wobble answer, wobble FM voice, ghost notes, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, layered sub stack, FM 808, body bass answer, granular bass figure, staccato sub bursts, mono kick, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, bass melody climbs, rising energy, parallel low-mid layer, body bass, low reese counterline, distorted sub figure, ghost notes, 2 bars]

[inst - chest-sub, bass pans wide behind, wide stereo layer, FM 808, chest-sub melody, phase-wavy synth line, double-time bass gallop, rolling hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, parallel low-mid layer, tempo push, wide stereo layer, octave sub stack, wavy low-mid line, acid squelch line, rolling hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, wide stereo layer, full send laser full send reese drop, response line, double-time feel, low chest-sub, body bass answer, square-wave pulse figure, driving sub pulse run, rolling hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, low-mid climbs, tempo push, octave 808 stack, mono chest-sub, low wobble answer, late snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, full send laser harder wobble drop, counter-line, double-time feel, stacked 808, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, FM 808, chest-sub melody, granular bass figure, driving sub pulse run, room snare, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, laser electric tower stacked reese drop, counter-line, double-time feel, body bass, low wobble answer, staccato sub bursts, pushed snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, parallel low-mid layer, stacked 808, low reese counterline, warped FM lead, fast bass triplets, pushed snare, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, laser electric tower harder warped drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, double-time bass gallop, chopped hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, low-mid climbs, tempo push, octave 808 stack, stacked 808, low wobble answer, hat density up, 2 bars]

[outro - neuro wobble sub, bass circles the low-mid, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, hat density up, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `277` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `03-warm-merge`

Catalog id `audio/albums/drive-through/hour-2/03-warm-merge`.

US-safe EDM take: Drive-through warm-merge wave bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 2 | `[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, su...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/03-warm-merge` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, sub energy lifts, rising energy, side snare, warped 808 wreck, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, stacked warped drop, double-time feel, low chest-sub, wavy low-mid line, rapid hi-hats, rolling hats, wave bass, heavy wave drop, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, offbeat push, tempo push, late snare, fold grind, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, kick pattern flip, early kick, rapid hi-hats roll, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, layered sub stack, full send warped drop, mono chest-sub, low wobble answer, square-wave pulse figure, offbeat hats, syncopated hats, wave 808 hold merge, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, ghost snare, tempo push, open hat, stacked wave bass, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, stacked reese drop, mono chest-sub, low-mid bass melody, rapid hi-hats, closed hat, harder warped drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub energy lifts, accelerating hats, room snare, chest-sub 808, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, offbeat push, rising energy, loose hats, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, wreck warped drop, mono chest-sub, low wobble answer, acid squelch line, ghost snare, pushed snare, 808 slide, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, heavy reese drop, mono chest-sub, low-mid bass melody, square-wave pulse figure, trap drums denser, hat density up, full send drop, 2 bars]

[inst - FM warp sub, bass circles the low-mid, low chest-sub, kick pattern flip, kick opens, low 808 wall, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, full send wobble drop, mono chest-sub, low reese counterline, offbeat hats, kick tightens, warped fold, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, ghost snare, snare answers, kick holds, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, stacked warped drop, double-time feel, mono chest-sub, low wobble answer, rapid hi-hats, offbeat push, wave ride, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, low chest-sub, trap drums denser, straight hats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, harder reese drop, double-time feel, mono chest-sub, low-mid bass melody, acid squelch line, kick pattern flip, triplet hats, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, ghost snare, accelerating hats, low chest-sub, backbeat shove, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, sub energy lifts, rising energy, low chest-sub, dry hats, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, mono chest-sub, wide hat bed, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 1 | `[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, su...` |
| 2 | `281` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, sub energy lifts, rising energy, side snare, warped 808 wreck, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, stacked warped drop, double-time feel, low chest-sub, wavy low-mid line, rapid hi-hats, rolling hats, wave bass, heavy wave drop, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, offbeat push, tempo push, late snare, fold grind, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, kick pattern flip, early kick, rapid hi-hats roll, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, layered sub stack, full send warped drop, mono chest-sub, low wobble answer, square-wave pulse figure, offbeat hats, syncopated hats, wave 808 hold merge, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, ghost snare, tempo push, open hat, stacked wave bass, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, stacked reese drop, mono chest-sub, low-mid bass melody, rapid hi-hats, closed hat, harder warped drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub energy lifts, accelerating hats, room snare, chest-sub 808, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, offbeat push, rising energy, loose hats, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, wreck warped drop, mono chest-sub, low wobble answer, acid squelch line, ghost snare, pushed snare, 808 slide, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, heavy reese drop, mono chest-sub, low-mid bass melody, square-wave pulse figure, trap drums denser, hat density up, full send drop, 2 bars]

[inst - FM warp sub, bass circles the low-mid, low chest-sub, kick pattern flip, kick opens, low 808 wall, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, full send wobble drop, mono chest-sub, low reese counterline, offbeat hats, kick tightens, warped fold, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, ghost snare, snare answers, kick holds, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, stacked warped drop, double-time feel, mono chest-sub, low wobble answer, rapid hi-hats, offbeat push, wave ride, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, low chest-sub, trap drums denser, straight hats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, harder reese drop, double-time feel, mono chest-sub, low-mid bass melody, acid squelch line, kick pattern flip, triplet hats, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick tightens, ghost snare, accelerating hats, low chest-sub, backbeat shove, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, sub energy lifts, rising energy, low chest-sub, dry hats, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, mono chest-sub, wide hat bed, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `281` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `03 - Warm Merge` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `03 - Warm Merge` |
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
| 1 | `Hour 2` |
| 2 | `Warm Merge` |
| 3 | `3` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `03 - Warm Merge` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 2 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stut...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/03-warm-merge` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stutter gate, rising energy, mono chest-sub, rolling hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, wide laser heavy wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, granular bass figure, staccato sub bursts, late snare, 2 bars]

[inst - FM warp sub, wide 3D bass field, mono chest-sub, fast bass triplets, early kick, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, octave 808 stack, wide laser full send warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, double-time bass gallop, syncopated hats, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - chest-sub, layers surround the ear, low chest-sub, rolling 808 run, closed hat, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, multi-stack heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, staccato sub bursts, room snare, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, low chest-sub, chest-sub melody, fast bass triplets, tight kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, multi-stack full send reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, loose hats, 2 bars]

[inst - FM warp sub, panning low-mid sweep, low chest-sub, wavy low-mid line, driving sub pulse run, pushed snare, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, multi-stack stacked wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, wobble FM voice, rolling 808 run, chopped hats, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, low chest-sub, body bass answer, phase-wavy synth line, staccato sub bursts, hat density up, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, stutter gate, rising energy, mono chest-sub, low wobble answer, warped FM lead, kick opens, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, multi-stack wreck reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, snare answers, 2 bars]

[inst - octave sub pulse, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, multi-stack heavy wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, staccato sub bursts, straight hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, wide stereo layer, low chest-sub, body bass answer, fast bass triplets, triplet hats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, octave 808 stack, multi-stack full send warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - chest-sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, layered sub stack, mono chest-sub, low-mid bass melody, warped FM lead, rolling 808 run, dry hats, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, wide laser heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, acid squelch line, staccato sub bursts, wide hat bed, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, wide stereo layer, mono chest-sub, low reese counterline, mono kick, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 1 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stut...` |
| 2 | `281` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stutter gate, rising energy, mono chest-sub, rolling hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, wide laser heavy wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, granular bass figure, staccato sub bursts, late snare, 2 bars]

[inst - FM warp sub, wide 3D bass field, mono chest-sub, fast bass triplets, early kick, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, octave 808 stack, wide laser full send warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, double-time bass gallop, syncopated hats, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - chest-sub, layers surround the ear, low chest-sub, rolling 808 run, closed hat, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, multi-stack heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, staccato sub bursts, room snare, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, low chest-sub, chest-sub melody, fast bass triplets, tight kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, multi-stack full send reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, loose hats, 2 bars]

[inst - FM warp sub, panning low-mid sweep, low chest-sub, wavy low-mid line, driving sub pulse run, pushed snare, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, multi-stack stacked wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, wobble FM voice, rolling 808 run, chopped hats, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, low chest-sub, body bass answer, phase-wavy synth line, staccato sub bursts, hat density up, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, stutter gate, rising energy, mono chest-sub, low wobble answer, warped FM lead, kick opens, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, multi-stack wreck reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, snare answers, 2 bars]

[inst - octave sub pulse, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, multi-stack heavy wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, staccato sub bursts, straight hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, wide stereo layer, low chest-sub, body bass answer, fast bass triplets, triplet hats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, octave 808 stack, multi-stack full send warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - chest-sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, layered sub stack, mono chest-sub, low-mid bass melody, warped FM lead, rolling 808 run, dry hats, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, wide laser heavy warped drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, acid squelch line, staccato sub bursts, wide hat bed, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, wide stereo layer, mono chest-sub, low reese counterline, mono kick, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `281` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 2 | `[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats,...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/03-warm-merge` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats, tempo push, stacked 808, syncopated hats, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, wide stereo layer, phase-charged full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, staccato sub bursts, open hat, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, closed hat, 2 bars]

[inst - chest-sub, bass pans wide behind, FM 808, double-time bass gallop, room snare, 2 bars]

[drop - wavy phase sub, layers surround the ear, layered sub stack, laser electric heavy warped drop, counter-line, double-time feel, stacked 808, low wobble answer, driving sub pulse run, tight kick, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, low-mid orbit widens, accelerating hats, FM 808, loose hats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, wide stereo layer, laser electric full send reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, distorted sub figure, staccato sub bursts, pushed snare, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, FM 808, wavy low-mid line, granular bass figure, fast bass triplets, chopped hats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, panning bass layer, laser electric stacked wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, double-time bass gallop, hat density up, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, rolling hats, tempo push, FM 808, body bass answer, phase-wavy synth line, kick opens, 2 bars]

[drop - chest-sub, low-mid from every angle, parallel low-mid layer, laser electric harder warped drop, counter-line, double-time feel, stacked 808, low wobble answer, rolling 808 run, kick tightens, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, stacked 808, low-mid bass melody, neuro wobble lead, fast bass triplets, offbeat push, 2 bars]

[drop - octave sub pulse, bass pans wide behind, panning bass layer, phase-charged stacked warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, double-time bass gallop, straight hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, low reese counterline, distorted sub figure, triplet hats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, phase-charged harder reese drop, response line, double-time feel, FM 808, body bass answer, rolling 808 run, backbeat shove, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, phase-charged wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, fast bass triplets, dry hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, downbeat kick, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, layered sub stack, FM 808, wavy low-mid line, acid squelch line, driving sub pulse run, mono kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, laser electric harder wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, neuro wobble lead, rolling 808 run, side snare, 2 bars]

[build-up - FM warp sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, sub pickup, rising energy, octave 808 stack, stacked 808, low wobble answer, distorted sub figure, late snare, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 1 | `[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats,...` |
| 2 | `281` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats, tempo push, stacked 808, syncopated hats, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, wide stereo layer, phase-charged full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, staccato sub bursts, open hat, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, closed hat, 2 bars]

[inst - chest-sub, bass pans wide behind, FM 808, double-time bass gallop, room snare, 2 bars]

[drop - wavy phase sub, layers surround the ear, layered sub stack, laser electric heavy warped drop, counter-line, double-time feel, stacked 808, low wobble answer, driving sub pulse run, tight kick, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, low-mid orbit widens, accelerating hats, FM 808, loose hats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, wide stereo layer, laser electric full send reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, distorted sub figure, staccato sub bursts, pushed snare, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, FM 808, wavy low-mid line, granular bass figure, fast bass triplets, chopped hats, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, panning bass layer, laser electric stacked wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, double-time bass gallop, hat density up, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, rolling hats, tempo push, FM 808, body bass answer, phase-wavy synth line, kick opens, 2 bars]

[drop - chest-sub, low-mid from every angle, parallel low-mid layer, laser electric harder warped drop, counter-line, double-time feel, stacked 808, low wobble answer, rolling 808 run, kick tightens, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, stacked 808, low-mid bass melody, neuro wobble lead, fast bass triplets, offbeat push, 2 bars]

[drop - octave sub pulse, bass pans wide behind, panning bass layer, phase-charged stacked warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, double-time bass gallop, straight hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, low reese counterline, distorted sub figure, triplet hats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, phase-charged harder reese drop, response line, double-time feel, FM 808, body bass answer, rolling 808 run, backbeat shove, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, phase-charged wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, fast bass triplets, dry hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, downbeat kick, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, layered sub stack, FM 808, wavy low-mid line, acid squelch line, driving sub pulse run, mono kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, laser electric harder wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, neuro wobble lead, rolling 808 run, side snare, 2 bars]

[build-up - FM warp sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, sub pickup, rising energy, octave 808 stack, stacked 808, low wobble answer, distorted sub figure, late snare, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `281` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 2 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climb...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/03-warm-merge` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climbs, accelerating hats, FM 808, wavy low-mid line, early kick, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, panning bass layer, full send laser full send wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, wobble FM voice, driving sub pulse run, syncopated hats, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, downbeat sub pulse, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, stacked 808, low wobble answer, staccato sub bursts, closed hat, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, energy surge, tempo push, FM 808, chest-sub melody, room snare, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, octave 808 stack, full send laser harder reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, neuro wobble lead, double-time bass gallop, tight kick, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - chest-sub, bass pans wide behind, layered sub stack, full send laser wreck wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, distorted sub figure, rolling 808 run, pushed snare, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, panning bass layer, laser electric tower harder reese drop, second low-mid line, double-time feel, body bass, low reese counterline, double-time bass gallop, kick tightens, 2 bars]

[inst - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, parallel low-mid layer, laser electric tower wreck wobble drop, counter-line, double-time feel, body bass, low wobble answer, rolling 808 run, offbeat push, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, parallel low-mid layer, mono chest-sub, low-mid bass melody, double-time bass gallop, offbeat push, 2 bars]

[drop - chest-sub, bass pans wide behind, octave 808 stack, laser electric tower heavy warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, fast bass triplets, triplet hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, bass melody climbs, accelerating hats, panning bass layer, octave sub stack, wavy low-mid line, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, max stack laser heavy warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, fast bass triplets, dry hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, parallel low-mid layer, rising energy, parallel low-mid layer, octave sub stack, body bass answer, dry hats, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, wide stereo layer, body bass, low wobble answer, distorted sub figure, staccato sub bursts, wide hat bed, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, octave 808 stack, full send laser heavy reese drop, counter melody, double-time feel, octave sub stack, chest-sub melody, fast bass triplets, mono kick, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, octave 808 stack, low chest-sub, wavy low-mid line, phase-wavy synth line, rolling 808 run, mono kick, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, octave 808 stack, laser electric tower harder reese drop, response line, double-time feel, FM 808, body bass answer, double-time bass gallop, mono kick, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[outro - octave sub pulse, bass pans wide behind, kick pattern flip, rapid hi-hats, body bass, low wobble answer, syncopated hats, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| 1 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climb...` |
| 2 | `281` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climbs, accelerating hats, FM 808, wavy low-mid line, early kick, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, panning bass layer, full send laser full send wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, wobble FM voice, driving sub pulse run, syncopated hats, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, downbeat sub pulse, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, stacked 808, low wobble answer, staccato sub bursts, closed hat, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, energy surge, tempo push, FM 808, chest-sub melody, room snare, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, octave 808 stack, full send laser harder reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, neuro wobble lead, double-time bass gallop, tight kick, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - chest-sub, bass pans wide behind, layered sub stack, full send laser wreck wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, distorted sub figure, rolling 808 run, pushed snare, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, panning bass layer, laser electric tower harder reese drop, second low-mid line, double-time feel, body bass, low reese counterline, double-time bass gallop, kick tightens, 2 bars]

[inst - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, parallel low-mid layer, laser electric tower wreck wobble drop, counter-line, double-time feel, body bass, low wobble answer, rolling 808 run, offbeat push, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, parallel low-mid layer, mono chest-sub, low-mid bass melody, double-time bass gallop, offbeat push, 2 bars]

[drop - chest-sub, bass pans wide behind, octave 808 stack, laser electric tower heavy warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, fast bass triplets, triplet hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, bass melody climbs, accelerating hats, panning bass layer, octave sub stack, wavy low-mid line, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, max stack laser heavy warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, fast bass triplets, dry hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, parallel low-mid layer, rising energy, parallel low-mid layer, octave sub stack, body bass answer, dry hats, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, wide stereo layer, body bass, low wobble answer, distorted sub figure, staccato sub bursts, wide hat bed, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, octave 808 stack, full send laser heavy reese drop, counter melody, double-time feel, octave sub stack, chest-sub melody, fast bass triplets, mono kick, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, octave 808 stack, low chest-sub, wavy low-mid line, phase-wavy synth line, rolling 808 run, mono kick, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, octave 808 stack, laser electric tower harder reese drop, response line, double-time feel, FM 808, body bass answer, double-time bass gallop, mono kick, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[outro - octave sub pulse, bass pans wide behind, kick pattern flip, rapid hi-hats, body bass, low wobble answer, syncopated hats, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `281` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `04-colour-span`

Catalog id `audio/albums/drive-through/hour-2/04-colour-span`.

US-safe EDM take: Drive-through colour-span color bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 2 | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens,...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/04-colour-span` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens, accelerating hats, backbeat shove, chest-sub 808 warp, 2 bars]

[drop - FM warp sub, bass circles the low-mid, layered sub stack, wreck wobble drop, FM 808, chest-sub melody, square-wave pulse figure, kick pattern flip, ghost notes, color bass, heavy color drop, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick only on downbeats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, ghost snare, wide hat bed, analog 808 stack, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, ghost snare, tempo push, mono kick, warped color, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, panning bass layer, full send reese drop, double-time feel, FM 808, body bass answer, trap drums denser, side snare, harder warped drop, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, sub energy lifts, accelerating hats, rolling hats, rapid hi-hats denser, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, offbeat hats, late snare, color 808 sustain span, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, wide stereo layer, heavy reese drop, stacked 808, low-mid bass melody, neuro wobble lead, ghost snare, early kick, full send drop, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, rapid hi-hats, syncopated hats, stacked color wreck, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, full send wobble drop, double-time feel, stacked 808, low reese counterline, trap drums denser, open hat, warped sub, 2 bars]

[inst - chest-sub, bass circles the low-mid, kick pattern flip, closed hat, kick holds, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, stacked warped drop, stacked 808, low wobble answer, offbeat hats, room snare, hats denser, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, sub energy lifts, tempo push, FM 808, tight kick, color ride, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, panning bass layer, full send warped drop, FM 808, wavy low-mid line, acid squelch line, trap drums denser, pushed snare, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, stacked reese drop, double-time feel, FM 808, body bass answer, square-wave pulse figure, offbeat hats, hat density up, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, stacked 808, ghost snare, kick opens, 2 bars]

[drop - wavy phase sub, low-mid from every angle, octave 808 stack, harder wobble drop, double-time feel, FM 808, chest-sub melody, granular bass figure, rapid hi-hats, kick tightens, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts, rising energy, stacked 808, snare answers, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, wreck warped drop, double-time feel, FM 808, wavy low-mid line, kick pattern flip, offbeat push, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, downbeat impact, tempo push, stacked 808, straight hats, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 1 | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens,...` |
| 2 | `283` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens, accelerating hats, backbeat shove, chest-sub 808 warp, 2 bars]

[drop - FM warp sub, bass circles the low-mid, layered sub stack, wreck wobble drop, FM 808, chest-sub melody, square-wave pulse figure, kick pattern flip, ghost notes, color bass, heavy color drop, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick only on downbeats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, ghost snare, wide hat bed, analog 808 stack, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, ghost snare, tempo push, mono kick, warped color, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, panning bass layer, full send reese drop, double-time feel, FM 808, body bass answer, trap drums denser, side snare, harder warped drop, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, sub energy lifts, accelerating hats, rolling hats, rapid hi-hats denser, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, offbeat hats, late snare, color 808 sustain span, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, wide stereo layer, heavy reese drop, stacked 808, low-mid bass melody, neuro wobble lead, ghost snare, early kick, full send drop, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, rapid hi-hats, syncopated hats, stacked color wreck, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, full send wobble drop, double-time feel, stacked 808, low reese counterline, trap drums denser, open hat, warped sub, 2 bars]

[inst - chest-sub, bass circles the low-mid, kick pattern flip, closed hat, kick holds, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, stacked warped drop, stacked 808, low wobble answer, offbeat hats, room snare, hats denser, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, sub energy lifts, tempo push, FM 808, tight kick, color ride, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, panning bass layer, full send warped drop, FM 808, wavy low-mid line, acid squelch line, trap drums denser, pushed snare, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, stacked reese drop, double-time feel, FM 808, body bass answer, square-wave pulse figure, offbeat hats, hat density up, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, stacked 808, ghost snare, kick opens, 2 bars]

[drop - wavy phase sub, low-mid from every angle, octave 808 stack, harder wobble drop, double-time feel, FM 808, chest-sub melody, granular bass figure, rapid hi-hats, kick tightens, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts, rising energy, stacked 808, snare answers, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, wreck warped drop, double-time feel, FM 808, wavy low-mid line, kick pattern flip, offbeat push, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, downbeat impact, tempo push, stacked 808, straight hats, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `283` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `04 - Colour Span` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `04 - Colour Span` |
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
| 1 | `Hour 2` |
| 2 | `Colour Span` |
| 3 | `4` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `04 - Colour Span` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 2 | `[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo pus...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/04-colour-span` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo push, ghost notes, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, electric harder reese drop, response line, double-time feel, body bass, body bass answer, trap drums denser, dry hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - octave sub pulse, layers surround the ear, parallel low-mid layer, electric wreck wobble drop, counter melody, double-time feel, body bass, chest-sub melody, neuro wobble lead, offbeat hats, mono kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, layered sub stack, electric full send warped drop, low wobble answer, body bass, wavy low-mid line, warped FM lead, kick pattern flip, kick opens, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, electric stacked reese drop, response line, double-time feel, body bass, body bass answer, neuro wobble lead, ghost snare, snare answers, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, electric full send reese drop, response line, body bass, body bass answer, wobble FM voice, kick pattern flip, early kick, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, accelerating hats, octave sub stack, syncopated hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, layered sub stack, electric full send reese drop, counter-lead answers, octave sub stack, low-mid bass melody, granular bass figure, kick pattern flip, triplet hats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, electric heavy reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, rapid hi-hats, closed hat, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, trap drums denser, room snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, octave 808 stack, electric heavy reese drop, response line, body bass, body bass answer, rapid hi-hats, dry hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, offbeat hats, loose hats, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, side snare, accelerating hats, octave sub stack, pushed snare, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, body bass, rapid hi-hats, chopped hats, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, wavy low-mid line, warped FM lead, kick pattern flip, kick opens, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, bass pressure builds, tempo push, octave sub stack, low reese counterline, acid squelch line, kick tightens, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, body bass, body bass answer, neuro wobble lead, ghost snare, snare answers, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, sub swell, accelerating hats, octave sub stack, low wobble answer, square-wave pulse figure, offbeat push, 2 bars]

[inst - chest-sub, bass circles the low-mid, body bass, chest-sub melody, distorted sub figure, trap drums denser, straight hats, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, downbeat impact, rising energy, octave sub stack, low-mid bass melody, triplet hats, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 1 | `[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo pus...` |
| 2 | `283` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo push, ghost notes, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, electric harder reese drop, response line, double-time feel, body bass, body bass answer, trap drums denser, dry hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - octave sub pulse, layers surround the ear, parallel low-mid layer, electric wreck wobble drop, counter melody, double-time feel, body bass, chest-sub melody, neuro wobble lead, offbeat hats, mono kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, layered sub stack, electric full send warped drop, low wobble answer, body bass, wavy low-mid line, warped FM lead, kick pattern flip, kick opens, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, electric stacked reese drop, response line, double-time feel, body bass, body bass answer, neuro wobble lead, ghost snare, snare answers, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, electric full send reese drop, response line, body bass, body bass answer, wobble FM voice, kick pattern flip, early kick, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, accelerating hats, octave sub stack, syncopated hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, layered sub stack, electric full send reese drop, counter-lead answers, octave sub stack, low-mid bass melody, granular bass figure, kick pattern flip, triplet hats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, electric heavy reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, rapid hi-hats, closed hat, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, trap drums denser, room snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, octave 808 stack, electric heavy reese drop, response line, body bass, body bass answer, rapid hi-hats, dry hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, offbeat hats, loose hats, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, side snare, accelerating hats, octave sub stack, pushed snare, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, body bass, rapid hi-hats, chopped hats, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, wavy low-mid line, warped FM lead, kick pattern flip, kick opens, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, bass pressure builds, tempo push, octave sub stack, low reese counterline, acid squelch line, kick tightens, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, body bass, body bass answer, neuro wobble lead, ghost snare, snare answers, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, sub swell, accelerating hats, octave sub stack, low wobble answer, square-wave pulse figure, offbeat push, 2 bars]

[inst - chest-sub, bass circles the low-mid, body bass, chest-sub melody, distorted sub figure, trap drums denser, straight hats, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, downbeat impact, rising energy, octave sub stack, low-mid bass melody, triplet hats, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `283` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 2 | `[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/04-colour-span` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising energy, mono kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, laser-lit wreck wobble drop, counter melody, mono chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, offbeat hats, late snare, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, laser-lit harder wobble drop, second low-mid line, low chest-sub, low reese counterline, ghost snare, early kick, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, layered sub stack, laser-lit wreck warped drop, counter-line, low chest-sub, low wobble answer, phase-wavy synth line, trap drums denser, open hat, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, mono chest-sub, kick pattern flip, closed hat, 2 bars]

[drop - chest-sub, layers surround the ear, wide stereo layer, electric full send reese drop, low wobble answer, body bass, wavy low-mid line, rapid hi-hats, wide hat bed, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, panning bass layer, laser-lit full send wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, rapid hi-hats, loose hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, gated bass, tempo push, mono chest-sub, pushed snare, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, low chest-sub, kick pattern flip, chopped hats, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, laser-lit heavy wobble drop, counter melody, mono chest-sub, chest-sub melody, offbeat hats, hat density up, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, sub swell, tempo push, low chest-sub, kick opens, 2 bars]

[inst - octave sub pulse, low-mid from every angle, mono chest-sub, rapid hi-hats, kick tightens, 2 bars]

[drop - FM warp sub, wide 3D bass field, layered sub stack, laser-lit wreck wobble drop, second low-mid line, low chest-sub, low reese counterline, acid squelch line, trap drums denser, snare answers, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, mono chest-sub, body bass answer, kick pattern flip, offbeat push, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, laser-lit heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, offbeat hats, straight hats, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, bass pressure builds, accelerating hats, mono chest-sub, chest-sub melody, distorted sub figure, triplet hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, low chest-sub, low-mid bass melody, rapid hi-hats, backbeat shove, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser-lit wreck warped drop, low wobble answer, mono chest-sub, wavy low-mid line, wobble FM voice, trap drums denser, ghost notes, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, kick stomp, accelerating hats, low chest-sub, low reese counterline, dry hats, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 1 | `[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising ...` |
| 2 | `283` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising energy, mono kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, laser-lit wreck wobble drop, counter melody, mono chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, offbeat hats, late snare, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, laser-lit harder wobble drop, second low-mid line, low chest-sub, low reese counterline, ghost snare, early kick, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, layered sub stack, laser-lit wreck warped drop, counter-line, low chest-sub, low wobble answer, phase-wavy synth line, trap drums denser, open hat, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, mono chest-sub, kick pattern flip, closed hat, 2 bars]

[drop - chest-sub, layers surround the ear, wide stereo layer, electric full send reese drop, low wobble answer, body bass, wavy low-mid line, rapid hi-hats, wide hat bed, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, panning bass layer, laser-lit full send wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, rapid hi-hats, loose hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, gated bass, tempo push, mono chest-sub, pushed snare, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, low chest-sub, kick pattern flip, chopped hats, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, laser-lit heavy wobble drop, counter melody, mono chest-sub, chest-sub melody, offbeat hats, hat density up, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, sub swell, tempo push, low chest-sub, kick opens, 2 bars]

[inst - octave sub pulse, low-mid from every angle, mono chest-sub, rapid hi-hats, kick tightens, 2 bars]

[drop - FM warp sub, wide 3D bass field, layered sub stack, laser-lit wreck wobble drop, second low-mid line, low chest-sub, low reese counterline, acid squelch line, trap drums denser, snare answers, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, mono chest-sub, body bass answer, kick pattern flip, offbeat push, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, laser-lit heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, offbeat hats, straight hats, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, bass pressure builds, accelerating hats, mono chest-sub, chest-sub melody, distorted sub figure, triplet hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, low chest-sub, low-mid bass melody, rapid hi-hats, backbeat shove, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser-lit wreck warped drop, low wobble answer, mono chest-sub, wavy low-mid line, wobble FM voice, trap drums denser, ghost notes, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, kick stomp, accelerating hats, low chest-sub, low reese counterline, dry hats, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `283` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 2 | `[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel lo...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/04-colour-span` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel low-mid layer, tempo push, octave sub stack, low wobble answer, warped FM lead, wide hat bed, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, max stack laser wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, staccato sub bursts, mono kick, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, energy surge, accelerating hats, octave sub stack, low-mid bass melody, neuro wobble lead, side snare, 2 bars]

[inst - wavy phase sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, max stack laser full send wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, neuro wobble lead, rolling 808 run, syncopated hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, parallel low-mid layer, tempo push, mono chest-sub, wavy low-mid line, open hat, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, layered sub stack, max stack laser stacked warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, fast bass triplets, closed hat, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, FM 808, low wobble answer, wobble FM voice, rolling 808 run, closed hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, octave-stacked electric heavy warped drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, warped FM lead, double-time bass gallop, closed hat, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, octave-stacked electric stacked warped drop, counter-line, double-time feel, FM 808, low wobble answer, wobble FM voice, fast bass triplets, hat density up, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, max stack laser heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, double-time bass gallop, hat density up, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, wide stereo layer, mono chest-sub, body bass answer, square-wave pulse figure, driving sub pulse run, kick opens, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, kick doubles, rising energy, wide stereo layer, stacked 808, chest-sub melody, kick opens, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, max stack laser full send wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, rolling 808 run, kick opens, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, bass melody climbs, rising energy, octave 808 stack, octave sub stack, low reese counterline, warped FM lead, kick tightens, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, panning bass layer, body bass, body bass answer, fast bass triplets, snare answers, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, max stack laser harder warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, driving sub pulse run, triplet hats, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, energy surge, accelerating hats, octave 808 stack, mono chest-sub, body bass answer, backbeat shove, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, panning bass layer, low chest-sub, low wobble answer, neuro wobble lead, staccato sub bursts, ghost notes, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, full send laser harder reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, distorted sub figure, driving sub pulse run, ghost notes, 2 bars]

[outro - chest-sub, wide 3D bass field, kick pattern flip, rapid hi-hats, body bass, body bass answer, dry hats, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| 1 | `[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel lo...` |
| 2 | `283` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel low-mid layer, tempo push, octave sub stack, low wobble answer, warped FM lead, wide hat bed, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, max stack laser wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, staccato sub bursts, mono kick, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, energy surge, accelerating hats, octave sub stack, low-mid bass melody, neuro wobble lead, side snare, 2 bars]

[inst - wavy phase sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, max stack laser full send wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, neuro wobble lead, rolling 808 run, syncopated hats, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, parallel low-mid layer, tempo push, mono chest-sub, wavy low-mid line, open hat, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, layered sub stack, max stack laser stacked warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, fast bass triplets, closed hat, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, FM 808, low wobble answer, wobble FM voice, rolling 808 run, closed hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, octave-stacked electric heavy warped drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, warped FM lead, double-time bass gallop, closed hat, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, octave-stacked electric stacked warped drop, counter-line, double-time feel, FM 808, low wobble answer, wobble FM voice, fast bass triplets, hat density up, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, max stack laser heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, double-time bass gallop, hat density up, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, wide stereo layer, mono chest-sub, body bass answer, square-wave pulse figure, driving sub pulse run, kick opens, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, kick doubles, rising energy, wide stereo layer, stacked 808, chest-sub melody, kick opens, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, max stack laser full send wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, rolling 808 run, kick opens, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, bass melody climbs, rising energy, octave 808 stack, octave sub stack, low reese counterline, warped FM lead, kick tightens, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, panning bass layer, body bass, body bass answer, fast bass triplets, snare answers, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, max stack laser harder warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, driving sub pulse run, triplet hats, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, energy surge, accelerating hats, octave 808 stack, mono chest-sub, body bass answer, backbeat shove, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, panning bass layer, low chest-sub, low wobble answer, neuro wobble lead, staccato sub bursts, ghost notes, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, full send laser harder reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, distorted sub figure, driving sub pulse run, ghost notes, 2 bars]

[outro - chest-sub, wide 3D bass field, kick pattern flip, rapid hi-hats, body bass, body bass answer, dry hats, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `283` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `05-garage-ticket`

Catalog id `audio/albums/drive-through/hour-2/05-garage-ticket`.

US-safe EDM take: Drive-through garage-ticket festival trap warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `67.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hat...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/05-garage-ticket` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hats, tempo push, loose hats, warped 808 wreck, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, laser-lit heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, ghost snare, pushed snare, festival trap, heavy trap drop, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, gated bass, accelerating hats, chopped hats, chest-sub stamp, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, laser-lit full send warped drop, response line, double-time feel, mono chest-sub, body bass answer, phase-wavy synth line, trap drums denser, hat density up, rapid hi-hats roll, 2 bars]

[inst - FM warp sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, laser-lit stacked reese drop, counter melody, mono chest-sub, chest-sub melody, acid squelch line, offbeat hats, kick tightens, 808 slide, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, side snare, tempo push, low chest-sub, snare answers, stacked trap bass, 2 bars]

[drop - chest-sub, wide 3D bass field, layered sub stack, laser-lit harder wobble drop, low wobble answer, mono chest-sub, wavy low-mid line, square-wave pulse figure, rapid hi-hats, offbeat push, harder warped drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, tom run, accelerating hats, low chest-sub, straight hats, chest warp, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, mono chest-sub, kick pattern flip, triplet hats, kick tightens, 2 bars]

[drop - octave sub pulse, layers surround the ear, octave 808 stack, laser-lit stacked wobble drop, counter-line, low chest-sub, low wobble answer, offbeat hats, backbeat shove, chest-sub 808 punch, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, downbeat kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, layered sub stack, laser-lit harder warped drop, counter-lead answers, low chest-sub, low-mid bass melody, warped FM lead, rapid hi-hats, dry hats, full send drop, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - chest-sub, panning low-mid sweep, wide stereo layer, laser-lit wreck reese drop, second low-mid line, low chest-sub, low reese counterline, neuro wobble lead, kick pattern flip, mono kick, chest-sub 808 wall, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, tom run, tempo push, mono chest-sub, side snare, warped trap, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, laser-lit heavy wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, ghost snare, rolling hats, kick holds, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, mono chest-sub, chest-sub melody, late snare, 808 ride, 2 bars]

[drop - FM warp sub, bass circles the low-mid, parallel low-mid layer, laser-lit full send warped drop, counter-lead answers, low chest-sub, low-mid bass melody, trap drums denser, early kick, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, low reese counterline, warped FM lead, offbeat hats, open hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, panning bass layer, laser-lit heavy warped drop, response line, mono chest-sub, body bass answer, ghost snare, closed hat, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, sub pickup, rising energy, low chest-sub, low wobble answer, neuro wobble lead, room snare, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 1 | `[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hat...` |
| 2 | `293` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hats, tempo push, loose hats, warped 808 wreck, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, laser-lit heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, ghost snare, pushed snare, festival trap, heavy trap drop, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, gated bass, accelerating hats, chopped hats, chest-sub stamp, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, laser-lit full send warped drop, response line, double-time feel, mono chest-sub, body bass answer, phase-wavy synth line, trap drums denser, hat density up, rapid hi-hats roll, 2 bars]

[inst - FM warp sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, laser-lit stacked reese drop, counter melody, mono chest-sub, chest-sub melody, acid squelch line, offbeat hats, kick tightens, 808 slide, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, side snare, tempo push, low chest-sub, snare answers, stacked trap bass, 2 bars]

[drop - chest-sub, wide 3D bass field, layered sub stack, laser-lit harder wobble drop, low wobble answer, mono chest-sub, wavy low-mid line, square-wave pulse figure, rapid hi-hats, offbeat push, harder warped drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, tom run, accelerating hats, low chest-sub, straight hats, chest warp, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, mono chest-sub, kick pattern flip, triplet hats, kick tightens, 2 bars]

[drop - octave sub pulse, layers surround the ear, octave 808 stack, laser-lit stacked wobble drop, counter-line, low chest-sub, low wobble answer, offbeat hats, backbeat shove, chest-sub 808 punch, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, downbeat kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, layered sub stack, laser-lit harder warped drop, counter-lead answers, low chest-sub, low-mid bass melody, warped FM lead, rapid hi-hats, dry hats, full send drop, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - chest-sub, panning low-mid sweep, wide stereo layer, laser-lit wreck reese drop, second low-mid line, low chest-sub, low reese counterline, neuro wobble lead, kick pattern flip, mono kick, chest-sub 808 wall, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, tom run, tempo push, mono chest-sub, side snare, warped trap, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, laser-lit heavy wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, ghost snare, rolling hats, kick holds, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, mono chest-sub, chest-sub melody, late snare, 808 ride, 2 bars]

[drop - FM warp sub, bass circles the low-mid, parallel low-mid layer, laser-lit full send warped drop, counter-lead answers, low chest-sub, low-mid bass melody, trap drums denser, early kick, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, low reese counterline, warped FM lead, offbeat hats, open hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, panning bass layer, laser-lit heavy warped drop, response line, mono chest-sub, body bass answer, ghost snare, closed hat, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, sub pickup, rising energy, low chest-sub, low wobble answer, neuro wobble lead, room snare, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `293` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `05 - Garage Ticket` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `05 - Garage Ticket` |
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
| 1 | `Hour 2` |
| 2 | `Garage Ticket` |
| 3 | `5` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `05 - Garage Ticket` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 2 | `[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bar...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/05-garage-ticket` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, octave 808 stack, laser electric harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, chopped hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, octave 808 stack, tempo push, low chest-sub, hat density up, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric wreck warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, distorted sub figure, rolling 808 run, kick opens, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, mono chest-sub, fast bass triplets, snare answers, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, phase-charged harder warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, double-time bass gallop, offbeat push, 2 bars]

[build-up - FM warp sub, wide 3D bass field, downbeat kick, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, low chest-sub, wavy low-mid line, rolling 808 run, triplet hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, parallel low-mid layer, laser electric stacked warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, staccato sub bursts, backbeat shove, 2 bars]

[inst - chest-sub, layers surround the ear, low chest-sub, body bass answer, fast bass triplets, ghost notes, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, laser electric harder reese drop, counter-line, double-time feel, mono chest-sub, low wobble answer, double-time bass gallop, dry hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, mono chest-sub, low-mid bass melody, rolling 808 run, mono kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, parallel low-mid layer, phase-charged stacked reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, phase-wavy synth line, staccato sub bursts, side snare, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, low chest-sub, body bass answer, acid squelch line, double-time bass gallop, late snare, 2 bars]

[drop - chest-sub, wide 3D bass field, panning bass layer, laser electric full send reese drop, counter-line, double-time feel, mono chest-sub, low wobble answer, neuro wobble lead, driving sub pulse run, early kick, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, parallel low-mid layer, laser electric stacked wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, staccato sub bursts, open hat, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, octave 808 stack, mono chest-sub, low reese counterline, wobble FM voice, double-time bass gallop, room snare, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub pickup, accelerating hats, panning bass layer, low chest-sub, body bass answer, phase-wavy synth line, tight kick, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 1 | `[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bar...` |
| 2 | `293` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, octave 808 stack, laser electric harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, chopped hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, octave 808 stack, tempo push, low chest-sub, hat density up, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric wreck warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, distorted sub figure, rolling 808 run, kick opens, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, mono chest-sub, fast bass triplets, snare answers, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, phase-charged harder warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, double-time bass gallop, offbeat push, 2 bars]

[build-up - FM warp sub, wide 3D bass field, downbeat kick, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, low chest-sub, wavy low-mid line, rolling 808 run, triplet hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, parallel low-mid layer, laser electric stacked warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, staccato sub bursts, backbeat shove, 2 bars]

[inst - chest-sub, layers surround the ear, low chest-sub, body bass answer, fast bass triplets, ghost notes, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, laser electric harder reese drop, counter-line, double-time feel, mono chest-sub, low wobble answer, double-time bass gallop, dry hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, mono chest-sub, low-mid bass melody, rolling 808 run, mono kick, 2 bars]

[drop - FM warp sub, panning low-mid sweep, parallel low-mid layer, phase-charged stacked reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, phase-wavy synth line, staccato sub bursts, side snare, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, low chest-sub, body bass answer, acid squelch line, double-time bass gallop, late snare, 2 bars]

[drop - chest-sub, wide 3D bass field, panning bass layer, laser electric full send reese drop, counter-line, double-time feel, mono chest-sub, low wobble answer, neuro wobble lead, driving sub pulse run, early kick, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, parallel low-mid layer, laser electric stacked wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, staccato sub bursts, open hat, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, octave 808 stack, mono chest-sub, low reese counterline, wobble FM voice, double-time bass gallop, room snare, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub pickup, accelerating hats, panning bass layer, low chest-sub, body bass answer, phase-wavy synth line, tight kick, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `293` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 2 | `[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo l...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/05-garage-ticket` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo layer, accelerating hats, body bass, wavy low-mid line, distorted sub figure, kick opens, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, laser electric tower wreck warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, double-time bass gallop, kick tightens, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, parallel low-mid layer, laser electric tower heavy reese drop, counter-line, double-time feel, octave sub stack, low wobble answer, phase-wavy synth line, rolling 808 run, offbeat push, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, body bass, chest-sub melody, warped FM lead, staccato sub bursts, straight hats, 2 bars]

[drop - FM warp sub, low-mid from every angle, octave 808 stack, laser electric tower full send wobble drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, fast bass triplets, triplet hats, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, octave sub stack, low reese counterline, driving sub pulse run, ghost notes, 2 bars]

[drop - chest-sub, bass pans wide behind, parallel low-mid layer, full send laser heavy wobble drop, response line, double-time feel, body bass, body bass answer, distorted sub figure, rolling 808 run, dry hats, 2 bars]

[inst - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, low-mid climbs, tempo push, octave 808 stack, body bass, chest-sub melody, wobble FM voice, mono kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, laser electric tower wreck wobble drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, phase-wavy synth line, double-time bass gallop, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, wide stereo layer, accelerating hats, layered sub stack, body bass, wavy low-mid line, warped FM lead, rolling hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, downbeat kick, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, full send laser harder wobble drop, response line, double-time feel, body bass, body bass answer, neuro wobble lead, staccato sub bursts, early kick, 2 bars]

[inst - chest-sub, low-mid from every angle, octave 808 stack, octave sub stack, low wobble answer, fast bass triplets, syncopated hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, full send laser wreck warped drop, counter melody, double-time feel, body bass, chest-sub melody, double-time bass gallop, open hat, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, downbeat kick, 2 bars]

[inst - octave sub pulse, bass pans wide behind, parallel low-mid layer, body bass, wavy low-mid line, rolling 808 run, room snare, 2 bars]

[drop - FM warp sub, layers surround the ear, wide stereo layer, laser electric tower harder warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, phase-wavy synth line, staccato sub bursts, tight kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, octave 808 stack, body bass, body bass answer, warped FM lead, fast bass triplets, loose hats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, panning bass layer, laser electric tower wreck reese drop, counter-line, double-time feel, octave sub stack, low wobble answer, acid squelch line, double-time bass gallop, pushed snare, 2 bars]

[outro - chest-sub, layers surround the ear, kick pattern flip, rapid hi-hats, FM 808, low reese counterline, pushed snare, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| 1 | `[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo l...` |
| 2 | `293` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo layer, accelerating hats, body bass, wavy low-mid line, distorted sub figure, kick opens, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, laser electric tower wreck warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, double-time bass gallop, kick tightens, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, parallel low-mid layer, laser electric tower heavy reese drop, counter-line, double-time feel, octave sub stack, low wobble answer, phase-wavy synth line, rolling 808 run, offbeat push, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, body bass, chest-sub melody, warped FM lead, staccato sub bursts, straight hats, 2 bars]

[drop - FM warp sub, low-mid from every angle, octave 808 stack, laser electric tower full send wobble drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, fast bass triplets, triplet hats, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, octave sub stack, low reese counterline, driving sub pulse run, ghost notes, 2 bars]

[drop - chest-sub, bass pans wide behind, parallel low-mid layer, full send laser heavy wobble drop, response line, double-time feel, body bass, body bass answer, distorted sub figure, rolling 808 run, dry hats, 2 bars]

[inst - wavy phase sub, layers surround the ear, downbeat kick, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, low-mid climbs, tempo push, octave 808 stack, body bass, chest-sub melody, wobble FM voice, mono kick, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, laser electric tower wreck wobble drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, phase-wavy synth line, double-time bass gallop, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, wide stereo layer, accelerating hats, layered sub stack, body bass, wavy low-mid line, warped FM lead, rolling hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, downbeat kick, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, full send laser harder wobble drop, response line, double-time feel, body bass, body bass answer, neuro wobble lead, staccato sub bursts, early kick, 2 bars]

[inst - chest-sub, low-mid from every angle, octave 808 stack, octave sub stack, low wobble answer, fast bass triplets, syncopated hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, full send laser wreck warped drop, counter melody, double-time feel, body bass, chest-sub melody, double-time bass gallop, open hat, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, downbeat kick, 2 bars]

[inst - octave sub pulse, bass pans wide behind, parallel low-mid layer, body bass, wavy low-mid line, rolling 808 run, room snare, 2 bars]

[drop - FM warp sub, layers surround the ear, wide stereo layer, laser electric tower harder warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, phase-wavy synth line, staccato sub bursts, tight kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, octave 808 stack, body bass, body bass answer, warped FM lead, fast bass triplets, loose hats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, panning bass layer, laser electric tower wreck reese drop, counter-line, double-time feel, octave sub stack, low wobble answer, acid squelch line, double-time bass gallop, pushed snare, 2 bars]

[outro - chest-sub, layers surround the ear, kick pattern flip, rapid hi-hats, FM 808, low reese counterline, pushed snare, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `293` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `165` |
| 1 | `2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `06-liquid-grade`

Catalog id `audio/albums/drive-through/hour-2/06-liquid-grade`.

US-safe EDM take: Drive-through liquid-grade drumstep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `63.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 2 | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack t...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/06-liquid-grade` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack tightens, rising energy, open hat, reese wreck, 2 bars]

[drop - wavy phase sub, wide 3D bass field, octave 808 stack, heavy warped drop, double-time feel, low chest-sub, wavy low-mid line, ghost snare, closed hat, amen break, heavy drumstep drop, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, rapid hi-hats, room snare, warped amen, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, full send reese drop, low chest-sub, body bass answer, trap drums denser, tight kick, amen break, 2 bars]

[inst - FM warp sub, layers surround the ear, kick pattern flip, loose hats, rapid hi-hats 808 liquid, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, wide stereo layer, stacked wobble drop, low chest-sub, chest-sub melody, offbeat hats, pushed snare, harder reese drop, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, ghost snare, rising energy, chopped hats, reese stack, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, rapid hi-hats, hat density up, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, layered sub stack, full send wobble drop, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, trap drums denser, kick opens, hats denser, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, stacked warped drop, mono chest-sub, low wobble answer, distorted sub figure, offbeat hats, snare answers, reese hold, 2 bars]

[inst - FM warp sub, wide 3D bass field, ghost snare, offbeat push, stacked amen wreck, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, panning bass layer, harder reese drop, mono chest-sub, low-mid bass melody, rapid hi-hats, straight hats, full send drop, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, low chest-sub, trap drums denser, triplet hats, warped 808 punch, 2 bars]

[build-up - chest-sub, layers surround the ear, downbeat sub pulse, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, low chest-sub, offbeat hats, ghost notes, chest-sub 808 wreck, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, octave 808 stack, heavy warped drop, double-time feel, mono chest-sub, low wobble answer, ghost snare, dry hats, harder warped drop, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, offbeat push, tempo push, low chest-sub, wide hat bed, drumstep grind, 2 bars]

[inst - FM warp sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, wreck warped drop, low chest-sub, wavy low-mid line, kick pattern flip, side snare, kick holds, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - chest-sub, wide 3D bass field, octave 808 stack, heavy reese drop, low chest-sub, body bass answer, phase-wavy synth line, ghost snare, late snare, reese ride, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, downbeat impact, accelerating hats, mono chest-sub, early kick, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 1 | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack t...` |
| 2 | `307` |
| 3 | `fixed` |
| 4 | `176` |
| 5 | `63.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack tightens, rising energy, open hat, reese wreck, 2 bars]

[drop - wavy phase sub, wide 3D bass field, octave 808 stack, heavy warped drop, double-time feel, low chest-sub, wavy low-mid line, ghost snare, closed hat, amen break, heavy drumstep drop, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, rapid hi-hats, room snare, warped amen, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, full send reese drop, low chest-sub, body bass answer, trap drums denser, tight kick, amen break, 2 bars]

[inst - FM warp sub, layers surround the ear, kick pattern flip, loose hats, rapid hi-hats 808 liquid, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, wide stereo layer, stacked wobble drop, low chest-sub, chest-sub melody, offbeat hats, pushed snare, harder reese drop, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, ghost snare, rising energy, chopped hats, reese stack, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, rapid hi-hats, hat density up, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, layered sub stack, full send wobble drop, double-time feel, mono chest-sub, low reese counterline, neuro wobble lead, trap drums denser, kick opens, hats denser, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, stacked warped drop, mono chest-sub, low wobble answer, distorted sub figure, offbeat hats, snare answers, reese hold, 2 bars]

[inst - FM warp sub, wide 3D bass field, ghost snare, offbeat push, stacked amen wreck, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, panning bass layer, harder reese drop, mono chest-sub, low-mid bass melody, rapid hi-hats, straight hats, full send drop, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, low chest-sub, trap drums denser, triplet hats, warped 808 punch, 2 bars]

[build-up - chest-sub, layers surround the ear, downbeat sub pulse, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, low chest-sub, offbeat hats, ghost notes, chest-sub 808 wreck, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, octave 808 stack, heavy warped drop, double-time feel, mono chest-sub, low wobble answer, ghost snare, dry hats, harder warped drop, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, kick tightens, offbeat push, tempo push, low chest-sub, wide hat bed, drumstep grind, 2 bars]

[inst - FM warp sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, wreck warped drop, low chest-sub, wavy low-mid line, kick pattern flip, side snare, kick holds, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - chest-sub, wide 3D bass field, octave 808 stack, heavy reese drop, low chest-sub, body bass answer, phase-wavy synth line, ghost snare, late snare, reese ride, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, downbeat impact, accelerating hats, mono chest-sub, early kick, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `307` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `06 - Liquid Grade` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `06 - Liquid Grade` |
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
| 1 | `Hour 2` |
| 2 | `Liquid Grade` |
| 3 | `6` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `06 - Liquid Grade` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 2 | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo p...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/06-liquid-grade` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo push, tight kick, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, electric full send reese drop, response line, double-time feel, FM 808, body bass answer, ghost snare, loose hats, 2 bars]

[inst - FM warp sub, bass pans wide behind, rapid hi-hats, pushed snare, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, electric stacked wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, trap drums denser, chopped hats, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, stacked 808, kick pattern flip, hat density up, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, electric harder warped drop, low wobble answer, FM 808, wavy low-mid line, acid squelch line, offbeat hats, kick opens, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, stacked 808, ghost snare, kick tightens, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, parallel low-mid layer, electric wreck reese drop, response line, double-time feel, FM 808, body bass answer, square-wave pulse figure, rapid hi-hats, snare answers, 2 bars]

[drop - octave sub pulse, bass pans wide behind, octave 808 stack, electric harder warped drop, second low-mid line, mono chest-sub, low reese counterline, warped FM lead, offbeat hats, offbeat push, 2 bars]

[inst - FM warp sub, low-mid from every angle, FM 808, kick pattern flip, straight hats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, layered sub stack, electric wreck reese drop, counter-line, mono chest-sub, low wobble answer, neuro wobble lead, rapid hi-hats, triplet hats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, parallel low-mid layer, electric stacked warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, square-wave pulse figure, trap drums denser, backbeat shove, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, side snare, tempo push, stacked 808, ghost notes, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, octave 808 stack, electric harder reese drop, low wobble answer, low chest-sub, wavy low-mid line, granular bass figure, offbeat hats, dry hats, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, FM 808, offbeat hats, mono kick, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, FM 808, wavy low-mid line, granular bass figure, rapid hi-hats, rolling hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, sub swell, tempo push, stacked 808, low reese counterline, wobble FM voice, late snare, 2 bars]

[inst - chest-sub, low-mid from every angle, FM 808, body bass answer, kick pattern flip, early kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, FM 808, chest-sub melody, acid squelch line, ghost snare, open hat, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, kick stomp, rising energy, stacked 808, low-mid bass melody, neuro wobble lead, closed hat, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 1 | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo p...` |
| 2 | `307` |
| 3 | `fixed` |
| 4 | `176` |
| 5 | `63.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo push, tight kick, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, electric full send reese drop, response line, double-time feel, FM 808, body bass answer, ghost snare, loose hats, 2 bars]

[inst - FM warp sub, bass pans wide behind, rapid hi-hats, pushed snare, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, electric stacked wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, trap drums denser, chopped hats, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, stacked 808, kick pattern flip, hat density up, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, electric harder warped drop, low wobble answer, FM 808, wavy low-mid line, acid squelch line, offbeat hats, kick opens, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, stacked 808, ghost snare, kick tightens, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, parallel low-mid layer, electric wreck reese drop, response line, double-time feel, FM 808, body bass answer, square-wave pulse figure, rapid hi-hats, snare answers, 2 bars]

[drop - octave sub pulse, bass pans wide behind, octave 808 stack, electric harder warped drop, second low-mid line, mono chest-sub, low reese counterline, warped FM lead, offbeat hats, offbeat push, 2 bars]

[inst - FM warp sub, low-mid from every angle, FM 808, kick pattern flip, straight hats, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, layered sub stack, electric wreck reese drop, counter-line, mono chest-sub, low wobble answer, neuro wobble lead, rapid hi-hats, triplet hats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, parallel low-mid layer, electric stacked warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, square-wave pulse figure, trap drums denser, backbeat shove, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, side snare, tempo push, stacked 808, ghost notes, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, octave 808 stack, electric harder reese drop, low wobble answer, low chest-sub, wavy low-mid line, granular bass figure, offbeat hats, dry hats, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, FM 808, offbeat hats, mono kick, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, FM 808, wavy low-mid line, granular bass figure, rapid hi-hats, rolling hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, sub swell, tempo push, stacked 808, low reese counterline, wobble FM voice, late snare, 2 bars]

[inst - chest-sub, low-mid from every angle, FM 808, body bass answer, kick pattern flip, early kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, FM 808, chest-sub melody, acid squelch line, ghost snare, open hat, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, kick stomp, rising energy, stacked 808, low-mid bass melody, neuro wobble lead, closed hat, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `307` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 2 | `[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars] ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/06-liquid-grade` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, wide stereo layer, laser-lit full send warped drop, response line, low chest-sub, body bass answer, distorted sub figure, kick pattern flip, tight kick, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, accelerating hats, rising energy, loose hats, 2 bars]

[inst - wavy phase sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, laser-lit harder reese drop, counter-line, stacked 808, low wobble answer, granular bass figure, trap drums denser, kick opens, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, stacked 808, offbeat hats, snare answers, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, panning bass layer, electric harder wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, trap drums denser, snare answers, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - chest-sub, low-mid orbits the sub, low chest-sub, rapid hi-hats, offbeat push, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, parallel low-mid layer, laser-lit harder warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, trap drums denser, straight hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - FM warp sub, bass pans wide behind, stacked 808, ghost snare, dry hats, 2 bars]

[drop - neuro wobble sub, layers surround the ear, parallel low-mid layer, laser-lit heavy reese drop, low wobble answer, FM 808, wavy low-mid line, wobble FM voice, rapid hi-hats, wide hat bed, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, gated bass, tempo push, octave sub stack, wide hat bed, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, bass pans wide behind, wide stereo layer, laser-lit full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick pattern flip, mono kick, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, tom run, rising energy, low chest-sub, wavy low-mid line, distorted sub figure, side snare, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, parallel low-mid layer, laser-lit heavy wobble drop, counter-lead answers, stacked 808, low-mid bass melody, square-wave pulse figure, rapid hi-hats, early kick, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick only on downbeats, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, stacked 808, low reese counterline, granular bass figure, kick pattern flip, open hat, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, electric heavy warped drop, counter-line, body bass, low wobble answer, phase-wavy synth line, rapid hi-hats, open hat, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, downbeat impact, tempo push, mono chest-sub, low-mid bass melody, open hat, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 1 | `[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars] ...` |
| 2 | `307` |
| 3 | `fixed` |
| 4 | `176` |
| 5 | `63.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, wide stereo layer, laser-lit full send warped drop, response line, low chest-sub, body bass answer, distorted sub figure, kick pattern flip, tight kick, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, accelerating hats, rising energy, loose hats, 2 bars]

[inst - wavy phase sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, laser-lit harder reese drop, counter-line, stacked 808, low wobble answer, granular bass figure, trap drums denser, kick opens, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, stacked 808, offbeat hats, snare answers, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, panning bass layer, electric harder wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, trap drums denser, snare answers, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - chest-sub, low-mid orbits the sub, low chest-sub, rapid hi-hats, offbeat push, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, parallel low-mid layer, laser-lit harder warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, trap drums denser, straight hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - FM warp sub, bass pans wide behind, stacked 808, ghost snare, dry hats, 2 bars]

[drop - neuro wobble sub, layers surround the ear, parallel low-mid layer, laser-lit heavy reese drop, low wobble answer, FM 808, wavy low-mid line, wobble FM voice, rapid hi-hats, wide hat bed, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, gated bass, tempo push, octave sub stack, wide hat bed, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - chest-sub, bass pans wide behind, wide stereo layer, laser-lit full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick pattern flip, mono kick, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, tom run, rising energy, low chest-sub, wavy low-mid line, distorted sub figure, side snare, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, parallel low-mid layer, laser-lit heavy wobble drop, counter-lead answers, stacked 808, low-mid bass melody, square-wave pulse figure, rapid hi-hats, early kick, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick only on downbeats, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, stacked 808, low reese counterline, granular bass figure, kick pattern flip, open hat, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, electric heavy warped drop, counter-line, body bass, low wobble answer, phase-wavy synth line, rapid hi-hats, open hat, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, downbeat impact, tempo push, mono chest-sub, low-mid bass melody, open hat, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `307` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `63.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 2 | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-m...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/06-liquid-grade` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-mid layer, rising energy, octave sub stack, chest-sub melody, wobble FM voice, pushed snare, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, laser electric tower harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, warped FM lead, staccato sub bursts, pushed snare, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, bass melody climbs, accelerating hats, FM 808, body bass answer, pushed snare, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, stacked 808, low wobble answer, square-wave pulse figure, rolling 808 run, chopped hats, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, parallel low-mid layer, rising energy, FM 808, chest-sub melody, hat density up, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, body bass, low wobble answer, square-wave pulse figure, double-time bass gallop, snare answers, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, octave 808 stack, octave-stacked electric stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, driving sub pulse run, offbeat push, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick only on downbeats, 2 bars]

[inst - chest-sub, bass circles the low-mid, panning bass layer, mono chest-sub, low reese counterline, phase-wavy synth line, double-time bass gallop, straight hats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, panning bass layer, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, acid squelch line, staccato sub bursts, straight hats, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, octave-stacked electric wreck wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, double-time bass gallop, backbeat shove, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, layers surround the ear, layered sub stack, max stack laser harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, square-wave pulse figure, staccato sub bursts, mono kick, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, energy surge, tempo push, parallel low-mid layer, octave sub stack, wavy low-mid line, side snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, parallel low-mid layer, laser electric tower heavy warped drop, response line, double-time feel, low chest-sub, body bass answer, rolling 808 run, side snare, 2 bars]

[inst - FM warp sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, body bass, low wobble answer, phase-wavy synth line, rolling 808 run, early kick, 2 bars]

[inst - wavy phase sub, bass pans wide behind, wide stereo layer, low chest-sub, body bass answer, fast bass triplets, closed hat, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, full send laser heavy warped drop, counter melody, double-time feel, FM 808, chest-sub melody, rolling 808 run, closed hat, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, wide stereo layer, octave sub stack, wavy low-mid line, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, octave 808 stack, max stack laser stacked wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, square-wave pulse figure, driving sub pulse run, room snare, 2 bars]

[outro - FM warp sub, low-mid from every angle, kick pattern flip, rapid hi-hats, stacked 808, low-mid bass melody, room snare, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| 1 | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-m...` |
| 2 | `307` |
| 3 | `fixed` |
| 4 | `176` |
| 5 | `63.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 176 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-mid layer, rising energy, octave sub stack, chest-sub melody, wobble FM voice, pushed snare, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, laser electric tower harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, warped FM lead, staccato sub bursts, pushed snare, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, bass melody climbs, accelerating hats, FM 808, body bass answer, pushed snare, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, stacked 808, low wobble answer, square-wave pulse figure, rolling 808 run, chopped hats, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, parallel low-mid layer, rising energy, FM 808, chest-sub melody, hat density up, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, body bass, low wobble answer, square-wave pulse figure, double-time bass gallop, snare answers, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, octave 808 stack, octave-stacked electric stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, driving sub pulse run, offbeat push, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick only on downbeats, 2 bars]

[inst - chest-sub, bass circles the low-mid, panning bass layer, mono chest-sub, low reese counterline, phase-wavy synth line, double-time bass gallop, straight hats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, panning bass layer, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, acid squelch line, staccato sub bursts, straight hats, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, octave-stacked electric wreck wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, double-time bass gallop, backbeat shove, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, layers surround the ear, layered sub stack, max stack laser harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, square-wave pulse figure, staccato sub bursts, mono kick, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, energy surge, tempo push, parallel low-mid layer, octave sub stack, wavy low-mid line, side snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, parallel low-mid layer, laser electric tower heavy warped drop, response line, double-time feel, low chest-sub, body bass answer, rolling 808 run, side snare, 2 bars]

[inst - FM warp sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, body bass, low wobble answer, phase-wavy synth line, rolling 808 run, early kick, 2 bars]

[inst - wavy phase sub, bass pans wide behind, wide stereo layer, low chest-sub, body bass answer, fast bass triplets, closed hat, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, wide stereo layer, full send laser heavy warped drop, counter melody, double-time feel, FM 808, chest-sub melody, rolling 808 run, closed hat, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, wide stereo layer, octave sub stack, wavy low-mid line, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, octave 808 stack, max stack laser stacked wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, square-wave pulse figure, driving sub pulse run, room snare, 2 bars]

[outro - FM warp sub, low-mid from every angle, kick pattern flip, rapid hi-hats, stacked 808, low-mid bass melody, room snare, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `307` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `176` |
| 1 | `1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `07-jump-bay`

Catalog id `audio/albums/drive-through/hour-2/07-jump-bay`.

US-safe EDM take: Drive-through jump-bay brostep warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `89.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 2 | `[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kic...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/07-jump-bay` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kick punch, tempo push, syncopated hats, growl wreck, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, heavy wobble drop, octave sub stack, wavy low-mid line, acid squelch line, kick pattern flip, open hat, brostep, heavy brostep drop, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, ghost snare, accelerating hats, closed hat, warped 808, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, full send warped drop, octave sub stack, body bass answer, square-wave pulse figure, ghost snare, room snare, rapid hi-hats roll, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, sub energy lifts, rising energy, tight kick, growl sustain, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, stacked reese drop, octave sub stack, chest-sub melody, granular bass figure, trap drums denser, loose hats, harder warped drop, 2 bars]

[inst - FM warp sub, panning low-mid sweep, kick pattern flip, pushed snare, sub crush, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, harder wobble drop, octave sub stack, wavy low-mid line, phase-wavy synth line, offbeat hats, chopped hats, chest-sub 808, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, ghost snare, hat density up, rapid hi-hats denser, 2 bars]

[build-up - chest-sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, parallel low-mid layer, stacked wobble drop, body bass, low wobble answer, neuro wobble lead, trap drums denser, kick tightens, wobble hold, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, sub energy lifts, accelerating hats, snare answers, brostep wreck, 2 bars]

[inst - octave sub pulse, layers surround the ear, offbeat hats, offbeat push, stacked growl, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, full send wobble drop, octave sub stack, wavy low-mid line, granular bass figure, ghost snare, straight hats, full send drop, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, parallel low-mid layer, stacked warped drop, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, trap drums denser, backbeat shove, kick tightens, 2 bars]

[build-up - chest-sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, octave sub stack, offbeat hats, dry hats, growl bass hold, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, full send warped drop, body bass, low-mid bass melody, neuro wobble lead, ghost snare, wide hat bed, stacked 808 wreck, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens, rising energy, octave sub stack, mono kick, chest-sub, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, trap drums denser, side snare, kick holds, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, wide stereo layer, heavy warped drop, octave sub stack, body bass answer, kick pattern flip, rolling hats, hats denser, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, offbeat hats, late snare, growl ride, 2 bars]

[drop - chest-sub, 3D low-mid orbit, panning bass layer, full send reese drop, double-time feel, octave sub stack, chest-sub melody, ghost snare, early kick, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, parallel low-mid layer, stacked wobble drop, octave sub stack, wavy low-mid line, acid squelch line, trap drums denser, open hat, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, kick pattern flip, closed hat, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, harder warped drop, octave sub stack, body bass answer, offbeat hats, room snare, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, body bass, ghost snare, tight kick, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, layered sub stack, wreck reese drop, double-time feel, octave sub stack, chest-sub melody, granular bass figure, rapid hi-hats, loose hats, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, kick stomp, tempo push, body bass, pushed snare, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 1 | `[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kic...` |
| 2 | `311` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kick punch, tempo push, syncopated hats, growl wreck, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, heavy wobble drop, octave sub stack, wavy low-mid line, acid squelch line, kick pattern flip, open hat, brostep, heavy brostep drop, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, ghost snare, accelerating hats, closed hat, warped 808, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, panning bass layer, full send warped drop, octave sub stack, body bass answer, square-wave pulse figure, ghost snare, room snare, rapid hi-hats roll, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, sub energy lifts, rising energy, tight kick, growl sustain, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, stacked reese drop, octave sub stack, chest-sub melody, granular bass figure, trap drums denser, loose hats, harder warped drop, 2 bars]

[inst - FM warp sub, panning low-mid sweep, kick pattern flip, pushed snare, sub crush, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, harder wobble drop, octave sub stack, wavy low-mid line, phase-wavy synth line, offbeat hats, chopped hats, chest-sub 808, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, ghost snare, hat density up, rapid hi-hats denser, 2 bars]

[build-up - chest-sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, parallel low-mid layer, stacked wobble drop, body bass, low wobble answer, neuro wobble lead, trap drums denser, kick tightens, wobble hold, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, sub energy lifts, accelerating hats, snare answers, brostep wreck, 2 bars]

[inst - octave sub pulse, layers surround the ear, offbeat hats, offbeat push, stacked growl, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, full send wobble drop, octave sub stack, wavy low-mid line, granular bass figure, ghost snare, straight hats, full send drop, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, parallel low-mid layer, stacked warped drop, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, trap drums denser, backbeat shove, kick tightens, 2 bars]

[build-up - chest-sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, octave sub stack, offbeat hats, dry hats, growl bass hold, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, panning bass layer, full send warped drop, body bass, low-mid bass melody, neuro wobble lead, ghost snare, wide hat bed, stacked 808 wreck, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens, rising energy, octave sub stack, mono kick, chest-sub, 2 bars]

[inst - FM warp sub, bass circles the low-mid, body bass, trap drums denser, side snare, kick holds, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, wide stereo layer, heavy warped drop, octave sub stack, body bass answer, kick pattern flip, rolling hats, hats denser, 2 bars]

[inst - phase-distorted sub, layers surround the ear, body bass, offbeat hats, late snare, growl ride, 2 bars]

[drop - chest-sub, 3D low-mid orbit, panning bass layer, full send reese drop, double-time feel, octave sub stack, chest-sub melody, ghost snare, early kick, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, parallel low-mid layer, stacked wobble drop, octave sub stack, wavy low-mid line, acid squelch line, trap drums denser, open hat, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, kick pattern flip, closed hat, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, harder warped drop, octave sub stack, body bass answer, offbeat hats, room snare, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, body bass, ghost snare, tight kick, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, layered sub stack, wreck reese drop, double-time feel, octave sub stack, chest-sub melody, granular bass figure, rapid hi-hats, loose hats, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, kick stomp, tempo push, body bass, pushed snare, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `311` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `07 - Jump Bay` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `07 - Jump Bay` |
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
| 1 | `Hour 2` |
| 2 | `Jump Bay` |
| 3 | `7` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `07 - Jump Bay` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 2 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on down...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/07-jump-bay` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, laser electric stacked reese drop, counter-line, double-time feel, stacked 808, low wobble answer, staccato sub bursts, room snare, 2 bars]

[inst - wavy phase sub, layers surround the ear, body bass, driving sub pulse run, room snare, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, wide laser wreck warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, warped FM lead, rolling 808 run, tight kick, 2 bars]

[inst - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, wide stereo layer, multi-stack harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, double-time bass gallop, hat density up, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, rolling hats, rising energy, mono chest-sub, kick opens, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, laser electric heavy reese drop, counter-line, double-time feel, stacked 808, low wobble answer, fast bass triplets, kick opens, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, kick run, rising energy, FM 808, kick tightens, 2 bars]

[inst - wavy phase sub, wide 3D bass field, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, multi-stack heavy wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, phase-wavy synth line, fast bass triplets, snare answers, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, kick run, rising energy, stacked 808, low reese counterline, straight hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, mono chest-sub, low reese counterline, phase-wavy synth line, rolling 808 run, backbeat shove, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, layered sub stack, multi-stack stacked warped drop, response line, double-time feel, low chest-sub, body bass answer, staccato sub bursts, ghost notes, 2 bars]

[inst - octave sub pulse, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, laser electric wreck wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, rolling 808 run, dry hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, rolling hats, rising energy, body bass, low reese counterline, granular bass figure, dry hats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, octave sub stack, body bass answer, wobble FM voice, driving sub pulse run, wide hat bed, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, phase-charged harder wobble drop, response line, double-time feel, FM 808, body bass answer, wobble FM voice, double-time bass gallop, side snare, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, beat stutter, accelerating hats, low chest-sub, body bass answer, wobble FM voice, late snare, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, mono chest-sub, low wobble answer, double-time bass gallop, early kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, laser electric stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, staccato sub bursts, early kick, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, stutter gate, tempo push, FM 808, wavy low-mid line, syncopated hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, multi-stack stacked warped drop, counter-line, double-time feel, body bass, low wobble answer, granular bass figure, staccato sub bursts, open hat, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, stutter gate, tempo push, parallel low-mid layer, stacked 808, low wobble answer, room snare, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave 808 stack, mono chest-sub, low wobble answer, granular bass figure, driving sub pulse run, loose hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, panning bass layer, multi-stack wreck reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, wobble FM voice, rolling 808 run, pushed snare, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, panning bass layer, FM 808, wavy low-mid line, double-time bass gallop, pushed snare, 2 bars]

[drop - FM warp sub, panning low-mid sweep, layered sub stack, laser electric full send warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, acid squelch line, driving sub pulse run, chopped hats, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick stomp, tempo push, layered sub stack, body bass, low wobble answer, chopped hats, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 1 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on down...` |
| 2 | `311` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, laser electric stacked reese drop, counter-line, double-time feel, stacked 808, low wobble answer, staccato sub bursts, room snare, 2 bars]

[inst - wavy phase sub, layers surround the ear, body bass, driving sub pulse run, room snare, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, wide laser wreck warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, warped FM lead, rolling 808 run, tight kick, 2 bars]

[inst - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, wide stereo layer, multi-stack harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, double-time bass gallop, hat density up, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, rolling hats, rising energy, mono chest-sub, kick opens, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, laser electric heavy reese drop, counter-line, double-time feel, stacked 808, low wobble answer, fast bass triplets, kick opens, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, kick run, rising energy, FM 808, kick tightens, 2 bars]

[inst - wavy phase sub, wide 3D bass field, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, multi-stack heavy wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, phase-wavy synth line, fast bass triplets, snare answers, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, kick run, rising energy, stacked 808, low reese counterline, straight hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, mono chest-sub, low reese counterline, phase-wavy synth line, rolling 808 run, backbeat shove, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, layered sub stack, multi-stack stacked warped drop, response line, double-time feel, low chest-sub, body bass answer, staccato sub bursts, ghost notes, 2 bars]

[inst - octave sub pulse, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, laser electric wreck wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, rolling 808 run, dry hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, rolling hats, rising energy, body bass, low reese counterline, granular bass figure, dry hats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, octave sub stack, body bass answer, wobble FM voice, driving sub pulse run, wide hat bed, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, panning bass layer, phase-charged harder wobble drop, response line, double-time feel, FM 808, body bass answer, wobble FM voice, double-time bass gallop, side snare, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, beat stutter, accelerating hats, low chest-sub, body bass answer, wobble FM voice, late snare, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, mono chest-sub, low wobble answer, double-time bass gallop, early kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, laser electric stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, staccato sub bursts, early kick, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, stutter gate, tempo push, FM 808, wavy low-mid line, syncopated hats, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, sparse four-on-floor kick, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, multi-stack stacked warped drop, counter-line, double-time feel, body bass, low wobble answer, granular bass figure, staccato sub bursts, open hat, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, stutter gate, tempo push, parallel low-mid layer, stacked 808, low wobble answer, room snare, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave 808 stack, mono chest-sub, low wobble answer, granular bass figure, driving sub pulse run, loose hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, panning bass layer, multi-stack wreck reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, wobble FM voice, rolling 808 run, pushed snare, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, panning bass layer, FM 808, wavy low-mid line, double-time bass gallop, pushed snare, 2 bars]

[drop - FM warp sub, panning low-mid sweep, layered sub stack, laser electric full send warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, acid squelch line, driving sub pulse run, chopped hats, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick stomp, tempo push, layered sub stack, body bass, low wobble answer, chopped hats, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `311` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `77.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `77.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 2 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tem...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/07-jump-bay` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tempo push, body bass, room snare, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, phase-charged wreck warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, acid squelch line, staccato sub bursts, loose hats, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, stutter gate, rising energy, mono chest-sub, loose hats, 2 bars]

[inst - FM warp sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - wavy phase sub, layers surround the ear, panning bass layer, laser electric harder reese drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, driving sub pulse run, chopped hats, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, kick run, accelerating hats, FM 808, kick tightens, 2 bars]

[inst - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, panning bass layer, laser electric heavy wobble drop, response line, double-time feel, FM 808, body bass answer, warped FM lead, double-time bass gallop, offbeat push, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave sub stack, chest-sub melody, staccato sub bursts, offbeat push, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, multi-stack heavy wobble drop, counter-line, double-time feel, mono chest-sub, low wobble answer, acid squelch line, double-time bass gallop, backbeat shove, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, stutter gate, rising energy, stacked 808, low-mid bass melody, square-wave pulse figure, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, multi-stack full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rolling 808 run, dry hats, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, stacked 808, low reese counterline, granular bass figure, double-time bass gallop, dry hats, 2 bars]

[drop - chest-sub, low-mid from every angle, panning bass layer, wide laser wreck warped drop, counter-line, double-time feel, body bass, low wobble answer, staccato sub bursts, dry hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, low chest-sub, wavy low-mid line, neuro wobble lead, rolling 808 run, wide hat bed, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, octave 808 stack, tempo push, mono chest-sub, low reese counterline, mono kick, 2 bars]

[inst - wavy phase sub, wide 3D bass field, FM 808, wavy low-mid line, double-time bass gallop, late snare, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, octave 808 stack, tempo push, stacked 808, low reese counterline, square-wave pulse figure, early kick, 2 bars]

[drop - octave sub pulse, bass pans wide behind, parallel low-mid layer, laser electric full send wobble drop, response line, double-time feel, FM 808, body bass answer, distorted sub figure, rolling 808 run, syncopated hats, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, beat stutter, tempo push, parallel low-mid layer, octave sub stack, chest-sub melody, wobble FM voice, syncopated hats, 2 bars]

[inst - FM warp sub, wide 3D bass field, parallel low-mid layer, low chest-sub, wavy low-mid line, staccato sub bursts, syncopated hats, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, wide stereo layer, laser electric stacked reese drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, fast bass triplets, open hat, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, stutter gate, rising energy, octave 808 stack, low chest-sub, body bass answer, neuro wobble lead, closed hat, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, parallel low-mid layer, stacked 808, low reese counterline, rolling 808 run, loose hats, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, sub pickup, rising energy, wide stereo layer, FM 808, body bass answer, neuro wobble lead, pushed snare, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 1 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tem...` |
| 2 | `311` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `77.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tempo push, body bass, room snare, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, phase-charged wreck warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, acid squelch line, staccato sub bursts, loose hats, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, stutter gate, rising energy, mono chest-sub, loose hats, 2 bars]

[inst - FM warp sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - wavy phase sub, layers surround the ear, panning bass layer, laser electric harder reese drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, driving sub pulse run, chopped hats, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, kick run, accelerating hats, FM 808, kick tightens, 2 bars]

[inst - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, panning bass layer, laser electric heavy wobble drop, response line, double-time feel, FM 808, body bass answer, warped FM lead, double-time bass gallop, offbeat push, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave sub stack, chest-sub melody, staccato sub bursts, offbeat push, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, multi-stack heavy wobble drop, counter-line, double-time feel, mono chest-sub, low wobble answer, acid squelch line, double-time bass gallop, backbeat shove, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, stutter gate, rising energy, stacked 808, low-mid bass melody, square-wave pulse figure, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, multi-stack full send warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rolling 808 run, dry hats, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, stacked 808, low reese counterline, granular bass figure, double-time bass gallop, dry hats, 2 bars]

[drop - chest-sub, low-mid from every angle, panning bass layer, wide laser wreck warped drop, counter-line, double-time feel, body bass, low wobble answer, staccato sub bursts, dry hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, low chest-sub, wavy low-mid line, neuro wobble lead, rolling 808 run, wide hat bed, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, octave 808 stack, tempo push, mono chest-sub, low reese counterline, mono kick, 2 bars]

[inst - wavy phase sub, wide 3D bass field, FM 808, wavy low-mid line, double-time bass gallop, late snare, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, octave 808 stack, tempo push, stacked 808, low reese counterline, square-wave pulse figure, early kick, 2 bars]

[drop - octave sub pulse, bass pans wide behind, parallel low-mid layer, laser electric full send wobble drop, response line, double-time feel, FM 808, body bass answer, distorted sub figure, rolling 808 run, syncopated hats, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, beat stutter, tempo push, parallel low-mid layer, octave sub stack, chest-sub melody, wobble FM voice, syncopated hats, 2 bars]

[inst - FM warp sub, wide 3D bass field, parallel low-mid layer, low chest-sub, wavy low-mid line, staccato sub bursts, syncopated hats, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, wide stereo layer, laser electric stacked reese drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, fast bass triplets, open hat, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, stutter gate, rising energy, octave 808 stack, low chest-sub, body bass answer, neuro wobble lead, closed hat, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, parallel low-mid layer, stacked 808, low reese counterline, rolling 808 run, loose hats, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, sub pickup, rising energy, wide stereo layer, FM 808, body bass answer, neuro wobble lead, pushed snare, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `311` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `91.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `91.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 2 | `[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doub...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/07-jump-bay` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doubles, rising energy, low chest-sub, wavy low-mid line, phase-wavy synth line, room snare, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, parallel low-mid layer, octave-stacked electric harder reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, fast bass triplets, loose hats, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, wide stereo layer, full send laser heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, neuro wobble lead, staccato sub bursts, pushed snare, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, wide stereo layer, accelerating hats, low chest-sub, chest-sub melody, square-wave pulse figure, chopped hats, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, octave sub stack, chest-sub melody, staccato sub bursts, kick opens, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, wide stereo layer, full send laser stacked reese drop, counter melody, double-time feel, FM 808, chest-sub melody, square-wave pulse figure, rolling 808 run, snare answers, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, low-mid climbs, tempo push, stacked 808, low-mid bass melody, offbeat push, 2 bars]

[inst - neuro wobble sub, layers surround the ear, body bass, low reese counterline, driving sub pulse run, offbeat push, 2 bars]

[drop - phase-distorted sub, 3D low-mid orbit, panning bass layer, octave-stacked electric stacked wobble drop, response line, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, rolling 808 run, straight hats, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wide stereo layer, accelerating hats, panning bass layer, low chest-sub, chest-sub melody, acid squelch line, straight hats, 2 bars]

[inst - FM warp sub, low-mid from every angle, layered sub stack, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, triplet hats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, wide stereo layer, max stack laser full send wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, neuro wobble lead, double-time bass gallop, ghost notes, 2 bars]

[inst - chest-sub, low-mid orbits the sub, panning bass layer, stacked 808, low-mid bass melody, neuro wobble lead, fast bass triplets, wide hat bed, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, layered sub stack, full send laser full send wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, double-time bass gallop, mono kick, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, parallel low-mid layer, tempo push, layered sub stack, octave sub stack, body bass answer, granular bass figure, mono kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, body bass, low wobble answer, wobble FM voice, fast bass triplets, side snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, full send laser stacked reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rolling 808 run, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, octave-stacked electric stacked reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, acid squelch line, rolling 808 run, early kick, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, kick doubles, rising energy, parallel low-mid layer, FM 808, wavy low-mid line, acid squelch line, open hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, wide stereo layer, laser electric tower stacked reese drop, second low-mid line, double-time feel, stacked 808, low reese counterline, neuro wobble lead, rolling 808 run, closed hat, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, wide stereo layer, body bass, low wobble answer, distorted sub figure, double-time bass gallop, closed hat, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, energy surge, accelerating hats, octave 808 stack, octave sub stack, chest-sub melody, room snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, octave 808 stack, low chest-sub, wavy low-mid line, fast bass triplets, room snare, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, full send laser full send wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, energy surge, accelerating hats, parallel low-mid layer, body bass, low reese counterline, pushed snare, 2 bars]

[inst - chest-sub, low-mid from every angle, kick only on downbeats, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, low-mid climbs, tempo push, panning bass layer, FM 808, body bass answer, acid squelch line, kick opens, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, panning bass layer, octave sub stack, chest-sub melody, square-wave pulse figure, rolling 808 run, kick opens, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, heavy wobble drop, sub pickup, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, staccato sub bursts, kick tightens, 2 bars]

[outro - octave sub pulse, low-mid from every angle, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, kick tightens, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| 1 | `[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doub...` |
| 2 | `311` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `91.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doubles, rising energy, low chest-sub, wavy low-mid line, phase-wavy synth line, room snare, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, parallel low-mid layer, octave-stacked electric harder reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, fast bass triplets, loose hats, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, wide stereo layer, full send laser heavy warped drop, counter-line, double-time feel, mono chest-sub, low wobble answer, neuro wobble lead, staccato sub bursts, pushed snare, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, wide stereo layer, accelerating hats, low chest-sub, chest-sub melody, square-wave pulse figure, chopped hats, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, octave sub stack, chest-sub melody, staccato sub bursts, kick opens, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, wide stereo layer, full send laser stacked reese drop, counter melody, double-time feel, FM 808, chest-sub melody, square-wave pulse figure, rolling 808 run, snare answers, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, low-mid climbs, tempo push, stacked 808, low-mid bass melody, offbeat push, 2 bars]

[inst - neuro wobble sub, layers surround the ear, body bass, low reese counterline, driving sub pulse run, offbeat push, 2 bars]

[drop - phase-distorted sub, 3D low-mid orbit, panning bass layer, octave-stacked electric stacked wobble drop, response line, double-time feel, octave sub stack, body bass answer, phase-wavy synth line, rolling 808 run, straight hats, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wide stereo layer, accelerating hats, panning bass layer, low chest-sub, chest-sub melody, acid squelch line, straight hats, 2 bars]

[inst - FM warp sub, low-mid from every angle, layered sub stack, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, triplet hats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, wide stereo layer, max stack laser full send wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, neuro wobble lead, double-time bass gallop, ghost notes, 2 bars]

[inst - chest-sub, low-mid orbits the sub, panning bass layer, stacked 808, low-mid bass melody, neuro wobble lead, fast bass triplets, wide hat bed, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, layered sub stack, full send laser full send wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, double-time bass gallop, mono kick, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, parallel low-mid layer, tempo push, layered sub stack, octave sub stack, body bass answer, granular bass figure, mono kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, body bass, low wobble answer, wobble FM voice, fast bass triplets, side snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, full send laser stacked reese drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rolling 808 run, side snare, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, octave-stacked electric stacked reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, acid squelch line, rolling 808 run, early kick, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, kick doubles, rising energy, parallel low-mid layer, FM 808, wavy low-mid line, acid squelch line, open hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, wide stereo layer, laser electric tower stacked reese drop, second low-mid line, double-time feel, stacked 808, low reese counterline, neuro wobble lead, rolling 808 run, closed hat, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, wide stereo layer, body bass, low wobble answer, distorted sub figure, double-time bass gallop, closed hat, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, energy surge, accelerating hats, octave 808 stack, octave sub stack, chest-sub melody, room snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, octave 808 stack, low chest-sub, wavy low-mid line, fast bass triplets, room snare, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, full send laser full send wobble drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, energy surge, accelerating hats, parallel low-mid layer, body bass, low reese counterline, pushed snare, 2 bars]

[inst - chest-sub, low-mid from every angle, kick only on downbeats, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, low-mid climbs, tempo push, panning bass layer, FM 808, body bass answer, acid squelch line, kick opens, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, panning bass layer, octave sub stack, chest-sub melody, square-wave pulse figure, rolling 808 run, kick opens, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, heavy wobble drop, sub pickup, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, staccato sub bursts, kick tightens, 2 bars]

[outro - octave sub pulse, low-mid from every angle, kick pattern flip, rapid hi-hats, mono chest-sub, low reese counterline, kick tightens, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `311` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `08-psy-median`

Catalog id `audio/albums/drive-through/hour-2/08-psy-median`.

US-safe EDM take: Drive-through psy-median neuro warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 2 | `[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating ha...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/08-psy-median` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating hats, tempo push, rolling hats, reese 808 wreck, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, parallel low-mid layer, laser-lit wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, acid squelch line, trap drums denser, late snare, reese bass, heavy neuro drop, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, layered sub stack, laser-lit full send reese drop, counter melody, double-time feel, body bass, chest-sub melody, granular bass figure, rapid hi-hats, kick tightens, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[drop - wavy phase sub, low-mid from every angle, panning bass layer, laser-lit harder reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, ghost snare, open hat, rapid hi-hats roll, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, gated bass, rising energy, FM 808, room snare, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, parallel low-mid layer, laser-lit wreck wobble drop, counter-line, octave sub stack, low wobble answer, wobble FM voice, trap drums denser, room snare, harder stacked drop, 2 bars]

[inst - FM warp sub, bass pans wide behind, body bass, kick pattern flip, tight kick, warped 808 wall, 2 bars]

[drop - neuro wobble sub, layers surround the ear, octave 808 stack, laser-lit heavy warped drop, counter-lead answers, octave sub stack, low-mid bass melody, offbeat hats, loose hats, chest-sub, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, gated bass, tempo push, body bass, pushed snare, chest-sub wreck, 2 bars]

[inst - chest-sub, low-mid orbits the sub, octave sub stack, rapid hi-hats, chopped hats, neuro warp, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, triplet hats, accelerating hats, body bass, hat density up, kick holds, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, octave sub stack, kick pattern flip, kick opens, reese ride, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, octave 808 stack, laser-lit heavy reese drop, counter melody, body bass, chest-sub melody, offbeat hats, kick tightens, full send drop, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, accelerating hats, octave sub stack, snare answers, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, laser-lit wreck reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, trap drums denser, straight hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, bass pressure builds, accelerating hats, body bass, body bass answer, triplet hats, 2 bars]

[inst - wavy phase sub, layers surround the ear, octave sub stack, low wobble answer, offbeat hats, backbeat shove, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, laser-lit harder reese drop, counter melody, double-time feel, body bass, chest-sub melody, square-wave pulse figure, ghost snare, ghost notes, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, body bass, wavy low-mid line, granular bass figure, trap drums denser, wide hat bed, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, sub pickup, rising energy, octave sub stack, low reese counterline, wobble FM voice, mono kick, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 1 | `[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating ha...` |
| 2 | `313` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `B minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating hats, tempo push, rolling hats, reese 808 wreck, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, parallel low-mid layer, laser-lit wreck reese drop, counter melody, double-time feel, body bass, chest-sub melody, acid squelch line, trap drums denser, late snare, reese bass, heavy neuro drop, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, layered sub stack, laser-lit full send reese drop, counter melody, double-time feel, body bass, chest-sub melody, granular bass figure, rapid hi-hats, kick tightens, 2 bars]

[inst - chest-sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[drop - wavy phase sub, low-mid from every angle, panning bass layer, laser-lit harder reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, ghost snare, open hat, rapid hi-hats roll, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, gated bass, rising energy, FM 808, room snare, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, parallel low-mid layer, laser-lit wreck wobble drop, counter-line, octave sub stack, low wobble answer, wobble FM voice, trap drums denser, room snare, harder stacked drop, 2 bars]

[inst - FM warp sub, bass pans wide behind, body bass, kick pattern flip, tight kick, warped 808 wall, 2 bars]

[drop - neuro wobble sub, layers surround the ear, octave 808 stack, laser-lit heavy warped drop, counter-lead answers, octave sub stack, low-mid bass melody, offbeat hats, loose hats, chest-sub, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, gated bass, tempo push, body bass, pushed snare, chest-sub wreck, 2 bars]

[inst - chest-sub, low-mid orbits the sub, octave sub stack, rapid hi-hats, chopped hats, neuro warp, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, triplet hats, accelerating hats, body bass, hat density up, kick holds, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, octave sub stack, kick pattern flip, kick opens, reese ride, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, octave 808 stack, laser-lit heavy reese drop, counter melody, body bass, chest-sub melody, offbeat hats, kick tightens, full send drop, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, accelerating hats, octave sub stack, snare answers, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, parallel low-mid layer, laser-lit wreck reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, trap drums denser, straight hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, bass pressure builds, accelerating hats, body bass, body bass answer, triplet hats, 2 bars]

[inst - wavy phase sub, layers surround the ear, octave sub stack, low wobble answer, offbeat hats, backbeat shove, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, laser-lit harder reese drop, counter melody, double-time feel, body bass, chest-sub melody, square-wave pulse figure, ghost snare, ghost notes, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, body bass, wavy low-mid line, granular bass figure, trap drums denser, wide hat bed, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, sub pickup, rising energy, octave sub stack, low reese counterline, wobble FM voice, mono kick, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `313` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `08 - Psy Median` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `08 - Psy Median` |
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
| 1 | `Hour 2` |
| 2 | `Psy Median` |
| 3 | `8` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `08 - Psy Median` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 2 | `[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 b...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/08-psy-median` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, parallel low-mid layer, electric harder reese drop, response line, low chest-sub, body bass answer, rapid hi-hats, early kick, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, trap drums denser, syncopated hats, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, electric wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, warped FM lead, kick pattern flip, open hat, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, gated bass, rising energy, mono chest-sub, closed hat, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, layered sub stack, electric heavy warped drop, low wobble answer, low chest-sub, wavy low-mid line, ghost snare, room snare, 2 bars]

[build-up - chest-sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, bass pans wide behind, wide stereo layer, electric full send reese drop, response line, low chest-sub, body bass answer, distorted sub figure, trap drums denser, loose hats, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, electric harder warped drop, response line, FM 808, body bass answer, rapid hi-hats, backbeat shove, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, stacked 808, trap drums denser, ghost notes, 2 bars]

[drop - bitcrushed 808, layers surround the ear, layered sub stack, laser-lit harder warped drop, counter-line, mono chest-sub, low wobble answer, rapid hi-hats, wide hat bed, 2 bars]

[drop - neuro wobble sub, layers surround the ear, octave 808 stack, electric wreck wobble drop, second low-mid line, mono chest-sub, low reese counterline, phase-wavy synth line, kick pattern flip, ghost notes, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, bass pressure builds, tempo push, mono chest-sub, kick tightens, 2 bars]

[drop - chest-sub, low-mid orbits the sub, layered sub stack, electric heavy warped drop, counter-line, mono chest-sub, low wobble answer, acid squelch line, ghost snare, wide hat bed, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, low chest-sub, ghost snare, straight hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - FM warp sub, bass pans wide behind, low chest-sub, wavy low-mid line, trap drums denser, backbeat shove, 2 bars]

[build-up - neuro wobble sub, layers surround the ear, kick tightens, gated bass, tempo push, mono chest-sub, low reese counterline, phase-wavy synth line, ghost notes, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, low chest-sub, body bass answer, offbeat hats, dry hats, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, low chest-sub, chest-sub melody, neuro wobble lead, rapid hi-hats, mono kick, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, downbeat impact, rising energy, mono chest-sub, low-mid bass melody, side snare, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 1 | `[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 b...` |
| 2 | `313` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `B minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, parallel low-mid layer, electric harder reese drop, response line, low chest-sub, body bass answer, rapid hi-hats, early kick, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, trap drums denser, syncopated hats, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, octave 808 stack, electric wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, warped FM lead, kick pattern flip, open hat, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, gated bass, rising energy, mono chest-sub, closed hat, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, layered sub stack, electric heavy warped drop, low wobble answer, low chest-sub, wavy low-mid line, ghost snare, room snare, 2 bars]

[build-up - chest-sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, bass pans wide behind, wide stereo layer, electric full send reese drop, response line, low chest-sub, body bass answer, distorted sub figure, trap drums denser, loose hats, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, electric harder warped drop, response line, FM 808, body bass answer, rapid hi-hats, backbeat shove, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, stacked 808, trap drums denser, ghost notes, 2 bars]

[drop - bitcrushed 808, layers surround the ear, layered sub stack, laser-lit harder warped drop, counter-line, mono chest-sub, low wobble answer, rapid hi-hats, wide hat bed, 2 bars]

[drop - neuro wobble sub, layers surround the ear, octave 808 stack, electric wreck wobble drop, second low-mid line, mono chest-sub, low reese counterline, phase-wavy synth line, kick pattern flip, ghost notes, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, bass pressure builds, tempo push, mono chest-sub, kick tightens, 2 bars]

[drop - chest-sub, low-mid orbits the sub, layered sub stack, electric heavy warped drop, counter-line, mono chest-sub, low wobble answer, acid squelch line, ghost snare, wide hat bed, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, low chest-sub, ghost snare, straight hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick only on downbeats, 2 bars]

[inst - FM warp sub, bass pans wide behind, low chest-sub, wavy low-mid line, trap drums denser, backbeat shove, 2 bars]

[build-up - neuro wobble sub, layers surround the ear, kick tightens, gated bass, tempo push, mono chest-sub, low reese counterline, phase-wavy synth line, ghost notes, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, low chest-sub, body bass answer, offbeat hats, dry hats, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, low chest-sub, chest-sub melody, neuro wobble lead, rapid hi-hats, mono kick, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, downbeat impact, rising energy, mono chest-sub, low-mid bass melody, side snare, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `313` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 2 | `[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick dou...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/08-psy-median` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick doubles, accelerating hats, stacked 808, low wobble answer, warped FM lead, open hat, 2 bars]

[drop - FM warp sub, wide 3D bass field, wide stereo layer, laser electric tower wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, fast bass triplets, closed hat, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, downbeat sub pulse, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, kick doubles, accelerating hats, FM 808, wavy low-mid line, tight kick, 2 bars]

[inst - chest-sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, bass circles the low-mid, panning bass layer, octave-stacked electric wreck warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, fast bass triplets, mono kick, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, kick doubles, accelerating hats, stacked 808, low wobble answer, wobble FM voice, chopped hats, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, FM 808, chest-sub melody, phase-wavy synth line, double-time bass gallop, hat density up, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, octave-stacked electric full send reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, staccato sub bursts, syncopated hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, kick doubles, accelerating hats, layered sub stack, FM 808, wavy low-mid line, acid squelch line, kick tightens, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, parallel low-mid layer, stacked 808, low reese counterline, neuro wobble lead, staccato sub bursts, snare answers, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, laser electric tower wreck reese drop, response line, double-time feel, FM 808, body bass answer, fast bass triplets, offbeat push, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick doubles, accelerating hats, octave 808 stack, stacked 808, low wobble answer, distorted sub figure, straight hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, laser electric tower heavy wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, granular bass figure, driving sub pulse run, triplet hats, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, laser electric tower full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, staccato sub bursts, ghost notes, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, wide stereo layer, tempo push, wide stereo layer, stacked 808, low reese counterline, dry hats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, octave 808 stack, laser electric tower stacked reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, double-time bass gallop, wide hat bed, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, kick doubles, accelerating hats, panning bass layer, stacked 808, low wobble answer, neuro wobble lead, mono kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, layered sub stack, FM 808, chest-sub melody, square-wave pulse figure, rolling 808 run, side snare, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, full send laser full send reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, staccato sub bursts, rolling hats, 2 bars]

[inst - octave sub pulse, wide 3D bass field, wide stereo layer, FM 808, wavy low-mid line, granular bass figure, fast bass triplets, late snare, 2 bars]

[outro - FM warp sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, low chest-sub, chest-sub melody, late snare, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| 1 | `[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick dou...` |
| 2 | `313` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `B minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick doubles, accelerating hats, stacked 808, low wobble answer, warped FM lead, open hat, 2 bars]

[drop - FM warp sub, wide 3D bass field, wide stereo layer, laser electric tower wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, fast bass triplets, closed hat, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, downbeat sub pulse, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, kick doubles, accelerating hats, FM 808, wavy low-mid line, tight kick, 2 bars]

[inst - chest-sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, bass circles the low-mid, panning bass layer, octave-stacked electric wreck warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, fast bass triplets, mono kick, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, kick doubles, accelerating hats, stacked 808, low wobble answer, wobble FM voice, chopped hats, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, FM 808, chest-sub melody, phase-wavy synth line, double-time bass gallop, hat density up, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, octave-stacked electric full send reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, staccato sub bursts, syncopated hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, kick doubles, accelerating hats, layered sub stack, FM 808, wavy low-mid line, acid squelch line, kick tightens, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, parallel low-mid layer, stacked 808, low reese counterline, neuro wobble lead, staccato sub bursts, snare answers, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, laser electric tower wreck reese drop, response line, double-time feel, FM 808, body bass answer, fast bass triplets, offbeat push, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick doubles, accelerating hats, octave 808 stack, stacked 808, low wobble answer, distorted sub figure, straight hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, laser electric tower heavy wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, granular bass figure, driving sub pulse run, triplet hats, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, laser electric tower full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, staccato sub bursts, ghost notes, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, wide stereo layer, tempo push, wide stereo layer, stacked 808, low reese counterline, dry hats, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, octave 808 stack, laser electric tower stacked reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, double-time bass gallop, wide hat bed, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, kick doubles, accelerating hats, panning bass layer, stacked 808, low wobble answer, neuro wobble lead, mono kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, layered sub stack, FM 808, chest-sub melody, square-wave pulse figure, rolling 808 run, side snare, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, full send laser full send reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, staccato sub bursts, rolling hats, 2 bars]

[inst - octave sub pulse, wide 3D bass field, wide stereo layer, FM 808, wavy low-mid line, granular bass figure, fast bass triplets, late snare, 2 bars]

[outro - FM warp sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, low chest-sub, chest-sub melody, late snare, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `313` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `1, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `09-groove-mile`

Catalog id `audio/albums/drive-through/hour-2/09-groove-mile`.

US-safe EDM take: Drive-through groove-mile hybrid trap warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 2 | `[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/09-groove-mile` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end pressure builds, rising energy, kick opens, warped hybrid-trap drums 808 wreck, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, parallel low-mid layer, harder wobble drop, low chest-sub, body bass answer, warped FM lead, ghost snare, kick tightens, warped hybrid-trap, heavy warped drop, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, low-mid stack tightens, tempo push, snare answers, mile grind, 2 bars]

[drop - chest-sub, bass circles the low-mid, octave 808 stack, wreck warped drop, low chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, offbeat push, rapid hi-hats roll, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, kick tightens, accelerating hats, straight hats, 808 bounce hold, 2 bars]

[inst - bitcrushed 808, layers surround the ear, offbeat hats, triplet hats, stacked 808 warp, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, parallel low-mid layer, harder warped drop, mono chest-sub, low reese counterline, granular bass figure, ghost snare, backbeat shove, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, octave 808 stack, wreck reese drop, mono chest-sub, low wobble answer, phase-wavy synth line, trap drums denser, dry hats, chest punch, 2 bars]

[inst - phase-distorted sub, panning low-mid sweep, kick pattern flip, wide hat bed, kick tightens, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, layered sub stack, heavy wobble drop, mono chest-sub, low-mid bass melody, offbeat hats, mono kick, chest-sub 808, 2 bars]

[inst - wavy phase sub, low-mid from every angle, ghost snare, side snare, body bass wreck, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, wide stereo layer, full send warped drop, double-time feel, mono chest-sub, low reese counterline, rapid hi-hats, rolling hats, full send drop, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, low chest-sub, trap drums denser, late snare, warped trap, 2 bars]

[drop - FM warp sub, bass pans wide behind, panning bass layer, stacked reese drop, mono chest-sub, low wobble answer, granular bass figure, kick pattern flip, early kick, kick holds, 2 bars]

[inst - neuro wobble sub, layers surround the ear, low chest-sub, offbeat hats, syncopated hats, hats denser, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, sparse four-on-floor kick, 2 bars]

[inst - chest-sub, low-mid orbits the sub, low chest-sub, rapid hi-hats, closed hat, 808 ride, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, octave 808 stack, wreck warped drop, double-time feel, mono chest-sub, low reese counterline, acid squelch line, trap drums denser, room snare, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, offbeat push, accelerating hats, low chest-sub, tight kick, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, mono chest-sub, offbeat hats, loose hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, mono chest-sub, chopped hats, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 1 | `[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end...` |
| 2 | `317` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end pressure builds, rising energy, kick opens, warped hybrid-trap drums 808 wreck, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, parallel low-mid layer, harder wobble drop, low chest-sub, body bass answer, warped FM lead, ghost snare, kick tightens, warped hybrid-trap, heavy warped drop, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, low-mid stack tightens, tempo push, snare answers, mile grind, 2 bars]

[drop - chest-sub, bass circles the low-mid, octave 808 stack, wreck warped drop, low chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, offbeat push, rapid hi-hats roll, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, kick tightens, accelerating hats, straight hats, 808 bounce hold, 2 bars]

[inst - bitcrushed 808, layers surround the ear, offbeat hats, triplet hats, stacked 808 warp, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, parallel low-mid layer, harder warped drop, mono chest-sub, low reese counterline, granular bass figure, ghost snare, backbeat shove, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, octave 808 stack, wreck reese drop, mono chest-sub, low wobble answer, phase-wavy synth line, trap drums denser, dry hats, chest punch, 2 bars]

[inst - phase-distorted sub, panning low-mid sweep, kick pattern flip, wide hat bed, kick tightens, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, layered sub stack, heavy wobble drop, mono chest-sub, low-mid bass melody, offbeat hats, mono kick, chest-sub 808, 2 bars]

[inst - wavy phase sub, low-mid from every angle, ghost snare, side snare, body bass wreck, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, wide stereo layer, full send warped drop, double-time feel, mono chest-sub, low reese counterline, rapid hi-hats, rolling hats, full send drop, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, low chest-sub, trap drums denser, late snare, warped trap, 2 bars]

[drop - FM warp sub, bass pans wide behind, panning bass layer, stacked reese drop, mono chest-sub, low wobble answer, granular bass figure, kick pattern flip, early kick, kick holds, 2 bars]

[inst - neuro wobble sub, layers surround the ear, low chest-sub, offbeat hats, syncopated hats, hats denser, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, sparse four-on-floor kick, 2 bars]

[inst - chest-sub, low-mid orbits the sub, low chest-sub, rapid hi-hats, closed hat, 808 ride, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, octave 808 stack, wreck warped drop, double-time feel, mono chest-sub, low reese counterline, acid squelch line, trap drums denser, room snare, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, offbeat push, accelerating hats, low chest-sub, tight kick, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, mono chest-sub, offbeat hats, loose hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, pre-impact hold, accelerating hats, mono chest-sub, chopped hats, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `317` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `09 - Groove Mile` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `09 - Groove Mile` |
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
| 1 | `Hour 2` |
| 2 | `Groove Mile` |
| 3 | `9` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `09 - Groove Mile` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 2 | `[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/09-groove-mile` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, accelerating hats, kick tightens, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, layered sub stack, laser-lit full send wobble drop, low wobble answer, low chest-sub, wavy low-mid line, trap drums denser, snare answers, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, wide stereo layer, laser-lit stacked warped drop, response line, double-time feel, low chest-sub, body bass answer, phase-wavy synth line, offbeat hats, straight hats, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, mono chest-sub, ghost snare, triplet hats, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, laser-lit harder reese drop, counter melody, low chest-sub, chest-sub melody, rapid hi-hats, backbeat shove, 2 bars]

[inst - chest-sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, laser-lit wreck wobble drop, low wobble answer, low chest-sub, wavy low-mid line, kick pattern flip, dry hats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, laser-lit harder reese drop, second low-mid line, mono chest-sub, low reese counterline, neuro wobble lead, rapid hi-hats, syncopated hats, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, sub swell, rising energy, stacked 808, tight kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, parallel low-mid layer, laser-lit wreck wobble drop, counter-line, double-time feel, mono chest-sub, low wobble answer, kick pattern flip, closed hat, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, laser-lit stacked reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, offbeat hats, room snare, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, body bass, kick pattern flip, pushed snare, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, laser-lit harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, phase-wavy synth line, rapid hi-hats, loose hats, 2 bars]

[inst - neuro wobble sub, layers surround the ear, body bass, ghost snare, hat density up, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, low chest-sub, open hat, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, sub swell, rising energy, low chest-sub, chest-sub melody, granular bass figure, room snare, 2 bars]

[inst - neuro wobble sub, layers surround the ear, mono chest-sub, low-mid bass melody, offbeat hats, tight kick, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[inst - chest-sub, low-mid orbits the sub, mono chest-sub, low reese counterline, warped FM lead, rapid hi-hats, pushed snare, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, gated bass, accelerating hats, low chest-sub, body bass answer, acid squelch line, chopped hats, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, pre-impact hold, tempo push, mono chest-sub, low wobble answer, hat density up, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 1 | `[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, ...` |
| 2 | `317` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, accelerating hats, kick tightens, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, layered sub stack, laser-lit full send wobble drop, low wobble answer, low chest-sub, wavy low-mid line, trap drums denser, snare answers, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, wide stereo layer, laser-lit stacked warped drop, response line, double-time feel, low chest-sub, body bass answer, phase-wavy synth line, offbeat hats, straight hats, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, mono chest-sub, ghost snare, triplet hats, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, laser-lit harder reese drop, counter melody, low chest-sub, chest-sub melody, rapid hi-hats, backbeat shove, 2 bars]

[inst - chest-sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, laser-lit wreck wobble drop, low wobble answer, low chest-sub, wavy low-mid line, kick pattern flip, dry hats, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, laser-lit harder reese drop, second low-mid line, mono chest-sub, low reese counterline, neuro wobble lead, rapid hi-hats, syncopated hats, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, sub swell, rising energy, stacked 808, tight kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, parallel low-mid layer, laser-lit wreck wobble drop, counter-line, double-time feel, mono chest-sub, low wobble answer, kick pattern flip, closed hat, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, laser-lit stacked reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, offbeat hats, room snare, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, body bass, kick pattern flip, pushed snare, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, laser-lit harder wobble drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, phase-wavy synth line, rapid hi-hats, loose hats, 2 bars]

[inst - neuro wobble sub, layers surround the ear, body bass, ghost snare, hat density up, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, low chest-sub, open hat, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, sub swell, rising energy, low chest-sub, chest-sub melody, granular bass figure, room snare, 2 bars]

[inst - neuro wobble sub, layers surround the ear, mono chest-sub, low-mid bass melody, offbeat hats, tight kick, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[inst - chest-sub, low-mid orbits the sub, mono chest-sub, low reese counterline, warped FM lead, rapid hi-hats, pushed snare, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, gated bass, accelerating hats, low chest-sub, body bass answer, acid squelch line, chopped hats, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, pre-impact hold, tempo push, mono chest-sub, low wobble answer, hat density up, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `317` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 2 | `[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/09-groove-mile` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, panning bass layer, electric wreck wobble drop, counter melody, low chest-sub, chest-sub melody, rapid hi-hats, offbeat push, 2 bars]

[inst - chest-sub, panning low-mid sweep, trap drums denser, straight hats, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, electric heavy warped drop, low wobble answer, low chest-sub, wavy low-mid line, square-wave pulse figure, kick pattern flip, triplet hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, mono chest-sub, offbeat hats, backbeat shove, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, electric full send reese drop, response line, double-time feel, low chest-sub, body bass answer, granular bass figure, ghost snare, ghost notes, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, side snare, accelerating hats, mono chest-sub, dry hats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, electric stacked wobble drop, counter melody, low chest-sub, chest-sub melody, trap drums denser, wide hat bed, 2 bars]

[inst - phase-distorted sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, gated bass, accelerating hats, low chest-sub, side snare, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, mono chest-sub, ghost snare, rolling hats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, parallel low-mid layer, electric stacked wobble drop, low wobble answer, FM 808, wavy low-mid line, trap drums denser, syncopated hats, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, octave 808 stack, electric harder warped drop, response line, double-time feel, FM 808, body bass answer, square-wave pulse figure, offbeat hats, closed hat, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, octave sub stack, trap drums denser, closed hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, layered sub stack, electric wreck reese drop, counter melody, double-time feel, FM 808, chest-sub melody, granular bass figure, rapid hi-hats, tight kick, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, bass pressure builds, rising energy, stacked 808, low-mid bass melody, loose hats, 2 bars]

[drop - phase-distorted sub, layers surround the ear, octave 808 stack, laser-lit wreck reese drop, counter-lead answers, mono chest-sub, low-mid bass melody, wobble FM voice, rapid hi-hats, chopped hats, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, stacked 808, low reese counterline, warped FM lead, offbeat hats, chopped hats, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, side snare, rising energy, FM 808, body bass answer, acid squelch line, hat density up, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, electric wreck wobble drop, counter-line, stacked 808, low wobble answer, neuro wobble lead, rapid hi-hats, kick opens, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, triplet hats, rising energy, body bass, low-mid bass melody, distorted sub figure, kick opens, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, bass returns, tempo push, mono chest-sub, low reese counterline, wobble FM voice, kick opens, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 1 | `[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick...` |
| 2 | `317` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, panning bass layer, electric wreck wobble drop, counter melody, low chest-sub, chest-sub melody, rapid hi-hats, offbeat push, 2 bars]

[inst - chest-sub, panning low-mid sweep, trap drums denser, straight hats, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, parallel low-mid layer, electric heavy warped drop, low wobble answer, low chest-sub, wavy low-mid line, square-wave pulse figure, kick pattern flip, triplet hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, mono chest-sub, offbeat hats, backbeat shove, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, electric full send reese drop, response line, double-time feel, low chest-sub, body bass answer, granular bass figure, ghost snare, ghost notes, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, side snare, accelerating hats, mono chest-sub, dry hats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, electric stacked wobble drop, counter melody, low chest-sub, chest-sub melody, trap drums denser, wide hat bed, 2 bars]

[inst - phase-distorted sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, gated bass, accelerating hats, low chest-sub, side snare, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, mono chest-sub, ghost snare, rolling hats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, parallel low-mid layer, electric stacked wobble drop, low wobble answer, FM 808, wavy low-mid line, trap drums denser, syncopated hats, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, octave 808 stack, electric harder warped drop, response line, double-time feel, FM 808, body bass answer, square-wave pulse figure, offbeat hats, closed hat, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, octave sub stack, trap drums denser, closed hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, layered sub stack, electric wreck reese drop, counter melody, double-time feel, FM 808, chest-sub melody, granular bass figure, rapid hi-hats, tight kick, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, bass pressure builds, rising energy, stacked 808, low-mid bass melody, loose hats, 2 bars]

[drop - phase-distorted sub, layers surround the ear, octave 808 stack, laser-lit wreck reese drop, counter-lead answers, mono chest-sub, low-mid bass melody, wobble FM voice, rapid hi-hats, chopped hats, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, stacked 808, low reese counterline, warped FM lead, offbeat hats, chopped hats, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, side snare, rising energy, FM 808, body bass answer, acid squelch line, hat density up, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, electric wreck wobble drop, counter-line, stacked 808, low wobble answer, neuro wobble lead, rapid hi-hats, kick opens, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, triplet hats, rising energy, body bass, low-mid bass melody, distorted sub figure, kick opens, 2 bars]

[build-up - phase-distorted sub, panning low-mid sweep, kick tightens, bass returns, tempo push, mono chest-sub, low reese counterline, wobble FM voice, kick opens, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `317` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 2 | `[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars] [dr...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/09-groove-mile` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, wobble FM voice, staccato sub bursts, straight hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, energy surge, accelerating hats, FM 808, chest-sub melody, phase-wavy synth line, triplet hats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, stacked 808, low-mid bass melody, double-time bass gallop, backbeat shove, 2 bars]

[drop - FM warp sub, layers surround the ear, octave 808 stack, octave-stacked electric heavy wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, rolling 808 run, wide hat bed, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, parallel low-mid layer, tempo push, body bass, low-mid bass melody, mono kick, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, layered sub stack, laser electric tower heavy warped drop, response line, double-time feel, low chest-sub, body bass answer, rolling 808 run, side snare, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, energy surge, accelerating hats, layered sub stack, FM 808, chest-sub melody, granular bass figure, side snare, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, octave-stacked electric stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, wobble FM voice, driving sub pulse run, rolling hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - FM warp sub, wide 3D bass field, layered sub stack, body bass, low-mid bass melody, wobble FM voice, fast bass triplets, open hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, octave 808 stack, max stack laser stacked reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, granular bass figure, driving sub pulse run, tight kick, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, stacked 808, low wobble answer, neuro wobble lead, double-time bass gallop, open hat, 2 bars]

[drop - chest-sub, layers surround the ear, octave 808 stack, octave-stacked electric heavy reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, rolling 808 run, tight kick, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, panning bass layer, body bass, low wobble answer, staccato sub bursts, loose hats, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, octave-stacked electric full send wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, square-wave pulse figure, fast bass triplets, pushed snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, layers surround the ear, layered sub stack, max stack laser wreck wobble drop, response line, double-time feel, FM 808, body bass answer, double-time bass gallop, pushed snare, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, bass melody climbs, rising energy, parallel low-mid layer, stacked 808, low wobble answer, chopped hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, wide stereo layer, FM 808, chest-sub melody, acid squelch line, rolling 808 run, hat density up, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, panning bass layer, max stack laser stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, driving sub pulse run, backbeat shove, 2 bars]

[outro - wavy phase sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, stacked 808, low reese counterline, snare answers, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| 1 | `[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars] [dr...` |
| 2 | `317` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `D major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, wobble FM voice, staccato sub bursts, straight hats, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, energy surge, accelerating hats, FM 808, chest-sub melody, phase-wavy synth line, triplet hats, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, stacked 808, low-mid bass melody, double-time bass gallop, backbeat shove, 2 bars]

[drop - FM warp sub, layers surround the ear, octave 808 stack, octave-stacked electric heavy wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, rolling 808 run, wide hat bed, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, parallel low-mid layer, tempo push, body bass, low-mid bass melody, mono kick, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, low-mid from every angle, layered sub stack, laser electric tower heavy warped drop, response line, double-time feel, low chest-sub, body bass answer, rolling 808 run, side snare, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, energy surge, accelerating hats, layered sub stack, FM 808, chest-sub melody, granular bass figure, side snare, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, octave-stacked electric stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, wobble FM voice, driving sub pulse run, rolling hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - FM warp sub, wide 3D bass field, layered sub stack, body bass, low-mid bass melody, wobble FM voice, fast bass triplets, open hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, octave 808 stack, max stack laser stacked reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, granular bass figure, driving sub pulse run, tight kick, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, stacked 808, low wobble answer, neuro wobble lead, double-time bass gallop, open hat, 2 bars]

[drop - chest-sub, layers surround the ear, octave 808 stack, octave-stacked electric heavy reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, rolling 808 run, tight kick, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, panning bass layer, body bass, low wobble answer, staccato sub bursts, loose hats, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, octave-stacked electric full send wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, square-wave pulse figure, fast bass triplets, pushed snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, layers surround the ear, layered sub stack, max stack laser wreck wobble drop, response line, double-time feel, FM 808, body bass answer, double-time bass gallop, pushed snare, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, bass melody climbs, rising energy, parallel low-mid layer, stacked 808, low wobble answer, chopped hats, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, wide stereo layer, FM 808, chest-sub melody, acid squelch line, rolling 808 run, hat density up, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, panning bass layer, max stack laser stacked wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, driving sub pulse run, backbeat shove, 2 bars]

[outro - wavy phase sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, stacked 808, low reese counterline, snare answers, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `317` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `10-donk-ramp`

Catalog id `audio/albums/drive-through/hour-2/10-donk-ramp`.

US-safe EDM take: Drive-through donk-ramp tearout warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `89.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 2 | `[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 b...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, stacked wobble drop, stacked 808, chest-sub melody, acid squelch line, rapid hi-hats, chopped hats, tearout, heavy tearout drop, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, kick tightens, accelerating hats, hat density up, growl 808 wreck, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, kick pattern flip, kick opens, chest-sub ramp, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, wide stereo layer, full send wobble drop, double-time feel, FM 808, low reese counterline, distorted sub figure, offbeat hats, kick tightens, harder warped drop, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, low-end pressure builds, accelerating hats, snare answers, chest-sub 808 stack, 2 bars]

[drop - neuro wobble sub, layers surround the ear, panning bass layer, stacked warped drop, double-time feel, FM 808, low wobble answer, wobble FM voice, rapid hi-hats, offbeat push, tearout grind, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, low-mid stack tightens, rising energy, straight hats, rapid hi-hats denser, 2 bars]

[drop - chest-sub, low-mid orbits the sub, parallel low-mid layer, harder reese drop, FM 808, low-mid bass melody, kick pattern flip, triplet hats, growl sustain, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, offbeat hats, backbeat shove, dirty analog wreck, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, octave 808 stack, wreck wobble drop, FM 808, low reese counterline, ghost snare, ghost notes, full send drop, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid from every angle, layered sub stack, heavy warped drop, double-time feel, FM 808, low wobble answer, trap drums denser, wide hat bed, warped 808, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, ghost snare, rising energy, mono kick, kick holds, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, offbeat hats, side snare, rapid hi-hats roll, 2 bars]

[drop - chest-sub, bass pans wide behind, octave 808 stack, wreck warped drop, stacked 808, wavy low-mid line, phase-wavy synth line, ghost snare, rolling hats, growl ride, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, layered sub stack, heavy reese drop, stacked 808, body bass answer, acid squelch line, trap drums denser, early kick, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, wide stereo layer, full send wobble drop, stacked 808, chest-sub melody, square-wave pulse figure, offbeat hats, open hat, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, ghost snare, accelerating hats, FM 808, closed hat, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, panning bass layer, stacked warped drop, stacked 808, wavy low-mid line, granular bass figure, rapid hi-hats, room snare, 2 bars]

[inst - chest-sub, low-mid from every angle, FM 808, trap drums denser, tight kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, harder reese drop, stacked 808, body bass answer, phase-wavy synth line, kick pattern flip, loose hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, offbeat push, tempo push, FM 808, pushed snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, stacked reese drop, double-time feel, FM 808, low-mid bass melody, rapid hi-hats, hat density up, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, stacked 808, trap drums denser, kick opens, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, parallel low-mid layer, harder wobble drop, FM 808, low reese counterline, kick pattern flip, kick tightens, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, sub energy lifts, accelerating hats, stacked 808, snare answers, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, downbeat impact, tempo push, FM 808, offbeat push, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 1 | `[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 b...` |
| 2 | `331` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, stacked wobble drop, stacked 808, chest-sub melody, acid squelch line, rapid hi-hats, chopped hats, tearout, heavy tearout drop, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, kick tightens, accelerating hats, hat density up, growl 808 wreck, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, kick pattern flip, kick opens, chest-sub ramp, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, wide stereo layer, full send wobble drop, double-time feel, FM 808, low reese counterline, distorted sub figure, offbeat hats, kick tightens, harder warped drop, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, low-end pressure builds, accelerating hats, snare answers, chest-sub 808 stack, 2 bars]

[drop - neuro wobble sub, layers surround the ear, panning bass layer, stacked warped drop, double-time feel, FM 808, low wobble answer, wobble FM voice, rapid hi-hats, offbeat push, tearout grind, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, low-mid stack tightens, rising energy, straight hats, rapid hi-hats denser, 2 bars]

[drop - chest-sub, low-mid orbits the sub, parallel low-mid layer, harder reese drop, FM 808, low-mid bass melody, kick pattern flip, triplet hats, growl sustain, 2 bars]

[inst - wavy phase sub, sub anchored, mids orbit, offbeat hats, backbeat shove, dirty analog wreck, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, octave 808 stack, wreck wobble drop, FM 808, low reese counterline, ghost snare, ghost notes, full send drop, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - FM warp sub, low-mid from every angle, layered sub stack, heavy warped drop, double-time feel, FM 808, low wobble answer, trap drums denser, wide hat bed, warped 808, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick tightens, ghost snare, rising energy, mono kick, kick holds, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, offbeat hats, side snare, rapid hi-hats roll, 2 bars]

[drop - chest-sub, bass pans wide behind, octave 808 stack, wreck warped drop, stacked 808, wavy low-mid line, phase-wavy synth line, ghost snare, rolling hats, growl ride, 2 bars]

[build-up - wavy phase sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, layered sub stack, heavy reese drop, stacked 808, body bass answer, acid squelch line, trap drums denser, early kick, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, wide stereo layer, full send wobble drop, stacked 808, chest-sub melody, square-wave pulse figure, offbeat hats, open hat, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, ghost snare, accelerating hats, FM 808, closed hat, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, panning bass layer, stacked warped drop, stacked 808, wavy low-mid line, granular bass figure, rapid hi-hats, room snare, 2 bars]

[inst - chest-sub, low-mid from every angle, FM 808, trap drums denser, tight kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, harder reese drop, stacked 808, body bass answer, phase-wavy synth line, kick pattern flip, loose hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, offbeat push, tempo push, FM 808, pushed snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, stacked reese drop, double-time feel, FM 808, low-mid bass melody, rapid hi-hats, hat density up, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, stacked 808, trap drums denser, kick opens, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, parallel low-mid layer, harder wobble drop, FM 808, low reese counterline, kick pattern flip, kick tightens, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, sub energy lifts, accelerating hats, stacked 808, snare answers, 2 bars]

[build-up - wavy phase sub, panning low-mid sweep, kick tightens, downbeat impact, tempo push, FM 808, offbeat push, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `331` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `10 - Donk Ramp` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `10 - Donk Ramp` |
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
| 1 | `Hour 2` |
| 2 | `Donk Ramp` |
| 3 | `10` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `10 - Donk Ramp` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 2 | `[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack, rising energy, FM 808, chopped hats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, octave 808 stack, multi-stack heavy reese drop, response line, double-time feel, stacked 808, body bass answer, staccato sub bursts, hat density up, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, FM 808, fast bass triplets, kick opens, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, layered sub stack, multi-stack full send wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, warped FM lead, double-time bass gallop, kick tightens, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, stutter gate, accelerating hats, FM 808, snare answers, 2 bars]

[drop - wavy phase sub, low-mid from every angle, wide stereo layer, multi-stack stacked warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, neuro wobble lead, rolling 808 run, offbeat push, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, octave 808 stack, rising energy, FM 808, straight hats, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, stacked 808, fast bass triplets, triplet hats, 2 bars]

[drop - FM warp sub, bass pans wide behind, layered sub stack, wide laser full send warped drop, counter-line, double-time feel, FM 808, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - neuro wobble sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, FM 808, low-mid bass melody, phase-wavy synth line, rolling 808 run, dry hats, 2 bars]

[drop - chest-sub, low-mid orbits the sub, octave 808 stack, multi-stack heavy warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, warped FM lead, staccato sub bursts, wide hat bed, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, multi-stack full send reese drop, response line, double-time feel, stacked 808, body bass answer, neuro wobble lead, double-time bass gallop, side snare, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, FM 808, low wobble answer, square-wave pulse figure, driving sub pulse run, rolling hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, octave 808 stack, rising energy, stacked 808, chest-sub melody, distorted sub figure, late snare, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, FM 808, low-mid bass melody, staccato sub bursts, early kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, multi-stack harder warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, fast bass triplets, syncopated hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, octave 808 stack, rising energy, FM 808, low reese counterline, open hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, multi-stack wreck reese drop, response line, double-time feel, stacked 808, body bass answer, driving sub pulse run, closed hat, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, stacked 808, chest-sub melody, neuro wobble lead, staccato sub bursts, tight kick, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, stutter gate, accelerating hats, FM 808, low-mid bass melody, square-wave pulse figure, loose hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, layered sub stack, stacked 808, wavy low-mid line, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, parallel low-mid layer, wide laser wreck wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, driving sub pulse run, chopped hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, octave 808 stack, wide laser heavy warped drop, counter-line, double-time feel, FM 808, low wobble answer, staccato sub bursts, kick opens, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, wide laser full send reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, acid squelch line, double-time bass gallop, snare answers, 2 bars]

[inst - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, downbeat impact, rising energy, wide stereo layer, FM 808, low reese counterline, straight hats, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 1 | `[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack...` |
| 2 | `331` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack, rising energy, FM 808, chopped hats, 2 bars]

[drop - FM warp sub, low-mid orbits the sub, octave 808 stack, multi-stack heavy reese drop, response line, double-time feel, stacked 808, body bass answer, staccato sub bursts, hat density up, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, FM 808, fast bass triplets, kick opens, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, layered sub stack, multi-stack full send wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, warped FM lead, double-time bass gallop, kick tightens, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, stutter gate, accelerating hats, FM 808, snare answers, 2 bars]

[drop - wavy phase sub, low-mid from every angle, wide stereo layer, multi-stack stacked warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, neuro wobble lead, rolling 808 run, offbeat push, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, octave 808 stack, rising energy, FM 808, straight hats, 2 bars]

[inst - octave sub pulse, bass circles the low-mid, stacked 808, fast bass triplets, triplet hats, 2 bars]

[drop - FM warp sub, bass pans wide behind, layered sub stack, wide laser full send warped drop, counter-line, double-time feel, FM 808, low wobble answer, double-time bass gallop, backbeat shove, 2 bars]

[build-up - neuro wobble sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, 3D low-mid orbit, FM 808, low-mid bass melody, phase-wavy synth line, rolling 808 run, dry hats, 2 bars]

[drop - chest-sub, low-mid orbits the sub, octave 808 stack, multi-stack heavy warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, warped FM lead, staccato sub bursts, wide hat bed, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, multi-stack full send reese drop, response line, double-time feel, stacked 808, body bass answer, neuro wobble lead, double-time bass gallop, side snare, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, FM 808, low wobble answer, square-wave pulse figure, driving sub pulse run, rolling hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, octave 808 stack, rising energy, stacked 808, chest-sub melody, distorted sub figure, late snare, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, FM 808, low-mid bass melody, staccato sub bursts, early kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, multi-stack harder warped drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, fast bass triplets, syncopated hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick tightens, octave 808 stack, rising energy, FM 808, low reese counterline, open hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, multi-stack wreck reese drop, response line, double-time feel, stacked 808, body bass answer, driving sub pulse run, closed hat, 2 bars]

[build-up - bitcrushed 808, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, stacked 808, chest-sub melody, neuro wobble lead, staccato sub bursts, tight kick, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, stutter gate, accelerating hats, FM 808, low-mid bass melody, square-wave pulse figure, loose hats, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, layered sub stack, stacked 808, wavy low-mid line, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, parallel low-mid layer, wide laser wreck wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, driving sub pulse run, chopped hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, wide 3D bass field, octave 808 stack, wide laser heavy warped drop, counter-line, double-time feel, FM 808, low wobble answer, staccato sub bursts, kick opens, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, wide laser full send reese drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, acid squelch line, double-time bass gallop, snare answers, 2 bars]

[inst - FM warp sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, kick tightens, downbeat impact, rising energy, wide stereo layer, FM 808, low reese counterline, straight hats, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `331` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 2 | `[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, tempo push, mono chest-sub, kick opens, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, wide laser stacked warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, acid squelch line, double-time bass gallop, kick tightens, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, octave 808 stack, multi-stack stacked warped drop, response line, double-time feel, mono chest-sub, body bass answer, double-time bass gallop, open hat, 2 bars]

[breakdown - neuro wobble sub, sub anchored, mids orbit, rapid hi-hats, tempo dip, octave 808 stack, FM 808, low wobble answer, phase-wavy synth line, pushed snare, 2 bars]

[drop - wavy phase sub, bass pans wide behind, panning bass layer, laser electric wreck wobble drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, square-wave pulse figure, fast bass triplets, closed hat, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, phase-charged full send warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, staccato sub bursts, ghost notes, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, laser electric full send warped drop, low wobble answer, double-time feel, body bass, wavy low-mid line, distorted sub figure, staccato sub bursts, chopped hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, octave sub stack, fast bass triplets, hat density up, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, layered sub stack, wide laser harder wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, rolling 808 run, hat density up, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, parallel low-mid layer, wide laser full send wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, granular bass figure, staccato sub bursts, triplet hats, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, side snare, 2 bars]

[drop - wavy phase sub, low-mid from every angle, panning bass layer, laser electric full send wobble drop, counter melody, double-time feel, body bass, chest-sub melody, wobble FM voice, staccato sub bursts, dry hats, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, wide laser heavy reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, driving sub pulse run, offbeat push, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, FM 808, low wobble answer, granular bass figure, offbeat push, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, low-mid orbit widens, accelerating hats, FM 808, low wobble answer, syncopated hats, 2 bars]

[inst - chest-sub, bass circles the low-mid, downbeat kick, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, kick run, tempo push, mono chest-sub, chest-sub melody, neuro wobble lead, room snare, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, chest-sub melody, driving sub pulse run, loose hats, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, octave sub stack, low-mid bass melody, square-wave pulse figure, pushed snare, 2 bars]

[inst - wavy phase sub, bass pans wide behind, low chest-sub, low reese counterline, granular bass figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, octave 808 stack, rising energy, mono chest-sub, body bass answer, wobble FM voice, chopped hats, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, layered sub stack, FM 808, low-mid bass melody, hat density up, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, beat stutter, rising energy, panning bass layer, octave sub stack, low-mid bass melody, offbeat push, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, octave 808 stack, rising energy, layered sub stack, mono chest-sub, body bass answer, distorted sub figure, straight hats, 2 bars]

[inst - neuro wobble sub, layers surround the ear, layered sub stack, stacked 808, chest-sub melody, double-time bass gallop, straight hats, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, downbeat impact, rising energy, parallel low-mid layer, FM 808, low-mid bass melody, phase-wavy synth line, triplet hats, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 1 | `[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, ...` |
| 2 | `331` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, tempo push, mono chest-sub, kick opens, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, wide laser stacked warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, acid squelch line, double-time bass gallop, kick tightens, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, octave 808 stack, multi-stack stacked warped drop, response line, double-time feel, mono chest-sub, body bass answer, double-time bass gallop, open hat, 2 bars]

[breakdown - neuro wobble sub, sub anchored, mids orbit, rapid hi-hats, tempo dip, octave 808 stack, FM 808, low wobble answer, phase-wavy synth line, pushed snare, 2 bars]

[drop - wavy phase sub, bass pans wide behind, panning bass layer, laser electric wreck wobble drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, square-wave pulse figure, fast bass triplets, closed hat, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, panning bass layer, phase-charged full send warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, staccato sub bursts, ghost notes, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, panning bass layer, laser electric full send warped drop, low wobble answer, double-time feel, body bass, wavy low-mid line, distorted sub figure, staccato sub bursts, chopped hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, octave sub stack, fast bass triplets, hat density up, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, layered sub stack, wide laser harder wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, rolling 808 run, hat density up, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, parallel low-mid layer, wide laser full send wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, granular bass figure, staccato sub bursts, triplet hats, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, side snare, 2 bars]

[drop - wavy phase sub, low-mid from every angle, panning bass layer, laser electric full send wobble drop, counter melody, double-time feel, body bass, chest-sub melody, wobble FM voice, staccato sub bursts, dry hats, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, panning bass layer, wide laser heavy reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, driving sub pulse run, offbeat push, 2 bars]

[build-up - FM warp sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, FM 808, low wobble answer, granular bass figure, offbeat push, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, low-mid orbit widens, accelerating hats, FM 808, low wobble answer, syncopated hats, 2 bars]

[inst - chest-sub, bass circles the low-mid, downbeat kick, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, kick run, tempo push, mono chest-sub, chest-sub melody, neuro wobble lead, room snare, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, body bass, chest-sub melody, driving sub pulse run, loose hats, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, octave sub stack, low-mid bass melody, square-wave pulse figure, pushed snare, 2 bars]

[inst - wavy phase sub, bass pans wide behind, low chest-sub, low reese counterline, granular bass figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, octave 808 stack, rising energy, mono chest-sub, body bass answer, wobble FM voice, chopped hats, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, beat stutter, rising energy, layered sub stack, FM 808, low-mid bass melody, hat density up, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, beat stutter, rising energy, panning bass layer, octave sub stack, low-mid bass melody, offbeat push, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[build-up - wavy phase sub, low-mid from every angle, kick tightens, octave 808 stack, rising energy, layered sub stack, mono chest-sub, body bass answer, distorted sub figure, straight hats, 2 bars]

[inst - neuro wobble sub, layers surround the ear, layered sub stack, stacked 808, chest-sub melody, double-time bass gallop, straight hats, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, downbeat impact, rising energy, parallel low-mid layer, FM 808, low-mid bass melody, phase-wavy synth line, triplet hats, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `331` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `89.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 2 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbe...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, laser electric wreck wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, granular bass figure, rolling 808 run, snare answers, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, low-mid orbit widens, tempo push, FM 808, snare answers, 2 bars]

[drop - FM warp sub, panning low-mid sweep, octave 808 stack, phase-charged stacked wobble drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, body bass, fast bass triplets, offbeat push, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, layered sub stack, phase-charged harder warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, double-time bass gallop, straight hats, 2 bars]

[build-up - wavy phase sub, 3D low-mid orbit, kick tightens, stutter gate, tempo push, mono chest-sub, ghost notes, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, low chest-sub, staccato sub bursts, dry hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, layered sub stack, phase-charged heavy reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, distorted sub figure, fast bass triplets, wide hat bed, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising energy, stacked 808, wavy low-mid line, wobble FM voice, wide hat bed, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, body bass, body bass answer, warped FM lead, double-time bass gallop, wide hat bed, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, octave 808 stack, laser electric wreck reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, rolling 808 run, rolling hats, 2 bars]

[build-up - wavy phase sub, 3D low-mid orbit, kick tightens, kick run, rising energy, stacked 808, wavy low-mid line, wobble FM voice, syncopated hats, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, body bass, body bass answer, rolling 808 run, syncopated hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, syncopated hats, 2 bars]

[drop - octave sub pulse, layers surround the ear, wide stereo layer, laser electric full send warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, driving sub pulse run, open hat, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, beat stutter, accelerating hats, FM 808, low reese counterline, granular bass figure, open hat, 2 bars]

[drop - FM warp sub, bass circles the low-mid, wide stereo layer, phase-charged wreck warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, phase-wavy synth line, rolling 808 run, open hat, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, octave 808 stack, accelerating hats, body bass, chest-sub melody, warped FM lead, closed hat, 2 bars]

[drop - phase-distorted sub, layers surround the ear, panning bass layer, phase-charged heavy reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, acid squelch line, fast bass triplets, room snare, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, warped FM lead, pushed snare, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, wide 3D bass field, panning bass layer, phase-charged stacked wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, neuro wobble lead, staccato sub bursts, hat density up, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, low-mid orbit widens, tempo push, panning bass layer, stacked 808, body bass answer, distorted sub figure, hat density up, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, panning bass layer, body bass, chest-sub melody, fast bass triplets, hat density up, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, phase-charged harder reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, double-time bass gallop, kick opens, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, panning bass layer, low chest-sub, low-mid bass melody, phase-wavy synth line, staccato sub bursts, straight hats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, layered sub stack, phase-charged heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, fast bass triplets, triplet hats, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, downbeat sub pulse, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, downbeat impact, rising energy, parallel low-mid layer, FM 808, low wobble answer, square-wave pulse figure, backbeat shove, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 1 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbe...` |
| 2 | `331` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `89.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, laser electric wreck wobble drop, counter-line, double-time feel, low chest-sub, low wobble answer, granular bass figure, rolling 808 run, snare answers, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, low-mid orbit widens, tempo push, FM 808, snare answers, 2 bars]

[drop - FM warp sub, panning low-mid sweep, octave 808 stack, phase-charged stacked wobble drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, body bass, fast bass triplets, offbeat push, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, layered sub stack, phase-charged harder warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, double-time bass gallop, straight hats, 2 bars]

[build-up - wavy phase sub, 3D low-mid orbit, kick tightens, stutter gate, tempo push, mono chest-sub, ghost notes, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, low chest-sub, staccato sub bursts, dry hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, layered sub stack, phase-charged heavy reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, distorted sub figure, fast bass triplets, wide hat bed, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising energy, stacked 808, wavy low-mid line, wobble FM voice, wide hat bed, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, body bass, body bass answer, warped FM lead, double-time bass gallop, wide hat bed, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, octave 808 stack, laser electric wreck reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, rolling 808 run, rolling hats, 2 bars]

[build-up - wavy phase sub, 3D low-mid orbit, kick tightens, kick run, rising energy, stacked 808, wavy low-mid line, wobble FM voice, syncopated hats, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, body bass, body bass answer, rolling 808 run, syncopated hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, syncopated hats, 2 bars]

[drop - octave sub pulse, layers surround the ear, wide stereo layer, laser electric full send warped drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, driving sub pulse run, open hat, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, beat stutter, accelerating hats, FM 808, low reese counterline, granular bass figure, open hat, 2 bars]

[drop - FM warp sub, bass circles the low-mid, wide stereo layer, phase-charged wreck warped drop, counter-line, double-time feel, octave sub stack, low wobble answer, phase-wavy synth line, rolling 808 run, open hat, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, octave 808 stack, accelerating hats, body bass, chest-sub melody, warped FM lead, closed hat, 2 bars]

[drop - phase-distorted sub, layers surround the ear, panning bass layer, phase-charged heavy reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, acid squelch line, fast bass triplets, room snare, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, warped FM lead, pushed snare, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, wide 3D bass field, panning bass layer, phase-charged stacked wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, neuro wobble lead, staccato sub bursts, hat density up, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, low-mid orbit widens, tempo push, panning bass layer, stacked 808, body bass answer, distorted sub figure, hat density up, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, panning bass layer, body bass, chest-sub melody, fast bass triplets, hat density up, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, phase-charged harder reese drop, counter-lead answers, double-time feel, octave sub stack, low-mid bass melody, double-time bass gallop, kick opens, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, panning bass layer, low chest-sub, low-mid bass melody, phase-wavy synth line, staccato sub bursts, straight hats, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, layered sub stack, phase-charged heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, fast bass triplets, triplet hats, 2 bars]

[build-up - octave sub pulse, panning low-mid sweep, downbeat sub pulse, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, downbeat impact, rising energy, parallel low-mid layer, FM 808, low wobble answer, square-wave pulse figure, backbeat shove, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `331` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 5 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `86.0` |
| 1 | `fixed` |

**Pass 5 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `86.0` |
| 1 | `1` |

**ez_edm_prompt pass 5** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 2 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energy surge, rising energy, FM 808, low reese counterline, neuro wobble lead, kick tightens, 2 bars]

[drop - FM warp sub, low-mid from every angle, octave 808 stack, full send laser stacked wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, driving sub pulse run, offbeat push, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, bass melody climbs, tempo push, FM 808, low wobble answer, distorted sub figure, offbeat push, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, octave sub stack, low-mid bass melody, wobble FM voice, rolling 808 run, offbeat push, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, octave-stacked electric stacked warped drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, wobble FM voice, driving sub pulse run, triplet hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, wide stereo layer, rising energy, octave sub stack, low reese counterline, triplet hats, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, laser electric tower stacked warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, stacked 808, body bass answer, acid squelch line, fast bass triplets, dry hats, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, layered sub stack, laser electric tower harder reese drop, response line, double-time feel, mono chest-sub, body bass answer, acid squelch line, staccato sub bursts, mono kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, energy surge, rising energy, stacked 808, chest-sub melody, mono kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, max stack laser harder wobble drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, granular bass figure, staccato sub bursts, rolling hats, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, low-mid climbs, accelerating hats, wide stereo layer, body bass, body bass answer, phase-wavy synth line, rolling hats, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, full send laser harder wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, wobble FM voice, staccato sub bursts, syncopated hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, bass melody climbs, tempo push, layered sub stack, FM 808, low wobble answer, warped FM lead, syncopated hats, 2 bars]

[inst - FM warp sub, layers surround the ear, wide stereo layer, low chest-sub, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, octave-stacked electric harder warped drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, neuro wobble lead, staccato sub bursts, closed hat, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, wide stereo layer, rising energy, wide stereo layer, octave sub stack, low reese counterline, distorted sub figure, closed hat, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric tower harder warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, staccato sub bursts, loose hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, low-mid climbs, accelerating hats, octave 808 stack, FM 808, low-mid bass melody, hat density up, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, max stack laser wreck warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, square-wave pulse figure, double-time bass gallop, snare answers, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, wide stereo layer, body bass, wavy low-mid line, acid squelch line, driving sub pulse run, chopped hats, 2 bars]

[drop - FM warp sub, panning low-mid sweep, octave 808 stack, laser electric tower heavy warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, neuro wobble lead, rolling 808 run, hat density up, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, layered sub stack, octave sub stack, low wobble answer, distorted sub figure, fast bass triplets, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, laser electric tower stacked reese drop, response line, double-time feel, mono chest-sub, body bass answer, driving sub pulse run, straight hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, kick doubles, tempo push, panning bass layer, low chest-sub, low wobble answer, distorted sub figure, triplet hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, layered sub stack, laser electric tower harder wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, staccato sub bursts, backbeat shove, 2 bars]

[outro - neuro wobble sub, low-mid orbits the sub, kick pattern flip, rapid hi-hats, octave sub stack, low wobble answer, ghost notes, 2 bars]
```

**ACE tags + lyrics (pass 5)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| 1 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| 2 | `331` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `86.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `F# minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energy surge, rising energy, FM 808, low reese counterline, neuro wobble lead, kick tightens, 2 bars]

[drop - FM warp sub, low-mid from every angle, octave 808 stack, full send laser stacked wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, driving sub pulse run, offbeat push, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, bass melody climbs, tempo push, FM 808, low wobble answer, distorted sub figure, offbeat push, 2 bars]

[inst - neuro wobble sub, panning low-mid sweep, octave sub stack, low-mid bass melody, wobble FM voice, rolling 808 run, offbeat push, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, layered sub stack, octave-stacked electric stacked warped drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, wobble FM voice, driving sub pulse run, triplet hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, wide stereo layer, rising energy, octave sub stack, low reese counterline, triplet hats, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, laser electric tower stacked warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, stacked 808, body bass answer, acid squelch line, fast bass triplets, dry hats, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, layered sub stack, laser electric tower harder reese drop, response line, double-time feel, mono chest-sub, body bass answer, acid squelch line, staccato sub bursts, mono kick, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, energy surge, rising energy, stacked 808, chest-sub melody, mono kick, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, max stack laser harder wobble drop, low wobble answer, double-time feel, stacked 808, wavy low-mid line, granular bass figure, staccato sub bursts, rolling hats, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, low-mid climbs, accelerating hats, wide stereo layer, body bass, body bass answer, phase-wavy synth line, rolling hats, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, full send laser harder wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, wobble FM voice, staccato sub bursts, syncopated hats, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, bass melody climbs, tempo push, layered sub stack, FM 808, low wobble answer, warped FM lead, syncopated hats, 2 bars]

[inst - FM warp sub, layers surround the ear, wide stereo layer, low chest-sub, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, octave-stacked electric harder warped drop, counter-lead answers, double-time feel, FM 808, low-mid bass melody, neuro wobble lead, staccato sub bursts, closed hat, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, wide stereo layer, rising energy, wide stereo layer, octave sub stack, low reese counterline, distorted sub figure, closed hat, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric tower harder warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, staccato sub bursts, loose hats, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, low-mid climbs, accelerating hats, octave 808 stack, FM 808, low-mid bass melody, hat density up, 2 bars]

[inst - phase-distorted sub, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, max stack laser wreck warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, square-wave pulse figure, double-time bass gallop, snare answers, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, wide stereo layer, body bass, wavy low-mid line, acid squelch line, driving sub pulse run, chopped hats, 2 bars]

[drop - FM warp sub, panning low-mid sweep, octave 808 stack, laser electric tower heavy warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, neuro wobble lead, rolling 808 run, hat density up, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, layered sub stack, octave sub stack, low wobble answer, distorted sub figure, fast bass triplets, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, laser electric tower stacked reese drop, response line, double-time feel, mono chest-sub, body bass answer, driving sub pulse run, straight hats, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, kick doubles, tempo push, panning bass layer, low chest-sub, low wobble answer, distorted sub figure, triplet hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, layered sub stack, laser electric tower harder wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, staccato sub bursts, backbeat shove, 2 bars]

[outro - neuro wobble sub, low-mid orbits the sub, kick pattern flip, rapid hi-hats, octave sub stack, low wobble answer, ghost notes, 2 bars]
```

**ACE sampler (pass 5)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `331` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `11-bounce-booth`

Catalog id `audio/albums/drive-through/hour-2/11-bounce-booth`.

US-safe EDM take: Drive-through bounce-booth chest bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `67.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 2 | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-e...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/11-bounce-booth` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-end pressure builds, rising energy, snare answers, warped 808 wreck, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, stacked warped drop, FM 808, low wobble answer, acid squelch line, trap drums denser, offbeat push, heavy chest drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, low-mid stack tightens, tempo push, straight hats, booth grind, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, harder reese drop, FM 808, low-mid bass melody, square-wave pulse figure, offbeat hats, triplet hats, rapid hi-hats roll, 2 bars]

[inst - octave sub pulse, layers surround the ear, ghost snare, backbeat shove, 808 punch hold, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, wreck wobble drop, FM 808, low reese counterline, rapid hi-hats, ghost notes, harder warped drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, kick pattern flip, wide hat bed, stacked chest-sub 808, 2 bars]

[drop - chest-sub, panning low-mid sweep, panning bass layer, harder wobble drop, double-time feel, stacked 808, chest-sub melody, warped FM lead, offbeat hats, mono kick, chest-sub wall, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, ghost snare, side snare, kick tightens, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, wreck warped drop, double-time feel, stacked 808, wavy low-mid line, neuro wobble lead, rapid hi-hats, rolling hats, chest-sub hold, 2 bars]

[inst - octave sub pulse, wide 3D bass field, trap drums denser, late snare, low 808 wreck, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, FM 808, offbeat hats, syncopated hats, warped chest, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, downbeat kick, 2 bars]

[inst - chest-sub, 3D low-mid orbit, FM 808, rapid hi-hats, closed hat, kick holds, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, wide stereo layer, stacked warped drop, stacked 808, wavy low-mid line, warped FM lead, trap drums denser, room snare, full send drop, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, panning bass layer, harder reese drop, double-time feel, stacked 808, body bass answer, neuro wobble lead, offbeat hats, loose hats, hats denser, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, FM 808, ghost snare, pushed snare, chest ride, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, parallel low-mid layer, wreck wobble drop, double-time feel, stacked 808, chest-sub melody, distorted sub figure, rapid hi-hats, chopped hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, FM 808, trap drums denser, hat density up, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, sub pickup, accelerating hats, stacked 808, kick opens, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 1 | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-e...` |
| 2 | `337` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-end pressure builds, rising energy, snare answers, warped 808 wreck, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, stacked warped drop, FM 808, low wobble answer, acid squelch line, trap drums denser, offbeat push, heavy chest drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, low-mid stack tightens, tempo push, straight hats, booth grind, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, harder reese drop, FM 808, low-mid bass melody, square-wave pulse figure, offbeat hats, triplet hats, rapid hi-hats roll, 2 bars]

[inst - octave sub pulse, layers surround the ear, ghost snare, backbeat shove, 808 punch hold, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, parallel low-mid layer, wreck wobble drop, FM 808, low reese counterline, rapid hi-hats, ghost notes, harder warped drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, downbeat kick, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, kick pattern flip, wide hat bed, stacked chest-sub 808, 2 bars]

[drop - chest-sub, panning low-mid sweep, panning bass layer, harder wobble drop, double-time feel, stacked 808, chest-sub melody, warped FM lead, offbeat hats, mono kick, chest-sub wall, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, ghost snare, side snare, kick tightens, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, parallel low-mid layer, wreck warped drop, double-time feel, stacked 808, wavy low-mid line, neuro wobble lead, rapid hi-hats, rolling hats, chest-sub hold, 2 bars]

[inst - octave sub pulse, wide 3D bass field, trap drums denser, late snare, low 808 wreck, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, FM 808, offbeat hats, syncopated hats, warped chest, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, downbeat kick, 2 bars]

[inst - chest-sub, 3D low-mid orbit, FM 808, rapid hi-hats, closed hat, kick holds, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, wide stereo layer, stacked warped drop, stacked 808, wavy low-mid line, warped FM lead, trap drums denser, room snare, full send drop, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, panning bass layer, harder reese drop, double-time feel, stacked 808, body bass answer, neuro wobble lead, offbeat hats, loose hats, hats denser, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, FM 808, ghost snare, pushed snare, chest ride, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, parallel low-mid layer, wreck wobble drop, double-time feel, stacked 808, chest-sub melody, distorted sub figure, rapid hi-hats, chopped hats, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, FM 808, trap drums denser, hat density up, 2 bars]

[build-up - chest-sub, bass circles the low-mid, kick tightens, sub pickup, accelerating hats, stacked 808, kick opens, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `337` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `11 - Bounce Booth` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `11 - Bounce Booth` |
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
| 1 | `Hour 2` |
| 2 | `Bounce Booth` |
| 3 | `11` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `11 - Bounce Booth` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 2 | `[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor ki...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/11-bounce-booth` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, wide 3D bass field, wide stereo layer, electric heavy warped drop, response line, FM 808, body bass answer, granular bass figure, offbeat hats, straight hats, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, ghost snare, triplet hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, panning bass layer, electric full send reese drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, rapid hi-hats, backbeat shove, 2 bars]

[build-up - chest-sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, electric stacked wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, acid squelch line, kick pattern flip, dry hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, electric wreck reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, phase-wavy synth line, trap drums denser, room snare, 2 bars]

[inst - FM warp sub, panning low-mid sweep, body bass, kick pattern flip, tight kick, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, electric heavy wobble drop, response line, octave sub stack, body bass answer, offbeat hats, loose hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, laser-lit wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, square-wave pulse figure, trap drums denser, loose hats, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, stacked 808, kick pattern flip, late snare, 2 bars]

[drop - chest-sub, panning low-mid sweep, panning bass layer, electric full send reese drop, second low-mid line, stacked 808, low reese counterline, rapid hi-hats, pushed snare, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, layered sub stack, electric wreck warped drop, response line, FM 808, body bass answer, phase-wavy synth line, trap drums denser, chopped hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, triplet hats, accelerating hats, FM 808, open hat, 2 bars]

[inst - octave sub pulse, layers surround the ear, stacked 808, trap drums denser, closed hat, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, side snare, rising energy, FM 808, room snare, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, stacked 808, low-mid bass melody, distorted sub figure, offbeat hats, tight kick, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - chest-sub, panning low-mid sweep, stacked 808, low reese counterline, rapid hi-hats, pushed snare, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, bass pressure builds, accelerating hats, FM 808, body bass answer, phase-wavy synth line, chopped hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, sub swell, rising energy, FM 808, chest-sub melody, acid squelch line, kick opens, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, sub pickup, accelerating hats, stacked 808, low-mid bass melody, neuro wobble lead, kick tightens, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 1 | `[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor ki...` |
| 2 | `337` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, wide 3D bass field, wide stereo layer, electric heavy warped drop, response line, FM 808, body bass answer, granular bass figure, offbeat hats, straight hats, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, ghost snare, triplet hats, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, panning bass layer, electric full send reese drop, counter melody, double-time feel, FM 808, chest-sub melody, phase-wavy synth line, rapid hi-hats, backbeat shove, 2 bars]

[build-up - chest-sub, layers surround the ear, sparse four-on-floor kick, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, electric stacked wobble drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, acid squelch line, kick pattern flip, dry hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, parallel low-mid layer, electric wreck reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, phase-wavy synth line, trap drums denser, room snare, 2 bars]

[inst - FM warp sub, panning low-mid sweep, body bass, kick pattern flip, tight kick, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, octave 808 stack, electric heavy wobble drop, response line, octave sub stack, body bass answer, offbeat hats, loose hats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, laser-lit wreck wobble drop, counter melody, double-time feel, low chest-sub, chest-sub melody, square-wave pulse figure, trap drums denser, loose hats, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, stacked 808, kick pattern flip, late snare, 2 bars]

[drop - chest-sub, panning low-mid sweep, panning bass layer, electric full send reese drop, second low-mid line, stacked 808, low reese counterline, rapid hi-hats, pushed snare, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, layered sub stack, electric wreck warped drop, response line, FM 808, body bass answer, phase-wavy synth line, trap drums denser, chopped hats, 2 bars]

[build-up - bitcrushed 808, bass pans wide behind, kick tightens, triplet hats, accelerating hats, FM 808, open hat, 2 bars]

[inst - octave sub pulse, layers surround the ear, stacked 808, trap drums denser, closed hat, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, side snare, rising energy, FM 808, room snare, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, stacked 808, low-mid bass melody, distorted sub figure, offbeat hats, tight kick, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - chest-sub, panning low-mid sweep, stacked 808, low reese counterline, rapid hi-hats, pushed snare, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, bass pressure builds, accelerating hats, FM 808, body bass answer, phase-wavy synth line, chopped hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, sub swell, rising energy, FM 808, chest-sub melody, acid squelch line, kick opens, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick tightens, sub pickup, accelerating hats, stacked 808, low-mid bass melody, neuro wobble lead, kick tightens, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `337` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 2 | `[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/11-bounce-booth` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, tempo push, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser-lit full send reese drop, counter melody, mono chest-sub, chest-sub melody, warped FM lead, offbeat hats, ghost notes, 2 bars]

[inst - octave sub pulse, low-mid from every angle, downbeat kick, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, accelerating hats, tempo push, wide hat bed, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, parallel low-mid layer, laser-lit heavy reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, trap drums denser, mono kick, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, FM 808, offbeat hats, kick opens, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, laser-lit full send wobble drop, counter-line, low chest-sub, low wobble answer, granular bass figure, offbeat hats, rolling hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, triplet hats, rising energy, mono chest-sub, late snare, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, stacked 808, trap drums denser, offbeat push, 2 bars]

[drop - chest-sub, low-mid from every angle, parallel low-mid layer, laser-lit heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, trap drums denser, syncopated hats, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, accelerating hats, rising energy, low chest-sub, open hat, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, electric wreck wobble drop, counter-lead answers, FM 808, low-mid bass melody, acid squelch line, ghost snare, backbeat shove, 2 bars]

[inst - octave sub pulse, bass pans wide behind, kick only on downbeats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, bass pressure builds, rising energy, mono chest-sub, tight kick, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, stacked 808, kick pattern flip, wide hat bed, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, wide stereo layer, laser-lit harder wobble drop, low wobble answer, mono chest-sub, wavy low-mid line, wobble FM voice, kick pattern flip, pushed snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser-lit wreck wobble drop, response line, stacked 808, body bass answer, distorted sub figure, ghost snare, syncopated hats, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, accelerating hats, rising energy, octave sub stack, low reese counterline, acid squelch line, rolling hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, laser-lit heavy reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, kick tightens, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, low chest-sub, low-mid bass melody, square-wave pulse figure, snare answers, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, mono chest-sub, wavy low-mid line, offbeat hats, offbeat push, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, bass returns, rising energy, low chest-sub, low reese counterline, straight hats, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 1 | `[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, ...` |
| 2 | `337` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, tempo push, backbeat shove, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser-lit full send reese drop, counter melody, mono chest-sub, chest-sub melody, warped FM lead, offbeat hats, ghost notes, 2 bars]

[inst - octave sub pulse, low-mid from every angle, downbeat kick, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, accelerating hats, tempo push, wide hat bed, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, parallel low-mid layer, laser-lit heavy reese drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, square-wave pulse figure, trap drums denser, mono kick, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, FM 808, offbeat hats, kick opens, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, laser-lit full send wobble drop, counter-line, low chest-sub, low wobble answer, granular bass figure, offbeat hats, rolling hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, triplet hats, rising energy, mono chest-sub, late snare, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, stacked 808, trap drums denser, offbeat push, 2 bars]

[drop - chest-sub, low-mid from every angle, parallel low-mid layer, laser-lit heavy wobble drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, warped FM lead, trap drums denser, syncopated hats, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, accelerating hats, rising energy, low chest-sub, open hat, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, electric wreck wobble drop, counter-lead answers, FM 808, low-mid bass melody, acid squelch line, ghost snare, backbeat shove, 2 bars]

[inst - octave sub pulse, bass pans wide behind, kick only on downbeats, 2 bars]

[build-up - FM warp sub, layers surround the ear, kick tightens, bass pressure builds, rising energy, mono chest-sub, tight kick, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, stacked 808, kick pattern flip, wide hat bed, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, wide stereo layer, laser-lit harder wobble drop, low wobble answer, mono chest-sub, wavy low-mid line, wobble FM voice, kick pattern flip, pushed snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, layered sub stack, laser-lit wreck wobble drop, response line, stacked 808, body bass answer, distorted sub figure, ghost snare, syncopated hats, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, accelerating hats, rising energy, octave sub stack, low reese counterline, acid squelch line, rolling hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, parallel low-mid layer, laser-lit heavy reese drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, neuro wobble lead, trap drums denser, kick tightens, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, bass pressure builds, accelerating hats, low chest-sub, low-mid bass melody, square-wave pulse figure, snare answers, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, mono chest-sub, wavy low-mid line, offbeat hats, offbeat push, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, kick tightens, bass returns, rising energy, low chest-sub, low reese counterline, straight hats, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `337` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 2 | `[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy sur...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/11-bounce-booth` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy surge, accelerating hats, octave sub stack, low wobble answer, wobble FM voice, triplet hats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, max stack laser full send warped drop, counter melody, double-time feel, body bass, chest-sub melody, double-time bass gallop, backbeat shove, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, bass melody climbs, rising energy, octave sub stack, low-mid bass melody, warped FM lead, ghost notes, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, max stack laser stacked reese drop, low wobble answer, double-time feel, body bass, wavy low-mid line, acid squelch line, rolling 808 run, dry hats, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, body bass, body bass answer, fast bass triplets, mono kick, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, wide stereo layer, max stack laser wreck wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, driving sub pulse run, late snare, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody climbs, rising energy, mono chest-sub, body bass answer, square-wave pulse figure, early kick, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, distorted sub figure, staccato sub bursts, syncopated hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, panning bass layer, octave-stacked electric harder warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, warped FM lead, fast bass triplets, syncopated hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, parallel low-mid layer, octave sub stack, low wobble answer, driving sub pulse run, closed hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, panning bass layer, octave-stacked electric heavy reese drop, response line, double-time feel, mono chest-sub, body bass answer, staccato sub bursts, loose hats, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, layered sub stack, low chest-sub, low wobble answer, neuro wobble lead, fast bass triplets, pushed snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, octave-stacked electric full send wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, double-time bass gallop, chopped hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, max stack laser wreck wobble drop, response line, double-time feel, body bass, body bass answer, driving sub pulse run, chopped hats, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, wide stereo layer, octave sub stack, low wobble answer, rolling 808 run, hat density up, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, parallel low-mid layer, tempo push, octave 808 stack, body bass, chest-sub melody, acid squelch line, kick opens, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, max stack laser full send warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, double-time bass gallop, offbeat push, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, wide stereo layer, mono chest-sub, chest-sub melody, driving sub pulse run, straight hats, 2 bars]

[outro - octave sub pulse, low-mid from every angle, kick pattern flip, rapid hi-hats, body bass, body bass answer, straight hats, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| 1 | `[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy sur...` |
| 2 | `337` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy surge, accelerating hats, octave sub stack, low wobble answer, wobble FM voice, triplet hats, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, max stack laser full send warped drop, counter melody, double-time feel, body bass, chest-sub melody, double-time bass gallop, backbeat shove, 2 bars]

[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, bass melody climbs, rising energy, octave sub stack, low-mid bass melody, warped FM lead, ghost notes, 2 bars]

[drop - FM warp sub, low-mid from every angle, wide stereo layer, max stack laser stacked reese drop, low wobble answer, double-time feel, body bass, wavy low-mid line, acid squelch line, rolling 808 run, dry hats, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[inst - phase-distorted sub, bass circles the low-mid, body bass, body bass answer, fast bass triplets, mono kick, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, wide stereo layer, max stack laser wreck wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, neuro wobble lead, driving sub pulse run, late snare, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody climbs, rising energy, mono chest-sub, body bass answer, square-wave pulse figure, early kick, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, distorted sub figure, staccato sub bursts, syncopated hats, 2 bars]

[build-up - chest-sub, bass pans wide behind, kick only on downbeats, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, panning bass layer, octave-stacked electric harder warped drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, warped FM lead, fast bass triplets, syncopated hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, downbeat sub pulse, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, parallel low-mid layer, octave sub stack, low wobble answer, driving sub pulse run, closed hat, 2 bars]

[drop - wavy phase sub, layers surround the ear, panning bass layer, octave-stacked electric heavy reese drop, response line, double-time feel, mono chest-sub, body bass answer, staccato sub bursts, loose hats, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, layered sub stack, low chest-sub, low wobble answer, neuro wobble lead, fast bass triplets, pushed snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, parallel low-mid layer, octave-stacked electric full send wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, double-time bass gallop, chopped hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - FM warp sub, layers surround the ear, parallel low-mid layer, max stack laser wreck wobble drop, response line, double-time feel, body bass, body bass answer, driving sub pulse run, chopped hats, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, wide stereo layer, octave sub stack, low wobble answer, rolling 808 run, hat density up, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, parallel low-mid layer, tempo push, octave 808 stack, body bass, chest-sub melody, acid squelch line, kick opens, 2 bars]

[drop - wavy phase sub, wide 3D bass field, parallel low-mid layer, max stack laser full send warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, double-time bass gallop, offbeat push, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, wide stereo layer, mono chest-sub, chest-sub melody, driving sub pulse run, straight hats, 2 bars]

[outro - octave sub pulse, low-mid from every angle, kick pattern flip, rapid hi-hats, body bass, body bass answer, straight hats, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `337` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `165` |
| 1 | `1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `12-toll-growl`

Catalog id `audio/albums/drive-through/hour-2/12-toll-growl`.

US-safe EDM take: Drive-through toll-growl riddim warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 2 | `[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/12-toll-growl` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, heavy reese drop, mono chest-sub, low wobble answer, phase-wavy synth line, kick pattern flip, loose hats, wobble bass, heavy riddim drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub energy lifts, accelerating hats, pushed snare, tearout wobble wreck, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, ghost snare, chopped hats, warped toll, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, wreck reese drop, double-time feel, low chest-sub, wavy low-mid line, neuro wobble lead, rapid hi-hats, hat density up, rapid hi-hats roll, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, mono kick punch, accelerating hats, kick opens, warped sustain, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, kick pattern flip, kick tightens, sub crush, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, harder reese drop, mono chest-sub, low wobble answer, offbeat hats, snare answers, harder warped drop, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, wreck wobble drop, mono chest-sub, low-mid bass melody, phase-wavy synth line, rapid hi-hats, straight hats, chest-sub 808, 2 bars]

[inst - phase-distorted sub, layers surround the ear, trap drums denser, triplet hats, rapid hi-hats denser, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, heavy warped drop, mono chest-sub, low reese counterline, acid squelch line, kick pattern flip, backbeat shove, warped hold, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, mono kick punch, tempo push, ghost notes, stacked wobble wreck, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, mono chest-sub, ghost snare, dry hats, wobble wall, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, layered sub stack, wreck warped drop, double-time feel, low chest-sub, chest-sub melody, distorted sub figure, rapid hi-hats, wide hat bed, full send drop, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-mid stack tightens, tempo push, mono chest-sub, mono kick, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, octave 808 stack, harder warped drop, double-time feel, mono chest-sub, low reese counterline, offbeat hats, rolling hats, bass warped hold, 2 bars]

[inst - chest-sub, bass circles the low-mid, low chest-sub, ghost snare, late snare, low rumble, 2 bars]

[drop - wavy phase sub, bass pans wide behind, layered sub stack, wreck reese drop, double-time feel, mono chest-sub, low wobble answer, rapid hi-hats, early kick, kick holds, 2 bars]

[inst - bitcrushed 808, layers surround the ear, low chest-sub, trap drums denser, syncopated hats, hats denser, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, heavy wobble drop, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick pattern flip, open hat, warped ride, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, kick stomp, rising energy, low chest-sub, closed hat, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 1 | `[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, ...` |
| 2 | `347` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, heavy reese drop, mono chest-sub, low wobble answer, phase-wavy synth line, kick pattern flip, loose hats, wobble bass, heavy riddim drop, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub energy lifts, accelerating hats, pushed snare, tearout wobble wreck, 2 bars]

[inst - phase-distorted sub, sub anchored, mids orbit, ghost snare, chopped hats, warped toll, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, wreck reese drop, double-time feel, low chest-sub, wavy low-mid line, neuro wobble lead, rapid hi-hats, hat density up, rapid hi-hats roll, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, mono kick punch, accelerating hats, kick opens, warped sustain, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, kick pattern flip, kick tightens, sub crush, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, harder reese drop, mono chest-sub, low wobble answer, offbeat hats, snare answers, harder warped drop, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, wreck wobble drop, mono chest-sub, low-mid bass melody, phase-wavy synth line, rapid hi-hats, straight hats, chest-sub 808, 2 bars]

[inst - phase-distorted sub, layers surround the ear, trap drums denser, triplet hats, rapid hi-hats denser, 2 bars]

[drop - chest-sub, 3D low-mid orbit, wide stereo layer, heavy warped drop, mono chest-sub, low reese counterline, acid squelch line, kick pattern flip, backbeat shove, warped hold, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, mono kick punch, tempo push, ghost notes, stacked wobble wreck, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, mono chest-sub, ghost snare, dry hats, wobble wall, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, layered sub stack, wreck warped drop, double-time feel, low chest-sub, chest-sub melody, distorted sub figure, rapid hi-hats, wide hat bed, full send drop, 2 bars]

[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-mid stack tightens, tempo push, mono chest-sub, mono kick, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, octave 808 stack, harder warped drop, double-time feel, mono chest-sub, low reese counterline, offbeat hats, rolling hats, bass warped hold, 2 bars]

[inst - chest-sub, bass circles the low-mid, low chest-sub, ghost snare, late snare, low rumble, 2 bars]

[drop - wavy phase sub, bass pans wide behind, layered sub stack, wreck reese drop, double-time feel, mono chest-sub, low wobble answer, rapid hi-hats, early kick, kick holds, 2 bars]

[inst - bitcrushed 808, layers surround the ear, low chest-sub, trap drums denser, syncopated hats, hats denser, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, heavy wobble drop, mono chest-sub, low-mid bass melody, square-wave pulse figure, kick pattern flip, open hat, warped ride, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, kick stomp, rising energy, low chest-sub, closed hat, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `347` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `12 - Toll Growl` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `12 - Toll Growl` |
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
| 1 | `Hour 2` |
| 2 | `Toll Growl` |
| 3 | `12` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `12 - Toll Growl` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, ri...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/12-toll-growl` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, rising energy, stacked 808, loose hats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, wide laser harder reese drop, response line, double-time feel, FM 808, body bass answer, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, rolling hats, tempo push, stacked 808, chopped hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, wide laser wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, rolling 808 run, hat density up, 2 bars]

[inst - FM warp sub, panning low-mid sweep, stacked 808, staccato sub bursts, kick opens, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, wide laser heavy warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, stacked 808, double-time bass gallop, snare answers, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, wide laser full send reese drop, response line, double-time feel, FM 808, body bass answer, driving sub pulse run, offbeat push, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, wide laser stacked wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, staccato sub bursts, triplet hats, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, low-mid bass melody, backbeat shove, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, FM 808, wavy low-mid line, wobble FM voice, double-time bass gallop, ghost notes, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, wide stereo layer, multi-stack full send wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - chest-sub, panning low-mid sweep, stacked 808, low wobble answer, staccato sub bursts, mono kick, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, layered sub stack, wide laser heavy wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, neuro wobble lead, fast bass triplets, side snare, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, wide stereo layer, wide laser full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, driving sub pulse run, late snare, 2 bars]

[inst - FM warp sub, bass circles the low-mid, octave 808 stack, stacked 808, low reese counterline, rolling 808 run, early kick, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, panning bass layer, FM 808, body bass answer, wobble FM voice, syncopated hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, layered sub stack, stacked 808, low wobble answer, fast bass triplets, open hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, parallel low-mid layer, wide laser harder wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, warped FM lead, double-time bass gallop, closed hat, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick stomp, accelerating hats, wide stereo layer, stacked 808, low-mid bass melody, room snare, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 1 | `[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, ri...` |
| 2 | `347` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, rising energy, stacked 808, loose hats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, wide laser harder reese drop, response line, double-time feel, FM 808, body bass answer, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, rolling hats, tempo push, stacked 808, chopped hats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, octave 808 stack, wide laser wreck wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, rolling 808 run, hat density up, 2 bars]

[inst - FM warp sub, panning low-mid sweep, stacked 808, staccato sub bursts, kick opens, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, layered sub stack, wide laser heavy warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[inst - phase-distorted sub, low-mid from every angle, stacked 808, double-time bass gallop, snare answers, 2 bars]

[drop - chest-sub, wide 3D bass field, wide stereo layer, wide laser full send reese drop, response line, double-time feel, FM 808, body bass answer, driving sub pulse run, offbeat push, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, panning bass layer, wide laser stacked wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, staccato sub bursts, triplet hats, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, stacked 808, low-mid bass melody, backbeat shove, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, FM 808, wavy low-mid line, wobble FM voice, double-time bass gallop, ghost notes, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, wide stereo layer, multi-stack full send wobble drop, second low-mid line, double-time feel, stacked 808, low reese counterline, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - chest-sub, panning low-mid sweep, stacked 808, low wobble answer, staccato sub bursts, mono kick, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, layered sub stack, wide laser heavy wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, neuro wobble lead, fast bass triplets, side snare, 2 bars]

[build-up - bitcrushed 808, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, wide stereo layer, wide laser full send warped drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, driving sub pulse run, late snare, 2 bars]

[inst - FM warp sub, bass circles the low-mid, octave 808 stack, stacked 808, low reese counterline, rolling 808 run, early kick, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, low-mid orbit widens, accelerating hats, panning bass layer, FM 808, body bass answer, wobble FM voice, syncopated hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, layered sub stack, stacked 808, low wobble answer, fast bass triplets, open hat, 2 bars]

[drop - chest-sub, 3D low-mid orbit, parallel low-mid layer, wide laser harder wobble drop, counter melody, double-time feel, FM 808, chest-sub melody, warped FM lead, double-time bass gallop, closed hat, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick stomp, accelerating hats, wide stereo layer, stacked 808, low-mid bass melody, room snare, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `347` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `91.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `91.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 2 | `[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody c...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/12-toll-growl` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody climbs, accelerating hats, body bass, low wobble answer, wobble FM voice, hat density up, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, wide stereo layer, octave-stacked electric wreck wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, phase-wavy synth line, double-time bass gallop, kick opens, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, parallel low-mid layer, rising energy, body bass, low-mid bass melody, kick tightens, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, layered sub stack, max stack laser harder wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, neuro wobble lead, staccato sub bursts, offbeat push, 2 bars]

[build-up - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - wavy phase sub, layers surround the ear, body bass, low wobble answer, double-time bass gallop, triplet hats, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, octave-stacked electric stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, granular bass figure, driving sub pulse run, backbeat shove, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, parallel low-mid layer, rising energy, body bass, low-mid bass melody, ghost notes, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, layered sub stack, octave-stacked electric harder warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, staccato sub bursts, dry hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, energy surge, tempo push, parallel low-mid layer, body bass, low reese counterline, warped FM lead, wide hat bed, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, octave-stacked electric wreck reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, double-time bass gallop, mono kick, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, bass melody climbs, accelerating hats, octave 808 stack, body bass, low wobble answer, neuro wobble lead, side snare, 2 bars]

[inst - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, max stack laser harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, staccato sub bursts, late snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, parallel low-mid layer, octave sub stack, wavy low-mid line, granular bass figure, fast bass triplets, early kick, 2 bars]

[drop - FM warp sub, layers surround the ear, wide stereo layer, max stack laser wreck wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, wobble FM voice, double-time bass gallop, syncopated hats, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, octave 808 stack, octave sub stack, body bass answer, phase-wavy synth line, driving sub pulse run, open hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, body bass, low wobble answer, rolling 808 run, closed hat, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, energy surge, tempo push, layered sub stack, octave sub stack, chest-sub melody, acid squelch line, room snare, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, parallel low-mid layer, max stack laser full send reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, fast bass triplets, tight kick, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, wide stereo layer, octave sub stack, wavy low-mid line, square-wave pulse figure, double-time bass gallop, loose hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, max stack laser stacked wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, distorted sub figure, driving sub pulse run, pushed snare, 2 bars]

[inst - FM warp sub, wide 3D bass field, panning bass layer, octave sub stack, body bass answer, rolling 808 run, chopped hats, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, layered sub stack, max stack laser harder warped drop, counter-line, double-time feel, body bass, low wobble answer, wobble FM voice, staccato sub bursts, hat density up, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - chest-sub, layers surround the ear, wide stereo layer, body bass, low-mid bass melody, double-time bass gallop, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, octave-stacked electric stacked warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, acid squelch line, driving sub pulse run, snare answers, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, energy surge, tempo push, panning bass layer, body bass, low reese counterline, neuro wobble lead, offbeat push, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, layered sub stack, octave sub stack, body bass answer, square-wave pulse figure, staccato sub bursts, straight hats, 2 bars]

[drop - FM warp sub, panning low-mid sweep, parallel low-mid layer, full send warped drop, sub pickup, counter-line, double-time feel, body bass, low wobble answer, fast bass triplets, triplet hats, 2 bars]

[outro - neuro wobble sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, octave sub stack, chest-sub melody, backbeat shove, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| 1 | `[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody c...` |
| 2 | `347` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `91.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `A minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody climbs, accelerating hats, body bass, low wobble answer, wobble FM voice, hat density up, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, wide stereo layer, octave-stacked electric wreck wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, phase-wavy synth line, double-time bass gallop, kick opens, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, parallel low-mid layer, rising energy, body bass, low-mid bass melody, kick tightens, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, layered sub stack, max stack laser harder wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, neuro wobble lead, staccato sub bursts, offbeat push, 2 bars]

[build-up - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - wavy phase sub, layers surround the ear, body bass, low wobble answer, double-time bass gallop, triplet hats, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, octave-stacked electric stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, granular bass figure, driving sub pulse run, backbeat shove, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, parallel low-mid layer, rising energy, body bass, low-mid bass melody, ghost notes, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, layered sub stack, octave-stacked electric harder warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, staccato sub bursts, dry hats, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, energy surge, tempo push, parallel low-mid layer, body bass, low reese counterline, warped FM lead, wide hat bed, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, octave-stacked electric wreck reese drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, double-time bass gallop, mono kick, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, bass melody climbs, accelerating hats, octave 808 stack, body bass, low wobble answer, neuro wobble lead, side snare, 2 bars]

[inst - wavy phase sub, wide 3D bass field, downbeat kick, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, layered sub stack, max stack laser harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, distorted sub figure, staccato sub bursts, late snare, 2 bars]

[inst - octave sub pulse, bass pans wide behind, parallel low-mid layer, octave sub stack, wavy low-mid line, granular bass figure, fast bass triplets, early kick, 2 bars]

[drop - FM warp sub, layers surround the ear, wide stereo layer, max stack laser wreck wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, wobble FM voice, double-time bass gallop, syncopated hats, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, octave 808 stack, octave sub stack, body bass answer, phase-wavy synth line, driving sub pulse run, open hat, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, panning bass layer, max stack laser heavy warped drop, counter-line, double-time feel, body bass, low wobble answer, rolling 808 run, closed hat, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, kick tightens, energy surge, tempo push, layered sub stack, octave sub stack, chest-sub melody, acid squelch line, room snare, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, parallel low-mid layer, max stack laser full send reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, fast bass triplets, tight kick, 2 bars]

[inst - bitcrushed 808, sub center, low-mid moves wide, wide stereo layer, octave sub stack, wavy low-mid line, square-wave pulse figure, double-time bass gallop, loose hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, octave 808 stack, max stack laser stacked wobble drop, second low-mid line, double-time feel, body bass, low reese counterline, distorted sub figure, driving sub pulse run, pushed snare, 2 bars]

[inst - FM warp sub, wide 3D bass field, panning bass layer, octave sub stack, body bass answer, rolling 808 run, chopped hats, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, layered sub stack, max stack laser harder warped drop, counter-line, double-time feel, body bass, low wobble answer, wobble FM voice, staccato sub bursts, hat density up, 2 bars]

[build-up - phase-distorted sub, bass pans wide behind, downbeat kick, 2 bars]

[inst - chest-sub, layers surround the ear, wide stereo layer, body bass, low-mid bass melody, double-time bass gallop, kick tightens, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, octave 808 stack, octave-stacked electric stacked warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, acid squelch line, driving sub pulse run, snare answers, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, energy surge, tempo push, panning bass layer, body bass, low reese counterline, neuro wobble lead, offbeat push, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, layered sub stack, octave sub stack, body bass answer, square-wave pulse figure, staccato sub bursts, straight hats, 2 bars]

[drop - FM warp sub, panning low-mid sweep, parallel low-mid layer, full send warped drop, sub pickup, counter-line, double-time feel, body bass, low wobble answer, fast bass triplets, triplet hats, 2 bars]

[outro - neuro wobble sub, sub center, low-mid moves wide, kick pattern flip, rapid hi-hats, octave sub stack, chest-sub melody, backbeat shove, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `347` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `13-night-oil`

Catalog id `audio/albums/drive-through/hour-2/13-night-oil`.

US-safe EDM take: Drive-through night-oil hybrid trap warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `79.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `79.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 2 | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass ...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/13-night-oil` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass pressure builds, rising energy, kick tightens, warped 808 wreck, 2 bars]

[drop - chest-sub, wide 3D bass field, parallel low-mid layer, electric harder reese drop, second low-mid line, body bass, low reese counterline, ghost snare, snare answers, festival trap, heavy hybrid drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, sub swell, tempo push, offbeat push, oil grind, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, electric wreck wobble drop, counter-line, body bass, low wobble answer, trap drums denser, straight hats, rapid hi-hats roll, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, accelerating hats, octave sub stack, triplet hats, 808 slide, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, body bass, offbeat hats, backbeat shove, trap bass wall, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, parallel low-mid layer, electric harder wobble drop, low wobble answer, octave sub stack, wavy low-mid line, acid squelch line, ghost snare, ghost notes, harder warped drop, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, kick tightens, bass pressure builds, accelerating hats, body bass, dry hats, chest-sub crush, 2 bars]

[inst - chest-sub, panning low-mid sweep, octave sub stack, trap drums denser, wide hat bed, chest-sub wreck, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, electric stacked wobble drop, counter-line, body bass, low wobble answer, distorted sub figure, kick pattern flip, mono kick, full send drop, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, parallel low-mid layer, electric harder warped drop, counter-lead answers, body bass, low-mid bass melody, ghost snare, rolling hats, hybrid warp, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, body bass, trap drums denser, early kick, kick holds, 2 bars]

[drop - phase-distorted sub, layers surround the ear, panning bass layer, electric stacked warped drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, kick pattern flip, syncopated hats, 808 ride, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, offbeat hats, open hat, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, parallel low-mid layer, electric harder reese drop, counter melody, octave sub stack, chest-sub melody, ghost snare, closed hat, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, body bass, rapid hi-hats, room snare, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, octave 808 stack, electric wreck wobble drop, low wobble answer, octave sub stack, wavy low-mid line, trap drums denser, tight kick, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, electric heavy warped drop, response line, octave sub stack, body bass answer, phase-wavy synth line, offbeat hats, pushed snare, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, bass pressure builds, rising energy, body bass, low wobble answer, warped FM lead, chopped hats, 2 bars]

[drop - chest-sub, bass circles the low-mid, wide stereo layer, electric full send reese drop, counter melody, octave sub stack, chest-sub melody, rapid hi-hats, hat density up, 2 bars]

[inst - wavy phase sub, bass pans wide behind, body bass, low-mid bass melody, trap drums denser, kick opens, 2 bars]

[drop - bitcrushed 808, layers surround the ear, panning bass layer, electric stacked wobble drop, low wobble answer, octave sub stack, wavy low-mid line, square-wave pulse figure, kick pattern flip, kick tightens, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, accelerating hats, body bass, low reese counterline, snare answers, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, bass returns, tempo push, octave sub stack, body bass answer, offbeat push, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 1 | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass ...` |
| 2 | `349` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `79.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass pressure builds, rising energy, kick tightens, warped 808 wreck, 2 bars]

[drop - chest-sub, wide 3D bass field, parallel low-mid layer, electric harder reese drop, second low-mid line, body bass, low reese counterline, ghost snare, snare answers, festival trap, heavy hybrid drop, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, sub swell, tempo push, offbeat push, oil grind, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, electric wreck wobble drop, counter-line, body bass, low wobble answer, trap drums denser, straight hats, rapid hi-hats roll, 2 bars]

[build-up - octave sub pulse, layers surround the ear, kick tightens, accelerating hats, octave sub stack, triplet hats, 808 slide, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, body bass, offbeat hats, backbeat shove, trap bass wall, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, parallel low-mid layer, electric harder wobble drop, low wobble answer, octave sub stack, wavy low-mid line, acid squelch line, ghost snare, ghost notes, harder warped drop, 2 bars]

[build-up - phase-distorted sub, sub anchored, mids orbit, kick tightens, bass pressure builds, accelerating hats, body bass, dry hats, chest-sub crush, 2 bars]

[inst - chest-sub, panning low-mid sweep, octave sub stack, trap drums denser, wide hat bed, chest-sub wreck, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, electric stacked wobble drop, counter-line, body bass, low wobble answer, distorted sub figure, kick pattern flip, mono kick, full send drop, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, kick only on downbeats, 2 bars]

[drop - octave sub pulse, wide 3D bass field, parallel low-mid layer, electric harder warped drop, counter-lead answers, body bass, low-mid bass melody, ghost snare, rolling hats, hybrid warp, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[inst - neuro wobble sub, bass pans wide behind, body bass, trap drums denser, early kick, kick holds, 2 bars]

[drop - phase-distorted sub, layers surround the ear, panning bass layer, electric stacked warped drop, response line, double-time feel, octave sub stack, body bass answer, acid squelch line, kick pattern flip, syncopated hats, 808 ride, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, offbeat hats, open hat, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, parallel low-mid layer, electric harder reese drop, counter melody, octave sub stack, chest-sub melody, ghost snare, closed hat, 2 bars]

[inst - bitcrushed 808, sub anchored, mids orbit, body bass, rapid hi-hats, room snare, 2 bars]

[drop - octave sub pulse, panning low-mid sweep, octave 808 stack, electric wreck wobble drop, low wobble answer, octave sub stack, wavy low-mid line, trap drums denser, tight kick, 2 bars]

[inst - FM warp sub, sub center, low-mid moves wide, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, low-mid from every angle, layered sub stack, electric heavy warped drop, response line, octave sub stack, body bass answer, phase-wavy synth line, offbeat hats, pushed snare, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, kick tightens, bass pressure builds, rising energy, body bass, low wobble answer, warped FM lead, chopped hats, 2 bars]

[drop - chest-sub, bass circles the low-mid, wide stereo layer, electric full send reese drop, counter melody, octave sub stack, chest-sub melody, rapid hi-hats, hat density up, 2 bars]

[inst - wavy phase sub, bass pans wide behind, body bass, low-mid bass melody, trap drums denser, kick opens, 2 bars]

[drop - bitcrushed 808, layers surround the ear, panning bass layer, electric stacked wobble drop, low wobble answer, octave sub stack, wavy low-mid line, square-wave pulse figure, kick pattern flip, kick tightens, 2 bars]

[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, accelerating hats, body bass, low reese counterline, snare answers, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, bass returns, tempo push, octave sub stack, body bass answer, offbeat push, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `349` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `13 - Night Oil` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `13 - Night Oil` |
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
| 1 | `Hour 2` |
| 2 | `Night Oil` |
| 3 | `13` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `13 - Night Oil` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, risin...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/13-night-oil` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, rising energy, offbeat push, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, electric heavy warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, ghost snare, straight hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, laser-lit stacked wobble drop, response line, double-time feel, low chest-sub, body bass answer, offbeat hats, triplet hats, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, laser-lit full send warped drop, counter melody, low chest-sub, chest-sub melody, trap drums denser, late snare, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, downbeat kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, wide stereo layer, laser-lit wreck warped drop, counter-line, stacked 808, low wobble answer, kick pattern flip, mono kick, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, gated bass, accelerating hats, stacked 808, room snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, parallel low-mid layer, laser-lit full send warped drop, low wobble answer, FM 808, wavy low-mid line, trap drums denser, tight kick, 2 bars]

[drop - phase-distorted sub, layers surround the ear, parallel low-mid layer, laser-lit wreck wobble drop, response line, low chest-sub, body bass answer, phase-wavy synth line, kick pattern flip, closed hat, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, tom run, tempo push, body bass, loose hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, octave 808 stack, laser-lit heavy warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, acid squelch line, ghost snare, tight kick, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, laser-lit harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rapid hi-hats, loose hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, octave sub stack, offbeat hats, hat density up, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, sub swell, tempo push, octave sub stack, closed hat, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, body bass, offbeat hats, room snare, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, bass pressure builds, tempo push, mono chest-sub, low wobble answer, warped FM lead, room snare, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, chest-sub melody, acid squelch line, kick pattern flip, tight kick, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, FM 808, chest-sub melody, rapid hi-hats, hat density up, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, tom run, accelerating hats, stacked 808, low-mid bass melody, neuro wobble lead, kick opens, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, low reese counterline, distorted sub figure, ghost snare, kick opens, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick stomp, accelerating hats, octave sub stack, body bass answer, granular bass figure, kick tightens, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 1 | `[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, risin...` |
| 2 | `349` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, rising energy, offbeat push, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, parallel low-mid layer, electric heavy warped drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, ghost snare, straight hats, 2 bars]

[build-up - neuro wobble sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, wide stereo layer, laser-lit stacked wobble drop, response line, double-time feel, low chest-sub, body bass answer, offbeat hats, triplet hats, 2 bars]

[drop - chest-sub, panning low-mid sweep, layered sub stack, laser-lit full send warped drop, counter melody, low chest-sub, chest-sub melody, trap drums denser, late snare, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, downbeat kick, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, wide stereo layer, laser-lit wreck warped drop, counter-line, stacked 808, low wobble answer, kick pattern flip, mono kick, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, kick tightens, gated bass, accelerating hats, stacked 808, room snare, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, parallel low-mid layer, laser-lit full send warped drop, low wobble answer, FM 808, wavy low-mid line, trap drums denser, tight kick, 2 bars]

[drop - phase-distorted sub, layers surround the ear, parallel low-mid layer, laser-lit wreck wobble drop, response line, low chest-sub, body bass answer, phase-wavy synth line, kick pattern flip, closed hat, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, tom run, tempo push, body bass, loose hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, octave 808 stack, laser-lit heavy warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, acid squelch line, ghost snare, tight kick, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, laser-lit harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, rapid hi-hats, loose hats, 2 bars]

[inst - phase-distorted sub, layers surround the ear, octave sub stack, offbeat hats, hat density up, 2 bars]

[build-up - chest-sub, panning low-mid sweep, kick tightens, sub swell, tempo push, octave sub stack, closed hat, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, body bass, offbeat hats, room snare, 2 bars]

[build-up - neuro wobble sub, bass pans wide behind, kick tightens, bass pressure builds, tempo push, mono chest-sub, low wobble answer, warped FM lead, room snare, 2 bars]

[inst - phase-distorted sub, layers surround the ear, low chest-sub, chest-sub melody, acid squelch line, kick pattern flip, tight kick, 2 bars]

[build-up - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, FM 808, chest-sub melody, rapid hi-hats, hat density up, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, tom run, accelerating hats, stacked 808, low-mid bass melody, neuro wobble lead, kick opens, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, low reese counterline, distorted sub figure, ghost snare, kick opens, 2 bars]

[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, kick stomp, accelerating hats, octave sub stack, body bass answer, granular bass figure, kick tightens, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `349` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 2 | `[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/13-night-oil` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, panning bass layer, octave-stacked electric wreck reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, fast bass triplets, straight hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, energy surge, rising energy, mono chest-sub, low-mid bass melody, wobble FM voice, triplet hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, octave-stacked electric full send wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, wobble FM voice, staccato sub bursts, wide hat bed, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, parallel low-mid layer, octave-stacked electric stacked warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, double-time bass gallop, side snare, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, rolling 808 run, late snare, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, octave 808 stack, mono chest-sub, low reese counterline, wobble FM voice, staccato sub bursts, late snare, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, parallel low-mid layer, max stack laser stacked reese drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, granular bass figure, double-time bass gallop, open hat, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, bass melody climbs, tempo push, wide stereo layer, stacked 808, low reese counterline, closed hat, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, octave 808 stack, full send laser stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, acid squelch line, double-time bass gallop, room snare, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, parallel low-mid layer, accelerating hats, octave 808 stack, low chest-sub, wavy low-mid line, room snare, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, panning bass layer, mono chest-sub, low reese counterline, fast bass triplets, tight kick, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, energy surge, rising energy, layered sub stack, low chest-sub, body bass answer, loose hats, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, octave 808 stack, octave-stacked electric harder warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, rolling 808 run, hat density up, 2 bars]

[build-up - octave sub pulse, low-mid from every angle, kick tightens, energy surge, rising energy, panning bass layer, FM 808, body bass answer, granular bass figure, kick opens, 2 bars]

[inst - FM warp sub, wide 3D bass field, kick only on downbeats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, layered sub stack, laser electric tower harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, rolling 808 run, kick tightens, 2 bars]

[outro - phase-distorted sub, low-mid from every angle, kick pattern flip, rapid hi-hats, low chest-sub, body bass answer, snare answers, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| 1 | `[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2...` |
| 2 | `349` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `C major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, panning bass layer, octave-stacked electric wreck reese drop, counter melody, double-time feel, low chest-sub, chest-sub melody, fast bass triplets, straight hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, energy surge, rising energy, mono chest-sub, low-mid bass melody, wobble FM voice, triplet hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, panning bass layer, octave-stacked electric full send wobble drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, wobble FM voice, staccato sub bursts, wide hat bed, 2 bars]

[inst - octave sub pulse, low-mid orbits the sub, downbeat sub pulse, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, parallel low-mid layer, octave-stacked electric stacked warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, double-time bass gallop, side snare, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, octave 808 stack, octave-stacked electric harder reese drop, counter-line, double-time feel, stacked 808, low wobble answer, rolling 808 run, late snare, 2 bars]

[build-up - neuro wobble sub, wide 3D bass field, kick only on downbeats, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, octave 808 stack, mono chest-sub, low reese counterline, wobble FM voice, staccato sub bursts, late snare, 2 bars]

[drop - bitcrushed 808, bass circles the low-mid, parallel low-mid layer, max stack laser stacked reese drop, low wobble answer, double-time feel, FM 808, wavy low-mid line, granular bass figure, double-time bass gallop, open hat, 2 bars]

[build-up - octave sub pulse, bass pans wide behind, kick tightens, bass melody climbs, tempo push, wide stereo layer, stacked 808, low reese counterline, closed hat, 2 bars]

[inst - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, octave 808 stack, full send laser stacked wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, acid squelch line, double-time bass gallop, room snare, 2 bars]

[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, parallel low-mid layer, accelerating hats, octave 808 stack, low chest-sub, wavy low-mid line, room snare, 2 bars]

[inst - phase-distorted sub, bass pans wide behind, panning bass layer, mono chest-sub, low reese counterline, fast bass triplets, tight kick, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, energy surge, rising energy, layered sub stack, low chest-sub, body bass answer, loose hats, 2 bars]

[drop - bitcrushed 808, sub center, low-mid moves wide, octave 808 stack, octave-stacked electric harder warped drop, second low-mid line, double-time feel, stacked 808, low reese counterline, rolling 808 run, hat density up, 2 bars]

[build-up - octave sub pulse, low-mid from every angle, kick tightens, energy surge, rising energy, panning bass layer, FM 808, body bass answer, granular bass figure, kick opens, 2 bars]

[inst - FM warp sub, wide 3D bass field, kick only on downbeats, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, layered sub stack, laser electric tower harder reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, rolling 808 run, kick tightens, 2 bars]

[outro - phase-distorted sub, low-mid from every angle, kick pattern flip, rapid hi-hats, low chest-sub, body bass answer, snare answers, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `349` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `165` |
| 1 | `1, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `14-chest-pass`

Catalog id `audio/albums/drive-through/hour-2/14-chest-pass`.

US-safe EDM take: Drive-through chest-pass dirty bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `66.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 2 | `[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor ki...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, stacked wobble drop, double-time feel, FM 808, wavy low-mid line, warped FM lead, offbeat hats, kick opens, dirty bass, dual-action pedal bass, heavy chest drop, 2 bars]

[inst - chest-sub, bass circles the low-mid, ghost snare, kick tightens, sub warp wreck, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, harder warped drop, double-time feel, FM 808, body bass answer, neuro wobble lead, rapid hi-hats, snare answers, pass grind, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, kick pattern flip, straight hats, rapid hi-hats denser, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, ghost snare, backbeat shove, 808 hold, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, harder reese drop, stacked 808, low reese counterline, rapid hi-hats, ghost notes, harder warped drop, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[drop - wavy phase sub, low-mid from every angle, octave 808 stack, wreck wobble drop, double-time feel, stacked 808, low wobble answer, acid squelch line, kick pattern flip, wide hat bed, dual-action pedal bass, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, heavy warped drop, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, ghost snare, side snare, stacked 808 wall, 2 bars]

[build-up - FM warp sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, full send reese drop, stacked 808, low reese counterline, granular bass figure, trap drums denser, late snare, pedal 808 hold, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, offbeat push, accelerating hats, FM 808, early kick, hats roll, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, stacked wobble drop, stacked 808, low wobble answer, offbeat hats, syncopated hats, full send drop, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, low-end pressure builds, rising energy, FM 808, open hat, body bass wreck, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, stacked 808, rapid hi-hats, closed hat, warped chest, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, wide stereo layer, full send wobble drop, double-time feel, FM 808, wavy low-mid line, neuro wobble lead, trap drums denser, room snare, kick holds, 2 bars]

[build-up - FM warp sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, panning bass layer, stacked warped drop, FM 808, body bass answer, distorted sub figure, offbeat hats, loose hats, hats denser, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, pre-impact hold, tempo push, stacked 808, pushed snare, pedal ride, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 1 | `[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor ki...` |
| 2 | `353` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, panning bass layer, stacked wobble drop, double-time feel, FM 808, wavy low-mid line, warped FM lead, offbeat hats, kick opens, dirty bass, dual-action pedal bass, heavy chest drop, 2 bars]

[inst - chest-sub, bass circles the low-mid, ghost snare, kick tightens, sub warp wreck, 2 bars]

[drop - wavy phase sub, bass pans wide behind, parallel low-mid layer, harder warped drop, double-time feel, FM 808, body bass answer, neuro wobble lead, rapid hi-hats, snare answers, pass grind, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, sparse four-on-floor kick, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, kick pattern flip, straight hats, rapid hi-hats denser, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[inst - neuro wobble sub, sub anchored, mids orbit, ghost snare, backbeat shove, 808 hold, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, parallel low-mid layer, harder reese drop, stacked 808, low reese counterline, rapid hi-hats, ghost notes, harder warped drop, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, downbeat kick, 2 bars]

[drop - wavy phase sub, low-mid from every angle, octave 808 stack, wreck wobble drop, double-time feel, stacked 808, low wobble answer, acid squelch line, kick pattern flip, wide hat bed, dual-action pedal bass, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, bass circles the low-mid, layered sub stack, heavy warped drop, double-time feel, stacked 808, low-mid bass melody, square-wave pulse figure, ghost snare, side snare, stacked 808 wall, 2 bars]

[build-up - FM warp sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, full send reese drop, stacked 808, low reese counterline, granular bass figure, trap drums denser, late snare, pedal 808 hold, 2 bars]

[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, offbeat push, accelerating hats, FM 808, early kick, hats roll, 2 bars]

[drop - chest-sub, low-mid orbits the sub, panning bass layer, stacked wobble drop, stacked 808, low wobble answer, offbeat hats, syncopated hats, full send drop, 2 bars]

[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, low-end pressure builds, rising energy, FM 808, open hat, body bass wreck, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, stacked 808, rapid hi-hats, closed hat, warped chest, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, wide stereo layer, full send wobble drop, double-time feel, FM 808, wavy low-mid line, neuro wobble lead, trap drums denser, room snare, kick holds, 2 bars]

[build-up - FM warp sub, low-mid from every angle, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, panning bass layer, stacked warped drop, FM 808, body bass answer, distorted sub figure, offbeat hats, loose hats, hats denser, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, pre-impact hold, tempo push, stacked 808, pushed snare, pedal ride, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `353` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `14 - Chest Pass` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `14 - Chest Pass` |
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
| 1 | `Hour 2` |
| 2 | `Chest Pass` |
| 3 | `14` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `14 - Chest Pass` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 2 | `[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid or...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid orbit widens, accelerating hats, octave sub stack, hat density up, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, phase-charged heavy wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, driving sub pulse run, kick opens, 2 bars]

[inst - FM warp sub, bass circles the low-mid, octave sub stack, rolling 808 run, kick tightens, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged full send warped drop, second low-mid line, double-time feel, body bass, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, rolling hats, tempo push, octave sub stack, offbeat push, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, double-time bass gallop, straight hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, octave 808 stack, laser electric heavy warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, driving sub pulse run, triplet hats, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, rolling hats, tempo push, body bass, low-mid bass melody, square-wave pulse figure, backbeat shove, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged wreck warped drop, second low-mid line, double-time feel, body bass, low reese counterline, fast bass triplets, dry hats, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, octave sub stack, body bass answer, wobble FM voice, double-time bass gallop, wide hat bed, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, octave 808 stack, phase-charged heavy reese drop, counter-line, double-time feel, body bass, low wobble answer, driving sub pulse run, mono kick, 2 bars]

[inst - chest-sub, bass circles the low-mid, octave sub stack, chest-sub melody, warped FM lead, rolling 808 run, side snare, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, rolling hats, tempo push, body bass, low-mid bass melody, rolling hats, 2 bars]

[inst - bitcrushed 808, layers surround the ear, kick only on downbeats, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, phase-charged stacked warped drop, second low-mid line, double-time feel, body bass, low reese counterline, double-time bass gallop, early kick, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, kick tightens, beat stutter, rising energy, panning bass layer, body bass, low wobble answer, open hat, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, layered sub stack, laser electric full send warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, wobble FM voice, staccato sub bursts, closed hat, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, rolling hats, tempo push, parallel low-mid layer, body bass, low-mid bass melody, phase-wavy synth line, room snare, 2 bars]

[drop - wavy phase sub, low-mid from every angle, wide stereo layer, laser electric stacked reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, low-mid orbit widens, accelerating hats, octave 808 stack, body bass, low reese counterline, loose hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick tightens, pre-impact hold, tempo push, panning bass layer, octave sub stack, body bass answer, neuro wobble lead, pushed snare, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 1 | `[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid or...` |
| 2 | `353` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid orbit widens, accelerating hats, octave sub stack, hat density up, 2 bars]

[drop - octave sub pulse, wide 3D bass field, octave 808 stack, phase-charged heavy wobble drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, driving sub pulse run, kick opens, 2 bars]

[inst - FM warp sub, bass circles the low-mid, octave sub stack, rolling 808 run, kick tightens, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged full send warped drop, second low-mid line, double-time feel, body bass, low reese counterline, staccato sub bursts, snare answers, 2 bars]

[build-up - phase-distorted sub, layers surround the ear, kick tightens, rolling hats, tempo push, octave sub stack, offbeat push, 2 bars]

[inst - chest-sub, 3D low-mid orbit, body bass, double-time bass gallop, straight hats, 2 bars]

[drop - wavy phase sub, low-mid orbits the sub, octave 808 stack, laser electric heavy warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, driving sub pulse run, triplet hats, 2 bars]

[build-up - bitcrushed 808, sub anchored, mids orbit, kick tightens, rolling hats, tempo push, body bass, low-mid bass melody, square-wave pulse figure, backbeat shove, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged wreck warped drop, second low-mid line, double-time feel, body bass, low reese counterline, fast bass triplets, dry hats, 2 bars]

[inst - neuro wobble sub, low-mid from every angle, octave sub stack, body bass answer, wobble FM voice, double-time bass gallop, wide hat bed, 2 bars]

[drop - phase-distorted sub, wide 3D bass field, octave 808 stack, phase-charged heavy reese drop, counter-line, double-time feel, body bass, low wobble answer, driving sub pulse run, mono kick, 2 bars]

[inst - chest-sub, bass circles the low-mid, octave sub stack, chest-sub melody, warped FM lead, rolling 808 run, side snare, 2 bars]

[build-up - wavy phase sub, bass pans wide behind, kick tightens, rolling hats, tempo push, body bass, low-mid bass melody, rolling hats, 2 bars]

[inst - bitcrushed 808, layers surround the ear, kick only on downbeats, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, wide stereo layer, phase-charged stacked warped drop, second low-mid line, double-time feel, body bass, low reese counterline, double-time bass gallop, early kick, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, sparse four-on-floor kick, 2 bars]

[build-up - neuro wobble sub, sub anchored, mids orbit, kick tightens, beat stutter, rising energy, panning bass layer, body bass, low wobble answer, open hat, 2 bars]

[drop - phase-distorted sub, panning low-mid sweep, layered sub stack, laser electric full send warped drop, counter melody, double-time feel, octave sub stack, chest-sub melody, wobble FM voice, staccato sub bursts, closed hat, 2 bars]

[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, rolling hats, tempo push, parallel low-mid layer, body bass, low-mid bass melody, phase-wavy synth line, room snare, 2 bars]

[drop - wavy phase sub, low-mid from every angle, wide stereo layer, laser electric stacked reese drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, warped FM lead, double-time bass gallop, tight kick, 2 bars]

[build-up - bitcrushed 808, wide 3D bass field, kick tightens, low-mid orbit widens, accelerating hats, octave 808 stack, body bass, low reese counterline, loose hats, 2 bars]

[build-up - octave sub pulse, bass circles the low-mid, kick tightens, pre-impact hold, tempo push, panning bass layer, octave sub stack, body bass answer, neuro wobble lead, pushed snare, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `353` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 2 | `[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, risi...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, rising energy, low chest-sub, snare answers, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, panning bass layer, multi-stack full send warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, warped FM lead, driving sub pulse run, offbeat push, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, phase-charged stacked reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, warped FM lead, staccato sub bursts, closed hat, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, wide laser heavy warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, fast bass triplets, backbeat shove, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, low-mid orbit widens, tempo push, FM 808, loose hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, panning bass layer, wide laser full send reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, driving sub pulse run, dry hats, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, low reese counterline, wobble FM voice, wide hat bed, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, phase-charged heavy reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, fast bass triplets, hat density up, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, wide laser heavy wobble drop, counter-line, double-time feel, body bass, low wobble answer, fast bass triplets, ghost notes, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, octave 808 stack, accelerating hats, low chest-sub, chest-sub melody, acid squelch line, rolling hats, 2 bars]

[drop - FM warp sub, bass circles the low-mid, wide stereo layer, laser electric wreck reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, rolling 808 run, snare answers, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, panning bass layer, multi-stack wreck wobble drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, square-wave pulse figure, rolling 808 run, mono kick, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, mono chest-sub, low reese counterline, distorted sub figure, staccato sub bursts, syncopated hats, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, mono chest-sub, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, octave 808 stack, accelerating hats, low chest-sub, chest-sub melody, phase-wavy synth line, room snare, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, FM 808, body bass answer, phase-wavy synth line, staccato sub bursts, dry hats, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, rising energy, parallel low-mid layer, low chest-sub, wavy low-mid line, acid squelch line, loose hats, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, wide stereo layer, mono chest-sub, low reese counterline, neuro wobble lead, fast bass triplets, pushed snare, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, panning bass layer, mono chest-sub, low wobble answer, driving sub pulse run, hat density up, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub pickup, accelerating hats, layered sub stack, low chest-sub, chest-sub melody, kick opens, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 1 | `[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, risi...` |
| 2 | `353` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, rising energy, low chest-sub, snare answers, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, panning bass layer, multi-stack full send warped drop, second low-mid line, double-time feel, mono chest-sub, low reese counterline, warped FM lead, driving sub pulse run, offbeat push, 2 bars]

[drop - bitcrushed 808, bass pans wide behind, octave 808 stack, phase-charged stacked reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, warped FM lead, staccato sub bursts, closed hat, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, wide stereo layer, wide laser heavy warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, fast bass triplets, backbeat shove, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, low-mid orbit widens, tempo push, FM 808, loose hats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, panning bass layer, wide laser full send reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, driving sub pulse run, dry hats, 2 bars]

[build-up - FM warp sub, wide 3D bass field, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, low reese counterline, wobble FM voice, wide hat bed, 2 bars]

[drop - wavy phase sub, sub center, low-mid moves wide, panning bass layer, phase-charged heavy reese drop, counter-lead answers, double-time feel, stacked 808, low-mid bass melody, fast bass triplets, hat density up, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, wide laser heavy wobble drop, counter-line, double-time feel, body bass, low wobble answer, fast bass triplets, ghost notes, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, octave 808 stack, accelerating hats, low chest-sub, chest-sub melody, acid squelch line, rolling hats, 2 bars]

[drop - FM warp sub, bass circles the low-mid, wide stereo layer, laser electric wreck reese drop, response line, double-time feel, FM 808, body bass answer, acid squelch line, rolling 808 run, snare answers, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, panning bass layer, multi-stack wreck wobble drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, square-wave pulse figure, rolling 808 run, mono kick, 2 bars]

[inst - octave sub pulse, sub anchored, mids orbit, mono chest-sub, low reese counterline, distorted sub figure, staccato sub bursts, syncopated hats, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - neuro wobble sub, sub center, low-mid moves wide, mono chest-sub, low wobble answer, double-time bass gallop, closed hat, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, octave 808 stack, accelerating hats, low chest-sub, chest-sub melody, phase-wavy synth line, room snare, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, FM 808, body bass answer, phase-wavy synth line, staccato sub bursts, dry hats, 2 bars]

[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, rising energy, parallel low-mid layer, low chest-sub, wavy low-mid line, acid squelch line, loose hats, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, wide stereo layer, mono chest-sub, low reese counterline, neuro wobble lead, fast bass triplets, pushed snare, 2 bars]

[build-up - phase-distorted sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - FM warp sub, 3D low-mid orbit, panning bass layer, mono chest-sub, low wobble answer, driving sub pulse run, hat density up, 2 bars]

[build-up - neuro wobble sub, low-mid orbits the sub, kick tightens, sub pickup, accelerating hats, layered sub stack, low chest-sub, chest-sub melody, kick opens, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `353` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 2 | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit w...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit widens, tempo push, octave sub stack, kick tightens, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, phase-charged heavy warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, distorted sub figure, double-time bass gallop, straight hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, kick run, rising energy, stacked 808, straight hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, downbeat sub pulse, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, phase-charged full send wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, rolling 808 run, triplet hats, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - chest-sub, low-mid from every angle, low chest-sub, double-time bass gallop, wide hat bed, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, phase-charged harder warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, mono kick, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, multi-stack heavy wobble drop, response line, double-time feel, FM 808, body bass answer, granular bass figure, double-time bass gallop, side snare, 2 bars]

[build-up - octave sub pulse, low-mid from every angle, kick tightens, rolling hats, rising energy, octave sub stack, chest-sub melody, side snare, 2 bars]

[drop - FM warp sub, wide 3D bass field, parallel low-mid layer, laser electric stacked reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, fast bass triplets, rolling hats, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave sub stack, wavy low-mid line, acid squelch line, double-time bass gallop, late snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, low chest-sub, wavy low-mid line, staccato sub bursts, closed hat, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, rolling hats, rising energy, mono chest-sub, low reese counterline, room snare, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, wide laser full send reese drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, rolling 808 run, room snare, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - FM warp sub, panning low-mid sweep, octave 808 stack, octave sub stack, wavy low-mid line, phase-wavy synth line, driving sub pulse run, tight kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, laser electric stacked reese drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, fast bass triplets, kick opens, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, panning bass layer, wide laser wreck warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, phase-wavy synth line, staccato sub bursts, kick tightens, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, downbeat impact, accelerating hats, panning bass layer, low chest-sub, body bass answer, acid squelch line, kick tightens, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 1 | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit w...` |
| 2 | `353` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit widens, tempo push, octave sub stack, kick tightens, 2 bars]

[drop - bitcrushed 808, 3D low-mid orbit, octave 808 stack, phase-charged heavy warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, distorted sub figure, double-time bass gallop, straight hats, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, kick run, rising energy, stacked 808, straight hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, downbeat sub pulse, 2 bars]

[drop - FM warp sub, layers surround the ear, panning bass layer, phase-charged full send wobble drop, counter melody, double-time feel, octave sub stack, chest-sub melody, rolling 808 run, triplet hats, 2 bars]

[build-up - neuro wobble sub, 3D low-mid orbit, downbeat kick, 2 bars]

[inst - chest-sub, low-mid from every angle, low chest-sub, double-time bass gallop, wide hat bed, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, phase-charged harder warped drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, neuro wobble lead, driving sub pulse run, mono kick, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, low-mid orbits the sub, layered sub stack, multi-stack heavy wobble drop, response line, double-time feel, FM 808, body bass answer, granular bass figure, double-time bass gallop, side snare, 2 bars]

[build-up - octave sub pulse, low-mid from every angle, kick tightens, rolling hats, rising energy, octave sub stack, chest-sub melody, side snare, 2 bars]

[drop - FM warp sub, wide 3D bass field, parallel low-mid layer, laser electric stacked reese drop, counter-lead answers, double-time feel, body bass, low-mid bass melody, warped FM lead, fast bass triplets, rolling hats, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave sub stack, wavy low-mid line, acid squelch line, double-time bass gallop, late snare, 2 bars]

[build-up - chest-sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, low chest-sub, wavy low-mid line, staccato sub bursts, closed hat, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, rolling hats, rising energy, mono chest-sub, low reese counterline, room snare, 2 bars]

[drop - phase-distorted sub, bass pans wide behind, wide stereo layer, wide laser full send reese drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, rolling 808 run, room snare, 2 bars]

[build-up - octave sub pulse, sub anchored, mids orbit, downbeat kick, 2 bars]

[inst - FM warp sub, panning low-mid sweep, octave 808 stack, octave sub stack, wavy low-mid line, phase-wavy synth line, driving sub pulse run, tight kick, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, octave 808 stack, laser electric stacked reese drop, counter-line, double-time feel, stacked 808, low wobble answer, distorted sub figure, fast bass triplets, kick opens, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, bass circles the low-mid, panning bass layer, wide laser wreck warped drop, low wobble answer, double-time feel, octave sub stack, wavy low-mid line, phase-wavy synth line, staccato sub bursts, kick tightens, 2 bars]

[build-up - bitcrushed 808, low-mid orbits the sub, kick tightens, downbeat impact, accelerating hats, panning bass layer, low chest-sub, body bass answer, acid squelch line, kick tightens, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `353` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 5 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `fixed` |

**Pass 5 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `66.0` |
| 1 | `1` |

**ez_edm_prompt pass 5** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 2 | `[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars] [drop...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser electric tower harder warped drop, counter-line, double-time feel, FM 808, low wobble answer, acid squelch line, rolling 808 run, triplet hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, wide stereo layer, rising energy, octave sub stack, low-mid bass melody, square-wave pulse figure, triplet hats, 2 bars]

[inst - chest-sub, low-mid from every angle, low chest-sub, low reese counterline, granular bass figure, staccato sub bursts, triplet hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, laser electric tower wreck wobble drop, response line, double-time feel, mono chest-sub, body bass answer, wobble FM voice, fast bass triplets, backbeat shove, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, low chest-sub, low wobble answer, double-time bass gallop, ghost notes, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, full send laser harder reese drop, response line, double-time feel, stacked 808, body bass answer, wobble FM voice, rolling 808 run, mono kick, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, layered sub stack, full send laser wreck wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, fast bass triplets, rolling hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, layered sub stack, body bass, wavy low-mid line, neuro wobble lead, rolling 808 run, rolling hats, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric tower stacked wobble drop, response line, double-time feel, mono chest-sub, body bass answer, distorted sub figure, double-time bass gallop, rolling hats, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, parallel low-mid layer, low chest-sub, low wobble answer, granular bass figure, driving sub pulse run, late snare, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, bass melody climbs, tempo push, wide stereo layer, mono chest-sub, chest-sub melody, early kick, 2 bars]

[inst - FM warp sub, layers surround the ear, layered sub stack, FM 808, low wobble answer, granular bass figure, fast bass triplets, closed hat, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, full send laser stacked wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, double-time bass gallop, room snare, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, max stack laser wreck reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, acid squelch line, fast bass triplets, tight kick, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, parallel low-mid layer, accelerating hats, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, tight kick, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, full send laser wreck wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, fast bass triplets, pushed snare, 2 bars]

[build-up - FM warp sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave 808 stack, FM 808, low-mid bass melody, granular bass figure, rolling 808 run, kick tightens, 2 bars]

[outro - phase-distorted sub, low-mid from every angle, kick pattern flip, rapid hi-hats, low chest-sub, low wobble answer, kick tightens, 2 bars]
```

**ACE tags + lyrics (pass 5)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| 1 | `[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars] [drop...` |
| 2 | `353` |
| 3 | `fixed` |
| 4 | `168` |
| 5 | `66.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `E minor` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action pedal bass, 808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 168 bpm, instrumental, no vocals
```

```text
[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, octave 808 stack, laser electric tower harder warped drop, counter-line, double-time feel, FM 808, low wobble answer, acid squelch line, rolling 808 run, triplet hats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, wide stereo layer, rising energy, octave sub stack, low-mid bass melody, square-wave pulse figure, triplet hats, 2 bars]

[inst - chest-sub, low-mid from every angle, low chest-sub, low reese counterline, granular bass figure, staccato sub bursts, triplet hats, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, laser electric tower wreck wobble drop, response line, double-time feel, mono chest-sub, body bass answer, wobble FM voice, fast bass triplets, backbeat shove, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, low chest-sub, low wobble answer, double-time bass gallop, ghost notes, 2 bars]

[drop - FM warp sub, sub anchored, mids orbit, octave 808 stack, full send laser harder reese drop, response line, double-time feel, stacked 808, body bass answer, wobble FM voice, rolling 808 run, mono kick, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick only on downbeats, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, layered sub stack, full send laser wreck wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, fast bass triplets, rolling hats, 2 bars]

[inst - octave sub pulse, bass pans wide behind, layered sub stack, body bass, wavy low-mid line, neuro wobble lead, rolling 808 run, rolling hats, 2 bars]

[drop - chest-sub, sub anchored, mids orbit, layered sub stack, laser electric tower stacked wobble drop, response line, double-time feel, mono chest-sub, body bass answer, distorted sub figure, double-time bass gallop, rolling hats, 2 bars]

[inst - wavy phase sub, panning low-mid sweep, parallel low-mid layer, low chest-sub, low wobble answer, granular bass figure, driving sub pulse run, late snare, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, bass melody climbs, tempo push, wide stereo layer, mono chest-sub, chest-sub melody, early kick, 2 bars]

[inst - FM warp sub, layers surround the ear, layered sub stack, FM 808, low wobble answer, granular bass figure, fast bass triplets, closed hat, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, parallel low-mid layer, full send laser stacked wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, double-time bass gallop, room snare, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - octave sub pulse, low-mid from every angle, wide stereo layer, max stack laser wreck reese drop, second low-mid line, double-time feel, octave sub stack, low reese counterline, acid squelch line, fast bass triplets, tight kick, 2 bars]

[build-up - chest-sub, layers surround the ear, kick tightens, parallel low-mid layer, accelerating hats, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, tight kick, 2 bars]

[inst - wavy phase sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, low-mid orbits the sub, panning bass layer, full send laser wreck wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, fast bass triplets, pushed snare, 2 bars]

[build-up - FM warp sub, wide 3D bass field, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, bass circles the low-mid, octave 808 stack, FM 808, low-mid bass melody, granular bass figure, rolling 808 run, kick tightens, 2 bars]

[outro - phase-distorted sub, low-mid from every angle, kick pattern flip, rapid hi-hats, low chest-sub, low wobble answer, kick tightens, 2 bars]
```

**ACE sampler (pass 5)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `353` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `168` |
| 1 | `2, 1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `15-sunrise-sub`

Catalog id `audio/albums/drive-through/hour-2/15-sunrise-sub`.

US-safe EDM take: Drive-through sunrise-sub wave bass warp, ACE-Step 1.5 turbo AIO, instrumental, warped bass, invented timbre
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
| 0 | `67.0` |
| 1 | `fixed` |

**Latent length (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 2 | `[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bar...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, full send warped drop, double-time feel, body bass, wavy low-mid line, acid squelch line, ghost snare, late snare, wave bass, heavy wave drop, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, downbeat kick, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, sub energy lifts, tempo push, syncopated hats, warped sub wreck, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, kick pattern flip, open hat, fold 808, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, harder wobble drop, body bass, chest-sub melody, granular bass figure, offbeat hats, closed hat, rapid hi-hats roll, 2 bars]

[inst - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, wreck warped drop, double-time feel, body bass, wavy low-mid line, rapid hi-hats, tight kick, wave 808 sustain dawn, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, heavy reese drop, double-time feel, body bass, body bass answer, kick pattern flip, pushed snare, harder warped drop, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, sub energy lifts, rising energy, chopped hats, chest gold wreck, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, layered sub stack, full send wobble drop, body bass, chest-sub melody, square-wave pulse figure, ghost snare, hat density up, 808 punch, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, rapid hi-hats, kick opens, low 808 wreck, 2 bars]

[drop - chest-sub, low-mid from every angle, wide stereo layer, stacked warped drop, body bass, wavy low-mid line, trap drums denser, kick tightens, full send drop, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, low-end pressure builds, accelerating hats, octave sub stack, snare answers, wave warp, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, full send warped drop, octave sub stack, low wobble answer, warped FM lead, ghost snare, straight hats, kick holds, 2 bars]

[inst - FM warp sub, layers surround the ear, body bass, rapid hi-hats, triplet hats, wave ride, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, wide stereo layer, stacked reese drop, octave sub stack, low-mid bass melody, neuro wobble lead, trap drums denser, backbeat shove, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, offbeat push, rising energy, body bass, ghost notes, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, octave sub stack, offbeat hats, dry hats, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, layered sub stack, full send reese drop, body bass, body bass answer, granular bass figure, ghost snare, wide hat bed, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, downbeat impact, rising energy, octave sub stack, mono kick, 2 bars]
```

**ACE tags + lyrics** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 1 | `[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bar...` |
| 2 | `359` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bars]

[drop - bitcrushed 808, panning low-mid sweep, layered sub stack, full send warped drop, double-time feel, body bass, wavy low-mid line, acid squelch line, ghost snare, late snare, wave bass, heavy wave drop, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, downbeat kick, 2 bars]

[build-up - FM warp sub, low-mid from every angle, kick tightens, sub energy lifts, tempo push, syncopated hats, warped sub wreck, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, kick pattern flip, open hat, fold 808, 2 bars]

[drop - phase-distorted sub, bass circles the low-mid, panning bass layer, harder wobble drop, body bass, chest-sub melody, granular bass figure, offbeat hats, closed hat, rapid hi-hats roll, 2 bars]

[inst - chest-sub, bass pans wide behind, downbeat kick, 2 bars]

[drop - wavy phase sub, layers surround the ear, parallel low-mid layer, wreck warped drop, double-time feel, body bass, wavy low-mid line, rapid hi-hats, tight kick, wave 808 sustain dawn, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, octave 808 stack, heavy reese drop, double-time feel, body bass, body bass answer, kick pattern flip, pushed snare, harder warped drop, 2 bars]

[build-up - FM warp sub, sub anchored, mids orbit, kick tightens, sub energy lifts, rising energy, chopped hats, chest gold wreck, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, layered sub stack, full send wobble drop, body bass, chest-sub melody, square-wave pulse figure, ghost snare, hat density up, 808 punch, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, rapid hi-hats, kick opens, low 808 wreck, 2 bars]

[drop - chest-sub, low-mid from every angle, wide stereo layer, stacked warped drop, body bass, wavy low-mid line, trap drums denser, kick tightens, full send drop, 2 bars]

[build-up - wavy phase sub, wide 3D bass field, kick tightens, low-end pressure builds, accelerating hats, octave sub stack, snare answers, wave warp, 2 bars]

[inst - bitcrushed 808, bass circles the low-mid, kick only on downbeats, 2 bars]

[drop - octave sub pulse, bass pans wide behind, layered sub stack, full send warped drop, octave sub stack, low wobble answer, warped FM lead, ghost snare, straight hats, kick holds, 2 bars]

[inst - FM warp sub, layers surround the ear, body bass, rapid hi-hats, triplet hats, wave ride, 2 bars]

[drop - neuro wobble sub, 3D low-mid orbit, wide stereo layer, stacked reese drop, octave sub stack, low-mid bass melody, neuro wobble lead, trap drums denser, backbeat shove, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, offbeat push, rising energy, body bass, ghost notes, 2 bars]

[inst - chest-sub, sub anchored, mids orbit, octave sub stack, offbeat hats, dry hats, 2 bars]

[drop - wavy phase sub, panning low-mid sweep, layered sub stack, full send reese drop, body bass, body bass answer, granular bass figure, ghost snare, wide hat bed, 2 bars]

[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, downbeat impact, rising energy, octave sub stack, mono kick, 2 bars]
```

**ACE sampler** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `359` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**FLAC master** (`SaveAudio`)

| Slot | Value |
| --- | --- |
| 0 | `15 - Sunrise Sub` |

**MP3 320k** (`SaveAudioMP3`)

| Slot | Value |
| --- | --- |
| 0 | `15 - Sunrise Sub` |
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
| 1 | `Hour 2` |
| 2 | `Sunrise Sub` |
| 3 | `15` |
| 4 | `15` |
| 5 | `2026` |
| 6 | `skip` |
| 7 | `15 - Sunrise Sub` |

**Pass 2 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 2 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 2** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 2 | `[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 ba...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, 3D low-mid orbit, panning bass layer, laser electric wreck warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, rolling 808 run, early kick, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick tightens, stutter gate, accelerating hats, mono chest-sub, syncopated hats, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, parallel low-mid layer, laser electric heavy reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, warped FM lead, fast bass triplets, open hat, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, mono chest-sub, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, octave 808 stack, laser electric full send wobble drop, response line, double-time feel, low chest-sub, body bass answer, neuro wobble lead, driving sub pulse run, room snare, 2 bars]

[inst - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, layered sub stack, laser electric stacked warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, staccato sub bursts, loose hats, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, layered sub stack, laser electric stacked reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, staccato sub bursts, straight hats, 2 bars]

[inst - chest-sub, bass pans wide behind, low chest-sub, wavy low-mid line, double-time bass gallop, chopped hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, octave 808 stack, rising energy, mono chest-sub, low reese counterline, hat density up, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, kick run, tempo push, mono chest-sub, low wobble answer, kick tightens, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, low chest-sub, chest-sub melody, neuro wobble lead, fast bass triplets, snare answers, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, phase-charged harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, offbeat push, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, kick run, tempo push, low chest-sub, wavy low-mid line, distorted sub figure, straight hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, wide 3D bass field, layered sub stack, laser electric stacked wobble drop, response line, double-time feel, low chest-sub, body bass answer, staccato sub bursts, backbeat shove, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, kick run, tempo push, parallel low-mid layer, mono chest-sub, low wobble answer, phase-wavy synth line, ghost notes, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, laser electric harder warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, warped FM lead, double-time bass gallop, dry hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, panning bass layer, low chest-sub, wavy low-mid line, neuro wobble lead, rolling 808 run, mono kick, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, downbeat impact, rising energy, layered sub stack, mono chest-sub, low reese counterline, side snare, 2 bars]
```

**ACE tags + lyrics (pass 2)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 1 | `[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 ba...` |
| 2 | `359` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, 3D low-mid orbit, panning bass layer, laser electric wreck warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, rolling 808 run, early kick, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick tightens, stutter gate, accelerating hats, mono chest-sub, syncopated hats, 2 bars]

[drop - wavy phase sub, sub anchored, mids orbit, parallel low-mid layer, laser electric heavy reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, warped FM lead, fast bass triplets, open hat, 2 bars]

[inst - bitcrushed 808, panning low-mid sweep, mono chest-sub, double-time bass gallop, closed hat, 2 bars]

[drop - octave sub pulse, sub center, low-mid moves wide, octave 808 stack, laser electric full send wobble drop, response line, double-time feel, low chest-sub, body bass answer, neuro wobble lead, driving sub pulse run, room snare, 2 bars]

[inst - FM warp sub, low-mid from every angle, downbeat kick, 2 bars]

[drop - neuro wobble sub, wide 3D bass field, layered sub stack, laser electric stacked warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, staccato sub bursts, loose hats, 2 bars]

[drop - bitcrushed 808, wide 3D bass field, layered sub stack, laser electric stacked reese drop, low wobble answer, double-time feel, low chest-sub, wavy low-mid line, staccato sub bursts, straight hats, 2 bars]

[inst - chest-sub, bass pans wide behind, low chest-sub, wavy low-mid line, double-time bass gallop, chopped hats, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, octave 808 stack, rising energy, mono chest-sub, low reese counterline, hat density up, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, kick only on downbeats, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, kick tightens, kick run, tempo push, mono chest-sub, low wobble answer, kick tightens, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, low chest-sub, chest-sub melody, neuro wobble lead, fast bass triplets, snare answers, 2 bars]

[drop - neuro wobble sub, panning low-mid sweep, wide stereo layer, phase-charged harder wobble drop, counter-lead answers, double-time feel, mono chest-sub, low-mid bass melody, double-time bass gallop, offbeat push, 2 bars]

[build-up - phase-distorted sub, sub center, low-mid moves wide, kick tightens, kick run, tempo push, low chest-sub, wavy low-mid line, distorted sub figure, straight hats, 2 bars]

[inst - chest-sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[drop - wavy phase sub, wide 3D bass field, layered sub stack, laser electric stacked wobble drop, response line, double-time feel, low chest-sub, body bass answer, staccato sub bursts, backbeat shove, 2 bars]

[build-up - bitcrushed 808, bass circles the low-mid, kick tightens, kick run, tempo push, parallel low-mid layer, mono chest-sub, low wobble answer, phase-wavy synth line, ghost notes, 2 bars]

[drop - octave sub pulse, bass pans wide behind, wide stereo layer, laser electric harder warped drop, counter melody, double-time feel, low chest-sub, chest-sub melody, warped FM lead, double-time bass gallop, dry hats, 2 bars]

[build-up - FM warp sub, layers surround the ear, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, 3D low-mid orbit, panning bass layer, low chest-sub, wavy low-mid line, neuro wobble lead, rolling 808 run, mono kick, 2 bars]

[build-up - phase-distorted sub, low-mid orbits the sub, kick tightens, downbeat impact, rising energy, layered sub stack, mono chest-sub, low reese counterline, side snare, 2 bars]
```

**ACE sampler (pass 2)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `359` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 3 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `79.0` |
| 1 | `fixed` |

**Pass 3 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `79.0` |
| 1 | `1` |

**ez_edm_prompt pass 3** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 2 | `[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hat...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hats, tempo push, mono chest-sub, early kick, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, octave 808 stack, multi-stack harder warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, driving sub pulse run, syncopated hats, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, layered sub stack, multi-stack wreck reese drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, staccato sub bursts, closed hat, 2 bars]

[inst - phase-distorted sub, panning low-mid sweep, mono chest-sub, fast bass triplets, room snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, wide stereo layer, multi-stack heavy wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, double-time bass gallop, tight kick, 2 bars]

[drop - wavy phase sub, layers surround the ear, wide stereo layer, wide laser heavy wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, wobble FM voice, double-time bass gallop, mono kick, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, low chest-sub, rolling 808 run, pushed snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, wide laser full send warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, rolling 808 run, rolling hats, 2 bars]

[inst - FM warp sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, wide laser heavy warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, double-time bass gallop, kick opens, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, multi-stack heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, syncopated hats, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick tightens, rolling hats, tempo push, mono chest-sub, body bass answer, snare answers, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, multi-stack full send reese drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, granular bass figure, rolling 808 run, closed hat, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, low-mid orbit widens, accelerating hats, mono chest-sub, chest-sub melody, warped FM lead, straight hats, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, low chest-sub, low-mid bass melody, double-time bass gallop, triplet hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, low chest-sub, low reese counterline, square-wave pulse figure, rolling 808 run, ghost notes, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, rolling hats, tempo push, mono chest-sub, body bass answer, dry hats, 2 bars]

[inst - chest-sub, bass pans wide behind, low chest-sub, low wobble answer, granular bass figure, fast bass triplets, wide hat bed, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, wide stereo layer, mono chest-sub, chest-sub melody, wobble FM voice, mono kick, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave 808 stack, low chest-sub, low-mid bass melody, phase-wavy synth line, driving sub pulse run, side snare, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, layered sub stack, low chest-sub, low reese counterline, staccato sub bursts, late snare, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, rolling hats, tempo push, parallel low-mid layer, mono chest-sub, body bass answer, neuro wobble lead, early kick, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, syncopated hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, sub pickup, accelerating hats, octave 808 stack, mono chest-sub, chest-sub melody, distorted sub figure, open hat, 2 bars]
```

**ACE tags + lyrics (pass 3)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 1 | `[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hat...` |
| 2 | `359` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `79.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hats, tempo push, mono chest-sub, early kick, 2 bars]

[drop - octave sub pulse, 3D low-mid orbit, octave 808 stack, multi-stack harder warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, driving sub pulse run, syncopated hats, 2 bars]

[inst - FM warp sub, low-mid orbits the sub, downbeat kick, 2 bars]

[drop - neuro wobble sub, sub anchored, mids orbit, layered sub stack, multi-stack wreck reese drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, staccato sub bursts, closed hat, 2 bars]

[inst - phase-distorted sub, panning low-mid sweep, mono chest-sub, fast bass triplets, room snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, wide stereo layer, multi-stack heavy wobble drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, double-time bass gallop, tight kick, 2 bars]

[drop - wavy phase sub, layers surround the ear, wide stereo layer, wide laser heavy wobble drop, counter melody, double-time feel, mono chest-sub, chest-sub melody, wobble FM voice, double-time bass gallop, mono kick, 2 bars]

[inst - bitcrushed 808, wide 3D bass field, low chest-sub, rolling 808 run, pushed snare, 2 bars]

[drop - octave sub pulse, low-mid orbits the sub, panning bass layer, wide laser full send warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, rolling 808 run, rolling hats, 2 bars]

[inst - FM warp sub, bass pans wide behind, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, layers surround the ear, wide stereo layer, wide laser heavy warped drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, double-time bass gallop, kick opens, 2 bars]

[drop - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, multi-stack heavy warped drop, counter-line, double-time feel, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, syncopated hats, 2 bars]

[build-up - chest-sub, low-mid orbits the sub, kick tightens, rolling hats, tempo push, mono chest-sub, body bass answer, snare answers, 2 bars]

[drop - wavy phase sub, wide 3D bass field, panning bass layer, multi-stack full send reese drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, granular bass figure, rolling 808 run, closed hat, 2 bars]

[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, low-mid orbit widens, accelerating hats, mono chest-sub, chest-sub melody, warped FM lead, straight hats, 2 bars]

[inst - octave sub pulse, sub center, low-mid moves wide, low chest-sub, low-mid bass melody, double-time bass gallop, triplet hats, 2 bars]

[build-up - FM warp sub, low-mid from every angle, downbeat sub pulse, 2 bars]

[inst - neuro wobble sub, wide 3D bass field, low chest-sub, low reese counterline, square-wave pulse figure, rolling 808 run, ghost notes, 2 bars]

[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, rolling hats, tempo push, mono chest-sub, body bass answer, dry hats, 2 bars]

[inst - chest-sub, bass pans wide behind, low chest-sub, low wobble answer, granular bass figure, fast bass triplets, wide hat bed, 2 bars]

[build-up - wavy phase sub, layers surround the ear, kick tightens, low-mid orbit widens, accelerating hats, wide stereo layer, mono chest-sub, chest-sub melody, wobble FM voice, mono kick, 2 bars]

[inst - bitcrushed 808, 3D low-mid orbit, octave 808 stack, low chest-sub, low-mid bass melody, phase-wavy synth line, driving sub pulse run, side snare, 2 bars]

[build-up - octave sub pulse, low-mid orbits the sub, downbeat kick, 2 bars]

[inst - FM warp sub, sub anchored, mids orbit, layered sub stack, low chest-sub, low reese counterline, staccato sub bursts, late snare, 2 bars]

[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, rolling hats, tempo push, parallel low-mid layer, mono chest-sub, body bass answer, neuro wobble lead, early kick, 2 bars]

[inst - phase-distorted sub, sub center, low-mid moves wide, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, syncopated hats, 2 bars]

[build-up - chest-sub, low-mid from every angle, kick tightens, sub pickup, accelerating hats, octave 808 stack, mono chest-sub, chest-sub melody, distorted sub figure, open hat, 2 bars]
```

**ACE sampler (pass 3)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `359` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 4 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 4 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 4** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 2 | `[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run,...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run, rising energy, mono chest-sub, syncopated hats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, phase-charged full send warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, double-time bass gallop, open hat, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, mono chest-sub, driving sub pulse run, closed hat, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, panning bass layer, phase-charged stacked reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, acid squelch line, rolling 808 run, room snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, fast bass triplets, open hat, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, stutter gate, tempo push, low chest-sub, loose hats, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, wide stereo layer, laser electric full send reese drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, octave 808 stack, accelerating hats, low chest-sub, low reese counterline, granular bass figure, chopped hats, 2 bars]

[inst - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged heavy reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, phase-wavy synth line, staccato sub bursts, kick opens, 2 bars]

[inst - phase-distorted sub, layers surround the ear, mono chest-sub, chest-sub melody, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, stutter gate, tempo push, low chest-sub, low-mid bass melody, acid squelch line, snare answers, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, mono chest-sub, wavy low-mid line, neuro wobble lead, driving sub pulse run, offbeat push, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, phase-charged stacked warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, rolling 808 run, straight hats, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, downbeat kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, fast bass triplets, backbeat shove, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, wobble FM voice, ghost notes, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, octave 808 stack, low chest-sub, low-mid bass melody, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[build-up - chest-sub, bass circles the low-mid, downbeat kick, 2 bars]

[drop - wavy phase sub, bass pans wide behind, layered sub stack, phase-charged heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, staccato sub bursts, mono kick, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, stutter gate, tempo push, parallel low-mid layer, mono chest-sub, body bass answer, neuro wobble lead, side snare, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, rolling hats, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, pre-impact hold, accelerating hats, octave 808 stack, mono chest-sub, chest-sub melody, distorted sub figure, late snare, 2 bars]
```

**ACE tags + lyrics (pass 4)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 1 | `[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run,...` |
| 2 | `359` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run, rising energy, mono chest-sub, syncopated hats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, wide stereo layer, phase-charged full send warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, double-time bass gallop, open hat, 2 bars]

[inst - neuro wobble sub, low-mid orbits the sub, mono chest-sub, driving sub pulse run, closed hat, 2 bars]

[drop - phase-distorted sub, sub anchored, mids orbit, panning bass layer, phase-charged stacked reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, acid squelch line, rolling 808 run, room snare, 2 bars]

[drop - chest-sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, phase-wavy synth line, fast bass triplets, open hat, 2 bars]

[build-up - wavy phase sub, sub center, low-mid moves wide, kick tightens, stutter gate, tempo push, low chest-sub, loose hats, 2 bars]

[drop - bitcrushed 808, low-mid from every angle, wide stereo layer, laser electric full send reese drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, distorted sub figure, double-time bass gallop, pushed snare, 2 bars]

[build-up - octave sub pulse, wide 3D bass field, kick tightens, octave 808 stack, accelerating hats, low chest-sub, low reese counterline, granular bass figure, chopped hats, 2 bars]

[inst - FM warp sub, bass circles the low-mid, downbeat sub pulse, 2 bars]

[drop - neuro wobble sub, bass pans wide behind, layered sub stack, phase-charged heavy reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, phase-wavy synth line, staccato sub bursts, kick opens, 2 bars]

[inst - phase-distorted sub, layers surround the ear, mono chest-sub, chest-sub melody, warped FM lead, fast bass triplets, kick tightens, 2 bars]

[build-up - chest-sub, 3D low-mid orbit, kick tightens, stutter gate, tempo push, low chest-sub, low-mid bass melody, acid squelch line, snare answers, 2 bars]

[inst - wavy phase sub, low-mid orbits the sub, mono chest-sub, wavy low-mid line, neuro wobble lead, driving sub pulse run, offbeat push, 2 bars]

[drop - bitcrushed 808, sub anchored, mids orbit, panning bass layer, phase-charged stacked warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, rolling 808 run, straight hats, 2 bars]

[inst - octave sub pulse, panning low-mid sweep, downbeat kick, 2 bars]

[drop - FM warp sub, sub center, low-mid moves wide, parallel low-mid layer, phase-charged harder reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, fast bass triplets, backbeat shove, 2 bars]

[build-up - neuro wobble sub, low-mid from every angle, kick tightens, octave 808 stack, accelerating hats, mono chest-sub, chest-sub melody, wobble FM voice, ghost notes, 2 bars]

[inst - phase-distorted sub, wide 3D bass field, octave 808 stack, low chest-sub, low-mid bass melody, phase-wavy synth line, driving sub pulse run, dry hats, 2 bars]

[build-up - chest-sub, bass circles the low-mid, downbeat kick, 2 bars]

[drop - wavy phase sub, bass pans wide behind, layered sub stack, phase-charged heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, staccato sub bursts, mono kick, 2 bars]

[build-up - bitcrushed 808, layers surround the ear, kick tightens, stutter gate, tempo push, parallel low-mid layer, mono chest-sub, body bass answer, neuro wobble lead, side snare, 2 bars]

[inst - octave sub pulse, 3D low-mid orbit, wide stereo layer, low chest-sub, low wobble answer, square-wave pulse figure, double-time bass gallop, rolling hats, 2 bars]

[build-up - FM warp sub, low-mid orbits the sub, kick tightens, pre-impact hold, accelerating hats, octave 808 stack, mono chest-sub, chest-sub melody, distorted sub figure, late snare, 2 bars]
```

**ACE sampler (pass 4)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `359` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Pass 5 clock** (`PrimitiveNode`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `fixed` |

**Pass 5 latent (seconds)** (`EmptyAceStep1.5LatentAudio`)

| Slot | Value |
| --- | --- |
| 0 | `67.0` |
| 1 | `1` |

**ez_edm_prompt pass 5** (`EZAceStepPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `custom` |
| 1 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, bass melody clim...` |
| 3 | `false` |
| 4 | `instrumental` |
| 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, bass melody climbs, rising energy, mono chest-sub, chest-sub melody, square-wave pulse figure, open hat, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, wide stereo layer, laser electric tower wreck wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, rolling 808 run, closed hat, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, panning bass layer, laser electric tower heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, wobble FM voice, fast bass triplets, tight kick, 2 bars]

[inst - FM warp sub, panning low-mid sweep, mono chest-sub, body bass answer, double-time bass gallop, loose hats, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, laser electric tower full send reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, warped FM lead, driving sub pulse run, pushed snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass melody climbs, rising energy, mono chest-sub, chest-sub melody, chopped hats, 2 bars]

[inst - chest-sub, wide 3D bass field, low chest-sub, low-mid bass melody, staccato sub bursts, hat density up, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, full send laser heavy reese drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, square-wave pulse figure, fast bass triplets, kick opens, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, layered sub stack, low chest-sub, low reese counterline, distorted sub figure, double-time bass gallop, kick tightens, 2 bars]

[drop - octave sub pulse, layers surround the ear, parallel low-mid layer, full send laser full send wobble drop, response line, double-time feel, mono chest-sub, body bass answer, driving sub pulse run, snare answers, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, layered sub stack, laser electric tower heavy reese drop, response line, double-time feel, stacked 808, body bass answer, granular bass figure, fast bass triplets, backbeat shove, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, parallel low-mid layer, tempo push, parallel low-mid layer, FM 808, low wobble answer, wobble FM voice, ghost notes, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, wide stereo layer, max stack laser heavy wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, acid squelch line, fast bass triplets, dry hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, wide stereo layer, mono chest-sub, body bass answer, square-wave pulse figure, rolling 808 run, dry hats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, layered sub stack, full send laser heavy wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, neuro wobble lead, fast bass triplets, side snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, parallel low-mid layer, tempo push, octave 808 stack, body bass, wavy low-mid line, early kick, 2 bars]

[inst - octave sub pulse, layers surround the ear, octave 808 stack, mono chest-sub, body bass answer, square-wave pulse figure, fast bass triplets, early kick, 2 bars]

[drop - chest-sub, panning low-mid sweep, octave 808 stack, laser electric tower wreck wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, granular bass figure, rolling 808 run, early kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, panning bass layer, FM 808, low-mid bass melody, wobble FM voice, staccato sub bursts, syncopated hats, 2 bars]

[outro - bitcrushed 808, sub anchored, mids orbit, kick pattern flip, rapid hi-hats, low chest-sub, low wobble answer, syncopated hats, 2 bars]
```

**ACE tags + lyrics (pass 5)** (`TextEncodeAceStepAudio1.5`)

| Slot | Value |
| --- | --- |
| 0 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| 1 | `[build-up - chest-sub, layers surround the ear, kick tightens, bass melody clim...` |
| 2 | `359` |
| 3 | `fixed` |
| 4 | `165` |
| 5 | `67.0` |
| 6 | `4` |
| 7 | `unknown` |
| 8 | `G major` |
| 9 | `true` |
| 10 | `2.0` |
| 11 | `0.85` |
| 12 | `0.9` |
| 13 | `0` |
| 14 | `0.0` |

```text
wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers, escalating layered drops, heavy fast bass, layered drop ladder, drop first, 165 bpm, instrumental, no vocals
```

```text
[build-up - chest-sub, layers surround the ear, kick tightens, bass melody climbs, rising energy, mono chest-sub, chest-sub melody, square-wave pulse figure, open hat, 2 bars]

[drop - wavy phase sub, 3D low-mid orbit, wide stereo layer, laser electric tower wreck wobble drop, counter-lead answers, double-time feel, low chest-sub, low-mid bass melody, rolling 808 run, closed hat, 2 bars]

[inst - bitcrushed 808, low-mid orbits the sub, kick only on downbeats, 2 bars]

[drop - octave sub pulse, sub anchored, mids orbit, panning bass layer, laser electric tower heavy warped drop, second low-mid line, double-time feel, low chest-sub, low reese counterline, wobble FM voice, fast bass triplets, tight kick, 2 bars]

[inst - FM warp sub, panning low-mid sweep, mono chest-sub, body bass answer, double-time bass gallop, loose hats, 2 bars]

[drop - neuro wobble sub, sub center, low-mid moves wide, parallel low-mid layer, laser electric tower full send reese drop, counter-line, double-time feel, low chest-sub, low wobble answer, warped FM lead, driving sub pulse run, pushed snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass melody climbs, rising energy, mono chest-sub, chest-sub melody, chopped hats, 2 bars]

[inst - chest-sub, wide 3D bass field, low chest-sub, low-mid bass melody, staccato sub bursts, hat density up, 2 bars]

[drop - wavy phase sub, bass circles the low-mid, panning bass layer, full send laser heavy reese drop, low wobble answer, double-time feel, mono chest-sub, wavy low-mid line, square-wave pulse figure, fast bass triplets, kick opens, 2 bars]

[inst - bitcrushed 808, bass pans wide behind, layered sub stack, low chest-sub, low reese counterline, distorted sub figure, double-time bass gallop, kick tightens, 2 bars]

[drop - octave sub pulse, layers surround the ear, parallel low-mid layer, full send laser full send wobble drop, response line, double-time feel, mono chest-sub, body bass answer, driving sub pulse run, snare answers, 2 bars]

[build-up - FM warp sub, 3D low-mid orbit, downbeat sub pulse, 2 bars]

[drop - phase-distorted sub, low-mid from every angle, layered sub stack, laser electric tower heavy reese drop, response line, double-time feel, stacked 808, body bass answer, granular bass figure, fast bass triplets, backbeat shove, 2 bars]

[build-up - chest-sub, wide 3D bass field, kick tightens, parallel low-mid layer, tempo push, parallel low-mid layer, FM 808, low wobble answer, wobble FM voice, ghost notes, 2 bars]

[inst - wavy phase sub, bass circles the low-mid, sparse four-on-floor kick, 2 bars]

[drop - neuro wobble sub, low-mid orbits the sub, wide stereo layer, max stack laser heavy wobble drop, low wobble answer, double-time feel, body bass, wavy low-mid line, acid squelch line, fast bass triplets, dry hats, 2 bars]

[inst - bitcrushed 808, low-mid from every angle, wide stereo layer, mono chest-sub, body bass answer, square-wave pulse figure, rolling 808 run, dry hats, 2 bars]

[drop - FM warp sub, 3D low-mid orbit, layered sub stack, full send laser heavy wobble drop, second low-mid line, double-time feel, FM 808, low reese counterline, neuro wobble lead, fast bass triplets, side snare, 2 bars]

[build-up - phase-distorted sub, low-mid from every angle, kick tightens, parallel low-mid layer, tempo push, octave 808 stack, body bass, wavy low-mid line, early kick, 2 bars]

[inst - octave sub pulse, layers surround the ear, octave 808 stack, mono chest-sub, body bass answer, square-wave pulse figure, fast bass triplets, early kick, 2 bars]

[drop - chest-sub, panning low-mid sweep, octave 808 stack, laser electric tower wreck wobble drop, counter melody, double-time feel, stacked 808, chest-sub melody, granular bass figure, rolling 808 run, early kick, 2 bars]

[inst - wavy phase sub, sub center, low-mid moves wide, panning bass layer, FM 808, low-mid bass melody, wobble FM voice, staccato sub bursts, syncopated hats, 2 bars]

[outro - bitcrushed 808, sub anchored, mids orbit, kick pattern flip, rapid hi-hats, low chest-sub, low wobble answer, syncopated hats, 2 bars]
```

**ACE sampler (pass 5)** (`KSampler`)

| Slot | Value |
| --- | --- |
| 0 | `359` |
| 1 | `fixed` |
| 2 | `8` |
| 3 | `1.0` |
| 4 | `euler` |
| 5 | `simple` |
| 6 | `1.0` |

**Beat-join passes** (`EZAudioBeatJoin`)

| Slot | Value |
| --- | --- |
| 0 | `165` |
| 1 | `2, 1, 2, 2` |
| 2 | `120.0` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `album`

Catalog id `audio/albums/drive-through/hour-2/album`.

Pack Hour 2 zip + m3u
Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, or film shots) is encoded as written. Turn Enhance on only if you want the 4B rewriter.

**Pack album zip** (`EZAlbumPack`)

| Slot | Value |
| --- | --- |
| 0 | `Drive-through` |
| 1 | `Hour 2` |

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## `cover`

Catalog id `audio/albums/drive-through/hour-2/cover`.

Album cover still for Drive-through / Hour 2

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
| 0 | `square album cover, graphic print, toll booth glow, chest-sub night, long expos...` |

```text
square album cover, graphic print, toll booth glow, chest-sub night, long exposure headlights, fictional act Drive-through, album Hour 2, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

**Negative** (`CLIPTextEncode`)

| Slot | Value |
| --- | --- |
| 0 | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt...` |

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

**Latent (wired from Format)** (`EmptyFlux2LatentImage`)

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
| 0 | `albums/Drive-through/Hour 2/cover` |

**Draft still (set to ez_still_draft_00001_.png)** (`LoadImage`)

| Slot | Value |
| --- | --- |
| 0 | `example.png` |
| 1 | `image` |

**Klein Prompt Enhance** (`EZKleinPromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `square album cover, graphic print, toll booth glow, chest-sub night, long expos...` |
| 1 | `A photoreal still of a tropical coastal city rooftop terrace at golden hour. An...` |
| 2 | `true` |
| 3 | `t2i` |
| 4 | `YouTube 16:9 still` |
| 5 | `none` |
| 6 | `stills/instagram-square` |

```text
square album cover, graphic print, toll booth glow, chest-sub night, long exposure headlights, fictional act Drive-through, album Hour 2, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

```text
A photoreal still of a tropical coastal city rooftop terrace at golden hour. An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams stands mid-stride on the terrace. Warm gold-cyan holographic glyph rings bloom from a compact unmarked data-staff, empty of lettering. Instagram 1:1 square. Subject centered, warm key, unmarked surfaces.
```

**Negative Prompt Enhance** (`EZNegativePromptEnhance`)

| Slot | Value |
| --- | --- |
| 0 | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt...` |
| 1 | `true` |
| 2 | `klein` |

```text
game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks
```

**Quality** (`EZQuality`)

| Slot | Value |
| --- | --- |
| 0 | `lab` |

**Format / platform** (`EZImageFormat`)

| Slot | Value |
| --- | --- |
| 0 | `Instagram - square (1024x1024)` |
| 1 | `none` |
| 2 | `1024` |
| 3 | `1024` |
| 4 | `1` |
| 5 | `Match input` |

**Upscale still** (`EZImageUpscale`)

| Slot | Value |
| --- | --- |
| 0 | `none` |

**Describe image** (`EZImageDescribe`)

| Slot | Value |
| --- | --- |
| 0 | `false` |

**Check models** (`EZModelCheck`)

| Slot | Value |
| --- | --- |
| 0 | `Click Check models. Queue does not run this node.` |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.37.0 / lab `INPUT_TYPES` - not SD1.5 folklore.

### `CheckpointLoaderSimple` - Load Checkpoint

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

**How it affects generation:** Lab music is the turbo AIO. XL is opt-in via download-music --tier xl - swap only if you meant to.

**This graph (all 15 instances):** `ace_step_1.5_turbo_aio.safetensors`

### `ModelSamplingAuraFlow` - ModelSamplingAuraFlow

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

### `PrimitiveNode` - Primitive

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

| Instance | Value |
| --- | --- |
| Song Duration | `67.0` |
| Pass 2 clock | `67.0` |
| Pass 3 clock | `67.0` |
| Pass 4 clock | `67.0` |
| Pass 5 clock | `67.0` |
| Song Duration | `89.0` |
| Pass 2 clock | `89.0` |
| Pass 3 clock | `89.0` |
| Pass 4 clock | `66.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `66.0` |
| Pass 4 clock | `66.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `66.0` |
| Pass 4 clock | `66.0` |
| Song Duration | `67.0` |
| Pass 2 clock | `67.0` |
| Pass 3 clock | `67.0` |
| Song Duration | `63.0` |
| Pass 2 clock | `63.0` |
| Pass 3 clock | `63.0` |
| Pass 4 clock | `63.0` |
| Song Duration | `89.0` |
| Pass 2 clock | `89.0` |
| Pass 3 clock | `77.0` |
| Pass 4 clock | `91.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `66.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `66.0` |
| Pass 4 clock | `66.0` |
| Song Duration | `89.0` |
| Pass 2 clock | `89.0` |
| Pass 3 clock | `89.0` |
| Pass 4 clock | `89.0` |
| Pass 5 clock | `86.0` |
| Song Duration | `67.0` |
| Pass 2 clock | `67.0` |
| Pass 3 clock | `67.0` |
| Pass 4 clock | `67.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `91.0` |
| Song Duration | `79.0` |
| Pass 2 clock | `67.0` |
| Pass 3 clock | `67.0` |
| Song Duration | `66.0` |
| Pass 2 clock | `66.0` |
| Pass 3 clock | `66.0` |
| Pass 4 clock | `66.0` |
| Pass 5 clock | `66.0` |
| Song Duration | `67.0` |
| Pass 2 clock | `67.0` |
| Pass 3 clock | `79.0` |
| Pass 4 clock | `67.0` |
| Pass 5 clock | `67.0` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Whether the primitive mutates after Queue.

**How it affects generation:** fixed keeps duration/context pinned.

**This graph (all 60 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

### `EmptyAceStep1.5LatentAudio` - Empty ACE-Step 1.5 Latent Audio

Allocate an ACE-Step audio latent for N seconds.

!!! warning "Lab notes"

    Draft is the cold-open bar length. Full is the pre-chorus bar length. Nill Bye albums are 64-210 s. Drive-through is 180-480 s built from 3-5 ACE passes of 63-93 s each, from per-take bar math, not a shared clock target. seconds is also a socket from PrimitiveNode so App Duration stays in one place.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `seconds` | in | `FLOAT` | Wired from Song Duration primitive on music graphs. |
| `LATENT` | out | `LATENT` | Audio latent for KSampler. |

#### `seconds`

Type `FLOAT`. Range / default: draft / full / album plan.

Duration in seconds.

**How it affects generation:** Longer latents cost RAM/time linearly. Nill Bye stays 64-210 s. A Drive-through ACE pass stays 63-93 s inside a 180-480 s multi-pass take. Stay at the seeded length unless you have headroom.

| Instance | Value |
| --- | --- |
| Latent length (seconds) | `67.0` |
| Pass 2 latent (seconds) | `67.0` |
| Pass 3 latent (seconds) | `67.0` |
| Pass 4 latent (seconds) | `67.0` |
| Pass 5 latent (seconds) | `67.0` |
| Latent length (seconds) | `89.0` |
| Pass 2 latent (seconds) | `89.0` |
| Pass 3 latent (seconds) | `89.0` |
| Pass 4 latent (seconds) | `66.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `66.0` |
| Pass 4 latent (seconds) | `66.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `66.0` |
| Pass 4 latent (seconds) | `66.0` |
| Latent length (seconds) | `67.0` |
| Pass 2 latent (seconds) | `67.0` |
| Pass 3 latent (seconds) | `67.0` |
| Latent length (seconds) | `63.0` |
| Pass 2 latent (seconds) | `63.0` |
| Pass 3 latent (seconds) | `63.0` |
| Pass 4 latent (seconds) | `63.0` |
| Latent length (seconds) | `89.0` |
| Pass 2 latent (seconds) | `89.0` |
| Pass 3 latent (seconds) | `77.0` |
| Pass 4 latent (seconds) | `91.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `66.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `66.0` |
| Pass 4 latent (seconds) | `66.0` |
| Latent length (seconds) | `89.0` |
| Pass 2 latent (seconds) | `89.0` |
| Pass 3 latent (seconds) | `89.0` |
| Pass 4 latent (seconds) | `89.0` |
| Pass 5 latent (seconds) | `86.0` |
| Latent length (seconds) | `67.0` |
| Pass 2 latent (seconds) | `67.0` |
| Pass 3 latent (seconds) | `67.0` |
| Pass 4 latent (seconds) | `67.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `91.0` |
| Latent length (seconds) | `79.0` |
| Pass 2 latent (seconds) | `67.0` |
| Pass 3 latent (seconds) | `67.0` |
| Latent length (seconds) | `66.0` |
| Pass 2 latent (seconds) | `66.0` |
| Pass 3 latent (seconds) | `66.0` |
| Pass 4 latent (seconds) | `66.0` |
| Pass 5 latent (seconds) | `66.0` |
| Latent length (seconds) | `67.0` |
| Pass 2 latent (seconds) | `67.0` |
| Pass 3 latent (seconds) | `79.0` |
| Pass 4 latent (seconds) | `67.0` |
| Pass 5 latent (seconds) | `67.0` |

#### `batch_size`

Type `INT`. Range / default: 1.

Takes per Queue.

**How it affects generation:** Stay 1.

**This graph (all 60 instances):** `1`

### `EZAceStepPromptEnhance` - ACE-Step Prompt Enhance

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

**This graph (all 60 instances):** `custom`

#### `tags`

Type `STRING`.

Genre-first tags.

**How it affects generation:** Keep vocal identity tags stable across an album. Drive-through is not rap-over-club.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ez_edm_prompt pass 2 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ez_edm_prompt pass 3 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ez_edm_prompt pass 4 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ez_edm_prompt pass 5 | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ez_edm_prompt | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ez_edm_prompt pass 2 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ez_edm_prompt pass 3 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ez_edm_prompt pass 4 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ez_edm_prompt | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ez_edm_prompt pass 2 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ez_edm_prompt pass 3 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ez_edm_prompt pass 4 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ez_edm_prompt | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ez_edm_prompt pass 2 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ez_edm_prompt pass 3 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ez_edm_prompt pass 4 | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ez_edm_prompt | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ez_edm_prompt pass 2 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ez_edm_prompt pass 3 | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ez_edm_prompt | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ez_edm_prompt pass 2 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ez_edm_prompt pass 3 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ez_edm_prompt pass 4 | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ez_edm_prompt | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ez_edm_prompt pass 2 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ez_edm_prompt pass 3 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ez_edm_prompt pass 4 | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ez_edm_prompt | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ez_edm_prompt pass 2 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ez_edm_prompt pass 3 | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ez_edm_prompt | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ez_edm_prompt pass 2 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ez_edm_prompt pass 3 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ez_edm_prompt pass 4 | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ez_edm_prompt | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ez_edm_prompt pass 2 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ez_edm_prompt pass 3 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ez_edm_prompt pass 4 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ez_edm_prompt pass 5 | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ez_edm_prompt | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ez_edm_prompt pass 2 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ez_edm_prompt pass 3 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ez_edm_prompt pass 4 | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ez_edm_prompt | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ez_edm_prompt pass 2 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ez_edm_prompt pass 3 | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ez_edm_prompt | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ez_edm_prompt pass 2 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ez_edm_prompt pass 3 | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ez_edm_prompt | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ez_edm_prompt pass 2 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ez_edm_prompt pass 3 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ez_edm_prompt pass 4 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ez_edm_prompt pass 5 | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ez_edm_prompt | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ez_edm_prompt pass 2 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ez_edm_prompt pass 3 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ez_edm_prompt pass 4 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ez_edm_prompt pass 5 | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |

#### `lyrics`

Type `STRING`.

Sectioned lyrics.

**How it affects generation:** Enhance off on catalog takes so exclusive verses stay pinned.

| Instance | Value |
| --- | --- |
| ez_edm_prompt | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts...` |
| ez_edm_prompt pass 2 | `[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, ris...` |
| ez_edm_prompt pass 3 | `[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising ...` |
| ez_edm_prompt pass 4 | `[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising...` |
| ez_edm_prompt pass 5 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| ez_edm_prompt | `[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bar...` |
| ez_edm_prompt pass 2 | `[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 b...` |
| ez_edm_prompt pass 3 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, ki...` |
| ez_edm_prompt pass 4 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wi...` |
| ez_edm_prompt | `[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, su...` |
| ez_edm_prompt pass 2 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stut...` |
| ez_edm_prompt pass 3 | `[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats,...` |
| ez_edm_prompt pass 4 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climb...` |
| ez_edm_prompt | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens,...` |
| ez_edm_prompt pass 2 | `[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo pus...` |
| ez_edm_prompt pass 3 | `[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising ...` |
| ez_edm_prompt pass 4 | `[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel lo...` |
| ez_edm_prompt | `[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hat...` |
| ez_edm_prompt pass 2 | `[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bar...` |
| ez_edm_prompt pass 3 | `[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo l...` |
| ez_edm_prompt | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack t...` |
| ez_edm_prompt pass 2 | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo p...` |
| ez_edm_prompt pass 3 | `[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars] ...` |
| ez_edm_prompt pass 4 | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-m...` |
| ez_edm_prompt | `[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kic...` |
| ez_edm_prompt pass 2 | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on down...` |
| ez_edm_prompt pass 3 | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tem...` |
| ez_edm_prompt pass 4 | `[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doub...` |
| ez_edm_prompt | `[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating ha...` |
| ez_edm_prompt pass 2 | `[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 b...` |
| ez_edm_prompt pass 3 | `[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick dou...` |
| ez_edm_prompt | `[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end...` |
| ez_edm_prompt pass 2 | `[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, ...` |
| ez_edm_prompt pass 3 | `[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick...` |
| ez_edm_prompt pass 4 | `[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars] [dr...` |
| ez_edm_prompt | `[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 b...` |
| ez_edm_prompt pass 2 | `[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack...` |
| ez_edm_prompt pass 3 | `[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, ...` |
| ez_edm_prompt pass 4 | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbe...` |
| ez_edm_prompt pass 5 | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| ez_edm_prompt | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-e...` |
| ez_edm_prompt pass 2 | `[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor ki...` |
| ez_edm_prompt pass 3 | `[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, ...` |
| ez_edm_prompt pass 4 | `[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy sur...` |
| ez_edm_prompt | `[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, ...` |
| ez_edm_prompt pass 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, ri...` |
| ez_edm_prompt pass 3 | `[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody c...` |
| ez_edm_prompt | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass ...` |
| ez_edm_prompt pass 2 | `[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, risin...` |
| ez_edm_prompt pass 3 | `[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2...` |
| ez_edm_prompt | `[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor ki...` |
| ez_edm_prompt pass 2 | `[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid or...` |
| ez_edm_prompt pass 3 | `[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, risi...` |
| ez_edm_prompt pass 4 | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit w...` |
| ez_edm_prompt pass 5 | `[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars] [drop...` |
| ez_edm_prompt | `[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bar...` |
| ez_edm_prompt pass 2 | `[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 ba...` |
| ez_edm_prompt pass 3 | `[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hat...` |
| ez_edm_prompt pass 4 | `[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run,...` |
| ez_edm_prompt pass 5 | `[build-up - chest-sub, layers surround the ear, kick tightens, bass melody clim...` |

#### `enhance`

Type `BOOLEAN`. Range / default: false on albums.

Run the rewriter.

**How it affects generation:** On only when you typed a lazy hook and want the GGUF to expand it.

**This graph (all 60 instances):** `false`

#### `mode`

Type `COMBO`.

Vocal vs instrumental sanitizer.

**How it affects generation:** instrumental forces no-vocals tags and [inst] lyrics.

**This graph (all 60 instances):** `instrumental`

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
| ez_edm_prompt | `audio/albums/drive-through/hour-2/01-rumble-strip` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/01-rumble-strip` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/01-rumble-strip` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/01-rumble-strip` |
| ez_edm_prompt pass 5 | `audio/albums/drive-through/hour-2/01-rumble-strip` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/02-low-lane` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/02-low-lane` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/02-low-lane` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/02-low-lane` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/03-warm-merge` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/03-warm-merge` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/03-warm-merge` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/03-warm-merge` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/04-colour-span` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/04-colour-span` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/04-colour-span` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/04-colour-span` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/05-garage-ticket` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/05-garage-ticket` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/05-garage-ticket` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/06-liquid-grade` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/06-liquid-grade` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/06-liquid-grade` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/06-liquid-grade` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/07-jump-bay` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/07-jump-bay` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/07-jump-bay` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/07-jump-bay` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/08-psy-median` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/08-psy-median` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/08-psy-median` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/09-groove-mile` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/09-groove-mile` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/09-groove-mile` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/09-groove-mile` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/10-donk-ramp` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/10-donk-ramp` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/10-donk-ramp` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/10-donk-ramp` |
| ez_edm_prompt pass 5 | `audio/albums/drive-through/hour-2/10-donk-ramp` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/11-bounce-booth` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/11-bounce-booth` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/11-bounce-booth` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/11-bounce-booth` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/12-toll-growl` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/12-toll-growl` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/12-toll-growl` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/13-night-oil` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/13-night-oil` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/13-night-oil` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/14-chest-pass` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/14-chest-pass` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/14-chest-pass` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/14-chest-pass` |
| ez_edm_prompt pass 5 | `audio/albums/drive-through/hour-2/14-chest-pass` |
| ez_edm_prompt | `audio/albums/drive-through/hour-2/15-sunrise-sub` |
| ez_edm_prompt pass 2 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |
| ez_edm_prompt pass 3 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |
| ez_edm_prompt pass 4 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |
| ez_edm_prompt pass 5 | `audio/albums/drive-through/hour-2/15-sunrise-sub` |

### `TextEncodeAceStepAudio1.5` - ACE-Step 1.5 Text Encode

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
| ACE tags + lyrics | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ACE tags + lyrics (pass 2) | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ACE tags + lyrics (pass 3) | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ACE tags + lyrics (pass 4) | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ACE tags + lyrics (pass 5) | `warped hybrid-trap, trap drums, rapid hi-hats, dual-action pedal bass, chest-su...` |
| ACE tags + lyrics | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ACE tags + lyrics (pass 2) | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ACE tags + lyrics (pass 3) | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ACE tags + lyrics (pass 4) | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, stacked 808, 808, or...` |
| ACE tags + lyrics | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ACE tags + lyrics (pass 2) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ACE tags + lyrics (pass 3) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ACE tags + lyrics (pass 4) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, chest-sub bass, origina...` |
| ACE tags + lyrics | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ACE tags + lyrics (pass 2) | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ACE tags + lyrics (pass 3) | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ACE tags + lyrics (pass 4) | `color bass, low-mid bass, chest-sub, rapid hi-hats, trap drums, warped bass, 80...` |
| ACE tags + lyrics | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ACE tags + lyrics (pass 2) | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ACE tags + lyrics (pass 3) | `festival trap, trap drums, 808, rapid hi-hats, warped bass, chest-sub, original...` |
| ACE tags + lyrics | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ACE tags + lyrics (pass 2) | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ACE tags + lyrics (pass 3) | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ACE tags + lyrics (pass 4) | `drumstep, amen break, chest-sub, trap drums, reese bass, warped bass, 808, orig...` |
| ACE tags + lyrics | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ACE tags + lyrics (pass 2) | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ACE tags + lyrics (pass 3) | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ACE tags + lyrics (pass 4) | `dirty dubstep, wobble bass, chest-sub, rapid hi-hats, trap drums, growl bass, 8...` |
| ACE tags + lyrics | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ACE tags + lyrics (pass 2) | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ACE tags + lyrics (pass 3) | `neuro bass, reese bass, chest-sub, rapid hi-hats, trap drums, stacked 808, warp...` |
| ACE tags + lyrics | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ACE tags + lyrics (pass 2) | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ACE tags + lyrics (pass 3) | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ACE tags + lyrics (pass 4) | `warped hybrid-trap, trap drums, rapid hi-hats, warped bass, chest-sub, 808, ori...` |
| ACE tags + lyrics | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ACE tags + lyrics (pass 2) | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ACE tags + lyrics (pass 3) | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ACE tags + lyrics (pass 4) | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ACE tags + lyrics (pass 5) | `tearout, warped bass, chest-sub, rapid hi-hats, trap drums, growl bass, 808, or...` |
| ACE tags + lyrics | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ACE tags + lyrics (pass 2) | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ACE tags + lyrics (pass 3) | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ACE tags + lyrics (pass 4) | `chest bass, chest-sub, 808, rapid hi-hats, trap drums, warped bass, original co...` |
| ACE tags + lyrics | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ACE tags + lyrics (pass 2) | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ACE tags + lyrics (pass 3) | `riddim, warped bass, chest-sub, rapid hi-hats, trap drums, wobble bass, 808, or...` |
| ACE tags + lyrics | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ACE tags + lyrics (pass 2) | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ACE tags + lyrics (pass 3) | `warped hybrid-trap, trap drums, rapid hi-hats, chest-sub bass, warped bass, 808...` |
| ACE tags + lyrics | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ACE tags + lyrics (pass 2) | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ACE tags + lyrics (pass 3) | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ACE tags + lyrics (pass 4) | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ACE tags + lyrics (pass 5) | `dirty bass, warped bass, chest-sub, rapid hi-hats, trap drums, dual-action peda...` |
| ACE tags + lyrics | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ACE tags + lyrics (pass 2) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ACE tags + lyrics (pass 3) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ACE tags + lyrics (pass 4) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |
| ACE tags + lyrics (pass 5) | `wave bass, warped bass, 808, rapid hi-hats, trap drums, fold bass, chest-sub, o...` |

#### `lyrics`

Type `STRING`.

Sectioned lyrics or [inst] cues.

**How it affects generation:** Non-empty lines under a section are sung. Instrumental graphs must keep cues inside [brackets].

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, sub energy lifts...` |
| ACE tags + lyrics (pass 2) | `[build-up - FM warp sub, 3D low-mid orbit, kick tightens, octave 808 stack, ris...` |
| ACE tags + lyrics (pass 3) | `[build-up - chest-sub, wide 3D bass field, kick tightens, rolling hats, rising ...` |
| ACE tags + lyrics (pass 4) | `[build-up - FM warp sub, panning low-mid sweep, kick tightens, kick run, rising...` |
| ACE tags + lyrics (pass 5) | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| ACE tags + lyrics | `[build-up - wavy phase sub, bass circles the low-mid, downbeat sub pulse, 2 bar...` |
| ACE tags + lyrics (pass 2) | `[build-up - neuro wobble sub, bass circles the low-mid, downbeat sub pulse, 2 b...` |
| ACE tags + lyrics (pass 3) | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, ki...` |
| ACE tags + lyrics (pass 4) | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick tightens, wi...` |
| ACE tags + lyrics | `[build-up - neuro wobble sub, sub center, low-mid moves wide, kick tightens, su...` |
| ACE tags + lyrics (pass 2) | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick tightens, stut...` |
| ACE tags + lyrics (pass 3) | `[build-up - FM warp sub, low-mid from every angle, kick tightens, rolling hats,...` |
| ACE tags + lyrics (pass 4) | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, bass melody climb...` |
| ACE tags + lyrics | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, kick tightens,...` |
| ACE tags + lyrics (pass 2) | `[build-up - chest-sub, wide 3D bass field, kick tightens, side snare, tempo pus...` |
| ACE tags + lyrics (pass 3) | `[build-up - bitcrushed 808, 3D low-mid orbit, kick tightens, sub swell, rising ...` |
| ACE tags + lyrics (pass 4) | `[build-up - neuro wobble sub, panning low-mid sweep, kick tightens, parallel lo...` |
| ACE tags + lyrics | `[build-up - chest-sub, layers surround the ear, kick tightens, accelerating hat...` |
| ACE tags + lyrics (pass 2) | `[build-up - FM warp sub, layers surround the ear, kick only on downbeats, 2 bar...` |
| ACE tags + lyrics (pass 3) | `[build-up - phase-distorted sub, 3D low-mid orbit, kick tightens, wide stereo l...` |
| ACE tags + lyrics | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid stack t...` |
| ACE tags + lyrics (pass 2) | `[build-up - bitcrushed 808, wide 3D bass field, kick tightens, tom run, tempo p...` |
| ACE tags + lyrics (pass 3) | `[build-up - neuro wobble sub, sub anchored, mids orbit, downbeat kick, 2 bars] ...` |
| ACE tags + lyrics (pass 4) | `[build-up - octave sub pulse, wide 3D bass field, kick tightens, parallel low-m...` |
| ACE tags + lyrics | `[build-up - neuro wobble sub, bass circles the low-mid, kick tightens, mono kic...` |
| ACE tags + lyrics (pass 2) | `[build-up - octave sub pulse, sub center, low-mid moves wide, kick only on down...` |
| ACE tags + lyrics (pass 3) | `[build-up - chest-sub, low-mid orbits the sub, kick tightens, beat stutter, tem...` |
| ACE tags + lyrics (pass 4) | `[build-up - chest-sub, sub center, low-mid moves wide, kick tightens, kick doub...` |
| ACE tags + lyrics | `[build-up - FM warp sub, low-mid orbits the sub, kick tightens, accelerating ha...` |
| ACE tags + lyrics (pass 2) | `[build-up - wavy phase sub, low-mid orbits the sub, kick only on downbeats, 2 b...` |
| ACE tags + lyrics (pass 3) | `[build-up - octave sub pulse, low-mid from every angle, kick tightens, kick dou...` |
| ACE tags + lyrics | `[build-up - FM warp sub, sub center, low-mid moves wide, kick tightens, low-end...` |
| ACE tags + lyrics (pass 2) | `[build-up - wavy phase sub, low-mid orbits the sub, kick tightens, gated bass, ...` |
| ACE tags + lyrics (pass 3) | `[build-up - neuro wobble sub, low-mid orbits the sub, sparse four-on-floor kick...` |
| ACE tags + lyrics (pass 4) | `[build-up - octave sub pulse, bass pans wide behind, downbeat kick, 2 bars] [dr...` |
| ACE tags + lyrics | `[build-up - phase-distorted sub, panning low-mid sweep, downbeat sub pulse, 2 b...` |
| ACE tags + lyrics (pass 2) | `[build-up - octave sub pulse, 3D low-mid orbit, kick tightens, octave 808 stack...` |
| ACE tags + lyrics (pass 3) | `[build-up - wavy phase sub, bass circles the low-mid, kick tightens, kick run, ...` |
| ACE tags + lyrics (pass 4) | `[build-up - bitcrushed 808, sub center, low-mid moves wide, kick only on downbe...` |
| ACE tags + lyrics (pass 5) | `[build-up - phase-distorted sub, bass circles the low-mid, kick tightens, energ...` |
| ACE tags + lyrics | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, low-e...` |
| ACE tags + lyrics (pass 2) | `[build-up - octave sub pulse, low-mid from every angle, sparse four-on-floor ki...` |
| ACE tags + lyrics (pass 3) | `[build-up - neuro wobble sub, wide 3D bass field, kick tightens, triplet hats, ...` |
| ACE tags + lyrics (pass 4) | `[build-up - wavy phase sub, sub anchored, mids orbit, kick tightens, energy sur...` |
| ACE tags + lyrics | `[build-up - octave sub pulse, layers surround the ear, kick only on downbeats, ...` |
| ACE tags + lyrics (pass 2) | `[build-up - chest-sub, layers surround the ear, kick tightens, beat stutter, ri...` |
| ACE tags + lyrics (pass 3) | `[build-up - bitcrushed 808, panning low-mid sweep, kick tightens, bass melody c...` |
| ACE tags + lyrics | `[build-up - phase-distorted sub, low-mid from every angle, kick tightens, bass ...` |
| ACE tags + lyrics (pass 2) | `[build-up - chest-sub, layers surround the ear, kick tightens, sub swell, risin...` |
| ACE tags + lyrics (pass 3) | `[build-up - FM warp sub, sub anchored, mids orbit, sparse four-on-floor kick, 2...` |
| ACE tags + lyrics | `[build-up - neuro wobble sub, low-mid from every angle, sparse four-on-floor ki...` |
| ACE tags + lyrics (pass 2) | `[build-up - bitcrushed 808, low-mid from every angle, kick tightens, low-mid or...` |
| ACE tags + lyrics (pass 3) | `[build-up - FM warp sub, layers surround the ear, kick tightens, kick run, risi...` |
| ACE tags + lyrics (pass 4) | `[build-up - chest-sub, low-mid from every angle, kick tightens, low-mid orbit w...` |
| ACE tags + lyrics (pass 5) | `[build-up - FM warp sub, sub anchored, mids orbit, downbeat kick, 2 bars] [drop...` |
| ACE tags + lyrics | `[build-up - wavy phase sub, sub anchored, mids orbit, downbeat sub pulse, 2 bar...` |
| ACE tags + lyrics (pass 2) | `[build-up - neuro wobble sub, layers surround the ear, downbeat sub pulse, 2 ba...` |
| ACE tags + lyrics (pass 3) | `[build-up - bitcrushed 808, layers surround the ear, kick tightens, rolling hat...` |
| ACE tags + lyrics (pass 4) | `[build-up - octave sub pulse, layers surround the ear, kick tightens, kick run,...` |
| ACE tags + lyrics (pass 5) | `[build-up - chest-sub, layers surround the ear, kick tightens, bass melody clim...` |

#### `seed`

Type `INT`.

ACE encoder seed (audio-codes LLM).

**How it affects generation:** Independent from KSampler seed. Lab locks it with the take.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `271` |
| ACE tags + lyrics (pass 2) | `271` |
| ACE tags + lyrics (pass 3) | `271` |
| ACE tags + lyrics (pass 4) | `271` |
| ACE tags + lyrics (pass 5) | `271` |
| ACE tags + lyrics | `277` |
| ACE tags + lyrics (pass 2) | `277` |
| ACE tags + lyrics (pass 3) | `277` |
| ACE tags + lyrics (pass 4) | `277` |
| ACE tags + lyrics | `281` |
| ACE tags + lyrics (pass 2) | `281` |
| ACE tags + lyrics (pass 3) | `281` |
| ACE tags + lyrics (pass 4) | `281` |
| ACE tags + lyrics | `283` |
| ACE tags + lyrics (pass 2) | `283` |
| ACE tags + lyrics (pass 3) | `283` |
| ACE tags + lyrics (pass 4) | `283` |
| ACE tags + lyrics | `293` |
| ACE tags + lyrics (pass 2) | `293` |
| ACE tags + lyrics (pass 3) | `293` |
| ACE tags + lyrics | `307` |
| ACE tags + lyrics (pass 2) | `307` |
| ACE tags + lyrics (pass 3) | `307` |
| ACE tags + lyrics (pass 4) | `307` |
| ACE tags + lyrics | `311` |
| ACE tags + lyrics (pass 2) | `311` |
| ACE tags + lyrics (pass 3) | `311` |
| ACE tags + lyrics (pass 4) | `311` |
| ACE tags + lyrics | `313` |
| ACE tags + lyrics (pass 2) | `313` |
| ACE tags + lyrics (pass 3) | `313` |
| ACE tags + lyrics | `317` |
| ACE tags + lyrics (pass 2) | `317` |
| ACE tags + lyrics (pass 3) | `317` |
| ACE tags + lyrics (pass 4) | `317` |
| ACE tags + lyrics | `331` |
| ACE tags + lyrics (pass 2) | `331` |
| ACE tags + lyrics (pass 3) | `331` |
| ACE tags + lyrics (pass 4) | `331` |
| ACE tags + lyrics (pass 5) | `331` |
| ACE tags + lyrics | `337` |
| ACE tags + lyrics (pass 2) | `337` |
| ACE tags + lyrics (pass 3) | `337` |
| ACE tags + lyrics (pass 4) | `337` |
| ACE tags + lyrics | `347` |
| ACE tags + lyrics (pass 2) | `347` |
| ACE tags + lyrics (pass 3) | `347` |
| ACE tags + lyrics | `349` |
| ACE tags + lyrics (pass 2) | `349` |
| ACE tags + lyrics (pass 3) | `349` |
| ACE tags + lyrics | `353` |
| ACE tags + lyrics (pass 2) | `353` |
| ACE tags + lyrics (pass 3) | `353` |
| ACE tags + lyrics (pass 4) | `353` |
| ACE tags + lyrics (pass 5) | `353` |
| ACE tags + lyrics | `359` |
| ACE tags + lyrics (pass 2) | `359` |
| ACE tags + lyrics (pass 3) | `359` |
| ACE tags + lyrics (pass 4) | `359` |
| ACE tags + lyrics (pass 5) | `359` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed.

Seed control.

**How it affects generation:** fixed on every lab take.

**This graph (all 60 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

#### `bpm`

Type `INT`. Range / default: 10-300.

Tempo written into the codes.

**How it affects generation:** Must match the tags' BPM. Mismatch makes the vocal drift the grid.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics (pass 2) | `165` |
| ACE tags + lyrics (pass 3) | `165` |
| ACE tags + lyrics (pass 4) | `165` |
| ACE tags + lyrics (pass 5) | `165` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics (pass 2) | `165` |
| ACE tags + lyrics (pass 3) | `165` |
| ACE tags + lyrics | `176` |
| ACE tags + lyrics (pass 2) | `176` |
| ACE tags + lyrics (pass 3) | `176` |
| ACE tags + lyrics (pass 4) | `176` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics (pass 5) | `168` |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics (pass 2) | `165` |
| ACE tags + lyrics (pass 3) | `165` |
| ACE tags + lyrics (pass 4) | `165` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics (pass 2) | `165` |
| ACE tags + lyrics (pass 3) | `165` |
| ACE tags + lyrics | `168` |
| ACE tags + lyrics (pass 2) | `168` |
| ACE tags + lyrics (pass 3) | `168` |
| ACE tags + lyrics (pass 4) | `168` |
| ACE tags + lyrics (pass 5) | `168` |
| ACE tags + lyrics | `165` |
| ACE tags + lyrics (pass 2) | `165` |
| ACE tags + lyrics (pass 3) | `165` |
| ACE tags + lyrics (pass 4) | `165` |
| ACE tags + lyrics (pass 5) | `165` |

#### `duration`

Type `FLOAT`.

Seconds (duplicated on the latent).

**How it affects generation:** Keep in lockstep with EmptyAceStep1.5LatentAudio / Primitive.

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `67.0` |
| ACE tags + lyrics (pass 2) | `67.0` |
| ACE tags + lyrics (pass 3) | `67.0` |
| ACE tags + lyrics (pass 4) | `67.0` |
| ACE tags + lyrics (pass 5) | `67.0` |
| ACE tags + lyrics | `89.0` |
| ACE tags + lyrics (pass 2) | `89.0` |
| ACE tags + lyrics (pass 3) | `89.0` |
| ACE tags + lyrics (pass 4) | `66.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `66.0` |
| ACE tags + lyrics (pass 4) | `66.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `66.0` |
| ACE tags + lyrics (pass 4) | `66.0` |
| ACE tags + lyrics | `67.0` |
| ACE tags + lyrics (pass 2) | `67.0` |
| ACE tags + lyrics (pass 3) | `67.0` |
| ACE tags + lyrics | `63.0` |
| ACE tags + lyrics (pass 2) | `63.0` |
| ACE tags + lyrics (pass 3) | `63.0` |
| ACE tags + lyrics (pass 4) | `63.0` |
| ACE tags + lyrics | `89.0` |
| ACE tags + lyrics (pass 2) | `89.0` |
| ACE tags + lyrics (pass 3) | `77.0` |
| ACE tags + lyrics (pass 4) | `91.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `66.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `66.0` |
| ACE tags + lyrics (pass 4) | `66.0` |
| ACE tags + lyrics | `89.0` |
| ACE tags + lyrics (pass 2) | `89.0` |
| ACE tags + lyrics (pass 3) | `89.0` |
| ACE tags + lyrics (pass 4) | `89.0` |
| ACE tags + lyrics (pass 5) | `86.0` |
| ACE tags + lyrics | `67.0` |
| ACE tags + lyrics (pass 2) | `67.0` |
| ACE tags + lyrics (pass 3) | `67.0` |
| ACE tags + lyrics (pass 4) | `67.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `91.0` |
| ACE tags + lyrics | `79.0` |
| ACE tags + lyrics (pass 2) | `67.0` |
| ACE tags + lyrics (pass 3) | `67.0` |
| ACE tags + lyrics | `66.0` |
| ACE tags + lyrics (pass 2) | `66.0` |
| ACE tags + lyrics (pass 3) | `66.0` |
| ACE tags + lyrics (pass 4) | `66.0` |
| ACE tags + lyrics (pass 5) | `66.0` |
| ACE tags + lyrics | `67.0` |
| ACE tags + lyrics (pass 2) | `67.0` |
| ACE tags + lyrics (pass 3) | `79.0` |
| ACE tags + lyrics (pass 4) | `67.0` |
| ACE tags + lyrics (pass 5) | `67.0` |

#### `timesignature`

Type `COMBO`. Range / default: 4.

Beats per bar.

**How it affects generation:** Rap Apps stay 4. Album takes may use 2, 3, or 6 when the bed is not a dance grid.

**This graph (all 60 instances):** `4`

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

**This graph (all 60 instances):** `unknown`

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

**How it affects generation:** Rap Apps stay C minor. Catalog takes set a key per song (Drive-through walks fifths).

| Instance | Value |
| --- | --- |
| ACE tags + lyrics | `D major` |
| ACE tags + lyrics (pass 2) | `D major` |
| ACE tags + lyrics (pass 3) | `D major` |
| ACE tags + lyrics (pass 4) | `D major` |
| ACE tags + lyrics (pass 5) | `D major` |
| ACE tags + lyrics | `F# minor` |
| ACE tags + lyrics (pass 2) | `F# minor` |
| ACE tags + lyrics (pass 3) | `F# minor` |
| ACE tags + lyrics (pass 4) | `F# minor` |
| ACE tags + lyrics | `A major` |
| ACE tags + lyrics (pass 2) | `A major` |
| ACE tags + lyrics (pass 3) | `A major` |
| ACE tags + lyrics (pass 4) | `A major` |
| ACE tags + lyrics | `A minor` |
| ACE tags + lyrics (pass 2) | `A minor` |
| ACE tags + lyrics (pass 3) | `A minor` |
| ACE tags + lyrics (pass 4) | `A minor` |
| ACE tags + lyrics | `C major` |
| ACE tags + lyrics (pass 2) | `C major` |
| ACE tags + lyrics (pass 3) | `C major` |
| ACE tags + lyrics | `E minor` |
| ACE tags + lyrics (pass 2) | `E minor` |
| ACE tags + lyrics (pass 3) | `E minor` |
| ACE tags + lyrics (pass 4) | `E minor` |
| ACE tags + lyrics | `G major` |
| ACE tags + lyrics (pass 2) | `G major` |
| ACE tags + lyrics (pass 3) | `G major` |
| ACE tags + lyrics (pass 4) | `G major` |
| ACE tags + lyrics | `B minor` |
| ACE tags + lyrics (pass 2) | `B minor` |
| ACE tags + lyrics (pass 3) | `B minor` |
| ACE tags + lyrics | `D major` |
| ACE tags + lyrics (pass 2) | `D major` |
| ACE tags + lyrics (pass 3) | `D major` |
| ACE tags + lyrics (pass 4) | `D major` |
| ACE tags + lyrics | `F# minor` |
| ACE tags + lyrics (pass 2) | `F# minor` |
| ACE tags + lyrics (pass 3) | `F# minor` |
| ACE tags + lyrics (pass 4) | `F# minor` |
| ACE tags + lyrics (pass 5) | `F# minor` |
| ACE tags + lyrics | `A major` |
| ACE tags + lyrics (pass 2) | `A major` |
| ACE tags + lyrics (pass 3) | `A major` |
| ACE tags + lyrics (pass 4) | `A major` |
| ACE tags + lyrics | `A minor` |
| ACE tags + lyrics (pass 2) | `A minor` |
| ACE tags + lyrics (pass 3) | `A minor` |
| ACE tags + lyrics | `C major` |
| ACE tags + lyrics (pass 2) | `C major` |
| ACE tags + lyrics (pass 3) | `C major` |
| ACE tags + lyrics | `E minor` |
| ACE tags + lyrics (pass 2) | `E minor` |
| ACE tags + lyrics (pass 3) | `E minor` |
| ACE tags + lyrics (pass 4) | `E minor` |
| ACE tags + lyrics (pass 5) | `E minor` |
| ACE tags + lyrics | `G major` |
| ACE tags + lyrics (pass 2) | `G major` |
| ACE tags + lyrics (pass 3) | `G major` |
| ACE tags + lyrics (pass 4) | `G major` |
| ACE tags + lyrics (pass 5) | `G major` |

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
| `C minor` | Rap Apps stay C minor. Catalog takes set a key per song. Drive-through walks fifths so a live set still mixes. |
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

**This graph (all 60 instances):** `true`

#### `cfg_scale`

Type `FLOAT`. Range / default: 2.0.

Guidance inside audio-code generation.

**How it affects generation:** 2.0 is the ACE default. Higher follows tags/lyrics more tightly and can sound rigid.

**This graph (all 60 instances):** `2.0`

#### `temperature`

Type `FLOAT`. Range / default: 0.85.

Sampling temperature for audio codes.

**How it affects generation:** Lower = more deterministic. Higher = wilder fills.

**This graph (all 60 instances):** `0.85`

#### `top_p`

Type `FLOAT`. Range / default: 0.9.

Nucleus sampling.

**How it affects generation:** 0.9 is the lab default.

**This graph (all 60 instances):** `0.9`

#### `top_k`

Type `INT`. Range / default: 0 = off.

Top-k token cap.

**How it affects generation:** 0 disables top-k (lab).

**This graph (all 60 instances):** `0`

#### `min_p`

Type `FLOAT`. Range / default: 0.0.

Minimum probability floor.

**How it affects generation:** 0.0 disables min-p (lab).

**This graph (all 60 instances):** `0.0`

### `ConditioningZeroOut` - Conditioning Zero Out

Replace a conditioning with zeros (unconditional / empty negative).

!!! warning "Lab notes"

    ACE graphs zero the negative so CFG 1.0 stays a true uncond skip.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `conditioning` | in | `CONDITIONING` | Usually an unused negative encode. |
| `CONDITIONING` | out | `CONDITIONING` | Zeroed cond for KSampler.negative. |

No widgets. Sockets only.

### `KSampler` - KSampler

Denoise a latent for N steps at a CFG, sampler, and scheduler.

!!! warning "Lab notes"

    Distilled Klein is CFG 1.0 / 4 steps / euler / simple. Raising CFG is not a quality knob. Wan 5B uses uni_pc and CFG 5. LTX distilled uses euler / simple / CFG 1.0 / 20 steps. ACE-Step uses 8 steps / CFG 1.0 / euler. TRELLIS uses 12 steps / CFG 7.5 / euler / normal.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `model` | in | `MODEL` | UNET / transformer after any ModelSampling* patch. |
| `positive` | in | `CONDITIONING` | What to include (CLIP / ACE / LTX prompt). |
| `negative` | in | `CONDITIONING` | What to avoid. Distilled Klein ignores this well - put constraints in the positive. |
| `latent_image` | in | `LATENT` | Noise canvas or encoded start image / video / audio latent. |
| `LATENT` | out | `LATENT` | Denoised latent for VAE decode. |

#### `seed`

Type `INT`. Range / default: 0 ... 2^64-1; lab 42.

Random seed for the noise tensor.

**How it affects generation:** Same seed + same graph ~ same picture or clip. Lab locks 42 on smokes so drafts are comparable.

| Instance | Value |
| --- | --- |
| ACE sampler | `271` |
| ACE sampler (pass 2) | `271` |
| ACE sampler (pass 3) | `271` |
| ACE sampler (pass 4) | `271` |
| ACE sampler (pass 5) | `271` |
| ACE sampler | `277` |
| ACE sampler (pass 2) | `277` |
| ACE sampler (pass 3) | `277` |
| ACE sampler (pass 4) | `277` |
| ACE sampler | `281` |
| ACE sampler (pass 2) | `281` |
| ACE sampler (pass 3) | `281` |
| ACE sampler (pass 4) | `281` |
| ACE sampler | `283` |
| ACE sampler (pass 2) | `283` |
| ACE sampler (pass 3) | `283` |
| ACE sampler (pass 4) | `283` |
| ACE sampler | `293` |
| ACE sampler (pass 2) | `293` |
| ACE sampler (pass 3) | `293` |
| ACE sampler | `307` |
| ACE sampler (pass 2) | `307` |
| ACE sampler (pass 3) | `307` |
| ACE sampler (pass 4) | `307` |
| ACE sampler | `311` |
| ACE sampler (pass 2) | `311` |
| ACE sampler (pass 3) | `311` |
| ACE sampler (pass 4) | `311` |
| ACE sampler | `313` |
| ACE sampler (pass 2) | `313` |
| ACE sampler (pass 3) | `313` |
| ACE sampler | `317` |
| ACE sampler (pass 2) | `317` |
| ACE sampler (pass 3) | `317` |
| ACE sampler (pass 4) | `317` |
| ACE sampler | `331` |
| ACE sampler (pass 2) | `331` |
| ACE sampler (pass 3) | `331` |
| ACE sampler (pass 4) | `331` |
| ACE sampler (pass 5) | `331` |
| ACE sampler | `337` |
| ACE sampler (pass 2) | `337` |
| ACE sampler (pass 3) | `337` |
| ACE sampler (pass 4) | `337` |
| ACE sampler | `347` |
| ACE sampler (pass 2) | `347` |
| ACE sampler (pass 3) | `347` |
| ACE sampler | `349` |
| ACE sampler (pass 2) | `349` |
| ACE sampler (pass 3) | `349` |
| ACE sampler | `353` |
| ACE sampler (pass 2) | `353` |
| ACE sampler (pass 3) | `353` |
| ACE sampler (pass 4) | `353` |
| ACE sampler (pass 5) | `353` |
| ACE sampler | `359` |
| ACE sampler (pass 2) | `359` |
| ACE sampler (pass 3) | `359` |
| ACE sampler (pass 4) | `359` |
| ACE sampler (pass 5) | `359` |
| KSampler | `42` |

#### `control_after_generate`

Type `COMBO`. Range / default: fixed (lab).

What happens to seed after Queue.

**How it affects generation:** fixed keeps iteration honest while you change the prompt.

**This graph (all 61 instances):** `fixed`

**Other choices**

| Choice | What it does |
| --- | --- |
| `fixed` | Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints. |
| `increment` | Add 1 after Queue. Use for a sequence of variations. |
| `decrement` | Subtract 1 after Queue. |
| `randomize` | Draw a new seed after Queue. Exploration only. |

#### `steps`

Type `INT`. Range / default: 1-10000; Klein distilled 4; LTX 20; Wan 20; ACE 8; TRELLIS 12.

Denoising iterations.

**How it affects generation:** More steps refine detail with diminishing returns. Distilled Klein is authored at 4 - raising steps is slower, not a quality knob. Do not raise LTX/Wan toward a 90 s denoise.

**This graph (all 61 instances):** `8`

#### `cfg`

Type `FLOAT`. Range / default: 0-100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5.

Classifier-free guidance scale.

**How it affects generation:** Distilled Klein is CFG 1.0 - raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.

**This graph (all 61 instances):** `1.0`

#### `sampler_name`

Type `COMBO`. Range / default: euler (most lab); uni_pc (Wan).

ODE / SDE algorithm that removes noise.

**How it affects generation:** euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.

**This graph (all 61 instances):** `euler`

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

**This graph (all 61 instances):** `simple`

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

Type `FLOAT`. Range / default: 0-1; lab 1.0.

Fraction of the latent to replace with denoised signal.

**How it affects generation:** 1.0 is full generation (T2I / T2V / ACE). Values below 1 keep structure from an encoded start image (Klein edit / clay). Lab I2V uses dedicated latent nodes, not denoise<1 on empty noise.

**This graph (all 61 instances):** `1.0`

### `VAEDecodeAudio` - VAE Decode Audio

Decode an ACE audio latent to AUDIO.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | ACE KSampler output. |
| `vae` | in | `VAE` | ACE VAE from the AIO checkpoint. |
| `AUDIO` | out | `AUDIO` | Waveform for SaveAudio. |

No widgets. Sockets only.

### `SaveAudio` - Save Audio

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
| FLAC master | `01 - Rumble Strip` |
| FLAC master | `02 - Low Lane` |
| FLAC master | `03 - Warm Merge` |
| FLAC master | `04 - Colour Span` |
| FLAC master | `05 - Garage Ticket` |
| FLAC master | `06 - Liquid Grade` |
| FLAC master | `07 - Jump Bay` |
| FLAC master | `08 - Psy Median` |
| FLAC master | `09 - Groove Mile` |
| FLAC master | `10 - Donk Ramp` |
| FLAC master | `11 - Bounce Booth` |
| FLAC master | `12 - Toll Growl` |
| FLAC master | `13 - Night Oil` |
| FLAC master | `14 - Chest Pass` |
| FLAC master | `15 - Sunrise Sub` |

### `SaveAudioMP3` - Save Audio (MP3)

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
| MP3 320k | `01 - Rumble Strip` |
| MP3 320k | `02 - Low Lane` |
| MP3 320k | `03 - Warm Merge` |
| MP3 320k | `04 - Colour Span` |
| MP3 320k | `05 - Garage Ticket` |
| MP3 320k | `06 - Liquid Grade` |
| MP3 320k | `07 - Jump Bay` |
| MP3 320k | `08 - Psy Median` |
| MP3 320k | `09 - Groove Mile` |
| MP3 320k | `10 - Donk Ramp` |
| MP3 320k | `11 - Bounce Booth` |
| MP3 320k | `12 - Toll Growl` |
| MP3 320k | `13 - Night Oil` |
| MP3 320k | `14 - Chest Pass` |
| MP3 320k | `15 - Sunrise Sub` |

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

### `Note` - Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

| Instance | Value |
| --- | --- |
| Operator note | `## 01-rumble-strip US-safe EDM **325 s** take: **rumble strip**. Fictional act ...` |
| Operator note | `## 02-low-lane US-safe EDM **324 s** take: **low lane**. Fictional act **Drive-...` |
| Operator note | `## 03-warm-merge US-safe EDM **255 s** take: **warm merge**. Fictional act **Dr...` |
| Operator note | `## 04-colour-span US-safe EDM **257 s** take: **colour span**. Fictional act **...` |
| Operator note | `## 05-garage-ticket US-safe EDM **195 s** take: **garage ticket**. Fictional ac...` |
| Operator note | `## 06-liquid-grade US-safe EDM **245 s** take: **liquid grade**. Fictional act ...` |
| Operator note | `## 07-jump-bay US-safe EDM **337 s** take: **jump bay**. Fictional act **Drive-...` |
| Operator note | `## 08-psy-median US-safe EDM **194 s** take: **psy median**. Fictional act **Dr...` |
| Operator note | `## 09-groove-mile US-safe EDM **257 s** take: **groove mile**. Fictional act **...` |
| Operator note | `## 10-donk-ramp US-safe EDM **432 s** take: **donk ramp**. Fictional act **Driv...` |
| Operator note | `## 11-bounce-booth US-safe EDM **261 s** take: **bounce booth**. Fictional act ...` |
| Operator note | `## 12-toll-growl US-safe EDM **217 s** take: **toll growl**. Fictional act **Dr...` |
| Operator note | `## 13-night-oil US-safe EDM **209 s** take: **night oil**. Fictional act **Driv...` |
| Operator note | `## 14-chest-pass US-safe EDM **320 s** take: **chest pass**. Fictional act **Dr...` |
| Operator note | `## 15-sunrise-sub US-safe EDM **337 s** take: **sunrise sub**. Fictional act **...` |
| Operator note | `## audio/albums/drive-through/hour-2/album Album **Hour 2** by **Drive-through*...` |
| Operator note | `## audio/albums/drive-through/hour-2/cover Format / platform sets pixels (Custo...` |

### `LoadImage` - Load Image

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
| Draft still (set to ez_still_draft_0000... | `example.png` |

#### `upload`

Type `COMBO`. Range / default: image.

Upload widget type.

**How it affects generation:** Leave image. This is the choose-file control, not a generation knob.

**This graph (all 16 instances):** `image`

### `EZAudioMetadata` - Audio Metadata

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

**This graph (all 15 instances):** `Hour 2`

#### `title`

Type `STRING`.

Track title.

**How it affects generation:** Pairs with SaveAudio stem NN - Song Title.

| Instance | Value |
| --- | --- |
| Album metadata | `Rumble Strip` |
| Album metadata | `Low Lane` |
| Album metadata | `Warm Merge` |
| Album metadata | `Colour Span` |
| Album metadata | `Garage Ticket` |
| Album metadata | `Liquid Grade` |
| Album metadata | `Jump Bay` |
| Album metadata | `Psy Median` |
| Album metadata | `Groove Mile` |
| Album metadata | `Donk Ramp` |
| Album metadata | `Bounce Booth` |
| Album metadata | `Toll Growl` |
| Album metadata | `Night Oil` |
| Album metadata | `Chest Pass` |
| Album metadata | `Sunrise Sub` |

#### `track`

Type `INT`. Range / default: 1-99.

Track number.

**How it affects generation:** Numbered takes 01-20.

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

**How it affects generation:** skip on every audio Queue (Cover LoadImage is bypassed). generate is klein occupancy - later session. upload: graph view, Ctrl+B Cover image, then wire.

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
| Album metadata | `01 - Rumble Strip` |
| Album metadata | `02 - Low Lane` |
| Album metadata | `03 - Warm Merge` |
| Album metadata | `04 - Colour Span` |
| Album metadata | `05 - Garage Ticket` |
| Album metadata | `06 - Liquid Grade` |
| Album metadata | `07 - Jump Bay` |
| Album metadata | `08 - Psy Median` |
| Album metadata | `09 - Groove Mile` |
| Album metadata | `10 - Donk Ramp` |
| Album metadata | `11 - Bounce Booth` |
| Album metadata | `12 - Toll Growl` |
| Album metadata | `13 - Night Oil` |
| Album metadata | `14 - Chest Pass` |
| Album metadata | `15 - Sunrise Sub` |

### `EZAudioBeatJoin` - Beat-join passes

Stitch multi-pass ACE masters into one take on the bar grid.

!!! warning "Lab notes"

    Drive-through takes render 3-5 ACE passes per graph; each pass decodes to its own AUDIO and wires audio_01..audio_NN in render order. SaveAudio, SaveAudioMP3, and EZAudioMetadata read only this node's output.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `audio_01` | in | `AUDIO` | First pass decode (required). |
| `audio_02` | in | `AUDIO` | Second pass decode; holes before a wired socket are an error. |
| `audio_08` | in | `AUDIO` | Optional tail; unused sockets stay unwired. |
| `audio` | out | `AUDIO` | Joined master for the saves and metadata stamp. |

#### `bpm`

Type `INT`. Range / default: 40-300.

Bar-grid tempo.

**How it affects generation:** Matches the take bpm; the bar is 240/bpm seconds at these half-time feels.

| Instance | Value |
| --- | --- |
| Beat-join passes | `165` |
| Beat-join passes | `168` |
| Beat-join passes | `168` |
| Beat-join passes | `168` |
| Beat-join passes | `165` |
| Beat-join passes | `176` |
| Beat-join passes | `168` |
| Beat-join passes | `168` |
| Beat-join passes | `168` |
| Beat-join passes | `168` |
| Beat-join passes | `165` |
| Beat-join passes | `168` |
| Beat-join passes | `165` |
| Beat-join passes | `168` |
| Beat-join passes | `165` |

#### `overlap_bars`

Type `STRING`.

Whole bars per seam.

**How it affects generation:** One number for all seams or comma-separated per seam; the lab ships the plan's overlap bars.

| Instance | Value |
| --- | --- |
| Beat-join passes | `2, 1, 2, 2` |
| Beat-join passes | `2, 2, 2` |
| Beat-join passes | `2, 2, 2` |
| Beat-join passes | `1, 2, 2` |
| Beat-join passes | `2, 2` |
| Beat-join passes | `1, 2, 2` |
| Beat-join passes | `2, 2, 2` |
| Beat-join passes | `1, 2` |
| Beat-join passes | `1, 2, 2` |
| Beat-join passes | `2, 1, 2, 2` |
| Beat-join passes | `1, 2, 2` |
| Beat-join passes | `2, 2` |
| Beat-join passes | `1, 2` |
| Beat-join passes | `2, 1, 2, 2` |
| Beat-join passes | `2, 1, 2, 2` |

#### `crossover_hz`

Type `FLOAT`. Range / default: 40-500.

Sub/mid split.

**How it affects generation:** 120 default; the sub band hands off linearly so two 808s never stack or null.

**This graph (all 15 instances):** `120.0`

### `EZQuality` - Quality

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

### `EZModelCheck` - Check models

Manual disk check for occupancy + Quality weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph (all 17 instances):** `Click Check models. Queue does not run this node.`

### `EZAlbumPack` - Album Pack

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

**This graph:** `Hour 2`

### `UNETLoader` - Load Diffusion Model

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

### `CLIPLoader` - Load CLIP

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

**How it affects generation:** flux2 wraps Klein strings in a Qwen chat template - do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.

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

### `VAELoader` - Load VAE

Load the autoencoder that maps pixels <-> latents (and LTX audio).

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

### `CLIPTextEncode` - CLIP Text Encode

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

**How it affects generation:** Klein: sentences, subject -> place -> light -> camera. Wan I2V: motion + one camera only. LTX: present-tense paragraph with audio interleaved. Distilled Klein quality lives here, not in CFG.

| Instance | Value |
| --- | --- |
| Positive | `square album cover, graphic print, toll booth glow, chest-sub night, long expos...` |
| Negative | `game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melt...` |

### `EmptyFlux2LatentImage` - Empty Flux.2 Latent

Allocate a Klein / Flux.2 still latent (width x height x batch).

!!! warning "Lab notes"

    Draft 768x432 batch 2. Hero / LTX feeders 1280x704. Portrait 1024x1280 or 768x1280. 1280x720 is OK for thumbnails, not for LTX feeders.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `LATENT` | out | `LATENT` | Noise canvas for KSampler. |

#### `width`

Type `INT`. Range / default: lab 768 / 1280 / 1024 / 432....

Latent pixel width.

**How it affects generation:** Sets the still's width. Match the intended platform (16:9, 9:16, 1:1, 4:5).

**This graph:** `1024`

#### `height`

Type `INT`.

Latent pixel height.

**How it affects generation:** 1280x704 is the LTX VAE grid (div32). 1280x720 is not.

**This graph:** `1024`

#### `batch_size`

Type `INT`. Range / default: draft 2; others 1.

How many stills in one Queue.

**How it affects generation:** Draft uses 2 for a cheap fork. Heroes stay 1.

**This graph:** `1`

### `VAEDecode` - VAE Decode

Decode image/video latents to pixels.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `samples` | in | `LATENT` | KSampler output (video or still). |
| `vae` | in | `VAE` | Matching family VAE. |
| `IMAGE` | out | `IMAGE` | Frames or still. |

No widgets. Sockets only.

### `SaveImage` - Save Image

Write PNG stills under the output folder.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `images` | in | `IMAGE` | Decoded still or last-frame. |

#### `filename_prefix`

Type `STRING`.

Save prefix.

**How it affects generation:** Lab prefixes start with ez_. Last-frame savers on shot graphs feed concat-shots.

**This graph:** `albums/Drive-through/Hour 2/cover`

### `EZKleinPromptEnhance` - Klein Prompt Enhance

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

**This graph:** `square album cover, graphic print, toll booth glow, chest-sub night, long exposure headlights, fictional act Drive-through, album Hour 2, no text, no letters, no logos, no living person likeness, no ...`

```text
square album cover, graphic print, toll booth glow, chest-sub night, long exposure headlights, fictional act Drive-through, album Hour 2, no text, no letters, no logos, no living person likeness, no celebrity, no photograph
```

#### `prompt`

Type `STRING`.

Lazy sentence or authored still prompt.

**How it affects generation:** When Enhance is on, the GGUF expands this into Klein-native sentences.

**This graph:** `A photoreal still of a tropical coastal city rooftop terrace at golden hour. An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread...`

```text
A photoreal still of a tropical coastal city rooftop terrace at golden hour. An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams stands mid-stride on the terrace. Warm gold-cyan holographic glyph rings bloom from a compact unmarked data-staff, empty of lettering. Instagram 1:1 square. Subject centered, warm key, unmarked surfaces.
```

#### `enhance`

Type `BOOLEAN`. Range / default: on for lazy printers.

Run the rewriter.

**How it affects generation:** Off = encode the widget as-is (plus style suffix if set).

**This graph:** `true`

#### `mode`

Type `COMBO`. Range / default: t2i / edit / identity / text_swap / background_swap / background_edit.

System prompt flavor.

**How it affects generation:** t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet). text_swap = glyph-lock lettering on a source still. background_swap = replace environment including ground. background_edit = restyle the environment in place.

**This graph:** `t2i`

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

Framing hint (YouTube 16:9 still, Instagram 4:5, ...).

**How it affects generation:** Steers aspect language in the rewrite. Does not set the latent size - EmptyFlux2LatentImage does.

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

**This graph:** `stills/instagram-square`

### `EZNegativePromptEnhance` - Negative Prompt Enhance

Rewrite a negative CLIP seed against the final positive. Stays on when Rewrite prompt is off.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `positive` | in | `STRING` | Final positive CLIP string (enhance output, Prompt Join, or shot bundle). |
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

Rewrite negative. App label: Rewrite negative.

**How it affects generation:** Stays on when Rewrite prompt is off. Off skips the LLM; the conflict filter still runs.

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

### `EZImageFormat` - Format / platform

Pick a Klein still canvas (aspect or named platform) and an optional Cinema Rack look recipe.

!!! warning "Lab notes"

    stills/still-studio wires width/height/batch into EmptyFlux2LatentImage, hint into Enhance duration_hint, prefix into SaveImage, and look splice into Enhance context. Quality does not change size. Match input snaps aspect to a loaded still.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Optional still used when Output size is Match input. |
| `width` | out | `INT` | Latent width (div16). |
| `height` | out | `INT` | Latent height (div16). |
| `batch` | out | `INT` | Batch size. |
| `hint` | out | `STRING` | Enhance duration / framing line. |
| `prefix` | out | `STRING` | SaveImage filename prefix. |
| `context` | out | `STRING` | Look-recipe splice for Enhance context. |

#### `format`

Type `COMBO`. Range / default: 16:9 LTX feeder / platform jobs / Custom.

Aspect or named platform job.

**How it affects generation:** Preset writes pixels, save prefix, and Rewrite prompt framing. Custom uses Width x Height (snapped to div16, max 2048). Does not change Quality, CLIP, or VAE.

**This graph:** `Instagram - square (1024x1024)`

**Other choices**

| Choice | What it does |
| --- | --- |
| `Custom` | Width x Height widgets, snapped to div16. |
| `16:9 draft (768x432)` | 768x432. aspect_16_9_draft. |
| `16:9 LTX feeder (1280x704)` | 1280x704. aspect_16_9_ltx. |
| `16:9 (1280x720)` | 1280x720. aspect_16_9. |
| `16:9 mid (1024x576)` | 1024x576. aspect_16_9_mid. |
| `1:1 square (1024x1024)` | 1024x1024. aspect_1_1. |
| `1:1 circle-safe (768x768)` | 768x768. aspect_1_1_circle. |
| `4:5 portrait (1024x1280)` | 1024x1280. aspect_4_5. |
| `9:16 draft (432x768)` | 432x768. aspect_9_16_draft. |
| `9:16 (576x1024)` | 576x1024. aspect_9_16. |
| `9:16 LTX feeder (768x1280)` | 768x1280. aspect_9_16_ltx. |
| `~1.91:1 landscape (1216x640)` | 1216x640. aspect_191. |
| `~3:1 banner (1536x512)` | 1536x512. aspect_3_1. |
| `4:1 banner (1536x384)` | 1536x384. aspect_4_1. |
| `2:3 pin (768x1152)` | 768x1152. aspect_2_3. |
| `3:4 panel (768x1024)` | 768x1024. aspect_3_4. |
| `YouTube - thumbnail (1280x720)` | 1280x720. youtube_thumb. |
| `YouTube - channel art (1536x864)` | 1536x864. youtube_channel_art. |
| `YouTube - channel icon (768x768)` | 768x768. youtube_channel_icon. |
| `YouTube - Shorts thumb (576x1024)` | 576x1024. youtube_shorts_thumb. |
| `YouTube - Community (1024x1024)` | 1024x1024. youtube_community. |
| `YouTube - chapter card (1280x720)` | 1280x720. youtube_chapter. |
| `YouTube - subscribe plate (1280x720)` | 1280x720. youtube_subscribe. |
| `YouTube - end screen (1280x720)` | 1280x720. youtube_endscreen. |
| `Instagram - square (1024x1024)` | 1024x1024. ig_square. |
| `Instagram - 4:5 portrait (1024x1280)` | 1024x1280. ig_portrait. |
| `Instagram - landscape (1216x640)` | 1216x640. ig_landscape. |
| `Instagram - Story (576x1024)` | 576x1024. ig_story. |
| `Instagram - Reel cover (576x1024)` | 576x1024. ig_reel. |
| `Instagram - Highlight (768x768)` | 768x768. ig_highlight. |
| `Instagram - profile (768x768)` | 768x768. ig_profile. |
| `TikTok - cover (576x1024)` | 576x1024. tt_cover. |
| `TikTok - Shop (1024x1024)` | 1024x1024. tt_shop. |
| `X - post (1280x720)` | 1280x720. x_post. |
| `X - header (1536x512)` | 1536x512. x_header. |
| `X - card (1216x640)` | 1216x640. x_card. |
| `LinkedIn - square (1024x1024)` | 1024x1024. li_post. |
| `LinkedIn - landscape (1216x640)` | 1216x640. li_landscape. |
| `LinkedIn - banner (1536x384)` | 1536x384. li_banner. |
| `LinkedIn - article (1216x640)` | 1216x640. li_article. |
| `Pinterest - pin (768x1152)` | 768x1152. pin. |
| `Pinterest - Idea Pin (576x1024)` | 576x1024. pin_story. |
| `Facebook - post (1216x640)` | 1216x640. fb_post. |
| `Threads - 4:5 (1024x1280)` | 1024x1280. threads. |
| `Twitch - offline (1280x720)` | 1280x720. twitch_offline. |
| `Twitch - starting soon (1280x720)` | 1280x720. twitch_starting. |
| `Twitch - BRB (1280x720)` | 1280x720. twitch_brb. |
| `Twitch - ending (1280x720)` | 1280x720. twitch_ending. |
| `Twitch - overlay (1280x720)` | 1280x720. twitch_overlay. |
| `Twitch - panel (768x1024)` | 768x1024. twitch_panel. |
| `Twitch - profile (768x768)` | 768x768. twitch_profile. |
| `Twitch - banner (1536x512)` | 1536x512. twitch_banner. |
| `Spotify - playlist (1024x1024)` | 1024x1024. spot_playlist. |
| `Spotify - Canvas still (576x1024)` | 576x1024. spot_canvas. |
| `Album - cover (1024x1024)` | 1024x1024. album_cover. |
| `Lyric card (1024x1024)` | 1024x1024. lyric_card. |
| `Audiogram - wide (1280x720)` | 1280x720. ag_wide. |
| `Audiogram - vertical (576x1024)` | 576x1024. ag_vert. |
| `Podcast - episode art (1024x1024)` | 1024x1024. episode_art. |
| `Podcast - cover (1024x1024)` | 1024x1024. podcast_cover. |
| `Open Graph / blog (1216x640)` | 1216x640. og. |
| `Email - header (1216x640)` | 1216x640. email_header. |
| `Substack - hero (1216x640)` | 1216x640. substack. |
| `Patreon - post (1024x1280)` | 1024x1280. patreon. |
| `Channel - banner (1536x512)` | 1536x512. banner. |
| `End-card / CTA (1280x720)` | 1280x720. endcard. |
| `Quote background (1024x1024)` | 1024x1024. quote_bg. |
| `Lower-third plate (1280x720)` | 1280x720. lower_third. |
| `Food / tabletop (1024x1280)` | 1024x1280. food_tabletop. |
| `Shorts still (432x768)` | 432x768. shorts_still. |
| `Hook still (432x768)` | 432x768. hook_still. |
| `Product packshot (1024x1024)` | 1024x1024. packshot. |
| `Product lifestyle (1024x1280)` | 1024x1280. lifestyle. |
| `Desk setup (1280x720)` | 1280x720. desk_setup. |
| `Coming soon (1280x720)` | 1280x720. coming_soon. |
| `Slide title (1280x720)` | 1280x720. slide_title. |
| `Zoom / Meet background (1280x720)` | 1280x720. zoom_bg. |
| `Merch - tee (1024x1024)` | 1024x1024. merch_tee. |
| `Merch - mug (1024x1024)` | 1024x1024. merch_mug. |
| `Print poster (768x1152)` | 768x1152. poster. |

#### `look`

Type `COMBO`. Range / default: none.

Optional Cinema Rack starter.

**How it affects generation:** none leaves look to Style + Prompt. A pick splices Klein still language into Enhance context. Full 13-axis desk is inspire/cinema-rack.

**This graph:** `none`

**Other choices**

| Choice | What it does |
| --- | --- |
| `none` | Off. Style + Prompt own look. |
| `Noir interrogation` | rec_noir_push |
| `Locked portrait` | rec_locked_portrait |
| `Golden wide` | rec_golden_wide |
| `Handheld documentary` | rec_handheld_doc |
| `Vertical hook` | rec_vertical_hook |
| `Rain track` | rec_rain_track |
| `Product orbit` | rec_orbit_product |
| `Drone reveal` | rec_drone_reveal |
| `Night bible` | rec_identity_night |
| `Western noon` | rec_western_noon |
| `Slow push to eyes` | rec_slow_push_eyes |
| `FPV dive` | rec_fpv_dive |
| `Match-cut AV` | rec_match_cut_ltx |
| `Fog push` | rec_fog_push |
| `Body-cam sprint` | rec_bodycam_sprint |
| `Bounce beauty` | rec_romcom_beauty |
| `Overcast wide` | rec_overcast_wide |
| `Macro pour` | rec_macro_pour |
| `Crane reveal` | rec_crane_reveal |
| `Split diopter two-plane` | rec_split_diopter |
| `Night practical push` | rec_night_practical_push |
| `Hyperlapse path` | rec_hyperlapse |
| `Talking MCU` | rec_talking_mcu |
| `Anamorphic-class night` | rec_anamorphic_night |

#### `width`

Type `INT`. Range / default: 16-2048, step 16.

Custom width.

**How it affects generation:** Used when Format is Custom. Presets ignore this widget at Queue.

**This graph:** `1024`

#### `height`

Type `INT`. Range / default: 16-2048, step 16.

Custom height.

**How it affects generation:** Used when Format is Custom. Presets ignore this widget at Queue.

**This graph:** `1024`

#### `batch_size`

Type `INT`. Range / default: 1-4.

How many stills in one Run.

**How it affects generation:** Large canvases stay at 1.

**This graph:** `1`

#### `size_mode`

Type `COMBO`. Range / default: Match input / Force format.

Match a loaded still's aspect, or keep Format / platform.

**How it affects generation:** Match input (default) picks the nearest aspect catalog row when a still is loaded. Force format keeps the Format pick. No still: authored format. Quality does not change size.

**This graph:** `Match input`

### `EZImageUpscale` - Upscale still

Optional lanczos upscale after a still decode. none passes the tensor through.

!!! warning "Lab notes"

    Wired before SaveImage on stills, creator stills, and DCC still plates. One App dropdown drives every output.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Decoded still. |
| `IMAGE` | out | `IMAGE` | Possibly upscaled still. |
| `upscale` | out | `STRING` | Combo id for additional EZImageUpscale nodes. |

#### `upscale`

Type `COMBO`. Range / default: none / 2x / 4x / 4K.

Upscale mode.

**How it affects generation:** none is a passthrough. 2x and 4x are lanczos. 4K fits the still in a 3840x2160 box (portrait 2160x3840). No extra weights.

**This graph:** `none`

**Other choices**

| Choice | What it does |
| --- | --- |
| `none` | Pass through. |
| `2x` | Double pixels. |
| `4x` | Quadruple pixels. |
| `4K` | Fit in a 4K box. |

### `EZImageDescribe` - Describe image

Caption a source still so Prompt Enhance can name inventory and lettering.

!!! warning "Lab notes"

    Off (default) returns empty and does not load the describe GGUF. Opt-in: download-llm --tier describe (Qwen2.5-VL-3B Apache).

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `image` | in | `IMAGE` | Source still. Lazy - skipped when enable is off. |
| `caption` | out | `STRING` | Short caption, or empty. |

#### `enable`

Type `BOOLEAN`. Range / default: off.

Run the captioner.

**How it affects generation:** Off skips the VLM. On needs download-llm --tier describe.

**This graph:** `false`
