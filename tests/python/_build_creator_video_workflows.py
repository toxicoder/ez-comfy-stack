#!/usr/bin/env python3
"""Build / patch lab workflows: LTX audio mux, preview UX, unified 90s films, creator toolkit.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_creator_video_workflows.py
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
import sys

from _wire_prompt_enhance import _rewrite_enhance_blurb, normalize_enhance_widgets
from _lab_theme import (
    CREATOR_IDENTITY,
    I2V_LOCK,
    KLEIN_HOOK,
    KLEIN_NEG_STILL,
    KLEIN_SHORTS,
    KLEIN_THUMBNAIL,
    LTX_BROLL,
    LTX_BROLL_AUDIO,
    LTX_HOOK_AUDIO,
    LTX_HOOK_AV,
    LTX_SHORTS_AUDIO,
    LTX_SHORTS_I2V,
    LTX_WEATHER,
    LTX_WEATHER_AUDIO,
    ROOFTOP_INVENTORY,
    STORYBOARD,
    WAN_ORBIT,
    WAN_SHORTS_I2V,
)

ENHANCE_NOTE = (
    "Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, "
    "the Enhance node shows the prompt CLIP used. Turn Enhance off to pin the widget text."
)

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_prompt_enhance.client import join_prompt  # noqa: E402

WF = ROOT / "workflows"
SHORTS = WF / "shorts"

PREVIEW_BULLET = (
    "After Queue, click **Save video (MP4) — open node for preview** for an inline "
    "preview. File lands on the host at `${COMFY_OUTPUT_DIR}/ez_*_*.mp4` "
    "(container `/outputs`). Save frames PNG is secondary."
)
LTX_CANVAS_LANDSCAPE = (
    "LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid)."
)
LTX_CANVAS_PORTRAIT = (
    "LTX canvas 768x1280 (width/height must be divisible by 32; 720 and 1080 are invalid)."
)
GIF_PREVIEW_BULLET = (
    "After Queue, click **Infinite loop (ping-pong) — open for preview** for an "
    "inline preview. File lands on the host at `${COMFY_OUTPUT_DIR}/ez_gif_loop_*.gif`."
)

CREATOR_STEMS = (
    "klein-shorts-still-lab-example",
    "wan-shorts-i2v-lab-example",
    "ltx-shorts-i2v-lab-example",
    "klein-thumbnail-lab-example",
    "klein-product-packshot-lab-example",
    "klein-before-after-lab-example",
    "klein-style-lock-lab-example",
    "wan-bumper-loop-lab-example",
    "ltx-broll-ambient-lab-example",
    "klein-storyboard-6up-lab-example",
)

CREATOR_STEMS_V2 = (
    "klein-endcard-cta-lab-example",
    "klein-quote-bg-lab-example",
    "klein-og-blog-lab-example",
    "klein-podcast-cover-lab-example",
    "klein-banner-wide-lab-example",
    "klein-ig-square-lab-example",
    "klein-hook-still-lab-example",
    "klein-lower-third-bg-lab-example",
    "klein-food-tabletop-lab-example",
    "klein-lighting-trio-lab-example",
    "klein-time-of-day-lab-example",
    "klein-camera-angles-lab-example",
    "klein-color-moods-lab-example",
    "wan-orbit-i2v-lab-example",
    "wan-push-in-i2v-lab-example",
    "wan-parallax-i2v-lab-example",
    "wan-sticker-loop-lab-example",
    "ltx-weather-broll-lab-example",
    "ltx-interior-ambience-lab-example",
    "ltx-hook-av-lab-example",
)

FILMS = (
    (
        "go-see",
        "gosee",
        "film-go-see-90s-run-lab-example",
        "go-see.shots.yaml",
        "first-person running",
    ),
    (
        "still-here",
        "stillhere",
        "film-still-here-90s-lab-example",
        "still-here.shots.yaml",
        "household morning",
    ),
    (
        "switchyard",
        "switchyard",
        "film-switchyard-90s-lab-example",
        "switchyard.shots.yaml",
        "night freight yard",
    ),
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, graph: dict) -> None:
    _assert_no_overlap(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


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


def _nodes_by_type(graph: dict, ntype: str) -> list[dict]:
    return [n for n in graph["nodes"] if n.get("type") == ntype]


def _node(graph: dict, ntype: str, title: str | None = None) -> dict:
    for n in graph["nodes"]:
        if n.get("type") != ntype:
            continue
        if title is None or n.get("title") == title:
            return n
    raise KeyError(f"{ntype} {title}")


def _group(gid: int, title: str, x: float, y: float, w: float, h: float, color: str) -> dict:
    return {
        "id": gid,
        "title": title,
        "bounding": [x, y, w, h],
        "color": color,
        "font_size": 24,
        "flags": {},
    }


def _ensure_preview_line(text: str, *, gif: bool = False) -> str:
    bullet = GIF_PREVIEW_BULLET if gif else PREVIEW_BULLET
    if "open node for preview" in text or "open for preview" in text:
        return text
    # Insert after the first heading line
    lines = text.split("\n")
    if lines and lines[0].startswith("##"):
        return lines[0] + "\n\n" + bullet + "\n" + "\n".join(lines[1:])
    return bullet + "\n\n" + text


def wire_ltx_audio(graph: dict) -> dict:
    """Attach LTXVAudioVAEDecode → VHS.audio if missing."""
    if any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"]):
        # Still ensure VHS.audio is linked
        vhs = _node(graph, "VHS_VideoCombine")
        audio_in = next(i for i in vhs["inputs"] if i["name"] == "audio")
        if audio_in.get("link") is not None:
            return graph

    separate = _node(graph, "LTXVSeparateAVLatent")
    audio_vae = next(
        n
        for n in graph["nodes"]
        if n.get("type") == "VAELoader" and "audio" in (n.get("title") or "").lower()
    )
    vhs = _node(graph, "VHS_VideoCombine")

    new_id = int(graph["last_node_id"]) + 1
    link_base = int(graph["last_link_id"])

    # Link IDs
    link_samples = link_base + 1
    link_vae = link_base + 2
    link_audio = link_base + 3

    # Place beside VHS, not below (shot graphs already use the space under VAEDecode).
    decode = {
        "id": new_id,
        "type": "LTXVAudioVAEDecode",
        "pos": [vhs["pos"][0] + 360, vhs["pos"][1]],
        "size": [320, 66],
        "flags": {},
        "order": max(n.get("order", 0) for n in graph["nodes"]) + 1,
        "mode": 0,
        "inputs": [
            {"name": "samples", "type": "LATENT", "link": link_samples},
            {"name": "audio_vae", "type": "VAE", "link": link_vae},
        ],
        "outputs": [
            {
                "name": "Audio",
                "type": "AUDIO",
                "links": [link_audio],
                "slot_index": 0,
            }
        ],
        "properties": {"Node name for S&R": "LTXVAudioVAEDecode"},
        "widgets_values": [],
        "title": "Audio VAE Decode",
    }
    graph["nodes"].append(decode)

    # Separate audio_latent output (slot 1)
    audio_out = separate["outputs"][1]
    assert audio_out["name"] == "audio_latent"
    existing = audio_out.get("links") or []
    if not isinstance(existing, list):
        existing = []
    audio_out["links"] = existing + [link_samples]

    # Fan-out audio VAE loader
    vae_out = audio_vae["outputs"][0]
    vae_links = vae_out.get("links") or []
    if not isinstance(vae_links, list):
        vae_links = []
    vae_out["links"] = vae_links + [link_vae]

    # VHS audio input
    audio_in = next(i for i in vhs["inputs"] if i["name"] == "audio")
    audio_in["link"] = link_audio

    graph["links"].extend(
        [
            [link_samples, separate["id"], 1, new_id, 0, "LATENT"],
            [link_vae, audio_vae["id"], 0, new_id, 1, "VAE"],
            [link_audio, new_id, 0, vhs["id"], 1, "AUDIO"],
        ]
    )
    graph["last_node_id"] = new_id
    graph["last_link_id"] = link_audio
    return graph


def polish_video_graph(graph: dict, *, gif: bool = False) -> dict:
    """Titles, save_output, preview note."""
    for n in graph["nodes"]:
        if n.get("type") == "VHS_VideoCombine":
            wv = n["widgets_values"]
            if isinstance(wv, dict):
                wv["save_output"] = True
            if gif:
                n["title"] = "Infinite loop (ping-pong) — open for preview"
            else:
                n["title"] = "Save video (MP4) — open node for preview"
        if n.get("type") == "SaveImage":
            title = n.get("title") or ""
            if "last" in title.lower():
                continue
            if "secondary" not in title.lower():
                n["title"] = "Save frames (secondary)"

    for n in graph["nodes"]:
        if n.get("type") not in ("Note", "MarkdownNote"):
            continue
        vals = n.get("widgets_values")
        if not isinstance(vals, list) or not vals:
            continue
        text = str(vals[0])
        if n.get("type") == "MarkdownNote" and "shot map" in text.lower():
            continue
        n["widgets_values"][0] = _rewrite_enhance_blurb(
            _ensure_preview_line(text, gif=gif)
        )

    extra = graph.setdefault("extra", {})
    if isinstance(extra.get("lab_note"), str):
        extra["lab_note"] = _rewrite_enhance_blurb(
            _ensure_preview_line(extra["lab_note"], gif=gif)
        )
    return graph


def patch_existing_video_graphs() -> None:
    video_files = [
        WF / "wan-i2v-5s-lab-example.json",
        WF / "wan-t2v-5s-lab-example.json",
        WF / "wan-i2v-shot-lab-example.json",
        WF / "ltx-i2v-5s-lab-example.json",
        WF / "ltx-t2v-5s-lab-example.json",
        WF / "ltx-i2v-shot-lab-example.json",
        WF / "wan-gif-loop-lab-example.json",
    ]
    for path in video_files:
        graph = _load(path)
        gif = path.name.startswith("wan-gif")
        if path.name.startswith("ltx-"):
            wire_ltx_audio(graph)
        polish_video_graph(graph, gif=gif)
        normalize_enhance_widgets(graph)
        # Point shot notes at unified films
        if path.name in (
            "wan-i2v-shot-lab-example.json",
            "ltx-i2v-shot-lab-example.json",
        ):
            note = next(n for n in graph["nodes"] if n.get("type") == "Note")
            text = note["widgets_values"][0]
            tip = (
                "\n90s films: prefer the unified **film-*-90s-*-lab-example** graphs "
                "(identity + LTX print + shot map in one file). This graph remains the "
                "generic 5.00s printer / Wan rehearsal.\n"
            )
            if "unified" not in text:
                note["widgets_values"][0] = text.rstrip() + tip
                graph["extra"]["lab_note"] = note["widgets_values"][0]
        _dump(path, graph)


# --- YAML shot map helpers -------------------------------------------------


def _parse_shots_yaml(text: str) -> dict:
    meta: dict[str, str] = {}
    for key in (
        "film",
        "slug",
        "frames",
        "fps",
        "duration_s",
        "beats",
        "shots_per_beat",
        "total_shots",
        "publish_cap_s",
    ):
        m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        if not m:
            raise SystemExit(f"missing meta {key}")
        meta[key] = m.group(1).strip()

    ident_m = re.search(r"^identity_look:\s*\|\s*\n((?:  .*\n)+)", text, re.M)
    if not ident_m:
        raise SystemExit("missing identity_look")
    identity = " ".join(line.strip() for line in ident_m.group(1).splitlines() if line.strip())

    shots: list[dict[str, str]] = []
    blocks = re.split(r"\n  - beat:", text)[1:]
    for block in blocks:
        body = "beat:" + block

        def field(name: str) -> str:
            m = re.search(rf"^\s*{name}:\s*(.+)$", body, re.M)
            if not m:
                raise SystemExit(f"missing {name}")
            return m.group(1).strip()

        def block_field(name: str) -> str:
            m = re.search(rf"^[ \t]*{name}:[ \t]*\|[ \t]*\n", body, re.M)
            if not m:
                raise SystemExit(f"missing block {name}")
            lines = []
            for line in body[m.end() :].splitlines():
                # Shot fields are indented 4 spaces; folded content is 6+.
                if re.match(r"^    \S", line):
                    break
                if not line.strip():
                    break
                if re.match(r"^      \S", line) or re.match(r"^        \S", line):
                    lines.append(line.strip())
                else:
                    break
            if not lines:
                raise SystemExit(f"empty block {name}")
            return " ".join(lines)

        shots.append(
            {
                "beat": field("beat"),
                "shot": field("shot"),
                "prefix": field("prefix"),
                "load_from": field("load_from"),
                "motion": block_field("motion"),
                "audio": block_field("audio"),
            }
        )
    return {"meta": meta, "identity": identity, "shots": shots}


def build_shot_map_markdown(film: str, label: str, parsed: dict) -> str:
    slug = parsed["meta"]["slug"]
    lines = [
        f"## {film} 90s shot map ({label})",
        "",
        "Unified graph: Queue **Identity (Klein)** once (LTX group starts bypassed).",
        "Then Ctrl+B to bypass Identity and enable **Shot print (LTX)**. Retarget LoadImage,",
        "Motion+Audio, and prefixes for each of 18 shots. Optional Wan rehearsal:",
        "**wan-i2v-shot-lab-example**.",
        "",
        "18 × 120 frames @ 24 fps = 90.00s. Last frame of shot N is LoadImage of shot N+1.",
        f"Concat: `./scripts/utilities/concat-shots.sh --film {film} --yes`",
        "",
        "Do not Queue a 90s denoise in one graph. US-safe local pack only. No score "
        "(breath and world only).",
        "",
        f"**Identity look:** {parsed['identity']}",
        "",
    ]
    for s in parsed["shots"]:
        p = s["prefix"]
        lines.extend(
            [
                f"### b{s['beat']} s{s['shot']} `{p}`",
                f"- LoadImage: `{s['load_from']}`",
                f"- VHS LTX: `{p}_ltx_video` · last: `{p}_last` · optional Wan: `{p}_wan_video`",
                f"- Motion: {s['motion']}",
                f"- Audio: {s['audio']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_film_operator_note(stem: str, film: str, slug: str, label: str) -> str:
    return f"""## {stem}

