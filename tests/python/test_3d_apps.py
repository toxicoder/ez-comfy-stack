"""3d-lane Studio Apps: blockout, shot-to-prop, prop-variants, hero-from-photos,
multi-image-asset, character-batch, world-elements.

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

# The seven apps this file owns. still-to-mesh is owned by its own test file.
NEW_APPS = (
    "blockout-mesh",
    "shot-to-prop",
    "prop-variants",
    "hero-from-photos",
    "multi-image-asset",
    "character-batch",
    "world-elements",
)
TEXTURED_APPS = (
    "shot-to-prop",
    "prop-variants",
    "hero-from-photos",
    "multi-image-asset",
    "character-batch",
    "world-elements",
)
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
    "hero-from-photos": SHARED_CHROME
    | TEXTURE_PASS
    | SINGLE_ITEM_CONVERTER
    | {"LoadImage"},
    # Four sources, four guards, and four conditionings, but the sets are the
    # same: one model stack and one fused chain behind them.
    "multi-image-asset": SHARED_CHROME
    | TEXTURE_PASS
    | SINGLE_ITEM_CONVERTER
    | {"LoadImage"},
    "character-batch": SHARED_CHROME | TEXTURE_PASS | {"LoadImage"},
    # The ground plate rides in on a second LoadImage and a second conditioning;
    # the scene.json layout is the second half of this same Queue.
    "world-elements": SHARED_CHROME
    | TEXTURE_PASS
    | SINGLE_ITEM_CONVERTER
    | {"LoadImage", "EZSceneLayout"},
}
# The batched App writes one .glb per batch item, so it skips MeshToFile3D.
MESH_PRODUCER = {
    "blockout-mesh": "MeshToFile3D",
    "shot-to-prop": "MeshToFile3D",
    "prop-variants": "PaintMesh",
    "hero-from-photos": "MeshToFile3D",
    "multi-image-asset": "MeshToFile3D",
    "character-batch": "PaintMesh",
    "world-elements": "MeshToFile3D",
}
SAVE_PREFIX = {
    "blockout-mesh": "assets/objects/_lab-blockout/blockout",
    "shot-to-prop": "assets/objects/_lab-shot-prop/prop",
    "prop-variants": "assets/objects/_lab-variants/prop",
    "hero-from-photos": "assets/objects/_lab-hero/hero",
    "multi-image-asset": "assets/objects/_lab-multiview/asset",
    "character-batch": "assets/objects/_lab-characters/character",
    "world-elements": "assets/objects/_lab-world/element",
}
SOURCE_TYPE = {
    "blockout-mesh": "EZDCCLoadStillPack",
    "shot-to-prop": "EZDCCLoadGuideStill",
    "prop-variants": "LoadImage",
    "hero-from-photos": "LoadImage",
    "multi-image-asset": "LoadImage",
    "character-batch": "LoadImage",
    "world-elements": "LoadImage",
}
# How many image sources each App is designed around: four views for the fused
# asset, prop source plus ground plate for the world element, one everywhere else.
SOURCE_COUNT = {
    "trellis2": 1,
    "still-to-mesh": 1,
    "blockout-mesh": 1,
    "shot-to-prop": 1,
    "prop-variants": 1,
    "hero-from-photos": 1,
    "multi-image-asset": 4,
    "character-batch": 1,
    "world-elements": 2,
}
EXPECTED_HANDOFF = {
    "blockout-mesh": ["3d/trellis2"],
    "shot-to-prop": ["3d/prop-variants"],
    # Prop variants is the end of the prop line: nothing to hand on to.
    "prop-variants": [],
    "hero-from-photos": ["3d/multi-image-asset"],
    "multi-image-asset": ["3d/world-elements"],
    # A chosen character is a finished asset: the batch App ends its line.
    "character-batch": [],
    # The mesh and the scene.json layout come off one Queue: the layout node
    # is in this graph. The handoff invites you to dress the whole set next.
    "world-elements": ["3d/set-dressing"],
}
BATCH_SIZE = {
    "blockout-mesh": 1,
    "shot-to-prop": 1,
    "prop-variants": 4,
    "hero-from-photos": 1,
    "multi-image-asset": 1,
    "character-batch": 4,
    "world-elements": 1,
}
# The stages each App actually runs, in order, as extra.lab_trellis claims.
EXPECTED_STAGES = {
    "blockout-mesh": ["structure", "shape"],
    "shot-to-prop": ["structure", "shape", "upsample", "texture"],
    "prop-variants": ["structure", "shape", "upsample", "texture"],
    "hero-from-photos": ["structure", "shape", "upsample", "texture"],
    "multi-image-asset": ["structure", "shape", "upsample", "texture"],
    "character-batch": ["structure", "shape", "upsample", "texture"],
    "world-elements": ["structure", "shape", "upsample", "texture"],
}
# Widgets the App page must surface, so the operator retunes a Run without
# opening the graph. ``quality`` is stamped by the Quality node.
EXPECTED_APP_WIDGETS: dict[str, frozenset[str]] = {
    "blockout-mesh": frozenset({"plate", "quality", "steps", "filename_prefix"}),
    "shot-to-prop": frozenset(
        {
            "slug",
            "shot_id",
            "layer",
            "quality",
            "target_resolution",
            "steps",
            "filename_prefix",
        }
    ),
    "prop-variants": frozenset(
        {
            "image",
            "quality",
            "batch_size",
            "target_resolution",
            "steps",
            "filename_prefix",
        }
    ),
    "hero-from-photos": frozenset(
        {"image", "quality", "target_resolution", "steps", "filename_prefix"}
    ),
    "multi-image-asset": frozenset(
        {"image", "quality", "target_resolution", "steps", "filename_prefix"}
    ),
    "character-batch": frozenset(
        {
            "image",
            "quality",
            "batch_size",
            "target_resolution",
            "steps",
            "filename_prefix",
        }
    ),
    "world-elements": frozenset(
        {
            "image",
            "quality",
            "target_resolution",
            "steps",
            "filename_prefix",
            "assets",
            "camera_pos",
            "hdri",
        }
    ),
}
TEXTURELESS_PINS = frozenset({UNET, CLIP_VISION, SHAPE_VAE})
EXPECTED_PINS: dict[str, frozenset[str]] = {
    "trellis2": ALLOWED_PINS,
    "blockout-mesh": TEXTURELESS_PINS,
    "shot-to-prop": ALLOWED_PINS,
    "prop-variants": ALLOWED_PINS,
    "hero-from-photos": ALLOWED_PINS,
    "multi-image-asset": ALLOWED_PINS,
    "character-batch": ALLOWED_PINS,
    "world-elements": ALLOWED_PINS,
}


def _image_sources(graph: dict[str, Any], stem: str) -> list[dict[str, Any]]:
    """The image-producing source nodes of a 3d printer.

    A single-plate App has one; the fused multi-view App has four, and the
    world App adds a ground plate beside its prop source.

    Args:
        graph: Parsed workflow.
        stem: Graph basename this test is checking.

    Returns:
        The source node dicts, in node order.
    """
    hits: list[dict[str, Any]] = [
        node for node in graph["nodes"] if node.get("type") in SOURCE_TYPES
    ]
    assert len(hits) == SOURCE_COUNT[stem], (graph.get("id"), [node.get("type") for node in hits])
    return hits


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
    expected_outputs = [_only_node(graph, "SaveGLB")["id"]]
    if stem == "world-elements":
        # The world App is a two-part printer: the mesh and the scene layout.
        expected_outputs.append(_only_node(graph, "EZSceneLayout")["id"])
    assert outputs == expected_outputs
    assert all(isinstance(node_id, int) and node_id in live for node_id in outputs)


@pytest.mark.parametrize("stem", NEW_APPS)
def test_node_type_set_is_exact(stem: str) -> None:
    """The chain is exactly the nodes the app is meant to run, no more."""
    graph = _graph(stem)
    types = {str(node.get("type")) for node in graph["nodes"]}
    assert types == EXPECTED_TYPES[stem], types ^ EXPECTED_TYPES[stem]
    gates = _nodes_of(graph, "EZDCCOccupancyGate")
    assert gates, stem
    for gate in gates:
        assert gate["widgets_values"] == ["trellis"], (stem, gate["id"])


@pytest.mark.parametrize("stem", NEW_APPS)
def test_image_source_is_the_designed_loader(stem: str) -> None:
    """The image chain starts on the source nodes this app was designed around."""
    graph = _graph(stem)
    sources = _image_sources(graph, stem)
    assert {str(node.get("type")) for node in sources} == {SOURCE_TYPE[stem]}
    if SOURCE_COUNT[stem] == 1:
        assert sources[0]["id"] == _only_node(graph, SOURCE_TYPE[stem])["id"]
    conditioning = _nodes_of(graph, "Trellis2Conditioning")
    assert conditioning, stem
    for source in sources:
        assert any(
            _reaches(graph, int(source["id"]), int(node["id"])) for node in conditioning
        ), (stem, source["id"], source.get("title"))


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
    sources = _image_sources(graph, stem)
    conditionings = _nodes_of(graph, "Trellis2Conditioning")
    assert conditionings, stem
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
        if any(
            _reaches(graph, int(guard["id"]), int(node["id"])) for node in conditionings
        )
    ]
    assert on_path, stem
    for source in sources:
        assert any(
            _reaches(graph, int(source["id"]), int(guard["id"])) for guard in on_path
        ), (stem, source["id"], source.get("title"))
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


def _by_title(graph: dict[str, Any], ntype: str, title: str) -> dict[str, Any]:
    """The single node of one type carrying one title.

    Args:
        graph: Parsed workflow.
        ntype: Comfy node type.
        title: Node title to match.

    Returns:
        The node dict.

    Raises:
        AssertionError: When the title does not match exactly one node.
    """
    hits = [node for node in _nodes_of(graph, ntype) if node.get("title") == title]
    assert len(hits) == 1, (graph.get("id"), ntype, title, [node["id"] for node in hits])
    return hits[0]


def _feeder(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    """The node feeding one named input slot.

    Args:
        graph: Parsed workflow.
        node: Node whose input slot is read.
        name: Input slot name.

    Returns:
        The originating node dict.

    Raises:
        AssertionError: When that slot is unwired.
    """
    link = _input_link(node, name)
    assert link is not None, (graph.get("id"), node.get("title"), name)
    return _origin_node(graph, int(link))


def _app_rows(graph: dict[str, Any]) -> dict[str, list[Any]]:
    """The App-page rows grouped by widget name.

    Args:
        graph: Parsed workflow.

    Returns:
        Widget name to the rows that expose it.
    """
    rows: dict[str, list[Any]] = {}
    for row in graph["extra"]["linearData"]["inputs"]:
        rows.setdefault(str(row[1]), []).append(row)
    return rows


@pytest.mark.parametrize("stem", NEW_APPS)
def test_operator_note_opens_with_its_own_graph_id(stem: str) -> None:
    """The note the operator reads is headed by this graph's own id."""
    note = str(_graph(stem)["extra"]["lab_note"])
    assert note.startswith(f"## 3d/{stem}"), note.splitlines()[0]


