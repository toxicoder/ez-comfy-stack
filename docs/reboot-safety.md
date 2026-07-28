---
title: Reboot Safety
description: Stop the ComfyUI stack before rebooting a remotely managed DGX Spark.
tags: [safety, reboot]
---

# Reboot Safety

**What's on this page**

- Golden rule and recommended sequence
- Why containers do not auto-return after reboot
- Recovery when SSH is already unresponsive

**What this enables**

- Rebooting a Spark without losing SSH recoverability or corrupting long downloads

## Golden rule

**Never reboot with the heavy ComfyUI stack still running.**

```mermaid
flowchart LR
  subgraph Unsafe["Anti-pattern"]
    R1["Stack still running"] --> R2["reboot"]
    R2 --> R3["Risk: load / recovery pain"]
  end
  subgraph Safe["Golden path"]
    S1["manage.sh stop"] --> S2["status"]
    S2 --> S3["reboot"]
    S3 --> S4["doctor → start"]
  end
```

## Sequence

1. From your workstation / SSH session:

   ```bash
   ./scripts/manage.sh stop
   ./scripts/manage.sh status
   ```

2. Reboot the node (`sudo reboot` or out-of-band BMC).

3. After boot, verify Docker and GPU:

   ```bash
   ./scripts/manage.sh doctor
   ```

4. Only then start again:

   ```bash
   ./scripts/manage.sh start
   ```

```mermaid
sequenceDiagram
  actor Op as Operator
  participant M as manage.sh
  participant H as Spark host
  participant D as Docker / ComfyUI

  Op->>M: stop
  M->>D: compose down keep models + volume
  Op->>M: status
  M-->>Op: stopped
  Op->>H: reboot / BMC
  H-->>Op: back up
  Op->>M: doctor
  M-->>Op: preflight OK
  Op->>M: start type yes
  M->>D: compose up
```

## Why containers do not return

Compose uses `restart: "no"`. There is no systemd unit that auto-starts this demo. That is intentional.

```mermaid
stateDiagram-v2
  [*] --> Stopped
  Stopped --> Running: manage.sh start type yes
  Running --> Stopped: manage.sh stop
  Running --> Stopped: host reboot restart no
  Stopped --> Stopped: host reboot stays off
  note right of Stopped
    Manual start only.
    No systemd auto-start.
  end note
```

## If SSH is already unresponsive

- Use BMC / serial console  
- Hard power cycle only as last resort  
- After recovery: `download-limit clear`, `manage.sh stop`, then doctor  

```mermaid
flowchart TB
  Dead["SSH unresponsive"] --> BMC["BMC / serial console"]
  BMC --> Power{"hard power cycle<br/>last resort?"}
  Power -->|only if needed| Cycle["Power cycle"]
  Power -->|console works| Shell["Host shell"]
  Cycle --> Shell
  Shell --> Clear["download-limit clear"]
  Clear --> Stop["manage.sh stop"]
  Stop --> Doctor["manage.sh doctor"]
  Doctor --> Start["manage.sh start when ready"]
```
