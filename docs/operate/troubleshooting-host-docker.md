---
title: Troubleshooting — host and Docker
description: Docker missing, group/daemon, MODELS_DIR permissions, and Spark farm SSH on DGX Spark.
tags: [troubleshooting, docker, models-dir, spark-farm]
---

# Troubleshooting — host and Docker

**What's on this page**

- **Docker missing** / group / daemon on a reimaged Spark
- **MODELS_DIR** not writable and nested `comfy/` permission
- **Spark farm SSH** — `SPARK_HOSTS` / `SPARK_FABRIC_IPS` from `config/spark-farm.example.env`

**What this enables**

- **Getting** `doctor` green after an OS reimage
- **Sharing** weights on the fabric without rsync over the mgmt NIC or a remote compose up

!!! warning "Prefer apt Docker CE"

    Snap Docker cannot attach the NVIDIA Container Toolkit. After `./scripts/manage.sh setup --install-docker`, `newgrp docker` or re-login SSH. Prefer `./scripts/manage.sh setup` when Docker or `${MODELS_DIR}` is missing.

!!! danger "Never remote compose up"

    Farm nodes still use `restart: "no"` and local heavy confirm. `spark-farm.sh` never starts compose on another Spark.

## Host & Docker

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `docker missing` in doctor | Docker not installed / snap-only | `./scripts/manage.sh setup --install-docker` (sudo apt CE + compose); then `newgrp docker` or re-login |
| docker permission denied | Not in `docker` group this session | `sudo usermod -aG docker $USER` then `newgrp docker` or re-login SSH |
| docker daemon not reachable | dockerd not running | `sudo systemctl start docker` |
| `MODELS_DIR … not writable` | `${MODELS_DIR}` missing or root-owned | `./scripts/manage.sh setup` (sudo mkdir + chown). Last resort: `sudo mkdir -p "${MODELS_DIR}" && sudo chown "$USER:$USER" "${MODELS_DIR}"` **or** `MODELS_DIR=$HOME/models` |
| `mkdir: …/comfy/…: Permission denied` during `download-models` | Nested `comfy/<subdir>` is root-owned (container `mkdir` on the bind-mount) while snapshots under `${MODELS_DIR}` are writable. Cache-hit still needs a writable layout dir to symlink. | Re-run `./scripts/manage.sh download-models` — linking now sudo-heals each layout dir (same heal on `setup` / `start`). Last resort: `sudo chown -R "$USER:$USER" "${MODELS_DIR}/comfy"` |
| `ln: … comfy/llm/….gguf: Permission denied` then `GGUF ready` | Relink into a nested dir the user cannot write; the GGUF is already present | Start is OK — Enhance works if that path exists. Heal: `./scripts/manage.sh download-models` **or** `setup` / `start` (sudo-chown `comfy/`). Do not abort start |
| Pending / can't start container | Docker/GPU runtime | `nvidia-smi`, Container Toolkit install |
| `failed to fetch oauth token: denied` / `nvcr.io` Access Denied on `start` | NGC base image pull without login | Pull latest (default bases are **Docker Hub** `nvidia/cuda` **runtime** for builder and final). Rebuild: `./scripts/manage.sh start`. If you set `CUDA_BASE_IMAGE` / `CUDA_RUNTIME_IMAGE` to `nvcr.io/...`, run `docker login nvcr.io` (user `$oauthtoken`, password = NGC API key) |
| Spark farm SSH / rsync over the wrong NIC | Using management hostnames for weights, or expecting remote compose | Source `config/spark-farm.example.env` (`SPARK_HOSTS` + `${SPARK_USER}` for SSH; `SPARK_FABRIC_IPS` for NFS/rsync). Never rsync weights over the management NIC. `./scripts/utilities/spark-farm.sh` **never** remote `compose up` — run `./scripts/manage.sh start` locally on each node (type **yes**). [Spark farm](../spark-farm.md) |

### Docker missing on DGX Spark

Docker is usually pre-installed on DGX Spark, but updates or OS reimages can remove it. Prefer **apt Docker CE** (not snap) so the NVIDIA Container Toolkit can attach GPUs.

```bash
./scripts/manage.sh setup --install-docker
# sudo password + type yes if prompted
newgrp docker   # if permission denied in this shell
./scripts/manage.sh doctor
```

=== "Interactive"

    ```bash
    ./scripts/manage.sh setup --install-docker
    ```

=== "Non-interactive"

    ```bash
    LAB_NON_INTERACTIVE=1 LAB_CONFIRM_TOKEN=yes SETUP_INSTALL_DOCKER=1 \
      ./scripts/manage.sh setup
    ```

### MODELS_DIR permission denied

Default cache is `/mnt/models` (shared with nvidia-dgx-spark-lab). Prefer bootstrap:

```bash
./scripts/manage.sh setup
# creates/chowns MODELS_DIR and MODELS_DIR/comfy with sudo when needed
```

`download-models` and `start` also sudo-heal nested `comfy/` (HF snapshots at the top level can be writable while `comfy/` is still root-owned). Do not prefix those commands with `sudo`.

Manual last resort:

```bash
sudo mkdir -p "${MODELS_DIR:-/mnt/models}/comfy"
sudo chown -R "$USER:$USER" "${MODELS_DIR:-/mnt/models}"
# or in .env:
# MODELS_DIR=$HOME/models
./scripts/manage.sh doctor
```

---
