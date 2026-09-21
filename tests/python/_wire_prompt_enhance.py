"""One-shot helper: rewrite lab CLIP prompts and wire enhance nodes.

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_wire_prompt_enhance.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from _lab_layout import (
    NODE_GAP,
    estimated_node_size,
    finalize_layout,
    node_overlap_hits,
)
from _lab_paths import lab_json

from _lab_theme import (
    GOSEE_LTX_I2V_01,
    GOSEE_WAN_I2V_01,
    KLEIN_NEG_STILL,
    KLEIN_STILL,
    LTX_AUDIO_HINT,
    LTX_I2V,
    LTX_T2V,
    LTX_TALKING_AUDIO,
    LTX_TALKING_HEAD,
    WAN_I2V,
    WAN_T2V,
    WAN_VACE,
)

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

KLEIN_NEG_FILM = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
WAN_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, frame stutter, "
    "rubbery motion, melting edges, texture crawl, sudden cuts, watermark, burned-in text"
)
BLURB = (
    "Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, "
    "the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn "
    "Enhance off to use the widget text as-is. Optional style dropdown."
)
PIN_OFF_BLURB = (
    "Prompt enhance is **off** so authored text (recipe, script labels, ACE tags, "
    "or film shots) is encoded as written. Turn Enhance on only if you want the "
    "4B rewriter."
)
PIN_ENHANCE_OFF = frozenset(
    {
        "films/go-see",
        "films/still-here",
        "films/switchyard",
        "stills/talking-head",
        "motion/av/dialogue-8s",
        "motion/av/multishot-8s",
        "motion/av/product-hero",
        "motion/av/first-last-8s",
        "motion/av/audio-to-video-8s",
        "motion/loops/gif-loop",
        "motion/loops/bumper-loop",
        "motion/loops/sticker-loop",
        "motion/silent/orbit-still-5s",
        "motion/silent/push-in-still-5s",
        "motion/silent/parallax-still-5s",
        "dcc/depth-control-8s",
        "dcc/canny-control-8s",
        "dcc/depth-control-shorts",
        "audio/podcast/two-host-episode",
        "audio/podcast/radio-drama",
        "audio/music/rap-draft",
        "audio/music/rap-full",
    }
)


def enhance_pin_off(graph_id: str) -> bool:
    """True when seeded JSON should pin Enhance off (authored / structured text)."""
    gid = str(graph_id or "")
    if gid in PIN_ENHANCE_OFF:
        return True
    if gid.startswith("films/") and "/act-0" in gid:
        return True
    if gid.startswith("music-rap-nill-bye-") or gid.startswith(
        "music-edm-drive-through-"
    ):
        return True
    if gid.startswith("audio/albums/") and not gid.endswith("/cover"):
        return True
    if gid.startswith("audio/music/"):
        return True
    if gid.startswith("audio/dub/"):
        return True
    from _creator_pack3 import pack3_pin_off

    if gid in pack3_pin_off():
        return True
    return False
SHIFT = 460
ENHANCE_H = 420


def overlap_hits(graph: dict[str, Any]) -> list[str]:
    """Return estimated Vue AABB overlap strings (shared lab layout contract)."""
    return node_overlap_hits(graph)


def next_ids(graph: dict[str, Any]) -> tuple[int, int]:
    nid = max(int(n["id"]) for n in graph["nodes"]) + 1
    lid = 1
    if graph.get("links"):
        lid = max(int(link[0]) for link in graph["links"]) + 1
    return nid, lid


def shift_x(graph: dict[str, Any], min_x: float, delta: int) -> None:
    for node in graph["nodes"]:
        if node["pos"][0] >= min_x:
            node["pos"][0] = node["pos"][0] + delta
    for group in graph.get("groups") or []:
        box = group["bounding"]
        left, _top, width, _height = box[0], box[1], box[2], box[3]
        if left >= min_x:
            box[0] = left + delta
        elif left + width > min_x:
            box[2] = width + delta


def remove_node(graph: dict[str, Any], node_id: int) -> None:
    graph["nodes"] = [n for n in graph["nodes"] if int(n["id"]) != node_id]
    graph["links"] = [
        link
        for link in graph.get("links") or []
        if int(link[1]) != node_id and int(link[3]) != node_id
    ]
    live = {int(link[0]) for link in graph.get("links") or []}
    for node in graph["nodes"]:
        for out in node.get("outputs") or []:
            links = out.get("links")
            if isinstance(links, list):
                out["links"] = [lid for lid in links if int(lid) in live]
        for inp in node.get("inputs") or []:
            if inp.get("link") is not None and int(inp["link"]) not in live:
                inp["link"] = None


def clip_by_title(graph: dict[str, Any], title: str) -> dict[str, Any]:
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == title:
            return node
    raise SystemExit(f"missing CLIP {title} in {graph.get('id')}")


def _node_of_type(graph: dict[str, Any], ntype: str) -> dict[str, Any] | None:
    for node in graph["nodes"]:
        if node.get("type") == ntype:
            return node
    return None


def set_neg(graph: dict[str, Any], text: str) -> None:
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative":
            node["widgets_values"] = [text]


def _rewrite_enhance_blurb(body: str, *, pin_off: bool = False) -> str:
    lines = [
        line
        for line in body.splitlines()
        if "XAI_API_KEY" not in line and "leave Enhance off" not in line
    ]
    text = "\n".join(lines).rstrip()
    if pin_off:
        text = (
            text.replace("Prompt enhance is on by default", "Prompt enhance is **off**")
            .replace("Prompt enhance is **on**", "Prompt enhance is **off**")
            .replace("enhance **on**", "enhance **off**")
            .replace("Enhance **on**", "Enhance **off**")
            .replace("Identity-mode enhance is on.", "Identity-mode enhance is off.")
            .replace("enhance is **on**", "enhance is **off**")
        )
        if "Prompt enhance is **off**" not in text and "Enhance **off**" not in text:
            text = text + "\n" + PIN_OFF_BLURB
        return text + "\n"
    if "Prompt enhance is on by default" not in text and "Prompt enhance is **off**" not in text:
        text = text + "\n" + BLURB
    return text + "\n"


def _as_enhance_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return True


def _catalog_for_graph(graph: dict[str, Any]) -> str:
    extra = graph.get("extra") or {}
    return str(extra.get("lab_rel") or graph.get("id") or "")


def normalize_enhance_widgets(graph: dict[str, Any]) -> None:
    """Pad enhance-node widgets. Default enhance true. Identity titles use identity mode."""
    graph_id = str((graph.get("extra") or {}).get("lab_rel") or graph.get("id") or "")
    catalog = _catalog_for_graph(graph)
    for node in graph["nodes"]:
        ntype = node.get("type")
        values = list(node.get("widgets_values") or [])
        title = str(node.get("title") or "")
        if ntype in ("EZKleinPromptEnhance", "EZWanPromptEnhance"):
            if len(values) >= 7:
                sample, prompt, enhance, mode, hint, style, cat = values[:7]
            else:
                sample, cat = "custom", catalog
                prompt = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                default_mode = "t2i" if ntype == "EZKleinPromptEnhance" else "t2v"
                mode = values[2] if len(values) > 2 else default_mode
                hint = values[3] if len(values) > 3 else ""
                style = values[4] if len(values) > 4 else "none"
            enhance = _as_enhance_flag(enhance)
            if ntype == "EZKleinPromptEnhance":
                if "IDENTITY" in title.upper() or mode == "identity":
                    mode = "identity"
                elif "TEXT SWAP" in title.upper() or mode == "text_swap":
                    mode = "text_swap"
                elif "BACKGROUND SWAP" in title.upper() or mode == "background_swap":
                    mode = "background_swap"
                elif "BACKGROUND EDIT" in title.upper() or mode == "background_edit":
                    mode = "background_edit"
                elif mode not in (
                    "t2i",
                    "edit",
                    "identity",
                    "text_swap",
                    "background_swap",
                    "background_edit",
                ):
                    mode = "t2i"
            else:
                if "flf" in graph_id or mode == "flf":
                    mode = "flf"
                elif "vace" in graph_id or mode == "vace":
                    mode = "vace"
                elif "s2v" in graph_id or mode == "s2v":
                    mode = "s2v"
                elif mode not in ("t2v", "i2v", "flf", "vace", "s2v"):
                    mode = "t2v"
            node["widgets_values"] = [
                sample or "custom",
                prompt,
                enhance,
                mode,
                hint,
                style if style else "none",
                cat or catalog,
            ]
        elif ntype == "EZLTXPromptEnhance":
            if len(values) >= 8:
                sample, prompt, enhance, mode, hint, audio, style, cat = values[:8]
            else:
                sample, cat = "custom", catalog
                prompt = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                mode = values[2] if len(values) > 2 else "t2v"
                hint = values[3] if len(values) > 3 else "5 seconds, 24 fps"
                audio = values[4] if len(values) > 4 else ""
                style = values[5] if len(values) > 5 else "none"
            if mode not in ("t2v", "i2v", "iclora"):
                mode = "t2v"
            node["widgets_values"] = [
                sample or "custom",
                prompt,
                _as_enhance_flag(enhance),
                mode,
                hint,
                audio,
                style if style else "none",
                cat or catalog,
            ]
        elif ntype == "EZLongCatPromptEnhance":
            if len(values) >= 7:
                sample, prompt, enhance, mode, hint, style, cat = values[:7]
            else:
                sample, cat = "custom", catalog
                prompt = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                mode = values[2] if len(values) > 2 else "t2v"
                hint = values[3] if len(values) > 3 else "5 seconds, 30 fps"
                style = values[4] if len(values) > 4 else "none"
            if mode not in ("t2v", "i2v", "vc"):
                mode = "t2v"
            node["widgets_values"] = [
                sample or "custom",
                prompt,
                _as_enhance_flag(enhance),
                mode,
                hint,
                style if style else "none",
                cat or catalog,
            ]
        elif ntype == "EZZimagePromptEnhance":
            if len(values) >= 6:
                sample, prompt, enhance, hint, style, cat = values[:6]
            else:
                sample, cat = "custom", catalog
                prompt = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                hint = values[2] if len(values) > 2 else "YouTube 16:9 still"
                style = values[3] if len(values) > 3 else "none"
            node["widgets_values"] = [
                sample or "custom",
                prompt,
                _as_enhance_flag(enhance),
                hint,
                style if style else "none",
                cat or catalog,
            ]
        elif ntype == "EZDreamXPromptEnhance":
            if len(values) >= 7:
                sample, prompt, enhance, hint, audio, style, cat = values[:7]
            else:
                sample, cat = "custom", catalog
                prompt = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                hint = values[2] if len(values) > 2 else "5 seconds, 24 fps"
                audio = values[3] if len(values) > 3 else ""
                style = values[4] if len(values) > 4 else "none"
            node["widgets_values"] = [
                sample or "custom",
                prompt,
                _as_enhance_flag(enhance),
                hint,
                audio,
                style if style else "none",
                cat or catalog,
            ]
        elif ntype == "EZAceStepPromptEnhance":
            if len(values) >= 6:
                sample, tags, lyrics, enhance, mode, cat = values[:6]
            else:
                sample, cat = "custom", catalog
                tags = values[0] if values else ""
                lyrics = values[1] if len(values) > 1 else ""
                enhance = True
                mode = values[3] if len(values) > 3 else "vocal"
            if mode not in ("vocal", "instrumental"):
                mode = "vocal"
            node["widgets_values"] = [
                sample or "custom",
                tags,
                lyrics,
                _as_enhance_flag(enhance),
                mode,
                cat or catalog,
            ]
        elif ntype == "EZNegativePromptEnhance":
            prompt = values[0] if values else ""
            enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
            family = values[2] if len(values) > 2 else "klein"
            if family not in NEGATIVE_FAMILY_IDS:
                family = "klein"
            node["widgets_values"] = [prompt, enhance, family]
        elif ntype == "EZRapLyrics":
            if len(values) >= 4:
                sample, text, enhance, cat = values[0], values[1], values[2], values[3]
            else:
                sample, cat = "custom", catalog
                text = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
            node["widgets_values"] = [
                sample or "custom",
                text,
                _as_enhance_flag(enhance),
                cat or catalog,
            ]
        elif ntype == "EZPodcastScript":
            if len(values) >= 5:
                sample, text, enhance, flavor, cat = values[:5]
            else:
                sample, cat = "custom", catalog
                text = values[0] if values else ""
                enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
                flavor = values[2] if len(values) > 2 else "podcast_two_host"
            node["widgets_values"] = [
                sample or "custom",
                text,
                _as_enhance_flag(enhance),
                flavor,
                cat or catalog,
            ]
        elif ntype == "EZPodcastLearn":
            if len(values) >= 7:
                sample, sources, fmt, duration, fetch, enhance, cat = values[:7]
            else:
                sample, cat = "custom", catalog
                sources = values[0] if values else ""
                fmt = values[1] if len(values) > 1 else "Explainer"
                duration = values[2] if len(values) > 2 else "8 min briefing"
                fetch = values[3] if len(values) > 3 else True
                enhance = _as_enhance_flag(values[4]) if len(values) > 4 else True
            fetch_flag = fetch
            if isinstance(fetch, str):
                fetch_flag = fetch.strip().lower() in {"1", "true", "yes", "on"}
            node["widgets_values"] = [
                sample or "custom",
                sources,
                fmt or "Explainer",
                duration or "8 min briefing",
                bool(fetch_flag),
                _as_enhance_flag(enhance),
                cat or catalog,
            ]
        elif ntype == "EZCreativeResearch":
            if len(values) >= 7:
                sample, text, mode, web, sub, hist, cat = values[:7]
            else:
                sample, cat = "custom", catalog
                text = values[0] if values else ""
                mode = values[1] if len(values) > 1 else "research"
                web = values[2] if len(values) > 2 else True
                sub = values[3] if len(values) > 3 else 2
                hist = values[4] if len(values) > 4 else ""
            node["widgets_values"] = [
                sample or "custom",
                text,
                mode,
                web,
                sub,
                hist,
                cat or catalog,
            ]
        elif ntype == "EZSamplePrompt":
            if len(values) >= 3:
                sample, text, cat = values[0], values[1], values[2]
            else:
                sample, cat = "custom", catalog
                text = values[0] if values else ""
            node["widgets_values"] = [sample or "custom", text, cat or catalog]


def append_note(graph: dict[str, Any]) -> None:
    extra = graph.setdefault("extra", {})
    pin_off = enhance_pin_off(str(extra.get("lab_rel") or graph.get("id") or ""))
    for node in graph["nodes"]:
        if node.get("type") in ("Note", "MarkdownNote"):
            values = node.get("widgets_values") or [""]
            node["widgets_values"] = [
                _rewrite_enhance_blurb(str(values[0]), pin_off=pin_off)
            ]
    extra = graph.setdefault("extra", {})
    note = str(extra.get("lab_note") or "")
    if note:
        extra["lab_note"] = _rewrite_enhance_blurb(note, pin_off=pin_off)


def ensure_enhance(
    graph: dict[str, Any],
    clip: dict[str, Any],
    *,
    ntype: str,
    title: str,
    widgets: list,
    size_h: int,
) -> None:
    existing = _node_of_type(graph, ntype)
    if existing is not None:
        existing["widgets_values"] = widgets
        existing["title"] = title
        return
    wire_enhance(
        graph,
        clip,
        ntype=ntype,
        title=title,
        widgets=widgets,
        size_h=size_h,
    )


def wire_enhance(
    graph: dict[str, Any],
    clip: dict[str, Any],
    *,
    ntype: str,
    title: str,
    widgets: list,
    size_h: int,
) -> None:
    origin_x, origin_y = clip["pos"][0], clip["pos"][1]
    shift_x(graph, origin_x - 1, SHIFT)
    nid, lid = next_ids(graph)
    enhance = {
        "id": nid,
        "type": ntype,
        "pos": [origin_x, origin_y],
        "size": [420, size_h],
        "flags": {},
        "order": max(int(clip.get("order") or 0) - 1, 0),
        "mode": 0,
        "inputs": [],
        "outputs": [
            {
                "name": "prompt",
                "type": "STRING",
                "links": [lid],
                "slot_index": 0,
            }
        ],
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
        "title": title,
    }
    graph["nodes"].append(enhance)
    text_inp = next((i for i in clip.get("inputs") or [] if i.get("name") == "text"), None)
    if text_inp is None:
        clip.setdefault("inputs", []).append(
            {
                "name": "text",
                "type": "STRING",
                "link": lid,
                "widget": {"name": "text"},
            }
        )
        dest_slot = len(clip["inputs"]) - 1
    else:
        text_inp["link"] = lid
        dest_slot = clip["inputs"].index(text_inp)
    graph.setdefault("links", []).append([lid, nid, 0, int(clip["id"]), dest_slot, "STRING"])
    graph["last_node_id"] = nid
    graph["last_link_id"] = lid
    graph["revision"] = int(graph.get("revision") or 0) + 1
    _push_notes_clear(graph)


def _push_notes_clear(graph: dict[str, Any]) -> None:
    for _ in range(24):
        hits = overlap_hits(graph)
        if not hits:
            return
        moved = False
        for node in graph["nodes"]:
            if node.get("type") not in ("Note", "MarkdownNote"):
                continue
            nid = str(node["id"])
            if any(nid + "(" in hit for hit in hits):
                node["pos"][1] = float(node["pos"][1]) + 80
                moved = True
        if not moved:
            return
    raise SystemExit(f"could not clear note overlaps: {overlap_hits(graph)}")


def save(path: Path, graph: dict[str, Any]) -> None:
    finalize_layout(graph)
    path.write_text(json.dumps(graph, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def klein(path: Path, prompt: str, *, neg: str) -> None:
    graph = load(path)
    clip = clip_by_title(graph, "Positive")
    clip["widgets_values"] = [prompt]
    set_neg(graph, neg)
    ensure_enhance(
        graph,
        clip,
        ntype="EZKleinPromptEnhance",
        title="Klein Prompt Enhance",
        widgets=[prompt, True, "t2i", "YouTube 16:9 still", "none"],
        size_h=ENHANCE_H,
    )
    append_note(graph)
    normalize_enhance_widgets(graph)
    save(path, graph)


def wan_i2v(path: Path, prompt: str) -> None:
    graph = load(path)
    if _node_of_type(graph, "EZWanPromptEnhance") is None:
        look = None
        for node in graph["nodes"]:
            if node.get("type") == "CLIPTextEncode" and node.get("title") == "Positive":
                look = node
                break
        if look is not None:
            remove_node(graph, int(look["id"]))
    clip = clip_by_title(graph, "Motion / prompt")
    clip["widgets_values"] = [prompt]
    set_neg(graph, WAN_NEG)
    ensure_enhance(
        graph,
        clip,
        ntype="EZWanPromptEnhance",
        title="Wan Prompt Enhance",
        widgets=[prompt, True, "i2v", "5 seconds, 24 fps", "none"],
        size_h=ENHANCE_H,
    )
    append_note(graph)
    normalize_enhance_widgets(graph)
    save(path, graph)


def wan_t2v(path: Path) -> None:
    graph = load(path)
    if _node_of_type(graph, "EZWanPromptEnhance") is None:
        extra = None
        for node in graph["nodes"]:
            if node.get("type") == "CLIPTextEncode" and node.get("title") == "Positive":
                extra = node
                break
        if extra is not None:
            remove_node(graph, int(extra["id"]))
        clip = clip_by_title(graph, "Positive motion")
        clip["title"] = "Positive"
    else:
        clip = clip_by_title(graph, "Positive")
    clip["widgets_values"] = [WAN_T2V]
    set_neg(graph, WAN_NEG)
    ensure_enhance(
        graph,
        clip,
        ntype="EZWanPromptEnhance",
        title="Wan Prompt Enhance",
        widgets=[WAN_T2V, True, "t2v", "5 seconds, 24 fps", "none"],
        size_h=ENHANCE_H,
    )
    append_note(graph)
    normalize_enhance_widgets(graph)
    save(path, graph)


def ltx_i2v(path: Path, prompt: str, audio: str, title: str) -> None:
    graph = load(path)
    clip = clip_by_title(graph, title)
    clip["widgets_values"] = [prompt]
    set_neg(graph, WAN_NEG)
    ensure_enhance(
        graph,
        clip,
        ntype="EZLTXPromptEnhance",
        title="LTX Prompt Enhance",
        widgets=[prompt, True, "i2v", "5 seconds, 24 fps", audio, "none"],
        size_h=ENHANCE_H,
    )
    append_note(graph)
    normalize_enhance_widgets(graph)
    save(path, graph)


def ltx_t2v(path: Path) -> None:
    graph = load(path)
    clip = clip_by_title(graph, "Positive")
    clip["widgets_values"] = [LTX_T2V]
    set_neg(graph, WAN_NEG)
    ensure_enhance(
        graph,
        clip,
        ntype="EZLTXPromptEnhance",
        title="LTX Prompt Enhance",
        widgets=[LTX_T2V, True, "t2v", "5 seconds, 24 fps", LTX_AUDIO_HINT, "none"],
        size_h=ENHANCE_H,
    )
    append_note(graph)
    normalize_enhance_widgets(graph)
    save(path, graph)


POS_ENHANCE_FAMILY = {
    "EZKleinPromptEnhance": "klein",
    "EZWanPromptEnhance": "wan",
    "EZLTXPromptEnhance": "ltx",
    "EZZimagePromptEnhance": "zimage",
    "EZLongCatPromptEnhance": "longcat",
    "EZDreamXPromptEnhance": "dreamx",
}
NEGATIVE_FAMILY_IDS = frozenset((*POS_ENHANCE_FAMILY.values(), "s2v"))
NEG_ENHANCE_H = 280


def _node_width(node: dict[str, Any]) -> float:
    size = node.get("size", [420, 120])
    if isinstance(size, dict):
        return float(size.get("0", 420))
    return float(size[0])


def _clip_loader_id(
    graph: dict[str, Any],
    clip: dict[str, Any],
    links_by_id: dict[int, list],
) -> int | None:
    inp = next((i for i in clip.get("inputs") or [] if i.get("name") == "clip"), None)
    if not inp or inp.get("link") is None:
        return None
    link = links_by_id.get(int(inp["link"]))
    if link is None:
        return None
    return int(link[1])


def _positive_enhance_source(
    graph: dict[str, Any],
    neg_clip: dict[str, Any],
) -> dict[str, Any] | None:
    links_by_id = {int(link[0]): link for link in graph.get("links") or []}
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    loader = _clip_loader_id(graph, neg_clip, links_by_id)
    candidates: list[dict[str, Any]] = []
    for clip in graph["nodes"]:
        if clip.get("type") != "CLIPTextEncode":
            continue
        if int(clip["id"]) == int(neg_clip["id"]):
            continue
        if "neg" in str(clip.get("title") or "").lower():
            continue
        if loader is not None and _clip_loader_id(graph, clip, links_by_id) != loader:
            continue
        src = _clip_text_source(graph, clip)
        if src is None:
            continue
        if src.get("type") in POS_ENHANCE_FAMILY:
            candidates.append(src)
            continue
        if src.get("type") != "EZPromptJoin":
            continue
        ident_inp = next(
            (i for i in src.get("inputs") or [] if i.get("name") == "identity"),
            None,
        )
        if ident_inp is None or ident_inp.get("link") is None:
            continue
        ident_link = links_by_id.get(int(ident_inp["link"]))
        if ident_link is None:
            continue
        ident_src = by_id.get(int(ident_link[1]))
        if ident_src and ident_src.get("type") in POS_ENHANCE_FAMILY:
            candidates.append(ident_src)
    if candidates:
        return candidates[0]
    for node in graph["nodes"]:
        if node.get("type") in POS_ENHANCE_FAMILY:
            return node
    return None


def _family_for_negative(
    graph: dict[str, Any],
    pos_enh: dict[str, Any] | None,
) -> str:
    if pos_enh is not None:
        mapped = POS_ENHANCE_FAMILY.get(str(pos_enh.get("type") or ""))
        if mapped == "wan":
            values = list(pos_enh.get("widgets_values") or [])
            mode = values[3] if len(values) >= 7 else (
                values[2] if len(values) > 2 else ""
            )
            if str(mode) == "s2v":
                return "s2v"
        if mapped:
            return mapped
    occ = str((graph.get("extra") or {}).get("lab_occupancy") or "").lower()
    if occ in POS_ENHANCE_FAMILY.values():
        return occ
    return "klein"


def _nudge_clear(graph: dict[str, Any], node: dict[str, Any]) -> None:
    nid = str(node["id"])
    for _ in range(36):
        hits = [hit for hit in overlap_hits(graph) if nid + "(" in hit]
        if not hits:
            return
        node["pos"][1] = float(node["pos"][1]) + 80
    for _ in range(12):
        hits = [hit for hit in overlap_hits(graph) if nid + "(" in hit]
        if not hits:
            return
        node["pos"][0] = float(node["pos"][0]) + 40


def _link_positive_to_negative(
    graph: dict[str, Any],
    pos_enh: dict[str, Any],
    neg_enh: dict[str, Any],
    lid: int,
) -> None:
    outputs = pos_enh.setdefault("outputs", [])
    if not outputs:
        outputs.append(
            {
                "name": "prompt",
                "type": "STRING",
                "links": [lid],
                "slot_index": 0,
            }
        )
    else:
        links = outputs[0].setdefault("links", [])
        if not isinstance(links, list):
            outputs[0]["links"] = [lid]
        else:
            links.append(lid)
    inputs = neg_enh.setdefault("inputs", [])
    pos_inp = next((i for i in inputs if i.get("name") == "positive"), None)
    if pos_inp is None:
        inputs.append({"name": "positive", "type": "STRING", "link": lid})
        dest_slot = len(inputs) - 1
    else:
        pos_inp["link"] = lid
        dest_slot = inputs.index(pos_inp)
    graph.setdefault("links", []).append(
        [lid, int(pos_enh["id"]), 0, int(neg_enh["id"]), dest_slot, "STRING"]
    )


def insert_negative_enhance(graph: dict[str, Any]) -> None:
    """Wire EZNegativePromptEnhance into every CLIP Negative encoder."""
    pending: list[dict[str, Any]] = []
    for clip in graph["nodes"]:
        if clip.get("type") != "CLIPTextEncode":
            continue
        if "neg" not in str(clip.get("title") or "").lower():
            continue
        src = _clip_text_source(graph, clip)
        if src is not None and src.get("type") == "EZNegativePromptEnhance":
            continue
        pending.append(clip)
    for clip in pending:
        seed = ""
        values = clip.get("widgets_values") or []
        if values:
            seed = str(values[0] or "")
        pos_enh = _positive_enhance_source(graph, clip)
        family = _family_for_negative(graph, pos_enh)
        clip_x = float(clip["pos"][0])
        clip_y = float(clip["pos"][1])
        if clip_x >= SHIFT:
            origin_x, origin_y = clip_x - SHIFT, clip_y
        else:
            origin_x, origin_y = clip_x + _node_width(clip) + 20, clip_y
        nid, lid = next_ids(graph)
        pos_lid = lid + 1
        enhance: dict[str, Any] = {
            "id": nid,
            "type": "EZNegativePromptEnhance",
            "pos": [origin_x, origin_y],
            "size": [420, NEG_ENHANCE_H],
            "flags": {},
            "order": max(int(clip.get("order") or 0) - 1, 0),
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "links": [lid],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZNegativePromptEnhance"},
            "widgets_values": [seed, True, family],
            "title": "Negative Prompt Enhance",
        }
        graph["nodes"].append(enhance)
        text_inp = next(
            (i for i in clip.get("inputs") or [] if i.get("name") == "text"),
            None,
        )
        if text_inp is None:
            clip.setdefault("inputs", []).append(
                {
                    "name": "text",
                    "type": "STRING",
                    "link": lid,
                    "widget": {"name": "text"},
                }
            )
            dest_slot = len(clip["inputs"]) - 1
        else:
            text_inp["link"] = lid
            dest_slot = clip["inputs"].index(text_inp)
        graph.setdefault("links", []).append(
            [lid, nid, 0, int(clip["id"]), dest_slot, "STRING"]
        )
        if pos_enh is not None:
            _link_positive_to_negative(graph, pos_enh, enhance, pos_lid)
            graph["last_link_id"] = max(int(graph.get("last_link_id") or 0), lid, pos_lid)
        else:
            graph["last_link_id"] = max(int(graph.get("last_link_id") or 0), lid)
        graph["last_node_id"] = max(int(graph.get("last_node_id") or 0), nid)
        graph["revision"] = int(graph.get("revision") or 0) + 1
        _nudge_clear(graph, enhance)


def _clip_text_source(graph: dict[str, Any], clip: dict[str, Any]) -> dict[str, Any] | None:
    text_inp = next((i for i in clip.get("inputs") or [] if i.get("name") == "text"), None)
    if not text_inp or text_inp.get("link") is None:
        return None
    lid = int(text_inp["link"])
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    for link in graph.get("links") or []:
        if int(link[0]) == lid:
            return by_id.get(int(link[1]))
    return None


def insert_join_shot_enhance(graph: dict[str, Any]) -> None:
    """Klein t2i enhance between Prompt Join and CLIP so CLIP shows the rewrite."""
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    pending: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for clip in graph["nodes"]:
        if clip.get("type") != "CLIPTextEncode":
            continue
        title = str(clip.get("title") or "")
        if "neg" in title.lower():
            continue
        src = _clip_text_source(graph, clip)
        if src is None or src.get("type") != "EZPromptJoin":
            continue
        pending.append((src, clip))
    for join, clip in pending:
        hint = "YouTube 16:9 still"
        ident = next(
            (n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance"),
            None,
        )
        if ident and len(ident.get("widgets_values") or []) > 3:
            hint = ident["widgets_values"][3] or hint
        joined = (clip.get("widgets_values") or [""])[0]
        origin_x, origin_y = clip["pos"][0], clip["pos"][1]
        nid, lid = next_ids(graph)
        join_to_enh = lid + 1
        enhance: dict[str, Any] = {
            "id": nid,
            "type": "EZKleinPromptEnhance",
            "pos": [origin_x - 440, origin_y],
            "size": [420, 280],
            "flags": {},
            "order": max(int(clip.get("order") or 0) - 1, 0),
            "mode": 0,
            "inputs": [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "link": None,
                    "widget": {"name": "prompt"},
                }
            ],
            "outputs": [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "links": [lid],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZKleinPromptEnhance"},
            "widgets_values": [joined, True, "t2i", hint, "none"],
            "title": f"{clip.get('title') or 'Shot'} enhance",
        }
        graph["nodes"].append(enhance)
        join_out = (join.get("outputs") or [{}])[0]
        old_links = [int(x) for x in (join_out.get("links") or [])]
        clip_text = next((i for i in clip.get("inputs") or [] if i.get("name") == "text"), None)
        old_lid = int(clip_text["link"]) if clip_text and clip_text.get("link") is not None else None
        enhance["inputs"][0]["link"] = join_to_enh
        if clip_text is None:
            clip.setdefault("inputs", []).append(
                {
                    "name": "text",
                    "type": "STRING",
                    "link": lid,
                    "widget": {"name": "text"},
                }
            )
            dest_slot = len(clip["inputs"]) - 1
        else:
            clip_text["link"] = lid
            dest_slot = clip["inputs"].index(clip_text)
        graph["links"] = [
            link
            for link in graph.get("links") or []
            if old_lid is None or int(link[0]) != old_lid
        ]
        if isinstance(join_out.get("links"), list):
            join_out["links"] = [x for x in old_links if old_lid is None or int(x) != old_lid]
            join_out["links"].append(join_to_enh)
        graph["links"].append([join_to_enh, int(join["id"]), 0, nid, 0, "STRING"])
        graph["links"].append([lid, nid, 0, int(clip["id"]), dest_slot, "STRING"])
        graph["last_node_id"] = max(int(graph.get("last_node_id") or 0), nid)
        graph["last_link_id"] = max(int(graph.get("last_link_id") or 0), lid, join_to_enh)
    _push_notes_clear(graph)


def insert_ace_enhance(graph: dict[str, Any]) -> None:
    """Wire EZAceStepPromptEnhance into ACE-Step encoders that lack tags/lyrics links."""
    for enc in list(graph["nodes"]):
        if enc.get("type") != "TextEncodeAceStepAudio1.5":
            continue
        title = str(enc.get("title") or "")
        if "neg" in title.lower():
            continue
        inputs = enc.setdefault("inputs", [])
        tags_inp = next((i for i in inputs if i.get("name") == "tags"), None)
        lyrics_inp = next((i for i in inputs if i.get("name") == "lyrics"), None)
        if tags_inp and tags_inp.get("link") is not None:
            continue
        if lyrics_inp and lyrics_inp.get("link") is not None:
            continue
        values = list(enc.get("widgets_values") or [])
        tags = values[0] if values else ""
        lyrics = values[1] if len(values) > 1 else ""
        instrumental = not str(lyrics).strip() or "[inst]" in str(lyrics).lower()
        if "instrumental" in str(tags).lower() or "no vocals" in str(tags).lower():
            instrumental = True
        nid, lid = next_ids(graph)
        lid_lyrics = lid + 1
        origin_x, origin_y = enc["pos"][0], enc["pos"][1]
        enhance = {
            "id": nid,
            "type": "EZAceStepPromptEnhance",
            "pos": [origin_x - 440, origin_y],
            "size": [400, 320],
            "flags": {},
            "order": max(int(enc.get("order") or 0) - 1, 0),
            "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "tags", "type": "STRING", "links": [lid], "slot_index": 0},
                {"name": "lyrics", "type": "STRING", "links": [lid_lyrics], "slot_index": 1},
            ],
            "properties": {"Node name for S&R": "EZAceStepPromptEnhance"},
            "widgets_values": [
                tags,
                lyrics,
                not enhance_pin_off(str(graph.get("id") or "")),
                "instrumental" if instrumental else "vocal",
            ],
            "title": f"{title} enhance" if title else "ACE-Step Prompt Enhance",
        }
        graph["nodes"].append(enhance)
        if tags_inp is None:
            inputs.append(
                {
                    "name": "tags",
                    "type": "STRING",
                    "link": lid,
                    "widget": {"name": "tags"},
                }
            )
            tags_slot = len(inputs) - 1
        else:
            tags_inp["link"] = lid
            tags_slot = inputs.index(tags_inp)
        if lyrics_inp is None:
            inputs.append(
                {
                    "name": "lyrics",
                    "type": "STRING",
                    "link": lid_lyrics,
                    "widget": {"name": "lyrics"},
                }
            )
            lyrics_slot = len(inputs) - 1
        else:
            lyrics_inp["link"] = lid_lyrics
            lyrics_slot = inputs.index(lyrics_inp)
        graph.setdefault("links", []).append(
            [lid, nid, 0, int(enc["id"]), tags_slot, "STRING"]
        )
        graph["links"].append(
            [lid_lyrics, nid, 1, int(enc["id"]), lyrics_slot, "STRING"]
        )
        graph["last_node_id"] = nid
        graph["last_link_id"] = lid_lyrics
    _push_notes_clear(graph)


def _set_node_enhance(node: dict[str, Any], on: bool) -> None:
    """Write the enhance boolean on one EZ *PromptEnhance / writer node."""
    ntype = node.get("type")
    values = list(node.get("widgets_values") or [])
    flag = bool(on)
    if ntype == "EZNegativePromptEnhance" or ntype == "EZDubScript":
        while len(values) < 2:
            values.append(flag)
        values[1] = flag
        node["widgets_values"] = values
        return
    if ntype == "EZPodcastLearn":
        idx = 5 if len(values) >= 7 else 4
        while len(values) <= idx:
            values.append(flag)
        values[idx] = flag
        node["widgets_values"] = values
        return
    if ntype in (
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZRapLyrics",
        "EZPodcastScript",
    ):
        idx = 2 if len(values) >= 4 else 1
        while len(values) <= idx:
            values.append(flag)
        values[idx] = flag
        node["widgets_values"] = values
        return
    if ntype == "EZAceStepPromptEnhance":
        idx = 3 if len(values) >= 6 else 2
        while len(values) <= idx:
            values.append(flag)
        values[idx] = flag
        node["widgets_values"] = values


def apply_enhance_policy(graph: dict[str, Any]) -> None:
    """Pin positive Enhance off on authored graphs. Negative rewrite stays on."""
    extra = graph.get("extra") or {}
    gid = str(extra.get("lab_rel") or graph.get("id") or "")
    if any(n.get("type") == "EZPodcastLearn" for n in graph.get("nodes") or []):
        for node in graph.get("nodes") or []:
            if node.get("type") == "EZAceStepPromptEnhance":
                _set_node_enhance(node, False)
    elif enhance_pin_off(gid):
        for node in graph.get("nodes") or []:
            ntype = node.get("type")
            if ntype == "EZDubScript":
                continue
            if ntype in (
                "EZKleinPromptEnhance",
                "EZWanPromptEnhance",
                "EZLTXPromptEnhance",
                "EZAceStepPromptEnhance",
                "EZRapLyrics",
                "EZPodcastScript",
            ):
                _set_node_enhance(node, False)
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZNegativePromptEnhance":
            _set_node_enhance(node, True)
    if not enhance_pin_off(gid):
        return
    if any(n.get("type") == "EZPodcastLearn" for n in graph.get("nodes") or []):
        return
    extra = graph.setdefault("extra", {})
    for key in ("lab_note", "lab_description"):
        raw = extra.get(key)
        if isinstance(raw, str) and raw.strip():
            extra[key] = _rewrite_enhance_blurb(raw, pin_off=True)
    for node in graph.get("nodes") or []:
        if node.get("type") not in ("Note", "MarkdownNote"):
            continue
        values = node.get("widgets_values") or [""]
        node["widgets_values"] = [_rewrite_enhance_blurb(str(values[0]), pin_off=True)]
    if isinstance(extra.get("lab_app_mode"), dict) and gid.startswith("film-"):
        extra["lab_app_mode"]["enhance_off_identity"] = True


def _next_link_id(graph: dict[str, Any]) -> int:
    lid = 1
    if graph.get("links"):
        lid = max(int(link[0]) for link in graph["links"]) + 1
    return lid


def _ensure_named_input(
    node: dict[str, Any],
    name: str,
    ltype: str = "STRING",
    widget: str | None = None,
) -> dict[str, Any]:
    inputs = node.setdefault("inputs", [])
    existing = next((item for item in inputs if item.get("name") == name), None)
    if existing is not None:
        if widget and "widget" not in existing:
            existing["widget"] = {"name": widget}
        return existing
    item: dict[str, Any] = {"name": name, "type": ltype, "link": None}
    if widget:
        item["widget"] = {"name": widget}
    inputs.append(item)
    return item


def _link_string(
    graph: dict[str, Any],
    src: dict[str, Any],
    dst: dict[str, Any],
    dest_name: str,
    *,
    src_slot: int = 0,
    widget: str | None = None,
) -> int | None:
    """Wire src STRING output into dst named input. Skip if already linked from src."""
    dest = _ensure_named_input(dst, dest_name, widget=widget)
    if dest.get("link") is not None:
        lid = int(dest["link"])
        for link in graph.get("links") or []:
            if int(link[0]) == lid and int(link[1]) == int(src["id"]):
                return lid
        return lid
    outputs = src.setdefault("outputs", [])
    while len(outputs) <= src_slot:
        outputs.append(
            {
                "name": "prompt",
                "type": "STRING",
                "links": [],
                "slot_index": len(outputs),
            }
        )
    lid = _next_link_id(graph)
    links = outputs[src_slot].setdefault("links", [])
    if not isinstance(links, list):
        outputs[src_slot]["links"] = [lid]
    else:
        links.append(lid)
        outputs[src_slot]["links"] = links
    dest["link"] = lid
    dest_slot = dst["inputs"].index(dest)
    graph.setdefault("links", []).append(
        [lid, int(src["id"]), src_slot, int(dst["id"]), dest_slot, "STRING"]
    )
    graph["last_link_id"] = max(int(graph.get("last_link_id") or 0), lid)
    return lid


def repair_dest_input_links(graph: dict[str, Any]) -> None:
    """Set dest inputs[slot].link from links[] so Nodes 2.0 keeps the wire."""
    by_id = {int(n["id"]): n for n in graph.get("nodes") or []}
    for link in graph.get("links") or []:
        if not isinstance(link, list) or len(link) < 5:
            continue
        lid, dest, slot = int(link[0]), int(link[3]), int(link[4])
        node = by_id.get(dest)
        if node is None:
            continue
        inputs = node.get("inputs") or []
        if slot >= len(inputs):
            continue
        recorded = inputs[slot].get("link")
        if recorded is None:
            inputs[slot]["link"] = lid


def wire_identity_context_to_ltx(graph: dict[str, Any]) -> None:
    """Fan Klein identity STRING into every LTX enhance context socket."""
    klein = next(
        (n for n in graph.get("nodes") or [] if n.get("type") == "EZKleinPromptEnhance"),
        None,
    )
    if klein is None:
        return
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZLTXPromptEnhance":
            continue
        _link_string(graph, klein, node, "context")


def wire_script_context_to_ace(graph: dict[str, Any]) -> None:
    """Fan podcast script or learn digest STRING into ACE-Step enhance context."""
    learn = next(
        (n for n in graph.get("nodes") or [] if n.get("type") == "EZPodcastLearn"),
        None,
    )
    script = next(
        (n for n in graph.get("nodes") or [] if n.get("type") == "EZPodcastScript"),
        None,
    )
    src = learn if learn is not None else script
    if src is None:
        return
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZAceStepPromptEnhance":
            continue
        _link_string(graph, src, node, "context")


def _graph_ids(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(node["id"]): node for node in graph.get("nodes") or []}


def _graph_links(graph: dict[str, Any]) -> dict[int, list[Any]]:
    return {int(link[0]): link for link in graph.get("links") or []}


def _named_input(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next(
        (item for item in node.get("inputs") or [] if item.get("name") == name),
        None,
    )


def _linked_node(
    graph: dict[str, Any], node: dict[str, Any], name: str
) -> dict[str, Any] | None:
    """Return the node wired into ``name``, if any."""
    item = _named_input(node, name)
    if item is None or item.get("link") is None:
        return None
    link = _graph_links(graph).get(int(item["link"]))
    if link is None:
        return None
    return _graph_ids(graph).get(int(link[1]))


def _unlink_named(graph: dict[str, Any], node: dict[str, Any], name: str) -> None:
    """Drop the link currently wired into ``name``."""
    item = _named_input(node, name)
    if item is None or item.get("link") is None:
        return
    lid = int(item["link"])
    item["link"] = None
    kept: list[list[Any]] = []
    old: list[Any] | None = None
    for link in graph.get("links") or []:
        if int(link[0]) == lid:
            old = link
            continue
        kept.append(link)
    graph["links"] = kept
    if old is None:
        return
    src = _graph_ids(graph).get(int(old[1]))
    if src is None:
        return
    slot = int(old[2])
    outputs = src.get("outputs") or []
    if slot >= len(outputs):
        return
    outputs[slot]["links"] = [
        link_id
        for link_id in (outputs[slot].get("links") or [])
        if int(link_id) != lid
    ]


def _add_typed_link(
    graph: dict[str, Any],
    src: dict[str, Any],
    src_slot: int,
    dst: dict[str, Any],
    dest_name: str,
    ltype: str,
    *,
    widget: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> int:
    """Wire ``src`` slot into ``dst.dest_name``. Returns the new link id."""
    lid = _next_link_id(graph)
    inputs = dst.setdefault("inputs", [])
    dest = _named_input(dst, dest_name)
    if dest is None:
        dest = {"name": dest_name, "type": ltype, "link": None}
        inputs.append(dest)
    dest["type"] = ltype
    dest["link"] = lid
    if widget is not None and "widget" not in dest:
        dest["widget"] = widget
    if extra:
        for key, value in extra.items():
            dest[key] = value
    dest_slot = inputs.index(dest)
    outputs = src.setdefault("outputs", [])
    while len(outputs) <= src_slot:
        outputs.append(
            {
                "name": ltype.lower(),
                "type": ltype,
                "links": [],
                "slot_index": len(outputs),
            }
        )
    slot_links = outputs[src_slot].setdefault("links", [])
    if not isinstance(slot_links, list):
        outputs[src_slot]["links"] = [lid]
    else:
        slot_links.append(lid)
    graph.setdefault("links", []).append(
        [lid, int(src["id"]), int(src_slot), int(dst["id"]), dest_slot, ltype]
    )
    graph["last_link_id"] = lid
    return lid


def _relink_named(
    graph: dict[str, Any],
    dst: dict[str, Any],
    dest_name: str,
    src: dict[str, Any],
    src_slot: int,
    ltype: str,
) -> None:
    _unlink_named(graph, dst, dest_name)
    _add_typed_link(graph, src, src_slot, dst, dest_name, ltype)


def _place_cursor(graph: dict[str, Any], skip: dict[str, Any] | None = None) -> list[float]:
    """Right-hand column origin, stored on the graph until repair finishes."""
    cursor = graph.get("_ez_cursor")
    if isinstance(cursor, list) and len(cursor) == 2:
        return cursor
    max_right = 40.0
    top = 80.0
    for node in graph.get("nodes") or []:
        if node is skip:
            continue
        pos = node.get("pos") or [0, 0]
        width, _height = estimated_node_size(node)
        max_right = max(max_right, float(pos[0]) + width)
    for group in graph.get("groups") or []:
        box = group.get("bounding") or [0, 0, 0, 0]
        max_right = max(max_right, float(box[0]) + float(box[2]))
    graph["_ez_cursor"] = [max_right + NODE_GAP, top]
    return graph["_ez_cursor"]


def _place_new(graph: dict[str, Any], node: dict[str, Any]) -> None:
    cursor = _place_cursor(graph, skip=node)
    node["pos"] = [cursor[0], cursor[1]]
    _width, height = estimated_node_size(node)
    cursor[1] = cursor[1] + height + NODE_GAP


def _copy_size(node: dict[str, Any], default: list[float]) -> list[float]:
    size = node.get("size") or default
    if isinstance(size, dict):
        return [float(size.get("0", default[0])), float(size.get("1", default[1]))]
    return [float(size[0]), float(size[1])]


def _walk_conditioning(
    graph: dict[str, Any], start: dict[str, Any] | None, prefer: str
) -> dict[str, Any] | None:
    """Walk backward along ``prefer`` / conditioning to a CLIPTextEncode."""
    seen: set[int] = set()
    current = start
    role = prefer
    while current is not None and int(current["id"]) not in seen:
        seen.add(int(current["id"]))
        if current.get("type") == "CLIPTextEncode":
            return current
        inputs = current.get("inputs") or []
        chosen: dict[str, Any] | None = None
        for name in (role, "conditioning"):
            chosen = next(
                (
                    item
                    for item in inputs
                    if item.get("name") == name and item.get("link") is not None
                ),
                None,
            )
            if chosen is not None:
                break
        if chosen is None:
            cands = [
                item
                for item in inputs
                if str(item.get("type") or "") == "CONDITIONING"
                and item.get("link") is not None
            ]
            if len(cands) != 1:
                return None
            chosen = cands[0]
        if chosen is None:
            return None
        link = _graph_links(graph).get(int(chosen["link"]))
        if link is None:
            return None
        current = _graph_ids(graph).get(int(link[1]))
        role = str(chosen.get("name") or role)
    return None


def _sampler_pairs(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """KSampler positive/negative CLIP pairs and their text sources."""
    pairs: list[dict[str, Any]] = []
    links = _graph_links(graph)
    ids = _graph_ids(graph)
    for sampler in graph.get("nodes") or []:
        if sampler.get("type") not in ("KSampler", "KSamplerAdvanced"):
            continue
        pos_in = _named_input(sampler, "positive")
        neg_in = _named_input(sampler, "negative")
        if (
            pos_in is None
            or neg_in is None
            or pos_in.get("link") is None
            or neg_in.get("link") is None
        ):
            continue
        pos_link = links.get(int(pos_in["link"]))
        neg_link = links.get(int(neg_in["link"]))
        if pos_link is None or neg_link is None:
            continue
        pos_clip = _walk_conditioning(
            graph, ids.get(int(pos_link[1])), "positive"
        )
        neg_clip = _walk_conditioning(
            graph, ids.get(int(neg_link[1])), "negative"
        )
        if pos_clip is None or neg_clip is None:
            continue
        pairs.append(
            {
                "sampler": sampler,
                "pos_src": _linked_node(graph, pos_clip, "text"),
                "neg_clip": neg_clip,
                "neg_src": _linked_node(graph, neg_clip, "text"),
                "direct": ids.get(int(neg_link[1])),
            }
        )
    return pairs


def _append_node(graph: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    graph.setdefault("nodes", []).append(node)
    graph["last_node_id"] = max(int(graph.get("last_node_id") or 0), int(node["id"]))
    _place_new(graph, node)
    return node


def _clone_negative_enhance(
    graph: dict[str, Any], template: dict[str, Any], pos_src: dict[str, Any]
) -> dict[str, Any]:
    nid, _lid = next_ids(graph)
    values = list(template.get("widgets_values") or ["", True, "klein"])
    while len(values) < 3:
        values.append(True if len(values) == 1 else "klein")
    values[1] = True
    node = _append_node(
        graph,
        {
            "id": nid,
            "type": "EZNegativePromptEnhance",
            "pos": [0, 0],
            "size": _copy_size(template, [420.0, 280.0]),
            "flags": {},
            "order": int(template.get("order") or 0),
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "links": [],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZNegativePromptEnhance"},
            "widgets_values": values,
            "title": f"Negative {pos_src.get('title') or 'shot'}",
        },
    )
    _relink_named(graph, node, "positive", pos_src, 0, "STRING")
    return node


def _clone_negative_clip(
    graph: dict[str, Any], template: dict[str, Any], text_src: dict[str, Any]
) -> dict[str, Any]:
    nid, _lid = next_ids(graph)
    node = _append_node(
        graph,
        {
            "id": nid,
            "type": "CLIPTextEncode",
            "pos": [0, 0],
            "size": _copy_size(template, [400.0, 200.0]),
            "flags": {},
            "order": int(template.get("order") or 0),
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "CONDITIONING",
                    "type": "CONDITIONING",
                    "links": [],
                    "slot_index": 0,
                }
            ],
            "properties": dict(
                template.get("properties") or {"Node name for S&R": "CLIPTextEncode"}
            ),
            "widgets_values": list(template.get("widgets_values") or [""]),
            "title": f"Negative {text_src.get('title') or 'shot'}",
        },
    )
    links = _graph_links(graph)
    ids = _graph_ids(graph)
    for item in template.get("inputs") or []:
        name = str(item.get("name") or "")
        if name == "text":
            _add_typed_link(
                graph,
                text_src,
                0,
                node,
                "text",
                "STRING",
                widget={"name": "text"},
            )
            continue
        if item.get("link") is None:
            copied = {key: value for key, value in item.items() if key != "link"}
            copied["link"] = None
            node.setdefault("inputs", []).append(copied)
            continue
        old = links.get(int(item["link"]))
        if old is None:
            continue
        src = ids.get(int(old[1]))
        if src is None:
            continue
        extra = {"shape": item["shape"]} if "shape" in item else None
        widget = item.get("widget") if isinstance(item.get("widget"), dict) else None
        _add_typed_link(
            graph,
            src,
            int(old[2]),
            node,
            name,
            str(old[5]),
            widget=widget,
            extra=extra,
        )
    return node


def _clone_reference_latent(
    graph: dict[str, Any], template: dict[str, Any], cond_clip: dict[str, Any]
) -> dict[str, Any]:
    nid, _lid = next_ids(graph)
    node = _append_node(
        graph,
        {
            "id": nid,
            "type": "ReferenceLatent",
            "pos": [0, 0],
            "size": _copy_size(template, [280.0, 80.0]),
            "flags": {},
            "order": int(template.get("order") or 0),
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "CONDITIONING",
                    "type": "CONDITIONING",
                    "links": [],
                    "slot_index": 0,
                }
            ],
            "properties": dict(
                template.get("properties") or {"Node name for S&R": "ReferenceLatent"}
            ),
            "widgets_values": list(template.get("widgets_values") or []),
            "title": str(template.get("title") or "Negative + identity plate"),
        },
    )
    links = _graph_links(graph)
    ids = _graph_ids(graph)
    for item in template.get("inputs") or []:
        name = str(item.get("name") or "")
        if name == "conditioning":
            _add_typed_link(graph, cond_clip, 0, node, "conditioning", "CONDITIONING")
            continue
        if item.get("link") is None:
            continue
        old = links.get(int(item["link"]))
        if old is None:
            continue
        src = ids.get(int(old[1]))
        if src is None:
            continue
        extra = {"shape": item["shape"]} if "shape" in item else None
        _add_typed_link(
            graph, src, int(old[2]), node, name, str(old[5]), extra=extra
        )
    return node


def _split_shared_join_negatives(graph: dict[str, Any]) -> bool:
    """Give each Prompt Join its own negative enhance and CLIP."""
    changed = False
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for pair in _sampler_pairs(graph):
        groups[int(pair["neg_clip"]["id"])].append(pair)
    for group in groups.values():
        sources: list[dict[str, Any]] = []
        joined = True
        for pair in group:
            src = pair["pos_src"]
            if not isinstance(src, dict) or src.get("type") != "EZPromptJoin":
                joined = False
                break
            sources.append(src)
        if not joined or len({int(src["id"]) for src in sources}) < 2:
            continue
        template = group[0]["neg_src"]
        if not isinstance(template, dict) or template.get("type") != "EZNegativePromptEnhance":
            continue
        ordered = sorted(group, key=lambda pair: int(pair["sampler"]["id"]))
        keep = ordered[0]
        keep_src = keep["pos_src"]
        _relink_named(graph, template, "positive", keep_src, 0, "STRING")
        _set_node_enhance(template, True)
        built: dict[int, dict[str, Any]] = {
            int(keep_src["id"]): {"clip": keep["neg_clip"]}
        }
        changed = True
        for pair in ordered[1:]:
            src = pair["pos_src"]
            sid = int(src["id"])
            if sid not in built:
                enh = _clone_negative_enhance(graph, template, src)
                clip = _clone_negative_clip(graph, keep["neg_clip"], enh)
                built[sid] = {"clip": clip}
            slot = built[sid]
            direct = pair["direct"]
            if isinstance(direct, dict) and direct.get("type") == "ReferenceLatent":
                ref = slot.get("ref")
                if not isinstance(ref, dict):
                    ref = _clone_reference_latent(graph, direct, slot["clip"])
                    slot["ref"] = ref
                _relink_named(graph, pair["sampler"], "negative", ref, 0, "CONDITIONING")
            else:
                _relink_named(
                    graph, pair["sampler"], "negative", slot["clip"], 0, "CONDITIONING"
                )
    return changed


def _bundle_film_ltx(graph: dict[str, Any]) -> bool:
    """Point the shared film LTX negative at every shot's final prompt."""
    extra = graph.get("extra") or {}
    gid = str(extra.get("lab_rel") or graph.get("id") or "")
    if not gid.startswith("films/"):
        return False
    sources: list[dict[str, Any]] = []
    seen: set[int] = set()
    for node in graph.get("nodes") or []:
        if node.get("type") != "CLIPTextEncode":
            continue
        if "neg" in str(node.get("title") or "").lower():
            continue
        src = _linked_node(graph, node, "text")
        if src is None or src.get("type") != "EZLTXPromptEnhance":
            continue
        if int(src["id"]) in seen:
            continue
        seen.add(int(src["id"]))
        sources.append(src)
    sources.sort(key=lambda node: int(node["id"]))
    if len(sources) < 2:
        return False
    negative = None
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZNegativePromptEnhance":
            continue
        values = node.get("widgets_values") or []
        family = str(values[2]) if len(values) > 2 else ""
        if family == "ltx":
            negative = node
            break
    if negative is None:
        return False
    current = _linked_node(graph, negative, "positive")
    if current is not None and current.get("type") == "EZPromptBundle":
        linked: list[int] = []
        for item in current.get("inputs") or []:
            if item.get("link") is None:
                continue
            origin = _graph_ids(graph).get(
                int(_graph_links(graph)[int(item["link"])][1])
            )
            if origin is not None:
                linked.append(int(origin["id"]))
        if linked == [int(node["id"]) for node in sources]:
            return False
    nid, _lid = next_ids(graph)
    bundle = _append_node(
        graph,
        {
            "id": nid,
            "type": "EZPromptBundle",
            "pos": [0, 0],
            "size": [420.0, 200.0],
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "links": [],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZPromptBundle"},
            "widgets_values": [],
            "title": "Shot prompt bundle",
        },
    )
    for index, src in enumerate(sources, start=1):
        _add_typed_link(graph, src, 0, bundle, f"text_{index:02d}", "STRING")
    _relink_named(graph, negative, "positive", bundle, 0, "STRING")
    return True


