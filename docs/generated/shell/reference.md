---
title: Generated shell reference
description: Auto-generated manage.sh and utility reference from structured comments in scripts/.
tags: [cli, manage, generated, reference]
---

# Generated shell reference

**What's on this page**

- **Commands and helpers** extracted from `# ##`, `# @command`, and `# @function` comments
- **Usage fences** that keep session variables such as `${SPARK_HOST}` and `${MODELS_DIR}`
- **Safety notes** turned into admonitions

**What this enables**

- **Looking up** a verb next to the comment that ships in the script
- **Keeping** [manage.sh reference](../../manage-cli.md) a scan catalog while this page stays generated

> Generated from structured comments in `scripts/`. Edit the source comments and re-run
> `python3 docs/generate_shell_docs.py` (or `make docs`). Do not hand-edit this file.

<!-- source: scripts/manage.sh -->
## manage

Operator CLI for the ez-comfy-stack unified Visual Generative AI demo
(ComfyUI US-safe local studio on a single NVIDIA DGX Spark).

Purpose:
  Single entrypoint for day-to-day stack lifecycle: preflight (doctor), status,
  start/stop/restart, logs, model downloads (bandwidth-limited by default), and
  cleanup of the Comfy state volume. Keeps heavy GPU work explicit and safe for
  remote-SSH operation.

```bash
Usage:
  ./scripts/manage.sh help|setup|doctor|status|start|stop|restart|logs|download-models [--limit auto|N|off] [--drop-incomplete]|download-podcast [--tier analog|acestep|chatterbox|qwen3tts|all] [--limit auto|N|off]|download-dub [--tier asr|clone|all] [--limit auto|N|off]|download-music [--tier turbo|xl|all] [--limit auto|N|off]|download-llm [--tier enhance|qwen36-35b-a3b|all] [--limit auto|N|off]|cleanup
  ./scripts/manage.sh reset-hf-partials [--yes] [--force]
  ./scripts/manage.sh download-limit status|run|clear|wrap ...

```

!!! warning

    Safety:
      - Manual start only (compose restart: "no")
      - Heavy confirmation for start/restart
      - Host free-memory/disk headroom checks before start
      - Model downloads default to bandwidth-limited (download-limit auto @ 85%)
      - Always stop before node reboot
      - setup may use sudo only to create/chown MODELS_DIR#
    Environment:
      See .env.example — MODELS_DIR, HF_TOKEN, MEM_LIMIT, DOWNLOAD_LIMIT,
      LAB_NON_INTERACTIVE, LAB_CONFIRM_TOKEN, MIN_HOST_FREE_GIB, etc.

Exit codes:
  0 — success or interactive user abort on confirm
  1 — hard failure (preflight, docker, missing confirm token, unknown command)

### Command: manage

### Command: help

Print the human-facing command list and environment pointer to stdout.
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  Always 0.

### Command: setup

Bootstrap host prerequisites for doctor/download/start.
Creates .env from example if missing; prepares MODELS_DIR (sudo mkdir/chown);
installs Docker CE when missing (confirm / --install-docker); installs hf CLI
when missing; soft-checks GPU; then runs doctor.
Side effects: May write .env; may sudo for MODELS_DIR and package install.
Globals:
  REPO_ROOT, MODELS_DIR, LAB_NO_SUDO, SETUP_INSTALL_DOCKER, SETUP_YES
Arguments:
  Optional: --install-docker  force docker install path
            --yes             skip install confirmation
Outputs:
  Status via log/warn/err on stderr
Returns:
  0 when doctor passes; 1 when host still not ready

### Command: doctor

Run operator preflight checks without starting the stack.
Validates Docker + Compose, optional nvidia-smi, hf CLI presence (soft),
MEM_LIMIT budget warning, host free RAM/disk headroom, MODELS_DIR presence,
flux/ltx readiness JSON, and existence of the compose file.
Side effects: May invoke docker, nvidia-smi, download-*-status (no network pull).
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  0 when all hard checks pass; 1 if any hard check fails.

### Command: status

Show human-readable or JSON status of the Compose project.
Globals:
  See file header / caller environment.
Arguments:
  $1  Optional `--json` for machine-readable compose_status_json on stdout.
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  0 after printing; docker failures are warned, not always fatal.

### Command: start

Confirm, check headroom, then start the unified studio Compose stack.
Returns after compose up -d + verify; the stack is not tied to this shell.
Side effects: May build/start containers; requires operator confirmation.
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  0 on success or interactive abort; 1 on failed confirm/headroom/compose.

### Command: stop

Stop stack containers while retaining volumes and the host model cache.
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  Exit status of stack_stop.

### Command: restart

Stop then start (re-runs full start confirmation and headroom checks).
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  Exit status of the final start path.

### Command: logs

Follow Docker Compose logs for the stack.
Globals:
  See file header / caller environment.
Arguments:
  $@  Extra args for `compose logs -f` (service filter, --tail, etc.).
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  0 on success; non-zero on failure where applicable.

### Command: clear-hf-locks

Clear stale Hugging Face download locks under MODELS_DIR.
Globals:
  MODELS_DIR
Arguments:
  None
Outputs:
  Status via log/warn
Returns:
  0

### Command: reset-hf-partials

Delete HF *.incomplete partials so a hung resume can start that file fresh.
Refuses while hf download is running unless --force.
Globals:
  MODELS_DIR, LAB_NON_INTERACTIVE, LAB_MOCK_HF_RUNNING
Arguments:
  Optional: --yes  skip confirm; --force  allow while hf is running
Outputs:
  Status via log/warn/err
Returns:
  0 on success or abort; 1 on usage error or running hf without --force

### Command: download-models

Download lab weights under MODELS_DIR with bandwidth limits.
DOWNLOAD_LIMIT (auto|N|off) is the default; --limit overrides for this run.
wrap always clears shaping on exit. off|0 skips throttle (SSH risk).
Globals:
  DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
Arguments:
  Optional: --limit auto|N|off
Outputs:
  Status via log/warn/err on stderr
Returns:
  0 when lab files are ready; 1 on usage error or incomplete weights

### Command: download-podcast

Opt-in podcast weights under MODELS_DIR with the same download-limit wrap.
Missing analog pack is not a doctor failure. Does not change download-models.
Globals:
  DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
Arguments:
  Optional: --tier analog|acestep|chatterbox|qwen3tts|all
            --limit auto|N|off
Outputs:
  Status via log/warn/err
Returns:
  0 on success; 1 on usage or download failure

### Command: download-dub

Opt-in dub weights under MODELS_DIR with the same download-limit wrap.
Missing ASR/clone pack is not a doctor failure. Does not change download-models.
With compose up, pip-installs faster-whisper, the llama-cpp-python CPU
wheel, then the Chatterbox V3 zip.
Globals:
  DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
Arguments:
  Optional: --tier asr|clone|all
            --limit auto|N|off
Outputs:
  Status via log/warn/err
Returns:
  0 on success; 1 on usage or download failure

### Command: download-music

