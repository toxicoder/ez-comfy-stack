---
title: DCC guide pack
description: Block in Blender, dump a 1280×704 clay/depth pack, Klein-look the first frame, print a depth-guided LTX 5.00s hero.
tags: [dcc, blender, guide-pack, klein, ltx, occupancy, ic-lora]
---

# DCC guide pack

**What's on this page**

- The DCC ↔ Comfy **print** handshake (`guides/<slug>/<shot>/`)
- Single-frame still packs (`guides/<slug>/stills/<plate>/`)
- Occupancy: stop Comfy before a dump
- Instagram clay stills are a different pack (`house-views`, 1024×1280)
- Script desk, overlay QC, animatic, stem mix
- Klein-from-clay / plates / canny Apps
- Opt-in LTX IC-LoRA Union Control (depth, canny, shorts) and Wan FLF from the pack
- Path A / B / D

**What this enables**

- A 5.00s LTX print that keeps the camera you blocked
- Creator stills (hero, packshot, IG, shorts) from one clay plate
- Fail-closed packs (1280×704 or 768×1280, 120 frames @ 24 fps) before Comfy sees them
- Laptop DCC / Spark Comfy as the default on one GB10

This extends `ez_film`. It does **not** replace the 5.00s printer or the sidecar occupancy rule. Blender stays on the host — never in `docker/Dockerfile` or Compose.

!!! danger "Stop Comfy first"

    Pack writing is a host GPU job. `export-guides` **dies** (exit 2) if compose is up. Same XOR as `manage.sh blender`. `restart: "no"` is unchanged.

---

## Operator loop (Path B)

```bash
./scripts/manage.sh stop
./scripts/manage.sh export-guides --engine blender --film go-see --shot 12 --blend /path/to/shot.blend --print ltx-iclora-depth
./scripts/manage.sh start          # type yes
# Queue workflows/_lab/dcc/klein-from-clay-lab-example.json on first.png
./scripts/manage.sh overlay-qc --film go-see --shot 12 --look /path/to/ez_clay_hero.png
# After download-ltx --tier iclora: Templates → LTX-2.5 Union Control, depth from depth.mp4
# Stop LTX. Stem mix (occupancy audio):
./scripts/manage.sh stem-mix --film go-see --shot 12 --bg /path/to/print.mp4
```

Cheap pacing gate (host ffmpeg; compose may stay up):

```bash
./scripts/manage.sh film-animatic --film go-see
```

Script desk writes `films/<slug>/shots.yaml` (does not clobber lab YAML):

```bash
./scripts/manage.sh shot-sheet run --film go-see
```

Default on one GB10 is **Path D**: block and MCP on the laptop, rsync `guides/` to the Spark, Spark only runs Comfy.

```bash
rsync -a guides/go-see/12/ spark-0:/mnt/comfy-output/guides/go-see/12/
./scripts/manage.sh start
```

## Pack contract

`${COMFY_OUTPUT_DIR}/guides/<slug>/<shot_id>/`

| File | Rule |
| --- | --- |
| `shot.yaml` | `ez.guide.shot.v1` — 120 frames, 24 fps, **1280×704** or **768×1280** |
| `first.png` / `last.png` | Exact LTX VAE grid. Never 1280×720 |
| `rgb/` + `clay.mp4` | Workbench / unshaded clay. Not Cycles beauty |
| `depth/` + `depth.mp4` | Mist 0–1, near=white / far=black. Raw metric Z is a QC fail |
| `canny/` + `canny.mp4` | Workbench outline / Freestyle line-art (always dumped) |
| `normal/` | Optional EEVEE Normal (`--include-normal`); omitted when EEVEE is missing |
| `camera.json` | Per-frame extrinsics (`pos` / `rot` / `fov`) |

QC is fail-closed: wrong size, wrong frame count, or compose-up → non-zero, pack not marked ok.

Clay is Workbench. **Beauty MP4 is Path A only** (engine-final ingest in a later PR).

## Still packs (not 120 frames)

`${COMFY_OUTPUT_DIR}/guides/<slug>/stills/<plate>/` — `ez.guide.still.v1`. Allowed sizes: 1280×704, 768×1280, 1024×1280, 1024×1024, 1280×720 (thumb, Klein only).

