---
title: Declined and research integrations
description: "Third-party models and node packs evaluated for the Spark stack: the NVIDIA candidates allowed for local experimentation, the ones declined, the license on each, what you may publish from them, and the tool-by-tool verdict behind every row of the opt-in nvidia-lab tier."
tags: [models, safety, licenses, video, 3d, integrations]
---

# Declined and research integrations

**What's on this page**

- **The four gates** - what a candidate has to clear, and which gate decided each verdict
- **Research lane** - 11 NVIDIA models you may download and run locally to experiment, each with its license and its permitted use
- **Declined** - the candidates that cannot run here, cannot be licensed here, or have no stated license at all
- **Dead ends** - candidates that do not exist or have nothing to run, so you do not spend a day on them
- **Enforcement** - how the catalog keeps the refuse list off disk and the research lane out of your downloads
- **Reopening** - how to run an evaluation again when a vendor ships new artifacts
- **Per item** - what it is, the blocking fact, what would reopen it, what to use instead
- **NVIDIA lab tier** - the tool-by-tool verdicts on the upstream repos, container images, CLIs, install shapes, and lab graphs the opt-in tier carries, each with the catalog row that refuses it an install path

**What this enables**

- Read one page instead of re-researching a candidate that was already turned, with the vendor source for each verdict
- Tell a license wall from a hardware wall, which decides whether waiting helps
- Know, before a 90 GB download, whether you are allowed to publish what the model prints
- Confirm the catalog keeps refused weights off `${MODELS_DIR}`, and keeps the research lane out of `download-models` without you auditing the list by hand
- Confirm no `nvidia-lab` row reaches the image, the manifest, or Compose, and that an artifact lands only after the confirm, the headroom preflight, and the occupancy check
- Re-test a declined candidate against the four gates when a vendor ships new artifacts

This stack is a single-DGX-Spark (GB10, 128 GB unified memory) local studio. A
candidate has to clear four gates at once:

| Gate | Question |
| --- | --- |
| **G1 license** | May its weights run inside a product container, and may the outputs be used commercially? |
| **G2 artifact** | Is there a `linux_aarch64` artifact that installs on GB10? |
| **G3 envelope** | Do its memory and disk fit beside the pinned catalog on one 128 GB box? |
| **G4 lane** | Does its modality actually serve an image, video, or audio lane? |

Any single gate is enough to keep a model out of the **promoted catalog**. A
non-commercial license is not, by itself, a reason to stop you experimenting on
your own box - which is why NVIDIA research models now have a research lane
below instead of a flat refusal. What a non-commercial license does bar is
publishing the result for money.

The findings below were taken from the vendor's own model cards, release indexes, and issue trackers.

**Not legal advice.** This page encodes the stack's **download and workflow
policy**. It is not legal advice. Read each model card and license yourself
before you monetize anything. Several licenses below are quoted from the
vendor's own text; where they conflict, the vendor's text wins.

Two taxonomies live on this page and they answer different questions. A **model weight** you want to download is governed by the research lane below, which is scoped to the weights disclosed in `config/model-manifest.yaml` under `research:` - a disclosure list, not a download list. An **external tool** - an upstream repo, a container image, a CLI, its install shape, and the lab graph that drives it - is governed by the `## NVIDIA lab tier: tool-by-tool verdicts` section further down, which is scoped to the rows in `custom_nodes/ez_nvidia_lab/catalog.json` and the `bazelisk run //:manage -- nvidia-lab` verb. A candidate can sit in both: the research lane says what you may run locally on your own box, the tier row says whether this stack will install and drive it for you.

## Summary

This table is the weights taxonomy: it records which gate decided each model weight's verdict. The tool rows have their own table under `## NVIDIA lab tier: tool-by-tool verdicts`.

