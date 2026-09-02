---
title: Troubleshooting
description: Common failures for ez-comfy-stack on DGX Spark and how to fix them.
tags: [troubleshooting, comfyui, docker]
---

# Troubleshooting

**What's on this page**

- Symptom → cause → action by theme
- Decision tree for common failures
- Useful log commands and reset paths

**What this enables**

- Recovering from OOM, stuck bandwidth limits, empty models, and long cold starts

!!! tip "Try this first"

    ```bash
    ./scripts/manage.sh doctor
    ```

    Many rows below are hard failures `doctor` already reports. Prefer `./scripts/manage.sh setup` when Docker or `MODELS_DIR` is missing.

---

## Host & Docker

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `docker missing` in doctor | Docker not installed / snap-only | `./scripts/manage.sh setup --install-docker` (sudo apt CE + compose); then `newgrp docker` or re-login |
| docker permission denied | Not in `docker` group this session | `sudo usermod -aG docker $USER` then `newgrp docker` or re-login SSH |
| docker daemon not reachable | dockerd not running | `sudo systemctl start docker` |
| `MODELS_DIR … not writable` | `/mnt/models` missing or root-owned | `./scripts/manage.sh setup` **or** `sudo mkdir -p /mnt/models && sudo chown $USER:$USER /mnt/models` **or** `MODELS_DIR=$HOME/models` |
| Pending / can't start container | Docker/GPU runtime | `nvidia-smi`, Container Toolkit install |
| `failed to fetch oauth token: denied` / `nvcr.io` Access Denied on `start` | NGC base image pull without login | Pull latest (default bases are **Docker Hub** `nvidia/cuda` devel builder + runtime final). Rebuild: `./scripts/manage.sh start`. If you set `CUDA_BASE_IMAGE` / `CUDA_RUNTIME_IMAGE` to `nvcr.io/...`, run `docker login nvcr.io` (user `$oauthtoken`, password = NGC API key) |

### Docker missing on DGX Spark

Docker is usually pre-installed on DGX Spark, but updates or OS reimages can remove it. Prefer **apt Docker CE** (not snap) so the NVIDIA Container Toolkit can attach GPUs.

```bash
./scripts/manage.sh setup --install-docker
# sudo password + type yes if prompted
newgrp docker   # if permission denied in this shell
./scripts/manage.sh doctor
```

=== "Interactive"

    ```bash
    ./scripts/manage.sh setup --install-docker
    ```

=== "Non-interactive"

    ```bash
    LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes SETUP_INSTALL_DOCKER=1 \
      ./scripts/manage.sh setup
    ```

### MODELS_DIR permission denied

Default cache is `/mnt/models` (shared with nvidia-dgx-spark-lab). Prefer bootstrap:

```bash
./scripts/manage.sh setup
# creates/chowns MODELS_DIR with sudo when needed
```

Manual equivalent:

```bash
sudo mkdir -p /mnt/models
sudo chown "$USER:$USER" /mnt/models
# or in .env:
# MODELS_DIR=$HOME/models
./scripts/manage.sh doctor
```

---

## Downloads & bandwidth

| Symptom | Likely cause | Action |
| --- | --- | --- |
| wondershaper `qdisc kind is unknown` / RTNETLINK | No HTB/IFB (common on DGX Spark) | Expected; wrap uses **gentle HF max-workers** from measured speed (HTTP probe). Not a hard Mbps cap. `DOWNLOAD_LIMIT=off` for full blast |
| Speedtest failed / always 50 Mbps | CLI missing or probe blocked | Auto-installs `speedtest-cli` when possible; **clears limits before measure**; then HTTP probe / live RX. Check outbound HTTPS if all fail |
| ++ctrl+c++ does not stop download | Old tee pipeline orphan | Pull latest; wrap/hf use process groups — Ctrl+C should stop `hf` within seconds |
| `Still waiting to acquire lock` on `*.lock` | Stale HF locks from killed downloads | `./scripts/manage.sh clear-hf-locks` or auto-clear on download-models; if stuck: `HF_LOCK_CLEAR_FORCE=1 ./scripts/manage.sh clear-hf-locks` |
| SSH freezes during download | Full-rate HF pull (limit off or soft-fail) | Prefer working `download-limit`; lower fixed Mbps; `download-limit clear` if half-applied |
| `huggingface-cli is deprecated` / 0 GB after download-models | Scripts used stub CLI | Pull latest; ensure `hf` on PATH (`pipx install huggingface_hub`); re-run download-models |
| Download failed / gated license | No token or license not accepted | Accept model license on HF; set `HF_TOKEN` in `.env` or `hf auth login` |
| Long Python `GatedRepoError` traceback | Older CLI path / unparsed hub error | Current stack prints a short checklist; open the model URL, Agree as the token’s user, re-run download. Debug: `LAB_DEBUG=1` |
| Limits stuck after kill | trap skipped | `./scripts/manage.sh download-limit clear` |

