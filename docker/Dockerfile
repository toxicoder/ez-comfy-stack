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
# Layer cache contract (high-velocity dev + pull):
#   Builder: COPY only the phase modules each RUN needs (torch survives nodes edits).
#   Runtime: COPY /opt/parts/venv then /opt/parts/app BEFORE entrypoint/install/patch.
#   Phases: venv+torch | comfy | nodes+finalize+package — torch layer survives node edits.
#   BuildKit pip cache mount: wheels reuse when a phase layer does rebuild.
#   Client pull: app-only changes re-download app layer; venv multi-GB stays cached.
#
# Base images:
#   Builder default: public Docker Hub nvidia/cuda devel (compile optional wheels).
#   Runtime default: public Docker Hub nvidia/cuda runtime (no nvcc).
#   Override: CUDA_BASE_IMAGE / CUDA_RUNTIME_IMAGE (NGC after docker login nvcr.io).
#
# Pins (validated 2026-07-29 — bump deliberately; see docs/models-and-cache.md):
#   COMFYUI_REF=v0.29.0  COMFYUI_MANAGER_REF=4.2.2  COMFYUI_NUNCHAKU_NODE_REF=v1.2.1

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
    && mkdir -p /opt/ez-comfy/workflows /models /opt/ez-comfy/install-comfy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ez-comfy

# Prebuild Comfy + torch into the image (public git/pip only; no HF tokens).
# Set EZ_COMFY_PREBUILD=0 to skip (thin image; cold pip at runtime).
# Pins default to validated tags; override build-args to bump or float.
ARG EZ_COMFY_PREBUILD=1
ARG COMFYUI_REF=v0.29.0
ARG COMFYUI_MANAGER_REF=4.2.2
ARG COMFYUI_NUNCHAKU_NODE_REF=v1.2.1
ENV COMFY_HOME=/opt/comfy-prebuilt \
    MODELS_ROOT=/models \
    LAB_PREBUILT_ROOT=/opt/comfy-prebuilt \
    LAB_PARTS_ROOT=/opt/parts \
    COMFYUI_REF=${COMFYUI_REF} \
    COMFYUI_MANAGER_REF=${COMFYUI_MANAGER_REF} \
    COMFYUI_NUNCHAKU_NODE_REF=${COMFYUI_NUNCHAKU_NODE_REF}

# Phase pair 1: only torch-stable module inputs (nodes edits must not bust this)
COPY --chmod=755 install-comfy/common.sh install-comfy/phase-venv-torch.sh \
    /opt/ez-comfy/install-comfy/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase venv + torch → /opt/comfy-prebuilt …"; \
      bash -euo pipefail -c '\
        source /opt/ez-comfy/install-comfy/common.sh; \
        source /opt/ez-comfy/install-comfy/phase-venv-torch.sh; \
        phase_venv; \
        phase_torch'; \
    else \
      echo "[Dockerfile] EZ_COMFY_PREBUILD=0 — skipping prebuild"; \
      mkdir -p /opt/comfy-prebuilt /opt/parts/venv /opt/parts/app; \
    fi

# Phase 2: ComfyUI clone + requirements (medium churn)
COPY --chmod=755 install-comfy/phase-comfy.sh /opt/ez-comfy/install-comfy/
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${EZ_COMFY_PREBUILD}" = "1" ]; then \
      echo "[Dockerfile] phase comfy …"; \
      bash -euo pipefail -c '\
        source /opt/ez-comfy/install-comfy/common.sh; \
        source /opt/ez-comfy/install-comfy/phase-venv-torch.sh; \
        source /opt/ez-comfy/install-comfy/phase-comfy.sh; \
        phase_comfy'; \
    fi

# Phase 3: custom nodes + stamp/strip/links + split parts for runtime layers
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
        phase_nodes; \
        LAB_PACKAGE_PARTS=1 phase_finalize; \
        rm -rf /tmp/* /var/tmp/*'; \
    fi

# ── runtime: slim CUDA runtime + split prebuilt parts ───────────────────────
FROM ${CUDA_RUNTIME_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime only: no build-essential / python3-dev / git-lfs (cold install uses wheels).
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv \
    curl ca-certificates libgl1 libglib2.0-0 rsync \
    && mkdir -p /opt/ez-comfy/workflows /models /opt/ez-comfy/install-comfy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ez-comfy

# Heavy stable layer first — final .venv after all pip (torch + comfy + node deps)
COPY --from=builder /opt/parts/venv /opt/comfy-prebuilt/.venv

# Medium churn — ComfyUI sources + custom_nodes + stamp (no .venv)
COPY --from=builder /opt/parts/app /opt/comfy-prebuilt

# Volatile ops scripts last — entrypoint/patch/orchestrator edits rebuild only thin layers
COPY --chmod=755 install-comfy.sh entrypoint.sh /opt/ez-comfy/
COPY --chmod=755 install-comfy/ /opt/ez-comfy/install-comfy/
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
