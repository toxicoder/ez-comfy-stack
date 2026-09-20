"""In-scope lab Apps expose Format / platform; locked graphs stay fixed-size."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_paths import lab_graph_paths, lab_json, lab_rel_of  # noqa: E402
from _wire_format import FORMAT_BLURB, FORMAT_SCOPE, format_kind  # noqa: E402


def _load(rel: str) -> dict[str, Any]:
    return json.loads(lab_json(rel).read_text(encoding="utf-8"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src_type(graph: dict[str, Any], node: dict[str, Any], name: str) -> str:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    origin = int(_link_map(graph)[int(inp["link"])][1])
    return str(_by_id(graph)[origin].get("type") or "")


def _widget_names(graph: dict[str, Any]) -> list[str]:
    linear = (graph.get("extra") or {}).get("linearData") or {}
    return [entry[1] for entry in linear.get("inputs") or []]


def test_in_scope_apps_wire_format_and_app_widgets() -> None:
    still_type = "EZImageFormat"
    video_type = "EZVideoFormat"
    for rel in sorted(FORMAT_SCOPE):
        graph = _load(rel)
        kind = format_kind(rel)
        ntype = still_type if kind == "still" else video_type
        types = {node.get("type") for node in graph["nodes"]}
        assert ntype in types, rel
        assert FORMAT_BLURB in str((graph.get("extra") or {}).get("lab_note") or ""), rel
        names = _widget_names(graph)
        assert "format" in names, rel
        assert "size_mode" in names, rel
        assert "width" in names, rel
        assert "height" in names, rel
        if kind == "video":
            assert "duration_s" in names, rel
        if rel in {"stills/still-studio", "stills/image-studio"}:
            assert "look" in names
        else:
            assert "look" not in names, rel
        assert "family" not in names, rel
        if kind == "still":
            latent = next(
                node
                for node in graph["nodes"]
                if node.get("type") == "EmptyFlux2LatentImage"
            )
            assert _src_type(graph, latent, "width") == still_type, rel
        else:
            latent = next(
                node
                for node in graph["nodes"]
                if node.get("type")
                in {
                    "Wan22ImageToVideoLatent",
                    "LTXVImgToVideo",
                    "EmptyLTXVLatentVideo",
                }
            )
            assert _src_type(graph, latent, "width") == video_type, rel


def test_locked_apps_do_not_gain_a_format_picker() -> None:
    locked = (
        "stills/text-swap",
        "stills/platform-pack",
        "stills/character-tweak",
        "stills/background-swap",
        "motion/silent/vace-join",
        "films/go-see",
        "inspire/prompt-forge",
    )
    for rel in locked:
        graph = _load(rel)
        types = {node.get("type") for node in graph["nodes"]}
        assert "EZImageFormat" not in types, rel
        assert "EZVideoFormat" not in types, rel


def test_every_lab_format_node_is_in_scope() -> None:
    unexpected: list[str] = []
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        graph = json.loads(path.read_text(encoding="utf-8"))
        types = {node.get("type") for node in graph.get("nodes") or []}
        if "EZImageFormat" in types or "EZVideoFormat" in types:
            if rel not in FORMAT_SCOPE:
                unexpected.append(rel)
    assert unexpected == []