Opt-in ACE-Step music weights under MODELS_DIR with the same download-limit wrap.
Missing turbo AIO is not a doctor failure. Does not change download-models.
turbo dest is the podcast acestep snapshot (do not pull the 10 GB AIO twice).
Globals:
  DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
Arguments:
  Optional: --tier turbo|xl|all
            --limit auto|N|off
Outputs:
  Status via log/warn/err
Returns:
  0 on success; 1 on usage or download failure

### Command: download-limit

Proxy remaining argv to scripts/utilities/download-limit.sh.
Globals:
  See file header / caller environment.
Arguments:
  $@  Forwarded subcommand and flags (status|run|clear|wrap …).
Outputs:
  Status via log/warn/err on stderr unless noted.
Returns:
  0 on success; non-zero on failure where applicable.

### Command: print-shot

Dispatch print-shot to utilities/print-shot.sh.
Globals:
  REPO_ROOT
Arguments:
  $@  film id [shot id]
Outputs:
  print-shot logs
Returns:
  print-shot status

### Command: film-resume

Resume a film (skip ok shots with valid duration).
Globals:
  REPO_ROOT
Arguments:
  $1  film id
Outputs:
  print-shot logs
Returns:
  print-shot status

### Command: film-export-otio

Export OTIO timeline from a film jobstore.
Globals:
  REPO_ROOT
Arguments:
  $1  film id
Returns:
  film-export-otio status

### Command: film-proxies

NVENC proxies for a film (refuse if compose is up).
Globals:
  REPO_ROOT
Arguments:
  $@  film id and flags
Returns:
  film-proxies status

### Command: take-promote

Promote a take into shots/NN.mp4.
Globals:
  REPO_ROOT
Arguments:
  $1  film
  $2  shot id
  $3  take number

### Command: promote-workflow

Copy a live user graph into the repo lab tree. Does not commit.
Globals:
  REPO_ROOT
Arguments:
  $@  promote-workflow flags
Returns:
  promote-workflow status

### Command: album-render

Queue a shipped music album then zip the output folder.
Globals:
  REPO_ROOT
Arguments:
  $@  album-render flags
Returns:
  album-render status

### Command: download-restore

Opt-in restore pack download (SeedVR2-3B). Does not reap. Not download-models.
Globals:
  REPO_ROOT
Arguments:
  $@  download-restore flags
Returns:
  download-restore status

### Command: download-3d

Opt-in 3D packs (TRELLIS.2 native, DA3-BASE).

### Command: download-llm

Opt-in / default LLM GGUF packs with the same download-limit wrap.
enhance is already in download-models. qwen36-35b-a3b is occupancy llm-desk.
Missing 35B pack is not a doctor failure.
Globals:
  DOWNLOAD_LIMIT, MODELS_DIR, REPO_ROOT
Arguments:
  Optional: --tier enhance|qwen36-35b-a3b|all
            --limit auto|N|off
Outputs:
  Status via log/warn/err
Returns:
  0 on success; 1 on usage or download failure

### Command: occupancy

Occupancy desk (park / enter / status).

### Command: llm-sidecar

Host llama-server sidecar (occupancy llm-desk).

### Command: blender-mcp

In-tree Blender MCP (typed tools, occupancy-aware).

### Command: research-mcp

In-tree creative research MCP (typed tools, occupancy-aware).

### Command: studio-mcp

In-tree studio MCP (clone lab graphs into _user/; no Queue).

### Command: blender-llm

Optional on-box Qwen3-4B CPU client for blender-mcp.

### Command: blender

Host Blender sidecar (refuses if Comfy is a heavy job).

### Command: blender-install

Host apt install of Ubuntu blender (never in docker/Dockerfile).

### Command: export-guides

Occupancy-gated Blender guide-pack dump (P0). Godot is P2.
Globals:
  REPO_ROOT
Arguments:
  $@  blender-guide.sh flags
Returns:
  blender-guide status (2 if compose is up)

### Command: blender-stills

Occupancy-gated Blender still-pack dump (P0). Godot is P2.
Globals:
  REPO_ROOT
Arguments:
  $@  blender-stills.sh flags
Returns:
  blender-stills status (2 if compose is up)

### Command: house-views

Occupancy-gated Blender Instagram clay dump (P0). Godot is P2.
Globals:
  REPO_ROOT
Arguments:
  $@  house-views.sh flags
Returns:
  house-views status (2 if compose is up)

### Command: asset-ls

Read-only Asset Bible catalog (outputs under COMFY_OUTPUT_DIR/assets).
Globals:
  REPO_ROOT
Arguments:
  $@  asset-ls.sh flags (--json, --output-dir DIR)
Outputs:
  Catalog listing or JSON on stdout
Returns:
  asset-ls.sh status

### Command: film-accept

Fail-closed accept gate before 90s concat.

### Command: shot-sheet

Write films/<slug>/shots.yaml with shot-card defaults.

### Command: overlay-qc

Clay vs look overlay QC (host ffmpeg, no GPU).

### Command: film-animatic

Cheap 90s animatic from clay or held stills.

### Command: stem-mix

Picture-lock stem mix (CPU ffmpeg).

### Command: audio-still-video

Mux a still + audio master to YouTube MP4 (CPU ffmpeg).
Globals:
  REPO_ROOT
Arguments:
  $@  audio-still-video.sh flags (--audio, --image, --out, --size, --fit)
Outputs:
  Status on stderr; MP4 on disk
Returns:
  audio-still-video.sh status

### Command: download-longcat

Opt-in LongCat-Video (MIT, no NCCL).

### Command: download-dreamx

Opt-in DreamX-Creator 1.0 (Apache; not World).

### Command: spark-timing

Kitchen smoke wall-clock table (operator-measured; CI has no GPU).
Globals:
  REPO_ROOT
Arguments:
  $@  show|record --klein N --wan N --ltx N [--json]
Outputs:
  Status on stderr; JSON on stdout with --json
Returns:
  spark-timing.sh status

### Command: models-status

Print keep-set / refuse from the disk bible (does not delete).
Globals:
  REPO_ROOT
Arguments:
  $@  models-manifest.sh args
Outputs:
  status logs
Returns:
  0

### Command: reap-models

Dispatch reap-models (default --plan).
Globals:
  REPO_ROOT
Arguments:
  $@  reap-models flags
Outputs:
  plan/apply logs
Returns:
  reap-models status

### Command: disk-wizard

Dispatch disk-wizard (default --plan / TTY wizard).
Globals:
  REPO_ROOT
Arguments:
  $@  disk-wizard flags
Outputs:
  plan/apply logs
Returns:
  disk-wizard status

### Command: cleanup

After DELETE confirmation, remove Compose volumes (Comfy install state only).
Globals:
  See file header / caller environment.
Arguments:
  None
Outputs:
  Status via log/warn/err
Returns:
  0 on success/abort; 1 on hard confirm failure

<!-- source: scripts/lib/blender_host.sh -->
## blender_host

Resolve a host Blender binary for Workbench dumps. Never in docker/Dockerfile.
Source after scripts/lib/common.sh (uses err). Not executable.

!!! warning

    Safety:
      Does not start Compose. Does not apt-install unless blender-install.sh
      is invoked. Does not weaken restart: "no", headroom, or download-limit.

