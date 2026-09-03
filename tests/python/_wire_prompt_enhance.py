"""One-shot helper: rewrite lab CLIP prompts and wire enhance nodes.

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_wire_prompt_enhance.py
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_theme import (
    KLEIN_NEG_STILL,
    KLEIN_STILL,
    LTX_AUDIO_HINT,
    LTX_I2V,
    LTX_T2V,
    WAN_I2V,
    WAN_T2V,
)

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

KLEIN_NEG_FILM = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
KLEIN_GOSEE = (
    "First-person photoreal dawn running still. An olive windbreaker and worn black "
    "gloves stay in frame, hands pumping at the edges as wet tar and unmarked rooftops "
    "fill the view. Identity lock for the whole short. No violence."
)
KLEIN_STILLHERE = (
    "Third-person household morning still. One cream ceramic mug with a hairline chip "
    "on the rim sits on a honey-oak table in first light. White subway tile backsplash, "
    "one linen curtain at a single window. Unmarked kitchen, empty of brands. The mug "
    "is the identity lock. SFW, no real likenesses."
)
KLEIN_SWITCHYARD = (
    "Night freight-yard still in rain. Three generic unmarked boxcars sit on wet ballast "
    "under one yard lamp. Photoreal, empty of railroad company marks. Identity lock for the short."
)
WAN_GOSEE_I2V = (
    "First-person running camera. Olive windbreaker and worn black gloves; arms pump "
    "at the edges of the frame. Dawn rooftop, pigeon scatter. Footfalls on wet tar. "
    "Continuous forward run. Keep the start-image identity locked. One continuous "
    "5.00 second take at 24 fps."
)
WAN_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, frame stutter, "
    "rubbery motion, melting edges, texture crawl, sudden cuts, watermark, burned-in text"
)
LTX_GOSEE_I2V = (
    "The start image holds as the first frame. First-person running camera as gloved "
    "hands pump at the edges of the frame on a dawn rooftop. Footfalls on wet tar, "
    "pigeons scatter, continuous forward run. Breath sits close to the lens, wind in "
    "the hood, tar grit under shoes. No score, no music, no licensed songs."
)
BLURB = (
    "Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, "
    "the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn "
    "Enhance off to use the widget text as-is. Optional style dropdown."
)
SHIFT = 460
ENHANCE_H = 420


def overlap_hits(graph: dict) -> list[str]:
    pad = 20
    boxes = []
    for node in graph["nodes"]:
        x, y = node["pos"]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (
                node["id"],
                node["type"],
                x - pad,
                y - pad,
                x + width + pad,
                y + height + pad,
            )
        )
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                hits.append(f"{a[0]}({a[1]}) vs {b[0]}({b[1]})")
    return hits


def next_ids(graph: dict) -> tuple[int, int]:
    nid = max(int(n["id"]) for n in graph["nodes"]) + 1
    lid = 1
    if graph.get("links"):
        lid = max(int(link[0]) for link in graph["links"]) + 1
    return nid, lid


def shift_x(graph: dict, min_x: float, delta: int) -> None:
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


def remove_node(graph: dict, node_id: int) -> None:
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


def clip_by_title(graph: dict, title: str) -> dict:
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == title:
            return node
    raise SystemExit(f"missing CLIP {title} in {graph.get('id')}")


def _node_of_type(graph: dict, ntype: str) -> dict | None:
    for node in graph["nodes"]:
        if node.get("type") == ntype:
            return node
    return None


def set_neg(graph: dict, text: str) -> None:
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative":
            node["widgets_values"] = [text]


def _rewrite_enhance_blurb(body: str) -> str:
    lines = [
        line
        for line in body.splitlines()
        if "XAI_API_KEY" not in line and "leave Enhance off" not in line
    ]
    text = "\n".join(lines).rstrip()
    if "Prompt enhance is on by default" not in text:
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


def normalize_enhance_widgets(graph: dict) -> None:
    """Pad enhance-node widgets. Keep an existing enhance flag; default true if missing."""
    for node in graph["nodes"]:
        ntype = node.get("type")
        values = list(node.get("widgets_values") or [])
        if ntype in ("EZKleinPromptEnhance", "EZWanPromptEnhance"):
            prompt = values[0] if values else ""
            enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
            mode = values[2] if len(values) > 2 else ("t2i" if ntype == "EZKleinPromptEnhance" else "t2v")
            hint = values[3] if len(values) > 3 else ""
            style = values[4] if len(values) > 4 else "none"
            if style != "none" and len(values) < 5:
                style = "none"
            node["widgets_values"] = [prompt, enhance, mode, hint, style if style else "none"]
        elif ntype == "EZLTXPromptEnhance":
            prompt = values[0] if values else ""
            enhance = _as_enhance_flag(values[1]) if len(values) > 1 else True
            mode = values[2] if len(values) > 2 else "t2v"
            hint = values[3] if len(values) > 3 else "5 seconds, 24 fps"
            audio = values[4] if len(values) > 4 else ""
            style = values[5] if len(values) > 5 else "none"
            node["widgets_values"] = [prompt, enhance, mode, hint, audio, style if style else "none"]


def append_note(graph: dict) -> None:
    for node in graph["nodes"]:
        if node.get("type") in ("Note", "MarkdownNote"):
            values = node.get("widgets_values") or [""]
            node["widgets_values"] = [_rewrite_enhance_blurb(str(values[0]))]
    extra = graph.setdefault("extra", {})
    note = str(extra.get("lab_note") or "")
    if note:
        extra["lab_note"] = _rewrite_enhance_blurb(note)


def ensure_enhance(
    graph: dict,
    clip: dict,
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
    graph: dict,
    clip: dict,
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


def _push_notes_clear(graph: dict) -> None:
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


def save(path: Path, graph: dict) -> None:
    hits = overlap_hits(graph)
    if hits:
        raise SystemExit(f"overlap in {path.name}: {hits}")
    path.write_text(json.dumps(graph, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load(path: Path) -> dict:
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


def main() -> None:
    klein(WF / "klein-still-draft-lab-example.json", KLEIN_STILL, neg=KLEIN_NEG_STILL)
    klein(WF / "klein-still-hero-lab-example.json", KLEIN_STILL, neg=KLEIN_NEG_STILL)
    wan_i2v(WF / "wan-i2v-5s-lab-example.json", WAN_I2V)
    wan_t2v(WF / "wan-t2v-5s-lab-example.json")
    ltx_i2v(
        WF / "ltx-i2v-5s-lab-example.json",
        LTX_I2V,
        LTX_AUDIO_HINT,
        "Motion / prompt",
    )
    ltx_t2v(WF / "ltx-t2v-5s-lab-example.json")
    print("wired prompt-enhance nodes")


if __name__ == "__main__":
    main()
