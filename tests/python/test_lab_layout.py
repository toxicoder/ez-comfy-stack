"""Node spacing contract: estimated Vue AABBs keep NODE_GAP, no overlaps."""

from __future__ import annotations

import copy
from typing import Any

from _lab_layout import (
    GENERIC_GROUP_TITLES,
    LAB_NODE_Y0,
    LAB_X0,
    NODE_GAP,
    VUE_HEIGHT_EXTRA,
    ensure_node_spacing,
    estimated_node_size,
    finalize_layout,
    has_named_stages,
    node_overlap_hits,
    node_pos,
    operator_note,
    organize_stages,
    topo_rank,
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


def test_quality_spacing_leaves_clear_header_untouched() -> None:
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


def _out(name: str, ltype: str, links: list[int] | None = None) -> dict[str, Any]:
    return {"name": name, "type": ltype, "links": links or [], "slot_index": 0}


def _inp(name: str, ltype: str, link: int | None = None) -> dict[str, Any]:
    return {"name": name, "type": ltype, "link": link}


def _klein_printer() -> dict[str, Any]:
    """Disconnected-looking Klein still with parked note, quality, and optional ref."""
    nodes = [
        _node(1, "UNETLoader", [40, 80], [360, 82]),
        _node(2, "CLIPLoader", [40, 234], [360, 106]),
        _node(3, "VAELoader", [40, 412], [360, 58]),
        _node(4, "CLIPTextEncode", [948, 80], [420, 160]),
        _node(5, "CLIPTextEncode", [948, 604], [420, 160]),
        _node(6, "EmptyFlux2LatentImage", [948, 836], [320, 106]),
        _node(7, "KSampler", [1440, 80], [330, 262]),
        _node(8, "VAEDecode", [1840, 80], [240, 46]),
        _node(9, "SaveImage", [1840, 198], [280, 270]),
        _node(10, "Note", [40, 1032], [960, 280]),
        _node(11, "EZKleinPromptEnhance", [480, 80], [420, 280]),
        _node(12, "EZNegativePromptEnhance", [480, 1384], [420, 280]),
        _node(13, "EZQuality", [40, -120], [320, 82]),
        _node(14, "EZImageFormat", [1048, 1014], [360, 220]),
        _node(15, "EZOptionalImage", [-400, 400], [360, 120]),
        _node(19, "EZModelCheck", [40, -332], [320, 140]),
    ]
    nodes[3]["title"] = "Positive"
    nodes[4]["title"] = "Negative"
    nodes[9]["title"] = "Operator note"
    nodes[12]["title"] = "Quality"
    nodes[15]["title"] = "Check models"
    nodes[0]["outputs"] = [_out("MODEL", "MODEL", [1])]
    nodes[1]["outputs"] = [_out("CLIP", "CLIP", [2, 3])]
    nodes[2]["outputs"] = [_out("VAE", "VAE", [7])]
    nodes[3]["inputs"] = [_inp("clip", "CLIP", 2), _inp("text", "STRING", 10)]
    nodes[3]["outputs"] = [_out("CONDITIONING", "CONDITIONING", [4])]
    nodes[4]["inputs"] = [_inp("clip", "CLIP", 3), _inp("text", "STRING", 11)]
    nodes[4]["outputs"] = [_out("CONDITIONING", "CONDITIONING", [5])]
    nodes[5]["outputs"] = [_out("LATENT", "LATENT", [6])]
    nodes[6]["inputs"] = [
        _inp("model", "MODEL", 1),
        _inp("positive", "CONDITIONING", 4),
        _inp("negative", "CONDITIONING", 5),
        _inp("latent_image", "LATENT", 6),
    ]
    nodes[6]["outputs"] = [_out("LATENT", "LATENT", [8])]
    nodes[7]["inputs"] = [_inp("samples", "LATENT", 8), _inp("vae", "VAE", 7)]
    nodes[7]["outputs"] = [_out("IMAGE", "IMAGE", [9])]
    nodes[8]["inputs"] = [_inp("images", "IMAGE", 9)]
    nodes[10]["outputs"] = [_out("prompt", "STRING", [10, 12])]
    nodes[11]["inputs"] = [_inp("positive", "STRING", 12)]
    nodes[11]["outputs"] = [_out("prompt", "STRING", [11])]
    links = [
        [1, 1, 0, 7, 0, "MODEL"],
        [2, 2, 0, 4, 0, "CLIP"],
        [3, 2, 0, 5, 0, "CLIP"],
        [4, 4, 0, 7, 1, "CONDITIONING"],
        [5, 5, 0, 7, 2, "CONDITIONING"],
        [6, 6, 0, 7, 3, "LATENT"],
        [7, 3, 0, 8, 1, "VAE"],
        [8, 7, 0, 8, 0, "LATENT"],
        [9, 8, 0, 9, 0, "IMAGE"],
        [10, 11, 0, 4, 1, "STRING"],
        [11, 12, 0, 5, 1, "STRING"],
        [12, 11, 0, 12, 0, "STRING"],
    ]
    return {"nodes": nodes, "links": links, "groups": [], "revision": 1}


def _group_titles(graph: dict[str, Any]) -> set[str]:
    return {str(grp.get("title") or "") for grp in graph.get("groups") or []}


def test_operator_note_prefers_operator_title() -> None:
    graph = {
        "nodes": [
            _node(1, "MarkdownNote", [40, 500], [400, 120]),
            _node(2, "Note", [40, 80], [960, 280]),
        ]
    }
    graph["nodes"][1]["title"] = "Operator note — still"
    note = operator_note(graph)
    assert note is not None
    assert int(note["id"]) == 2


def test_topo_rank_follows_links() -> None:
    graph = _klein_printer()
    ranks = topo_rank(graph)
    assert ranks[1] == 0
    assert ranks[9] > ranks[7]
    assert ranks[7] > ranks[1]


def test_finalize_layout_puts_note_top_left() -> None:
    graph = _klein_printer()
    finalize_layout(graph)
    note = operator_note(graph)
    assert note is not None
    nx, ny = node_pos(note)
    assert nx == LAB_X0
    assert ny == LAB_NODE_Y0
    for node in graph["nodes"]:
        x, y = node_pos(node)
        assert y + 0.5 >= ny
        assert x + 0.5 >= nx
        if int(node["id"]) == int(note["id"]):
            continue
        assert x > nx or y > ny


def test_quality_and_check_sit_in_header_right_of_note() -> None:
    graph = _klein_printer()
    finalize_layout(graph)
    note = operator_note(graph)
    assert note is not None
    nx, ny = node_pos(note)
    check = next(n for n in graph["nodes"] if n["type"] == "EZModelCheck")
    quality = next(n for n in graph["nodes"] if n["type"] == "EZQuality")
    cx, cy = node_pos(check)
    qx, qy = node_pos(quality)
    assert cy == ny
    assert qy == ny
    assert cx > nx
    assert qx > cx


def test_restage_empty_groups_into_stages() -> None:
    graph = _klein_printer()
    finalize_layout(graph)
    titles = _group_titles(graph)
    assert "NOTE" in titles
    assert "QUALITY" in titles
    assert "MODEL" in titles
    assert "PROMPT" in titles
    assert "SETTINGS" in titles
    assert "OUTPUT" in titles
    assert "INPUT" in titles
    ranks = topo_rank(graph)
    loaders = [n for n in graph["nodes"] if n["type"] in {"UNETLoader", "CLIPLoader", "VAELoader"}]
    saves = [n for n in graph["nodes"] if n["type"] == "SaveImage"]
    loader_x = sorted(node_pos(n)[0] for n in loaders)[len(loaders) // 2]
    save_x = sorted(node_pos(n)[0] for n in saves)[0]
    assert loader_x < save_x
    assert ranks[1] < ranks[9]
    optional = next(n for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    assert node_pos(optional)[0] >= LAB_X0
    assert node_overlap_hits(graph) == []


def test_named_shot_groups_are_kept() -> None:
    shot_a = _node(3, "KSampler", [500, 400], [330, 262])
    shot_b = _node(4, "KSampler", [500, 800], [330, 262])
    graph: dict[str, Any] = {
        "nodes": [
            _node(1, "Note", [40, 1200], [960, 280]),
            _node(2, "UNETLoader", [40, 80], [360, 82]),
            shot_a,
            shot_b,
            _node(5, "EZQuality", [40, -120], [320, 82]),
            _node(6, "EZModelCheck", [40, -332], [320, 140]),
        ],
        "groups": [
            {
                "id": 1,
                "title": "SHOT 01 tower",
                "bounding": [480, 360, 380, 340],
                "color": "#3f789e",
                "font_size": 24,
                "flags": {},
            },
            {
                "id": 2,
                "title": "SHOT 02 foyer",
                "bounding": [480, 760, 380, 340],
                "color": "#a1309b",
                "font_size": 24,
                "flags": {},
            },
        ],
        "links": [],
        "revision": 1,
    }
    graph["nodes"][0]["title"] = "Operator note"
    assert has_named_stages(graph)
    organize_stages(graph)
    titles = _group_titles(graph)
    assert "SHOT 01 tower" in titles
    assert "SHOT 02 foyer" in titles
    assert "NOTE" in titles
    note = operator_note(graph)
    assert note is not None
    assert node_pos(note) == (LAB_X0, float(LAB_NODE_Y0))
    assert node_pos(shot_a)[1] < node_pos(shot_b)[1]


def test_organize_stages_is_idempotent() -> None:
    graph = _klein_printer()
    organize_stages(graph)
    first = copy.deepcopy(graph)
    organize_stages(graph)
    for left, right in zip(first["nodes"], graph["nodes"], strict=True):
        assert left["pos"] == right["pos"]
    assert _group_titles(first) == _group_titles(graph)


def test_generic_titles_constant_covers_restage_names() -> None:
    assert {"NOTE", "QUALITY", "MODEL", "INPUT", "PROMPT", "SETTINGS", "OUTPUT"} <= (
        GENERIC_GROUP_TITLES
    )
