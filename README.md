# ez-comfy-stack

[![Docs (latest)](https://img.shields.io/badge/docs-latest-indigo?style=for-the-badge&logo=materialformkdocs&logoColor=white)](https://toxicoder.github.io/ez-comfy-stack/latest/)
[![Docs (development)](https://img.shields.io/badge/docs-development-blueviolet?style=for-the-badge&logo=materialformkdocs&logoColor=white)](https://toxicoder.github.io/ez-comfy-stack/development/)
[![CI](https://img.shields.io/github/actions/workflow/status/toxicoder/ez-comfy-stack/ci.yml?branch=development&style=for-the-badge&logo=github&label=CI)](https://github.com/toxicoder/ez-comfy-stack/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/toxicoder/ez-comfy-stack?style=for-the-badge)](LICENSE)

**Simplified Visual Generative AI** demo for a **single NVIDIA DGX Spark**: ComfyUI with the unified **Flux → LTX** pipeline (image + video), Docker Compose, shared `/mnt/models` cache, and remote-SSH-safe download throttling.

**Documentation:** [latest](https://toxicoder.github.io/ez-comfy-stack/latest/) (from `main`) · [development](https://toxicoder.github.io/ez-comfy-stack/development/) (from `development`) — MkDocs Material, published per branch via GitHub Pages.

Inspired by [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab) visual workloads — without K3s, Ansible, or the full lab dashboard. Use the lab for production multi-stack operations; use this repo for faster demos.

## Goals

- One command path to a working ComfyUI flux-to-ltx stack on one Spark  
- Shared model cache compatible with other stacks (`/mnt/models`)  
- Operator CLI (`manage.sh`) for start / stop / status / doctor  
- Bandwidth-limited downloads with **auto = 85% of speedtest**  
- Never auto-start heavy GPU work after reboot  
- Hermetic tests with a **100% coverage gate**

## Architecture

```mermaid
flowchart TB
  Op["Operator"] --> CLI["manage.sh"]
  CLI --> Compose["Docker Compose · restart: no"]
  Compose --> Comfy["ComfyUI container"]
  Models["/mnt/models"] -.->|bind| Comfy
  State["comfy-state volume"] -.-> Comfy
  Comfy --> UI[":8188"]
  Op --> UI
```

## Quick start

```bash
cp .env.example .env   # set HF_TOKEN if needed
./scripts/manage.sh doctor
./scripts/manage.sh download-models   # throttled flux-fast + ltx-balanced
./scripts/manage.sh start             # type yes
./scripts/manage.sh status
# open http://<spark-ip>:8188
./scripts/manage.sh stop              # before reboot
```

```mermaid
sequenceDiagram
  actor Op as Operator
  participant M as manage.sh
  participant D as Docker / ComfyUI
  participant B as Browser

  Op->>M: doctor
  Op->>M: download-models
  Note over M: wrap --limit auto · 85% of speedtest
  Op->>M: start type yes
  M->>D: compose up
  Op->>B: open :8188
  Op->>M: stop before reboot
```

## Layout

```text
docker/           Dockerfile + compose (flux-to-ltx)
scripts/manage.sh Operator CLI
scripts/lib/      Shared shell helpers
scripts/utilities download-flux, download-ltx, download-limit
config/           Resource / headroom policy
workflows/        Seeded lab ComfyUI example graphs
docs/             MkDocs site
tests/            BATS + pytest + coverage gate
```

```mermaid
flowchart LR
  Docker["docker/"] --> Manage["scripts/manage.sh"]
  Manage --> Lib["scripts/lib/"]
  Manage --> Util["scripts/utilities/"]
  Manage --> Cfg["config/"]
  Docker --> WF["workflows/"]
  Docs["docs/"] --> Tests["tests/"]
```

## Documentation

**Read online (published):** [latest](https://toxicoder.github.io/ez-comfy-stack/latest/) · [development](https://toxicoder.github.io/ez-comfy-stack/development/)

CI deploys docs via `.github/workflows/deploy-docs.yml` after push to `main` / `development` (docs paths) or `workflow_dispatch`. PR checks run `make docs` only.

```bash
pip install -r docs/requirements.txt
make docs          # site/ (strict MkDocs build)
# or: mkdocs serve
```

Key pages (branch-relative source): [Getting Started](docs/getting-started.md) · [Visual Generative AI](docs/visual-generative-ai.md) · [Download Limit](docs/download-limit.md) · [Reboot Safety](docs/reboot-safety.md)

## Development

```bash
make test
make coverage
make lint
make docs
```

## Safety

- Compose `restart: "no"` — manual start only  
- Heavy confirmation + free RAM/disk headroom  
- Download throttle by default  
- See [docs/reboot-safety.md](docs/reboot-safety.md)

## License

MIT — see [LICENSE](LICENSE).
