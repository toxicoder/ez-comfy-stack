---
title: Declined integrations
description: Third-party models and node packs that were evaluated for the Spark stack and rejected, including every NVIDIA row the opt-in nvidia-lab tier refuses, with the evidence, the exact gate that would reopen each, and the catalog path to use instead.
tags: [models, safety, licenses, video, integrations]
---

# Declined integrations

**What's on this page**

- **Rejected** - Project Lyra 2.0, Nous Research Arete-27B, ComfyUI\_Nvidia\_VFX\_Nodes, and every NVIDIA research row the tier refuses
- **NVIDIA lab tier** - each NVIDIA candidate here also carries a catalog row; this page is the verdict and the evidence, the tier page is the catalog
- **Per item** - what it is, the blocking fact, what would reopen it, what to use instead
- **Enforcement** - how the tier catalog and the refuse list keep the weights off disk
- **Reopening** - how to run the evaluation again

**What this enables**

- Read one page instead of re-researching a candidate that was already turned
  down, with the vendor source for each verdict
- Tell a license wall from a hardware wall, which decides whether waiting helps
- Confirm the catalog keeps both weight sets off `${MODELS_DIR}` without you
  auditing the download list by hand
- Re-test a declined candidate against the four gates when a vendor ships new
  artifacts

This stack is a single-DGX-Spark (GB10, 128 GB unified memory) local studio. A
candidate has to clear four gates at once: a license that permits running it in
a product container, a `linux_aarch64` artifact that installs on GB10, a memory
and disk envelope that fits beside the pinned catalog, and a modality that
actually serves an image, video, or audio lane. Any single gate is enough to
decline. The findings below were taken from the vendor's own model cards,
release indexes, and issue trackers.

## Summary

The NVIDIA candidates below are no longer verdicts in prose only. Each carries a
row in the opt-in **nvidia-lab** tier catalog at
`custom_nodes/ez_nvidia_lab/catalog.json`, and that row is what refuses it an
install path. This page carries the verdict and the evidence;
[NVIDIA lab](../nvidia-lab.md) carries the catalog, the footprints, and the
verbs that install the rows that cleared the gates. The verdict words below
match the tier statuses: **Declined** is a refused row (`blocked-license` or
`blocked-platform`), **Deferred** is a row parked on a fact nobody has
published yet.

| Candidate | Verdict | Blocking gate | Reopen when |
| --- | --- | --- | --- |
| NVIDIA Project Lyra (Lyra 2.0) | Declined | License bars deployment and production use | NVIDIA relicenses the checkpoints |
| Nous Research Arete-27B | Declined | Text-only model with no GGUF; no media lane to serve | A CPU-runnable GGUF exists and a use beyond the pinned writer appears |
| ComfyUI\_Nvidia\_VFX\_Nodes | Declined | No `linux_aarch64` wheel for the `nvidia-vfx` runtime | NVIDIA publishes an aarch64 wheel that works on GB10 |
| LuxDiT | Declined | The code itself ships the NVIDIA OneWay Noncommercial License | NVIDIA relicenses the code away from the OneWay Noncommercial terms |
| InfiniCube | Declined | Weights bar commercial use, sit on a personal Hugging Face account, and bind to the Waymo Open Dataset ToS | Weights relicensed for commercial use and hosted by the NVIDIA org |
| dvlt (Deja View) | Declined | Non-commercial weights plus the VGGT terms on the derived files, which refuse the best hardware fit in the tier | The weights are relicensed, or a permissive checkpoint of the same size appears |
| SplatPainting | Declined | The vendored `deps/gsplats` tree carries Inria and MPII research licenses | That dependency is replaced or relicensed so a build needs no research-licensed tree |
| PixelUMM | Deferred | 121.6 GB of distributed checkpoints behind a documented seven-GPU path, on a card tagged `license:other` | A quantized single-GPU inference checkpoint with a readable permissive weight license |
| Cosmos Drive Dreams | Declined | x86\_64-only Cosmos wheels and NGC containers; no `linux_aarch64` artifact resolves | Upstream Cosmos publishes linux\_aarch64 wheels or an arm64 container that runs on GB10 |
| ComfyUI DLSS 5 Enhancer | Declined | A Windows D3D12 `nvngx.dll` worker, the same NGX wall as ComfyUI\_Nvidia\_VFX\_Nodes | NVIDIA ships a linux\_aarch64 NGX runtime either pack can drive |
| Omniverse NuRec GA (`nre/nurec-ga`) | Deferred | arm64 exists only as non-gating `-arm64` or `-multiarch` nightly tags, and the container license and NGC entitlement are not public | A gated `-arm64` or `-multiarch` tag on a release-branch build, plus a public container license and entitlement |
| Gamma-World | Deferred | No named weight host, no stated weight license, no memory envelope | Upstream names the host, states the weight license, and publishes the envelope |
| Asset Harvester | Deferred | Weight license and GPU class unpublished, for an AV-asset domain no lane serves | A published weight license, a GPU class that fits one Spark, and a lane that wants AV assets |
| Instant NuRec | Deferred | Weight license not stated in the repository, and the input domain is multi-camera driving logs | The model card states a product-usable weight license and an aarch64 dependency set resolves |

