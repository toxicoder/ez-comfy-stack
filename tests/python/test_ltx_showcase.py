"""LTX-2.5 showcase App contracts (dialogue, multishot, product, FLF, A2V)."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json
from _lab_theme import (
    LTX_A2V,
    LTX_DIALOGUE,
    LTX_FLF,
    LTX_MULTISHOT,
    LTX_PRODUCT_HERO,
)
from _stamp_app_mode import linear_input_node_id

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Wav2Lip", "wav2lip")

SHOWCASE = (
    ("motion/av/dialogue-8s", "ez_ltx_dialogue", "t2v"),
    ("motion/av/multishot-8s", "ez_ltx_multishot", "t2v"),
    ("motion/av/product-hero", "ez_ltx_product", "i2v"),
    ("motion/av/first-last-8s", "ez_ltx_flf", "flf"),
    ("motion/av/audio-to-video-8s", "ez_ltx_a2v", "a2v"),
)


def _load(stem: str) -> dict:
    return json.loads(lab_json(stem).read_text(encoding="utf-8"))


def _by_type(graph: dict, ntype: str) -> list[dict]:
    return [n for n in graph["nodes"] if n.get("type") == ntype]


def _source_of(graph: dict, node: dict, name: str) -> dict | None:
    inp = next((i for i in node.get("inputs") or [] if i.get("name") == name), None)
    if inp is None or inp.get("link") is None:
        return None
    lid = int(inp["link"])
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    for link in graph.get("links") or []:
        if int(link[0]) == lid:
            return by_id.get(int(link[1]))
    return None


def _labels(graph: dict) -> list[str]:
    linear = (graph.get("extra") or {}).get("linearData") or {}
    out: list[str] = []
    for entry in linear.get("inputs") or []:
        if len(entry) >= 3 and isinstance(entry[2], dict) and entry[2].get("label"):
            out.append(str(entry[2]["label"]))
        else:
            out.append(str(entry[1]))
    return out


def _widget_names(graph: dict) -> list[str]:
    linear = (graph.get("extra") or {}).get("linearData") or {}
    return [str(entry[1]) for entry in linear.get("inputs") or []]


def test_showcase_files_prefixes_and_occupancy() -> None:
    for stem, prefix, _kind in SHOWCASE:
        path = lab_json(stem)
        assert path.is_file(), stem
        graph = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(graph)
        for needle in BANNED:
            assert needle not in blob, (stem, needle)
        extra = graph.get("extra") or {}
        assert graph.get("id") == Path(stem).name
        assert extra.get("lab_rel") == stem
        assert extra.get("lab_ltx_av") is True
        assert extra.get("lab_note", "").strip()
        assert extra.get("lab_description", "").strip()
        mode = extra.get("lab_app_mode") or {}
        assert mode.get("occupancy") == "ltx"
        assert mode.get("lane") == "produce"
        assert mode.get("default_view") == "app"
        assert prefix in blob, (stem, prefix)
        vhs = _by_type(graph, "VHS_VideoCombine")
        assert vhs, stem
        for node in vhs:
            widgets = node["widgets_values"]
            assert widgets["save_output"] is True
            assert str(widgets["filename_prefix"]).startswith("ez_")
            assert "preview" in (node.get("title") or "").lower()
        enhance = _by_type(graph, "EZLTXPromptEnhance")
        assert enhance, stem
        values = enhance[0]["widgets_values"]
        flag = values[2] if len(values) >= 8 else values[1]
        assert flag is False


def test_dialogue_and_multishot_are_t2v_av() -> None:
    dialogue = _load("motion/av/dialogue-8s.json")
    multi = _load("motion/av/multishot-8s.json")
    for graph, prompt in ((dialogue, LTX_DIALOGUE), (multi, LTX_MULTISHOT)):
        types = {n.get("type") for n in graph["nodes"]}
        assert "LTXVImgToVideo" not in types
        assert "EmptyLTXVLatentVideo" in types
        assert "LTXVConcatAVLatent" in types
        assert "LTXVAudioVAEDecode" in types
        assert "LTXVEmptyLatentAudio" in types
        blob = json.dumps(graph)
        assert prompt[:40] in blob
        latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyLTXVLatentVideo")
        assert latent["widgets_values"][0] == 1280
        assert latent["widgets_values"][1] == 704
        assert int(latent["widgets_values"][2]) == 193
    assert any(n.get("type") == "LTXVModalityGuidance" for n in dialogue["nodes"])
    modality = next(n for n in dialogue["nodes"] if n.get("type") == "LTXVModalityGuidance")
    sampler = next(n for n in dialogue["nodes"] if n.get("type") == "KSampler")
    assert _source_of(dialogue, sampler, "model") is modality
    assert '"' in LTX_DIALOGUE or "\u201c" in LTX_DIALOGUE
    assert "hard cut" in LTX_MULTISHOT.lower()
    assert "match cut" in LTX_MULTISHOT.lower()


def test_product_hero_is_i2v_from_packshot() -> None:
    graph = _load("motion/av/product-hero.json")
    assert any(n.get("type") == "LTXVImgToVideo" for n in graph["nodes"])
    note = graph["extra"]["lab_note"]
    assert "packshot" in note.lower()
    assert "stills/product-packshot" in note or "ez_packshot" in note
    blob = json.dumps(graph)
    assert LTX_PRODUCT_HERO[:40] in blob
    img = next(n for n in graph["nodes"] if n.get("type") == "LTXVImgToVideo")
    assert int(img["widgets_values"][0]) == 1280
    assert int(img["widgets_values"][1]) == 704
    assert int(img["widgets_values"][2]) == 193


def test_flf_guides_video_latent_before_concat() -> None:
    graph = _load("motion/av/first-last-8s.json")
    loaders = _by_type(graph, "LoadImage")
    assert len(loaders) == 2
    titles = {str(n.get("title") or "") for n in loaders}
    assert "First frame" in titles
    assert "Last frame" in titles
    for loader in loaders:
        image_out = next(o for o in loader["outputs"] if str(o.get("name") or "").upper() == "IMAGE")
        assert image_out.get("links"), loader.get("title")
    guides = _by_type(graph, "LTXVAddGuide")
    assert len(guides) == 2
    idxs = sorted(int(n["widgets_values"][0]) for n in guides)
    assert idxs == [-1, 0]
    concat = next(n for n in graph["nodes"] if n.get("type") == "LTXVConcatAVLatent")
    video_src = _source_of(graph, concat, "video_latent")
    assert video_src is not None
    assert video_src.get("type") == "LTXVAddGuide"
    for guide in guides:
        latent_src = _source_of(graph, guide, "latent")
        assert latent_src is not None
        assert latent_src.get("type") in {"EmptyLTXVLatentVideo", "LTXVAddGuide"}
        assert latent_src.get("type") != "LTXVConcatAVLatent"
    assert any(n.get("type") == "LTXVCropGuides" for n in graph["nodes"])
    crop = next(n for n in graph["nodes"] if n.get("type") == "LTXVCropGuides")
    decode = next(n for n in graph["nodes"] if n.get("type") == "VAEDecode")
    assert _source_of(graph, decode, "samples") is crop or _source_of(graph, decode, "latent") is crop
    blob = json.dumps(graph)
    assert LTX_FLF[:40] in blob


def test_a2v_muxes_original_audio_not_decode() -> None:
    graph = _load("motion/av/audio-to-video-8s.json")
    types = {n.get("type") for n in graph["nodes"]}
    assert "LoadAudio" in types
    assert "LTXVAudioVAEEncode" in types
    assert "LTXVAudioVAEDecode" not in types
    vhs = next(n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine")
    audio_src = _source_of(graph, vhs, "audio")
    assert audio_src is not None
    assert audio_src.get("type") == "LoadAudio"
    encode = next(n for n in graph["nodes"] if n.get("type") == "LTXVAudioVAEEncode")
    assert _source_of(graph, encode, "audio") is audio_src
    concat = next(n for n in graph["nodes"] if n.get("type") == "LTXVConcatAVLatent")
    assert _source_of(graph, concat, "audio_latent") is encode
    blob = json.dumps(graph)
    assert LTX_A2V[:40] in blob
    assert "Wav2Lip" not in blob


def test_showcase_app_mode_integer_ids() -> None:
    for stem, _prefix, kind in SHOWCASE:
        graph = _load(stem)
        extra = graph.get("extra") or {}
        linear = extra.get("linearData") or {}
        live = {int(n["id"]) for n in graph["nodes"]}
        names = _widget_names(graph)
        labels = _labels(graph)
        assert "prompt" in names, stem
        assert "enhance" in names, stem
        assert "seed" in names, stem
        for entry in linear.get("inputs") or []:
            nid = linear_input_node_id(entry)
            assert isinstance(entry[0], int), (stem, entry[0])
            assert ":" not in str(entry[0]), (stem, entry[0])
            assert nid in live, (stem, entry)
        if kind == "flf":
            assert names.count("image") == 2, names
            assert "First frame" in labels
            assert "Last frame" in labels
        if kind == "a2v":
            assert "audio" in names, names
            assert any("audio" in label.lower() for label in labels)
        if kind == "i2v":
            assert "image" in names
            assert "style" not in names
        if kind == "t2v":
            assert "style" in names
            assert "image" not in names


def test_talking_head_note_points_at_real_a2v() -> None:
    graph = _load("stills/talking-head.json")
    note = graph["extra"]["lab_note"]
    assert "motion/av/audio-to-video-8s" in note