@pytest.mark.parametrize("stem", NEW_APPS)
def test_lab_trellis_claims_match_the_nodes(stem: str) -> None:
    """The lab_trellis summary describes the chain that is actually on the canvas."""
    graph = _graph(stem)
    trellis = graph["extra"]["lab_trellis"]
    assert trellis["unet"] == UNET
    assert trellis["stages"] == EXPECTED_STAGES[stem]
    assert trellis["textured"] is (stem in TEXTURED_APPS)
    assert trellis["native_only"] is True
    assert trellis["save_prefix"] == SAVE_PREFIX[stem]
    assert trellis["batch_size"] == _only_node(graph, "EmptyTrellis2LatentStructure")[
        "widgets_values"
    ][0]
    textured = stem in TEXTURED_APPS
    assert trellis["resolution"] == (UPSAMPLE_TARGET_RESOLUTION if textured else None)
    types = {str(node.get("type")) for node in graph["nodes"]}
    for stage, ntype in (
        ("structure", "VaeDecodeStructureTrellis2"),
        ("shape", "Trellis2ShapeStage"),
        ("upsample", "Trellis2UpsampleStage"),
        ("texture", "Trellis2TextureStage"),
    ):
        assert (stage in trellis["stages"]) is (ntype in types), (stem, stage)


