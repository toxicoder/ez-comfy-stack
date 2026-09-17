"""Shared ComfyUI group geometry and node spacing for lab workflow builders.

Not imported by pytest collection (leading underscore). Builders import it.

ComfyUI draws the group title in the top LiteGraph.NODE_TITLE_HEIGHT (30px) of
``group.bounding``. Native ``LGraphGroup.resizeTo`` uses that plus 10px pad.
Lab graphs add a small extra gap so the first node is not flush with the header.

Node spacing uses an estimated Nodes 2.0 (Vue) AABB so serialized LiteGraph
``size`` values do not pack widgets on top of each other. Estimates are never
written back into ``node.size``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# LiteGraph.NODE_TITLE_HEIGHT (30) + native resizeTo pad (10) + 16px gap.
GROUP_TITLE_INSET = 56
GROUP_FONT_SIZE = 24
# First node row in 4-column lab graphs; group top sits GROUP_TITLE_INSET above it.
LAB_NODE_Y0 = 80
LAB_GROUP_Y0 = LAB_NODE_Y0 - GROUP_TITLE_INSET

# Clear pixels between estimated node AABBs (Nodes 2.0 Vue widgets run taller
# than LiteGraph computeSize). pad=NODE_GAP/2 is the overlap-test expansion.
NODE_GAP = 48.0
ROW_Y_TOLERANCE = 40.0
COL_X_TOLERANCE = 80.0
VUE_HEIGHT_EXTRA = 24.0
GROUP_BOX_PAD = 20.0
QUALITY_TYPE = "EZQuality"

# Touching group edges is OK; positive overlap area above this is a defect.
_GROUP_OVERLAP_EPS = 1.0
_MOVE_EPS = 0.5

# Minimum serialized-or-estimated height for widgets that Vue draws taller.
_TYPE_HEIGHT_FLOOR: dict[str, float] = {
    "CLIPTextEncode": 160.0,
    "KSampler": 262.0,
    "SaveImage": 270.0,
    "LoadImage": 314.0,
    "EZQuality": 82.0,
    "EZImageFormat": 220.0,
    "EZRapLyrics": 420.0,
    "EZPodcastScript": 420.0,
    "EZSamplePrompt": 420.0,
    "EZCreativeResearch": 420.0,
}


def node_pos(node: dict[str, Any]) -> tuple[float, float]:
    """Return (x, y) for a serialized Comfy node."""
    pos = node.get("pos") or [0, 0]
    if isinstance(pos, dict):
        return float(pos.get("0", 0)), float(pos.get("1", 0))
    return float(pos[0]), float(pos[1])


def _coord(value: float) -> int | float:
    """Round canvas coords; keep ints when the value is whole pixels."""
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return int(rounded)
    return round(value, 1)


def set_node_pos(node: dict[str, Any], x: float, y: float) -> None:
    """Write ``pos`` without switching list/dict shape."""
    pos = node.get("pos")
    cx, cy = _coord(x), _coord(y)
    if isinstance(pos, dict):
        pos["0"] = cx
        pos["1"] = cy
        return
    node["pos"] = [cx, cy]


def node_size(node: dict[str, Any]) -> tuple[float, float]:
    """Return (width, height) for a serialized Comfy node."""
    size = node.get("size", [200, 100])
    if isinstance(size, dict):
        return float(size.get("0", 200)), float(size.get("1", 100))
    return float(size[0]), float(size[1])


def _height_floor(ntype: str) -> float:
    if ntype in _TYPE_HEIGHT_FLOOR:
        return _TYPE_HEIGHT_FLOOR[ntype]
    if ntype.endswith("PromptEnhance"):
        return 420.0
    if ntype.startswith("SaveAudio"):
        return 270.0
    return 0.0


def estimated_node_size(node: dict[str, Any]) -> tuple[float, float]:
    """Return collision size: max(serialized, type floor) plus Vue chrome.

    Never smaller than the stored LiteGraph size. Not written back to JSON.
    """
    width, height = node_size(node)
    ntype = str(node.get("type") or "")
    height = max(height, _height_floor(ntype)) + VUE_HEIGHT_EXTRA
    return width, height


def node_center(node: dict[str, Any]) -> tuple[float, float]:
    """Return the centre of a node's serialized rect (Comfy membership)."""
    x, y = node_pos(node)
    width, height = node_size(node)
    return x + width / 2.0, y + height / 2.0


def contains_centre(box: list[float], cx: float, cy: float) -> bool:
    """True if (cx, cy) lies inside bounding ``[x, y, w, h]`` (inclusive)."""
    x, y, width, height = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
    return x <= cx <= x + width and y <= cy <= y + height


