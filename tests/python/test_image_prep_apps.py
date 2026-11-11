"""photos-lane image-prep Apps: the cutout and the four-view plate.

Hermetic: stdlib + the repo's own ``_lab_paths`` helpers over the shipped
graphs in ``workflows/_lab/photos``. Asserts the Studio App stamp, the exact
``EZCutout`` socket set with no model stack behind it, the
``LoadImage -> EZSnapImage -> VAEEncode -> ReferenceLatent -> KSampler ->
VAEDecode -> SaveImage`` chain repeated over four views of one subject, the
Klein 4B pins copied out of the sibling photos graphs, and that the shipped
JSON is byte-for-byte what the builder writes. No network, no Docker, no GPU,
no ComfyUI import.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from _build_image_prep import BACKDROP, BUILDERS, DILATE, FEATHER, NEGATIVE
from _lab_families import graph_stacks, stack_violations
from _lab_layout import ensure_node_spacing, finalize_layout
from _lab_paths import LAB_ROOT, apply_lab_identity, load_lab_graph

ROOT = Path(__file__).resolve().parents[2]

CUTOUT_REL = "photos/cutout"
MULTI_VIEW_REL = "photos/multi-view"
APPS = (CUTOUT_REL, MULTI_VIEW_REL)
VIEWS = ("FRONT", "SIDE", "BACK", "TOP-DOWN")
VIEW_PREFIXES = ("ez_multiview_front", "ez_multiview_side", "ez_multiview_back", "ez_multiview_topdown")

# The Klein still stack the photos lane pins, read out of photos/identity-sheet.
KLEIN_UNET = "flux-2-klein-4b-fp8.safetensors"
KLEIN_CLIP = "qwen_3_4b.safetensors"
KLEIN_VAE = "flux2-vae.safetensors"

# A cutout is a light pre-pass; the node owns its own weight, so a loader here
# would turn it into a two-stack App.
LOADER_TYPES = frozenset(
    {"UNETLoader", "CLIPLoader", "VAELoader", "CheckpointLoaderSimple", "CLIPVisionLoader"}
)
# Non-catalog model families must never appear in a promoted graph.
BANNED = ("MiniMax", "Seedance", "Kling", "z_image_turbo", "klein-9b", "FLUX.2-dev")
# Room-tour vocabulary belongs to the other photos apps, not to a subject turntable.
ROOM_WORDS = ("room", "building", "furniture", "kitchen", "terrace", "wall", "landscape")


def _path(rel: str) -> Path:
    """Return the shipped JSON path for one image-prep App.

    Args:
        rel: ``_lab``-relative id.

    Returns:
        Path under ``workflows/_lab``.
    """
    return LAB_ROOT / f"{rel}.json"


def _load(rel: str) -> dict[str, Any]:
    """Load one shipped image-prep graph.

    Args:
        rel: ``_lab``-relative id.

    Returns:
        Parsed graph dict.
    """
    return load_lab_graph(_path(rel))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Index a graph's nodes by id.

    Args:
        graph: Parsed graph dict.

    Returns:
        ``{node id: node dict}``.
    """
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    """Index the link table by link id.

    Args:
        graph: Parsed graph dict.

    Returns:
        ``{link id: link row}``.
    """
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the node feeding one named input.

    Args:
        graph: Parsed graph dict.
        node: Consumer node.
        name: Input socket name.

    Returns:
        The origin node.
    """
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    origin = int(_link_map(graph)[int(inp["link"])][1])
    return _by_id(graph)[origin]


def _titled(graph: dict[str, Any], ntype: str, title: str) -> dict[str, Any]:
    """Return the one node of a class carrying one title.

    Args:
        graph: Parsed graph dict.
        ntype: Node class name.
        title: Node title.

    Returns:
        The matching node.
    """
    hits: list[dict[str, Any]] = [
        node
        for node in graph["nodes"]
        if node.get("type") == ntype and node.get("title") == title
    ]
    assert len(hits) == 1, (ntype, title, [node.get("title") for node in hits])
    return hits[0]


def _savers(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every ``SaveImage`` node in build order.

    Args:
        graph: Parsed graph dict.

    Returns:
        ``SaveImage`` nodes.
    """
    return [node for node in graph["nodes"] if node.get("type") == "SaveImage"]


def _regenerated(rel: str) -> dict[str, Any]:
    """Rebuild one App in memory the way ``main()`` writes it.

    Args:
        rel: ``_lab``-relative id.

    Returns:
        The graph the builder produces for that id.
    """
    graph = BUILDERS[rel]()
    finalize_layout(graph)
    apply_lab_identity(graph, rel)
    ensure_node_spacing(graph)
    return graph


