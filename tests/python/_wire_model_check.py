"""Stamp EZModelCheck onto shipped lab graphs.

Not collected by pytest (leading underscore). Builders and tests import
``ensure_model_check_node``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_layout import NODE_GAP, VUE_HEIGHT_EXTRA, estimated_node_size, node_pos
from _lab_paths import lab_graph_paths
from _wire_quality import ensure_quality_node, find_quality_node

CHECK_TYPE = "EZModelCheck"
CHECK_TITLE = "Check models"
CHECK_WIDGET = "status"
CHECK_DEFAULT = "Click Check models. Queue does not run this node."
CHECK_SIZE = (320.0, 140.0)
CHECK_PAD = NODE_GAP / 2.0


def _node_rect(node: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y = node_pos(node)
    width, height = estimated_node_size(node)
    return x, y, width, height


def _padded(
    x: float, y: float, width: float, height: float
) -> tuple[float, float, float, float]:
    return (
        x - CHECK_PAD,
        y - CHECK_PAD,
        x + width + CHECK_PAD,
        y + height + CHECK_PAD,
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
        if node.get("type") == CHECK_TYPE:
            continue
        x, y, width, height = _node_rect(node)
        boxes.append(_padded(x, y, width, height))
    return boxes


def _place(graph: dict[str, Any]) -> list[float]:
    boxes = _occupied(graph)
    width, height = CHECK_SIZE[0], CHECK_SIZE[1] + VUE_HEIGHT_EXTRA
    quality = find_quality_node(graph)
    candidates: list[tuple[float, float]] = []
    if quality is not None:
        qx, qy = node_pos(quality)
        qw, qh = estimated_node_size(quality)
        extra = max(0.0, height - qh)
        candidates.append((qx, qy - height - NODE_GAP))
        candidates.append((qx + qw + NODE_GAP, qy - extra))
        candidates.append((qx - width - NODE_GAP, qy - extra))
        candidates.append((qx + qw + NODE_GAP, qy - height - NODE_GAP))
    ys = [node_pos(n)[1] for n in graph.get("nodes") or []]
    xs = [node_pos(n)[0] for n in graph.get("nodes") or []]
    min_y = min(ys) if ys else 80.0
    min_x = min(xs) if xs else 40.0
    max_x = max(xs) if xs else 40.0
    candidates.extend(
        [
            (40.0, -280.0),
            (380.0, -120.0),
            (40.0, min_y - 180.0),
            (min_x, min_y - 180.0),
            (-360.0, min_y),
            (max_x + 380.0, min_y),
            (min_x - 360.0, -120.0),
        ]
    )
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
    return [min_x - 400.0, min_y - 280.0]


def _next_node_id(graph: dict[str, Any]) -> int:
    live = [int(node["id"]) for node in graph.get("nodes") or []]
    last = int(graph.get("last_node_id") or 0)
    current = max(live + [last] + [0])
    return current + 1


def _check_node(node_id: int, pos: list[float]) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": CHECK_TYPE,
        "pos": pos,
        "size": [CHECK_SIZE[0], CHECK_SIZE[1]],
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "properties": {"Node name for S&R": CHECK_TYPE},
        "widgets_values": [CHECK_DEFAULT],
        "title": CHECK_TITLE,
    }


def find_model_check_node(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the EZModelCheck node when present.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node dict or None.
    """
    hits = [n for n in graph.get("nodes") or [] if n.get("type") == CHECK_TYPE]
    if not hits:
        return None
    return hits[0]


def ensure_model_check_node(
    graph: dict[str, Any], *, move: bool = False
) -> dict[str, Any]:
    """Add EZModelCheck when missing. Does not add linearData widgets.

    Idempotent. Does not move an existing Check models node unless ``move``.
    Quality is stamped first so placement can sit above or beside it.

    Args:
        graph: Serialized Comfy graph (mutated).
        move: Recompute ``pos`` on an existing node (restamp).

    Returns:
        The same graph dict.
    """
    ensure_quality_node(graph)
    existing = find_model_check_node(graph)
    if existing is not None:
        if move:
            existing["pos"] = _place(graph)
            existing["size"] = [CHECK_SIZE[0], CHECK_SIZE[1]]
        return graph
    node_id = _next_node_id(graph)
    pos = _place(graph)
    graph.setdefault("nodes", []).append(_check_node(node_id, pos))
    graph["last_node_id"] = node_id
    return graph


def stamp_all_model_check(root: Path | None = None) -> int:
    """Write EZModelCheck onto every lab JSON under workflows/_lab.

    Args:
        root: Optional workflows root (contains ``_lab``).

    Returns:
        Number of files written.
    """
    written = 0
    for path in lab_graph_paths(root):
        graph = json.loads(path.read_text(encoding="utf-8"))
        ensure_model_check_node(graph, move=True)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        written += 1
    return written


if __name__ == "__main__":
    count = stamp_all_model_check()
    print(f"stamped EZModelCheck on {count} graphs")
