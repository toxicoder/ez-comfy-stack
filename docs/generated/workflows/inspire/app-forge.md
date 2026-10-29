---
title: "inspire/app-forge"
description: "No-UNET App Forge: clone a lab graph into live _user/"
tags: [workflows, generated, comfyui, inspire]
---

# inspire/app-forge

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `inspire/app-forge` from Apps or Workflows.

> Generated from `workflows/_lab/inspire/app-forge.json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).

## Purpose

Occupancy **llm**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## inspire/app-forge

App Forge - clone a shipped lab graph into live `_user/` as a new App.
No UNET, no VAE, no KSampler. Does not Queue the result.

Occupancy: llm - graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down, then a keyword
heuristic if the GGUF is missing. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Brief** (or pick a sample). Leave **Template** on auto, or pin
   a lab id such as stills/instagram-square.
2. Set **Slug** (lowercase, hyphen). **As app** on writes `*.app.json`.
3. Queue. Read **Path**, **Picked template**, and **Result occupancy**.
4. Open `_user/<slug>` from the Apps sidebar. Queue that graph when GB10
   occupancy matches the result (klein / wan / ltx / ...).

Laptop agents: `./scripts/manage.sh studio-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
Does not write `workflows/_lab/`. Keepers: `promote-workflow`.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

## How to Queue

