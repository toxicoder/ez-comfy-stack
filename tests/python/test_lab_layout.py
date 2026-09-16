"""Node spacing contract: estimated Vue AABBs keep NODE_GAP, no overlaps."""

from __future__ import annotations

import copy
from typing import Any

from _lab_layout import (
    LAB_NODE_Y0,
    NODE_GAP,
    VUE_HEIGHT_EXTRA,
    ensure_node_spacing,
    estimated_node_size,
    node_overlap_hits,
    node_pos,
)


def _node(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
) -> dict[str, Any]:
    return {
        "id": nid,
        "type": ntype,
        "pos": list(pos),
        "size": list(size),
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "properties": {},
        "widgets_values": [],
        "title": ntype,
    }


def test_estimated_enhance_uses_type_floor() -> None:
    node = _node(1, "EZKleinPromptEnhance", [40, 80], [420, 280])
    width, height = estimated_node_size(node)
    assert width == 420
    assert height == 420 + VUE_HEIGHT_EXTRA


def test_vue_tall_enhance_pushes_same_column_node_below() -> None:
    nodes = [
        _node(1, "EZKleinPromptEnhance", [40, 80], [420, 280]),
        _node(2, "CLIPLoader", [40, 380], [360, 106]),
    ]
    graph: dict[str, Any] = {"nodes": nodes, "groups": [], "revision": 1}
    assert node_overlap_hits(graph)
    ensure_node_spacing(graph)
    _x, y = node_pos(nodes[1])
    _width, enhance_h = estimated_node_size(nodes[0])
    assert y >= 80 + enhance_h + NODE_GAP
    assert node_overlap_hits(graph) == []
    assert nodes[0]["size"] == [420, 280]


def test_same_y_row_spreads_x_not_y() -> None:
    nodes = [
        _node(1, "VAEDecode", [40, 80], [240, 46]),
        _node(2, "SaveImage", [200, 80], [280, 270]),
    ]
    graph: dict[str, Any] = {"nodes": nodes, "groups": [], "revision": 1}
    ensure_node_spacing(graph)
    assert node_pos(nodes[0])[1] == 80
    assert node_pos(nodes[1])[1] == 80
    left_right = 40 + estimated_node_size(nodes[0])[0]
    assert node_pos(nodes[1])[0] >= left_right + NODE_GAP
    assert node_overlap_hits(graph) == []


def test_quality_stays_above_first_row() -> None:
    nodes = [
        _node(1, "UNETLoader", [40, 80], [360, 82]),
        _node(13, "EZQuality", [40, -120], [320, 82]),
    ]
    graph: dict[str, Any] = {"nodes": nodes, "groups": [], "revision": 1}
    ensure_node_spacing(graph)
    qx, qy = node_pos(nodes[1])
    assert qx == 40
    assert qy == -120
    assert qy < LAB_NODE_Y0
    assert node_overlap_hits(graph) == []


def test_ensure_node_spacing_is_idempotent() -> None:
    nodes = [
        _node(1, "EZKleinPromptEnhance", [40, 80], [420, 280]),
        _node(2, "CLIPLoader", [40, 380], [360, 106]),
        _node(3, "Note", [40, 500], [960, 200]),
    ]
    graph: dict[str, Any] = {"nodes": nodes, "groups": [], "revision": 1}
    ensure_node_spacing(graph)
    first = copy.deepcopy(graph)
    ensure_node_spacing(graph)
    first_nodes = first["nodes"]
    assert isinstance(first_nodes, list)
    assert nodes[0]["pos"] == first_nodes[0]["pos"]
    assert nodes[1]["pos"] == first_nodes[1]["pos"]
    assert nodes[2]["pos"] == first_nodes[2]["pos"]
    assert graph["revision"] == first["revision"]


def test_diagonal_neighbors_get_node_gap() -> None:
    nodes = [
        _node(1, "EZKleinPromptEnhance", [480, 80], [420, 280]),
        _node(2, "KSampler", [940, 212], [330, 262]),
    ]
    graph: dict[str, Any] = {"nodes": nodes, "groups": [], "revision": 1}
    assert node_overlap_hits(graph)
    ensure_node_spacing(graph)
    assert node_overlap_hits(graph) == []
    left = 480 + estimated_node_size(nodes[0])[0]
    kx, ky = node_pos(nodes[1])
    assert kx >= left + NODE_GAP or ky >= 80 + estimated_node_size(nodes[0])[1] + NODE_GAP


def test_subgraph_nodes_are_spaced() -> None:
    inner_nodes = [
        _node(1, "EZKleinPromptEnhance", [40, 80], [420, 280]),
        _node(2, "CLIPLoader", [40, 380], [360, 106]),
    ]
    inner: dict[str, Any] = {"id": "sub", "nodes": inner_nodes, "groups": []}
    graph: dict[str, Any] = {
        "nodes": [_node(1, "Note", [40, 80], [400, 120])],
        "groups": [],
        "definitions": {"subgraphs": [inner]},
        "revision": 1,
    }
    ensure_node_spacing(graph)
    assert node_overlap_hits(inner) == []
    _width, enhance_h = estimated_node_size(inner_nodes[0])
    assert node_pos(inner_nodes[1])[1] >= 80 + enhance_h + NODE_GAP
