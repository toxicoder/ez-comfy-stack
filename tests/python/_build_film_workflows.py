#!/usr/bin/env python3
"""Build one-click 90s film graphs: Klein identity + 18 LTX printers + stitch.

Run via tests/python/_build_creator_video_workflows.py (build_all_films).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from _wire_prompt_enhance import normalize_enhance_widgets

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_film.shots import parse_shots_yaml  # noqa: E402

WF = ROOT / "workflows"
SHORTS = WF / "shorts"

LTX_CANVAS_LANDSCAPE = (
    "LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid)."
)
PREVIEW_BULLET = (
    "After Queue, click **Save 90s film (MP4) — open node for preview** for an inline "
    "preview of the stitched short. File: `${COMFY_OUTPUT_DIR}/ez_*_90s.mp4` "
    "(container `/outputs`). Per-shot VHS nodes remain for inspection."
)
KLEIN_NEG_PHOTO = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
LTX_NEGATIVE = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)

FILMS = (
    (
        "go-see",
        "gosee",
        "film-go-see-90s-run-lab-example",
        "go-see.shots.yaml",
        "first-person running",
        (
            ("1", "Dawn rooftop", "run on wet tar", "next roof", "warehouse roof"),
            ("2", "Warehouse → market", "stair", "alley / awning", "out to river"),
            ("3", "River / forest", "stones", "bridge arch", "creek path"),
            ("4", "Headland", "trees thin", "boulder", "generic lighthouse"),
            ("5", "Wall / meadow", "granite steps", "dry-stone gap", "meadow"),
            ("6", "Ridge hold", "slow to rail", "look", "quiet laugh"),
        ),
    ),
    (
        "still-here",
        "stillhere",
        "film-still-here-90s-lab-example",
        "still-here.shots.yaml",
        "household morning",
        (
            ("1", "Kitchen, first light", "kettle", "pour", "mug + off-screen hum"),
            ("2", "Table", "steam", "hum closer", "doorway"),
            ("3", "Hands on mug", "wrap", "motif answers", "hold"),
            ("4", "Living room", "sun bar", "silhouette", "doorway"),
            ("5", "Doorway", "silhouette", "look + hum", "pull back"),
            ("6", "Table hold", "empty chair", "last note", "house quiet"),
        ),
    ),
    (
        "switchyard",
        "switchyard",
        "film-switchyard-90s-lab-example",
        "switchyard.shots.yaml",
        "night freight yard",
        (
            ("1", "Gravel walk", "rain walk", "puddles", "stop between cars"),
            ("2", "Between cars", "gloves on rail", "coupling clank", "look up"),
            ("3", "Ladder", "climb", "continue", "roof edge"),
            ("4", "Roof walk", "along cars", "distant horn", "look down"),
            ("5", "Drop to gravel", "splash", "window glow", "keep walking"),
            ("6", "Lamp hold", "stop", "look down the string", "quiet laugh"),
        ),
    ),
)

# Shared LTX node ids
ID_LTX_UNET = 100
ID_LTX_VIDEO_VAE = 101
ID_LTX_CLIP = 102
ID_LTX_AUDIO_VAE = 103
ID_LTX_NEG = 104
ID_LTX_EMPTY_AUDIO = 105
ID_UNLOAD = 50
ID_MARKDOWN = 12
ID_CONCAT = 900
SHOT_ID_BASE = 200
SHOT_ID_STRIDE = 20

SHOT_DX = 1560
BEAT_DY = 900
BEAT_X = 2200
BEAT_Y0 = 20


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, graph: dict) -> None:
    _assert_no_overlap(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    boxes: list[tuple[int, str, float, float, float, float]] = []
    for node in graph["nodes"]:
        x, y = node["pos"]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (node["id"], node["type"], x - pad, y - pad, x + width + pad, y + height + pad)
        )
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


def _inp(name: str, typ: str, link: int | None = None, *, shape: int | None = None, widget: str | None = None) -> dict:
    item: dict = {"name": name, "type": typ, "link": link}
    if shape is not None:
        item["shape"] = shape
    if widget is not None:
        item["widget"] = {"name": widget}
    return item


def _out(name: str, typ: str, slot: int, links: list[int] | None = None) -> dict:
    return {
        "name": name,
        "type": typ,
        "links": [] if links is None else links,
        "slot_index": slot,
    }


def _mk(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets,
    inputs: list[dict],
    outputs: list[dict],
    *,
    mode: int = 0,
    extra_props: dict | None = None,
) -> dict:
    props = {"Node name for S&R": ntype}
    if extra_props:
        props.update(extra_props)
    return {
        "id": nid,
        "type": ntype,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": nid,
        "mode": mode,
        "inputs": inputs,
        "outputs": outputs,
        "properties": props,
        "widgets_values": widgets,
        "title": title,
    }


def _add_link(graph: dict, src: dict, src_slot: int, dst: dict, dst_name: str, ltype: str) -> int:
    lid = int(graph["last_link_id"]) + 1
    graph["last_link_id"] = lid
    dst_inp = next(i for i in dst["inputs"] if i["name"] == dst_name)
    dst_slot = dst["inputs"].index(dst_inp)
    dst_inp["link"] = lid
    out = src["outputs"][src_slot]
    links = out.get("links")
    if not isinstance(links, list):
        links = []
    links.append(lid)
    out["links"] = links
    graph["links"].append([lid, src["id"], src_slot, dst["id"], dst_slot, ltype])
    return lid


def _by_id(graph: dict, nid: int) -> dict:
    return next(n for n in graph["nodes"] if n["id"] == nid)


def build_shot_map_markdown(film: str, label: str, parsed: dict, beats: tuple) -> str:
    lines = [
        f"## {film} 90s ({label})",
        "",
        "Queue **once**. Klein identity still → 18 × 5.00s LTX AV prints (last-frame "
        "continuity) → **Save 90s film (MP4)**. Do not Queue a 90s denoise (120 frames "
        "per shot). Optional silent rehearsal: **wan-i2v-shot-lab-example**. Optional "
        f"host stitch: `./scripts/utilities/concat-shots.sh --film {film} --yes`.",
        "",
        "18 × 120 frames @ 24 fps = 90.00s. US-safe local pack only. No score.",
        "",
        f"**Identity look:** {parsed['identity']}",
        "",
        "| Beat | Place | s1 | s2 | s3 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for beat, place, s1, s2, s3 in beats:
        lines.append(f"| {beat} | {place} | {s1} | {s2} | {s3} |")
    lines.append("")
    return "\n".join(lines)


def build_film_operator_note(stem: str, film: str, slug: str, label: str) -> str:
    return f"""## {stem}