| Candidate | Verdict | Blocking gate | Reopen when |
| --- | --- | --- | --- |
| 3DGRUT, ArtiFixer, Fixer, Lyra-1, Lyra-2.0, PixelUMM, GEN3C, LuxDiT, InfiniCube, Cosmos-Drive-Dreams, DVLT | **Research lane** | none for local experimentation | - |
| ComfyUI\_Nvidia\_VFX\_Nodes | Declined | G2: no `linux_aarch64` wheel for `nvidia-vfx` | NVIDIA publishes an aarch64 wheel that works on GB10 |
| ComfyUI-DLSS5-Enhancer | Declined | G2: Windows x86 binaries only | The runtime gains a Linux Arm path |
| NGC `nre-ga` (Omniverse NuRec) | Declined | G2/G4: `amd64`-only image, lidar input | The `nurec-ga` arm64 tag proves out and a use appears |
| PixelUMM, InfiniCube, GEN3C, Cosmos-Drive-Dreams | Research lane, **blocked on this box** | G2 or G3 | An aarch64 build or a smaller footprint |
| InstantSplat, LongSplat, SplatPainting, nvdiffrec, nvdiffrast | Declined | G1: non-commercial code license | NVIDIA relicenses the source |
| Gamma-World, TokenGS | Declined | G1: the checkpoint states no license at all | The owner declares a license |
| Kaolin, instant-nurec | Declined | G4: no image, video, or audio lane of their own | A lane appears |
| Nous Research Arete-27B | Declined | G4: text-only, no GGUF, no media lane | A CPU-runnable GGUF and a use beyond the pinned writer |
| Project-Lyra, GEN3C-D | Dead end | nothing to run / does not exist | never |

## Research lane (opt-in, experimentation only)

These eleven are NVIDIA research models. They are listed in
`config/model-manifest.yaml` under `research:`, which is a **disclosure list,
not a download list**. Three things hold by construction:

1. `bazelisk run //:manage -- download-models` never fetches any of them. Only
   `packs:` rows feed downloads.
2. Nothing in the lane is keep-set protected, so `reap-models` treats a research
   tier dir as ordinary disk.
3. Nothing in the lane is pinned in a promoted workflow. The promoted catalog
   stays Klein 4B stills, Wan 2.2 silent motion, LTX-2.5 AV, TRELLIS.2, and
   TripoSplat.

You download them yourself, out of band, in your own container or venv.

### What you may publish

| Model | Weights license | Sell it, put it on monetized YouTube, ship it to a client? |
| --- | --- | --- |
| 3DGRUT, Fixer, Lyra-1, GEN3C | Apache-2.0, or NVIDIA Open Model License | **Yes.** The cards state commercial use is allowed. Note the stack still does not promote these. |
| ArtiFixer, PixelUMM, LuxDiT, DVLT | NVIDIA One-Way Noncommercial (DVLT's checkpoint is excluded from its repo's Apache grant) | **No.** Research and evaluation only. |
| InfiniCube | Waymo Dataset License Agreement for Non-Commercial Use | **No.** The card states commercial use of the weights is prohibited. |
| Lyra-2.0 | NVIDIA Internal Scientific Research and Development Model License | **No, and it is worse than non-commercial.** See below. |
| Cosmos-Drive-Dreams | Apache-2.0 code; the Cosmos checkpoints carry their own NVIDIA terms | **Confirm the Cosmos card first.** Do not assume. |

The clearest statement of what "non-commercial" buys you is the LuxDiT license,
section 3.3, quoted verbatim:

> The Work and any derivative works thereof only may be used or intended for use
> non-commercially. Notwithstanding the foregoing, NVIDIA Corporation and its
> affiliates may use the Work and any derivative works commercially. As used
> herein, "non-commercially" means for research or evaluation purposes only.

Note the asymmetry: NVIDIA may use it commercially and you may not.

### Lyra-2.0 is the strictest license in the set

Moving Lyra-2.0 off the refuse list relaxed one thing and did not touch the
others. The original blocking facts still stand, quoted from the vendor's own
terms: the model and any derivative "may not be distributed, deployed,
sublicensed, publicly displayed, publicly performed", and you "may not use the
Model or a Derivative Model in a production environment or for the purpose of
generating works for sale or distribution". The repository code is Apache-2.0,
which does not change the weight terms.

