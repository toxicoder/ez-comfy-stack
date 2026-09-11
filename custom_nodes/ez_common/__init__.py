"""Shared operator progress for in-canvas ez_* packs. No nodes."""

from __future__ import annotations

import sys
from typing import Any

NODE_CLASS_MAPPINGS: dict[str, Any] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}


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
