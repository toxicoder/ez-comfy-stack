#!/usr/bin/env python3
"""Build the 200 services-pack lab graphs from existing printers.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_services_pack.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _lab_layout import LAB_GROUP_Y0, finalize_layout, group as _group
from _lab_paths import LAB_ROOT, ROOT, apply_lab_identity, lab_dest, lab_json
from _lab_theme import CREATOR_IDENTITY, I2V_LOCK, KLEIN_NEG_STILL
from _services_pack import SERVICES, ServiceSpec
from _stamp_app_mode import stamp_suite_graph
from _wire_format import pick_still_format, pick_video_format, wire_lab_graph
from _wire_prompt_enhance import enable_lab_graph, normalize_enhance_widgets

import _build_creator_video_workflows as cv

CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

SAMPLES_INDEX = (
    ROOT
    / "custom_nodes"
    / "ez_prompt_enhance"
    / "js"
    / "samples"
    / "index.json"
)
CATALOG_PAGE = ROOT / "docs" / "create" / "workflows-services.md"

PRODUCT_IDENTITY = (
    "A photoreal still of a cream ceramic mug with a hairline chip on the rim, "
    "unmarked, on honey-oak beside a dark window. Soft studio key, gentle contact "
    "shadow. Empty of lettering."
)
DESK_IDENTITY = (
    "A photoreal still of a sunlit oak desk with linen, an unmarked notebook, and "
    "a ceramic mug. Screens stay empty of logos. Empty of lettering."
)
FOOD_IDENTITY = (
    "A photoreal still of plated food on unmarked crockery, a linen napkin on oak, "
    "soft window sidelight. Empty of lettering."
)
PLACE_IDENTITY = (
    "A photoreal still of an unmarked interior, pale plaster and oak, no logos on "
    "walls or screens. Empty of lettering."
)
KLEIN_NEG_PHOTO = cv.KLEIN_NEG_PHOTO

GROUP_TITLES = {
    "ecommerce": "Ecommerce / product",
    "performance-ads": "Performance ads",
    "local-business": "Local business",
    "education": "Education / courses",
    "podcast-clips": "Podcast clips",
    "real-estate": "Real estate",
    "fashion-beauty": "Fashion and beauty",
    "b2b-saas": "B2B / SaaS",
    "events-wedding": "Events and wedding",
    "fitness-travel": "Fitness and travel",
}

OCC_LINE = {
    "klein": "klein - stop Wan, LTX, podcast, music",
    "wan": "wan - stop LTX, podcast, music",
    "ltx": "ltx - stop Wan, podcast, music, other LTX",
}

_STILL_FORMAT = "EZImageFormat"
_VIDEO_FORMAT = "EZVideoFormat"


def _identity(spec: ServiceSpec) -> str:
    if spec.identity == "product":
        base = PRODUCT_IDENTITY
    elif spec.identity == "desk":
        base = DESK_IDENTITY
    elif spec.identity == "food":
        base = FOOD_IDENTITY
    elif spec.identity == "interior":
        base = PLACE_IDENTITY
    else:
        base = CREATOR_IDENTITY
    return f"{base} {spec.lock}".strip()


def _note(spec: ServiceSpec) -> str:
    width, height = spec.size
    lines = [
        f"## {spec.rel}",
        "",
        f"{spec.title}. Lab size **{width}x{height}**. Prefix `{spec.prefix}`.",
        "Empty of lettering. Add titles in your editor, not in the prompt.",
        f"Occupancy: {OCC_LINE[spec.occupancy]}. One GB10 job.",
        "Handoff: none.",
    ]
    if spec.kind in {"wan_i2v", "wan_loop", "ltx_av"}:
        lines.append(
            "After Queue, click **Save video (MP4) - open node for preview**. "
            "File lands on `${COMFY_OUTPUT_DIR}`."
        )
        lines.append("LoadImage defaults to example.png so Queue smokes.")
    if spec.occupancy == "ltx":
        canvas = "768x1280" if spec.portrait else "1280x704"
        lines.append(
            f"LTX canvas {canvas} (width/height must be divisible by 32; "
            "720 and 1080 are invalid). Disclose AI-generated media. "
            "No score. Mouths will not match."
        )
    return "\n".join(lines) + "\n"


def _retarget_still_format(graph: dict[str, Any], spec: ServiceSpec) -> None:
    """Keep the printer format node; retarget pixels to this job."""
    nodes = [node for node in graph.get("nodes") or [] if node.get("type") == _STILL_FORMAT]
    if not nodes:
        return
    row = pick_still_format(spec.rel, spec.size[0], spec.size[1], spec.prefix)
    nodes[0]["widgets_values"] = [row.label, "none", spec.size[0], spec.size[1], 1]


def _retarget_video_format(graph: dict[str, Any], spec: ServiceSpec) -> None:
    """Keep the printer format node; retarget pixels to this job."""
    from ez_image.video_formats import FAMILY_LTX, FAMILY_WAN, get_family

    nodes = [node for node in graph.get("nodes") or [] if node.get("type") == _VIDEO_FORMAT]
    if not nodes:
        return
    family = FAMILY_WAN if spec.occupancy == "wan" else FAMILY_LTX
    row = pick_video_format(family, spec.size[0], spec.size[1])
    nodes[0]["widgets_values"] = [
        get_family(family).label,
        row.label,
        spec.size[0],
        spec.size[1],
    ]


def _dump(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(LAB_ROOT).with_suffix("").as_posix()
    apply_lab_identity(graph, rel)
    enable_lab_graph(graph)
    normalize_enhance_widgets(graph)
    wire_lab_graph(graph)
    stamp_suite_graph(graph)
    finalize_layout(graph)
    apply_lab_identity(graph, rel)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def _patch_cv_io() -> None:
    orig = cv.lab_json

    def lab_json(stem: str, **kwargs: Any) -> Path:
        try:
            return orig(stem, **kwargs)
        except FileNotFoundError:
            return lab_dest(str(stem).removesuffix(".json"))

    cv.lab_json = lab_json
    cv._dump = _dump


def _set_prompt_klein(graph: dict, prompt: str, *, enhance: bool) -> None:
    enh = cv._node(graph, "EZKleinPromptEnhance")
    values = list(enh["widgets_values"])
    values[0] = prompt
    values[1] = enhance
    enh["widgets_values"] = values
    cv._node(graph, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]


def _klein_single(spec: ServiceSpec) -> None:
    src = "stills/still-hero.json" if spec.template == "hero" else "stills/still-draft.json"
    graph = cv._load(lab_json(src))
    graph["id"] = spec.rel
    graph["revision"] = 1
    latent = cv._node(graph, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [spec.size[0], spec.size[1], 1]
    latent["title"] = f"Size {spec.size[0]}x{spec.size[1]}"
    _retarget_still_format(graph, spec)
    save = cv._node(graph, "SaveImage")
    save["widgets_values"] = [spec.prefix]
    save["title"] = "Save PNG"
    prompt = _identity(spec)
    _set_prompt_klein(graph, prompt, enhance=not spec.enhance_pin)
    if spec.identity in {"product", "food"}:
        cv._set_neg(graph, KLEIN_NEG_PHOTO)
    else:
        cv._set_neg(graph, KLEIN_NEG_STILL)
    cv._set_note(graph, _note(spec), spec.title)
    graph["groups"] = [
        _group(1, "MODEL", 20, LAB_GROUP_Y0, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, LAB_GROUP_Y0, 920, 400, "#3f789e"),
        _group(3, "SETTINGS", 1420, LAB_GROUP_Y0, 380, 500, "#a1309b"),
        _group(4, "OUTPUT", 1820, LAB_GROUP_Y0, 340, 430, "#3f789e"),
    ]
    _dump(lab_dest(spec.rel), graph)


def _set_wan_motion(graph: dict, motion: str, *, enhance: bool, hint: str) -> None:
    if I2V_LOCK.lower() not in motion.lower():
        motion = f"{motion.rstrip()} {I2V_LOCK}"
    cv._node(graph, "EZWanPromptEnhance")["widgets_values"] = [
        motion,
        enhance,
        "i2v",
        hint,
        "none",
    ]
    cv._node(graph, "CLIPTextEncode", "Motion / prompt")["widgets_values"] = [motion]


def _wan_i2v(spec: ServiceSpec) -> None:
    src = (
        "motion/silent/shorts-still-5s.json"
        if spec.portrait
        else "motion/silent/still-to-video-5s.json"
    )
    graph = cv._load(lab_json(src))
    graph["id"] = spec.rel
    graph["revision"] = 1
    lat = cv._node(graph, "Wan22ImageToVideoLatent")
    values = list(lat["widgets_values"])
    values[0], values[1], values[2] = spec.size[0], spec.size[1], 121
    lat["widgets_values"] = values
    lat["title"] = f"I2V size {spec.size[0]}x{spec.size[1]} x 121"
    _retarget_video_format(graph, spec)
    vhs = cv._node(graph, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = spec.prefix
    cv.polish_video_graph(graph)
    _set_wan_motion(
        graph,
        spec.lock,
        enhance=False,
        hint="5 seconds, 24 fps, 9:16" if spec.portrait else "5 seconds, 24 fps",
    )
    cv._set_note(graph, _note(spec), spec.title)
    _dump(lab_dest(spec.rel), graph)


def _wan_loop(spec: ServiceSpec) -> None:
    graph = cv._load(lab_json("motion/loops/gif-loop.json"))
    graph["id"] = spec.rel
    graph["revision"] = 1
    lat = cv._node(graph, "Wan22ImageToVideoLatent")
    values = list(lat["widgets_values"])
    values[0], values[1], values[2] = spec.size[0], spec.size[1], 49
    lat["widgets_values"] = values
    lat["title"] = f"Loop size {spec.size[0]}x{spec.size[1]} x 49"
    _retarget_video_format(graph, spec)
    vhs = cv._node(graph, "VHS_VideoCombine")
    vhs["widgets_values"]["format"] = "video/h264-mp4"
    vhs["widgets_values"]["pingpong"] = True
    vhs["widgets_values"]["frame_rate"] = 12
    vhs["widgets_values"]["filename_prefix"] = spec.prefix
    vhs["widgets_values"]["save_output"] = True
    cv.polish_video_graph(graph)
    for node in graph["nodes"]:
        if node.get("type") == "SaveImage":
            node["widgets_values"] = [f"{spec.prefix}_frames"]
            node["title"] = "Save frames (secondary)"
    _set_wan_motion(
        graph,
        spec.lock,
        enhance=False,
        hint="looping, 12 fps, ping-pong",
    )
    cv._set_note(graph, _note(spec), spec.title)
    _dump(lab_dest(spec.rel), graph)


def _set_ltx_size(graph: dict, width: int, height: int, length: int = 193) -> None:
    for node in graph["nodes"]:
        ntype = node.get("type")
        values = node.get("widgets_values")
        if not isinstance(values, list) or len(values) < 2:
            continue
        if ntype in {"LTXVImgToVideo", "EmptyLTXVLatentVideo"}:
            values[0], values[1] = width, height
            if len(values) >= 3:
                values[2] = length
            node["widgets_values"] = values
            node["title"] = f"Size {width}x{height}"
        if ntype == "LTXVEmptyLatentAudio" and values:
            values[0] = length
            node["widgets_values"] = values


def _ltx_av(spec: ServiceSpec) -> None:
    graph = cv._load(lab_json(f"{spec.template}.json"))
    graph["id"] = spec.rel
    graph["revision"] = 1
    cv.wire_ltx_audio(graph)
    _set_ltx_size(graph, spec.size[0], spec.size[1])
    _retarget_video_format(graph, spec)
    vhs = cv._node(graph, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = spec.prefix
    cv.polish_video_graph(graph)
    prompt = spec.lock
    if spec.ltx_mode == "i2v" and I2V_LOCK.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {I2V_LOCK}"
    hint = "8 seconds, 24 fps, 9:16" if spec.portrait else "8 seconds, 24 fps"
    cv._node(graph, "EZLTXPromptEnhance")["widgets_values"] = [
        prompt,
        True,
        spec.ltx_mode,
        hint,
        spec.audio_hint,
        "none",
    ]
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") in (
            "Positive",
            "Motion / prompt",
            "Motion + audio",
        ):
            node["widgets_values"] = [prompt]
    cv._set_note(graph, _note(spec), spec.title)
    _dump(lab_dest(spec.rel), graph)


def _update_sample_index() -> None:
    payload = json.loads(SAMPLES_INDEX.read_text(encoding="utf-8"))
    for spec in SERVICES:
        payload[spec.rel] = spec.sample_catalog
    SAMPLES_INDEX.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {SAMPLES_INDEX.relative_to(ROOT)}")


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _write_catalog() -> None:
    lines = [
        "---",
        "title: Services pack (agency Apps)",
        "description: Two hundred Klein, Wan, and LTX Apps for ecommerce, ads, local business, education, podcasts, real estate, fashion, B2B, events, and travel jobs.",
        "tags: [comfyui, workflows, services, klein, wan, ltx, catalog]",
        "---",
        "",
        "# Services pack (agency Apps)",
        "",
        "**What's on this page**",
        "",
        "- **Two hundred job Apps** nested under `_lab/services/<vertical>/`",
        "- **Agency SKUs** (product photography, paid-social, local business, courses, podcasts, listings, fashion, B2B, events, fitness/travel)",
        "- **Silent Wan loops / I2V** and **LTX AV** plates mixed into each vertical",
        "- **Lab sizes vs upload pixels** - Size column is the **default**. **Format / platform** retargets the same App. Match aspect; scale in an editor if a client wants more pixels",
        "",
        "**What this enables**",
        "",
        "- **Queuing a job-named App** (PDP on-white, UGC kitchen AV, listing walkthrough) instead of restyling a generic still",
        "- **Keeping occupancy XOR** - Klein, Wan, and LTX still do not share a GB10 session",
        "",
        "**Who this is for:** studio users after `stills/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).",
        "",
        "These graphs clone the shipped Klein 4B / Wan 2.2 / LTX-2.5 printers. They do **not** add models. Empty of lettering - composite titles later. LTX feeders stay **div32**.",
        "",
        "Safety impact: **none**. `restart: \"no\"`, headroom, and download-limit are unchanged.",
        "",
    ]
    current = ""
    for index, spec in enumerate(SERVICES):
        if spec.group != current:
            current = spec.group
            lines.extend(
                [
                    f"## {GROUP_TITLES[current]}",
                    "",
                    "| Workflow | Size | Prefix | What it does |",
                    "| --- | --- | --- | --- |",
                ]
            )
        width, height = spec.size
        link = f"**[{spec.rel}](../generated/workflows/{spec.rel}.md)**"
        lines.append(
            f"| {link} | {width}x{height} | `{spec.prefix}` | {_md_cell(spec.title)} |"
        )
        nxt = SERVICES[index + 1] if index + 1 < len(SERVICES) else None
        if nxt is None or nxt.group != current:
            lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    CATALOG_PAGE.write_text(text, encoding="utf-8")
    print(f"wrote {CATALOG_PAGE.relative_to(ROOT)}")


def build_all() -> None:
    _patch_cv_io()
    for spec in SERVICES:
        if spec.kind == "klein_single":
            _klein_single(spec)
        elif spec.kind == "wan_i2v":
            _wan_i2v(spec)
        elif spec.kind == "wan_loop":
            _wan_loop(spec)
        elif spec.kind == "ltx_av":
            _ltx_av(spec)
        else:
            raise SystemExit(f"unknown kind {spec.kind} for {spec.rel}")
    _update_sample_index()
    _write_catalog()


def main() -> None:
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    build_all()
    print("services pack done")


if __name__ == "__main__":
    main()
