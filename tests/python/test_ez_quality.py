"""Hermetic tests for EZQuality presets, node, and graph stamp."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from _lab_paths import lab_json, lab_graph_paths
from _wire_quality import (
    QUALITY_TYPE,
    QUALITY_WIDGET,
    ensure_quality_node,
    find_quality_node,
)

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_quality import nodes as quality_nodes  # noqa: E402
from ez_quality.nodes import EZQuality  # noqa: E402
from ez_quality.presets import (  # noqa: E402
    AUDIO_DRAFT_STEPS,
    AUDIO_HIGH_STEPS,
    AUDIO_MAX_STEPS,
    AUDIO_STANDARD_STEPS,
    CLIP_4B,
    CLIP_8B,
    FLUX2_DEV,
    KLEIN_9B,
    KLEIN_9B_BASE,
    KLEIN_9B_CFG,
    KLEIN_9B_STEPS,
    KLEIN_BASE,
    KLEIN_DISTILLED,
    KLEIN_DRAFT_CFG,
    KLEIN_DRAFT_STEPS,
    KLEIN_HIGH_BASE_CFG,
    KLEIN_HIGH_BASE_STEPS,
    KLEIN_HIGH_DISTILLED_CFG,
    KLEIN_HIGH_DISTILLED_STEPS,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    LTX_DRAFT_STEPS,
    LTX_HIGH_STEPS,
    LTX_MAX_STEPS,
    LTX_STANDARD_STEPS,
    QUALITY_CHOICES,
    QUALITY_CUSTOM,
    QUALITY_DRAFT,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_HIGH,
    QUALITY_LAB,
    QUALITY_MAX,
    QUALITY_STANDARD,
    QUALITY_ULTRA,
    QualityOverlay,
    TRELLIS_DRAFT_STEPS,
    TRELLIS_HIGH_STEPS,
    TRELLIS_MAX_STEPS,
    TRELLIS_STANDARD_STEPS,
    UNET_NAME_INDEX,
    VAE_SMALL,
    WAN_DRAFT_STEPS,
    WAN_HIGH_STEPS,
    WAN_MAX_STEPS,
    WAN_STANDARD_STEPS,
    _klein_overlay,
    _pick_unet,
    apply_to_graph,
    infer_occupancy,
    is_banned_unet,
    is_klein_4b_unet,
    is_klein_9b_unet,
    normalize_quality,
    resolve_overlay,
)

JS = CUSTOM / "ez_quality" / "js" / "ez_quality.js"


def _load(name: str) -> dict:
    return json.loads(lab_json(name).read_text(encoding="utf-8"))


def _sampler(graph: dict) -> dict:
    return next(n for n in graph["nodes"] if n.get("type") == "KSampler")


def _unet(graph: dict) -> dict:
    return next(n for n in graph["nodes"] if n.get("type") == "UNETLoader")


def _values(node: dict) -> list:
    raw = node.get("widgets_values")
    assert isinstance(raw, list)
    return raw


def _graph_node(graph: dict, index: int) -> dict:
    nodes = graph.get("nodes")
    assert isinstance(nodes, list)
    node = nodes[index]
    assert isinstance(node, dict)
    return node


def test_pack_mappings() -> None:
    assert quality_nodes.NODE_CLASS_MAPPINGS["EZQuality"] is EZQuality
    assert quality_nodes.NODE_DISPLAY_NAME_MAPPINGS["EZQuality"] == "Quality"
    assert EZQuality.OUTPUT_NODE is True
    types = EZQuality.INPUT_TYPES()
    combo = types["required"]["quality"][0]
    assert list(combo) == list(QUALITY_CHOICES)
    assert QUALITY_FREE_COMMERCIAL in QUALITY_CHOICES
    high_at = QUALITY_CHOICES.index(QUALITY_HIGH)
    free_at = QUALITY_CHOICES.index(QUALITY_FREE_COMMERCIAL)
    ultra_at = QUALITY_CHOICES.index(QUALITY_ULTRA)
    assert high_at < free_at < ultra_at


def test_report_normalizes_unknown() -> None:
    out = EZQuality().report("nope")
    assert out["result"] == (QUALITY_LAB,)
    assert out["ui"]["text"] == (QUALITY_LAB,)
    assert EZQuality().report("HIGH")["result"] == (QUALITY_HIGH,)


def test_normalize_quality() -> None:
    assert normalize_quality("Draft") == QUALITY_DRAFT
    assert normalize_quality(None) == QUALITY_LAB
    assert normalize_quality("weird") == QUALITY_LAB
    assert normalize_quality(QUALITY_FREE_COMMERCIAL) == QUALITY_FREE_COMMERCIAL
    assert normalize_quality("free_commercial") == QUALITY_FREE_COMMERCIAL
    assert normalize_quality("FREE_COMMERCIAL") == QUALITY_FREE_COMMERCIAL
    assert normalize_quality("  Free Commercial Use (<$10M)  ") == QUALITY_FREE_COMMERCIAL


def test_banned_unet_needles() -> None:
    assert not is_banned_unet("flux-2-klein-9b.safetensors")
    assert not is_banned_unet(FLUX2_DEV)
    assert is_banned_unet("z_image_turbo_bf16.safetensors")
    assert is_banned_unet("MiniMax-H3.safetensors")
    assert not is_banned_unet(KLEIN_DISTILLED)
    assert not is_banned_unet(KLEIN_BASE)
    assert is_klein_9b_unet(KLEIN_9B) is True


def test_klein_high_without_base_keeps_cfg_1() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_HIGH,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED,),
    )
    assert overlay.steps == KLEIN_HIGH_DISTILLED_STEPS
    assert overlay.cfg == KLEIN_HIGH_DISTILLED_CFG
    assert overlay.unet_name is None


def test_klein_high_with_base_swaps_unet() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_HIGH,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
    )
    assert overlay.unet_name == KLEIN_BASE
    assert overlay.steps == KLEIN_HIGH_BASE_STEPS
    assert overlay.cfg == KLEIN_HIGH_BASE_CFG


def test_klein_high_never_selects_banned() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_HIGH,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, "flux-2-klein-9b.safetensors"),
    )
    assert overlay.unet_name is None
    assert overlay.cfg == KLEIN_HIGH_DISTILLED_CFG


def test_klein_draft_steps_and_cfg() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_DRAFT,
        authored_steps=8,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
    )
    assert overlay.steps == KLEIN_DRAFT_STEPS
    assert overlay.cfg == KLEIN_DRAFT_CFG
    assert overlay.unet_name is None


def test_lab_is_noop() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_LAB,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_BASE,),
    )
    assert overlay == resolve_overlay(
        occupancy="wan",
        quality=QUALITY_LAB,
        authored_steps=20,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
    )


def test_wan_overlay_steps_only() -> None:
    draft = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_DRAFT,
        authored_steps=20,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
    )
    high = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_HIGH,
        authored_steps=20,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
    )
    assert draft.steps == WAN_DRAFT_STEPS
    assert high.steps == WAN_HIGH_STEPS
    assert draft.cfg is None and high.cfg is None
    assert draft.unet_name is None and high.unet_name is None


def test_wan_high_does_not_write_14b() -> None:
    overlay = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_HIGH,
        authored_steps=8,
        authored_cfg=3.0,
        unet_name="wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
        available_unets=(
            "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            "wan2.2_ti2v_5B_fp16.safetensors",
        ),
    )
    assert overlay.steps is None
    assert overlay.unet_name is None


def test_ltx_and_film_never_change_cfg() -> None:
    for occ in ("ltx", "film"):
        high = resolve_overlay(
            occupancy=occ,
            quality=QUALITY_HIGH,
            authored_steps=20,
            authored_cfg=1.0,
            unet_name="ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
        )
        assert high.steps == LTX_HIGH_STEPS
        assert high.cfg is None
        assert high.unet_name is None
        draft = resolve_overlay(
            occupancy=occ,
            quality=QUALITY_DRAFT,
            authored_steps=20,
            authored_cfg=1.0,
            unet_name="ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
        )
        assert draft.steps == LTX_DRAFT_STEPS


def test_audio_and_trellis_and_inspire() -> None:
    audio = resolve_overlay(
        occupancy="audio",
        quality=QUALITY_HIGH,
        authored_steps=8,
        authored_cfg=1.0,
        unet_name="",
    )
    assert audio.steps == AUDIO_HIGH_STEPS
    assert audio.cfg is None
    draft_audio = resolve_overlay(
        occupancy="audio",
        quality=QUALITY_DRAFT,
        authored_steps=8,
        authored_cfg=1.0,
        unet_name="",
    )
    assert draft_audio.steps == AUDIO_DRAFT_STEPS
    trellis = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_HIGH,
        authored_steps=12,
        authored_cfg=7.5,
        unet_name="",
    )
    assert trellis.steps == TRELLIS_HIGH_STEPS
    assert trellis.cfg is None
    inspire = resolve_overlay(
        occupancy="llm",
        quality=QUALITY_HIGH,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name="",
    )
    assert inspire.steps is None


def test_apply_klein_draft_does_not_change_latent_size() -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    before = list(latent["widgets_values"])
    apply_to_graph(graph, QUALITY_DRAFT, available_unets=(KLEIN_DISTILLED,))
    assert latent["widgets_values"] == before
    sampler = _sampler(graph)
    assert sampler["widgets_values"][KSAMPLER_STEPS_INDEX] == KLEIN_DRAFT_STEPS
    assert sampler["widgets_values"][KSAMPLER_CFG_INDEX] == KLEIN_DRAFT_CFG


def test_apply_klein_high_fallback_keeps_distilled() -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    apply_to_graph(graph, QUALITY_HIGH, available_unets=(KLEIN_DISTILLED,))
    assert _unet(graph)["widgets_values"][UNET_NAME_INDEX] == KLEIN_DISTILLED
    sampler = _sampler(graph)
    assert sampler["widgets_values"][KSAMPLER_STEPS_INDEX] == KLEIN_HIGH_DISTILLED_STEPS
    assert sampler["widgets_values"][KSAMPLER_CFG_INDEX] == KLEIN_HIGH_DISTILLED_CFG


def test_apply_klein_high_swaps_when_base_listed() -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    apply_to_graph(
        graph, QUALITY_HIGH, available_unets=(KLEIN_DISTILLED, KLEIN_BASE)
    )
    assert _unet(graph)["widgets_values"][UNET_NAME_INDEX] == KLEIN_BASE
    sampler = _sampler(graph)
    assert sampler["widgets_values"][KSAMPLER_STEPS_INDEX] == KLEIN_HIGH_BASE_STEPS
    assert sampler["widgets_values"][KSAMPLER_CFG_INDEX] == pytest.approx(
        KLEIN_HIGH_BASE_CFG
    )


def test_apply_wan_does_not_change_frames_or_unet() -> None:
    graph = copy.deepcopy(_load("motion/silent/still-to-video-5s.json"))
    unet_before = _unet(graph)["widgets_values"][UNET_NAME_INDEX]
    latent = next(
        n for n in graph["nodes"] if n.get("type") == "Wan22ImageToVideoLatent"
    )
    latent_before = copy.deepcopy(latent.get("widgets_values"))
    apply_to_graph(graph, QUALITY_HIGH)
    assert _unet(graph)["widgets_values"][UNET_NAME_INDEX] == unet_before
    assert "14B" not in unet_before
    assert "14B" not in _unet(graph)["widgets_values"][UNET_NAME_INDEX]
    assert latent.get("widgets_values") == latent_before
    assert _sampler(graph)["widgets_values"][KSAMPLER_STEPS_INDEX] == WAN_HIGH_STEPS


def test_apply_ltx_does_not_change_length() -> None:
    graph = copy.deepcopy(_load("motion/av/still-to-video-8s.json"))
    video = next(n for n in graph["nodes"] if n.get("type") == "LTXVImgToVideo")
    before = list(video["widgets_values"])
    apply_to_graph(graph, QUALITY_HIGH)
    assert video["widgets_values"] == before
    assert _sampler(graph)["widgets_values"][KSAMPLER_STEPS_INDEX] == LTX_HIGH_STEPS
    assert _sampler(graph)["widgets_values"][KSAMPLER_CFG_INDEX] == 1.0


def test_apply_a14b_is_noop() -> None:
    graph = copy.deepcopy(_load("optional/still-to-video-a14b.json"))
    sampler_before = list(_sampler(graph)["widgets_values"])
    unets_before = [
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "UNETLoader"
    ]
    apply_to_graph(
        graph,
        QUALITY_HIGH,
        available_unets=tuple(unets_before),
    )
    assert list(_sampler(graph)["widgets_values"]) == sampler_before
    after = [
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "UNETLoader"
    ]
    assert after == unets_before


def test_ensure_quality_node_is_idempotent() -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    ensure_quality_node(graph)
    first = find_quality_node(graph)
    assert first is not None
    node_id = first["id"]
    count = sum(1 for n in graph["nodes"] if n.get("type") == QUALITY_TYPE)
    ensure_quality_node(graph)
    again = find_quality_node(graph)
    assert again is not None
    assert sum(1 for n in graph["nodes"] if n.get("type") == QUALITY_TYPE) == count == 1
    assert again["id"] == node_id
    linear = graph["extra"]["linearData"]["inputs"]
    quality_rows = [row for row in linear if row[1] == QUALITY_WIDGET]
    assert len(quality_rows) == 1
    assert linear[0][1] == QUALITY_WIDGET
    assert linear[0][0] == node_id


def test_ensure_quality_keeps_required_still_first() -> None:
    graph = copy.deepcopy(_load("stills/talking-head.json"))
    ensure_quality_node(graph)
    names = [row[1] for row in graph["extra"]["linearData"]["inputs"]]
    assert names[0] == "image"
    assert names[1] == QUALITY_WIDGET
    quality = find_quality_node(graph)
    assert quality is not None
    assert graph["extra"]["linearData"]["inputs"][1][0] == quality["id"]


def test_ensure_quality_places_without_overlap() -> None:
    graph = copy.deepcopy(_load("films/go-see.json"))
    ensure_quality_node(graph)
    quality = find_quality_node(graph)
    assert quality is not None
    qx, qy = float(quality["pos"][0]), float(quality["pos"][1])
    qw, qh = 320.0, 82.0
    pad = 20.0
    qa = (qx - pad, qy - pad, qx + qw + pad, qy + qh + pad)
    for node in graph["nodes"]:
        if node is quality:
            continue
        pos = node.get("pos") or [0, 0]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            w, h = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            w, h = float(size[0]), float(size[1])
        ba = (
            float(pos[0]) - pad,
            float(pos[1]) - pad,
            float(pos[0]) + w + pad,
            float(pos[1]) + h + pad,
        )
        hit = qa[0] < ba[2] and qa[2] > ba[0] and qa[1] < ba[3] and qa[3] > ba[1]
        assert not hit, (node.get("id"), node.get("type"))


@pytest.mark.parametrize("path", lab_graph_paths(), ids=lambda p: p.name)
def test_every_lab_graph_has_one_quality_node(path: Path) -> None:
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = [n for n in graph.get("nodes") or [] if n.get("type") == QUALITY_TYPE]
    assert len(hits) == 1, path
    extra = graph.get("extra") or {}
    assert extra.get("lab_quality", {}).get("default") == QUALITY_LAB
    mode = extra.get("lab_app_mode") or {}
    if mode.get("enabled") is True:
        linear = extra.get("linearData") or {}
        inputs = linear.get("inputs") or []
        assert inputs, path
        names = [entry[1] for entry in inputs]
        idx = 0
        while idx < len(names) and names[idx] == "image":
            idx += 1
        assert names[idx] == QUALITY_WIDGET, path
        assert int(inputs[idx][0]) == int(hits[0]["id"])


def test_klein_9b_is_not_klein_4b() -> None:
    assert is_klein_4b_unet("flux-2-klein-9b.safetensors") is False
    assert is_klein_4b_unet(KLEIN_DISTILLED) is True


def test_pick_unet_refuses_banned_and_missing() -> None:
    assert _pick_unet("MiniMax-H3.safetensors", {"MiniMax-H3.safetensors"}) is None
    assert _pick_unet(FLUX2_DEV, {FLUX2_DEV}) == FLUX2_DEV
    assert _pick_unet(KLEIN_BASE, {KLEIN_DISTILLED}) is None
    assert _pick_unet(KLEIN_BASE, {KLEIN_BASE}) == KLEIN_BASE
    assert _pick_unet(KLEIN_BASE, set()) is None


def test_unknown_occupancy_is_noop() -> None:
    overlay = resolve_overlay(
        occupancy="dub",
        quality=QUALITY_HIGH,
        authored_steps=8,
        authored_cfg=1.0,
        unet_name="",
    )
    assert overlay.steps is None
    assert overlay.unet_name is None


def test_klein_draft_from_base_restores_distilled() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_DRAFT,
        authored_steps=24,
        authored_cfg=3.5,
        unet_name=KLEIN_BASE,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
    )
    assert overlay.steps == KLEIN_DRAFT_STEPS
    assert overlay.cfg == KLEIN_DRAFT_CFG
    assert overlay.unet_name == KLEIN_DISTILLED


def test_infer_occupancy_from_node_types() -> None:
    assert infer_occupancy({"nodes": [{"type": "EZFilmConcat"}]}) == "film"
    assert infer_occupancy({"nodes": [{"type": "MeshToFile3D"}]}) == "trellis"
    assert infer_occupancy({"nodes": [{"type": "SaveAudio"}]}) == "audio"
    assert infer_occupancy({"nodes": [{"type": "SaveAudioMP3"}]}) == "audio"
    assert (
        infer_occupancy(
            {
                "nodes": [
                    {"type": "VHS_VideoCombine"},
                    {
                        "type": "UNETLoader",
                        "widgets_values": [
                            "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
                        ],
                    },
                ]
            }
        )
        == "ltx"
    )
    assert (
        infer_occupancy(
            {
                "nodes": [
                    {"type": "SaveVideo"},
                    {
                        "type": "UNETLoader",
                        "widgets_values": ["wan2.2_ti2v_5B_fp16.safetensors"],
                    },
                ]
            }
        )
        == "wan"
    )
    assert infer_occupancy({"nodes": [{"type": "VHS_VideoCombine"}]}) == "wan"
    assert infer_occupancy({"nodes": [{"type": "SaveImage"}]}) == "klein"
    assert infer_occupancy({"nodes": [{"type": "Note"}]}) == ""
    assert infer_occupancy({"extra": "nope", "nodes": []}) == ""
    assert infer_occupancy({"extra": {"lab_app_mode": {"occupancy": ""}}}) == ""


def test_apply_skips_empty_and_non_klein_unets() -> None:
    graph = {
        "extra": {"lab_app_mode": {"occupancy": "klein"}},
        "nodes": [
            {"type": "Note", "widgets_values": ["hi"]},
            {"type": "UNETLoader", "widgets_values": []},
            {"type": "UNETLoader", "widgets_values": [KLEIN_DISTILLED]},
            {
                "type": "UNETLoader",
                "widgets_values": ["wan2.2_ti2v_5B_fp16.safetensors"],
            },
            {
                "type": "KSampler",
                "widgets_values": [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
            },
        ],
    }
    apply_to_graph(
        graph, QUALITY_HIGH, available_unets=(KLEIN_DISTILLED, KLEIN_BASE)
    )
    assert _values(_graph_node(graph, 1)) == []
    assert _values(_graph_node(graph, 2))[0] == KLEIN_BASE
    assert _values(_graph_node(graph, 3))[0] == "wan2.2_ti2v_5B_fp16.safetensors"


def test_apply_with_no_unet_loader() -> None:
    graph = {
        "extra": {"lab_app_mode": {"occupancy": "audio"}},
        "nodes": [
            {"type": "Note", "widgets_values": ["n"]},
            {
                "type": "KSampler",
                "widgets_values": [42, "fixed", 8, 1.0, "euler", "simple", 1.0],
            },
        ],
    }
    apply_to_graph(graph, QUALITY_HIGH)
    assert _values(_graph_node(graph, 1))[KSAMPLER_STEPS_INDEX] == AUDIO_HIGH_STEPS


def test_apply_refuses_banned_unet_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    before = _unet(graph)["widgets_values"][UNET_NAME_INDEX]

    def _banned(**_kwargs: object) -> QualityOverlay:
        return QualityOverlay(unet_name="MiniMax-H3.safetensors")

    monkeypatch.setattr("ez_quality.presets.resolve_overlay", _banned)
    apply_to_graph(graph, QUALITY_HIGH, available_unets=(KLEIN_BASE,))
    assert _unet(graph)["widgets_values"][UNET_NAME_INDEX] == before


def test_js_mirrors_preset_constants() -> None:
    body = JS.read_text(encoding="utf-8")
    assert "widget.value" in body
    assert "beforeQueued" in body
    assert "node_widget" not in body
    assert "onResize" not in body
    assert KLEIN_BASE in body
    assert str(WAN_HIGH_STEPS) in body
    assert str(KLEIN_HIGH_BASE_STEPS) in body
    assert "wan2.2_i2v_high_noise_14B" not in body
    assert 'includes("14b")' in body
    assert "flux-2-klein-9b" in body.lower() or "klein-9b" in body
    assert QUALITY_CUSTOM in body
    assert "clip_name" in body
    assert VAE_SMALL in body


def test_custom_and_lab_are_noop() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_CUSTOM,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE, KLEIN_9B),
    )
    assert overlay == QualityOverlay()
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    before = _values(_sampler(graph))[KSAMPLER_STEPS_INDEX]
    apply_to_graph(
        graph,
        QUALITY_HIGH,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
    )
    high_steps = _values(_sampler(graph))[KSAMPLER_STEPS_INDEX]
    assert high_steps == KLEIN_HIGH_BASE_STEPS
    apply_to_graph(graph, QUALITY_CUSTOM, available_unets=(KLEIN_BASE,))
    assert _values(_sampler(graph))[KSAMPLER_STEPS_INDEX] == high_steps
    apply_to_graph(graph, QUALITY_LAB, available_unets=(KLEIN_BASE,))
    assert _values(_sampler(graph))[KSAMPLER_STEPS_INDEX] == high_steps
    assert before == 4


def test_ultra_selects_9b_and_8b_te_when_present() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_ULTRA,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B),
        available_clips=(CLIP_4B, CLIP_8B),
        available_vaes=(VAE_SMALL,),
    )
    assert overlay.unet_name == KLEIN_9B
    assert overlay.clip_name == CLIP_8B
    assert overlay.vae_name == VAE_SMALL
    assert overlay.steps == KLEIN_9B_STEPS
    assert overlay.cfg == KLEIN_9B_CFG


def test_ultra_falls_back_to_high_without_9b() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_ULTRA,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
        available_clips=(CLIP_4B,),
    )
    assert overlay.unet_name == KLEIN_BASE
    assert overlay.steps == KLEIN_HIGH_BASE_STEPS
    assert overlay.clip_name == CLIP_4B


def test_max_prefers_9b_base_then_dev() -> None:
    nine = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_MAX,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B_BASE, FLUX2_DEV),
        available_clips=(CLIP_8B, CLIP_4B),
    )
    assert nine.unet_name == KLEIN_9B_BASE
    assert nine.clip_name == CLIP_8B
    dev = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_MAX,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, FLUX2_DEV),
        available_clips=("mistral_3_small_flux2_bf16.safetensors",),
    )
    assert dev.unet_name == FLUX2_DEV
    assert dev.clip_name == "mistral_3_small_flux2_bf16.safetensors"


def test_standard_is_distilled_8_steps() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_STANDARD,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_BASE,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
        available_clips=(CLIP_4B,),
    )
    assert overlay.unet_name == KLEIN_DISTILLED
    assert overlay.steps == 8
    assert overlay.cfg == 1.0


def test_apply_writes_clip_and_vae_on_klein() -> None:
    graph = {
        "extra": {"lab_app_mode": {"occupancy": "klein"}},
        "nodes": [
            {"type": "UNETLoader", "widgets_values": [KLEIN_DISTILLED]},
            {"type": "CLIPLoader", "widgets_values": [CLIP_4B, "flux2", "default"]},
            {"type": "VAELoader", "widgets_values": ["flux2-vae.safetensors"]},
            {
                "type": "KSampler",
                "widgets_values": [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
            },
        ],
    }
    apply_to_graph(
        graph,
        QUALITY_ULTRA,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B),
        available_clips=(CLIP_4B, CLIP_8B),
        available_vaes=("flux2-vae.safetensors", VAE_SMALL),
    )
    assert _values(_graph_node(graph, 0))[0] == KLEIN_9B
    assert _values(_graph_node(graph, 1))[0] == CLIP_8B
    assert _values(_graph_node(graph, 2))[0] == VAE_SMALL
    assert _values(_graph_node(graph, 3))[KSAMPLER_STEPS_INDEX] == KLEIN_9B_STEPS


def test_wan_max_bumps_steps_not_unet() -> None:
    overlay = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_MAX,
        authored_steps=20,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
        available_unets=(
            "wan2.2_ti2v_5B_fp16.safetensors",
            "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
        ),
    )
    assert overlay.steps == WAN_MAX_STEPS
    assert overlay.unet_name is None


def test_named_qualities_cover_family_step_tables() -> None:
    wan_std = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_STANDARD,
        authored_steps=16,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
    )
    assert wan_std.steps == WAN_STANDARD_STEPS
    ltx_std = resolve_overlay(
        occupancy="ltx",
        quality=QUALITY_STANDARD,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="ltx-2.5.safetensors",
    )
    assert ltx_std.steps == LTX_STANDARD_STEPS
    ltx_max = resolve_overlay(
        occupancy="film",
        quality=QUALITY_MAX,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="ltx-2.5.safetensors",
    )
    assert ltx_max.steps == LTX_MAX_STEPS
    audio_std = resolve_overlay(
        occupancy="audio",
        quality=QUALITY_STANDARD,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name="",
    )
    assert audio_std.steps == AUDIO_STANDARD_STEPS
    audio_max = resolve_overlay(
        occupancy="audio",
        quality=QUALITY_MAX,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name="",
    )
    assert audio_max.steps == AUDIO_MAX_STEPS
    trellis_draft = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_DRAFT,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="",
    )
    assert trellis_draft.steps == TRELLIS_DRAFT_STEPS
    trellis_std = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_STANDARD,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="",
    )
    assert trellis_std.steps == TRELLIS_STANDARD_STEPS
    trellis_max = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_MAX,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="",
    )
    assert trellis_max.steps == TRELLIS_MAX_STEPS
    trellis_high = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_HIGH,
        authored_steps=12,
        authored_cfg=1.0,
        unet_name="",
    )
    assert trellis_high.steps == TRELLIS_HIGH_STEPS


def test_max_without_9b_or_dev_falls_back_to_high() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_MAX,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_BASE),
        available_clips=(CLIP_4B,),
    )
    assert overlay.unet_name == KLEIN_BASE
    assert overlay.steps == KLEIN_HIGH_BASE_STEPS


def test_apply_skips_non_flux2_clip_and_vae() -> None:
    graph = {
        "extra": {"lab_app_mode": {"occupancy": "klein"}},
        "nodes": [
            {"type": "UNETLoader", "widgets_values": [KLEIN_DISTILLED]},
            {
                "type": "CLIPLoader",
                "widgets_values": ["umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan"],
            },
            {"type": "VAELoader", "widgets_values": ["wan2.2_vae.safetensors"]},
            {
                "type": "KSampler",
                "widgets_values": [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
            },
        ],
    }
    apply_to_graph(
        graph,
        QUALITY_ULTRA,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B),
        available_clips=(CLIP_4B, CLIP_8B),
        available_vaes=("wan2.2_vae.safetensors", VAE_SMALL),
    )
    assert _values(_graph_node(graph, 0))[0] == KLEIN_9B
    assert _values(_graph_node(graph, 1))[0] == "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    assert _values(_graph_node(graph, 2))[0] == "wan2.2_vae.safetensors"


def test_free_commercial_klein_matches_high_and_never_nc() -> None:
    nc = (KLEIN_DISTILLED, KLEIN_BASE, KLEIN_9B, KLEIN_9B_BASE, FLUX2_DEV)
    clips = (CLIP_4B, CLIP_8B)
    vaes = (VAE_SMALL,)
    commercial = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=nc,
        available_clips=clips,
        available_vaes=vaes,
    )
    high = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_HIGH,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=nc,
        available_clips=clips,
        available_vaes=vaes,
    )
    assert commercial == high
    assert commercial.unet_name == KLEIN_BASE
    assert commercial.steps == KLEIN_HIGH_BASE_STEPS
    assert commercial.cfg == KLEIN_HIGH_BASE_CFG
    assert commercial.clip_name == CLIP_4B
    from_nine = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_9B,
        available_unets=nc,
        available_clips=clips,
        available_vaes=vaes,
    )
    assert from_nine.unet_name == KLEIN_BASE
    from_dev = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=4,
        authored_cfg=4.0,
        unet_name=FLUX2_DEV,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B, FLUX2_DEV),
        available_clips=clips,
        available_vaes=vaes,
    )
    assert from_dev.unet_name == KLEIN_DISTILLED
    assert from_dev.steps == KLEIN_HIGH_DISTILLED_STEPS
    no_base = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name=KLEIN_DISTILLED,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B, FLUX2_DEV),
    )
    assert no_base.unet_name is None
    assert no_base.steps == KLEIN_HIGH_DISTILLED_STEPS


def test_free_commercial_ltx_is_high_steps_wan_audio_are_noop() -> None:
    ltx = resolve_overlay(
        occupancy="ltx",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    )
    film = resolve_overlay(
        occupancy="film",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=20,
        authored_cfg=1.0,
        unet_name="ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    )
    assert ltx.steps == LTX_HIGH_STEPS
    assert film.steps == LTX_HIGH_STEPS
    assert ltx.cfg is None and ltx.unet_name is None
    wan = resolve_overlay(
        occupancy="wan",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=20,
        authored_cfg=5.0,
        unet_name="wan2.2_ti2v_5B_fp16.safetensors",
    )
    assert wan == QualityOverlay()
    audio = resolve_overlay(
        occupancy="audio",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=8,
        authored_cfg=1.0,
        unet_name="",
    )
    trellis = resolve_overlay(
        occupancy="trellis",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=12,
        authored_cfg=1.0,
        unet_name="",
    )
    llm = resolve_overlay(
        occupancy="llm",
        quality=QUALITY_FREE_COMMERCIAL,
        authored_steps=4,
        authored_cfg=1.0,
        unet_name="",
    )
    assert audio == QualityOverlay()
    assert trellis == QualityOverlay()
    assert llm == QualityOverlay()


def test_apply_free_commercial_keeps_size_and_skips_wan() -> None:
    still = copy.deepcopy(_load("stills/still-draft.json"))
    latent = next(n for n in still["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    before = list(latent["widgets_values"])
    apply_to_graph(
        still,
        QUALITY_FREE_COMMERCIAL,
        available_unets=(KLEIN_DISTILLED, KLEIN_9B, FLUX2_DEV, KLEIN_BASE),
    )
    assert latent["widgets_values"] == before
    assert _unet(still)["widgets_values"][UNET_NAME_INDEX] == KLEIN_BASE
    assert _sampler(still)["widgets_values"][KSAMPLER_STEPS_INDEX] == KLEIN_HIGH_BASE_STEPS
    ltx_graph = copy.deepcopy(_load("motion/av/still-to-video-8s.json"))
    video = next(n for n in ltx_graph["nodes"] if n.get("type") == "LTXVImgToVideo")
    length_before = list(video["widgets_values"])
    apply_to_graph(ltx_graph, QUALITY_FREE_COMMERCIAL)
    assert video["widgets_values"] == length_before
    assert _sampler(ltx_graph)["widgets_values"][KSAMPLER_STEPS_INDEX] == LTX_HIGH_STEPS
    wan_graph = copy.deepcopy(_load("motion/silent/still-to-video-5s.json"))
    wan_steps = list(_sampler(wan_graph)["widgets_values"])
    wan_unet = _unet(wan_graph)["widgets_values"][UNET_NAME_INDEX]
    apply_to_graph(wan_graph, QUALITY_FREE_COMMERCIAL)
    assert list(_sampler(wan_graph)["widgets_values"]) == wan_steps
    assert _unet(wan_graph)["widgets_values"][UNET_NAME_INDEX] == wan_unet


def test_js_mentions_free_commercial_and_clip_feeders() -> None:
    body = JS.read_text(encoding="utf-8")
    assert QUALITY_FREE_COMMERCIAL in body
    assert "free_commercial" in body
    assert "16:9 LTX feeder (1280×704)" in body
    assert "9:16 LTX feeder (768×1280)" in body
    assert "aspect_16_9_draft" in body
    assert "aspect_9_16_draft" in body


def test_klein_overlay_unknown_choice_uses_high() -> None:
    overlay = _klein_overlay(
        "not-a-quality",
        4,
        KLEIN_DISTILLED,
        CLIP_4B,
        "flux2-vae.safetensors",
        {KLEIN_DISTILLED, KLEIN_BASE},
        {CLIP_4B},
        {"flux2-vae.safetensors"},
    )
    assert overlay.unet_name == KLEIN_BASE
    assert overlay.steps == KLEIN_HIGH_BASE_STEPS