{LTX_CANVAS_LANDSCAPE}

{PREVIEW_BULLET}

One-click 90s film ({label}): Klein identity still + 18 sequential LTX 5.00s AV prints + in-graph stitch.
Models: Klein 4B distilled FP8 (identity, 4-step, Enhance **off**) · LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio VAEs (print).
LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

1. Queue **once**. Klein runs first; models unload; then 18 × 5.00s LTX prints chain last-frame → next start.
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) — expected, not a hang.
3. Open **Save 90s film (MP4) — open node for preview**. File: `${{COMFY_OUTPUT_DIR}}/ez_{slug}_90s.mp4`.
4. Optional single-shot iterate: **ltx-i2v-shot-lab-example**. Optional silent rehearsal: **wan-i2v-shot-lab-example**.
5. Spark-farm / host stitch fallback: `./scripts/utilities/concat-shots.sh --film {film} --yes`

Do not Queue a 90s denoise (keep 120-frame widgets). US-safe local pack only. No score.
Canned Klein / LTX prompts are model-native; leave Enhance **off** to pin them.
"""


def _shot_origin(index: int) -> tuple[float, float]:
    beat = index // 3
    col = index % 3
    return BEAT_X + col * SHOT_DX, BEAT_Y0 + beat * BEAT_DY


def _shot_nodes(index: int, slug: str, prompt: str, prefix: str, seed: int) -> list[dict]:
    ox, oy = _shot_origin(index)
    base = SHOT_ID_BASE + index * SHOT_ID_STRIDE
    nid_pos = base
    nid_i2v = base + 1
    nid_cond = base + 2
    nid_cat = base + 3
    nid_ks = base + 4
    nid_sep = base + 5
    nid_vdec = base + 6
    nid_adec = base + 7
    nid_vhs = base + 8
    nid_batch = base + 9
    nid_save = base + 10
    title = f"b{(index // 3) + 1} s{(index % 3) + 1} LTX I2V"
    return [
        _mk(
            nid_pos,
            "CLIPTextEncode",
            [ox, oy],
            [420, 180],
            title,
            [prompt],
            [_inp("clip", "CLIP"), _inp("text", "STRING", widget="text")],
            [_out("CONDITIONING", "CONDITIONING", 0)],
        ),
        _mk(
            nid_i2v,
            "LTXVImgToVideo",
            [ox + 460, oy],
            [320, 200],
            "LTX Img→Video condition",
            [1280, 704, 120, 1],
            [
                _inp("positive", "CONDITIONING"),
                _inp("negative", "CONDITIONING"),
                _inp("vae", "VAE"),
                _inp("image", "IMAGE"),
            ],
            [
                _out("positive", "CONDITIONING", 0),
                _out("negative", "CONDITIONING", 1),
                _out("latent", "LATENT", 2),
            ],
        ),
        _mk(
            nid_cond,
            "LTXVConditioning",
            [ox + 460, oy + 240],
            [280, 82],
            "LTX frame rate cond",
            [24.0],
            [_inp("positive", "CONDITIONING"), _inp("negative", "CONDITIONING")],
            [_out("positive", "CONDITIONING", 0), _out("negative", "CONDITIONING", 1)],
        ),
        _mk(
            nid_cat,
            "LTXVConcatAVLatent",
            [ox + 460, oy + 362],
            [280, 66],
            "Concat AV latents",
            [],
            [_inp("video_latent", "LATENT"), _inp("audio_latent", "LATENT")],
            [_out("latent", "LATENT", 0)],
        ),
        _mk(
            nid_ks,
            "KSampler",
            [ox + 820, oy],
            [320, 262],
            "KSampler",
            [seed, "fixed", 20, 1.0, "euler", "simple", 1.0],
            [
                _inp("model", "MODEL"),
                _inp("positive", "CONDITIONING"),
                _inp("negative", "CONDITIONING"),
                _inp("latent_image", "LATENT"),
            ],
            [_out("LATENT", "LATENT", 0)],
        ),
        _mk(
            nid_sep,
            "LTXVSeparateAVLatent",
            [ox + 820, oy + 302],
            [280, 66],
            "Separate AV latents",
            [],
            [_inp("av_latent", "LATENT")],
            [_out("video_latent", "LATENT", 0), _out("audio_latent", "LATENT", 1)],
        ),
        _mk(
            nid_vdec,
            "VAEDecode",
            [ox + 1180, oy],
            [240, 46],
            "VAE Decode",
            [],
            [_inp("samples", "LATENT"), _inp("vae", "VAE")],
            [_out("IMAGE", "IMAGE", 0)],
        ),
        _mk(
            nid_adec,
            "LTXVAudioVAEDecode",
            [ox + 1180, oy + 86],
            [320, 66],
            "Audio VAE Decode",
            [],
            [_inp("samples", "LATENT"), _inp("audio_vae", "VAE")],
            [_out("Audio", "AUDIO", 0)],
        ),
        _mk(
            nid_vhs,
            "VHS_VideoCombine",
            [ox + 1180, oy + 192],
            [320, 420],
            "Save video (MP4) — open node for preview",
            {
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": f"{prefix}_ltx_video",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 18,
                "save_metadata": True,
                "trim_to_audio": False,
                "pingpong": False,
                "save_output": True,
            },
            [
                _inp("images", "IMAGE"),
                _inp("audio", "AUDIO", shape=7),
                _inp("meta_batch", "VHS_BatchManager", shape=7),
                _inp("vae", "VAE", shape=7),
            ],
            [_out("Filenames", "VHS_FILENAMES", 0, None)],
        ),
        _mk(
            nid_batch,
            "ImageFromBatch",
            [ox, oy + 220],
            [240, 80],
            "Last frame",
            [119, 1],
            [_inp("image", "IMAGE")],
            [_out("IMAGE", "IMAGE", 0)],
            extra_props={"cnr_id": "comfy-core"},
        ),
        _mk(
            nid_save,
            "SaveImage",
            [ox, oy + 340],
            [280, 270],
            "Save last frame",
            [f"{prefix}_last"],
            [_inp("images", "IMAGE")],
            [],
        ),
    ]


def build_one_click_film(
    film: str,
    slug: str,
    stem: str,
    yaml_name: str,
    label: str,
    beats: tuple,
) -> dict:
    parsed = parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
    identity = parsed["identity"]
    graph = copy.deepcopy(_load(WF / "klein-still-draft-lab-example.json"))
    graph["id"] = stem
    graph["revision"] = int(graph.get("revision", 1)) + 1
    graph["links"] = [list(link) for link in graph.get("links") or []]

    op_note = build_film_operator_note(stem, film, slug, label)
    shot_md = build_shot_map_markdown(film, label, parsed, beats)

    for node in graph["nodes"]:
        if node.get("type") == "EmptyFlux2LatentImage":
            node["widgets_values"] = [1280, 720, 1]
            node["title"] = "Latent 1280x720 batch 1"
        if node.get("type") == "KSampler":
            node["widgets_values"] = [42, "fixed", 4, 1.0, "euler", "simple", 1.0]
        if node.get("type") == "SaveImage":
            node["widgets_values"] = [f"ez_{slug}_identity"]
            node["title"] = "Save identity PNG"
        if node.get("type") == "Note":
            node["widgets_values"] = [op_note]
            node["title"] = "Operator note — one-click 90s film"
            node["size"] = [960, 280]
        if node.get("type") == "EZKleinPromptEnhance":
            node["widgets_values"] = [identity, False, "t2i", "YouTube 16:9 still", "none"]
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Positive":
            node["widgets_values"] = [identity]
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative":
            node["widgets_values"] = [KLEIN_NEG_PHOTO]

    markdown = _mk(
        ID_MARKDOWN,
        "MarkdownNote",
        [40, 2000],
        [960, 520],
        f"{film} 90s shot map",
        [shot_md],
        [],
        [],
    )
    unload = _mk(
        ID_UNLOAD,
        "EZUnloadModels",
        [1840, 500],
        [320, 80],
        "Unload models (pass IMAGE)",
        [],
        [_inp("image", "IMAGE")],
        [_out("image", "IMAGE", 0)],
    )
    ltx_unet = _mk(
        ID_LTX_UNET,
        "UNETLoader",
        [40, 1180],
        [520, 82],
        "LTX-2.5 distilled INT8-convrot",
        ["ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "default"],
        [],
        [_out("MODEL", "MODEL", 0)],
    )
    ltx_video_vae = _mk(
        ID_LTX_VIDEO_VAE,
        "VAELoader",
        [40, 1310],
        [360, 58],
        "LTX-2.5 video VAE",
        ["ltx-2.5-video-vae-bf16.safetensors"],
        [],
        [_out("VAE", "VAE", 0)],
    )
    ltx_clip = _mk(
        ID_LTX_CLIP,
        "CLIPLoader",
        [40, 1410],
        [520, 110],
        "Gemma4-with-proj (ltxv)",
        ["gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "ltxv", "default"],
        [],
        [_out("CLIP", "CLIP", 0)],
    )
    ltx_audio_vae = _mk(
        ID_LTX_AUDIO_VAE,
        "VAELoader",
        [40, 1560],
        [360, 58],
        "LTX-2.5 audio VAE",
        ["ltx-2.5-audio-vae-bf16.safetensors"],
        [],
        [_out("VAE", "VAE", 0)],
    )
    ltx_neg = _mk(
        ID_LTX_NEG,
        "CLIPTextEncode",
        [40, 1660],
        [420, 120],
        "Negative",
        [LTX_NEGATIVE],
        [_inp("clip", "CLIP")],
        [_out("CONDITIONING", "CONDITIONING", 0)],
    )
    ltx_empty = _mk(
        ID_LTX_EMPTY_AUDIO,
        "LTXVEmptyLatentAudio",
        [40, 1820],
        [300, 130],
        "Empty LTX audio latent",
        [120, 24.0, 1],
        [_inp("audio_vae", "VAE")],
        [_out("Latent", "LATENT", 0)],
    )
    concat_inputs = [
        _inp(f"shot_{i:02d}", "VHS_FILENAMES") for i in range(1, 19)
    ]
    concat = _mk(
        ID_CONCAT,
        "EZFilmConcat",
        [BEAT_X, BEAT_Y0 + 6 * BEAT_DY + 40],
        [420, 140],
        "Save 90s film (MP4) — open node for preview",
        [film, 90.0],
        concat_inputs,
        [_out("path", "STRING", 0)],
    )

    shot_nodes: list[dict] = []
    for index, shot in enumerate(parsed["shots"]):
        shot_nodes.extend(
            _shot_nodes(index, slug, shot["ltx_i2v"], shot["prefix"], 42 + index)
        )

    graph["nodes"].extend(
        [
            markdown,
            unload,
            ltx_unet,
            ltx_video_vae,
            ltx_clip,
            ltx_audio_vae,
            ltx_neg,
            ltx_empty,
            concat,
            *shot_nodes,
        ]
    )

    klein_decode = _by_id(graph, 8)
    _add_link(graph, klein_decode, 0, unload, "image", "IMAGE")
    _add_link(graph, ltx_clip, 0, ltx_neg, "clip", "CLIP")
    _add_link(graph, ltx_audio_vae, 0, ltx_empty, "audio_vae", "VAE")

    by_id = {n["id"]: n for n in graph["nodes"]}
    prev_last = None
    for index in range(18):
        base = SHOT_ID_BASE + index * SHOT_ID_STRIDE
        pos = by_id[base]
        i2v = by_id[base + 1]
        cond = by_id[base + 2]
        cat = by_id[base + 3]
        ks = by_id[base + 4]
        sep = by_id[base + 5]
        vdec = by_id[base + 6]
        adec = by_id[base + 7]
        vhs = by_id[base + 8]
        batch = by_id[base + 9]
        save = by_id[base + 10]
        _add_link(graph, ltx_clip, 0, pos, "clip", "CLIP")
        _add_link(graph, pos, 0, i2v, "positive", "CONDITIONING")
        _add_link(graph, ltx_neg, 0, i2v, "negative", "CONDITIONING")
        _add_link(graph, ltx_video_vae, 0, i2v, "vae", "VAE")
        if index == 0:
            _add_link(graph, unload, 0, i2v, "image", "IMAGE")
        else:
            _add_link(graph, prev_last, 0, i2v, "image", "IMAGE")
        _add_link(graph, i2v, 0, cond, "positive", "CONDITIONING")
        _add_link(graph, i2v, 1, cond, "negative", "CONDITIONING")
        _add_link(graph, i2v, 2, cat, "video_latent", "LATENT")
        _add_link(graph, ltx_empty, 0, cat, "audio_latent", "LATENT")
        _add_link(graph, ltx_unet, 0, ks, "model", "MODEL")
        _add_link(graph, cond, 0, ks, "positive", "CONDITIONING")
        _add_link(graph, cond, 1, ks, "negative", "CONDITIONING")
        _add_link(graph, cat, 0, ks, "latent_image", "LATENT")
        _add_link(graph, ks, 0, sep, "av_latent", "LATENT")
        _add_link(graph, sep, 0, vdec, "samples", "LATENT")
        _add_link(graph, ltx_video_vae, 0, vdec, "vae", "VAE")
        _add_link(graph, sep, 1, adec, "samples", "LATENT")
        _add_link(graph, ltx_audio_vae, 0, adec, "audio_vae", "VAE")
        _add_link(graph, vdec, 0, vhs, "images", "IMAGE")
        _add_link(graph, adec, 0, vhs, "audio", "AUDIO")
        _add_link(graph, vdec, 0, batch, "image", "IMAGE")
        _add_link(graph, batch, 0, save, "images", "IMAGE")
        _add_link(graph, vhs, 0, concat, f"shot_{index + 1:02d}", "VHS_FILENAMES")
        prev_last = batch

    graph["last_node_id"] = max(n["id"] for n in graph["nodes"])
    groups = [
        _group(1, "1. Identity (Klein)", 20, 20, 2100, 1100, "#3f789e"),
        _group(2, "2. LTX models", 20, 1140, 600, 820, "#a1309b"),
    ]
    for beat in range(6):
        groups.append(
            _group(
                3 + beat,
                f"{3 + beat}. Beat {beat + 1} (3 × 5.00s LTX)",
                BEAT_X - 20,
                BEAT_Y0 + beat * BEAT_DY - 20,
                3 * SHOT_DX + 40,
                BEAT_DY,
                "#3f789e" if beat % 2 == 0 else "#a1309b",
            )
        )
    groups.append(
        _group(
            9,
            "9. Publish 90s MP4",
            BEAT_X - 20,
            BEAT_Y0 + 6 * BEAT_DY,
            2000,
            280,
            "#3f789e",
        )
    )
    graph["groups"] = groups
    graph["extra"] = {
        "lab_profile": stem,
        "lab_note": op_note,
        "lab_description": f"One-click 90s {label}: Klein identity + 18 LTX 5.00s AV shots + stitch",
        "lab_film": film,
        "lab_slug": slug,
        "lab_ltx_av": True,
        "lab_one_click": True,
    }
    graph["version"] = 0.4
    normalize_enhance_widgets(graph)
    return graph


def build_all_films() -> None:
    for film, slug, stem, yaml_name, label, beats in FILMS:
        graph = build_one_click_film(film, slug, stem, yaml_name, label, beats)
        _dump(SHORTS / f"{stem}.json", graph)


if __name__ == "__main__":
    build_all_films()