@pytest.mark.parametrize("stem", NEW_APPS)
def test_mesh_producer_and_converter_match_the_batch(stem: str) -> None:
    """One mesh per Queue converts through MeshToFile3D; a batch feeds it raw.

    ``MeshToFile3D`` serializes batch item 0 only, so the completeness gate
    forbids it above batch 1 and the graph must not carry it at all.
    """
    graph = _graph(stem)
    converters = _nodes_of(graph, "MeshToFile3D")
    batch_size = graph["extra"]["lab_trellis"]["batch_size"]
    if batch_size > 1:
        assert converters == [], (stem, [node["id"] for node in converters])
    else:
        assert len(converters) == 1, (stem, [node["id"] for node in converters])
        assert _feeder(graph, _only_node(graph, "SaveGLB"), "mesh")["id"] == converters[0]["id"]
        painted = "PaintMesh" if stem in TEXTURED_APPS else "VaeDecodeShapeTrellis"
        assert _feeder(graph, converters[0], "mesh")["type"] == painted, stem


@pytest.mark.parametrize("stem", NEW_APPS)
def test_app_page_surfaces_the_knobs(stem: str) -> None:
    """The App page exposes the knobs the operator retunes, each labelled.

    A row without a label and description renders as a bare widget name, which
    is how an operator ends up guessing what a number does.
    """
    graph = _graph(stem)
    rows = _app_rows(graph)
    missing = EXPECTED_APP_WIDGETS[stem] - set(rows)
    assert missing == frozenset(), (stem, sorted(missing))
    for widget_name, widget_rows in rows.items():
        for row in widget_rows:
            assert len(row) == 3, (stem, widget_name, row)
            config = row[2]
            assert isinstance(config, dict), (stem, widget_name, row)
            assert str(config.get("label", "")).strip(), (stem, widget_name, row)
            assert str(config.get("description", "")).strip(), (stem, widget_name, row)
    # A knob the operator can only reach by opening the graph is a defect.
    if graph["extra"]["lab_trellis"]["batch_size"] > 1:
        assert "batch_size" in rows, stem