{LTX_CANVAS_LANDSCAPE}

Unified 90s film graph ({label}): Klein identity still + LTX 5.00s AV shot printer + shot map.
Models: Klein 4B distilled FP8 (identity) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

{PREVIEW_BULLET}

1. Leave **Shot print (LTX)** bypassed (Ctrl+B). Queue **Identity (Klein)** → `ez_{slug}_identity_*.png`.
2. Bypass Identity; enable Shot print. Set LoadImage to the identity PNG (shot 1) or previous `*_last`.
3. Paste Motion + Audio from the on-canvas shot map. Set VHS prefix `ez_{slug}_bN_sM_ltx_video` and last-frame `ez_{slug}_bN_sM_last`. Queue **5.00s** AV.
4. Repeat 18 times. Optional silent rehearsal: **wan-i2v-shot-lab-example**.
5. `./scripts/utilities/concat-shots.sh --film {film} --yes`

Do not Queue a 90s denoise. US-safe local pack only. No score.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used. Turn Enhance off to pin canned identity.
"""


def _remap_subgraph(nodes: list[dict], links: list[list], id_offset: int, link_offset: int, pos_dx: float, pos_dy: float) -> tuple[list[dict], list[list], dict[int, int]]:
    id_map = {n["id"]: n["id"] + id_offset for n in nodes}
    new_nodes = []
    for n in nodes:
        nn = copy.deepcopy(n)
        nn["id"] = id_map[n["id"]]
        nn["pos"] = [n["pos"][0] + pos_dx, n["pos"][1] + pos_dy]
        for inp in nn.get("inputs") or []:
            if inp.get("link") is not None:
                inp["link"] = int(inp["link"]) + link_offset
        for out in nn.get("outputs") or []:
            links_list = out.get("links")
            if isinstance(links_list, list):
                out["links"] = [int(x) + link_offset for x in links_list]
        new_nodes.append(nn)

    new_links = []
    for link in links:
        lid, src, src_slot, dst, dst_slot, ltype = link
        new_links.append(
            [
                int(lid) + link_offset,
                id_map[src],
                src_slot,
                id_map[dst],
                dst_slot,
                ltype,
            ]
        )
    return new_nodes, new_links, id_map


def _refresh_film_notes(graph: dict, film: str, slug: str, stem: str, label: str, yaml_name: str) -> dict:
    parsed = _parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
    shot_md = build_shot_map_markdown(film, label, parsed)
    op_note = build_film_operator_note(stem, film, slug, label)
    for n in graph["nodes"]:
        if n.get("type") == "Note":
            n["widgets_values"] = [op_note]
            n["title"] = "Operator note — unified 90s film"
        if n.get("type") == "MarkdownNote":
            n["widgets_values"] = [shot_md]
            n["title"] = f"{film} 90s shot map"
            n["size"] = [960, max(float(n["size"][1]), 1400)]
    for n in graph["nodes"]:
        if n.get("type") == "LTXVImgToVideo":
            vals = n.get("widgets_values") or []
            if len(vals) >= 2:
                vals[0], vals[1] = 1280, 704
    # Ensure LTX audio + preview polish on embedded printer
    if not any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"]):
        # Only wire if a VHS exists (unified graph)
        if any(n.get("type") == "VHS_VideoCombine" for n in graph["nodes"]):
            wire_ltx_audio(graph)
    for n in graph["nodes"]:
        if n.get("type") == "VHS_VideoCombine":
            n["title"] = "Save video (MP4) — open node for preview"
            n["widgets_values"]["save_output"] = True
        if n.get("type") == "SaveImage" and "last" not in (n.get("title") or "").lower():
            if "identity" in str(n.get("widgets_values", [""])[0]):
                n["title"] = "Save identity PNG"
            elif "secondary" not in (n.get("title") or "").lower() and n.get("title") != "Save identity PNG":
                if "ltx_frames" in str(n.get("widgets_values", [""])[0]) or "frames" in (n.get("title") or "").lower():
                    n["title"] = "Save frames (secondary)"
    graph.setdefault("extra", {})
    graph["extra"]["lab_note"] = op_note
    graph["extra"]["lab_description"] = f"Unified 90s {label}: Klein identity + LTX 5.00s AV shots"
    graph["extra"]["lab_film"] = film
    graph["extra"]["lab_slug"] = slug
    graph["extra"]["lab_ltx_av"] = True
    graph["extra"]["lab_profile"] = stem
    normalize_enhance_widgets(graph)
    return graph


def build_unified_film(
    film: str,
    slug: str,
    stem: str,
    yaml_name: str,
    label: str,
) -> dict:
    raw = _load(SHORTS / f"{stem}.json")
    # Idempotent: already unified → refresh notes/maps/audio only.
    if any(n.get("type") == "LTXVImgToVideo" for n in raw["nodes"]):
        return _refresh_film_notes(raw, film, slug, stem, label, yaml_name)

    klein = raw
    ltx = _load(WF / "ltx-i2v-shot-lab-example.json")
    # Ensure audio already wired in source
    wire_ltx_audio(ltx)
    polish_video_graph(ltx)

    parsed = _parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
    shot_md = build_shot_map_markdown(film, label, parsed)
    op_note = build_film_operator_note(stem, film, slug, label)

    # Strip LTX notes — film keeps one Note + MarkdownNote
    ltx_nodes = [n for n in ltx["nodes"] if n.get("type") not in ("Note", "MarkdownNote")]
    ltx_note_ids = {n["id"] for n in ltx["nodes"] if n.get("type") in ("Note", "MarkdownNote")}
    ltx_links = [
        link
        for link in ltx["links"]
        if link[1] not in ltx_note_ids and link[3] not in ltx_note_ids
    ]

    klein_max_id = max(n["id"] for n in klein["nodes"])
    klein_max_link = max((link[0] for link in klein.get("links") or []), default=0)
    # Place LTX to the right of Klein
    remapped_nodes, remapped_links, id_map = _remap_subgraph(
        ltx_nodes,
        ltx_links,
        id_offset=klein_max_id + 10,
        link_offset=klein_max_link + 10,
        pos_dx=3200,
        pos_dy=0,
    )

    # Default: bypass LTX compute so first Queue is identity-only
    bypass_types = {
        "UNETLoader",
        "VAELoader",
        "CLIPLoader",
        "LoadImage",
        "CLIPTextEncode",
        "EZLTXPromptEnhance",
        "LTXVImgToVideo",
        "LTXVConditioning",
        "KSampler",
        "LTXVEmptyLatentAudio",
        "LTXVConcatAVLatent",
        "LTXVSeparateAVLatent",
        "VAEDecode",
        "LTXVAudioVAEDecode",
        "VHS_VideoCombine",
        "SaveImage",
        "ImageFromBatch",
    }
    for n in remapped_nodes:
        if n["type"] in bypass_types:
            n["mode"] = 4  # Bypass

    # Retarget LTX prefixes for this film's b1s1
    prefix = f"ez_{slug}_b1_s1"
    for n in remapped_nodes:
        if n.get("type") == "VHS_VideoCombine":
            n["widgets_values"]["filename_prefix"] = f"{prefix}_ltx_video"
            n["title"] = "Save video (MP4) — open node for preview"
        if n.get("type") == "SaveImage":
            w = n["widgets_values"][0]
            if "last" in (n.get("title") or "").lower() or w.endswith("_last"):
                n["widgets_values"] = [f"{prefix}_last"]
                n["title"] = "Save last frame"
            else:
                n["widgets_values"] = [f"{prefix}_ltx_frames"]
                n["title"] = "Save frames (secondary)"

    # Update Klein note + markdown
    for n in klein["nodes"]:
        if n.get("type") == "Note":
            n["widgets_values"] = [op_note]
            n["title"] = "Operator note — unified 90s film"
        if n.get("type") == "MarkdownNote":
            n["widgets_values"] = [shot_md]
            n["title"] = f"{film} 90s shot map"
            # Widen for audio lines
            n["size"] = [960, max(float(n["size"][1]), 1400)]

    # Title Klein save
    for n in klein["nodes"]:
        if n.get("type") == "SaveImage":
            n["title"] = "Save identity PNG"

    graph: dict = {
        "id": stem,
        "revision": int(klein.get("revision", 1)) + 1,
        "last_node_id": max(n["id"] for n in remapped_nodes + klein["nodes"]),
        "last_link_id": max(
            (link[0] for link in (klein.get("links") or []) + remapped_links),
            default=0,
        ),
        "nodes": klein["nodes"] + remapped_nodes,
        "links": list(klein.get("links") or []) + remapped_links,
        "groups": [
            _group(1, "1. Identity (Klein) — Queue first", 20, 20, 2000, 1200, "#3f789e"),
            _group(
                2,
                "2. Shot print (LTX) — starts bypassed; Ctrl+B to enable",
                3180,
                20,
                2800,
                1400,
                "#a1309b",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": stem,
            "lab_note": op_note,
            "lab_description": f"Unified 90s {label}: Klein identity + LTX 5.00s AV shots",
            "lab_film": film,
            "lab_slug": slug,
            "lab_ltx_av": True,
        },
        "version": 0.4,
    }
    return graph


def build_all_films() -> None:
    for film, slug, stem, yaml_name, label in FILMS:
        graph = build_unified_film(film, slug, stem, yaml_name, label)
        _dump(SHORTS / f"{stem}.json", graph)


# --- Creator toolkit -------------------------------------------------------


KLEIN_NEG_PHOTO = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)


def _set_neg(graph: dict, text: str) -> None:
    for n in graph["nodes"]:
        if n.get("type") == "CLIPTextEncode" and n.get("title") == "Negative":
            n["widgets_values"] = [text]


def _set_note(graph: dict, note: str, description: str) -> None:
    graph["extra"]["lab_note"] = note
    graph["extra"]["lab_description"] = description
    graph["extra"]["lab_profile"] = graph["id"]
    for n in graph["nodes"]:
        if n.get("type") == "Note":
            n["widgets_values"] = [note]
            break


def build_creator_toolkit() -> None:
    # 1. Vertical Shorts still
    g = _load(WF / "klein-still-draft-lab-example.json")
    g["id"] = "klein-shorts-still-lab-example"
    g["revision"] = 1
    latent = _node(g, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [432, 768, 1]
    latent["title"] = "Size 9:16 (width x height x batch)"
    save = _node(g, "SaveImage")
    save["widgets_values"] = ["ez_shorts_still"]
    save["title"] = "Save PNG"
    enh = _node(g, "EZKleinPromptEnhance")
    prompt = KLEIN_SHORTS
    enh["widgets_values"][0] = prompt
    _node(g, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]
    note = f"""## klein-shorts-still-lab-example

