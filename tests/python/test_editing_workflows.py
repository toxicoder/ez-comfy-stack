"""Editing-lane lab graph: Wan 2.2 silent T2V cutaway for the ez_edit agent.

Hermetic: stdlib + JSON. Re-runs the builder in-process and compares bytes, so
it never touches the network, ComfyUI, or the GPU.
"""

from __future__ import annotations

import json

from _audit_lab_graphs import BANNED_ANYWHERE, BANNED_LOADER, audit_lab_graphs
from _build_editing_workflows import (
    ENHANCE_TITLE,
    LAB_REL,
    NEG_ENHANCE_TITLE,
    NEGATIVE_TITLE,
    PACKAGE_SUBPATH,
    PREFIX,
    PROMPT_TITLE,
    ROOT,
    SAVER_TITLE,
    WAN_CLIP,
    WAN_UNET,
    WAN_VAE,
    main as build_main,
)
from _lab_layout import group_overlap_hits, node_overlap_hits, title_inset_hits
from _lab_paths import LAB_ROOT, lab_json, lane_for_stem

PACKAGE_GRAPH = ROOT / PACKAGE_SUBPATH
GATE_TYPE = "EZDCCOccupancyGate"
MAX_NODES = 20


def _load() -> dict:
    """Parse the shipped lab graph.

    Returns:
        Graph dict for ``film/generate-cutaway``.
    """
    path = lab_json(f"{LAB_REL}.json")
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _by_type(graph: dict, ntype: str) -> list[dict]:
    """Return nodes of one type.

    Args:
        graph: Serialized Comfy graph.
        ntype: Comfy class name.

    Returns:
        Matching nodes.
    """
    return [node for node in graph["nodes"] if node.get("type") == ntype]


def _one(graph: dict, ntype: str) -> dict:
    """Return the single node of ``ntype``.

    Args:
        graph: Serialized Comfy graph.
        ntype: Comfy class name.

    Returns:
        The one matching node.
    """
    hits = _by_type(graph, ntype)
    assert len(hits) == 1, (ntype, len(hits))
    return hits[0]


def _clip_by_title(graph: dict, title: str) -> dict:
    """Return the CLIP Text Encode node titled ``title``.

    Args:
        graph: Serialized Comfy graph.
        title: Canvas title of the encode node.

    Returns:
        The one matching node.
    """
    hits = [
        node for node in _by_type(graph, "CLIPTextEncode") if node.get("title") == title
    ]
    assert len(hits) == 1, (title, len(hits))
    return hits[0]


def _node_of(graph: dict, links: dict[int, list], link_id: int) -> dict:
    """Return the node a link leaves from.

    Args:
        graph: Serialized Comfy graph.
        links: Link id to link row map.
        link_id: Link id to follow.

    Returns:
        The source node.
    """
    by_id = {int(node["id"]): node for node in graph["nodes"]}
    return by_id[int(links[link_id][1])]


def test_editing_lane_dir_and_graph_exist() -> None:
    """The promoted lane folder holds the cutaway graph."""
    lane = LAB_ROOT / "film"
    assert lane.is_dir(), lane
    assert "generate-cutaway.json" in sorted(path.name for path in lane.glob("*.json"))
    assert lane_for_stem(LAB_REL) == "film"


def test_graph_identity_and_audit_pass() -> None:
    """The graph carries lab identity and clears the shipped-graph auditor."""
    graph = _load()
    assert graph.get("id") == "generate-cutaway"
    assert graph["extra"]["lab_rel"] == LAB_REL
    assert graph["extra"]["workflowRendererVersion"] == "Vue-corrected"
    assert graph["extra"]["lab_note"].strip()
    assert graph["extra"]["lab_description"].strip()
    assert node_overlap_hits(graph) == []
    assert group_overlap_hits(graph) == []
    assert title_inset_hits(graph) == []
    assert audit_lab_graphs(LAB_ROOT) >= 8


def test_package_copy_is_byte_identical() -> None:
    """The ez_edit package copy matches the lab graph byte for byte."""
    lab_bytes = lab_json(f"{LAB_REL}.json").read_bytes()
    assert PACKAGE_GRAPH.is_file(), PACKAGE_GRAPH
    assert PACKAGE_GRAPH.read_bytes() == lab_bytes


def test_generator_is_idempotent() -> None:
    """Re-running the builder rewrites both JSON files unchanged."""
    before = {
        "lab": lab_json(f"{LAB_REL}.json").read_bytes(),
        "package": PACKAGE_GRAPH.read_bytes(),
    }
    assert build_main() == 0
    after = {
        "lab": lab_json(f"{LAB_REL}.json").read_bytes(),
        "package": PACKAGE_GRAPH.read_bytes(),
    }
    assert after == before


