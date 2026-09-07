---
title: Splat sidecar
description: SuperSplat MIT host viewer for Gaussian splats. Not in the Dockerfile. Occupancy with Comfy.
tags: [splat, supersplat, sidecar, occupancy]
---

# Splat sidecar

**What's on this page**

- SuperSplat as a **host** static viewer (MIT)
- Why it is not in `docker/Dockerfile`
- Occupancy with Comfy / TRELLIS

**What this enables**

- Inspecting a splat on the Spark without baking a viewer into the Comfy image
- Keeping Pixal3D / Inria 3DGS **out** of the default pack

!!! warning "Host viewer"

    SuperSplat (`playcanvas/supersplat`, MIT) is a static viewer you run on the host. It is **not** cloned into this MIT tree, **not** a Compose service, and **not** a `manage.sh` verb.

---

## Operator path

1. `./scripts/manage.sh stop` — encoder / GPU occupancy
2. Open SuperSplat on the host (upstream release or local static build)
3. Load the splat file from disk. Do not point it at the Comfy volume as a live mount while compose is up

TripoSR / TripoSplat weights remain an opt-in manifest pack (`triposplat`) and are **not** a default. `--drop-pack triposplat` cannot eat `flux2-vae`.

Banned as defaults: Inria 3DGS, Pixal3D-as-default, nvdiffrast TRELLIS. See [Model licenses](licenses.md).

Related: [Studio sidecars](studio-sidecars.md) · [Blender GB10 sidecar](blender-gb10-sidecar.md).
