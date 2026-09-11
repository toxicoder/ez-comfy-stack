"""Read-only occupancy XOR for in-canvas Queue (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

from .pack import output_directory

HEAVY_MODES = ("klein", "trellis", "wan", "ltx")


class OccupancyError(RuntimeError):
    """Occupancy XOR refused this Queue."""


def occupancy_path() -> Path:
    """``${COMFY_OUTPUT_DIR}/.occupancy.json`` (outputs tree, never MODELS_DIR)."""
    return output_directory() / ".occupancy.json"


def read_mode(path: Path | None = None) -> str:
    """Return occupancy mode, or ``unknown`` when the file is missing.

    Args:
        path: State file. Default: ``occupancy_path()``.

    Returns:
        Mode string.

    Raises:
        OccupancyError: file exists but is unreadable or not a JSON object.
    """
    state = occupancy_path() if path is None else path
    if not state.is_file():
        return "unknown"
    try:
        raw = state.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise OccupancyError(f"unreadable occupancy state at {state}: {exc}") from exc
    if not isinstance(data, dict):
        raise OccupancyError(f"occupancy state at {state} is not a JSON object")
    mode = str(data.get("mode") or "").strip()
    return mode or "unknown"


def check_occupancy(required_mode: str) -> str:
    """Fail-closed XOR against ``.occupancy.json``.

    Missing file passes as ``unknown`` (first-run / pytest). Does not start
    Compose, does not call Manager unload, does not launch a host DCC.

    Args:
        required_mode: Heavy mode this graph needs (klein / trellis / wan / ltx).

    Returns:
        Current mode (``unknown`` when the file is missing).

    Raises:
        OccupancyError: idle, blender-desk, or mismatched heavy mode.
    """
    required = str(required_mode or "").strip()
    mode = read_mode()
    if mode == "unknown":
        return mode
    if mode == required:
        return mode
    if mode == "idle":
        raise OccupancyError(
            f"occupancy is idle; occupancy enter {required} then start"
        )
    if mode == "blender-desk":
        raise OccupancyError(
            "occupancy is blender-desk (park is for dumps); "
            f"stop Blender, occupancy enter {required} --yes"
        )
    raise OccupancyError(
        f"occupancy is {mode}, required {required}; unload first"
    )
