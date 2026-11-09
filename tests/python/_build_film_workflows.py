#!/usr/bin/env python3
"""Build one-click 90s film graphs: Klein identity + 18 LTX printers + stitch.

Run via tests/python/_build_creator_video_workflows.py (build_all_films).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from _lab_ids import PLATE_STEM as _PLATE_STEM
from _lab_layout import GROUP_TITLE_INSET, finalize_layout, group as _group
from _lab_paths import apply_lab_identity, lab_dest, lab_json, lab_rel_of
from _long_film_bibles import ACT_TITLES, SPECS
from _stamp_app_mode import stamp_suite_graph
from _wire_prompt_enhance import (
    _link_string,
    enable_lab_graph,
    remove_node,
    repair_negative_sources,
)

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_film.nodes import FILM_DISCLOSURE  # noqa: E402
from ez_film.shots import parse_shots_yaml  # noqa: E402

WF = ROOT / "workflows"
SHORTS = WF / "shorts"

LTX_CANVAS_LANDSCAPE = (
    "LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid)."
)
PREVIEW_BULLET = (
    "The stitched MP4 is written automatically to `${COMFY_OUTPUT_DIR}` "
    "(container `/outputs`) as a faststart H.264 master, plus an HTML sidecar. After "
    "Queue, a **Film ready** overlay offers play and download. Per-shot VHS nodes "
    "remain for inspection. Optional board: studio-ui `/watch/<slug>`."
)
KLEIN_NEG_PHOTO = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)
KLEIN_NEG_GOSEE = (
    "plastic skin, melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks, "
    "third-person figure, standing wizard, second person in frame, wearer's face, another runner ahead, "
    "full body from behind, wingsuit control bar, handlebar grip, lettering on gloves, "
    "circular vignette, decorative frame, costume chrome, staff, pole, wizard staff, carried object, "
    "game-engine cutscene, CGI render, illustration"
)
LTX_NEGATIVE = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)
LTX_NEGATIVE_GOSEE = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text, third-person follow, full body from behind, "
    "second person in frame, wearer's face, another runner ahead, "
    "standing wizard, costume change, lettering on gloves, circular vignette, "
    "decorative frame, repeating planter tiles, game-engine lighting, "
    "wooden fishing pier, wingsuit handlebar, readable captions, "
    "staff, pole, wizard staff, carried object, CGI render, illustration, cartoon shading"
)

FILMS = (
    (
        "go-see",
        "gosee",
        "film/go-see",
        "go-see.shots.yaml",
        "first-person parkour",
        (
            ("1", "Golden-hour tropical rooftops", "dead sprint", "tucked front flip", "kong + wall-run drop"),
            ("2", "Waterfront maglev / bay skybridge", "grating sprint", "cat leap", "dive into gardens"),
            ("3", "Hanging tropical gardens", "glass wall-run", "tic-tac vaults", "water curtain burst"),
            ("4", "Tropical storm causeway", "rain sprint", "precision leap", "dash vault to cliffs"),
            ("5", "Coastal jungle ridge", "ridge sprint", "slide a root arch", "climb-run to overlook"),
            ("6", "Warm-night bay overlook", "last sprint", "leap to rail", "hold + breath"),
        ),
    ),
    (
        "still-here",
        "stillhere",
        "film/still-here",
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
        "film/switchyard",
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
PLATE_ID_CEILING = 50
PLATE_STEM = _PLATE_STEM
# The plate is fed straight into the LTX print pass, which renders at a locked
# 1280x704. A size or upscale picker on the plate would only desync the two.
_LOCKED_PIXEL_NODES = frozenset({"EZImageFormat", "EZImageUpscale"})
ID_LOAD = 51
ID_MARKDOWN = 52
ID_CONCAT = 900
ID_DISCLOSURE = 901
ID_IDENTITY = 905

LONG_LABELS = {
    "tide-table": "dawn skiff",
    "night-oven": "overnight bakery",
    "glasshouse": "storm glasshouse",
    "last-lane": "night two-lane",
    "breakwater": "storm-wall walk",
}
POV_FILMS = frozenset({"go-see", "last-lane", "breakwater"})
SHOT_ID_BASE = 200
SHOT_ID_STRIDE = 20

SHOT_DX = 1560
BEAT_DY = 900
BEAT_X = 2200
BEAT_Y0 = 20


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    apply_lab_identity(graph, lab_rel_of(path))
    stamp_suite_graph(graph)
    finalize_layout(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    del pad
    finalize_layout(graph)


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
    widgets: list[Any] | dict[str, Any],
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
        f"## {film} ({label})",
        "",
        "Queue **once**. Klein identity still -> 18 x 5.00s LTX AV prints (last-frame "
        "continuity) -> **Save 90s film (MP4)**. Do not Queue a 90s denoise (121 frames "
        "= 1+8n per shot). Optional silent rehearsal: **video/silent/still-to-shot**. Optional "
        f"host stitch: `bazelisk run //scripts:run-utility -- concat-shots --film {film} --yes`.",
        "",
        "18 x 121 frames @ 24 fps (LTX 1+8n) stitch under a 90.00s cap. US-safe local pack only. No score. "
        "Play/download: overlay, `ez_*_90s.html`, or studio-ui `/watch/<slug>`.",
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


def build_film_operator_note(
    stem: str,
    film: str,
    slug: str,
    label: str,
    *,
    act: int = 0,
) -> str:
    enhance_line = (
        "Prompt enhance is **off** so the pinned identity and each baked LTX I2V "
        "paragraph are encoded as written. The identity STRING is wired into each "
        "shot enhance as context (used only if you turn Enhance on)."
    )
    klein_line = (
        "Models: LTX-2.5 distilled INT8-convrot + gemma4 CLIP ltxv + video/audio "
        "VAEs. The Klein 4B identity plate is its own app (**00-plate** in this "
        "series); Queue it first."
    )
    queue_line = (
        f"1. Queue **{stem.rsplit('/', 1)[0]}/{PLATE_STEM}** once (one Klein still), then "
        "Queue this app once: 18 x 5.00s LTX prints chain last-frame -> next start."
    )
    note = f"""## {stem}

