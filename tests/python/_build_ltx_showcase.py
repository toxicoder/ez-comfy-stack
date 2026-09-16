#!/usr/bin/env python3
"""Build LTX-2.5 showcase lab Apps (dialogue, multishot, product, FLF, A2V).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_ltx_showcase.py
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from _lab_layout import finalize_layout
from _lab_paths import apply_lab_identity, lab_dest, lab_json
from _lab_theme import (
    I2V_LOCK,
    LTX_A2V,
    LTX_A2V_AUDIO,
    LTX_DIALOGUE,
    LTX_DIALOGUE_AUDIO,
    LTX_FLF,
    LTX_FLF_AUDIO,
    LTX_MULTISHOT,
    LTX_MULTISHOT_AUDIO,
    LTX_PRODUCT_AUDIO,
    LTX_PRODUCT_HERO,
)
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]

LTX_CANVAS = (
    "LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid)."
)
PREVIEW = (
    "After Queue, click **Save video (MP4) — open node for preview** for an inline "
    "preview. File lands on the host at `${COMFY_OUTPUT_DIR}/ez_*_*.mp4` "
    "(container `/outputs`). Save frames PNG is secondary."
)
LICENSE = (
    "LTX Community License — not Apache. $10M company-revenue cap. Disclose "
    "AI-generated media; do not strip provenance; do not distill."
)
OCCUPANCY = "Occupancy: ltx — stop Wan, podcast, music, other LTX. One GB10 job."
MODELS = (
    "Models: ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors + "
    "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors (CLIP type ltxv) + "
    "ltx-2.5-video-vae-bf16.safetensors + ltx-2.5-audio-vae-bf16.safetensors."
)
PIN_OFF = (
    "Prompt enhance is **off** so authored text is encoded as written. Turn Enhance "
    "on only if you want the 4B rewriter."
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    del pad
    finalize_layout(graph)


def _dump(stem: str, graph: dict) -> None:
    apply_lab_identity(graph, stem)
    stamp_suite_graph(graph)
    finalize_layout(graph)
    dest = lab_dest(stem)
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)}")


def _node(graph: dict, ntype: str, title: str | None = None) -> dict:
    for node in graph["nodes"]:
        if node.get("type") != ntype:
            continue
        if title is None or node.get("title") == title:
            return node
    raise KeyError(f"{ntype} {title}")


def _nodes(graph: dict, ntype: str) -> list[dict]:
    return [n for n in graph["nodes"] if n.get("type") == ntype]


def _input(node: dict, name: str) -> dict:
    return next(i for i in node["inputs"] if i.get("name") == name)


def _output(node: dict, slot: int = 0) -> dict:
    return node["outputs"][slot]


def _next_ids(graph: dict) -> tuple[int, int]:
    return int(graph["last_node_id"]) + 1, int(graph["last_link_id"]) + 1


def _add_link(
    graph: dict,
    src: dict,
    src_slot: int,
    dst: dict,
    dst_slot: int,
    type_name: str,
) -> int:
    _, lid = _next_ids(graph)
    graph["last_link_id"] = lid
    out = src["outputs"][src_slot]
    links = out.get("links")
    if not isinstance(links, list):
        links = [] if links is None else [links]
    links.append(lid)
    out["links"] = links
    out["slot_index"] = src_slot
    dst["inputs"][dst_slot]["link"] = lid
    graph["links"].append([lid, src["id"], src_slot, dst["id"], dst_slot, type_name])
    return lid


def _unlink_input(graph: dict, node: dict, name: str) -> None:
    inp = _input(node, name)
    lid = inp.get("link")
    if lid is None:
        return
    lid = int(lid)
    inp["link"] = None
    for other in graph["nodes"]:
        for out in other.get("outputs") or []:
            links = out.get("links")
            if isinstance(links, list) and lid in links:
                out["links"] = [x for x in links if int(x) != lid]
                if not out["links"]:
                    out["links"] = None
    graph["links"] = [lnk for lnk in graph["links"] if int(lnk[0]) != lid]


def _remove_node(graph: dict, node: dict) -> None:
    nid = int(node["id"])
    drop: set[int] = set()
    for out in node.get("outputs") or []:
        for lid in out.get("links") or []:
            drop.add(int(lid))
    for inp in node.get("inputs") or []:
        if inp.get("link") is not None:
            drop.add(int(inp["link"]))
    for other in graph["nodes"]:
        if int(other["id"]) == nid:
            continue
        for out in other.get("outputs") or []:
            links = out.get("links")
            if isinstance(links, list):
                kept = [x for x in links if int(x) not in drop]
                out["links"] = kept or None
        for inp in other.get("inputs") or []:
            if inp.get("link") is not None and int(inp["link"]) in drop:
                inp["link"] = None
    graph["links"] = [lnk for lnk in graph["links"] if int(lnk[0]) not in drop]
    graph["nodes"] = [n for n in graph["nodes"] if int(n["id"]) != nid]


def _set_note(graph: dict, note: str, description: str) -> None:
    extra = graph.setdefault("extra", {})
    extra["lab_note"] = note
    extra["lab_description"] = description
    extra["lab_ltx_av"] = True
    extra["lab_ltx_tier"] = "balanced"
    extra["lab_profile"] = extra.get("lab_rel") or graph.get("id")
    for node in graph["nodes"]:
        if node.get("type") == "Note":
            node["widgets_values"] = [note]
            break


def _set_prompt(
    graph: dict,
    prompt: str,
    *,
    mode: str,
    audio_hint: str,
    enhance: bool = False,
) -> None:
    if mode == "i2v" and I2V_LOCK.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {I2V_LOCK}"
    enh = _node(graph, "EZLTXPromptEnhance")
    values = list(enh.get("widgets_values") or [])
    while len(values) < 6:
        values.append("none" if len(values) == 5 else "")
    values[0] = prompt
    values[1] = enhance
    values[2] = "i2v" if mode in {"i2v", "flf", "a2v"} else "t2v"
    values[3] = "5 seconds, 24 fps"
    values[4] = audio_hint
    values[5] = "none"
    enh["widgets_values"] = values
    for node in graph["nodes"]:
        if node.get("type") == "CLIPTextEncode" and node.get("title") in {
            "Positive",
            "Motion / prompt",
            "Motion + audio",
        }:
            node["widgets_values"] = [prompt]


def _set_prefix(graph: dict, prefix: str) -> None:
    vhs = _node(graph, "VHS_VideoCombine")
    vhs["widgets_values"]["filename_prefix"] = prefix
    vhs["widgets_values"]["save_output"] = True
    vhs["title"] = "Save video (MP4) — open node for preview"
    for node in graph["nodes"]:
        if node.get("type") == "SaveImage":
            node["widgets_values"] = [f"{prefix}_frames"]
            node["title"] = "Save frames (secondary)"


def _clone(src_stem: str, dest_stem: str) -> dict:
    graph = copy.deepcopy(_load(lab_json(src_stem)))
    apply_lab_identity(graph, dest_stem)
    graph["revision"] = int(graph.get("revision") or 1) + 1
    return graph


def _append_node(graph: dict, node: dict) -> dict:
    nid, _ = _next_ids(graph)
    node["id"] = nid
    node["order"] = max(int(n.get("order") or 0) for n in graph["nodes"]) + 1
    graph["last_node_id"] = nid
    graph["nodes"].append(node)
    return node


def _insert_modality(graph: dict) -> None:
    unet = _node(graph, "UNETLoader")
    sampler = _node(graph, "KSampler")
    guidance = _append_node(
        graph,
        {
            "type": "LTXVModalityGuidance",
            "pos": [40, 600],
            "size": [360, 106],
            "flags": {},
            "mode": 0,
            "inputs": [{"name": "model", "type": "MODEL", "link": None}],
            "outputs": [
                {
                    "name": "MODEL",
                    "type": "MODEL",
                    "links": None,
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "LTXVModalityGuidance"},
            "widgets_values": [3.0, 0.0, 1.0],
            "title": "LTX A/V coupling",
        },
    )
    _unlink_input(graph, sampler, "model")
    _add_link(graph, unet, 0, guidance, 0, "MODEL")
    _add_link(graph, guidance, 0, sampler, 0, "MODEL")


def _polish_t2v(graph: dict, stem: str, prefix: str, prompt: str, audio: str, note: str, desc: str) -> None:
    _set_prefix(graph, prefix)
    _set_prompt(graph, prompt, mode="t2v", audio_hint=audio, enhance=False)
    _set_note(graph, note, desc)
    _dump(stem, graph)


def build_dialogue() -> None:
    graph = _clone("ltx/t2v-5s", "ltx/dialogue-5s")
    _insert_modality(graph)
    note = f"""## ltx/dialogue-5s

