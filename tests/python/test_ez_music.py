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
from ez_music.diss_examples import DISS_DURATION_S, DISS_EXAMPLES  # noqa: E402
from ez_music.nodes import (  # noqa: E402
    DRAFT_LYRICS,
    EZRapLyrics,
    FULL_LYRICS,
    NODE_CLASS_MAPPINGS,
    load_writer_prompt,
)

LIVING_MC_NEEDLES = ("Drake", "Kendrick", "Eminem", "Suno", "Udio", "Bill Nye")


def test_pack_imports_without_extra_pip() -> None:
    assert ez_music.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {"EZRapLyrics"}
    cls = NODE_CLASS_MAPPINGS["EZRapLyrics"]
    assert cls.CATEGORY == "ez-comfy/music"
    spec = cls.INPUT_TYPES()
    assert spec["required"]["enhance"][1]["default"] is True
    assert "[verse]" in spec["required"]["lyrics"][1]["default"]
    assert "[chorus]" in spec["required"]["lyrics"][1]["default"]


def test_seed_lyrics_have_sections() -> None:
    assert "[verse]" in DRAFT_LYRICS
    assert "[chorus]" in DRAFT_LYRICS
    assert "[verse]" in FULL_LYRICS
    assert "[chorus]" in FULL_LYRICS
    assert "[outro]" in FULL_LYRICS
    for needle in LIVING_MC_NEEDLES:
        assert needle not in DRAFT_LYRICS
        assert needle not in FULL_LYRICS


EXPECTED_NILL_BYE_TITLES = (
    "lab coat lecture",
    "peer review",
    "in his feels",
    "fake cool",
    "hypothesis vs rumor",
    "control group",
    "sample size",
    "placebo",
    "error bars",
    "lab notebook",
    "office hours",
    "grant denied",
    "contamination",
    "double blind",
    "replicate or retract",
)


def test_nill_bye_diss_examples_are_original_180s() -> None:
    assert DISS_DURATION_S == 180.0
    assert len(DISS_EXAMPLES) == 15
    prefixes: list[str] = []
    stems: list[str] = []
    seeds: list[int] = []
    spoken = 0
    for ex in DISS_EXAMPLES:
        assert ex["duration"] == DISS_DURATION_S
        lyrics = ex["lyrics"]
        assert "[verse]" in lyrics
        assert "[chorus]" in lyrics
        assert "[outro]" in lyrics
        assert lyrics.count("[verse]") >= 3
        assert lyrics.count("[chorus]") >= 3
        assert "Nill Bye" in lyrics
        assert "Rake" in lyrics
        assert str(ex["bpm"]) in ex["tags"]
        assert ex["stem"].startswith("music-rap-nill-bye-")
        assert ex["stem"].endswith("-lab-example")
        assert ex["prefix"].startswith("ez_rap_nill_")
        for needle in LIVING_MC_NEEDLES:
            assert needle not in lyrics
            assert needle not in ex["tags"]
            assert needle not in ex["description"]
        prefixes.append(ex["prefix"])
        stems.append(ex["stem"])
        seeds.append(int(ex["seed"]))
        if "[spoken word]" in lyrics:
            spoken += 1
    assert len(set(prefixes)) == 15
    assert len(set(stems)) == 15
    assert spoken == 2
    assert any(seed != 42 for seed in seeds)
    assert tuple(ex["title"] for ex in DISS_EXAMPLES) == EXPECTED_NILL_BYE_TITLES
    assert "Rake walks in with a club report" in DISS_EXAMPLES[0]["lyrics"]
    assert "Peer review time" in DISS_EXAMPLES[1]["lyrics"]
    assert "Rake in his feels like a full-time job" in DISS_EXAMPLES[2]["lyrics"]
    assert "Rake talk club like a uniform" in DISS_EXAMPLES[3]["lyrics"]
    assert "Hypothesis: Rake is cool" in DISS_EXAMPLES[4]["lyrics"]


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
