"""Build operator-app lab graphs (still / GIF / dream-house).

Not imported by pytest (leading underscore). Run from repo root:
  python3 tests/python/_build_app_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    finalize_layout,
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
    TEXT_SWAP,
)
from _lab_paths import apply_lab_identity, lab_dest, lab_json, lab_rel_of
from _stamp_app_mode import stamp_suite_graph
from _wire_format import wire_lab_graph
from _wire_image_describe import wire_image_describe
from _wire_prompt_enhance import append_note
from _wire_upscale import wire_upscale

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_image.modes import (  # noqa: E402
    ENHANCE_MODE_COMBO,
    default_category_label,
    default_mode_label,
)
from ez_prompt_enhance.client import join_prompt, load_view_pack  # noqa: E402

WF = ROOT / "workflows"

KLEIN_NEG = KLEIN_NEG_STILL
HOUSE_SHOTS = [
    (item["label"], item["shot"]) for item in load_view_pack("place_10")
]
# Klein prefers ~150 words for a single still; join adds lock + shot + closer.
JOINED_WORD_CAP = 220
GIF_NEG = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)

STUDIO_NOTE = """## stills/still-studio

Klein 4B still desk. Pick Format / platform for pixels, save prefix, and Rewrite prompt framing. Custom uses Width × Height (snapped to ÷16, max 2048).
Look recipe is an optional Cinema Rack starter (Enhance context). Style stays on Rewrite prompt. Quality does not change size.
Default canvas: 1280×704 (LTX I2V feeder). 1280×720 platform rows are stills-only — scale in an editor if a host wants more pixels.
Models: flux-2-klein-4b-fp8.safetensors + qwen_3_4b.safetensors (CLIP type flux2) + flux2-vae.safetensors.
Click Image model to swap distilled / NVFP4 / base. High quality may swap Klein base when download-image --tier base is on disk.
Save prefix follows Format (Custom keeps ez_still_studio). Empty of lettering — composite titles later.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). Turn Rewrite prompt off to pin the widget text. Optional style dropdown.
Handoff: motion/silent/still-to-video-5s, motion/av/still-to-video-8s, stills/text-swap.
"""

IMAGE_STUDIO_NOTE = """## stills/image-studio

Universal Klein 4B still desk with 100 creator modes (background swap, change text, change ratio, face lock, packshot, …).
Pick Mode category then Creator mode. The mode sets Rewrite prompt mode (t2i / edit / text_swap / identity), save prefix, and a locked instruction spliced into Enhance context.
Format / platform still sets pixels and Look recipe. Custom uses Width × Height (snapped to ÷16, max 2048). Quality does not change size.
Example / reference is optional — Queue without a file. When present, Klein attaches it as a native Flux.2 reference. Modes never error if the still is empty. Face swap is original characters only.
Authored models: flux-2-klein-4b-fp8.safetensors + qwen_3_4b.safetensors (CLIP type flux2) + flux2-vae.safetensors. Apache-2.0.
Quality ultra/max may select opt-in Non-Commercial weights when those files are on disk (gated, not YouTube-ok). Lab default stays 4B. Do not pin those filenames on this graph.
Save prefix follows Creator mode (`ez_gen_photoreal` for Photoreal still). Empty of lettering unless the mode is a text job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). Turn Rewrite prompt off to pin the widget text. Optional style dropdown.
Handoff: motion/silent/still-to-video-5s, motion/av/still-to-video-8s, stills/text-swap, stills/still-studio.
"""

STILL_NOTE = """## stills/still-daily

Daily Klein 4B still app. Click the UNET filename to swap Apache Klein 4B weights.
CLIP (qwen_3_4b, type flux2) and flux2-vae stay the same for every Klein 4B UNET.

Swap table:
- flux-2-klein-4b-fp8.safetensors — daily default, 4 steps, CFG 1.0
- flux-2-klein-4b-nvfp4.safetensors — Spark NVFP4 (download-image --tier nvfp4), 4 steps, CFG 1.0
- flux-2-klein-base-4b-fp8.safetensors — more quality (download-image --tier base), raise steps to 20-28 and CFG to about 3.5

SETTINGS: Format / platform sets pixels (default 1024×576 16:9 mid). Custom uses Width × Height. Seed, steps, CFG on KSampler.
Save prefix: ez_still_app.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used. Turn Enhance off to pin the widget text.
"""

GIF_NOTE = """## motion/loops/gif-loop