{LTX_CANVAS}

{PREVIEW}

LTX-2.5 distilled **dialogue** T2V (~5 s). Joint AV speech Wan cannot mux. {LICENSE}
{MODELS}
121 frames @ 24 fps. Authored quoted line; mouths will not match. {PIN_OFF}
Modality guidance (A/V coupling, scale 3.0) is on — one extra forward pass per step.
Two-stage DFR stays in Comfy **Templates → LTX-2.5**.

{OCCUPANCY}
"""
    _polish_t2v(
        graph,
        "ltx/dialogue-5s",
        "ez_ltx_dialogue",
        LTX_DIALOGUE,
        LTX_DIALOGUE_AUDIO,
        note,
        "LTX-2.5 dialogue AV T2V, quoted speech, modality guidance",
    )


def build_multishot() -> None:
    graph = _clone("ltx/t2v-5s", "ltx/multishot-5s")
    note = f"""## ltx/multishot-5s

{LTX_CANVAS}

{PREVIEW}

LTX-2.5 distilled **native multishot** T2V (~5 s). Named cuts in one generation. {LICENSE}
{MODELS}
121 frames @ 24 fps. Prompt names a hard cut and a match cut; audio continuity is in the paragraph. {PIN_OFF}

{OCCUPANCY}
"""
    _polish_t2v(
        graph,
        "ltx/multishot-5s",
        "ez_ltx_multishot",
        LTX_MULTISHOT,
        LTX_MULTISHOT_AUDIO,
        note,
        "LTX-2.5 native multishot AV T2V with named cuts",
    )


def build_product() -> None:
    graph = _clone("ltx/i2v-5s", "ltx/product-hero")
    loader = _node(graph, "LoadImage")
    loader["title"] = "Start image"
    loader["widgets_values"] = ["example.png", "image"]
    _set_prefix(graph, "ez_ltx_product")
    _set_prompt(
        graph,
        LTX_PRODUCT_HERO,
        mode="i2v",
        audio_hint=LTX_PRODUCT_AUDIO,
        enhance=False,
    )
    note = f"""## ltx/product-hero

