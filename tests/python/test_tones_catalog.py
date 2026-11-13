"""Hermetic tests for the tone catalog and its operator JSON loader."""

from __future__ import annotations

import json
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_tones.catalog import (  # noqa: E402
    ALARM_MAX_S,
    ALARM_MIN_S,
    KINDS,
    NOTIFICATION_MAX_S,
    NOTIFICATION_MIN_S,
    RINGTONE_MAX_S,
    RINGTONE_MIN_S,
    TAG_MAX,
    TONE_CATALOG,
    Timbre,
    ToneKind,
    ToneSpec,
    by_slug,
    categories,
    load_catalog,
    tones_for,
    validate,
    write_catalog_template,
)
from ez_tones.synth import TIMBRES  # noqa: E402

LONG_PITCHES = [76, 79, 83, 79, 83, 88]


def _row(**overrides: object) -> dict[str, object]:
    """Build one valid operator row with fields swapped in.

    Args:
        overrides: Keys to add or replace.

    Returns:
        A row ready to drop into ``tones``.
    """
    base: dict[str, object] = {
        "slug": "operator-tone",
        "name": "Operator Tone",
        "kind": "notification",
        "category": "organic",
        "mood": "friendly",
        "timbre": "marimba",
        "bpm": 120,
        "pitches": list(LONG_PITCHES),
    }
    base.update(overrides)
    return base


def _write(tmp_path: Path, payload: object, name: str = "catalog.json") -> str:
    """Write a catalog file and hand back its path.

    Args:
        tmp_path: Directory for the file.
        payload: Object to serialise, or raw text.
        name: File name.

    Returns:
        Path to the file.
    """
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def _load(tmp_path: Path, rows: object) -> tuple[ToneSpec, ...]:
    """Write ``{"tones": rows}`` and load it over the shipped pack.

    Args:
        tmp_path: Directory for the file.
        rows: Value to put under ``tones``.

    Returns:
        The merged catalog.
    """
    return load_catalog(_write(tmp_path, {"tones": rows}))


def _base() -> ToneSpec:
    """A shipped row other tests bend out of shape.

    Returns:
        The soft triple tap notification.
    """
    spec = by_slug("soft-triple-tap")
    assert spec is not None
    return spec


def test_shipped_pack_is_big_and_balanced() -> None:
    """An operator could ship this as-is: three kinds, several styles."""
    assert len(TONE_CATALOG) >= 24
    assert set(KINDS) == {spec.kind for spec in TONE_CATALOG}
    assert len({spec.timbre for spec in TONE_CATALOG}) >= 5
    assert len(categories()) >= 4


def test_every_shipped_row_is_valid_and_play_ready() -> None:
    """Each row validates and sits inside its kind's duration budget."""
    for spec in TONE_CATALOG:
        validate(spec)
        assert spec.tags, spec.slug
        assert len(spec.tags) <= TAG_MAX
        assert spec.mood and spec.category and spec.name
        assert spec.timbre in TIMBRES
        if spec.kind == "notification":
            assert NOTIFICATION_MIN_S <= spec.duration_s <= NOTIFICATION_MAX_S
            assert spec.loopable, spec.slug
        elif spec.kind == "ringtone":
            assert RINGTONE_MIN_S <= spec.duration_s <= RINGTONE_MAX_S
        else:
            assert ALARM_MIN_S <= spec.duration_s <= ALARM_MAX_S
            assert spec.loopable, spec.slug


def test_slugs_are_unique_and_file_safe() -> None:
    """Slugs are the export basename, so they stay lowercase and flat."""
    slugs = [spec.slug for spec in TONE_CATALOG]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert slug == slug.strip().lower()
        assert "/" not in slug and " " not in slug


def test_selection_helpers_read_the_catalog() -> None:
    """Kind filter, slug lookup, and category list all answer."""
    assert len(tones_for("alarm")) == 6
    assert all(spec.kind == "alarm" for spec in tones_for("alarm"))
    assert tones_for("ringtone", TONE_CATALOG[:2]) == ()
    found = by_slug("bell-tower")
    assert found is not None and found.timbre == "bell"
    assert by_slug("no-such-tone") is None
    head = TONE_CATALOG[:2]
    assert categories(head) == tuple(sorted({spec.category for spec in head}))


def test_rows_are_frozen_so_a_pack_can_share_them() -> None:
    """A built catalog cannot be mutated under a running build."""
    with pytest.raises(FrozenInstanceError):
        setattr(_base(), "name", "mutated")


def test_load_catalog_adds_a_new_tone(tmp_path: Path) -> None:
    """An operator row lands after the shipped rows with sane defaults."""
    merged = _load(tmp_path, [_row()])
    assert merged[: len(TONE_CATALOG)] == TONE_CATALOG
    added = merged[-1]
    assert added.slug == "operator-tone"
    assert added.channels == 1
    assert added.tags == ()
    assert added.loopable is True
    assert added.duration_s == pytest.approx(2.55, abs=0.01)


