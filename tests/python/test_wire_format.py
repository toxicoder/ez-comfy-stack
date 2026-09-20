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

from _lab_paths import lab_json  # noqa: E402
from _wire_format import (  # noqa: E402
    FORMAT_BLURB,
    FORMAT_SCOPE,
    STILL_SCOPE,
    VIDEO_SCOPE,
    ensure_format_widgets,
    format_kind,
    pick_still_format,
    pick_video_format,
    wire_lab_graph,
    wire_still_format,
    wire_video_format,
)


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
    assert format_kind("stills/still-draft") == "still"
    assert format_kind("stills/still-studio") == "still"
    assert format_kind("stills/image-studio") == "still"
    assert format_kind("motion/silent/still-to-video-5s") == "video"
    assert format_kind("motion/av/text-to-video-8s") == "video"
    assert format_kind("creator/stills/youtube-channel-icon") == "still"
    assert format_kind("creator/silent/tiktok-hook") == "video"
    assert format_kind("stills/text-swap") is None
    assert format_kind("stills/platform-pack") is None
    assert format_kind("films/go-see") is None
    assert format_kind("motion/av/audio-to-video-8s") == "video"
    assert format_kind("stills/talking-head") == "video"
    assert format_kind("stills/lighting-trio") == "still"
    assert format_kind("stills/background-swap") is None
    assert "stills/still-draft" in STILL_SCOPE
    assert "motion/loops/gif-loop" in VIDEO_SCOPE
    assert FORMAT_SCOPE == STILL_SCOPE | VIDEO_SCOPE


def test_pick_still_and_video_defaults() -> None:
    draft = pick_still_format("stills/still-draft", 768, 432, "ez_still_draft")
    assert draft.id == "aspect_16_9_draft"
    thumb = pick_still_format("creator/stills/youtube-channel-icon", 768, 768, "ez_yt_icon")
    assert thumb.id == "youtube_channel_icon"
    custom = pick_still_format("stills/style-lock", 768, 960, "ez_style_lock")
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
    graph = copy.deepcopy(_load("stills/still-draft"))
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
    assert fmt["widgets_values"][0] == "16:9 draft (768×432)"
    assert "Match input" in fmt["widgets_values"]
    _strip_format(graph, "EZImageFormat")
    assert wire_still_format(graph) is True


def test_wire_video_links_wan_latent() -> None:
    graph = copy.deepcopy(_load("motion/silent/still-to-video-5s"))
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
    assert fmt["widgets_values"][1] == "Wan · 16:9 YouTube (832×480)"
    assert "Match input" in fmt["widgets_values"]
    assert "8 seconds" in fmt["widgets_values"]
    _strip_format(graph, "EZVideoFormat")
    assert wire_video_format(graph) is True


def test_ensure_format_widgets_is_idempotent() -> None:
    graph = copy.deepcopy(_load("stills/still-draft"))
    assert ensure_format_widgets(graph) is True or "Match input" in next(
        node["widgets_values"]
        for node in graph["nodes"]
        if node.get("type") == "EZImageFormat"
    )
    assert ensure_format_widgets(graph) is False
    video = copy.deepcopy(_load("motion/av/text-to-video-8s"))
    ensure_format_widgets(video)
    values = next(
        node["widgets_values"]
        for node in video["nodes"]
        if node.get("type") == "EZVideoFormat"
    )
    assert values.count("Match input") == 1
    assert values.count("8 seconds") == 1
    assert ensure_format_widgets(video) is False


def test_wire_skips_out_of_scope_and_mixed_pack() -> None:
    swap = copy.deepcopy(_load("stills/text-swap"))
    assert wire_lab_graph(swap) is False
    pack = copy.deepcopy(_load("stills/platform-pack"))
    assert wire_lab_graph(pack) is False
    assert not any(node.get("type") == "EZImageFormat" for node in pack["nodes"])


def test_gif_loop_skips_hint_link() -> None:
    graph = copy.deepcopy(_load("motion/loops/gif-loop"))
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
