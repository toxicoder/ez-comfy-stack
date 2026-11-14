"""Wire EZImageFormat / EZVideoFormat into canvas-owning lab graphs."""

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

from _lab_paths import cached_lab_graph_rows, lab_json  # noqa: E402
from _wire_format import (  # noqa: E402
    FORMAT_BLURB,
    FORMAT_SCOPE,
    STILL_FORMAT_TYPE,
    STILL_SCOPE,
    VIDEO_FORMAT_TYPE,
    VIDEO_SCOPE,
    align_size_mode,
    ensure_format_widgets,
    format_kind,
    graph_still_sources,
    pick_still_format,
    pick_video_format,
    size_mode_for,
    wire_lab_graph,
    wire_still_format,
    wire_video_format,
)
from ez_image.formats import SIZE_MODE_FORCE, SIZE_MODE_MATCH  # noqa: E402


def _load(rel: str) -> dict[str, Any]:
    return json.loads(lab_json(rel).read_text(encoding="utf-8"))


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph["nodes"]}


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _src(graph: dict[str, Any], node: dict[str, Any], name: str) -> dict[str, Any]:
    inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
    origin = int(_link_map(graph)[int(inp["link"])][1])
    return _by_id(graph)[origin]


def test_format_scope_covers_printers_and_skips_locked() -> None:
    assert format_kind("photos/still-draft") == "still"
    assert format_kind("photos/still-studio") == "still"
    assert format_kind("photos/image-studio") == "still"
    assert format_kind("video/silent/still-to-video-5s") == "video"
    assert format_kind("video/av/text-to-video-8s") == "video"
    assert format_kind("social/stills/youtube-channel-icon") == "still"
    assert format_kind("social/silent/tiktok-hook") == "video"
    assert format_kind("photos/text-swap") is None
    assert format_kind("photos/platform-pack") is None
    assert format_kind("film/go-see") is None
    assert format_kind("video/av/audio-to-video-8s") == "video"
    assert format_kind("video/av/talking-head") == "video"
    assert format_kind("photos/lighting-trio") == "still"
    assert format_kind("photos/background-swap") is None
    assert format_kind("photos/background-edit") is None
    assert "photos/still-draft" in STILL_SCOPE
    assert "video/loops/gif-loop" in VIDEO_SCOPE
    assert format_kind("audio/albums/drive-through/afterparty/cover") == "still"
    assert format_kind("audio/albums/nill-bye/peer-review/cover") == "still"
    assert FORMAT_SCOPE == STILL_SCOPE | VIDEO_SCOPE


def test_pick_still_and_video_defaults() -> None:
    draft = pick_still_format("photos/still-draft", 768, 432, "ez_still_draft")
    assert draft.id == "aspect_16_9_draft"
    thumb = pick_still_format("social/stills/youtube-channel-icon", 768, 768, "ez_yt_icon")
    assert thumb.id == "youtube_channel_icon"
    custom = pick_still_format("photos/style-lock", 768, 960, "ez_style_lock")
    assert custom.id == "custom"
    wan = pick_video_format("wan", 832, 480)
    assert wan.id == "wan_16_9"
    ltx = pick_video_format("ltx", 768, 1280)
    assert ltx.id == "ltx_9_16"
    odd = pick_video_format("wan", 640, 640)
    assert odd.id == "custom"


def _strip_format(graph: dict[str, Any], ntype: str) -> None:
    fmt_ids = {int(node["id"]) for node in graph["nodes"] if node.get("type") == ntype}
    graph["nodes"] = [
        node for node in graph["nodes"] if int(node["id"]) not in fmt_ids
    ]
    drop: set[int] = set()
    keep: list[Any] = []
    for link in graph.get("links") or []:
        if int(link[1]) in fmt_ids:
            drop.add(int(link[0]))
            continue
        keep.append(link)
    graph["links"] = keep
    for node in graph["nodes"]:
        node["inputs"] = [
            item
            for item in (node.get("inputs") or [])
            if item.get("link") is None or int(item["link"]) not in drop
        ]
        for out in node.get("outputs") or []:
            out["links"] = [
                lid for lid in (out.get("links") or []) if int(lid) not in drop
            ]


