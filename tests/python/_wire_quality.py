"""Stamp EZQuality onto shipped lab graphs.

Not collected by pytest (leading underscore). Builders and tests import
``ensure_quality_node``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_layout import estimated_node_size
from _lab_paths import lab_graph_paths

QUALITY_TYPE = "EZQuality"
QUALITY_TITLE = "Quality"
QUALITY_WIDGET = "quality"
QUALITY_DEFAULT = "lab"
QUALITY_SIZE = (320.0, 82.0)
QUALITY_PAD = 20.0
QUALITY_LABEL = {
    "label": "Quality",
    "description": (
        "custom freezes the last overlay. lab restores graph defaults. "
        "Free Commercial Use (<$10M) is Klein 4B + LTX-2.5 (never Non-Commercial stills). "
        "ultra/max may select opt-in Non-Commercial weights when on disk. "
        "Family-specific — not --tier."
    ),
}


def _node_rect(node: dict[str, Any]) -> tuple[float, float, float, float]:
    pos = node.get("pos") or [0, 0]
    x, y = float(pos[0]), float(pos[1])
    width, height = estimated_node_size(node)
    return x, y, width, height


def _padded(
    x: float, y: float, width: float, height: float
) -> tuple[float, float, float, float]:
    return (
        x - QUALITY_PAD,
        y - QUALITY_PAD,
        x + width + QUALITY_PAD,
        y + height + QUALITY_PAD,
    )


def _hit(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return (
        left[0] < right[2]
        and left[2] > right[0]
        and left[1] < right[3]
        and left[3] > right[1]
    )


def _occupied(graph: dict[str, Any]) -> list[tuple[float, float, float, float]]:
    boxes: list[tuple[float, float, float, float]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == QUALITY_TYPE:
            continue
        x, y, width, height = _node_rect(node)
        boxes.append(_padded(x, y, width, height))
    return boxes


def _place(graph: dict[str, Any]) -> list[float]:
    boxes = _occupied(graph)
    width, height = QUALITY_SIZE
    ys = [float((n.get("pos") or [0, 0])[1]) for n in graph.get("nodes") or []]
    xs = [float((n.get("pos") or [0, 0])[0]) for n in graph.get("nodes") or []]
    min_y = min(ys) if ys else 80.0
    min_x = min(xs) if xs else 40.0
    max_x = max(xs) if xs else 40.0
    candidates: list[tuple[float, float]] = [
        (40.0, -120.0),
        (40.0, min_y - 140.0),
        (min_x, min_y - 140.0),
        (-360.0, min_y),
        (max_x + 380.0, min_y),
        (min_x - 360.0, -120.0),
    ]
    y_cursor = min_y - 400.0
    while y_cursor <= min_y - 80.0:
        x_cursor = min_x - 400.0
        while x_cursor <= min_x + 80.0:
            candidates.append((x_cursor, y_cursor))
            x_cursor += 40.0
        y_cursor += 40.0
    for x, y in candidates:
        probe = _padded(x, y, width, height)
        if any(_hit(probe, box) for box in boxes):
            continue
        return [x, y]
    return [min_x - 400.0, min_y - 200.0]


def _next_node_id(graph: dict[str, Any]) -> int:
    live = [int(node["id"]) for node in graph.get("nodes") or []]
    last = int(graph.get("last_node_id") or 0)
    current = max(live + [last] + [0])
    return current + 1


def _quality_node(node_id: int, pos: list[float]) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": QUALITY_TYPE,
        "pos": pos,
        "size": [QUALITY_SIZE[0], QUALITY_SIZE[1]],
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {
                "name": "quality",
                "type": "STRING",
                "links": None,
                "slot_index": 0,
            }
        ],
        "properties": {"Node name for S&R": QUALITY_TYPE},
        "widgets_values": [QUALITY_DEFAULT],
        "title": QUALITY_TITLE,
    }


def _prepend_linear(graph: dict[str, Any], node_id: int) -> None:
    extra = graph.get("extra")
    if not isinstance(extra, dict):
        return
    linear = extra.get("linearData")
    if not isinstance(linear, dict):
        return
    inputs = list(linear.get("inputs") or [])
    kept: list[Any] = []
    for entry in inputs:
        if (
            isinstance(entry, (list, tuple))
            and len(entry) >= 2
            and entry[1] == QUALITY_WIDGET
        ):
            continue
        kept.append(entry)
    kept.insert(0, [int(node_id), QUALITY_WIDGET, dict(QUALITY_LABEL)])
    linear["inputs"] = kept


def find_quality_node(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the EZQuality node when present.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node dict or None.
    """
    hits = [n for n in graph.get("nodes") or [] if n.get("type") == QUALITY_TYPE]
    if not hits:
        return None
    return hits[0]


def ensure_quality_node(graph: dict[str, Any]) -> dict[str, Any]:
    """Add EZQuality when missing and stamp extra.lab_quality + linearData.

    Idempotent. Does not move an existing Quality node. Does not apply
    Draft/High overlays (shipped JSON stays Lab).

    Args:
        graph: Serialized Comfy graph (mutated).

    Returns:
        The same graph dict.
    """
    extra = graph.setdefault("extra", {})
    extra["lab_quality"] = {"default": QUALITY_DEFAULT}
    existing = find_quality_node(graph)
    if existing is None:
        node_id = _next_node_id(graph)
        pos = _place(graph)
        graph.setdefault("nodes", []).append(_quality_node(node_id, pos))
        graph["last_node_id"] = node_id
        existing = find_quality_node(graph)
    if existing is not None:
        _prepend_linear(graph, int(existing["id"]))
    return graph


def stamp_all_quality(root: Path | None = None) -> int:
    """Write EZQuality onto every lab JSON under workflows/_lab.

    Args:
        root: Optional workflows root (contains ``_lab``).

    Returns:
        Number of files written.
    """
    written = 0
    for path in lab_graph_paths(root):
        graph = json.loads(path.read_text(encoding="utf-8"))
        ensure_quality_node(graph)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        written += 1
    return written


if __name__ == "__main__":
    count = stamp_all_quality()
    print(f"stamped EZQuality on {count} graphs")
