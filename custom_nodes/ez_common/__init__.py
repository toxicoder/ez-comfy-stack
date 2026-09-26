"""Shared operator progress and output-dir resolution for in-canvas ez_* packs.

No nodes. Other packs must lazy-import this module inside functions (Comfy 0.34
does not register sibling folder names at load). Type-only imports of
``ComfyInputTypes`` under ``TYPE_CHECKING`` are safe because every pack uses
``from __future__ import annotations``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, TypeAlias

from .path import ensure_custom_nodes_path
from .protocols import (
    ComfyNode,
    CompletedProc,
    FileSystem,
    OccupancyPolicy,
    OccupancySource,
    ProgressReporter,
    StatusSink,
    SubprocessRunner,
)

NODE_CLASS_MAPPINGS: dict[str, type[Any]] = {}
"""Comfy registry (empty - this pack has no nodes)."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
"""Comfy display-name registry (empty - this pack has no nodes)."""

_DEFAULT_OUTPUT = "/mnt/comfy-output"
"""Host fallback when Comfy and container paths are unset."""

_CONTAINER_OUTPUT = "/outputs"
"""In-container compose bind; used when that directory exists."""


ComfyInputTypes: TypeAlias = dict[str, Any]
"""ComfyUI ``INPUT_TYPES`` payload (required/optional/hidden widget specs).

Widget values stay ``Any``: combo lists and option dicts mix str/int/bool.
Tensor types are not imported here. TypedDict is avoided so tests can index
``optional`` when a node omits that key.
"""


class NullProgress:
    """Stand-in when Comfy ProgressBar is unavailable (pytest)."""

    def update(self, n: int = 1) -> None:
        """Ignore a relative progress step.

        Args:
            n: Unused step count (Comfy ProgressBar API).
        """
        return

    def update_absolute(self, value: int) -> None:
        """Ignore an absolute progress value.

        Args:
            value: Unused absolute value (Comfy ProgressBar API).
        """
        return


class NodeLogSink:
    """:class:`StatusSink` that writes ``[prefix] message`` via :func:`node_log`."""

    def __init__(self, prefix: str) -> None:
        """Bind a pack prefix.

        Args:
            prefix: Pack id such as ``ez_dub``.
        """
        self._prefix = prefix

    def log(self, message: str) -> None:
        """Write a human status line.

        Args:
            message: Status text without a trailing newline.
        """
        node_log(self._prefix, message)


def node_log(prefix: str, message: str) -> None:
    """Write ``[prefix] message`` to stderr (shows up in manage.sh logs).

    Args:
        prefix: Pack id such as ``ez_dub``.
        message: Human status line without a trailing newline.
    """
    print(f"[{prefix}] {message}", file=sys.stderr)


def node_progress(total: int) -> ProgressReporter:
    """Comfy ProgressBar when importable, else NullProgress.

    Args:
        total: Expected steps; values below 1 clamp to 1.

    Returns:
        Comfy ``ProgressBar`` or :class:`NullProgress` (both match
        :class:`ProgressReporter`).
    """
    n = int(total) if total else 1
    if n < 1:
        n = 1
    try:
        from comfy.utils import ProgressBar  # type: ignore[import-not-found]

        return ProgressBar(n)
    except Exception:  # noqa: BLE001 - fail-soft in tests / missing Comfy
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
    except Exception:  # noqa: BLE001 - Comfy is optional in unit tests
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


__all__ = [
    "ComfyInputTypes",
    "ComfyNode",
    "CompletedProc",
    "FileSystem",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "NodeLogSink",
    "NullProgress",
    "OccupancyPolicy",
    "OccupancySource",
    "ProgressReporter",
    "StatusSink",
    "SubprocessRunner",
    "ensure_custom_nodes_path",
    "node_log",
    "node_progress",
    "output_root",
]