Wan 2.2 TI2V-5B Apache silent GIF (~4 s @ 12 fps, 49 frames).
Models: wan2.2_ti2v_5B_fp16.safetensors + umt5_xxl_fp8_e4m3fn_scaled.safetensors (CLIP type wan) + wan2.2_vae.safetensors.
PRIMARY OUTPUT: VHS image/gif. loop_count 0 = infinite. Ping-pong ON so playback goes forward then reverse — first and last frames meet for a seamless loop.
Easy loop: leave Infinite loop (ping-pong) ON. Turn ping-pong OFF only for one-way motion (a walk or dolly looks wrong in reverse).
LoadImage default example.png so Queue works; after still-app set ez_still_app_*.png.
Motion: locked camera plus breeze / fabric / city lights. Do not prompt a walk or a one-way dolly.
Do not Queue 121-frame Wan drafts here. Prefix: ez_gif_loop.
Prompt enhance is **off** so the locked-camera cyclic motion stays ping-pong safe. Turn Enhance on only if you want the 4B rewriter.
"""

HOUSE_NOTE = """## stills/dream-house

Ten Instagram 4:5 stills: a virtual tour of **one place** (Klein 4B distilled, 4 steps, CFG 1.0, 1024x1280). Type any place in HOUSE IDENTITY — the default placeholder is the lab penthouse.
HOUSE IDENTITY is a camera-free world bible (rooms, furniture, outdoor lamps, sky, surroundings, time of day). Enhance extracts only the rooms and furniture you named — name lounge, kitchen, dining, bath, bedroom, terrace, study, and outdoor lamps so the tour can enter them. Name each room’s backdrop in the bible (which wall or opening that room faces). Hidden SHOT cards are camera stations (tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study): lens, camera height, a distinct room program (entrance hall, living hall, cook line, dining hall, sleep chamber, wet room, open-air terrace, writing room), near/far planes, and which room — not a penthouse template and not one volume restyled. They do not name dusk, materials, or architecture. Prompt Join lock=view front-loads the shot and closes with “this still is only the room and backdrop the shot names.” Shots 02–10 are independent T2I (empty latent, same seed 42); they do not ReferenceLatent the identity still.
Identity-mode enhance is **on**. Shot cards are not Klein-t2i-enhanced — a per-shot rewrite would mutate the bible. Optional style dropdown applies to the bible.
Queue writes ez_dream_house_01 through ez_dream_house_10. Unused SHOT groups may be bypassed (Ctrl+B). Dawn / noon / night of one camera belong on klein-time-of-day, not this tour.
If materials drift across rooms, swap the UNET to Klein base 4B and raise steps/CFG as on klein-still-daily.
"""

CLAY_LOCK = (
    "Keep the clay blocking, camera, and silhouette from the start image. "
    "Do not redesign layout."
)

HOUSE_CLAY_NOTE = """## stills/dream-house-clay

Ten Instagram 4:5 Klein **edits** of a greybox (1024x1280, seed 42). Persistence is the 3D cameras — Klein only restyles.

`manage.sh start` seeds ez_house_clay_01.png … 10.png into COMFY_OUTPUT_DIR/input (container /inputs) so LoadImage can Queue. Seed copies an existing house-views pack when present; otherwise it renders the shipped lab-penthouse layout (no Blender). Reload the App if it was open before seed. Prefix ez_dream_house_clay_01 … 10.

Workbench dump (optional, higher quality) — stop Comfy first:

  ./scripts/manage.sh stop
  ./scripts/manage.sh house-views --slug lab-penthouse
  ./scripts/manage.sh start

Copy an existing dump without Blender (compose may stay up):

  ./scripts/manage.sh house-views --slug lab-penthouse --install-inputs

Reseed LoadImage plates without Blender (compose may stay up):

  ./scripts/manage.sh house-views --slug lab-penthouse --seed-inputs

HOUSE IDENTITY is the same camera-free world bible as stills/dream-house. Shot cards are camera stations from place_10 (lens, camera height, a distinct room program, near/far planes, and which room). Prompt Join lock=view. Each shot VAEEncodes its clay plate into ReferenceLatent. Shot cards are not Klein-t2i-enhanced.

Language-only tour (no geometry) → stills/dream-house. Do not substitute T2I stills or example.png as clay. Occupancy XOR: do not Blender-dump while compose is up. Seed/copy-inputs may run while compose is up.
Optional style dropdown applies to the bible. Unused SHOT groups may be bypassed (Ctrl+B).
"""

CHARACTER_DRAFT_NOTE = """## stills/character-draft

Klein 4B character still. Type a character, pick a style, Queue. 1024x1280 (Instagram 4:5), seed 42, Enhance on (t2i so style applies). Prefix `ez_character`.

Handoff: load **stills/character-tweak**, pick `ez_character_*.png`, and prompt the change.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
"""

CHARACTER_TWEAK_NOTE = """## stills/character-tweak

Klein 4B **edit** of a character still. LoadImage: `ez_character_*.png` from Character Draft (or any Klein still). Prompt only the change. Enhance **edit**. Style restyles medium/grade; identity stays in the reference image. Prefix `ez_character_tweak`. Size 1024x1280.

VAEEncode + ReferenceLatent. Do not Queue without a start image.

Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
"""

TEXT_SWAP_NOTE = """## stills/text-swap

