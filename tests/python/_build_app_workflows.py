"""Build operator-app lab graphs (still / GIF / dream-house).

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_build_app_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    ensure_group_title_inset,
    group as _group,
)
from _lab_theme import (
    CHARACTER_DRAFT,
    CHARACTER_TWEAK,
    CREATOR_IDENTITY,
    GIF_MOTION,
    HOUSE_IDENTITY,
    KLEIN_NEG_STILL,
    KLEIN_STILL_DAILY,
)
from _lab_paths import lab_dest, lab_json
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_prompt_enhance.client import join_prompt, load_view_pack  # noqa: E402

WF = ROOT / "workflows"

KLEIN_NEG = KLEIN_NEG_STILL
HOUSE_SHOTS = [
    (item["label"], item["shot"]) for item in load_view_pack("place_10")
]
# Klein prefers ~150 words; join adds lock + shot after the bible.
JOINED_WORD_CAP = 180
GIF_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)

STILL_NOTE = """## klein-still-daily-lab-example

Daily Klein 4B still app. Click the UNET filename to swap Apache Klein 4B weights.
CLIP (qwen_3_4b, type flux2) and flux2-vae stay the same for every Klein 4B UNET.

Swap table:
- flux-2-klein-4b-fp8.safetensors — daily default, 4 steps, CFG 1.0
- flux-2-klein-4b-nvfp4.safetensors — Spark NVFP4 (download-image --tier nvfp4), 4 steps, CFG 1.0
- flux-2-klein-base-4b-fp8.safetensors — more quality (download-image --tier base), raise steps to 20-28 and CFG to about 3.5

SETTINGS: width/height on EmptyFlux2LatentImage (default 1024x576 16:9). 1:1 = 768x768. 9:16 = 576x1024. Instagram 4:5 = 1024x1280. Seed, steps, CFG on KSampler.
Save prefix: ez_still_app.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used. Turn Enhance off to pin the widget text.
"""

GIF_NOTE = """## wan-gif-loop-lab-example

Wan 2.2 TI2V-5B Apache silent GIF (~4 s @ 12 fps, 49 frames).
Models: wan2.2_ti2v_5B_fp16.safetensors + umt5_xxl_fp8_e4m3fn_scaled.safetensors (CLIP type wan) + wan2.2_vae.safetensors.
PRIMARY OUTPUT: VHS image/gif. loop_count 0 = infinite. Ping-pong ON so playback goes forward then reverse — first and last frames meet for a seamless loop.
Easy loop: leave Infinite loop (ping-pong) ON. Turn ping-pong OFF only for one-way motion (a walk or dolly looks wrong in reverse).
LoadImage default example.png so Queue works; after still-app set ez_still_app_*.png.
Motion: locked camera plus breeze / fabric / city lights. Do not prompt a walk or a one-way dolly.
Do not Queue 121-frame Wan drafts here. Prefix: ez_gif_loop.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used. Turn Enhance off to pin the widget text.
"""

HOUSE_NOTE = """## klein-dream-house-lab-example

Ten Instagram 4:5 stills: a virtual tour of **one place** (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280). Type any place in HOUSE IDENTITY — the default placeholder is the lab penthouse.
HOUSE IDENTITY is a camera-free world bible (rooms, furniture, outdoor lamps, sky, surroundings). Enhance extracts only the rooms and furniture you named — name lounge, kitchen, bath, bedroom, and outdoor lamps so the tour can enter them. Hidden SHOT cards are a walkthrough (exterior, entrance, inside, lounge, kitchen, bath, bedroom, drone, day, night), not a penthouse template. Prompt Join lock=view front-loads the shot. Shots 02–10 are independent T2I (empty latent, same seed 42); they do not ReferenceLatent the identity still.
Identity-mode enhance is **on**. Shot cards are not Klein-t2i-enhanced — a per-shot rewrite would mutate the bible. Optional style dropdown applies to the bible.
Queue writes ez_dream_house_01 through ez_dream_house_10. Unused SHOT groups may be bypassed (Ctrl+B). Day and night may change sky and lamp state; massing, rooms, furniture, and surroundings must not.
If materials drift across rooms, swap the UNET to Klein base 4B and raise steps/CFG as on klein-still-daily.
"""

CHARACTER_DRAFT_NOTE = """## klein-character-draft-lab-example