@pytest.mark.parametrize("rel", APPS)
def test_app_identity(rel: str) -> None:
    """The file stem, ``id``, and ``extra.lab_rel`` agree with the path."""
    graph = _load(rel)
    assert graph.get("id") == rel.rsplit("/", 1)[-1]
    extra = graph["extra"]
    assert extra.get("lab_rel") == rel
    assert extra.get("lab_profile") == rel
    assert str(extra.get("lab_description") or "").strip()
    assert extra.get("workflowRendererVersion") == "Vue-corrected"
    assert graph.get("version") is not None
    assert graph.get("revision") is not None
    assert any(node.get("type") == "Note" for node in graph["nodes"])
    assert str(extra.get("lab_note") or "").startswith(f"## {rel}")


@pytest.mark.parametrize("rel", APPS)
def test_app_mode_stamp(rel: str) -> None:
    """The App Mode stamp names the photos lane and a real handoff chain."""
    mode = _load(rel)["extra"]["lab_app_mode"]
    assert mode["enabled"] is True
    assert mode["default_view"] == "app"
    assert mode["lane"] == "photos"


@pytest.mark.parametrize("rel", APPS)
def test_linear_data_references_live_nodes(rel: str) -> None:
    """Every persisted App row points at a node the graph actually holds."""
    extra = _load(rel)["extra"]
    live = {int(node["id"]) for node in _load(rel)["nodes"]}
    for entry in extra["linearData"]["inputs"]:
        assert int(entry[0]) in live, entry
        assert isinstance(entry[1], str) and entry[1]
    for node_id in extra["linearData"]["outputs"]:
        assert int(node_id) in live, node_id


@pytest.mark.parametrize("rel", APPS)
def test_banned_needles_absent(rel: str) -> None:
    """No excluded model family is named anywhere in the graph."""
    blob = json.dumps(_load(rel))
    for needle in BANNED:
        assert needle not in blob, (rel, needle)


@pytest.mark.parametrize("rel", APPS)
def test_shipped_json_is_what_the_builder_writes(rel: str) -> None:
    """The graph on disk is generated, not hand-authored."""
    shipped = json.loads(_path(rel).read_text(encoding="utf-8"))
    assert _regenerated(rel) == shipped


def test_cutout_occupancy_and_handoff() -> None:
    """The cutout is a light pre-pass that hands off to the view plate and 3d."""
    mode = _load(CUTOUT_REL)["extra"]["lab_app_mode"]
    assert mode["occupancy"] == "none"
    assert mode["handoff"] == ["photos/multi-view", "3d/hero-from-photos"]


def test_cutout_carries_no_model_stack() -> None:
    """EZCutout owns its weight, so no loader may sit on this canvas."""
    graph = _load(CUTOUT_REL)
    types = {node.get("type") for node in graph["nodes"]}
    assert "EZCutout" in types
    assert not types & LOADER_TYPES, sorted(types & LOADER_TYPES)
    assert graph_stacks(graph) == set()
    assert stack_violations(graph) == []


def test_cutout_socket_set_matches_the_node_contract() -> None:
    """EZCutout is coded against the sockets the first-party node declares."""
    node = _titled(_load(CUTOUT_REL), "EZCutout", "BiRefNet cutout")
    assert [slot["name"] for slot in node["inputs"]] == ["image", "backdrop", "dilate", "feather"]
    assert [slot["type"] for slot in node["inputs"]] == ["IMAGE", "COMBO", "INT", "INT"]
    assert [slot["name"] for slot in node["outputs"]] == ["image", "matte", "mask"]
    assert [slot["type"] for slot in node["outputs"]] == ["IMAGE", "IMAGE", "MASK"]
    assert node["widgets_values"] == [BACKDROP, DILATE, FEATHER]


def test_cutout_chain_writes_a_cutout_and_a_matte() -> None:
    """The cut still and the grey matte that produced it are both printed."""
    graph = _load(CUTOUT_REL)
    cutout = _titled(graph, "EZCutout", "BiRefNet cutout")
    load = _src(graph, cutout, "image")
    assert load["type"] == "LoadImage"
    assert load["widgets_values"][0] == "example.png"
    savers = _savers(graph)
    assert len(savers) == 2
    assert [node["widgets_values"][0] for node in savers] == ["ez_cutout", "ez_cutout_matte"]
    for index, node in enumerate(savers):
        up = _src(graph, node, "images")
        assert up["type"] == "EZImageUpscale"
        assert _src(graph, up, "image") is cutout
        row = next(
            row
            for row in graph["links"]
            if row[1] == cutout["id"] and row[3] == up["id"]
        )
        assert row[2] == index
        assert row[5] == "IMAGE"
    # The MASK slot stays open for an operator who wants to route the raw alpha
    # somewhere else; nothing in this graph consumes it.
    mask_slot = cutout["outputs"][2]
    assert mask_slot["name"] == "mask" and mask_slot["type"] == "MASK"
    assert not mask_slot["links"]