## NVIDIA Project Lyra

Lyra is NVIDIA's open generative 3D world model line, and its two releases do
not carry the same weight terms. `nv-tlabs/lyra` is the canonical repository for
both; `nv-tlabs/Project-Lyra` is only the GitHub Pages site - an `index.html`,
styles, and assets - and holds no code. The tier carries each release as its own
row, so the installable half is not refused with the half that is.

### Lyra 1.x is installable through the tier

Lyra 1.x generates a camera-controlled walkthrough video of a 3D-consistent
world from one image. The code is Apache-2.0 and the `nvidia/Lyra` weights carry
the NVIDIA Open Model License, which permits commercial use, so the row is
**opt-in** and installs with `bazelisk run //:manage -- nvidia-lab install lyra-1`.

The cost is the run, not the license. The README reports testing on H100 and
A100 only, the row budgets 80 GB of VRAM and 100 GB of disk, the Cosmos Predict 1
backbone is pulled separately, and the install builds Triton and custom kernels.
No GB10 run has been reported, so treat the first one as the measurement.

### Lyra 2.0 stays declined

Lyra 2.0 takes one image plus a camera trajectory, generates a walkthrough video
with a 14B Wan 2.1 image-to-video DiT, then reconstructs 3D Gaussian Splats from
it.

**Blocked on license.** The `nvidia/Lyra-2.0` checkpoints are released under the
NVIDIA Internal Scientific Research and Development Model License. Its terms of
use state that the model and any derivative "may not be distributed, deployed,
sublicensed, publicly displayed, publicly performed", and that you "may not use
the Model or a Derivative Model in a production environment or for the purpose
of generating works for sale or distribution". Running it inside a product
container is deployment. The repository code is Apache-2.0, which does not
change the weight terms.

**Blocked on size and hardware too.** The checkpoint set is roughly 98 GB, of
which about 97 GB is inference weights, including a 68 GB 32-shard DCP DiT. The
maintainer reports a 48 GB card out-of-memory even with every offload flag on,
and puts the practical floor near 80 GB with no quantization planned. Install is
a recursive clone under conda with Python 3.10, CUDA 12.8, torch 2.7.1, and
source builds of `flash-attn` 2.6.3 and TransformerEngine. This image is
CUDA 13.0 with torch 2.14.1, so those pins would have to be reconciled by hand.
Upstream targets H100 and GB200; nothing has been reported on GB10, and the
attention dispatch table stops before that architecture. There are no ComfyUI
nodes in the repository and no third-party wrapper.

**What would reopen it.** NVIDIA relicenses the `nvidia/Lyra-2.0` checkpoints so
deployment and production use are permitted - the row's own `reopen` sentence.

