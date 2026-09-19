"""klein/still-studio graph: format picker wired into latent, hint, prefix."""

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
from _stamp_app_mode import STAMP_SPECS, infer_suite_inputs  # noqa: E402


def _load() -> dict[str, Any]:
    return load_lab_graph(lab_json("klein/still-studio.json"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    link_id = int(inp["link"])
    origin = int(_link_map(graph)[link_id][1])
    return _by_id(graph)[origin]


def test_still_studio_identity_and_app_mode() -> None:
    graph = _load()
    extra = graph["extra"]
    assert extra.get("lab_rel") == "klein/still-studio"
    assert graph.get("id") == "still-studio"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    assert mode["default_view"] == "app"
    assert "wan/still-to-video-5s" in mode["handoff"]
    assert "ltx/still-to-video-5s" in mode["handoff"]
    assert "klein/text-swap" in mode["handoff"]
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_still_studio"


def test_still_studio_format_wires_latent_hint_prefix_context() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZImageFormat" in types
    assert "EmptyFlux2LatentImage" in types
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZImageFormat")
    latent = next(
        node for node in graph["nodes"] if node.get("type") == "EmptyFlux2LatentImage"
    )
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert _src(graph, latent, "width")["id"] == fmt["id"]
    assert _src(graph, latent, "height")["id"] == fmt["id"]
    assert _src(graph, latent, "batch_size")["id"] == fmt["id"]
    assert _src(graph, enh, "duration_hint")["id"] == fmt["id"]
    assert _src(graph, enh, "context")["id"] == fmt["id"]
    assert _src(graph, save, "filename_prefix")["id"] == fmt["id"]
    values = list(fmt.get("widgets_values") or [])
    assert values[0] == "16:9 LTX feeder (1280×704)"
    assert values[1] == "none"
    assert values[2] == 1280
    assert values[3] == 704
    assert values[4] == 1


def test_still_studio_enhance_and_app_widgets() -> None:
    graph = _load()
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    values = list(enh["widgets_values"] or [])
    assert values[0] == "custom"
    assert values[2] is True
    assert values[3] == "t2i"
    assert values[6] == "klein/still-studio"
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert names[:7] == [
        "quality",
        "sample",
        "prompt",
        "format",
        "style",
        "enhance",
        "look",
    ]
    assert "seed" in names
    assert "width" in names
    assert "height" in names
    assert "batch_size" in names
    assert "unet_name" in names
    assert names.index("width") > names.index("seed")
    fmt = next(n for n in graph["nodes"] if n.get("type") == "EZImageFormat")
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    width_nodes = [
        entry[0] for entry in graph["extra"]["linearData"]["inputs"] if entry[1] == "width"
    ]
    assert width_nodes == [fmt["id"]]
    assert latent["id"] not in width_nodes
    spec = STAMP_SPECS["klein/still-studio"]
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    assert "Format / platform" in labels
    assert "Look recipe" in labels


def test_still_studio_optional_ref_does_not_require_image() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZOptionalImage" in types
    assert "EZKleinRefCanvas" in types
    opt = next(n for n in graph["nodes"] if n.get("type") == "EZOptionalImage")
    assert (opt.get("widgets_values") or [""])[0] == ""
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert "filename" in names


def test_still_studio_json_roundtrip() -> None:
    path = lab_json("klein/still-studio.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["extra"]["workflowRendererVersion"] == "Vue-corrected"
    assert raw["extra"]["lab_rel"] == "klein/still-studio"