def _retarget_singleton_negatives(graph: dict[str, Any]) -> bool:
    """Point a 1:1 negative at the positive CLIP's text source."""
    changed = False
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for pair in _sampler_pairs(graph):
        groups[int(pair["neg_clip"]["id"])].append(pair)
    for group in groups.values():
        sources = [pair["pos_src"] for pair in group]
        if any(not isinstance(src, dict) for src in sources):
            continue
        ids = {int(src["id"]) for src in sources if isinstance(src, dict)}
        if len(ids) != 1:
            continue
        src = sources[0]
        negative = group[0]["neg_src"]
        if (
            not isinstance(negative, dict)
            or negative.get("type") != "EZNegativePromptEnhance"
            or not isinstance(src, dict)
        ):
            continue
        current = _linked_node(graph, negative, "positive")
        if current is not None and current.get("type") == "EZPromptBundle":
            continue
        if current is not None and int(current["id"]) == int(src["id"]):
            continue
        _relink_named(graph, negative, "positive", src, 0, "STRING")
        changed = True
    return changed


def repair_negative_sources(graph: dict[str, Any]) -> bool:
    """Pin negative rewrite on and feed it each shot's final positive.

    Args:
        graph: Serialized lab graph. Mutated in place.

    Returns:
        True when nodes, links, or the negative enhance flag changed.
    """
    changed = _bundle_film_ltx(graph)
    changed = _split_shared_join_negatives(graph) or changed
    changed = _retarget_singleton_negatives(graph) or changed
    from _stamp_app_mode import stamp_rewrite_negative

    changed = stamp_rewrite_negative(graph) or changed
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZNegativePromptEnhance":
            continue
        values = node.get("widgets_values") or []
        if len(values) < 2 or values[1] is not True:
            changed = True
        _set_node_enhance(node, True)
    graph.pop("_ez_cursor", None)
    if changed:
        repair_dest_input_links(graph)
        graph["revision"] = int(graph.get("revision") or 0) + 1
    return changed


