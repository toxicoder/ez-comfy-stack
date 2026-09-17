"""Audio Rack language addendum for ACE Prompt Enhance (hermetic, no GGUF)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import audio  # noqa: E402
from ez_prompt_enhance import cinema  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402


def test_bpm_tokens_are_unique() -> None:
    audio.reset_audio_caches_for_tests()
    tokens = audio.bpm_tokens()
    assert tokens
    assert len(tokens) == len(set(tokens))
    assert "88 bpm" in tokens
    assert audio.bpm_tokens() == tokens


def test_recipe_exemplars_cover_axes_from_recipes() -> None:
    audio.reset_audio_caches_for_tests()
    exemplars = audio.recipe_axis_exemplars()
    assert "genre_style" in exemplars
    recipes = audio.load_recipes()
    assert recipes
    first = next(iter(recipes.values()))
    axes = first.get("axes") or {}
    assert isinstance(axes, dict)
    for axis_id, tid in axes.items():
        assert axis_id in exemplars
        assert str(exemplars[axis_id].get("id")) == str(tid)


def test_audio_language_addendum_lists_axes_recipes_and_bpm() -> None:
    audio.reset_audio_caches_for_tests()
    vocal = audio.audio_language_addendum("ace_tags")
    words = vocal.split()
    assert 200 <= len(words) <= 1200
    for axis_id in audio.axis_ids():
        label = str(audio.load_axes()[axis_id]["label"])
        assert label in vocal
    for recipe in audio.load_recipes().values():
        assert str(recipe["label"]) in vocal
    assert "Audio Rack" in vocal
    assert "88 bpm" in vocal
    inst = audio.audio_language_addendum("ace_instrumental")
    assert "Instrumental:" in inst
    lyrics = audio.audio_language_addendum("ace_lyrics")
    assert "Lyrics:" in lyrics
    assert audio.audio_language_addendum("klein_t2i") == ""
    assert audio.addendum_kind("ace_tags") == "vocal"
    assert audio.addendum_kind("ace_instrumental") == "instrumental"
    assert audio.addendum_kind("ace_lyrics") == "lyrics"
    assert audio.addendum_kind("klein_t2i") == "skip"
    assert audio.addendum_kind("ace_tags", "instrumental") == "instrumental"


def test_cinema_addendum_still_skips_ace() -> None:
    cinema.reset_cinema_caches_for_tests()
    assert cinema.cinema_language_addendum("ace_tags") == ""
    assert cinema.addendum_kind("ace_tags") == "skip"


def test_clip_clause_and_empty_catalog_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio.reset_audio_caches_for_tests()
    assert audio._clip_clause("one two three") == "one two three"
    long = " ".join(f"word{i}" for i in range(24))
    clipped = audio._clip_clause(long, 18)
    assert clipped.endswith("…")
    assert len(clipped.split()) == 18
    monkeypatch.setattr(
        audio,
        "load_axis",
        lambda axis: (
            [
                {"bpm": ""},
                {"bpm": "88 bpm"},
                {"bpm": "88 bpm"},
                {"bpm": "140 bpm"},
            ]
            if axis == "tempo_groove"
            else (_ for _ in ()).throw(KeyError(axis))
        ),
    )
    assert audio.bpm_tokens() == ("88 bpm", "140 bpm")
    monkeypatch.setattr(
        audio,
        "load_axis",
        lambda *_a, **_k: (_ for _ in ()).throw(KeyError("tempo_groove")),
    )
    assert audio.bpm_tokens() == ()
    monkeypatch.setattr(
        audio,
        "load_recipes",
        lambda: {
            "bad": {"id": "bad", "label": "Bad", "axes": ["nope"]},
            "ghost": {
                "id": "ghost",
                "label": "Ghost",
                "axes": {"genre_style": "missing_id"},
            },
            "rec_x": {"id": "rec_x", "label": "", "axes": {"": "gen_boom_bap"}},
        },
    )
    assert audio.recipe_axis_exemplars() == {}
    labeled = audio.audio_language_addendum("ace_tags")
    assert "rec_x" in labeled or "Recipes:" not in labeled
    monkeypatch.setattr(audio, "load_recipes", lambda: {})
    monkeypatch.setattr(audio, "recipe_axis_exemplars", lambda: {})
    empty = audio.audio_language_addendum("ace_tags")
    assert "Recipes:" not in empty
    assert "Example clauses" not in empty
    assert "Vocal tags:" in empty
    blank_entry = {"id": "x", "clause": "   "}
    monkeypatch.setattr(
        audio,
        "recipe_axis_exemplars",
        lambda: {"genre_style": blank_entry},
    )
    no_examples = audio.audio_language_addendum("ace_tags")
    assert "Example clauses" not in no_examples
    monkeypatch.setattr(audio, "bpm_tokens", lambda: ())
    silent = audio.audio_language_addendum("ace_instrumental")
    assert "BPM tokens" not in silent


def test_with_audio_system_skips_visual_and_appends_ace() -> None:
    audio.reset_audio_caches_for_tests()
    assert client.with_audio_system("sys", "klein_t2i") == "sys"
    out = client.with_audio_system("sys", "ace_tags")
    assert out.startswith("sys")
    assert "Audio Rack" in out
    assert "Vocal tags:" in out
