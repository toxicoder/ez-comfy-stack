"""Native TRELLIS.2 lab graph: INT8, upsample 1024, SaveGLB, no Pixal3D."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
BANNED = ("Pixal3D", "pixal3d", "MiniMax", "MagCache")
# ComfyUI v0.43.0 Trellis2UpsampleStage: target_resolution is an INT bounded
# 1024-2048 in steps of 128. 512 and 256 are not accepted values at all.
UPSAMPLE_TARGET_RESOLUTION = 1024
# MeshToFile3D has no widgets and is not an output node; SaveGLB is the node
# that writes the .glb, so the chain must terminate on it.
SAVE_GLB_PREFIX = "3d/trellis2"


def _link_origin(graph: dict[str, Any], link_id: int) -> dict[str, Any]:
    """Node a link id originates from.

    Args:
        graph: Parsed Comfy workflow.
        link_id: ``links[][0]`` id referenced by a node input slot.

    Returns:
        The originating node dict.
    """
    for link in graph.get("links") or []:
        if int(link[0]) == link_id:
            origin_id = int(link[1])
            nodes: list[dict[str, Any]] = graph["nodes"]
            return next(node for node in nodes if int(node["id"]) == origin_id)
    raise AssertionError(f"link {link_id} is not in graph {graph.get('id')}")


def test_klein_trellis2_graph_contract() -> None:
    graph: dict[str, Any] = json.loads(lab_json("3d/trellis2.json").read_text(encoding="utf-8"))
    assert graph["id"] == "trellis2"
    assert graph["extra"].get("lab_rel") == "3d/trellis2"
    assert "3d" in lab_json("3d/trellis2.json").parts
    extra = graph["extra"]
    assert extra["lab_app_mode"]["occupancy"] == "trellis"
    assert extra["lab_app_mode"]["lane"] == "3d"
    assert extra["lab_app_mode"]["default_view"] == "app"
    assert extra["lab_trellis"]["unet"] == "trellis_2_int8_convrot.safetensors"
    assert extra["lab_trellis"]["resolution"] == UPSAMPLE_TARGET_RESOLUTION
    assert extra["lab_trellis"]["native_only"] is True
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob, needle
    assert "trellis_2_int8_convrot.safetensors" in blob
    assert "dino_v3_vit_l.safetensors" in blob
    types = {n.get("type") for n in graph["nodes"]}
    for needed in (
        "LoadImage",
        "EZUnloadModels",
        "CLIPVisionLoader",
        "UNETLoader",
        "Trellis2Conditioning",
        "Trellis2ShapeStage",
        "Trellis2UpsampleStage",
        "Trellis2TextureStage",
        "MeshToFile3D",
        "SaveGLB",
    ):
        assert needed in types, needed
    upsample = next(n for n in graph["nodes"] if n.get("type") == "Trellis2UpsampleStage")
    widgets = upsample.get("widgets_values") or []
    assert len(widgets) == 1, widgets
    target_resolution = widgets[0]
    assert isinstance(target_resolution, int) and not isinstance(target_resolution, bool)
    assert target_resolution == UPSAMPLE_TARGET_RESOLUTION
    to_glb = next(n for n in graph["nodes"] if n.get("type") == "MeshToFile3D")
    assert to_glb.get("widgets_values") == []
    save_glb = next(n for n in graph["nodes"] if n.get("type") == "SaveGLB")
    assert save_glb.get("widgets_values") == [SAVE_GLB_PREFIX]
    save_input = (save_glb.get("inputs") or [])[0]
    assert _link_origin(graph, int(save_input["link"]))["id"] == to_glb["id"]
    assert "occupancy enter trellis" in extra["lab_note"]


def test_download_3d_manifest_is_native_int8() -> None:
    text = (ROOT / "config" / "model-manifest.yaml").read_text(encoding="utf-8")
    assert "Comfy-Org__TRELLIS.2_trellis2" in text
    assert "trellis_2_int8_convrot.safetensors" in text
    assert "dino_v3_vit_l.safetensors" in text
    assert "ss_flow_img_dit_xl.safetensors" not in text
