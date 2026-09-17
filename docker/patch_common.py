"""Shared fail-soft helpers for Spark ComfyUI rewrite patches.

Needles, markers, and log prefixes stay in each ``patch_*.py``. This module
owns compile checks, newline-aware splice, and the default-root CLI.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

DEFAULT_COMFY_ROOT = "/comfy-state/ComfyUI"
"""Container ComfyUI checkout used when the CLI is given no path."""


def compiles(
    source: str,
    filename: str = "<patch>",
    *,
    allow_indented_snippet: bool = False,
) -> bool:
    """Return True if source is valid Python syntax.

    Args:
        source: Python source to compile.
        filename: Name used in SyntaxError messages.
        allow_indented_snippet: When True, also accept an indent-only block
            by wrapping it as a function body (unit tests for
            ``patch_get_free_memory``).

    Returns:
        Whether ``source`` compiles as a module (or wrapped snippet).
    """
    try:
        compile(source, filename, "exec")
        return True
    except SyntaxError:
        pass
    if not allow_indented_snippet:
        return False
    body = "".join(
        ("    " + ln if ln.strip() else ln) for ln in source.splitlines(keepends=True)
    )
    try:
        compile(f"def _lab_wrap():\n{body}", filename, "exec")
        return True
    except SyntaxError:
        return False


def consumed_and_newline(text: str, needle: str, idx: int) -> tuple[str, str]:
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


def cli_main(
    apply: Callable[[Path], int],
    argv: list[str] | None = None,
    *,
    default_root: str = DEFAULT_COMFY_ROOT,
) -> int:
    """CLI entrypoint: optional ComfyUI root, then ``apply(root)``.

    Args:
        apply: Patch function (always fail-soft ``0`` in production).
        argv: Argument vector *without* the program name. ``None`` uses
            ``sys.argv[1:]``.
        default_root: Used when ``argv`` is empty.

    Returns:
        Exit code from ``apply``.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0] if args else default_root)
    return apply(root)
