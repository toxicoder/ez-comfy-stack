"""Native TRELLIS.2 lab graph: INT8, 512, no Pixal3D, occupancy trellis."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
BANNED = ("Pixal3D", "pixal3d", "MiniMax", "MagCache")


def test_klein_trellis2_graph_contract() -> None:
    graph = json.loads(lab_json("klein-trellis2-lab-example.json").read_text(encoding="utf-8"))
    assert graph["id"] == "klein-trellis2-lab-example"
    assert lab_json("klein-trellis2-lab-example.json").parent.name == "optional"
    extra = graph["extra"]
    assert extra["lab_app_mode"]["occupancy"] == "trellis"
    assert extra["lab_app_mode"]["lane"] == "optional"
    assert extra["lab_trellis"]["unet"] == "trellis_2_int8_convrot.safetensors"
    assert extra["lab_trellis"]["resolution"] == 512
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
    ):
        assert needed in types, needed
    upsample = next(n for n in graph["nodes"] if n.get("type") == "Trellis2UpsampleStage")
    assert "512" in [str(v) for v in (upsample.get("widgets_values") or [])]
    assert "occupancy enter trellis" in extra["lab_note"]


def test_download_3d_manifest_is_native_int8() -> None:
    text = (ROOT / "config" / "model-manifest.yaml").read_text(encoding="utf-8")
    assert "Comfy-Org__TRELLIS.2_trellis2" in text
    assert "trellis_2_int8_convrot.safetensors" in text
    assert "dino_v3_vit_l.safetensors" in text
    assert "ss_flow_img_dit_xl.safetensors" not in text