**Use instead.** A walkthrough you may actually run is the tier's `lyra-1` row.
Stills come from Klein and motion from Wan 2.2 and LTX-2.5, all in the pinned
catalog. For 3D, the native TRELLIS lane covers image-to-3D. See
[NVIDIA lab](../nvidia-lab.md), [TRELLIS and 3D](../learn/pipeline.md) and
[Models and cache](../models-and-cache.md).

## Nous Research Arete-27B

Arete-27B is a supervised fine-tune of a 27B Qwen text model. It is 27.4B
parameters in BF16, about 54.7 GB across 18 shards, Apache-2.0 and ungated, with
a 262k context. Its stated purpose is to change the political answering behavior
of the base model.

**Blocked on fit.** It is text-generation only. Its image and video encoder is
inherited and frozen, so it reads media and produces none, which leaves it no
lane in a media pipeline. The stack's local model lane runs GGUF files
CPU-only so a writer never competes with a GPU tenant for GB10 memory, and
Arete-27B has no official GGUF release at all. Loading 54.7 GB of BF16 to
rewrite a prompt sentence also breaks the one-heavy-GPU-job occupancy rule that
keeps the stack stable.

**Use instead.** Prompt Enhance uses the pinned Qwen3-4B GGUF on CPU, the
opt-in 35B pack covers the desk writer, and Qwen2.5-VL covers captioning. All
three arrive with `bazelisk run //:manage -- download-models`. See
[Prompting](../prompting.md) and [GGUF models](../models-and-cache.md).

## ComfyUI\_Nvidia\_VFX\_Nodes

This pack adds three nodes backed by NVIDIA's NGX runtime: `RTXVideoSuperResolution`
(multi-mode upscale, denoise, deblur), `RTXTrueHDR` (SDR to BT.2020 HLG/PQ), and
`RTXVideoFrameGeneration` (2-16x frame interpolation). It needs no Hugging Face
download because the weights ship inside the wheel.

**Blocked on architecture.** The pack installs with
`python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com`,
and that index publishes only `manylinux x86_64`, `win_amd64`, and `win_arm64`
wheels. There is no `linux_aarch64` wheel, so the install cannot resolve inside
this image. The README's "RTX Spark is supported" line refers to the
Windows-on-Arm part, which the `win_arm64` wheel serves; it is not evidence for
DGX Spark.

**Two further issues on Blackwell Linux.** The super-resolution node returns an
all-black tensor with no exception on Blackwell under Linux, because the bundled
NGX cubins lack that architecture. The runtime also loads its own cuDNN with
`RTLD_GLOBAL` and rewrites `LD_LIBRARY_PATH`, which aborts later cuDNN consumers
such as the pose models. Both are open upstream.

**Use instead.** The image and video lanes already expose the stack's own
upscaling and format nodes. Until an aarch64 wheel exists, run HDR and
interpolation passes on an x86 workstation and bring the finished file back in.
See [Shorts](../shorts.md) and [Cinema](../visual-generative-ai.md).

## LuxDiT

LuxDiT estimates image-based lighting from a single photo or a video with a
video diffusion transformer. It is the relighting capability the 3D lane does
not have, which is why the row stays in the catalog as a card rather than
disappearing.

**Blocked on license.** The repository ships the NVIDIA OneWay Noncommercial
License, so it is the code itself, not only the weights, that bars use inside a
product container. The `nvidia/LuxDiT` card tags its 23.5 GB image checkpoint
`license:other`, which is a second wall behind the first.

**What would reopen it.** NVIDIA relicenses the code away from the OneWay
Noncommercial terms. The weight terms then have to be readable as a permission
for product use, not a card tag.

**Use instead.** Nothing in the promoted stack relights a shot today. The 3D
lane goes image to mesh with TRELLIS.2 and the [Asset Bible](../asset-bible.md)
records those outputs, so a relight stays in the DCC tools beside the stack for
now. See [3D pipeline](../learn/pipeline.md) and [NVIDIA lab](../nvidia-lab.md).