{LTX_CANVAS_LANDSCAPE}

{PREVIEW_BULLET}

LTX print pass ({label}): 18 sequential LTX 5.00s AV prints + in-graph stitch.
{klein_line}
LTX Community License - not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

{queue_line}
2. Wall-clock is 18 sequential 5s prints (tens of minutes to a couple of hours on GB10) - expected, not a hang.
3. The MP4 is already on disk at `${{COMFY_OUTPUT_DIR}}/ez_{slug}_90s.mp4` (act graphs write `ez_{slug}_actN_90s.mp4`). A **Film ready** overlay plays it. Copy off the Spark with scp.
4. Optional single-shot iterate: **video/av/still-to-shot**. Optional silent rehearsal: **video/silent/still-to-shot**.
5. Spark-farm / host stitch fallback: `bazelisk run //scripts:run-utility -- concat-shots --film {film} --yes`

Do not Queue a 90s denoise (keep 121-frame / 1+8n widgets). US-safe local pack only. No score.
{enhance_line}
"""
    if act > 0:
        prev = (
            "Act 1 starts from the identity plate. "
            if act == 1
            else (
                f"Act {act} LoadImage should be the previous act last frame "
                f"(ez_{slug}_b{(act - 1) * 6}_s3_last_*.png). "
            )
        )
        note = (
            note
            + f"\nThis graph is **act {act}/5** of a 7.5 min film (90 x 5.00s). "
            + prev
            + f"In-graph stitch writes `ez_{slug}_act{act}_90s.mp4`. "
            + f"After all five acts: `concat-shots.sh --film {film} --yes` -> "
            + f"`ez_{slug}_450s.mp4`.\n"
        )
    return note


def _shot_origin(index: int) -> tuple[float, float]:
    beat = index // 3
    col = index % 3
    return BEAT_X + col * SHOT_DX, BEAT_Y0 + beat * BEAT_DY


def _shot_nodes(
    index: int,
    slug: str,
    prompt: str,
    prefix: str,
    seed: int,
    *,
    enhance: bool = True,
) -> list[dict]:
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
    nid_enh = base + 11
    title = f"b{(index // 3) + 1} s{(index % 3) + 1} LTX I2V"
    return [
        _mk(
            nid_enh,
            "EZLTXPromptEnhance",
            [ox, oy],
            [420, 280],
            f"{title} enhance",
            [prompt, enhance, "i2v", "5 seconds, 24 fps", "", "none"],
            [],
            [_out("prompt", "STRING", 0)],
        ),
        _mk(
            nid_pos,
            "CLIPTextEncode",
            [ox, oy + 320],
            [420, 160],
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
            "LTX Img->Video condition",
            [1280, 704, 121, 1],
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
            "Save video (MP4) - open node for preview",
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
            [ox + 820, oy + 430],
            [240, 80],
            "Last frame",
            [120, 1],
            [_inp("image", "IMAGE")],
            [_out("IMAGE", "IMAGE", 0)],
            extra_props={"cnr_id": "comfy-core"},
        ),
        _mk(
            nid_save,
            "SaveImage",
            [ox + 820, oy + 550],
            [280, 200],
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
    *,
    act: int = 0,
    shot_offset: int = 0,
) -> dict:
    parsed = parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
    identity = parsed["identity"]
    plate_prefix = f"ez_{slug}_plate"
    graph = copy.deepcopy(_load(lab_json("photos/still-draft.json")))
    graph["id"] = stem
    graph["revision"] = int(graph.get("revision", 1)) + 1
    graph["links"] = [list(link) for link in graph.get("links") or []]

    op_note = build_film_operator_note(stem, film, slug, label, act=act)
    shot_md = build_shot_map_markdown(film, label, parsed, beats)

    for node in graph["nodes"]:
        if node.get("type") == "EmptyFlux2LatentImage":
            node["widgets_values"] = [1280, 704, 1]
            node["title"] = "Latent 1280x704 batch 1"
        if node.get("type") == "KSampler":
            node["widgets_values"] = [42, "fixed", 4, 1.0, "euler", "simple", 1.0]
        if node.get("type") == "SaveImage":
            node["widgets_values"] = [plate_prefix]
            node["title"] = "Save identity plate"
        if node.get("type") == "Note":
            node["widgets_values"] = [op_note]
            node["title"] = "Operator note - one-click film"
            node["size"] = [960, 280]
        if node.get("type") == "EZKleinPromptEnhance":
            node["widgets_values"] = [
                identity,
                False,
                "t2i" if film in POV_FILMS else "identity",
                "YouTube 16:9 still",
                "none",
            ]
        if node.get("type") == "EZNegativePromptEnhance":
            node["pos"] = [480.0, 400.0]
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Positive":
            node["widgets_values"] = [identity]
        if node.get("type") == "CLIPTextEncode" and node.get("title") == "Negative":
            node["widgets_values"] = [
                KLEIN_NEG_GOSEE if film in POV_FILMS else KLEIN_NEG_PHOTO
            ]

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
        [LTX_NEGATIVE_GOSEE if film in POV_FILMS else LTX_NEGATIVE],
        [_inp("clip", "CLIP")],
        [_out("CONDITIONING", "CONDITIONING", 0)],
    )
    ltx_empty = _mk(
        ID_LTX_EMPTY_AUDIO,
        "LTXVEmptyLatentAudio",
        [40, 1820],
        [300, 130],
        "Empty LTX audio latent",
        [121, 24.0, 1],
        [_inp("audio_vae", "VAE")],
        [_out("Latent", "LATENT", 0)],
    )
    concat_inputs = [
        *(_inp(f"shot_{i:02d}", "VHS_FILENAMES") for i in range(1, 19)),
        _inp("disclosure", "STRING", widget="disclosure"),
    ]
    xfade_cs = 8 if film in POV_FILMS else 0
    concat_title = (
        f"Save act {act} (90s MP4) - play / download"
        if act > 0
        else "Save 90s film (MP4) - play / download"
    )
    concat = _mk(
        ID_CONCAT,
        "EZFilmConcat",
        [40, 2560],
        [420, 200],
        concat_title,
        [film, 90.0, xfade_cs, act],
        concat_inputs,
        [_out("path", "STRING", 0)],
    )
    disclosure = _mk(
        ID_DISCLOSURE,
        "EZFilmDisclosure",
        [500, 2560],
        [420, 120],
        "LTX AI-media disclosure (end-card)",
        [""],
        [],
        [_out("text", "STRING", 0)],
    )

    shot_rows = parsed["shots"][shot_offset : shot_offset + 18]
    if len(shot_rows) != 18:
        raise SystemExit(
            f"{film} act={act} offset={shot_offset} need 18 shots, got {len(shot_rows)}"
        )
    shot_nodes: list[dict] = []
    for index, shot in enumerate(shot_rows):
        shot_nodes.extend(
            _shot_nodes(
                index,
                slug,
                shot["ltx_i2v"],
                shot["prefix"],
                42 + shot_offset + index,
                enhance=False,
            )
        )

    graph["nodes"].extend(
        [
            markdown,
            ltx_unet,
            ltx_video_vae,
            ltx_clip,
            ltx_audio_vae,
            ltx_neg,
            ltx_empty,
            concat,
            *shot_nodes,
            disclosure,
        ]
    )

    if act >= 2:
        prev_shot = parsed["shots"][shot_offset - 1]
        start_frame = f"{prev_shot['prefix']}_last.png"
        load_title = "Load previous act last frame"
    else:
        start_frame = f"{plate_prefix}.png"
        load_title = "Load identity plate"
    load = _mk(
        ID_LOAD,
        "LoadImage",
        [1480.0, 1500.0],
        [320.0, 314.0],
        load_title,
        [start_frame, "image"],
        [],
        [
            _out("IMAGE", "IMAGE", 0),
            _out("MASK", "MASK", 1),
        ],
        extra_props={"cnr_id": "comfy-core"},
    )
    graph["nodes"].append(load)
    _add_link(graph, ltx_clip, 0, ltx_neg, "clip", "CLIP")
    _add_link(graph, ltx_audio_vae, 0, ltx_empty, "audio_vae", "VAE")

    by_id = {n["id"]: n for n in graph["nodes"]}
    prev_last: dict | None = None
    for index in range(18):
        base = SHOT_ID_BASE + index * SHOT_ID_STRIDE
        pos = by_id[base]
        i2v = by_id[base + 1]
        enh = by_id[base + 11]
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
        _add_link(graph, enh, 0, pos, "text", "STRING")
        _add_link(graph, pos, 0, i2v, "positive", "CONDITIONING")
        _add_link(graph, ltx_neg, 0, i2v, "negative", "CONDITIONING")
        _add_link(graph, ltx_video_vae, 0, i2v, "vae", "VAE")
        if index == 0:
            _add_link(graph, load, 0, i2v, "image", "IMAGE")
        else:
            assert prev_last is not None
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
    _add_link(graph, disclosure, 0, concat, "disclosure", "STRING")

    graph["last_node_id"] = max(n["id"] for n in graph["nodes"])
    groups = [
        _group(1, "1. Identity (Klein)", 20, 20, 2100, 1100, "#3f789e"),
        _group(2, "2. LTX models", 20, 1180 - GROUP_TITLE_INSET, 600, 820, "#a1309b"),
    ]
    for beat in range(6):
        groups.append(
            _group(
                3 + beat,
                f"{3 + beat}. Beat {beat + 1} (3 x 5.00s LTX)",
                BEAT_X - 20,
                BEAT_Y0 + beat * BEAT_DY - GROUP_TITLE_INSET,
                3 * SHOT_DX + 40,
                BEAT_DY,
                "#3f789e" if beat % 2 == 0 else "#a1309b",
            )
        )
    groups.append(
        _group(
            9,
            "9. Publish 90s MP4",
            20,
            2560 - GROUP_TITLE_INSET,
            1000,
            280,
            "#3f789e",
        )
    )
    graph["groups"] = groups
    graph["extra"] = {
        "lab_profile": stem,
        "lab_note": op_note,
        "lab_description": f"One-click {label}: 18 LTX 5.00s AV shots + stitch",
        "lab_film": film,
        "lab_slug": slug,
        "lab_act": act,
        "lab_ltx_av": True,
        "lab_one_click": True,
        "lab_disclosure": FILM_DISCLOSURE,
        "lab_dfr": {
            "print": "ltx",
            "note": (
                "Two-stage DFR lives in Comfy Templates -> LTX-2.5 (not vendored). "
                "YAML print: dfr selects that path. Lab printers stay 5.00s / 1280x704 / 1+8n."
            ),
        },
    }
    graph["version"] = 0.4
    return graph


def _act_beat_table(film: str, act: int) -> tuple:
    spec = SPECS[film]
    start = (act - 1) * 6
    rows = []
    for index in range(6):
        beat = spec["beats"][start + index]
        shots = beat["shots"]
        rows.append(
            (
                str(index + 1),
                beat["place"],
                shots[0][0],
                shots[1][0],
                shots[2][0],
            )
        )
    title = ACT_TITLES[film][act - 1]
    return tuple(rows), title


def build_plate_note(stem: str, film: str, slug: str, label: str, next_stem: str) -> str:
    """Operator note for the Klein identity-plate app of one film or series.

    Args:
        stem: This plate graph's lane-relative id.
        film: Film or series slug the note is written for.
        slug: Short name used in the saved-plate prefix.
        label: Human title for the film or series.
        next_stem: Lane-relative id of the print pass the operator loads next.
            It must be a graph that ships: series slugs have ``act-01`` and no
            ``feature``, one-film slugs have ``feature`` and no acts.

    Returns:
        The note markdown for the plate graph.
    """
    return f"""## {stem}

