"""Read-only occupancy XOR for in-canvas Queue (fail-closed).

The mode machine itself lives in :mod:`ez_common.occupancy`, which mirrors
``scripts/lib/occupancy.sh``. This module is the Comfy-facing wrapper: it turns
a verdict into an :class:`OccupancyError`, and it never blocks a Queue on a
desk record whose sidecar is gone.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ez_common.occupancy import (
    HEAVY_MODES,
    Occupancy,
    OccupancyStateError,
    decide_heavy_queue,
    read_state,
)

from .pack import output_directory

__all__ = [
    "HEAVY_MODES",
    "OccupancyError",
    "check_occupancy",
    "occupancy_path",
    "read_mode",
]


class OccupancyError(RuntimeError):
    """Occupancy XOR refused this Queue."""


def _warn(message: str) -> None:
    """Surface a non-fatal occupancy note to the ComfyUI log.

    Args:
        message: Line to print after the pack prefix.
    """
    print(f"[ez_dcc occupancy] {message}", file=sys.stderr)


def occupancy_path() -> Path:
    """``${COMFY_OUTPUT_DIR}/.occupancy.json`` (outputs tree, never MODELS_DIR).

    Returns:
        Occupancy state file path (may not exist yet).
    """
    return output_directory() / ".occupancy.json"


def _read(path: Path | None = None) -> Occupancy:
    """Read the record, mapping a corrupt file onto :class:`OccupancyError`.

    Args:
        path: State file. Default: :func:`occupancy_path`.

    Returns:
        The immutable read.

    Raises:
        OccupancyError: File exists but is unreadable or not a JSON object.
    """
    try:
        return read_state(occupancy_path() if path is None else path)
    except OccupancyStateError as exc:
        raise OccupancyError(str(exc)) from exc


def read_mode(path: Path | None = None) -> str:
    """Return the recorded occupancy mode, or ``unknown`` when none exists.

    This is the raw record. Policy reads
    :attr:`ez_common.occupancy.Occupancy.effective_mode`, which reads a desk
    whose sidecar died as released.

    Args:
        path: State file. Default: :func:`occupancy_path`.

    Returns:
        Mode string.

    Raises:
        OccupancyError: File exists but is unreadable or not a JSON object.
    """
    return _read(path).mode


def check_occupancy(required_mode: str) -> str:
    """Fail-closed XOR against ``.occupancy.json``.

    Missing file passes as ``unknown`` (first-run / pytest). Does not start
    Compose, does not call Manager unload, does not launch a host DCC.

    A desk mode blocks the Queue only while its sidecar lives. A ``blender-desk``
    or ``llm-desk`` record left behind by a killed sidecar or a host reboot
    names no GPU work, so it releases with a log line rather than dead-ending
    the graph on an instruction the operator cannot carry out.

    Args:
        required_mode: Heavy mode this graph needs (klein / trellis / wan / ltx).

    Returns:
        Current mode (``unknown`` when the file is missing).

    Raises:
        OccupancyError: idle, a live blender-desk or llm-desk, or a mismatched
            heavy mode.
    """
    required = str(required_mode or "").strip()
    state = _read()
    allowed, hint = decide_heavy_queue(required, state)
    if not allowed:
        raise OccupancyError(hint)
    if hint:
        _warn(hint)
    return state.mode
