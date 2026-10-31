---
title: Quick reference
description: Copy-paste commands for update, start, stop, model downloads, and disk space on one DGX Spark.
tags: [operate, quick-reference, doctor, start, stop, download, disk]
---

# Quick reference

**What's on this page**

- **Update** - stop, pull the branch these docs describe, start
- **Run** - doctor, start, stop, status, logs, open the UI
- **Models** - default download and stuck partials
- **Disk** - free space check, plan-only wizard, plan-only reap
- **Occupancy** - read who holds the GPU

**What this enables**

- **Grabbing** a command without re-reading Getting Started
- **Checking** disk before a pull, and freeing space without deleting the lab keep-set
- **Jumping** to the page that explains the command when the one-liner is not enough

**Who this is for:** operators who have a working Spark and want the command, not the
prose. Every block below runs on the Spark from the repo root. `start` still asks you to
type **yes**. `restart: "no"`, headroom, and download-limit clear-on-exit are unchanged.

---

## Update the stack

Stop, pull only `__DOCS_GIT_REF__` (the branch these docs were built from), then start and
type **yes**.

1. `./scripts/manage.sh stop`
2. `git fetch origin && git checkout __DOCS_GIT_REF__ && git pull --ff-only origin __DOCS_GIT_REF__`
3. `./scripts/manage.sh start` - type **yes**

**Check it worked:** `git branch --show-current` prints `__DOCS_GIT_REF__` and
`./scripts/manage.sh doctor` prints `Doctor OK`.

An update does not re-download weights. Details: [Update the stack](update.md).

---

## Run the studio

1. `./scripts/manage.sh doctor` - expect `Doctor OK`
2. `./scripts/manage.sh start` - type **yes**. Headroom is a hard fail.
3. `./scripts/manage.sh status` - the project is up
4. `./scripts/manage.sh logs` - read the container log
5. `./scripts/manage.sh stop` - container down, volumes kept

On the Spark, open `http://${SPARK_HOST}:${COMFY_PORT}`. From a laptop, forward the port
first:

```bash
ssh -L "${COMFY_PORT}:127.0.0.1:${COMFY_PORT}" "${SPARK_USER}@${SPARK_HOST}"
```

**Check it worked:** `http://127.0.0.1:${COMFY_PORT}` loads the ComfyUI canvas on the
laptop. The day as one loop: [Daily loop](daily.md).

---

## Download models

Default Klein 4B + Wan 2.2 5B + LTX-2.5 + prompt-enhance GGUF. This does not pull podcast,
dub, music, or 3D.

1. `df -h` - confirm free disk before a multi-GB pull
2. `./scripts/manage.sh download-models` - throttled by `${DOWNLOAD_LIMIT}` (default `auto`)
3. `./scripts/manage.sh models-status` - the lab basenames are on disk

Stuck `*.incomplete` partials only (finished weights stay):

```bash
./scripts/manage.sh reset-hf-partials
```

**Check it worked:** `download-models` exits 0; it exits non-zero until every lab basename
is present. Every pack, size, and command is one table:
[Download tiers](../download-tiers.md). Basenames and resume:
[Model packs by family](models-packs.md).

---

## Reclaim disk

```bash
./scripts/manage.sh disk-wizard --plan
./scripts/manage.sh reap-models --plan
```

`--plan` only prints a plan. Adding `--apply --yes` is what deletes or quarantines.
`disk-wizard` walks host leftovers; `reap-models` walks `${MODELS_DIR}` classes only.
[Disk wizard](../disk-wizard.md) says which tool touches which files.

`cleanup` removes the `ez-comfy-state` volume after you type `DELETE`. It does not delete
`${MODELS_DIR}` or `${COMFY_OUTPUT_DIR}`.

```bash
./scripts/manage.sh cleanup
```

**Check it worked:** `df -h` shows the space back, and `./scripts/manage.sh models-status`
still reports the lab weights present.

---

## Read the GPU

```bash
./scripts/manage.sh occupancy status
```

**Check it worked:** the printout names the current mode. One heavy GPU job at a time.
Modes, park, and stop: [Occupancy desk](../occupancy.md).

---

## Next

1. [Daily loop](daily.md) - the same commands as a numbered working day
2. [Update the stack](update.md) - what an update does and does not touch
3. [Download tiers](../download-tiers.md) - every pack with size and command
4. [Disk wizard](../disk-wizard.md) - plan-first reclaim for host leftovers
5. [Troubleshooting](../troubleshooting.md) - when a command does not behave
