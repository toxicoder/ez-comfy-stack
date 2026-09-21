"""Insert EZBackgroundCast into Klein background-swap / background-edit graphs.

Not collected by pytest. Builders import this.
"""

from __future__ import annotations

from typing import Any

from _lab_layout import node_pos
from _wire_format import (
    _link_out,
    _next_node_id,
    _nodes_of,
)

CAST_TYPE = "EZBackgroundCast"
ENHANCE_TYPE = "EZKleinPromptEnhance"
CAST_RELS = frozenset({"stills/background-swap", "stills/background-edit"})


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


def _make_cast(nid: int, pos: list[float]) -> dict[str, Any]:
    """Build an EZBackgroundCast node dict.

    Args:
        nid: Node id.
        pos: Canvas position.

    Returns:
        Node payload.
    """
    return {
        "id": nid,
        "type": CAST_TYPE,
        "pos": pos,
        "size": [280, 90],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [
            {
                "name": "other_characters",
                "type": "BOOLEAN",
                "link": None,
                "widget": {"name": "other_characters"},
            },
            {
                "name": "background_characters",
                "type": "BOOLEAN",
                "link": None,
                "widget": {"name": "background_characters"},
            },
        ],
        "outputs": [
            {
                "name": "cast",
                "type": "STRING",
                "links": [],
                "slot_index": 0,
            }
        ],
        "properties": {"Node name for S&R": CAST_TYPE},
        "widgets_values": [True, True],
        "title": "Background cast",
    }


def _relink_cast(
    graph: dict[str, Any], node: dict[str, Any], enhance: dict[str, Any]
) -> None:
    """Point an existing cast node at Enhance.background_cast.

    Args:
        graph: Serialized graph.
        node: EZBackgroundCast node.
        enhance: EZKleinPromptEnhance node.
    """
    out = (node.get("outputs") or [{}])[0]
    links = list(out.get("links") or [])
    if links:
        return
    _link_out(graph, node, 0, enhance, "background_cast", "STRING", widget=False)


def wire_background_cast(graph: dict[str, Any]) -> bool:
    """Insert EZBackgroundCast and link the token into Enhance.

    Args:
        graph: Serialized lab graph (mutated).

    Returns:
        True when a node was inserted.
    """
    if _lab_rel(graph) not in CAST_RELS:
        return False
    hits = _nodes_of(graph, ENHANCE_TYPE)
    if not hits:
        return False
    enhance = hits[0]
    existing = _nodes_of(graph, CAST_TYPE)
    if existing:
        _relink_cast(graph, existing[0], enhance)
        return False
    nid = _next_node_id(graph)
    x, y = node_pos(enhance)
    node = _make_cast(nid, [x + 320.0, y + 200.0])
    graph.setdefault("nodes", []).append(node)
    _link_out(graph, node, 0, enhance, "background_cast", "STRING", widget=False)
    return True