## InfiniCube

InfiniCube generates an unbounded voxel world with video and dynamic Gaussians
for driving scenes, from a prompt and a pose.

**Blocked on license.** The checkpoints are hosted on a personal Hugging Face
account (`yifanlu/InfiniCube-checkpoints`) rather than the NVIDIA org, their
terms allow research and educational use only and prohibit commercial use, and
they bind the user to the Waymo Open Dataset terms of service on top. The code
being Apache-2.0 does not change any of that. The run is heavy as well: the Wan
14B stage is about 20 minutes per 93-frame 480p clip on an A100.

**What would reopen it.** The weights are relicensed for commercial use and
hosted by the NVIDIA org, so the terms come from the vendor and not from a
personal account.

**Use instead.** Stills from Klein and motion from Wan 2.2 and LTX-2.5. The
input domain is driving scenes, which no lane in this stack produces, so even a
clean license would need a use case first. See
[Model licenses](../licenses.md) and [NVIDIA lab](../nvidia-lab.md).

## dvlt (Deja View)

dvlt reconstructs multi-view geometry as pointmaps, depth, and camera poses with
a looping transformer. It is the closest fit to this machine in the whole tier.

**Blocked on license.** The `nvidia/dvlt` weights are under an NVIDIA license for
non-commercial research and evaluation use only, and the VGGT-derived files in
the repository carry the VGGT License rather than the Apache-2.0 the rest of the
tree uses. Two non-commercial terms, one on the weights and one on part of the
code.

**Blocked on nothing else.** 0.5 GB of weights, a
documented single-GPU path, 12 GB of VRAM and 5 GB of disk - the footprint a
splat capture front end actually wants on one Spark. The conda pins (torch 2.5.1,
CUDA 12.4) are the only other friction.

**What would reopen it.** The weights are relicensed for commercial use, or a
permissive checkpoint of the same size appears.

**Use instead.** The `3dgrut` row trains and renders from a COLMAP capture with
no weights to license at all, and the [Splat sidecar](../splat-sidecar.md)
viewer reads the scenes it mints. See [NVIDIA lab](../nvidia-lab.md).

## SplatPainting

SplatPainting is an interactive brush for painting and editing a Gaussian Splat
scene. The editing surface is genuinely useful for the 3D lane, so the row stays
as a card.

**Blocked on license.** The repository is Apache-2.0 except the vendored
`deps/gsplats` tree, which carries Inria and MPII research licenses. A build that
links that tree is not clean for a product image, and the disk refuse list
already names `Inria-3DGS` for the same reason.

**What would reopen it.** The gsplat dependency is replaced or relicensed so a
build needs no research-licensed tree.

**Use instead.** Scene edits belong in the DCC lane before the mesh is minted,
and [Splat sidecar](../splat-sidecar.md) stays a viewer that mints nothing. See
[DCC workflows](../dcc-workflows.md) and [NVIDIA lab](../nvidia-lab.md).

## PixelUMM

PixelUMM is an encoder-free unified model that understands and generates both
images and video in one network.

**Blocked on footprint and on terms.** The released weights are 121.6 GB of
distributed checkpoints, the model also pulls a 16 GB Qwen3-8B, and the
documented training path asks for seven GPUs of 48 GiB or more. That is a
cluster, and this stack is one Spark; the row marks GB10 unsupported. The
Hugging Face card tags the weights `license:other` and the terms were not
readable as permission for product use.

**What would reopen it.** A quantized single-GPU inference checkpoint with a
readable permissive weight license. Both halves have to land: the footprint and
the terms.

**Use instead.** Klein, Wan 2.2, and LTX-2.5 generate; Qwen2.5-VL captions. All
of it arrives with `bazelisk run //:manage -- download-models`. See
[Prompting](../prompting.md) and [Models and cache](../models-and-cache.md).