{LTX_CANVAS}

{PREVIEW}

LTX-2.5 distilled **product hero** I2V (~5 s). LoadImage: `ez_packshot_*.png` from **klein/product-packshot** (or any tabletop still). {LICENSE}
{MODELS}
Slow orbit + table/glass SFX. Start image owns look. {PIN_OFF}

{OCCUPANCY}
"""
    _set_note(graph, note, "LTX-2.5 product-hero I2V from a Klein packshot")
    _dump("ltx/product-hero", graph)


def _load_image(title: str, filename: str, pos: list[float]) -> dict:
    return {
        "type": "LoadImage",
        "pos": pos,
        "size": [320, 314],
        "flags": {},
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "MASK", "type": "MASK", "links": None, "slot_index": 1},
        ],
        "properties": {"Node name for S&R": "LoadImage"},
        "widgets_values": [filename, "image"],
        "title": title,
    }


def _add_guide(title: str, pos: list[float], frame_idx: int) -> dict:
    return {
        "type": "LTXVAddGuide",
        "pos": pos,
        "size": [320, 180],
        "flags": {},
        "mode": 0,
        "inputs": [
            {"name": "positive", "type": "CONDITIONING", "link": None},
            {"name": "negative", "type": "CONDITIONING", "link": None},
            {"name": "vae", "type": "VAE", "link": None},
            {"name": "latent", "type": "LATENT", "link": None},
            {"name": "image", "type": "IMAGE", "link": None},
        ],
        "outputs": [
            {"name": "positive", "type": "CONDITIONING", "links": None, "slot_index": 0},
            {"name": "negative", "type": "CONDITIONING", "links": None, "slot_index": 1},
            {"name": "latent", "type": "LATENT", "links": None, "slot_index": 2},
        ],
        "properties": {"Node name for S&R": "LTXVAddGuide"},
        "widgets_values": [frame_idx, 1.0],
        "title": title,
    }


def build_flf() -> None:
    graph = _clone("ltx/t2v-5s", "ltx/flf-5s")
    empty = _node(graph, "EmptyLTXVLatentVideo")
    pos_enc = _node(graph, "CLIPTextEncode", "Positive")
    neg_enc = _node(graph, "CLIPTextEncode", "Negative")
    cond = _node(graph, "LTXVConditioning")
    concat = _node(graph, "LTXVConcatAVLatent")
    separate = _node(graph, "LTXVSeparateAVLatent")
    decode = _node(graph, "VAEDecode")
    video_vae = _node(graph, "VAELoader", "LTX-2.5 video VAE")

    first = _append_node(graph, _load_image("First frame", "example.png", [1080, 790]))
    last = _append_node(graph, _load_image("Last frame", "example.png", [1080, 1144]))
    g0 = _append_node(graph, _add_guide("Guide first frame", [1440, 790], 0))
    g1 = _append_node(graph, _add_guide("Guide last frame", [1440, 1010], -1))
    crop = _append_node(
        graph,
        {
            "type": "LTXVCropGuides",
            "pos": [2260, 520],
            "size": [280, 86],
            "flags": {},
            "mode": 0,
            "inputs": [
                {"name": "positive", "type": "CONDITIONING", "link": None},
                {"name": "negative", "type": "CONDITIONING", "link": None},
                {"name": "latent", "type": "LATENT", "link": None},
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": None, "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": None, "slot_index": 1},
                {"name": "latent", "type": "LATENT", "links": None, "slot_index": 2},
            ],
            "properties": {"Node name for S&R": "LTXVCropGuides"},
            "widgets_values": [],
            "title": "Crop guide frames",
        },
    )

    _unlink_input(graph, cond, "positive")
    _unlink_input(graph, cond, "negative")
    _unlink_input(graph, concat, "video_latent")
    decode_in = next(i for i in decode["inputs"] if i.get("type") == "LATENT")
    _unlink_input(graph, decode, str(decode_in["name"]))

    _add_link(graph, pos_enc, 0, g0, 0, "CONDITIONING")
    _add_link(graph, neg_enc, 0, g0, 1, "CONDITIONING")
    _add_link(graph, video_vae, 0, g0, 2, "VAE")
    _add_link(graph, empty, 0, g0, 3, "LATENT")
    _add_link(graph, first, 0, g0, 4, "IMAGE")

    _add_link(graph, g0, 0, g1, 0, "CONDITIONING")
    _add_link(graph, g0, 1, g1, 1, "CONDITIONING")
    _add_link(graph, video_vae, 0, g1, 2, "VAE")
    _add_link(graph, g0, 2, g1, 3, "LATENT")
    _add_link(graph, last, 0, g1, 4, "IMAGE")

    _add_link(graph, g1, 0, cond, 0, "CONDITIONING")
    _add_link(graph, g1, 1, cond, 1, "CONDITIONING")
    _add_link(graph, g1, 2, concat, 0, "LATENT")

    _add_link(graph, cond, 0, crop, 0, "CONDITIONING")
    _add_link(graph, cond, 1, crop, 1, "CONDITIONING")
    _add_link(graph, separate, 0, crop, 2, "LATENT")
    _add_link(graph, crop, 2, decode, 0, "LATENT")

    _set_prefix(graph, "ez_ltx_flf")
    _set_prompt(graph, LTX_FLF, mode="i2v", audio_hint=LTX_FLF_AUDIO, enhance=False)
    note = f"""## ltx/flf-5s

