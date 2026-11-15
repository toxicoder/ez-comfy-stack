---
title: NVIDIA lab tier reference
description: "Generated per-row reference for the opt-in NVIDIA lab tier: status, licenses, artifact, arm64, GB10, footprint, and the reopen condition for every catalog row."
tags: [nvidia, generated, reference, license, splat, world-models]
---

# NVIDIA lab tier reference

**What's on this page**

- **Rows by status** - every tool id grouped under the status it carries
- **Master table** - licenses, artifact, platform, and footprint per row
- **Tool cards** - task, input, output, weights, gate notes, and the reopen sentence

**What this enables**

- **Reading** one row without opening the catalog JSON
- **Telling** an installable row from a card that only records a verdict
- **Quoting** the gate notes and the reopen condition a decision rests on

Catalog schema 1, tier `nvidia-lab`, updated 2026-11-15. The operator-facing page is [NVIDIA lab tier](../../nvidia-lab.md).

> Generated from `custom_nodes/ez_nvidia_lab/catalog.json`. Do not hand-edit this file: edit the catalog, then run `bazelisk run //docs:generate_nvidia_lab` and commit the diff.

## Rows by status

### opt-in

- `3dgrut` - 3DGRUT (3DGRT + 3DGUT)
- `3dgrut-artifixer-fork` - 3DGRUT-ArtiFixer (pinned fork)
- `artifixer` - ArtiFixer
- `gen3c` - GEN3C
- `lyra-1` - Project Lyra 1.x
- `vk-gaussian-splatting` - Vulkan Gaussian Splatting viewer

### blocked-license

- `dvlt` - dvlt (Deja View)
- `infinicube` - InfiniCube
- `luxdit` - LuxDiT
- `lyra-2` - Project Lyra 2.0
- `splatpainting` - SplatPainting

### blocked-platform

- `cosmos-drive-dreams` - Cosmos Drive Dreams
- `dlss5-enhancer` - ComfyUI DLSS 5 Enhancer

### deferred

- `asset-harvester` - Asset Harvester
- `gamma-world` - Gamma-World
- `instant-nurec` - Instant NuRec
- `nurec-ga` - Omniverse NuRec GA (NGC nre-ga)
- `pixelumm` - PixelUMM

## Master table

| id | title | status | code license | weights license | commercial use | arm64 | gb10 | artifact | comfy shape | VRAM GB | disk GB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3dgrut | 3DGRUT (3DGRT + 3DGUT) | opt-in | Apache-2.0 | none | permitted | unknown | unverified | source-build | host-cli | 24 | 20 |
| 3dgrut-artifixer-fork | 3DGRUT-ArtiFixer (pinned fork) | opt-in | Apache-2.0 | none | permitted | unknown | unverified | source-build | host-cli | 24 | 20 |
| artifixer | ArtiFixer | opt-in | Apache-2.0 | NVIDIA Open Model License | permitted | published | unverified | container-image | host-cli | 40 | 120 |
| asset-harvester | Asset Harvester | deferred | Apache-2.0 | not read | unknown | unknown | unverified | source-build | none | not published | not published |
| cosmos-drive-dreams | Cosmos Drive Dreams | blocked-platform | Apache-2.0 | NVIDIA Open Model License (inherited from the Cosmos cards) | permitted | absent | unsupported | container-image | host-cli | 40 | 80 |
| dlss5-enhancer | ComfyUI DLSS 5 Enhancer | blocked-platform | MIT with a runtime carve-out for the bundled NVIDIA binaries | none redistributed; the neural models are NVIDIA NGX, ReShade, and RenoDX binaries under NVIDIA driver terms | unknown | absent | unsupported | custom-nodes | node-pack | 8 | 1 |
| dvlt | dvlt (Deja View) | blocked-license | Apache-2.0 for most files; VGGT-derived files carry the VGGT License | NVIDIA License, non-commercial research and evaluation use only | non-commercial | unknown | unverified | source-build | host-cli | 12 | 5 |
| gamma-world | Gamma-World | deferred | Apache-2.0 | not stated | unknown | unknown | unverified | source-build | none | not published | not published |
| gen3c | GEN3C | opt-in | Apache-2.0 | NVIDIA Open Model License | permitted | unknown | unverified | source-build | host-cli | 43 | 60 |
| infinicube | InfiniCube | blocked-license | Apache-2.0 | research and educational use only; commercial use of the weights is prohibited, and the terms bind to the Waymo Open Dataset ToS | non-commercial | unknown | unverified | source-build | none | 40 | 60 |
| instant-nurec | Instant NuRec | deferred | Apache-2.0 | not stated in the README | unknown | unknown | unverified | source-build | host-cli | 24 | 40 |
| luxdit | LuxDiT | blocked-license | NVIDIA OneWay Noncommercial License | Hugging Face card tagged license:other | non-commercial | unknown | unverified | source-build | none | 24 | 40 |
| lyra-1 | Project Lyra 1.x | opt-in | Apache-2.0 | NVIDIA Open Model License | permitted | unknown | unverified | source-build | host-cli | 80 | 100 |
| lyra-2 | Project Lyra 2.0 | blocked-license | Apache-2.0 | NVIDIA Internal Scientific Research and Development Model License | non-commercial | absent | unsupported | source-build | none | 80 | 120 |
| nurec-ga | Omniverse NuRec GA (NGC nre-ga) | deferred | Apache-2.0 (the open SDK at github.com/NVIDIA/NuRec) | not published; the container itself is under the NGC license, whose text is not reachable without an NGC session | unknown | partial | unverified | container-image | sidecar | 48 | 60 |
| pixelumm | PixelUMM | deferred | Apache-2.0 with file-specific exceptions | Hugging Face card tagged license:other, terms not read | unknown | unknown | unsupported | source-build | none | 240 | 200 |
| splatpainting | SplatPainting | blocked-license | Apache-2.0 except deps/gsplats, which is Inria and MPII licensed | none | non-commercial | unknown | unverified | source-build | none | 24 | 15 |
| vk-gaussian-splatting | Vulkan Gaussian Splatting viewer | opt-in | NVIDIA sample-code license (SPDX headers) | none | conditional | unknown | unverified | viewer | viewer | 8 | 3 |

