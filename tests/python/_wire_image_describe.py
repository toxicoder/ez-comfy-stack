"""Insert EZImageDescribe into visual Enhance graphs that have one still.

Not collected by pytest. Builders and the lab patcher import this.
"""

from __future__ import annotations

from typing import Any

from _lab_layout import node_pos
from _wire_format import (
    _append_link,
    _link_out,
    _next_node_id,
    _nodes_of,
    _push_output_link,
)
from _wire_upscale import _unlink

START_CONSUMERS = frozenset(
    {
        "VAEEncode",
        "EZSnapImage",
        "EZKleinRefCanvas",
        "LTXVImgToVideo",
        "Wan22ImageToVideoLatent",
        "ImageScale",
    }
)
DESCRIBE_TYPE = "EZImageDescribe"
ENHANCE_TYPES = (
    "EZKleinPromptEnhance",
    "EZWanPromptEnhance",
    "EZLTXPromptEnhance",
    "EZZimagePromptEnhance",
    "EZLongCatPromptEnhance",
    "EZDreamXPromptEnhance",
)
SKIP_RELS = frozenset(
    {
        "inspire/prompt-forge",
        "inspire/cinema-rack",
        "inspire/audio-rack",
        "inspire/research-chat",
        "inspire/app-forge",
        "inspire/beat-sheet",
    }
)


def _lab_rel(graph: dict[str, Any]) -> str:
    """Return extra.lab_rel or graph id.

    Args:
        graph: Serialized graph.

    Returns:
        Lab-relative id.
    """
    extra = graph.get("extra") or {}
    rel = extra.get("lab_rel")
    if isinstance(rel, str) and rel.strip():
        return rel.strip()
    return str(graph.get("id") or "").strip()


def describe_in_scope(graph: dict[str, Any]) -> bool:
    """True when this graph should gain EZImageDescribe.

    One still source (LoadImage or EZOptionalImage) plus a visual Enhance.
    Multi-LoadImage tours stay skipped so Queue does not caption ten plates.

    Args:
        graph: Serialized graph.

    Returns:
        Whether to insert the node.
    """
    rel = _lab_rel(graph)
    if rel in SKIP_RELS or rel.startswith("audio/") or rel.startswith("films/"):
        return False
    if _nodes_of(graph, DESCRIBE_TYPE):
        return False
    enhance = None
    for ntype in ENHANCE_TYPES:
        hits = _nodes_of(graph, ntype)
        if hits:
            enhance = hits[0]
            break
    if enhance is None:
        return False
    return _preferred_still(graph) is not None


def _make_describe(nid: int, pos: list[float]) -> dict[str, Any]:
    """Build an EZImageDescribe node dict.

    Args:
        nid: Node id.
        pos: Canvas position.

    Returns:
        Node payload.
    """
    return {
        "id": nid,
        "type": DESCRIBE_TYPE,
        "pos": pos,
        "size": [280, 90],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [
            {
                "name": "enable",
                "type": "BOOLEAN",
                "link": None,
                "widget": {"name": "enable"},
            },
            {"name": "image", "type": "IMAGE", "link": None},
        ],
        "outputs": [
            {"name": "caption", "type": "STRING", "links": [], "slot_index": 0},
        ],
        "properties": {"Node name for S&R": DESCRIBE_TYPE},
        "widgets_values": [False],
        "title": "Describe image",
    }


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Index nodes by id.

    Args:
        graph: Serialized graph.

    Returns:
        id → node.
    """
    return {int(node["id"]): node for node in graph.get("nodes") or []}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    """Index links by id.

    Args:
        graph: Serialized graph.

    Returns:
        link id → row.
    """
    return {int(row[0]): row for row in graph.get("links") or []}


def _feeds_generation(graph: dict[str, Any], node: dict[str, Any]) -> bool:
    """True when this still is already on the denoise / ref path.

    Args:
        graph: Serialized graph.
        node: LoadImage or EZOptionalImage.

    Returns:
        Whether an output IMAGE hits a generation consumer (not describe).
    """
    by_id = _by_id(graph)
    links = _link_map(graph)
    for out in node.get("outputs") or []:
        if out.get("type") not in {"IMAGE", "*"}:
            continue
        for lid in out.get("links") or []:
            row = links.get(int(lid))
            if not row:
                continue
            dest = by_id.get(int(row[3]))
            if dest is None:
                continue
            ntype = str(dest.get("type") or "")
            if ntype in START_CONSUMERS:
                return True
    return False


def _preferred_still(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Pick EZOptionalImage, else a LoadImage that already feeds generation.

    Args:
        graph: Serialized graph.

    Returns:
        Source node, or None.
    """
    opts = _nodes_of(graph, "EZOptionalImage")
    if len(opts) == 1:
        return opts[0]
    loads = [
        node
        for node in _nodes_of(graph, "LoadImage")
        if _feeds_generation(graph, node)
    ]
    if len(loads) == 1:
        return loads[0]
    return None


def _retarget_describe_image(graph: dict[str, Any]) -> bool:
    """Point an existing describe node at the preferred still.

    Args:
        graph: Serialized graph (mutated).

    Returns:
        True when a link was rewritten.
    """
    hits = _nodes_of(graph, DESCRIBE_TYPE)
    src = _preferred_still(graph)
    if not hits:
        return False
    node = hits[0]
    if src is None:
        img_in = next(
            (item for item in node.get("inputs") or [] if item.get("name") == "image"),
            None,
        )
        if img_in is not None and img_in.get("link") is not None:
            _unlink(graph, int(img_in["link"]))
            img_in["link"] = None
            return True
        return False
    img_in = next(
        (item for item in node.get("inputs") or [] if item.get("name") == "image"),
        None,
    )
    if img_in is None:
        return False
    old = img_in.get("link")
    if old is not None:
        _unlink(graph, int(old))
    img_link = _append_link(graph, int(src["id"]), 0, int(node["id"]), 1, "IMAGE")
    img_in["link"] = img_link
    _push_output_link(src, 0, img_link)
    return True


def wire_image_describe(graph: dict[str, Any]) -> bool:
    """Insert EZImageDescribe and link caption into Enhance.image_desc.

    Args:
        graph: Serialized lab graph (mutated).

    Returns:
        True when a node was inserted.
    """
    if _nodes_of(graph, DESCRIBE_TYPE):
        _retarget_describe_image(graph)
        return False
    if not describe_in_scope(graph):
        return False
    src = _preferred_still(graph)
    if src is None:
        return False
    enhance = None
    for ntype in ENHANCE_TYPES:
        hits = _nodes_of(graph, ntype)
        if hits:
            enhance = hits[0]
            break
    if enhance is None:
        return False
    nid = _next_node_id(graph)
    x, y = node_pos(enhance)
    node = _make_describe(nid, [x, y + 200.0])
    graph.setdefault("nodes", []).append(node)
    img_link = _append_link(graph, int(src["id"]), 0, nid, 1, "IMAGE")
    node["inputs"][1]["link"] = img_link
    _push_output_link(src, 0, img_link)
    _link_out(graph, node, 0, enhance, "image_desc", "STRING", widget=False)
    return True
