---
title: Occupancy desk
description: One heavy GPU job on GB10 — park Comfy for Blender Workbench or the 35B writing desk, then restore Klein / TRELLIS / Wan / LTX.
tags: [occupancy, blender, trellis, safety, gb10]
---

# Occupancy desk

**What's on this page**

- Why GB10 is still one heavy GPU job
- Modes: idle, blender-desk, llm-desk, klein, trellis, wan, ltx
- Park Comfy with `POST /free` instead of `stop` for Workbench dumps or the 35B sidecar
- What stays XOR (NVENC, Cycles CUDA, LTX next to TRELLIS, llm-desk next to blender-desk)
- Graph occupancy label `llm` (Prompt Forge) is **not** a CLI mode
- In-tree MCP: blender-mcp (desk) and research-mcp (GPU sidecar when llm-desk; CPU 4B as OOM fallback; Path D)

**What this enables**

- Host Blender clay dumps without typing **yes** on a full `start` cycle every time
- An opt-in 35B writing desk (`llm-desk`) while Comfy weights are parked
- A later TRELLIS (`klein-trellis2-lab-example`) or LTX Queue after Blender / the sidecar is stopped
- Unchanged `restart: "no"`, heavy confirm, `mem_limit: 90g`, headroom 28 GiB

!!! danger "One heavy job"

    Parked Comfy is **not** a second denoise. `blender-desk` is Workbench / CPU after models unload. `llm-desk` is the host 35B llama-server after models unload — that sidecar **is** the GPU job. Cycles CUDA, TRELLIS, Wan, LTX, and llm-desk still XOR with each other. This does **not** weaken `restart: "no"`, headroom, or download-limit clear-on-exit.

---

## Modes

| Mode | Compose | Comfy weights | 35B sidecar | GPU job |
| --- | --- | --- | --- | --- |
| `idle` | down | — | **stopped** | none |
| `blender-desk` | up **or** down | `POST /free` unload when up | **stopped** | Workbench / CPU dumps |
| `llm-desk` | up **or** down | `POST /free` unload when up | **running** (`127.0.0.1:30000`) | host llama-server GGUF |
| `klein` | up, 90g/80g | Klein 4B | **stopped** | stills |
| `trellis` | up, 90g/80g | TRELLIS.2 INT8 | **stopped** | image→mesh |
| `wan` / `ltx` | up, 90g/80g | video | **stopped** | 5s print |

App occupancy keys (`none` / `llm` / `klein` / …) on Prompt Forge and research-chat are **graph labels**. `llm` means nothing GPU. It is not `occupancy enter llm`.

```bash
./scripts/manage.sh occupancy status
./scripts/manage.sh occupancy enter blender-desk
./scripts/manage.sh blender -- --background
./scripts/manage.sh occupancy enter llm-desk --yes
# OpenAI-compatible: http://127.0.0.1:30000/v1
./scripts/manage.sh occupancy enter trellis --yes
```

One-time 35B pull (throttled; **not** `download-models`):

```bash
./scripts/manage.sh download-llm --tier qwen36-35b-a3b
```

Host `llama-server` must be on `PATH` (aarch64). Missing binary prints a host-install hint and exits 1 — do not apt/pip inside Docker. vLLM + `nvidia/Qwen3.6-35B-A3B-NVFP4` is an operator alternative only (not wired). Path D: `ssh -L 30000:127.0.0.1:30000`.

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
- Not `occupancy enter llm` (graph label only). Use `llm-desk` for the 35B sidecar.

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

**research-mcp** is the creative-process desk (chat, web search, sequential research subagents, `list_lab_apps` / `describe_app`). Graph occupancy **llm**: GPU 35B sidecar when `llm-desk` is up (`http://127.0.0.1:30000/v1` on the host; `host.docker.internal` from Comfy). CPU 4B only if the sidecar is down or occupancy is Wan/LTX/TRELLIS. It does **not** refuse a GPU Comfy session and does **not** map `idle` → `blender-desk` or `llm-desk`. Same pipeline as **research-chat-lab-example**. HTTPS search is SSRF-guarded (no arbitrary `fetch_url` tool).

```bash
./scripts/manage.sh research-mcp --stdio
./scripts/manage.sh research-mcp --call research '{"message":"night rooftop lighting"}'
```

Path D: laptop agent is the MCP client; Spark runs `research-mcp`. Briefs land under `${COMFY_OUTPUT_DIR}/research/` (never `MODELS_DIR`). Copy prompt ingredients into Prompt Forge, then Spark Still. MCP does not Queue Comfy.

Related: [ComfyUI Apps](studio-apps.md), [Blender GB10 sidecar](blender-gb10-sidecar.md), [Studio sidecars](studio-sidecars.md), [Hardware, memory, and safety](learn/hardware.md).
