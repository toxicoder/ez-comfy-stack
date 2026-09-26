---
title: Contributor Dev Container
description: Multi-arch Linux contributor image with Bazel, Node 22, Python 3.12, and Grok Build - host LLM via host.docker.internal, not host networking.
tags: [contributing, devcontainer, docker, grok]
---

# Contributor Dev Container

**What's on this page**

- **Reopen in Container** on macOS, Windows (WSL2), Linux, and DGX Spark
- **What is baked** vs post-create vs the Docker-outside-of-Docker Feature
- **Grok Build** in the image - device-code or `XAI_API_KEY`, optional host LLM
- **Sandbox** - no host netns; Grok denies the Docker socket
- **Pin bumps** and the GHCR cache tag

**What this enables**

- **Working** with the same Bazel/lint/Node/Python pins on Apple Silicon, Intel, WSL2, and Spark
- **Rebuilding** cheaply when only one CLI pin changes (layer order + BuildKit cache + GHCR)
- **Calling** a host Ollama / LM Studio / llama.cpp server without `--network=host`

**Who this is for:** contributors and agents using VS Code / Cursor Dev Containers. Studio operators on the Spark stay on [Set up this computer](../start/this-computer.md) - this image is not the Comfy GPU image.

The container OS is always **Linux** (`linux/amd64` or `linux/arm64`). Windows and macOS hosts run that Linux image through Docker Desktop, OrbStack, Colima, or Engine 20.10+.

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

---

## Open it

1. Install Docker Desktop (Mac/Windows) or Docker Engine 20.10+ (Linux / Spark).
2. Open the **repo root** in VS Code or Cursor.
3. Command Palette -> **Dev Containers: Reopen in Container**.

First create installs `tests/requirements.txt` into `~/.venv` and prewarms `bazelisk` / `grok`. Named volumes keep Bazel and pip caches across rebuilds.

Then: `bazelisk run //:validate`.

---

## What lives where

| Layer | Contents | Rebuilds when |
| --- | --- | --- |
| Image (apt) | Ubuntu 24.04, Python 3.12, bubblewrap, shellcheck | Rarely |
| Image (Node) | Official Node 22 tarball | `NODE_VERSION` / SHA256 |
| Image (CLIs) | bazelisk, buildifier, shfmt | those pins |
| Image (Grok) | Grok Build binary (~170 MiB) | `GROK_VERSION` |
| Image (config) | `/etc/grok/managed_config.toml`, `~/.grok/sandbox.toml` | grok config files |
| Feature | docker-outside-of-docker `1.10.1` (host `docker.sock` + GID) | Feature pin |
| post-create | `~/.venv` from `tests/requirements.txt` | requirements / recreate |
| Opt-in | `docs-site npm ci` | `DEVCONTAINER_INSTALL_DOCS_SITE=1` |

Pins: `.devcontainer/tool-versions.env`. Dockerfile `ARG` defaults must match (BATS). Do **not** `COPY` that env file before apt - it would bust the package layer.

Docs site: `./docs/setup-docs.sh` (or set `DEVCONTAINER_INSTALL_DOCS_SITE=1` on create). Skipping default `npm ci` keeps create light.

GHCR cache: `ghcr.io/toxicoder/ez-comfy-devcontainer:development` (published after merge to `development`). A miss on the first pull is expected.

This image is **not** `ghcr.io/toxicoder/ez-comfy:us-safe-studio*` (Comfy CUDA). See [Project conventions](../project-conventions.md).

---

## Grok Build

`grok` is on `PATH`. Auth (pick one):

```bash
export XAI_API_KEY="xai-..."   # forwarded from the host env when set
grok login --device-auth       # no browser loopback inside the container
```

Do not bind-mount host `~/.grok/auth.json`.

### Host LLM (Ollama, LM Studio, llama.cpp)

The container uses its **own** network namespace plus:

```text
--add-host=host.docker.internal:host-gateway
```

That works on Docker Desktop and on Linux Engine. It is **not** `--network=host`.

| Server | URL from inside the container |
| --- | --- |
| Ollama | `http://host.docker.internal:11434/v1` (default `host-llm` model) |
| LM Studio | `http://host.docker.internal:1234/v1` |
| llama.cpp / LiteLLM | same hostname, your port |

On **Linux Engine**, the host server must listen on `0.0.0.0` (or the Docker bridge), not `127.0.0.1`. Docker Desktop on Mac/Windows can reach host localhost through the VM.

```text
/model host-llm
```

Default model stays the xAI catalog so a machine without a local LLM still works.

---

## Sandbox

| Control | What it does |
| --- | --- |
| Default bridge | Container is not on the host netns |
| `runArgs` `--cap-drop` | Drops `SYS_ADMIN`, `SYS_MODULE`, `SYS_PTRACE`, `NET_ADMIN`, `NET_RAW`, `MKNOD` |
| `GROK_SANDBOX=devcontainer` | Workspace writes + kernel deny of `docker.sock`, `**/.env`, `**/*.pem`, SSH keys |
| `shell_environment_policy inherit = "core"` | Child bash does not inherit `XAI_API_KEY` |
| bubblewrap | Required for Grok `deny` lists on Linux |

The Docker-outside-of-Docker Feature still mounts the host socket so **you** can run Compose from the terminal. Grok's sandbox denies that socket so the **agent** cannot `docker run --privileged`.

---

## Bump a pin

1. Edit `.devcontainer/tool-versions.env`
2. Match Dockerfile `ARG` defaults and `devcontainer.json` `build.args`
3. For Node, also update `NODE_SHA256_X64` / `NODE_SHA256_ARM64` from `https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt` (`.tar.xz` linux-x64 / linux-arm64)
4. `bazelisk test //tests:bats_devcontainer_test`

---

## Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Host LLM connection refused | Server bound to `127.0.0.1` on Linux Engine | Listen on `0.0.0.0`; confirm `host.docker.internal` resolves |
| `grok` refuses to start (sandbox / deny) | bubblewrap missing or sandbox.toml unreadable | Image must include `bubblewrap`; do not delete `~/.grok/sandbox.toml` |
| Slow create | `docs-site npm ci` running | Leave `DEVCONTAINER_INSTALL_DOCS_SITE` unset; use `./docs/setup-docs.sh` when you need the docs app |
| GHCR cache miss | Image not published yet | First merge to `development` publishes `ez-comfy-devcontainer:development`; local Dockerfile still builds |

Related: [Building with Bazel](building-with-bazel.md) - [Contributing](contributing.md) - [Host and Docker](../operate/troubleshooting-host-docker.md)