def test_cutout_app_row_leads_with_the_photo() -> None:
    """The sidebar asks for the still first, then the backdrop and edge knobs."""
    names = [entry[1] for entry in _load(CUTOUT_REL)["extra"]["linearData"]["inputs"]]
    assert names == ["image", "backdrop", "dilate", "feather", "upscale"]


def test_cutout_note_names_the_image_to_3d_job() -> None:
    """The note says who the cutout is for and what each printed file is."""
    note = _load(CUTOUT_REL)["extra"]["lab_note"].casefold()
    assert "image-to-3d" in note
    assert "character or object" in note
    assert "ez_cutout_matte" in note
    assert "birefnet" in note
    assert "fails soft" in note
    assert "backdrop" in note
    assert "occupancy: none" in note


@pytest.mark.parametrize("rel", APPS)
def test_every_save_runs_through_upscale(rel: str) -> None:
    """A photos App prints the upscaled still, on one shared dropdown."""
    graph = _load(rel)
    ups = [node for node in graph["nodes"] if node.get("type") == "EZImageUpscale"]
    savers = _savers(graph)
    assert len(ups) == len(savers)
    for node in savers:
        assert _src(graph, node, "images")["type"] == "EZImageUpscale"
    free = [
        node
        for node in ups
        if not any(
            slot.get("name") == "upscale" and slot.get("link") is not None
            for slot in node.get("inputs") or []
        )
    ]
    assert len(free) == 1, "one App dropdown must drive every save"
    assert free[0]["widgets_values"] == ["none"]
    rows = {int(row[0]) for row in graph["links"] if row[5] == "STRING"}
    for node in ups:
        if node is free[0]:
            continue
        slot = next(item for item in node["inputs"] if item["name"] == "upscale")
        assert int(slot["link"]) in rows


def test_multi_view_occupancy_and_handoff() -> None:
    """The view plate owns a Klein session and feeds the mesh printers."""
    mode = _load(MULTI_VIEW_REL)["extra"]["lab_app_mode"]
    assert mode["occupancy"] == "klein"
    assert mode["handoff"] == ["3d/multi-image-asset", "3d/hero-from-photos"]


def test_multi_view_pins_the_klein_still_stack() -> None:
    """One UNET, one text encoder, one VAE, with the photos-lane filenames."""
    graph = _load(MULTI_VIEW_REL)
    unets = [node for node in graph["nodes"] if node.get("type") == "UNETLoader"]
    clips = [node for node in graph["nodes"] if node.get("type") == "CLIPLoader"]
    vaes = [node for node in graph["nodes"] if node.get("type") == "VAELoader"]
    assert [node["widgets_values"] for node in unets] == [[KLEIN_UNET, "default"]]
    assert [node["widgets_values"] for node in clips] == [[KLEIN_CLIP, "flux2", "default"]]
    assert [node["widgets_values"] for node in vaes] == [[KLEIN_VAE]]
    assert graph_stacks(graph) == {"klein"}
    assert stack_violations(graph) == []


def test_multi_view_is_a_reference_edit_on_one_plate() -> None:
    """Four samplers read one snapped, encoded plate through ReferenceLatent."""
    graph = _load(MULTI_VIEW_REL)
    types = {node.get("type") for node in graph["nodes"]}
    assert "EmptyFlux2LatentImage" not in types
    assert "EZCubicCondition" not in types
    samplers = [node for node in graph["nodes"] if node.get("type") == "KSampler"]
    assert len(samplers) == 4
    encode = _src(graph, samplers[0], "latent_image")
    assert encode["type"] == "VAEEncode"
    for sampler in samplers:
        positive = _src(graph, sampler, "positive")
        assert positive["type"] == "ReferenceLatent"
        negative = _src(graph, sampler, "negative")
        assert negative["type"] == "CLIPTextEncode"
        assert "negative" in str(negative.get("title", "")).lower()
        assert _src(graph, negative, "clip")["type"] == "CLIPLoader"
        assert _src(graph, sampler, "latent_image")["id"] == encode["id"]
        assert _src(graph, positive, "latent")["id"] == encode["id"]
    snap = _src(graph, encode, "pixels")
    assert snap["type"] == "EZSnapImage"
    load = _src(graph, snap, "image")
    assert load["type"] == "LoadImage"
    assert _src(graph, encode, "vae")["type"] == "VAELoader"


