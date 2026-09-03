---
title: 90s shorts
description: Build the three US-safe 90s shorts from one unified film graph per short (18 × 5.00s shots), then concat with a 90s cap.
tags: [shorts, wan, ltx, klein, youtube, comfyui]
---

# 90s shorts

**What's on this page**

- Why 18 × 5.00s shots instead of one 90s Queue
- One unified Comfy graph per film (Klein identity + LTX print + shot map)
- Shot maps for go-see (first-person running), still-here, and switchyard
- Operator loop: identity → unmute LTX → 18 prints → concat
- Model-native look / motion / audio prompts ([Prompting](prompting.md))
- Spark farm: parallel 5s Queues, local concat

**What this enables**

- Three continuous ~90s films (first-person running go-see, still-here, switchyard) on the **US-safe local pack**
- Last-frame continuity without a 90s denoise
- A 90.00s publish cap (`ffmpeg -t 90`)
- One workflow file per film — no switching between bible / wan-shot / ltx-shot graphs

!!! warning "Not legal advice"

    LTX-2.5 is the audio model and is **not Apache**. Community License: free commercial under **$10M COMPANY** annual revenue (affiliates count); disclose AI-generated media; do not strip provenance; do not distill. Wan 2.2 TI2V-5B is Apache 2.0 and silent. See [Model licenses](licenses.md).

---

## Why not one 90s graph

Default lab graphs iterate in **minutes**. A 90s (or 30–60s) denoise on GB10 is the wrong default.

Continuity is **last frame of shot N → LoadImage of shot N+1**. Each micro-shot is independent:

| | |
| --- | --- |
| Micro-shot | **120 frames @ 24 fps = 5.00 s** |
| LTX print size | **1280×704** (VAE ÷32; not 1280×720) |
| Klein identity | **1280×720** still OK; I2V center-crops ~16 px |
| Beats | **6** (same places as the old six-column films) |
| Micro-shots per beat | **3** (enter / traverse / exit) |
| Picture | **18 × 5.00 s = 90.00 s** |
| Publish | `concat-shots.sh --film … --yes` → ffmpeg **`-t 90`**; fail if probe `> 90` |

Do **not** Queue 90s, 241+ frames, or a single-graph film. If a latent widget errors on even length, you may set **121** (4n+1 / 8n+1) on that shot and still concat with the 90s cap.

```mermaid
flowchart LR
  Load["Load film-*-90s graph"] --> Id["Queue Identity Klein"]
  Id --> Unmute["Bypass Identity · enable LTX"]
  Unmute --> Shot["Queue LTX 5.00s AV ×18"]
  Shot --> Last["Save last frame"]
  Last --> Next["Next shot LoadImage"]
  Next --> Shot
  Shot --> Concat["concat-shots --film · cap 90s"]
```

---

## Models (US-safe local pack only)

| Job | Where | Model | License |
| --- | --- | --- | --- |
| Identity still | Same file: group **1. Identity (Klein)** | Klein 4B distilled FP8 | Apache 2.0 |
| Print + synced world audio | Same file: group **2. Shot print (LTX)** | LTX-2.5 distilled I2V | Community License (not Apache) |
| Optional silent rehearsal | `workflows/wan-i2v-shot-lab-example.json` | Wan 2.2 TI2V-5B I2V | Apache 2.0, silent |

Unified film files:

- `workflows/shorts/film-go-see-90s-run-lab-example.json`
- `workflows/shorts/film-still-here-90s-lab-example.json`
- `workflows/shorts/film-switchyard-90s-lab-example.json`

Deliverable MP4s are **LTX I2V heroes** (breath, world objects, **no score**) with audio muxed via `LTXVAudioVAEDecode` → `VHS_VideoCombine`. Wan is an optional cheap motion draft — skip it if you already like the camera.

LTX-2.5 native multishot (several cuts in one 5–10s clip) is an optional experiment **inside** a beat, not the 90s path.

---

## Operator loop

Each film graph ships **Klein identity + LTX 5.00s printer + full shot map (Motion + Audio)** in one file. The container entrypoint copies `*.json` and `shorts/*.json` into Comfy `user/default/workflows/`.