def group_members(graph: dict[str, Any], group: dict[str, Any]) -> list[dict[str, Any]]:
    """Nodes whose centre sits inside the group rect (Comfy ``containsCentre``)."""
    box = group["bounding"]
    return [node for node in graph.get("nodes") or [] if contains_centre(box, *node_center(node))]


def group(
    gid: int,
    title: str,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
) -> dict[str, Any]:
    """Serialize a LiteGraph group with the lab title-bar contract."""
    return {
        "id": gid,
        "title": title,
        "bounding": [x, y, w, h],
        "color": color,
        "font_size": GROUP_FONT_SIZE,
        "flags": {},
    }


def _h_overlap(a: list[float], b: list[float]) -> bool:
    ax, _ay, aw, _ah = a
    bx, _by, bw, _bh = b
    return ax < bx + bw and ax + aw > bx


def _overlap_area(a: list[float], b: list[float]) -> float:
    ax, ay, aw, ah = (float(v) for v in a)
    bx, by, bw, bh = (float(v) for v in b)
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy


def title_inset_hits(graph: dict[str, Any], inset: float = GROUP_TITLE_INSET) -> list[str]:
    """Groups whose first member node sits under ``inset`` px from the top."""
    hits: list[str] = []
    for grp in graph.get("groups") or []:
        members = group_members(graph, grp)
        if not members:
            continue
        min_y = min(node_pos(node)[1] for node in members)
        top = float(grp["bounding"][1])
        gap = min_y - top
        if gap + 1e-6 < inset:
            title = grp.get("title", "?")
            hits.append(f"{title}: inset {gap:.1f}px < {inset}")
    return hits


def group_overlap_hits(graph: dict[str, Any]) -> list[str]:
    """Pairs of groups whose rects overlap by more than a touching edge."""
    groups = list(graph.get("groups") or [])
    hits: list[str] = []
    for i, a in enumerate(groups):
        for b in groups[i + 1 :]:
            area = _overlap_area(a["bounding"], b["bounding"])
            if area > _GROUP_OVERLAP_EPS:
                hits.append(
                    f"{a.get('title', a.get('id'))} vs {b.get('title', b.get('id'))}: {area:.1f}px²"
                )
    return hits


def ensure_group_title_inset(graph: dict[str, Any], inset: float = GROUP_TITLE_INSET) -> None:
    """Shift each group up so member nodes clear the title bar.

    Keeps group height (bottom moves with top) so stacked neighbours keep their
    gap. Stops at another group's bottom (touching is OK). Does not move nodes;
    remaining shortfalls are builder layout bugs and fail ``title_inset_hits``.
    """
    groups = list(graph.get("groups") or [])
    if not groups:
        return
    # Top-most first so a lower group can rise up to a neighbour that already moved.
    ordered = sorted(groups, key=lambda grp: float(grp["bounding"][1]))
    for grp in ordered:
        members = group_members(graph, grp)
        if not members:
            continue
        box = grp["bounding"]
        min_y = min(node_pos(node)[1] for node in members)
        extra = inset - (min_y - float(box[1]))
        if extra <= 0:
            continue
        new_y = float(box[1]) - extra
        this_bottom = float(box[1]) + float(box[3])
        for other in groups:
            if other is grp:
                continue
            other_box = other["bounding"]
            if not _h_overlap(box, other_box):
                continue
            other_bottom = float(other_box[1]) + float(other_box[3])
            other_top = float(other_box[1])
            if other_top < this_bottom and other_bottom > new_y:
                new_y = max(new_y, other_bottom)
        applied = float(box[1]) - new_y
        if applied <= 0:
            continue
        box[1] = new_y


def _estimated_rect(node: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y = node_pos(node)
    width, height = estimated_node_size(node)
    return x, y, x + width, y + height


def _rects_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    pad: float = 0.0,
) -> bool:
    return (
        left[0] - pad < right[2] + pad
        and left[2] + pad > right[0] - pad
        and left[1] - pad < right[3] + pad
        and left[3] + pad > right[1] - pad
    )


