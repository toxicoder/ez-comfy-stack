"""US-safe podcast lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

from _ace_widgets_contract import assert_ace_encoder_widgets, iter_ace_encoders
from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]

DISCLOSURE = (
    "Voices and music on this show are synthesized. The hosts are original "
    "characters, not recordings of real people."
)
BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "minimax_h3",
    "F5-TTS",
    "XTTS",
    "Fish Audio",
    "Rogan",
    "Ramsay",
    "TTS-Audio-Suite",
    "OldTimeRadio",
    "ElevenLabs",
)


def _load(stem: str) -> dict:
    path = lab_json(stem)
    assert path.is_file(), stem
    return json.loads(path.read_text(encoding="utf-8"))


def test_audio_first_podcast_graph() -> None:
    graph = _load("podcast-audio-first-lab-example")
    assert graph["id"] == "podcast-audio-first-lab-example"
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-podcast"
    assert extra["lab_note"].strip()
    assert extra["lab_description"].strip()
    blob = json.dumps(graph)
    for prefix in (
        "ez_podcast_script",
        "ez_podcast_voice",
        "ez_podcast_bed",
        "ez_podcast_mix",
        "ez_podcast_ep",
    ):
        assert prefix in blob, prefix
    assert DISCLOSURE in blob
    assert "klein-podcast-cover-lab-example" in blob
    titles = {n.get("title") for n in graph["nodes"]}
    assert "MODEL" in {g["title"] for g in graph["groups"]}
    assert "PROMPT" in {g["title"] for g in graph["groups"]}
    assert "SETTINGS" in {g["title"] for g in graph["groups"]}
    assert "OUTPUT" in {g["title"] for g in graph["groups"]}
    script = next(n for n in graph["nodes"] if n["type"] == "EZPodcastScript")
    assert script["widgets_values"][1] is True
    assert any(n["type"] == "EZPodcastDisclosure" for n in graph["nodes"])
    assert any(n["type"] == "EZKokoroTTS" for n in graph["nodes"])
    ace = list(iter_ace_encoders(graph))
    assert ace
    for node in ace:
        assert_ace_encoder_widgets(node, where=f"podcast-audio-first:{node.get('title')}")
    pos = next(n for n in ace if "bed" in (n.get("title") or "").lower())
    tags, lyrics = pos["widgets_values"][0], pos["widgets_values"][1]
    assert "instrumental" in tags.lower()
    assert "no vocals" in tags.lower()
    assert lyrics == ""
    assert any(n["type"] == "EmptyAceStep1.5LatentAudio" for n in graph["nodes"])
    assert any(n["type"] == "AudioAdjustVolume" for n in graph["nodes"])
    duck = next(n for n in graph["nodes"] if n["type"] == "AudioAdjustVolume")
    assert duck["widgets_values"][0] <= -12
    assert duck["widgets_values"][0] >= -18
    flac = next(n for n in graph["nodes"] if n["type"] == "SaveAudio")
    assert flac["widgets_values"][0] == "ez_podcast_ep"
    mp3 = next(n for n in graph["nodes"] if n["type"] == "SaveAudioMP3")
    assert mp3["widgets_values"][0] == "ez_podcast_mix"
    assert mp3["widgets_values"][1] == "320k"
    assert "Note" in {n["type"] for n in graph["nodes"]}
    for needle in BANNED:
        assert needle not in blob, needle
    assert titles  # used
    ckpt = next(n for n in graph["nodes"] if n["type"] == "CheckpointLoaderSimple")
    assert ckpt["widgets_values"][0] == "ace_step_1.5_turbo_aio.safetensors"


def test_radio_drama_graph() -> None:
    graph = _load("podcast-radio-drama-lab-example")
    assert graph["id"] == "podcast-radio-drama-lab-example"
    extra = graph["extra"]
    assert extra["lab_profile"] == "us-safe-radio"
    blob = json.dumps(graph)
    for prefix in (
        "ez_radio_script",
        "ez_radio_voice",
        "ez_radio_bed",
        "ez_radio_sting",
        "ez_radio_mix",
        "ez_radio_ep",
        "ez_radio_bumper",
        "ez_radio_hook",
    ):
        assert prefix in blob, prefix
    assert DISCLOSURE in blob
    script = next(n for n in graph["nodes"] if n["type"] == "EZPodcastScript")
    assert script["widgets_values"][1] is True
    assert script["widgets_values"][2] == "radio_drama"
    tts = next(n for n in graph["nodes"] if n["type"] == "EZKokoroTTS")
    assert tts["widgets_values"][3] is True
    for n in iter_ace_encoders(graph):
        assert_ace_encoder_widgets(n, where=f"podcast-radio-drama:{n.get('title')}")
        if "negative" in (n.get("title") or "").lower():
            continue
        tags, lyrics = n["widgets_values"][0], n["widgets_values"][1]
        assert "instrumental" in tags.lower()
        assert "no vocals" in tags.lower()
        assert lyrics == ""
    bumper = [
        n
        for n in graph["nodes"]
        if n.get("title", "").endswith("(off)") or "preview (off)" in n.get("title", "")
    ]
    assert bumper
    for n in bumper:
        assert n["mode"] == 4, n.get("title")
    flac = next(n for n in graph["nodes"] if n["type"] == "SaveAudio")
    assert flac["widgets_values"][0] == "ez_radio_ep"
    for needle in BANNED:
        assert needle not in blob, needle
    assert "one-graph film" in extra["lab_note"].lower()


def _app_names(graph: dict) -> list[str]:
    return [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]


def _app_labels(graph: dict) -> list[str]:
    labels: list[str] = []
    for entry in graph["extra"]["linearData"]["inputs"]:
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or entry[1])
    return labels


def test_podcast_apps_expose_voices_length_not_clone_refs() -> None:
    audio = _load("podcast-audio-first-lab-example")
    names = _app_names(audio)
    assert "speaker_a_voice" in names
    assert "speaker_b_voice" in names
    assert "speed" in names
    assert "seconds" in names
    assert "lyrics" not in names
    assert "backend" not in names
    assert "speaker_a_ref" not in names
    labels = _app_labels(audio)
    assert "Script" in labels
    assert "Bed tags" in labels
    assert len(labels) == len(set(labels)), labels
    radio = _load("podcast-radio-drama-lab-example")
    radio_names = _app_names(radio)
    assert radio_names.count("seconds") == 2
    assert "announcer_voice" in radio_names
    assert "include_announcer" in radio_names
    assert "lyrics" not in radio_names
    radio_labels = _app_labels(radio)
    assert "Sting tags" in radio_labels
    assert "Bed tags" in radio_labels
    assert len(radio_labels) == len(set(radio_labels)), radio_labels