def test_multi_view_decodes_and_prints_four_views() -> None:
    """Each view ends on its own ``SaveImage`` under the ``ez_multiview`` prefix."""
    graph = _load(MULTI_VIEW_REL)
    savers = _savers(graph)
    assert [node["widgets_values"][0] for node in savers] == list(VIEW_PREFIXES)
    for node in savers:
        upscale = _src(graph, node, "images")
        assert upscale["type"] == "EZImageUpscale"
        decode = _src(graph, upscale, "image")
        assert decode["type"] == "VAEDecode"
        assert _src(graph, decode, "vae")["type"] == "VAELoader"
        sampler = _src(graph, decode, "samples")
        assert sampler["type"] == "KSampler"


def test_multi_view_shares_one_seed_and_the_distilled_ladder() -> None:
    """Identical seed and settings, so the only variable left is the camera."""
    graph = _load(MULTI_VIEW_REL)
    samplers = [node for node in graph["nodes"] if node.get("type") == "KSampler"]
    assert len(samplers) == 4
    for sampler in samplers:
        widgets = sampler["widgets_values"]
        assert widgets[0] == 42
        assert widgets[1] == "fixed"
        assert widgets[2] == 4
        assert widgets[3] == 1.0
        assert widgets[6] == 1.0


def test_multi_view_shot_cards_move_only_the_camera() -> None:
    """Four ``view``-locked shot cards hang off one identity bible."""
    graph = _load(MULTI_VIEW_REL)
    joins = [node for node in graph["nodes"] if node.get("type") == "EZPromptJoin"]
    assert len(joins) == 4
    assert [node["title"] for node in joins] == [f"SHOT {suffix}" for suffix in VIEWS]
    enhancer = _titled(graph, "EZKleinPromptEnhance", "IDENTITY")
    for join in joins:
        widgets = join["widgets_values"]
        assert len(widgets) == 3
        assert widgets[2] == "view"
        assert "camera" in str(widgets[0]).casefold()
        assert "same identity" in str(widgets[0]).casefold()
        assert _src(graph, join, "identity") is enhancer
    positive_titles = {
        node.get("title")
        for node in graph["nodes"]
        if node.get("type") == "CLIPTextEncode"
        and "negative" not in str(node.get("title", "")).lower()
    }
    assert positive_titles == {f"Positive {suffix}" for suffix in VIEWS}


def test_multi_view_promises_a_subject_not_a_room_tour() -> None:
    """The bible is one character or object; rooms belong to the other apps."""
    graph = _load(MULTI_VIEW_REL)
    enhancer = _titled(graph, "EZKleinPromptEnhance", "IDENTITY")
    bible = str(enhancer["widgets_values"][1])
    assert str(enhancer["widgets_values"][3]) == "identity"
    lowered = bible.casefold()
    assert "character" in lowered
    assert "one" in lowered
    for word in ROOM_WORDS:
        assert word not in lowered, word
    note = str(graph["extra"]["lab_note"]).casefold()
    assert "room tour" in note
    assert "photos/identity-sheet" in note


def test_multi_view_negative_is_rewritten_against_its_own_view() -> None:
    """Every view carries its own negative rewrite, fed by that view's shot card."""
    graph = _load(MULTI_VIEW_REL)
    enhances = [
        node for node in graph["nodes"] if node.get("type") == "EZNegativePromptEnhance"
    ]
    assert len(enhances) == 4
    samplers = [node for node in graph["nodes"] if node.get("type") == "KSampler"]
    assert len(samplers) == 4
    for sampler in samplers:
        negative = _src(graph, sampler, "negative")
        enhance = _src(graph, negative, "text")
        assert enhance["type"] == "EZNegativePromptEnhance"
        assert enhance["widgets_values"] == [NEGATIVE, True, "klein"]
        assert _src(graph, negative, "clip")["type"] == "CLIPLoader"
        shot = _src(graph, _src(graph, sampler, "positive"), "conditioning")
        assert _src(graph, enhance, "positive") is _src(graph, shot, "text")
    rows = _load(MULTI_VIEW_REL)["extra"]["linearData"]["inputs"]
    labels = [entry[2]["label"] for entry in rows if len(entry) > 2 and "label" in entry[2]]
    assert "Rewrite negative" in labels


def test_multi_view_app_row_leads_with_the_photo() -> None:
    """The sidebar shows the start image, then the identity and seed knobs."""
    names = [entry[1] for entry in _load(MULTI_VIEW_REL)["extra"]["linearData"]["inputs"]]
    assert names[0] == "image"
    assert "sample" in names
    assert "prompt" in names
    assert "enhance" in names
    assert "seed" in names