Vertical Shorts/Reels still (Klein 4B distilled FP8). Default **432×768** (9:16).
Save prefix: `ez_shorts_still`. Feed into **wan-shorts-i2v-lab-example** or **ltx-shorts-i2v-lab-example**.
Widgets: seed / steps / CFG / size on canvas. Prompt enhance is on by default; read the rewrite on the node after Queue.
"""
    _set_note(g, note, "Klein 4B vertical 9:16 Shorts still")
    g["groups"] = [
        _group(1, "MODEL", 20, 40, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, 40, 920, 400, "#3f789e"),
        _group(3, "SETTINGS", 1420, 40, 380, 500, "#a1309b"),
        _group(4, "OUTPUT", 1820, 40, 340, 430, "#3f789e"),
    ]
    _dump(WF / "klein-shorts-still-lab-example.json", g)

    # 2. Vertical Wan I2V
    g = _load(WF / "wan-i2v-5s-lab-example.json")
    g["id"] = "wan-shorts-i2v-lab-example"
    g["revision"] = 1
    lat = _node(g, "Wan22ImageToVideoLatent")
    # width, height, length — keep 121 smoke length; vertical size
    vals = list(lat["widgets_values"])
    # Typical order: width, height, length, batch… inspect
    # Wan22ImageToVideoLatent widgets: [width, height, length, batch]
    if len(vals) >= 3:
        vals[0], vals[1] = 480, 832
        vals[2] = 121
        lat["widgets_values"] = vals
    lat["title"] = "Vertical size + length (9:16)"
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = "ez_shorts_wan_video"
    polish_video_graph(g)
    motion = WAN_SHORTS_I2V
    enh = _node(g, "EZWanPromptEnhance")
    enh["widgets_values"] = [motion, True, "i2v", "5 seconds, 24 fps, 9:16", "none"]
    _node(g, "CLIPTextEncode", "Motion / prompt")["widgets_values"] = [motion]
    note = f"""## wan-shorts-i2v-lab-example

