"""Stamp EZQuality onto shipped lab graphs.

Not collected by pytest (leading underscore). Builders and tests import
``ensure_quality_node``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_layout import (
    LAB_NODE_Y0,
    LAB_X0,
    NODE_GAP,
    estimated_node_size,
    node_pos,
    operator_note,
)
from _lab_paths import lab_graph_paths
from ez_quality.presets import (
    OVERLAY_NODE_TYPES,
    QUALITY_STANDARD,
    infer_occupancy,
    is_trellis_guidance_free_stage,
    normalize_quality,
    tiers_for_family,
)

QUALITY_TYPE = "EZQuality"
QUALITY_TITLE = "Detail"
QUALITY_WIDGET = "quality"
QUALITY_DEFAULT = QUALITY_STANDARD
QUALITY_SIZE = (320.0, 82.0)
QUALITY_PAD = 20.0
QUALITY_LABEL = {
    "label": "Detail",
    "description": (
        "draft is a quick look. standard is what this App ships tuned for. "
        "final is the best this App's own stack can do. A rung never changes "
        "size and never leaves this App's model stack. The caption names the "
        "steps, CFG, weights, and license Queue actually sends."
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
    note = operator_note(graph)
    check = next(
        (node for node in graph.get("nodes") or [] if node.get("type") == "EZModelCheck"),
        None,
    )
    candidates: list[tuple[float, float]] = []
    if note is not None:
        nx, ny = node_pos(note)
        nw, _nh = estimated_node_size(note)
        x = nx + nw + NODE_GAP
        if check is not None:
            cx, _cy = node_pos(check)
            cw, _ch = estimated_node_size(check)
            x = cx + cw + NODE_GAP
        candidates.append((x, ny))
    else:
        candidates.append((float(LAB_X0), float(LAB_NODE_Y0)))
        if check is not None:
            cx, cy = node_pos(check)
            cw, _ch = estimated_node_size(check)
            candidates.insert(0, (cx + cw + NODE_GAP, cy))
    ys = [node_pos(node)[1] for node in graph.get("nodes") or []]
    xs = [node_pos(node)[0] for node in graph.get("nodes") or []]
    min_y = min(ys) if ys else float(LAB_NODE_Y0)
    min_x = min(xs) if xs else float(LAB_X0)
    max_x = max(xs) if xs else float(LAB_X0)
    candidates.extend(
        [
            (float(LAB_X0), min_y + 40.0),
            (max_x + 380.0, min_y),
            (min_x, min_y + 180.0),
        ]
    )
    floor_y = node_pos(note)[1] if note is not None else None
    for x, y in candidates:
        if floor_y is not None and y + 1e-6 < floor_y:
            continue
        probe = _padded(x, y, width, height)
        if any(_hit(probe, box) for box in boxes):
            continue
        return [x, y]
    fallback_y = floor_y if floor_y is not None else min_y
    return [min_x + 380.0, fallback_y]


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


def _quality_insert_index(inputs: list[Any]) -> int:
    """Return the index after any leading LoadImage App widgets.

    Required still pickers stay first so Queue cannot hide a missing file.
    The Detail row follows those pickers (or index 0 when the graph has none).

    Args:
        inputs: ``linearData.inputs`` rows.

    Returns:
        Insertion index for the Detail widget.
    """
    idx = 0
    for entry in inputs:
        if (
            isinstance(entry, (list, tuple))
            and len(entry) >= 2
            and entry[1] == "image"
        ):
            idx += 1
            continue
        break
    return idx


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
    kept.insert(
        _quality_insert_index(kept),
        [int(node_id), QUALITY_WIDGET, dict(QUALITY_LABEL)],
    )
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


def family_honors_tiers(graph: dict[str, Any]) -> bool:
    """True when some rung would actually change this graph.

    Two things have to hold. The family inferred from the graph's loaders has
    a rung ladder of its own, and the graph carries at least one node type the
    overlay can write. An audio graph with no KSampler and no loader passes the
    first test and fails the second, and every rung on it queues unchanged.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        False when every rung would be a no-op, so the row belongs nowhere.
    """
    if not tiers_for_family(infer_occupancy(graph)):
        return False
    family = infer_occupancy(graph)
    return any(
        node.get("type") in OVERLAY_NODE_TYPES
        and not is_trellis_guidance_free_stage(node, family)
        for node in (graph.get("nodes") or [])
    )


def strip_quality_node(graph: dict[str, Any]) -> bool:
    """Remove every EZQuality node, its App widget row, and its default stamp.

    A selector that cannot change anything is worse than none: it offers levels
    that queue unchanged and read as applied. Graphs whose family owns no
    overlay field get the node taken back out.

    Args:
        graph: Serialized Comfy graph (mutated).

    Returns:
        True when the graph held a Detail node to remove.
    """
    nodes = graph.get("nodes") or []
    kept = [node for node in nodes if node.get("type") != QUALITY_TYPE]
    if len(kept) == len(nodes):
        return False
    graph["nodes"] = kept
    extra = graph.get("extra")
    if isinstance(extra, dict):
        extra.pop("lab_quality", None)
        linear = extra.get("linearData")
        if isinstance(linear, dict):
            quality_ids = {int(n["id"]) for n in nodes if n.get("type") == QUALITY_TYPE}
            linear["inputs"] = [
                entry
                for entry in (linear.get("inputs") or [])
                if not (
                    isinstance(entry, (list, tuple))
                    and entry
                    and (
                        entry[0] in quality_ids
                        or (len(entry) >= 2 and entry[1] == QUALITY_WIDGET)
                    )
                )
            ]
    return True


def _relabel_quality_node(node: dict[str, Any]) -> None:
    """Bring an existing Detail node onto the current row title and rung.

    Builders stamp graphs that predate the ladder, so a shipped JSON can still
    carry the retired row title and a retired tier id. The recorded value goes
    through ``normalize_quality`` so an accepted legacy tier lands on its rung
    and a value nothing recognizes falls back to the default rung.

    Args:
        node: The EZQuality node dict (mutated in place).

    Returns:
        The rung the node now records.
    """
    node["title"] = QUALITY_TITLE
    widgets = node.get("widgets_values")
    recorded = widgets[0] if isinstance(widgets, list) and widgets else ""
    rung = normalize_quality(str(recorded)) if recorded else QUALITY_DEFAULT
    node["widgets_values"] = [rung]
    named = node.get("widgets_values_named")
    if isinstance(named, dict):
        named[QUALITY_WIDGET] = rung
    return rung


def ensure_quality_node(graph: dict[str, Any]) -> dict[str, Any]:
    """Add EZQuality when missing and stamp extra.lab_quality + linearData.

    Idempotent. Does not move an existing Detail node, but does relabel it and
    pull a retired tier id onto its rung, so re-stamping migrates shipped JSON
    onto the ladder. No rung is ever *applied* here: standard writes nothing,
    and a graph authored at another rung keeps that rung. ``linearData`` keeps
    required still pickers first, then Detail. ``extra.lab_quality`` always
    agrees with the node's own recorded rung.

    A graph whose family has no rung to write gets the node removed instead:
    see ``strip_quality_node``.

    Args:
        graph: Serialized Comfy graph (mutated).

    Returns:
        The same graph dict.
    """
    if not family_honors_tiers(graph):
        strip_quality_node(graph)
        return graph
    extra = graph.setdefault("extra", {})
    existing = find_quality_node(graph)
    if existing is None:
        node_id = _next_node_id(graph)
        pos = _place(graph)
        graph.setdefault("nodes", []).append(_quality_node(node_id, pos))
        graph["last_node_id"] = node_id
        existing = find_quality_node(graph)
    rung = _relabel_quality_node(existing) if existing is not None else QUALITY_DEFAULT
    extra["lab_quality"] = {"default": rung}
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
