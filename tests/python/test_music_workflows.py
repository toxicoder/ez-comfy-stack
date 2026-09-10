"""US-safe rap lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

from ez_music.diss_examples import DISS_EXAMPLES
from ez_music.edm_examples import EDM_EXAMPLES

from _ace_widgets_contract import assert_ace_encoder_widgets
from _lab_paths import LAB_ROOT, lab_json
from _stamp_app_mode import (
    DRIVE_THROUGH_STAMP_STEMS,
    NILL_BYE_STAMP_STEMS,
    STAMP_SPECS,
)

ROOT = Path(__file__).resolve().parents[2]

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
    path = lab_json(stem)
    assert path.is_file(), stem
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_shared(
    graph: dict,
    stem: str,
    prefix: str,
    duration: float,
    *,
    bpm: int = 88,
    seed: int = 42,
    tags: str | None = None,
    ace_mode: str = "vocal",
    edm_vocal_treat: bool = False,
) -> None:
    assert graph["id"] == stem
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-music"
    assert extra["lab_note"].strip()
    assert extra["lab_description"].strip()
    titles = {g["title"] for g in graph["groups"]}
    assert titles == {"MODEL", "DURATION", "PROMPT", "OUTPUT"}
    blob = json.dumps(graph)
    assert prefix in blob
    if ace_mode == "vocal" and edm_vocal_treat:
        assert "[chorus]" in blob
        assert "[inst]" in blob
        assert "[verse]" not in blob
    elif ace_mode == "vocal":
        assert "[verse]" in blob
        assert "[chorus]" in blob
    else:
        assert "[inst]" in blob
        assert "[outro]" in blob
        assert "[verse]" not in blob
        assert "[chorus]" not in blob
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
    widgets = assert_ace_encoder_widgets(enc, where=stem)
    assert widgets[2] == seed
    assert widgets[3] == "fixed"
    assert widgets[4] == bpm
    assert widgets[5] == duration
    assert widgets[6] == "4"
    assert widgets[7] == "en"
    assert widgets[8] == "C minor"
    assert widgets[9] is True
    sampler = next(n for n in graph["nodes"] if n["type"] == "KSampler")
    sw = sampler["widgets_values"]
    assert sw[0] == seed
    assert sw[2] == 8
    assert sw[3] in (1, 1.0)
    assert sw[4] == "euler"
    assert sw[5] == "simple"
    flac = next(n for n in graph["nodes"] if n["type"] == "SaveAudio")
    assert flac["widgets_values"][0] == prefix
    mp3 = next(n for n in graph["nodes"] if n["type"] == "SaveAudioMP3")
    assert mp3["widgets_values"][0] == prefix
    ace = next(n for n in graph["nodes"] if n["type"] == "EZAceStepPromptEnhance")
    assert ace["widgets_values"][2] is False
    assert ace["widgets_values"][3] == ace_mode
    if tags is not None:
        assert ace["widgets_values"][0] == tags
        assert widgets[0] == tags
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


def test_music_rap_nill_bye_diss_graphs() -> None:
    assert len(DISS_EXAMPLES) == 45
    assert tuple(ex["stem"] for ex in DISS_EXAMPLES) == NILL_BYE_STAMP_STEMS
    for ex in DISS_EXAMPLES:
        stem = ex["stem"]
        graph = _load(stem)
        _assert_shared(
            graph,
            stem,
            ex["prefix"],
            float(ex["duration"]),
            bpm=int(ex["bpm"]),
            seed=int(ex["seed"]),
            tags=ex["tags"],
        )
        blob = json.dumps(graph)
        assert "[outro]" in blob
        assert "Nill Bye" in blob
        assert "Rake" in blob
        assert blob.count("[chorus]") >= 3
        note = graph["extra"]["lab_note"]
        assert "180" in note
        assert "on its own" in note.lower() or "queue on its own" in note.lower()
        if ex["title"] in {"peer review", "grant denied", "story time"}:
            assert "[spoken word]" in blob
        rel = lab_json(stem).relative_to(LAB_ROOT)
        assert rel.parts[:3] == ("audio", "nill-bye", f"phase{ex['phase']}")


def test_nill_bye_stems_are_stamped_audio() -> None:
    stems = {ex["stem"] for ex in DISS_EXAMPLES}
    assert stems <= set(STAMP_SPECS)
    for stem in stems:
        assert STAMP_SPECS[stem]["lane"] == "audio"
        assert STAMP_SPECS[stem]["occupancy"] == "audio"


COLUMN_NODE_POS = (
    (1, 40.0, 80.0),
    (2, 40.0, 220.0),
    (3, 40.0, 380.0),
    (4, 40.0, 520.0),
    (5, 500.0, 80.0),
    (6, 500.0, 520.0),
    (7, 940.0, 80.0),
    (8, 940.0, 180.0),
    (9, 1340.0, 80.0),
    (10, 1340.0, 180.0),
    (11, 1340.0, 300.0),
    (12, 1340.0, 440.0),
)


def _node_fingerprint(graph: dict) -> tuple[tuple[int, float, float], ...]:
    nodes = sorted(graph["nodes"], key=lambda node: int(node["id"]))
    return tuple(
        (int(node["id"]), float(node["pos"][0]), float(node["pos"][1]))
        for node in nodes
    )


def test_music_edm_drive_through_graphs() -> None:
    assert len(EDM_EXAMPLES) == 85
    assert tuple(ex["stem"] for ex in EDM_EXAMPLES) == DRIVE_THROUGH_STAMP_STEMS
    for ex in EDM_EXAMPLES:
        stem = ex["stem"]
        graph = _load(stem)
        treat = ex["ace_mode"] == "vocal"
        _assert_shared(
            graph,
            stem,
            ex["prefix"],
            float(ex["duration"]),
            bpm=int(ex["bpm"]),
            seed=int(ex["seed"]),
            tags=ex["tags"],
            ace_mode=ex["ace_mode"],
            edm_vocal_treat=treat,
        )
        blob = json.dumps(graph)
        assert "Drive-through" in blob
        assert "[verse]" not in blob
        note = graph["extra"]["lab_note"]
        assert "180" in note
        assert "on its own" in note.lower() or "queue on its own" in note.lower()
        assert "rave" in note.lower() or "live" in note.lower()
        if treat:
            assert "vocal" in note.lower()
            assert blob.lower().count("[chorus]") >= 1
        else:
            assert "instrumental" in note.lower()
            assert "[chorus]" not in blob
        ace = next(n for n in graph["nodes"] if n["type"] == "EZAceStepPromptEnhance")
        assert ace["title"] == "ez_edm_prompt"
        rel = lab_json(stem).relative_to(LAB_ROOT)
        assert rel.parts[:3] == ("audio", "drive-through", f"phase{ex['phase']}")


def test_drive_through_phase2_layouts_vary() -> None:
    fingerprints: set[tuple[tuple[int, float, float], ...]] = set()
    for ex in EDM_EXAMPLES:
        graph = _load(ex["stem"])
        fingerprint = _node_fingerprint(graph)
        if ex["phase"] < 2:
            assert fingerprint == COLUMN_NODE_POS, ex["stem"]
        else:
            fingerprints.add(fingerprint)
    assert len(fingerprints) >= 5


def test_drive_through_stems_are_stamped_audio() -> None:
    stems = {ex["stem"] for ex in EDM_EXAMPLES}
    assert stems <= set(STAMP_SPECS)
    for stem in stems:
        assert STAMP_SPECS[stem]["lane"] == "audio"
        assert STAMP_SPECS[stem]["occupancy"] == "audio"
        assert STAMP_SPECS[stem]["ace_instrumental_score"] is True


def test_music_apps_expose_duration_and_vocal_mode() -> None:
    stems = [
        "music-rap-draft-lab-example",
        "music-rap-full-lab-example",
        *[ex["stem"] for ex in DISS_EXAMPLES],
        *[ex["stem"] for ex in EDM_EXAMPLES],
    ]
    for stem in stems:
        graph = _load(stem)
        names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
        assert "seconds" in names, stem
        assert "mode" in names, stem
        assert "backend" not in names, stem
        labels = [
            ((entry[2] or {}).get("label") if len(entry) > 2 else None) or entry[1]
            for entry in graph["extra"]["linearData"]["inputs"]
        ]
        assert "Duration (seconds)" in labels, stem
        assert "Vocal / instrumental" in labels, stem