1. Load one film graph (`film-go-see-90s-run-lab-example` / `film-still-here-90s-lab-example` / `film-switchyard-90s-lab-example`).
2. Leave **Shot print (LTX)** bypassed (default). Queue **Identity (Klein)** → `ez_<slug>_identity_*.png`.
3. Ctrl+B: bypass Identity; enable Shot print. Set LoadImage to the identity PNG (shot 1) or the previous `ez_<slug>_bN_sM_last`.
4. Paste **Motion + Audio** from the on-canvas shot map (source of truth also in `{film}.shots.yaml`). Set VHS prefix `ez_<slug>_bN_sM_ltx_video` and last-frame SaveImage `ez_<slug>_bN_sM_last`. Leave LTX **1280×704** (do not type 720). Queue **5.00s** AV.
5. After Queue, click **Save video (MP4) — open node for preview** for an inline preview. File: `${COMFY_OUTPUT_DIR}/ez_<slug>_bN_sM_ltx_video_*.mp4`.
6. Repeat for all 18 shots. Optional silent rehearsal: open **wan-i2v-shot-lab-example** with the same first frame.
7. Concat (dry-run first; `--yes` writes the cap). Default dir is `${COMFY_OUTPUT_DIR}`:

```bash
FILM=go-see   # or still-here | switchyard
./scripts/utilities/concat-shots.sh --film "${FILM}" --dry-run
./scripts/utilities/concat-shots.sh --film "${FILM}" --yes
```

Publish names under `${COMFY_OUTPUT_DIR}` (default `/mnt/comfy-output`): `ez_gosee_90s.mp4`, `ez_stillhere_90s.mp4`, `ez_switchyard_90s.mp4`.

YouTube: disclose AI-generated media (LTX term). Do not strip provenance.

---

## Shot maps

First-person **go-see** is **camera language**, not licensed IP. Same SFW / no unlicensed marks / no real likenesses as the rest of the stack.

=== "go-see"

    First-person **running**. Identity lock: olive windbreaker + worn black gloves in frame. Footfalls and arms, not parkour. **No score** (breath + world).

    | Beat | Place | s1 enter | s2 traverse | s3 exit |
    | --- | --- | --- | --- | --- |
    | 1 | Dawn rooftop | Run on wet tar, gloves pumping | Run across the next roof | Run onto warehouse roof |
    | 2 | Warehouse → market | Run down the stair | Run the alley, duck awning | Run out toward river |
    | 3 | River / forest | Run across stones | Run through bridge arch | Run the creek path |
    | 4 | Headland | Trees thin, keep running | Run past boulder | Run toward generic lighthouse |
    | 5 | Wall / meadow | Run up granite steps | Run through dry-stone gap | Run into meadow |
    | 6 | Ridge hold | Slow; hands on wooden rail | Look | Quiet laugh, hold |

=== "still-here"

    Third-person household morning. Identity lock: plain ceramic mug. Invented two-note child-hum (no real-child first frame, no licensed music).

    | Beat | Place | Notes |
    | --- | --- | --- |
    | 1 | Kitchen, first light | Kettle, pour, mug, hum off-screen |
    | 2 | Table | Steam, hum closer, doorway |
    | 3 | Hands on mug | Motif answers, house creak |
    | 4 | Living room | Sun bar, silhouette in the next doorway |
    | 5 | Doorway | Silhouette only — no close-up identity |
    | 6 | Table hold | Empty chair, last hummed note, house quiet |

=== "switchyard"

    Night freight yard. Identity lock: rain, ballast, generic unmarked boxcars, yard lamp. No railroad company marks.

    | Beat | Place | Notes |
    | --- | --- | --- |
    | 1 | Gravel walk | Rain, lamps, stop between first unmarked cars |
    | 2 | Between cars | Gloves on a rusty ladder rail, coupling clank |
    | 3 | Ladder | Climb in the rain, roof edge |
    | 4 | Roof walk | Distant generic horn — not a real carrier identity |
    | 5 | Drop to gravel | Window glow, no readable sign |
    | 6 | Lamp hold | Look down the dark string of cars, quiet laugh |

Prefixes: `ez_gosee_b{1..6}_s{1..3}`, `ez_stillhere_…`, `ez_switchyard_…`. Machine-readable lists: `workflows/shorts/*.shots.yaml`.

---

## Spark farm

Three Sparks can Queue **different beats** in parallel (independent 5s jobs, shared `${MODELS_DIR}`). On each UI load the same **film-*-90s** graph (or **ltx-i2v-shot-lab-example** for a generic printer) and Queue; concat stays on one host. `spark-farm.sh run --film go-see` prints that Queue reminder (it does not POST graphs). No NCCL. See [Spark farm](spark-farm.md).

---

## Safety

Unchanged: `restart: "no"`, heavy confirm on `start`, headroom preflight, download-limit wrap. This path does not start Docker; it only stitches files already under `COMFY_OUTPUT_DIR`.
