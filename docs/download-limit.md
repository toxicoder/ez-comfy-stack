---
title: Download Limit
description: Throttle model downloads with wondershaper; auto mode uses speedtest and caps at 85% of line rate.
tags: [bandwidth, wondershaper, speedtest, safety]
---

# Download Limit

**What's on this page**

- Why bandwidth limits matter on remote Sparks
- CLI usage (`status`, `run`, `clear`, `wrap`)
- Auto mode (85% of speedtest) and wrap lifecycle

**What this enables**

- Downloading multi‑GB FLUX/LTX weights without saturating the uplink and freezing SSH

## Why

DGX Spark nodes are often operated **over the internet** without physical console access. A full-rate Hugging Face pull can starve interactive SSH. This utility applies kernel-level traffic shaping via **wondershaper**.

Inspired by the throttled Ollama downloader in `dgx-spark-it-up`, generalized and improved with **auto** limiting.

```mermaid
flowchart LR
  subgraph Bad["Without limit"]
    HF1["Full-rate HF pull"] --> Sat["WAN saturated"]
    Sat --> Dead["SSH freezes"]
  end
  subgraph Good["With download-limit wrap"]
    HF2["Throttled pull"] --> Cap["≤ 85% of line rate"]
    Cap --> SSH["SSH stays usable"]
  end
```

## Commands

```bash
./scripts/utilities/download-limit.sh status [--json]
./scripts/utilities/download-limit.sh run --limit 50
./scripts/utilities/download-limit.sh run --limit auto
./scripts/utilities/download-limit.sh clear
./scripts/utilities/download-limit.sh wrap --limit auto -- <command...>
```

Via manage:

```bash
./scripts/manage.sh download-limit clear
./scripts/manage.sh download-models   # wrap --limit ${DOWNLOAD_LIMIT:-auto}
```

### CLI decision tree

```mermaid
flowchart TB
  Start["download-limit.sh"] --> Cmd{"subcommand"}
  Cmd -->|status| Status["Report iface + limit<br/>optional --json"]
  Cmd -->|run| Run["Apply fixed or auto limit"]
  Cmd -->|clear| Clear["Remove wondershaper limit"]
  Cmd -->|wrap| Wrap["Apply limit → run command<br/>always clear on exit"]
```

## Auto mode

1. Run `speedtest-cli` (or Ookla `speedtest`)  
2. Read download Mbps  
3. Apply `floor(0.85 × measured)` (minimum 1 Mbps)  
4. If speedtest fails, use `DOWNLOAD_LIMIT_FALLBACK` (default 50)

```mermaid
flowchart TB
  A["--limit auto"] --> B["speedtest-cli or Ookla speedtest"]
  B --> C{"measured Mbps?"}
  C -->|yes| D["limit = max 1, floor 0.85 × Mbps"]
  C -->|no / fail| E["DOWNLOAD_LIMIT_FALLBACK<br/>default 50 Mbps"]
  D --> F["wondershaper on default-route iface"]
  E --> F
  F --> G{"tc qdisc active?"}
  G -->|yes| OK["limit applied"]
  G -->|no| Fail["apply fails · clear partial state"]
```

Upload is set to a high **legal** “uncapped” rate (clamped for HTB). Extremely large historical defaults (e.g. 100000 Mbps) produced `Illegal "rate"` on some kernels.

## Apply verification and soft-fail

After wondershaper runs, the utility checks that a shaping qdisc is active (`tc qdisc show`, or hermetic mocks). If apply fails:

| Command | Behavior |
| --- | --- |
| `run` | **Hard-fail** (operator asked for a standing limit) |
| `wrap` | **Soft-fail** by default: warn + run command **unthrottled** (SSH risk), still clear on exit |
| `wrap` + `DOWNLOAD_LIMIT_REQUIRE=1` | **Hard-fail** like `run` |

**Safety impact:** Soft-fail can saturate the WAN when HTB/wondershaper is broken. Prefer fixing qdisc modules (`sch_htb`) or using a lower fixed limit once shaping works. Clear-on-exit remains mandatory.

## Wrap lifecycle

`wrap` always clears on `EXIT` / `INT` / `TERM` so a killed download cannot leave the host permanently throttled.

```mermaid
sequenceDiagram
  participant Op as Operator / manage.sh
  participant W as download-limit wrap
  participant WS as wondershaper
  participant Cmd as command e.g. download-flux

  Op->>W: wrap --limit auto -- command
  W->>WS: apply limit + verify qdisc
  alt apply ok
    W->>Cmd: run throttled
  else apply fail and not REQUIRE
    W-->>Op: warn unthrottled SSH risk
    W->>Cmd: run unthrottled
  else apply fail and REQUIRE=1
    W-->>Op: hard fail
  end
  alt success
    Cmd-->>W: exit 0
  else kill / fail
    Cmd-->>W: INT / TERM / non-zero
  end
  W->>WS: clear limit trap EXIT/INT/TERM
  Note over W,WS: Always clear even when traps fire on kill
```

## Emergency clear

If the host feels “stuck” throttled after a crash:

```bash
./scripts/utilities/download-limit.sh clear
```

`wrap` always clears on `EXIT` / `INT` / `TERM`.

```mermaid
flowchart TB
  Stuck["Host feels stuck<br/>or trap skipped"] --> Clear["download-limit clear<br/>or manage.sh download-limit clear"]
  Clear --> Resume["Resume SSH / downloads"]
```

## Units

Limits are in **Mbps** (megabits), not MB/s. Example: 40 Mbps ≈ 5 MB/s.
