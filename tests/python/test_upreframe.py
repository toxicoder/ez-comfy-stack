"""stills/upscale-reframe: Klein 4B upscale + aspect reframe of a loaded still.

Hermetic: stdlib + JSON + in-tree test helpers. No Comfy, Docker, or GPU. The
graph reframes by regenerating a blank Format-sized canvas guided by the
encoded source, so these tests pin the shape that makes that work: the loaded
picker is first and wired, the canvas follows Format, the source reaches the
sampler as a ReferenceLatent, and one delivery upscale closes the chain.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
CUSTOM = ROOT / "custom_nodes"
for _extra in (str(PY), str(CUSTOM)):
    if _extra not in sys.path:
        sys.path.insert(0, _extra)

from _lab_layout import (  # noqa: E402
    CHECK_TYPE,
    QUALITY_TYPE,
    group_overlap_hits,
    node_overlap_hits,
    node_pos,
    operator_note,
)
from _lab_paths import lab_json, load_lab_graph  # noqa: E402
from _stamp_app_mode import (  # noqa: E402
    STAMP_SPECS,
    infer_suite_inputs,
    infer_suite_outputs,
    stamp_suite_graph,
)
from _wire_format import (  # noqa: E402
    FORMAT_SCOPE,
    KLEIN_GENERIC,
    format_kind,
    pick_still_format,
)
from _wire_upscale import (  # noqa: E402
    DEFAULT_UPSCALE,
    UPSCALE_TYPE,
    upscale_in_scope,
    wire_upscale,
)
from ez_image.formats import CUSTOM_ID, SIZE_MODE_MATCH  # noqa: E402

REL = "stills/upscale-reframe"
SAVE_PREFIX = "ez_reframe"
CANVAS = (1280, 704)
PLUMBING_WIDGETS = ("steps", "cfg", "scheduler", "denoise", "sample_type")


def _graph() -> dict[str, Any]:
    return load_lab_graph(lab_json(REL))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _input(node: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in node["inputs"] if item["name"] == name)


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the node feeding one input, or fail when it is unlinked."""
    inp = _input(node, name)
    assert inp.get("link") is not None, (node["type"], name)
    origin = int(_link_map(graph)[int(inp["link"])][1])
    return _by_id(graph)[origin]


def _of_type(graph: dict[str, Any], ntype: str) -> list[dict[str, Any]]:
    return [node for node in graph["nodes"] if node.get("type") == ntype]


def test_upreframe_identity_occupancy_and_stamp_spec() -> None:
    graph = _graph()
    extra = graph["extra"]
    assert graph["id"] == "upscale-reframe"
    assert extra["lab_rel"] == REL
    assert extra["workflowRendererVersion"] == "Vue-corrected"
    mode = extra["lab_app_mode"]
    assert mode["lane"] == "produce"
    assert mode["occupancy"] == "klein"
    assert mode["default_view"] == "app"
    spec = STAMP_SPECS[REL]
    assert spec["lane"] == "produce"
    assert spec["occupancy"] == "klein"


def test_upreframe_picker_is_first_and_wired() -> None:
    """The required image picker leads linearData, Quality follows."""
    graph = _graph()
    inputs = graph["extra"]["linearData"]["inputs"]
    names = [entry[1] for entry in inputs]
    assert names[0] == "image"
    assert names[1] == "quality"
    picker = _by_id(graph)[int(inputs[0][0])]
    assert picker["type"] == "LoadImage"
    assert _of_type(graph, "LoadImage") == [picker]
    # Wired: the pick feeds the reference chain, so Queue cannot ignore it.
    assert [link for link in picker["outputs"][0]["links"]], picker["type"]
    # The App shows the picker but keeps the sampler plumbing hidden: Quality
    # and Check models carry the look decisions instead.
    assert not [name for name in names if name in PLUMBING_WIDGETS]


def test_upreframe_canvas_follows_format() -> None:
    """Format owns the canvas: in scope, Custom default, and it drives latent."""
    graph = _graph()
    assert REL in KLEIN_GENERIC
    assert REL in FORMAT_SCOPE
    assert format_kind(REL) == "still"
    fmt_nodes = _of_type(graph, "EZImageFormat")
    assert len(fmt_nodes) == 1
    fmt = fmt_nodes[0]
    values = list(fmt.get("widgets_values") or [])
    # [format, look, width, height, batch, size_mode]
    assert values[0] == "Custom"
    assert values[1] == "none"
    assert values[5] == SIZE_MODE_MATCH
    assert (values[2], values[3]) == CANVAS
    assert pick_still_format(REL, *CANVAS).id == CUSTOM_ID
    sampler = _of_type(graph, "KSampler")[0]
    latent = _src(graph, sampler, "latent_image")
    assert latent["type"] == "EmptyFlux2LatentImage"
    assert tuple(list(latent["widgets_values"] or [])[:2]) == CANVAS
    for slot, name in enumerate(("width", "height", "batch_size")):
        assert _src(graph, latent, name) is fmt, name


