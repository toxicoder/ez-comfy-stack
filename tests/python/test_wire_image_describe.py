"""Insert EZImageDescribe when a graph has one still and a visual Enhance."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _wire_describe_ref import describe_needs_source  # noqa: E402
from _wire_image_describe import describe_in_scope, wire_image_describe  # noqa: E402


def _drop_node(graph: dict[str, Any], node_id: int) -> None:
    """Delete one node and every link that touched it.

    Arguments:
        graph: Serialized graph (mutated).
        node_id: Node to remove.

    Outputs:
        None. Node, link rows, and socket bookkeeping are pruned together, which
        is what a builder pass that deleted a picker leaves behind.

    Returns:
        None.
    """
    gone = {
        int(row[0])
        for row in graph["links"]
        if int(row[1]) == node_id or int(row[3]) == node_id
    }
    graph["links"] = [row for row in graph["links"] if int(row[0]) not in gone]
    for node in graph["nodes"]:
        for item in node.get("inputs") or []:
            if item.get("link") in gone:
                item["link"] = None
        for out in node.get("outputs") or []:
            out["links"] = [x for x in (out.get("links") or []) if int(x) not in gone]
    graph["nodes"] = [node for node in graph["nodes"] if int(node["id"]) != node_id]


def _add_plate(graph: dict[str, Any]) -> None:
    """Add a second LoadImage feeding generation: the multi-plate tour shape.

    Arguments:
        graph: Serialized graph (mutated).

    Outputs:
        None. A loader and the VAEEncode it feeds are appended, and the graph
        counters follow them.

    Returns:
        None.
    """
    nid = max(int(node["id"]) for node in graph["nodes"]) + 1
    lid = max([int(row[0]) for row in graph["links"]] or [0]) + 1
    graph["nodes"].append(
        {
            "id": nid,
            "type": "LoadImage",
            "pos": [0, 300],
            "inputs": [],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [lid], "slot_index": 0}
            ],
            "widgets_values": ["plate-two.png", "image"],
        }
    )
    graph["nodes"].append(
        {
            "id": nid + 1,
            "type": "VAEEncode",
            "pos": [200, 300],
            "inputs": [{"name": "pixels", "type": "IMAGE", "link": lid}],
            "outputs": [],
        }
    )
    graph["links"].append([lid, nid, 0, nid + 1, 0, "IMAGE"])
    graph["last_node_id"] = nid + 1
    graph["last_link_id"] = lid


def _describe(graph: dict[str, Any]) -> dict[str, Any]:
    """The one captioner on the graph."""
    return next(n for n in graph["nodes"] if n.get("type") == "EZImageDescribe")



def _graph(*, loads: int = 1, enhance: bool = True) -> dict:
    nodes: list[dict] = []
    links: list[list[Any]] = []
    nid = 1
    lid = 1
    for _ in range(loads):
        nodes.append(
            {
                "id": nid,
                "type": "LoadImage",
                "pos": [0, 0],
                "inputs": [],
                "outputs": [
                    {
                        "name": "IMAGE",
                        "type": "IMAGE",
                        "links": [lid],
                        "slot_index": 0,
                    }
                ],
                "widgets_values": ["example.png", "image"],
            }
        )
        enc_id = nid + 50
        nodes.append(
            {
                "id": enc_id,
                "type": "VAEEncode",
                "pos": [200, 0],
                "inputs": [{"name": "pixels", "type": "IMAGE", "link": lid}],
                "outputs": [],
            }
        )
        links.append([lid, nid, 0, enc_id, 0, "IMAGE"])
        nid += 1
        lid += 1
    if enhance:
        nodes.append(
            {
                "id": nid,
                "type": "EZKleinPromptEnhance",
                "pos": [200, 0],
                "inputs": [],
                "outputs": [
                    {"name": "prompt", "type": "STRING", "links": [], "slot_index": 0}
                ],
                "widgets_values": ["custom", "hello", True, "edit", "", "none", ""],
            }
        )
    return {
        "last_node_id": nid + 50,
        "last_link_id": lid,
        "extra": {"lab_rel": "photos/character-tweak"},
        "nodes": nodes,
        "links": links,
    }


def test_describe_scope_needs_one_still() -> None:
    assert describe_in_scope(_graph(loads=1)) is True
    assert describe_in_scope(_graph(loads=2)) is False
    assert describe_in_scope(_graph(loads=1, enhance=False)) is False
    skipped = _graph()
    skipped["extra"]["lab_rel"] = "labs/assist/prompt-forge"
    assert describe_in_scope(skipped) is False


def test_wire_image_describe_links_caption() -> None:
    graph = _graph()
    assert wire_image_describe(graph) is True
    desc = next(n for n in graph["nodes"] if n.get("type") == "EZImageDescribe")
    assert desc["widgets_values"][0] is False
    enh = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    cap = next(item for item in enh["inputs"] if item.get("name") == "image_desc")
    assert cap["link"] is not None
    assert wire_image_describe(graph) is False


def test_the_builder_leaves_no_starved_captioner() -> None:
    """The node is never inserted with an image slot nothing can ever fill."""
    graph = _graph()
    assert wire_image_describe(graph) is True
    assert describe_needs_source(graph) == []


def test_a_second_plate_keeps_the_caption_still() -> None:
    """A tour gains a plate; the caption keeps the still it was already reading.

    The preferred still only names a loader that feeds generation and only when
    there is exactly one, so a second plate makes it abstain. Dropping the link
    then was how the shipped graphs lost the still behind a live toggle.
    """
    graph = _graph()
    assert wire_image_describe(graph) is True
    link = _describe(graph)["inputs"][1]["link"]
    assert link is not None
    _add_plate(graph)

    assert wire_image_describe(graph) is False

    assert _describe(graph)["inputs"][1]["link"] == link
    assert [row for row in graph["links"] if int(row[0]) == link]


def test_a_caption_that_lost_its_picker_gains_one() -> None:
    """A deleted loader does not leave the toggle standing over an empty slot."""
    graph = _graph()
    assert wire_image_describe(graph) is True
    loader = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    _drop_node(graph, int(loader["id"]))

    assert wire_image_describe(graph) is False

    assert _describe(graph)["inputs"][1]["link"] is not None
    assert any(n.get("type") == "EZOptionalImage" for n in graph["nodes"])
    assert describe_needs_source(graph) == []


def test_a_repurposed_producer_is_not_left_behind_the_toggle() -> None:
    """A node that stopped being a still cannot keep feeding the captioner."""
    graph = _graph()
    assert wire_image_describe(graph) is True
    loader = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    loader["type"] = "Note"

    assert wire_image_describe(graph) is False

    link = _describe(graph)["inputs"][1]["link"]
    assert link is not None
    producer = next(
        node for node in graph["nodes"] if node["id"] == int(
            next(row for row in graph["links"] if int(row[0]) == link)[1]
        )
    )
    assert producer.get("type") == "EZOptionalImage"

