"""Audio-finish App: occupancy audio, no UNET, stem-mix handoff."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Wav2Lip")
HEAVY = ("UNETLoader", "VAELoader", "KSampler", "VAEDecode")


def test_audio_finish_app_contract() -> None:
    graph = json.loads(lab_json("audio-finish-lab-example.json").read_text(encoding="utf-8"))
    assert graph["id"] == "audio-finish-lab-example"
    types = {n.get("type") for n in graph["nodes"]}
    for heavy in HEAVY:
        assert heavy not in types
    assert "SaveAudio" in types
    extra = graph["extra"]
    assert extra["lab_app_mode"]["occupancy"] == "audio"
    assert extra["lab_app_mode"]["lane"] == "audio"
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob, needle
    assert "stem-mix" in extra["lab_note"]
    assert "I=-14" in extra["lab_note"] or "loudnorm" in extra["lab_note"]
    primitives = [n for n in graph["nodes"] if n.get("type") == "PrimitiveNode"]
    assert len(primitives) == 5
    titles = [n.get("title") for n in primitives]
    assert "Film slug" in titles
    assert "Include MX" in titles
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveAudio")
    assert save["widgets_values"][0] == "ez_stem_mix"
    assert extra["lab_app_mode"]["default_view"] == "app"
    assert "1280x720" not in blob and "1280×720" not in blob