## Cosmos Drive Dreams

Cosmos Drive Dreams generates synthetic multi-view autonomous-vehicle video and
LiDAR from HD map, bounding box, and LiDAR conditions.

**Blocked on architecture.** The Cosmos 1 upstream it needs ships x86\_64 NGC
images and prebuilt CUDA wheels, so nothing resolves inside this aarch64 image.
The license is not the problem here: the weights inherit the NVIDIA Open Model
License from the Cosmos cards and permit commercial use. The domain is the other
wall - the inputs are autonomous-vehicle sensor conditions, which no lane in this
stack produces.

**What would reopen it.** Upstream Cosmos publishes linux\_aarch64 wheels or an
arm64 container that runs on GB10.

**Use instead.** The image and video lanes. A driving-sim lane would have to
exist before this row had a job. See [Cinema](../visual-generative-ai.md) and
[NVIDIA lab](../nvidia-lab.md).

## ComfyUI DLSS 5 Enhancer

This node pack pushes RGBA frames and estimated motion vectors through the DLSS 5
neural renderer and returns reconstructed frames at 1.5x to 3x. Its own code is
MIT with a runtime carve-out for the bundled NVIDIA binaries.

**Blocked on architecture.** The pack is a client of a native D3D12 worker
process that hosts ReShade, must be named `nvngx.dll`, and is installed by a
Windows embedded-python path against a GeForce driver. There is no Linux path at
all, so it cannot run in this container. That is the same NGX wall that already
declines ComfyUI\_Nvidia\_VFX\_Nodes one section above, and the same wall
`nvidia-lab` records on the `dlss5-enhancer` row.

**What would reopen it.** NVIDIA ships a linux\_aarch64 NGX runtime the pack can
drive - the reopen condition the VFX nodes row waits on too.

**Use instead.** The stack's own upscaling and format nodes, as the VFX nodes row
above says. See [Shorts](../shorts.md) and [NVIDIA lab](../nvidia-lab.md).

## Omniverse NuRec GA

Omniverse NuRec GA (the NGC container `nre/nurec-ga`) trains and serves Gaussian
Neural 3DGRT and 3DGUT scenes over gRPC and renders novel views from them. The
open SDK at `NVIDIA/NuRec` is Apache-2.0; the container is not the SDK.

**Blocked on platform and on an unread license text.** NVIDIA states that general
Linux aarch64 is not a supported user platform, and that Grace-Blackwell
enablement reaches you only through the `-arm64` or `-multiarch` tags, which
build as non-gating nightly or on-demand jobs and may not exist for a given
release. Container security scanning covers x86\_64 only. The floor is above
24 GB with 48 GB recommended on an R580 driver or newer. The container license
text, and whether an NGC entitlement is needed to pull it at all, could not be
confirmed from any public page.

**What would reopen it.** NVIDIA publishes a gated `-arm64` or `-multiarch` tag
for a release-branch build and states the container license and the entitlement
terms in public.

**Use instead.** The `3dgrut` row - Apache-2.0, no weights, kernels compiled on
the host - trains and renders the same scene family, and the `artifixer` row
ships a published linux/arm64 CUDA 13 image. See
[NVIDIA lab](../nvidia-lab.md) and its
[generated reference](../generated/nvidia-lab/tier.md).

## Gamma-World, Asset Harvester, and Instant NuRec

Three rows parked as **deferred** because the facts are missing rather than
adverse. Gamma-World rolls out synchronized future observations and actions for
several agents in one interactive world model. Asset Harvester generates
simulatable autonomous-vehicle assets for simulation. Instant NuRec reconstructs
a simulatable multi-camera driving world in one feed-forward pass with no
per-scene training.

**Blocked on missing facts.** Gamma-World documents converting a released
checkpoint to DCP but never says where that checkpoint is hosted, publishes no
VRAM envelope, and states no weight license. Asset Harvester publishes no weight
license and no GPU class. Instant NuRec is Apache-2.0 code whose README states no
weight license at all, and whose uv lockfile pins are the aarch64 risk. There is
nothing to size one Spark against, so the rows record the open questions instead
of a guess.