def test_upreframe_reframe_is_a_blank_canvas_with_a_source_reference() -> None:
    """Source plate reaches the sampler as ReferenceLatent, not as a stretch."""
    graph = _graph()
    sampler = _of_type(graph, "KSampler")[0]
    load = _of_type(graph, "LoadImage")[0]
    canvas = _src(graph, sampler, "latent_image")
    assert canvas["type"] == "EmptyFlux2LatentImage"
    reference = _src(graph, sampler, "positive")
    assert reference["type"] == "ReferenceLatent"
    plate = _src(graph, reference, "latent")
    assert plate["type"] == "VAEEncode"
    snapped = _src(graph, plate, "pixels")
    assert snapped["type"] == "EZSnapImage"
    assert _src(graph, plate, "vae")["type"] == "VAELoader"
    assert _src(graph, snapped, "image") is load
    positive = _src(graph, reference, "conditioning")
    assert positive["type"] == "CLIPTextEncode"
    enhance = _src(graph, positive, "text")
    assert enhance["type"] == "EZKleinPromptEnhance"
    assert enhance["widgets_values"][2] is True
    # Both conditioning links exist and denoise stays inside (0, 1]: the canvas
    # regenerates instead of forwarding a scaled copy of the source.
    assert sampler["inputs"][2]["link"] is not None
    denoise = float(sampler["widgets_values"][6])
    steps = int(sampler["widgets_values"][2])
    assert 0.0 < denoise <= 1.0
    assert steps == 8
    assert _src(graph, sampler, "negative")["type"] == "CLIPTextEncode"


def test_upreframe_describe_and_negative_enhance_stay_optional() -> None:
    graph = _graph()
    describe = _of_type(graph, "EZImageDescribe")
    assert len(describe) == 1
    assert _src(graph, describe[0], "image") is _of_type(graph, "LoadImage")[0]
    assert describe[0]["widgets_values"] == [False]
    negative = _of_type(graph, "EZNegativePromptEnhance")
    assert len(negative) == 1
    assert _src(graph, negative[0], "positive")["type"] == "EZKleinPromptEnhance"


def test_upreframe_delivery_chain_ends_in_one_upscale_and_one_save() -> None:
    graph = _graph()
    assert upscale_in_scope(REL) is True
    saves = _of_type(graph, "SaveImage")
    assert len(saves) == 1
    assert saves[0]["widgets_values"][0] == SAVE_PREFIX
    upscales = _of_type(graph, UPSCALE_TYPE)
    assert len(upscales) == 1
    upscale = upscales[0]
    assert upscale["widgets_values"][0] == DEFAULT_UPSCALE
    assert _src(graph, upscale, "image")["type"] == "VAEDecode"
    assert _src(graph, saves[0], "images") is upscale
    # Already wired: a second pass of the helper must not add a node.
    assert wire_upscale(copy.deepcopy(graph), REL) is False


def test_upreframe_layout_keeps_gaps_and_the_header_row() -> None:
    graph = _graph()
    assert node_overlap_hits(graph) == []
    assert group_overlap_hits(graph) == []
    note = operator_note(graph)
    assert note is not None
    note_x, note_y = node_pos(note)
    assert (note_x, note_y) == (40.0, 80.0)
    header = [node for node in graph["nodes"] if node.get("type") in {QUALITY_TYPE, CHECK_TYPE}]
    assert {node.get("title") for node in header} == {"Quality", "Check models"}
    for node in header:
        assert node_pos(node)[1] == note_y
        assert node_pos(node)[0] > note_x


def test_upreframe_stamping_is_a_fixed_point() -> None:
    """The shipped JSON is already stamped: re-stamping changes nothing."""
    graph = _graph()
    spec = STAMP_SPECS[REL]
    inferred = infer_suite_inputs(graph, spec)
    stamped = graph["extra"]["linearData"]["inputs"]
    assert [(int(entry[0]), entry[1]) for entry in inferred] == [
        (int(entry[0]), entry[1]) for entry in stamped
    ]
    assert infer_suite_outputs(graph, spec) == [
        int(nid) for nid in graph["extra"]["linearData"]["outputs"]
    ]
    restamped = stamp_suite_graph(copy.deepcopy(graph))
    assert (
        restamped["extra"]["linearData"]["inputs"]
        == graph["extra"]["linearData"]["inputs"]
    )
    assert (
        restamped["extra"]["linearData"]["outputs"]
        == graph["extra"]["linearData"]["outputs"]
    )
    assert restamped["extra"]["lab_app_mode"] == graph["extra"]["lab_app_mode"]