def test_node_budget_and_chain() -> None:
    """The cutaway chain stays small and keeps the copied Wan 2.2 skeleton."""
    graph = _load()
    assert len(graph["nodes"]) < MAX_NODES, len(graph["nodes"])
    types = {str(node.get("type")) for node in graph["nodes"]}
    for ntype in (
        "Note",
        "UNETLoader",
        "CLIPLoader",
        "VAELoader",
        "CLIPTextEncode",
        "EZWanPromptEnhance",
        "EZNegativePromptEnhance",
        "Wan22ImageToVideoLatent",
        "ModelSamplingSD3",
        "KSampler",
        "VAEDecode",
        GATE_TYPE,
        "VHS_VideoCombine",
        "EZQuality",
        "EZModelCheck",
    ):
        assert ntype in types, ntype
    assert "LoadImage" not in types
    assert len(_by_type(graph, "CLIPTextEncode")) == 2
    for loader, widget in (
        ("UNETLoader", WAN_UNET),
        ("CLIPLoader", WAN_CLIP),
        ("VAELoader", WAN_VAE),
    ):
        values = _one(graph, loader)["widgets_values"]
        assert widget in values, (loader, values)
    assert _one(graph, "CLIPLoader")["widgets_values"][1] == "wan"


def test_enhance_pair_owns_both_clips() -> None:
    """The Wan rewrite feeds the Positive CLIP; the negative rewrite reads it.

    The enhance node is the live prompt path, so the agent patches its widget
    (a link over a CLIP widget makes that widget dead at queue time).
    """
    graph = _load()
    links = {int(link[0]): link for link in graph["links"]}
    enhance = _one(graph, "EZWanPromptEnhance")
    neg_enh = _one(graph, "EZNegativePromptEnhance")
    assert enhance["widgets_values"][2] is True, enhance["widgets_values"]
    assert enhance["widgets_values"][3] == "t2v"
    assert enhance["widgets_values"][6] == LAB_REL
    assert neg_enh["widgets_values"][1] is True, neg_enh["widgets_values"]
    assert neg_enh["widgets_values"][2] == "wan"

    def text_source(title: str) -> dict:
        clip = _clip_by_title(graph, title)
        row = next(inp for inp in clip["inputs"] if inp["name"] == "text")
        assert row["link"] is not None, title
        return _node_of(graph, links, int(row["link"]))

    assert text_source(PROMPT_TITLE)["type"] == "EZWanPromptEnhance"
    assert text_source(NEGATIVE_TITLE)["type"] == "EZNegativePromptEnhance"
    pos_row = next(inp for inp in neg_enh["inputs"] if inp["name"] == "positive")
    assert pos_row["link"] is not None
    assert _node_of(graph, links, int(pos_row["link"]))["id"] == enhance["id"]
    # The Positive CLIP widget only mirrors the enhance prompt, so patching it
    # cannot reach UMT5; the prompt patch target is the enhance node.
    mirror = _clip_by_title(graph, PROMPT_TITLE)
    assert mirror["widgets_values"][0] == enhance["widgets_values"][1]


def test_occupancy_gate_wan_mode_on_the_output_edge() -> None:
    """The gate pins mode wan and sits on the IMAGE edge into the MP4 saver."""
    graph = _load()
    gate = _one(graph, GATE_TYPE)
    assert gate["widgets_values"] == ["wan"]
    links = {int(link[0]): link for link in graph["links"]}
    out_links = gate["outputs"][0]["links"]
    assert len(out_links) == 1
    saver = _one(graph, "VHS_VideoCombine")
    link = links[int(out_links[0])]
    assert int(link[1]) == int(gate["id"])
    assert int(link[3]) == int(saver["id"])
    decode = _one(graph, "VAEDecode")
    in_link = links[int(gate["inputs"][0]["link"])]
    assert int(in_link[1]) == int(decode["id"])


