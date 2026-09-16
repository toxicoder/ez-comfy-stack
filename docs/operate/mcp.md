---
title: MCP
description: In-tree blender-mcp, research-mcp, and studio-mcp typed tools, Path D SSH tunnels, occupancy, no execute_code.
tags: [mcp, blender, research, studio, occupancy, ssh]
---

# MCP

**What's on this page**

- **blender-mcp** typed tools (occupancy + host Blender) — no `execute_code`
- **research-mcp** typed tools (chat, search, lab apps) — no `execute_code`
- **studio-mcp** typed tools (clone lab graphs into `_user/`) — no `execute_code`, no Queue
- **Path D** SSH tunnels with session vars
- **Occupancy** — bpy needs `blender-desk`; research-mcp is CPU GGUF and does not refuse a GPU session

**What this enables**

- **Wiring** a laptop agent as the MCP client while the Spark only runs stdio servers
- **Dumping** clay stills / guides without a cloud 3D API
- **Keeping** research briefs on `${COMFY_OUTPUT_DIR}/research/` (never `${MODELS_DIR}`)

Desk narrative: [Occupancy](../occupancy.md). Matrix: [Occupancy matrix](occupancy-matrix.md).

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

!!! danger "No execute_code"

    In-tree MCP is typed-tool stdio (`scripts/lib/blender_mcp.py`, `research_mcp.py`, `studio_mcp.py`). **No** `execute_code`, **no** telemetry, **no** arbitrary `fetch_url`. Official Comfy Cloud MCP / `comfy-mcp` stay out of the image (`manage.sh start` is the Comfy launch path). Host only — never in `docker/Dockerfile`.

---

## Path D SSH tunnels

Laptop agent = MCP client. Spark = `blender-mcp` / `research-mcp` (and optional Comfy / 35B sidecar).

```bash
ssh -L "${COMFY_PORT}:127.0.0.1:${COMFY_PORT}" "${SPARK_USER}@${SPARK_HOST}"
ssh -L 30000:127.0.0.1:30000 "${SPARK_USER}@${SPARK_HOST}"
```

Then on the Spark:

```bash
./scripts/manage.sh occupancy enter blender-desk
./scripts/manage.sh blender-mcp --stdio
# optional on-box 4B (CPU, same GGUF as prompt-enhance):
./scripts/manage.sh blender-llm "greybox mug on a table, dump still mug"
```

```bash
./scripts/manage.sh research-mcp --stdio
./scripts/manage.sh research-mcp --call research '{"message":"night rooftop lighting"}'
```

`--list-tools` and `--call TOOL [JSON]` work without stdio. Discovery-only calls (`--list-tools`, occupancy/list/describe) skip bpy / llama.

---

## blender-mcp

Wrappers: `scripts/utilities/blender-mcp.sh` → `scripts/lib/blender_mcp.py`. Server name `ez-blender`. Protocol `2024-11-05`.

bpy tools require **blender-desk** (or Compose down). Non-desk returns `occupancy enter blender-desk first (Comfy is a heavy job)`. Starting bpy MCP records `mcp_pid` and maps **idle → blender-desk**.

`occupancy_enter` **does not start Compose**. Tool description lists `idle|blender-desk|klein|trellis|wan|ltx` (the handler still forwards `mode` to `occupancy.sh enter`).

| Tool | Args | What |
| --- | --- | --- |
| `occupancy_status` | — | Read mode, parked, PIDs |
| `occupancy_enter` | `mode` (required), `yes` boolean | Enter a CLI occupancy mode |
| `scene_info` | optional `blend` | List object names (`bpy.data.objects`) |
| `create_primitive` | `kind` (`cube` `uv_sphere` `cylinder` `plane` `cone`), `name` | Workbench primitive |
| `set_camera` | `location` `[x,y,z]` (default `[0,-8,2]`) | Set Camera location |
| `keyframe_object` | `name` (required), `frame` (default 1) | Location keyframe |
| `export_glb` | optional `path` | GLB under `${COMFY_OUTPUT_DIR}/assets` by default. **Refuses** a path whose parts include `models` but not `assets` |
| `export_guides` | `film` (default `go-see`), `shot` (default `12`), optional `blend` | Host `blender-guide.sh` |
| `blender_stills` | `film`, `plate` (default `mug`), optional `size`, `blend` | Host `blender-stills.sh` |
| `house_views` | `slug` (default `lab-penthouse`) | Host `house-views.sh` |

