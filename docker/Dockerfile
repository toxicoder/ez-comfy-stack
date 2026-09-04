# syntax=docker/dockerfile:1
# Purpose:
#   Multi-stage CUDA image for ComfyUI us-safe-studio on DGX Spark (GB10 / aarch64).
#   Builder stages (runtime base + compilers) prebuild ComfyUI + PyTorch in
#   cache-friendly phases; final stage is slim CUDA runtime. Layer order keeps
#   multi-GB torch stable when only ops scripts, Comfy pins, or node pip change.
#
# Privacy:
#   Build context is only whitelisted docker/* scripts (see .dockerignore).
#   Never bake secrets, dotenv files, host paths, or model weights into this image.
#
# Source of truth: this file
# Safety:
#   No models in image (host MODELS_DIR). restart: "no" in compose.
#
# Layer cache contract (high-velocity dev + pull):
#   Torch stage: COPY only core.sh + phase-venv-torch.sh (not common.sh / pins).
#   Pin ARGs are declared in the stage that uses them (never ENV'd before torch).
#   Runtime COPY --link: /opt/parts/venv (torch) then venv-extra then app, then ops.
#   Phases: torch | comfy | nodes+finalize+package — torch layer survives node edits.
#   venv-extra is the pip delta after torch so Comfy/node wheels do not re-pull torch.
#   BuildKit pip + apt cache mounts: reuse when a phase layer does rebuild.
#   Client pull: COPY --link rebases venv when only runtime apt changes.
#
# Base images:
#   Default builder AND runtime: public Docker Hub nvidia/cuda runtime (no nvcc).
#   Override CUDA_BASE_IMAGE to a devel tag if you must compile CUDA extensions.
#   NGC: CUDA_BASE_IMAGE / CUDA_RUNTIME_IMAGE after docker login nvcr.io.
#
# Pins (validated 2026-07-29; Comfy bump 2026-08-26; torch pin 2026-09-03):
#   TORCH_VERSION=2.14.0  (cu130 index)
#   COMFYUI_REF=v0.34.0  COMFYUI_MANAGER_REF=4.2.2  COMFYUI_NUNCHAKU_NODE_REF=v1.2.1
#   COMFYUI_VHS_REF= (empty = VideoHelperSuite main; required for LTX lab MP4)

ARG CUDA_BASE_IMAGE=nvidia/cuda:13.0.0-runtime-ubuntu24.04
ARG CUDA_RUNTIME_IMAGE=nvidia/cuda:13.0.0-runtime-ubuntu24.04

# ── builder-base: runtime CUDA + compilers (not the ~8GB devel toolkit) ─────
FROM ${CUDA_BASE_IMAGE} AS builder-base

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LAB_KEEP_PIP_CACHE=1 \
    COMFY_HOME=/opt/comfy-prebuilt \
    MODELS_ROOT=/models \
    LAB_PREBUILT_ROOT=/opt/comfy-prebuilt \
    LAB_PARTS_ROOT=/opt/parts

# Keep apt downloads in BuildKit cache mounts (not in the image layer).
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
      >/etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv python3-dev \
    gcc g++ \
    curl ca-certificates libgl1 libglib2.0-0 rsync \
    && mkdir -p /opt/ez-comfy/workflows /models /opt/ez-comfy/install-comfy /opt/parts

WORKDIR /opt/ez-comfy

# ── torch: multi-GB cu130 wheels (no Comfy/node pin ARGs in this stage) ─────
FROM builder-base AS torch

ARG EZ_COMFY_PREBUILD=1
ARG TORCH_VERSION=2.14.0
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu130
ENV TORCH_VERSION=${TORCH_VERSION} \
    TORCH_INDEX_URL=${TORCH_INDEX_URL}

# Only torch-stable inputs — common.sh (clone/link/strip) must not appear here.
COPY --chmod=755 install-comfy/core.sh install-comfy/phase-venv-torch.sh \
    /opt/ez-comfy/install-comfy/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase venv + torch → /opt/comfy-prebuilt …"; \
      bash -euo pipefail -c '\
        source /opt/ez-comfy/install-comfy/core.sh; \
        source /opt/ez-comfy/install-comfy/phase-venv-torch.sh; \
        export LAB_PACKAGE_PARTS=1; \
        phase_venv; \
        phase_torch'; \
    else \
      echo "[Dockerfile] EZ_COMFY_PREBUILD=0 — skipping prebuild"; \
      mkdir -p /opt/comfy-prebuilt /opt/parts/venv /opt/parts/venv-extra /opt/parts/app; \
    fi

# ── comfy: clone pin + requirements (venv-extra / app; torch snapshot kept) ─
FROM torch AS comfy

ARG EZ_COMFY_PREBUILD=1
ARG COMFYUI_REF=v0.34.0
ENV COMFYUI_REF=${COMFYUI_REF}

