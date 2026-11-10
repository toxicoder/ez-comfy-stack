"""Native TRELLIS.2 lab graph: INT8, upsample 1024, SaveGLB, no Pixal3D."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
BANNED = ("Pixal3D", "pixal3d", "MiniMax", "MagCache")
# ComfyUI v0.43.0 Trellis2UpsampleStage: target_resolution is an INT bounded
# 1024-2048 in steps of 128. 512 and 256 are not accepted values at all.
UPSAMPLE_TARGET_RESOLUTION = 1024
# MeshToFile3D has no widgets and is not an output node; SaveGLB is the node
# that writes the .glb, so the chain must terminate on it. The prefix follows
# the same assets/objects/_lab-<slug>/<stem> convention as the four sibling 3d
# apps, so every mesh lands in the one output tree the catalog walks and the
# MCP export_glb verb reads (it defaults to ${COMFY_OUTPUT_DIR}/assets).
SAVE_GLB_PREFIX = "assets/objects/_lab-trellis2/mesh"
SAVE_GLB_PREFIX_RE = re.compile(r"assets/objects/_lab-[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*\Z")
# The four siblings, asserted live so the convention cannot silently drift.
SIBLING_SAVE_GLB_PREFIXES: dict[str, str] = {
    "3d/still-to-mesh.json": "assets/objects/_lab-mug/mesh",
    "3d/blockout-mesh.json": "assets/objects/_lab-blockout/blockout",
    "3d/shot-to-prop.json": "assets/objects/_lab-shot-prop/prop",
    "3d/prop-variants.json": "assets/objects/_lab-variants/prop",
}


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


def _save_glb_prefix(graph: dict[str, Any]) -> str:
    """The single ``filename_prefix`` widget on the graph's only SaveGLB node.

    Args:
        graph: Parsed Comfy workflow.

    Returns:
        The widget value written verbatim under ComfyUI's output root.
    """
    nodes = [n for n in graph["nodes"] if n.get("type") == "SaveGLB"]
    assert len(nodes) == 1, [n.get("id") for n in nodes]
    widgets = nodes[0].get("widgets_values") or []
    assert len(widgets) == 1, widgets
    prefix = widgets[0]
    assert isinstance(prefix, str), prefix
    return prefix


def test_save_glb_prefix_matches_the_sibling_convention() -> None:
    """One predictable output directory for every mesh the 3d lane mints.

    A prefix outside ``assets/objects/_lab-<slug>/<stem>`` opens a second
    top-level bucket in the output tree, which ``ez_outputs/catalog.py`` and the
    MCP ``export_glb`` verb (default ``${COMFY_OUTPUT_DIR}/assets``) both miss.
    The graph path ``3d/trellis2`` is app identity and must not double as the
    output path.
    """
    graph: dict[str, Any] = json.loads(lab_json("3d/trellis2.json").read_text(encoding="utf-8"))
    prefix = _save_glb_prefix(graph)
    assert prefix == SAVE_GLB_PREFIX
    assert SAVE_GLB_PREFIX_RE.fullmatch(prefix), prefix
    assert not prefix.startswith("3d/"), "the lane path is a graph path, not an output path"
    assert graph["extra"]["lab_trellis"]["save_prefix"] == prefix
    for rel, expected in SIBLING_SAVE_GLB_PREFIXES.items():
        sibling: dict[str, Any] = json.loads(lab_json(rel).read_text(encoding="utf-8"))
        sibling_prefix = _save_glb_prefix(sibling)
        assert sibling_prefix == expected, rel
        assert SAVE_GLB_PREFIX_RE.fullmatch(sibling_prefix), f"{rel}: {sibling_prefix}"


def test_operator_note_names_the_real_landing_path() -> None:
    """The note tells the operator where the mesh lands, so it cannot lie.

    The prefix moved out of ``output/3d/``; a stale note would send the
    operator looking in a bucket the graph no longer writes to.
    """
    graph: dict[str, Any] = json.loads(lab_json("3d/trellis2.json").read_text(encoding="utf-8"))
    expected = f"output/{_save_glb_prefix(graph)}_NNNNN_.glb"
    note = graph["extra"]["lab_note"]
    assert expected in note
    assert "output/3d/" not in note
    widgets = next(n for n in graph["nodes"] if n.get("type") == "Note").get("widgets_values") or []
    assert note in widgets, "the Note node and extra.lab_note carry the same text"


def test_download_3d_manifest_is_native_int8() -> None:
    text = (ROOT / "config" / "model-manifest.yaml").read_text(encoding="utf-8")
    assert "Comfy-Org__TRELLIS.2_trellis2" in text
    assert "trellis_2_int8_convrot.safetensors" in text
    assert "dino_v3_vit_l.safetensors" in text
    assert "ss_flow_img_dit_xl.safetensors" not in text