Klein 4B **lettering swap**. Load a still that already has type. Type the new lettering (or "Replace SALE with OPEN"). Enhance **text_swap** rewrites a glyph-lock instruction: same typeface, weight, tracking, perspective, material, and every other pixel. Output PNG matches the source width and height (snapped to the Flux.2 ÷16 grid for denoise, then scaled back). Prefix `ez_text_swap`.

Do not Queue without a start image. Short high-contrast lettering holds best. For tiny or dense type, set Quality **High** (Klein base if `download-image --tier base` is on disk). Distilled 4B is best-effort, not a typesetter.

Type only the new lettering (HELLO) or a targeting line (Replace SALE with OPEN). The graph always wraps that into a glyph-lock instruction, even when Rewrite prompt is off.

VAEEncode of the snapped source is the latent canvas and the ReferenceLatent. Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Style is hidden — the source still owns look.
"""

BACKGROUND_SWAP_NOTE = """## stills/background-swap

Klein 4B **background swap**. Load a still. Pick a sample place or type a custom background. Keep the subject; replace only the background and ground contact. Output PNG matches the source width and height. Prefix `ez_bg_swap`.

Do not Queue without a start image. Describe image (default off) captions the source so Rewrite prompt can name wardrobe and props. Upscale (default none) is lanczos after decode.

VAEEncode of the snapped source is the latent canvas and the ReferenceLatent. Occupancy: klein — stop Wan, LTX, podcast, music. One GB10 job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). Style is hidden — the source still owns look.
"""

PACK_NOTE = """## stills/platform-pack

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
    rel = lab_rel_of(path)
    apply_lab_identity(graph, rel)
    wire_lab_graph(graph)
    wire_upscale(graph, rel)
    wire_image_describe(graph)
    stamp_suite_graph(graph)
    append_note(graph)
    finalize_layout(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def _assert_house_word_cap() -> None:
    for label, shot in HOUSE_SHOTS:
        text = join_prompt(HOUSE_IDENTITY, shot, "", "view")
        n = len(text.split())
        if n > JOINED_WORD_CAP:
            raise SystemExit(f"joined prompt too long for {label}: {n} words")
        clay = join_prompt(HOUSE_IDENTITY, shot, CLAY_LOCK, "view")
        cn = len(clay.split())
        if cn > JOINED_WORD_CAP + 40:
            raise SystemExit(f"clay joined prompt too long for {label}: {cn} words")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    del pad
    finalize_layout(graph)


def build_still_app() -> dict:
    graph = json.loads(lab_json("stills/still-draft.json").read_text(encoding="utf-8"))
    graph["id"] = "stills/still-daily"
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
    graph["extra"]["lab_profile"] = "stills/still-daily"
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


def _append_link(
    graph: dict,
    src: int,
    src_slot: int,
    dst: int,
    dst_slot: int,
    ltype: str | list[str],
) -> int:
    last = int(graph.get("last_link_id") or 0) + 1
    graph["last_link_id"] = last
    links = list(graph.get("links") or [])
    links.append([last, src, src_slot, dst, dst_slot, ltype])
    graph["links"] = links
    return last


def _push_output_link(node: dict, slot: int, link_id: int) -> None:
    outputs = list(node.get("outputs") or [])
    while len(outputs) <= slot:
        outputs.append({"name": "", "type": "*", "links": [], "slot_index": len(outputs)})
    out = outputs[slot]
    existing = list(out.get("links") or [])
    existing.append(link_id)
    out["links"] = existing
    out["slot_index"] = slot
    node["outputs"] = outputs


def _add_widget_input(node: dict, name: str, typ: str, link_id: int) -> int:
    inputs = list(node.get("inputs") or [])
    inputs.append(
        {
            "name": name,
            "type": typ,
            "link": link_id,
            "widget": {"name": name},
        }
    )
    node["inputs"] = inputs
    return len(inputs) - 1


def build_still_studio() -> dict:
    graph = json.loads(lab_json("stills/still-draft.json").read_text(encoding="utf-8"))
    apply_lab_identity(graph, "stills/still-studio")
    nid = int(graph.get("last_node_id") or 0) + 1
    graph["last_node_id"] = nid
    graph["revision"] = 1
    unet = _node(graph, "UNETLoader")
    unet["title"] = "Image model — click filename to swap"
    latent = _node(graph, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [1280, 704, 1]
    latent["title"] = "Latent (wired from Format)"
    save = _node(graph, "SaveImage")
    save["widgets_values"] = ["ez_still_studio"]
    save["title"] = "Save PNG"
    enh = _node(graph, "EZKleinPromptEnhance")
    enh_values = list(enh.get("widgets_values") or [])
    while len(enh_values) < 7:
        enh_values.append("")
    enh_values[0] = "custom"
    enh_values[2] = True
    enh_values[3] = "t2i"
    enh_values[4] = "YouTube 16:9 still, LTX feeder"
    enh_values[5] = "none"
    enh_values[6] = "stills/still-studio"
    enh["widgets_values"] = enh_values
    note = _node(graph, "Note")
    note["widgets_values"] = [STUDIO_NOTE]
    fmt = {
        "id": nid,
        "type": "EZImageFormat",
        "pos": [1440, 414],
        "size": [360, 220],
        "flags": {},
        "order": 11,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "width", "type": "INT", "links": [], "slot_index": 0},
            {"name": "height", "type": "INT", "links": [], "slot_index": 1},
            {"name": "batch", "type": "INT", "links": [], "slot_index": 2},
            {"name": "hint", "type": "STRING", "links": [], "slot_index": 3},
            {"name": "prefix", "type": "STRING", "links": [], "slot_index": 4},
            {"name": "context", "type": "STRING", "links": [], "slot_index": 5},
        ],
        "properties": {"Node name for S&R": "EZImageFormat"},
        "widgets_values": [
            "16:9 LTX feeder (1280×704)",
            "none",
            1280,
            704,
            1,
        ],
        "title": "Format / platform",
    }
    graph["nodes"].append(fmt)
    w_link = _append_link(graph, nid, 0, int(latent["id"]), 0, "INT")
    _add_widget_input(latent, "width", "INT", w_link)
    _push_output_link(fmt, 0, w_link)
    h_link = _append_link(graph, nid, 1, int(latent["id"]), 1, "INT")
    _add_widget_input(latent, "height", "INT", h_link)
    _push_output_link(fmt, 1, h_link)
    b_link = _append_link(graph, nid, 2, int(latent["id"]), 2, "INT")
    _add_widget_input(latent, "batch_size", "INT", b_link)
    _push_output_link(fmt, 2, b_link)
    hint_link = _append_link(graph, nid, 3, int(enh["id"]), 0, "STRING")
    _add_widget_input(enh, "duration_hint", "STRING", hint_link)
    _push_output_link(fmt, 3, hint_link)
    prefix_link = _append_link(graph, nid, 4, int(save["id"]), 1, "STRING")
    _add_widget_input(save, "filename_prefix", "STRING", prefix_link)
    _push_output_link(fmt, 4, prefix_link)
    ctx_link = _append_link(graph, nid, 5, int(enh["id"]), 1, "STRING")
    enh_inputs = list(enh.get("inputs") or [])
    enh_inputs.append({"name": "context", "type": "STRING", "link": ctx_link})
    enh["inputs"] = enh_inputs
    _push_output_link(fmt, 5, ctx_link)
    graph["extra"]["lab_profile"] = "stills/still-studio"
    graph["extra"]["lab_note"] = STUDIO_NOTE
    graph["extra"]["lab_description"] = (
        "Klein 4B still desk: format/platform picker, style, enhance, look recipe"
    )
    graph["groups"] = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, LAB_GROUP_Y0, 920, 620, "#3f789e"),
        _group(3, "FORMAT", 1420, LAB_GROUP_Y0, 400, 720, "#a1309b"),
        _group(4, "OUTPUT", 1860, LAB_GROUP_Y0, 360, 520, "#3f789e"),
    ]
    return graph


