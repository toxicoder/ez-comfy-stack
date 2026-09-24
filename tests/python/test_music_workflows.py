"""US-safe rap lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

from ez_music.diss_examples import DISS_EXAMPLES
from ez_music.edm_examples import EDM_EXAMPLES
from ez_music.song_plan import demo_draft_seconds, demo_full_seconds

from _ace_widgets_contract import assert_ace_encoder_widgets
from _lab_paths import LAB_ROOT, lab_json
from _stamp_app_mode import (
    DRIVE_THROUGH_STAMP_STEMS,
    NILL_BYE_STAMP_STEMS,
    NODE_MODE_BYPASS,
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
    meter: str = "4",
    keyscale: str = "C minor",
) -> None:
    assert graph["id"] == Path(stem).name
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-music"
    assert extra["lab_note"].strip()
    assert extra["lab_description"].strip()
    titles = {g["title"] for g in graph["groups"]}
    assert {"MODEL", "DURATION", "PROMPT", "OUTPUT"} <= titles
    assert {"NOTE", "QUALITY"} <= titles
    blob = json.dumps(graph)
    assert prefix in blob
    if ace_mode == "vocal" and edm_vocal_treat:
        assert "[chorus]" in blob
        assert "[inst" in blob or "[drop" in blob
        assert "[verse]" not in blob
    elif ace_mode == "vocal":
        assert "[verse]" in blob
        assert "[chorus]" in blob
    else:
        assert "[inst" in blob or "[drop" in blob
        assert "[outro" in blob
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
    assert widgets[6] == meter
    assert widgets[7] == ("unknown" if ace_mode == "instrumental" else "en")
    assert widgets[8] == keyscale
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
    ace_w = ace["widgets_values"]
    if len(ace_w) >= 6:
        assert ace_w[3] is False
        assert ace_w[4] == ace_mode
        if tags is not None:
            assert ace_w[1] == tags
    else:
        assert ace_w[2] is False
        assert ace_w[3] == ace_mode
        if tags is not None:
            assert ace_w[0] == tags
        assert widgets[0] == tags
    assert "Note" in {n["type"] for n in graph["nodes"]}
    assert "stills/thumbnail" in extra["lab_note"]
    assert "stills/podcast-cover" in extra["lab_note"]
    assert extra.get("lab_album")
    assert extra["lab_album"]["art_mode"] in {"skip", "upload", "generate"}
    assert any(n["type"] == "EZAudioMetadata" for n in graph["nodes"])


def test_music_rap_draft_graph() -> None:
    graph = _load("audio/music/rap-draft")
    _assert_shared(graph, "rap-draft", "ez_rap_draft", float(demo_draft_seconds()))
    note = graph["extra"]["lab_note"].lower()
    assert "instrumental" in note
    assert "[inst]" in graph["extra"]["lab_note"]
    assert "no vocals" in note
    assert "boom-bap" in note or "boom bap" in note


def test_music_rap_full_graph() -> None:
    graph = _load("audio/music/rap-full")
    _assert_shared(graph, "rap-full", "ez_rap_full", float(demo_full_seconds()))
    blob = json.dumps(graph)
    assert "[outro]" in blob
    assert "[pre-chorus]" in blob
    assert blob.count("[chorus]") >= 2


def test_music_rap_nill_bye_diss_graphs() -> None:
    assert len(DISS_EXAMPLES) == 135
    assert tuple(ex["rel"] for ex in DISS_EXAMPLES) == NILL_BYE_STAMP_STEMS
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
            meter=str(ex["meter"]),
            keyscale=str(ex["keyscale"]),
        )
        blob = json.dumps(graph)
        assert "[outro]" in blob
        assert "Nill Bye" in blob
        if ex["series"] in {"civic", "civic-club"}:
            assert "Abbott" in blob
            assert "Rake" not in blob
        elif ex["series"] in {"federal", "federal-club"}:
            assert "Trump" in blob
            assert "Rake" not in blob
            assert "Abbott" not in blob
        elif ex["series"] in {"progress", "progress-club"}:
            assert "Rake" not in blob
            assert "Abbott" not in blob
            assert "Trump" not in blob
            assert "progress" in graph["extra"]["lab_note"].lower()
            assert " diss" not in graph["extra"]["lab_note"].lower()
        else:
            assert "Rake" in blob
        assert "[chorus]" in blob or "[chorus -" in blob
        note = graph["extra"]["lab_note"]
        assert str(int(ex["duration"])) in note
        assert ex["form_id"] in note
        assert ex["keyscale"] in note
        assert "on its own" in note.lower() or "queue on its own" in note.lower()
        if ex["title"] in {
            "peer review",
            "grant denied",
            "story time",
            "abject failure",
            "disaster stamp",
            "one eighty seven",
            "pardon flood",
            "registered report",
            "duty switch",
        }:
            assert "[spoken word]" in blob
        rel = lab_json(stem).relative_to(LAB_ROOT)
        assert rel.parts[:4] == ("audio", "albums", "nill-bye", ex["album_slug"])


def test_nill_bye_stems_are_stamped_audio() -> None:
    stems = {ex["rel"] for ex in DISS_EXAMPLES}
    assert stems <= set(STAMP_SPECS)
    for stem in stems:
        assert STAMP_SPECS[stem]["lane"] == "audio"
        assert STAMP_SPECS[stem]["occupancy"] == "audio"


COLUMN_NODE_POS = (
    (1, 40.0, 744.0),
    (2, 40.0, 916.0),
    (3, 40.0, 1092.0),
    (4, 2976.0, 744.0),
    (5, 500.0, 744.0),
    (6, 500.0, 1236.0),
    (7, 948.0, 744.0),
    (8, 948.0, 876.0),
    (9, 1340.0, 744.0),
    (10, 1340.0, 876.0),
    (11, 1340.0, 1218.0),
    (12, 40.0, 80.0),
)


def _node_fingerprint(graph: dict) -> tuple[tuple[int, float, float], ...]:
    nodes = sorted(graph["nodes"], key=lambda node: int(node["id"]))
    return tuple(
        (int(node["id"]), float(node["pos"][0]), float(node["pos"][1]))
        for node in nodes
    )


def test_music_edm_drive_through_graphs() -> None:
    assert len(EDM_EXAMPLES) == 101
    assert tuple(ex["rel"] for ex in EDM_EXAMPLES) == DRIVE_THROUGH_STAMP_STEMS
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
            meter=str(ex["meter"]),
            keyscale=str(ex["keyscale"]),
        )
        blob = json.dumps(graph)
        assert "Drive-through" in blob
        assert "[verse]" not in blob
        note = graph["extra"]["lab_note"]
        assert str(int(ex["duration"])) in note
        assert ex["form_id"] in note
        assert "on its own" in note.lower() or "queue on its own" in note.lower()
        assert "rave" in note.lower() or "live" in note.lower()
        if treat:
            assert "vocal" in note.lower()
            assert blob.lower().count("[chorus]") >= 1
        else:
            assert "instrumental" in note.lower()
            assert "[chorus]" not in blob
            ace_enc = next(
                n for n in graph["nodes"] if n["type"] == "TextEncodeAceStepAudio1.5"
            )
            assert ace_enc["widgets_values"][7] == "unknown"
        ace = next(n for n in graph["nodes"] if n["type"] == "EZAceStepPromptEnhance")
        assert ace["title"] == "ez_edm_prompt"
        rel = lab_json(stem).relative_to(LAB_ROOT)
        assert rel.parts[:4] == ("audio", "albums", "drive-through", ex["album_slug"])


def test_drive_through_phase2_layouts_vary() -> None:
    fingerprints: set[tuple[tuple[int, float, float], ...]] = set()
    for ex in EDM_EXAMPLES:
        graph = _load(ex["stem"])
        fingerprint = tuple(item for item in _node_fingerprint(graph) if item[0] <= 12)
        if ex["phase"] < 2:
            assert fingerprint == COLUMN_NODE_POS, ex["stem"]
        else:
            fingerprints.add(fingerprint)
    assert len(fingerprints) >= 5


def test_drive_through_stems_are_stamped_audio() -> None:
    stems = {ex["rel"] for ex in EDM_EXAMPLES}
    assert stems <= set(STAMP_SPECS)
    for stem in stems:
        assert STAMP_SPECS[stem]["lane"] == "audio"
        assert STAMP_SPECS[stem]["occupancy"] == "audio"
        assert STAMP_SPECS[stem]["ace_instrumental_score"] is True


def test_music_apps_expose_duration_and_vocal_mode() -> None:
    stems = [
        "audio/music/rap-draft",
        "audio/music/rap-full",
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
        assert "Album art" in labels, stem
        assert "Cover image" not in labels, stem
        assert "image" not in names, stem
        assert "Artist" in labels, stem
        assert "Album" in labels, stem
        load = next(n for n in graph["nodes"] if n["type"] == "LoadImage")
        assert load["title"] == "Cover image"
        assert int(load.get("mode") or 0) == NODE_MODE_BYPASS, stem
        image_out = next(
            out for out in load["outputs"] if str(out.get("name") or "").upper() == "IMAGE"
        )
        assert not image_out.get("links")
        meta = next(n for n in graph["nodes"] if n["type"] == "EZAudioMetadata")
        cover_in = next(inp for inp in meta["inputs"] if inp.get("name") == "cover")
        assert cover_in.get("link") is None
        assert meta["widgets_values"][6] == "skip"