1. `./scripts/manage.sh start` so `_lab` is seeded
2. Load **inspire/app-forge** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart LR
  N1["Operator note"]
  N2["App Forge"]
  N3["Quality"]
  N4["Check models"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Operator note | `Note` | NOTE |
| 2 | App Forge | `EZAppForge` | FORGE |
| 3 | Quality | `EZQuality` | QUALITY |
| 4 | Check models | `EZModelCheck` | QUALITY |

## Node parameter reference

Every unique node type on this graph. Widgets are in lab JSON order. Choices are ComfyUI v0.43.0 / lab `INPUT_TYPES` - not SD1.5 folklore.

### `Note` - Note

On-canvas operator note (not executed).

!!! warning "Lab notes"

    Every lab graph has one. Purpose, models, sampler, occupancy, run steps.

#### `text`

Type `STRING`.

Markdown-ish operator note.

**How it affects generation:** Does not affect pixels. Read it before Queue.

**This graph:** `## inspire/app-forge App Forge - clone a shipped lab graph into live `_user/` as a new App. No UNET, no VAE, no KSampler. Does not Queue the result. Occupancy: llm - graph label (not a CLI mode). Pre...`

```text
## inspire/app-forge

App Forge - clone a shipped lab graph into live `_user/` as a new App.
No UNET, no VAE, no KSampler. Does not Queue the result.

Occupancy: llm - graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down, then a keyword
heuristic if the GGUF is missing. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Brief** (or pick a sample). Leave **Template** on auto, or pin
   a lab id such as stills/instagram-square.
2. Set **Slug** (lowercase, hyphen). **As app** on writes `*.app.json`.
3. Queue. Read **Path**, **Picked template**, and **Result occupancy**.
4. Open `_user/<slug>` from the Apps sidebar. Queue that graph when GB10
   occupancy matches the result (klein / wan / ltx / ...).

Laptop agents: `./scripts/manage.sh studio-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
Does not write `workflows/_lab/`. Keepers: `promote-workflow`.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.
```

### `EZAppForge` - App Forge

Clone a shipped lab graph into live _user/ as a new App. No UNET.

!!! warning "Lab notes"

    Occupancy llm. Does not Queue the result. Does not write _lab. Keyword heuristic if GGUF is missing. Path D: studio-mcp. Not Comfy Cloud MCP.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `path` | out | `STRING` | Written _user path or error. |

#### `sample`

Type `COMBO`. Range / default: custom.

Sample brief or Custom.

**How it affects generation:** Custom uses the Brief box.

**This graph:** `custom`

#### `prompt`

Type `STRING`.

Brief.

**How it affects generation:** What the new App should make. Template auto picks a lab graph.

**This graph:** `1:1 IG still of a chipped cobalt mug on pale stone, unmarked surfaces.`

#### `template`

Type `COMBO`. Range / default: auto.

Lab graph to clone.

**How it affects generation:** auto uses the GGUF planner or a keyword heuristic. Pin stills/instagram-square to skip.

**This graph:** `auto`

#### `slug`

Type `STRING`.

Filename stem.

**How it affects generation:** Live _user/<slug>.app.json. Lowercase letters, digits, hyphen.

**This graph:** `mug-ig`

#### `as_app`

Type `BOOLEAN`. Range / default: true.

Write an App.

**How it affects generation:** true writes *.app.json for the Apps sidebar.

**This graph:** `true`

#### `overwrite`

Type `BOOLEAN`. Range / default: false.

Replace existing.

**How it affects generation:** false refuses an existing _user file.

**This graph:** `false`

#### `catalog`

Type `STRING`.

Catalog id.

**How it affects generation:** Leave as stamped.

**This graph:** `inspire/app-forge`

### `EZQuality` - Quality

Workflow-global quality combo. JS overlays family-specific sampler, UNET, CLIP, and VAE widgets.

!!! warning "Lab notes"

    Workflow-global quality combo. presets.py is the only tier definition and the frontend reads a table generated from it. The combo is DERIVED from the widgets, not typed: it names the tier whose owned parameters the widgets actually hold, lab when they match the load-time authored values, custom otherwise, and it re-derives on load, graph change, widget edit, and Queue. custom is not absorbing - putting the owned widgets back on a tier's values re-derives that tier. A tier value that cannot be written (weight not installed, widget not built) is a FAILED apply: the combo drops to custom and the caption names what diverged. Writes resolve per node instance, so every sampler and loader in a graph is written. Only parameters the family's tiers own are compared, so a CFG edit on a steps-only family keeps the level. A combo whose node mode is nonzero is ignored. Never --tier quality.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `quality` | out | `STRING` | Selected quality id. |

#### `quality`

Type `COMBO`. Range / default: lab.

Derived from the widgets: the named tier they match, lab for the authored values, custom otherwise.

**How it affects generation:** Named qualities may swap UNET, CLIP, and VAE, per node instance. A tier value that cannot be written is a failed apply, so the combo drops to custom rather than claiming a swap the prompt does not contain. Quality does not touch the Width / Height or Duration widgets; the one size effect is Free Commercial Use (<$10M) on Klein stills, where a generic 16:9 / 9:16 Format row retargets to the LTX feeder size (1280x704 / 768x1280). On Klein, high and Free Commercial Use (<$10M) are the same profile (Apache Klein 4B base, 24 steps, CFG 3.5 - never 9B / FLUX.2-dev) and ultra/max swap in Klein 9B or FLUX.2-dev when those files are on disk (FLUX Non-Commercial, not YouTube-ok); ultra/max are no-ops on audio and trellis. Wan / LTX / film / audio / trellis tiers set steps only, never CFG or weights. flux3-* need the gated FLUX 3 pull (download-image --tier flux3 / flux3-base / flux3-nvfp4) and are the only tiers that write on a graph pinning FLUX 3 Klein weights.

**This graph:** `lab`

**Other choices**

| Choice | What it does |
| --- | --- |
| `custom` | Widgets match no tier, so they queue as they are. No overlay. |
| `draft` | Faster Apache Klein 4B (NVFP4 if on disk). |
| `lab` | Authored lab widgets. Default. |
| `standard` | Distilled 4B, 8 steps, CFG 1.0. |
| `high` | Klein base 4B + CFG 3.5 when on disk; else extra distilled steps at CFG 1.0. |
| `Free Commercial Use (<$10M)` | Klein 4B stills (never 9B / FLUX.2-dev) + LTX-2.5 steps. Optional SeedVR2 polish on the PNG, not 4K. Wan / audio / trellis are no-ops. |
| `ultra` | Klein 9B distilled when on disk (FLUX Non-Commercial). Else high. |
| `max` | Klein 9B base or FLUX.2-dev when on disk (FLUX Non-Commercial). Else high. |
| `flux3-fast` | FLUX 3 Image Klein distilled INT8 (flux3-image-klein-int8-convrot.safetensors), 16 steps, CFG 1.0. Gated FLUX Kommunity; writes only on a FLUX 3 graph. |
| `flux3-quality` | FLUX 3 Image Klein base INT8 (flux3-image-klein-base-int8-convrot.safetensors), 50 steps, CFG 3.5. Gated FLUX Kommunity; writes only on a FLUX 3 graph. |
| `flux3-nvfp4` | FLUX 3 Image Klein base NVFP4 (flux3-image-klein-base-nvfp4.safetensors), 50 steps, CFG 3.5. Gated FLUX Kommunity; writes only on a FLUX 3 graph. |

### `EZModelCheck` - Check models

Manual disk check for occupancy + Quality weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph:** `Click Check models. Queue does not run this node.`