def _input_named(node: dict, name: str) -> dict:
    for item in node.get("inputs") or []:
        if item.get("name") == name:
            return item
    raise KeyError(name)


def _drop_output_link(node: dict, slot: int, link_id: int) -> None:
    outputs = list(node.get("outputs") or [])
    out = outputs[slot]
    existing = [int(item) for item in (out.get("links") or []) if int(item) != int(link_id)]
    out["links"] = existing
    node["outputs"] = outputs


def build_image_studio() -> dict:
    graph = json.loads(lab_json("stills/still-studio.json").read_text(encoding="utf-8"))
    apply_lab_identity(graph, "stills/image-studio")
    nid = int(graph.get("last_node_id") or 0) + 1
    graph["last_node_id"] = nid
    graph["revision"] = int(graph.get("revision") or 0) + 1
    fmt = _node(graph, "EZImageFormat")
    enh = _node(graph, "EZKleinPromptEnhance")
    save = _node(graph, "SaveImage")
    note = _node(graph, "Note")
    save["widgets_values"] = ["ez_gen_photoreal"]
    save["title"] = "Save PNG"
    enh_values = list(enh.get("widgets_values") or [])
    while len(enh_values) < 7:
        enh_values.append("")
    enh_values[6] = "stills/image-studio"
    enh["widgets_values"] = enh_values
    note["widgets_values"] = [IMAGE_STUDIO_NOTE]
    mode_inputs: list[dict[str, Any]] = [
        {"name": "context", "type": "STRING", "link": None},
    ]
    mode: dict[str, Any] = {
        "id": nid,
        "type": "EZImageMode",
        "pos": [1440, 80],
        "size": [360, 140],
        "flags": {},
        "order": 12,
        "mode": 0,
        "inputs": mode_inputs,
        "outputs": [
            {"name": "context", "type": "STRING", "links": [], "slot_index": 0},
            {
                "name": "enhance_mode",
                "type": ENHANCE_MODE_COMBO,
                "links": [],
                "slot_index": 1,
            },
            {"name": "prefix", "type": "STRING", "links": [], "slot_index": 2},
        ],
        "properties": {"Node name for S&R": "EZImageMode"},
        "widgets_values": [default_category_label(), default_mode_label()],
        "title": "Creator mode",
    }
    graph["nodes"].append(mode)
    ctx_in = _input_named(enh, "context")
    ctx_link_id = int(ctx_in["link"])
    ctx_row = next(row for row in graph["links"] if int(row[0]) == ctx_link_id)
    enh_id = int(enh["id"])
    _drop_output_link(fmt, 5, ctx_link_id)
    ctx_row[3] = nid
    ctx_row[4] = 0
    mode_inputs[0]["link"] = ctx_link_id
    _push_output_link(fmt, 5, ctx_link_id)
    mode_ctx = _append_link(graph, nid, 0, enh_id, 1, "STRING")
    ctx_in["link"] = mode_ctx
    _push_output_link(mode, 0, mode_ctx)
    mode_enh = _append_link(graph, nid, 1, enh_id, 2, ENHANCE_MODE_COMBO)
    enh_inputs = list(enh.get("inputs") or [])
    enh_inputs.append(
        {
            "name": "mode",
            "type": ENHANCE_MODE_COMBO,
            "link": mode_enh,
            "widget": {"name": "mode"},
        }
    )
    enh["inputs"] = enh_inputs
    _push_output_link(mode, 1, mode_enh)
    prefix_in = _input_named(save, "filename_prefix")
    prefix_link_id = int(prefix_in["link"])
    prefix_row = next(row for row in graph["links"] if int(row[0]) == prefix_link_id)
    _drop_output_link(fmt, 4, prefix_link_id)
    prefix_row[1] = nid
    prefix_row[2] = 2
    _push_output_link(mode, 2, prefix_link_id)
    graph["extra"]["lab_profile"] = "stills/image-studio"
    graph["extra"]["lab_note"] = IMAGE_STUDIO_NOTE
    graph["extra"]["lab_description"] = (
        "Klein 4B universal still desk: 100 creator modes, format/platform, optional ref"
    )
    graph["groups"] = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, LAB_GROUP_Y0, 920, 620, "#3f789e"),
        _group(3, "FORMAT", 1420, LAB_GROUP_Y0, 400, 900, "#a1309b"),
        _group(4, "OUTPUT", 1860, LAB_GROUP_Y0, 360, 520, "#3f789e"),
    ]
    return graph


