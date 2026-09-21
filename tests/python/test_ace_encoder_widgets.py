"""Native ACE-Step 1.5 encoder widgets_values stay aligned with v0.37.0."""

from __future__ import annotations

import json
from pathlib import Path

from ez_music.diss_examples import DISS_EXAMPLES
from ez_music.edm_examples import EDM_EXAMPLES
from ez_music.song_plan import demo_draft_seconds, demo_full_seconds

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
    cases: list[tuple[str, float, int, str, str]] = [
        ("audio/music/rap-draft", float(demo_draft_seconds()), 88, "4", "C minor"),
        ("audio/music/rap-full", float(demo_full_seconds()), 88, "4", "C minor"),
    ]
    for diss in DISS_EXAMPLES:
        cases.append(
            (
                diss["stem"],
                float(diss["duration"]),
                int(diss["bpm"]),
                str(diss["meter"]),
                str(diss["keyscale"]),
            )
        )
    for edm in EDM_EXAMPLES:
        cases.append(
            (
                edm["stem"],
                float(edm["duration"]),
                int(edm["bpm"]),
                str(edm["meter"]),
                str(edm["keyscale"]),
            )
        )
    for stem, duration, bpm, meter, keyscale in cases:
        graph = _load(lab_json(stem))
        enc = next(iter_ace_encoders(graph))
        widgets = assert_ace_encoder_widgets(enc, where=stem)
        assert widgets[3] == "fixed"
        assert widgets[4] == bpm
        assert widgets[5] == duration
        assert widgets[6] == meter
        expect_lang = "en"
        row = next((ex for ex in EDM_EXAMPLES if ex["stem"] == stem), None)
        if row is not None and row["ace_mode"] == "instrumental":
            expect_lang = "unknown"
        assert widgets[7] == expect_lang
        assert widgets[8] == keyscale
        assert widgets[9] is True


def test_podcast_ace_encoders_keep_instrumental_codes_off() -> None:
    for stem in (
        "audio/podcast/two-host-episode",
        "audio/podcast/radio-drama",
        "audio/podcast/learn-episode",
    ):
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
