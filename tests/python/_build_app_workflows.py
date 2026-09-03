"""Build operator-app lab graphs (still / GIF / dream-house).

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_build_app_workflows.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

KLEIN_STILL = (
    "A photoreal still photograph of a small-town main street at golden hour. "
    "A single red bicycle leans against a brick storefront. Warm sidelight rakes "
    "the brick and the bicycle's chrome. Shot on a 35mm lens at eye level, framed "
    "for YouTube 16:9. Unmarked facades, empty of signage, clean surfaces without lettering."
)
KLEIN_NEG = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
HOUSE_IDENTITY = (
    "A photoreal still photograph of a contemporary cedar-and-glass lake house. "
    "Vertical cedar siding, a charcoal standing-seam roof, and tall black-framed "
    "windows face a still alpine lake. Warm oak floors run indoors. An evergreen "
    "ridge rises behind the unmarked house. Golden wood grain, clean glass, and "
    "quiet water. Framed for Instagram 4:5 portrait. Solitary house, empty terraces, "
    "unmarked surfaces."
)
HOUSE_SHOTS = [
    (
        "01 curb appeal",
        "Golden-hour curb appeal from the gravel drive, 24mm at eye level, "
        "Instagram 4:5 portrait. Warm sidelight rakes the cedar. Empty drive.",
    ),
    (
        "02 entry",
        "Front entry with a tall black-framed glass door, 35mm, Instagram 4:5. "
        "Soft morning light on cedar and stone. Empty porch, unmarked door.",
    ),
    (
        "03 living room",
        "Living room looking through the glass wall toward the still lake, 24mm, "
        "Instagram 4:5. Oak floors, linen sofa, late-day sun. Empty of occupants.",
    ),
    (
        "04 kitchen",
        "Kitchen island in pale stone, morning sidelight, 35mm, Instagram 4:5. "
        "Cedar cabinets, black hardware, unmarked surfaces.",
    ),
    (
        "05 dining",
        "Dining table by the window at evening, lamps lit, 35mm, Instagram 4:5. "
        "Oak table, simple ceramic, lake twilight beyond the glass.",
    ),
    (
        "06 bedroom",
        "Primary bedroom with linen bedding and a lake window, 35mm, Instagram 4:5. "
        "Soft dawn light, cedar wall, solitary room.",
    ),
    (
        "07 bath",
        "Spa bath in pale stone and cedar, 35mm, Instagram 4:5. A freestanding tub "
        "faces frosted glass. Quiet, unmarked fixtures.",
    ),
    (
        "08 deck",
        "Lakeside deck at dusk, 24mm, Instagram 4:5. Cedar boards, simple chairs, "
        "still water, evergreen ridge.",
    ),
    (
        "09 twilight",
        "Twilight exterior, interior lamps glowing through black-framed glass, "
        "24mm, Instagram 4:5. Solitary house on the lake.",
    ),
    (
        "10 ridge view",
        "Elevated wide view of the property from the ridge, 24mm, Instagram 4:5. "
        "The cedar-and-glass house sits above the still lake among evergreens.",
    ),
]
GIF_MOTION = (
    "Locked camera. A light breeze moves leaves and a thin curtain. Water and "
    "fabric drift, then settle. Keep the start-image identity locked. Gentle "
    "cyclic motion for a looping GIF."
)
GIF_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)

STILL_NOTE = """## still-app-lab-example

Daily Klein 4B still app. Click the UNET filename to swap Apache Klein 4B weights.
CLIP (qwen_3_4b, type flux2) and flux2-vae stay the same for every Klein 4B UNET.

Swap table:
- flux-2-klein-4b-fp8.safetensors — daily default, 4 steps, CFG 1.0
- flux-2-klein-4b-nvfp4.safetensors — Spark NVFP4 (download-image --tier nvfp4), 4 steps, CFG 1.0
- flux-2-klein-base-4b-fp8.safetensors — more quality (download-image --tier base), raise steps to 20-28 and CFG to about 3.5

SETTINGS: width/height on EmptyFlux2LatentImage (default 1024x576 16:9). 1:1 = 768x768. 9:16 = 576x1024. Instagram 4:5 = 1024x1280. Seed, steps, CFG on KSampler.
Save prefix: ez_still_app.
Prompt enhance: leave Enhance off for this canned prompt. Set Enhance true and XAI_API_KEY to rewrite a lazy sentence.
"""

GIF_NOTE = """## gif-loop-lab-example

Wan 2.2 TI2V-5B Apache silent GIF (~4 s @ 12 fps, 49 frames).
Models: wan2.2_ti2v_5B_fp16.safetensors + umt5_xxl_fp8_e4m3fn_scaled.safetensors (CLIP type wan) + wan2.2_vae.safetensors.
PRIMARY OUTPUT: VHS image/gif. loop_count 0 = infinite. Ping-pong ON so playback goes forward then reverse — first and last frames meet for a seamless loop.
Easy loop: leave Infinite loop (ping-pong) ON. Turn ping-pong OFF only for one-way motion (a walk or dolly looks wrong in reverse).
LoadImage default example.png so Queue works; after still-app set ez_still_app_*.png.
Motion: locked camera plus breeze / fabric / leaves. Do not prompt a walk or a one-way dolly.
Do not Queue 121-frame Wan drafts here. Prefix: ez_gif_loop.
Prompt enhance: leave Enhance off for this canned prompt. Set Enhance true and XAI_API_KEY to rewrite a lazy sentence.
"""

HOUSE_NOTE = """## dream-house-lab-example

