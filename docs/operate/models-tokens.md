---
title: Gated models and HF_TOKEN
description: Hugging Face gated-repo access for LTX-2.5. A token in .env is not a license click.
tags: [models, huggingface, ltx, token, gated]
---

# Gated models and HF_TOKEN

**What's on this page**

- **Which default weights are gated** (LTX-2.5) vs Apache (Klein 4B, Wan 2.2 5B)
- **`HF_TOKEN` in `.env`** versus accepting the Lightricks license in the browser
- **Fine-grained token** gated-repo read

**What this enables**

- **Pulling LTX-2.5** after the same Hugging Face account agrees to the Community License
- **Passing `--token` from `HF_TOKEN`** so download-models wins over a leftover `hf auth login`

**Who this is for:** operators before `download-models`. Layout: [Models and cache](../models-and-cache.md). Packs: [Download packs](models-packs.md).

---

## Gated models / HF_TOKEN

**LTX-2.5** (`Lightricks/LTX-2.5`) is gated. Klein 4B distilled and Wan 2.2 5B are Apache and do not need a license click. A token in `.env` is **not** the same as accepting the Lightricks license.

```bash
# .env
HF_TOKEN=hf_...
# Browser, same account: https://huggingface.co/Lightricks/LTX-2.5 → Agree
# or: hf auth login
hf auth whoami
```

Fine-grained tokens need **gated repo** read. `download-models` passes `--token` from `HF_TOKEN` so it wins over a leftover `hf auth login`.

Do not put `HF_TOKEN` in the GHCR image, compose YAML, or git. The prebuilt image does **not** contain `HF_TOKEN`, `.env`, or host PII. See [Download packs](models-packs.md#prebuilt-container-image-ghcr).
