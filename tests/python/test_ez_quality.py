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
from ez_quality.check import (  # noqa: E402
    CMD_DOWNLOAD_MODELS,
    CMD_IMAGE_9B,
    CMD_IMAGE_9B_BASE,
    CMD_IMAGE_FLUX2_DEV,
    CMD_IMAGE_FLUX3,
    CMD_IMAGE_FLUX3_BASE,
    CMD_IMAGE_FLUX3_NVFP4,
    CMD_IMAGE_FLUX3_PUP,
    CMD_IMAGE_FLUX3_TE,
    CMD_PERSON_MASK,
    PERSON_WEIGHT,
    SUB_CLIP,
    SUB_PERSON,
    SUB_UNET,
    SUB_VAE,
    _DEFAULT_FILES,
    CheckHints,
    FileSpec,
    command_for_filename,
    requirements_for,
    scan,
)
from ez_quality.nodes import EZQuality  # noqa: E402
from ez_quality.presets import (  # noqa: E402
    AUDIO_DRAFT_STEPS,
    AUDIO_HIGH_STEPS,
    AUDIO_MAX_STEPS,
    AUDIO_STANDARD_STEPS,
    CLIP_4B,
    CLIP_8B,
    CLIP_NAME_INDEX,
    CLIP_TYPE_FLUX2,
    FLUX2_DEV,
    FLUX2_DEV_CFG,
    FLUX2_DEV_STEPS,
    FLUX3_QUALITY_CHOICES,
    KLEIN3_BASE,
    KLEIN3_DISTILLED,
    KLEIN3_FAST_CFG,
    KLEIN3_FAST_STEPS,
    KLEIN3_NVFP4,
    KLEIN3_NVFP4_CFG,
    KLEIN3_NVFP4_STEPS,
    KLEIN3_QUALITY_CFG,
    KLEIN3_QUALITY_STEPS,
    KLEIN3_TE,
    KLEIN3_UPSAMPLER,
    KLEIN_9B,
    KLEIN_9B_BASE,
    KLEIN_9B_BASE_CFG,
    KLEIN_9B_BASE_STEPS,
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
    KLEIN_STANDARD_CFG,
    KLEIN_STANDARD_STEPS,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    LTX_DRAFT_STEPS,
    LTX_HIGH_STEPS,
    LTX_MAX_STEPS,
    LTX_STANDARD_STEPS,
    QUALITY_CHOICES,
    QUALITY_CUSTOM,
    QUALITY_DRAFT,
    QUALITY_FLUX3_FAST,
    QUALITY_FLUX3_NVFP4,
    QUALITY_FLUX3_QUALITY,
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
    VAE_FULL,
    VAE_NAME_INDEX,
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
    is_klein3_clip,
    is_klein3_unet,
    is_klein3_upsampler,
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
        # Required stills, then image-studio Iterate / This run, then Quality.
        while idx < len(names) and names[idx] in {"image", "iterate", "run_summary"}:
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
    assert "freezeQualityToCustom" in body
    assert "widgets_values[idx]" in body


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


def test_person_mask_need_follows_the_reinsert_node(tmp_path: Path) -> None:
    """EZReinsertPeople adds the optional DeepLabV3 checkpoint to Check models.

    Args:
        tmp_path: Scratch models root for the disk scan.
    """
    with_node = requirements_for(
        CheckHints(
            lab_rel="stills/background-swap",
            occupancy="none",
            types=("EZCubicCondition", "EZReinsertPeople"),
        )
    )
    need = next(need for need in with_node if need.pack == "person-mask")
    assert need.cmd == CMD_PERSON_MASK
    assert need.files == (FileSpec(SUB_PERSON, PERSON_WEIGHT),)
    assert PERSON_WEIGHT == "deeplabv3_resnet50_coco-cd0a2569.pth"
    without_node = requirements_for(
        CheckHints(
            lab_rel="stills/background-edit",
            occupancy="none",
            types=("EZKleinPromptEnhance",),
        )
    )
    assert without_node == []

    missing = scan(
        CheckHints(
            lab_rel="stills/background-swap",
            occupancy="none",
            types=("EZReinsertPeople",),
        ),
        (tmp_path,),
    )
    assert any(row.pack == "person-mask" for row in missing.missing)
    assert CMD_PERSON_MASK in missing.commands
    assert "ez-person" in [row.subdir for row in missing.missing]

    weight = tmp_path / "comfy" / SUB_PERSON / PERSON_WEIGHT
    weight.parent.mkdir(parents=True, exist_ok=True)
    weight.write_bytes(b"x")
    found = scan(
        CheckHints(
            lab_rel="stills/background-swap",
            occupancy="none",
            types=("EZReinsertPeople",),
        ),
        (tmp_path,),
    )
    assert any(
        row.pack == "person-mask" and row.state == "present" for row in found.present
    )
    assert not any(row.pack == "person-mask" for row in found.missing)


def test_js_mentions_free_commercial_and_clip_feeders() -> None:
    body = JS.read_text(encoding="utf-8")
    assert QUALITY_FREE_COMMERCIAL in body
    assert "free_commercial" in body
    assert "16:9 LTX feeder (1280x704)" in body
    assert "9:16 LTX feeder (768x1280)" in body
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


KLEIN3_ALL: tuple[str, ...] = (KLEIN3_DISTILLED, KLEIN3_BASE, KLEIN3_NVFP4)
OTHER_FAMILY_UNETS: tuple[str, ...] = (
    KLEIN_DISTILLED,
    KLEIN_BASE,
    KLEIN_9B,
    KLEIN_9B_BASE,
    FLUX2_DEV,
    "wan2.2_ti2v_5B_fp16.safetensors",
    "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    "",
)


def _flux3_graph(
    unet: str = KLEIN3_DISTILLED,
    clip: str = KLEIN3_TE,
    vae: str = VAE_FULL,
) -> dict:
    return {
        "extra": {"lab_app_mode": {"occupancy": "klein"}},
        "nodes": [
            {"type": "UNETLoader", "widgets_values": [unet, "default"]},
            {"type": "CLIPLoader", "widgets_values": [clip, "flux2", "default"]},
            {"type": "VAELoader", "widgets_values": [vae]},
            {
                "type": "KSampler",
                "widgets_values": [42, "fixed", 20, 2.5, "euler", "simple", 1.0],
            },
            {"type": "EmptyFlux2LatentImage", "widgets_values": [1024, 1024, 1]},
        ],
    }


def test_flux3_constants_are_the_pinned_hf_filenames() -> None:
    assert KLEIN3_DISTILLED == "flux3-image-klein-int8-convrot.safetensors"
    assert KLEIN3_BASE == "flux3-image-klein-base-int8-convrot.safetensors"
    assert KLEIN3_NVFP4 == "flux3-image-klein-base-nvfp4.safetensors"
    assert KLEIN3_TE == "qwen3vl_4b_int8_convrot.safetensors"
    assert KLEIN3_UPSAMPLER == (
        "qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors"
    )
    assert VAE_FULL == "flux2-vae.safetensors"
    assert (KLEIN3_FAST_STEPS, KLEIN3_FAST_CFG) == (16, 1.0)
    assert (KLEIN3_QUALITY_STEPS, KLEIN3_QUALITY_CFG) == (50, 3.5)
    assert (KLEIN3_NVFP4_STEPS, KLEIN3_NVFP4_CFG) == (50, 3.5)
    for name in (*KLEIN3_ALL, KLEIN3_TE, KLEIN3_UPSAMPLER):
        assert is_banned_unet(name) is False
        assert name not in _DEFAULT_FILES


def test_flux3_quality_choices_are_additive() -> None:
    assert FLUX3_QUALITY_CHOICES == (
        QUALITY_FLUX3_FAST,
        QUALITY_FLUX3_QUALITY,
        QUALITY_FLUX3_NVFP4,
    )
    assert QUALITY_CHOICES[:8] == (
        QUALITY_CUSTOM,
        QUALITY_DRAFT,
        QUALITY_LAB,
        QUALITY_STANDARD,
        QUALITY_HIGH,
        QUALITY_FREE_COMMERCIAL,
        QUALITY_ULTRA,
        QUALITY_MAX,
    )
    assert QUALITY_CHOICES[8:] == FLUX3_QUALITY_CHOICES
    spec = EZQuality.INPUT_TYPES()["required"]["quality"]
    assert list(spec[0]) == list(QUALITY_CHOICES)
    assert spec[1]["default"] == QUALITY_LAB
    assert normalize_quality("FLUX3-Fast") == QUALITY_FLUX3_FAST
    assert normalize_quality("  flux3-quality ") == QUALITY_FLUX3_QUALITY
    assert normalize_quality("flux3-nvfp4") == QUALITY_FLUX3_NVFP4
    assert normalize_quality("flux3_fast") == QUALITY_LAB
    assert EZQuality().report("flux3-fast")["result"] == (QUALITY_FLUX3_FAST,)


def test_is_klein3_predicates() -> None:
    for name in KLEIN3_ALL:
        assert is_klein3_unet(name) is True
        assert is_klein_4b_unet(name) is False
        assert is_klein_9b_unet(name) is False
    assert is_klein3_unet("flux-3-image-klein-int8-convrot.safetensors") is True
    for name in (KLEIN_DISTILLED, KLEIN_9B, FLUX2_DEV, KLEIN3_UPSAMPLER, ""):
        assert is_klein3_unet(name) is False
    assert is_klein3_clip(KLEIN3_TE) is True
    assert is_klein3_clip(CLIP_4B) is False
    assert is_klein3_clip(CLIP_8B) is False
    assert is_klein3_clip(KLEIN3_UPSAMPLER) is False
    assert is_klein3_upsampler(KLEIN3_UPSAMPLER) is True
    assert is_klein3_upsampler(KLEIN3_TE) is False
    assert is_klein3_upsampler(KLEIN3_DISTILLED) is False


def test_flux3_fast_profile_writes_distilled_16_steps_cfg_1() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FLUX3_FAST,
        authored_steps=20,
        authored_cfg=2.5,
        unet_name=KLEIN3_NVFP4,
        available_unets=KLEIN3_ALL,
        clip_name=CLIP_4B,
        available_clips=(CLIP_4B, KLEIN3_TE),
        vae_name=VAE_SMALL,
        available_vaes=(VAE_SMALL, VAE_FULL),
    )
    assert overlay == QualityOverlay(
        steps=KLEIN3_FAST_STEPS,
        cfg=KLEIN3_FAST_CFG,
        unet_name=KLEIN3_DISTILLED,
        clip_name=KLEIN3_TE,
        vae_name=VAE_FULL,
        clip_type=CLIP_TYPE_FLUX2,
    )