<!-- source: scripts/lib/check_tool.sh -->
## check_tool helper

Resilient tool checker used by lints/run_*.sh and CI installers.
By default, a missing tool prints a message and exits 0 so local runs can
continue when optional linters are not installed.

When CI=true or REQUIRE_LINT_TOOLS=1, a missing tool is fatal (exit 1).

### Function `check_tool`

```bash
Usage:
```

  source "$(dirname "$0")/../lib/check_tool.sh"
  check_tool shellcheck "apt install shellcheck"

!!! warning

    Safety: Read-only PATH probe. No GPU, Docker, or network.

<!-- source: scripts/lib/common.sh -->
## common

Shared logging, fatal helpers, and environment loading for ez-comfy-stack.

Purpose:
  Keep operator diagnostics consistent (prefixed; always on stderr) so stdout
  remains free for machine-readable data such as --json payloads.

Audience:
  Sourced by manage.sh and utilities after paths.sh. Not executable alone.

Style:
  Google Shell Style Guide (project deviations in docs/project-conventions.md).
  All error/status messages go to STDERR (Google S3).

<!-- source: scripts/lib/compose.sh -->
## compose

Docker Compose wrappers for the unified ComfyUI US-safe studio stack.

Purpose:
  Isolate every docker/compose invocation behind helpers that pin the project
  file (`docker/docker-compose.yml`) and project name (`ez-comfy`). This keeps
  manage.sh thin and makes hermetic tests able to inject COMPOSE_BIN mocks.

Audience:
  Sourced by manage.sh after paths.sh and common.sh.

Environment:
  MODELS_DIR, COMFY_PORT, MEM_LIMIT, MEM_RESERVATION — exported into compose
  COMPOSE_BIN — optional full command override for tests (space-separated ok)
  LAB_STACK_FOLLOW — 1 = stream logs until UI port is open (default 0: detach)

!!! warning

    Safety:
      stack_start does not ask for confirmation (caller must require_heavy_confirm).
      stack_start ignores SIGHUP so an SSH drop does not abort compose up.
      stack_start returns after up -d + verify; it does not stay bound to the shell.
      stack_cleanup_state removes named volumes but never deletes host MODELS_DIR.
      restart: "no" is unchanged — logout is not a reboot and does not auto-start.

<!-- source: scripts/lib/disk_scan.sh -->
## disk_scan

Read-only filesystem / docker survey helpers for disk-wizard.
Source after common.sh. Not executable.

!!! warning

    Safety:
      Does not delete. Realpath jail. Hermetic tests set LAB_HERMETIC=1 and
      DISK_WIZARD_HOME so $HOME is never walked on a developer laptop.

<!-- source: scripts/lib/films.sh -->
## films

Shared film catalog helpers for host utilities (slug, cap, shot count).

Purpose:
  One lookup for shipped film ids so concat / accept / compile / print-shot
  do not copy go-see|still-here|switchyard case maps. Reads
  custom_nodes/ez_film/catalog.py via python3.

Audience:
  Sourced by film utilities after common.sh. Requires REPO_ROOT.

Style:
  Google Shell Style Guide (project deviations in docs/project-conventions.md).

<!-- source: scripts/lib/models.sh -->
## models

Shared keep-set / realpath / MODELS_DIR safety for reap-models.

Audience: sourced by reap-models.sh and models-manifest.sh.

<!-- source: scripts/lib/occupancy.sh -->
## occupancy

Mode machine for one heavy GPU job on GB10.
Source after scripts/lib/compose.sh. Not executable.

!!! warning

    Safety:
      One heavy GPU job: klein / trellis / wan / ltx, or host NVENC, or llm-desk.
      blender-desk is Workbench after POST /free (parked Comfy), not a second CUDA job.
      llm-desk is host llama-server after POST /free, XOR with blender-desk and visual.
      Does not weaken restart: "no", mem_limit 90g, or headroom.

<!-- source: scripts/lib/paths.sh -->
## paths

Path resolution helpers for ez-comfy-stack operator scripts and utilities.

Purpose:
  Provide a single way to locate the repository root, Docker Compose file, and
  shared model cache without hard-coding absolute paths.

Audience:
  Sourced by entry scripts under scripts/ and scripts/utilities/. Not executable.

