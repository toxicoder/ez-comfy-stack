"""3d-lane Studio Apps: blockout, shot-to-prop, prop-variants.

Hermetic: stdlib + the repo's own ``_lab_paths`` helpers over the shipped
graphs in ``workflows/_lab/3d``. Asserts the Studio App stamp, the exact
TRELLIS.2 node chain per app, the ``SaveGLB`` terminal and which node may feed
it, the
occupancy guard in the image path, and the catalogued model pins. No network,
no Docker, no GPU, no ComfyUI import.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from _lab_paths import lab_json, load_lab_graph

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "model-manifest.yaml"

# Non-catalog model families must never appear in a promoted 3d graph.
BANNED = ("MiniMax", "Seedance", "Kling", "z_image_turbo", "klein-9b")

UNET = "trellis_2_int8_convrot.safetensors"
CLIP_VISION = "dino_v3_vit_l.safetensors"
SHAPE_VAE = "trellis_2_shape_vae_bf16.safetensors"
TEXTURE_VAE = "trellis_2_texture_vae_bf16.safetensors"
ALLOWED_PINS = frozenset({UNET, CLIP_VISION, SHAPE_VAE, TEXTURE_VAE})
# Only widget 0 of each loader is a filename; UNETLoader widget 1 is the
# weight-dtype combo ("default") and is not a model pin.
LOADER_TYPES = frozenset({"CLIPVisionLoader", "UNETLoader", "VAELoader"})
SOURCE_TYPES = frozenset({"LoadImage", "EZDCCLoadStillPack", "EZDCCLoadGuideStill"})
MODEL_FILE_SUFFIXES = (".safetensors", ".ckpt", ".pt", ".bin")

# ComfyUI v0.43.0 Trellis2UpsampleStage: target_resolution is an INT bounded
# 1024-2048 in steps of 128; these apps run the 1024 floor.
UPSAMPLE_TARGET_RESOLUTION = 1024

# The three apps this file owns. still-to-mesh is owned by its own test file.
NEW_APPS = ("blockout-mesh", "shot-to-prop", "prop-variants")
TEXTURED_APPS = ("shot-to-prop", "prop-variants")
# Every 3d graph, used only for the rules the whole lane must honour.
ALL_3D_APPS = ("trellis2", *NEW_APPS, "still-to-mesh")
# still-to-mesh is mid-change elsewhere, so the widget-level pin audit covers
# the graphs this file owns plus the promoted trellis2 graph.
PIN_AUDIT_APPS = ("trellis2", *NEW_APPS)

SHARED_CHROME = frozenset(
    {
        "Note",
        "EZDCCOccupancyGate",
        "EZUnloadModels",
        "CLIPVisionLoader",
        "UNETLoader",
        "VAELoader",
        "Trellis2Conditioning",
        "EmptyTrellis2LatentStructure",
        "KSampler",
        "VaeDecodeStructureTrellis2",
        "Trellis2ShapeStage",
        "VaeDecodeShapeTrellis",
        "SaveGLB",
        "EZQuality",
        "EZModelCheck",
    }
)
# MeshToFile3D serializes one batch item only, so a batched App must feed
# SaveGLB the MESH directly instead of routing through it.
SINGLE_ITEM_CONVERTER = frozenset({"MeshToFile3D"})
TEXTURE_PASS = frozenset(
    {
        "Trellis2UpsampleStage",
        "Trellis2TextureStage",
        "VaeDecodeTextureTrellis",
        "PaintMesh",
    }
)
EXPECTED_TYPES: dict[str, frozenset[str]] = {
    "blockout-mesh": SHARED_CHROME | SINGLE_ITEM_CONVERTER | {"EZDCCLoadStillPack"},
    "shot-to-prop": SHARED_CHROME
    | TEXTURE_PASS
    | SINGLE_ITEM_CONVERTER
    | {"EZDCCLoadGuideStill", "EZDCCPreviewGuideLayer"},
    "prop-variants": SHARED_CHROME | TEXTURE_PASS | {"LoadImage"},
}
# The batched App writes one .glb per batch item, so it skips MeshToFile3D.
MESH_PRODUCER = {
    "blockout-mesh": "MeshToFile3D",
    "shot-to-prop": "MeshToFile3D",
    "prop-variants": "PaintMesh",
}
SAVE_PREFIX = {
    "blockout-mesh": "assets/objects/_lab-blockout/blockout",
    "shot-to-prop": "assets/objects/_lab-shot-prop/prop",
    "prop-variants": "assets/objects/_lab-variants/prop",
}
SOURCE_TYPE = {
    "blockout-mesh": "EZDCCLoadStillPack",
    "shot-to-prop": "EZDCCLoadGuideStill",
    "prop-variants": "LoadImage",
}
EXPECTED_HANDOFF = {
    "blockout-mesh": ["3d/trellis2"],
    "shot-to-prop": ["3d/prop-variants"],
    # Prop variants is the end of the prop line: nothing to hand on to.
    "prop-variants": [],
}
BATCH_SIZE = {"blockout-mesh": 1, "shot-to-prop": 1, "prop-variants": 4}
TEXTURELESS_PINS = frozenset({UNET, CLIP_VISION, SHAPE_VAE})
EXPECTED_PINS: dict[str, frozenset[str]] = {
    "trellis2": ALLOWED_PINS,
    "blockout-mesh": TEXTURELESS_PINS,
    "shot-to-prop": ALLOWED_PINS,
    "prop-variants": ALLOWED_PINS,
}


def _image_source(graph: dict[str, Any]) -> dict[str, Any]:
    """The single image-producing source node of a 3d printer.

    Args:
        graph: Parsed workflow.

    Returns:
        The source node dict.
    """
    hits: list[dict[str, Any]] = [
        node for node in graph["nodes"] if node.get("type") in SOURCE_TYPES
    ]
    assert len(hits) == 1, (graph.get("id"), [node.get("type") for node in hits])
    return hits[0]


def _reaches(graph: dict[str, Any], start_id: int, target_id: int) -> bool:
    """Whether data flows from one node to another along the link list.

    Args:
        graph: Parsed workflow.
        start_id: Origin node id.
        target_id: Node id to look for downstream.

    Returns:
        True when a directed link path exists.
    """
    edges: dict[int, list[int]] = {}
    for link in graph.get("links") or []:
        edges.setdefault(int(link[1]), []).append(int(link[3]))
    seen: set[int] = set()
    pending = [start_id]
    while pending:
        current = pending.pop()
        if current == target_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(edges.get(current, []))
    return False


def _graph(stem: str) -> dict[str, Any]:
    """Parse one shipped 3d graph out of the cached lab tree.

    Args:
        stem: Graph basename without ``.json``.

    Returns:
        The parsed workflow dict.
    """
    path = lab_json(f"3d/{stem}.json")
    assert path.is_file(), path
    assert path.parent.name == "3d", path
    return load_lab_graph(path)


def _nodes_of(graph: dict[str, Any], ntype: str) -> list[dict[str, Any]]:
    """Every node of one type.

    Args:
        graph: Parsed workflow.
        ntype: Comfy node type.

    Returns:
        Matching node dicts.
    """
    return [node for node in graph["nodes"] if node.get("type") == ntype]


def _only_node(graph: dict[str, Any], ntype: str) -> dict[str, Any]:
    """The single node of one type, failing when the count is not exactly one.

    Args:
        graph: Parsed workflow.
        ntype: Comfy node type.

    Returns:
        The node dict.
    """
    hits = _nodes_of(graph, ntype)
    assert len(hits) == 1, (graph.get("id"), ntype, [node.get("id") for node in hits])
    return hits[0]


def _input_link(node: dict[str, Any], name: str) -> int | None:
    """Link id feeding one named input slot.

    Args:
        node: Node dict.
        name: Input slot name.

    Returns:
        The link id, or ``None`` when the slot is unwired or absent.
    """
    for slot in node.get("inputs") or []:
        if slot.get("name") == name:
            link = slot.get("link")
            return None if link is None else int(link)
    return None


def _origin_node(graph: dict[str, Any], link_id: int) -> dict[str, Any]:
    """Node a link id originates from.

    Args:
        graph: Parsed workflow.
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


