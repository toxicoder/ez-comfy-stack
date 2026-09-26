"""stills/background-swap and stills/background-edit: Klein source-sized edits."""

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


def _load(rel: str = "stills/background-swap.json") -> dict[str, Any]:
    return load_lab_graph(lab_json(rel))


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
    assert "other_characters" in names
    assert "background_characters" in names
    assert "style" not in names
    assert "format" not in names
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZImageFormat" not in types
    assert "EZImageUpscale" in types
    assert "EZImageDescribe" in types
    assert "EZBackgroundCast" in types


def test_background_swap_is_size_matched_klein_edit() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EmptyFlux2LatentImage" not in types
    assert "ReferenceLatent" not in types
    assert "EZCubicCondition" in types
    assert "EZReinsertPeople" in types
    assert "EZSnapImage" in types
    assert "EZEmptyFlux2FromImage" in types
    assert "EZMatchImageSize" in types
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    values = list(enh["widgets_values"] or [])
    mode = values[3] if len(values) >= 7 else values[2]
    assert mode == "background_swap"
    prompt = str(values[1] if len(values) >= 7 else values[0])
    assert "entire environment" in prompt.casefold()
    assert "ground or floor" in prompt.casefold()
    assert "replace only the background" not in prompt.casefold()
    assert _src(graph, enh, "background_cast")["type"] == "EZBackgroundCast"
    desc = next(node for node in graph["nodes"] if node.get("type") == "EZImageDescribe")
    assert desc["widgets_values"][0] is True
    assert _src(graph, desc, "image")["type"] == "LoadImage"
    assert _src(graph, enh, "image_desc")["type"] == "EZImageDescribe"
    sampler = next(node for node in graph["nodes"] if node.get("type") == "KSampler")
    assert _src(graph, sampler, "latent_image")["type"] == "EZEmptyFlux2FromImage"
    assert _src(graph, sampler, "positive")["type"] == "EZCubicCondition"
    ref = next(node for node in graph["nodes"] if node.get("type") == "EZCubicCondition")
    assert _src(graph, ref, "latent")["type"] == "VAEEncode"
    assert _src(graph, ref, "image")["type"] == "EZSnapImage"
    assert _src(graph, ref, "vae")["type"] == "VAELoader"
    assert _src(graph, ref, "prompt")["type"] == "EZKleinPromptEnhance"
    assert ref.get("widgets_values") == []
    match = next(node for node in graph["nodes"] if node.get("type") == "EZMatchImageSize")
    pasted = _src(graph, match, "image")
    assert pasted["type"] == "EZReinsertPeople"
    assert pasted.get("widgets_values") == []
    assert _src(graph, pasted, "plate")["type"] == "VAEDecode"
    assert _src(graph, pasted, "source")["type"] == "LoadImage"
    assert _src(graph, pasted, "prompt")["type"] == "EZKleinPromptEnhance"
    empty = next(
        node for node in graph["nodes"] if node.get("type") == "EZEmptyFlux2FromImage"
    )
    assert _src(graph, empty, "image")["type"] == "EZSnapImage"
    pos = next(
        node
        for node in graph["nodes"]
        if node.get("type") == "CLIPTextEncode" and node.get("title") != "Negative"
    )
    assert "entire environment" in str(pos["widgets_values"][0]).casefold()
    neg = next(
        node
        for node in graph["nodes"]
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative"
    )
    neg_text = str(neg["widgets_values"][0]).casefold()
    assert "game-engine" not in neg_text
    assert "pixar" not in neg_text
    assert "illustration" not in neg_text
    note = graph["extra"]["lab_note"].casefold()
    assert "empty flux" in note or "empty klein" in note
    assert "describe image (default on)" in note
    assert "block study" in note
    assert "pasted back" in note


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
    assert "New background" in labels
    assert "Other characters" in labels
    assert "Background characters" in labels
    assert any("source" in label.lower() for label in labels)


def test_background_edit_identity_style_and_samples() -> None:
    graph = _load("stills/background-edit.json")
    extra = graph["extra"]
    assert extra.get("lab_rel") == "stills/background-edit"
    assert graph.get("id") == "background-edit"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_bg_edit"
    names = [entry[1] for entry in extra["linearData"]["inputs"]]
    assert names[0] == "image"
    assert "style" in names
    assert "other_characters" in names
    assert "background_characters" in names
    assert "format" not in names
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZImageFormat" not in types
    assert "EZBackgroundCast" in types
    assert "ReferenceLatent" in types
    assert "EZCubicCondition" not in types
    assert "EZReinsertPeople" not in types
    assert "EZSnapImage" in types
    assert "EZMatchImageSize" in types
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    values = list(enh["widgets_values"] or [])
    enhance_mode = values[3] if len(values) >= 7 else values[2]
    assert enhance_mode == "background_edit"
    assert catalog_for_rel("stills/background-edit") == "klein_background_edit"
    rows = load_catalog("klein_background_edit")
    assert len(rows) == 30
    assert sample_labels("klein_background_edit")[-1] == "custom"
    spec = STAMP_SPECS["stills/background-edit"]
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    assert "Background edit" in labels
    assert "Style" in labels
    assert "Other characters" in labels


def test_background_apps_save_the_upscaled_still() -> None:
    """Upscale sits between match-to-source and SaveImage on both apps."""
    for rel in ("stills/background-swap.json", "stills/background-edit.json"):
        graph = _load(rel)
        save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
        upscale = _src(graph, save, "images")
        assert upscale["type"] == "EZImageUpscale"
        assert _src(graph, upscale, "image")["type"] == "EZMatchImageSize"
        note = str(graph["extra"]["lab_note"])
        assert "when Upscale is none" in note
        assert "4K lanczos-resize the saved PNG" in note


def test_background_swap_json_roundtrip() -> None:
    path = lab_json("stills/background-swap.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["extra"]["workflowRendererVersion"] == "Vue-corrected"
