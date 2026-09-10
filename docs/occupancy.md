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

State lives at `${COMFY_OUTPUT_DIR}/.occupancy.json` (outputs, never `MODELS_DIR`).

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

Related: [Blender GB10 sidecar](blender-gb10-sidecar.md), [Studio sidecars](studio-sidecars.md), [Hardware, memory, and safety](learn/hardware.md).