def _is_in_link_graph(graph: dict[str, Any], node: dict[str, Any]) -> bool:
    """Whether a node both sends and receives a link, i.e. sits in a chain.

    Args:
        graph: Parsed workflow.
        node: Node dict from that graph.

    Returns:
        True when the node appears as both a link origin and a link target.
    """
    node_id = int(node["id"])
    links = graph.get("links") or []
    sends = any(int(link[1]) == node_id for link in links)
    receives = any(int(link[3]) == node_id for link in links)
    return sends and receives


def _loader_widgets(graph: dict[str, Any]) -> list[str]:
    """Every model filename a loader node carries.

    Arguments widget 0 is the filename on CLIPVisionLoader, UNETLoader, and
    VAELoader; the remaining widgets are dtypes and combos.

    Args:
        graph: Parsed workflow.

    Returns:
        Filename widget values, in node order.
    """
    found: list[str] = []
    for node in graph["nodes"]:
        if node.get("type") not in LOADER_TYPES:
            continue
        widgets = node.get("widgets_values") or []
        assert widgets, (graph.get("id"), node.get("type"), node.get("id"))
        first = widgets[0]
        assert isinstance(first, str), (graph.get("id"), node.get("type"), first)
        found.append(first)
        for extra_value in widgets[1:]:
            assert not (isinstance(extra_value, str) and extra_value.endswith(MODEL_FILE_SUFFIXES)), (
                graph.get("id"),
                node.get("type"),
                extra_value,
            )
    return found