{LTX_CANVAS}

{PREVIEW}

LTX-2.5 distilled **first-last-frame** AV (~5 s). Two Klein stills (hero 1280×704) pin start and end via `LTXVAddGuide` on the **video** latent, then audio concat. {LICENSE}
{MODELS}
Guides are cropped after sample. Load **First frame** / **Last frame** (`ez_still_hero_*.png`). Same aspect. {PIN_OFF}
Official FLF2V subgraph stays in Comfy **Templates → LTX-2.5**.

{OCCUPANCY}
"""
    _set_note(graph, note, "LTX-2.5 first-last-frame AV using core AddGuide nodes")
    _dump("ltx/flf-5s", graph)


def build_a2v() -> None:
    graph = _clone("ltx/i2v-5s", "ltx/a2v-5s")
    loader = _node(graph, "LoadImage")
    loader["title"] = "Start image"
    concat = _node(graph, "LTXVConcatAVLatent")
    vhs = _node(graph, "VHS_VideoCombine")
    audio_vae = next(
        n
        for n in graph["nodes"]
        if n.get("type") == "VAELoader" and "audio" in str(n.get("title") or "").lower()
    )
    empty_audio = _node(graph, "LTXVEmptyLatentAudio")
    decode_audio = _node(graph, "LTXVAudioVAEDecode")

    audio = _append_node(
        graph,
        {
            "type": "LoadAudio",
            "pos": [40, 600],
            "size": [320, 82],
            "flags": {},
            "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "AUDIO", "type": "AUDIO", "links": None, "slot_index": 0}
            ],
            "properties": {"Node name for S&R": "LoadAudio"},
            "widgets_values": ["ez_a2v_bed.wav"],
            "title": "Audio file",
        },
    )
    encode = _append_node(
        graph,
        {
            "type": "LTXVAudioVAEEncode",
            "pos": [40, 740],
            "size": [300, 66],
            "flags": {},
            "mode": 0,
            "inputs": [
                {"name": "audio", "type": "AUDIO", "link": None},
                {"name": "audio_vae", "type": "VAE", "link": None},
            ],
            "outputs": [
                {"name": "Latent", "type": "LATENT", "links": None, "slot_index": 0}
            ],
            "properties": {"Node name for S&R": "LTXVAudioVAEEncode"},
            "widgets_values": [],
            "title": "Encode + freeze bed",
        },
    )

    _unlink_input(graph, concat, "audio_latent")
    _unlink_input(graph, vhs, "audio")
    _remove_node(graph, decode_audio)
    _remove_node(graph, empty_audio)

    _add_link(graph, audio, 0, encode, 0, "AUDIO")
    _add_link(graph, audio_vae, 0, encode, 1, "VAE")
    _add_link(graph, encode, 0, concat, 1, "LATENT")
    _add_link(graph, audio, 0, vhs, 1, "AUDIO")

    _set_prefix(graph, "ez_ltx_a2v")
    _set_prompt(graph, LTX_A2V, mode="i2v", audio_hint=LTX_A2V_AUDIO, enhance=False)
    note = f"""## ltx/a2v-5s

