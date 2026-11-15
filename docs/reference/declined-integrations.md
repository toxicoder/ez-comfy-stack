---
title: Declined and research integrations
description: "Third-party models and node packs evaluated for the Spark stack: the NVIDIA candidates allowed for local experimentation, the ones declined, the license on each, and what you may publish from them."
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

**What this enables**

- Read one page instead of re-researching a candidate that was already turned, with the vendor source for each verdict
- Tell a license wall from a hardware wall, which decides whether waiting helps
- Know, before a 90 GB download, whether you are allowed to publish what the model prints
- Confirm the catalog keeps refused weights off `${MODELS_DIR}`, and keeps the research lane out of `download-models` without you auditing the list by hand

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

**Not legal advice.** This page encodes the stack's **download and workflow
policy**. It is not legal advice. Read each model card and license yourself
before you monetize anything. Several licenses below are quoted from the
vendor's own text; where they conflict, the vendor's text wins.

## Summary

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
| PixelUMM | `nv-tlabs/PixelUMM` | `nvidia/PixelUMM` | blocked | Unified image+video understand and generate, 30.41 GB. Needs a CUDA 13.0 aarch64 PyTorch wheel that does not exist (pytorch/pytorch#160162), and its FlashAttention arch list stops at 100. One source file stays CC BY-NC 4.0. |
| GEN3C | `nv-tlabs/GEN3C` | `nvidia/GEN3C-Cosmos-7B` | blocked | License-clean, but pins torch 2.6 on an NGC 24.10 base and source-builds apex; zero aarch64 hits across 614 tracked files; about 220 GB disk. |
| LuxDiT | `nv-tlabs/LuxDiT` | `nvidia/LuxDiT` | marginal | HDR environment-map lighting from RGB, 21.87 GB. No CUDA extension and no torch pin, so it is the least blocked of the non-commercial set. Emits `.exr` envmaps - a relighting stage, not a finished image. A community node exists (`jzhang-POP/ComfyUI-LuxDiT`, MIT, 1 star). |
| InfiniCube | `nv-tlabs/InfiniCube` | `yifanlu/InfiniCube-checkpoints` | blocked | Installs literal `linux_x86_64` cu121 `gsplat` and `fvdb` wheels with no aarch64 twin. Weights are a Waymo derivative. 76.64 GB. |
| Cosmos-Drive-Dreams | `nv-tlabs/Cosmos-Drive-Dreams` | `nvidia/Cosmos-Drive-Dreams` | blocked | Asks for about 300 GB free; models alone are 66 + 44 + 67 GB and the companion dataset is near 3 TB. Driving-domain input, so thin on G4 as well. |
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

## Enforcement

The refuse list is fail-closed and lives in `config/model-manifest.yaml`, owned
by the `//config:policy` target. A path whose name contains a refuse token is
classified as a banned weight, so the disk wizard names it instead of treating
it as reclaimable or as part of the keep-set. The research lane is a **separate
section**: it never reaches the keep-set, and no verb fetches from it.

```bash
bazelisk test //tests:bats_models_manifest_test   # refuse list present and opt-in; research lane listed and unfetched
bazelisk test //tests:pytest --test_arg=tests/python/test_disk_catalog.py
```

Nothing in this stack downloads these weights. `bazelisk run //:manage --
download-models` fetches only what `packs:` pins, and the cleanup verbs default
to `--plan`.

## Reopening an evaluation

Architecture and license terms change. Re-check the primary source before you
spend a day on this:

1. For an NVIDIA wheel, list the release index and confirm the exact wheel tag
   for `linux_aarch64` and your Python ABI. A `win_arm64` wheel does not prove
   Linux Arm support.
2. For a checkpoint, read the license section of the model card itself and look
   for the words "production" and "deploy". A card tag reading Apache-2.0 can
   sit beside a stricter license in the body, and the repo LICENSE can cover the
   code while the weights sit under something else entirely - which is exactly
   what happened with `dvlt`.
3. If the weights are on a **personal** Hugging Face account with no license
   tag, treat that as declined until the owner declares one.
4. For a node pack, confirm it has no cloud or license-server call, since this
   stack is local-only.
5. Check the hardware claim against GB10 specifically. "Tested on H100 and A100"
   is not "runs on Spark".

To promote a research model into the real catalog, clear all four gates, drop its
`research:` row and add a `packs:` row in the same change, with a test proving
the path works on GB10, then promote the graph with
`bazelisk run //:manage -- promote-workflow` and update the docs in the same
change.
