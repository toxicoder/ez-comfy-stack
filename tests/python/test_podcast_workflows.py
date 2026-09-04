"""US-safe podcast lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

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
    path = WF / f"{stem}.json"
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
    assert script["widgets_values"][1] is False
    assert any(n["type"] == "EZPodcastDisclosure" for n in graph["nodes"])
    assert any(n["type"] == "EZKokoroTTS" for n in graph["nodes"])
    ace = [n for n in graph["nodes"] if n["type"] == "TextEncodeAceStepAudio1.5"]
    assert ace
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
    assert script["widgets_values"][1] is False
    assert script["widgets_values"][2] == "radio_drama"
    tts = next(n for n in graph["nodes"] if n["type"] == "EZKokoroTTS")
    assert tts["widgets_values"][3] is True
    for n in graph["nodes"]:
        if n["type"] == "TextEncodeAceStepAudio1.5" and "negative" not in (n.get("title") or "").lower():
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