def _h_overlap_rect(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return left[0] < right[2] and left[2] > right[0]


def node_overlap_hits(graph: dict[str, Any], pad: float | None = None) -> list[str]:
    """Pairs of nodes whose estimated Vue AABBs overlap (including ``pad``).

    Default ``pad`` is ``NODE_GAP / 2`` so a clean ``NODE_GAP`` edge gap passes
    and anything tighter is a defect.
    """
    expand = NODE_GAP / 2.0 if pad is None else pad
    nodes = list(graph.get("nodes") or [])
    boxes: list[tuple[object, object, tuple[float, float, float, float]]] = []
    for node in nodes:
        boxes.append((node.get("id"), node.get("type"), _estimated_rect(node)))
    hits: list[str] = []
    for i, left in enumerate(boxes):
        for right in boxes[i + 1 :]:
            if _rects_overlap(left[2], right[2], expand):
                hits.append(f"{left[0]}({left[1]}) vs {right[0]}({right[1]})")
    return hits


def assert_no_overlap(graph: dict[str, Any]) -> None:
    """Raise SystemExit when estimated node AABBs overlap."""
    hits = node_overlap_hits(graph)
    if hits:
        raise SystemExit(f"overlap {hits[0]}")
    group_hits = group_overlap_hits(graph)
    if group_hits:
        raise SystemExit(f"group overlap {group_hits[0]}")


def finalize_layout(graph: dict[str, Any]) -> None:
    """Space nodes, refit groups, then refuse remaining overlaps.

    Builders call this immediately before writing JSON.
    """
    ensure_node_spacing(graph)
    assert_no_overlap(graph)


def _same_column(left_x: float, right_x: float) -> bool:
    return abs(left_x - right_x) < COL_X_TOLERANCE


def _cluster_rows(nodes: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group nodes whose tops are close, unless they share a column."""
    ordered = sorted(nodes, key=lambda node: (node_pos(node)[1], node_pos(node)[0]))
    rows: list[list[dict[str, Any]]] = []
    for node in ordered:
        x, y = node_pos(node)
        placed = False
        for row in rows:
            anchor_y = min(node_pos(member)[1] for member in row)
            if abs(y - anchor_y) > ROW_Y_TOLERANCE:
                continue
            if any(_same_column(x, node_pos(member)[0]) for member in row):
                continue
            row.append(node)
            placed = True
            break
        if not placed:
            rows.append([node])
    return rows


def _spread_row_x(row: list[dict[str, Any]]) -> bool:
    """Push nodes right so estimated widths in this row do not overlap."""
    moved = False
    ordered = sorted(row, key=lambda node: node_pos(node)[0])
    prev_right = None
    for node in ordered:
        x, y = node_pos(node)
        width, _height = estimated_node_size(node)
        if prev_right is not None and x < prev_right + NODE_GAP:
            x = prev_right + NODE_GAP
            set_node_pos(node, x, y)
            moved = True
        prev_right = x + width
    return moved


def _place_rows(rows: list[list[dict[str, Any]]]) -> bool:
    """Push each row down as a unit so it clears already-placed estimated AABBs."""
    moved = False
    placed: list[tuple[float, float, float, float]] = []
    for row in rows:
        dy = 0.0
        for node in row:
            rect = _estimated_rect(node)
            for prev in placed:
                if not _h_overlap_rect(rect, prev):
                    continue
                need = prev[3] + NODE_GAP - rect[1]
                if need > dy:
                    dy = need
        if dy > _MOVE_EPS:
            for node in row:
                x, y = node_pos(node)
                set_node_pos(node, x, y + dy)
            moved = True
        for node in row:
            placed.append(_estimated_rect(node))
    return moved


def _clearance_moves(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> tuple[float, float]:
    """Return (dx, dy) to move ``right`` so estimated AABBs keep ``NODE_GAP``."""
    need_x = left[2] + NODE_GAP - right[0]
    need_y = left[3] + NODE_GAP - right[1]
    if need_x <= _MOVE_EPS and need_y <= _MOVE_EPS:
        return 0.0, 0.0
    if need_x <= _MOVE_EPS:
        return 0.0, max(0.0, need_y)
    if need_y <= _MOVE_EPS:
        return max(0.0, need_x), 0.0
    if need_x <= need_y:
        return need_x, 0.0
    return 0.0, need_y


def _resolve_collisions(nodes: list[dict[str, Any]]) -> bool:
    """Separate remaining padded-AABB hits with the smaller of right vs down."""
    moved = False
    for _ in range(48):
        cycle = False
        ordered = sorted(nodes, key=lambda node: (node_pos(node)[1], node_pos(node)[0]))
        for i, node in enumerate(ordered):
            rect = _estimated_rect(node)
            dx = 0.0
            dy = 0.0
            for prev in ordered[:i]:
                prev_rect = _estimated_rect(prev)
                if not _rects_overlap(prev_rect, rect, NODE_GAP / 2.0):
                    continue
                extra_x, extra_y = _clearance_moves(prev_rect, rect)
                dx = max(dx, extra_x)
                dy = max(dy, extra_y)
            if dx <= _MOVE_EPS and dy <= _MOVE_EPS:
                continue
            if dx > _MOVE_EPS and dy > _MOVE_EPS:
                if dx <= dy:
                    dy = 0.0
                else:
                    dx = 0.0
            x, y = node_pos(node)
            set_node_pos(node, x + dx, y + dy)
            cycle = True
            moved = True
        if not cycle:
            break
    return moved


def _snapshot_group_members(
    graph: dict[str, Any],
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    by_id = {int(node["id"]): node for node in graph.get("nodes") or []}
    snapped: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for grp in graph.get("groups") or []:
        members = group_members(graph, grp)
        live = [by_id[int(node["id"])] for node in members if int(node["id"]) in by_id]
        snapped.append((grp, live))
    return snapped


def _refit_group(grp: dict[str, Any], members: list[dict[str, Any]]) -> bool:
    if not members:
        return False
    xs: list[float] = []
    ys: list[float] = []
    rights: list[float] = []
    bottoms: list[float] = []
    for node in members:
        x, y = node_pos(node)
        width, height = estimated_node_size(node)
        xs.append(x)
        ys.append(y)
        rights.append(x + width)
        bottoms.append(y + height)
    new_x = min(xs) - GROUP_BOX_PAD
    new_y = min(ys) - GROUP_TITLE_INSET
    new_r = max(rights) + GROUP_BOX_PAD
    new_b = max(bottoms) + GROUP_BOX_PAD
    box = grp.setdefault("bounding", [new_x, new_y, new_r - new_x, new_b - new_y])
    new_box = [new_x, new_y, new_r - new_x, new_b - new_y]
    changed = False
    for i, value in enumerate(new_box):
        if abs(float(box[i]) - value) > _MOVE_EPS:
            changed = True
        box[i] = _coord(value)
    return changed


def _separate_overlapping_groups(
    membership: list[tuple[dict[str, Any], list[dict[str, Any]]]],
) -> bool:
    moved = False
    ordered = sorted(membership, key=lambda item: float(item[0]["bounding"][1]))
    for i, (lower_grp, lower_members) in enumerate(ordered):
        lower_box = lower_grp["bounding"]
        for upper_grp, _upper_members in ordered[:i]:
            upper_box = upper_grp["bounding"]
            if _overlap_area(upper_box, lower_box) <= _GROUP_OVERLAP_EPS:
                continue
            if not _h_overlap(upper_box, lower_box):
                continue
            upper_bottom = float(upper_box[1]) + float(upper_box[3])
            dy = upper_bottom - float(lower_box[1])
            if dy <= _MOVE_EPS:
                continue
            for node in lower_members:
                x, y = node_pos(node)
                set_node_pos(node, x, y + dy)
            moved = True
            _refit_group(lower_grp, lower_members)
    return moved


def _space_one_graph(graph: dict[str, Any]) -> bool:
    nodes = [node for node in graph.get("nodes") or [] if node.get("type") != QUALITY_TYPE]
    if not nodes:
        return False
    membership = _snapshot_group_members(graph)
    moved = False
    rows = _cluster_rows(nodes)
    for row in rows:
        if _spread_row_x(row):
            moved = True
    if _place_rows(rows):
        moved = True
    if _resolve_collisions(nodes):
        moved = True
    for grp, members in membership:
        if _refit_group(grp, members):
            moved = True
    ensure_group_title_inset(graph)
    if _separate_overlapping_groups(membership):
        moved = True
        for grp, members in membership:
            _refit_group(grp, members)
        ensure_group_title_inset(graph)
    return moved


def ensure_node_spacing(graph: dict[str, Any]) -> bool:
    """Push nodes down/right so estimated Vue AABBs keep ``NODE_GAP``.

    Preserves left-to-right row order. Does not rewrite ``size``. Recurses into
    ``definitions.subgraphs``. Idempotent once gaps are clean.

    Arguments:
        graph: Serialized Comfy graph (mutated).
    Returns:
        True when any node ``pos`` or group ``bounding`` changed.
    """
    moved = False
    for _ in range(8):
        cycle = _space_one_graph(graph)
        defs = graph.get("definitions")
        if isinstance(defs, dict):
            for sub in defs.get("subgraphs") or []:
                if isinstance(sub, dict) and sub.get("nodes"):
                    if _space_one_graph(sub):
                        cycle = True
        if not cycle:
            break
        moved = True
    else:
        moved = True
    if moved:
        graph["revision"] = int(graph.get("revision") or 0) + 1
    return moved


def relayout_lab_graphs(root: Path | None = None) -> int:
    """Run ``ensure_node_spacing`` on every lab JSON. Returns files written."""
    from _lab_paths import ROOT, lab_graph_paths

    written = 0
    for path in lab_graph_paths(root):
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            continue
        before = json.dumps(graph, sort_keys=True)
        ensure_node_spacing(graph)
        after = json.dumps(graph, sort_keys=True)
        if before == after:
            continue
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        written += 1
    blocks = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs"
    if blocks.is_dir():
        for path in sorted(blocks.glob("*.json")):
            graph = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(graph, dict):
                continue
            before = json.dumps(graph, sort_keys=True)
            ensure_node_spacing(graph)
            after = json.dumps(graph, sort_keys=True)
            if before == after:
                continue
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            written += 1
    return written


if __name__ == "__main__":
    count = relayout_lab_graphs()
    print(f"relayout wrote {count} graphs")
