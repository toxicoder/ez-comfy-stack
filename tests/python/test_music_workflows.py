"""US-safe rap lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "minimax_h3",
    "Suno",
    "Udio",
    "Drake",
    "Kendrick",
    "Eminem",
    "F5",
    "XTTS",
    "Fish",
    "TTS-Audio-Suite",
    "OldTimeRadio",
    "XAI_API_KEY",
)


def _load(stem: str) -> dict:
    path = WF / f"{stem}.json"
    assert path.is_file(), stem
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_shared(graph: dict, stem: str, prefix: str, duration: float) -> None:
    assert graph["id"] == stem
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-music"
    assert extra["lab_note"].strip()
    assert extra["lab_description"].strip()
    titles = {g["title"] for g in graph["groups"]}
    assert titles == {"MODEL", "DURATION", "PROMPT", "OUTPUT"}
    blob = json.dumps(graph)
    assert prefix in blob
    assert "[verse]" in blob
    assert "[chorus]" in blob
    for needle in BANNED:
        assert needle not in blob, (stem, needle)
    ckpt = next(n for n in graph["nodes"] if n["type"] == "CheckpointLoaderSimple")
    assert ckpt["widgets_values"][0] == "ace_step_1.5_turbo_aio.safetensors"
    assert any(n["type"] == "ModelSamplingAuraFlow" for n in graph["nodes"])
    assert any(n["type"] == "ConditioningZeroOut" for n in graph["nodes"])
    assert any(n["type"] == "PrimitiveNode" for n in graph["nodes"])
    prim = next(n for n in graph["nodes"] if n["type"] == "PrimitiveNode")
    assert prim["widgets_values"][0] == duration
    enc = next(n for n in graph["nodes"] if n["type"] == "TextEncodeAceStepAudio1.5")
    widgets = enc["widgets_values"]
    assert widgets[3] == 88
    assert widgets[4] == duration
    assert widgets[5] == "4"
    assert widgets[6] == "en"
    assert widgets[8] is True
    sampler = next(n for n in graph["nodes"] if n["type"] == "KSampler")
    sw = sampler["widgets_values"]
    assert sw[2] == 8
    assert sw[3] in (1, 1.0)
    assert sw[4] == "euler"
    assert sw[5] == "simple"
    flac = next(n for n in graph["nodes"] if n["type"] == "SaveAudio")
    assert flac["widgets_values"][0] == prefix
    mp3 = next(n for n in graph["nodes"] if n["type"] == "SaveAudioMP3")
    assert mp3["widgets_values"][0] == prefix
    lyrics = next(n for n in graph["nodes"] if n["type"] == "EZRapLyrics")
    assert lyrics["widgets_values"][1] is False
    assert "Note" in {n["type"] for n in graph["nodes"]}
    assert "klein-thumbnail-lab-example" in extra["lab_note"]
    assert "klein-podcast-cover-lab-example" in extra["lab_note"]


def test_music_rap_draft_graph() -> None:
    graph = _load("music-rap-draft-lab-example")
    _assert_shared(graph, "music-rap-draft-lab-example", "ez_rap_draft", 32.0)
    note = graph["extra"]["lab_note"].lower()
    assert "instrumental" in note
    assert "[inst]" in graph["extra"]["lab_note"]
    assert "no vocals" in note
    assert "boom-bap" in note or "boom bap" in note


def test_music_rap_full_graph() -> None:
    graph = _load("music-rap-full-lab-example")
    _assert_shared(graph, "music-rap-full-lab-example", "ez_rap_full", 96.0)
    blob = json.dumps(graph)
    assert "[outro]" in blob
    assert blob.count("[chorus]") >= 2