def build_gif_loop() -> dict:
    graph = json.loads(lab_json("motion/silent/still-to-video-5s.json").read_text(encoding="utf-8"))
    graph["id"] = "motion/loops/gif-loop"
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
    enh["widgets_values"] = [GIF_MOTION, False, "i2v", "4 seconds, 12 fps, looping GIF", "none"]
    motion = _node(graph, "CLIPTextEncode", "Motion / prompt")
    motion["widgets_values"] = [GIF_MOTION]
    neg = _node(graph, "CLIPTextEncode", "Negative")
    neg["widgets_values"] = [GIF_NEG]
    note = _node(graph, "Note")
    note["widgets_values"] = [GIF_NOTE]
    graph["extra"]["lab_profile"] = "motion/loops/gif-loop"
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
        "id": "stills/dream-house",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "stills/dream-house",
            "lab_flux_tier": "fast",
            "lab_note": HOUSE_NOTE,
            "lab_description": "Ten Instagram 4:5 Klein stills: virtual tour of one place (outside, rooms, terrace, drone)",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }


def build_dream_house_clay() -> dict:
    """Ten Klein edits of house-views clay stills (same bible, ReferenceLatent)."""
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
            [420, 420],
            "Operator note",
            [HOUSE_CLAY_NOTE],
            6,
        )
    )

    lid = add_link(2, 0, 5, 0, "CLIP")
    nodes[4]["inputs"][0]["link"] = lid
    clip_links.append(lid)

    row_h = 380
    shot_y0 = 80
    for i, (label, shot) in enumerate(HOUSE_SHOTS):
        y = shot_y0 + i * row_h
        join_id = 20 + i * 10
        clip_id = 21 + i * 10
        load_id = 22 + i * 10
        enc_id = 23 + i * 10
        ref_id = 24 + i * 10
        ks_id = 25 + i * 10
        dec_id = 26 + i * 10
        save_id = 27 + i * 10
        prefix = f"ez_dream_house_clay_{i + 1:02d}"
        clay_name = f"ez_house_clay_{i + 1:02d}.png"
        full = join_prompt(HOUSE_IDENTITY, shot, CLAY_LOCK, "view")
        n = 20 + i * 10

        join_out: list[int] = []
        clip_out: list[int] = []
        load_out: list[int] = []
        enc_out: list[int] = []
        ref_out: list[int] = []
        ks_out: list[int] = []
        dec_out: list[int] = []

        nodes.append(
            _base_node(
                join_id,
                "EZPromptJoin",
                [520, y],
                [400, 180],
                f"SHOT {label}",
                [shot, CLAY_LOCK, "view"],
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
                [340, 120],
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
                load_id,
                "LoadImage",
                [1360, y],
                [280, 80],
                f"Clay {i + 1:02d} ({clay_name})",
                [clay_name, "image"],
                n + 2,
                outputs=[out("IMAGE", "IMAGE", load_out)],
            )
        )
        nodes.append(
            _base_node(
                enc_id,
                "VAEEncode",
                [1680, y],
                [220, 60],
                f"Encode clay {i + 1:02d}",
                [],
                n + 3,
                inputs=[
                    {"name": "pixels", "type": "IMAGE", "link": None},
                    {"name": "vae", "type": "VAE", "link": None},
                ],
                outputs=[out("LATENT", "LATENT", enc_out)],
            )
        )
        nodes.append(
            _base_node(
                ref_id,
                "ReferenceLatent",
                [1940, y],
                [260, 80],
                f"Positive + clay {i + 1:02d}",
                [],
                n + 4,
                inputs=[
                    {"name": "conditioning", "type": "CONDITIONING", "link": None},
                    {"name": "latent", "type": "LATENT", "link": None, "shape": 7},
                ],
                outputs=[out("CONDITIONING", "CONDITIONING", ref_out)],
            )
        )
        nodes.append(
            _base_node(
                ks_id,
                "KSampler",
                [2240, y],
                [300, 240],
                f"Sampler {i + 1:02d}",
                [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
                n + 5,
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
                [2580, y],
                [220, 46],
                f"Decode {i + 1:02d}",
                [],
                n + 6,
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
                [2840, y],
                [280, 80],
                f"Save {i + 1:02d}",
                [prefix],
                n + 7,
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

        lid = add_link(load_id, 0, enc_id, 0, "IMAGE")
        by_id[enc_id]["inputs"][0]["link"] = lid
        load_out.append(lid)

        lid = add_link(3, 0, enc_id, 1, "VAE")
        by_id[enc_id]["inputs"][1]["link"] = lid
        vae_links.append(lid)

        lid = add_link(clip_id, 0, ref_id, 0, "CONDITIONING")
        by_id[ref_id]["inputs"][0]["link"] = lid
        clip_out.append(lid)

        lid = add_link(enc_id, 0, ref_id, 1, "LATENT")
        by_id[ref_id]["inputs"][1]["link"] = lid
        enc_out.append(lid)

        lid = add_link(1, 0, ks_id, 0, "MODEL")
        by_id[ks_id]["inputs"][0]["link"] = lid
        unet_links.append(lid)

        lid = add_link(ref_id, 0, ks_id, 1, "CONDITIONING")
        by_id[ks_id]["inputs"][1]["link"] = lid
        ref_out.append(lid)

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
        _group(2, "HOUSE IDENTITY", 20, LAB_GROUP_Y0 + 430, 460, 360, "#a1309b"),
    ]
    for i, (label, _) in enumerate(HOUSE_SHOTS):
        y = shot_y0 + i * row_h
        groups.append(
            _group(10 + i, f"SHOT {label}", 500, y - GROUP_TITLE_INSET, 2680, 360, "#3f789e")
        )

    last_id = max(n["id"] for n in nodes)
    return {
        "id": "stills/dream-house-clay",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "stills/dream-house-clay",
            "lab_flux_tier": "fast",
            "lab_note": HOUSE_CLAY_NOTE,
            "lab_description": (
                "Ten Instagram 4:5 Klein edits of Blender clay views "
                "(3D persistence, AI finish)"
            ),
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
        "id": "stills/platform-pack",
        "revision": 1,
        "last_node_id": last_id,
        "last_link_id": link_id,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "stills/platform-pack",
            "lab_flux_tier": "fast",
            "lab_note": PACK_NOTE,
            "lab_description": "Six Klein platform plates from one identity; independent T2I per aspect",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }


def build_character_draft() -> dict:
    graph = json.loads(lab_json("stills/still-draft.json").read_text(encoding="utf-8"))
    graph["id"] = "stills/character-draft"
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
    extra["lab_profile"] = "stills/character-draft"
    extra["lab_note"] = CHARACTER_DRAFT_NOTE
    extra["lab_description"] = "Klein 4B character still, 1024x1280, style on, prefix ez_character"
    return graph


def build_character_tweak() -> dict:
    from _build_dcc_workflows import build_klein_from_clay

    graph = build_klein_from_clay()
    graph["id"] = "stills/character-tweak"
    graph["revision"] = 1
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "stills/character-tweak"
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


def _rewire_text_swap_canvas(graph: dict) -> None:
    """Drop the fixed latent; snap source → encode → sampler + reference; match size."""
    from _build_dcc_workflows import _add_link, _append_out_link
    from _wire_prompt_enhance import next_ids, remove_node

    empty = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    remove_node(graph, int(empty["id"]))
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    encode = next(n for n in graph["nodes"] if n.get("type") == "VAEEncode")
    decode = next(n for n in graph["nodes"] if n.get("type") == "VAEDecode")
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")

    def _drop_link_into(node: dict, name: str) -> None:
        inp = next(item for item in node.get("inputs") or [] if item.get("name") == name)
        old = inp.get("link")
        if old is None:
            return
        old_id = int(old)
        graph["links"] = [link for link in graph.get("links") or [] if int(link[0]) != old_id]
        inp["link"] = None
        live = {int(link[0]) for link in graph.get("links") or []}
        for other in graph["nodes"]:
            for out in other.get("outputs") or []:
                links = out.get("links")
                if isinstance(links, list):
                    out["links"] = [lid for lid in links if int(lid) in live]

    _drop_link_into(encode, "pixels")
    _drop_link_into(save, "images")

    nid, lid = next_ids(graph)
    snap_id = nid
    match_id = nid + 1
    link_load_snap = lid
    link_snap_enc = lid + 1
    link_enc_samp = lid + 2
    link_dec_match = lid + 3
    link_load_match = lid + 4
    link_match_save = lid + 5

    graph["nodes"].append(
        {
            "id": snap_id,
            "type": "EZSnapImage",
            "pos": [2180, 410],
            "size": [240, 60],
            "flags": {},
            "order": 19,
            "mode": 0,
            "inputs": [{"name": "image", "type": "IMAGE", "link": link_load_snap}],
            "outputs": [
                {
                    "name": "IMAGE",
                    "type": "IMAGE",
                    "links": [link_snap_enc],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZSnapImage"},
            "widgets_values": [],
            "title": "Snap to Klein grid",
        }
    )
    graph["nodes"].append(
        {
            "id": match_id,
            "type": "EZMatchImageSize",
            "pos": [1840, 140],
            "size": [280, 80],
            "flags": {},
            "order": 22,
            "mode": 0,
            "inputs": [
                {"name": "image", "type": "IMAGE", "link": link_dec_match},
                {"name": "size_src", "type": "IMAGE", "link": link_load_match},
            ],
            "outputs": [
                {
                    "name": "IMAGE",
                    "type": "IMAGE",
                    "links": [link_match_save],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "EZMatchImageSize"},
            "widgets_values": [],
            "title": "Match source size",
        }
    )

    def _slot(node: dict, name: str) -> int:
        for index, item in enumerate(node.get("inputs") or []):
            if item.get("name") == name:
                return index
        raise KeyError(name)

    pix = next(item for item in encode["inputs"] if item.get("name") == "pixels")
    pix["link"] = link_snap_enc
    images = next(item for item in save["inputs"] if item.get("name") == "images")
    images["link"] = link_match_save
    latent_in = next(
        item for item in sampler["inputs"] if item.get("name") == "latent_image"
    )
    latent_in["link"] = link_enc_samp

    _append_out_link(load, 0, link_load_snap)
    _append_out_link(load, 0, link_load_match)
    _append_out_link(encode, 0, link_enc_samp)
    decode_out = decode["outputs"][0]
    dec_links = [lid for lid in (decode_out.get("links") or []) if lid]
    decode_out["links"] = dec_links + [link_dec_match]

    _add_link(graph, link_load_snap, int(load["id"]), 0, snap_id, 0, "IMAGE")
    _add_link(
        graph,
        link_snap_enc,
        snap_id,
        0,
        int(encode["id"]),
        _slot(encode, "pixels"),
        "IMAGE",
    )
    _add_link(
        graph,
        link_enc_samp,
        int(encode["id"]),
        0,
        int(sampler["id"]),
        _slot(sampler, "latent_image"),
        "LATENT",
    )
    _add_link(graph, link_dec_match, int(decode["id"]), 0, match_id, 0, "IMAGE")
    _add_link(graph, link_load_match, int(load["id"]), 0, match_id, 1, "IMAGE")
    _add_link(
        graph,
        link_match_save,
        match_id,
        0,
        int(save["id"]),
        _slot(save, "images"),
        "IMAGE",
    )
    graph["last_node_id"] = match_id
    graph["last_link_id"] = link_match_save


def _strip_cloned_canvas_helpers(graph: dict) -> None:
    """Drop Format / optional-ref nodes cloned from still-hero."""
    from _wire_prompt_enhance import remove_node

    for ntype in ("EZImageFormat", "EZOptionalImage", "EZKleinRefCanvas"):
        for node in list(graph.get("nodes") or []):
            if node.get("type") == ntype:
                remove_node(graph, int(node["id"]))


def build_text_swap() -> dict:
    graph = build_character_tweak()
    _strip_cloned_canvas_helpers(graph)
    graph["id"] = "stills/text-swap"
    graph["revision"] = 1
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "stills/text-swap"
    extra["lab_note"] = TEXT_SWAP_NOTE
    extra["lab_description"] = (
        "Klein 4B lettering swap. LoadImage source still. Snap + ReferenceLatent. "
        "Output matches source size. Prefix ez_text_swap."
    )
    extra.pop("lab_dcc", None)
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            node["widgets_values"] = [
                "custom",
                TEXT_SWAP,
                True,
                "text_swap",
                "match the source still",
                "none",
                "stills/text-swap",
            ]
            node["title"] = "Klein Prompt Enhance (text swap)"
        elif ntype == "CLIPTextEncode" and node.get("title") != "Negative":
            node["widgets_values"] = [TEXT_SWAP]
        elif ntype == "SaveImage":
            node["widgets_values"] = ["ez_text_swap"]
            node["title"] = "Save text swap"
        elif ntype == "LoadImage":
            node["widgets_values"] = ["example.png", "image"]
            node["title"] = "Source still"
        elif ntype == "Note":
            node["widgets_values"] = [TEXT_SWAP_NOTE]
            node["title"] = "Operator note"
        elif ntype == "VAEEncode":
            node["title"] = "Encode snapped source"
        elif ntype == "ReferenceLatent":
            node["title"] = "Positive + source plate"
        elif ntype == "KSampler":
            widgets = list(node.get("widgets_values") or [])
            if len(widgets) >= 7:
                widgets[0] = 42
                widgets[1] = "fixed"
                widgets[2] = 8
                widgets[3] = 1.0
                widgets[6] = 1.0
            node["widgets_values"] = widgets
    _rewire_text_swap_canvas(graph)
    return graph


def build_background_swap() -> dict:
    graph = build_text_swap()
    graph["id"] = "stills/background-swap"
    graph["revision"] = 1
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "stills/background-swap"
    extra["lab_note"] = BACKGROUND_SWAP_NOTE
    extra["lab_description"] = (
        "Klein 4B background swap. LoadImage source still. Snap + ReferenceLatent. "
        "Output matches source size. Prefix ez_bg_swap."
    )
    default_prompt = (
        "Keep the subject from the reference. Replace only the background with a fog "
        "harbor pier at blue hour. Match ground contact and wrap light. Original "
        "characters only. Empty of new lettering."
    )
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            node["widgets_values"] = [
                "custom",
                default_prompt,
                True,
                "edit",
                "match the source still",
                "none",
                "stills/background-swap",
            ]
            node["title"] = "Klein Prompt Enhance (edit)"
        elif ntype == "CLIPTextEncode" and node.get("title") != "Negative":
            node["widgets_values"] = [default_prompt]
        elif ntype == "SaveImage":
            node["widgets_values"] = ["ez_bg_swap"]
            node["title"] = "Save background swap"
        elif ntype == "LoadImage":
            node["widgets_values"] = ["example.png", "image"]
            node["title"] = "Source still"
        elif ntype == "Note":
            node["widgets_values"] = [BACKGROUND_SWAP_NOTE]
            node["title"] = "Operator note"
    return graph


def main() -> None:
    still = build_still_app()
    studio = build_still_studio()
    image_studio = build_image_studio()
    gif = build_gif_loop()
    house = build_dream_house()
    house_clay = build_dream_house_clay()
    pack = build_platform_pack()
    draft = build_character_draft()
    tweak = build_character_tweak()
    swap = build_text_swap()
    bg = build_background_swap()
    _dump(lab_json("stills/still-daily.json"), still)
    _dump(lab_dest("stills/still-studio"), studio)
    _dump(lab_dest("stills/image-studio"), image_studio)
    _dump(lab_json("motion/loops/gif-loop.json"), gif)
    _dump(lab_json("stills/dream-house.json"), house)
    _dump(lab_dest("stills/dream-house-clay"), house_clay)
    _dump(lab_json("stills/platform-pack.json"), pack)
    _dump(lab_dest("stills/character-draft"), draft)
    _dump(lab_dest("stills/character-tweak"), tweak)
    _dump(lab_dest("stills/text-swap"), swap)
    _dump(lab_dest("stills/background-swap"), bg)
    print(
        "wrote still-app, still-studio, image-studio, gif-loop, dream-house, dream-house-clay, "
        "platform-pack, character draft/tweak, text-swap, background-swap"
    )


if __name__ == "__main__":
    main()
