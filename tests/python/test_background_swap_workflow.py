"""stills/background-swap: Klein edit, source-sized, 100 samples, no Format."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
CUSTOM = ROOT / "custom_nodes"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from _lab_paths import lab_json, load_lab_graph  # noqa: E402
from _stamp_app_mode import infer_suite_inputs, STAMP_SPECS  # noqa: E402
from ez_prompt_enhance.samples import (  # noqa: E402
    BACKGROUND_SWAP_COUNT,
    catalog_for_rel,
    load_catalog,
    sample_labels,
)


def _load() -> dict[str, Any]:
    return load_lab_graph(lab_json("stills/background-swap.json"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    link_id = int(inp["link"])
    origin = int(_link_map(graph)[link_id][1])
    return _by_id(graph)[origin]


def test_background_swap_identity_and_app_mode() -> None:
    graph = _load()
    extra = graph["extra"]
    assert extra.get("lab_rel") == "stills/background-swap"
    assert graph.get("id") == "background-swap"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_bg_swap"
    names = [entry[1] for entry in extra["linearData"]["inputs"]]
    assert names[0] == "image"
    assert "enable" in names
    assert "upscale" in names
    assert "style" not in names
    assert "format" not in names
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZImageFormat" not in types
    assert "EZImageUpscale" in types
    assert "EZImageDescribe" in types


def test_background_swap_is_size_matched_klein_edit() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EmptyFlux2LatentImage" not in types
    assert "ReferenceLatent" in types
    assert "EZSnapImage" in types
    assert "EZMatchImageSize" in types
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    values = list(enh["widgets_values"] or [])
    mode = values[3] if len(values) >= 7 else values[2]
    assert mode == "edit"
    desc = next(node for node in graph["nodes"] if node.get("type") == "EZImageDescribe")
    assert desc["widgets_values"][0] is False
    assert _src(graph, desc, "image")["type"] == "LoadImage"
    assert _src(graph, enh, "image_desc")["type"] == "EZImageDescribe"


def test_background_swap_catalog_has_one_hundred_recipes() -> None:
    assert catalog_for_rel("stills/background-swap") == "klein_background_swap"
    rows = load_catalog("klein_background_swap")
    assert len(rows) == BACKGROUND_SWAP_COUNT
    assert sample_labels("klein_background_swap")[-1] == "custom"
    spec = STAMP_SPECS["stills/background-swap"]
    graph = _load()
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    assert "Describe image" in labels
    assert "Upscale" in labels
    assert any("source" in label.lower() for label in labels)


def test_background_swap_json_roundtrip() -> None:
    path = lab_json("stills/background-swap.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["extra"]["workflowRendererVersion"] == "Vue-corrected"
