# syntax=docker/dockerfile:1
# Purpose:
#   Multi-stage CUDA image for ComfyUI flux-to-ltx on DGX Spark (GB10 / aarch64).
#   Builder (devel) prebuilds ComfyUI + PyTorch in cache-friendly phases; runtime
#   (runtime base) is slim. Layer order keeps multi-GB torch/comfy stable when
#   only ops scripts (entrypoint / patch) change.
#
# Privacy:
#   Build context is only whitelisted docker/* scripts (see .dockerignore).
#   Never bake secrets, dotenv files, host paths, or model weights into this image.
#
# Source of truth: this file
# Safety:
#   No models in image (host MODELS_DIR). restart: "no" in compose.
#
# Layer cache contract (high-velocity dev):
#   Builder: only install-comfy.sh before prebuild RUNs.
#   Runtime: COPY multi-GB prebuilt BEFORE entrypoint/install/patch (volatile last).
#   Phases: venv+torch | comfy | nodes+finalize — torch layer survives node edits.
#   BuildKit pip cache mount: wheels reuse when a phase layer does rebuild.
#
# Base images:
#   Builder default: public Docker Hub nvidia/cuda devel (compile optional wheels).
#   Runtime default: public Docker Hub nvidia/cuda runtime (no nvcc).
#   Override: CUDA_BASE_IMAGE / CUDA_RUNTIME_IMAGE (NGC after docker login nvcr.io).

ARG CUDA_BASE_IMAGE=nvidia/cuda:13.0.0-devel-ubuntu24.04
ARG CUDA_RUNTIME_IMAGE=nvidia/cuda:13.0.0-runtime-ubuntu24.04

# ── builder: install Comfy + torch in phased layers ─────────────────────────
FROM ${CUDA_BASE_IMAGE} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LAB_KEEP_PIP_CACHE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs python3 python3-pip python3-venv python3-dev \
    build-essential curl ca-certificates libgl1 libglib2.0-0 rsync \
    && git lfs install --system \
    && mkdir -p /opt/ez-comfy/workflows /models \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ez-comfy

# Sole script input to prebuild — entrypoint/patch must NOT appear before these RUNs
COPY --chmod=755 install-comfy.sh /opt/ez-comfy/

# Prebuild Comfy + torch into the image (public git/pip only; no HF tokens).
# Set EZ_COMFY_PREBUILD=0 to skip (thin image; cold pip at runtime).
# Optional COMFYUI_REF pins ComfyUI git ref for reproducible clones.
ARG EZ_COMFY_PREBUILD=1
ARG COMFYUI_REF=
ENV COMFY_HOME=/opt/comfy-prebuilt \
    MODELS_ROOT=/models \
    LAB_PREBUILT_ROOT=/opt/comfy-prebuilt \
    COMFYUI_REF=${COMFYUI_REF}

# Phase pair 1: venv + multi-GB torch (rarely invalidated)
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase venv + torch → /opt/comfy-prebuilt …"; \
      bash /opt/ez-comfy/install-comfy.sh --phase venv && \
      bash /opt/ez-comfy/install-comfy.sh --phase torch; \
    else \
      echo "[Dockerfile] EZ_COMFY_PREBUILD=0 — skipping prebuild"; \
      mkdir -p /opt/comfy-prebuilt; \
    fi

# Phase 2: ComfyUI clone + requirements (medium churn)
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase comfy …"; \
      bash /opt/ez-comfy/install-comfy.sh --phase comfy; \
    fi

# Phase 3: custom nodes + stamp/strip/links (higher churn; no torch reinstall)
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase nodes + finalize …"; \
      bash /opt/ez-comfy/install-comfy.sh --phase nodes && \
      bash /opt/ez-comfy/install-comfy.sh --phase finalize && \
      rm -rf /tmp/* /var/tmp/*; \
    fi

# ── runtime: slim CUDA runtime + prebuilt tree ──────────────────────────────
FROM ${CUDA_RUNTIME_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime only: no build-essential / python3-dev / git-lfs (cold install uses wheels).
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv \
    curl ca-certificates libgl1 libglib2.0-0 rsync \
    && mkdir -p /opt/ez-comfy/workflows /models \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ez-comfy

# Heavy stable layer first — only invalidates when builder prebuild changes
COPY --from=builder /opt/comfy-prebuilt /opt/comfy-prebuilt

# Volatile ops scripts last — entrypoint/patch/install edits rebuild only this thin layer
COPY --chmod=755 install-comfy.sh entrypoint.sh /opt/ez-comfy/
COPY --chmod=644 patch_get_free_memory.py /opt/ez-comfy/

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