## Tool cards

### `3dgrut` - 3DGRUT (3DGRT + 3DGUT)

- **Task**: Trains and renders ray-traced and unscented-transform Gaussian particle scenes from a capture.
- **Input**: COLMAP-style capture of one scene
- **Output**: trained scene plus rendered images, exported as PLY, USD, or NuRec
- **Upstream**: <https://github.com/nv-tlabs/3dgrut>
- **See also**: <https://docs.nvidia.com/nurec/>
- **Weights**: none
- **Artifact ref**: `https://github.com/nv-tlabs/3dgrut.git`
- **Gate notes**: No weights to license because the operator trains per scene. CUDA kernels compile at install; the repo default is CUDA 12.8 and CUDA 13 is experimental, and no aarch64 or GB10 build is documented. The 3DGUT raster path avoids the RT-core requirement the 3DGRT path carries.
- **Reopen**: n/a - this row is installable, but the first GB10 build has to be proven on the host.

**Sources**

- <https://github.com/nv-tlabs/3dgrut>

### `3dgrut-artifixer-fork` - 3DGRUT-ArtiFixer (pinned fork)

- **Task**: The ArtiFixer-maintained fork of 3DGRUT that the ArtiFixer app vendors as thirdparty/3DGRUT-ArtiFixer.
- **Input**: same capture as 3DGRUT
- **Output**: the scene build ArtiFixer consumes
- **Upstream**: <https://github.com/nv-tlabs/3DGRUT-ArtiFixer>
- **See also**: <https://github.com/nv-tlabs/3dgrut>
- **Weights**: none
- **Artifact ref**: `https://github.com/nv-tlabs/3DGRUT-ArtiFixer.git`
- **Gate notes**: This is the answer to the question the operator asked: 3DGRUT-ArtiFixer is a fork of 3dgrut pinned to one upstream commit, used as a vendored dependency, not a separate product. It warns that CUDA 11.8 is incompatible with Blackwell and compute capability 10.0 or newer, and offers only an experimental CUDA 12.8.1 path.
- **Reopen**: n/a - install it through the artifixer row rather than on its own.

**Sources**

- <https://github.com/nv-tlabs/3DGRUT-ArtiFixer>

### `artifixer` - ArtiFixer

