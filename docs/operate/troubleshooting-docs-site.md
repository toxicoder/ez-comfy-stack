---
title: Troubleshooting — docs site
description: Fix docs copy-paste that still shows session-variable chips instead of Your Spark values.
tags: [troubleshooting, docs, session-variables]
---

# Troubleshooting — docs site

**What's on this page**

- **Session chips** still showing `${SPARK_HOST}` / `${MODELS_DIR}`
- **Hard-refresh** when docs JS or a cached `commands.js` / `tables.js` is blocked
- **Table chrome** — pinned header or on-screen horizontal scrollbar missing on a wide table

**What this enables**

- **Fixing** copy-paste without treating it as a Spark/`doctor` failure
- **Editing** the same session fields as **Your Spark** (this browser only)

!!! tip "Not a Spark failure"

    Highlighted chips (dotted underline) are the same session fields as **Your Spark** — click to edit. Values stay in this browser only. Stack issues: [Troubleshooting](../troubleshooting.md).

## Docs site

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Copy still shows `${SPARK_HOST}` / `${MODELS_DIR}` | Docs JS blocked, or a hard-cached `commands.js` | Hard-refresh the docs tab. Highlighted chips (dotted underline) are the same session fields as **Your Spark** — click to edit. Not a Spark/`doctor` failure. Values stay in this browser only |
| Wide table has no on-screen horizontal bar, or the pinned header does not pan with columns | Docs JS blocked, or a hard-cached `tables.js` | Hard-refresh the docs tab. `.ez-table-hscroll` is a `tables.js` mirror of the wrap `scrollLeft` (native bar sits at the table bottom). Not a Spark/`doctor` failure |