def test_flux3_quality_and_nvfp4_profiles_use_their_own_unet() -> None:
    quality = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FLUX3_QUALITY,
        authored_steps=16,
        authored_cfg=1.0,
        unet_name=KLEIN3_DISTILLED,
        available_unets=KLEIN3_ALL,
        clip_name=KLEIN3_TE,
        available_clips=(CLIP_4B, KLEIN3_TE),
        vae_name=VAE_FULL,
        available_vaes=(VAE_FULL,),
    )
    assert quality.unet_name == KLEIN3_BASE
    assert quality.steps == KLEIN3_QUALITY_STEPS
    assert quality.cfg == KLEIN3_QUALITY_CFG
    assert quality.clip_name is None
    assert quality.vae_name is None
    assert quality.clip_type == CLIP_TYPE_FLUX2
    nvfp4 = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FLUX3_NVFP4,
        authored_steps=16,
        authored_cfg=1.0,
        unet_name=KLEIN3_DISTILLED,
        available_unets=KLEIN3_ALL,
        clip_name=KLEIN3_TE,
        available_clips=(KLEIN3_TE,),
        vae_name=VAE_FULL,
        available_vaes=(VAE_FULL,),
    )
    assert nvfp4.unet_name == KLEIN3_NVFP4
    assert nvfp4.steps == KLEIN3_NVFP4_STEPS
    assert nvfp4.cfg == KLEIN3_NVFP4_CFG


