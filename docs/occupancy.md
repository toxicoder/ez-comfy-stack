---
title: Occupancy desk
description: One heavy GPU job on GB10 — park Comfy for Blender Workbench, then restore Klein / TRELLIS / Wan / LTX.
tags: [occupancy, blender, trellis, safety, gb10]
---

# Occupancy desk

**What's on this page**

- Why GB10 is still one heavy GPU job
- Modes: idle, blender-desk, klein, trellis, wan, ltx
- Park Comfy with `POST /free` instead of `stop` for Workbench dumps
- What stays XOR (NVENC, Cycles CUDA, LTX next to TRELLIS)
- In-tree MCP: blender-mcp (desk) and research-mcp (CPU research; Path D)

**What this enables**

- Host Blender clay dumps without typing **yes** on a full `start` cycle every time
- A later TRELLIS (`klein-trellis2-lab-example`) or LTX Queue after Blender is stopped
- Unchanged `restart: "no"`, heavy confirm, `mem_limit: 90g`, headroom 28 GiB

!!! danger "One heavy job"

    Parked Comfy is **not** a second denoise. `blender-desk` is Workbench / CPU after models unload. Cycles CUDA, TRELLIS, Wan, and LTX still XOR with each other.

---

## Modes

| Mode | Compose | Comfy weights | Host Blender | GPU job |
| --- | --- | --- | --- | --- |
| `idle` | down | — | off | none |
| `blender-desk` | up **or** down | `POST /free` unload when up | Workbench / CPU | clay / primitives / dumps |
| `klein` | up, 90g/80g | Klein 4B | **stopped** | stills |
| `trellis` | up, 90g/80g | TRELLIS.2 INT8 | **stopped** | image→mesh |
| `wan` / `ltx` | up, 90g/80g | video | **stopped** | 5s print |

```bash
./scripts/manage.sh occupancy status
./scripts/manage.sh occupancy enter blender-desk
./scripts/manage.sh blender -- --background
./scripts/manage.sh occupancy enter trellis --yes
```

`occupancy enter` **does not** start Compose. Heavy modes tell you to `./scripts/manage.sh start` (type **yes**) when the container is down.

State lives at `${COMFY_OUTPUT_DIR}/.occupancy.json` (outputs, never `MODELS_DIR`). In-canvas **Occupancy gate** (`EZDCCOccupancyGate`) reads that file only — it does not start Compose or spawn Blender. [Stay in Comfy after a Blender dump](learn/comfy-first-blender.md).

---

## Park vs stop

`stop` is the hammer: container down, volumes kept. Use it for NVENC proxies, SuperSplat, or a wedged UI.

`occupancy enter blender-desk` keeps Compose up, waits for an empty queue, then `POST /free` `{unload_models, free_memory}` (the Manager unload). Host Workbench dumps (`export-guides`, `blender-stills`, `house-views`, `blender`) are allowed. NVENC still dies if compose is up.

If `/free` fails, Workbench may still contend for unified memory — `occupancy idle` then.

---

## What this is not

- Not a Compose profile for Blender (Blender stays a host binary)
- Not Cycles GPU / OptiX while Compose is up
- Not lowering `mem_limit: 90g` or `min_host_free_gib: 28`
- Not two denoises (Klein + LTX, TRELLIS + LTX, Wan + TRELLIS)

---

## MCP (mcp-construct)

In-tree MCP servers are typed-tool stdio processes. **No** `execute_code`, **no** telemetry. Official Comfy Cloud MCP / `comfy-mcp` stay out of the image (`manage.sh start` is the launch path).

**blender-mcp** wraps occupancy and host Blender (primitives, camera, keyframes, GLB, guide dumps). **No** cloud 3D APIs. bpy tools need blender-desk.

```bash
./scripts/manage.sh occupancy enter blender-desk
./scripts/manage.sh blender-mcp --stdio
# optional on-box 4B (CPU, same GGUF as prompt-enhance):
./scripts/manage.sh blender-llm "greybox mug on a table, dump still mug"
```

Qwen3-4B will place primitives. Cinematic scenes: Path D — laptop Grok/Cursor as the MCP client over SSH, Spark only runs blender-mcp. If `llama-cli` is missing, `blender-llm` prints that hint and exits 1.

**research-mcp** is the creative-process desk (chat, web search, sequential research subagents, `list_lab_apps` / `describe_app`). Occupancy **llm**: CPU GGUF (`n_gpu_layers=0`). It does **not** refuse a GPU Comfy session and does **not** map `idle` → `blender-desk`. Unified memory still contends — prefer a gap between Klein/Wan/LTX Queues for long research. Same pipeline as **research-chat-lab-example**. HTTPS search is SSRF-guarded (no arbitrary `fetch_url` tool).

```bash
./scripts/manage.sh research-mcp --stdio
./scripts/manage.sh research-mcp --call research '{"message":"night rooftop lighting"}'
```

Path D: laptop agent is the MCP client; Spark runs `research-mcp`. Briefs land under `${COMFY_OUTPUT_DIR}/research/` (never `MODELS_DIR`). Copy prompt ingredients into Prompt Forge, then Spark Still. MCP does not Queue Comfy.

Related: [ComfyUI Apps](studio-apps.md), [Blender GB10 sidecar](blender-gb10-sidecar.md), [Studio sidecars](studio-sidecars.md), [Hardware, memory, and safety](learn/hardware.md).
