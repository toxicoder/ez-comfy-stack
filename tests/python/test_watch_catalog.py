"""Hermetic tests for the Wear OS watch face catalog and its loader."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_raster import hex_to_rgba  # noqa: E402
from ez_watch.catalog import (  # noqa: E402
    COMPLICATION_TYPES,
    DEFAULT_DESIGN_EDGE,
    DEFAULT_STEP_GOAL,
    DESIGN_EDGE_LARGE_DP,
    DESIGN_EDGE_MIN_DP,
    MAX_COLOR_OPTIONS,
    MAX_COMPLICATION_SLOTS,
    SHAPES,
    SHAPE_RECT,
    SHAPE_ROUND,
    SHAPE_SQUARE,
    STYLES,
    STYLE_ANALOG,
    STYLE_COMPLICATION,
    STYLE_DIGITAL,
    STYLE_HYBRID,
    WATCH_FACE_CATALOG,
    ComplicationSlotSpec,
    ThemePalette,
    Typography,
    WatchFaceSpec,
    by_slug,
    categories,
    faces_for,
    load_catalog,
    write_catalog_template,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
SHIPPED_SLUGS: tuple[str, ...] = (
    "aurora-analog",
    "foundry-analog",
    "lumen-analog",
    "meridian-analog",
    "signal-digital",
    "tally-digital",
    "vector-digital",
    "harbor-hybrid",
    "atrium-hybrid",
    "transit-hybrid",
    "ledger-forward",
    "atrium-forward",
    "cadence-forward",
)


def _theme(name: str = "Ember", *colors: str) -> ThemePalette:
    """Build one colourway.

    Args:
        name: Colourway name.
        *colors: Hex colour strings.

    Returns:
        The palette.
    """
    return ThemePalette(name=name, colors=colors or ("#FF7A18", "#FFF3E0"))


def _slot(slot_id: int = 1, **overrides: object) -> ComplicationSlotSpec:
    """Build one complication slot.

    Args:
        slot_id: Slot id.
        overrides: Keys to add or replace.

    Returns:
        The slot spec.
    """
    base: dict[str, object] = {
        "slot_id": slot_id,
        "x": 10,
        "y": 20,
        "width": 80,
        "height": 40,
        "supported_types": ("SHORT_TEXT",),
    }
    base.update(overrides)
    return ComplicationSlotSpec(**base)  # type: ignore[arg-type]


def _type(**overrides: object) -> Typography:
    """Build one typography record.

    Args:
        overrides: Keys to add or replace.

    Returns:
        The typography.
    """
    base: dict[str, object] = {"family": "sans-serif", "time_size": 24, "label_size": 12}
    base.update(overrides)
    return Typography(**base)  # type: ignore[arg-type]


def _spec(**overrides: object) -> WatchFaceSpec:
    """Build one valid face with fields swapped in.

    Args:
        overrides: Keys to add or replace.

    Returns:
        The spec.
    """
    base: dict[str, object] = {
        "slug": "test-face",
        "name": "Test Face",
        "style": STYLE_ANALOG,
        "shape": SHAPE_ROUND,
        "palette": (_theme(),),
        "complications": (_slot(),),
        "typography": _type(),
    }
    base.update(overrides)
    return WatchFaceSpec(**base)  # type: ignore[arg-type]


_DELETE = object()


def _row(**overrides: object) -> dict[str, object]:
    """Build one valid new-face override row.

    Args:
        overrides: Keys to add, replace, or delete when set to ``_DELETE``.

    Returns:
        A row ready to drop into ``watch_faces``.
    """
    base: dict[str, object] = {
        "slug": "operator-face",
        "name": "Operator Face",
        "style": STYLE_ANALOG,
        "shape": SHAPE_ROUND,
        "palette": [{"name": "Ember", "colors": ["#FF7A18", "#FFF3E0"]}],
    }
    for key, value in overrides.items():
        if value is _DELETE:
            del base[key]
        else:
            base[key] = value
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


def _load(tmp_path: Path, rows: object) -> tuple[WatchFaceSpec, ...]:
    """Write ``{"watch_faces": rows}`` and merge it over the shipped catalog.

    Args:
        tmp_path: Directory for the file.
        rows: Value to put under ``watch_faces``.

    Returns:
        The merged catalog.
    """
    return load_catalog(_write(tmp_path, {"watch_faces": rows}, name="merge.json"))


def _position(catalog: tuple[WatchFaceSpec, ...], slug: str) -> int:
    """Index of one slug inside a merged catalog.

    Args:
        catalog: Merged faces.
        slug: Face slug.

    Returns:
        Position in catalog order.
    """
    return [face.slug for face in catalog].index(slug)


# ---------------------------------------------------------------------------
# The shipped catalog
# ---------------------------------------------------------------------------


def test_shipped_catalog_has_thirteen_faces_across_every_style_and_shape() -> None:
    """The set an operator can sell today is complete and varied."""
    assert tuple(face.slug for face in WATCH_FACE_CATALOG) == SHIPPED_SLUGS
    assert {face.style for face in WATCH_FACE_CATALOG} == set(STYLES)
    assert {face.shape for face in WATCH_FACE_CATALOG} == set(SHAPES)
    assert len(faces_for(STYLE_ANALOG)) == 4
    assert len(faces_for(STYLE_DIGITAL)) == 3
    assert len(faces_for(STYLE_HYBRID)) == 3
    assert len(faces_for(STYLE_COMPLICATION)) == 3


def test_shipped_faces_stay_inside_the_platform_limits() -> None:
    """No shipped face can trip a Play gate on size or vocabulary."""
    assert (DESIGN_EDGE_MIN_DP, DESIGN_EDGE_LARGE_DP) == (192, 227)
    assert DEFAULT_STEP_GOAL == 10000
    for face in WATCH_FACE_CATALOG:
        assert 1 <= len(face.palette) <= MAX_COLOR_OPTIONS, face.slug
        assert len(face.complications) <= MAX_COMPLICATION_SLOTS, face.slug
        assert len({slot.slot_id for slot in face.complications}) == len(face.complications)
        assert face.design_edge >= 1 and face.name.strip() and face.category
        assert all(tag.strip() for tag in face.tags), face.slug
        assert face.background.startswith("#"), face.slug
        for theme in face.palette:
            for color in theme.colors:
                assert hex_to_rgba(color).alpha == 255, (face.slug, color)
        for slot in face.complications:
            assert slot.slot_id >= 1 and slot.width > 0 and slot.height > 0
            assert set(slot.supported_types) <= set(COMPLICATION_TYPES)


def test_shipped_slugs_are_unique_and_package_safe() -> None:
    """Slugs seed package names, so they stay lowercase, flat, and unique."""
    slugs = [face.slug for face in WATCH_FACE_CATALOG]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert SLUG_PATTERN.match(slug), slug
        assert "/" not in slug and " " not in slug


def test_categories_are_the_sorted_self_tags() -> None:
    """The picker list is sorted, unique, and drawn from the catalog."""
    assert tuple(categories()) == ("Classic", "Dashboard", "Minimal", "Retro", "Sport")
    assert list(categories()) == sorted({face.category for face in WATCH_FACE_CATALOG})


def test_faces_for_filters_the_catalog_in_order() -> None:
    """Each style filter returns only that style, in catalog order."""
    analog = faces_for(STYLE_ANALOG)
    assert tuple(face.slug for face in analog) == (
        "aurora-analog",
        "foundry-analog",
        "lumen-analog",
        "meridian-analog",
    )
    assert all(face.style == STYLE_COMPLICATION for face in faces_for(STYLE_COMPLICATION))
    assert faces_for(STYLE_DIGITAL)[0].slug == "signal-digital"
    assert faces_for(STYLE_HYBRID)[-1].slug == "transit-hybrid"


def test_faces_for_rejects_a_style_it_cannot_emit() -> None:
    """A typo in the style filter says which values are legal."""
    with pytest.raises(ValueError, match=r"style 'orbits' not in"):
        faces_for("orbits")


def test_by_slug_answers_for_every_face_and_rejects_a_stranger() -> None:
    """Lookup is by identity for shipped faces and an error otherwise."""
    for face in WATCH_FACE_CATALOG:
        assert by_slug(face.slug) is face
    assert by_slug("cadence-forward").typography.time_size == 58
    with pytest.raises(ValueError, match="unknown watch face slug 'skeleton'"):
        by_slug("skeleton")


# ---------------------------------------------------------------------------
# Dataclass invariants
# ---------------------------------------------------------------------------


def test_new_face_defaults_match_the_documented_ones() -> None:
    """A face that states nothing else gets the published defaults."""
    face = _spec()
    assert face.show_ticks is True
    assert face.show_hands is True
    assert face.show_date is True
    assert face.show_battery is True
    assert face.show_step_complication is False
    assert face.ambient_minimal is False
    assert face.tags == ()
    assert face.category == "Minimal"
    assert face.design_edge == DEFAULT_DESIGN_EDGE == 450
    assert face.background == "#000000"


def test_configurable_is_true_while_any_layer_is_offered() -> None:
    """Every sellable face exposes at least its colourway to the editor."""
    assert by_slug("meridian-analog").configurable is True
    bare = _spec(show_ticks=False, show_date=False, show_battery=False)
    assert bare.configurable is True


def test_catalog_records_are_frozen() -> None:
    """A built catalog cannot be mutated under a running build."""
    for record, key, value in (
        (_theme(), "name", "mutated"),
        (_slot(), "slot_id", 9),
        (_type(), "family", "serif"),
        (_spec(), "name", "mutated"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(record, key, value)


def test_theme_palette_rejects_a_blank_name_or_no_colours() -> None:
    """A colourway with nothing to show is not a colourway."""
    with pytest.raises(ValueError, match="theme name is empty"):
        _theme("   ")
    with pytest.raises(ValueError, match="theme 'Ember' has no colors"):
        ThemePalette(name="Ember", colors=())


def test_slot_rejects_a_bad_id_or_an_empty_box() -> None:
    """The renderer needs a positive id and a positive box."""
    with pytest.raises(ValueError, match=r"slot_id must be >= 1, got 0"):
        _slot(slot_id=0)
    with pytest.raises(ValueError, match="slot 1 box must be positive, got 0x40"):
        _slot(width=0)
    with pytest.raises(ValueError, match="slot 1 box must be positive, got 80x0"):
        _slot(height=0)


def test_slot_rejects_no_types_or_an_unknown_type() -> None:
    """Every declared type has to be one the platform defines."""
    with pytest.raises(ValueError, match="slot 1 declares no types"):
        _slot(supported_types=())
    with pytest.raises(ValueError, match="slot 1 has unknown type 'SIREN'"):
        _slot(supported_types=("SIREN",))


def test_typography_rejects_a_blank_family_or_a_bad_size() -> None:
    """Text needs a family and a positive size to render at all."""
    with pytest.raises(ValueError, match="font family is empty"):
        _type(family=" ")
    with pytest.raises(ValueError, match="font sizes must be >= 1"):
        _type(time_size=0)
    with pytest.raises(ValueError, match="font sizes must be >= 1"):
        _type(label_size=-3)


@pytest.mark.parametrize(
    ("slug", "message"),
    [
        ("", "slug '' must match"),
        ("a", "slug 'a' must match"),
        ("-lead", "slug '-lead' must match"),
        ("UPPER", "slug 'UPPER' must match"),
        ("two words", "slug 'two words' must match"),
        ("x" * 40, "must match"),
    ],
)
def test_spec_rejects_a_slug_that_is_not_package_safe(slug: str, message: str) -> None:
    """The slug is a package name, so its shape is enforced."""
    with pytest.raises(ValueError, match=re.escape(message)):
        _spec(slug=slug)


def test_spec_rejects_a_blank_name_or_a_bad_style_or_shape() -> None:
    """Name, style, and shape are checked against the published lists."""
    with pytest.raises(ValueError, match="name is empty"):
        _spec(name="   ")
    with pytest.raises(ValueError, match=r"style 'skeleton' not in"):
        _spec(style="skeleton")
    with pytest.raises(ValueError, match=r"shape 'oval' not in"):
        _spec(shape="oval")


def test_spec_rejects_an_empty_or_oversized_palette() -> None:
    """A face sells with 1..100 colourways, matching ColorConfiguration."""
    with pytest.raises(ValueError, match="face test-face needs at least one colourway"):
        _spec(palette=())
    over = tuple(_theme(f"T{i}", "#FFFFFF") for i in range(MAX_COLOR_OPTIONS + 1))
    with pytest.raises(ValueError, match="face test-face has over 100 themes"):
        _spec(palette=over)
    assert len(_spec(palette=tuple(_theme(f"T{i}", "#FFFFFF") for i in range(100))).palette) == 100


def test_spec_rejects_too_many_slots_or_a_repeated_slot_id() -> None:
    """WO-P10 caps slots at eight and slot ids stay unique."""
    many = tuple(_slot(slot_id=index + 1) for index in range(MAX_COMPLICATION_SLOTS + 1))
    with pytest.raises(ValueError, match="face test-face has over 8 slots"):
        _spec(complications=many)
    with pytest.raises(ValueError, match="face test-face repeats slot_id 1"):
        _spec(complications=(_slot(slot_id=1), _slot(slot_id=1, x=90)))


def test_spec_rejects_a_non_positive_design_edge() -> None:
    """The virtual screen has to have a size."""
    with pytest.raises(ValueError, match="design_edge must be >= 1, got 0"):
        _spec(design_edge=0)
    assert _spec(shape=SHAPE_RECT, design_edge=400).design_edge == 400


# ---------------------------------------------------------------------------
# load_catalog
# ---------------------------------------------------------------------------


def test_load_catalog_appends_a_new_face_with_the_documented_defaults(
    tmp_path: Path,
) -> None:
    """A new slug joins the catalog with shipped defaults filled in."""
    merged = _load(tmp_path, [_row()])
    assert len(merged) == len(WATCH_FACE_CATALOG) + 1
    assert merged[: len(WATCH_FACE_CATALOG)] == WATCH_FACE_CATALOG
    added = merged[-1]
    assert added.slug == "operator-face"
    assert added.style == STYLE_ANALOG and added.shape == SHAPE_ROUND
    assert added.palette == (ThemePalette(name="Ember", colors=("#FF7A18", "#FFF3E0")),)
    assert added.complications == ()
    assert added.typography == Typography("sans-serif", 48, 20)
    assert added.show_ticks is True and added.show_hands is True
    assert added.show_date is True and added.show_battery is True
    assert added.show_step_complication is False and added.ambient_minimal is False
    assert added.tags == () and added.category == "Minimal"
    assert added.design_edge == DEFAULT_DESIGN_EDGE
    assert added.background == "#000000"


def test_load_catalog_overrides_only_the_keys_a_row_states(tmp_path: Path) -> None:
    """A partial row keeps every other field of the shipped face."""
    shipped = by_slug("aurora-analog")
    merged = _load(
        tmp_path,
        [_row(slug="aurora-analog", name="Aurora (retuned)", palette=_DELETE)],
    )
    assert len(merged) == len(WATCH_FACE_CATALOG)
    assert merged[_position(merged, "aurora-analog")] == replace(
        shipped, name="Aurora (retuned)"
    )


def test_load_catalog_honours_every_optional_key(tmp_path: Path) -> None:
    """The full field set round-trips from JSON into the spec."""
    merged = _load(
        tmp_path,
        [
            _row(
                style=STYLE_COMPLICATION,
                shape=SHAPE_SQUARE,
                palette=[
                    {"name": "Volt", "colors": ["#C6FF00", "#FFFFFF"]},
                    {"name": "Coral", "colors": ["#FF6B4A"]},
                ],
                complications=[
                    {
                        "slot_id": 4,
                        "x": 8,
                        "y": 12,
                        "width": 90,
                        "height": 30,
                        "supported_types": ["SHORT_TEXT", "RANGED_VALUE"],
                    },
                    {
                        "slot_id": 7,
                        "x": 8,
                        "y": 60,
                        "width": 90,
                        "height": 30,
                        "supported_types": ["EMPTY"],
                    },
                ],
                typography=[{"family": "serif", "time_size": 40, "label_size": 14}],
                show_ticks=False,
                show_hands=False,
                show_date=False,
                show_battery=False,
                show_step_complication=True,
                tags=[" Sport ", "wear", "sport"],
                category="Sport",
                ambient_minimal=True,
                design_edge=400,
                background="#101010",
            )
        ],
    )
    added = merged[-1]
    assert added.style == STYLE_COMPLICATION and added.shape == SHAPE_SQUARE
    assert added.palette == (
        ThemePalette(name="Volt", colors=("#C6FF00", "#FFFFFF")),
        ThemePalette(name="Coral", colors=("#FF6B4A",)),
    )
    assert added.complications == (
        ComplicationSlotSpec(4, 8, 12, 90, 30, ("SHORT_TEXT", "RANGED_VALUE")),
        ComplicationSlotSpec(7, 8, 60, 90, 30, ("EMPTY",)),
    )
    assert added.typography == Typography("serif", 40, 14)
    assert added.show_ticks is False
    assert added.show_hands is False
    assert added.show_date is False
    assert added.show_battery is False
    assert added.show_step_complication is True
    assert added.tags == ("Sport", "wear", "sport")
    assert added.category == "Sport"
    assert added.ambient_minimal is True
    assert added.design_edge == 400
    assert added.background == "#101010"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("yes", True), ("ON", True), ("1", True), ("true", True), ("no", False), ("Off", False)],
)
def test_load_catalog_reads_yes_no_strings_as_flags(
    tmp_path: Path, raw: str, expected: bool
) -> None:
    """An operator may spell a switch either way in JSON."""
    merged = _load(tmp_path, [_row(slug="aurora-analog", show_ticks=raw)])
    assert merged[_position(merged, "aurora-analog")].show_ticks is expected


def test_load_catalog_keeps_catalog_order_and_appends_new_faces(tmp_path: Path) -> None:
    """An override replaces in place; a new slug lands last."""
    merged = _load(
        tmp_path,
        [
            _row(slug="cadence-forward", name="Cadence (retuned)"),
            _row(slug="operator-face"),
            _row(slug="another-face", name="Another Face"),
        ],
    )
    assert [face.slug for face in merged] == [*SHIPPED_SLUGS, "operator-face", "another-face"]
    assert merged[_position(merged, "cadence-forward")].name == "Cadence (retuned)"
    assert merged[_position(merged, "cadence-forward")] is not by_slug("cadence-forward")


def test_load_catalog_trims_the_slug_it_merges_on(tmp_path: Path) -> None:
    """Whitespace around a slug still finds the shipped face."""
    merged = _load(tmp_path, [_row(slug="  aurora-analog  ", name="Padded")])
    assert len(merged) == len(WATCH_FACE_CATALOG)
    assert merged[_position(merged, "aurora-analog")].name == "Padded"


def test_load_catalog_accepts_a_bare_list_and_a_watch_faces_object(
    tmp_path: Path,
) -> None:
    """Either document shape is a catalog."""
    rows = [_row(slug="aurora-analog", name="Bare")]
    from_list = load_catalog(_write(tmp_path, rows, name="list.json"))
    from_object = load_catalog(_write(tmp_path, {"watch_faces": rows}, name="object.json"))
    assert from_list == from_object
    assert from_list[_position(from_list, "aurora-analog")].name == "Bare"


def test_load_catalog_keeps_shipped_data_when_a_child_list_is_empty(
    tmp_path: Path,
) -> None:
    """An empty palette, slot, or type list means "leave it alone"."""
    shipped = by_slug("foundry-analog")
    merged = _load(
        tmp_path,
        [_row(slug="foundry-analog", palette=[], complications=[], typography=[])],
    )
    kept = merged[_position(merged, "foundry-analog")]
    assert kept.palette == shipped.palette
    assert kept.complications == shipped.complications
    assert kept.typography == shipped.typography


def test_template_round_trips_through_the_loader(tmp_path: Path) -> None:
    """The file the operator edits is a file the loader reads back unchanged."""
    path = write_catalog_template(tmp_path / "nested" / "template.json")
    assert isinstance(path, int) and path > 0
    file_path = tmp_path / "nested" / "template.json"
    assert file_path.is_file()
    assert path == len(file_path.read_bytes())
    document = json.loads(file_path.read_text(encoding="utf-8"))
    assert sorted(document) == ["readme", "watch_faces"]
    assert document["readme"]
    assert len(document["watch_faces"]) == 1
    merged = load_catalog(str(file_path))
    assert merged[: len(WATCH_FACE_CATALOG)] == WATCH_FACE_CATALOG
    assert merged[0] == WATCH_FACE_CATALOG[0]


def test_template_carries_every_field_the_loader_accepts(tmp_path: Path) -> None:
    """The example states each key, so an operator can copy any line."""
    write_catalog_template(tmp_path / "template.json")
    row = json.loads((tmp_path / "template.json").read_text(encoding="utf-8"))["watch_faces"][0]
    assert sorted(row) == sorted(
        {
            "slug",
            "name",
            "style",
            "shape",
            "palette",
            "complications",
            "typography",
            "show_ticks",
            "show_hands",
            "show_date",
            "show_battery",
            "show_step_complication",
            "tags",
            "category",
            "ambient_minimal",
            "design_edge",
            "background",
        }
    )
    assert sorted(row["complications"][0]) == sorted(
        ["slot_id", "x", "y", "width", "height", "supported_types"]
    )
    assert sorted(row["typography"][0]) == sorted(["family", "time_size", "label_size"])
    assert sorted(row["palette"][0]) == ["colors", "name"]


def test_template_is_plain_ascii(tmp_path: Path) -> None:
    """Nothing in the operator file trips the punctuation gate."""
    write_catalog_template(tmp_path / "template.json")
    text = (tmp_path / "template.json").read_text(encoding="utf-8")
    assert text.isascii()
    assert text.endswith("\n")


# ---------------------------------------------------------------------------
# load_catalog failure paths
# ---------------------------------------------------------------------------


def test_load_catalog_reports_a_file_it_cannot_read(tmp_path: Path) -> None:
    """A typo in the path names the file that is not there."""
    missing = tmp_path / "nowhere.json"
    with pytest.raises(ValueError, match="cannot read catalog"):
        load_catalog(str(missing))
    with pytest.raises(ValueError, match="cannot read catalog"):
        load_catalog(tmp_path)


def test_load_catalog_reports_a_file_that_is_not_json(tmp_path: Path) -> None:
    """A half-edited file says so instead of raising a raw decoder error."""
    with pytest.raises(ValueError, match="is not valid JSON"):
        load_catalog(_write(tmp_path, "{ nope", name="bad.json"))


@pytest.mark.parametrize("text", ["null", "3", '"faces"', "true"])
def test_load_catalog_rejects_a_document_that_is_not_a_row_list(
    tmp_path: Path, text: str
) -> None:
    """Only a list, or an object holding one, is a catalog."""
    with pytest.raises(ValueError, match="must hold a list or an object with watch_faces"):
        load_catalog(_write(tmp_path, text, name="shape.json"))


@pytest.mark.parametrize("text", ['{"watch_faces": {}}', '{"watch_faces": "rows"}'])
def test_load_catalog_rejects_an_inner_list_that_is_not_a_list(
    tmp_path: Path, text: str
) -> None:
    """``watch_faces`` itself has to be a list."""
    with pytest.raises(ValueError, match="watch_faces must be a list"):
        load_catalog(_write(tmp_path, text, name="inner.json"))


def test_load_catalog_accepts_an_empty_set_of_rows(tmp_path: Path) -> None:
    """A catalog file with no rows is the shipped catalog."""
    assert load_catalog(_write(tmp_path, "[]", name="empty.json")) == WATCH_FACE_CATALOG
    assert load_catalog(_write(tmp_path, "{}", name="bare.json")) == WATCH_FACE_CATALOG


@pytest.mark.parametrize("rows", [["x"], [None], [42], [{"name": "no slug"}], [{"slug": " "}]])
def test_load_catalog_rejects_a_row_that_is_not_an_object_with_a_slug(
    tmp_path: Path, rows: list[object]
) -> None:
    """Each row is an object that states a slug."""
    expected = (
        "each watch face row must be an object"
        if not isinstance(rows[0], dict)
        else "needs a slug"
    )
    with pytest.raises(ValueError, match=expected):
        _load(tmp_path, rows)


@pytest.mark.parametrize("missing", ["name", "style", "shape", "palette"])
def test_new_face_row_must_state_every_required_key(tmp_path: Path, missing: str) -> None:
    """A brand new face states slug, name, style, shape, and palette."""
    with pytest.raises(ValueError, match="new face row is missing required keys"):
        _load(tmp_path, [_row(**{missing: _DELETE})])


def test_load_catalog_rejects_a_key_the_loader_does_not_know(tmp_path: Path) -> None:
    """A typo is a typo, whether it is on a new face or an override."""
    with pytest.raises(ValueError, match=r"has unknown keys \['colourways'\]"):
        _load(tmp_path, [_row(colourways=[])])
    with pytest.raises(ValueError, match=r"has unknown keys \['zzz'\]"):
        _load(tmp_path, [{"slug": "aurora-analog", "zzz": 1}])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"name": 3}, "name must be a string, got int"),
        ({"style": None}, "style must be a string, got NoneType"),
        ({"shape": ["round"]}, "shape must be a string, got list"),
        ({"category": 1.5}, "category must be a string, got float"),
        ({"background": False}, "background must be a string, got bool"),
        ({"design_edge": "450"}, "design_edge must be an integer"),
        ({"design_edge": True}, "design_edge must be an integer, got True"),
        ({"design_edge": 1.5}, "design_edge must be an integer, got 1.5"),
        ({"design_edge": None}, "design_edge must be an integer, got None"),
        ({"show_ticks": 1}, "show_ticks must be a boolean, got 1"),
        ({"show_hands": ["yes"]}, "show_hands must be a boolean"),
        ({"tags": "sport"}, "tags must be a list, got str"),
        ({"tags": [1]}, "tags must hold strings, got 1"),
        ({"tags": None}, "tags must be a list, got NoneType"),
        ({"palette": {}}, "palette must be a list, got dict"),
        ({"palette": ["Ember"]}, "palette must hold objects, got 'Ember'"),
        ({"palette": [{"colors": ["#FFF"]}]}, "palette entry needs a name and colors"),
        ({"palette": [{"name": " "}]}, "palette entry needs a name and colors"),
        ({"palette": [{"name": "x", "colors": []}]}, "palette entry needs a name and colors"),
        ({"complications": "slot"}, "complications must be a list, got str"),
        ({"complications": [1]}, "complications must hold objects, got 1"),
        ({"typography": "serif"}, "typography must be a list, got str"),
        ({"typography": [3]}, "typography must hold objects, got 3"),
        ({"typography": [{"family": 3}]}, "family must be a string, got int"),
        ({"typography": [{"time_size": "big"}]}, "time_size must be an integer"),
        ({"typography": [{"label_size": True}]}, "label_size must be an integer, got True"),
    ],
)
def test_load_catalog_names_the_field_that_broke(
    tmp_path: Path, overrides: dict[str, object], message: str
) -> None:
    """Every malformed row fails with the key and the value that caused it."""
    with pytest.raises(ValueError, match=re.escape(message)):
        _load(tmp_path, [_row(slug="aurora-analog", **overrides)])


def test_load_catalog_validates_rows_it_builds(tmp_path: Path) -> None:
    """A row that parses still has to build a legal face."""
    with pytest.raises(ValueError, match=r"slot_id must be >= 1, got 0"):
        _load(
            tmp_path,
            [
                _row(
                    slug="aurora-analog",
                    complications=[
                        {
                            "slot_id": 0,
                            "x": 0,
                            "y": 0,
                            "width": 10,
                            "height": 10,
                            "supported_types": ["SHORT_TEXT"],
                        }
                    ],
                )
            ],
        )
    with pytest.raises(ValueError, match="slot 1 declares no types"):
        _load(
            tmp_path,
            [
                _row(
                    slug="aurora-analog",
                    complications=[{"slot_id": 1, "x": 0, "y": 0, "width": 10, "height": 10}],
                )
            ],
        )
    with pytest.raises(ValueError, match="face aurora-analog repeats slot_id 1"):
        row = {
            "slot_id": 1,
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 10,
            "supported_types": ["SHORT_TEXT"],
        }
        _load(tmp_path, [_row(slug="aurora-analog", complications=[row, dict(row)])])
    with pytest.raises(ValueError, match="style 'orbits' not in"):
        _load(tmp_path, [_row(slug="aurora-analog", style="orbits")])
    with pytest.raises(ValueError, match="slot 1 has unknown type 'GLYPH'"):
        _load(
            tmp_path,
            [
                _row(
                    slug="aurora-analog",
                    complications=[
                        {
                            "slot_id": 1,
                            "x": 0,
                            "y": 0,
                            "width": 10,
                            "height": 10,
                            "supported_types": ["GLYPH"],
                        }
                    ],
                )
            ],
        )


def test_load_catalog_rejects_a_shape_that_is_not_a_round_face(tmp_path: Path) -> None:
    """Only the three published shapes build."""
    with pytest.raises(ValueError, match=r"shape 'pill' not in"):
        _load(tmp_path, [_row(shape="pill")])
    assert _load(tmp_path, [_row(shape=SHAPE_RECT)])[-1].shape == SHAPE_RECT