Klein 4B character still. Type a character, pick a style, Queue. 1024x1280 (Instagram 4:5), seed 42, Enhance on (t2i so style applies). Prefix `ez_character`.

Handoff: load **klein-character-tweak-lab-example**, pick `ez_character_*.png`, and prompt the change.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
"""

CHARACTER_TWEAK_NOTE = """## klein-character-tweak-lab-example

Klein 4B **edit** of a character still. LoadImage: `ez_character_*.png` from Character Draft (or any Klein still). Prompt only the change. Enhance **edit**. Style restyles medium/grade; identity stays in the reference image. Prefix `ez_character_tweak`. Size 1024x1280.

VAEEncode + ReferenceLatent. Do not Queue without a start image.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
"""

PACK_NOTE = """## klein-platform-pack-lab-example

One identity, six platform plates (Klein 4B distilled, 4 steps, CFG 1.0, seed 42). Type any subject in PACK IDENTITY. Identity-mode enhance is **on** (camera-free bible). Each plate is independent T2I (own latent, no ReferenceLatent across aspect ratios). Hidden cards are framing only.

Prefixes and sizes (copy of the single-plate graphs):
- ez_pack_thumb 1280x720
- ez_pack_ig 1024x1024 (1:1)
- ez_pack_portrait 1024x1280 (Instagram 4:5)
- ez_pack_shorts 432x768 (9:16)
- ez_pack_og 1216x640
- ez_pack_banner 1536x512 (~3:1)

