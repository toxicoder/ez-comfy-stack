"""Insert EZImageDescribe when a graph has one still and a visual Enhance."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _wire_image_describe import describe_in_scope, wire_image_describe  # noqa: E402


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
        "extra": {"lab_rel": "stills/character-tweak"},
        "nodes": nodes,
        "links": links,
    }


def test_describe_scope_needs_one_still() -> None:
    assert describe_in_scope(_graph(loads=1)) is True
    assert describe_in_scope(_graph(loads=2)) is False
    assert describe_in_scope(_graph(loads=1, enhance=False)) is False
    skipped = _graph()
    skipped["extra"]["lab_rel"] = "inspire/prompt-forge"
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