- **Task**: Repairs and extends under-observed regions of a Gaussian-Neural scene with an autoregressive video-diffusion prior.
- **Input**: COLMAP capture, a trained 3DGUT scene, and a camera trajectory
- **Output**: corrected novel views for the reconstructed scene
- **Upstream**: <https://github.com/nv-tlabs/ArtiFixer>
- **See also**: <https://github.com/nv-tlabs/3DGRUT-ArtiFixer>, <https://research.nvidia.com/labs/sil/projects/artifixer/>
- **Weights**: `nvidia/ArtiFixer` / `artifixer-1.3b.pt` (6.72 GB, ungated); `nvidia/ArtiFixer` / `artifixer-14b.pt` (67.64 GB, ungated)
- **Artifact ref**: `ghcr.io/nv-tlabs/artifixer:cuda13-aarch64-ffmpeg-free-20261021-5b1bb939`
- **Gate notes**: Apache-2.0 code, ungated weights, and a published linux/arm64 CUDA 13 image; NVIDIA lists H100, GB200 and GB300 as tested, GB10 not among them.
- **Reopen**: n/a - this row is installable.

**Sources**

- <https://github.com/nv-tlabs/ArtiFixer>
- <https://github.com/nv-tlabs/ArtiFixer/blob/main/docs/setup.md>

### `asset-harvester` - Asset Harvester

- **Task**: Generates simulatable autonomous-vehicle assets for simulation.
- **Input**: an asset request
- **Output**: a simulatable AV asset
- **Upstream**: <https://github.com/NVIDIA/asset-harvester>
- **See also**: none
- **Weights**: none
- **Artifact ref**: `https://github.com/NVIDIA/asset-harvester.git`
- **Gate notes**: The output domain is autonomous-vehicle assets for simulation, which no lane in this stack serves, and the weight license and GPU class are unpublished. Recorded so the next evaluation does not start from zero.
- **Reopen**: A published weight license plus a GPU class that fits one Spark, and a use for AV assets in a media lane.

**Sources**

- <https://github.com/NVIDIA/asset-harvester>

### `cosmos-drive-dreams` - Cosmos Drive Dreams

- **Task**: Generates synthetic multi-view autonomous-vehicle video and LiDAR from HD map, bounding box, and LiDAR conditions.
- **Input**: HD map, bounding boxes, and LiDAR conditions
- **Output**: multi-view synthetic AV video plus LiDAR
- **Upstream**: <https://github.com/nv-tlabs/Cosmos-Drive-Dreams>
- **See also**: <https://huggingface.co/nvidia/Cosmos-Transfer1-7B-Sample-AV>
- **Weights**: `nvidia/Cosmos-Transfer1-7B-Sample-AV` / `base_model.pt` (28.95 GB, gated)
- **Artifact ref**: `nvcr.io/nvidia/cosmos`
- **Gate notes**: The license is workable but the Cosmos 1 upstream it needs ships x86_64 NGC images and prebuilt CUDA wheels, so nothing resolves inside this aarch64 image. Its input domain is autonomous-vehicle sensor conditions, which no lane in this stack produces.
- **Reopen**: Upstream Cosmos publishes linux_aarch64 wheels or an arm64 container that runs on GB10.

**Sources**

- <https://github.com/nv-tlabs/Cosmos-Drive-Dreams>

### `dlss5-enhancer` - ComfyUI DLSS 5 Enhancer

- **Task**: Pushes RGBA frames and estimated motion vectors through the DLSS 5 neural renderer and returns reconstructed frames.
- **Input**: RGBA8 image or video plus motion vectors
- **Output**: reconstructed and upscaled frames at 1.5x to 3x
- **Upstream**: <https://github.com/Blueforcer/ComfyUI-DLSS5-Enhancer>
- **See also**: none
- **Weights**: none
- **Artifact ref**: `https://github.com/Blueforcer/ComfyUI-DLSS5-Enhancer`
- **Gate notes**: The pack is a client of a native D3D12 worker process that hosts ReShade and must be named nvngx.dll, installed by a Windows embedded-python path against a GeForce driver. There is no Linux path at all, so it cannot run in this container. This is the same NGX wall that already declines ComfyUI_Nvidia_VFX_Nodes.
- **Reopen**: NVIDIA ships a linux_aarch64 NGX runtime the pack can drive, which the VFX nodes row also waits on.

