---
title: Audio Rack
description: Pick one audio or music technique per axis and splice it into ACE-Step tags and lyrics form.
tags: [audio, music, prompting, ace-step, inspire]
---

# Audio Rack

Use this page when the track is right but the tag list is not: it turns music
grammar into thirteen dropdowns and hands you ACE-Step tags plus a lyrics form.
It is deterministic - no LLM. For the ACE rewriter that uses the same catalog
language, see [Prompting](../prompting.md); for the camera equivalent,
[Cinema Rack](cinema-rack.md).

**What's on this page**

- **Axes** - the thirteen widgets and what each one does on an instrumental or a podcast bed
- **Flavors** - what the rack emits per family, plus recipe fill and conflict order
- **Drive-through recipes** - the shipped bass-set starters and their mix locks
- **Handoff** - where to paste the tags and lyrics it writes
- **Related** - what to load next

**What this enables**

- **Building a professional ACE-Step prompt** from dropdowns instead of remembering tag grammar
- **Copying tags and lyrics form** into **audio/music/rap-draft**, **audio/music/rap-full**, or a podcast bed
- **Starting a Drive-through take** from a shipped recipe instead of a blank tag box
- **Keeping one BPM token** so the encoder widget and the tags cannot disagree

**Who this is for:** studio users after Prompt Forge / Cinema Rack. Occupancy **llm**. No UNET. Do not load ACE-Step on this canvas.

Load **inspire/audio-rack**. Optional **Brief**, pick techniques, Queue, then read the vocal and instrumental Enhance boxes.

```mermaid
flowchart LR
  B["Brief"] --> R["Audio Rack"]
  A["13 axes - one pick each"] --> R
  Rec["Recipe fills empty axes"] --> R
  R --> T["ACE tags"]
  R --> L["Lyrics form"]
```

## Axes

Pick **none** or one id per axis. Splicing is across axes, not two tempos on one take.

| Widget | Axis | Instrumental / podcast |
| --- | --- | --- |
| Genre | Genre | kept |
| Tempo | Tempo and Groove | kept; notes emit BPM |
| Drums | Drums and Rhythm | kept |
| Bass | Bass and Low End | kept |
| Harmony | Harmony and Mode | kept (tags only; does not set ACE keyscale) |
| Instruments | Instruments and Texture | kept |
| Vocal | Vocal Identity | omitted |
| Form | Form and Arrangement | Timed ACE skeletons (`[pre-chorus]`, `[bridge]`, `[breakdown]`, `[build-up]`), not color pockets |
| Mix | Mix and Production | kept |
| Space | Space and Ambience | kept |
| Sound design | Sound Design | drop-first FX may be dropped on podcast |
| Mood | Mood and Energy | kept |
| Use | Use Case | kept |

Catalog encyclopedia (generated, do not hand-edit): [Audio technique catalogs](../generated/audio/index.md).

ACE tag order is encoder grammar, not widget order: genre -> mood -> drums -> bass -> instruments -> harmony -> vocal -> mix -> space -> design -> use -> BPM last. Form writes lyrics only.

## Flavors

| Family | What the rack emits |
| --- | --- |
| `ace_vocal` | Genre-first tags including vocal identity. Lyrics = brief (if any) + form skeleton. |
| `ace_instrumental` | Vocal axis dropped. Tags force `instrumental, no vocals`. Form uses `[inst]` / `[drop]`. Brief omitted. |
| `podcast_bed` | Same as instrumental, plus techniques that are not `podcast_ok` are dropped. |

A **Recipe** fills axes that are still `none`. An explicit dropdown always wins.

When two picks conflict, the **later splice-order** axis wins. Notes on the rack list what was dropped.

The rack emits at most one BPM token. Match `TextEncodeAceStepAudio1.5` BPM to that note. Do not also type a second BPM in the brief.

## Drive-through recipes

Shipped Drive-through takes under `_lab/audio/albums/drive-through/` splice these starters. The arranger then snaps tempo onto 165-176 and replaces the form with a per-take run of movements dealt from eight archetypes, each a sequence of 2-bar stanzas (180-480 s total, 3-5 ACE-Step passes, each cell under 3 seconds). Bass identity stays with the recipe:

| Recipe | Genre |
| --- | --- |
| `rec_drive_through_drop` | Hybrid trap |
| `rec_drive_riddim` | Riddim bass |
| `rec_drive_tearout` | Tearout |
| `rec_drive_brostep` | Brostep |
| `rec_drive_wave` | Wave bass |
| `rec_drive_color` | Color bass |
| `rec_drive_dirty` | Dirty bass |
| `rec_drive_dirty_dubstep` | Dirty dubstep |
| `rec_drive_drumstep` | Drumstep |
| `rec_drive_neuro` | Neuro bass |
| `rec_drive_chest` | Chest bass |
| `rec_drive_festival_trap` | Festival trap |
| `rec_drive_dj_shout` | Hybrid trap + `voc_dj_shout` |

Instrumental takes use `mix_drive_lock` (808, original composition, heavy chest bass, bass boosted, wide low-mid layers, fast switch-ups, deep 3D spatial low-mid, stacked 808 layers, electric warp texture, wavy FM layers). The DJ-shout lane keeps `mix_drive_treat` with the same chest-bass lock for manual recipes. Drive recipes leave the sound-design axis empty so a noise riser is not a whole-clip tag. Color bass tags stay `low-mid bass`, not formant. Do not pick `ins_warped_saw` on a Drive-through graph (supersaw is a high-pitch needle). Playbook: [Drive-through EDM lane](music-edm.md).

## Handoff

1. Queue **inspire/audio-rack** (occupancy **llm**).
2. Copy the tags / lyrics boxes.
3. Paste into **audio/music/rap-draft** (or a Drive-through / podcast bed graph). Set Family to `ace_instrumental` / `podcast_bed` first if you want those filters already applied.
4. Optional: turn Enhance **off** on the destination if the rack string is already ACE-native.

Do **not** co-resident ACE-Step with Klein / Wan / LTX. The rack canvas is occupancy **llm** so you can splice without loading the AIO.

Safety impact: none. Prompt JSON + CPU node. No Docker, restart, or headroom change.

---

## Related

1. Queue the tags you just spliced: [Audio graphs](workflows-audio.md)
2. Run the rap lane: [RAP-FIRST rap lane](music-rap.md)
3. Run the EDM lane: [Drive-through EDM lane](music-edm.md)
4. How the ACE rewriter uses the same catalog language: [Prompting](../prompting.md)
5. Splice the camera instead of the mix: [Cinema Rack](cinema-rack.md)