def test_load_catalog_overrides_a_shipped_row_in_place(tmp_path: Path) -> None:
    """Re-cutting a shipped tone keeps its position and replaces its data."""
    original = by_slug("bell-post")
    assert original is not None
    merged = _load(
        tmp_path,
        [_row(slug="bell-post", name="Bell Post (operator cut)", bpm=104)],
    )
    assert len(merged) == len(TONE_CATALOG)
    index = [spec.slug for spec in merged].index("bell-post")
    assert merged[index].name == "Bell Post (operator cut)"
    assert merged[index].bpm == 104
    assert merged[index].duration_s != original.duration_s


def test_motif_form_and_explicit_flags_round_trip(tmp_path: Path) -> None:
    """The explicit step form honours every optional key."""
    merged = _load(
        tmp_path,
        [
            _row(
                slug="explicit-steps",
                kind="ringtone",
                pitches=None,
                motif=[[69, 1.2, 0.9], [None, 0.6, 0.0], [76, 1.5, 0.7]],
                tags=["Bold", "mine", "mine", " Call "],
                loopable=False,
                channels=2,
            )
        ],
    )
    spec = by_slug("explicit-steps", merged)
    assert spec is not None
    assert spec.channels == 2
    assert spec.loopable is False
    assert spec.tags == ("bold", "mine", "call")
    assert spec.motif[0] == (69, 1.2, 0.9)
    assert spec.motif[1][0] is None
    assert spec.duration_s == pytest.approx(3.3)


def test_pitches_form_honours_beat_velocity_and_gap(tmp_path: Path) -> None:
    """The simple form scales the beat and leaves the requested gap."""
    merged = _load(
        tmp_path,
        [
            _row(
                slug="paced",
                kind="notification",
                beat_s=0.4,
                velocity=0.6,
                gap_ratio=0.5,
                pitches=[60, 64, 67, 72, 67, 64] * 2,
            )
        ],
    )
    spec = by_slug("paced", merged)
    assert spec is not None
    assert all(step[2] == 0.6 for step in spec.motif)
    assert spec.motif[0][1] == pytest.approx(0.2)
    assert spec.duration_s == pytest.approx(2.4)


def test_template_round_trips_through_the_loader(tmp_path: Path) -> None:
    """The file the operator edits is a file the loader accepts."""
    path = write_catalog_template(str(tmp_path / "nested" / "template.json"))
    assert path.is_file()
    merged = load_catalog(str(path))
    assert len(merged) == len(TONE_CATALOG) + 2
    ping = by_slug("my-new-ping", merged)
    ring = by_slug("my-new-ring", merged)
    assert ping is not None and ping.loopable and ping.channels == 1
    assert ring is not None and ring.channels == 2
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["_comment"]
    assert any("motif" in field for field in document["_fields"])
    assert len(document["tones"]) == 2


def test_template_is_plain_ascii(tmp_path: Path) -> None:
    """Nothing in the operator file trips the punctuation gate."""
    path = write_catalog_template(str(tmp_path / "template.json"))
    assert path.read_text(encoding="utf-8").isascii()


def test_load_catalog_rejects_a_missing_file(tmp_path: Path) -> None:
    """A typo in the catalog path names the file that is not there."""
    with pytest.raises(ValueError, match="catalog file not found"):
        load_catalog(str(tmp_path / "nowhere.json"))


def test_load_catalog_rejects_bad_json(tmp_path: Path) -> None:
    """A half-edited file says so instead of raising a raw decoder error."""
    with pytest.raises(ValueError, match="not valid JSON"):
        load_catalog(_write(tmp_path, "{ nope", name="bad.json"))


