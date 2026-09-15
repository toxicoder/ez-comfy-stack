"""Shared operator progress and output-dir resolution for in-canvas ez_* packs.

No nodes. Other packs must lazy-import this module inside functions (Comfy 0.34
does not register sibling folder names at load).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

NODE_CLASS_MAPPINGS: dict[str, Any] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

_DEFAULT_OUTPUT = "/mnt/comfy-output"
_CONTAINER_OUTPUT = "/outputs"


class NullProgress:
    """Stand-in when Comfy ProgressBar is unavailable (pytest)."""

    def update(self, n: int = 1) -> None:
        return

    def update_absolute(self, value: int) -> None:
        return


def node_log(prefix: str, message: str) -> None:
    """Write ``[prefix] message`` to stderr (shows up in manage.sh logs)."""
    print(f"[{prefix}] {message}", file=sys.stderr)


def node_progress(total: int) -> Any:
    """Comfy ProgressBar when importable, else NullProgress."""
    n = int(total) if total else 1
    if n < 1:
        n = 1
    try:
        from comfy.utils import ProgressBar  # type: ignore[import-not-found]

        return ProgressBar(n)
    except Exception:  # noqa: BLE001 — fail-soft in tests / missing Comfy
        return NullProgress()


def output_root(*, default: str | Path | None = _DEFAULT_OUTPUT) -> Path:
    """Resolve the durable Comfy output directory (container bind or host).

    Prefer Comfy ``folder_paths``, then ``/outputs`` when that directory
    exists, then ``COMFY_OUTPUT_DIR`` / ``COMFY_OUTPUT``. Compose sets the
    container env to ``/outputs``; host scripts keep the host path.

    Args:
        default: Last-resort path when nothing else is set. ``None`` uses
            ``/mnt/comfy-output``.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        import folder_paths  # type: ignore[import-not-found]

        raw = folder_paths.get_output_directory()
        if raw:
            return Path(raw)
    except Exception:  # noqa: BLE001 — Comfy is optional in unit tests
        pass
    if Path(_CONTAINER_OUTPUT).is_dir():
        return Path(_CONTAINER_OUTPUT)
    for key in ("COMFY_OUTPUT_DIR", "COMFY_OUTPUT"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return Path(value)
    if default is None:
        return Path(_DEFAULT_OUTPUT)
    return Path(default)