@pytest.mark.parametrize("stem", NEW_APPS)
def test_app_identity(stem: str) -> None:
    """The graph id, lab_rel, renderer stamp, and version keys are its own."""
    graph = _graph(stem)
    assert graph["id"] == stem
    extra = graph["extra"]
    assert extra["lab_rel"] == f"3d/{stem}"
    assert extra["workflowRendererVersion"] == "Vue-corrected"
    assert graph.get("version") is not None
    assert graph.get("revision") is not None
    assert extra["lab_profile"] == f"3d/{stem}"
    assert str(extra["lab_note"]).strip()
    assert str(extra["lab_description"]).strip()


@pytest.mark.parametrize("stem", NEW_APPS)
def test_app_mode_stamp(stem: str) -> None:
    """Each app opens in App mode on the trellis occupancy in the 3d lane."""
    app_mode = _graph(stem)["extra"]["lab_app_mode"]
    assert app_mode["enabled"] is True
    assert app_mode["lane"] == "3d"
    assert app_mode["occupancy"] == "trellis"
    assert app_mode["default_view"] == "app"
    assert app_mode["handoff"] == EXPECTED_HANDOFF[stem]


@pytest.mark.parametrize("stem", NEW_APPS)
def test_linear_data_references_live_nodes(stem: str) -> None:
    """The App-mode linear inputs and outputs point at nodes that exist."""
    graph = _graph(stem)
    linear = graph["extra"]["linearData"]
    live = {int(node["id"]) for node in graph["nodes"]}
    rows = linear["inputs"]
    assert rows, graph["id"]
    widget_names: list[str] = []
    for row in rows:
        assert isinstance(row, list) and len(row) >= 2, row
        assert isinstance(row[0], int) and row[0] in live, row
        assert isinstance(row[1], str) and row[1], row
        widget_names.append(row[1])
    assert "quality" in widget_names
    outputs = linear["outputs"]
    assert outputs == [_only_node(graph, "SaveGLB")["id"]]
    assert all(isinstance(node_id, int) and node_id in live for node_id in outputs)


@pytest.mark.parametrize("stem", NEW_APPS)
def test_node_type_set_is_exact(stem: str) -> None:
    """The chain is exactly the nodes the app is meant to run, no more."""
    graph = _graph(stem)
    types = {str(node.get("type")) for node in graph["nodes"]}
    assert types == EXPECTED_TYPES[stem], types ^ EXPECTED_TYPES[stem]
    assert _only_node(graph, "EZDCCOccupancyGate")["widgets_values"] == ["trellis"]


