"""Hermetic tests for ez_music (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_music  # noqa: E402
from ez_music import nodes  # noqa: E402
from ez_music.nodes import (  # noqa: E402
    DRAFT_LYRICS,
    EZRapLyrics,
    FULL_LYRICS,
    NODE_CLASS_MAPPINGS,
    load_writer_prompt,
)


def test_pack_imports_without_extra_pip() -> None:
    assert ez_music.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {"EZRapLyrics"}
    cls = NODE_CLASS_MAPPINGS["EZRapLyrics"]
    assert cls.CATEGORY == "ez-comfy/music"
    spec = cls.INPUT_TYPES()
    assert spec["required"]["enhance"][1]["default"] is False
    assert "[verse]" in spec["required"]["lyrics"][1]["default"]
    assert "[chorus]" in spec["required"]["lyrics"][1]["default"]


def test_seed_lyrics_have_sections() -> None:
    assert "[verse]" in DRAFT_LYRICS
    assert "[chorus]" in DRAFT_LYRICS
    assert "[verse]" in FULL_LYRICS
    assert "[chorus]" in FULL_LYRICS
    assert "[outro]" in FULL_LYRICS
    for needle in ("Drake", "Kendrick", "Eminem", "Suno", "Udio"):
        assert needle not in DRAFT_LYRICS
        assert needle not in FULL_LYRICS


def test_writer_prompt_forbids_living_mcs() -> None:
    prompt = load_writer_prompt()
    blob = prompt.lower()
    assert "living" in blob
    assert "song title" in blob or "existing song" in blob
    assert "famous" in blob and "hook" in blob
    assert "in the style of" in blob


def test_lyrics_enhance_off_passthrough() -> None:
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZRapLyrics().run(DRAFT_LYRICS, False)
    complete.assert_not_called()
    assert out["result"][0] == DRAFT_LYRICS
    assert out["ui"]["passthrough"][0] == "enhance off"


def test_lyrics_missing_gguf_passthrough() -> None:
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("", "GGUF missing")),
        patch("ez_prompt_enhance.client._close_llm"),
    ):
        out = EZRapLyrics().run(DRAFT_LYRICS, True)
    assert out["result"][0] == DRAFT_LYRICS
    assert "GGUF missing" in out["ui"]["passthrough"][0]
