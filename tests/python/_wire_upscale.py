"""Insert EZImageUpscale on the IMAGE edge into every SaveImage.

Not collected by pytest. Builders and the lab patcher import this.
"""

from __future__ import annotations

from typing import Any

from _lab_layout import node_pos
from _lab_paths import lab_rel_of
from _wire_format import (
    _append_link,
    _link_out,
    _next_node_id,
    _nodes_of,
    _push_output_link,
)

UPSCALE_TYPE = "EZImageUpscale"
SAVE_TYPE = "SaveImage"
DEFAULT_UPSCALE = "none"

# Produce stills + DCC still plates. Skip audio albums, film acts, VHS.
UPSCALE_PREFIXES = (
    "stills/",
    "creator/stills/",
)
UPSCALE_RELS = frozenset(
    {
        "dcc/clay-hero",
        "dcc/clay-plates",
        "dcc/canny-hero",
        "dcc/guide-still",
    }
)


def upscale_in_scope(lab_rel: str) -> bool:
    """True when this graph should gain EZImageUpscale on SaveImage.

    Args:
        lab_rel: ``extra.lab_rel`` id.

    Returns:
        Whether to insert upscale nodes.
    """
    rel = str(lab_rel or "").strip()
    if rel in UPSCALE_RELS:
        return True
    return any(rel.startswith(prefix) for prefix in UPSCALE_PREFIXES)


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    """Index links by id.

    Args:
        graph: Serialized graph.

    Returns:
        link id → link row.
    """
    return {int(row[0]): row for row in graph.get("links") or []}


def _incoming_image(graph: dict[str, Any], save: dict[str, Any]) -> tuple[int, int] | None:
    """Return (origin_id, origin_slot) for SaveImage.images.

    Args:
        graph: Serialized graph.
        save: SaveImage node.

    Returns:
        Origin pair, or None when unwired.
    """
    links = _link_map(graph)
    for item in save.get("inputs") or []:
        if item.get("name") != "images":
            continue
        lid = item.get("link")
        if lid is None:
            return None
        row = links.get(int(lid))
        if not row:
            return None
        return int(row[1]), int(row[2])
    return None


def _unlink(graph: dict[str, Any], link_id: int) -> None:
    """Drop one link id from graph.links and node sockets.

    Args:
        graph: Serialized graph (mutated).
        link_id: Link to remove.
    """
    lid = int(link_id)
    graph["links"] = [
        row for row in graph.get("links") or [] if int(row[0]) != lid
    ]
    for node in graph.get("nodes") or []:
        for item in node.get("inputs") or []:
            if item.get("link") is not None and int(item["link"]) == lid:
                item["link"] = None
        for out in node.get("outputs") or []:
            existing = list(out.get("links") or [])
            out["links"] = [x for x in existing if int(x) != lid]


def _make_upscale(nid: int, pos: list[float], linked_mode: bool) -> dict[str, Any]:
    """Build an EZImageUpscale node dict.

    Args:
        nid: Node id.
        pos: Canvas position.
        linked_mode: True when upscale combo is a linked input.

    Returns:
        Node payload.
    """
    inputs: list[dict[str, Any]] = [
        {"name": "image", "type": "IMAGE", "link": None},
    ]
    if linked_mode:
        inputs.append(
            {
                "name": "upscale",
                "type": "STRING",
                "link": None,
                "widget": {"name": "upscale"},
            }
        )
    return {
        "id": nid,
        "type": UPSCALE_TYPE,
        "pos": pos,
        "size": [280, 80],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": inputs,
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "upscale", "type": "STRING", "links": [], "slot_index": 1},
        ],
        "properties": {"Node name for S&R": UPSCALE_TYPE},
        "widgets_values": [DEFAULT_UPSCALE],
        "title": "Upscale still",
    }


def wire_upscale(graph: dict[str, Any], lab_rel: str = "") -> bool:
    """Insert EZImageUpscale before each SaveImage when in scope.

    The first node owns the combo. Extra SaveImage paths take ``upscale``
    as a linked widget so App Mode shows one dropdown.

    Args:
        graph: Serialized lab graph (mutated).
        lab_rel: Optional rel override.

    Returns:
        True when at least one node was inserted.
    """
    extra = graph.get("extra") or {}
    rel = lab_rel or str(extra.get("lab_rel") or graph.get("id") or "")
    if not upscale_in_scope(rel):
        return False
    if _nodes_of(graph, UPSCALE_TYPE):
        return False
    saves = _nodes_of(graph, SAVE_TYPE)
    if not saves:
        return False
    master: dict[str, Any] | None = None
    inserted = False
    for index, save in enumerate(saves):
        origin = _incoming_image(graph, save)
        if origin is None:
            continue
        src_id, src_slot = origin
        save_in = None
        for item in save.get("inputs") or []:
            if item.get("name") == "images" and item.get("link") is not None:
                save_in = item
                break
        if save_in is None:
            continue
        old_link = int(save_in["link"])
        _unlink(graph, old_link)
        nid = _next_node_id(graph)
        x, y = node_pos(save)
        pos = [x - 40.0, y + 140.0]
        node = _make_upscale(nid, pos, linked_mode=master is not None)
        graph.setdefault("nodes", []).append(node)
        img_link = _append_link(graph, src_id, src_slot, nid, 0, "IMAGE")
        node["inputs"][0]["link"] = img_link
        src_node = next(
            item for item in graph["nodes"] if int(item["id"]) == src_id
        )
        _push_output_link(src_node, src_slot, img_link)
        dst_slot = 0
        for slot, item in enumerate(save.get("inputs") or []):
            if item.get("name") == "images":
                dst_slot = slot
                break
        out_link = _append_link(
            graph, nid, 0, int(save["id"]), dst_slot, "IMAGE"
        )
        save_in["link"] = out_link
        _push_output_link(node, 0, out_link)
        if master is None:
            master = node
        else:
            _link_out(graph, master, 1, node, "upscale", "STRING", widget=True)
        inserted = True
        del index
    return inserted