@pytest.mark.parametrize("stem", NEW_APPS)
def test_image_source_is_the_designed_loader(stem: str) -> None:
    """The image chain starts on the source node this app was designed around."""
    graph = _graph(stem)
    source = _only_node(graph, SOURCE_TYPE[stem])
    assert source["id"] == _image_source(graph)["id"]
    conditioning = _only_node(graph, "Trellis2Conditioning")
    assert _reaches(graph, int(source["id"]), int(conditioning["id"])) is True


@pytest.mark.parametrize("stem", NEW_APPS)
def test_structure_batch_matches_the_design(stem: str) -> None:
    """The structure latent asks for exactly the batch the app promises."""
    graph = _graph(stem)
    empty = _only_node(graph, "EmptyTrellis2LatentStructure")
    widgets = empty.get("widgets_values") or []
    assert len(widgets) == 1, widgets
    batch_size = widgets[0]
    assert isinstance(batch_size, int) and not isinstance(batch_size, bool)
    assert batch_size == BATCH_SIZE[stem]
    assert graph["extra"]["lab_trellis"]["batch_size"] == BATCH_SIZE[stem]


@pytest.mark.parametrize("stem", NEW_APPS)
def test_chain_ends_on_save_glb(stem: str) -> None:
    """SaveGLB is the terminal writer, fed by the producer its batch needs.

    A single-item App converts through ``MeshToFile3D``. The batched App must
    not: that node keeps only batch item 0, so it would silently drop three of
    the four candidate meshes the App advertises.
    """
    graph = _graph(stem)
    save_glb = _only_node(graph, "SaveGLB")
    assert save_glb.get("widgets_values") == [SAVE_PREFIX[stem]]
    link = _input_link(save_glb, "mesh")
    assert link is not None
    origin = _origin_node(graph, link)
    assert origin.get("type") == MESH_PRODUCER[stem]
    to_glb = _nodes_of(graph, "MeshToFile3D")
    if MESH_PRODUCER[stem] == "MeshToFile3D":
        assert len(to_glb) == 1
        assert to_glb[0]["id"] == origin["id"]
        assert to_glb[0].get("widgets_values") == []
    else:
        assert to_glb == []
        assert graph["extra"]["lab_trellis"]["batch_size"] > 1
    # SaveGLB is the terminal node: nothing reads out of it.
    assert (save_glb.get("outputs") or []) == []


@pytest.mark.parametrize("stem", NEW_APPS)
def test_every_ksampler_is_conditioned(stem: str) -> None:
    """No sampler can queue without both its conditioning slots wired."""
    graph = _graph(stem)
    samplers = _nodes_of(graph, "KSampler")
    assert samplers
    for sampler in samplers:
        title = str(sampler.get("title"))
        assert _input_link(sampler, "positive") is not None, (graph["id"], title)
        assert _input_link(sampler, "negative") is not None, (graph["id"], title)
        assert _input_link(sampler, "model") is not None, (graph["id"], title)
        assert _input_link(sampler, "latent_image") is not None, (graph["id"], title)


@pytest.mark.parametrize("stem", TEXTURED_APPS)
def test_textured_apps_upsample_at_1024(stem: str) -> None:
    """A textured app runs the upsample stage at the int 1024 floor."""
    graph = _graph(stem)
    upsample = _only_node(graph, "Trellis2UpsampleStage")
    widgets = upsample.get("widgets_values") or []
    assert len(widgets) == 1, widgets
    target_resolution = widgets[0]
    assert isinstance(target_resolution, int) and not isinstance(target_resolution, bool)
    assert target_resolution == UPSAMPLE_TARGET_RESOLUTION
    assert graph["extra"]["lab_trellis"]["resolution"] == UPSAMPLE_TARGET_RESOLUTION
    assert _only_node(graph, "Trellis2TextureStage") is not None
    assert _only_node(graph, "PaintMesh") is not None


def test_blockout_runs_no_texture_pass() -> None:
    """A blockout is a gray-box proxy: the texture half must be absent."""
    graph = _graph("blockout-mesh")
    types = {str(node.get("type")) for node in graph["nodes"]}
    for absent in ("Trellis2TextureStage", "PaintMesh", "Trellis2UpsampleStage"):
        assert absent not in types, absent
    assert TEXTURE_PASS.isdisjoint(types)
    assert TEXTURE_VAE not in _loader_widgets(graph)
    assert TEXTURE_VAE not in json.dumps(graph)
    assert graph["extra"]["lab_trellis"]["textured"] is False
    assert graph["extra"]["lab_trellis"]["stages"] == ["structure", "shape"]
    assert graph["extra"]["lab_trellis"]["resolution"] is None


