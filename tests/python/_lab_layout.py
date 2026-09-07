"""Shared ComfyUI group geometry for lab workflow builders.

Not imported by pytest collection (leading underscore). Builders import it.

ComfyUI draws the group title in the top LiteGraph.NODE_TITLE_HEIGHT (30px) of
``group.bounding``. Native ``LGraphGroup.resizeTo`` uses that plus 10px pad.
Lab graphs add a small extra gap so the first node is not flush with the header.
"""

from __future__ import annotations

from typing import Any

# LiteGraph.NODE_TITLE_HEIGHT (30) + native resizeTo pad (10) + 16px gap.
GROUP_TITLE_INSET = 56
GROUP_FONT_SIZE = 24
# First node row in 4-column lab graphs; group top sits GROUP_TITLE_INSET above it.
LAB_NODE_Y0 = 80
LAB_GROUP_Y0 = LAB_NODE_Y0 - GROUP_TITLE_INSET

# Touching group edges is OK; positive overlap area above this is a defect.
_GROUP_OVERLAP_EPS = 1.0


def node_size(node: dict[str, Any]) -> tuple[float, float]:
    """Return (width, height) for a serialized Comfy node."""
    size = node.get("size", [200, 100])
    if isinstance(size, dict):
        return float(size.get("0", 200)), float(size.get("1", 100))
    return float(size[0]), float(size[1])


def node_center(node: dict[str, Any]) -> tuple[float, float]:
    """Return the centre of a node's serialized rect (Comfy membership)."""
    x, y = float(node["pos"][0]), float(node["pos"][1])
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
        min_y = min(float(node["pos"][1]) for node in members)
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
        min_y = min(float(node["pos"][1]) for node in members)
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
