"""Hermetic tests for ez_podcast (no Comfy, no network, no GGUF, no Kokoro)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_podcast  # noqa: E402
from ez_podcast import nodes  # noqa: E402
from ez_podcast.nodes import (  # noqa: E402
    BACKEND_CHATTERBOX,
    BACKEND_KOKORO,
    DISCLOSURE_TEXT,
    EZKokoroTTS,
    EZPodcastDisclosure,
    EZPodcastScript,
    NODE_CLASS_MAPPINGS,
    SEED_SCRIPT,
    load_writer_prompt,
    parse_speaker_turns,
    prepend_disclosure,
    resolve_tts_backend,
)


def test_pack_imports_without_kokoro() -> None:
    assert ez_podcast.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZPodcastScript",
        "EZPodcastDisclosure",
        "EZKokoroTTS",
    }
    for cls in NODE_CLASS_MAPPINGS.values():
        assert cls.CATEGORY == "ez-comfy/podcast"


def test_disclosure_string_exact() -> None:
    assert DISCLOSURE_TEXT == (
        "Voices and music on this show are synthesized. The hosts are original "
        "characters, not recordings of real people."
    )
    out = EZPodcastDisclosure().run("Speaker A: Hello.")
    assert out[0].startswith(DISCLOSURE_TEXT)
    assert "Speaker A: Hello." in out[0]


def test_prepend_disclosure_idempotent() -> None:
    once = prepend_disclosure(SEED_SCRIPT)
    assert once.startswith(DISCLOSURE_TEXT)
    assert prepend_disclosure(once) == once.strip()
    assert prepend_disclosure("  ") == DISCLOSURE_TEXT


def test_parse_speaker_turns() -> None:
    turns = parse_speaker_turns(SEED_SCRIPT)
    roles = [role for role, _ in turns]
    assert roles == ["speaker_a", "speaker_b", "speaker_a", "speaker_b"]
    assert "Local Signal" in turns[0][1]
    mixed = parse_speaker_turns("Announcer: Open.\nSpeaker A: Hi.\ncontinued.")
    assert mixed[0] == ("announcer", "Open.")
    assert mixed[1][1].endswith("continued.")


def test_empty_refs_resolve_to_kokoro() -> None:
    assert resolve_tts_backend("chatterbox", "", "") == BACKEND_KOKORO
    assert resolve_tts_backend("qwen3tts", None, None) == BACKEND_KOKORO
    assert resolve_tts_backend("nope") == BACKEND_KOKORO
    assert resolve_tts_backend(BACKEND_CHATTERBOX, "/tmp/owned.wav", "") == BACKEND_CHATTERBOX
    assert resolve_tts_backend("kokoro", "/tmp/owned.wav", "") == BACKEND_KOKORO


def test_writer_prompts_exist() -> None:
    two = load_writer_prompt("podcast_two_host")
    assert "Speaker A:" in two
    assert "Speaker B:" in two
    radio = load_writer_prompt("radio_drama")
    assert "fiction" in radio.lower() or "invented" in radio.lower()
    assert "news rewrite" in radio.lower() or "news" in radio.lower()


def test_script_enhance_off_passthrough() -> None:
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZPodcastScript().run(SEED_SCRIPT, False, "podcast_two_host")
    complete.assert_not_called()
    assert out["result"][0] == SEED_SCRIPT
    assert out["ui"]["passthrough"][0] == "enhance off"


def test_script_missing_gguf_passthrough() -> None:
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("", "GGUF missing")),
        patch("ez_prompt_enhance.client._close_llm"),
    ):
        out = EZPodcastScript().run(SEED_SCRIPT, True, "podcast_two_host")
    assert out["result"][0] == SEED_SCRIPT
    assert "GGUF missing" in out["ui"]["passthrough"][0]


def test_script_success_unloads_writer() -> None:
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("Speaker A: Hi.\nSpeaker B: Yo.", None)),
        patch("ez_prompt_enhance.client._close_llm") as close,
    ):
        out = EZPodcastScript().run("lazy", True, "podcast_two_host")
    close.assert_called()
    assert "Speaker A: Hi." in out["result"][0]


def test_kokoro_tts_no_turns_empty_audio() -> None:
    audio = EZKokoroTTS().run("   ", include_announcer=False)[0]
    assert audio["sample_rate"] == 24000


def test_kokoro_missing_onnx_does_not_raise(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    audio = EZKokoroTTS().run(SEED_SCRIPT)[0]
    assert "sample_rate" in audio
