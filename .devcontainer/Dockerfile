# syntax=docker/dockerfile:1
# ## Contributor dev image for ez-comfy-stack
#
# Multi-arch Linux image (linux/amd64 + linux/arm64) so the same definition
# works on Apple Silicon, Intel Mac / Windows x86_64 (Docker Desktop/WSL2),
# Linux Engine, and DGX Spark (Grace ARM64). The container OS is always Linux.
#
# Layer cache contract (do not regress):
#   Apt is first and does not COPY pin files.
#   Version ARG for Node / Bazel CLIs / Grok are declared immediately above
#   the RUN that uses them so a Grok bump does not rebuild Node.
#   BuildKit apt cache mounts: reuse packages when a layer does rebuild.
#   Build context is .devcontainer/ only (whitelist .dockerignore).
#   Workspace sources are bind-mounted at runtime - never COPY the repo.
#
# Tool versions: .devcontainer/tool-versions.env (ARG defaults must match).
# Compose studio / CUDA image is docker/Dockerfile - not this file.

FROM mcr.microsoft.com/devcontainers/base:noble

ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/vscode/.venv/bin:/usr/local/bin:${PATH}"

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# Keep apt downloads in BuildKit cache mounts (not in the image layer).
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
      >/etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
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
    xz-utils \
    zstd \
    bubblewrap \
    && rm -f /etc/apt/apt.conf.d/docker-clean

# Node 22 official tarball (linux-x64 / linux-arm64). ARG scope starts here.
# Artifacts: node-v*-linux-x64.tar.xz and node-v*-linux-arm64.tar.xz.
ARG NODE_VERSION=22.23.2
ARG NODE_SHA256_X64=d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307
ARG NODE_SHA256_ARM64=fff4078c5def658577f92c88db7db3bc0072924bfb93fe52c1e744a54e94abb8
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
      amd64) narch=x64; nsha="${NODE_SHA256_X64}" ;; \
      arm64) narch=arm64; nsha="${NODE_SHA256_ARM64}" ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH} (need amd64 or arm64)" >&2; exit 1 ;; \
    esac; \
    tmp="$(mktemp)"; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${narch}.tar.xz" \
      -o "${tmp}"; \
    echo "${nsha}  ${tmp}" | sha256sum -c -; \
    tar -xJf "${tmp}" -C /usr/local --strip-components=1; \
    rm -f "${tmp}"; \
    node --version; \
    npm --version

# Pinned lint CLIs (bazelisk-linux-${TARGETARCH}). ARG scope starts here.
ARG BAZELISK_VERSION=v1.25.0
ARG BUILDIFIER_VERSION=v8.2.1
ARG SHFMT_ASSET_VERSION=3.10.0
ARG TARGETARCH
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

# Grok Build (~170MiB). Last heavy download so version bumps stay cheap.
# Artifacts: grok-*-linux-x86_64 and grok-*-linux-aarch64 from x.ai/cli.
ARG GROK_VERSION=1.0.40
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
      amd64) base="https://x.ai/cli/grok-${GROK_VERSION}-linux-x86_64" ;; \
      arm64) base="https://x.ai/cli/grok-${GROK_VERSION}-linux-aarch64" ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH} (need amd64 or arm64)" >&2; exit 1 ;; \
    esac; \
    tmp="$(mktemp)"; \
    if curl -fsSL -o "${tmp}.zst" "${base}.zst"; then \
      zstd -q -dc "${tmp}.zst" >/usr/local/bin/grok; \
    elif curl -fsSL -o "${tmp}.gz" "${base}.gz"; then \
      gzip -dc "${tmp}.gz" >/usr/local/bin/grok; \
    else \
      curl -fsSL -o /usr/local/bin/grok "${base}"; \
    fi; \
    rm -f "${tmp}" "${tmp}.zst" "${tmp}.gz"; \
    chmod +x /usr/local/bin/grok; \
    ln -sf /usr/local/bin/grok /usr/local/bin/agent; \
    grok --version

COPY grok/config.toml /tmp/grok-config.toml
COPY grok/sandbox.toml /tmp/grok-sandbox.toml
RUN mkdir -p /etc/grok /home/vscode/.grok \
    && cp /tmp/grok-config.toml /etc/grok/managed_config.toml \
    && cp /tmp/grok-config.toml /home/vscode/.grok/config.toml \
    && cp /tmp/grok-sandbox.toml /home/vscode/.grok/sandbox.toml \
    && chown -R vscode:vscode /home/vscode/.grok \
    && chmod 0644 /etc/grok/managed_config.toml \
    && rm -f /tmp/grok-config.toml /tmp/grok-sandbox.toml
