---
title: Update the stack
description: Stop the studio, pull the git branch these docs were built from, then start again and type yes.
tags: [operate, update, git, start, stop]
---

# Update the stack

**What's on this page**

- **Which branch** these docs describe (`__DOCS_GIT_REF__`)
- **Stop, pull, start** - the order that picks up scripts, workflows, and the container image
- **What an update does not do** - it does not re-download weights or delete `${MODELS_DIR}`

**What this enables**

- **Moving** a Spark onto the same branch you are reading, without mixing `main` and `development`
- **Restarting** so bind-mounted workflows and custom nodes match that checkout
- **Leaving** weights and outputs where they are

**Who this is for:** operators bringing a working Spark onto the branch these pages
describe. These pages were built from git ref `__DOCS_GIT_REF__`. `/latest/` is `main`.
`/development/` is `development`. Run the commands on the Spark, in the repo root. Do not
pull the other branch from this page.

`restart: "no"` still applies. Type **yes** on `start`. Headroom is still a hard fail.
Download-limit wrap still clears on exit.

First clone is [Getting Started](../getting-started.md). Power-off is
[Reboot safety](../reboot-safety.md). Copy-paste for the rest of the day is
[Quick reference](quick-reference.md).

---

## 1. Stop the studio

The container comes down. `${MODELS_DIR}`, `${COMFY_OUTPUT_DIR}`, and the `ez-comfy-state`
volume stay.

```bash
./scripts/manage.sh stop
```

**Check it worked:** `./scripts/manage.sh status` shows Comfy is not running.

---

## 2. Pull this docs branch

```bash
git fetch origin
```

```bash
git checkout __DOCS_GIT_REF__
```

```bash
git pull --ff-only origin __DOCS_GIT_REF__
```

**Check it worked:** `git branch --show-current` prints `__DOCS_GIT_REF__`.

If `--ff-only` refuses, this checkout has local commits. Do not force. Move those commits
aside, or stay on them and do not expect these docs to match.

---

## 3. Start again

`start` pulls the image for the branch you just checked out. `main` uses
`ghcr.io/toxicoder/ez-comfy:us-safe-studio`. `development` uses
`us-safe-studio-development`. The entrypoint recopies `workflows/` and `custom_nodes/` from
this checkout. Type **yes**. A headroom refuse is a hard fail.

```bash
./scripts/manage.sh start
```

```bash
./scripts/manage.sh doctor
```

```bash
./scripts/manage.sh status
```

**Check it worked:** doctor prints `Doctor OK` (missing weights are a warning, not a fail),
status shows the project up, and `http://${SPARK_HOST}:${COMFY_PORT}` loads the canvas.

---

## What an update does not touch

An update does not run `download-models` and does not delete `${MODELS_DIR}`. Weights,
generated media, and your `_user/` graphs stay put. A new graph may need a pack from
[Download tiers](../download-tiers.md).

---

## Next

1. [Daily loop](daily.md) - back to the working loop after the restart
2. [Quick reference](quick-reference.md) - the copy-paste version of these steps
3. [Download tiers](../download-tiers.md) - pull the pack a new graph needs
4. [Models and cache](../models-and-cache.md) - what survives a stop and an image pull
5. [Troubleshooting](../troubleshooting.md) - if the studio does not come back up
