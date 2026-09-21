"""motion/av/clip-chain: four LTX beats, last-frame continuity, occupancy ltx."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_paths import lab_json  # noqa: E402
from _ltx_app_duration import FILM_KEEP_RELS, FRAMES_APP, ltx_length  # noqa: E402
from _stamp_app_mode import (  # noqa: E402
    STAMP_SPECS,
    infer_suite_inputs,
    infer_suite_outputs,
    stamp_suite_graph,
)

REL = "motion/av/clip-chain"


def _load() -> dict[str, Any]:
    return json.loads(lab_json(REL).read_text(encoding="utf-8"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    origin = int(_link_map(graph)[int(inp["link"])][1])
    return _by_id(graph)[origin]


def _vhs_prefix(node: dict[str, Any]) -> str:
    values = node.get("widgets_values") or {}
    if isinstance(values, dict):
        return str(values.get("filename_prefix") or "")
    return ""


def test_clip_chain_identity_occupancy_and_stamp_spec() -> None:
    graph = _load()
    extra = graph["extra"]
    assert extra.get("lab_rel") == REL
    assert graph.get("id") == "clip-chain"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "ltx"
    assert mode["default_view"] == "app"
    spec = STAMP_SPECS[REL]
    assert spec["clip_chain_widgets"] is True
    assert spec["occupancy"] == "ltx"
    assert spec["lane"] == "produce"
    assert REL not in FILM_KEEP_RELS


def test_clip_chain_has_no_image_from_batch_or_hero_frames() -> None:
    graph = _load()
    types = {node.get("type") for node in graph["nodes"]}
    assert "ImageFromBatch" not in types
    assert "EZClipLastFrame" in types
    assert "EZClipConcat" in types
    assert "EZFilmConcat" not in types
    assert "EZUnloadModels" not in types
    assert "EZKleinPromptEnhance" not in types
    prefixes = [
        str((node.get("widgets_values") or [""])[0])
        for node in graph["nodes"]
        if node.get("type") == "SaveImage"
    ]
    assert prefixes
    assert all(not item.startswith("ez_ltx_hero_frames") for item in prefixes)
    assert "ez_ltx_hero_frames" not in json.dumps(graph)
    assert all(item.endswith("_last") for item in prefixes)


def test_clip_chain_unique_vhs_prefixes_and_concat() -> None:
    graph = _load()
    vhs = [
        node for node in graph["nodes"] if node.get("type") == "VHS_VideoCombine"
    ]
    prefixes = sorted(_vhs_prefix(node) for node in vhs)
    assert prefixes == [
        "ez_clip_b01_ltx_video",
        "ez_clip_b02_ltx_video",
        "ez_clip_b03_ltx_video",
        "ez_clip_b04_ltx_video",
    ]
    assert len(set(prefixes)) == 4
    concat = next(node for node in graph["nodes"] if node.get("type") == "EZClipConcat")
    for index, node in enumerate(sorted(vhs, key=_vhs_prefix), start=1):
        assert _src(graph, concat, f"clip_{index:02d}") is node


def test_clip_chain_format_family_and_all_four_i2v_sizes() -> None:
    graph = _load()
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZVideoFormat")
    values = list(fmt.get("widgets_values") or [])
    assert values[0] == "LTX-2.5"
    assert values[4] == "Match input"
    assert values[5] == "8 seconds"
    i2v = [
        node for node in graph["nodes"] if node.get("type") == "LTXVImgToVideo"
    ]
    assert len(i2v) == 4
    for node in i2v:
        assert _src(graph, node, "width") is fmt
        assert _src(graph, node, "height") is fmt
        assert ltx_length(node) == FRAMES_APP
    empty = [
        node for node in graph["nodes"] if node.get("type") == "LTXVEmptyLatentAudio"
    ]
    assert len(empty) == 1
    assert ltx_length(empty[0]) == FRAMES_APP
    blob = json.dumps(graph)
    assert "8 seconds, 24 fps" in blob


def test_clip_chain_last_frame_continuity() -> None:
    graph = _load()
    lasts = [
        node for node in graph["nodes"] if node.get("type") == "EZClipLastFrame"
    ]
    i2v = [
        node for node in graph["nodes"] if node.get("type") == "LTXVImgToVideo"
    ]
    assert len(lasts) == 4
    assert len(i2v) == 4
    gate = next(
        node for node in graph["nodes"] if node.get("type") == "EZDCCOccupancyGate"
    )
    assert gate["widgets_values"][0] == "ltx"
    i2v_sorted = sorted(i2v, key=lambda node: int(node["id"]))
    lasts_sorted = sorted(lasts, key=lambda node: int(node["id"]))
    assert _src(graph, i2v_sorted[0], "image") is gate
    for index in range(1, 4):
        assert _src(graph, i2v_sorted[index], "image") is lasts_sorted[index - 1]


def test_clip_chain_app_widgets_hide_occupancy_and_keep_unique_labels() -> None:
    graph = _load()
    linear = graph["extra"]["linearData"]
    names = [entry[1] for entry in linear["inputs"]]
    assert names[0] == "image"
    assert "required_mode" not in names
    assert "style" not in names
    assert names.count("sample") == 1
    assert names.count("prompt") == 4
    assert names.count("value") == 4
    labels = [
        (entry[2] or {}).get("label") if len(entry) > 2 else entry[1]
        for entry in linear["inputs"]
    ]
    assert labels[0] in {"Start image", "Start frame"}
    assert "Beat 1 prompt" in labels
    assert "Beat 2 prompt" in labels
    assert "Beat 3 prompt" in labels
    assert "Beat 4 prompt" in labels
    assert len(labels) == len(set(labels)), labels
    types = [
        _by_id(graph)[int(nid)].get("type") for nid in linear["outputs"]
    ]
    assert types.count("VHS_VideoCombine") == 4
    assert types.count("EZClipConcat") == 1
    assert types.count("SaveImage") == 4
    assert types.index("VHS_VideoCombine") < types.index("EZClipConcat")
    assert types.index("EZClipConcat") < types.index("SaveImage")


def test_clip_chain_infer_matches_stamped_linear_data() -> None:
    graph = _load()
    spec = STAMP_SPECS[REL]
    inferred = infer_suite_inputs(graph, spec)
    stamped = graph["extra"]["linearData"]["inputs"]
    assert [(int(a[0]), a[1]) for a in inferred] == [
        (int(b[0]), b[1]) for b in stamped
    ]
    assert infer_suite_outputs(graph, spec) == [
        int(nid) for nid in graph["extra"]["linearData"]["outputs"]
    ]
    restamped = stamp_suite_graph(copy.deepcopy(graph))
    assert restamped["extra"]["linearData"]["inputs"] == stamped
    assert restamped["extra"]["linearData"]["outputs"] == graph["extra"]["linearData"][
        "outputs"
    ]


def test_clip_chain_shared_primitives_and_enhance_on() -> None:
    graph = _load()
    seed = next(
        node
        for node in graph["nodes"]
        if node.get("type") == "PrimitiveNode" and node.get("title") == "Seed"
    )
    rewrite = next(
        node
        for node in graph["nodes"]
        if node.get("type") == "PrimitiveNode"
        and node.get("title") == "Rewrite prompt"
    )
    samplers = [node for node in graph["nodes"] if node.get("type") == "KSampler"]
    assert len(samplers) == 4
    for node in samplers:
        assert _src(graph, node, "seed") is seed
    enhances = [
        node for node in graph["nodes"] if node.get("type") == "EZLTXPromptEnhance"
    ]
    assert [node.get("title") for node in sorted(enhances, key=lambda n: n["title"])] == [
        "Beat 1",
        "Beat 2",
        "Beat 3",
        "Beat 4",
    ]
    for node in enhances:
        assert _src(graph, node, "enhance") is rewrite
        values = list(node.get("widgets_values") or [])
        assert values[2] is True
        assert values[3] == "i2v"
        assert values[4] == "8 seconds, 24 fps"