def test_flux3_profile_keeps_authored_files_when_weights_are_missing() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FLUX3_QUALITY,
        authored_steps=12,
        authored_cfg=2.0,
        unet_name=KLEIN3_DISTILLED,
        available_unets=(KLEIN3_DISTILLED,),
        clip_name=CLIP_4B,
        available_clips=(CLIP_4B,),
        vae_name=VAE_SMALL,
        available_vaes=(VAE_SMALL,),
    )
    assert overlay == QualityOverlay(
        steps=KLEIN3_QUALITY_STEPS,
        cfg=KLEIN3_QUALITY_CFG,
        clip_type=CLIP_TYPE_FLUX2,
    )


def test_flux3_profile_applies_when_only_the_te_pins_flux3() -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=QUALITY_FLUX3_FAST,
        authored_steps=20,
        authored_cfg=2.5,
        unet_name="",
        available_unets=KLEIN3_ALL,
        clip_name=KLEIN3_TE,
        available_clips=(CLIP_4B, KLEIN3_TE),
        vae_name=VAE_FULL,
        available_vaes=(VAE_FULL,),
    )
    assert overlay.unet_name == KLEIN3_DISTILLED
    assert overlay.steps == KLEIN3_FAST_STEPS


@pytest.mark.parametrize("quality", FLUX3_QUALITY_CHOICES)
@pytest.mark.parametrize("unet_name", OTHER_FAMILY_UNETS)
def test_flux3_profiles_never_touch_other_families(
    quality: str, unet_name: str
) -> None:
    overlay = resolve_overlay(
        occupancy="klein",
        quality=quality,
        authored_steps=20,
        authored_cfg=2.5,
        unet_name=unet_name,
        available_unets=(*KLEIN3_ALL, KLEIN_DISTILLED, KLEIN_BASE, KLEIN_9B, FLUX2_DEV),
        clip_name=CLIP_4B,
        available_clips=(CLIP_4B, CLIP_8B, KLEIN3_TE),
        vae_name=VAE_FULL,
        available_vaes=(VAE_FULL, VAE_SMALL),
    )
    assert overlay == QualityOverlay()