Vertical silent Wan 5B I2V for Shorts (~5 s @ 24 fps). Apache 2.0.
LoadImage: `ez_shorts_still_*.png` (or example.png to smoke-test).
PRIMARY OUTPUT: MP4 via VHS. Prefix `ez_shorts_wan_video`.

{PREVIEW_BULLET}
"""
    _set_note(g, note, "Wan 5B vertical 9:16 silent I2V ~5s")
    _dump(WF / "wan-shorts-i2v-lab-example.json", g)

    # 3. Vertical LTX I2V AV
    g = _load(WF / "ltx-i2v-5s-lab-example.json")
    g["id"] = "ltx-shorts-i2v-lab-example"
    g["revision"] = 1
    wire_ltx_audio(g)
    # LTXVImgToVideo widgets include width/height/length
    img2v = _node(g, "LTXVImgToVideo")
    wvals = list(img2v["widgets_values"])
    # common: [width, height, length, ...]
    if len(wvals) >= 3:
        wvals[0], wvals[1], wvals[2] = 768, 1280, 121
        img2v["widgets_values"] = wvals
    img2v["title"] = "Vertical I2V (9:16)"
    audio = _node(g, "LTXVEmptyLatentAudio")
    audio["widgets_values"][0] = 121
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = "ez_shorts_ltx_video"
    polish_video_graph(g)
    prompt = LTX_SHORTS_I2V
    enh = _node(g, "EZLTXPromptEnhance")
    enh["widgets_values"] = [prompt, True, "i2v", "5 seconds, 24 fps, 9:16", LTX_SHORTS_AUDIO, "none"]
    for n in g["nodes"]:
        if n.get("type") == "CLIPTextEncode" and n.get("title") in (
            "Positive",
            "Motion / prompt",
            "Motion + audio",
        ):
            n["widgets_values"] = [prompt]
    note = f"""## ltx-shorts-i2v-lab-example

{LTX_CANVAS_PORTRAIT}

Vertical AV Shorts I2V (~5 s). LTX-2.5 distilled. Community License — not Apache. $10M cap.
LoadImage: `ez_shorts_still_*.png`. Prefix `ez_shorts_ltx_video`. World audio muxed into MP4.

{PREVIEW_BULLET}
Disclose AI-generated media; do not strip provenance; do not distill. No score.
"""
    _set_note(g, note, "LTX-2.5 vertical 9:16 AV I2V ~5s")
    _dump(WF / "ltx-shorts-i2v-lab-example.json", g)

    # 4. Thumbnail
    g = _load(WF / "klein-still-hero-lab-example.json")
    g["id"] = "klein-thumbnail-lab-example"
    g["revision"] = 1
    save = _node(g, "SaveImage")
    save["widgets_values"] = ["ez_thumbnail"]
    prompt = KLEIN_THUMBNAIL
    enh = _node(g, "EZKleinPromptEnhance")
    enh["widgets_values"][0] = prompt
    _node(g, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]
    note = """## klein-thumbnail-lab-example

YouTube thumbnail still (Klein 4B). Default 1280×720. Prefix `ez_thumbnail`.
Keep the subject large and readable at small sizes. Do not burn in titles — add text in your editor.
"""
    _set_note(g, note, "Klein 4B YouTube thumbnail 1280x720")
    _dump(WF / "klein-thumbnail-lab-example.json", g)

    # 5. Product packshot
    g = _load(WF / "klein-still-hero-lab-example.json")
    g["id"] = "klein-product-packshot-lab-example"
    g["revision"] = 1
    save = _node(g, "SaveImage")
    save["widgets_values"] = ["ez_packshot"]
    latent = _node(g, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [1024, 1024, 1]
    prompt = (
        "A clean product packshot on a seamless light-gray cyclorama. A matte ceramic mug "
        "centered, soft studio key light, gentle contact shadow, unmarked surface, no logos. "
        "Photoreal commercial still, square 1:1 framing."
    )
    enh = _node(g, "EZKleinPromptEnhance")
    enh["widgets_values"][0] = prompt
    _node(g, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]
    _set_neg(g, KLEIN_NEG_PHOTO)
    note = """## klein-product-packshot-lab-example

Clean product / packshot still (Klein 4B). Default 1024×1024. Prefix `ez_packshot`.
Swap the subject in the prompt; keep seamless background and soft studio light.
"""
    _set_note(g, note, "Klein 4B product packshot 1:1")
    _dump(WF / "klein-product-packshot-lab-example.json", g)

    mug_identity = (
        "A photoreal still of a small kitchen table at first light. One cream ceramic mug "
        "with a hairline chip on the rim sits empty on honey-oak beside a dark window. "
        "White subway tile, one linen curtain. Cool blue shadows, unmarked surfaces."
    )
    _klein_pack(
        stem="klein-before-after-lab-example",
        size=(768, 432),
        identity=mug_identity,
        inventory="cream ceramic mug with a hairline chip, honey-oak table, white subway tile, linen curtain",
        shots=[
            (
                "ez_before",
                "BEFORE",
                "Canonical plate. Empty mug, cool blue window light, same 35mm camera.",
            ),
            (
                "ez_after",
                "AFTER",
                "Same kitchen, mug, and camera. Mug filled with coffee, warm morning sun, soft steam.",
            ),
        ],
        neg=KLEIN_NEG_PHOTO,
        note=f"""## klein-before-after-lab-example

Two Klein 4B stills of one mug. SHOT BEFORE is the identity plate; AFTER Klein-edits from it. Prefixes `ez_before` and `ez_after`. Do not bypass BEFORE on a cold canvas.