def test_prompt_size_and_fps_widgets_are_agent_patchable() -> None:
    """Prompt, size, length, fps, and seed live on widgets the agent patches."""
    graph = _load()
    by_id = {int(node["id"]): node for node in graph["nodes"]}
    widgets = graph["extra"]["lab_edit"]["widgets"]
    # patch -> (node title, widget name, where it lives, widget slot, value type)
    expected: dict[str, tuple[str, str, str, int | None, type]] = {
        "prompt": (ENHANCE_TITLE, "prompt", "slot", 1, str),
        "enhance": (ENHANCE_TITLE, "enhance", "slot", 2, bool),
        "negative_prompt": (NEG_ENHANCE_TITLE, "prompt", "slot", 0, str),
        "negative_enhance": (NEG_ENHANCE_TITLE, "enhance", "slot", 1, bool),
        "width": ("Video size & length", "width", "row", None, int),
        "height": ("Video size & length", "height", "row", None, int),
        "length": ("Video size & length", "length", "slot", 2, int),
        "seed": ("KSampler", "seed", "slot", 0, int),
        "fps": (SAVER_TITLE, "frame_rate", "dict", None, int),
        "filename_prefix": (SAVER_TITLE, "filename_prefix", "dict", None, str),
    }
    assert set(widgets) == set(expected)
    for name, (title, widget, kind, slot, value_type) in expected.items():
        ref = widgets[name]
        node = by_id[int(ref["node"])]
        assert node["title"] == title, (name, node.get("title"))
        assert ref["widget"] == widget, name
        values = node["widgets_values"]
        if kind == "dict":
            assert isinstance(values, dict) and widget in values, name
            assert isinstance(values[widget], value_type), name
        elif kind == "slot":
            assert isinstance(values, list) and slot is not None, name
            assert isinstance(values[slot], value_type), (name, values)
        else:
            rows = [
                str(inp.get("widget", {}).get("name"))
                for inp in node.get("inputs") or []
                if isinstance(inp, dict) and inp.get("widget")
            ]
            assert widget in rows, (name, rows)

    enhance = _one(graph, "EZWanPromptEnhance")
    assert len(str(enhance["widgets_values"][1])) > 80

    latent = _one(graph, "Wan22ImageToVideoLatent")
    assert latent["widgets_values"][:3] == [832, 480, 121]
    start = next(inp for inp in latent["inputs"] if inp["name"] == "start_image")
    assert start.get("link") is None, "cutaways are text-to-video, no start frame"

    sampler = _one(graph, "KSampler")
    for name in ("positive", "negative", "latent_image", "model"):
        row = next(inp for inp in sampler["inputs"] if inp["name"] == name)
        assert row["link"] is not None, name

    saver = _one(graph, "VHS_VideoCombine")
    assert saver["widgets_values"]["format"] == "video/h264-mp4"
    assert saver["widgets_values"]["filename_prefix"] == PREFIX
    assert saver["widgets_values"]["save_output"] is True
    assert saver["widgets_values"]["frame_rate"] == 24


def test_app_mode_stamp_matches_sibling_lane() -> None:
    """App Mode stamps like the wan film lane the graph came from."""
    extra = _load()["extra"]
    mode = extra["lab_app_mode"]
    assert mode["enabled"] is True
    assert mode["lane"] == "film"
    assert mode["occupancy"] == "wan"
    assert mode["default_view"] == "app"
    assert mode["handoff"] == []
    assert extra["lab_quality"] == {"default": "standard"}
    linear = extra["linearData"]
    names = [entry[1] for entry in linear["inputs"]]
    assert names[0] == "quality"
    # The enhance node's prompt widget is the live prompt path the agent patches.
    assert names[1] == "prompt"
    assert linear["outputs"] == [int(_one(_load(), "VHS_VideoCombine")["id"])]
    assert "Occupancy:" in extra["lab_note"]


def test_shipped_graph_stays_clear_of_banned_needles() -> None:
    """No US-excluded model names, in the blob or in a loader pin."""
    graph = _load()
    blob = json.dumps(graph)
    for needle in BANNED_ANYWHERE:
        assert needle not in blob, needle
    for ntype in ("UNETLoader", "CLIPLoader", "VAELoader"):
        values = " ".join(str(v) for v in _one(graph, ntype)["widgets_values"]).lower()
        for needle in BANNED_LOADER:
            assert needle.lower() not in values, (ntype, needle)


def test_lane_registries_know_film() -> None:
    """The lane is registered in the tree helper, the promoter, and the docs."""
    from _lab_paths import ALLOWED_LANES

    assert "film" in ALLOWED_LANES
    promoter = (ROOT / "scripts" / "utilities" / "promote-workflow.sh").read_text(
        encoding="utf-8"
    )
    lane_line = (
        "readonly PROMOTE_LANES=(photos video social business film audio "
        "3d guides labs)"
    )
    assert lane_line in promoter
    doc_gen = (ROOT / "docs" / "generate_workflow_docs.py").read_text(encoding="utf-8")
    assert '"film",' in doc_gen