def test_apply_flux3_profile_writes_every_loader_and_sampler() -> None:
    graph = _flux3_graph(unet=KLEIN3_NVFP4, clip=CLIP_4B, vae=VAE_SMALL)
    latent = _values(_graph_node(graph, 4))
    apply_to_graph(
        graph,
        QUALITY_FLUX3_FAST,
        available_unets=KLEIN3_ALL,
        available_clips=(CLIP_4B, KLEIN3_TE),
        available_vaes=(VAE_SMALL, VAE_FULL),
    )
    assert _values(_graph_node(graph, 0))[UNET_NAME_INDEX] == KLEIN3_DISTILLED
    assert _values(_graph_node(graph, 1))[CLIP_NAME_INDEX] == KLEIN3_TE
    assert _values(_graph_node(graph, 1))[1] == CLIP_TYPE_FLUX2
    assert _values(_graph_node(graph, 2))[VAE_NAME_INDEX] == VAE_FULL
    assert _values(_graph_node(graph, 3))[KSAMPLER_STEPS_INDEX] == KLEIN3_FAST_STEPS
    assert _values(_graph_node(graph, 3))[KSAMPLER_CFG_INDEX] == KLEIN3_FAST_CFG
    assert _values(_graph_node(graph, 4)) == latent


def test_apply_flux3_profile_skips_foreign_clip_and_vae() -> None:
    graph = _flux3_graph(unet=KLEIN3_DISTILLED, clip="umt5_xxl_fp8_e4m3fn_scaled.safetensors")
    graph["nodes"][2]["widgets_values"] = ["wan2.2_vae.safetensors"]
    apply_to_graph(
        graph,
        QUALITY_FLUX3_QUALITY,
        available_unets=KLEIN3_ALL,
        available_clips=(CLIP_4B, KLEIN3_TE),
        available_vaes=(VAE_FULL,),
    )
    assert _values(_graph_node(graph, 0))[UNET_NAME_INDEX] == KLEIN3_BASE
    assert _values(_graph_node(graph, 1))[CLIP_NAME_INDEX] == (
        "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    )
    assert _values(_graph_node(graph, 1))[1] == "flux2"
    assert _values(_graph_node(graph, 2))[VAE_NAME_INDEX] == "wan2.2_vae.safetensors"
    assert (
        _values(_graph_node(graph, 3))[KSAMPLER_STEPS_INDEX] == KLEIN3_QUALITY_STEPS
    )


@pytest.mark.parametrize("quality", FLUX3_QUALITY_CHOICES)
def test_apply_flux3_profile_leaves_klein_graph_authored(quality: str) -> None:
    graph = copy.deepcopy(_load("stills/still-draft.json"))
    sampler_before = list(_values(_sampler(graph)))
    loaders_before = {
        node["type"]: list(node["widgets_values"])
        for node in graph["nodes"]
        if node.get("type") in {"UNETLoader", "CLIPLoader", "VAELoader"}
    }
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    latent_before = list(latent["widgets_values"])
    apply_to_graph(
        graph,
        quality,
        available_unets=KLEIN3_ALL,
        available_clips=(CLIP_4B, CLIP_8B, KLEIN3_TE),
        available_vaes=(VAE_FULL, VAE_SMALL),
    )
    assert list(_values(_sampler(graph))) == sampler_before
    assert latent["widgets_values"] == latent_before
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype in loaders_before:
            assert list(node["widgets_values"]) == loaders_before[ntype], ntype


def test_existing_family_overlays_are_unchanged_by_flux3() -> None:
    cases: list[tuple[str, str, tuple[str, ...], QualityOverlay]] = [
        (
            QUALITY_DRAFT,
            KLEIN_DISTILLED,
            (KLEIN_DISTILLED,),
            QualityOverlay(
                steps=KLEIN_DRAFT_STEPS, cfg=KLEIN_DRAFT_CFG, clip_type=CLIP_TYPE_FLUX2
            ),
        ),
        (
            QUALITY_STANDARD,
            KLEIN_BASE,
            (KLEIN_DISTILLED, KLEIN_BASE),
            QualityOverlay(
                steps=KLEIN_STANDARD_STEPS,
                cfg=KLEIN_STANDARD_CFG,
                unet_name=KLEIN_DISTILLED,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
        (
            QUALITY_HIGH,
            KLEIN_DISTILLED,
            (KLEIN_DISTILLED, KLEIN_BASE),
            QualityOverlay(
                steps=KLEIN_HIGH_BASE_STEPS,
                cfg=KLEIN_HIGH_BASE_CFG,
                unet_name=KLEIN_BASE,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
        (
            QUALITY_ULTRA,
            KLEIN_DISTILLED,
            (KLEIN_DISTILLED, KLEIN_9B),
            QualityOverlay(
                steps=KLEIN_9B_STEPS,
                cfg=KLEIN_9B_CFG,
                unet_name=KLEIN_9B,
                clip_name=CLIP_8B,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
        (
            QUALITY_MAX,
            KLEIN_DISTILLED,
            (KLEIN_DISTILLED, KLEIN_9B_BASE),
            QualityOverlay(
                steps=KLEIN_9B_BASE_STEPS,
                cfg=KLEIN_9B_BASE_CFG,
                unet_name=KLEIN_9B_BASE,
                clip_name=CLIP_8B,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
        (
            QUALITY_MAX,
            KLEIN_DISTILLED,
            (KLEIN_DISTILLED, FLUX2_DEV),
            QualityOverlay(
                steps=FLUX2_DEV_STEPS,
                cfg=FLUX2_DEV_CFG,
                unet_name=FLUX2_DEV,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
        (
            QUALITY_FREE_COMMERCIAL,
            KLEIN_9B,
            (KLEIN_DISTILLED, KLEIN_BASE, KLEIN_9B, KLEIN_9B_BASE, FLUX2_DEV),
            QualityOverlay(
                steps=KLEIN_HIGH_BASE_STEPS,
                cfg=KLEIN_HIGH_BASE_CFG,
                unet_name=KLEIN_BASE,
                clip_type=CLIP_TYPE_FLUX2,
            ),
        ),
    ]
    for quality, unet_name, unets, expected in cases:
        got = resolve_overlay(
            occupancy="klein",
            quality=quality,
            authored_steps=20,
            authored_cfg=2.5,
            unet_name=unet_name,
            available_unets=unets,
            clip_name=CLIP_4B,
            available_clips=(CLIP_4B, CLIP_8B),
            vae_name=VAE_FULL,
            available_vaes=(VAE_FULL,),
        )
        assert got == expected, (quality, unet_name)


def test_flux3_check_needs_are_per_profile() -> None:
    rows = {
        quality: {
            need.pack: need
            for need in requirements_for(
                CheckHints(lab_rel="stills/flux3", occupancy="klein", quality=quality)
            )
        }
        for quality in FLUX3_QUALITY_CHOICES
    }
    fast = rows[QUALITY_FLUX3_FAST]
    assert fast["flux3-fast-unet"].cmd == CMD_IMAGE_FLUX3
    assert fast["flux3-fast-unet"].files == (FileSpec(SUB_UNET, KLEIN3_DISTILLED),)
    quality_need = rows[QUALITY_FLUX3_QUALITY]
    assert quality_need["flux3-quality-unet"].cmd == CMD_IMAGE_FLUX3_BASE
    assert quality_need["flux3-quality-unet"].files == (FileSpec(SUB_UNET, KLEIN3_BASE),)
    nvfp4 = rows[QUALITY_FLUX3_NVFP4]
    assert nvfp4["flux3-nvfp4-unet"].cmd == CMD_IMAGE_FLUX3_NVFP4
    assert nvfp4["flux3-nvfp4-unet"].files == (FileSpec(SUB_UNET, KLEIN3_NVFP4),)
    for quality_rows in rows.values():
        assert quality_rows["flux3-te"].cmd == CMD_IMAGE_FLUX3_TE
        assert quality_rows["flux3-te"].files == (FileSpec(SUB_CLIP, KLEIN3_TE),)
        assert quality_rows["flux3-vae"].cmd == CMD_DOWNLOAD_MODELS
        assert quality_rows["flux3-vae"].files == (FileSpec(SUB_VAE, VAE_FULL),)
    for probe in (QUALITY_LAB, QUALITY_ULTRA, QUALITY_MAX, QUALITY_FREE_COMMERCIAL):
        packs = [
            need.pack
            for need in requirements_for(
                CheckHints(occupancy="klein", quality=probe)
            )
        ]
        assert not [pack for pack in packs if pack.startswith("flux3")], probe
    other_occ = requirements_for(
        CheckHints(occupancy="wan", quality=QUALITY_FLUX3_FAST)
    )
    assert not [need for need in other_occ if need.pack.startswith("flux3")]
    pinned = requirements_for(
        CheckHints(quality=QUALITY_FLUX3_NVFP4, unets=(KLEIN3_NVFP4,))
    )
    assert [need.pack for need in pinned if need.pack.startswith("flux3")] == [
        "flux3-nvfp4-unet",
        "flux3-te",
        "flux3-vae",
    ]


def test_command_for_filename_maps_flux3_files_without_moving_others() -> None:
    assert command_for_filename(KLEIN3_DISTILLED) == CMD_IMAGE_FLUX3
    assert command_for_filename(KLEIN3_BASE) == CMD_IMAGE_FLUX3_BASE
    assert command_for_filename(KLEIN3_NVFP4) == CMD_IMAGE_FLUX3_NVFP4
    assert command_for_filename(KLEIN3_TE) == CMD_IMAGE_FLUX3_TE
    assert command_for_filename(KLEIN3_UPSAMPLER) == CMD_IMAGE_FLUX3_PUP
    assert command_for_filename(KLEIN_DISTILLED) == CMD_DOWNLOAD_MODELS
    assert command_for_filename(VAE_FULL) == CMD_DOWNLOAD_MODELS
    assert command_for_filename(KLEIN_9B) == CMD_IMAGE_9B
    assert command_for_filename(KLEIN_9B_BASE) == CMD_IMAGE_9B_BASE
    assert command_for_filename(FLUX2_DEV) == CMD_IMAGE_FLUX2_DEV


def test_scan_flux3_quality_profile_missing_then_present(tmp_path: Path) -> None:
    hints = CheckHints(
        lab_rel="stills/flux3",
        occupancy="klein",
        quality=QUALITY_FLUX3_QUALITY,
        unets=(KLEIN3_BASE,),
        clips=(KLEIN3_TE,),
        vaes=(VAE_FULL,),
    )
    missing = scan(hints, (tmp_path,))
    missing_names = {row.name for row in missing.missing}
    assert KLEIN3_BASE in missing_names
    assert KLEIN3_TE in missing_names
    assert VAE_FULL in missing_names
    assert CMD_IMAGE_FLUX3_BASE in missing.commands
    assert CMD_IMAGE_FLUX3_TE in missing.commands
    for subdir, name in (
        (SUB_UNET, KLEIN3_BASE),
        (SUB_UNET, KLEIN_DISTILLED),
        (SUB_CLIP, KLEIN3_TE),
        (SUB_CLIP, CLIP_4B),
        (SUB_VAE, VAE_FULL),
    ):
        folder = tmp_path / "comfy" / subdir
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(b"x")
    found = scan(hints, (tmp_path,))
    present_names = {row.name for row in found.present}
    assert KLEIN3_BASE in present_names
    assert KLEIN3_TE in present_names
    assert VAE_FULL in present_names
    assert not [row for row in found.missing if row.pack.startswith("flux3")]
    assert found.ok


@pytest.mark.parametrize("choice", QUALITY_CHOICES)
def test_js_mirrors_every_quality_choice(choice: str) -> None:
    assert choice in JS.read_text(encoding="utf-8")


def test_js_mirrors_flux3_constants_and_predicates() -> None:
    body = JS.read_text(encoding="utf-8")
    for name in (*KLEIN3_ALL, KLEIN3_TE):
        assert name in body
    for choice in FLUX3_QUALITY_CHOICES:
        assert choice in body
    assert "function isKlein3Unet" in body
    assert "function isKlein3Clip" in body
    assert "firstClipName" in body
    assert f"const KLEIN3_FAST_STEPS = {KLEIN3_FAST_STEPS};" in body
    assert f"const KLEIN3_FAST_CFG = {KLEIN3_FAST_CFG};" in body
    assert f"const KLEIN3_QUALITY_STEPS = {KLEIN3_QUALITY_STEPS};" in body
    assert f"const KLEIN3_QUALITY_CFG = {KLEIN3_QUALITY_CFG};" in body
    assert f"const KLEIN3_NVFP4_STEPS = {KLEIN3_NVFP4_STEPS};" in body
    assert f"const KLEIN3_NVFP4_CFG = {KLEIN3_NVFP4_CFG};" in body

