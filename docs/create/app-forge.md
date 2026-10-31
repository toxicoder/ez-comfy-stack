---
title: App Forge
description: Clone a shipped lab graph into live _user/ as your own App, from a brief, on occupancy llm.
tags: [app-forge, studio-mcp, inspire, workflows, mcp]
---

# App Forge

Use this page when no shipped graph is quite your job: describe the App you
want, and App Forge clones the closest lab graph into live `_user/` with its
App Mode widgets, US-safe coords, and occupancy intact. It does not Queue
Comfy, and it never writes `workflows/_lab/`. Pick the shipped graph first on
[Workflow catalog](../studio-workflows.md); load the result on
[ComfyUI Apps](../studio-apps.md).

**What's on this page**

- **What it writes** - the widgets you fill and the file it produces
- **How auto picks** - how **Template** `auto` chooses a lab graph
- **Path D** - the same pipeline from a laptop agent
- **Related** - what to load next

**What this enables**

- **Making a new operator App** without editing raw JSON
- **Keeping US-safe coords**, App Mode widgets, and occupancy from the template
- **Driving the same pipeline** from a laptop agent
- **Keeping the shipped catalog clean** - the result lands in `_user/`, never `_lab/`

**Who this is for:** studio users after Prompt Forge. Occupancy **llm**. No UNET.

Load **inspire/app-forge**. Type a **Brief**, leave **Template** on auto (or pin `stills/instagram-square`), set **Slug**, Queue.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

```mermaid
flowchart LR
  B["Brief"] --> F["inspire/app-forge"]
  T["Template auto or pin"] --> F
  F --> C["Clone _lab graph"]
  C --> U["_user/<slug>.app.json"]
  U --> A["Open in Apps"]
  A --> Q["Queue under source occupancy"]
```

---

## What it writes

The generator App is occupancy **llm** (nothing GPU unless `llm-desk` is the writing desk). The **result** keeps the source occupancy (`klein` / `wan` / `ltx` / ...). Open `_user/<slug>` and Queue only when that family is legal.

| Widget | Role |
| --- | --- |
| **Brief** | What the new App should make |
| **Template** | `auto` or a lab id (`stills/still-draft`, `motion/silent/still-to-video-5s`, ...) |
| **Slug** | Live filename stem (`mug-ig`) |
| **As app** | On writes `*.app.json` (Apps sidebar) |
| **Overwrite** | Off refuses an existing `_user` file |

Dest: `${COMFY_OUTPUT_DIR}/comfy-user/default/workflows/_user/<slug>.app.json`. Never `workflows/_lab/`. Keepers: `./scripts/manage.sh promote-workflow`.

---

## How auto picks

When Template is **auto**, App Forge asks the on-box GGUF (or the 35B sidecar when `llm-desk` is up) for `{template, slug, slots}`. If the GGUF is missing it uses a keyword heuristic: `1:1` / square -> `stills/instagram-square`, silent / i2v -> `motion/silent/still-to-video-5s`, ltx / foley -> `motion/av/still-to-video-8s`, default `stills/still-draft`. It never invents node types.

Official Comfy Cloud MCP / PyPI `comfy-mcp` stay out of the image. This is the in-tree analog: templates first, typed tools, no `execute_code`.

---

## Path D

```bash
./scripts/manage.sh studio-mcp --stdio
./scripts/manage.sh studio-mcp --call generate_app '{"brief":"1:1 IG still of a mug","slug":"mug-ig"}'
```

Same pipeline as the App. Does not Queue Comfy. Does not refuse a GPU session. Does not map `idle` -> `blender-desk`.

---

## Related

1. Open the new App and Queue it: [ComfyUI Apps](../studio-apps.md)
2. Choose the template it cloned: [Workflow catalog](../studio-workflows.md)
3. Write the prompt the new App expects: [Prompting](../prompting.md)
4. Preview a prompt before you forge an App for it: [Cinema Rack](cinema-rack.md)
5. Promote a keeper into the lab catalog: `./scripts/manage.sh promote-workflow` ([manage.sh reference](../manage-cli.md))
