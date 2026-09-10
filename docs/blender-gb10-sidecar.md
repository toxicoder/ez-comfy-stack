---
title: Blender GB10 sidecar
description: Host Blender next to the US-safe studio. Refuses if Compose is up. Never in the Dockerfile.
tags: [blender, sidecar, occupancy, gb10]
---

# Blender GB10 sidecar

**What's on this page**

- Why Blender stays on the host
- `manage.sh blender` occupancy refuse
- Dump verbs: `export-guides` (5.00s pack) and `blender-stills` (creator plates)
- Install hint (not a packager)

**What this enables**

- Optional DCC pass on the same Spark after Comfy is stopped
- No Blender layer in `docker/Dockerfile` (image stays Comfy + torch)

!!! danger "Stop Comfy first"

    `blender.sh` **dies** if the studio compose project is running (same occupancy rule as NVENC proxies). `restart: "no"` is unchanged.

---

## Operator path

```bash
./scripts/manage.sh stop
./scripts/manage.sh blender -- --background
# or: ./scripts/utilities/blender.sh -- /path/to/scene.blend
./scripts/manage.sh export-guides --film go-see --shot 12 --blend /path/to/shot.blend
./scripts/manage.sh blender-stills --film go-see --plate mug --blend /path/to/prop.blend --size 1024x1024
```

If `blender` is not on `PATH`, the script prints an install hint and exits 1. This stack does **not** apt/pip/Docker-install Blender.

Exit **2** means compose is still up:

```bash
./scripts/manage.sh stop
./scripts/manage.sh blender
```

## What this is not

- Not a Compose profile (unlike optional [studio-ui](shorts.md))
- Not inside the Comfy container
- Not a reason to weaken `mem_limit: 90g` or headroom `min_host_free_gib: 28`

Guide packs (clay / depth / canny / first+last): [DCC guide pack](dcc-workflows.md) (`manage.sh export-guides`). Creator stills: [Blender creator suite](learn/blender-creator.md) (`manage.sh blender-stills`). Instagram 4:5 greybox stills: [Dream-house tours](learn/dream-house.md) (`manage.sh house-views`). TRELLIS.2 / DA3-BASE weights: [Studio sidecars](studio-sidecars.md). Splat viewer: [Splat sidecar](splat-sidecar.md).