def test_wire_still_draft_links_latent_and_hint() -> None:
    graph = copy.deepcopy(_load("photos/still-draft"))
    assert wire_still_format(graph) is False
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZImageFormat")
    latent = next(
        node for node in graph["nodes"] if node.get("type") == "EmptyFlux2LatentImage"
    )
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZKleinPromptEnhance"
    )
    save = next(node for node in graph["nodes"] if node.get("type") == "SaveImage")
    assert _src(graph, latent, "width")["id"] == fmt["id"]
    assert _src(graph, latent, "height")["id"] == fmt["id"]
    assert _src(graph, enh, "duration_hint")["id"] == fmt["id"]
    assert not any(item.get("name") == "filename_prefix" for item in save.get("inputs") or [])
    assert FORMAT_BLURB in str((graph.get("extra") or {}).get("lab_note") or "")
    assert fmt["widgets_values"][0] == "16:9 draft (768x432)"
    assert "Match input" in fmt["widgets_values"]
    _strip_format(graph, "EZImageFormat")
    assert wire_still_format(graph) is True


def test_wire_video_links_wan_latent() -> None:
    graph = copy.deepcopy(_load("video/silent/still-to-video-5s"))
    assert wire_video_format(graph) is False
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZVideoFormat")
    latent = next(
        node for node in graph["nodes"] if node.get("type") == "Wan22ImageToVideoLatent"
    )
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZWanPromptEnhance"
    )
    assert _src(graph, latent, "width")["id"] == fmt["id"]
    assert _src(graph, latent, "height")["id"] == fmt["id"]
    assert _src(graph, enh, "duration_hint")["id"] == fmt["id"]
    assert fmt["widgets_values"][0] == "Wan 5B"
    assert fmt["widgets_values"][1] == "Wan - 16:9 YouTube (832x480)"
    assert "Match input" in fmt["widgets_values"]
    assert "5 seconds" in fmt["widgets_values"]
    _strip_format(graph, "EZVideoFormat")
    assert wire_video_format(graph) is True


def test_ensure_format_widgets_is_idempotent() -> None:
    graph = copy.deepcopy(_load("photos/still-draft"))
    assert ensure_format_widgets(graph) is True or any(
        isinstance(item, str) and item.strip() in (SIZE_MODE_MATCH, SIZE_MODE_FORCE)
        for item in next(
            node["widgets_values"]
            for node in graph["nodes"]
            if node.get("type") == "EZImageFormat"
        )
    )
    assert ensure_format_widgets(graph) is False
    video = copy.deepcopy(_load("video/av/text-to-video-8s"))
    ensure_format_widgets(video)
    values = next(
        node["widgets_values"]
        for node in video["nodes"]
        if node.get("type") == "EZVideoFormat"
    )
    assert values.count(SIZE_MODE_MATCH) + values.count(SIZE_MODE_FORCE) == 1
    assert values.count("8 seconds") == 1
    assert ensure_format_widgets(video) is False


def test_wire_skips_out_of_scope_and_mixed_pack() -> None:
    swap = copy.deepcopy(_load("photos/text-swap"))
    assert wire_lab_graph(swap) is False
    pack = copy.deepcopy(_load("photos/platform-pack"))
    assert wire_lab_graph(pack) is False
    assert not any(node.get("type") == "EZImageFormat" for node in pack["nodes"])


def test_gif_loop_skips_hint_link() -> None:
    graph = copy.deepcopy(_load("video/loops/gif-loop"))
    assert wire_video_format(graph) is False
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZVideoFormat")
    enh = next(
        node for node in graph["nodes"] if node.get("type") == "EZWanPromptEnhance"
    )
    names = [item.get("name") for item in enh.get("inputs") or []]
    assert "duration_hint" not in names
    latent = next(
        node for node in graph["nodes"] if node.get("type") == "Wan22ImageToVideoLatent"
    )
    assert _src(graph, latent, "width")["id"] == fmt["id"]


INERT_APP = "business/b2b-saas/office-broll-av"
"""A canvas App whose graph owns no still the format node could read."""

LIVE_APP = "photos/thumbnail"
"""A canvas App that offers a reference still the format JS can read."""

LINKED_APP = "photos/upscale-reframe"
"""The one App that links a still straight into the format node."""