{ENHANCE_NOTE}
""",
        description="Klein 4B before/after still pair",
    )

    house_lock = (
        "One contemporary cedar-and-glass lake house. Vertical cedar siding, charcoal "
        "standing-seam hip roof, tall black-framed windows, unmarked surfaces, solitary, "
        "empty of people."
    )
    _klein_pack(
        stem="klein-style-lock-lab-example",
        size=(768, 960),
        identity=house_lock,
        inventory=(
            "vertical cedar siding, charcoal standing-seam hip roof, tall black-framed "
            "windows, linen sofa facing the lake glass, oak floors"
        ),
        persist="view",
        shots=[
            (
                "ez_style_01",
                "CURB",
                "Three-quarter lake facade of the same house, 24mm, golden-hour, Instagram "
                "4:5. Glass shows the linen sofa and oak floors inside.",
            ),
            (
                "ez_style_02",
                "LIVING",
                "From inside the living room of the same house, looking out the glass to "
                "the lake, late-day sun. Linen sofa in the foreground.",
            ),
            (
                "ez_style_03",
                "DECK",
                "Lakeside deck of the same house at dusk, cedar boards, quiet water, "
                "evergreen ridge.",
            ),
            (
                "ez_style_04",
                "TWILIGHT",
                "Twilight exterior of the same house. Lamps on; sofa silhouette through "
                "black-framed glass.",
            ),
        ],
        hint="Instagram 4:5 still",
        neg=KLEIN_NEG_PHOTO,
        note=f"""## klein-style-lock-lab-example

Four Klein 4B stills of one lake house from new cameras (Prompt Join lock=view). Locked inventory repeats through the glass and in the living room. Prefixes `ez_style_01`…`04`. Shots are independent T2I (same seed); they do not copy CURB's framing.

Turn Enhance off on IDENTITY to pin the bible.
""",
        description="Klein 4B four-still lake-house views, locked inventory",
    )

    # 8. Wan bumper loop MP4
    g = _load(WF / "wan-gif-loop-lab-example.json")
    g["id"] = "wan-bumper-loop-lab-example"
    g["revision"] = 1
    lat = _node(g, "Wan22ImageToVideoLatent")
    vals = list(lat["widgets_values"])
    if len(vals) >= 3:
        vals[2] = 49
        lat["widgets_values"] = vals
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["format"] = "video/h264-mp4"
    vhs["widgets_values"]["pingpong"] = True
    vhs["widgets_values"]["frame_rate"] = 12
    vhs["widgets_values"]["filename_prefix"] = "ez_bumper"
    vhs["widgets_values"]["save_output"] = True
    vhs["title"] = "Save video (MP4) — open node for preview"
    for n in g["nodes"]:
        if n.get("type") == "SaveImage":
            n["widgets_values"] = ["ez_bumper_frames"]
            n["title"] = "Save frames (secondary)"
    motion = (
        "Locked camera bumper loop. Soft cyclic breeze on leaves and fabric. Motion returns "
        "near the start pose for seamless ping-pong. Keep start-image identity locked. No walk, no dolly."
    )
    enh = _node(g, "EZWanPromptEnhance")
    if I2V_LOCK.lower() not in motion.lower():
        motion = f"{motion.rstrip()} {I2V_LOCK}"
    enh["widgets_values"] = [motion, True, "i2v", "looping bumper, 12 fps", "none"]
    _node(g, "CLIPTextEncode", "Motion / prompt")["widgets_values"] = [motion]
    note = f"""## wan-bumper-loop-lab-example

Short loopable MP4 bumper (Wan 5B, 49 frames @ 12 fps, ping-pong ON). Prefix `ez_bumper`.
LoadImage: a still or logo plate. Leave ping-pong on for seamless loops.

{PREVIEW_BULLET}
"""
    _set_note(g, note, "Wan 5B loopable MP4 bumper")
    polish_video_graph(g)
    _dump(WF / "wan-bumper-loop-lab-example.json", g)

    # 9. LTX ambient B-roll
    g = _load(WF / "ltx-t2v-5s-lab-example.json")
    g["id"] = "ltx-broll-ambient-lab-example"
    g["revision"] = 1
    wire_ltx_audio(g)
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = "ez_broll_video"
    polish_video_graph(g)
    prompt = LTX_BROLL
    enh = _node(g, "EZLTXPromptEnhance")
    enh["widgets_values"] = [
        prompt,
        False,
        "t2v",
        "5 seconds, 24 fps, locked camera B-roll",
        LTX_BROLL_AUDIO,
    ]
    for n in g["nodes"]:
        if n.get("type") == "CLIPTextEncode" and n.get("title") in ("Positive", "Motion / prompt"):
            n["widgets_values"] = [prompt]
    note = f"""## ltx-broll-ambient-lab-example

{LTX_CANVAS_LANDSCAPE}

Ambient B-roll AV plate (~5 s T2V). LTX-2.5 distilled. Community License — not Apache.
Locked camera, world audio muxed into MP4. Prefix `ez_broll_video`.

{PREVIEW_BULLET}
Disclose AI-generated media. No score.
"""
    _set_note(g, note, "LTX-2.5 ambient B-roll AV ~5s")
    _dump(WF / "ltx-broll-ambient-lab-example.json", g)

    board_shots = []
    for i, (prefix, camera) in enumerate(STORYBOARD):
        if i == 0:
            line = f"Canonical plate. {camera} Unmarked surfaces, empty of lettering."
        else:
            line = f"Same rooftop and wizard. {camera} Unmarked surfaces, empty of lettering."
        board_shots.append((prefix, f"{i + 1:02d}", line))
    _klein_pack(
        stem="klein-storyboard-6up-lab-example",
        size=(768, 432),
        identity=CREATOR_IDENTITY,
        inventory=ROOFTOP_INVENTORY,
        persist="view",
        shots=board_shots,
        note=f"""## klein-storyboard-6up-lab-example