Style:
  Follows the Google Shell Style Guide with project deviations documented in
  docs/project-conventions.md (notably #!/usr/bin/env bash).

Environment:
  REPO_ROOT   — optional override for the repository root (must be a directory)
  MODELS_DIR  — optional override for the shared model cache (default /mnt/models)

<!-- source: scripts/lib/progress.sh -->
## progress

Shared operator progress (bars, heartbeats, ffmpeg) for ez-comfy-stack.
Sourced from common.sh after log/warn/err. Not executable alone.

Contract: live updates on stderr only. Stdout stays --json / data.
TTY rewrites one line; non-TTY (CI, pipes) emits periodic newlines.

<!-- source: scripts/lib/safety.sh -->
## safety

Preflight checks, heavy confirmation, and host headroom for remote Spark safety.

Purpose:
  DGX Spark hosts are often operated over the internet without physical access.
  Starting a 90 GiB-class ComfyUI stack without free RAM/disk headroom can make
  SSH unresponsive. This library enforces explicit operator consent and minimum
  free resources before heavy work begins.

Invariants:

  - Heavy workloads never auto-start (Compose restart policy is "no"; this lib
    only gates explicit start paths).

  - Interactive start requires typing "yes" (case-insensitive full word).

  - Non-interactive automation requires LAB_NON_INTERACTIVE=1 and a matching
    LAB_CONFIRM_TOKEN (yes for start, DELETE for cleanup).

Audience:
  Sourced by manage.sh (and tests). Depends on common.sh (log/warn/err) and
  paths.sh (lab_models_dir) being available in the caller.

Environment (defaults applied if unset):
  MIN_HOST_FREE_GIB   — minimum free host RAM in GiB (default 28)
  MIN_DISK_FREE_GIB   — minimum free disk on models path in GiB (default 40)
  MEM_LIMIT           — Docker mem_limit string, e.g. 90g (default 90g)
  LAB_MOCK_FREE_MEM_GIB / LAB_MOCK_DISK_FREE_GIB — hermetic test overrides
  LAB_NON_INTERACTIVE / LAB_CONFIRM_TOKEN — automation confirm path

<!-- source: scripts/utilities/album-render.sh -->
## album-render

Queue one shipped music album on local ComfyUI, then zip the folder.

Purpose:
  One-go album: optional Klein cover, then each ACE-Step track, then pack.
  Sequential occupancy (klein XOR audio). Does not start compose.

```bash
Usage:
  ./scripts/utilities/album-render.sh status [--json]
  ./scripts/utilities/album-render.sh run --album ARTIST/SLUG
```

      [--art skip|upload|generate] [--image FILE] [--out DIR] [--dry-run]

```bash
  ./scripts/utilities/album-render.sh pack --album ARTIST/SLUG [--out DIR]

```

Environment:
  COMFY_OUTPUT_DIR, COMFY_PORT (default 8188), COMFY_URL, REPO_ROOT

!!! warning

    Safety:
      Does not start Docker. Does not change restart: "no". Sequential Queue.
      generate unloads models (POST /free) between cover and tracks.

Exit codes:
  0 success / dry-run; 1 usage / missing compose / queue failure.

### Command: album-render

<!-- source: scripts/utilities/asset-ls.sh -->
## asset-ls

Read-only Asset Bible catalog (status-like). Lists slugs under
COMFY_OUTPUT_DIR/assets. Does not download, Queue, or write.

```bash
Usage:
  ./scripts/utilities/asset-ls.sh [--json] [--output-dir DIR]

```

Environment:
  COMFY_OUTPUT_DIR — default catalog is ${COMFY_OUTPUT_DIR}/assets

!!! warning

    Safety:
      Assets are outputs, never MODELS_DIR. Occupancy unchanged.

### Command: asset-ls

<!-- source: scripts/utilities/audio-still-video.sh -->
## audio-still-video

Mux a user-supplied still with an audio master into a YouTube-ready MP4.
Host ffmpeg (libx264 stillimage + AAC). Does not change audio lab graphs.

Purpose:
  After Queue, turn FLAC/MP3 + a cover/thumbnail into H.264+AAC with
  +faststart so YouTube ingest accepts a still-image video.

```bash
Usage:
  ./scripts/utilities/audio-still-video.sh status [--json]
  ./scripts/utilities/audio-still-video.sh run --audio FILE --image FILE [--out FILE]
```

      [--size 1920x1080|1280x720|1080x1920] [--fit letterbox|crop|stretch]
      [--loudnorm off|youtube] [--dry-run]

Environment:
  COMFY_OUTPUT_DIR (not required; default --out is next to --audio)

!!! warning

    Safety:
      Does not start Docker. CPU encode; compose may stay up. Fails if ffmpeg
      is missing. Does not load ACE-Step / Klein / Wan / LTX.

Exit codes:
  0 success or dry-run; 1 usage / missing ffmpeg / mux failure.

### Command: audio-still-video

<!-- source: scripts/utilities/blender-guide.sh -->
## blender-guide

Occupancy-gated Blender dump of an ez.guide.shot.v1 pack (clay / depth /
first+last at 1280x704, 120 frames @ 24 fps). Never in docker/Dockerfile.

```bash
Usage:
  ./scripts/utilities/blender-guide.sh --film go-see --shot 12 [--blend FILE]
  ./scripts/utilities/blender-guide.sh --engine blender --film go-see --shot 12

```

!!! warning

    Safety:
      Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
      Software ffmpeg mux (pack-frames.sh) — not NVENC.

Exit codes:
  0 success; 1 usage / missing blender / QC fail; 2 compose running

### Command: export-guides

<!-- source: scripts/utilities/blender-install.sh -->
## blender-install

Host apt install of Ubuntu blender for Workbench dumps. Never in
docker/Dockerfile. Occupancy does not install Blender.

```bash
Usage:
  ./scripts/utilities/blender-install.sh
  ./scripts/manage.sh blender-install

```

!!! warning

    Safety:
      Host package only. Does not start Compose. Does not weaken restart: "no",
      headroom, or download-limit clear-on-exit. Does not fetch unofficial
      aarch64 CUDA tarballs.

Environment:
  BLENDER_BIN, LAB_MOCK_BLENDER_INSTALL, LAB_MOCK_BLENDER_BIN_DIR, LAB_NO_SUDO

### Command: blender-install

<!-- source: scripts/utilities/blender-llm.sh -->
## blender-llm

Optional on-box Qwen3-4B CPU client for blender-mcp. Fail-soft: if host
llama.cpp is missing, print the Path D hint (laptop MCP client).
Never GPU-offload. Never in docker/Dockerfile.

```bash
Usage:
  ./scripts/utilities/blender-llm.sh "greybox mug on a table"
```

### Command: blender-llm

<!-- source: scripts/utilities/blender-mcp.sh -->
## blender-mcp

In-tree Blender MCP (typed tools, no execute_code, no telemetry).
Host only — never in docker/Dockerfile. bpy tools require blender-desk.

```bash
Usage:
  ./scripts/utilities/blender-mcp.sh [--stdio]
  ./scripts/utilities/blender-mcp.sh --list-tools
  ./scripts/utilities/blender-mcp.sh --call TOOL [JSON]
```

### Command: blender-mcp

<!-- source: scripts/utilities/blender-stills.sh -->
## blender-stills

Occupancy-gated Blender dump of an ez.guide.still.v1 plate (single-frame
clay / depth / canny at creator sizes). Never in docker/Dockerfile.

```bash
Usage:
  ./scripts/utilities/blender-stills.sh --film go-see --plate mug --blend FILE
  ./scripts/utilities/blender-stills.sh --film go-see --plate mug --size 1024x1024

```

!!! warning

    Safety:
      Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
      --install-inputs copies first.png into COMFY_OUTPUT_DIR/input (compose may stay up).

Exit codes:
  0 success; 1 usage / missing blender / QC fail; 2 compose running

### Command: blender-stills

<!-- source: scripts/utilities/blender.sh -->
## blender

Host Blender sidecar. Dies if compose is a heavy job (occupancy).
blender-desk (parked via POST /free) allows Workbench. Never in
docker/Dockerfile — GB10 DCC stays on the host. See docs/occupancy.md.

```bash
Usage:
  ./scripts/utilities/blender.sh [--] [blender args]
```

### Command: blender

<!-- source: scripts/utilities/compile-film.sh -->
## compile-film

Compile workflows/shorts/{film}.shots.yaml into films/<slug>/ jobstore.

Purpose:
  Emit film.yaml, state.json (18 pending shots), and shots/NN.json stubs
  from the YAML bible. Does not Queue Comfy. Does not start Docker.

```bash
Usage:
  ./scripts/utilities/compile-film.sh FILM

```

Environment:
  COMFY_OUTPUT_DIR — default /mnt/comfy-output

Exit codes:
  0 success; 1 usage / parse error

### Command: compile-film

<!-- source: scripts/utilities/compress-cinema-clip.sh -->
## compress-cinema-clip

Re-encode a Cinema Rack illustration MP4 to muted 854x480 H.264 and
write a JPEG poster. Host ffmpeg. Does not start Docker.

Purpose:
  Keep encyclopedia clips small enough for Git LFS (target ≤512KiB).

```bash
Usage:
  ./scripts/utilities/compress-cinema-clip.sh --in FILE --out FILE
```

      [--poster FILE] [--crf 28] [--max-bytes 524288] [--dry-run]

!!! warning

    Safety:
      Does not start Docker. CPU encode; compose may stay up. Fails if
      ffmpeg is missing.

Exit codes:
  0 success or dry-run; 1 usage / missing ffmpeg / size cap.

### Command: compress-cinema-clip

<!-- source: scripts/utilities/concat-shots.sh -->
## concat-shots

Concatenate approved 5 s lab MP4s with ffmpeg (host / spark-farm fallback).

Purpose:
  Concatenate approved 5.00 s lab MP4s. Default glob is six ez_shot_01..06
  files. --film joins a catalog film in beat/shot order (18×5s / 90s, or
  90×5s / 450s) and caps at the film's publish_cap_s. Video is
  libx264 CRF 18 (stream-copy fallback); audio is AAC + YouTube loudnorm +
  faststart (same contract as EZFilmConcat).

```bash
Usage:
  ./scripts/utilities/concat-shots.sh [--dir DIR] [--out FILE] [--dry-run|--yes]
  ./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 [--out FILE]
  ./scripts/utilities/concat-shots.sh --film FILM [--yes]
  ./scripts/utilities/concat-shots.sh --film go-see --xfade 10 --yes

```

Environment:
  COMFY_OUTPUT_DIR — default /mnt/comfy-output
  Default glob: ez_shot_0{1..6}*.mp4
  --film: ez_<slug>_b{1..beats}_s{1..3}_ltx_video*.mp4 (prefers *-audio.mp4; fallback _wan_video)
  --cap-seconds: publish cap (default from catalog, else 90)

!!! warning

    Safety:
      Does not start Docker. Dry-run by default unless --yes.

Exit codes:
  0 success / dry-run; 1 usage or ffmpeg failure.

### Command: concat-shots

<!-- source: scripts/utilities/disk-wizard.sh -->
## disk-wizard

Guided, plan-first reclaim for leftover AI experiment files on a DGX Spark.
Does not overload manage.sh cleanup (volume-only) or reap-models (MODELS_DIR).

```bash
Usage:
  ./scripts/utilities/disk-wizard.sh --plan
  ./scripts/utilities/disk-wizard.sh --json
  ./scripts/utilities/disk-wizard.sh --apply --yes
  ./scripts/utilities/disk-wizard.sh restore --from .disk-quarantine/<utc>

```

!!! warning

    Safety:
      Default is --plan (read-only). --apply requires --yes.
      Review-class items quarantine. Dangerous / keep-set / ez-comfy-state refused.
      Never offers docker system prune -a --volumes.
      Does not weaken restart: no, start confirm, headroom, or download-limit.

### Command: disk-wizard

<!-- source: scripts/utilities/download-3d.sh -->
## download-3d

Opt-in 3D packs: native Comfy-Org TRELLIS.2 INT8 (MIT, no nvdiffrast) and
DA3-BASE (Apache). Never part of download-models. occupancy enter trellis
first (unload LTX). SuperSplat is a host viewer (docs/splat-sidecar.md).

```bash
Usage:
  ./scripts/utilities/download-3d.sh status|run [--tier trellis2|da3-base|all] [--json]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Occupancy: do not coreside with LTX/Wan denoise. DA3-LARGE is refused.

### Command: download-3d

<!-- source: scripts/utilities/download-dreamx.sh -->
## download-dreamx

Opt-in DreamX-Creator 1.0 (Apache joint AV). Never DreamX-World.
Not download-models. Unload LTX first.

```bash
Usage:
  ./scripts/utilities/download-dreamx.sh status|run [--tier creator|all] [--json]
```

### Command: download-dreamx

<!-- source: scripts/utilities/download-dub.sh -->
## download-dub

Opt-in Hugging Face pull for US-safe dub (ASR + multilingual clone) weights.

Purpose:
  Selective download of Silero VAD, faster-whisper large-v3, and Chatterbox
  Multilingual V3. Never part of download-models. Missing pack is not a
  doctor failure.

Audience:
  Operators on the Spark host. Prefer manage.sh download-dub.

```bash
Usage:
  ./scripts/utilities/download-dub.sh status|run|cleanup [--tier asr|clone|all] [--json]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Opt-in only. Use download-limit wrap on remote SSH.
      Refuses F5-TTS, XTTS, Fish, MiniMax H3, NLLB, SeamlessM4T, Wav2Lip,
      TTS-Audio-Suite, celebrity clone flags.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-dub

<!-- source: scripts/utilities/download-image.sh -->
## download-image

Download Apache FLUX.2 Klein 4B (and optional stills) into MODELS_DIR.

Purpose:
  Selective Hugging Face pull for the studio still generator.
  Default: Klein 4B distilled FP8 + Qwen3-4B TE + flux2 VAE (Apache 2.0).
  Opt-in FLUX Non-Commercial: 9b / 9b-base / 9b-nvfp4 / flux2-dev (gated, not YouTube-ok).

Audience:
  Operators on the Spark host. Prefer manage.sh download-models.

```bash
Usage:
  ./scripts/utilities/download-image.sh status [--tier fast|nvfp4|base|zimage|all|9b|9b-base|9b-nvfp4|small-vae|flux2-dev] [--json]
  ./scripts/utilities/download-image.sh run [--tier ...]
  ./scripts/utilities/download-image.sh cleanup [--tier ...] [--dry-run|--yes]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Large downloads — use download-limit wrap on remote SSH.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-image

<!-- source: scripts/utilities/download-limit.sh -->
## download-limit

Limit host download bandwidth so multi‑GB model pulls cannot starve remote SSH.

Purpose:
  Apply kernel traffic shaping via wondershaper on the default-route interface.
  Supports fixed Mbps caps and an **auto** mode that measures download Mbps
  (duration HTTP probe first, then Ookla, then speedtest-cli) and applies
  floor(0.85 × measured_download_mbps). Auto measurements are cached 24h on the
  host (not MODELS_DIR). Apply is verified via tc qdisc (or mocks).
  The wrap subcommand always clears limits on EXIT/INT/TERM so a killed download
  cannot leave the host permanently throttled. If apply fails, wrap soft-fails
  (warn + continue unthrottled) unless DOWNLOAD_LIMIT_REQUIRE=1.

Audience:
  Operators on remotely managed DGX Spark nodes; also invoked by manage.sh
  download-models.

```bash
Usage:
```

  download-limit.sh status [--json] [--refresh]
  download-limit.sh run --limit auto|N [--fallback N] [--refresh]
  download-limit.sh clear
  download-limit.sh wrap --limit auto|N [--refresh] -- <command...>

Requirements:

  - sudo (unless LAB_NO_SUDO=1 for mocks)

  - wondershaper (best-effort auto-install on apt/dnf/pacman)

  - HTB/sch_* kernel modules for real shaping

  - speedtest-cli or Ookla speedtest for auto mode (optional with fallback)

Test hooks:
  LAB_MOCK_IFACE, LAB_MOCK_WONDERSHAPER, LAB_MOCK_SPEEDTEST_MBPS,
  LAB_MOCK_HTTP_SPEED_MBPS, LAB_MOCK_LIMITS_ACTIVE, LAB_NO_SUDO,
  DOWNLOAD_LIMIT_REQUIRE, DOWNLOAD_LIMIT_CACHE_DIR, DOWNLOAD_LIMIT_CACHE_TTL_SEC

Units:
  Limits are megabits per second (Mbps), not MB/s. 40 Mbps ≈ 5 MB/s.
  Wondershaper rates are clamped to a legal HTB kbps range.

Exit codes:
  0 success (or wrap soft-fail with command success); 1 invalid args,
  missing interface, or hard apply failure (run / REQUIRE wrap).

### Command: download-limit

<!-- source: scripts/utilities/download-llm.sh -->
## download-llm

Download on-box GGUF packs: default prompt-enhance 4B, optional 35B desk.

Purpose:
  Selective Hugging Face pull. Apache 2.0. File-level include — not the
  full Unsloth GGUF tree. Default enhance pack is part of download-models.
  Opt-in qwen36-35b-a3b is occupancy llm-desk only (not download-models).

Audience:
  Operators on the Spark host. Prefer manage.sh download-llm / download-models.

```bash
Usage:
  ./scripts/utilities/download-llm.sh status|run|cleanup|link [--tier enhance|qwen36-35b-a3b|all] [--json]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      enhance ~3 GB (in download-models). 35B ~23 GB opt-in. Use download-limit
      wrap on remote SSH. Does not weaken restart: "no", headroom, or
      download-limit clear-on-exit.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-llm

<!-- source: scripts/utilities/download-longcat.sh -->
## download-longcat

Opt-in LongCat-Video (MIT). Second stack, not download-models.
Context-parallel two-Spark only behind LAB_ALLOW_CONTEXT_PARALLEL=1.
NCCL is out of this sample stack.

```bash
Usage:
  ./scripts/utilities/download-longcat.sh status|run [--tier video|avatar|all] [--json]
```

### Command: download-longcat

<!-- source: scripts/utilities/download-ltx.sh -->
## download-ltx

Download LTX-2.5 distilled INT8-convrot (default) or LTX-2.3 fallback.

Purpose:
  Fetch the small distilled AV set for lab graphs (not the 400 GB monorepo).
  Default 2.5: Lightricks/LTX-2.5 INT8-convrot + Gemma4-with-proj + VAEs.
  Fallback 2.3: Kijai/LTX2.3_comfy distilled FP8 + Gemma 3 DualCLIP.
  LTX Community License ($10M company-revenue cap) — not Apache. Gated HF.

Audience:
  Operators preparing a Spark host for manage.sh start. Prefer
  manage.sh download-models for throttled sequential flux+ltx pulls.

```bash
Usage:
  ./scripts/utilities/download-ltx.sh status [--tier 2.5|2.3|balanced|quality|gemma|iclora|all] [--json]
  ./scripts/utilities/download-ltx.sh run [--tier ...]
  ./scripts/utilities/download-ltx.sh cleanup [--tier ...] [--dry-run|--yes]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD — same semantics as download-flux.
  LTX_FULL_REPO=1 — download entire Kijai/LTX2.3_comfy snapshot (all variants).

!!! warning

    Safety:
      Multi‑GB transfer — use download-limit when on remote SSH.
      cleanup defaults to --dry-run; --yes deletes only non-selective files under
      the tier local-dir (never other MODELS_DIR trees like FLUX).

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-ltx

<!-- source: scripts/utilities/download-music.sh -->
## download-music

Opt-in Hugging Face pull for US-safe local ACE-Step music weights.

Purpose:
  Selective download of ACE-Step 1.5 turbo AIO (default) and optional XL
  split files. Never part of download-models. Turbo reuses the podcast
  acestep snapshot so the ~10 GB AIO is not pulled twice.

Audience:
  Operators on the Spark host. Prefer manage.sh download-music.

```bash
Usage:
  ./scripts/utilities/download-music.sh status|run|cleanup [--tier turbo|xl|all] [--json]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Opt-in only. Use download-limit wrap on remote SSH.
      Refuses MiniMax Music 3, MiniMax H3, Suno, Udio, Stable Audio partner.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-music

<!-- source: scripts/utilities/download-podcast.sh -->
## download-podcast

Opt-in Hugging Face pull for US-safe local podcast weights.

Purpose:
  Selective download of Kokoro ONNX (analog), native ACE-Step 1.5 beds,
  and optional Chatterbox / Qwen3-TTS extras. Never part of download-models.

Audience:
  Operators on the Spark host. Prefer manage.sh download-podcast.

```bash
Usage:
  ./scripts/utilities/download-podcast.sh status|run|cleanup [--tier analog|acestep|chatterbox|qwen3tts|all] [--json]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Opt-in only. Use download-limit wrap on remote SSH.
      Refuses F5-TTS, XTTS, Fish, MiniMax H3, Music 3, TTS-Audio-Suite, OldTimeRadio.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-podcast

<!-- source: scripts/utilities/download-restore.sh -->
## download-restore

Opt-in post-concat restore pack (SeedVR2-3B Apache). Never part of
download-models. Unload Comfy denoise first (occupancy).

```bash
Usage:
  ./scripts/utilities/download-restore.sh status [--tier seedvr2-3b] [--json]
  ./scripts/utilities/download-restore.sh run [--tier seedvr2-3b]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      ~15 GB. Not default. Do not coreside with LTX/Wan denoise.

### Command: download-restore

<!-- source: scripts/utilities/download-wan.sh -->
## download-wan

Download Apache Wan 2.2 Comfy-Org split files into MODELS_DIR.

Purpose:
  Selective pull of Wan 2.2 TI2V-5B (default silent motion) plus optional A14B
  and Fun InP A14B (first-last-frame, Apache). Not the whole Comfy-Org monorepo.
  No Wan 2.5+ API models.

Audience:
  Operators on the Spark host. Prefer manage.sh download-models.

```bash
Usage:
  ./scripts/utilities/download-wan.sh status [--tier 5b|a14b|fun-inp|all] [--json]
  ./scripts/utilities/download-wan.sh run [--tier ...]
  ./scripts/utilities/download-wan.sh cleanup [--tier ...] [--dry-run|--yes]

```

Environment:
  MODELS_DIR, HF_TOKEN, LAB_MOCK_HF_DOWNLOAD

!!! warning

    Safety:
      Large downloads — use download-limit wrap on remote SSH.

Exit codes:
  0 success; 1 usage/tier/CLI errors.

### Command: download-wan

<!-- source: scripts/utilities/dub-fetch.sh -->
## dub-fetch

Optional URL ingest for the dub lane (yt-dlp). Writes into COMFY_OUTPUT_DIR/input.

Purpose:
  Pull operator-owned / licensed media into COMFY_OUTPUT_DIR/input so
  EZDubIngest Source file can select it. YouTube ToS still applies.
  Not baked into the Docker image.

Audience:
  Operators on the Spark host.

```bash
Usage:
  ./scripts/utilities/dub-fetch.sh status|run --url URL [--out DIR]

```

Environment:
  COMFY_OUTPUT_DIR, LAB_MOCK_YT_DLP

!!! warning

    Safety:
      Opt-in. Does not start Docker. Refuses empty/non-http URLs.
      Does not commit cookies. Occupancy unchanged.

Exit codes:
  0 success; 1 usage / missing yt-dlp / fetch failure.

### Command: dub-fetch

<!-- source: scripts/utilities/film-accept.sh -->
## film-accept

Fail-closed accept gate before 90s concat (duration, 1280×704, LTX audio).

```bash
Usage:
  ./scripts/utilities/film-accept.sh go-see|still-here|switchyard

```

Environment:
  COMFY_OUTPUT_DIR

### Command: film-accept

<!-- source: scripts/utilities/film-animatic.sh -->
## film-animatic

Cheap 90s animatic from clay.mp4 or held stills. Host ffmpeg, no GPU.
May run while compose is up.

```bash
Usage:
  ./scripts/utilities/film-animatic.sh --film SLUG [--yaml PATH] [--guides DIR]

```

Exit codes:
  0 written; 1 usage / missing sources / ffmpeg fail.

### Command: film-animatic

<!-- source: scripts/utilities/film-export-otio.sh -->
## film-export-otio

Write films/<slug>/publish/<slug>.otio from jobstore state.json.

```bash
Usage:
  ./scripts/utilities/film-export-otio.sh go-see|still-here|switchyard

```

Environment:
  COMFY_OUTPUT_DIR

### Command: film-export-otio

<!-- source: scripts/utilities/film-proxies.sh -->
## film-proxies

Host h264_nvenc proxies for a film jobstore. Never rewrite masters.

```bash
Usage:
  ./scripts/utilities/film-proxies.sh go-see|still-here|switchyard [--yes]

```

!!! warning

    Safety:
      Refuses if compose comfyui is running. Dry-run by default.
      Proxies are 960×528 ~2 Mbps under films/<slug>/proxies/.

### Command: film-proxies

<!-- source: scripts/utilities/house-views.sh -->
## house-views

Occupancy-gated Blender dump of an ez.house.views.v1 pack (ten Instagram
4:5 Workbench clay + depth stills + greybox GLB). Never in docker/Dockerfile.

```bash
Usage:
  ./scripts/utilities/house-views.sh --slug lab-penthouse
  ./scripts/utilities/house-views.sh --slug lab-penthouse --layout FILE

```

!!! warning

    Safety:
      Host GPU job. Dies with exit 2 if compose is up. Does not start Comfy.
      Do not weaken restart: "no", headroom, or download-limit clear-on-exit.

Exit codes:
  0 success; 1 usage / missing blender / QC fail; 2 compose running

### Command: house-views

<!-- source: scripts/utilities/llm-sidecar.sh -->
## llm-sidecar

Host llama-server for the opt-in Qwen3.6-35B-A3B writing desk.
Occupancy llm-desk is the public path. Never in docker/Dockerfile.

```bash
Usage:
  ./scripts/utilities/llm-sidecar.sh status [--json]
  ./scripts/utilities/llm-sidecar.sh start
  ./scripts/utilities/llm-sidecar.sh stop

```

Environment:
  MODELS_DIR, COMFY_OUTPUT_DIR, EZ_LLM_SIDECAR_PORT, EZ_LLM_SIDECAR_CTX,
  EZ_LLM_SIDECAR_HOST, LAB_MOCK_LLAMA_SERVER, LAB_HERMETIC

!!! warning

    Safety:
      Bind 127.0.0.1 only. GPU-offload is allowed here (llm-desk XOR).
      Does not start Compose. Does not GPU-offload the in-canvas 4B.

### Command: llm-sidecar

<!-- source: scripts/utilities/models-manifest.sh -->
## models-manifest

status | keep-set | render for config/model-manifest.yaml

```bash
Usage:
  ./scripts/utilities/models-manifest.sh status|keep-set|render
```

### Command: models-manifest

<!-- source: scripts/utilities/nvenc-preview.sh -->
## nvenc-preview

Host h264_nvenc preview encode. Never rewrite film masters.

Purpose:
  Encode a preview MP4 with the Spark NVENC engine when ComfyUI is stopped
  so preview encode does not fight LTX/Wan denoise for the encoder.

```bash
Usage:
  ./scripts/utilities/nvenc-preview.sh --in MASTER.mp4 --out PREVIEW.mp4 [--yes]

```

!!! warning

    Safety:
      Refuses if compose comfyui is running. Dry-run by default.
      Does not start Docker. Does not delete inputs.

Exit codes:
  0 success / dry-run; 1 usage or refuse; 2 compose running

### Command: nvenc-preview

<!-- source: scripts/utilities/occupancy.sh -->
## occupancy

Occupancy desk: park Comfy, run host Workbench Blender, then restore a
heavy graph family (klein / trellis / wan / ltx). One GB10 GPU job.

```bash
Usage:
  ./scripts/utilities/occupancy.sh status [--json]
  ./scripts/utilities/occupancy.sh enter blender-desk|llm-desk|klein|trellis|wan|ltx|idle [--yes]

```

!!! warning

    Safety:
      Does not start Compose (start still types yes). Does not weaken
      restart: "no", mem_limit 90g, headroom, or download-limit clear-on-exit.
      NVENC stays XOR with compose-up. blender-desk is POST /free + Workbench.
      llm-desk is POST /free + host llama-server (XOR with blender-desk / visual).

### Command: occupancy

<!-- source: scripts/utilities/overlay-qc.sh -->
## overlay-qc

50% blend of clay first.png vs Klein look plate. Host ffmpeg, no GPU.
May run while compose is up (unlike export-guides).

```bash
Usage:
  ./scripts/utilities/overlay-qc.sh --film SLUG --shot ID --look PATH [--guides DIR]

```

!!! warning

    Safety:
      Does not start Docker. Fail-closed on 1280x704 mismatch.

Exit codes:
  0 overlay written; 1 usage / QC fail.

### Command: overlay-qc

<!-- source: scripts/utilities/pack-frames.sh -->
## pack-frames

Mux a PNG/EXR sequence to 24fps 1280x704 MP4 with software libx264.
Not NVENC — may run while Comfy is up because it does not use the GPU.

```bash
Usage:
  ./scripts/utilities/pack-frames.sh --in DIR --out FILE [--fps 24] [--pattern '%04d.png']
```

### Command: pack-frames

<!-- source: scripts/utilities/podcast-loudnorm.sh -->
## podcast-loudnorm

ffmpeg loudnorm for podcast / YouTube masters. Comfy cannot LUFS-normalize.

Purpose:
  Target −16 LUFS (podcast) or −14 LUFS (YouTube). Never silently skip.

```bash
Usage:
  ./scripts/utilities/podcast-loudnorm.sh status [--json]
  ./scripts/utilities/podcast-loudnorm.sh run --in FILE [--out FILE] [--target podcast|youtube]

```

Environment:
  COMFY_OUTPUT_DIR

!!! warning

    Safety:
      Does not start Docker. Fails if ffmpeg is missing or loudnorm fails.

Exit codes:
  0 success; 1 usage / missing ffmpeg / loudnorm failure.

### Command: podcast-loudnorm

<!-- source: scripts/utilities/print-shot.sh -->
## print-shot

Queue one compiled shot on local ComfyUI and record the take in jobstore.

Purpose:
  POST /prompt for films/<slug>/shots/NN.json, poll /history, copy the
  resulting MP4 to shots/NN.mp4, update state.json. film-resume skips
  ok shots whose duration is 5.00±0.05 s.

```bash
Usage:
  ./scripts/utilities/print-shot.sh <film> <id>
  ./scripts/utilities/print-shot.sh --resume <film>

```

Environment:
  COMFY_OUTPUT_DIR, COMFY_PORT (default 8188), MODELS_DIR
  COMFY_URL — override (tests)

!!! warning

    Safety:
      Does not start compose. Does not Queue the 18-printer canvas.

Exit codes:
  0 success / skip; 1 usage or Comfy/jobstore error

### Command: print-shot

<!-- source: scripts/utilities/promote-workflow.sh -->
## promote-workflow

Copy one live operator graph into the repo lab tree. Does not commit.

```bash
Usage:
  ./scripts/utilities/promote-workflow.sh \
    --from PATH --lane LANE --id STEM [--subdir REL]

```

Environment:
  REPO_ROOT (optional)

!!! warning

    Safety:
      Never copies _lab into _user. Refuses banned model strings and a
      missing id.

Exit codes:
  0 success; 1 usage / refuse

### Command: promote-workflow

<!-- source: scripts/utilities/reap-models.sh -->
## reap-models

Plan/apply/restore model cache cleanup. Never overloaded as manage.sh cleanup.

```bash
Usage:
  ./scripts/utilities/reap-models.sh --plan
  ./scripts/utilities/reap-models.sh --apply --class junk --yes
  ./scripts/utilities/reap-models.sh --apply --class superseded --quarantine --yes
  ./scripts/utilities/reap-models.sh --drop-pack triposplat --quarantine --yes
  ./scripts/utilities/reap-models.sh restore --from .reap-quarantine/<utc>
  ./scripts/utilities/reap-models.sh drop-quarantine --older-than 14d --yes

```

!!! warning

    Safety:
      --plan is default. --apply requires --yes.
      Refuses unsafe MODELS_DIR, path escape, compose-up (except junk), hf PID.
      Does not delete shared keep-set files (flux2-vae, ACE-Step AIO).

### Command: reap-models

<!-- source: scripts/utilities/research-mcp.sh -->
## research-mcp

In-tree creative research MCP (typed tools, no execute_code, no telemetry).
CPU GGUF + SSRF-safe HTTPS search. Does not refuse a GPU Comfy session.

```bash
Usage:
  ./scripts/utilities/research-mcp.sh [--stdio]
  ./scripts/utilities/research-mcp.sh --list-tools
  ./scripts/utilities/research-mcp.sh --call TOOL [JSON]
```

### Command: research-mcp

<!-- source: scripts/utilities/runner.sh -->
## Utility runner (Bazel entry)

Dispatches to `scripts/utilities/<name>.sh`.

### Command: run-utility

```bash
Usage:
```

  bazelisk run //scripts:run-utility -- download-limit status
  bazelisk run //scripts:run-utility -- occupancy status

!!! warning

    Safety:
      Only invokes scripts under scripts/utilities/; each utility keeps its
      own confirmations and download-limit clear-on-exit.

<!-- source: scripts/utilities/shot-sheet.sh -->
## shot-sheet

Write films/<slug>/shots.yaml from a lab bible with shot-card defaults.
Does not mutate workflows/shorts/*.shots.yaml unless --lab-example.

```bash
Usage:
  ./scripts/utilities/shot-sheet.sh status [--json] [--film SLUG]
  ./scripts/utilities/shot-sheet.sh run --film SLUG [--from PATH] [--out PATH] [--lab-example]

```

!!! warning

    Safety:
      Host only. Does not start Docker. No GPU.

Exit codes:
  0 success; 1 usage / parse / write failure.

### Command: shot-sheet

<!-- source: scripts/utilities/spark-farm.sh -->
## spark-farm

Probe independent Comfy workers on multiple Sparks (no NCCL, no H3 farm).

Purpose:
  status: SSH each SPARK_HOSTS entry (docker ps, disk, nvidia-smi, fabric ping).
  sync-models: rsync MODELS_DIR/comfy over SPARK_FABRIC_IPS only (not mgmt NIC).
  run: refuses MiniMax H3 names; operators Queue wan/still-to-shot / ltx/still-to-shot
  graphs per host, then concat-shots.sh locally.
  Never starts compose on a remote node — prints the local manage.sh start.

```bash
Usage:
  ./scripts/utilities/spark-farm.sh status [--json]
  ./scripts/utilities/spark-farm.sh sync-models
  ./scripts/utilities/spark-farm.sh run [--film go-see] [--seeds 509201,509211,509221]
  ./scripts/utilities/spark-farm.sh dispatch [--film go-see]
```

    Assign shots 01-06 / 07-12 / 13-18 (or even split). Each host runs
    local manage.sh print-shot. Never SSH-starts compose.

Environment:
  SPARK_HOSTS, SPARK_USER, SPARK_COMFY_URLS, SPARK_FABRIC_IPS, MODELS_DIR, FARM_SHARE
  See config/spark-farm.example.env

!!! warning

    Safety:
      Does not compose up remotely (heavy confirm stays local).
      rsync uses fabric IPs. restart: "no" unchanged.

Exit codes:
  0 success; 1 usage / SSH / rsync / queue errors.

### Command: spark-farm

<!-- source: scripts/utilities/spark-timing.sh -->
## spark-timing

Record wall-clock seconds for the three Kitchen smokes on a real Spark.
CI has no GPU — this file is the operator timing table. Do not invent seconds.

```bash
Usage:
  ./scripts/utilities/spark-timing.sh show [--json]
  ./scripts/utilities/spark-timing.sh record --klein N --wan N --ltx N [--json]

```

Environment:
  COMFY_OUTPUT_DIR (JSON lands at spark-timing.json; not git)

### Command: spark-timing

<!-- source: scripts/utilities/stem-mix.sh -->
## stem-mix

Picture-lock stem mix (DX / BG / FX / MX). Duck -15 dB under DX, YouTube loudnorm.
Occupancy: operator must already have stopped Klein/Wan/LTX. This script is CPU ffmpeg.

```bash
Usage:
  ./scripts/utilities/stem-mix.sh --film SLUG --shot ID [--dx PATH] --bg PATH [--fx PATH] [--mx PATH] [--video PATH]

```

Exit codes:
  0 mix written; 1 usage / missing ffmpeg / mix fail.

### Command: stem-mix

<!-- source: scripts/utilities/studio-mcp.sh -->
## studio-mcp

In-tree studio MCP (typed tools, no execute_code, no telemetry, no Queue).
Clones shipped _lab graphs into live _user/. CPU GGUF optional.
Does not refuse a GPU Comfy session.

```bash
Usage:
  ./scripts/utilities/studio-mcp.sh [--stdio]
  ./scripts/utilities/studio-mcp.sh --list-tools
  ./scripts/utilities/studio-mcp.sh --call TOOL [JSON]
```

### Command: studio-mcp

<!-- source: scripts/utilities/take-promote.sh -->
## take-promote

Promote a take from films/<slug>/takes/<id>/tNNN.mp4 to shots/<id>.mp4.

```bash
Usage:
  ./scripts/utilities/take-promote.sh <film> <id> <take>

```

Environment:
  COMFY_OUTPUT_DIR

### Command: take-promote
