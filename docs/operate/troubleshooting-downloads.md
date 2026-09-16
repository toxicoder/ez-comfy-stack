---
title: Troubleshooting — downloads and bandwidth
description: wondershaper/qdisc, stuck download limits, HF locks, and the gated LTX-2.5 license click.
tags: [troubleshooting, downloads, bandwidth, huggingface, ltx]
---

# Troubleshooting — downloads and bandwidth

**What's on this page**

- **wondershaper / qdisc** soft-fail and stuck `download-limit`
- **HF locks** and hung resume (`0 MiB/s`)
- **Gated LTX license** — `HF_TOKEN` is not the license click
- **Wrong `--tier`** — pack ids live on [Download tiers](../download-tiers.md); `--limit` is Mbps

**What this enables**

- **Downloading** Klein/Wan/LTX without freezing SSH
- **Clearing** wrap limits on exit (do not weaken that)

!!! warning "HF_TOKEN is not the LTX license click"

    `HF_TOKEN` in `.env` only authenticates. Open https://huggingface.co/Lightricks/LTX-2.5 as the **same** Hugging Face user (`hf auth whoami`) and click Agree, then re-run `./scripts/manage.sh download-models`. Klein/Wan can cache-hit while LTX is still missing.

!!! warning "Unthrottled wrap can freeze SSH"

    Missing HTB (`qdisc kind is unknown`) is a **soft-fail** on wrap — it warns and continues unthrottled. Persistent `download-limit run` still hard-fails. Wrap **always clears on exit**. `DOWNLOAD_LIMIT=off` is full blast.

## Downloads & bandwidth

| Symptom | Likely cause | Action |
| --- | --- | --- |
| wondershaper `qdisc kind is unknown` / RTNETLINK | No HTB/IFB (common on DGX Spark) | Expected; wrap uses **gentle HF max-workers** from measured speed (HTTP probe). Not a hard Mbps cap. `DOWNLOAD_LIMIT=off` for full blast |
| Speedtest failed / always 50 Mbps | CLI missing or probe blocked | Auto-installs `speedtest-cli` when possible; **clears limits before measure**; then duration HTTP probe / live RX. Or skip the probe: `./scripts/manage.sh download-models --limit 40` |
| Auto cap way below line rate | Old 15 MB completed-file probe, or sivel `speedtest-cli` winning first | Pull latest. Auto uses a **duration** HTTP sample (timeout is valid) then 85%. Remeasure: `./scripts/manage.sh download-limit status --refresh`. Cache is 24h host-local |
| Auto cap too high / SSH still sluggish | Speedtest over-reads the path you share with SSH, or a stale-high 24h cache after WAN drop | `./scripts/manage.sh download-limit status --refresh` then `--limit N` with a lower Mbps (e.g. 20–40). Persistent: `DOWNLOAD_LIMIT=40` in `.env`. `DOWNLOAD_LIMIT_CACHE_TTL_SEC=0` disables cache |
| ++ctrl+c++ does not stop download | Old tee pipeline orphan | Pull latest; wrap/hf use process groups — Ctrl+C should stop `hf` within seconds |
| `Still waiting to acquire lock` on `*.lock` | Stale HF locks from killed downloads | `./scripts/manage.sh clear-hf-locks` or auto-clear on download-models; if stuck **and no hf is running**: `HF_LOCK_CLEAR_FORCE=1 ./scripts/manage.sh clear-hf-locks` |
| `↓ … 0 MiB/s` + `found N incomplete` + lock still held | Hung **resume** — live `hf` holds the lock, partial not growing | ++ctrl+c++. Do **not** FORCE-clear locks while it runs. Then `./scripts/manage.sh reset-hf-partials --yes` and re-run, or `./scripts/manage.sh download-models --drop-incomplete`. Finished `.safetensors` are kept |
| SSH freezes during download | Full-rate HF pull (limit off or soft-fail) | Prefer working `download-limit`; lower fixed Mbps; `download-limit clear` if half-applied |
| `Required tool missing: hf` | Host has no modern Hugging Face CLI | Pull latest; `setup` / `download-models` auto-install `hf`. Do not `sudo` the whole command (sudo PATH hides `~/.local/bin`). Manual fallback: `pipx install huggingface_hub` |
| `huggingface-cli is deprecated` / 0 GB after download-models | Scripts used stub CLI | Pull latest; auto-install prefers `hf` over the stub; re-run download-models |
| Download failed / gated license | No token or **LTX-2.5 license not accepted** for that token | `HF_TOKEN` set is not enough. Open https://huggingface.co/Lightricks/LTX-2.5 as the **same** user (`hf auth whoami`), click Agree, then re-run `download-models`. Klein/Wan can cache-hit while LTX is still missing |
| Long Python `GatedRepoError` traceback | CLI stderr was leaking (should be a short checklist) | Pull latest; traceback is captured to a log. `LAB_DEBUG=1` still dumps the last 40 lines |
| No `↓` / `══ n/m ══` progress line | Piped SSH, `EZ_COMFY_PROGRESS=0`, or `HF_PROGRESS=0` | Progress rewrites a TTY line; pipes get a newline every interval. Unset those env vars. `LAB_DEBUG=1` for extra traces |
| Command looks hung (ffmpeg / Blender / compose build) | Heartbeat interval or no TTY | Wait for `… still running` / `elapsed m:ss`. `EZ_COMFY_PROGRESS_INTERVAL=2` is the default tick |
| Limits stuck after kill | trap skipped | `./scripts/manage.sh download-limit clear` |

### wondershaper / qdisc failures

`download-models` wraps downloads under wondershaper. If the kernel rejects HTB (`qdisc kind is unknown`) or illegal rates, **wrap soft-fails**: it warns and continues **unthrottled** (SSH risk). Persistent `download-limit run` still hard-fails. Set `DOWNLOAD_LIMIT_REQUIRE=1` to hard-fail wrap too.

```bash
./scripts/manage.sh download-limit clear
# optional: sudo modprobe sch_htb sch_ingress sch_sfq
./scripts/manage.sh download-models --limit 40
# or skip throttle entirely (SSH risk):
# DOWNLOAD_LIMIT=off ./scripts/manage.sh download-models
```

---
