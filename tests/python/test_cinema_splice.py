"""Splice engine and Cinema Rack node tests."""

from __future__ import annotations
import pytest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import cinema  # noqa: E402
from ez_prompt_enhance.nodes import EZCinemaRack, NODE_CLASS_MAPPINGS  # noqa: E402


def _first_id(axis_id: str) -> str:
    rows = cinema.load_axis(axis_id)
    assert rows, axis_id
    return str(rows[0]["id"])


def _id_with_wan_token() -> str:
    for row in cinema.load_axis("camera_movement"):
        token = str(row.get("wan_token") or "").strip()
        if token:
            return str(row["id"])
    raise AssertionError("no camera_movement wan_token")


def test_unknown_pick_and_empty_rack() -> None:
    cinema.reset_cinema_caches_for_tests()
    empty = cinema.splice({}, flavor=cinema.FLAVOR_KLEIN, subject="")
    assert empty.text == ""
    assert empty.used == ()
    ghost = cinema.splice(
        {"lighting": "not_a_real_technique"},
        flavor=cinema.FLAVOR_KLEIN,
        subject="A red bicycle on a hill",
    )
    assert "red bicycle" in ghost.text.lower()
    assert any(item.technique_id == "not_a_real_technique" for item in ghost.dropped)
    assert cinema.technique(cinema.NONE) is None
    assert cinema.technique("") is None
    assert cinema.validate_id("dolly_in")
    assert not cinema.validate_id("Dolly In")
    bad_flavor = cinema.splice({}, flavor="nope", subject="Hello")
    assert "Hello" in bad_flavor.text


def test_klein_uses_still_freeze_and_omits_editing() -> None:
    cinema.reset_cinema_caches_for_tests()
    move = _id_with_wan_token()
    edit_rows = cinema.load_axis("editing_transitions")
    edit = str(edit_rows[0]["id"])
    result = cinema.splice(
        {"camera_movement": move, "editing_transitions": edit},
        flavor=cinema.FLAVOR_KLEIN,
        subject="A techno wizard on a rooftop",
    )
    entry = cinema.technique(move)
    assert entry is not None
    still = str(entry.get("still") or "").strip()
    if still:
        assert still.rstrip(".") in result.text or still in result.text
    assert edit not in result.used
    assert any("omitted on stills" in item.reason for item in result.dropped)


def test_identity_skips_camera_keeps_light() -> None:
    cinema.reset_cinema_caches_for_tests()
    move = _first_id("camera_movement")
    light = _first_id("lighting")
    result = cinema.splice(
        {"camera_movement": move, "lighting": light},
        flavor=cinema.FLAVOR_KLEIN_IDENTITY,
        subject="World bible of one penthouse",
    )
    assert move not in result.used
    assert light in result.used
    assert "penthouse" in result.text.lower()


def test_wan_drops_morph_cut() -> None:
    cinema.reset_cinema_caches_for_tests()
    morph = None
    for row in cinema.load_axis("editing_transitions"):
        if not cinema._as_bool(row.get("motion_ok"), True):
            morph = str(row["id"])
            break
    if morph is None:
        return
    result = cinema.splice(
        {"editing_transitions": morph},
        flavor=cinema.FLAVOR_WAN_T2V,
        subject="A pier",
    )
    assert morph not in result.used
    assert any("not a motion technique" in item.reason for item in result.dropped)


def test_wan_emits_exactly_one_camera_token() -> None:
    cinema.reset_cinema_caches_for_tests()
    move = _id_with_wan_token()
    token = str((cinema.technique(move) or {}).get("wan_token") or "")
    t2v = cinema.splice(
        {"camera_movement": move, "lighting": _first_id("lighting")},
        flavor=cinema.FLAVOR_WAN_T2V,
        subject="A runner on a pier",
    )
    assert t2v.wan_camera == token
    assert t2v.text.lower().count(token.lower()) == 1
    i2v = cinema.splice(
        {
            "camera_movement": move,
            "lighting": _first_id("lighting"),
            "genre_looks": _first_id("genre_looks"),
        },
        flavor=cinema.FLAVOR_WAN_I2V,
        subject="ignored subject",
    )
    assert "ignored subject" not in i2v.text.lower()
    assert i2v.wan_camera == token
    assert _first_id("lighting") not in i2v.used
    none_cam = cinema.splice({}, flavor=cinema.FLAVOR_WAN_T2V, subject="A pier")
    assert none_cam.wan_camera == cinema.DEFAULT_WAN_CAMERA