Six Klein 4B storyboard frames of one rooftop from new cameras (lock=view). Prefixes `ez_board_01`…`06`. Independent T2I, same seed, locked inventory. Turn Enhance off on IDENTITY to pin the bible.
""",
        description="Klein 4B six-frame storyboard pack, new cameras",
    )


def _klein_single(
    *,
    stem: str,
    template: str,
    size: tuple[int, int],
    prefix: str,
    prompt: str,
    note: str,
    description: str,
    size_title: str | None = None,
    neg: str | None = None,
) -> None:
    src = WF / "klein-still-hero-lab-example.json" if template == "hero" else WF / "klein-still-draft-lab-example.json"
    g = _load(src)
    g["id"] = stem
    g["revision"] = 1
    latent = _node(g, "EmptyFlux2LatentImage")
    latent["widgets_values"] = [size[0], size[1], 1]
    latent["title"] = size_title or f"Size {size[0]}x{size[1]}"
    save = _node(g, "SaveImage")
    save["widgets_values"] = [prefix]
    save["title"] = "Save PNG"
    _node(g, "EZKleinPromptEnhance")["widgets_values"][0] = prompt
    _node(g, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]
    if neg is not None:
        _set_neg(g, neg)
    _set_note(g, note, description)
    g["groups"] = [
        _group(1, "MODEL", 20, 40, 430, 430, "#3f789e"),
        _group(2, "PROMPT", 460, 40, 920, 400, "#3f789e"),
        _group(3, "SETTINGS", 1420, 40, 380, 500, "#a1309b"),
        _group(4, "OUTPUT", 1820, 40, 340, 430, "#3f789e"),
    ]
    _dump(WF / f"{stem}.json", g)


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


def _klein_pack(
    *,
    stem: str,
    shots: list[tuple[str, str, str]],
    size: tuple[int, int],
    note: str,
    description: str,
    cols: int = 2,
    identity: str = CREATOR_IDENTITY,
    inventory: str = ROOFTOP_INVENTORY,
    hint: str = "YouTube 16:9 still",
    neg: str | None = None,
    persist: str = "state",
) -> None:
    """Multi-shot Klein pack.

    persist=state: shot 01 T2I, 02–N ReferenceLatent of 01 (same camera).
    persist=view: every shot independent T2I with a locked world bible (new camera).
    """
    del cols  # layout is a vertical shot stack, shared loaders
    if persist not in ("view", "state"):
        raise SystemExit(f"persist must be view or state, got {persist}")
    negative = neg if neg is not None else KLEIN_NEG_STILL
    enhance_on = persist != "view"
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
    latent_links: list[int] = []
    vae_enc_links: list[int] = []
    ref_neg_out: list[int] = []

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
            [420, 420],
            "IDENTITY",
            [identity, enhance_on, "t2i", hint, "none"],
            3,
            outputs=[out("prompt", "STRING", ident_links)],
        )
    )
    nodes.append(
        _base_node(
            5,
            "CLIPTextEncode",
            [40, 940],
            [420, 120],
            "Negative",
            [negative],
            4,
            inputs=[{"name": "clip", "type": "CLIP", "link": None}],
            outputs=[out("CONDITIONING", "CONDITIONING", neg_links)],
        )
    )
    nodes.append(
        _base_node(
            6,
            "EmptyFlux2LatentImage",
            [40, 1120],
            [280, 106],
            f"Size {size[0]}x{size[1]}",
            [size[0], size[1], 1],
            5,
            outputs=[out("LATENT", "LATENT", latent_links)],
        )
    )
    nodes.append(
        _base_node(
            7,
            "Note",
            [40, 1280],
            [420, 360],
            "Operator note",
            [note],
            6,
        )
    )
    use_ref = persist == "state"
    if use_ref:
        nodes.append(
            _base_node(
                8,
                "VAEEncode",
                [1740, 170],
                [240, 80],
                "Encode plate 01",
                [],
                7,
                inputs=[
                    {"name": "pixels", "type": "IMAGE", "link": None},
                    {"name": "vae", "type": "VAE", "link": None},
                ],
                outputs=[out("LATENT", "LATENT", vae_enc_links)],
            )
        )
        nodes.append(
            _base_node(
                9,
                "ReferenceLatent",
                [40, 1680],
                [280, 80],
                "Negative + identity plate",
                [],
                8,
                inputs=[
                    {"name": "conditioning", "type": "CONDITIONING", "link": None},
                    {"name": "latent", "type": "LATENT", "link": None, "shape": 7},
                ],
                outputs=[out("CONDITIONING", "CONDITIONING", ref_neg_out)],
            )
        )

    lid = add_link(2, 0, 5, 0, "CLIP")
    nodes[4]["inputs"][0]["link"] = lid
    clip_links.append(lid)
    if use_ref:
        by_shared = {n["id"]: n for n in nodes}
        lid = add_link(3, 0, 8, 1, "VAE")
        by_shared[8]["inputs"][1]["link"] = lid
        vae_links.append(lid)
        lid = add_link(5, 0, 9, 0, "CONDITIONING")
        by_shared[9]["inputs"][0]["link"] = lid
        neg_links.append(lid)
        lid = add_link(8, 0, 9, 1, "LATENT")
        by_shared[9]["inputs"][1]["link"] = lid
        vae_enc_links.append(lid)

    row_h = 380
    shot_y0 = 80
    for i, (prefix, title, shot) in enumerate(shots):
        y = shot_y0 + i * row_h
        join_id = 10 + i * 6
        clip_id = 11 + i * 6
        ks_id = 12 + i * 6
        dec_id = 13 + i * 6
        save_id = 14 + i * 6
        n = 20 + i * 6
        joined = join_prompt(identity, shot, inventory, persist)
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
                f"SHOT {title}",
                [shot, inventory, persist],
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
                f"Positive {title}",
                [joined],
                n + 1,
                inputs=[
                    {"name": "clip", "type": "CLIP", "link": None},
                    {"name": "text", "type": "STRING", "link": None, "widget": {"name": "text"}},
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
                f"Sampler {title}",
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
                f"Decode {title}",
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
                f"Save {title}",
                [prefix],
                n + 4,
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
        if use_ref and i > 0:
            ref_id = 15 + i * 6
            ref_out: list[int] = []
            nodes.append(
                _base_node(
                    ref_id,
                    "ReferenceLatent",
                    [980, y + 200],
                    [240, 80],
                    f"Ref from 01 ({title})",
                    [],
                    n + 5,
                    inputs=[
                        {"name": "conditioning", "type": "CONDITIONING", "link": None},
                        {"name": "latent", "type": "LATENT", "link": None, "shape": 7},
                    ],
                    outputs=[out("CONDITIONING", "CONDITIONING", ref_out)],
                )
            )
            by_id = {node["id"]: node for node in nodes}
            lid = add_link(clip_id, 0, ref_id, 0, "CONDITIONING")
            by_id[ref_id]["inputs"][0]["link"] = lid
            clip_out.append(lid)
            lid = add_link(8, 0, ref_id, 1, "LATENT")
            by_id[ref_id]["inputs"][1]["link"] = lid
            vae_enc_links.append(lid)
            lid = add_link(ref_id, 0, ks_id, 1, "CONDITIONING")
            by_id[ks_id]["inputs"][1]["link"] = lid
            ref_out.append(lid)
            lid = add_link(9, 0, ks_id, 2, "CONDITIONING")
            by_id[ks_id]["inputs"][2]["link"] = lid
            ref_neg_out.append(lid)
        else:
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
        if use_ref and i == 0:
            lid = add_link(dec_id, 0, 8, 0, "IMAGE")
            by_id[8]["inputs"][0]["link"] = lid
            dec_out.append(lid)

    groups = [
        _group(1, "MODEL", 20, 40, 430, 430, "#3f789e"),
        _group(2, "IDENTITY", 20, 450, 460, 500, "#a1309b"),
    ]
    for i, (_prefix, title, _shot) in enumerate(shots):
        y = shot_y0 + i * row_h
        groups.append(_group(10 + i, f"SHOT {title}", 500, y - 20, 1840, 360, "#3f789e"))
    g = {
        "id": stem,
        "revision": 1,
        "last_node_id": max(n["id"] for n in nodes),
        "last_link_id": max(link[0] for link in links),
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": stem,
            "lab_note": note,
            "lab_description": description,
        },
        "version": 0.4,
    }
    _dump(WF / f"{stem}.json", g)


def _wan_i2v(
    *,
    stem: str,
    prefix: str,
    motion: str,
    note: str,
    description: str,
    size: tuple[int, int] = (832, 480),
    length: int = 121,
) -> None:
    g = _load(WF / "wan-i2v-5s-lab-example.json")
    g["id"] = stem
    g["revision"] = 1
    lat = _node(g, "Wan22ImageToVideoLatent")
    vals = list(lat["widgets_values"])
    vals[0], vals[1], vals[2] = size[0], size[1], length
    lat["widgets_values"] = vals
    lat["title"] = f"I2V size {size[0]}x{size[1]} x {length}"
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = prefix
    polish_video_graph(g)
    if I2V_LOCK.lower() not in motion.lower():
        motion = f"{motion.rstrip()} {I2V_LOCK}"
    _node(g, "EZWanPromptEnhance")["widgets_values"] = [motion, True, "i2v", "5 seconds, 24 fps", "none"]
    _node(g, "CLIPTextEncode", "Motion / prompt")["widgets_values"] = [motion]
    _set_note(g, note, description)
    _dump(WF / f"{stem}.json", g)


def _wan_loop(
    *,
    stem: str,
    prefix: str,
    motion: str,
    note: str,
    description: str,
) -> None:
    g = _load(WF / "wan-gif-loop-lab-example.json")
    g["id"] = stem
    g["revision"] = 1
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["format"] = "video/h264-mp4"
    vhs["widgets_values"]["pingpong"] = True
    vhs["widgets_values"]["frame_rate"] = 12
    vhs["widgets_values"]["filename_prefix"] = prefix
    vhs["widgets_values"]["save_output"] = True
    polish_video_graph(g)
    for n in g["nodes"]:
        if n.get("type") == "SaveImage":
            n["widgets_values"] = [f"{prefix}_frames"]
            n["title"] = "Save frames (secondary)"
    if I2V_LOCK.lower() not in motion.lower():
        motion = f"{motion.rstrip()} {I2V_LOCK}"
    _node(g, "EZWanPromptEnhance")["widgets_values"] = [motion, True, "i2v", "looping sticker, 12 fps", "none"]
    _node(g, "CLIPTextEncode", "Motion / prompt")["widgets_values"] = [motion]
    _set_note(g, note, description)
    _dump(WF / f"{stem}.json", g)


def _ltx_av(
    *,
    stem: str,
    prefix: str,
    prompt: str,
    note: str,
    description: str,
    mode: str,
    audio_hint: str,
) -> None:
    src = WF / "ltx-i2v-5s-lab-example.json" if mode == "i2v" else WF / "ltx-t2v-5s-lab-example.json"
    g = _load(src)
    g["id"] = stem
    g["revision"] = 1
    wire_ltx_audio(g)
    vhs = _node(g, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = prefix
    polish_video_graph(g)
    enh = _node(g, "EZLTXPromptEnhance")
    if mode == "i2v" and I2V_LOCK.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {I2V_LOCK}"
    enh["widgets_values"] = [prompt, True, mode, "5 seconds, 24 fps", audio_hint, "none"]
    for n in g["nodes"]:
        if n.get("type") == "CLIPTextEncode" and n.get("title") in (
            "Positive",
            "Motion / prompt",
            "Motion + audio",
        ):
            n["widgets_values"] = [prompt]
    _set_note(g, note, description)
    _dump(WF / f"{stem}.json", g)


def build_creator_toolkit_v2() -> None:
    identity = CREATOR_IDENTITY

    _klein_single(
        stem="klein-endcard-cta-lab-example",
        template="hero",
        size=(1280, 720),
        prefix="ez_endcard",
        prompt=(
            f"{identity} Framed as a YouTube end-card plate: generous empty lower-right "
            "for a subscribe button later. Clean of burned-in text, logos, or UI chrome. "
            "HD 3D game-engine pre-rendered cutscene 16:9."
        ),
        note="""## klein-endcard-cta-lab-example

