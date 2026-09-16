# syntax=docker/dockerfile:1
# ## Contributor dev image for ez-comfy-stack
#
# Multi-arch Linux image (linux/amd64 + linux/arm64) so the same definition
# works on Apple Silicon, Intel Mac / Windows x86_64, Linux, and DGX Spark
# (Grace ARM64).
#
# Tool versions: .devcontainer/tool-versions.env
# Build context: .devcontainer/ (see devcontainer.json).
# Compose studio only — no cluster CLIs in this image.

FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

ARG BAZELISK_VERSION=v1.25.0
ARG BUILDIFIER_VERSION=v8.2.1
ARG SHFMT_ASSET_VERSION=3.10.0

COPY tool-versions.env /tmp/tool-versions.env

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    jq \
    make \
    python3 \
    python3-pip \
    python3-venv \
    shellcheck \
    bats \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN case "${TARGETARCH}" in \
      amd64|arm64) ARCH="${TARGETARCH}" ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH} (need amd64 or arm64)" >&2; exit 1 ;; \
    esac; \
    echo "Installing pinned CLIs for linux/${ARCH}..."; \
    curl -fsSL "https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-${ARCH}" \
      -o /usr/local/bin/bazelisk \
    && chmod +x /usr/local/bin/bazelisk \
    && ln -sf /usr/local/bin/bazelisk /usr/local/bin/bazel \
    && bazelisk version; \
    curl -fsSL "https://github.com/bazelbuild/buildtools/releases/download/${BUILDIFIER_VERSION}/buildifier-linux-${ARCH}" \
      -o /usr/local/bin/buildifier \
    && chmod +x /usr/local/bin/buildifier \
    && buildifier --version || true; \
    curl -fsSL "https://github.com/mvdan/sh/releases/download/v${SHFMT_ASSET_VERSION}/shfmt_v${SHFMT_ASSET_VERSION}_linux_${ARCH}" \
      -o /usr/local/bin/shfmt \
    && chmod +x /usr/local/bin/shfmt \
    && shfmt --version
