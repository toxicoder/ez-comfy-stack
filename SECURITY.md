# Security

## Reporting

Please report vulnerabilities privately via GitHub Security Advisories on this repository (or the maintainer contact listed on the GitHub profile). Do not open public issues for exploitable flaws.

```mermaid
flowchart LR
  Find["Find vulnerability"] --> Private["GitHub Security Advisory<br/>or maintainer contact"]
  Find --> Public["Public issue"]
  Private --> Fix["Coordinated fix"]
  Public --> Avoid["Avoid for exploitable flaws"]
```

## Scope notes

- This project is a **lab/demo** stack for controlled DGX Spark environments.  
- Do not expose ComfyUI (port 8188) to the public internet without authentication / network policy.  
- Never commit `HF_TOKEN`, `.env`, or host secrets.  
- `download-limit` uses `sudo` for wondershaper — review sudoers policy on shared hosts.  

```mermaid
flowchart TB
  subgraph Private["Controlled environment"]
    Spark["DGX Spark LAN / VPN"]
    UI["ComfyUI :8188"]
    Spark --> UI
  end
  subgraph Public["Do not do this"]
    Inet["Public internet"]
    Open["Unauthenticated :8188"]
    Inet --> Open
  end
  Private -->|"auth / network policy required"| Edge["If remote access needed"]
```

## Operational safety

Resource exhaustion can be as bad as a software CVE when the host is remote-only. Prefer:

- Bandwidth limits for large downloads  
- Docker memory limits and host headroom checks  
- Manual start only (`restart: "no"`)  

```mermaid
flowchart TB
  L1["download-limit auto 85%"] --> Safe["SSH stays recoverable"]
  L2["mem_limit + headroom preflight"] --> Safe
  L3["restart: no · type yes on start"] --> Safe
```