**Sources**

- <https://github.com/Blueforcer/ComfyUI-DLSS5-Enhancer>

### `dvlt` - dvlt (Deja View)

- **Task**: Reconstructs multi-view geometry as pointmaps, depth, and camera poses with a looping transformer.
- **Input**: multi-view images
- **Output**: pointmaps, depth, and camera poses
- **Upstream**: <https://github.com/nv-tlabs/dvlt>
- **See also**: <https://huggingface.co/nvidia/dvlt>
- **Weights**: `nvidia/dvlt` / `model.safetensors` (0.47 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/dvlt.git`
- **Gate notes**: Hardware-wise this is the best fit in the tier: 0.5 GB of weights and a documented single-GPU path, which would serve the splat capture front end directly. The weight license and the VGGT-derived code terms are both non-commercial, which is the only thing refusing it. The conda pins are torch 2.5.1 with CUDA 12.4.
- **Reopen**: The weights are relicensed for commercial use, or a permissive checkpoint of the same size appears.

**Sources**

- <https://github.com/nv-tlabs/dvlt>

### `gamma-world` - Gamma-World

- **Task**: Rolls out synchronized future observations and actions for several agents in one interactive world model.
- **Input**: observations and actions from N agents
- **Output**: future multi-agent video rollouts
- **Upstream**: <https://github.com/nv-tlabs/Gamma-World>
- **See also**: none
- **Weights**: none
- **Artifact ref**: `https://github.com/nv-tlabs/Gamma-World.git`
- **Gate notes**: The repository documents converting a released checkpoint to DCP but never says where the checkpoint is hosted, publishes no VRAM envelope, and states no weight license. There is nothing to size a single Spark against.
- **Reopen**: Upstream names the weight host, states a weight license, and publishes a memory envelope.

**Sources**

- <https://github.com/nv-tlabs/Gamma-World>

### `gen3c` - GEN3C

- **Task**: Generates a world-consistent video from one or more images plus a camera trajectory.
- **Input**: image or images plus a camera trajectory
- **Output**: a camera-controlled video
- **Upstream**: <https://github.com/nv-tlabs/GEN3C>
- **See also**: <https://huggingface.co/nvidia/GEN3C-Cosmos-7B>
- **Weights**: `nvidia/GEN3C-Cosmos-7B` / `model.pt` (28.9 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/GEN3C.git`
- **Gate notes**: The only generative item here whose weights permit commercial use outright. The README reports about 43 GB peak with full model offload and states the code was tested only on H100 and A100. It needs CUDA_HOME set and custom kernels built, and the download script wants an HF token.
- **Reopen**: n/a - installable, with an offload-dominated runtime on GB10 until someone reports a run there.

**Sources**

- <https://github.com/nv-tlabs/GEN3C>

### `infinicube` - InfiniCube

- **Task**: Generates an unbounded voxel world with video and dynamic Gaussians for driving scenes.
- **Input**: a driving-scene prompt and a pose
- **Output**: voxel world, video, and dynamic 3D Gaussians
- **Upstream**: <https://github.com/nv-tlabs/InfiniCube>
- **See also**: <https://huggingface.co/yifanlu/InfiniCube-checkpoints>
- **Weights**: `yifanlu/InfiniCube-checkpoints` / tree: `checkpoints/` (82.3 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/InfiniCube.git`
- **Gate notes**: The checkpoints forbid any commercial use and are hosted on a personal Hugging Face account rather than the NVIDIA org, on top of a Waymo dataset ToS bind. The Wan 14B stage is about 20 minutes per 93-frame 480p clip on an A100.
- **Reopen**: Weights relicensed for commercial use and hosted by the NVIDIA org.

**Sources**

- <https://github.com/nv-tlabs/InfiniCube>

### `instant-nurec` - Instant NuRec

- **Task**: Reconstructs a simulatable multi-camera driving world in one feed-forward pass, no per-scene training.
- **Input**: multi-camera driving log
- **Output**: a Gaussian scene with static and dynamic layers plus a sky cubemap
- **Upstream**: <https://github.com/NVIDIA/instant-nurec>
- **See also**: <https://huggingface.co/nvidia/instant-nurec>
- **Weights**: `nvidia/instant-nurec` / `instant_nurec.pt` (0.84 GB, ungated)
- **Artifact ref**: `https://github.com/NVIDIA/instant-nurec.git`
- **Gate notes**: Feed-forward reconstruction is the right shape for a single GPU, but the weights license is not stated in the repository and the uv lockfile pins are the aarch64 risk. Its input domain is driving logs, which no lane in this stack produces.
- **Reopen**: Re-test when the model card states a weight license that permits product use and a linux_aarch64 dependency set resolves.

**Sources**

- <https://github.com/NVIDIA/instant-nurec>

### `luxdit` - LuxDiT

- **Task**: Estimates image-based lighting from a single photo or video with a video diffusion transformer.
- **Input**: one image or a video
- **Output**: an environment light estimate for relighting
- **Upstream**: <https://github.com/nv-tlabs/LuxDiT>
- **See also**: <https://huggingface.co/nvidia/LuxDiT>
- **Weights**: `nvidia/LuxDiT` / tree: `luxdit_image/` (11.74 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/LuxDiT.git`
- **Gate notes**: The repository ships the NVIDIA OneWay Noncommercial License, so the code itself, not only the weights, bars use in a product container. This is the relighting capability the 3D lane does not have, which is why the card is worth keeping.
- **Reopen**: NVIDIA relicense the code away from the OneWay Noncommercial terms.

**Sources**

- <https://github.com/nv-tlabs/LuxDiT>

### `lyra-1` - Project Lyra 1.x

- **Task**: Generates a camera-controlled walkthrough video of a 3D-consistent world from one image.
- **Input**: one image plus a camera trajectory
- **Output**: a walkthrough fly-through video
- **Upstream**: <https://github.com/nv-tlabs/lyra>
- **See also**: <https://huggingface.co/nvidia/Lyra>
- **Weights**: `nvidia/Lyra` / `lyra_static.pt` (0.1 GB, ungated); `nvidia/Lyra` / `lyra_dynamic.pt` (0.1 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/lyra.git`
- **Gate notes**: nv-tlabs/lyra is the canonical repository; nv-tlabs/Project-Lyra is only the GitHub Pages site (index.html, styles, assets) and holds no code. The code is Apache-2.0 and the weights carry the NVIDIA Open Model License, which permits commercial use. The README states Lyra was tested only on H100 and A100, needs the Cosmos Predict 1 backbone pulled separately, and builds Triton and custom kernels.
- **Reopen**: n/a - installable, but budget a long per-clip run and prove it on GB10 first.

**Sources**

- <https://github.com/nv-tlabs/lyra/blob/main/README.md>
- <https://github.com/nv-tlabs/Project-Lyra>

### `lyra-2` - Project Lyra 2.0

- **Task**: Builds an explorable long-horizon 3D-consistent world from one image with a Wan-based video DiT.
- **Input**: one image plus a camera trajectory
- **Output**: a walkthrough video plus reconstructed Gaussian splats
- **Upstream**: <https://github.com/nv-tlabs/lyra>
- **See also**: <https://huggingface.co/nvidia/Lyra-2.0>
- **Weights**: `nvidia/Lyra-2.0` / tree: `checkpoints/` (97 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/lyra.git`
- **Gate notes**: Kept in the tier as a card so the verdict stays readable, not as an install path. The weight terms bar distribution, deployment, and production use, which running it inside a product container is. It is also about 98 GB, reported out of memory on a 48 GB card even with every offload flag, and built against CUDA 12.8 with torch 2.7.1 and source-built flash-attn, against this image's CUDA 13.0 with torch 2.14.1. Its refuse token stays in config/model-manifest.yaml.
- **Reopen**: NVIDIA relicenses the Lyra 2.0 checkpoints so deployment and production use are permitted.

**Sources**

- <https://huggingface.co/nvidia/Lyra-2.0>
- <https://github.com/nv-tlabs/lyra>

### `nurec-ga` - Omniverse NuRec GA (NGC nre-ga)

- **Task**: Trains and serves Gaussian-Neural 3DGRT and 3DGUT scenes over gRPC and renders novel views from them.
- **Input**: real-world sensor logs or a trained scene
- **Output**: rendered novel views and a USD scene
- **Upstream**: <https://catalog.ngc.nvidia.com/orgs/nvidia/nre/containers/nre-ga>
- **See also**: <https://docs.nvidia.com/nurec/release-notes/index.html>, <https://docs.nvidia.com/nurec/basics/hardware.html>
- **Weights**: none
- **Artifact ref**: `nvcr.io/nvidia/nre/nurec-ga`
- **Gate notes**: The catalog row the operator linked is the pre-rename name: NVIDIA renamed nre/nre-ga and nre/nre-tools-ga to nre/nurec-ga and nre/nurec-tools-ga. NVIDIA states general Linux aarch64 is not a supported user platform and that Grace-Blackwell enablement reaches you only through the -arm64 or -multiarch tags, which build as non-gating nightly or on-demand jobs and may not exist for a given release. Container security scanning covers x86_64 only, the floor is more than 24 GB with 48 GB recommended on an R580 driver or newer, and the container license text plus any NGC entitlement requirement could not be confirmed from a public page.
- **Reopen**: Re-test when NVIDIA publishes a gated -arm64 or -multiarch tag for a release-branch build and states the container license and entitlement terms in public.

**Sources**

- <https://docs.nvidia.com/nurec/release-notes/index.html>
- <https://docs.nvidia.com/nurec/basics/hardware.html>
- <https://docs.nvidia.com/nurec/basics/software.html>

### `pixelumm` - PixelUMM

- **Task**: Encoder-free unified image and video understanding and generation in one model.
- **Input**: text, image, or video
- **Output**: generated image or video
- **Upstream**: <https://github.com/nv-tlabs/PixelUMM>
- **See also**: <https://huggingface.co/nvidia/PixelUMM>
- **Weights**: `nvidia/PixelUMM` / shards: `S8-F*-R*/*.distcp` (121.6 GB, ungated); `Qwen/Qwen3-8B` / shards: `model-0000*-of-00005.safetensors` (16.4 GB, ungated)
- **Artifact ref**: `https://github.com/nv-tlabs/PixelUMM.git`
- **Gate notes**: The released weights are 121.6 GB of distributed checkpoints and the documented training path asks for seven GPUs of 48 GiB or more. That is a cluster, and this stack is one Spark. The weight terms on the card are license:other and were not readable as a permission for product use.
- **Reopen**: A quantized single-GPU inference checkpoint with a readable permissive weight license.

**Sources**

- <https://github.com/nv-tlabs/PixelUMM>

### `splatpainting` - SplatPainting

- **Task**: Paints and edits a Gaussian Splat scene interactively with a brush.
- **Input**: a Gaussian scene and brush strokes
- **Output**: an edited Gaussian scene
- **Upstream**: <https://github.com/nv-tlabs/SplatPainting>
- **See also**: none
- **Weights**: none
- **Artifact ref**: `https://github.com/nv-tlabs/SplatPainting.git`
- **Gate notes**: The repository is Apache-2.0 except the vendored deps/gsplats tree, which carries Inria and MPII research licenses, so a build that links it is not clean for a product image. The editing surface is genuinely useful for the 3D lane, which is why it stays as a card.
- **Reopen**: The gsplat dependency is replaced or relicensed so a build needs no research-licensed tree.

**Sources**

- <https://github.com/nv-tlabs/SplatPainting>

### `vk-gaussian-splatting` - Vulkan Gaussian Splatting viewer

- **Task**: Renders Gaussian Splat and 3DGRT particle scenes natively over Vulkan.
- **Input**: a particle scene file
- **Output**: a rendered view of the scene
- **Upstream**: <https://github.com/nvpro-samples/vk_gaussian_splatting>
- **See also**: <https://github.com/nvpro-samples/vk_wsi>
- **Weights**: none
- **Artifact ref**: `https://github.com/nvpro-samples/vk_gaussian_splatting.git`
- **Gate notes**: Being Vulkan it sidesteps the CUDA architecture and aarch64 wheel problems that block the rest of the tier, and it is the only viewer here. It renders, it generates nothing, and it needs a Vulkan-capable GB10 driver path. It stays a host-side viewer beside Comfy rather than an image dependency, on the same rule that keeps SuperSplat out of the image.
- **Reopen**: n/a - opt-in as a host viewer.

**Sources**

- <https://github.com/nvpro-samples/vk_gaussian_splatting>
