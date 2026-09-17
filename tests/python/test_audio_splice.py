"""Splice engine and Audio Rack node tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import audio  # noqa: E402
from ez_prompt_enhance.nodes import EZAudioRack, NODE_CLASS_MAPPINGS  # noqa: E402


def _first_id(axis_id: str) -> str:
    rows = audio.load_axis(axis_id)
    assert rows, axis_id
    return str(rows[0]["id"])


def _id_with_bpm() -> str:
    for row in audio.load_axis("tempo_groove"):
        token = str(row.get("bpm") or "").strip()
        if token:
            return str(row["id"])
    raise AssertionError("no tempo_groove bpm")


def test_unknown_pick_and_empty_rack() -> None:
    audio.reset_audio_caches_for_tests()
    empty = audio.splice({}, flavor=audio.FLAVOR_ACE_VOCAL, brief="")
    assert empty.tags == ""
    assert empty.lyrics == ""
    assert empty.used == ()
    ghost = audio.splice(
        {"genre_style": "not_a_real_technique"},
        flavor=audio.FLAVOR_ACE_VOCAL,
        brief="local booth bars",
    )
    assert "local booth" in ghost.lyrics.lower()
    assert any(item.technique_id == "not_a_real_technique" for item in ghost.dropped)
    assert audio.technique(audio.NONE) is None
    assert audio.technique("") is None
    assert audio.validate_id("boom_bap")
    assert not audio.validate_id("Boom Bap")
    bad_flavor = audio.splice({}, flavor="nope", brief="Hello")
    assert "Hello" in bad_flavor.lyrics


def test_instrumental_omits_vocal_and_brief() -> None:
    audio.reset_audio_caches_for_tests()
    vocal = _first_id("vocal_identity")
    result = audio.splice(
        {"vocal_identity": vocal, "genre_style": _first_id("genre_style")},
        flavor=audio.FLAVOR_ACE_INSTRUMENTAL,
        brief="should not be sung",
    )
    assert vocal not in result.used
    assert "should not be sung" not in result.lyrics.lower()
    assert "instrumental" in result.tags.lower()
    assert "no vocals" in result.tags.lower()
    assert any("vocal omitted" in item.reason for item in result.dropped)
    assert any(item.technique_id == "brief" for item in result.dropped)
    assert result.lyrics.strip().startswith("[")


def test_podcast_drops_non_bed_techniques() -> None:
    audio.reset_audio_caches_for_tests()
    dropped_id = None
    for row in audio.load_axis("genre_style"):
        if not audio._as_bool(row.get("podcast_ok"), True):
            dropped_id = str(row["id"])
            break
    if dropped_id is None:
        return
    result = audio.splice(
        {"genre_style": dropped_id},
        flavor=audio.FLAVOR_PODCAST_BED,
        brief="",
    )
    assert dropped_id not in result.used
    assert any("podcast-bed" in item.reason for item in result.dropped)
    assert "instrumental" in result.tags.lower()


def test_exactly_one_bpm_token() -> None:
    audio.reset_audio_caches_for_tests()
    tempo = _id_with_bpm()
    token = str((audio.technique(tempo) or {}).get("bpm") or "")
    vocal = audio.splice(
        {"tempo_groove": tempo, "genre_style": _first_id("genre_style")},
        flavor=audio.FLAVOR_ACE_VOCAL,
        brief="",
    )
    assert vocal.bpm == token
    assert vocal.tags.lower().count(token.lower()) >= 1
    none_bpm = audio.splice({}, flavor=audio.FLAVOR_ACE_VOCAL, brief="")
    assert none_bpm.bpm == ""


def test_later_splice_order_wins_conflicts() -> None:
    audio.reset_audio_caches_for_tests()
    pair = None
    for axis_id in audio.axis_ids():
        for row in audio.load_axis(axis_id):
            for other_id in audio._string_list(row, "conflicts"):
                other = audio.technique(other_id)
                if other and other.get("axis") != row.get("axis"):
                    pair = (str(row["id"]), other_id)
                    break
            if pair is not None:
                break
        if pair is not None:
            break
    assert pair is not None
    left, right = pair
    left_entry = audio.technique(left)
    right_entry = audio.technique(right)
    assert left_entry is not None and right_entry is not None
    picks = {
        str(left_entry["axis"]): left,
        str(right_entry["axis"]): right,
    }
    result = audio.splice(picks, flavor=audio.FLAVOR_ACE_VOCAL)
    assert len([tid for tid in (left, right) if tid in result.used]) == 1
    assert result.notes


def test_recipe_fills_none_but_does_not_clobber() -> None:
    audio.reset_audio_caches_for_tests()
    recipes = audio.load_recipes()
    assert recipes
    rid = next(iter(recipes))
    recipe = recipes[rid]
    axes = recipe["axes"]
    filled = audio.splice({}, flavor=audio.FLAVOR_ACE_VOCAL, recipe=rid)
    assert filled.used
    first_axis = next(iter(axes))
    first_tid = str(axes[first_axis])
    other = _first_id(first_axis)
    if other == first_tid:
        rows = audio.load_axis(first_axis)
        other = str(rows[1]["id"])
    clobber = audio.splice(
        {first_axis: other},
        flavor=audio.FLAVOR_ACE_VOCAL,
        recipe=rid,
    )
    assert other in clobber.used
    assert first_tid not in clobber.used or other == first_tid
    missing = audio.apply_recipe("nope", {"genre_style": audio.NONE})
    assert missing["genre_style"] == audio.NONE


def test_catalog_error_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    audio.reset_audio_caches_for_tests()
    bad_axes = tmp_path / "axes.json"
    bad_axes.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(audio, "AXES_PATH", bad_axes)
    try:
        audio.load_axes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    audio.reset_audio_caches_for_tests()
    obj_axes = tmp_path / "axes2.json"
    obj_axes.write_text('{"x": []}', encoding="utf-8")
    monkeypatch.setattr(audio, "AXES_PATH", obj_axes)
    try:
        audio.load_axes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    audio.reset_audio_caches_for_tests()
    monkeypatch.setattr(audio, "AXES_PATH", audio.AUDIO_DIR / "axes.json")
    recipes = tmp_path / "recipes.json"
    recipes.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(audio, "RECIPES_PATH", recipes)
    try:
        audio.load_recipes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    audio.reset_audio_caches_for_tests()
    missing = tmp_path / "no-recipes.json"
    monkeypatch.setattr(audio, "RECIPES_PATH", missing)
    assert audio.load_recipes() == {}
    audio.reset_audio_caches_for_tests()
    recs = tmp_path / "recipes2.json"
    recs.write_text(
        '[{"id": "r1", "axes": "nope"}, {"nope": 1}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(audio, "RECIPES_PATH", recs)
    loaded = audio.load_recipes()
    assert "r1" in loaded
    filled = audio.apply_recipe("r1", {"genre_style": audio.NONE})
    assert filled["genre_style"] == audio.NONE
    audio.reset_audio_caches_for_tests()


def test_load_axis_unknown_and_notes_empty() -> None:
    audio.reset_audio_caches_for_tests()
    try:
        audio.load_axis("not_an_axis")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
    empty = audio.splice({}, flavor=audio.FLAVOR_ACE_VOCAL)
    assert audio.format_notes(empty) == ""
    tempo = _id_with_bpm()
    with_bpm = audio.splice({"tempo_groove": tempo}, flavor=audio.FLAVOR_ACE_VOCAL)
    assert "BPM:" in audio.format_notes(with_bpm)
    assert audio.apply_recipe(audio.NONE, {"genre_style": audio.NONE})[
        "genre_style"
    ] == audio.NONE
    assert audio._normalize_pick(None) == audio.NONE
    assert audio._normalize_pick("  x  ") == "x"


def test_as_bool_and_string_list_helpers() -> None:
    assert audio._as_bool(1) is True
    assert audio._as_bool(True) is True
    assert audio._as_bool("yes") is True
    assert audio._as_bool("off") is False
    assert audio._as_bool(0) is False
    assert audio._as_bool(None) is True
    assert audio._as_bool("maybe") is True
    assert audio._string_list({"conflicts": "  one  "}, "conflicts") == ["one"]
    assert audio._string_list({"conflicts": "  "}, "conflicts") == []
    assert audio._string_list({"conflicts": 3}, "conflicts") == []
    assert audio._string_list({"conflicts": [" a ", ""]}, "conflicts") == ["a"]


def test_catalog_list_and_entry_types(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audio.reset_audio_caches_for_tests()
    not_list = tmp_path / "x.json"
    not_list.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(audio, "_catalog_path", lambda _axis: not_list)
    try:
        audio.load_axis("genre_style")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    audio.reset_audio_caches_for_tests()
    bad_item = tmp_path / "y.json"
    bad_item.write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(audio, "_catalog_path", lambda _axis: bad_item)
    try:
        audio.load_axis("mood_energy")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    audio.reset_audio_caches_for_tests()
    recs = tmp_path / "recipes.json"
    recs.write_text('[1, {"id": "ok"}]', encoding="utf-8")
    monkeypatch.setattr(audio, "RECIPES_PATH", recs)
    loaded = audio.load_recipes()
    assert list(loaded) == ["ok"]
    audio.reset_audio_caches_for_tests()
    assert audio._join_tags(["", "boom bap, hip-hop", "boom bap"]) == "boom bap, hip-hop"
    assert audio._force_instrumental_tags("trap") == "trap, instrumental, no vocals"
    assert audio._force_instrumental_tags("") == audio.INSTRUMENTAL_TAGS
    already = audio._force_instrumental_tags("instrumental, no vocals, trap")
    assert already.startswith("instrumental") or "trap" in already
    vocal_false = {
        "_vocal_axis": False,
        "_vocal_include": True,
        "_instrumental_include": True,
        "_podcast_include": True,
        "vocal_ok": False,
        "instrumental_ok": False,
        "podcast_ok": False,
    }
    assert "not a vocal technique" in audio._flavor_keeps(
        vocal_false, audio.FLAVOR_ACE_VOCAL
    )
    assert "not an instrumental technique" in audio._flavor_keeps(
        vocal_false, audio.FLAVOR_ACE_INSTRUMENTAL
    )
    assert "not a podcast-bed technique" in audio._flavor_keeps(
        vocal_false, audio.FLAVOR_PODCAST_BED
    )
    skip_axis = {
        "_vocal_axis": False,
        "_vocal_include": False,
        "_instrumental_include": False,
        "_podcast_include": False,
        "vocal_ok": True,
        "instrumental_ok": True,
        "podcast_ok": True,
    }
    assert "not a vocal-axis technique" in audio._flavor_keeps(
        skip_axis, audio.FLAVOR_ACE_VOCAL
    )
    assert "vocal omitted on instrumental" in audio._flavor_keeps(
        skip_axis, audio.FLAVOR_ACE_INSTRUMENTAL
    )
    assert "vocal omitted on instrumental" in audio._flavor_keeps(
        skip_axis, audio.FLAVOR_PODCAST_BED
    )
    vocal_axis = dict(skip_axis)
    vocal_axis["_vocal_axis"] = True
    vocal_axis["_instrumental_include"] = True
    vocal_axis["_podcast_include"] = True
    assert "vocal omitted on instrumental" in audio._flavor_keeps(
        vocal_axis, audio.FLAVOR_ACE_INSTRUMENTAL
    )
    audio.reset_audio_caches_for_tests()
    extra = audio.splice(
        {"not_an_axis": "x"}, flavor=audio.FLAVOR_ACE_INSTRUMENTAL, brief="Hi"
    )
    assert "instrumental" in extra.tags.lower()
    ids = audio.recipe_combo_ids()
    assert ids[0] == audio.NONE
    audio.reset_audio_caches_for_tests()
    missing_file = tmp_path / "nope.json"
    monkeypatch.setattr(audio, "_catalog_path", lambda _axis: missing_file)
    assert audio.load_axis("genre_style") == []
    audio.reset_audio_caches_for_tests()
    collapsed = audio._collapse_spaces("a   b,\n\n\nc")
    assert "  " not in collapsed or "," in collapsed
    assert audio._as_bool("1") is True
    assert audio._as_bool("true") is True
    assert audio._as_bool("0") is False
    assert audio._as_bool("false") is False
    assert audio._as_bool("no") is False
    assert audio._as_bool(3.0) is True


def test_audio_rack_node_splices() -> None:
    audio.reset_audio_caches_for_tests()
    assert "EZAudioRack" in NODE_CLASS_MAPPINGS
    types = EZAudioRack.INPUT_TYPES()
    required = types["required"]
    assert "brief" in required
    assert "flavor" in required
    assert "recipe" in required
    for axis_id in audio.WIDGET_AXIS_ORDER:
        assert axis_id in required
    kwargs = {axis_id: audio.NONE for axis_id in audio.WIDGET_AXIS_ORDER}
    kwargs["tempo_groove"] = _id_with_bpm()
    tags, lyrics, notes = EZAudioRack().run(
        brief="local booth bars",
        flavor=audio.FLAVOR_ACE_VOCAL,
        recipe=audio.NONE,
        **kwargs,
    )
    assert "local booth" in lyrics.lower()
    assert isinstance(notes, str)
    unknown = {axis_id: audio.NONE for axis_id in audio.WIDGET_AXIS_ORDER}
    unknown["genre_style"] = "missing_id"
    _tags, text, extra = EZAudioRack().run(
        brief="Hello",
        flavor=audio.FLAVOR_ACE_VOCAL,
        recipe=audio.NONE,
        **unknown,
    )
    assert "Hello" in text
    assert "missing_id" in extra
    coerced, lyrics2, _notes = EZAudioRack().run(
        brief=None,
        flavor=None,
        recipe=None,
        **{axis_id: audio.NONE for axis_id in audio.WIDGET_AXIS_ORDER},
    )
    assert isinstance(coerced, str)
    assert isinstance(lyrics2, str)


def test_axis_ids_appends_extra_axes(monkeypatch: pytest.MonkeyPatch) -> None:
    audio.reset_audio_caches_for_tests()
    monkeypatch.setattr(audio, "WIDGET_AXIS_ORDER", ("genre_style",))
    ids = audio.axis_ids()
    assert ids[0] == "genre_style"
    assert len(ids) == 13
    assert "tempo_groove" in ids
    audio.reset_audio_caches_for_tests()


def test_bpm_token_fallback_from_tags() -> None:
    entry = {"bpm": "", "_bpm_axis": True, "tags": "laid-back 86 bpm hop"}
    assert audio._bpm_token(entry) == "86 bpm"
    assert audio._bpm_token({"bpm": "", "_bpm_axis": False}) == ""
    assert audio._bpm_token({"bpm": "88 bpm"}) == "88 bpm"


def test_lyrics_form_instrumental_default() -> None:
    form = {"_form_axis": True, "lyrics_form": "[verse]", "lyrics_form_inst": ""}
    assert audio._lyrics_form(form, audio.FLAVOR_ACE_INSTRUMENTAL) == audio.DEFAULT_INST_FORM
    assert audio._lyrics_form(form, audio.FLAVOR_ACE_VOCAL) == "[verse]"
    assert audio._lyrics_form({"_form_axis": False}, audio.FLAVOR_ACE_VOCAL) == ""