def test_hero_from_photos_prints_one_full_chain() -> None:
    """The hero App is one plate through structure, shape, upsample, and paint."""
    graph = _graph("hero-from-photos")
    source = _only_node(graph, "LoadImage")
    conditioning = _only_node(graph, "Trellis2Conditioning")
    assert _feeder(graph, conditioning, "image")["type"] == "EZUnloadModels"
    assert _reaches(graph, int(source["id"]), int(conditioning["id"]))
    structure = _by_title(graph, "KSampler", "KSampler (structure)")
    assert _feeder(graph, structure, "positive")["id"] == conditioning["id"]
    assert _only_node(graph, "Trellis2UpsampleStage")["widgets_values"] == [
        UPSAMPLE_TARGET_RESOLUTION
    ]
    assert _feeder(graph, _only_node(graph, "Trellis2TextureStage"), "positive")["type"] in {
        "Trellis2ShapeStage",
        "Trellis2UpsampleStage",
    }
    assert _feeder(graph, _only_node(graph, "SaveGLB"), "mesh")["type"] == "MeshToFile3D"
    assert graph["extra"]["lab_app_mode"]["handoff"] == ["3d/multi-image-asset"]


def test_multi_image_asset_fuses_four_views_into_one_shape_stage() -> None:
    """Four views each condition the chain; the geometry is fused in one pass."""
    graph = _graph("multi-image-asset")
    sources = _image_sources(graph, "multi-image-asset")
    assert [str(node.get("title")) for node in sources] == [
        "Front view",
        "Side view",
        "Back view",
        "Top-down view",
    ]
    conditionings = _nodes_of(graph, "Trellis2Conditioning")
    assert len(conditionings) == 4, [node["id"] for node in conditionings]
    for source, conditioning in zip(sources, conditionings):
        assert _feeder(graph, conditioning, "image")["type"] == "EZUnloadModels"
        assert _reaches(graph, int(source["id"]), int(conditioning["id"]))
    # One fused geometry: a single latent, shape stage, and upsample stage.
    assert len(_nodes_of(graph, "EmptyTrellis2LatentStructure")) == 1
    assert len(_nodes_of(graph, "Trellis2ShapeStage")) == 1
    assert len(_nodes_of(graph, "Trellis2UpsampleStage")) == 1
    assert len(_nodes_of(graph, "Trellis2TextureStage")) == 1
    # Each view drives its own stage of that one chain.
    assert _feeder(
        graph, _by_title(graph, "KSampler", "KSampler (structure)"), "positive"
    )["title"] == ("Conditioning (front)")
    assert _feeder(graph, _only_node(graph, "Trellis2ShapeStage"), "positive")["title"] == (
        "Conditioning (side)"
    )
    assert _feeder(graph, _only_node(graph, "Trellis2UpsampleStage"), "positive")["title"] == (
        "Conditioning (back)"
    )
    assert _feeder(graph, _only_node(graph, "Trellis2TextureStage"), "positive")["title"] == (
        "Conditioning (top-down)"
    )
    assert _feeder(graph, _only_node(graph, "SaveGLB"), "mesh")["type"] == "MeshToFile3D"
    assert graph["extra"]["lab_app_mode"]["handoff"] == ["3d/world-elements"]


