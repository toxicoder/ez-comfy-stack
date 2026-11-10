---
title: Declined integrations
description: Third-party models and node packs that were evaluated for the Spark stack and rejected, with the evidence, the exact gate that would reopen each, and the catalog path to use instead.
tags: [models, safety, licenses, video, integrations]
---

# Declined integrations

**What's on this page**

- **Rejected** - NVIDIA Project Lyra, Nous Research Arete-27B, ComfyUI\_Nvidia\_VFX\_Nodes
- **Per item** - what it is, the blocking fact, what would reopen it, what to use instead
- **Enforcement** - how the catalog keeps the weights off disk
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

| Candidate | Verdict | Blocking gate | Reopen when |
| --- | --- | --- | --- |
| NVIDIA Project Lyra (Lyra 2.0) | Declined | License bars deployment and production use | NVIDIA relicenses the checkpoints |
| Nous Research Arete-27B | Declined | Text-only model with no GGUF; no media lane to serve | A CPU-runnable GGUF exists and a use beyond the pinned writer appears |
| ComfyUI\_Nvidia\_VFX\_Nodes | Declined | No `linux_aarch64` wheel for the `nvidia-vfx` runtime | NVIDIA publishes an aarch64 wheel that works on GB10 |

## NVIDIA Project Lyra

Lyra is NVIDIA's open generative 3D world model line. Lyra 2.0 takes one image
plus a camera trajectory, generates a walkthrough video with a 14B Wan 2.1
image-to-video DiT, then reconstructs 3D Gaussian Splats from it.

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

**Use instead.** Stills come from Klein and motion from Wan 2.2 and LTX-2.5, all
in the pinned catalog. For 3D, the native TRELLIS lane covers image-to-3D. See
[TRELLIS and 3D](../learn/pipeline.md) and
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

## Enforcement

The two weight-bearing candidates are in the fail-closed refuse list in
`config/model-manifest.yaml`, which is owned by the `//config:policy` target. A
path whose name contains a refuse token is classified as a banned weight, so the
disk wizard names it instead of treating it as reclaimable or as part of the
keep-set.

```bash
bazelisk test //tests:bats_models_manifest_test   # refuse list is present and opt-in
bazelisk test //tests:pytest --test_arg=tests/python/test_disk_catalog.py
```

Nothing in this stack downloads these weights. `bazelisk run //:manage --
download-models` fetches only what the manifest pins, and the cleanup verbs
default to `--plan`.

## Reopening an evaluation

Architecture and license terms change. Re-check the primary source before you
spend a day on this:

1. For an NVIDIA wheel, list the release index and confirm the exact wheel tag
   for `linux_aarch64` and your Python ABI. A `win_arm64` wheel does not prove
   Linux Arm support.
2. For a checkpoint, read the license section of the model card itself and look
   for the words "production" and "deploy". A card tag reading Apache-2.0 can
   sit beside a stricter license in the body.
3. For a node pack, confirm it has no cloud or license-server call, since this
   stack is local-only.
4. Clear the refuse token in the same change that promotes the pack, with a test
   proving the new path works on GB10.

If a candidate clears all four gates, promote it through
`bazelisk run //:manage -- promote-workflow` and update the docs in the same
change.
