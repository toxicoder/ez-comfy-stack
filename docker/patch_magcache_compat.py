#!/usr/bin/env python3
"""Make ComfyUI-MagCache import on ComfyUI v0.34+ (LTX RoPE refactor).

Background
----------
MagCache ``nodes.py`` and ``nodes_calibration.py`` still do::

    from comfy.ldm.lightricks.model import precompute_freqs_cis

ComfyUI v0.34.6 moved that helper to ``LTXBaseModel._precompute_freqs_cis``.
The module-level import fails the whole pack: ``__init__.py`` imports
calibration after ``nodes.py``, so wrapping only ``nodes.py`` still leaves
Wan 5B MagCache (``wan-i2v-5s-lab-example``) as IMPORT FAILED. Hero LTX
graphs must not use MagCache.

This rewrite wraps the import in every MagCache ``*.py`` that still has it,
and fail-softs the calibration import in ``__init__.py`` so a later
calibration break cannot take down Wan MagCache. Fail-soft: missing files
or unknown revisions skip with a warning and exit 0.

Idempotency is **per file**. A volume that already has ``nodes.py`` wrapped
must still wrap ``nodes_calibration.py`` on the next start.

Typical invocation
------------------
    python3 /opt/ez-comfy/patch_magcache_compat.py /comfy-state/ComfyUI
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "LAB_MAGCACHE_FREQS_PATCH"
INIT_MARKER = "LAB_MAGCACHE_CAL_IMPORT_PATCH"
PACK_REL = Path("custom_nodes") / "ComfyUI-MagCache"
NEEDLE = "from comfy.ldm.lightricks.model import precompute_freqs_cis"
INIT_NEEDLE = (
    "from .nodes_calibration import NODE_CLASS_MAPPINGS as Cal_NODES_CLASS, "
    "NODE_DISPLAY_NAME_MAPPINGS as Cal_NODES_DISPLAY"
)
FREQS_WARN_NAMES = frozenset({"nodes.py", "nodes_calibration.py"})


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


def _init_replacement(newline: str) -> str:
    """Return the fail-soft calibration import for MagCache ``__init__.py``.

    Args:
        newline: ``\\n`` or ``\\r\\n``.

    Returns:
        Source that always binds ``Cal_NODES_CLASS`` / ``Cal_NODES_DISPLAY``.
    """
    lines = (
        "try:",
        f"    {INIT_NEEDLE}  # {INIT_MARKER}",
        "except ImportError:",
        f"    Cal_NODES_CLASS = {{}}  # {INIT_MARKER}",
        "    Cal_NODES_DISPLAY = {}",
    )
    return newline.join(lines) + newline


def _compiles(source: str, filename: str = "<nodes.py>") -> bool:
    """Return True if source is valid Python syntax."""
    try:
        compile(source, filename, "exec")
        return True
    except SyntaxError:
        return False


def _consumed_and_newline(text: str, needle: str, idx: int) -> tuple[str, str]:
    """Return the needle plus its trailing newline, and the newline style.

    Args:
        text: File contents.
        needle: Exact substring at ``idx``.
        idx: Start of ``needle`` in ``text``.

    Returns:
        ``(consumed, newline)`` where ``consumed`` is replaced as a unit.
    """
    after = text[idx + len(needle) :]
    if after.startswith("\r\n"):
        return needle + "\r\n", "\r\n"
    if after.startswith("\n"):
        return needle + "\n", "\n"
    return needle, "\n"


def _splice(text: str, needle: str, block: str) -> str:
    """Replace the first ``needle`` line with ``block``.

    Args:
        text: File contents.
        needle: Exact import line without newline.
        block: Replacement including a trailing newline.

    Returns:
        New file contents.
    """
    idx = text.find(needle)
    consumed, _newline = _consumed_and_newline(text, needle, idx)
    return text[:idx] + block + text[idx + len(consumed) :]


def _write_if_compiles(path: Path, new_text: str, ok_message: str) -> None:
    """Write ``new_text`` when it compiles; otherwise warn and keep the file.

    Args:
        path: Target path.
        new_text: Candidate source.
        ok_message: Printed on success.
    """
    if not _compiles(new_text, str(path)):
        print(
            "[magcache-compat] WARNING: patched file would not compile; not writing",
            file=sys.stderr,
        )
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    print(ok_message)


def _patch_freqs_import(path: Path) -> None:
    """Wrap the LTX RoPE import in one MagCache module.

    Args:
        path: A ``*.py`` file under ComfyUI-MagCache.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    if MARKER in text:
        print("[magcache-compat] already applied")
        return
    if NEEDLE not in text:
        if path.name in FREQS_WARN_NAMES:
            print(
                "[magcache-compat] WARNING: expected LTX precompute_freqs_cis import "
                "not found; MagCache compat patch skipped (upstream change)",
                file=sys.stderr,
            )
        return
    _, newline = _consumed_and_newline(text, NEEDLE, text.find(NEEDLE))
    new_text = _splice(text, NEEDLE, _replacement(newline))
    _write_if_compiles(
        path, new_text, f"[magcache-compat] wrapped LTX RoPE import in {path}"
    )


def _patch_calibration_import(path: Path) -> None:
    """Fail-soft MagCache ``__init__.py`` calibration import.

    Args:
        path: MagCache ``__init__.py`` (may be missing).
    """
    if not path.is_file():
        return
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    if INIT_MARKER in text:
        print("[magcache-compat] already applied")
        return
    if INIT_NEEDLE not in text:
        print(
            "[magcache-compat] WARNING: expected nodes_calibration import "
            "not found; MagCache compat patch skipped (upstream change)",
            file=sys.stderr,
        )
        return
    _, newline = _consumed_and_newline(text, INIT_NEEDLE, text.find(INIT_NEEDLE))
    new_text = _splice(text, INIT_NEEDLE, _init_replacement(newline))
    _write_if_compiles(
        path, new_text, f"[magcache-compat] wrapped calibration import in {path}"
    )


def apply_patch(root: Path) -> int:
    """Wrap MagCache's LTX RoPE import under a ComfyUI root.

    Args:
        root: Path to the ComfyUI repository root (contains ``custom_nodes/``).

    Returns:
        Always ``0`` (fail-soft for entrypoints).
    """
    pack = root / PACK_REL
    if not pack.is_dir():
        print(f"[magcache-compat] skip: missing {pack}", file=sys.stderr)
        return 0
    for path in sorted(pack.glob("*.py")):
        _patch_freqs_import(path)
    _patch_calibration_import(pack / "__init__.py")
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
