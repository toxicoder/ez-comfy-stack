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
        link id -> link row.
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


def _node_by_id(graph: dict[str, Any], node_id: int) -> dict[str, Any] | None:
    """Return the node with ``node_id``.

    Args:
        graph: Serialized graph.
        node_id: Node id.

    Returns:
        Node dict, or None when missing.
    """
    for node in graph.get("nodes") or []:
        if int(node.get("id", -1)) == int(node_id):
            return node
    return None


def _image_output(node: dict[str, Any]) -> dict[str, Any] | None:
    """Return the IMAGE output socket.

    Args:
        node: EZImageUpscale node.

    Returns:
        Output dict, or None.
    """
    outputs = list(node.get("outputs") or [])
    for out in outputs:
        if str(out.get("name") or "") == "image":
            return out
    if outputs:
        return outputs[0]
    return None


def _image_input(node: dict[str, Any]) -> dict[str, Any]:
    """Return the image input, creating it when a reused node lacks one.

    Args:
        node: EZImageUpscale node (mutated when the socket is missing).

    Returns:
        Image input dict.
    """
    inputs = list(node.get("inputs") or [])
    for item in inputs:
        if item.get("name") == "image":
            node["inputs"] = inputs
            return item
    created = {"name": "image", "type": "IMAGE", "link": None}
    inputs.insert(0, created)
    node["inputs"] = inputs
    return created


def _upscale_mode_linked(node: dict[str, Any]) -> bool:
    """True when the upscale combo is driven by another node.

    Args:
        node: EZImageUpscale node.

    Returns:
        Whether the combo is a linked widget.
    """
    for item in node.get("inputs") or []:
        if item.get("name") == "upscale" and item.get("link") is not None:
            return True
    return False


def _fed_by_upscale(graph: dict[str, Any], save: dict[str, Any]) -> bool:
    """True when SaveImage.images comes from EZImageUpscale.

    Args:
        graph: Serialized graph.
        save: SaveImage node.

    Returns:
        Whether the save already receives the upscaled still.
    """
    origin = _incoming_image(graph, save)
    if origin is None:
        return False
    src = _node_by_id(graph, origin[0])
    return bool(src and src.get("type") == UPSCALE_TYPE)


def _orphan_upscales(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Upscale nodes whose image output has no links.

    Args:
        graph: Serialized graph.

    Returns:
        Orphans in graph order.
    """
    orphans: list[dict[str, Any]] = []
    for node in _nodes_of(graph, UPSCALE_TYPE):
        out = _image_output(node)
        if not list((out or {}).get("links") or []):
            orphans.append(node)
    return orphans


def _connect_upscale(
    graph: dict[str, Any],
    node: dict[str, Any],
    src_id: int,
    src_slot: int,
    save: dict[str, Any],
    save_in: dict[str, Any],
    dst_slot: int,
) -> None:
    """Wire ``src`` into an upscale node and that node into SaveImage.

    Drops any previous image input on ``node``. The SaveImage link must
    already be unlinked.

    Args:
        graph: Serialized graph (mutated).
        node: EZImageUpscale node.
        src_id: Node that currently owns the still.
        src_slot: Output slot on that node.
        save: SaveImage node.
        save_in: SaveImage images input.
        dst_slot: SaveImage input index.
    """
    img_in = _image_input(node)
    if img_in.get("link") is not None:
        _unlink(graph, int(img_in["link"]))
    nid = int(node["id"])
    img_link = _append_link(graph, src_id, src_slot, nid, 0, "IMAGE")
    img_in["link"] = img_link
    src_node = _node_by_id(graph, src_id)
    if src_node is not None:
        _push_output_link(src_node, src_slot, img_link)
    out_link = _append_link(
        graph, nid, 0, int(save["id"]), dst_slot, "IMAGE"
    )
    save_in["link"] = out_link
    _push_output_link(node, 0, out_link)


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

    The first unlinked combo owns the App dropdown. Extra SaveImage paths
    take ``upscale`` as a linked widget. An upscale node that does not feed
    a save is reused instead of left orphaned (Match -> Save with a dead
    decode -> upscale branch).

    Args:
        graph: Serialized lab graph (mutated).
        lab_rel: Optional rel override.

    Returns:
        True when at least one save was wired through upscale.
    """
    extra = graph.get("extra") or {}
    rel = lab_rel or str(extra.get("lab_rel") or graph.get("id") or "")
    if not upscale_in_scope(rel):
        return False
    saves = _nodes_of(graph, SAVE_TYPE)
    if not saves:
        return False
    pending = [
        save
        for save in saves
        if _incoming_image(graph, save) is not None and not _fed_by_upscale(graph, save)
    ]
    if not pending:
        return False
    orphans = _orphan_upscales(graph)
    masters = [
        node
        for node in _nodes_of(graph, UPSCALE_TYPE)
        if not _upscale_mode_linked(node)
    ]
    master: dict[str, Any] | None = masters[0] if masters else None
    inserted = False
    for save in pending:
        origin = _incoming_image(graph, save)
        if origin is None:
            continue
        src_id, src_slot = origin
        save_in = None
        dst_slot = 0
        for slot, item in enumerate(save.get("inputs") or []):
            if item.get("name") == "images" and item.get("link") is not None:
                save_in = item
                dst_slot = slot
                break
        if save_in is None:
            continue
        if orphans:
            node = orphans.pop(0)
        else:
            nid = _next_node_id(graph)
            x, y = node_pos(save)
            node = _make_upscale(
                nid, [x - 40.0, y + 140.0], linked_mode=master is not None
            )
            graph.setdefault("nodes", []).append(node)
        if save_in.get("link") is not None:
            _unlink(graph, int(save_in["link"]))
        _connect_upscale(
            graph, node, src_id, src_slot, save, save_in, dst_slot
        )
        if master is None:
            master = node
        elif node is not master and not _upscale_mode_linked(node):
            _link_out(graph, master, 1, node, "upscale", "STRING", widget=True)
        inserted = True
    return inserted
