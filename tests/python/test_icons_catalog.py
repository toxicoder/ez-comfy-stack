"""Hermetic tests for the icon catalog, its guards, and JSON overrides."""

from __future__ import annotations

import json
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_icons.catalog import (  # noqa: E402
    BACKGROUND_STYLES,
    ICON_CATALOG,
    ICON_STATUSES,
    Background,
    IconSpec,
    apply_status,
    by_slug,
    categories,
    glyph_names,
    icons_for,
    load_catalog,
    new_icon_scaffold,
    parse_background,
    select,
    write_catalog_template,
)

MINIMUM_ENTRIES = 60
MINIMUM_CATEGORIES = 30
SAMPLE_ROW: dict[str, object] = {
    "slug": "transit-rail",
    "name": "Rail Timetable",
    "package": "com.railwise.timetable",
    "component": ".MainActivity",
    "category": "travel",
    "tags": ["rail", "commute"],
    "glyph": "train",
    "palette": ["#F5F8FA", "#9BD6F0"],
    "background": "linear:#101C2A>#3E6B8F",
    "keywords": "train schedule commute",
    "status": "new",
    "notes": "Ships with the transit lane.",
}


def spec(**overrides: object) -> IconSpec:
    """Build one spec with sane defaults and the given overrides.

    Args:
        overrides: Field values to replace.

    Returns:
        A validated spec.
    """
    fields: dict[str, object] = {
        "slug": "probe-icon",
        "name": "Probe Icon",
        "package": "com.probe.app",
        "glyph": "star",
    }
    fields.update(overrides)
    return IconSpec(**fields)  # type: ignore[arg-type]


def test_catalog_is_broad_and_deduplicated() -> None:
    assert len(ICON_CATALOG) >= MINIMUM_ENTRIES
    assert len(categories()) >= MINIMUM_CATEGORIES
    assert len({entry.slug for entry in ICON_CATALOG}) == len(ICON_CATALOG)
    assert len({entry.package for entry in ICON_CATALOG}) == len(ICON_CATALOG)
    assert {entry.status for entry in ICON_CATALOG} == set(ICON_STATUSES)


def test_catalog_spans_launcher_demand() -> None:
    wanted = {
        "messaging",
        "phone",
        "camera",
        "gallery",
        "maps",
        "weather",
        "music",
        "podcast",
        "video",
        "social",
        "mail",
        "calendar",
        "clock",
        "notes",
        "tasks",
        "finance",
        "fitness",
        "health",
        "food",
        "travel",
        "shopping",
        "news",
        "reading",
        "games",
        "utilities",
        "files",
        "settings",
        "developer",
        "smarthome",
        "car",
        "kids",
        "education",
        "security",
        "account",
        "navigation",
    }
    assert wanted <= set(categories())
    assert by_slug("banking-ledger") is not None


def test_catalog_carries_palette_variants_per_glyph() -> None:
    reused = {entry.glyph for entry in ICON_CATALOG}
    shared = [glyph for glyph in reused if len({entry.palette for entry in ICON_CATALOG if entry.glyph == glyph}) > 1]
    assert len(shared) >= 5


def test_no_entry_names_a_legal_entity_or_internal_caps() -> None:
    for entry in ICON_CATALOG:
        assert entry.name.strip() == entry.name
        assert "Inc" not in entry.name and "Ltd" not in entry.name
        assert all(token.islower() or token[0].isupper() for token in entry.name.split())


def test_spec_is_frozen_and_normalises_text() -> None:
    entry = spec(slug="  spaced-slug  ", name="  Spaced Name  ")
    assert entry.slug == "spaced-slug"
    assert entry.name == "Spaced Name"
    with pytest.raises(FrozenInstanceError):
        entry.name = "Other"  # type: ignore[misc]


def test_spec_properties() -> None:
    entry = spec(
        slug="chat-bubble",
        name="Chat Bubble",
        component=".MainActivity",
        background="linear:#101C2A>#3E6B8F",
        tags=("chat",),
        keywords="dm talk",
    )
    assert entry.drawable == "chat_bubble"
    assert entry.themed_drawable == "chat_bubble_themed"
    assert entry.parsed_background == Background(style="linear", top="#101C2A", bottom="#3E6B8F")
    assert entry.component_info == "ComponentInfo{com.probe.app/.MainActivity}"
    assert entry.search_terms == ("bubble", "chat", "dm", "talk")


def test_spec_without_component_maps_by_package_only() -> None:
    assert spec().component_info == ""


def test_spec_rejects_malformed_fields() -> None:
    with pytest.raises(ValueError, match="slug is empty"):
        spec(slug="   ")
    with pytest.raises(ValueError, match="slug 'Bad Slug' is malformed"):
        spec(slug="Bad Slug")
    with pytest.raises(ValueError, match="name is empty"):
        spec(name=" ")
    with pytest.raises(ValueError, match="package is empty"):
        spec(package=" ")
    with pytest.raises(ValueError, match="package 'nodots' is malformed"):
        spec(package="nodots")
    with pytest.raises(ValueError, match="glyph '9bad' is malformed"):
        spec(glyph="9bad")
    with pytest.raises(ValueError, match="component '-nope' is malformed"):
        spec(component="-nope")
    with pytest.raises(ValueError, match="category is empty"):
        spec(category=" ")


