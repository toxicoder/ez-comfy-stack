---
title: Hugging Face tokens
description: Pull gated weights by putting HF_TOKEN in .env and accepting the license with the same account.
tags: [models, huggingface, ltx, token, gated]
---

# Hugging Face tokens

**What's on this page**

- **When you need this** - which packs refuse an anonymous pull
- **Accept the license** - the browser click, as the token's own account
- **Set `HF_TOKEN` in `.env`** - and why the click is not the token
- **Verify access** - who the token is, and whether the pack is on disk
- **What breaks otherwise** - the gated 403, the 401, and the rate limit

**What this enables**

- **Pulling LTX-2.5** after the same Hugging Face account agrees to the Community License
- **Passing `--token` from `HF_TOKEN`** so download-models wins over a leftover `hf auth login`
- **Telling a token failure from a license failure** before you re-run a 30 GB pull

**Who this is for:** operators before `download-models`. Layout:
[Models and cache](../models-and-cache.md). Packs and sizes:
[Download tiers](../download-tiers.md). Per-family basenames:
[Model packs by family](models-packs.md).

---

## When you need this

**LTX-2.5** (`Lightricks/LTX-2.5`) is gated. Klein 4B distilled and Wan 2.2 5B are Apache
and do not need a license click. Among opt-in packs, Klein 9B, FLUX.2 [dev], and all six
`flux3*` packs are gated too. A token in `.env` is **not** the same as accepting the
Lightricks license - you need both, from the **same** Hugging Face account.

---

## Accept the license, then set the token

1. Browser, signed in as the account that owns the token:
   `https://huggingface.co/Lightricks/LTX-2.5` -> **Agree**.

2. Put the token in the repo-root `.env`:

   ```bash
   # .env
   HF_TOKEN=hf_...
   ```

3. Or authenticate the CLI instead:

   ```bash
   hf auth login
   ```

Fine-grained tokens need **gated repo** read. `download-models` passes `--token` from
`HF_TOKEN` so it wins over a leftover `hf auth login`.

Do not put `HF_TOKEN` in the GHCR image, compose YAML, or git. The prebuilt image does **not**
contain `HF_TOKEN`, `.env`, or host PII. See
[Model packs by family](models-packs.md#prebuilt-container-image-ghcr).

---

## Verify access

```bash
hf auth whoami
```

**Check it worked:** it prints the account that clicked **Agree**. If it prints a different
account, that account has no access no matter what the first one agreed to.

```bash
./scripts/utilities/download-ltx.sh status --tier 2.5 --json
```

**Check it worked:** the pack reports ready once the LTX-2.5 files are under `${MODELS_DIR}`.
`./scripts/manage.sh download-models` exits non-zero until every lab basename is present.

---

## What breaks otherwise

| Symptom on the pull | What it means | Fix |
| --- | --- | --- |
| Gated-repo / "not in the authorized list" / 403 | The token's account never clicked **Agree** | Click **Agree** as that account, then re-run |
| `Invalid user token` / 401 | The token is missing, wrong, or expired | Set `HF_TOKEN` in `.env` or run `hf auth login` |
| 429 / rate limit | Too many requests, not a permission problem | Wait a few minutes and re-run `download-models` |
| Works on the laptop, fails on the Spark | The Spark has a different `hf auth login` identity | `hf auth whoami` on the Spark; `HF_TOKEN` beats the leftover login |

`download-models` prints the gated hint with the repo URL, the token identity, and the click
link when a pull is refused. Throttling and resume live on
[Download limit](../download-limit.md) and [Downloads and
bandwidth](troubleshooting-downloads.md).

---

## Next

1. [Download tiers](../download-tiers.md) - which packs are gated, and what each costs in GB
2. [Model packs by family](models-packs.md) - the basenames a gated pack owes you
3. [Models and cache](../models-and-cache.md) - where the pulled files land
4. [Model licenses](../licenses.md) - what each license allows you to publish
5. [Downloads and bandwidth](troubleshooting-downloads.md) - a pull that will not finish