### wondershaper / qdisc failures

`download-models` wraps downloads under wondershaper. If the kernel rejects HTB (`qdisc kind is unknown`) or illegal rates, **wrap soft-fails**: it warns and continues **unthrottled** (SSH risk). Persistent `download-limit run` still hard-fails. Set `DOWNLOAD_LIMIT_REQUIRE=1` to hard-fail wrap too.

```bash
./scripts/manage.sh download-limit clear
# optional: sudo modprobe sch_htb sch_ingress sch_sfq
./scripts/manage.sh download-models
# or explicitly:
# DOWNLOAD_LIMIT=off ./scripts/manage.sh download-models
```

---

## Start & runtime

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `start` refused | Headroom check | Free RAM/disk; stop other GPU jobs |
| Extreme model thrash / 5–15× slow | Unpatched free-memory | Confirm patch in container logs; re-run entrypoint install |
| Build OK, `status` empty / not in `docker ps` | Container exited immediately (`restart: "no"`) | Pull latest (workflow no longer mounts into `ComfyUI/` before clone). `./scripts/manage.sh logs` or `docker logs ez-comfy-flux-to-ltx`. Reset poisoned volume: `./scripts/manage.sh stop && docker volume rm ez-comfy-state` then `start` again. Stop other GPU containers if needed |
| `start` returns while logs still downloading torch | Normal cold install; multi‑GB wheels | Leave it running; `start` streams logs by default. Re-attach: `./scripts/manage.sh logs`. Markers: `[comfy-install] ══ step N/12 ══` (or `Docker phase: …` during image prebuild) |
| Quiet for minutes on step 4 (PyTorch) | Large cudnn/torch wheel download | Prefer GHCR prebuilt image (seed, no pip). Or wait for pip bars; host heartbeat every 30s |
| `docker pull ghcr.io/...` denied / not found | Wrong branch tag, package not published, or private | Confirm tag matches branch (`:flux-to-ltx` on `main`, `:flux-to-ltx-development` on `development`/feature — see `doctor`). Run `publish-image` on that long-lived branch; make GHCR package public; or `EZ_COMFY_IMAGE=…` / force local build: [Getting Started — build locally](getting-started.md#build-the-image-locally-optional) |
| First start still runs multi-GB pip | Thin image / no prebuilt / force cold | Check logs for “Seeding … prebuilt”. Rebuild with `EZ_COMFY_PREBUILD=1` or pull GHCR tag. Unset `LAB_FORCE_COLD_INSTALL` |
| `docker pull` / rebuild re-downloads multi‑GB after tiny script edit | Old image with monolithic prebuilt layer, or a real pip/torch change | Pull latest split layout: runtime has separate **venv** (~multi‑GB) and **app** layers. Ops scripts are late thin layers + compose bind-mounts. Nodes/source-only changes should re-pull **app** only; any pip change still re-pulls venv. See [Models & Cache](models-and-cache.md#image-layer-cache-high-velocity-rebuilds-pulls) |
| Local script change has no effect | Looking at baked image without restart | Compose mounts `docker/*.sh`, `docker/install-comfy/`, and the patch; restart after edit. To rebake prebuilt tree: [build locally](getting-started.md#build-the-image-locally-optional) (`LAB_STACK_FORCE_BUILD=1`) |
| `IndentationError` in `model_management.py` / `mem_free_torch` | Old free-memory patch broke indent | Pull latest (patch is bind-mounted). `./scripts/manage.sh stop && ./scripts/manage.sh start` — auto-repairs via git restore + re-patch. No full image rebuild required |
| Cold start forever | First PVC/volume pip+git | Wait; `manage.sh logs`; check network |
| Nunchaku import spam / `nunchaku 0.16.1` / missing `nunchaku.models` | Wrong **PyPI** package (`nunchaku` stats lib) or no aarch64 wheel on GB10 | Lab graphs do **not** need Nunchaku. Restart after image refresh (removes wrong package). Do **not** `pip install nunchaku` from PyPI. Optional real engine: GitHub wheels only (`NUNCHAKU_WHEEL_URL=…` or x86_64 cu/torch match). Spark aarch64: skip; use core UNET/CLIP/VAE loaders |
| Nunchaku missing | aarch64 wheel unavailable | Fail-soft; **\*-lab-example** Flux / LTX paths still work |

---

## Models & workflows

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Empty models in UI | Downloads not run | `download-flux` / `download-ltx` status; check `MODELS_DIR` mount |
| Missing `ae.safetensors` / `qwen_3_4b` / `z_image_turbo_*.safetensors` | **Z-Image** template, not this stack | Load a **\*-lab-example** workflow (e.g. **flux-txt2img-lab-example** / **flux-to-ltx-lab-example**). Stack models are Flux Klein NVFP4 + LTX-2.3 (see [Models & Cache](models-and-cache.md)). Run `download-models` if those files are missing under `MODELS_DIR/comfy/` |
| Missing `flux-2-klein-9b-nvfp4` or LTX `*.safetensors` in **\*-lab-example** graphs | Weights not on host and/or Comfy `models/*` not symlinked to host | 1) `./scripts/manage.sh download-models` (exits non-zero until lab basenames exist) 2) `ls $MODELS_DIR/comfy/diffusion_models` 3) `docker exec ez-comfy-flux-to-ltx ls -la /comfy-state/ComfyUI/models/diffusion_models` — should be a **symlink** to `/models/comfy/diffusion_models`. Restart after pull so `link_models` retargets. Flux is gated: set `HF_TOKEN` and accept the BFL license |
| Missing `flux2-vae.safetensors` (VAELoader) while Qwen TE is present | Companions partial (TE ~6.8 GB alone used to cache-hit skip VAE) | Re-run `./scripts/manage.sh download-models` or `./scripts/utilities/download-flux.sh run --tier companions`. Confirm `ls $MODELS_DIR/comfy/vae/flux2-vae.safetensors`. Restart Comfy after pull |
| Comfy log: path `…/models/vae/*.safetensors` **exists but doesn't link anywhere**; UI missing `flux2-vae` / `LTX23_*_vae` while host `ls` looks fine | Absolute host symlinks under `MODELS_DIR/comfy/*` (e.g. → `/mnt/models/…`) break inside the container where the cache is mounted at `/models` | Pull latest; re-run `./scripts/manage.sh download-models` (cache hit rewrites **relative** links — no full re-download). Check `readlink $MODELS_DIR/comfy/vae/flux2-vae.safetensors` starts with `../`, not `/`. Confirm: `docker exec ez-comfy-flux-to-ltx test -e /models/comfy/vae/flux2-vae.safetensors`. **Do not** wipe `ez-comfy-state` for this |
| Missing `LTX23_video_vae_bf16` / LTX distilled FP8 in **ltx-*-lab-example** | LTX balanced not downloaded or not linked (older `*te*` globs mis-linked every `*.safetensors` into `text_encoders/`) | Pull latest; `./scripts/utilities/download-ltx.sh run --tier balanced` then `ls $MODELS_DIR/comfy/{diffusion_models,vae}` (not only `text_encoders/`). `doctor` / `download-models` gate on the full lab set |
| CLIP / latent errors on Flux lab graphs | Wrong CLIP type or latent node | Use seeded **flux-*-lab-example** graphs: CLIP type **`flux2`** with `qwen_3_8b_fp4mixed`, latent **`EmptyFlux2LatentImage`**. Do not use `qwen_image` / Z-Image loaders |
| `Failed to find C compiler` / Triton on **CLIPTextEncode** | Runtime image missing `gcc`/`g++`; PyTorch 2.13 Triton JIT needs CC for `cuda_utils` / `bmm_outer_product` | Pull/rebuild image (runtime installs `gcc` `g++` + `python3-dev`) and restart. Confirm: `docker exec ez-comfy-flux-to-ltx which gcc` |
| `CalledProcessError` compiling `cuda_utils*.so` / `bmm_outer_product` on **CLIPTextEncode** (LTX Gemma or Flux) | Triton JIT has `gcc` but fails the compile (missing `Python.h` / `python3-dev`, or `libcuda.so.1` not on gcc `LIBRARY_PATH`). stderr is swallowed by Triton | Pull/rebuild image so runtime has **`python3-dev`** + `gcc`/`g++`. Restart. Confirm: `docker exec ez-comfy-flux-to-ltx test -f /usr/include/python3.*/Python.h && echo ok`. Logs should show `Triton JIT deps OK` (or auto-disable). Escape hatch: `LAB_DISABLE_TORCH_NATIVE_TRITON=1` then restart (eager/cuBLAS fallback; CLIP still works) |
| KSampler LTX: `Expected size 768 but got size 4096` / `embeddings_connector` | Missing Gemma TE or projection-only CLIPLoader | Lab graphs need **DualCLIPLoader**: `gemma_3_12B_it_fp4_mixed` + `ltx-2.3_text_projection_bf16`, type **`ltxv`**. Run `./scripts/manage.sh download-models`, re-open **ltx-*-lab-example** from `workflows/` |
| KSampler LTX: `cannot reshape tensor of 0 elements into shape [1, 0, 32, -1]` / `freqs_cis_matrix` / `av_model` audio RoPE | LTX-2.3 is a **joint AV** transformer; video-only latents leave audio length T=0 | Re-open a current **ltx-*-lab-example** graph (has `LTXVEmptyLatentAudio` + `LTXVConcatAVLatent` + `LTXVSeparateAVLatent` + `LTX23_audio_vae_bf16`). Do not feed `EmptyLTXVLatentVideo` / `LTXVImgToVideo` straight into `KSampler`. Confirm `ls $MODELS_DIR/comfy/vae/LTX23_audio_vae_bf16.safetensors` |
| Missing `gemma_3_12B_it_fp4_mixed` in LTX graphs | Gemma companion not downloaded | `./scripts/utilities/download-ltx.sh run --tier balanced` (auto-includes gemma) or `download-models`; `ls $MODELS_DIR/comfy/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors` |
| Missing `VHS_VideoCombine` node on **ltx-*-lab-example** | Image/volume predates VideoHelperSuite, or refresh clone failed | Pull/rebuild GHCR image (VHS is prebuilt). Restart container so stamp-present refresh runs `ensure_lab_video_nodes`. Confirm: `docker exec ez-comfy-flux-to-ltx test -d /comfy-state/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite`. Last resort: `LAB_FORCE_COLD_INSTALL=1` or volume cleanup, then re-open seeded workflows |
| LTX finished but I only see PNGs / no MP4 preview | Old workflow JSON without VHS, or looking only at SaveImage | Re-open current **ltx-*-lab-example** from `user/default/workflows/` (entrypoint re-copies host `workflows/`). After Queue, open **Save video (MP4)** node for preview; MP4 is under Comfy `output/` as `ez_ltx_*_video_*.mp4`. Frames via SaveImage are secondary — [Getting Started → Watch the video](getting-started.md#watch-the-video-ltx) |
| OOM / multi-minute hang on **ltx-*-30s-*** / ***-60s-*** | Long latents (721 / 1441 frames) are heavy | Prefer base **~10 s** graphs for smoke tests. Confirm headroom preflight; close other GPU jobs; start with `ltx-i2v-lab-example` / `ltx-t2v-lab-example` before long-run demos |
| Missing `MiniMaxH3*` / **Unknown pack** / UI says install Manager | Volume still on Comfy **v0.29.0** (stamp-present refresh used to skip the pin). These are **core** nodes in **v0.34.0**, not a custom pack | Do **not** `pip install comfyui-manager`. `git pull`, `stop` + `start` (logs: “Comfy pin changed” / “Syncing ComfyUI”). Confirm: `docker exec ez-comfy-flux-to-ltx grep MiniMaxH3AddGuide /comfy-state/ComfyUI/comfy_extras/nodes_minimax_h3.py`. If GHCR is still 0.29: `LAB_STACK_FORCE_BUILD=1 ./scripts/manage.sh start`. Last resort: `LAB_FORCE_COLD_INSTALL=1` or `cleanup` then start |
| H3 OOM at 1344×768×379 | Unified-memory pressure on GB10 | In the UI, set the six `MiniMaxH3ImageToVideo` nodes to **864×480**. Do **not** raise `MEM_LIMIT` |
| H3 download / generation geo or license error | MiniMax H3 Community License excluded territories (US/EU/UK/KR) for local open weights | Read [H3 films — license](h3-films.md). This stack does not geo-block the downloader |
| Stitched H3 MP4 longer than 90s | Concat kept 2164 unique frames (90.17s) | Graphs keep **2160** frames; `stitch-h3` uses `ffmpeg -t 90` and fails if probe `> 90` |

---

## Symptom decision tree

```mermaid
flowchart TB
  Q["What is broken?"]
  Q --> Docker{"doctor: docker missing?"}
  Q --> Models{"MODELS_DIR not writable?"}
  Q --> Qdisc{"wondershaper / qdisc errors?"}
  Q --> SSH{"SSH freezes<br/>or host sluggish?"}
  Q --> Start{"start refused?"}
  Q --> Empty{"Empty models in UI?"}
  Q --> Slow{"Extreme thrash<br/>5–15× slow?"}
  Q --> Cold{"Cold start forever?"}
  Q --> Limit{"Bandwidth limit stuck?"}

  Docker --> A0["apt docker-ce + compose plugin<br/>docker group · re-login"]
  Models --> A0b["sudo mkdir/chown /mnt/models<br/>or MODELS_DIR in .env"]
  Qdisc --> A0c["soft-fail unthrottled warn OK<br/>modprobe sch_htb · clear"]
  SSH -->|during download| A1["download-models / lower Mbps<br/>or download-limit clear"]
  Start --> A2["Free RAM/disk<br/>stop other GPU jobs · doctor"]
  Empty --> A3["download-flux/ltx status<br/>check MODELS_DIR mount"]
  Slow --> A4["Confirm free-memory patch<br/>in logs · restart container"]
  Cold --> A5["Wait 10–30+ min<br/>manage.sh logs · network"]
  Limit --> A6["manage.sh download-limit clear"]
```

---

## Logs

```bash
./scripts/manage.sh logs
docker logs ez-comfy-flux-to-ltx
```

```mermaid
flowchart LR
  Op["Operator"] --> M["manage.sh logs"]
  Op --> D["docker logs<br/>ez-comfy-flux-to-ltx"]
  M --> Out["Compose / service logs"]
  D --> Out
```

---

## Reset Comfy install (keeps models)

```bash
./scripts/manage.sh cleanup   # type DELETE
./scripts/manage.sh start
```

```mermaid
flowchart TB
  Cleanup["manage.sh cleanup<br/>type DELETE"] --> Vol["Remove named volume<br/>comfy-state only"]
  Vol --> Models["Host MODELS_DIR preserved"]
  Models --> Start["manage.sh start"]
  Start --> Reinstall["entrypoint reinstalls ComfyUI<br/>into fresh volume"]
```
