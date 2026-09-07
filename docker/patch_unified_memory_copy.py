#!/usr/bin/env python3
"""Patch ComfyUI safetensor loads for NVIDIA DGX Spark (GB10) unified memory.

Background
----------
With ``--disable-mmap``, ComfyUI's ``comfy/utils.py`` does::

    tensor = tensor.to(device=device, copy=True)

On discrete GPUs that copy is a host→device transfer. On GB10 unified memory
it **duplicates** the tensor in the same physical pool (GitHub ComfyUI#10896,
NVIDIA Spark ComfyUI guides). Combined with mmap-disable, large safetensors
can appear to need ~2× RAM.

This module rewrites that assignment to ``copy=False``. Fail-soft: missing
files or unknown ComfyUI revisions skip with a warning and exit 0.

Typical invocation
------------------
    python3 /opt/ez-comfy/patch_unified_memory_copy.py /comfy-state/ComfyUI
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "LAB_SPARK_UM_COPY_PATCH"
REL_PATH = Path("comfy") / "utils.py"
NEEDLE = "tensor = tensor.to(device=device, copy=True)"
REPLACEMENT = f"tensor = tensor.to(device=device, copy=False)  # {MARKER}"


def _compiles(source: str, filename: str = "<utils.py>") -> bool:
    """Return True if source is valid Python syntax."""
    try:
        compile(source, filename, "exec")
        return True
    except SyntaxError:
        return False


def apply_patch(root: Path) -> int:
    """Apply the copy=False unified-memory override under a ComfyUI root.

    Args:
        root: Path to the ComfyUI repository root (contains ``comfy/``).

    Returns:
        Always ``0`` (fail-soft for entrypoints).
    """
    path = root / REL_PATH
    if not path.is_file():
        print(f"[spark-um-copy] skip: missing {path}", file=sys.stderr)
        return 0

    with path.open(encoding="utf-8", newline="") as fh:
        original = fh.read()
    text = original

    if MARKER in text:
        print("[spark-um-copy] already applied")
        return 0

    if NEEDLE not in text:
        if "copy=False" in text and "tensor.to(device=device" in text:
            print("[spark-um-copy] already copy=False (upstream); skip")
            return 0
        print(
            "[spark-um-copy] WARNING: expected copy=True load pattern not found; "
            "unified-memory copy patch skipped (ComfyUI version drift)",
            file=sys.stderr,
        )
        return 0

    new_text = text.replace(NEEDLE, REPLACEMENT, 1)
    if not _compiles(new_text, str(path)):
        print(
            "[spark-um-copy] WARNING: patched file would not compile; not writing",
            file=sys.stderr,
        )
        return 0

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    print(f"[spark-um-copy] applied copy=False safetensor load override to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for container entrypoints and manual operator use.

    Args:
        argv: Optional argument vector *without* the program name. When ``None``,
            uses ``sys.argv[1:]``. First argument is the ComfyUI root.

    Returns:
        Exit code from :func:`apply_patch` (normally ``0``).
    """
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0] if args else "/comfy-state/ComfyUI")
    return apply_patch(root)


if __name__ == "__main__":
    raise SystemExit(main())