Identity plate ({label}): one Klein 4B still that every print in this series
starts from.

Models: Klein 4B distilled FP8 - 4-step, Enhance **off**, t2i mode. This app
loads no LTX model, so the Quality combo moves Klein tiers only.

1. Queue **once**. The still lands at `${{COMFY_OUTPUT_DIR}}/ez_{slug}_plate_00001_.png`.
2. Check the face, the wardrobe, and the location read before you Queue a print
   pass. Re-Queue here until the plate is right; it is 4 steps and cheap.
3. Next: **{next_stem}**. Its LoadImage reads `ez_{slug}_plate.png`, so change
   the seed here and re-Queue the plate before you re-Queue a print.
4. Optional still-only iterate: **photos/still-draft**. Optional silent
   rehearsal: **video/silent/still-to-shot**.

US-safe local pack only. Klein 4B stills are the promoted image family.
"""


PLATE_GROUP_TITLE = "1. Identity (Klein)"


def _image_producer(
    graph: dict[str, Any],
    links: dict[int, list[Any]],
    node: dict[str, Any],
    input_name: str,
) -> dict[str, Any] | None:
    """Return the node feeding ``node``'s named IMAGE input, skipping stripped pickers.

    Args:
        graph: Plate graph under construction.
        links: Link-id to link-row map for ``graph``.
        node: Consumer node whose input starts the walk.
        input_name: Input name to follow (``images`` / ``image``).

    Returns:
        The nearest upstream node that survives the picker strip, or ``None``.
    """
    entry = next(
        (item for item in node.get("inputs") or [] if item.get("name") == input_name),
        None,
    )
    if entry is None or entry.get("link") is None:
        return None
    producer = _by_id(graph, int(links[int(entry["link"])][1]))
    while producer.get("type") in _LOCKED_PIXEL_NODES:
        found = next(
            (
                item
                for item in producer.get("inputs") or []
                if item.get("name") in {"image", "images"} and item.get("link") is not None
            ),
            None,
        )
        if found is None:
            return None
        producer = _by_id(graph, int(links[int(found["link"])][1]))
    return producer


def _plate_view(graph: dict[str, Any], *, stem: str, note: str, description: str) -> dict[str, Any]:
    """Keep the Klein identity stack; the saved PNG is this app's whole output.

    Args:
        graph: Combined act graph (mutated; pass a copy).
        stem: ``_lab``-relative id this app is written under.
        note: Operator-note markdown for this app.
        description: ``extra.lab_description`` for the Apps sidebar.

    Returns:
        The graph with every LTX-side node removed.
    """
    link_rows = {int(link[0]): link for link in graph.get("links") or []}
    # Snapshot before the strip: the plate's saver hangs off EZImageUpscale, so
    # its producer has to be resolved while the picker chain is still present.
    savers = [
        node
        for node in graph["nodes"]
        if node.get("type") == "SaveImage" and int(node["id"]) < PLATE_ID_CEILING
    ]
    plate_sources = {
        int(saver["id"]): _image_producer(graph, link_rows, saver, "images")
        for saver in savers
    }
    for node in list(graph["nodes"]):
        if int(node["id"]) >= PLATE_ID_CEILING or node.get("type") in _LOCKED_PIXEL_NODES:
            remove_node(graph, int(node["id"]))
    for saver in savers:
        source = plate_sources[int(saver["id"])]
        if source is not None:
            _add_link(graph, source, 0, saver, "images", "IMAGE")
    graph["groups"] = [
        group
        for group in graph.get("groups") or []
        if group.get("title") == PLATE_GROUP_TITLE
    ]
    for node in graph["nodes"]:
        if node.get("type") == "Note":
            node["widgets_values"] = [note]
            node["title"] = "Operator note - identity plate"
    graph["id"] = stem
    graph["last_node_id"] = max(int(node["id"]) for node in graph["nodes"])
    graph["mode"] = 0
    extra = graph["extra"]
    extra["lab_rel"] = stem
    extra["lab_note"] = note
    extra["lab_description"] = description
    extra["lab_ltx_av"] = False
    extra["lab_one_click"] = False
    extra.pop("lab_dfr", None)
    finalize_layout(graph)
    enable_lab_graph(graph)
    return graph


def _shot_view(
    graph: dict[str, Any], *, stem: str, identity: str, note: str, description: str
) -> dict[str, Any]:
    """Keep the LTX print stack; the plate arrives as a PNG on disk.

    Args:
        graph: Combined act graph (mutated; pass a copy).
        stem: ``_lab``-relative id this app is written under.
        identity: Parsed identity paragraph, authored into the context source.
        note: Operator-note markdown for this app.
        description: ``extra.lab_description`` for the Apps sidebar.

    Returns:
        The graph with every Klein-side node removed.
    """
    for node in list(graph["nodes"]):
        if int(node["id"]) < PLATE_ID_CEILING and node.get("type") != "Note":
            remove_node(graph, int(node["id"]))
    context_src = _mk(
        ID_IDENTITY,
        "EZSamplePrompt",
        [40.0, 1560.0],
        [420.0, 200.0],
        "Identity context",
        ["custom", identity, stem],
        [],
        [_out("prompt", "STRING", 0)],
    )
    graph["nodes"].append(context_src)
    for node in graph["nodes"]:
        if node.get("type") == "EZLTXPromptEnhance":
            _link_string(graph, context_src, node, "context")
    graph["groups"] = [
        group
        for group in graph.get("groups") or []
        if group.get("title") != PLATE_GROUP_TITLE
    ]
    for node in graph["nodes"]:
        if node.get("type") == "Note":
            node["widgets_values"] = [note]
    graph["id"] = stem
    graph["last_node_id"] = max(int(node["id"]) for node in graph["nodes"])
    graph["mode"] = 0
    extra = graph["extra"]
    extra["lab_rel"] = stem
    extra["lab_note"] = note
    extra["lab_description"] = description
    finalize_layout(graph)
    enable_lab_graph(graph)
    repair_negative_sources(graph)
    return graph


def build_all_films() -> None:
    for film, slug, stem, yaml_name, label, beats in FILMS:
        combined = build_one_click_film(film, slug, stem, yaml_name, label, beats)
        parsed = parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
        _dump(
            lab_dest(f"{stem}/{PLATE_STEM}"),
            _plate_view(
                copy.deepcopy(combined),
                stem=f"{stem}/{PLATE_STEM}",
                note=build_plate_note(
                    f"{stem}/{PLATE_STEM}", film, slug, label, f"{stem}/feature"
                ),
                description=f"Klein identity plate for {label}",
            ),
        )
        _dump(
            lab_dest(f"{stem}/feature"),
            _shot_view(
                copy.deepcopy(combined),
                stem=f"{stem}/feature",
                identity=parsed["identity"],
                note=build_film_operator_note(f"{stem}/feature", film, slug, label),
                description="One-click 90s print pass: 18 LTX 5.00s AV shots + stitch",
            ),
        )
    for film, spec in SPECS.items():
        slug = spec["slug"]
        yaml_name = f"{film}.shots.yaml"
        parsed = parse_shots_yaml((SHORTS / yaml_name).read_text(encoding="utf-8"))
        series_label = LONG_LABELS[film]
        plate_stem = f"film/{film}/{PLATE_STEM}"
        for act in range(1, 6):
            beats, act_title = _act_beat_table(film, act)
            label = f"{series_label} - {act_title}"
            stem = f"film/{film}/act-0{act}"
            combined = build_one_click_film(
                film,
                slug,
                stem,
                yaml_name,
                label,
                beats,
                act=act,
                shot_offset=(act - 1) * 18,
            )
            _dump(
                lab_dest(stem),
                _shot_view(
                    combined,
                    stem=stem,
                    identity=parsed["identity"],
                    note=build_film_operator_note(stem, film, slug, label, act=act),
                    description=(
                        f"Act {act} print pass: 18 LTX 5.00s AV shots + stitch"
                    ),
                ),
            )
        beats, _ = _act_beat_table(film, 1)
        _dump(
            lab_dest(plate_stem),
            _plate_view(
                build_one_click_film(
                    film,
                    slug,
                    plate_stem,
                    yaml_name,
                    series_label,
                    beats,
                ),
                stem=plate_stem,
                note=build_plate_note(
                    plate_stem, film, slug, series_label, f"film/{film}/act-01"
                ),
                description=f"Klein identity plate for {series_label}",
            ),
        )


if __name__ == "__main__":
    build_all_films()