def test_spec_accepts_an_empty_component() -> None:
    assert spec(component="  ").component == ""


def test_spec_rejects_bad_palette_and_status() -> None:
    with pytest.raises(ValueError, match="palette is empty"):
        spec(palette=())
    with pytest.raises(ValueError, match="palette colour 'nope' is not hex"):
        spec(palette=("nope",))
    with pytest.raises(ValueError, match="status 'beta' is unknown"):
        spec(status="beta")
    with pytest.raises(ValueError, match="background colour"):
        spec(background="#gggggg")


@pytest.mark.parametrize("style", BACKGROUND_STYLES)
def test_parse_background_every_style(style: str) -> None:
    parsed = parse_background(f"{style}:#010203>#040506" if style != "solid" else "#010203")
    assert parsed.style == style
    assert parsed.top == "#010203"
    assert parsed.bottom == "" if style == "solid" else "#040506"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("#abc", Background("solid", "#abc", "")),
        ("#a1b2c3", Background("solid", "#a1b2c3", "")),
        ("#a1b2c3d4", Background("solid", "#a1b2c3d4", "")),
        ("#a1b2c3>#d4e5f6", Background("linear", "#a1b2c3", "#d4e5f6")),
        ("  radial:#a1b2c3>#d4e5f6  ", Background("radial", "#a1b2c3", "#d4e5f6")),
    ],
)
def test_parse_background_shapes(text: str, expected: Background) -> None:
    assert parse_background(text) == expected


def test_parse_background_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="background style 'diagonal' is unknown"):
        parse_background("diagonal:#010203>#040506")
    with pytest.raises(ValueError, match="carries too many colours"):
        parse_background("#010203>#040506>#070809")
    with pytest.raises(ValueError, match="background colour 'zzz' is not hex"):
        parse_background("zzz")
    with pytest.raises(ValueError, match="background colour 'zzz' is not hex"):
        parse_background("#010203>zzz")


def test_categories_and_glyphs_are_ordered() -> None:
    assert categories([spec(category="b"), spec(category="a"), spec(category="b")]) == ("b", "a")
    assert glyph_names([spec(glyph="star"), spec(glyph="bolt"), spec(glyph="star")]) == ("bolt", "star")


def test_by_slug_and_icons_for() -> None:
    assert by_slug("chat-bubble") is not None
    assert by_slug("no-such-slug") is None
    first, second = spec(category="mail"), spec(category="Mail")
    assert icons_for(" mail ", [first, second]) == (first, second)
    assert icons_for("nothing", [first]) == ()


def test_select_keeps_requested_order() -> None:
    chosen = select(ICON_CATALOG, only_slugs=["weather-sun", "chat-bubble"])
    assert [entry.slug for entry in chosen] == ["weather-sun", "chat-bubble"]


def test_select_filters_by_category() -> None:
    chosen = select(ICON_CATALOG, categories_filter=["Weather"])
    assert chosen and all(entry.category == "weather" for entry in chosen)


def test_select_rejects_unknown_slug_and_empty_result() -> None:
    with pytest.raises(ValueError, match="unknown slug"):
        select(ICON_CATALOG, only_slugs=["nope"])
    with pytest.raises(ValueError, match="matched no icons"):
        select(ICON_CATALOG, categories_filter=["nope"])


def test_load_catalog_merges_by_slug(tmp_path: Path) -> None:
    path = tmp_path / "override.json"
    path.write_text(json.dumps({"icons": [dict(SAMPLE_ROW)]}), encoding="utf-8")
    merged = load_catalog(path)
    assert len(merged) == len(ICON_CATALOG) + 1
    added = by_slug("transit-rail", merged)
    assert added is not None, "the override row lands under its own slug"
    assert added.package == "com.railwise.timetable"


def test_load_catalog_replaces_in_place(tmp_path: Path) -> None:
    row = dict(SAMPLE_ROW)
    row["slug"] = "chat-bubble"
    row["status"] = "redesign"
    path = tmp_path / "override.json"
    path.write_text(json.dumps([row]), encoding="utf-8")
    merged = load_catalog(path, base=[spec(slug="chat-bubble"), spec(slug="other")])
    assert [entry.slug for entry in merged] == ["chat-bubble", "other"]
    assert merged[0].status == "redesign"
    assert merged[0].name == "Rail Timetable"


def test_load_catalog_accepts_a_bare_array(tmp_path: Path) -> None:
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([dict(SAMPLE_ROW)]), encoding="utf-8")
    assert len(load_catalog(path, base=())) == 1


def test_load_catalog_keeps_new_slugs_sorted(tmp_path: Path) -> None:
    rows = [dict(SAMPLE_ROW), {**SAMPLE_ROW, "slug": "alpha-new"}]
    path = tmp_path / "rows.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    merged = load_catalog(path, base=())
    assert [entry.slug for entry in merged] == ["alpha-new", "transit-rail"]


