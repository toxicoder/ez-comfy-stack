# Purpose:
#   Build the CUDA 13 devel image used for ComfyUI flux-to-ltx on DGX Spark
#   (GB10 / aarch64). Ships install + entrypoint scripts and the Spark free-memory
#   patch; ComfyUI itself is cloned into the comfy-state volume at first start so
#   image rebuilds do not discard custom nodes or outputs.
# Source of truth: this file
# Regenerate: n/a (docker compose build)
# Safety:
#   No models baked into the image (mounted from host /mnt/models).
#   Auto-restart is disabled in docker-compose.yml (restart: "no").
#   PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True reduces allocator thrash.
#
# Base image:
#   Default is public Docker Hub nvidia/cuda (no NGC login). nvcr.io often
#   returns "oauth token: denied" without docker login nvcr.io.
#   Override: CUDA_BASE_IMAGE=nvcr.io/nvidia/cuda:13.0.0-devel-ubuntu24.04

ARG CUDA_BASE_IMAGE=nvidia/cuda:13.0.0-devel-ubuntu24.04
FROM ${CUDA_BASE_IMAGE} AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs python3 python3-pip python3-venv python3-dev \
    build-essential curl ca-certificates libgl1 libglib2.0-0 \
    && git lfs install --system \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ez-comfy

COPY install-comfy.sh entrypoint.sh patch_get_free_memory.py /opt/ez-comfy/
RUN chmod +x /opt/ez-comfy/install-comfy.sh /opt/ez-comfy/entrypoint.sh \
    && mkdir -p /opt/ez-comfy/workflows

ENV COMFY_HOME=/comfy-state/ComfyUI \
    MODELS_ROOT=/models \
    HF_HOME=/models \
    HUGGINGFACE_HUB_CACHE=/models/hub \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    CUDA_MODULE_LOADING=LAZY \
    LAB_VISUAL_ENABLE_NVFP4=1 \
    LAB_VISUAL_PROFILE=flux-to-ltx \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

EXPOSE 8188
ENTRYPOINT ["/opt/ez-comfy/entrypoint.sh"]