Read the relaxation precisely: the disk wizard no longer flags a `Lyra-2.0`
checkpoint as a banned weight, so **this page is now the only thing standing
between you and shipping Lyra-2.0 output commercially.** Running it locally to
see how a video-diffusion world model behaves is inside the license. Putting the
result in client work is outside it.

The other facts that kept it declined before also still apply: the checkpoint set
is roughly 98 GB, of which about 97 GB is inference weights including a 68 GB
32-shard DCP DiT; the maintainer reports a 48 GB card out-of-memory with every
offload flag on; install is a recursive clone under conda with Python 3.10, CUDA
12.8, torch 2.7.1, and source builds of `flash-attn` and TransformerEngine,
against a stack that is CUDA 13.0 with torch 2.14.1.

If you want Lyra and a license you can publish under, **Lyra-1 is the one.** Its
models are under the NVIDIA Open Model License, which permits commercial use.

### The lane, row by row

| Model | Upstream | Weights | GB10 | Worth knowing |
| --- | --- | --- | --- | --- |
| 3DGRUT | `nv-tlabs/3dgrut` | none, per-scene training | plausible | The only clean pass in the whole set. Apache-2.0, no weights to license, arm64 Docker build offered, CUDA 12.8 covers Blackwell. The 3DGUT raster path needs no RT cores; the 3DGRT ray-traced path wants them. |
| ArtiFixer | `nv-tlabs/ArtiFixer` | `nvidia/ArtiFixer` | plausible | Repairs artifacts in renders of a 3D Gaussian reconstruction. Ships a `cuda13-aarch64` image described for GB200/GB300, never measured on GB10. 1.3B is 6.72 GB; 14B is 67.64 GB. Scene prep wants COLMAP + MoGe + 3DGRUT plus a ~60 GB captioner; budget 160 GB. |
| Fixer | `nv-tlabs/Fixer` | `nvidia/Fixer` | marginal | Cleans splat and reconstruction renders. License-clean. Size and aarch64 build unverified. |
| Lyra-1 | `nv-tlabs/lyra` | `nvidia/Lyra` | marginal | Commercially clean. Python 3.10, source builds of Apex, transformer-engine, mamba; about 43 GB peak VRAM with full offload; tested on H100/A100 only. |
| Lyra-2.0 | `nv-tlabs/lyra` | `nvidia/Lyra-2.0` | marginal | See the section above. |
| PixelUMM | `nv-tlabs/PixelUMM` | `nvidia/PixelUMM` | blocked | Unified image+video understand and generate. **One** checkpoint dir is 30.41 GB; the repo holds four (`S8-F18-R01`, `S8-F19-R03`, `S8-F21-R02`, `S8-F22-R05`) at 30.41 GB each - `S8-F18-R01` measures 30.39 - so **121.63 GB across 480 `.distcp` shards** is the footprint the tier row budgets. Needs a CUDA 13.0 aarch64 PyTorch wheel that does not exist (pytorch/pytorch#160162), and its FlashAttention arch list stops at 100. One source file stays CC BY-NC 4.0. |
| GEN3C | `nv-tlabs/GEN3C` | `nvidia/GEN3C-Cosmos-7B` | blocked | License-clean, but pins torch 2.6 on an NGC 24.10 base and source-builds apex; zero aarch64 hits across 614 tracked files; about 220 GB disk. |
| LuxDiT | `nv-tlabs/LuxDiT` | `nvidia/LuxDiT` | marginal | HDR environment-map lighting from RGB. `nvidia/LuxDiT` measures **11.74 GB for `luxdit_image/`** and 11.74 GB for `luxdit_video/`, plus a negligible `hdr_merge_mlp/` - 23.49 GB for the repo; the tier row names the 11.74 GB image tree. No CUDA extension and no torch pin, so it is the least blocked of the non-commercial set. Emits `.exr` envmaps - a relighting stage, not a finished image. A community node exists (`jzhang-POP/ComfyUI-LuxDiT`, MIT, 1 star). |
| InfiniCube | `nv-tlabs/InfiniCube` | `yifanlu/InfiniCube-checkpoints` | blocked | Installs literal `linux_x86_64` cu121 `gsplat` and `fvdb` wheels with no aarch64 twin. Weights are a Waymo derivative. `yifanlu/InfiniCube-checkpoints` `checkpoints/` measures **82.3 GB**; the 76.64 GB figure this page carried covered no narrower scope, so the measured number stands. |
| Cosmos-Drive-Dreams | `nv-tlabs/Cosmos-Drive-Dreams` | `nvidia/Cosmos-Drive-Dreams` (gated) | blocked | Asks for about 300 GB free; models alone are 66 + 44 + 67 GB and the companion dataset is near 3 TB. Driving-domain input, so thin on G4 as well. That repo returns **HTTP 401** to an anonymous read, so every figure carried for it here is unverified; the tier row instead names the public `nvidia/Cosmos-Transfer1-7B-Sample-AV` (HTTP 200, `gated: "auto"`), whose `base_model.pt` measures 28.95 GB. |
| DVLT | `nv-tlabs/dvlt` | `nvidia/dvlt` | blocked | "Deja View": recurrent multi-view reconstruction emitting rays, depth, confidence, poses. A geometry front-end, not a renderer. Conda pins pytorch 2.5.1 / cuda 12.4. |

### Running a research model without wrecking the stack

**Occupancy.** These do not run inside the stack's image and get no `manage.sh`
verb. Run one at a time, in your own container or venv, **with Compose down**.
The stack holds a one-heavy-GPU-job rule so a writer never competes with a GPU
tenant for GB10 memory, and a 67 GB DiT is exactly the tenant that rule exists
to keep out. Full wording:
[Host sidecars overview](../studio-sidecars.md#occupancy-rule).

Every GB10 verdict above is an upstream hardware claim for **other** chips -
H100, A100, GB200, GB300. None of these has been measured on GB10. "plausible"
means nothing blocked it in principle, and is not a promise that it starts.

## Declined on hardware or size

**ComfyUI-DLSS5-Enhancer.** Real, MIT, 327 stars, and a genuine community
ComfyUI node - the only ComfyUI-native pack in this entire evaluation. It is
blocked on hardware, not on policy: the worker, the ReShade carrier, and the
RenoDX add-on are all Windows x86 binaries, the node gates on `RTX` appearing in
the `nvidia-smi` name (GB10 does not carry it), and RTX 20 cards are refused
outright. It ships no weights, so there is nothing for the refuse list to do;
the NGX runtime is a third-party proprietary build the project declines to
redistribute. Run it on a Windows RTX box if you want it.

**ComfyUI\_Nvidia\_VFX\_Nodes.** Three nodes over NVIDIA's NGX runtime:
`RTXVideoSuperResolution`, `RTXTrueHDR`, `RTXVideoFrameGeneration`. It installs
with `python -m pip install -U --no-build-isolation nvidia-vfx --index-url
https://pypi.nvidia.com`, and that index publishes only `manylinux x86_64`,
`win_amd64`, and `win_arm64` wheels. There is no `linux_aarch64` wheel, so the
install cannot resolve inside this image. The README's "RTX Spark is supported"
line refers to the Windows-on-Arm part that `win_arm64` serves; it is not
evidence for DGX Spark. Two further problems on Blackwell Linux: the
super-resolution node returns an all-black tensor with no exception because the
bundled NGX cubins lack that architecture, and the runtime loads its own cuDNN
with `RTLD_GLOBAL` and rewrites `LD_LIBRARY_PATH`, which aborts later cuDNN
consumers such as the pose models. Both are open upstream. **Use instead** the
stack's own upscaling and format nodes; run HDR and interpolation on an x86
workstation and bring the finished file back in.

**NGC `nre-ga`.** Note the name first: this is Omniverse **NuRec** (Neural
Reconstruction), not "Neural Rendering Engine" and not "Gaussian Anything" -
that last is an unrelated non-NVIDIA project. Source is open at `NVIDIA/NuRec`
under Apache-2.0, and 26.10 is the last release published on NGC, with images
renamed `nre-ga` to `nurec-ga`. `nre-ga:latest` is 14.29 GB compressed and its
manifest is single-arch `linux/amd64` on CUDA 12.8 with zero arm64 tags. The
`nurec-ga` family that gained DGX Spark enablement returned `UNAUTHORIZED` to
anonymous pull, so it needs an NGC account to inspect. Beyond the architecture,
its input is recorded camera plus lidar NCore data, which no lane of a studio
consumes.

**PixelUMM, InfiniCube, GEN3C, Cosmos-Drive-Dreams** are in the research lane
for their license and **blocked** on this box for hardware or disk. The row
table says which.

## Declined on license

These are NVIDIA and genuinely useful, but the **code** license is
non-commercial, so they cannot sit in a product image at all - which is a
stricter position than the research lane takes about weights.

- `NVlabs/InstantSplat` - Apache-2.0 plus a CC BY-NC third-party component.
- `NVlabs/LongSplat` - non-commercial with additional PROHIBITED clauses.
- `nv-tlabs/SplatPainting` - Apache-2.0 plus a non-commercial clause.
- `NVlabs/nvdiffrec` and `NVlabs/nvdiffrast` - the NVIDIA Source Code License,
  non-commercial. Both are already named elsewhere in this repo, and
  `docker/Dockerfile` deliberately stays free of nvdiffrast.

## Declined: the checkpoint states no license at all

Fail closed here. An undeclared weight is not a permissive one.

- **Gamma-World** - the code is Apache-2.0 and the engineering is interesting
  (multi-agent world model, 13.6 GB, a `cu130` extra already first-class), but
  the weights sit on the **personal** account `chijw/Gamma-World` and the
  Hugging Face API returns no license tag at all. You cannot assume commercial
  use, and you cannot assume the base `nvidia/Cosmos-Predict2.5-2B` terms were
  passed through.
- **TokenGS** - feed-forward 3DGS, code Apache-2.0, weights on personal
  `jiaweir/tokengs` with no license declared.

Re-test either one the day the owner puts a license on the checkpoint.

## Declined on lane

- **Kaolin** (`NVIDIAGameWorks/kaolin`) - Apache-2.0 and it does build for
  aarch64 on conda-forge, but it pins `pytorch >=2.12.1,<2.13` against our
  2.14.1, and it is a kernel library: it adds no modality of its own.
- **`NVIDIA/instant-nurec`** - Apache-2.0 code, weights under the NVIDIA Open
  Model License and "ready for commercial/non-commercial use", but the input is
  an NCore V4 multi-camera AV driving log. Nothing in a studio produces one.
- **Nous Research Arete-27B** - a 27.4B BF16 text fine-tune, about 54.7 GB,
  Apache-2.0 and ungated. Its image and video encoder is inherited and frozen,
  so it reads media and produces none, which leaves it no lane here. The local
  model lane runs GGUF on CPU so a writer never competes with a GPU tenant, and
  Arete-27B has no official GGUF at all. **Use instead** the pinned Qwen3-4B
  GGUF for Prompt Enhance, the opt-in 35B pack for the desk writer, and
  Qwen2.5-VL for captioning - all three arrive with
  `bazelisk run //:manage -- download-models`.

## Dead ends

Recorded so nobody spends a day looking for them.

- **`nv-tlabs/Project-Lyra`** is not code. It is the GitHub Pages site for
  Lyra 2.0: `index.html`, `styles.css`, `scripts.js`, `assets/`, `bibtex.tex`,
  and no LICENSE file. `NVlabs/Project-Lyra` is a 404. There is nothing to run.
  Use `nv-tlabs/lyra`.
- **`GEN3C-D` does not exist.** `gh api repos/nv-tlabs/GEN3C-D` returns 404 and
  an org search yields only `GEN3C` and `GEN3C_website`. The "-D" you saw is a
  figure label in a third-party paper.
- **404 and not real:** `NVlabs/dvlt`, `nv-tlabs/nvdiffrender`,
  `NVlabs/Kaolin`, `NVIDIA/kaolin`, `NVlabs/SIFT`, `nv-tlabs/FlashGems`,
  `nv-tlabs/SplatPose`, `nv-tlabs/splat-anything`, `NVlabs/SemanticGaussians`,
  `NVlabs/4DGaussians-NVIDIA`.
- **No official ComfyUI node exists for any NVIDIA candidate in this set.**
  Code search for `comfy` inside `nv-tlabs/lyra` returns zero hits, and
  ComfyUI+GEN3C, ComfyUI+InfiniCube, and ComfyUI+ArtiFixer all return none. The
  only third-party wrappers found are `jzhang-POP/ComfyUI-LuxDiT` and
  `Nynxz/ComfyUI-HyNomas`, the latter a PixelUMM fine-tune whose weights stay
  under the same NVIDIA One-Way Noncommercial License.

## What to use instead

Stills come from Klein and motion from Wan 2.2 and LTX-2.5, all in the pinned
catalog. For 3D, the native TRELLIS lane covers image-to-3D and the opt-in
`triposplat` pack covers splats, with SuperSplat as a host viewer. See
[TRELLIS and 3D](../learn/pipeline.md), [Splat sidecar](../splat-sidecar.md), and
[Models and cache](../models-and-cache.md).

## NVIDIA lab tier: tool-by-tool verdicts

Where the research lane above governs the weights disclosed in the manifest, this section governs the tools: upstream repos, container images, CLIs, install shapes, and the lab graphs that drive them.

The NVIDIA candidates below are no longer verdicts in prose only. Each carries a
row in the opt-in **nvidia-lab** tier catalog at
`custom_nodes/ez_nvidia_lab/catalog.json`, and that row is what refuses it an
install path. This page carries the verdict and the evidence;
[NVIDIA lab](../nvidia-lab.md) carries the catalog, the footprints, and the
verbs that install the rows that cleared the gates. The verdict words below
match the tier statuses: **Declined** is a refused row (`blocked-license` or
`blocked-platform`), **Deferred** is a row parked on a fact nobody has
published yet.

The two non-NVIDIA rows in this table, Nous Research Arete-27B and ComfyUI\_Nvidia\_VFX\_Nodes, carry no catalog row and are declined outright; the tier catalog covers the NVIDIA candidates. `Fixer` has a row in the research-lane table above but no tier row: the tier has never evaluated it as a tool.

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

### NVIDIA Project Lyra

Lyra is NVIDIA's open generative 3D world model line, and its two releases do
not carry the same weight terms. `nv-tlabs/lyra` is the canonical repository for
both; `nv-tlabs/Project-Lyra` is only the GitHub Pages site - an `index.html`,
styles, and assets - and holds no code. The tier carries each release as its own
row, so the installable half is not refused with the half that is.

#### Lyra 1.x is installable through the tier

Lyra 1.x generates a camera-controlled walkthrough video of a 3D-consistent
world from one image. The code is Apache-2.0 and the `nvidia/Lyra` weights carry
the NVIDIA Open Model License, which permits commercial use, so the row is
**opt-in** and installs with `bazelisk run //:manage -- nvidia-lab install lyra-1`.

The cost is the run, not the license. The README reports testing on H100 and
A100 only, the row budgets 80 GB of VRAM and 100 GB of disk, the Cosmos Predict 1
backbone is pulled separately, and the install builds Triton and custom kernels.
No GB10 run has been reported, so treat the first one as the measurement.

#### Lyra 2.0 stays declined

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

### Nous Research Arete-27B

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

### ComfyUI\_Nvidia\_VFX\_Nodes

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

### LuxDiT

LuxDiT estimates image-based lighting from a single photo or a video with a
video diffusion transformer. It is the relighting capability the 3D lane does
not have, which is why the row stays in the catalog as a card rather than
disappearing.

**Blocked on license.** The repository ships the NVIDIA OneWay Noncommercial
License, so it is the code itself, not only the weights, that bars use inside a
product container. The `nvidia/LuxDiT` card tags the weights `license:other`, which is a second wall behind the first, and that tag does not read as a permission for product use.

**The footprint, measured.** `nvidia/LuxDiT` is `luxdit_image/` at 11.74 GB plus `luxdit_video/` at 11.74 GB plus a negligible `hdr_merge_mlp/`, so 23.49 GB for the whole repo. The tier row names the 11.74 GB image tree, which is what a relight run pulls; the 23.5 GB figure this section carried was the repo total, and the 21.87 GB figure the lane table carried matches neither tree and is dropped.

**What would reopen it.** NVIDIA relicenses the code away from the OneWay
Noncommercial terms. The weight terms then have to be readable as a permission
for product use, not a card tag.

**Use instead.** Nothing in the promoted stack relights a shot today. The 3D
lane goes image to mesh with TRELLIS.2 and the [Asset Bible](../asset-bible.md)
records those outputs, so a relight stays in the DCC tools beside the stack for
now. See [3D pipeline](../learn/pipeline.md) and [NVIDIA lab](../nvidia-lab.md).

### InfiniCube

InfiniCube generates an unbounded voxel world with video and dynamic Gaussians
for driving scenes, from a prompt and a pose.

**Blocked on license.** The checkpoints are hosted on a personal Hugging Face
account (`yifanlu/InfiniCube-checkpoints`) rather than the NVIDIA org, their
terms allow research and educational use only and prohibit commercial use, and
they bind the user to the Waymo Open Dataset terms of service on top. The code
being Apache-2.0 does not change any of that. The run is heavy as well: the Wan
14B stage is about 20 minutes per 93-frame 480p clip on an A100.

**The footprint, measured.** `yifanlu/InfiniCube-checkpoints` `checkpoints/` sums to 82.3 GB. The lane table above carried 76.64 GB for no stated narrower scope, so the measured figure stands on both.

**What would reopen it.** The weights are relicensed for commercial use and
hosted by the NVIDIA org, so the terms come from the vendor and not from a
personal account.

**Use instead.** Stills from Klein and motion from Wan 2.2 and LTX-2.5. The
input domain is driving scenes, which no lane in this stack produces, so even a
clean license would need a use case first. See
[Model licenses](../licenses.md) and [NVIDIA lab](../nvidia-lab.md).

### dvlt (Deja View)

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

### SplatPainting

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

### PixelUMM

PixelUMM is an encoder-free unified model that understands and generates both
images and video in one network.

**Blocked on footprint and on terms.** The released weights are **121.63 GB of distributed checkpoints**: four dirs in `nvidia/PixelUMM`, `S8-F18-R01`, `S8-F19-R03`, `S8-F21-R02`, `S8-F22-R05`, at 30.41 GB each (`S8-F18-R01` measures 30.39), 480 `.distcp` shards in all, which the row rounds to 121.6. The single-checkpoint 30.41 GB figure in the lane table above is one of those four dirs, not the release. The model also pulls a 16 GB Qwen3-8B, and the documented training path asks for seven GPUs of 48 GiB or more. That is a cluster, and this stack is one Spark; the row marks GB10 unsupported. The Hugging Face card tags the weights `license:other` and the terms were not readable as permission for product use.

**What would reopen it.** A quantized single-GPU inference checkpoint with a
readable permissive weight license. Both halves have to land: the footprint and
the terms.

**Use instead.** Klein, Wan 2.2, and LTX-2.5 generate; Qwen2.5-VL captions. All
of it arrives with `bazelisk run //:manage -- download-models`. See
[Prompting](../prompting.md) and [Models and cache](../models-and-cache.md).

### Cosmos Drive Dreams

Cosmos Drive Dreams generates synthetic multi-view autonomous-vehicle video and
LiDAR from HD map, bounding box, and LiDAR conditions.

**Blocked on architecture.** The Cosmos 1 upstream it needs ships x86\_64 NGC
images and prebuilt CUDA wheels, so nothing resolves inside this aarch64 image.
The license is not the problem here: the weights inherit the NVIDIA Open Model
License from the Cosmos cards and permit commercial use. The domain is the other
wall - the inputs are autonomous-vehicle sensor conditions, which no lane in this
stack produces.

**The weights repo, and which figures are verified.** The tier row names `nvidia/Cosmos-Transfer1-7B-Sample-AV`, which is public (HTTP 200) with `gated: "auto"`; its `base_model.pt` measures 28.95 GB. The research-lane row above names `nvidia/Cosmos-Drive-Dreams`, which returns HTTP 401 to an anonymous read: it is gated, so the GB figures carried there for the models and the dataset could not be checked anonymously and are unverified.

**What would reopen it.** Upstream Cosmos publishes linux\_aarch64 wheels or an
arm64 container that runs on GB10.

**Use instead.** The image and video lanes. A driving-sim lane would have to
exist before this row had a job. See [Cinema](../visual-generative-ai.md) and
[NVIDIA lab](../nvidia-lab.md).

### ComfyUI DLSS 5 Enhancer

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

### Omniverse NuRec GA

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

### Gamma-World, Asset Harvester, and Instant NuRec

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

The refuse list is fail-closed and lives in `config/model-manifest.yaml`, owned
by the `//config:policy` target. A path whose name contains a refuse token is
classified as a banned weight, so the disk wizard names it instead of treating
it as reclaimable or as part of the keep-set. The research lane is a **separate
section**: it never reaches the keep-set, and no verb fetches from it.

The `Lyra-2.0` token stays in place, and so does `Arete-27B`. Lyra 1.x carries no token, because its weights are installable through the tier.

Every NVIDIA candidate above is also a row in the opt-in **nvidia-lab** tier, and
the catalog is the enforcement. `custom_nodes/ez_nvidia_lab/catalog.json` is the
single source of truth for each row's status, licenses, artifact, and footprint,
and `install` and `run` refuse any row whose status is not `opt-in` before
anything executes. This page is the prose behind the row; the row is what the CLI
reads. The verbs and the per-row footprints are on
[NVIDIA lab](../nvidia-lab.md).

```bash
bazelisk test //tests:bats_models_manifest_test   # refuse list present and opt-in; research lane listed and unfetched
bazelisk test //tests:pytest --test_arg=tests/python/test_disk_catalog.py
bazelisk test //tests:bats_nvidia_lab_test        # the catalog contract and the verbs
```

Nothing in this stack downloads these weights. `bazelisk run //:manage -- download-models` fetches only what `packs:` pins, no `nvidia-lab` row is a manifest pack, no row is a Compose service, and no row reaches the image. An artifact lands on the host only when you run `bazelisk run //:manage -- nvidia-lab install` on a row whose status is `opt-in`, which asks for **yes** first, runs the host headroom preflight, refuses while a heavy occupancy mode holds the GPU, and writes under `${EZ_NVIDIA_LAB_HOME:-$HOME/.ez-comfy/nvidia-lab}` - never inside the repo. The cleanup verbs default to `--plan`.

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
   sit beside a stricter license in the body, and the repo LICENSE can cover the
   code while the weights sit under something else entirely - which is exactly
   what happened with `dvlt`.
4. If the weights are on a **personal** Hugging Face account with no license
   tag, treat that as declined until the owner declares one.
5. For a node pack, confirm it has no cloud or license-server call, since this
   stack is local-only.
6. Check the hardware claim against GB10 specifically. "Tested on H100 and A100"
   is not "runs on Spark".
7. Clear the refuse token in the same change that promotes the pack, with a test proving the new path works on GB10.

To promote a research model into the real catalog, clear all four gates, drop its
`research:` row and add a `packs:` row in the same change, with a test proving
the path works on GB10, then promote the graph with
`bazelisk run //:manage -- promote-workflow` and update the docs in the same
change.
change. For a tier row the catalog edit comes first: the row's `status` is what
makes `install` accept it, so a re-test that clears the four gates changes
`custom_nodes/ez_nvidia_lab/catalog.json`, this page, and
[NVIDIA lab](../nvidia-lab.md) in one change, with
`bazelisk test //tests:bats_nvidia_lab_test` green.