def test_character_batch_batches_four_without_the_single_item_converter() -> None:
    """Four candidates come off one session, so no node may drop three of them."""
    graph = _graph("character-batch")
    assert _only_node(graph, "EmptyTrellis2LatentStructure")["widgets_values"] == [4]
    assert _nodes_of(graph, "MeshToFile3D") == []
    paint = _only_node(graph, "PaintMesh")
    assert _feeder(graph, _only_node(graph, "SaveGLB"), "mesh")["id"] == paint["id"]
    rows = _app_rows(graph)
    assert [row[0] for row in rows["batch_size"]] == [
        _only_node(graph, "EmptyTrellis2LatentStructure")["id"]
    ]
    assert graph["extra"]["lab_app_mode"]["handoff"] == []


def test_world_elements_paints_from_the_ground_plate_and_denies_a_splat() -> None:
    """The world App paints off the plate, denies a splat, and queues its layout.

    A world here is instanced ``.glb`` assets plus an off-line ``scene.json``:
    the note has to say so, because an operator who expects a captured
    environment queues the wrong thing. The layout document is written by the
    ``EZSceneLayout`` node inside this same graph, so one Queue returns both
    halves of the world.
    """
    graph = _graph("world-elements")
    sources = _image_sources(graph, "world-elements")
    assert [str(node.get("title")) for node in sources] == ["Prop source", "Ground plate"]
    plate_conditioning = next(
        node
        for node in _nodes_of(graph, "Trellis2Conditioning")
        if node.get("title") == "Conditioning (ground plate)"
    )
    texture = _only_node(graph, "Trellis2TextureStage")
    assert _feeder(graph, texture, "positive")["id"] == plate_conditioning["id"]
    assert _reaches(graph, int(sources[1]["id"]), int(plate_conditioning["id"]))
    structure = _by_title(graph, "KSampler", "KSampler (structure)")
    assert _feeder(graph, structure, "positive")["title"] == "Conditioning (prop)"
    assert _reaches(graph, int(sources[0]["id"]), int(structure["id"]))
    note = str(graph["extra"]["lab_note"])
    for needle in ("instanced `.glb`", "scene.json", "no gaussian splat", "off-line"):
        assert needle in note, (needle, note)
    assert _feeder(graph, _only_node(graph, "SaveGLB"), "mesh")["type"] == "MeshToFile3D"
    layout = _only_node(graph, "EZSceneLayout")
    assert layout["title"] == "Compose scene layout"
    assert layout["widgets_values"] == [
        "lab-world",
        "hero-olive-jacket\nmug-cobalt-chipped",
        "2.1, 1.6, 3.4",
        "0, 1.2, 0",
        35,
        "none",
        "world-elements",
        False,
    ]
    rows = _app_rows(graph)
    assert [row[0] for row in rows["assets"]] == [layout["id"]]
    assert [row[0] for row in rows["camera_pos"]] == [layout["id"]]
    assert [row[0] for row in rows["hdri"]] == [layout["id"]]
    assert graph["extra"]["lab_app_mode"]["handoff"] == ["3d/set-dressing"]