YouTube/end-card still (Klein 4B). Default 1280×720. Prefix `ez_endcard`.
Keep the lower-right quiet — add CTA text in your editor, not in the prompt.
""",
        description="Klein 4B end-card / CTA plate 1280x720",
        size_title="Size 16:9 end card",
    )
    _klein_single(
        stem="klein-quote-bg-lab-example",
        template="hero",
        size=(1024, 1024),
        prefix="ez_quote_bg",
        prompt=(
            f"{identity} Square 1:1. Soft bokeh, quiet center so overlay text can sit later. "
            "Empty of lettering. HD 3D game-engine pre-rendered cutscene quote-card background."
        ),
        note="""## klein-quote-bg-lab-example

Quote-card background (Klein 4B). Default 1024×1024. Prefix `ez_quote_bg`.
Keep the center empty of detail; add the quote in your editor.
""",
        description="Klein 4B quote-card background 1:1",
        size_title="Size 1:1 quote background",
    )
    _klein_single(
        stem="klein-og-blog-lab-example",
        template="hero",
        size=(1216, 640),
        prefix="ez_og",
        prompt=(
            f"{identity} Wide blog / Open Graph hero. Subject left-weighted, quiet right third "
            "for a headline later. Clean of burned-in text. HD 3D game-engine pre-rendered cutscene ~1.9:1."
        ),
        note="""## klein-og-blog-lab-example

Blog / Open Graph hero (Klein 4B). Default 1216×640. Prefix `ez_og`.
Leave space for a title overlay. No burned-in words.
""",
        description="Klein 4B blog / OG hero ~1.9:1",
        size_title="Size OG / blog hero",
    )
    _klein_single(
        stem="klein-podcast-cover-lab-example",
        template="hero",
        size=(1024, 1024),
        prefix="ez_podcast",
        prompt=(
            "A photoreal square podcast-cover still. A ceramic mug and a simple analog recorder "
            "sit on a wooden table in warm sidelight. Unmarked, empty of logos and lettering. 1:1."
        ),
        note="""## klein-podcast-cover-lab-example

Podcast / playlist cover (Klein 4B). Default 1024×1024. Prefix `ez_podcast`.
Swap the props in the prompt. Add show title in your editor.
""",
        description="Klein 4B podcast cover 1:1",
        size_title="Size 1:1 podcast cover",
        neg=KLEIN_NEG_PHOTO,
    )
    _klein_single(
        stem="klein-banner-wide-lab-example",
        template="hero",
        size=(1536, 512),
        prefix="ez_banner",
        prompt=(
            f"{identity} Ultra-wide channel / LinkedIn banner. Horizon low, empty sky band "
            "for a name overlay. Empty of lettering. HD 3D game-engine pre-rendered cutscene ~3:1."
        ),
        note="""## klein-banner-wide-lab-example

Channel / LinkedIn banner (Klein 4B). Default 1536×512. Prefix `ez_banner`.
Keep the upper band simple for a name overlay.
""",
        description="Klein 4B wide banner ~3:1",
        size_title="Size wide banner 3:1",
    )
    _klein_single(
        stem="klein-ig-square-lab-example",
        template="hero",
        size=(1024, 1024),
        prefix="ez_ig_square",
        prompt=(
            f"{identity} Instagram 1:1 square. Subject centered, warm key, unmarked surfaces."
        ),
        note="""## klein-ig-square-lab-example

Generic Instagram 1:1 still (Klein 4B). Default 1024×1024. Prefix `ez_ig_square`.
Edit the prompt for any feed post.
""",
        description="Klein 4B Instagram 1:1 still",
        size_title="Size 1:1 Instagram",
    )
    _klein_single(
        stem="klein-hook-still-lab-example",
        template="draft",
        size=(432, 768),
        prefix="ez_hook_still",
        prompt=KLEIN_HOOK,
        note="""## klein-hook-still-lab-example

First-frame Shorts hook still (Klein 4B). Default 432×768 (9:16). Prefix `ez_hook_still`.
Feed into **wan-shorts-i2v-lab-example** or **ltx-hook-av-lab-example**.
""",
        description="Klein 4B 9:16 Shorts hook still",
        size_title="Size 9:16 hook still",
    )
    _klein_single(
        stem="klein-lower-third-bg-lab-example",
        template="hero",
        size=(1280, 720),
        prefix="ez_lowerthird",
        prompt=(
            f"{identity} 16:9 plate with a clean, empty lower fifth for a lower-third graphic. "
            "Subject sits in the upper two-thirds. Empty of lettering."
        ),
        note="""## klein-lower-third-bg-lab-example

Lower-third-safe 16:9 plate (Klein 4B). Default 1280×720. Prefix `ez_lowerthird`.
Keep the bottom band empty; composite titles later.
""",
        description="Klein 4B lower-third-safe 16:9 plate",
        size_title="Size 16:9 lower-third plate",
    )
    _klein_single(
        stem="klein-food-tabletop-lab-example",
        template="hero",
        size=(1024, 1280),
        prefix="ez_tabletop",
        prompt=(
            "A photoreal food tabletop still, Instagram 4:5. A ceramic bowl of soup and a linen "
            "napkin on oak, soft window sidelight. Unmarked crockery, no logos, no lettering."
        ),
        note="""## klein-food-tabletop-lab-example

Food / tabletop still (Klein 4B). Default 1024×1280 (4:5). Prefix `ez_tabletop`.
Swap the dish in the prompt; keep unmarked surfaces.
""",
        description="Klein 4B food tabletop 4:5",
        size_title="Size 4:5 tabletop",
        neg=KLEIN_NEG_PHOTO,
    )

    _klein_pack(
        stem="klein-lighting-trio-lab-example",
        size=(768, 432),
        identity=identity,
        inventory=ROOFTOP_INVENTORY,
        shots=[
            (
                "ez_light_01",
                "KEY",
                "Canonical plate. Hard golden key light from camera left, deep contact shadows. 24mm, YouTube 16:9.",
            ),
            (
                "ez_light_02",
                "WINDOW",
                "Same rooftop and wizard. Soft overcast skylight, gentle falloff, cool shadows. Same camera.",
            ),
            (
                "ez_light_03",
                "NIGHT LAMP",
                "Same rooftop and wizard at night under rooftop sodium and city neon. Same camera.",
            ),
        ],
        note=f"""## klein-lighting-trio-lab-example

Same subject under three lights (Klein 4B). SHOT KEY is the identity plate. Queue the whole graph; 02–03 Klein-edit from 01 (VAEEncode + ReferenceLatent). Do not bypass KEY on a cold canvas.
Prefixes `ez_light_01`…`03` (key / window / night lamp). Change only the light.

