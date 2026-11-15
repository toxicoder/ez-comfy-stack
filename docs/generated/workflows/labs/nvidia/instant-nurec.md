---
title: "labs/nvidia/instant-nurec"
description: "Instant NuRec (deferred) - Reconstructs a simulatable multi-camera driving world in one feed-forward pass, no per-scene training. NVIDIA lab card: preflight,"
tags: [workflows, generated, comfyui, labs]
---

# labs/nvidia/instant-nurec

**What's on this page**

- **Purpose, occupancy, and models** from the on-canvas Note
- **Graph flow** (groups when the canvas is large)
- **Every node id** on this graph
- **Node parameter reference** for each type, with this graph's values and the other legal choices

**What this enables**

- **Queuing this filename** with known widgets
- **Changing a parameter** with a documented generation effect

**Who this is for:** studio users who loaded `labs/nvidia/instant-nurec` from Apps or Workflows.

> Generated from `workflows/_lab/labs/nvidia/instant-nurec.json`. Do not hand-edit this file. Re-run `bazelisk run //docs:docs`.

## Purpose

Occupancy **none**. Outputs under `${COMFY_OUTPUT_DIR}`. Unload the previous family before Queue.

```text
## labs/nvidia/instant-nurec

Instant NuRec - Reconstructs a simulatable multi-camera driving world in one feed-forward pass, no per-scene training.

Status: deferred. Install: git-clone. Artifact: source-build. Arm64: unknown. GB10: unverified. Comfy shape: host-cli.
Input: multi-camera driving log
Output: a Gaussian scene with static and dynamic layers plus a sky cubemap
Licenses: code Apache-2.0. Weights not stated in the README. Commercial use unknown.
Footprint: 24 GB VRAM, 40 GB disk. Weights: nvidia/instant-nurec/instant_nurec.pt@0.84.
Artifact ref: https://github.com/NVIDIA/instant-nurec.git
Upstream: https://github.com/NVIDIA/instant-nurec
Also: https://huggingface.co/nvidia/instant-nurec
Sources: https://github.com/NVIDIA/instant-nurec

Nothing in this graph touches the GPU. The row's work runs outside the Comfy process through the operator CLI, so the App claims no occupancy and stops no heavy job: the one-heavy-job rule is the CLI's to enforce, next to the heavy confirm and the headroom preflight.

Operator verbs (host shell):
  bazelisk run //:manage -- nvidia-lab status
  bazelisk run //:manage -- nvidia-lab plan instant-nurec

Canvas:
1. Preflight prints whether this Spark could run the row today - the catalog row, an aarch64 host, the binary that row's install kind needs, and the artifact ref.
2. The verdict card prints the blocking reason and the sentence that would reopen the row.
3. The tier table prints all 18 rows with their status and licenses.

Gate notes: Feed-forward reconstruction is the right shape for a single GPU, but the weights license is not stated in the repository and the uv lockfile pins are the aarch64 risk. Its input domain is driving logs, which no lane in this stack produces.
Reopen: Re-test when the model card states a weight license that permits product use and a linux_aarch64 dependency set resolves.
Verify: bazelisk test //tests:bats_nvidia_lab_test

Occupancy: none - stop nothing GPU. One GB10 job.
```

## How to Queue

1. `bazelisk run //:manage -- start` so `_lab` is seeded
2. Load **labs/nvidia/instant-nurec** from **Apps** or **Workflows**
3. Read the on-canvas Note, change widgets, Queue

Do not edit raw `_lab` JSON. Save keepers under `_user/`.

## Graph

```mermaid
flowchart LR
  N1["Operator note"]
  N2["Preflight"]
  N3["Verdict"]
  N4["Tier table"]
  N5["Check models"]
```

## Nodes on this graph

| Id | Title | Type | Group |
| --- | --- | --- | --- |
| 1 | Operator note | `Note` | NOTE |
| 2 | Preflight | `EZNvidiaLabPreflight` | SETTINGS |
| 3 | Verdict | `EZNvidiaLabVerdict` | SETTINGS |
| 4 | Tier table | `EZNvidiaLabCatalog` | SETTINGS |
| 5 | Check models | `EZModelCheck` | QUALITY |

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

**This graph:** `## labs/nvidia/instant-nurec Instant NuRec - Reconstructs a simulatable multi-camera driving world in one feed-forward pass, no per-scene training. Status: deferred. Install: git-clone. Artifact: sou...`