def _format_node(graph: dict[str, Any]) -> dict[str, Any]:
    """The graph's single canvas-format node."""
    hits = [
        node
        for node in graph["nodes"]
        if node.get("type") in (STILL_FORMAT_TYPE, VIDEO_FORMAT_TYPE)
    ]
    assert len(hits) == 1, f"expected one format node, found {len(hits)}"
    return hits[0]


def _set_size_mode(node: dict[str, Any], value: str) -> None:
    """Force one authored size mode onto a format node."""
    for index, item in enumerate(node["widgets_values"]):
        if isinstance(item, str) and item.strip() in (SIZE_MODE_MATCH, SIZE_MODE_FORCE):
            node["widgets_values"][index] = value
            return
    raise AssertionError("the node carries no size_mode widget")


def _size_mode(node: dict[str, Any]) -> str:
    """The authored size mode of a format node."""
    for item in node["widgets_values"]:
        if isinstance(item, str) and item.strip() in (SIZE_MODE_MATCH, SIZE_MODE_FORCE):
            return item
    raise AssertionError("the node carries no size_mode widget")


def test_a_canvas_with_no_still_of_its_own_authors_force_format() -> None:
    """Nothing in the graph can hand the canvas a still, so Match input lies."""
    graph = copy.deepcopy(_load(INERT_APP))
    assert graph_still_sources(graph) == []
    _set_size_mode(_format_node(graph), SIZE_MODE_MATCH)

    assert align_size_mode(graph) == 1
    assert _size_mode(_format_node(graph)) == SIZE_MODE_FORCE


def test_a_picker_the_operator_can_fill_keeps_match_input() -> None:
    """A file box anywhere in the App is a still the format can follow."""
    graph = copy.deepcopy(_load(LIVE_APP))
    assert graph_still_sources(graph), "the App is expected to offer a picker"
    _set_size_mode(_format_node(graph), SIZE_MODE_FORCE)

    assert align_size_mode(graph) == 1
    assert _size_mode(_format_node(graph)) == SIZE_MODE_MATCH


def test_a_linked_still_keeps_match_input_without_a_picker() -> None:
    """A still wired into the node is the clearest case of all."""
    graph = copy.deepcopy(_load(LINKED_APP))
    fmt = _format_node(graph)
    _set_size_mode(fmt, SIZE_MODE_FORCE)

    assert size_mode_for(fmt, graph) == SIZE_MODE_MATCH
    assert align_size_mode(graph) == 1
    assert _size_mode(_format_node(graph)) == SIZE_MODE_MATCH


def test_a_bypassed_picker_is_not_a_still_source() -> None:
    """A muted file box offers no file, so the mode has to stay honest."""
    graph = copy.deepcopy(_load(LIVE_APP))
    for node in graph_still_sources(graph):
        node["mode"] = 4
    assert graph_still_sources(graph) == []
    assert size_mode_for(_format_node(graph), graph) == SIZE_MODE_FORCE


def test_alignment_touches_nothing_but_the_size_mode() -> None:
    """The pass rewrites one widget cell and no geometry, rows, or counters."""
    graph = copy.deepcopy(_load(INERT_APP))
    _set_size_mode(_format_node(graph), SIZE_MODE_MATCH)
    before = copy.deepcopy(graph)

    align_size_mode(graph)

    for node_id, before_node in {int(n["id"]): n for n in before["nodes"]}.items():
        after_node = {int(n["id"]): n for n in graph["nodes"]}[node_id]
        for key in set(before_node) | set(after_node):
            if key == "widgets_values" and before_node.get("type") in (
                STILL_FORMAT_TYPE,
                VIDEO_FORMAT_TYPE,
            ):
                continue
            assert before_node.get(key) == after_node.get(key), f"{node_id}.{key}"
    assert graph["links"] == before["links"]
    assert graph["extra"] == before["extra"]


def test_alignment_is_idempotent() -> None:
    """A graph the pass has already authored is reported clean."""
    graph = copy.deepcopy(_load(INERT_APP))
    align_size_mode(graph)
    assert align_size_mode(graph) == 0


def test_the_shipped_catalog_authors_an_honest_size_mode() -> None:
    """No shipped App defaults to a behaviour its own graph cannot deliver."""
    outstanding = [
        rel
        for rel, _path, graph in cached_lab_graph_rows()
        if isinstance(graph, dict) and align_size_mode(copy.deepcopy(graph))
    ]
    assert outstanding == []