COPY --chmod=755 install-comfy/common.sh install-comfy/phase-comfy.sh \
    /opt/ez-comfy/install-comfy/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase comfy …"; \
      bash -euo pipefail -c '\
        source /opt/ez-comfy/install-comfy/common.sh; \
        source /opt/ez-comfy/install-comfy/phase-venv-torch.sh; \
        source /opt/ez-comfy/install-comfy/phase-comfy.sh; \
        export LAB_PACKAGE_PARTS=1; \
        phase_comfy'; \
    fi

# ── nodes: custom nodes + stamp/strip + split venv-extra + app ──────────────
FROM comfy AS nodes

ARG EZ_COMFY_PREBUILD=1
ARG COMFYUI_MANAGER_REF=4.2.2
ARG COMFYUI_NUNCHAKU_NODE_REF=v1.2.1
ARG COMFYUI_VHS_REF=
ENV COMFYUI_MANAGER_REF=${COMFYUI_MANAGER_REF} \
    COMFYUI_NUNCHAKU_NODE_REF=${COMFYUI_NUNCHAKU_NODE_REF} \
    COMFYUI_VHS_REF=${COMFYUI_VHS_REF}

COPY --chmod=755 install-comfy/phase-nodes.sh install-comfy/phase-finalize.sh \
    /opt/ez-comfy/install-comfy/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase nodes + finalize + package parts …"; \
      bash -euo pipefail -c '\
        source /opt/ez-comfy/install-comfy/common.sh; \
        source /opt/ez-comfy/install-comfy/phase-venv-torch.sh; \
        source /opt/ez-comfy/install-comfy/phase-comfy.sh; \
        source /opt/ez-comfy/install-comfy/phase-nodes.sh; \
        source /opt/ez-comfy/install-comfy/phase-finalize.sh; \
        export LAB_PACKAGE_PARTS=1; \
        phase_nodes; \
        phase_finalize; \
        rm -rf /tmp/* /var/tmp/*'; \
    else \
      mkdir -p /opt/parts/venv /opt/parts/venv-extra /opt/parts/app; \
    fi

# ── runtime: slim CUDA runtime + split prebuilt parts ───────────────────────
FROM ${CUDA_RUNTIME_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
      >/etc/apt/apt.conf.d/keep-cache

# Runtime: keep slim (no git-lfs / full build-essential).
# Triton JIT (PyTorch 2.13+ torch._native / first CLIPTextEncode) needs:
#   - gcc/g++  — compile cuda_utils.c (else "Failed to find C compiler")
#   - python3-dev — Python.h for that extension (else CalledProcessError from gcc)
# Not full build-essential: small apt layer; COPY --link keeps venv cacheable.
# ffmpeg: preferred by VideoHelperSuite (imageio-ffmpeg is pip fallback)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv python3-dev \
    gcc g++ \
    ffmpeg \
    curl ca-certificates libgl1 libglib2.0-0 rsync \
    && mkdir -p /opt/ez-comfy/workflows /models /opt/ez-comfy/install-comfy

WORKDIR /opt/ez-comfy

# Independent layers (--link): apt changes rebase without rewriting venv blobs.
# Overlay: torch venv, then extra pip (Comfy + nodes), then app sources.
COPY --link --from=torch /opt/parts/venv /opt/comfy-prebuilt/.venv
COPY --link --from=nodes /opt/parts/venv-extra /opt/comfy-prebuilt/.venv
COPY --link --from=nodes /opt/parts/app /opt/comfy-prebuilt

# Volatile ops scripts last — entrypoint/patch/orchestrator edits rebuild only thin layers
COPY --chmod=755 install-comfy.sh entrypoint.sh /opt/ez-comfy/
COPY --chmod=755 install-comfy/ /opt/ez-comfy/install-comfy/
COPY --chmod=644 patch_get_free_memory.py /opt/ez-comfy/
# PYTHONPATH sitecustomize: optional torch.backends.python_native.triton disable
COPY --chmod=644 pythonpath/ /opt/ez-comfy/pythonpath/

# Runtime uses the named volume; seed from LAB_PREBUILT_ROOT on first start
ENV COMFY_HOME=/comfy-state/ComfyUI \
    MODELS_ROOT=/models \
    HF_HOME=/models \
    HUGGINGFACE_HUB_CACHE=/models/hub \
    LAB_PREBUILT_ROOT=/opt/comfy-prebuilt \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    CUDA_MODULE_LOADING=LAZY \
    LAB_VISUAL_ENABLE_NVFP4=1 \
    LAB_VISUAL_PROFILE=flux-to-ltx \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Public OCI labels only (no private metadata)
LABEL org.opencontainers.image.title="ez-comfy flux-to-ltx" \
      org.opencontainers.image.description="ComfyUI flux-to-ltx sample for DGX Spark (no model weights)" \
      org.opencontainers.image.source="https://github.com/toxicoder/ez-comfy-stack"

EXPOSE 8188
ENTRYPOINT ["/opt/ez-comfy/entrypoint.sh"]