{ENHANCE_NOTE}
""",
        description="Klein 4B three-light study of one subject",
    )
    _klein_pack(
        stem="klein-time-of-day-lab-example",
        size=(768, 432),
        identity=identity,
        inventory=ROOFTOP_INVENTORY,
        shots=[
            (
                "ez_tod_01",
                "DUSK",
                "Canonical dusk plate, pink sky, city lamps just on. 24mm eye-level, YouTube 16:9.",
            ),
            (
                "ez_tod_02",
                "DAWN",
                "Same rooftop and wizard. First blue dawn, cool air, empty terrace. Same camera.",
            ),
            (
                "ez_tod_03",
                "NOON",
                "Same rooftop and wizard. Hard noon sun, short shadows. Same camera.",
            ),
            (
                "ez_tod_04",
                "NIGHT",
                "Same rooftop and wizard at night. Warm tower glow. Same camera.",
            ),
        ],
        note=f"""## klein-time-of-day-lab-example

Same place at dusk / dawn / noon / night (Klein 4B). SHOT DUSK is the identity plate. Queue the whole graph; 02–04 Klein-edit from 01. Do not bypass DUSK on a cold canvas.
Prefixes `ez_tod_01`…`04`. Change only time of day.

{ENHANCE_NOTE}
""",
        description="Klein 4B time-of-day four-still pack",
    )
    _klein_pack(
        stem="klein-camera-angles-lab-example",
        size=(768, 432),
        identity=identity,
        inventory=ROOFTOP_INVENTORY,
        persist="view",
        shots=[
            (
                "ez_angle_med",
                "MEDIUM",
                "35mm medium of the same rooftop and wizard; subject fills the middle third. YouTube 16:9.",
            ),
            (
                "ez_angle_wide",
                "WIDE",
                "24mm wide establishing of the same rooftop and wizard, lots of city and sky.",
            ),
            (
                "ez_angle_close",
                "CLOSE",
                "50mm close of the same rooftop and wizard on the data-staff, glyph rings, and coat materials.",
            ),
        ],
        note=f"""## klein-camera-angles-lab-example

Wide / medium / close of one subject (Klein 4B, lock=view). Prefixes `ez_angle_wide`, `ez_angle_med`, `ez_angle_close`. Independent T2I, same seed, locked inventory — new lens and framing, not copies of MEDIUM.

Turn Enhance off on IDENTITY to pin the bible.
""",
        description="Klein 4B wide/medium/close angle pack, new cameras",
    )
    _klein_pack(
        stem="klein-color-moods-lab-example",
        size=(768, 432),
        identity=identity,
        inventory=ROOFTOP_INVENTORY,
        shots=[
            (
                "ez_mood_01",
                "WARM",
                "Canonical plate. Warm amber grade, golden sidelight. 24mm, YouTube 16:9.",
            ),
            (
                "ez_mood_02",
                "COOL",
                "Same rooftop and wizard. Cool teal-and-steel grade, overcast. Same camera.",
            ),
            (
                "ez_mood_03",
                "MUTED",
                "Same rooftop and wizard. Muted filmic grade, desaturated copper, soft contrast. Same camera.",
            ),
            (
                "ez_mood_04",
                "HIGH KEY",
                "Same rooftop and wizard. High-key bright daylight, lifted shadows, clean whites. Same camera.",
            ),
        ],
        note=f"""## klein-color-moods-lab-example

Four color moods, shared identity (Klein 4B). SHOT WARM is the identity plate. Queue the whole graph; 02–04 Klein-edit from 01. Do not bypass WARM on a cold canvas.
Prefixes `ez_mood_01`…`04`. Change only grade / mood.

{ENHANCE_NOTE}
""",
        description="Klein 4B four-mood color pack",
    )

    _wan_i2v(
        stem="wan-orbit-i2v-lab-example",
        prefix="ez_orbit_video",
        motion=WAN_ORBIT,
        note=f"""## wan-orbit-i2v-lab-example

Silent Wan 5B I2V slow orbit (~5 s). LoadImage: packshot or still (`ez_packshot_*.png`).
Prefix `ez_orbit_video`.

{PREVIEW_BULLET}
""",
        description="Wan 5B silent orbit I2V ~5s",
    )
    _wan_i2v(
        stem="wan-push-in-i2v-lab-example",
        prefix="ez_pushin_video",
        motion=(
            "Slow cinematic push-in toward the start-image subject. Keep identity locked. "
            "One continuous ~5 s take at 24 fps. No orbit, no cut."
        ),
        note=f"""## wan-push-in-i2v-lab-example

Silent Wan 5B I2V hero push-in (~5 s). LoadImage: a still or thumbnail.
Prefix `ez_pushin_video`.

{PREVIEW_BULLET}
""",
        description="Wan 5B silent push-in I2V ~5s",
    )
    _wan_i2v(
        stem="wan-parallax-i2v-lab-example",
        prefix="ez_parallax_video",
        motion=(
            "Subtle parallax from the start still. Foreground drifts a hair left, background holds. "
            "Locked framing, Ken Burns-like depth, identity locked. One continuous ~5 s take."
        ),
        note=f"""## wan-parallax-i2v-lab-example

Silent Wan 5B I2V subtle parallax (~5 s). LoadImage: a still.
Prefix `ez_parallax_video`.

{PREVIEW_BULLET}
""",
        description="Wan 5B silent parallax I2V ~5s",
    )
    _wan_loop(
        stem="wan-sticker-loop-lab-example",
        prefix="ez_sticker",
        motion=(
            "Tight looping sticker motion. A small cyclic bounce or shimmer on the subject. "
            "Ping-pong friendly. Keep start-image identity locked. No walk, no dolly."
        ),
        note=f"""## wan-sticker-loop-lab-example

Loopable sticker MP4 (Wan 5B, 49 frames @ 12 fps, ping-pong ON). Prefix `ez_sticker`.
LoadImage: a cutout-friendly still.

{PREVIEW_BULLET}
""",
        description="Wan 5B looping sticker MP4",
    )

    _ltx_av(
        stem="ltx-weather-broll-lab-example",
        prefix="ez_weather_video",
        prompt=LTX_WEATHER,
        audio_hint=LTX_WEATHER_AUDIO,
        mode="t2v",
        note=f"""## ltx-weather-broll-lab-example

{LTX_CANVAS_LANDSCAPE}

Weather B-roll AV (~5 s T2V). LTX-2.5 distilled. Community License — not Apache.
Prefix `ez_weather_video`. World audio muxed into MP4.

{PREVIEW_BULLET}
Disclose AI-generated media. No score.
""",
        description="LTX-2.5 weather B-roll AV ~5s",
    )
    _ltx_av(
        stem="ltx-interior-ambience-lab-example",
        prefix="ez_interior_video",
        prompt=(
            "Locked-camera interior B-roll. A quiet unmarked kitchen at first light. Steam from a "
            "kettle, a ceramic mug on oak. House creak, kettle hush, distant clock. No music and "
            "no score. Five seconds."
        ),
        audio_hint="kettle, house creak, no score",
        mode="t2v",
        note=f"""## ltx-interior-ambience-lab-example

{LTX_CANVAS_LANDSCAPE}

Interior room-tone AV (~5 s T2V). LTX-2.5 distilled. Community License — not Apache.
Prefix `ez_interior_video`.

{PREVIEW_BULLET}
Disclose AI-generated media. No score.
""",
        description="LTX-2.5 interior ambience AV ~5s",
    )
    _ltx_av(
        stem="ltx-hook-av-lab-example",
        prefix="ez_hook_video",
        prompt=LTX_HOOK_AV,
        audio_hint=LTX_HOOK_AUDIO,
        mode="t2v",
        note=f"""## ltx-hook-av-lab-example

{LTX_CANVAS_LANDSCAPE}

~5 s AV cold-open / hook (LTX-2.5 T2V). Community License — not Apache.
Prefix `ez_hook_video`. Pair with **klein-hook-still-lab-example** if you want I2V instead.

{PREVIEW_BULLET}
Disclose AI-generated media. No score.
""",
        description="LTX-2.5 AV hook / cold open ~5s",
    )


def main() -> None:
    patch_existing_video_graphs()
    build_all_films()
    build_creator_toolkit()
    build_creator_toolkit_v2()
    for path in sorted(WF.rglob("*-lab-example.json")):
        graph = _load(path)
        normalize_enhance_widgets(graph)
        _dump(path, graph)
    print("done")


if __name__ == "__main__":
    main()
