#!/usr/bin/env python3
"""Patch ComfyUI free-memory queries for NVIDIA DGX Spark (GB10) unified memory.

Background
----------
On Grace Blackwell GB10, CUDA memory is unified with system RAM. ComfyUI's
``torch.cuda.mem_get_info`` path often under-reports free "VRAM" when any other
CUDA context holds allocations. ComfyUI then thrash-offloads models onto the
*same* physical memory, producing extreme slowdowns (often reported as 5–15×).

This module rewrites the free-memory probe in ``comfy/model_management.py`` so
it uses ``psutil.virtual_memory().available`` (host free RAM) instead of the
under-reported CUDA query.

Properties
----------
* **Idempotent** — a marker comment prevents double application.
* **Fail-soft** — missing files or unknown ComfyUI revisions skip with warnings
  and exit 0 so container entrypoints do not crash install paths.
* **Multi-pattern** — handles several historical ``mem_get_info`` call shapes.

Typical invocation
------------------
Inside the container (as root or the install user)::

    python3 /opt/ez-comfy/patch_get_free_memory.py /comfy-state/ComfyUI

Reference
---------
https://forums.developer.nvidia.com/t/comfyui-setup-optimized-for-dgx-spark/364846
"""

from __future__ import annotations

import sys
from pathlib import Path

# Marker embedded in patched lines so re-runs are no-ops.
MARKER = "LAB_SPARK_UNIFIED_MEMORY_PATCH"


def apply_patch(root: Path) -> int:
    """Apply the unified-memory free-memory override under a ComfyUI install root.

    Locates ``comfy/model_management.py``, searches for a known
    ``torch.cuda.mem_get_info`` assignment pattern, and replaces it with a
    ``psutil.virtual_memory().available`` read. If the marker is already present,
    returns success without rewriting.

    Args:
        root: Absolute or relative path to the ComfyUI repository root (the
            directory that contains the ``comfy/`` package). Defaults are chosen
            by :func:`main` when invoked from the CLI.

    Returns:
        Process-style exit code. Always ``0`` for skip/apply/warn paths so
        install scripts can treat patching as best-effort. Does not raise on
        ordinary version-drift misses.

    Side effects:
        May rewrite ``comfy/model_management.py`` in place (UTF-8). Prints status
        to stdout/stderr for container logs.

    Notes:
        Callers should ensure ``psutil`` is installed in the ComfyUI venv before
        runtime; install-comfy.sh installs it with Comfy requirements.
    """
    path = root / "comfy" / "model_management.py"
    if not path.is_file():
        print(f"[spark-patch] skip: missing {path}", file=sys.stderr)
        return 0
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("[spark-patch] already applied")
        return 0
    old = "mem_free_cuda, _ = torch.cuda.mem_get_info(dev)"
    new = (
        f"import psutil as _lab_psutil  # {MARKER}\n"
        f"        mem_free_cuda = _lab_psutil.virtual_memory().available  # {MARKER}"
    )
    if old not in text:
        alts = [
            "mem_free_total, mem_free_torch = torch.cuda.mem_get_info(dev)",
            "free_memory, total_memory = torch.cuda.mem_get_info(device)",
        ]
        matched = False
        for alt in alts:
            if alt in text:
                old = alt
                new = (
                    f"import psutil as _lab_psutil  # {MARKER}\n"
                    f"        mem_free_cuda = _lab_psutil.virtual_memory().available  # {MARKER}\n"
                    f"        mem_free_total = mem_free_cuda  # {MARKER}"
                )
                matched = True
                break
        if not matched:
            print(
                "[spark-patch] WARNING: expected mem_get_info pattern not found; "
                "unified-memory patch skipped (ComfyUI version drift)",
                file=sys.stderr,
            )
            return 0
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[spark-patch] applied unified-memory free-memory override to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for container entrypoints and manual operator use.

    Args:
        argv: Optional argument vector *without* the program name. When ``None``,
            uses ``sys.argv[1:]``. The first argument, if present, is the ComfyUI
            root; otherwise defaults to ``/comfy-state/ComfyUI``.

    Returns:
        Exit code from :func:`apply_patch` (normally ``0``).

    Raises:
        This function does not intentionally raise; filesystem errors from
        :meth:`Path.read_text` / :meth:`Path.write_text` may propagate to the
        caller for unexpected permission failures.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0] if args else "/comfy-state/ComfyUI")
    return apply_patch(root)


if __name__ == "__main__":
    raise SystemExit(main())
