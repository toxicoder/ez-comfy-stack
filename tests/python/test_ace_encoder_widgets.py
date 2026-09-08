"""Native ACE-Step 1.5 encoder widgets_values stay aligned with v0.34.0."""

from __future__ import annotations

import json
from pathlib import Path

from _ace_widgets_contract import assert_ace_encoder_widgets, iter_ace_encoders
from _lab_paths import lab_example_paths, lab_json

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_lab_ace_encoder_has_seed_control_and_valid_combos() -> None:
    seen = 0
    for path in lab_example_paths():
        graph = _load(path)
        gid = str(graph.get("id") or path.stem)
        for node in iter_ace_encoders(graph):
            seen += 1
            title = str(node.get("title") or node.get("id"))
            assert_ace_encoder_widgets(node, where=f"{gid}:{title}")
    assert seen >= 1, "expected at least one TextEncodeAceStepAudio1.5 in lab graphs"


def test_music_rap_encoder_keeps_vocal_codes_and_c_minor() -> None:
    for stem, duration in (
        ("music-rap-draft-lab-example", 32.0),
        ("music-rap-full-lab-example", 96.0),
    ):
        graph = _load(lab_json(stem))
        enc = next(iter_ace_encoders(graph))
        widgets = assert_ace_encoder_widgets(enc, where=stem)
        assert widgets[3] == "fixed"
        assert widgets[4] == 88
        assert widgets[5] == duration
        assert widgets[6] == "4"
        assert widgets[7] == "en"
        assert widgets[8] == "C minor"
        assert widgets[9] is True


def test_podcast_ace_encoders_keep_instrumental_codes_off() -> None:
    for stem in ("podcast-audio-first-lab-example", "podcast-radio-drama-lab-example"):
        graph = _load(lab_json(stem))
        encoders = list(iter_ace_encoders(graph))
        assert encoders, stem
        for node in encoders:
            widgets = assert_ace_encoder_widgets(node, where=f"{stem}:{node.get('title')}")
            assert widgets[3] == "fixed"
            assert widgets[6] == "4"
            assert widgets[7] == "en"
            assert widgets[8] == "C major"
            assert widgets[9] is False
