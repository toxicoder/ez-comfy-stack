"""One-shot helper: rewrite lab CLIP prompts and wire enhance nodes.

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_wire_prompt_enhance.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

KLEIN_STILL = (
    "A photoreal still photograph of a small-town main street at golden hour. "
    "A single red bicycle leans against a brick storefront. Warm sidelight rakes "
    "the brick and the bicycle's chrome. Shot on a 24mm lens at eye level, framed "
    "for YouTube 16:9. Unmarked facades, empty of signage, clean surfaces without lettering."
)
KLEIN_NEG = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
KLEIN_GOSEE = (
    "First-person photoreal dawn travel still. An olive windbreaker and worn black "
    "gloves stay in frame, hands visible against wet tar. Unmarked rooftops, empty "
    "of signage. Identity lock for the whole short. No violence."
)
KLEIN_STILLHERE = (
    "Third-person household morning still. A plain ceramic mug sits on a wooden table "
    "in first light. Unmarked kitchen, empty of brands. The mug is the identity lock. "
    "SFW, no real likenesses."
)
KLEIN_SWITCHYARD = (
    "Night freight-yard still in rain. Generic unmarked boxcars sit on wet ballast "
    "under a yard lamp. Photoreal, empty of railroad company marks. Identity lock for the short."
)
WAN_T2V = (
    "A red bicycle leans against a brick storefront on a small-town main street at "
    "golden hour, unmarked facades empty of signage. Warm sidelight rakes the brick "
    "and chrome. Leaves and a shop flag stir slowly in a light breeze while a pedestrian "
    "crosses the street in the far background. The camera dollies in slowly toward the "
    "bicycle over five seconds. Photoreal cinematic motion, 24mm, shallow depth of field, "
    "YouTube 16:9."
)
WAN_I2V = (
    "Slow cinematic dolly-in toward the bicycle. Leaves and a shop flag stir in a light "
    "breeze. A pedestrian crosses in the background. Keep the start-image identity locked. "
    "One continuous five-second take at 24 fps."
)
WAN_GOSEE_I2V = (
    "First-person travel camera. Hands in an olive windbreaker and worn black gloves plant "
    "on wet tar. Slow push toward the parapet; pigeons scatter. Vault the parapet. Parkour "
    "is transportation. Keep the start-image identity locked. One continuous 5.00 second take "
    "at 24 fps."
)
WAN_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, frame stutter, "
    "rubbery motion, melting edges, texture crawl, sudden cuts, watermark, burned-in text"
)
LTX_T2V = (
    "A wide photoreal shot of a small-town main street at golden hour. A red bicycle leans "
    "against a brick storefront as warm sidelight rakes the brick and chrome. Leaves and a "
    "shop flag stir in a light breeze while a pedestrian crosses in the background. The camera "
    "dollies in slowly toward the bicycle. Soft wind rustles the flag as distant footsteps tap "
    "the pavement and a faint shop bell clinks once. Unmarked facades sit empty of signage. "
    "No music and no score."
)
LTX_I2V = (
    "The start image holds as the first frame. The camera dollies in slowly toward the bicycle "
    "while leaves and a shop flag stir in a light breeze and a pedestrian crosses in the "
    "background. Soft wind rustles the flag as distant footsteps tap the pavement and a faint "
    "shop bell clinks once. The storefront and bicycle identity stay locked. No music and no score."
)
LTX_GOSEE_I2V = (
    "The start image holds as the first frame. First-person travel camera as gloved hands plant "
    "on wet tar at dawn. The view pushes toward the parapet while pigeons scatter, then vaults "
    "it. Parkour is transportation. Breath sits close to the lens, wind in the hood, tar grit "
    "under gloves. No score, no music, no licensed songs."
)
BLURB = (
    "Prompt enhance: a Klein/Wan/LTX Prompt Enhance node sits upstream of CLIP. "
    "Leave Enhance off to use this canned prompt. Set Enhance true and XAI_API_KEY "
    "to rewrite a lazy sentence."
)
SHIFT = 460


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


def set_neg(graph: dict, text: str) -> None:
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative":
            node["widgets_values"] = [text]


def append_note(graph: dict) -> None:
    for node in graph["nodes"]:
        if node.get("type") in ("Note", "MarkdownNote"):
            values = node.get("widgets_values") or [""]
            body = str(values[0])
            if "Prompt enhance:" not in body:
                node["widgets_values"] = [body.rstrip() + "\n" + BLURB + "\n"]
    extra = graph.setdefault("extra", {})
    note = str(extra.get("lab_note") or "")
    if note and "Prompt enhance:" not in note:
        extra["lab_note"] = note.rstrip() + "\n" + BLURB + "\n"


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


def klein(path: Path, prompt: str) -> None:
    graph = load(path)
    clip = clip_by_title(graph, "Positive")
    clip["widgets_values"] = [prompt]
    set_neg(graph, KLEIN_NEG)
    wire_enhance(
        graph,
        clip,
        ntype="EZKleinPromptEnhance",
        title="Klein Prompt Enhance",
        widgets=[prompt, False, "t2i", "YouTube 16:9 still"],
        size_h=280,
    )
    append_note(graph)
    save(path, graph)


def wan_i2v(path: Path, prompt: str) -> None:
    graph = load(path)
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
    wire_enhance(
        graph,
        clip,
        ntype="EZWanPromptEnhance",
        title="Wan Prompt Enhance",
        widgets=[prompt, False, "i2v", "5 seconds, 24 fps"],
        size_h=280,
    )
    append_note(graph)
    save(path, graph)


def wan_t2v(path: Path) -> None:
    graph = load(path)
    extra = None
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Positive":
            extra = node
            break
    if extra is not None:
        remove_node(graph, int(extra["id"]))
    clip = clip_by_title(graph, "Positive motion")
    clip["title"] = "Positive"
    clip["widgets_values"] = [WAN_T2V]
    set_neg(graph, WAN_NEG)
    wire_enhance(
        graph,
        clip,
        ntype="EZWanPromptEnhance",
        title="Wan Prompt Enhance",
        widgets=[WAN_T2V, False, "t2v", "5 seconds, 24 fps"],
        size_h=280,
    )
    append_note(graph)
    save(path, graph)


def ltx_i2v(path: Path, prompt: str, audio: str, title: str) -> None:
    graph = load(path)
    clip = clip_by_title(graph, title)
    clip["widgets_values"] = [prompt]
    set_neg(graph, WAN_NEG)
    wire_enhance(
        graph,
        clip,
        ntype="EZLTXPromptEnhance",
        title="LTX Prompt Enhance",
        widgets=[prompt, False, "i2v", "5 seconds, 24 fps", audio],
        size_h=340,
    )
    append_note(graph)
    save(path, graph)


def ltx_t2v(path: Path) -> None:
    graph = load(path)
    clip = clip_by_title(graph, "Positive")
    clip["widgets_values"] = [LTX_T2V]
    set_neg(graph, WAN_NEG)
    wire_enhance(
        graph,
        clip,
        ntype="EZLTXPromptEnhance",
        title="LTX Prompt Enhance",
        widgets=[LTX_T2V, False, "t2v", "5 seconds, 24 fps", "soft wind, distant footsteps, shop bell, no score"],
        size_h=340,
    )
    append_note(graph)
    save(path, graph)


def main() -> None:
    klein(WF / "still-draft-lab-example.json", KLEIN_STILL)
    klein(WF / "still-hero-lab-example.json", KLEIN_STILL)
    klein(WF / "still-studio-lab-example.json", KLEIN_STILL)
    klein(WF / "shorts" / "go-see-90s-lab-example.json", KLEIN_GOSEE)
    klein(WF / "shorts" / "still-here-90s-lab-example.json", KLEIN_STILLHERE)
    klein(WF / "shorts" / "switchyard-90s-lab-example.json", KLEIN_SWITCHYARD)
    wan_i2v(WF / "wan-i2v-draft-lab-example.json", WAN_I2V)
    wan_i2v(WF / "wan-shot-lab-example.json", WAN_I2V)
    wan_i2v(WF / "shorts" / "bridge-wan-lab-example.json", WAN_GOSEE_I2V)
    wan_t2v(WF / "wan-t2v-draft-lab-example.json")
    ltx_i2v(
        WF / "ltx-i2v-hero-lab-example.json",
        LTX_I2V,
        "soft wind, distant footsteps, shop bell, no score",
        "Motion / prompt",
    )
    ltx_i2v(
        WF / "shorts" / "bridge-ltx-lab-example.json",
        LTX_GOSEE_I2V,
        "breath close to the lens, wind in the hood, tar grit. No score, no music, no licensed songs.",
        "Motion + audio",
    )
    ltx_t2v(WF / "ltx-t2v-hero-lab-example.json")
    print("wired prompt-enhance nodes")


if __name__ == "__main__":
    main()