# ``set-dressing`` is the lane's one App that prints nothing, so it sits outside
# NEW_APPS: every rule above assumes a TRELLIS.2 chain, and this App has none.
LAYOUT_APP = "set-dressing"
LAYOUT_WIDGETS = (
    "scene_id",
    "assets",
    "camera_pos",
    "camera_look",
    "camera_fov",
    "hdri",
    "filename",
    "overwrite",
)


def test_set_dressing_is_a_document_only_world_app() -> None:
    """Dressing a set costs no GPU: no loaders, no samplers, no mesh writer."""
    graph = _graph(LAYOUT_APP)
    types = {str(node["type"]) for node in graph["nodes"]}
    # Note and Check models are the chrome every lab graph carries.
    assert types == {"Note", "EZSceneLayout", "EZModelCheck"}
    for ntype in (
        "UNETLoader",
        "CLIPVisionLoader",
        "VAELoader",
        "KSampler",
        "SaveGLB",
        "MeshToFile3D",
        "EZDCCOccupancyGate",
        "Trellis2Conditioning",
    ):
        assert ntype not in types, ntype
    assert "lab_trellis" not in graph["extra"]
    app_mode = graph["extra"]["lab_app_mode"]
    assert app_mode["occupancy"] == "none"
    assert app_mode["lane"] == "3d"
    assert app_mode["handoff"] == []
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob, needle


def test_set_dressing_surfaces_every_layout_widget() -> None:
    """The App page carries all eight knobs, since there is nothing else to set."""
    graph = _graph(LAYOUT_APP)
    layout = _only_node(graph, "EZSceneLayout")
    assert layout["title"] == "Compose scene layout"
    assert layout["widgets_values"] == [
        "lab-set",
        "hero-olive-jacket\nmug-cobalt-chipped",
        "2.1, 1.6, 3.4",
        "0, 1.2, 0",
        35,
        "none",
        "set-dressing",
        False,
    ]
    rows = _app_rows(graph)
    # Seven of the eight widgets reach the App page. ``overwrite`` stays on the
    # node: replacing a scene draft by accident is the one edit an operator
    # should have to make on the graph on purpose.
    assert sorted(rows) == sorted(set(LAYOUT_WIDGETS) - {"overwrite"}), sorted(rows)
    for widget in sorted(rows):
        assert [row[0] for row in rows[widget]] == [layout["id"]], widget
    assert "overwrite" not in rows
    assert graph["extra"]["linearData"]["outputs"] == [layout["id"]]


def test_set_dressing_note_offers_a_document_not_a_capture() -> None:
    """An operator who expects a scanned environment queued the wrong App."""
    graph = _graph(LAYOUT_APP)
    note = str(graph["extra"]["lab_note"])
    for needle in (
        "scene.json",
        "schemas/scene.json",
        "no gaussian splat",
        "no GPU time",
        "Asset Bible",
    ):
        assert needle in note, (needle, note)