def test_ltx_interleaves_audio_and_keeps_editing() -> None:
    cinema.reset_cinema_caches_for_tests()
    weather = None
    for row in cinema.load_axis("atmosphere_weather"):
        if str(row.get("audio") or "").strip():
            weather = str(row["id"])
            break
    assert weather
    edit = _first_id("editing_transitions")
    result = cinema.splice(
        {"atmosphere_weather": weather, "editing_transitions": edit},
        flavor=cinema.FLAVOR_LTX_T2V,
        subject="Rain hits the terrace",
    )
    audio = str((cinema.technique(weather) or {}).get("audio") or "")
    assert audio.rstrip(".") in result.text or audio in result.text
    assert edit in result.used


def test_later_splice_order_wins_conflicts() -> None:
    cinema.reset_cinema_caches_for_tests()
    pair = None
    for row in cinema.load_axis("camera_movement"):
        for other_id in cinema._string_list(row, "conflicts"):
            other = cinema.technique(other_id)
            if other and other.get("axis") != row.get("axis"):
                pair = (str(row["id"]), other_id)
                break
        if pair is not None:
            break
    assert pair is not None
    left, right = pair
    left_entry = cinema.technique(left)
    right_entry = cinema.technique(right)
    assert left_entry is not None and right_entry is not None
    picks = {
        str(left_entry["axis"]): left,
        str(right_entry["axis"]): right,
    }
    result = cinema.splice(picks, flavor=cinema.FLAVOR_LTX_T2V)
    assert len([tid for tid in (left, right) if tid in result.used]) == 1
    assert result.notes


def test_recipe_fills_none_but_does_not_clobber() -> None:
    cinema.reset_cinema_caches_for_tests()
    recipes = cinema.load_recipes()
    assert recipes
    rid = next(iter(recipes))
    recipe = recipes[rid]
    axes = recipe["axes"]
    filled = cinema.splice({}, flavor=cinema.FLAVOR_KLEIN, recipe=rid)
    assert filled.used
    override_axis = next(iter(axes))
    other = _first_id(override_axis)
    if other == axes[override_axis]:
        rows = cinema.load_axis(override_axis)
        other = str(rows[1]["id"])
    mixed = cinema.splice(
        {override_axis: other},
        flavor=cinema.FLAVOR_KLEIN,
        recipe=rid,
    )
    assert other in mixed.used
    missing = cinema.apply_recipe("nope", {"lighting": cinema.NONE})
    assert missing["lighting"] == cinema.NONE
    notes = cinema.format_notes(filled)
    assert isinstance(notes, str)


