"""Hermetic tests for ez_podcast (no Comfy, no network, no GGUF, no Kokoro)."""

from __future__ import annotations
import pytest

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
    BACKEND_QWEN3TTS,
    DISCLOSURE_TEXT,
    EZAudioLoopToMatch,
    EZKokoroTTS,
    EZPodcastDisclosure,
    EZPodcastLearn,
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
        "EZPodcastLearn",
        "EZAudioLoopToMatch",
    }
    for cls in NODE_CLASS_MAPPINGS.values():
        assert cls.CATEGORY == "ez-comfy/podcast"
    enhance = EZPodcastScript.INPUT_TYPES()["required"]["enhance"][1]
    assert enhance["default"] is True
    assert enhance["label_on"] == "On"
    assert enhance["label_off"] == "Off"


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


def test_optional_backend_hook_returns_pcm(tmp_path: Path) -> None:
    ref = tmp_path / "owned.wav"
    ref.write_bytes(b"RIFF")
    tts = EZKokoroTTS()
    assert tts._try_optional_backend("hello", BACKEND_QWEN3TTS, "") is None
    nodes.optional_backend_hook = lambda text, backend, path: [0.0, 0.1, 0.0]
    try:
        pcm = tts._try_optional_backend("hello", BACKEND_QWEN3TTS, str(ref))
        assert pcm == [0.0, 0.1, 0.0]
    finally:
        nodes.optional_backend_hook = None


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
    types = EZPodcastScript.INPUT_TYPES()
    assert types["optional"]["context"][1]["forceInput"] is True
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZPodcastScript().run(
            SEED_SCRIPT, False, "podcast_two_host", "research brief"
        )
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
        patch("ez_prompt_enhance.client.complete", return_value=("Speaker A: Hi.\nSpeaker B: Yo.", None)) as complete,
        patch("ez_prompt_enhance.client._close_llm") as close,
    ):
        out = EZPodcastScript().run("lazy", True, "podcast_two_host", "stay on the rack")
    close.assert_called()
    assert "Speaker A: Hi." in out["result"][0]
    user = complete.call_args[0][1]
    assert "lazy" in user
    assert "Context:" in user
    assert "stay on the rack" in user


def test_ensure_lab_custom_nodes_path_inserts_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()],
    )
    nodes._ensure_lab_custom_nodes_path()
    assert Path(sys.path[0]).resolve() == CUSTOM.resolve()


def test_kokoro_tts_no_turns_empty_audio() -> None:
    audio = EZKokoroTTS().run("   ", include_announcer=False)[0]
    assert audio["sample_rate"] == 24000


def test_kokoro_missing_onnx_does_not_raise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    audio = EZKokoroTTS().run(SEED_SCRIPT)[0]
    assert "sample_rate" in audio


# --------------------------------------------------------------------------- #
# Operator-facing widget surfaces
# --------------------------------------------------------------------------- #

# Every widget the five registered classes expose, pinned by name so a widget
# dropped from INPUT_TYPES cannot pass the tooltip invariant by not existing.
PODCAST_WIDGETS: dict[str, tuple[str, ...]] = {
    "EZPodcastScript": ("sample", "prompt", "enhance", "flavor", "catalog", "context"),
    "EZPodcastDisclosure": ("script",),
    "EZKokoroTTS": (
        "script",
        "speaker_a_voice",
        "speaker_b_voice",
        "announcer_voice",
        "include_announcer",
        "backend",
        "speaker_a_ref",
        "speaker_b_ref",
        "speed",
    ),
    "EZPodcastLearn": (
        "sample",
        "sources",
        "format",
        "duration",
        "fetch_links",
        "enhance",
        "catalog",
    ),
    "EZAudioLoopToMatch": (),
}

# Connection-only sockets: the graphs wire these names, so they stay bare
# tuples and owe no tooltip (no options dict exists to carry one).
PODCAST_SOCKETS: dict[str, tuple[str, ...]] = {
    "EZPodcastScript": (),
    "EZPodcastDisclosure": (),
    "EZKokoroTTS": (),
    "EZPodcastLearn": (),
    "EZAudioLoopToMatch": ("speech", "bed"),
}

PODCAST_NODE_CLASSES = (
    EZPodcastScript,
    EZPodcastDisclosure,
    EZKokoroTTS,
    EZPodcastLearn,
    EZAudioLoopToMatch,
)


def test_every_registered_widget_carries_an_operator_tooltip() -> None:
    """Every knob says what to put there and what happens."""
    assert set(PODCAST_WIDGETS) == set(NODE_CLASS_MAPPINGS)
    for cls in PODCAST_NODE_CLASSES:
        spec = cls.INPUT_TYPES()
        sockets = PODCAST_SOCKETS[cls.__name__]
        seen: list[str] = []
        for section in ("required", "optional"):
            for widget, field in spec.get(section, {}).items():
                where = f"{cls.__name__}.{section}.{widget}"
                assert isinstance(field, tuple), where
                if widget in sockets:
                    assert field == (field[0],), f"{where} socket is not bare"
                    continue
                assert len(field) == 2, f"{where} has no options dict"
                assert isinstance(field[1], dict), where
                tooltip = field[1].get("tooltip")
                assert isinstance(tooltip, str), f"{where} has no tooltip"
                assert tooltip.strip(), f"{where} tooltip is blank"
                assert tooltip.isascii(), f"{where} tooltip is not ASCII"
                assert tooltip.endswith("."), f"{where} tooltip is not a sentence"
                seen.append(widget)
        assert tuple(seen) == PODCAST_WIDGETS[cls.__name__], cls.__name__


def test_loop_to_match_sockets_stay_bare_tuples() -> None:
    """The bed and speech sockets stay the bare form the graphs wire."""
    types = EZAudioLoopToMatch.INPUT_TYPES()
    assert types["required"]["speech"] == ("AUDIO",)
    assert types["required"]["bed"] == ("AUDIO",)


def test_speaker_ref_widgets_name_the_wav_its_folder_and_the_empty_case() -> None:
    """Free-text refs say what they are, where they live, and what blank does."""
    required = EZKokoroTTS.INPUT_TYPES()["required"]
    for widget in ("speaker_a_ref", "speaker_b_ref"):
        tooltip = required[widget][1]["tooltip"]
        where = f"EZKokoroTTS.{widget}"
        assert "operator-owned reference WAV" in tooltip, where
        assert "COMFY_OUTPUT_DIR/input" in tooltip, where
        assert "/inputs" in tooltip, where
        assert "empty keeps the built-in Kokoro voice" in tooltip, where


def test_number_widgets_name_their_unit_or_multiplier() -> None:
    """Speed is a multiplier and duration a length in minutes, not a bare float."""
    speed = EZKokoroTTS.INPUT_TYPES()["required"]["speed"][1]
    assert "not seconds" in speed["tooltip"]
    assert speed["step"] == 0.05
    assert speed["default"] == 1.0 and speed["min"] == 0.5 and speed["max"] == 1.5
    duration = EZPodcastLearn.INPUT_TYPES()["required"]["duration"][1]
    assert "minutes" in duration["tooltip"]


def test_catalog_widgets_name_the_sample_folder_and_its_lister() -> None:
    """The hidden stem field says which file it picks and who lists it."""
    for cls in (EZPodcastScript, EZPodcastLearn):
        tooltip = cls.INPUT_TYPES()["required"]["catalog"][1]["tooltip"]
        where = cls.__name__
        assert "custom_nodes/ez_prompt_enhance/js/samples/" in tooltip, where
        assert "ez_prompt_enhance/samples.py lists" in tooltip, where