def test_prop_variants_batches_four_meshes() -> None:
    """Four candidates come out of one occupancy session, so batch_size is 4."""
    graph = _graph("prop-variants")
    empty = _only_node(graph, "EmptyTrellis2LatentStructure")
    widgets = empty.get("widgets_values") or []
    assert len(widgets) == 1, widgets
    batch_size = widgets[0]
    assert isinstance(batch_size, int) and not isinstance(batch_size, bool)
    assert batch_size == 4
    assert graph["extra"]["lab_trellis"]["batch_size"] == 4
    assert graph["extra"]["lab_app_mode"]["handoff"] == []


def test_shot_to_prop_sources_a_guide_still_and_previews_it() -> None:
    """The prop comes from a live shot's guide still, gated before the queue."""
    graph = _graph("shot-to-prop")
    guide = _only_node(graph, "EZDCCLoadGuideStill")
    assert guide["widgets_values"] == ["go-see", "12", "first"]
    preview = _only_node(graph, "EZDCCPreviewGuideLayer")
    assert _is_in_link_graph(graph, preview) is True
    gate = _only_node(graph, "EZDCCOccupancyGate")
    assert gate["widgets_values"] == ["trellis"]
    assert _is_in_link_graph(graph, gate) is True
    # guide -> preview -> gate -> unload -> conditioning
    gate_link = _input_link(gate, "image")
    assert gate_link is not None
    assert _origin_node(graph, gate_link)["id"] == preview["id"]
    unload = _only_node(graph, "EZUnloadModels")
    unload_link = _input_link(unload, "image")
    assert unload_link is not None
    assert _origin_node(graph, unload_link)["id"] == gate["id"]
    conditioning = _only_node(graph, "Trellis2Conditioning")
    conditioning_link = _input_link(conditioning, "image")
    assert conditioning_link is not None
    assert _origin_node(graph, conditioning_link)["id"] == unload["id"]


@pytest.mark.parametrize("stem", ALL_3D_APPS)
def test_image_path_is_occupancy_guarded(stem: str) -> None:
    """Every 3d graph gates or unloads between the image source and conditioning."""
    graph = _graph(stem)
    source = _image_source(graph)
    conditioning = _only_node(graph, "Trellis2Conditioning")
    guards = [
        node
        for node in graph["nodes"]
        if node.get("type") in {"EZDCCOccupancyGate", "EZUnloadModels"}
        and _is_in_link_graph(graph, node)
    ]
    assert guards, stem
    on_path = [
        guard
        for guard in guards
        if _reaches(graph, int(source["id"]), int(guard["id"]))
        and _reaches(graph, int(guard["id"]), int(conditioning["id"]))
    ]
    assert on_path, (stem, [guard.get("type") for guard in guards])
    for gate in _nodes_of(graph, "EZDCCOccupancyGate"):
        assert gate["widgets_values"] == ["trellis"], stem


@pytest.mark.parametrize("stem", ALL_3D_APPS)
def test_banned_needles_absent(stem: str) -> None:
    """No off-catalog model family is named anywhere in the serialized graph."""
    blob = json.dumps(_graph(stem))
    for needle in BANNED:
        assert needle not in blob, (stem, needle)


@pytest.mark.parametrize("stem", PIN_AUDIT_APPS)
def test_loader_widgets_are_catalogued_pins(stem: str) -> None:
    """Loader filenames name only the trellis pins the model manifest carries."""
    graph = _graph(stem)
    widgets = _loader_widgets(graph)
    assert widgets, stem
    assert frozenset(widgets) == EXPECTED_PINS[stem], (stem, sorted(widgets))
    manifest = MANIFEST.read_text(encoding="utf-8")
    for value in widgets:
        assert value in manifest, (stem, value)
    for pin in ALLOWED_PINS:
        assert pin in manifest, pin
