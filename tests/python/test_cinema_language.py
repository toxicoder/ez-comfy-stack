"""Cinema Rack language addendum for Prompt Enhance (hermetic, no GGUF)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import cinema  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402


def test_wan_camera_tokens_are_unique_catalog_verbs() -> None:
    cinema.reset_cinema_caches_for_tests()
    tokens = cinema.wan_camera_tokens()
    assert tokens
    assert len(tokens) == len(set(tokens))
    for needle in ("dolly in", "pan left", "fixed camera", "tracking", "orbit"):
        assert needle in tokens
    assert cinema.DEFAULT_WAN_CAMERA in tokens


def test_recipe_exemplars_cover_axes_from_recipes() -> None:
    cinema.reset_cinema_caches_for_tests()
    exemplars = cinema.recipe_axis_exemplars()
    assert "lighting" in exemplars
    assert "camera_movement" in exemplars
    recipes = cinema.load_recipes()
    assert recipes
    first = next(iter(recipes.values()))
    axes = first.get("axes") or {}
    assert isinstance(axes, dict)
    for axis_id, tid in axes.items():
        assert axis_id in exemplars
        assert str(exemplars[axis_id].get("id")) == str(tid)


def test_cinema_language_addendum_lists_axes_recipes_and_tokens() -> None:
    cinema.reset_cinema_caches_for_tests()
    still = cinema.cinema_language_addendum("klein_t2i")
    words = still.split()
    assert 200 <= len(words) <= 900
    for axis_id in cinema.axis_ids():
        label = str(cinema.load_axes()[axis_id]["label"])
        assert label in still
    for recipe in cinema.load_recipes().values():
        assert str(recipe["label"]) in still
    assert "Cinema Rack" in still
    assert "Rembrandt" in still or "golden" in still.lower()
    assert "Stills:" in still
    assert "never import a second location" in still.lower()
    ident = cinema.cinema_language_addendum("klein_identity")
    assert "Identity bible" in ident
    assert "lighting" in ident.lower()
    wan = cinema.cinema_language_addendum("wan_t2v")
    assert "Wan T2V" in wan
    for token in ("dolly in", "pan left", "fixed camera"):
        assert token in wan
    i2v = cinema.cinema_language_addendum("wan_i2v")
    assert "start image owns look" in i2v.lower()
    assert "dolly in" in i2v
    ltx = cinema.cinema_language_addendum("ltx_t2v")
    assert "present tense" in ltx.lower()
    iclora = cinema.cinema_language_addendum("ltx_iclora")
    assert "IC-LoRA" in iclora
    neg = cinema.cinema_language_addendum("negative_klein")
    assert "Do not negate" in neg
    assert cinema.cinema_language_addendum("ace_tags") == ""
    assert cinema.cinema_language_addendum("klein_text_swap") == ""
    assert cinema.addendum_kind("klein_text_swap") == "skip"
    assert cinema.addendum_kind("klein_t2i", "text_swap") == "skip"
    assert cinema.addendum_kind("klein_background_swap") == "skip"
    assert cinema.addendum_kind("klein_background_edit") == "skip"
    assert cinema.addendum_kind("klein_t2i", "background_swap") == "skip"
    assert cinema.addendum_kind("dreamx_i2v") == "i2v"
    assert cinema.addendum_kind("wan_t2v", "i2v") == "i2v"
    assert cinema.addendum_kind("ltx_t2v", "iclora") == "iclora"
    assert cinema.addendum_kind("longcat_t2v") == "wan"
    assert cinema.addendum_kind("ltx_t2v") == "ltx"
    assert cinema.addendum_kind("zimage_t2i") == "still"


def test_clip_clause_and_empty_catalog_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cinema.reset_cinema_caches_for_tests()
    assert cinema._clip_clause("one two three") == "one two three"
    long = " ".join(f"word{i}" for i in range(24))
    clipped = cinema._clip_clause(long, 18)
    assert clipped.endswith("…")
    assert len(clipped.split()) == 18
    monkeypatch.setattr(
        cinema,
        "load_axis",
        lambda axis: (
            [
                {"wan_token": ""},
                {"wan_token": "dolly in"},
                {"wan_token": "dolly in"},
                {"wan_token": "pan left"},
            ]
            if axis == "camera_movement"
            else (_ for _ in ()).throw(KeyError(axis))
        ),
    )
    assert cinema.wan_camera_tokens() == ("dolly in", "pan left")
    monkeypatch.setattr(
        cinema,
        "load_axis",
        lambda *_a, **_k: (_ for _ in ()).throw(KeyError("camera_movement")),
    )
    assert cinema.wan_camera_tokens() == ()
    monkeypatch.setattr(
        cinema,
        "load_recipes",
        lambda: {
            "bad": {"id": "bad", "label": "Bad", "axes": ["nope"]},
            "ghost": {
                "id": "ghost",
                "label": "Ghost",
                "axes": {"lighting": "missing_id"},
            },
            "rec_x": {"id": "rec_x", "label": "", "axes": {"": "lit_rembrandt"}},
        },
    )
    assert cinema.recipe_axis_exemplars() == {}
    labeled = cinema.cinema_language_addendum("klein_t2i")
    assert "rec_x" in labeled
    monkeypatch.setattr(cinema, "load_recipes", lambda: {})
    monkeypatch.setattr(cinema, "recipe_axis_exemplars", lambda: {})
    empty = cinema.cinema_language_addendum("klein_t2i")
    assert "Recipes:" not in empty
    assert "Example clauses" not in empty
    assert "Stills:" in empty
    blank_entry = {"id": "x", "clause": "   "}
    monkeypatch.setattr(
        cinema,
        "recipe_axis_exemplars",
        lambda: {"lighting": blank_entry},
    )
    no_examples = cinema.cinema_language_addendum("klein_t2i")
    assert "Example clauses" not in no_examples
    monkeypatch.setattr(cinema, "wan_camera_tokens", lambda: ())
    silent = cinema.cinema_language_addendum("wan_i2v")
    assert "Wan camera tokens" not in silent


def test_with_cinema_system_skips_ace_and_appends_visual() -> None:
    cinema.reset_cinema_caches_for_tests()
    assert client.with_cinema_system("sys", "ace_tags") == "sys"
    out = client.with_cinema_system("sys", "klein_t2i")
    assert out.startswith("sys")
    assert "Cinema Rack" in out
    assert "Stills:" in out
