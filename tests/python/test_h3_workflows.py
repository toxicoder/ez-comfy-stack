"""Parse and assert MiniMax H3 90s lab graphs (challenge cap 90.00s).

Hermetic: stdlib json only. No Comfy runtime, network, or GPU.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WF_DIR = ROOT / "workflows"
API_PATH = WF_DIR / "api" / "h3-shot-column.api.json"

FILMS = (
    ("h3-go-see-90s-lab-example.json", "video/GO_SEE_90s_H3"),
    ("h3-still-here-90s-lab-example.json", "video/STILL_HERE_90s_H3"),
    ("h3-switchyard-90s-lab-example.json", "video/SWITCHYARD_90s_H3"),
)

WEIGHTS = (
    "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "minimax_h3_video_vae_fp16.safetensors",
    "minimax_h3_audio_vae_fp32.safetensors",
)

FORBIDDEN_CUSTOM = (
    "H3MotionContext",
    "H3MotionContextTrim",
    "NikoDemon80",
)

API_PLACEHOLDERS = (
    "__PROMPT__",
    "__SEED__",
    "__FIRST_FRAME_PATH__",
    "__GUIDE_AUDIO_PATH__",
    "__LENGTH__",
    "__WIDTH__",
    "__HEIGHT__",
)


def _load(name: str) -> dict:
    path = WF_DIR / name
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _nodes_of(data: dict, ntype: str) -> list[dict]:
    return [n for n in data["nodes"] if n.get("type") == ntype]


def _widget_has(node: dict, value) -> bool:
    wv = node.get("widgets_values") or []
    named = node.get("widgets_values_named") or {}
    return value in wv or value in named.values()


@pytest.mark.parametrize("filename,prefix", FILMS)
def test_h3_lab_graph_challenge_contract(filename: str, prefix: str) -> None:
    data = _load(filename)
    stem = Path(filename).stem
    assert data.get("id") == stem

    i2v = _nodes_of(data, "MiniMaxH3ImageToVideo")
    assert len(i2v) == 6, filename
    for node in i2v:
        wv = node.get("widgets_values") or []
        named = node.get("widgets_values_named") or {}
        length = named.get("length", wv[3] if len(wv) > 3 else None)
        width = named.get("width", wv[1] if len(wv) > 1 else None)
        height = named.get("height", wv[2] if len(wv) > 2 else None)
        assert length == 379, (filename, node.get("id"), length)
        assert width == 1344, (filename, width)
        assert height == 768, (filename, height)
        assert 2164 not in wv and 2160 not in wv

    guides = _nodes_of(data, "MiniMaxH3AddGuide")
    assert len(guides) == 5, filename
    for node in guides:
        wv = node.get("widgets_values") or []
        named = node.get("widgets_values_named") or {}
        idx = named.get("frame_idx", wv[0] if wv else None)
        assert idx == 0, (filename, node.get("id"), idx)

    for ntype in ("MiniMaxH3ImageToVideo", "MiniMaxH3AddGuide", "MiniMaxH3SigmaShift"):
        for node in _nodes_of(data, ntype):
            props = node.get("properties") or {}
            assert props.get("cnr_id") == "comfy-core", (filename, ntype, node.get("id"))
            assert str(props.get("ver", "")).startswith("0.34"), (filename, ntype)

    blob = json.dumps(data)
    for weight in WEIGHTS:
        assert weight in blob, weight
    assert '"minimax"' in blob

    saves = _nodes_of(data, "SaveVideo")
    assert len(saves) == 1, filename
    assert _widget_has(saves[0], prefix)

    create = _nodes_of(data, "CreateVideo")
    assert len(create) == 1, filename
    fps = (create[0].get("widgets_values_named") or {}).get("fps")
    if fps is None:
        fps = (create[0].get("widgets_values") or [None])[0]
    assert float(fps) == 24.0

    cap_frames = [
        n
        for n in _nodes_of(data, "ImageFromBatch")
        if _widget_has(n, 2160)
    ]
    assert cap_frames, f"{filename}: missing ImageFromBatch keep of 2160 frames"

    audio_caps = [
        n
        for n in _nodes_of(data, "TrimAudioDuration")
        if _widget_has(n, 90.0) or _widget_has(n, 90)
    ]
    assert audio_caps, f"{filename}: missing TrimAudioDuration 90.00s cap"

    assert _nodes_of(data, "AudioConcat"), filename
    assert _nodes_of(data, "ImageBatch"), filename
    assert _nodes_of(data, "MiniMaxH3SigmaShift"), filename
    assert _nodes_of(data, "MarkdownNote") or _nodes_of(data, "Note")

    note = data.get("extra", {}).get("lab_note", "")
    assert isinstance(note, str) and note.strip()
    assert "90.00" in note or "90.0" in note
    assert "native" in note.lower() and "audio" in note.lower()
    assert "2160" in note

    types = {n.get("type") for n in data["nodes"]}
    for forbidden in FORBIDDEN_CUSTOM:
        assert forbidden not in types, forbidden

    load_audio = _nodes_of(data, "LoadAudio")
    assert not load_audio, f"{filename}: default graph must not LoadAudio a soundtrack"

    types = {n.get("type") for n in data["nodes"]}
    assert "VHS_VideoCombine" not in types


def test_go_see_identity_not_diluted() -> None:
    data = _load("h3-go-see-90s-lab-example.json")
    prompts = []
    for node in _nodes_of(data, "MiniMaxH3ImageToVideo"):
        wv = node.get("widgets_values") or []
        named = node.get("widgets_values_named") or {}
        text = named.get("prompt", wv[0] if wv else "")
        assert isinstance(text, str) and len(text) > 80
        prompts.append(text.lower())
    joined = "\n".join(prompts)
    assert "first-person" in joined or "first person" in joined
    assert "olive" in joined and "windbreaker" in joined
    assert "gloves" in joined
    assert "parkour" in joined or "vault" in joined or "barrel roll" in joined
    assert "lighthouse" in joined
    assert "quiet laugh" in joined or "quiet, short laugh" in joined
    for banned in ("trailer", "score swelling", "orchestral", "copyright"):
        assert banned not in joined


def test_api_shot_column_placeholders() -> None:
    assert API_PATH.is_file(), API_PATH
    data = json.loads(API_PATH.read_text(encoding="utf-8"))
    blob = json.dumps(data)
    for token in API_PLACEHOLDERS:
        assert token in blob, token
    assert "MiniMaxH3ImageToVideo" in blob
    assert "minimax_h3_fl2va_pruned_int8_convrot.safetensors" in blob
    assert "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors" in blob
