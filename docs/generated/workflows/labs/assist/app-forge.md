---
title: "labs/assist/app-forge"
description: "No-UNET App Forge: clone a lab graph into live _user/"
tags: [workflows, generated, comfyui, labs]
---

# labs/assist/app-forge

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `labs/assist/app-forge` from Apps or Workflows.

> Generated from `workflows/_lab/labs/assist/app-forge.json`. Do not hand-edit this file. Re-run `bazelisk run //docs:docs`.

## Purpose

Occupancy **llm**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## labs/assist/app-forge

App Forge - clone a shipped lab graph into live `_user/` as a new App.
No UNET, no VAE, no KSampler. Does not Queue the result.

Occupancy: llm - graph label (not a CLI mode). Prefer GPU 35B:

  bazelisk run //:manage -- occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down, then a keyword
heuristic if the GGUF is missing. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Brief** (or pick a sample). Leave **Template** on auto, or pin
   a lab id such as photos/instagram-square.
2. Set **Slug** (lowercase, hyphen). **As app** on writes `*.app.json`.
3. Queue. Read **Path**, **Picked template**, and **Result occupancy**.
4. Open `_user/<slug>` from the Apps sidebar. Queue that graph when GB10
   occupancy matches the result (klein / wan / ltx / ...).

Laptop agents: `bazelisk run //:manage -- studio-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
Does not write `workflows/_lab/`. Keepers: `promote-workflow`.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.

Handoff: labs/assist/prompt-forge, photos/still-draft. Load that graph next - the output is its input.
```

## How to Queue

1. `bazelisk run //:manage -- start` so `_lab` is seeded
2. Load **labs/assist/app-forge** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart LR
  N1["Operator note"]
  N2["App Forge"]
  N4["Check models"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Operator note | `Note` | NOTE |
| 2 | App Forge | `EZAppForge` | FORGE |
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

**This graph:** `## labs/assist/app-forge App Forge - clone a shipped lab graph into live `_user/` as a new App. No UNET, no VAE, no KSampler. Does not Queue the result. Occupancy: llm - graph label (not a CLI mode)....`

```text
## labs/assist/app-forge

App Forge - clone a shipped lab graph into live `_user/` as a new App.
No UNET, no VAE, no KSampler. Does not Queue the result.

Occupancy: llm - graph label (not a CLI mode). Prefer GPU 35B:

  bazelisk run //:manage -- occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down, then a keyword
heuristic if the GGUF is missing. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a **Brief** (or pick a sample). Leave **Template** on auto, or pin
   a lab id such as photos/instagram-square.
2. Set **Slug** (lowercase, hyphen). **As app** on writes `*.app.json`.
3. Queue. Read **Path**, **Picked template**, and **Result occupancy**.
4. Open `_user/<slug>` from the Apps sidebar. Queue that graph when GB10
   occupancy matches the result (klein / wan / ltx / ...).

Laptop agents: `bazelisk run //:manage -- studio-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
Does not write `workflows/_lab/`. Keepers: `promote-workflow`.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown.

Handoff: labs/assist/prompt-forge, photos/still-draft. Load that graph next - the output is its input.
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

**How it affects generation:** auto uses the GGUF planner or a keyword heuristic. Pin photos/instagram-square to skip.

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

**This graph:** `labs/assist/app-forge`

### `EZModelCheck` - Check models

Manual disk check for occupancy + Detail weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph:** `Click Check models. Queue does not run this node.`