Ten Instagram 4:5 stills of one cedar-and-glass lake house (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280).
Edit HOUSE IDENTITY once. Each SHOT card is only the camera line; Prompt Join stitches identity + shot.
Same seed 42 on every sampler. Queue writes ez_dream_house_01 through ez_dream_house_10.
Bypass unused SHOT groups (Ctrl+B) if you only want a subset. All ten on is the carousel pack.
Do not restyle the identity per shot — change camera, time of day, and room only.
Prompt enhance on identity: leave Enhance off for this canned bible. Set Enhance true and XAI_API_KEY to rewrite a lazy house description.
"""


def _node(graph: dict, ntype: str, title: str | None = None) -> dict:
    for n in graph["nodes"]:
        if n.get("type") != ntype:
            continue
        if title is None or n.get("title") == title:
            return n
    raise KeyError(f"{ntype} {title}")


def _dump(path: Path, graph: dict) -> None:
    _assert_no_overlap(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


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


def _group(gid: int, title: str, x: float, y: float, w: float, h: float, color: str) -> dict:
    return {
        "id": gid,
        "title": title,
        "bounding": [x, y, w, h],
        "color": color,
        "font_size": 24,
        "flags": {},
    }


def build_still_app() -> dict:
    graph = json.loads((WF / "still-draft-lab-example.json").read_text(encoding="utf-8"))
    graph["id"] = "still-app-lab-example"
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
    graph["extra"]["lab_profile"] = "still-app-lab-example"
    graph["extra"]["lab_note"] = STILL_NOTE
    graph["extra"]["lab_description"] = "Klein 4B still app 1024x576 4 steps"
    enh = _node(graph, "EZKleinPromptEnhance")
    enh["widgets_values"][0] = KLEIN_STILL
    pos = _node(graph, "CLIPTextEncode", "Positive")
    pos["widgets_values"] = [KLEIN_STILL]
    graph["groups"] = [
        _group(1, "MODEL", 20, 40, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, 40, 920, 400, "#3f789e"),
        _group(3, "SETTINGS", 1420, 40, 380, 500, "#a1309b"),
        _group(4, "OUTPUT", 1820, 40, 340, 430, "#3f789e"),
    ]
    return graph


def build_gif_loop() -> dict:
    graph = json.loads((WF / "wan-i2v-draft-lab-example.json").read_text(encoding="utf-8"))
    graph["id"] = "gif-loop-lab-example"
    graph["revision"] = 1
    lat = _node(graph, "Wan22ImageToVideoLatent")
    lat["widgets_values"][2] = 49
    lat["title"] = "GIF size and length (49 frames)"
    vhs = _node(graph, "VHS_VideoCombine")
    vhs["title"] = "Infinite loop (ping-pong)"
    vhs["widgets_values"]["format"] = "image/gif"
    vhs["widgets_values"]["pingpong"] = True
    vhs["widgets_values"]["loop_count"] = 0
    vhs["widgets_values"]["frame_rate"] = 12
    vhs["widgets_values"]["filename_prefix"] = "ez_gif_loop"
    save = _node(graph, "SaveImage")
    save["widgets_values"] = ["ez_gif_loop_frames"]
    enh = _node(graph, "EZWanPromptEnhance")
    enh["widgets_values"] = [GIF_MOTION, False, "i2v", "4 seconds, 12 fps, looping GIF"]
    motion = _node(graph, "CLIPTextEncode", "Motion / prompt")
    motion["widgets_values"] = [GIF_MOTION]
    neg = _node(graph, "CLIPTextEncode", "Negative")
    neg["widgets_values"] = [GIF_NEG]
    note = _node(graph, "Note")
    note["widgets_values"] = [GIF_NOTE]
    graph["extra"]["lab_profile"] = "gif-loop-lab-example"
    graph["extra"]["lab_note"] = GIF_NOTE
    graph["extra"]["lab_description"] = "Wan 5B looping GIF 49 frames ping-pong"
    groups = list(graph.get("groups") or [])
    groups.append(_group(3, "SETTINGS", 1400, 40, 640, 660, "#a1309b"))
    groups.append(_group(4, "OUTPUT", 2400, 40, 360, 480, "#3f789e"))
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
            [40, 480],
            [420, 280],
            "HOUSE IDENTITY",
            [HOUSE_IDENTITY, False, "t2i", "Instagram 4:5 still"],
            3,
            outputs=[out("prompt", "STRING", ident_links)],
        )
    )
    nodes.append(
        _base_node(
            5,
            "CLIPTextEncode",
            [40, 800],
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
            6,
            "EmptyFlux2LatentImage",
            [40, 960],
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
            [40, 1120],
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
        full = f"{HOUSE_IDENTITY} {shot}"
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
                [shot],
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
        _group(1, "MODEL", 20, 40, 430, 430, "#3f789e"),
        _group(2, "HOUSE IDENTITY", 20, 450, 460, 340, "#a1309b"),
    ]
    for i, (label, _) in enumerate(HOUSE_SHOTS):
        y = shot_y0 + i * row_h
        groups.append(
            _group(10 + i, f"SHOT {label}", 500, y - 20, 1840, 340, "#3f789e")
        )

    last_id = 14 + 9 * 5
    return {
        "id": "dream-house-lab-example",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "dream-house-lab-example",
            "lab_flux_tier": "fast",
            "lab_note": HOUSE_NOTE,
            "lab_description": "Ten Instagram 4:5 Klein stills of one lake house",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }


def main() -> None:
    still = build_still_app()
    gif = build_gif_loop()
    house = build_dream_house()
    _dump(WF / "still-app-lab-example.json", still)
    _dump(WF / "gif-loop-lab-example.json", gif)
    _dump(WF / "dream-house-lab-example.json", house)
    print("wrote still-app, gif-loop, dream-house")


if __name__ == "__main__":
    main()