No cloud 3D APIs.

---

## research-mcp

Wrappers: `scripts/utilities/research-mcp.sh` → `scripts/lib/research_mcp.py`. Server name `ez-research`.

CPU Qwen3-4B + SSRF-safe HTTPS search (Wikipedia + DuckDuckGo). **Does not refuse a GPU Comfy session.** Recording `mcp_pid` does **not** remap `idle` → `blender-desk` or `llm-desk`. Same pipeline as **inspire/research-chat**. MCP does **not** Queue Comfy.

| Tool | Args | What |
| --- | --- | --- |
| `occupancy_status` | — | Read `${COMFY_OUTPUT_DIR}/.occupancy.json` |
| `list_lab_apps` | — | Shipped `_lab` Apps (`id`, `lane`, `occupancy`, `handoff`) |
| `describe_app` | `stem` (required) | One App: occupancy, widgets, handoff, `lab_mcp` |
| `chat` | `message` (required), `history`, `web_search` | One-turn creative-process chat |
| `web_search` | `query` (required) | Titles, snippets, URLs (`limit=5`, no body fetch) |
| `research` | `message` (required), `history`, `web_search` (default true), `subagents` (default 2) | Planner + sequential search subagents + synthesizer |

Briefs: `${COMFY_OUTPUT_DIR}/research/`. Copy prompt ingredients into Prompt Forge, then Spark Still.

When `llm-desk` is up, graph occupancy **llm** may use the host sidecar (`http://127.0.0.1:30000/v1`; `host.docker.internal` from Comfy). CPU 4B is the OOM-safe path next to Wan / LTX / TRELLIS. Research-mcp itself does not GPU-offload llama.

---

## studio-mcp

Wrappers: `scripts/utilities/studio-mcp.sh` → `scripts/lib/studio_mcp.py`. Server name `ez-studio`.

Clones shipped `_lab` graphs into live `${COMFY_OUTPUT_DIR}/comfy-user/default/workflows/_user/`. **Does not Queue Comfy.** **Does not refuse a GPU session.** Recording `mcp_pid` does **not** remap `idle` → `blender-desk`. Same pipeline as **inspire/app-forge**. Official Comfy Cloud MCP stays out of tree.

| Tool | Args | What |
| --- | --- | --- |
| `occupancy_status` | — | Read occupancy JSON |
| `search_templates` | optional `query`, `occupancy`, `lane` | Lab Apps + studio-block ids |
| `get_template` / `describe_app` | `stem` | Occupancy, widgets, handoff |
| `apply_slots` | `stem`, `slots` | Patch widgets on a clone (no write) |
| `validate_workflow` | `stem` or `graph` | Banned strings, Vue-corrected, integer widget ids |
| `save_workflow` | `stem`, `slug` | Write `_user/` only |
| `create_app` | `stem`, `slug` | Write `*.app.json` |
| `generate_app` | `brief`, optional `template`, `slug` | Planner or keyword heuristic → clone → save |

```bash
./scripts/manage.sh studio-mcp --stdio
./scripts/manage.sh studio-mcp --call generate_app '{"brief":"1:1 IG still of a mug","slug":"mug-ig"}'
```

Not included: `run_workflow`, `execute_code`, partner APIs, Comfy Cloud.

---

## Related

| Need | Page |
| --- | --- |
| Modes table | [Occupancy](../occupancy.md) |
| Mode × jobs | [Occupancy matrix](occupancy-matrix.md) |
| App lanes | [ComfyUI Apps](../studio-apps.md) |
| Host Blender | [Blender GB10 sidecar](../blender-gb10-sidecar.md) |