**Blocked on domain too.** All three work in driving logs and AV assets, and no
lane in this stack produces or consumes either.

**What would reopen them.** Each row's own `reopen` sentence: upstream names the
weight host, states a weight license, and publishes a memory envelope. Re-check
the `sources` list on the row before spending a day on the repository.

**Use instead.** `gen3c` is the tier's one generative row whose weights permit
commercial use outright, and `lyra-1` covers a walkthrough from a still. See
[NVIDIA lab](../nvidia-lab.md).

## Enforcement

Every NVIDIA candidate above is also a row in the opt-in **nvidia-lab** tier, and
the catalog is the enforcement. `custom_nodes/ez_nvidia_lab/catalog.json` is the
single source of truth for each row's status, licenses, artifact, and footprint,
and `install` and `run` refuse any row whose status is not `opt-in` before
anything executes. This page is the prose behind the row; the row is what the CLI
reads. The verbs and the per-row footprints are on
[NVIDIA lab](../nvidia-lab.md).

The weight-bearing candidates stay in the fail-closed refuse list in
`config/model-manifest.yaml`, which is owned by the `//config:policy` target. The
`Lyra-2.0` token stays in place, and so does `Arete-27B`: a path whose name
contains a refuse token is classified as a banned weight, so the disk wizard
names it instead of treating it as reclaimable or as part of the keep-set. Lyra
1.x carries no token, because its weights are installable through the tier.

```bash
bazelisk test //tests:bats_models_manifest_test   # refuse list is present and opt-in
bazelisk test //tests:pytest --test_arg=tests/python/test_disk_catalog.py
bazelisk test //tests:bats_nvidia_lab_test        # the catalog contract and the verbs
```

Nothing in the tier downloads weights. `bazelisk run //:manage --
download-models` fetches only what the manifest pins, no `nvidia-lab` row is a
manifest pack, no row is a Compose service, and no row reaches the image. An
artifact lands on the host only when you run
`bazelisk run //:manage -- nvidia-lab install` on a row whose status is
`opt-in`, which asks for **yes** first, runs the host headroom preflight, refuses
while a heavy occupancy mode holds the GPU, and writes under
`${EZ_NVIDIA_LAB_HOME:-$HOME/.ez-comfy/nvidia-lab}` - never inside the repo. The
cleanup verbs default to `--plan`.

## Reopening an evaluation

Architecture and license terms change. Re-check the primary source before you
spend a day on this:

1. Read the catalog row before the vendor page.
   `bazelisk run //:manage -- nvidia-lab status <id>` prints the status the last
   evaluation recorded, and `plan <id>` prints the artifact, the footprint, and
   the target an install would use. The row's `gate_notes` and `reopen` fields
   are the previous findings, so the day starts from them and not from zero.
2. For an NVIDIA wheel, list the release index and confirm the exact wheel tag
   for `linux_aarch64` and your Python ABI. A `win_arm64` wheel does not prove
   Linux Arm support.
3. For a checkpoint, read the license section of the model card itself and look
   for the words "production" and "deploy". A card tag reading Apache-2.0 can
   sit beside a stricter license in the body.
4. For a node pack, confirm it has no cloud or license-server call, since this
   stack is local-only.
5. Clear the refuse token in the same change that promotes the pack, with a test
   proving the new path works on GB10.

If a candidate clears all four gates, promote it through
`bazelisk run //:manage -- promote-workflow` and update the docs in the same
change. For a tier row the catalog edit comes first: the row's `status` is what
makes `install` accept it, so a re-test that clears the four gates changes
`custom_nodes/ez_nvidia_lab/catalog.json`, this page, and
[NVIDIA lab](../nvidia-lab.md) in one change, with
`bazelisk test //tests:bats_nvidia_lab_test` green.