```bash
./scripts/manage.sh stop
./scripts/manage.sh blender-stills --film go-see --plate mug --blend /path/to/prop.blend --size 1024x1024
./scripts/manage.sh start
# Queue klein-from-clay-plates or klein-from-canny
```

`--install-inputs` copies `first.png` into `${COMFY_OUTPUT_DIR}/input` (compose may stay up). Playbook: [Blender creator suite](learn/blender-creator.md).

## Graphs

| Graph | Occupancy | Notes |
| --- | --- | --- |
| **beat-sheet-lab-example** | none | Script desk. Logline, audio policy, 18 cards. `shot-sheet` writes YAML. |
| **klein-from-clay-lab-example** | klein | Edit `first.png`, Enhance **on**, seed **42**, 1280×704. Overlay-qc after Queue. |
| **klein-from-clay-plates-lab-example** | klein | One clay still → hero / packshot / IG / shorts. Ctrl+B unused groups. |
| **klein-from-canny-lab-example** | klein | Edit `canny.png`, 1280×704, prefix `ez_canny_hero`. |
| **ltx-iclora-depth-5s-lab-example** | ltx | Envelope. Templates → LTX-2.5 Union Control. Depth default. Distilled-only. Refuse 19B. MagCache off. |
| **ltx-iclora-canny-5s-lab-example** | ltx | Same envelope; wire `canny.mp4`. |
| **ltx-iclora-depth-shorts-lab-example** | ltx | Same envelope at **768×1280**. Dump with `--width 768 --height 1280`. |
| **wan-flf-from-guide-lab-example** | wan | Fun InP `first.png` + `last.png`. Opt-in `download-wan --tier fun-inp`. MagCache off. |
| **audio-finish-lab-example** | audio | Stem mix desk. Host `stem-mix.sh`. ACE-Step group stays off. |

Print modes `wan-vace`, `wan-denk-cn`, and `dcc-final` stay valid on `shot.yaml` but are **not** lab printers in this suite (VACE stays 17-frame join; Fun Control / Path A beauty are later).

```bash
./scripts/manage.sh download-ltx --tier iclora   # not download-models
```

Official 2.5 Union Control distilled widgets `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors` onto the **distilled** transformer. Distilled-only. **Refuse 19B Union.** MagCache off.

## Paths

| Path | Meaning |
| --- | --- |
| **A** Engine-final | DCC beauty MP4 → jobstore later (`dcc-final`). No AI video. |
| **B** Hybrid clay → AI finish | DCC owns layout/camera/timing. AI owns materials/faces/light. **This PR.** |
| **D** Laptop-DCC / Spark-Comfy | Default ergonomics on one GB10. |

Godot is a first-class blocking engine in a later PR, not a second Blender. OpenToonz / Krita are plate emitters into the same pack, not v1 engines.

## Instagram clay stills (not this pack)

`house-views` is a **different** contract: ten 1024×1280 Workbench stills + greybox GLB under `assets/sets/<slug>/`, then **klein-dream-house-clay-lab-example**. Do not dump Instagram 4:5 into `guides/` or reuse `ez.guide.shot.v1` (that QC is 1280×704 / 120 frames). Playbook: [Dream-house tours](learn/dream-house.md).

```bash
./scripts/manage.sh stop
./scripts/manage.sh house-views --slug lab-penthouse
```

Do not run a live Blender MCP socket and Comfy on the same GB10.

## Safety

- Do not weaken `restart: "no"`, heavy confirm, `mem_limit: 90g`, `min_host_free_gib: 28`, or download-limit clear-on-exit.
- Never queue a DCC dump and a print in one session.
- Unload Klein before LTX. IC-LoRA is not part of `download-models`.
- `overlay-qc` / `film-animatic` / `stem-mix` do not start Docker and do not weaken occupancy XOR for dumps.

Related: [Blender creator suite](learn/blender-creator.md), [Clay to finish](learn/clay-to-finish.md), [Blender GB10 sidecar](blender-gb10-sidecar.md), [Studio sidecars](studio-sidecars.md), [90s shorts](shorts.md), [Model licenses](licenses.md).
