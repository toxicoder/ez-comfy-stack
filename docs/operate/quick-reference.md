---
title: Quick reference
description: Copy-paste commands for update, start, stop, model downloads, and disk space.
tags: [operate, quick-reference, doctor, start, stop, download, disk]
---

# Quick reference

**What's on this page**

- **Update** — stop, pull the branch these docs describe, start
- **Run** — doctor, start, stop, status, logs, open the UI
- **Models and disk** — default download, pack table, wizard, reap, cleanup

**What this enables**

- **Grabbing** a command without re-reading Getting Started
- **Checking** disk before a pull, and freeing space without deleting the lab keep-set
- **Jumping** to the page that explains the command when the one-liner is not enough

Run these on the Spark, from the repo root. `start` still asks you to type **yes**. `restart: "no"`, headroom, and download-limit clear-on-exit are unchanged.

Longer write-ups: [Update the stack](update.md), [Daily loop](daily.md), [Download tiers](../download-tiers.md), [Disk wizard](../disk-wizard.md).

---

## Update

Stop first. Pull only `__DOCS_GIT_REF__` (the branch these docs were built from). Then start and type **yes**.

```bash
./scripts/manage.sh stop
```

```bash
git fetch origin && git checkout __DOCS_GIT_REF__ && git pull --ff-only origin __DOCS_GIT_REF__
```

```bash
./scripts/manage.sh start
```

Details and what an update does not delete: [Update the stack](update.md).

---

## Run the studio

```bash
./scripts/manage.sh doctor
```

```bash
./scripts/manage.sh start
```

```bash
./scripts/manage.sh stop
```

```bash
./scripts/manage.sh status
```

```bash
./scripts/manage.sh logs
```

On the Spark, open `http://${SPARK_HOST}:${COMFY_PORT}`. From a laptop:

```bash
ssh -L "${COMFY_PORT}:127.0.0.1:${COMFY_PORT}" "${SPARK_USER}@${SPARK_HOST}"
```

Then open `http://127.0.0.1:${COMFY_PORT}`.

---

## Models

Default Klein 4B + Wan 2.2 5B + LTX-2.5 + prompt GGUF. This does not pull podcast, dub, music, or 3D.

```bash
./scripts/manage.sh download-models
```

Every other pack, with rough size and the matching command, is one table: [Download tiers](../download-tiers.md).

Stuck `*.incomplete` files (finished weights stay):

```bash
./scripts/manage.sh reset-hf-partials
```

---

## Disk

```bash
df -h
```

```bash
./scripts/manage.sh disk-wizard --plan
```

```bash
./scripts/manage.sh reap-models --plan
```

`disk-wizard --plan` and `reap-models --plan` only print a plan. Adding `--apply --yes` is what deletes or quarantines. [Disk wizard](../disk-wizard.md) says which tool touches which files.

`cleanup` removes the `ez-comfy-state` volume after you type `DELETE`. It does not delete `${MODELS_DIR}` or `${COMFY_OUTPUT_DIR}`.

```bash
./scripts/manage.sh cleanup
```

---

## Occupancy

```bash
./scripts/manage.sh occupancy status
```

One heavy GPU job. The mode list is [Occupancy](../occupancy.md).