def test_load_catalog_defaults_omitted_fields(tmp_path: Path) -> None:
    path = tmp_path / "min.json"
    path.write_text(json.dumps([{"slug": "bare-entry", "package": "com.bare.app"}]), encoding="utf-8")
    entry = load_catalog(path, base=())[0]
    assert entry.name == "Bare Entry"
    assert entry.category == "utilities"
    assert entry.glyph == "disc"
    assert entry.palette == ("#F2F5F7", "#7FC8F8")
    assert entry.background == "#1B2833"
    assert entry.status == "stable"
    assert entry.tags == ()


def test_load_catalog_reads_every_field(tmp_path: Path) -> None:
    path = tmp_path / "full.json"
    path.write_text(json.dumps([dict(SAMPLE_ROW)]), encoding="utf-8")
    entry = load_catalog(path, base=())[0]
    assert entry.component == ".MainActivity"
    assert entry.notes == "Ships with the transit lane."
    assert entry.tags == ("rail", "commute")
    assert entry.keywords == "train schedule commute"


def test_load_catalog_rejects_bad_documents(tmp_path: Path) -> None:
    cases = {
        "scalar.json": "7",
        "noicons.json": json.dumps({"pack_name": "x"}),
        "badicons.json": json.dumps({"icons": "nope"}),
        "row-not-object.json": json.dumps(["nope"]),
        "noslug.json": json.dumps([{"package": "com.a.b"}]),
        "emptypkg.json": json.dumps([{"slug": "a-b", "package": " "}]),
        "badhex.json": json.dumps([{"slug": "a-b", "package": "com.a.b", "palette": ["nope"]}]),
        "duplicates.json": json.dumps([dict(SAMPLE_ROW), dict(SAMPLE_ROW)]),
        "slug-not-string.json": json.dumps([{"slug": 5, "package": "com.a.b"}]),
        "tags-not-string.json": json.dumps(
            [{"slug": "a-b", "package": "com.a.b", "tags": [1]}]
        ),
        "tags-scalar.json": json.dumps([{"slug": "a-b", "package": "com.a.b", "tags": 5}]),
        "bad-status.json": json.dumps([{"slug": "a-b", "package": "com.a.b", "status": "beta"}]),
        "bad-background.json": json.dumps(
            [{"slug": "a-b", "package": "com.a.b", "background": "diagonal:#010203"}]
        ),
    }
    for name, body in cases.items():
        path = tmp_path / name
        path.write_text(body, encoding="utf-8")
        with pytest.raises(ValueError):
            load_catalog(path, base=())


def test_load_catalog_splits_string_tokens(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text(
        json.dumps(
            [{"slug": "a-b", "package": "com.a.b", "tags": "one, two;three four"}]
        ),
        encoding="utf-8",
    )
    assert load_catalog(path, base=())[0].tags == ("one", "two", "three", "four")


def test_load_catalog_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        load_catalog(tmp_path / "absent.json")


def test_write_catalog_template_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "starter" / "icons.json"
    written = write_catalog_template(path)
    assert written > 0
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["pack_name"] == "My Icon Pack"
    merged = load_catalog(path, base=())
    assert merged[0].slug == "chat-bubble"
    assert merged[0].glyph == "speech"


def test_new_icon_scaffold_prints_a_ready_row() -> None:
    text = new_icon_scaffold(
        "transit-rail",
        "Rail Timetable",
        "com.railwise.timetable",
        glyph="train",
        category="travel",
        component=".MainActivity",
        palette=("#F5F8FA", "#9BD6F0", "#FFFFFF"),
        background="radial:#101C2A>#3E6B8F",
        keywords="rail commute",
        tags=("rail",),
        status="new",
        notes="Added for the transit lane.",
    )
    row = json.loads(text)
    assert row["slug"] == "transit-rail"
    assert row["component"] == ".MainActivity"
    assert row["status"] == "new"
    assert row["glyph"] == "train"
    assert text == text.strip()


def test_new_icon_scaffold_writes_a_file(tmp_path: Path) -> None:
    path = tmp_path / "row.json"
    text = new_icon_scaffold("transit-rail", "Rail Timetable", "com.railwise.timetable", path=path)
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(text)
    assert len(load_catalog(path, base=())) == 1


def test_new_icon_scaffold_rejects_a_bad_row() -> None:
    with pytest.raises(ValueError, match="package is empty"):
        new_icon_scaffold("a-b", "A B", " ")


def test_apply_status_flags_a_redesign() -> None:
    entry = spec()
    assert apply_status(entry, "redesign").status == "redesign"
    assert entry.status == "stable"
    with pytest.raises(ValueError, match="status 'beta' is unknown"):
        apply_status(entry, "beta")  # type: ignore[arg-type]


def test_new_icon_scaffold_rejects_an_unknown_glyph() -> None:
    with pytest.raises(ValueError, match="is not a registered recipe"):
        new_icon_scaffold("a-b", "A B", "com.a.b", glyph="no-such-glyph")
