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

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
SHORTS = WF / "shorts"

PREVIEW_BULLET = (
    "After Queue, click **Save video (MP4) — open node for preview** for an inline "
    "preview. File lands on the host at `${COMFY_OUTPUT_DIR}/ez_*_*.mp4` "
    "(container `/outputs`). Save frames PNG is secondary."
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
        n["widgets_values"][0] = _ensure_preview_line(text, gif=gif)

    extra = graph.setdefault("extra", {})
    if isinstance(extra.get("lab_note"), str):
        extra["lab_note"] = _ensure_preview_line(extra["lab_note"], gif=gif)
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
Prompt enhance: leave Enhance off for canned prompts. Set Enhance true and XAI_API_KEY to rewrite a lazy sentence.
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
    prompt = (
        "A photoreal vertical still for Shorts. A red bicycle leans against a brick "
        "storefront at golden hour. Warm sidelight, unmarked facades, empty of signage. "
        "Shot on a 35mm lens, framed for 9:16 with headroom for captions."
    )
    enh["widgets_values"][0] = prompt
    _node(g, "CLIPTextEncode", "Positive")["widgets_values"] = [prompt]
    note = f"""## klein-shorts-still-lab-example

Vertical Shorts/Reels still (Klein 4B distilled FP8). Default **432×768** (9:16).
Save prefix: `ez_shorts_still`. Feed into **wan-shorts-i2v-lab-example** or **ltx-shorts-i2v-lab-example**.
Widgets: seed / steps / CFG / size on canvas. Prompt enhance optional (XAI_API_KEY).
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
    motion = (
        "Locked vertical framing for Shorts. Gentle breeze moves leaves and a shop flag. "
        "Camera holds, then a slow push-in. Keep the start-image identity locked. "
        "One continuous ~5 s take at 24 fps. No audio."
    )
    enh = _node(g, "EZWanPromptEnhance")
    enh["widgets_values"] = [motion, False, "i2v", "5 seconds, 24 fps, 9:16"]
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
    prompt = (
        "The start image holds as the first frame in vertical Shorts framing. Soft wind "
        "rustles a flag as distant footsteps tap the pavement and a faint shop bell clinks "
        "once. Slow push-in. No music and no score."
    )
    enh = _node(g, "EZLTXPromptEnhance")
    enh["widgets_values"] = [prompt, False, "i2v", "5 seconds, 24 fps, 9:16", "soft wind, footsteps, shop bell, no score"]
    for n in g["nodes"]:
        if n.get("type") == "CLIPTextEncode" and n.get("title") in (None, "Positive", "Motion / prompt"):
            # LTX uses enhance → CLIP; still set if present
            if n.get("title") == "Positive" or "Positive" in (n.get("title") or ""):
                n["widgets_values"] = [prompt]
    note = f"""## ltx-shorts-i2v-lab-example

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
    prompt = (
        "A bold YouTube thumbnail still, 16:9. A single red bicycle fills the frame against "
        "a brick storefront at golden hour. High contrast sidelight, clear subject separation, "
        "unmarked facades, empty of text and logos. Photoreal, eye-catching, no burned-in words."
    )
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
    note = """## klein-product-packshot-lab-example

Clean product / packshot still (Klein 4B). Default 1024×1024. Prefix `ez_packshot`.
Swap the subject in the prompt; keep seamless background and soft studio light.
"""
    _set_note(g, note, "Klein 4B product packshot 1:1")
    _dump(WF / "klein-product-packshot-lab-example.json", g)

    # 6. Before / after — two SaveImage branches from dream-house style clone of draft×2
    # Simpler: clone dream-house builder pattern with 2 shots
    g = _load(WF / "klein-still-draft-lab-example.json")
    # Build a minimal two-prompt graph by cloning draft and adding a second sampler chain
    before_prompt = (
        "A photoreal still of a small kitchen table at first light. A plain ceramic mug "
        "sits empty beside a dark window. Cool blue shadows, unmarked surfaces."
    )
    after_prompt = (
        "The same kitchen table and ceramic mug identity, now filled with coffee and lit by "
        "warm morning sun through the window. Soft steam, unmarked surfaces. Same camera."
    )
    base = _load(WF / "klein-still-draft-lab-example.json")
    # Use dream-house multi-shot approach: load dream house and strip to 2 — easier to clone draft twice via remap
    a = _load(WF / "klein-still-draft-lab-example.json")
    b = _load(WF / "klein-still-draft-lab-example.json")
    # Remove notes from B; remap B
    b_nodes = [n for n in b["nodes"] if n.get("type") != "Note"]
    b_links = [
        link
        for link in b["links"]
        if not any(n["id"] in (link[1], link[3]) and n.get("type") == "Note" for n in b["nodes"])
    ]
    # Actually filter links that reference only remaining nodes
    b_ids = {n["id"] for n in b_nodes}
    b_links = [link for link in b["links"] if link[1] in b_ids and link[3] in b_ids]
    remapped_b, remapped_links, _ = _remap_subgraph(
        b_nodes, b_links, id_offset=100, link_offset=100, pos_dx=0, pos_dy=920
    )
    # Shared models: keep A's loaders; bypass B's loaders and reconnect — too hard.
    # Simpler approach: two independent full graphs stacked (VRAM heavy but clear).
    for n in a["nodes"]:
        if n.get("type") == "SaveImage":
            n["widgets_values"] = ["ez_before"]
            n["title"] = "Save BEFORE"
        if n.get("type") == "EZKleinPromptEnhance":
            n["widgets_values"][0] = before_prompt
        if n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive":
            n["widgets_values"] = [before_prompt]
        if n.get("type") == "EmptyFlux2LatentImage":
            n["widgets_values"] = [768, 432, 1]
    for n in remapped_b:
        if n.get("type") == "SaveImage":
            n["widgets_values"] = ["ez_after"]
            n["title"] = "Save AFTER"
        if n.get("type") == "EZKleinPromptEnhance":
            n["widgets_values"][0] = after_prompt
        if n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive":
            n["widgets_values"] = [after_prompt]
        if n.get("type") == "EmptyFlux2LatentImage":
            n["widgets_values"] = [768, 432, 1]
        if n.get("type") == "Note":
            continue
    note_node = next(n for n in a["nodes"] if n.get("type") == "Note")
    note = """## klein-before-after-lab-example

Two Klein 4B stills with a shared subject identity (before / after). Prefixes `ez_before` and `ez_after`.
Edit both Positive prompts; keep the mug (or your subject) identical. Queue writes both PNGs.
"""
    note_node["widgets_values"] = [note]
    note_node["pos"] = [40, 1850]
    note_node["size"] = [960, 220]
    g = {
        "id": "klein-before-after-lab-example",
        "revision": 1,
        "last_node_id": max(n["id"] for n in a["nodes"] + remapped_b),
        "last_link_id": max(link[0] for link in (a.get("links") or []) + remapped_links),
        "nodes": [n for n in a["nodes"] if n.get("type") != "Note"] + remapped_b + [note_node],
        "links": list(a.get("links") or []) + remapped_links,
        "groups": [
            _group(1, "BEFORE", 20, 20, 2200, 850, "#3f789e"),
            _group(2, "AFTER", 20, 920, 2200, 850, "#a1309b"),
        ],
        "config": {},
        "extra": {
            "lab_profile": "klein-before-after-lab-example",
            "lab_note": note,
            "lab_description": "Klein 4B before/after still pair",
        },
        "version": 0.4,
    }
    _dump(WF / "klein-before-after-lab-example.json", g)

    # 7. Style lock — 4 variants (reuse before-after pattern with 4 clones)
    identity = (
        "Identity lock: a contemporary cedar-and-glass lake house with vertical cedar siding, "
        "charcoal standing-seam roof, tall black-framed windows, unmarked surfaces."
    )
    shots = [
        ("ez_style_01", "Golden-hour curb appeal from the gravel drive, 24mm, warm sidelight."),
        ("ez_style_02", "Living room looking through glass toward a still lake, late-day sun."),
        ("ez_style_03", "Lakeside deck at dusk, cedar boards, quiet water, evergreen ridge."),
        ("ez_style_04", "Twilight exterior with interior lamps glowing through black-framed glass."),
    ]
    nodes: list[dict] = []
    links: list[list] = []
    note_text = f"""## klein-style-lock-lab-example

Four Klein 4B stills sharing one identity lock. Prefixes `ez_style_01`…`04`.
Edit the identity once in each Positive prompt's first sentence; change only camera / time of day per card.
Identity: {identity}
"""
    for i, (prefix, camera) in enumerate(shots):
        src = _load(WF / "klein-still-draft-lab-example.json")
        src_nodes = [n for n in src["nodes"] if n.get("type") != "Note"]
        src_ids = {n["id"] for n in src_nodes}
        src_links = [link for link in src["links"] if link[1] in src_ids and link[3] in src_ids]
        rn, rl, _ = _remap_subgraph(
            src_nodes,
            src_links,
            id_offset=i * 100,
            link_offset=i * 100,
            pos_dx=(i % 2) * 2300,
            pos_dy=(i // 2) * 900,
        )
        prompt = f"A photoreal still photograph. {identity} {camera} Instagram-friendly framing. Solitary, empty of people."
        for n in rn:
            if n.get("type") == "SaveImage":
                n["widgets_values"] = [prefix]
                n["title"] = f"Save {prefix}"
            if n.get("type") == "EZKleinPromptEnhance":
                n["widgets_values"][0] = prompt
            if n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive":
                n["widgets_values"] = [prompt]
            if n.get("type") == "EmptyFlux2LatentImage":
                n["widgets_values"] = [768, 960, 1]  # 4:5-ish
        nodes.extend(rn)
        links.extend(rl)
    note_node = {
        "id": 999,
        "type": "Note",
        "pos": [40, 1850],
        "size": [960, 280],
        "flags": {},
        "order": 99,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "properties": {"Node name for S&R": "Note"},
        "widgets_values": [note_text],
        "title": "Operator note",
    }
    nodes.append(note_node)
    g = {
        "id": "klein-style-lock-lab-example",
        "revision": 1,
        "last_node_id": max(n["id"] for n in nodes),
        "last_link_id": max(link[0] for link in links),
        "nodes": nodes,
        "links": links,
        "groups": [
            _group(1, "STYLE 01", 20, 20, 2200, 850, "#3f789e"),
            _group(2, "STYLE 02", 2320, 20, 2200, 850, "#3f789e"),
            _group(3, "STYLE 03", 20, 920, 2200, 850, "#a1309b"),
            _group(4, "STYLE 04", 2320, 920, 2200, 850, "#a1309b"),
        ],
        "config": {},
        "extra": {
            "lab_profile": "klein-style-lock-lab-example",
            "lab_note": note_text,
            "lab_description": "Klein 4B four-still style-lock pack",
        },
        "version": 0.4,
    }
    _dump(WF / "klein-style-lock-lab-example.json", g)

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
    enh["widgets_values"] = [motion, False, "i2v", "looping bumper, 12 fps"]
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
    prompt = (
        "Locked-camera ambient B-roll of a quiet small-town main street at golden hour. "
        "Leaves drift, a shop flag stirs, distant footsteps and soft wind, a faint bell once. "
        "Photoreal, unmarked facades, empty of logos. No music and no score. Five seconds."
    )
    enh = _node(g, "EZLTXPromptEnhance")
    enh["widgets_values"] = [
        prompt,
        False,
        "t2v",
        "5 seconds, 24 fps, locked camera B-roll",
        "wind, footsteps, shop bell, no score",
    ]
    note = f"""## ltx-broll-ambient-lab-example

Ambient B-roll AV plate (~5 s T2V). LTX-2.5 distilled. Community License — not Apache.
Locked camera, world audio muxed into MP4. Prefix `ez_broll_video`.

{PREVIEW_BULLET}
Disclose AI-generated media. No score.
"""
    _set_note(g, note, "LTX-2.5 ambient B-roll AV ~5s")
    _dump(WF / "ltx-broll-ambient-lab-example.json", g)

    # 10. Storyboard 6-up
    board = [
        ("ez_board_01", "Wide establishing shot of a small-town main street at dawn, 24mm."),
        ("ez_board_02", "Medium shot of a red bicycle against a brick storefront, 35mm."),
        ("ez_board_03", "Detail of chrome handlebars and warm sidelight on brick, 50mm."),
        ("ez_board_04", "Street-level tracking angle as a pedestrian passes in the distance, 35mm."),
        ("ez_board_05", "Over-the-shoulder toward the unmarked shop window, golden hour."),
        ("ez_board_06", "Closing wide as lights warm in windows, quiet street, 24mm."),
    ]
    nodes = []
    links = []
    note_text = """## klein-storyboard-6up-lab-example

Six Klein 4B storyboard frames in one Queue. Prefixes `ez_board_01`…`06`.
Edit each Positive prompt for your beat sheet. Keep SFW / no unlicensed marks.
"""
    for i, (prefix, camera) in enumerate(board):
        src = _load(WF / "klein-still-draft-lab-example.json")
        src_nodes = [n for n in src["nodes"] if n.get("type") != "Note"]
        src_ids = {n["id"] for n in src_nodes}
        src_links = [link for link in src["links"] if link[1] in src_ids and link[3] in src_ids]
        rn, rl, _ = _remap_subgraph(
            src_nodes,
            src_links,
            id_offset=i * 100,
            link_offset=i * 100,
            pos_dx=(i % 3) * 2200,
            pos_dy=(i // 3) * 900,
        )
        prompt = (
            f"A photoreal storyboard still, YouTube 16:9. {camera} Unmarked facades, "
            "empty of signage. Clean cinematic frame."
        )
        for n in rn:
            if n.get("type") == "SaveImage":
                n["widgets_values"] = [prefix]
                n["title"] = f"Save {prefix}"
            if n.get("type") == "EZKleinPromptEnhance":
                n["widgets_values"][0] = prompt
            if n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive":
                n["widgets_values"] = [prompt]
            if n.get("type") == "EmptyFlux2LatentImage":
                n["widgets_values"] = [768, 432, 1]
            if n.get("type") == "KSampler":
                # slightly different seeds per board frame
                wv = list(n["widgets_values"])
                # seed is typically index 0 or 1 depending on control_after_generate
                if isinstance(wv[0], int):
                    wv[0] = 42 + i
                n["widgets_values"] = wv
        nodes.extend(rn)
        links.extend(rl)
    note_node = {
        "id": 999,
        "type": "Note",
        "pos": [40, 1850],
        "size": [960, 220],
        "flags": {},
        "order": 99,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "properties": {"Node name for S&R": "Note"},
        "widgets_values": [note_text],
        "title": "Operator note",
    }
    nodes.append(note_node)
    g = {
        "id": "klein-storyboard-6up-lab-example",
        "revision": 1,
        "last_node_id": max(n["id"] for n in nodes),
        "last_link_id": max(link[0] for link in links),
        "nodes": nodes,
        "links": links,
        "groups": [
            _group(i + 1, f"BOARD {i + 1:02d}", (i % 3) * 2200 + 20, (i // 3) * 900 + 20, 2100, 850, "#3f789e")
            for i in range(6)
        ],
        "config": {},
        "extra": {
            "lab_profile": "klein-storyboard-6up-lab-example",
            "lab_note": note_text,
            "lab_description": "Klein 4B six-frame storyboard pack",
        },
        "version": 0.4,
    }
    _dump(WF / "klein-storyboard-6up-lab-example.json", g)


def main() -> None:
    patch_existing_video_graphs()
    build_all_films()
    build_creator_toolkit()
    print("done")


if __name__ == "__main__":
    main()
