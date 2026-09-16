#!/usr/bin/env python3
"""Build the 100 creator-pack lab graphs from existing printers.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_creator_pack3.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _creator_pack3 import PACK3, Pack3Spec
from _lab_layout import LAB_GROUP_Y0, ensure_group_title_inset, group as _group
from _lab_paths import LAB_ROOT, ROOT, apply_lab_identity, lab_dest, lab_json
from _lab_theme import CREATOR_IDENTITY, I2V_LOCK, KLEIN_NEG_STILL
from _stamp_app_mode import stamp_suite_graph
from _wire_prompt_enhance import enable_lab_graph, normalize_enhance_widgets

import _build_creator_video_workflows as cv

SAMPLES_INDEX = (
    ROOT
    / "custom_nodes"
    / "ez_prompt_enhance"
    / "js"
    / "samples"
    / "index.json"
)
CATALOG_PAGE = ROOT / "docs" / "create" / "workflows-creator.md"

PRODUCT_IDENTITY = (
    "A photoreal still of a cream ceramic mug with a hairline chip on the rim, "
    "unmarked, on honey-oak beside a dark window. Soft studio key, gentle contact "
    "shadow. Empty of lettering."
)
DESK_IDENTITY = (
    "A photoreal still of a sunlit oak desk with linen, an unmarked notebook, and "
    "a ceramic mug. Screens stay empty of logos. Empty of lettering."
)
STREAM_IDENTITY = (
    "A photoreal still of a dim unmarked streaming desk with teal practicals and a "
    "quiet backdrop. Empty of lettering and UI chrome."
)
KLEIN_NEG_PHOTO = cv.KLEIN_NEG_PHOTO

GROUP_TITLES = {
    "youtube": "YouTube",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "x": "X",
    "linkedin": "LinkedIn",
    "pinterest": "Pinterest",
    "meta": "Facebook and Threads",
    "twitch": "Twitch / stream",
    "spotify": "Spotify / music visual",
    "podcast": "Podcast visual",
    "merch": "Merch / print",
    "slides": "Slides / stream bg",
    "web": "Email / web",
    "production": "Production plates",
    "wan": "Silent motion (Wan 2.2)",
    "ltx": "AV (LTX-2.5)",
}

OCC_LINE = {
    "klein": "klein — stop Wan, LTX, podcast, music",
    "wan": "wan — stop LTX, podcast, music",
    "ltx": "ltx — stop Wan, podcast, music, other LTX",
}


def _identity(spec: Pack3Spec) -> str:
    if spec.identity == "product":
        base = PRODUCT_IDENTITY
    elif spec.identity == "desk":
        base = DESK_IDENTITY
    elif spec.identity == "stream":
        base = STREAM_IDENTITY
    else:
        base = CREATOR_IDENTITY
    return f"{base} {spec.lock}".strip()


def _note(spec: Pack3Spec) -> str:
    width, height = spec.size
    hand = ", ".join(f"**{item}**" for item in spec.handoff) or "none"
    lines = [
        f"## {spec.rel}",
        "",
        f"{spec.title}. Lab size **{width}×{height}**. Prefix `{spec.prefix}`.",
        "Empty of lettering. Add titles in your editor, not in the prompt.",
        f"Occupancy: {OCC_LINE[spec.occupancy]}. One GB10 job.",
        f"Handoff: {hand}.",
    ]
    if spec.prefixes:
        listed = ", ".join(f"`{item}`" for item in spec.prefixes)
        lines.append(f"Pack prefixes: {listed}.")
    if spec.kind in {"wan_i2v", "wan_loop", "ltx_av"}:
        lines.append(
            "After Queue, click **Save video (MP4) — open node for preview**. "
            "File lands on `${COMFY_OUTPUT_DIR}`."
        )
        lines.append("LoadImage defaults to example.png so Queue smokes.")
    if "spotify-canvas" in spec.rel:
        lines.append(
            "Spotify Canvas is silent 9:16, 3–8 s, MP4 or JPG. Scale in an editor "
            "if the current Canvas pixel range rejects this height."
        )
    if spec.occupancy == "ltx":
        canvas = "768×1280" if spec.portrait else "1280×704"
        lines.append(
            f"LTX canvas {canvas} (width/height must be divisible by 32; "
            "720 and 1080 are invalid). Disclose AI-generated media. "
            "No score. Mouths will not match."
        )
    return "\n".join(lines) + "\n"


def _dump(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(LAB_ROOT).with_suffix("").as_posix()
    apply_lab_identity(graph, rel)
    enable_lab_graph(graph)
    normalize_enhance_widgets(graph)
    stamp_suite_graph(graph)
    ensure_group_title_inset(graph)
    cv._assert_no_overlap(graph)
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


def _klein_single(spec: Pack3Spec) -> None:
    src = "klein/still-hero.json" if spec.template == "hero" else "klein/still-draft.json"
    graph = cv._load(lab_json(src))
    graph["id"] = spec.rel
    graph["revision"] = 1
    latent = cv._node(graph, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [spec.size[0], spec.size[1], 1]
    latent["title"] = f"Size {spec.size[0]}x{spec.size[1]}"
    save = cv._node(graph, "SaveImage")
    save["widgets_values"] = [spec.prefix]
    save["title"] = "Save PNG"
    prompt = _identity(spec)
    _set_prompt_klein(graph, prompt, enhance=not spec.enhance_pin)
    if spec.identity == "product":
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


def _klein_pack(spec: Pack3Spec) -> None:
    cv._klein_pack(
        stem=spec.rel,
        shots=list(spec.shots),
        size=spec.size,
        note=_note(spec),
        description=spec.title,
        identity=_identity(spec) if spec.lock else (
            PRODUCT_IDENTITY
            if spec.identity == "product"
            else DESK_IDENTITY
            if spec.identity == "desk"
            else STREAM_IDENTITY
            if spec.identity == "stream"
            else CREATOR_IDENTITY
        ),
        persist=spec.persist,
        neg=KLEIN_NEG_PHOTO if spec.identity == "product" else KLEIN_NEG_STILL,
    )


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


def _wan_i2v(spec: Pack3Spec) -> None:
    src = "wan/shorts-i2v.json" if spec.portrait else "wan/i2v-5s.json"
    graph = cv._load(lab_json(src))
    graph["id"] = spec.rel
    graph["revision"] = 1
    lat = cv._node(graph, "Wan22ImageToVideoLatent")
    values = list(lat["widgets_values"])
    values[0], values[1], values[2] = spec.size[0], spec.size[1], 121
    lat["widgets_values"] = values
    lat["title"] = f"I2V size {spec.size[0]}x{spec.size[1]} x 121"
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


def _wan_loop(spec: Pack3Spec) -> None:
    graph = cv._load(lab_json("wan/gif-loop.json"))
    graph["id"] = spec.rel
    graph["revision"] = 1
    lat = cv._node(graph, "Wan22ImageToVideoLatent")
    values = list(lat["widgets_values"])
    values[0], values[1], values[2] = spec.size[0], spec.size[1], 49
    lat["widgets_values"] = values
    lat["title"] = f"Loop size {spec.size[0]}x{spec.size[1]} x 49"
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


def _set_ltx_size(graph: dict, width: int, height: int, length: int = 121) -> None:
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


def _ltx_av(spec: Pack3Spec) -> None:
    graph = cv._load(lab_json(f"{spec.template}.json"))
    graph["id"] = spec.rel
    graph["revision"] = 1
    cv.wire_ltx_audio(graph)
    _set_ltx_size(graph, spec.size[0], spec.size[1])
    vhs = cv._node(graph, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = spec.prefix
    cv.polish_video_graph(graph)
    prompt = spec.lock
    if spec.ltx_mode == "i2v" and I2V_LOCK.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {I2V_LOCK}"
    hint = "5 seconds, 24 fps, 9:16" if spec.portrait else "5 seconds, 24 fps"
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
    for spec in PACK3:
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
        "title: Creator pack (platform Apps)",
        "description: One hundred extra Klein, Wan, and LTX Apps for YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify, merch, and production plates.",
        "tags: [comfyui, workflows, creator, klein, wan, ltx, catalog]",
        "---",
        "",
        "# Creator pack (platform Apps)",
        "",
        "**What's on this page**",
        "",
        "- **One hundred extra Apps** nested under `_lab/<lane>/creator/`",
        "- **Platform stills** (YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify)",
        "- **Silent Wan loops / I2V** and **LTX AV** job plates",
        "- **Lab sizes vs upload pixels** — match aspect; scale in an editor if a platform wants more pixels",
        "",
        "**What this enables**",
        "",
        "- **Queuing a job-named App** (channel art, 4:5 feed, Canvas loop, BRB screen) instead of restyling a generic still",
        "- **Keeping occupancy XOR** — Klein, Wan, and LTX still do not share a GB10 session",
        "",
        "**Who this is for:** studio users after `klein/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).",
        "",
        "These graphs clone the shipped Klein 4B / Wan 2.2 / LTX-2.5 printers. They do **not** add models. Empty of lettering — composite titles later. LTX feeders stay **÷32**. Spotify Canvas is **silent**.",
        "",
        "Safety impact: **none**. `restart: \"no\"`, headroom, and download-limit are unchanged.",
        "",
    ]
    current = ""
    for index, spec in enumerate(PACK3):
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
            f"| {link} | {width}×{height} | `{spec.prefix}` | {_md_cell(spec.title)} |"
        )
        nxt = PACK3[index + 1] if index + 1 < len(PACK3) else None
        if nxt is None or nxt.group != current:
            lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    CATALOG_PAGE.write_text(text, encoding="utf-8")
    print(f"wrote {CATALOG_PAGE.relative_to(ROOT)}")


def build_all() -> None:
    _patch_cv_io()
    for spec in PACK3:
        if spec.kind == "klein_single":
            _klein_single(spec)
        elif spec.kind == "klein_pack":
            _klein_pack(spec)
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
    print("pack3 done")


if __name__ == "__main__":
    main()
