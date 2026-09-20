"""Insert EZImageUpscale before SaveImage."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _wire_upscale import upscale_in_scope, wire_upscale  # noqa: E402


def test_upscale_scope() -> None:
    assert upscale_in_scope("stills/still-draft") is True
    assert upscale_in_scope("creator/stills/youtube-channel-icon") is True
    assert upscale_in_scope("dcc/clay-hero") is True
    assert upscale_in_scope("motion/silent/still-to-video-5s") is False
    assert upscale_in_scope("audio/albums/nill-bye/peer-review/cover") is False


def test_wire_upscale_inserts_passthrough_node() -> None:
    graph: dict[str, Any] = {
        "last_node_id": 2,
        "last_link_id": 1,
        "extra": {"lab_rel": "stills/still-draft"},
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
    assert wire_upscale(graph, "stills/still-draft") is True
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
    assert wire_upscale(graph, "stills/still-draft") is False