```text
## labs/nvidia/instant-nurec

Instant NuRec - Reconstructs a simulatable multi-camera driving world in one feed-forward pass, no per-scene training.

Status: deferred. Install: git-clone. Artifact: source-build. Arm64: unknown. GB10: unverified. Comfy shape: host-cli.
Input: multi-camera driving log
Output: a Gaussian scene with static and dynamic layers plus a sky cubemap
Licenses: code Apache-2.0. Weights not stated in the README. Commercial use unknown.
Footprint: 24 GB VRAM, 40 GB disk. Weights: nvidia/instant-nurec/instant_nurec.pt@0.84.
Artifact ref: https://github.com/NVIDIA/instant-nurec.git
Upstream: https://github.com/NVIDIA/instant-nurec
Also: https://huggingface.co/nvidia/instant-nurec
Sources: https://github.com/NVIDIA/instant-nurec

Nothing in this graph touches the GPU. The row's work runs outside the Comfy process through the operator CLI, so the App claims no occupancy and stops no heavy job: the one-heavy-job rule is the CLI's to enforce, next to the heavy confirm and the headroom preflight.

Operator verbs (host shell):
  bazelisk run //:manage -- nvidia-lab status
  bazelisk run //:manage -- nvidia-lab plan instant-nurec

Canvas:
1. Preflight prints whether this Spark could run the row today - the catalog row, an aarch64 host, the binary that row's install kind needs, and the artifact ref.
2. The verdict card prints the blocking reason and the sentence that would reopen the row.
3. The tier table prints all 18 rows with their status and licenses.

Gate notes: Feed-forward reconstruction is the right shape for a single GPU, but the weights license is not stated in the repository and the uv lockfile pins are the aarch64 risk. Its input domain is driving logs, which no lane in this stack produces.
Reopen: Re-test when the model card states a weight license that permits product use and a linux_aarch64 dependency set resolves.
Verify: bazelisk test //tests:bats_nvidia_lab_test

Occupancy: none - stop nothing GPU. One GB10 job.
```

### `EZNvidiaLabPreflight` - NVIDIA lab preflight

Answer whether one catalog row could run on this Spark today.

!!! warning "Lab notes"

    Category EZ Comfy/NVIDIA Lab. Checks the catalog row exists, the host is aarch64, the binary that row's install verb needs is on PATH (docker for docker-pull, git for git-clone), the artifact ref is shaped like a pull spec or a clone URL, and what upstream says about GB10. There is no network probe: the container has no egress guarantee, so 'reachable' is the shape of the ref. Missing tooling is ok=False plus a reason, never an error. Installs nothing. An unverified GB10 is a note, not a blocker; unsupported is.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `report` | out | `STRING` | Every check with its verdict line and each blocking reason. |
| `ok` | out | `BOOLEAN` | False whenever a reason exists. |

#### `tool_id`

Type `STRING`. Range / default: artifixer.

Catalog row id to check.

**How it affects generation:** kebab-case id from catalog.json. An empty id or one no row carries is a reason, not a crash. The opt-in rows are the only install paths; every other row is a card.

**This graph:** `instant-nurec`

### `EZNvidiaLabVerdict` - NVIDIA lab verdict

Print why one row is off the install path, the sentence that would reopen it, and the command that re-checks it.

!!! warning "Lab notes"

    Category EZ Comfy/NVIDIA Lab. Reads the catalog only and runs nothing, so a blocked row is answerable on a host that cannot install it. An opt-in row says nothing blocks it. An output node: the verdict shows on the canvas after Queue.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `verdict` | out | `STRING` | The row's gate notes, its reopen line, and its verify command. |

#### `tool_id`

Type `STRING`. Range / default: nurec-ga.

Catalog row id to answer for.

**How it affects generation:** kebab-case id from catalog.json. The lab graphs pin it to the graph's own row; another id prints that row's verdict instead.

**This graph:** `instant-nurec`

### `EZNvidiaLabCatalog` - NVIDIA lab catalog

Print every NVIDIA lab row with its status, code license, weights license, and commercial-use verdict.

!!! warning "Lab notes"

    Category EZ Comfy/NVIDIA Lab. Reads the pack's own catalog.json with stdlib json, so a missing or malformed catalog prints the reason instead of failing the Queue. Nothing is installed and nothing is downloaded. An output node: the report shows on the canvas after Queue. A footprint of 0 in the catalog is not a size, it is the pack's way of saying upstream publishes no figure, so the list view prints 'vram not published' rather than 0 GB.

| Socket | Dir | Type | What it carries |
| --- | --- | --- | --- |
| `report` | out | `STRING` | The tier report: one aligned line per row on table, one labelled block per row on list. |

#### `detail`

Type `COMBO`. Range / default: table (lab).

Report shape.

**How it affects generation:** table is one aligned line per row (id, status, code license, weights license, commercial). list adds arm64, GB10, install, artifact, footprint, weights, and graph per row.

**This graph:** `table`

**Other choices**

| Choice | What it does |
| --- | --- |
| `list` | One block per row with arm64, gb10, install, footprint, graph. |
| `table` | One aligned line per row (lab default). |

### `EZModelCheck` - Check models

Manual disk check for occupancy + Detail weights. Queue does not run this node.

!!! warning "Lab notes"

    Click Check models (canvas button or App occupancy chip). Reports Ready, or missing files plus the host download command. Not an output node.

#### `status`

Type `STRING`.

Last check result.

**How it affects generation:** JS overwrites after Check models. Queue ignores this node.

**This graph:** `Click Check models. Queue does not run this node.`
