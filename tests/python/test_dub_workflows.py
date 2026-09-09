"""US-safe dub lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]

DISCLOSURE = (
    "This audio is an AI-translated dub. Voices are synthesized from the "
    "original speakers with the rights-holder's authorization."
)
BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "F5-TTS",
    "XTTS",
    "Fish Audio",
    "Rogan",
    "Ramsay",
    "TTS-Audio-Suite",
    "OldTimeRadio",
    "ElevenLabs",
    "Wav2Lip",
    "NLLB",
    "SeamlessM4T",
)


def _load(stem: str) -> dict:
    path = lab_json(stem)
    assert path.is_file(), stem
    return json.loads(path.read_text(encoding="utf-8"))


def _app_names(graph: dict) -> list[str]:
    return [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]


def _app_labels(graph: dict) -> list[str]:
    labels: list[str] = []
    for entry in graph["extra"]["linearData"]["inputs"]:
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    return labels


def test_dub_localize_graph() -> None:
    graph = _load("dub-localize-lab-example")
    assert graph["id"] == "dub-localize-lab-example"
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-dub"
    assert extra["lab_app_mode"]["occupancy"] == "audio"
    assert extra["lab_app_mode"]["lane"] == "audio"
    assert extra["lab_app_mode"]["default_view"] == "app"
    blob = json.dumps(graph)
    for prefix in ("ez_dub_mix", "ez_dub_yt", "ez_dub_script", "ez_dub_ingest"):
        assert prefix in blob, prefix
    assert DISCLOSURE in blob
    assert "I have rights" in blob or "have_rights" in blob
    ingest = next(n for n in graph["nodes"] if n["type"] == "EZDubIngest")
    assert ingest["widgets_values"][0] == "(none)"
    assert ingest["widgets_values"][1] is False
    assert ingest["widgets_values"][3] == ""
    script = next(n for n in graph["nodes"] if n["type"] == "EZDubScript")
    assert script["widgets_values"][1] is True
    assert script["widgets_values"][2] == "es"
    render = next(n for n in graph["nodes"] if n["type"] == "EZDubRender")
    assert render["widgets_values"][0] == "chatterbox-ml"
    flac = next(n for n in graph["nodes"] if n["type"] == "SaveAudio")
    assert flac["widgets_values"][0] == "ez_dub_mix"
    mp3 = next(n for n in graph["nodes"] if n["type"] == "SaveAudioMP3")
    assert mp3["widgets_values"][0] == "ez_dub_yt"
    titles = {g["title"] for g in graph["groups"]}
    assert "INPUT" in titles
    assert "PROMPT" in titles
    assert "OUTPUT" in titles
    for needle in BANNED:
        assert needle not in blob, needle
    names = _app_names(graph)
    assert names[0] == "source"
    assert "upload" in names
    assert "source_url" in names
    assert "have_rights" in names
    assert "target_language" in names
    labels = _app_labels(graph)
    assert "Source file" in labels
    assert "Upload media" in labels
    assert "Source URL" in labels
    assert "I have rights" in labels
    assert "Target language" in labels
    assert "Translation" in labels or "Rewrite translation" in labels
    assert len(labels) == len(set(labels)), labels
    note = graph["extra"]["lab_note"]
    assert "Source file" in note
    assert "Upload media" in note
