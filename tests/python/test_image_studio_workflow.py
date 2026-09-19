"""klein/image-studio graph: creator modes wired into enhance, prefix, optional ref."""

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
from _stamp_app_mode import STAMP_SPECS, infer_suite_inputs  # noqa: E402
from ez_image.modes import EZImageMode, default_mode_label, load_modes  # noqa: E402


def _load() -> dict[str, Any]:
    return load_lab_graph(lab_json("klein/image-studio.json"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    link_id = int(inp["link"])
    origin = int(_link_map(graph)[link_id][1])
    return _by_id(graph)[origin]


def test_image_studio_identity_and_app_mode() -> None:
    graph = _load()
    extra = graph["extra"]
    assert extra.get("lab_rel") == "klein/image-studio"
    assert graph.get("id") == "image-studio"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    assert mode["default_view"] == "app"
    assert "klein/still-studio" in mode["handoff"]
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_gen_photoreal"


def test_image_studio_mode_wires_context_enhance_prefix() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZImageMode" in types
    assert "EZImageFormat" in types
    assert "EZOptionalImage" in types
    assert "EZKleinRefCanvas" in types
    mode = next(node for node in graph["nodes"] if node.get("type") == "EZImageMode")
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZImageFormat")
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert _src(graph, mode, "context")["id"] == fmt["id"]
    assert _src(graph, enh, "context")["id"] == mode["id"]
    assert _src(graph, enh, "mode")["id"] == mode["id"]
    assert _src(graph, save, "filename_prefix")["id"] == mode["id"]
    values = list(mode.get("widgets_values") or [])
    assert values[0] == "Generate"
    assert values[1] == default_mode_label()


def test_image_studio_empty_ref_is_valid() -> None:
    graph = _load()
    opt = next(n for n in graph["nodes"] if n.get("type") == "EZOptionalImage")
    assert (opt.get("widgets_values") or [""])[0] == ""
    packed = EZImageMode().run("Generate", "Photoreal still")
    assert packed["result"][1] == "t2i"
    assert packed["result"][2].startswith("ez_")
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert "filename" in names
    assert "category" in names
    assert "mode" in names


def test_image_studio_catalog_has_one_hundred_modes() -> None:
    assert len(load_modes()) == 100
    spec = STAMP_SPECS["klein/image-studio"]
    graph = _load()
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    assert "Creator mode" in labels
    assert "Mode category" in labels
    assert "Example / reference (optional)" in labels


def test_image_studio_json_roundtrip() -> None:
    path = lab_json("klein/image-studio.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["extra"]["workflowRendererVersion"] == "Vue-corrected"
    assert raw["extra"]["lab_rel"] == "klein/image-studio"
    blob = json.dumps(raw)
    assert "MiniMax" not in blob
    unet = next(node for node in raw["nodes"] if node.get("type") == "UNETLoader")
    clip = next(node for node in raw["nodes"] if node.get("type") == "CLIPLoader")
    vae = next(node for node in raw["nodes"] if node.get("type") == "VAELoader")
    assert unet["widgets_values"][0] == "flux-2-klein-4b-fp8.safetensors"
    assert clip["widgets_values"][0] == "qwen_3_4b.safetensors"
    assert vae["widgets_values"][0] == "flux2-vae.safetensors"
