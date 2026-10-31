# ez-comfy-stack

[![Docs (latest)](https://img.shields.io/badge/docs-latest-orange?style=for-the-badge&logo=nextjs&logoColor=white)](https://toxicoder.github.io/ez-comfy-stack/latest/)
[![Docs (development)](https://img.shields.io/badge/docs-development-teal?style=for-the-badge&logo=nextjs&logoColor=white)](https://toxicoder.github.io/ez-comfy-stack/development/)
[![CI](https://img.shields.io/github/actions/workflow/status/toxicoder/ez-comfy-stack/ci.yml?branch=development&style=for-the-badge&logo=github&label=CI)](https://github.com/toxicoder/ez-comfy-stack/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/toxicoder/ez-comfy-stack?style=for-the-badge)](LICENSE)

**Simplified Visual Generative AI** demo for a **single NVIDIA DGX Spark**: ComfyUI in Docker Compose with a **US-safe local studio** (Apache Klein 4B stills, Apache Wan 2.2 silent motion, LTX-2.5 distilled AV), occupancy XOR, and remote-SSH-safe downloads.

| Feature | Default |
| --- | --- |
| Runtime | Docker Compose, one ComfyUI service |
| US-safe models | Klein 4B + Wan 2.2 + LTX-2.5 |
| Occupancy | One heavy GPU job (XOR) |
| Downloads | `download-limit auto` = **85%** of measured Mbps (24h host cache) |
| Restart | `restart: "no"` - type **yes** on start |
| Tests | **Bazelisk** is the only ingress - hermetic **100%** coverage gate via `bazelisk run //:validate` |

**Documentation:** [latest](https://toxicoder.github.io/ez-comfy-stack/latest/) (from `main`) - [development](https://toxicoder.github.io/ez-comfy-stack/development/) (from `development`) - Fumadocs (Next.js) with Orama search, glossary tooltips, Mermaid, and live editable command variables. Docs run through bazelisk too: `bazelisk run //docs:serve` locally, `bazelisk run //docs:docs` for the static export, `bazelisk test //docs:test_docs_site_render` for the content gate (`./docs/manage-docs.sh serve` is the no-Bazel path). Migration notes: [MIGRATION.md](MIGRATION.md).

## Start here

Read the four pages below in order and you will have a running studio and your first still.

1. [How the studio works](docs/learn/index.mdx) - what this is, the two roles on one machine, and the vocabulary the rest of the docs assume.
2. [Getting Started](docs/getting-started.mdx) - install, doctor, download the default pack, start, and Queue a still.
3. [Quick reference](docs/operate/quick-reference.md) - the commands you come back to every day.
4. [Troubleshooting overview](docs/troubleshooting.mdx) - the symptom router, when something refuses.

Two questions people ask first: which stack fits the job, and what may be run and published.
The comparison with the full [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab)
is on [This stack or nvidia-dgx-spark-lab](docs/start/when-to-use-vs-spark-lab.mdx); the licensing
rules are on [Model licenses](docs/licenses.mdx).

## What the docs cover

The site has seven tabs. Inside a tab, the sidebar groups the pages in the order you need
them, so the first page in a group is the one to read first.

| Tab | Groups | Open it when |
| --- | --- | --- |
| Home | - | You want the map and the default stack at a glance |
| Learn | The studio at a glance; Models, hardware, and safety; Look-dev and 3D concepts; Glossary | You want to know why the studio works this way before you fight it |
| Get started | Install and start; Choose and decide | You are on a fresh Spark and need it up |
| Studio | Start creating; Recipe racks; Graph catalogs; Films, podcasts, and music; 3D, Blender, and host tools | You have a job to make and need the right graph |
| Operate | Everyday loop; GPU occupancy; Models and downloads; Disk, backup, and data; Safety, scale, and feedback; Troubleshooting | You run this machine day to day |
| Reference | Commands and modes; Workflows and nodes; Config and boards | You need an exact flag, node, port, or schema |
| Contribute | Before you start; Build, test, and environment; Docs and security | You are changing this repo |

## Quick start

Full walkthrough: **[Getting Started](https://toxicoder.github.io/ez-comfy-stack/latest/getting-started/)** (or the [development](https://toxicoder.github.io/ez-comfy-stack/development/getting-started/) docs if you track that branch). Session variables:

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"

# first boot, once per machine: bazelisk + the lint toolchain the gates shell out to
bash scripts/setup-host.sh

# laptop (macOS/Linux/WSL): ./scripts/manage.sh setup-client
# one-shot from the laptop (never auto-starts): ./scripts/manage.sh onboard
./scripts/manage.sh setup --install-docker
bazelisk run //:manage -- doctor
./scripts/manage.sh download-models   # Klein 4B + Wan 2.2 5B + LTX-2.5
./scripts/manage.sh start             # type yes
# open http://${SPARK_HOST}:${COMFY_PORT}
# laptop: ssh -L "${COMFY_PORT}:127.0.0.1:${COMFY_PORT}" "${SPARK_USER}@${SPARK_HOST}"
./scripts/manage.sh stop              # before reboot
```

Non-host verbs lead with the same ingress as everything else, `bazelisk run //:manage -- <verb>`.
`./scripts/manage.sh <verb>` stays the documented escape hatch for `setup`, `download-models`,
`start`, and `stop`, which need docker, sudo, the GPU, or `$HOME`.

Cut and grade the result in **[Vlo](docs/vlo.mdx)** - a host-side, AGPL-3.0 timeline editor
that dials this stack's ComfyUI at `http://127.0.0.1:${COMFY_PORT:-8188}`, so every heavy
generation still runs on the Spark. It is a host app: never in the image, never a Compose
service, never a `manage.sh` verb.

```bash
git clone https://github.com/PxTicks/vlo && cd vlo && ./install.sh && ./run.sh
# then open http://127.0.0.1:6332 in Chrome or Edge
```

## The gates

One-time host bootstrap. Without it `bazelisk test //:lint` passes with no linters installed
at all, so a skipped linter after this point is a real defect:

```bash
bash scripts/setup-host.sh            # or: bazelisk run //:setup-host
bash scripts/setup-host.sh --check    # prove the toolchain is actually installed
```

Everything at once is the green build bar:

```bash
bazelisk run //:validate
```

Pick a lane from this table; each row runs the whole set for that job.

| You want to | Command |
| --- | --- |
| Run the fast lane CI runs (bats, pytest, typecheck, JS, inventory) | `bazelisk test //:test-fast` |
| Run every gate, including manual linters, the Playwright visual suite, and the Compose config check (needs host linters, the pinned docs-site npm tree, and a Docker CLI) | `bazelisk test //:test-all` |
| Run the linters only | `bazelisk test //:lint --test_tag_filters=manual` |
| Format what the linters flagged | `bazelisk run //:fix` |
| Check first-party Python coverage (100% fail-under) | `bazelisk test //:coverage` |
| Check types (Pyright + mypy) | `bazelisk test //tests:typecheck` |
| Run the nothing-goes-unmapped guard (every tracked file is in a Bazel target) | `bazelisk test //:owned_files_check` |
| Check the compose file the stack actually starts | `bazelisk test //docker:compose_config` |
| Check stack health against the real checkout | `bazelisk run //:manage -- doctor` |
| Build the docs: generators plus static export | `bazelisk run //docs:docs` |
| Run the docs generators on their own | `bazelisk run //docs:generate` |
| Serve the docs locally | `bazelisk run //docs:serve` |
| Rebuild derived frontend data (the Quality tier table comes from `custom_nodes/ez_quality/presets.py`, and `bazelisk test //:test-fast` fails if the generated JS drifts) | `bazelisk run //tests:build_quality_js` |

## Safety

- Compose `restart: "no"` - manual start only
- Heavy confirmation + free RAM/disk headroom
- Download throttle by default; wrap **clears on exit**
- One heavy GPU job at a time - park or stop before another desk takes the chip
- See [Reboot safety](docs/reboot-safety.mdx) before you reboot a Spark you reach over SSH

## License

MIT - see [LICENSE](LICENSE).
