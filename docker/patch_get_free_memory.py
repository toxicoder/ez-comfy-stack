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
* **Indent-safe** — single-line replacements preserve the matched line's indent
  (older multi-line inserts caused IndentationError on modern ComfyUI).
* **Self-healing** — if a previous broken patch is detected (MARKER present but
  file does not compile), restore via git checkout when possible and re-apply.
* **Fail-soft** — missing files or unknown ComfyUI revisions skip with warnings
  and exit 0 so container entrypoints do not crash install paths.

Typical invocation
------------------
Inside the container (as root or the install user)::

    python3 /opt/ez-comfy/patch_get_free_memory.py /comfy-state/ComfyUI

Reference
---------
https://forums.developer.nvidia.com/t/comfyui-setup-optimized-for-dgx-spark/364846
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Marker embedded in patched lines so re-runs are no-ops.
MARKER = "LAB_SPARK_UNIFIED_MEMORY_PATCH"

# (substring to find on a line, replacement RHS using same indent + MARKER)
# Replacement is a full line body without leading whitespace; indent is copied.
_PATTERNS: list[tuple[str, str]] = [
    (
        "mem_free_cuda, _ = torch.cuda.mem_get_info(dev)",
        "mem_free_cuda, _ = (__import__('psutil').virtual_memory().available, 0)"
        f"  # {MARKER}",
    ),
    (
        "mem_free_total, mem_free_torch = torch.cuda.mem_get_info(dev)",
        "mem_free_total, mem_free_torch = "
        "(__import__('psutil').virtual_memory().available, 0)"
        f"  # {MARKER}",
    ),
    (
        "free_memory, total_memory = torch.cuda.mem_get_info(device)",
        "free_memory, total_memory = ("
        "__import__('psutil').virtual_memory().available, "
        "__import__('psutil').virtual_memory().total)"
        f"  # {MARKER}",
    ),
]


def _compiles(source: str, filename: str = "<model_management.py>") -> bool:
    """Return True if source is valid Python syntax.

    Full modules (real ComfyUI files) compile as ``exec``. Indent-only snippets
    used in unit tests are accepted if they form a valid function body when wrapped.
    """
    try:
        compile(source, filename, "exec")
        return True
    except SyntaxError:
        pass
    # Snippet that is only an indented block (tests) — wrap as function body
    body = "".join(
        ("    " + ln if ln.strip() else ln) for ln in source.splitlines(keepends=True)
    )
    try:
        compile(f"def _lab_wrap():\n{body}", filename, "exec")
        return True
    except SyntaxError:
        return False


def _restore_from_git(root: Path, rel: str = "comfy/model_management.py") -> bool:
    """Best-effort git checkout of a file under the ComfyUI root."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "checkout", "--", rel],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _strip_marker_lines(text: str) -> str:
    """Remove lines that contain the patch marker (best-effort unpatch)."""
    lines = text.splitlines(keepends=True)
    kept = [ln for ln in lines if MARKER not in ln]
    return "".join(kept)


def _apply_single_line(text: str) -> tuple[str, bool]:
    """Replace the first matching mem_get_info line; preserve its indent.

    Returns:
        (new_text, changed)
    """
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        stripped = line.lstrip(" \t")
        # Keep newline style from original line
        nl = "\n"
        if line.endswith("\r\n"):
            nl = "\r\n"
        elif line.endswith("\n"):
            nl = "\n"
        core = stripped.rstrip("\r\n")
        for needle, replacement in _PATTERNS:
            if needle in core and MARKER not in core:
                indent = line[: len(line) - len(stripped)]
                lines[i] = f"{indent}{replacement}{nl}"
                return "".join(lines), True
    return text, False


def repair_broken_patch(root: Path, path: Path, text: str) -> str:
    """If a prior patch left invalid syntax, restore a clean file when possible.

    Order: git checkout → strip marker lines. Returns text to continue applying on.
    """
    print(
        "[spark-patch] prior patch left invalid syntax — attempting repair",
        file=sys.stderr,
    )
    if _restore_from_git(root):
        if path.is_file():
            with path.open(encoding="utf-8", newline="") as fh:
                restored = fh.read()
            if _compiles(restored, str(path)):
                print("[spark-patch] restored comfy/model_management.py via git")
                return restored
    stripped = _strip_marker_lines(text)
    if stripped != text:
        print("[spark-patch] stripped prior marker lines (best-effort)")
    return stripped


def apply_patch(root: Path) -> int:
    """Apply the unified-memory free-memory override under a ComfyUI install root.

    Locates ``comfy/model_management.py``, searches for a known
    ``torch.cuda.mem_get_info`` assignment pattern, and replaces it with a
    single-line ``psutil``-based free RAM read (same indentation). If a broken
    previous patch is present, repairs then re-applies.

    Args:
        root: Path to the ComfyUI repository root (contains ``comfy/``).

    Returns:
        Always ``0`` for skip/apply/warn paths (fail-soft for entrypoints).
    """
    path = root / "comfy" / "model_management.py"
    if not path.is_file():
        print(f"[spark-patch] skip: missing {path}", file=sys.stderr)
        return 0

    with path.open(encoding="utf-8", newline="") as fh:
        original = fh.read()
    text = original

    if MARKER in text:
        if _compiles(text, str(path)):
            print("[spark-patch] already applied")
            return 0
        text = repair_broken_patch(root, path, text)
        if MARKER in text and _compiles(text, str(path)):
            if text != original:
                with path.open("w", encoding="utf-8", newline="") as fh:
                    fh.write(text)
            print("[spark-patch] already applied (after repair)")
            return 0
        # fall through to apply on cleaned text (may still contain no MARKER)

    new_text, changed = _apply_single_line(text)
    if not changed:
        print(
            "[spark-patch] WARNING: expected mem_get_info pattern not found; "
            "unified-memory patch skipped (ComfyUI version drift)",
            file=sys.stderr,
        )
        # Persist repair (e.g. git restore / strip) even if re-apply missed
        if text != original and _compiles(text, str(path)):
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            print("[spark-patch] wrote repaired file without re-apply")
        return 0

    if not _compiles(new_text, str(path)):
        print(
            "[spark-patch] WARNING: patched file would not compile; not writing",
            file=sys.stderr,
        )
        return 0

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
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
    """
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0] if args else "/comfy-state/ComfyUI")
    return apply_patch(root)


if __name__ == "__main__":
    raise SystemExit(main())
