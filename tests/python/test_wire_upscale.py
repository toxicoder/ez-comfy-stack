"""Insert EZImageUpscale before SaveImage."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_paths import lab_graph_paths, lab_rel_of, load_lab_graph  # noqa: E402
from _wire_upscale import (  # noqa: E402
    UPSCALE_COMBO_TYPE,
    upscale_in_scope,
    wire_upscale,
)


def test_upscale_scope() -> None:
    assert upscale_in_scope("photos/still-draft") is True
    assert upscale_in_scope("social/stills/youtube-channel-icon") is True
    assert upscale_in_scope("guides/clay-hero") is True
    assert upscale_in_scope("video/silent/still-to-video-5s") is False
    assert upscale_in_scope("audio/albums/nill-bye/peer-review/cover") is False


def test_wire_upscale_inserts_passthrough_node() -> None:
    graph: dict[str, Any] = {
        "last_node_id": 2,
        "last_link_id": 1,
        "extra": {"lab_rel": "photos/still-draft"},
        "nodes": [
            {
                "id": 1,
                "type": "VAEDecode",
                "pos": [0, 0],
                "inputs": [],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [1], "slot_index": 0}
                ],
            },
            {
                "id": 2,
                "type": "SaveImage",
                "pos": [400, 0],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 1}],
                "outputs": [],
                "widgets_values": ["ez_x"],
            },
        ],
        "links": [[1, 1, 0, 2, 0, "IMAGE"]],
    }
    assert wire_upscale(graph, "photos/still-draft") is True
    types = [node.get("type") for node in graph["nodes"]]
    assert types.count("EZImageUpscale") == 1
    up = next(node for node in graph["nodes"] if node.get("type") == "EZImageUpscale")
    assert up["widgets_values"][0] == "none"
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    src_link = next(
        item for item in save["inputs"] if item.get("name") == "images"
    )
    origin = next(
        row for row in graph["links"] if int(row[0]) == int(src_link["link"])
    )
    assert int(origin[1]) == int(up["id"])
    assert wire_upscale(graph, "photos/still-draft") is False


def _save_image_source(graph: dict[str, Any], save: dict[str, Any]) -> dict[str, Any] | None:
    """Return the node feeding SaveImage.images."""
    links = {int(row[0]): row for row in graph.get("links") or []}
    nodes = {int(node["id"]): node for node in graph.get("nodes") or []}
    for item in save.get("inputs") or []:
        if item.get("name") != "images" or item.get("link") is None:
            continue
        row = links.get(int(item["link"]))
        if not row:
            return None
        return nodes.get(int(row[1]))
    return None


def test_wire_upscale_reuses_orphan_between_match_and_save() -> None:
    """A dead decode -> upscale branch is moved onto Match -> Save."""
    graph: dict[str, Any] = {
        "last_node_id": 4,
        "last_link_id": 3,
        "extra": {"lab_rel": "photos/background-swap"},
        "nodes": [
            {
                "id": 1,
                "type": "VAEDecode",
                "pos": [0, 0],
                "inputs": [],
                "outputs": [
                    {
                        "name": "IMAGE",
                        "type": "IMAGE",
                        "links": [1, 2],
                        "slot_index": 0,
                    }
                ],
            },
            {
                "id": 3,
                "type": "EZMatchImageSize",
                "pos": [200, 0],
                "inputs": [{"name": "image", "type": "IMAGE", "link": 1}],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [3], "slot_index": 0}
                ],
            },
            {
                "id": 4,
                "type": "EZImageUpscale",
                "pos": [200, 120],
                "inputs": [{"name": "image", "type": "IMAGE", "link": 2}],
                "outputs": [
                    {"name": "image", "type": "IMAGE", "links": [], "slot_index": 0},
                    {
                        "name": "upscale",
                        "type": list(UPSCALE_COMBO_TYPE),
                        "links": [],
                        "slot_index": 1,
                    },
                ],
                "widgets_values": ["none"],
            },
            {
                "id": 2,
                "type": "SaveImage",
                "pos": [400, 0],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 3}],
                "outputs": [],
                "widgets_values": ["ez_bg_swap"],
            },
        ],
        "links": [
            [1, 1, 0, 3, 0, "IMAGE"],
            [2, 1, 0, 4, 0, "IMAGE"],
            [3, 3, 0, 2, 0, "IMAGE"],
        ],
    }
    assert wire_upscale(graph, "photos/background-swap") is True
    ups = [node for node in graph["nodes"] if node.get("type") == "EZImageUpscale"]
    assert len(ups) == 1
    up = cast(dict[str, Any], ups[0])
    assert int(up["id"]) == 4
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert _save_image_source(graph, save) is up
    links = {int(row[0]): row for row in graph["links"]}
    nodes = {int(node["id"]): node for node in graph["nodes"]}
    inputs = cast(list[dict[str, Any]], up["inputs"])
    image_link = next(item["link"] for item in inputs if item["name"] == "image")
    match = cast(dict[str, Any], nodes[int(links[int(image_link)][1])])
    assert match["type"] == "EZMatchImageSize"
    decode = cast(dict[str, Any], nodes[1])
    decode_links = cast(list[int], decode["outputs"][0]["links"])
    for lid in decode_links:
        dest = cast(dict[str, Any], nodes[int(links[int(lid)][3])])
        assert dest["type"] != "EZImageUpscale"
    assert wire_upscale(graph, "photos/background-swap") is False


def test_lab_saves_run_through_upscale() -> None:
    """In-scope SaveImage nodes take the upscaled still; others are left alone."""
    misses: list[str] = []
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        graph = load_lab_graph(path)
        if not isinstance(graph, dict) or "nodes" not in graph:
            continue
        has_upscale = any(
            node.get("type") == "EZImageUpscale" for node in graph.get("nodes") or []
        )
        if upscale_in_scope(rel) or has_upscale:
            for node in graph.get("nodes") or []:
                if node.get("type") != "SaveImage":
                    continue
                src = _save_image_source(graph, node)
                if src is None or src.get("type") != "EZImageUpscale":
                    misses.append(
                        f"{rel} save#{node.get('id')} src={None if src is None else src.get('type')}"
                    )
            if upscale_in_scope(rel):
                copied = copy.deepcopy(graph)
                if wire_upscale(copied, rel):
                    misses.append(f"{rel} wire_upscale still had work")
        else:
            before = [node.get("type") for node in graph.get("nodes") or []]
            copied = copy.deepcopy(graph)
            assert wire_upscale(copied, rel) is False
            after = [node.get("type") for node in copied.get("nodes") or []]
            assert before == after, rel
    assert misses == [], "upscale not on save path:\n" + "\n".join(misses)


def _two_save_graph() -> dict[str, Any]:
    """Build a decode feeding two saves, the shape that shares one rung.

    Returns:
        A minimal graph in ``photos/still-draft`` scope, unsaved by the pass.
    """
    return {
        "last_node_id": 3,
        "last_link_id": 2,
        "extra": {"lab_rel": "photos/still-draft"},
        "nodes": [
            {
                "id": 1,
                "type": "VAEDecode",
                "pos": [0, 0],
                "inputs": [],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [1, 2], "slot_index": 0}
                ],
            },
            {
                "id": 2,
                "type": "SaveImage",
                "pos": [300, 0],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 1}],
                "outputs": [],
                "widgets_values": ["ez_pair"],
            },
            {
                "id": 3,
                "type": "SaveImage",
                "pos": [300, 200],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 2}],
                "outputs": [],
                "widgets_values": ["ez_pair_b"],
            },
        ],
        "links": [
            [1, 1, 0, 2, 0, "IMAGE"],
            [2, 1, 0, 3, 0, "IMAGE"],
        ],
    }


def test_shared_rung_links_under_the_combo_values() -> None:
    """A rung shared between saves is typed by its values, never by STRING.

    ComfyUI types a combo widget input by the list it accepts, so a link typed
    ``STRING`` into ``upscale`` is read as an invalid connection and the whole
    App is blocked from Queueing. The values list has to appear on the producing
    output slot, the consuming input slot, and the link row.
    """
    graph = _two_save_graph()
    assert wire_upscale(graph, "photos/still-draft") is True
    upscales = [
        node for node in graph["nodes"] if node.get("type") == "EZImageUpscale"
    ]
    assert len(upscales) == 2, "two saves take one master rung and one clone"
    master, clone = sorted(upscales, key=lambda node: int(node["id"]))
    clone_slot = next(
        slot for slot in clone["inputs"] if slot.get("name") == "upscale"
    )
    assert clone_slot["type"] == UPSCALE_COMBO_TYPE
    assert clone_slot.get("widget") == {"name": "upscale"}
    master_slot = next(
        slot for slot in master["outputs"] if slot.get("name") == "upscale"
    )
    assert master_slot["type"] == UPSCALE_COMBO_TYPE
    rows = [
        row
        for row in graph["links"]
        if int(row[1]) == int(master["id"]) and int(row[3]) == int(clone["id"])
    ]
    assert len(rows) == 1, "the clone takes exactly one shared rung"
    assert rows[0][5] == UPSCALE_COMBO_TYPE
