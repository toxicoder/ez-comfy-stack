#!/usr/bin/env python3
"""Make ComfyUI-MagCache import on ComfyUI v0.34+ (LTX RoPE refactor).

Background
----------
MagCache ``nodes.py`` still does::

    from comfy.ldm.lightricks.model import precompute_freqs_cis

ComfyUI v0.34.6 moved that helper to ``LTXBaseModel._precompute_freqs_cis``.
The module-level import fails the whole pack, including Wan 5B MagCache
(``wan-i2v-5s-lab-example``). Hero LTX graphs must not use MagCache.

This rewrite wraps the import in ``try/except ImportError`` so Wan MagCache
loads. MagCache-on-LTX stays unsupported. Fail-soft: missing files or unknown
revisions skip with a warning and exit 0.

Typical invocation
------------------
    python3 /opt/ez-comfy/patch_magcache_compat.py /comfy-state/ComfyUI
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "LAB_MAGCACHE_FREQS_PATCH"
REL_PATH = Path("custom_nodes") / "ComfyUI-MagCache" / "nodes.py"
NEEDLE = "from comfy.ldm.lightricks.model import precompute_freqs_cis"


def _replacement(newline: str) -> str:
    """Return the try/except import block for the given newline style.

    Args:
        newline: ``\\n`` or ``\\r\\n``.

    Returns:
        Source that still defines ``precompute_freqs_cis``.
    """
    lines = (
        "try:",
        f"    from comfy.ldm.lightricks.model import precompute_freqs_cis  # {MARKER}",
        "except ImportError:",
        f"    def precompute_freqs_cis(*_args, **_kwargs):  # {MARKER}",
        '        raise RuntimeError(',
        '            "MagCache LTX RoPE helper missing on this ComfyUI; "',
        '            "Wan MagCache still works"',
        "        )",
    )
    return newline.join(lines) + newline


def _compiles(source: str, filename: str = "<nodes.py>") -> bool:
    """Return True if source is valid Python syntax."""
    try:
        compile(source, filename, "exec")
        return True
    except SyntaxError:
        return False


def apply_patch(root: Path) -> int:
    """Wrap MagCache's LTX RoPE import under a ComfyUI root.

    Args:
        root: Path to the ComfyUI repository root (contains ``custom_nodes/``).

    Returns:
        Always ``0`` (fail-soft for entrypoints).
    """
    path = root / REL_PATH
    if not path.is_file():
        print(f"[magcache-compat] skip: missing {path}", file=sys.stderr)
        return 0

    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()

    if MARKER in text:
        print("[magcache-compat] already applied")
        return 0

    if NEEDLE not in text:
        print(
            "[magcache-compat] WARNING: expected LTX precompute_freqs_cis import "
            "not found; MagCache compat patch skipped (upstream change)",
            file=sys.stderr,
        )
        return 0

    idx = text.find(NEEDLE)
    after = text[idx + len(NEEDLE) :]
    if after.startswith("\r\n"):
        consumed = NEEDLE + "\r\n"
        newline = "\r\n"
    elif after.startswith("\n"):
        consumed = NEEDLE + "\n"
        newline = "\n"
    else:
        consumed = NEEDLE
        newline = "\n"
    new_text = text[:idx] + _replacement(newline) + text[idx + len(consumed) :]
    if not _compiles(new_text, str(path)):
        print(
            "[magcache-compat] WARNING: patched file would not compile; not writing",
            file=sys.stderr,
        )
        return 0

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    print(f"[magcache-compat] wrapped LTX RoPE import in {path}")
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
