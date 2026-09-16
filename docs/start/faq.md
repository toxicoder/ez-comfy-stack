---
title: FAQ
description: Short answers for doctor vs missing weights, --tier vs --limit, park vs stop, App Mode vs studio-ui, spark-lab, and cleanup.
tags: [faq, getting-started, occupancy, safety]
---

# FAQ

**What's on this page**

- **Doctor vs Missing Models** — preflight warnings are not a hard fail
- **`--tier` vs `--limit`** — pack id vs bandwidth
- **Park vs stop** — `POST /free` vs container down
- **App Mode vs studio-ui** — widget surface vs jobstore board
- **When to graduate** to nvidia-dgx-spark-lab
- **`cleanup` does not delete `${MODELS_DIR}`**

**What this enables**

- **Answering** the questions that already live across Operate pages, in one screen
- **Avoiding** a volume DELETE when you meant missing weights
- **Jumping** to the troubleshooting index when the short answer is not enough

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

First install is still [Getting Started](../getting-started.md). Symptom tables: [Troubleshooting](../troubleshooting.md).

---

## Why did `doctor` pass if Comfy says Missing Models?

`doctor` treats **missing weights as a warning**, not a hard fail. It checks Docker, GPU, RAM/disk headroom, writable dirs, and the `hf` CLI. Klein / Wan / LTX files are a separate `download-models` step.

```bash
./scripts/manage.sh doctor
./scripts/manage.sh download-models
./scripts/manage.sh start   # type: yes
```

`--limit` follows `${DOWNLOAD_LIMIT}` (default `auto` = 85% of a duration HTTP / speedtest sample, cached 24h on the host, when HTB works). Wrap **always clears on exit**.

---

## What is `--tier` vs `--limit`?

| Flag | Means | Does not mean |
| --- | --- | --- |
| **`--tier NAME`** | Which **pack** that one downloader pulls | A studio-wide quality ladder |
| **`--limit auto\|N\|off`** | Hugging Face **bandwidth** (Mbps) | Smaller / faster weights |

`download-models` has **no** `--tier`. Map: [Download tiers](../download-tiers.md). Throttle: [Download limit](../download-limit.md).

---

## Park vs stop?

| Command | Compose | Weights in GPU | When |
| --- | --- | --- | --- |
| **`occupancy enter blender-desk`** (park) | **Up** (or already down) | `POST /free` unload when up | Host Workbench dumps without typing **yes** on a full start cycle |
| **`occupancy enter llm-desk --yes`** | Up or down | Unload when up | Host 35B sidecar **is** the GPU job |
| **`./scripts/manage.sh stop`** | **Down** | Gone with the container | NVENC, SuperSplat, wedged UI, reboot |

Parked Comfy is **not** a second denoise. NVENC still dies if Compose is **up**. Matrix: [Occupancy matrix](../operate/occupancy-matrix.md). Desk: [Occupancy](../occupancy.md).

!!! danger "One heavy job"

    Do not Queue Klein next to Wan, LTX, TRELLIS, or `llm-desk`. `occupancy enter` does **not** start Compose.

---

## App Mode vs studio-ui?

| Surface | What it is | Port |
| --- | --- | --- |
| **App Mode** | Creator widgets on the same `_lab` JSON as the graph (Comfy frontend). Occupancy chip in the widget list | `${COMFY_PORT}` (8188) |
| **studio-ui** | Optional Compose **profile** `studio-ui`. Jobstore lights board. **No GPU** | `${STUDIO_UI_PORT:-8190}` |

They are not the same product. Default `start` does **not** launch studio-ui. Widget catalog: [ComfyUI Apps](../studio-apps.md). Board: [studio-ui](../reference/studio-ui.md).

---

## When do I graduate to nvidia-dgx-spark-lab?

Stay here for a **Compose demo** on one Spark (or independent Sparks sharing `${MODELS_DIR}`). Graduate when you need K3s, a multi-workload dashboard, or tensor-parallel LLMs.

This repo must **not** grow K3s, Bazel, or in-tree NCCL. Table: [When to use vs spark-lab](when-to-use-vs-spark-lab.md).

---

## Does `cleanup` delete my weights?

**No.** Type **DELETE** and `cleanup` removes the named volume **`ez-comfy-state`** (Comfy install + venv + lab `ez_*` copies). It does **not** delete `${MODELS_DIR}` or `${COMFY_OUTPUT_DIR}`.

Weights cleanup is `reap-models` (default `--plan`). Host leftovers: `disk-wizard` (default `--plan`). [Backup and restore](../operate/backup-restore.md) · [Disk wizard](../disk-wizard.md).

!!! danger "DELETE is the volume, not a cache wipe"

    Do not confuse `cleanup` with `docker system prune -a --volumes` or deleting `${MODELS_DIR}`. Those are not this verb.

---

## Related

| Need | Page |
| --- | --- |
| Symptom → action | [Troubleshooting](../troubleshooting.md) |
| Architecture | [Architecture](../learn/architecture.md) |
| Licenses before a 30 GB pull | [Model licenses](../licenses.md) |