{LTX_CANVAS}

{PREVIEW}

LTX-2.5 distilled **audio-to-video freeze** (~5 s). Drop a ~5 s wav/mp3 in `${{COMFY_OUTPUT_DIR}}/input` as `ez_a2v_bed.wav` (or pick it on **Audio file**). Optional start still locks look. {LICENSE}
{MODELS}
Audio VAE **encodes** the clip into the joint latent. The MP4 muxes the **original** waveform (no `LTXVAudioVAEDecode`). Residual denoise on the audio latent is possible; picture still follows the bed. Mouths will not match. Banned lip-sync OSS stays out.
Two-stage A2V with frozen tokens in both stages lives in Comfy **Templates → LTX-2.5**. {PIN_OFF}

Handoff from **klein/talking-head** or any Klein still. ACE-Step bed: stop/unload music occupancy first.

{OCCUPANCY}
"""
    _set_note(graph, note, "LTX-2.5 A2V freeze: encode bed, mux original waveform")
    _dump("ltx/a2v-5s", graph)


def patch_talking_head() -> None:
    path = lab_json("klein/talking-head.json")
    graph = _load(path)
    extra = graph.setdefault("extra", {})
    note = str(extra.get("lab_note") or "")
    if "ltx/a2v-5s" not in note:
        insert = (
            "Real single-stage freeze is **ltx/a2v-5s** (LoadAudio + encode, mux original wav). "
        )
        note = note.replace(
            "Official two-stage A2V lives in Comfy Templates → LTX-2.5.",
            insert + "Official two-stage A2V lives in Comfy Templates → LTX-2.5.",
        )
        extra["lab_note"] = note
        for node in graph["nodes"]:
            if node.get("type") == "Note":
                node["widgets_values"] = [note]
                break
    stamp_suite_graph(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def patch_handoff_stills() -> None:
    for stem in ("klein/still-hero", "klein/product-packshot"):
        path = lab_json(f"{stem}.json")
        graph = _load(path)
        stamp_suite_graph(graph)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    build_dialogue()
    build_multishot()
    build_product()
    build_flf()
    build_a2v()
    patch_talking_head()
    patch_handoff_stills()
    print("done")


if __name__ == "__main__":
    main()
