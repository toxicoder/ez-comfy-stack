"""klein/text-swap graph: glyph-lock Klein edit, output matches source size."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_paths import lab_json, load_lab_graph  # noqa: E402
from _stamp_app_mode import infer_suite_inputs, STAMP_SPECS  # noqa: E402


def _load() -> dict[str, Any]:
    return load_lab_graph(lab_json("klein/text-swap.json"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    link_id = int(inp["link"])
    origin = int(_link_map(graph)[link_id][1])
    return _by_id(graph)[origin]


def test_text_swap_identity_and_app_mode() -> None:
    graph = _load()
    extra = graph["extra"]
    assert extra.get("lab_rel") == "klein/text-swap"
    assert graph.get("id") == "text-swap"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    assert mode["default_view"] == "app"
    assert "wan/still-to-video-5s" in mode["handoff"]
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_text_swap"


def test_text_swap_is_size_matched_klein_edit() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EmptyFlux2LatentImage" not in types
    assert "ReferenceLatent" in types
    assert "EZSnapImage" in types
    assert "EZMatchImageSize" in types
    assert "LoadImage" in types
    sampler = next(node for node in graph["nodes"] if node.get("type") == "KSampler")
    encode = _src(graph, sampler, "latent_image")
    assert encode["type"] == "VAEEncode"
    positive = _src(graph, sampler, "positive")
    assert positive["type"] == "ReferenceLatent"
    ref_lat = _src(graph, positive, "latent")
    assert ref_lat["type"] == "VAEEncode"
    assert int(ref_lat["id"]) == int(encode["id"])
    snap = _src(graph, encode, "pixels")
    assert snap["type"] == "EZSnapImage"
    load = _src(graph, snap, "image")
    assert load["type"] == "LoadImage"
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    match = _src(graph, save, "images")
    assert match["type"] == "EZMatchImageSize"
    decoded = _src(graph, match, "image")
    assert decoded["type"] == "VAEDecode"
    size_src = _src(graph, match, "size_src")
    assert size_src["type"] == "LoadImage"
    assert int(size_src["id"]) == int(load["id"])


def test_text_swap_enhance_mode_and_app_widgets() -> None:
    graph = _load()
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    values = list(enh["widgets_values"] or [])
    mode = values[3] if len(values) >= 7 else values[2]
    assert mode == "text_swap"
    prompt = values[1] if len(values) >= 7 else values[0]
    assert "HELLO" in str(prompt)
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert names[0] == "quality"
    assert "sample" in names
    assert "prompt" in names
    assert "image" in names
    assert "enhance" in names
    assert "seed" in names
    assert "style" not in names
    spec = STAMP_SPECS["klein/text-swap"]
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    assert "New lettering" in labels
    assert "Style" not in labels
    assert any("source" in label.lower() for label in labels)