def test_catalog_error_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cinema.reset_cinema_caches_for_tests()
    bad_axes = tmp_path / "axes.json"
    bad_axes.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(cinema, "AXES_PATH", bad_axes)
    try:
        cinema.load_axes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    cinema.reset_cinema_caches_for_tests()
    obj_axes = tmp_path / "axes2.json"
    obj_axes.write_text('{"x": []}', encoding="utf-8")
    monkeypatch.setattr(cinema, "AXES_PATH", obj_axes)
    try:
        cinema.load_axes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    cinema.reset_cinema_caches_for_tests()
    monkeypatch.setattr(cinema, "AXES_PATH", cinema.CINEMA_DIR / "axes.json")
    recipes = tmp_path / "recipes.json"
    recipes.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cinema, "RECIPES_PATH", recipes)
    try:
        cinema.load_recipes()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    cinema.reset_cinema_caches_for_tests()
    missing = tmp_path / "no-recipes.json"
    monkeypatch.setattr(cinema, "RECIPES_PATH", missing)
    assert cinema.load_recipes() == {}
    cinema.reset_cinema_caches_for_tests()
    recs = tmp_path / "recipes2.json"
    recs.write_text(
        '[{"id": "r1", "axes": "nope"}, {"nope": 1}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(cinema, "RECIPES_PATH", recs)
    loaded = cinema.load_recipes()
    assert "r1" in loaded
    filled = cinema.apply_recipe("r1", {"lighting": cinema.NONE})
    assert filled["lighting"] == cinema.NONE
    cinema.reset_cinema_caches_for_tests()


def test_load_axis_unknown_and_notes_empty() -> None:
    cinema.reset_cinema_caches_for_tests()
    try:
        cinema.load_axis("not_an_axis")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
    empty = cinema.splice({}, flavor=cinema.FLAVOR_KLEIN)
    assert cinema.format_notes(empty) == ""
    wan = cinema.splice({}, flavor=cinema.FLAVOR_WAN_T2V, subject="A pier")
    assert "Wan camera" in cinema.format_notes(wan)
    assert cinema.apply_recipe(cinema.NONE, {"lighting": cinema.NONE})["lighting"] == cinema.NONE
    assert cinema._normalize_pick(None) == cinema.NONE
    assert cinema._normalize_pick("  x  ") == "x"


def test_as_bool_and_string_list_helpers() -> None:
    assert cinema._as_bool(True) is True
    assert cinema._as_bool("yes") is True
    assert cinema._as_bool("off") is False
    assert cinema._as_bool(0) is False
    assert cinema._as_bool(None) is True
    assert cinema._as_bool("maybe") is True
    assert cinema._string_list({"conflicts": "  one  "}, "conflicts") == ["one"]
    assert cinema._string_list({"conflicts": "  "}, "conflicts") == []
    assert cinema._string_list({"conflicts": 3}, "conflicts") == []
    assert cinema._string_list({"conflicts": [" a ", ""]}, "conflicts") == ["a"]


def test_catalog_list_and_entry_types(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cinema.reset_cinema_caches_for_tests()
    not_list = tmp_path / "x.json"
    not_list.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cinema, "_catalog_path", lambda _axis: not_list)
    try:
        cinema.load_axis("camera_movement")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    cinema.reset_cinema_caches_for_tests()
    bad_item = tmp_path / "y.json"
    bad_item.write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(cinema, "_catalog_path", lambda _axis: bad_item)
    try:
        cinema.load_axis("lighting")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    cinema.reset_cinema_caches_for_tests()
    recs = tmp_path / "recipes.json"
    recs.write_text('[1, {"id": "ok"}]', encoding="utf-8")
    monkeypatch.setattr(cinema, "RECIPES_PATH", recs)
    loaded = cinema.load_recipes()
    assert list(loaded) == ["ok"]
    cinema.reset_cinema_caches_for_tests()
    token = cinema._wan_token({"wan_token": "", "_wan_camera": True, "label": "Dolly In"})
    assert token == "dolly in"
    assert cinema._wan_token({"wan_token": "", "_wan_camera": False}) == ""
    assert cinema._join_sentences(["", "Hello"]) == "Hello."
    still_false = {
        "_still_mode": "clause",
        "_identity_include": True,
        "_i2v_include": True,
        "still_ok": False,
        "motion_ok": False,
        "av_ok": False,
    }
    assert "not a still technique" in cinema._flavor_keeps(still_false, cinema.FLAVOR_KLEIN)
    assert "not a motion technique" in cinema._flavor_keeps(still_false, cinema.FLAVOR_WAN_I2V)
    assert "not an AV technique" in cinema._flavor_keeps(still_false, cinema.FLAVOR_LTX_T2V)
    cinema.reset_cinema_caches_for_tests()
    extra = cinema.splice({"not_an_axis": "x"}, flavor=cinema.FLAVOR_KLEIN_EDIT, subject="Hi")
    assert "Hi" in extra.text
    ids = cinema.recipe_combo_ids()
    assert ids[0] == cinema.NONE


def test_cinema_rack_node_splices() -> None:
    cinema.reset_cinema_caches_for_tests()
    assert "EZCinemaRack" in NODE_CLASS_MAPPINGS
    types = EZCinemaRack.INPUT_TYPES()
    required = types["required"]
    assert "subject" in required
    assert "flavor" in required
    assert "recipe" in required
    for axis_id in cinema.WIDGET_AXIS_ORDER:
        assert axis_id in required
    kwargs = {axis_id: cinema.NONE for axis_id in cinema.WIDGET_AXIS_ORDER}
    kwargs["camera_movement"] = _id_with_wan_token()
    prompt, notes = EZCinemaRack().run(
        subject="A techno wizard on a rooftop",
        flavor=cinema.FLAVOR_KLEIN,
        recipe=cinema.NONE,
        **kwargs,
    )
    assert "techno wizard" in prompt.lower()
    assert isinstance(notes, str)
    unknown = {axis_id: cinema.NONE for axis_id in cinema.WIDGET_AXIS_ORDER}
    unknown["lighting"] = "missing_id"
    text, extra = EZCinemaRack().run(
        subject="Hello",
        flavor=cinema.FLAVOR_KLEIN,
        recipe=cinema.NONE,
        **unknown,
    )
    assert "Hello" in text
    assert "missing_id" in extra
    coerced, _notes = EZCinemaRack().run(
        subject=None,
        flavor=None,
        recipe=None,
        **{axis_id: cinema.NONE for axis_id in cinema.WIDGET_AXIS_ORDER},
    )
    assert isinstance(coerced, str)