@pytest.mark.parametrize("text", ['["a"]', "{}", '{"tones": {}}', '{"tones": ["x"]}'])
def test_load_catalog_rejects_a_wrong_shape(tmp_path: Path, text: str) -> None:
    """Only an object with a list of objects is a catalog."""
    with pytest.raises(ValueError, match="tones|JSON object"):
        load_catalog(_write(tmp_path, text, name="shape.json"))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"zzz": 1}, "unknown key"),
        ({"slug": None}, "'slug' must be a non-empty string"),
        ({"slug": "  "}, "'slug' must be a non-empty string"),
        ({"name": ""}, "'name' must be a non-empty string"),
        ({"category": 3}, "'category' must be a non-empty string"),
        ({"mood": []}, "'mood' must be a non-empty string"),
        ({"kind": "siren"}, "'kind' must be one of"),
        ({"kind": None}, "'kind' must be one of"),
        ({"timbre": "hollow"}, "'timbre' must be one of"),
        ({"timbre": None}, "'timbre' must be one of"),
        ({"bpm": None}, "'bpm' must be a whole number"),
        ({"bpm": 120.5}, "'bpm' must be a whole number"),
        ({"bpm": True}, "'bpm' must be a whole number"),
        ({"bpm": "fast"}, "'bpm' must be a whole number"),
        ({"pitches": None}, "needs a 'motif' or a 'pitches' list"),
        ({"pitches": []}, "'pitches' must be a non-empty list"),
        ({"pitches": "72"}, "'pitches' must be a non-empty list"),
        ({"pitches": ["seventy"]}, "'pitches' must be a whole number"),
        ({"beat_s": "x"}, "'beat_s' must be a number"),
        ({"velocity": "x"}, "'velocity' must be a number"),
        ({"gap_ratio": True}, "'gap_ratio' must be a number"),
        ({"tags": "one"}, "'tags' must be a list of strings"),
        ({"tags": [1]}, "'tags' must be a list of strings"),
        ({"tags": [" "]}, "'tags' must be a list of strings"),
        ({"loopable": "yes"}, "'loopable' must be true or false"),
        ({"channels": "2"}, "'channels' must be 1 or 2"),
        ({"channels": 5}, "'channels' must be 1 or 2"),
        ({"bpm": 39}, "bpm must be 40..240"),
        ({"tags": [f"t{i}" for i in range(13)]}, "at most 12 tags"),
    ],
)
def test_load_catalog_names_the_bad_row(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    """Every malformed operator row fails with the key that caused it."""
    row = _row(**overrides)
    if not {"pitches", "beat_s", "velocity", "gap_ratio"} & set(overrides):
        row["motif"] = [[pitch, 0.425, 0.9] for pitch in LONG_PITCHES]
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, [row])


def test_load_catalog_rejects_malformed_motif_steps(tmp_path: Path) -> None:
    """A step has to be pitch, duration, velocity."""
    with pytest.raises(ValueError, match="motif step 0 must be"):
        _load(tmp_path, [_row(pitches=None, motif=[[69, 0.3]])])
    with pytest.raises(ValueError, match=r"motif\[0\]\[0\]"):
        _load(tmp_path, [_row(pitches=None, motif=[[70.5, 0.3, 0.9]])])
    with pytest.raises(ValueError, match=r"motif\[1\]\[1\]"):
        _load(tmp_path, [_row(pitches=None, motif=[[69, 0.3, 0.9], [72, "x", 0.9]])])
    with pytest.raises(ValueError, match="'motif' must be a non-empty list"):
        _load(tmp_path, [_row(pitches=None, motif=[])])


def test_load_catalog_rejects_a_row_outside_its_budget(tmp_path: Path) -> None:
    """A notification that is too short never reaches the encoder."""
    with pytest.raises(ValueError, match="notification must be 2.0..5.0 s"):
        _load(tmp_path, [_row(pitches=[76, 79])])
    with pytest.raises(ValueError, match="ringtone must be 3.0..30.0 s"):
        _load(tmp_path, [_row(kind="ringtone", pitches=[76])])


def test_validate_checks_every_field_directly() -> None:
    """The validator is callable on its own and bites on each field."""
    spec = _base()
    with pytest.raises(ValueError, match="slug is empty"):
        validate(replace(spec, slug="  "))
    with pytest.raises(ValueError, match="name is empty"):
        validate(replace(spec, name=" "))
    with pytest.raises(ValueError, match="kind must be one of"):
        validate(replace(spec, kind=cast(ToneKind, "siren")))
    with pytest.raises(ValueError, match="timbre must be one of"):
        validate(replace(spec, timbre=cast(Timbre, "hollow")))
    with pytest.raises(ValueError, match="bpm must be"):
        validate(replace(spec, bpm=241))
    with pytest.raises(ValueError, match="channels must be 1 or 2"):
        validate(replace(spec, channels=3))
    with pytest.raises(ValueError, match="motif is empty"):
        validate(replace(spec, motif=()))
    with pytest.raises(ValueError, match="step 0 pitch 9 is outside"):
        validate(replace(spec, motif=((9, 0.3, 0.9),)))
    with pytest.raises(ValueError, match="step 0 duration must be > 0"):
        validate(replace(spec, motif=((69, 0.0, 0.9),)))
    with pytest.raises(ValueError, match="step 1 velocity must be in"):
        validate(replace(spec, motif=((69, 0.3, 0.9), (72, 0.3, 0.0))))


def test_kind_budgets_are_the_android_ones() -> None:
    """The documented Android reality is what the gate enforces."""
    assert (NOTIFICATION_MIN_S, NOTIFICATION_MAX_S) == (2.0, 5.0)
    assert (RINGTONE_MIN_S, RINGTONE_MAX_S) == (3.0, 30.0)
    assert (ALARM_MIN_S, ALARM_MAX_S) == (4.0, 30.0)
    assert KINDS == ("ringtone", "notification", "alarm")
    assert len(TIMBRES) == 7