Unused SHOT groups may be bypassed (Ctrl+B). Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
Handoff: Spark Still → this pack → Silent 5s / Hook AV.
"""

PACK_PLATES = [
    (
        "thumb",
        "ez_pack_thumb",
        1280,
        720,
        "Bold YouTube thumbnail still, 16:9. Subject large and readable. Clean of burned-in words.",
    ),
    (
        "ig",
        "ez_pack_ig",
        1024,
        1024,
        "Instagram 1:1 square. Subject centered, warm key, unmarked surfaces.",
    ),
    (
        "portrait",
        "ez_pack_portrait",
        1024,
        1280,
        "Instagram 4:5 portrait. Headroom for a caption, unmarked surfaces.",
    ),
    (
        "shorts",
        "ez_pack_shorts",
        432,
        768,
        "Vertical 9:16 Shorts still. Caption headroom at the top.",
    ),
    (
        "og",
        "ez_pack_og",
        1216,
        640,
        "Blog / Open Graph hero ~1.9:1. Subject left-weighted, quiet right third.",
    ),
    (
        "banner",
        "ez_pack_banner",
        1536,
        512,
        "Ultra-wide channel banner ~3:1. Horizon low, empty sky band for a name overlay.",
    ),
]


def _node(graph: dict, ntype: str, title: str | None = None) -> dict:
    for n in graph["nodes"]:
        if n.get("type") != ntype:
            continue
        if title is None or n.get("title") == title:
            return n
    raise KeyError(f"{ntype} {title}")


def _dump(path: Path, graph: dict) -> None:
    stamp_suite_graph(graph)
    ensure_group_title_inset(graph)
    _assert_no_overlap(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def _assert_house_word_cap() -> None:
    for label, shot in HOUSE_SHOTS:
        text = join_prompt(HOUSE_IDENTITY, shot, "", "view")
        n = len(text.split())
        if n > JOINED_WORD_CAP:
            raise SystemExit(f"joined prompt too long for {label}: {n} words")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    boxes: list[tuple[int, str, float, float, float, float]] = []
    for n in graph["nodes"]:
        x, y = n["pos"]
        s = n.get("size", [200, 100])
        if isinstance(s, dict):
            w, h = float(s.get("0", 200)), float(s.get("1", 100))
        else:
            w, h = float(s[0]), float(s[1])
        boxes.append((n["id"], n["type"], x - pad, y - pad, x + w + pad, y + h + pad))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                raise SystemExit(f"overlap {a[0]}({a[1]}) vs {b[0]}({b[1]})")


def build_still_app() -> dict:
    graph = json.loads(lab_json("klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    graph["id"] = "klein-still-daily-lab-example"
    graph["revision"] = 1
    unet = _node(graph, "UNETLoader")
    unet["title"] = "Image model — click filename to swap"
    latent = _node(graph, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [1024, 576, 1]
    latent["title"] = "Size (width x height x batch)"
    latent["pos"] = [1440, 390]
    ks = _node(graph, "KSampler")
    ks["title"] = "Sampler (seed / steps / CFG)"
    save = _node(graph, "SaveImage")
    save["widgets_values"] = ["ez_still_app"]
    save["title"] = "Save PNG"
    note = _node(graph, "Note")
    note["widgets_values"] = [STILL_NOTE]
    graph["extra"]["lab_profile"] = "klein-still-daily-lab-example"
    graph["extra"]["lab_note"] = STILL_NOTE
    graph["extra"]["lab_description"] = "Daily Klein 4B still; click UNET to swap distilled / NVFP4 / base"
    enh = _node(graph, "EZKleinPromptEnhance")
    enh["widgets_values"][0] = KLEIN_STILL_DAILY
    enh["widgets_values"][1] = True
    pos = _node(graph, "CLIPTextEncode", "Positive")
    pos["widgets_values"] = [KLEIN_STILL_DAILY]
    neg = _node(graph, "CLIPTextEncode", "Negative")
    neg["widgets_values"] = [KLEIN_NEG_STILL]
    graph["groups"] = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, LAB_GROUP_Y0, 920, 400, "#3f789e"),
        _group(3, "SETTINGS", 1420, LAB_GROUP_Y0, 380, 500, "#a1309b"),
        _group(4, "OUTPUT", 1820, LAB_GROUP_Y0, 340, 430, "#3f789e"),
    ]
    return graph


def build_gif_loop() -> dict:
    graph = json.loads(lab_json("wan-i2v-5s-lab-example.json").read_text(encoding="utf-8"))
    graph["id"] = "wan-gif-loop-lab-example"
    graph["revision"] = 1
    lat = _node(graph, "Wan22ImageToVideoLatent")
    lat["widgets_values"][2] = 49
    lat["title"] = "GIF size and length (49 frames)"
    vhs = _node(graph, "VHS_VideoCombine")
    vhs["title"] = "Infinite loop (ping-pong) — open for preview"
    vhs["widgets_values"]["format"] = "image/gif"
    vhs["widgets_values"]["pingpong"] = True
    vhs["widgets_values"]["loop_count"] = 0
    vhs["widgets_values"]["frame_rate"] = 12
    vhs["widgets_values"]["filename_prefix"] = "ez_gif_loop"
    save = _node(graph, "SaveImage")
    save["widgets_values"] = ["ez_gif_loop_frames"]
    enh = _node(graph, "EZWanPromptEnhance")
    enh["widgets_values"] = [GIF_MOTION, True, "i2v", "4 seconds, 12 fps, looping GIF", "none"]
    motion = _node(graph, "CLIPTextEncode", "Motion / prompt")
    motion["widgets_values"] = [GIF_MOTION]
    neg = _node(graph, "CLIPTextEncode", "Negative")
    neg["widgets_values"] = [GIF_NEG]
    note = _node(graph, "Note")
    note["widgets_values"] = [GIF_NOTE]
    graph["extra"]["lab_profile"] = "wan-gif-loop-lab-example"
    graph["extra"]["lab_note"] = GIF_NOTE
    graph["extra"]["lab_description"] = "Wan 5B looping GIF, 49 frames ping-pong @ 12 fps"
    groups = list(graph.get("groups") or [])
    groups.append(_group(3, "SETTINGS", 1400, LAB_GROUP_Y0, 640, 660, "#a1309b"))
    groups.append(_group(4, "OUTPUT", 2400, LAB_GROUP_Y0, 360, 480, "#3f789e"))
    graph["groups"] = groups
    return graph


def _base_node(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets: list | dict,
    order: int,
    inputs: list | None = None,
    outputs: list | None = None,
) -> dict:
    return {
        "id": nid,
        "type": ntype,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
        "title": title,
    }


def build_dream_house() -> dict:
    _assert_house_word_cap()
    nodes: list[dict] = []
    links: list[list] = []
    link_id = 0

    def add_link(src: int, src_slot: int, dst: int, dst_slot: int, ltype: str) -> int:
        nonlocal link_id
        link_id += 1
        links.append([link_id, src, src_slot, dst, dst_slot, ltype])
        return link_id

    def out(name: str, ltype: str, link_ids: list[int]) -> dict:
        return {
            "name": name,
            "type": ltype,
            "links": link_ids,
            "slot_index": 0,
        }

    unet_links: list[int] = []
    clip_links: list[int] = []
    vae_links: list[int] = []
    ident_links: list[int] = []
    neg_links: list[int] = []
    latent_links: list[int] = []

    nodes.append(
        _base_node(
            1,
            "UNETLoader",
            [40, 80],
            [360, 82],
            "Klein 4B distilled FP8",
            ["flux-2-klein-4b-fp8.safetensors", "default"],
            0,
            outputs=[out("MODEL", "MODEL", unet_links)],
        )
    )
    nodes.append(
        _base_node(
            2,
            "CLIPLoader",
            [40, 212],
            [360, 106],
            "Qwen3-4B TE",
            ["qwen_3_4b.safetensors", "flux2", "default"],
            1,
            outputs=[out("CLIP", "CLIP", clip_links)],
        )
    )
    nodes.append(
        _base_node(
            3,
            "VAELoader",
            [40, 368],
            [360, 58],
            "Flux2 VAE",
            ["flux2-vae.safetensors"],
            2,
            outputs=[out("VAE", "VAE", vae_links)],
        )
    )
    nodes.append(
        _base_node(
            4,
            "EZKleinPromptEnhance",
            [40, 510],
            [420, 420],
            "HOUSE IDENTITY",
            [HOUSE_IDENTITY, True, "identity", "Instagram 4:5 still", "none"],
            3,
            outputs=[out("prompt", "STRING", ident_links)],
        )
    )
    nodes.append(
        _base_node(
            5,
            "CLIPTextEncode",
            [40, 970],
            [420, 120],
            "Negative",
            [KLEIN_NEG_STILL],
            4,
            inputs=[{"name": "clip", "type": "CLIP", "link": None}],
            outputs=[out("CONDITIONING", "CONDITIONING", neg_links)],
        )
    )
    nodes.append(
        _base_node(
            6,
            "EmptyFlux2LatentImage",
            [40, 1150],
            [280, 106],
            "Instagram 4:5 1024x1280",
            [1024, 1280, 1],
            5,
            outputs=[out("LATENT", "LATENT", latent_links)],
        )
    )
    nodes.append(
        _base_node(
            7,
            "Note",
            [40, 1310],
            [420, 360],
            "Operator note",
            [HOUSE_NOTE],
            6,
        )
    )

    lid = add_link(2, 0, 5, 0, "CLIP")
    nodes[4]["inputs"][0]["link"] = lid
    clip_links.append(lid)

    row_h = 360
    shot_y0 = 80
    for i, (label, shot) in enumerate(HOUSE_SHOTS):
        y = shot_y0 + i * row_h
        join_id = 10 + i * 5
        clip_id = 11 + i * 5
        ks_id = 12 + i * 5
        dec_id = 13 + i * 5
        save_id = 14 + i * 5
        prefix = f"ez_dream_house_{i + 1:02d}"
        full = join_prompt(HOUSE_IDENTITY, shot, "", "view")
        n = 20 + i * 5

        join_out: list[int] = []
        clip_out: list[int] = []
        ks_out: list[int] = []
        dec_out: list[int] = []

        nodes.append(
            _base_node(
                join_id,
                "EZPromptJoin",
                [520, y],
                [420, 180],
                f"SHOT {label}",
                [shot, "", "view"],
                n,
                inputs=[{"name": "identity", "type": "STRING", "link": None}],
                outputs=[out("prompt", "STRING", join_out)],
            )
        )
        nodes.append(
            _base_node(
                clip_id,
                "CLIPTextEncode",
                [980, y],
                [360, 140],
                f"Positive {i + 1:02d}",
                [full],
                n + 1,
                inputs=[
                    {"name": "clip", "type": "CLIP", "link": None},
                    {
                        "name": "text",
                        "type": "STRING",
                        "link": None,
                        "widget": {"name": "text"},
                    },
                ],
                outputs=[out("CONDITIONING", "CONDITIONING", clip_out)],
            )
        )
        nodes.append(
            _base_node(
                ks_id,
                "KSampler",
                [1380, y],
                [320, 262],
                f"Sampler {i + 1:02d}",
                [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
                n + 2,
                inputs=[
                    {"name": "model", "type": "MODEL", "link": None},
                    {"name": "positive", "type": "CONDITIONING", "link": None},
                    {"name": "negative", "type": "CONDITIONING", "link": None},
                    {"name": "latent_image", "type": "LATENT", "link": None},
                ],
                outputs=[out("LATENT", "LATENT", ks_out)],
            )
        )
        nodes.append(
            _base_node(
                dec_id,
                "VAEDecode",
                [1740, y],
                [240, 46],
                f"Decode {i + 1:02d}",
                [],
                n + 3,
                inputs=[
                    {"name": "samples", "type": "LATENT", "link": None},
                    {"name": "vae", "type": "VAE", "link": None},
                ],
                outputs=[out("IMAGE", "IMAGE", dec_out)],
            )
        )
        nodes.append(
            _base_node(
                save_id,
                "SaveImage",
                [2020, y],
                [280, 270],
                f"Save {i + 1:02d}",
                [prefix],
                n + 4,
                inputs=[{"name": "images", "type": "IMAGE", "link": None}],
            )
        )

        by_id = {n["id"]: n for n in nodes}

        lid = add_link(4, 0, join_id, 0, "STRING")
        by_id[join_id]["inputs"][0]["link"] = lid
        ident_links.append(lid)

        lid = add_link(join_id, 0, clip_id, 1, "STRING")
        by_id[clip_id]["inputs"][1]["link"] = lid
        join_out.append(lid)

        lid = add_link(2, 0, clip_id, 0, "CLIP")
        by_id[clip_id]["inputs"][0]["link"] = lid
        clip_links.append(lid)

        lid = add_link(1, 0, ks_id, 0, "MODEL")
        by_id[ks_id]["inputs"][0]["link"] = lid
        unet_links.append(lid)

        lid = add_link(clip_id, 0, ks_id, 1, "CONDITIONING")
        by_id[ks_id]["inputs"][1]["link"] = lid
        clip_out.append(lid)

        lid = add_link(5, 0, ks_id, 2, "CONDITIONING")
        by_id[ks_id]["inputs"][2]["link"] = lid
        neg_links.append(lid)

        lid = add_link(6, 0, ks_id, 3, "LATENT")
        by_id[ks_id]["inputs"][3]["link"] = lid
        latent_links.append(lid)

        lid = add_link(ks_id, 0, dec_id, 0, "LATENT")
        by_id[dec_id]["inputs"][0]["link"] = lid
        ks_out.append(lid)

        lid = add_link(3, 0, dec_id, 1, "VAE")
        by_id[dec_id]["inputs"][1]["link"] = lid
        vae_links.append(lid)

        lid = add_link(dec_id, 0, save_id, 0, "IMAGE")
        by_id[save_id]["inputs"][0]["link"] = lid
        dec_out.append(lid)

    groups = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "HOUSE IDENTITY", 20, LAB_GROUP_Y0 + 430, 460, 340, "#a1309b"),
    ]
    for i, (label, _) in enumerate(HOUSE_SHOTS):
        y = shot_y0 + i * row_h
        groups.append(
            _group(10 + i, f"SHOT {label}", 500, y - GROUP_TITLE_INSET, 1840, 340, "#3f789e")
        )

    last_id = max(n["id"] for n in nodes)
    return {
        "id": "klein-dream-house-lab-example",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "klein-dream-house-lab-example",
            "lab_flux_tier": "fast",
            "lab_note": HOUSE_NOTE,
            "lab_description": "Ten Instagram 4:5 Klein stills: virtual tour of one place (outside, entrance, rooms, drone, day, night)",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }


def build_platform_pack() -> dict:
    nodes: list[dict] = []
    links: list[list] = []
    link_id = 0

    def add_link(src: int, src_slot: int, dst: int, dst_slot: int, ltype: str) -> int:
        nonlocal link_id
        link_id += 1
        links.append([link_id, src, src_slot, dst, dst_slot, ltype])
        return link_id

    def out(name: str, ltype: str, link_ids: list[int]) -> dict:
        return {"name": name, "type": ltype, "links": link_ids, "slot_index": 0}

    unet_links: list[int] = []
    clip_links: list[int] = []
    vae_links: list[int] = []
    ident_links: list[int] = []
    neg_links: list[int] = []

    nodes.append(
        _base_node(
            1,
            "UNETLoader",
            [40, 80],
            [360, 82],
            "Klein 4B distilled FP8",
            ["flux-2-klein-4b-fp8.safetensors", "default"],
            0,
            outputs=[out("MODEL", "MODEL", unet_links)],
        )
    )
    nodes.append(
        _base_node(
            2,
            "CLIPLoader",
            [40, 212],
            [360, 106],
            "Qwen3-4B TE",
            ["qwen_3_4b.safetensors", "flux2", "default"],
            1,
            outputs=[out("CLIP", "CLIP", clip_links)],
        )
    )
    nodes.append(
        _base_node(
            3,
            "VAELoader",
            [40, 368],
            [360, 58],
            "Flux2 VAE",
            ["flux2-vae.safetensors"],
            2,
            outputs=[out("VAE", "VAE", vae_links)],
        )
    )
    nodes.append(
        _base_node(
            4,
            "EZKleinPromptEnhance",
            [40, 510],
            [420, 420],
            "PACK IDENTITY",
            [CREATOR_IDENTITY, True, "identity", "platform pack still", "none"],
            3,
            outputs=[out("prompt", "STRING", ident_links)],
        )
    )
    nodes.append(
        _base_node(
            5,
            "CLIPTextEncode",
            [40, 970],
            [420, 120],
            "Negative",
            [KLEIN_NEG],
            4,
            inputs=[{"name": "clip", "type": "CLIP", "link": None}],
            outputs=[out("CONDITIONING", "CONDITIONING", neg_links)],
        )
    )
    nodes.append(
        _base_node(
            7,
            "Note",
            [40, 1150],
            [420, 400],
            "Operator note",
            [PACK_NOTE],
            5,
        )
    )
    lid = add_link(2, 0, 5, 0, "CLIP")
    nodes[4]["inputs"][0]["link"] = lid
    clip_links.append(lid)

    row_h = 360
    shot_y0 = 80
    for i, (label, prefix, width, height, shot) in enumerate(PACK_PLATES):
        y = shot_y0 + i * row_h
        join_id = 10 + i * 6
        clip_id = 11 + i * 6
        lat_id = 12 + i * 6
        ks_id = 13 + i * 6
        dec_id = 14 + i * 6
        save_id = 15 + i * 6
        full = join_prompt(CREATOR_IDENTITY, shot, "", "view")
        n = 20 + i * 6
        join_out: list[int] = []
        clip_out: list[int] = []
        lat_out: list[int] = []
        ks_out: list[int] = []
        dec_out: list[int] = []
        nodes.append(
            _base_node(
                join_id,
                "EZPromptJoin",
                [520, y],
                [420, 180],
                f"SHOT {label}",
                [shot, "", "view"],
                n,
                inputs=[{"name": "identity", "type": "STRING", "link": None}],
                outputs=[out("prompt", "STRING", join_out)],
            )
        )
        nodes.append(
            _base_node(
                clip_id,
                "CLIPTextEncode",
                [980, y],
                [360, 140],
                f"Positive {label}",
                [full],
                n + 1,
                inputs=[
                    {"name": "clip", "type": "CLIP", "link": None},
                    {
                        "name": "text",
                        "type": "STRING",
                        "link": None,
                        "widget": {"name": "text"},
                    },
                ],
                outputs=[out("CONDITIONING", "CONDITIONING", clip_out)],
            )
        )
        nodes.append(
            _base_node(
                lat_id,
                "EmptyFlux2LatentImage",
                [1380, y],
                [280, 106],
                f"Size {width}x{height}",
                [width, height, 1],
                n + 2,
                outputs=[out("LATENT", "LATENT", lat_out)],
            )
        )
        nodes.append(
            _base_node(
                ks_id,
                "KSampler",
                [1700, y],
                [320, 262],
                f"Sampler {label}",
                [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
                n + 3,
                inputs=[
                    {"name": "model", "type": "MODEL", "link": None},
                    {"name": "positive", "type": "CONDITIONING", "link": None},
                    {"name": "negative", "type": "CONDITIONING", "link": None},
                    {"name": "latent_image", "type": "LATENT", "link": None},
                ],
                outputs=[out("LATENT", "LATENT", ks_out)],
            )
        )
        nodes.append(
            _base_node(
                dec_id,
                "VAEDecode",
                [2060, y],
                [240, 46],
                f"Decode {label}",
                [],
                n + 4,
                inputs=[
                    {"name": "samples", "type": "LATENT", "link": None},
                    {"name": "vae", "type": "VAE", "link": None},
                ],
                outputs=[out("IMAGE", "IMAGE", dec_out)],
            )
        )
        nodes.append(
            _base_node(
                save_id,
                "SaveImage",
                [2340, y],
                [280, 270],
                f"Save {label}",
                [prefix],
                n + 5,
                inputs=[{"name": "images", "type": "IMAGE", "link": None}],
            )
        )
        by_id = {node["id"]: node for node in nodes}
        lid = add_link(4, 0, join_id, 0, "STRING")
        by_id[join_id]["inputs"][0]["link"] = lid
        ident_links.append(lid)
        lid = add_link(join_id, 0, clip_id, 1, "STRING")
        by_id[clip_id]["inputs"][1]["link"] = lid
        join_out.append(lid)
        lid = add_link(2, 0, clip_id, 0, "CLIP")
        by_id[clip_id]["inputs"][0]["link"] = lid
        clip_links.append(lid)
        lid = add_link(1, 0, ks_id, 0, "MODEL")
        by_id[ks_id]["inputs"][0]["link"] = lid
        unet_links.append(lid)
        lid = add_link(clip_id, 0, ks_id, 1, "CONDITIONING")
        by_id[ks_id]["inputs"][1]["link"] = lid
        clip_out.append(lid)
        lid = add_link(5, 0, ks_id, 2, "CONDITIONING")
        by_id[ks_id]["inputs"][2]["link"] = lid
        neg_links.append(lid)
        lid = add_link(lat_id, 0, ks_id, 3, "LATENT")
        by_id[ks_id]["inputs"][3]["link"] = lid
        lat_out.append(lid)
        lid = add_link(ks_id, 0, dec_id, 0, "LATENT")
        by_id[dec_id]["inputs"][0]["link"] = lid
        ks_out.append(lid)
        lid = add_link(3, 0, dec_id, 1, "VAE")
        by_id[dec_id]["inputs"][1]["link"] = lid
        vae_links.append(lid)
        lid = add_link(dec_id, 0, save_id, 0, "IMAGE")
        by_id[save_id]["inputs"][0]["link"] = lid
        dec_out.append(lid)

    groups = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "PACK IDENTITY", 20, LAB_GROUP_Y0 + 430, 460, 400, "#a1309b"),
    ]
    for i, (label, _, _, _, _) in enumerate(PACK_PLATES):
        y = shot_y0 + i * row_h
        groups.append(
            _group(10 + i, f"SHOT {label}", 500, y - GROUP_TITLE_INSET, 2160, 340, "#3f789e")
        )
    last_id = max(n["id"] for n in nodes)
    return {
        "id": "klein-platform-pack-lab-example",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "klein-platform-pack-lab-example",
            "lab_flux_tier": "fast",
            "lab_note": PACK_NOTE,
            "lab_description": "Six Klein platform plates from one identity; independent T2I per aspect",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }


def build_character_draft() -> dict:
    graph = json.loads(lab_json("klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    graph["id"] = "klein-character-draft-lab-example"
    graph["revision"] = 1
    latent = _node(graph, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [1024, 1280, 1]
    latent["title"] = "Size 4:5 character still"
    save = _node(graph, "SaveImage")
    save["widgets_values"] = ["ez_character"]
    save["title"] = "Save character"
    enh = _node(graph, "EZKleinPromptEnhance")
    enh["widgets_values"] = [
        CHARACTER_DRAFT,
        True,
        "t2i",
        "Instagram 4:5 character still",
        "none",
    ]
    pos = _node(graph, "CLIPTextEncode", "Positive")
    pos["widgets_values"] = [CHARACTER_DRAFT]
    note = _node(graph, "Note")
    note["widgets_values"] = [CHARACTER_DRAFT_NOTE]
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-character-draft-lab-example"
    extra["lab_note"] = CHARACTER_DRAFT_NOTE
    extra["lab_description"] = "Klein 4B character still, 1024x1280, style on, prefix ez_character"
    return graph


def build_character_tweak() -> dict:
    from _build_dcc_workflows import build_klein_from_clay

    graph = build_klein_from_clay()
    graph["id"] = "klein-character-tweak-lab-example"
    graph["revision"] = 1
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-character-tweak-lab-example"
    extra["lab_note"] = CHARACTER_TWEAK_NOTE
    extra["lab_description"] = (
        "Klein 4B character edit. LoadImage ez_character_*.png. ReferenceLatent. Prefix ez_character_tweak."
    )
    extra.pop("lab_dcc", None)
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            node["widgets_values"] = [
                CHARACTER_TWEAK,
                True,
                "edit",
                "Instagram 4:5 character edit",
                "none",
            ]
            node["title"] = "Klein Prompt Enhance (edit)"
        elif ntype == "CLIPTextEncode" and node.get("title") != "Negative":
            node["widgets_values"] = [CHARACTER_TWEAK]
        elif ntype == "SaveImage":
            node["widgets_values"] = ["ez_character_tweak"]
            node["title"] = "Save tweak"
        elif ntype == "LoadImage":
            node["widgets_values"] = ["example.png", "image"]
            node["title"] = "Character still (ez_character_*.png)"
        elif ntype == "EmptyFlux2LatentImage":
            node["widgets_values"] = [1024, 1280, 1]
            node["title"] = "Size 4:5 character still"
        elif ntype == "Note":
            node["widgets_values"] = [CHARACTER_TWEAK_NOTE]
            node["title"] = "Operator note"
        elif ntype == "VAEEncode":
            node["title"] = "Encode character plate"
            node["pos"] = [2180, 460]
        elif ntype == "ReferenceLatent":
            node["title"] = "Positive + character plate"
            node["pos"] = [1440, 400]
    return graph


def main() -> None:
    still = build_still_app()
    gif = build_gif_loop()
    house = build_dream_house()
    pack = build_platform_pack()
    draft = build_character_draft()
    tweak = build_character_tweak()
    _dump(lab_json("klein-still-daily-lab-example.json"), still)
    _dump(lab_json("wan-gif-loop-lab-example.json"), gif)
    _dump(lab_json("klein-dream-house-lab-example.json"), house)
    _dump(lab_json("klein-platform-pack-lab-example.json"), pack)
    _dump(lab_dest("klein-character-draft-lab-example"), draft)
    _dump(lab_dest("klein-character-tweak-lab-example"), tweak)
    print("wrote still-app, gif-loop, dream-house, platform-pack, character draft/tweak")


if __name__ == "__main__":
    main()