def enable_lab_graph(graph: dict[str, Any]) -> None:
    """Wire ACE tags, normalize widgets, then apply the on/off enhance policy."""
    insert_ace_enhance(graph)
    insert_negative_enhance(graph)
    wire_identity_context_to_ltx(graph)
    wire_script_context_to_ace(graph)
    repair_dest_input_links(graph)
    normalize_enhance_widgets(graph)
    apply_enhance_policy(graph)
    extra = graph.setdefault("extra", {})
    gid = str(extra.get("lab_rel") or graph.get("id") or "")
    if isinstance(extra.get("lab_app_mode"), dict) and not enhance_pin_off(gid):
        extra["lab_app_mode"]["enhance_off_identity"] = False
    if isinstance(extra.get("lab_dcc"), dict) and "enhance" in extra["lab_dcc"]:
        extra["lab_dcc"]["enhance"] = True
    if isinstance(extra.get("lab_identity"), dict) and "enhance" in extra["lab_identity"]:
        extra["lab_identity"]["enhance"] = True
    append_note(graph)


def main() -> None:
    klein(lab_json("stills/still-draft.json"), KLEIN_STILL, neg=KLEIN_NEG_STILL)
    klein(lab_json("stills/still-hero.json"), KLEIN_STILL, neg=KLEIN_NEG_STILL)
    wan_i2v(lab_json("motion/silent/still-to-video-5s.json"), WAN_I2V)
    wan_t2v(lab_json("motion/silent/text-to-video-5s.json"))
    wan_i2v(lab_json("motion/silent/still-to-shot.json"), GOSEE_WAN_I2V_01)
    wan_i2v(lab_json("motion/silent/first-last-5s.json"), WAN_I2V)
    wan_i2v(lab_json("motion/silent/vace-join.json"), WAN_VACE)
    wan_i2v(lab_json("optional/still-to-video-a14b.json"), WAN_I2V)
    ltx_i2v(
        lab_json("motion/av/still-to-video-8s.json"),
        LTX_I2V,
        LTX_AUDIO_HINT,
        "Motion / prompt",
    )
    ltx_t2v(lab_json("motion/av/text-to-video-8s.json"))
    ltx_i2v(
        lab_json("motion/av/still-to-shot.json"),
        GOSEE_LTX_I2V_01,
        LTX_AUDIO_HINT,
        "Motion + audio",
    )
    ltx_i2v(
        lab_json("stills/talking-head.json"),
        LTX_TALKING_HEAD,
        LTX_TALKING_AUDIO,
        "Motion / prompt",
    )
    print("wired prompt-enhance nodes")
    from _lab_paths import lab_graph_paths

    for path in lab_graph_paths():
        graph = load(path)
        insert_negative_enhance(graph)
        normalize_enhance_widgets(graph)
        apply_enhance_policy(graph)
        save(path, graph)
    print("wired negative-enhance nodes")


if __name__ == "__main__":
    main()
