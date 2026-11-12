"""Hermetic tests for the Watch Face Format project generator.

Every build here is pure Python and writes only inside ``tmp_path``: no
Gradle, no Android SDK, no network. The heavy path is exercised once through a
module-scoped fixture and the rest of the suite asserts on the artefacts that
build left behind, so the file stays quick under coverage.
"""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_raster import BLACK, Canvas, Rgba, hex_to_rgba  # noqa: E402
from ez_watch import project, validate  # noqa: E402
from ez_watch.catalog import (  # noqa: E402
    COMPLICATION_TYPES,
    ComplicationSlotSpec,
    ThemePalette,
    Typography,
    WatchFaceSpec,
    by_slug,
)
from ez_watch.project import (  # noqa: E402
    DEFAULT_PREVIEW_EDGE,
    DEFAULT_TOOL_VERSION,
    MIN_PREVIEW_EDGE,
    STORE_ASSET_DIR,
    ProjectResult,
    _application_id,
    _article,
    _build_gradle,
    _clip,
    _document,
    _escape,
    _face_canvas,
    _feature_plate,
    _full_description,
    _listing,
    _listing_markdown,
    _manifest_json,
    _manifest_xml,
    _nest,
    _open,
    _Painter,
    _paint_face,
    _paint_slot,
    _preview_digits,
    _readme,
    _scaled_for_edge,
    _select,
    _settings_gradle,
    _strings_xml,
    _tag,
    _theme_colors,
    _watch_face_info_xml,
    _watch_face_shapes_xml,
    build_face,
    build_face_pack,
    build_parser,
    hand_canvas,
    main,
)
from ez_watch.scene import WFF_VERSION_API, box_of  # noqa: E402

BASELINE_SLUG = "meridian-analog"
"""Round two-slot analog face: cheapest full build, and it validates clean."""

DIGITAL_SLUG = "vector-digital"
"""Square digital face with no hands, used for the shape and hand branches."""

BASELINE_FILES = (
    "AndroidManifest.xml",
    "README.md",
    "build.gradle",
    "manifest.json",
    "res/drawable/hand_hour.png",
    "res/drawable/hand_minute.png",
    "res/drawable/hand_second.png",
    "res/drawable/preview.png",
    "res/raw/watchface.xml",
    "res/values/strings.xml",
    "res/xml/watch_face_info.xml",
    "settings.gradle",
    "store-assets/feature-graphic.png",
    "store-assets/icon.png",
    "store-assets/screenshots/meridian-analog-theme-0.png",
    "store-assets/screenshots/meridian-analog-theme-1.png",
    "store-assets/screenshots/meridian-analog-theme-2.png",
    "store-listing.md",
)
"""Exact tree one round three-colourway analog face must emit."""

ANDROID_NS = "http://schemas.android.com/apk/res/android"
"""Namespace the manifest qualifies its attributes with."""


def _spec(**overrides: object) -> WatchFaceSpec:
    """Return the baseline face with a few fields changed.

    Args:
        **overrides: Fields to replace on the baseline spec.

    Returns:
        The patched spec.
    """
    return replace(by_slug(BASELINE_SLUG), **overrides)  # type: ignore[arg-type]


def _painter(edge: int = 64) -> tuple[Canvas, _Painter]:
    """Start a small opaque canvas with a painter bound to it.

    Args:
        edge: Square edge of the canvas.

    Returns:
        The canvas and its painter.
    """
    canvas = Canvas(edge, edge, fill=BLACK)
    return canvas, _Painter(canvas)


def _colors() -> tuple[Rgba, Rgba, Rgba]:
    """Pick the three drawing colours of the baseline face.

    Returns:
        ``(accent, secondary, text)``.
    """
    return _theme_colors(by_slug(BASELINE_SLUG), 0)


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory) -> tuple[ProjectResult, Path]:
    """Build the baseline face once for the whole module.

    Args:
        tmp_path_factory: pytest's session-wide temporary directories.

    Returns:
        The build result and the project folder it wrote.
    """
    out = tmp_path_factory.mktemp("base")
    result = build_face(by_slug(BASELINE_SLUG), out, preview_edge=MIN_PREVIEW_EDGE)
    return result, Path(result.out_dir)


# --------------------------------------------------------------------------
# helpers that need no build
# --------------------------------------------------------------------------


def test_constants_match_the_play_rules_they_document() -> None:
    """The published numbers the module advertises are the ones it uses."""
    assert DEFAULT_TOOL_VERSION == "1.0.0"
    assert DEFAULT_PREVIEW_EDGE == 450
    assert MIN_PREVIEW_EDGE == 384
    assert STORE_ASSET_DIR == "store-assets"
    assert DEFAULT_PREVIEW_EDGE >= MIN_PREVIEW_EDGE


def test_escape_quotes_the_three_xml_metacharacters() -> None:
    """Ampersand, angle brackets, and nothing else are rewritten."""
    assert _escape("R&D <beta> 100%") == "R&amp;D &lt;beta&gt; 100%"
    assert _escape("plain") == "plain"


def test_clip_cuts_on_a_word_edge_and_falls_back_to_a_hard_cut() -> None:
    """A long field is shortened, at a space when one exists."""
    assert _clip("short", 30) == "short"
    assert _clip("alpha beta gamma delta", 12) == "alpha beta"
    assert _clip("aaaaaaaaaaaaaaaa", 4) == "aaaa"


def test_tag_open_nest_and_document_render_deterministic_xml() -> None:
    """Attributes sort alphabetically, so the same input always matches."""
    assert _tag("Preview", {"value": "@drawable/preview", "alpha": "1"}) == (
        '<Preview alpha="1" value="@drawable/preview" />'
    )
    assert _tag("WatchFaceInfo", {}) == "<WatchFaceInfo />"
    assert _open("application", {"android:hasCode": "false"}) == (
        '<application android:hasCode="false">'
    )
    assert _open("manifest", {}) == "<manifest>"
    assert _nest("a", {}, ["<b />"]) == ("<a>", "  <b />", "</a>")
    text = _document("resources", {}, ['<string name="a">A</string>'])
    assert text.startswith('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n')
    assert text.endswith("</resources>\n")


def test_build_gradle_pins_the_api_the_format_version_implies() -> None:
    """Each declared version selects its own minimum SDK."""
    text = _build_gradle("com.example.face", 4)
    assert 'namespace "com.example.face"' in text
    assert "compileSdk 36" in text
    assert "minSdk 36" in text and "targetSdk 36" in text
    assert "minifyEnabled false" in text
    assert _build_gradle("com.example.face", 1).count("minSdk 33") == 1
    for version, api in WFF_VERSION_API.items():
        assert f"minSdk {api}" in _build_gradle("com.example.face", version)
    assert _settings_gradle() == 'rootProject.name = "watchface"\n'


def test_manifest_xml_declares_a_code_free_watch_package() -> None:
    """``hasCode="false"`` is the whole point of the shell."""
    text = _manifest_xml(4, "9.9.9")
    assert '<application android:hasCode="false" android:label="@string/watch_face_name">' in text
    assert "com.google.android.wearable.standalone" in text
    assert '<property android:name="com.google.wear.watchface.format.version" android:value="4" />' in text
    assert "ez-comfy-stack-9.9.9" in text
    assert '<uses-feature android:name="android.hardware.type.watch" />' in text
    assert "<activity" not in text and "<service" not in text
    root = ElementTree.fromstring(text)
    assert root.tag == "manifest"
    application = root.find("application")
    assert application is not None
    assert application.get(f"{{{ANDROID_NS}}}hasCode") == "false"
    assert application.get(f"{{{ANDROID_NS}}}label") == "@string/watch_face_name"


def test_watch_face_info_xml_gates_flavours_on_the_format_version() -> None:
    """Flavour support is a version 2 feature and nothing older may claim it."""
    spec = by_slug(BASELINE_SLUG)
    rich = _watch_face_info_xml(spec, flavors=True)
    plain = _watch_face_info_xml(spec, flavors=False)
    assert '<FlavorsSupported value="true" />' in rich
    assert "FlavorsSupported" not in plain
    assert '<Preview value="@drawable/preview" />' in plain
    assert '<Category value="Classic" />' in plain
    assert '<Editable value="true" />' in plain
    assert '<AvailableInRetail value="true" />' in plain
    assert '<MultipleInstancesAllowed value="true" />' in plain
    assert ElementTree.fromstring(rich).tag == "WatchFaceInfo"


def test_watch_face_shapes_xml_emits_the_round_small_and_large_pair() -> None:
    """WO-G10 allows ten entries; this file uses exactly two."""
    text = _watch_face_shapes_xml()
    assert '<WatchFace file="@raw/watchface" height="300" shape="CIRCLE" width="300" />' in text
    assert '<WatchFace file="@raw/watchface" height="450" shape="CIRCLE" width="450" />' in text
    assert len([line for line in text.splitlines() if "<WatchFace " in line]) == 2


def test_strings_xml_carries_every_label_the_face_references() -> None:
    """Each editor row and theme gets a string resource."""
    text = _strings_xml(by_slug(BASELINE_SLUG))
    assert '<string name="watch_face_name">Meridian Analog</string>' in text
    assert '<string name="theme_color_2_display_name">Jade</string>' in text
    assert '<string name="slot_2_display_name">Complication 2</string>' in text
    assert '<string name="show_ticks_display_name">Hour markers</string>' in text
    assert '<string name="show_date_display_name">Date</string>' in text
    assert "show_battery_display_name" not in text
    assert "hour_format_display_name" not in text
    assert ElementTree.fromstring(text).tag == "resources"
    battery = _strings_xml(_spec(show_battery=True))
    assert '<string name="show_battery_display_name">Battery</string>' in battery
    digital = _strings_xml(by_slug(DIGITAL_SLUG))
    assert '<string name="hour_format_24_display_name">24 hour</string>' in digital


def test_theme_colors_are_opaque_and_wrap_past_the_palette() -> None:
    """A colourway index beyond the list wraps instead of failing."""
    spec = by_slug(BASELINE_SLUG)
    first = _theme_colors(spec, 0)
    wrapped = _theme_colors(spec, len(spec.palette))
    assert first == wrapped
    assert all(color.as_tuple()[3] == 255 for color in first)
    assert _theme_colors(spec, 1) != first


def test_preview_digits_shows_the_marketing_pose() -> None:
    """The read-out is the 10:09 the preview time promises."""
    assert _preview_digits() == "10:09"


def test_scaled_for_edge_rescales_every_slot_box() -> None:
    """A half-size spec halves each slot and keeps at least one pixel."""
    spec = by_slug(BASELINE_SLUG)
    half = _scaled_for_edge(spec, 225)
    assert half.design_edge == 225
    for before, after in zip(spec.complications, half.complications, strict=True):
        assert after.x == round(before.x / 2)
        assert after.width == max(1, round(before.width / 2))
    assert _scaled_for_edge(replace(spec, complications=()), 225).complications == ()


def test_face_canvas_is_opaque_and_the_size_asked_for() -> None:
    """A preview canvas carries no transparent pixel anywhere."""
    canvas = _face_canvas(by_slug(BASELINE_SLUG), 0, 64)
    assert (canvas.width, canvas.height) == (64, 64)
    assert canvas.illuminated_ratio() > 0.0
    assert all(canvas.pixels[offset + 3] == 255 for offset in range(0, len(canvas.pixels), 4))


def test_feature_plate_is_the_exact_store_banner_size() -> None:
    """1024x500 with no alpha, which is what encode_rgb_png is used for."""
    canvas = _feature_plate(by_slug(BASELINE_SLUG), 1)
    assert (canvas.width, canvas.height) == (1024, 500)
    assert all(canvas.pixels[offset + 3] == 255 for offset in range(0, len(canvas.pixels), 4))


def test_hand_canvas_draws_the_three_hands_upwards() -> None:
    """Each hand puts white pixels from the centre up to its documented reach."""
    for kind, reach in (("hour", 0.26), ("minute", 0.38), ("second", 0.44)):
        canvas = hand_canvas(kind, 100)
        assert (canvas.width, canvas.height) == (100, 100)
        rows = {
            index // 4 // 100
            for index in range(3, len(canvas.pixels), 4)
            if canvas.pixels[index] > 0
        }
        assert min(rows) == round(50 - 100 * reach)
        assert max(rows) >= 50


def test_hand_canvas_rejects_a_hand_it_does_not_draw() -> None:
    """Only the three documented hands exist."""
    with pytest.raises(ValueError, match="unknown hand 'brush'"):
        hand_canvas("brush", 64)


def test_paint_slot_draws_each_supported_placeholder_kind() -> None:
    """Text, image, and ranged slots each take their own branch."""
    lit_kinds = (
        ("SHORT_TEXT", "LONG_TEXT"),
        ("LONG_TEXT",),
        ("MONOCHROMATIC_IMAGE", "SHORT_TEXT"),
        ("SMALL_IMAGE",),
        ("PHOTO_IMAGE", "SHORT_TEXT"),
        ("RANGED_VALUE", "SHORT_TEXT"),
    )
    for kinds in lit_kinds:
        canvas, painter = _painter(64)
        accent, secondary, text = _colors()
        _paint_slot(painter, ComplicationSlotSpec(1, 4, 4, 40, 24, kinds), accent, secondary, text)
        assert any(canvas.pixels[index] for index in range(0, len(canvas.pixels), 4)), kinds
    for kinds in lit_kinds + (("EMPTY",),):
        for kind in kinds:
            assert kind in COMPLICATION_TYPES


def test_paint_slot_leaves_an_empty_slot_blank() -> None:
    """An EMPTY slot reserves space and draws nothing."""
    canvas, painter = _painter(64)
    accent, secondary, text = _colors()
    _paint_slot(painter, ComplicationSlotSpec(1, 4, 4, 40, 24, ("EMPTY",)), accent, secondary, text)
    assert not any(canvas.pixels[index] for index in range(0, len(canvas.pixels), 4))


def test_paint_slot_clamps_a_label_bar_to_two_pixels_tall() -> None:
    """A slot one pixel tall still draws its label bar at the minimum height."""
    canvas, painter = _painter(16)
    accent, secondary, text = _colors()
    _paint_slot(painter, ComplicationSlotSpec(1, 0, 0, 12, 1, ("SHORT_TEXT",)), accent, secondary, text)
    assert len(canvas.pixels) == 16 * 16 * 4
    assert canvas.pixel(6, 0).as_tuple() == text.as_tuple()
    assert canvas.pixel(3, 0).as_tuple() == (0, 0, 0, 255)


def test_paint_face_covers_the_minimal_digital_dial() -> None:
    """No ticks, no hands, no date, and no complications still paints."""
    spec = _spec(
        style="digital",
        show_ticks=False,
        show_hands=False,
        show_date=False,
        complications=(),
    )
    canvas = Canvas(spec.design_edge, spec.design_edge, fill=BLACK)
    _paint_face(_Painter(canvas), spec, 0)
    assert any(canvas.pixels[index] for index in range(0, len(canvas.pixels), 4))


def test_paint_face_draws_the_ambient_ranged_arc_and_the_dial() -> None:
    """A face with a ranged slot paints the outer progress ring too."""
    spec = _spec(complications=(ComplicationSlotSpec(1, 10, 10, 40, 20, ("RANGED_VALUE",)),))
    canvas = Canvas(spec.design_edge, spec.design_edge, fill=BLACK)
    _paint_face(_Painter(canvas), spec, 0, bleed=1.09)
    assert canvas.illuminated_ratio() > 0.0


def test_painter_point_ignores_pixels_outside_the_canvas() -> None:
    """Off-canvas writes are dropped rather than raising."""
    canvas, painter = _painter(4)
    painter.point(-1, -1, bytes(BLACK.as_tuple()))
    painter.point(4, 4, bytes(BLACK.as_tuple()))
    painter.point(1, 1, bytes(hex_to_rgba("#FF0000").as_tuple()))
    assert canvas.pixel(1, 1).as_tuple() == (255, 0, 0, 255)


def test_painter_shifts_every_primitive_by_its_offset() -> None:
    """The feature-plate painter offsets columns without touching rows."""
    canvas = Canvas(16, 8, fill=BLACK)
    painter = _Painter(canvas, offset_x=8)
    painter.box(0, 0, 4, 4, hex_to_rgba("#00FF00"))
    assert canvas.pixel(9, 1).as_tuple() == (0, 255, 0, 255)
    assert canvas.pixel(1, 1).as_tuple() == (0, 0, 0, 255)


def test_painter_ring_clamps_a_zero_radius() -> None:
    """A ring with nothing to draw returns instead of painting."""
    canvas, painter = _painter(8)
    painter.ring(4.0, -1.0, 0.0, hex_to_rgba("#FFFFFF"))
    assert canvas.illuminated_ratio() == 0.0
    painter.ring(4.0, 3.0, 2.0, hex_to_rgba("#FFFFFF"), 300.0, 60.0)
    assert canvas.illuminated_ratio() > 0.0


def test_painter_ring_sweep_wraps_across_twelve_oclock() -> None:
    """A sweep that crosses 0 degrees lights both sides of the dial."""
    assert _Painter._in_sweep(0.0, -1.0, 350.0, 10.0) is True
    assert _Painter._in_sweep(0.0, 1.0, 350.0, 10.0) is False
    assert _Painter._in_sweep(1.0, 0.0, 0.0, 90.0) is True
    assert _Painter._in_sweep(-1.0, 0.0, 0.0, 90.0) is False


def test_painter_digits_renders_the_readout_and_ignores_noise() -> None:
    """Colon separators, digits, and unmapped glyphs are all handled."""
    spec = by_slug(DIGITAL_SLUG)
    box = box_of(spec, "time")
    canvas, painter = _painter(spec.design_edge)
    painter.digits(box, "10:09", hex_to_rgba("#FFFFFF"))
    assert canvas.illuminated_ratio() > 0.0
    quiet, quiet_painter = _painter(spec.design_edge)
    quiet_painter.digits(box, "::", hex_to_rgba("#FFFFFF"))
    assert quiet.illuminated_ratio() == 0.0
    odd, odd_painter = _painter(spec.design_edge)
    odd_painter.digits(box, "8X", hex_to_rgba("#FFFFFF"))
    assert odd.illuminated_ratio() > 0.0


def test_painter_digit_ignores_a_glyph_it_cannot_draw() -> None:
    """An unmapped character lights nothing rather than a partial glyph."""
    _, painter = _painter(32)
    before = painter.canvas.pixels[:]
    painter._digit(0, 0, 10, 20, 2, "Z", b"\xff\xff\xff\xff")
    assert painter.canvas.pixels == before


def test_painter_box_segment_and_disc_touch_the_buffer() -> None:
    """The three remaining primitives all write pixels."""
    canvas, painter = _painter(32)
    painter.box(2, 20, 4, 4, hex_to_rgba("#FF0000"))
    painter.segment(1.4, 1.4, 30.6, 30.6, hex_to_rgba("#00FF00"), 0)
    painter.disc(16.0, 4.0, hex_to_rgba("#0000FF"))
    assert canvas.pixel(3, 21).as_tuple() == (255, 0, 0, 255)
    assert canvas.pixel(5, 5).as_tuple() == (0, 255, 0, 255)
    assert canvas.pixel(16, 16).as_tuple() == (0, 0, 255, 255)
    assert canvas.illuminated_ratio() > 0.0


# --------------------------------------------------------------------------
# listing and manifest payloads
# --------------------------------------------------------------------------


def test_application_id_is_unique_per_slug() -> None:
    """Dashes become underscores so ids never collide or break the tooling."""
    assert _application_id(by_slug(BASELINE_SLUG)) == "com.ezcomfy.watchface.meridian_analog"
    assert _application_id(by_slug(DIGITAL_SLUG)) == "com.ezcomfy.watchface.vector_digital"


def test_listing_fields_fit_the_play_character_budgets() -> None:
    """Title, short, and full descriptions stay inside the published limits."""
    listing = _listing(by_slug(BASELINE_SLUG))
    title = str(listing["title"])
    short = str(listing["short_description"])
    assert title == "Meridian Analog for Wear OS"
    assert len(title) <= validate.LISTING_TITLE_LIMIT
    assert short == "Analog Wear OS watch face: 3 colorways, 2 complication slots."
    assert len(short) <= validate.LISTING_SHORT_LIMIT
    assert len(str(listing["full_description"])) <= validate.LISTING_FULL_LIMIT
    assert listing["category"] == "Classic" == listing["self_tag"]
    assert listing["tags"] == ["analog", "dress", "dressy"]
    assert listing["wear_os_wording"] == "Wear OS"
    assert listing["language"] == "en-US"
    assert "Data not collected" in str(listing["data_safety"])
    assert "does not display advertisements" in str(listing["ads"])


def test_style_word_for_the_complication_forward_faces() -> None:
    """The fourth style gets its own store wording rather than a fallback."""
    listing = _listing(by_slug("ledger-forward"))
    assert str(listing["short_description"]).startswith("Complication Wear OS watch face:")


def test_full_description_names_the_colourways_and_the_slot_count() -> None:
    """The store body sells what the face actually offers."""
    body = _full_description(by_slug(BASELINE_SLUG))
    assert "3 colorways to match your strap: Gold, Silver, Jade." in body
    assert "2 complication slots for steps, battery, weather, and more." in body
    assert "192 dp and 227 dp" in body
    assert body.isascii()


def test_article_follows_the_style_word_it_precedes() -> None:
    """Store copy puts the style right after the article, so it has to agree.

    Three of the four catalog styles open on a consonant and ``analog`` does
    not, so a template that hard-codes ``a`` ships "is a analog".
    """
    assert _article("analog") == "an"
    assert _article("Analog") == "an"
    assert _article("digital") == "a"
    assert _article("hybrid") == "a"
    assert _article("complication forward") == "a"
    assert _article("") == "a"


def test_full_description_reads_aloud_for_every_catalog_style() -> None:
    """No shipped face opens its own listing with a grammar error."""
    for spec in project.WATCH_FACE_CATALOG:
        word = spec.style.replace("-", " ")
        first = _full_description(spec).splitlines()[0]
        assert f"is {_article(word)} {word} Wear OS watch face" in first, first
        assert f"is a {word}" not in first or _article(word) == "a", first


def test_listing_markdown_shows_the_character_budgets_in_use() -> None:
    """The operator pastes this straight into Play Console."""
    spec = by_slug(BASELINE_SLUG)
    listing = _listing(spec)
    text = _listing_markdown(spec, listing)
    title = str(listing["title"])
    short = str(listing["short_description"])
    assert f"# {spec.name} - Play store listing" in text
    assert f"- Title ({len(title)}/30): {title}" in text
    assert f"- Short description ({len(short)}/80): {short}" in text
    assert "- Category and self-tag: Classic" in text
    assert "- Tags: analog, dress, dressy" in text
    assert f"- ``{STORE_ASSET_DIR}/icon.png`` - 512x512" in text
    assert "1024x500, no alpha" in text
    assert str(listing["full_description"]) in text
    assert text.isascii()


def test_readme_ships_the_bundle_separation_warning() -> None:
    """The emitted folder explains why it must stay code-free."""
    text = _readme(by_slug(BASELINE_SLUG), "com.ezcomfy.watchface.meridian_analog")
    assert "# Meridian Analog" in text
    assert "``com.ezcomfy.watchface.meridian_analog``" in text
    assert '``hasCode="false"``' in text
    assert "res/raw/watchface.xml" in text
    assert "res/xml/watch_face_shapes.xml" in text
    assert "## Add a face" in text and "--catalog" not in text
    assert text.isascii()


def test_manifest_json_records_the_build_the_gate_needs() -> None:
    """Every number the compliance check scores is written down."""
    spec = by_slug(BASELINE_SLUG)
    memory = validate.memory_estimate(450, hands=True, slot_boxes=((78, 34), (78, 34)))
    text = _manifest_json(
        spec,
        "com.ezcomfy.watchface.meridian_analog",
        4,
        "1.2.3",
        ("README.md", "AndroidManifest.xml"),
        _listing(spec),
        memory,
        0.071234,
        384,
    )
    document = json.loads(text)
    assert document["generated_by"] == "ez-comfy-stack ez_watch 1.2.3"
    assert document["package"] == "com.ezcomfy.watchface.meridian_analog"
    assert document["watch_face"] == {
        "slug": "meridian-analog",
        "name": "Meridian Analog",
        "style": "analog",
        "shape": "round",
        "category": "Classic",
        "tags": ["analog", "dress", "dressy"],
        "design_edge": 450,
        "preview_time": "10:09:30",
    }
    assert document["wff"] == {
        "version": 4,
        "min_sdk": 36,
        "publisher": "ez-comfy-stack-1.2.3",
        "preview_edge": 384,
    }
    assert [row["name"] for row in document["themes"]] == ["Gold", "Silver", "Jade"]
    assert document["themes"][0]["index"] == 0
    assert document["complication_slots"][0] == {
        "slot_id": 1,
        "x": 186,
        "y": 150,
        "width": 78,
        "height": 34,
        "supported_types": ["SHORT_TEXT", "EMPTY"],
        "bounding": "BoundingOval",
    }
    assert document["memory"] == {
        "design_edge": 450,
        "ambient_bytes": memory.ambient_bytes,
        "interactive_bytes": memory.interactive_bytes,
        "illuminated_ratio": 0.0712,
        "illuminated_limit": validate.ILLUMINATED_LIMIT,
    }
    assert sorted(document["files"]) == ["AndroidManifest.xml", "README.md"]
    assert document["listing"]["title"] == "Meridian Analog for Wear OS"
    assert text.endswith("}\n")
    assert text == json.dumps(document, indent=2, sort_keys=True) + "\n"


def test_manifest_json_uses_a_bounding_box_for_a_square_face() -> None:
    """Only a round face may claim an oval bounding shape."""
    spec = by_slug(DIGITAL_SLUG)
    memory = validate.memory_estimate(spec.design_edge, hands=False, slot_boxes=())
    text = _manifest_json(
        spec,
        _application_id(spec),
        1,
        DEFAULT_TOOL_VERSION,
        (),
        _listing(spec),
        memory,
        0.0,
        MIN_PREVIEW_EDGE,
    )
    document = json.loads(text)
    assert document["complication_slots"][0]["bounding"] == "BoundingBox"
    assert document["wff"] == {
        "version": 1,
        "min_sdk": 33,
        "publisher": "ez-comfy-stack-1.0.0",
        "preview_edge": 384,
    }


# --------------------------------------------------------------------------
# the build itself
# --------------------------------------------------------------------------


def test_build_face_writes_the_exact_file_set(base: tuple[ProjectResult, Path]) -> None:
    """One round analog face emits exactly these eighteen paths."""
    result, root = base
    assert isinstance(result, ProjectResult)
    assert result.slug == BASELINE_SLUG
    assert result.package == "com.ezcomfy.watchface.meridian_analog"
    assert result.out_dir == str(root)
    assert result.files == BASELINE_FILES
    assert result.dry_run is False
    assert sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()) == list(BASELINE_FILES)
    assert all((root / name).is_file() for name in result.files)


def test_build_face_reports_a_clean_gate(base: tuple[ProjectResult, Path]) -> None:
    """The shipped baseline passes every rule the validator knows."""
    result, _root = base
    assert result.findings == ()
    assert result.clean is True
    assert result.themes == ("Gold", "Silver", "Jade")
    assert result.slot_ids == (1, 2)
    assert result.memory.design_edge == 450
    assert result.memory.ambient_bytes == 3 * 4 * 450 * 450
    assert result.illuminated_ratio <= validate.ILLUMINATED_LIMIT


def test_build_face_is_byte_identical_across_runs(tmp_path: Path) -> None:
    """Same spec in, byte-identical files out, so a diff means a real change."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    first = build_face(by_slug(BASELINE_SLUG), left, preview_edge=MIN_PREVIEW_EDGE)
    second = build_face(by_slug(BASELINE_SLUG), right, preview_edge=MIN_PREVIEW_EDGE)
    assert first.files == second.files
    for name in first.files:
        assert (left / BASELINE_SLUG / name).read_bytes() == (right / BASELINE_SLUG / name).read_bytes()


def test_build_face_dry_run_writes_nothing(tmp_path: Path) -> None:
    """A dry run costs the raster work and touches no disk."""
    out = tmp_path / "dry"
    result = build_face(by_slug(BASELINE_SLUG), out, preview_edge=MIN_PREVIEW_EDGE, dry_run=True)
    assert not out.exists()
    assert result.dry_run is True
    assert result.files == BASELINE_FILES
    assert result.findings == ()
    assert result.clean is True


def test_build_face_rejects_a_preview_below_the_play_minimum(tmp_path: Path) -> None:
    """A 384 pixel short edge is the smallest screenshot Play takes."""
    with pytest.raises(ValueError, match="preview_edge must be at least 384, got 200"):
        build_face(by_slug(BASELINE_SLUG), tmp_path, preview_edge=200)


def test_build_face_adds_the_shapes_file_only_for_round_faces(
    tmp_path: Path,
) -> None:
    """Size variants mean the round small and large layouts."""
    round_result = build_face(
        by_slug(BASELINE_SLUG), tmp_path / "r", preview_edge=MIN_PREVIEW_EDGE, size_variants=True
    )
    assert round_result.files == tuple(sorted((*BASELINE_FILES, "res/xml/watch_face_shapes.xml")))
    shapes = Path(round_result.out_dir) / "res/xml/watch_face_shapes.xml"
    assert '<WatchFace file="@raw/watchface" height="450"' in shapes.read_text(encoding="utf-8")
    square = build_face(
        by_slug(DIGITAL_SLUG), tmp_path / "s", preview_edge=MIN_PREVIEW_EDGE, size_variants=True
    )
    assert "res/xml/watch_face_shapes.xml" not in square.files


def test_build_face_omits_hand_drawables_for_a_face_without_hands(
    tmp_path: Path,
) -> None:
    """A digital face ships no hand art for a renderer that will not use it."""
    result = build_face(by_slug(DIGITAL_SLUG), tmp_path, preview_edge=MIN_PREVIEW_EDGE)
    assert [name for name in result.files if "hand_" in name] == []
    assert "res/drawable/preview.png" in result.files
    assert result.themes == ("Volt", "Cyan", "Coral")


def test_build_face_declares_no_flavours_below_version_two(tmp_path: Path) -> None:
    """Version 1 may not claim flavour support."""
    result = build_face(
        by_slug(BASELINE_SLUG), tmp_path, preview_edge=MIN_PREVIEW_EDGE, wff_version=1
    )
    info = (Path(result.out_dir) / "res/xml/watch_face_info.xml").read_text(encoding="utf-8")
    assert "FlavorsSupported" not in info
    manifest = (Path(result.out_dir) / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert 'android:value="1"' in manifest
    assert result.clean is True


def test_build_face_can_add_literal_numerals_to_the_dial(tmp_path: Path) -> None:
    """The optional numerals reach the scene document."""
    plain = build_face(by_slug(BASELINE_SLUG), tmp_path / "a", preview_edge=MIN_PREVIEW_EDGE)
    numbered = build_face(
        by_slug(BASELINE_SLUG),
        tmp_path / "b",
        preview_edge=MIN_PREVIEW_EDGE,
        include_numerals=True,
    )
    left = (Path(plain.out_dir) / "res/raw/watchface.xml").read_text(encoding="utf-8")
    right = (Path(numbered.out_dir) / "res/raw/watchface.xml").read_text(encoding="utf-8")
    assert right != left
    assert len(right) > len(left)


def test_build_face_theme_selects_the_preview_colourway(tmp_path: Path) -> None:
    """The in-package preview shows the colourway the operator asked for."""
    first = build_face(by_slug(BASELINE_SLUG), tmp_path / "a", preview_edge=MIN_PREVIEW_EDGE, theme=0)
    second = build_face(by_slug(BASELINE_SLUG), tmp_path / "b", preview_edge=MIN_PREVIEW_EDGE, theme=1)
    left = (Path(first.out_dir) / "res/drawable/preview.png").read_bytes()
    right = (Path(second.out_dir) / "res/drawable/preview.png").read_bytes()
    assert left != right
    shot = (Path(second.out_dir) / STORE_ASSET_DIR / "screenshots/meridian-analog-theme-1.png").read_bytes()
    assert shot == right


def test_watch_face_xml_is_well_formed_with_one_scene(base: tuple[ProjectResult, Path]) -> None:
    """The face document parses and declares exactly one Scene."""
    _result, root = base
    text = (root / "res/raw/watchface.xml").read_text(encoding="utf-8")
    face = ElementTree.fromstring(text)
    assert face.tag == "WatchFace"
    assert face.get("width") == "450" and face.get("height") == "450"
    assert face.get("clipShape") == "CIRCLE"
    scenes = [child for child in face if child.tag == "Scene"]
    assert len(scenes) == 1
    assert [child.tag for child in scenes[0]] == [
        "Group",
        "Group",
        "AnalogClock",
        "ComplicationSlot",
        "ComplicationSlot",
    ]
    assert text.startswith('<?xml version="1.0" encoding="utf-8"?>\n')
    assert text.isascii()


def test_stored_assets_are_pngs_of_the_size_play_asks_for(
    base: tuple[ProjectResult, Path],
) -> None:
    """The icon is 512 square and the banner is 1024x500 with no alpha."""
    _result, root = base
    icon = validate.decode_png(root / validate.ICON_PNG)
    assert icon is not None and (icon.width, icon.height) == (512, 512)
    assert icon.opaque is True
    feature = validate.decode_png(root / validate.FEATURE_GRAPHIC_PNG)
    assert feature is not None and (feature.width, feature.height) == (1024, 500)
    assert feature.color_type == 2
    assert feature.has_trns is False and feature.opaque is True
    preview = validate.decode_png(root / validate.PREVIEW_PNG)
    assert preview is not None and (preview.width, preview.height) == (384, 384)
    assert preview.color_type == 6 and preview.opaque is True


def test_store_listing_files_ship_with_the_project(base: tuple[ProjectResult, Path]) -> None:
    """manifest.json, the listing page, and the README all land."""
    result, root = base
    document = json.loads((root / validate.MANIFEST_JSON).read_text(encoding="utf-8"))
    assert sorted(document["files"]) == [name for name in BASELINE_FILES if name != "manifest.json"]
    assert document["package"] == result.package
    assert document["memory"]["ambient_bytes"] == result.memory.ambient_bytes
    assert document["memory"]["illuminated_ratio"] == round(result.illuminated_ratio, 4)
    listing = (root / validate.STORE_LISTING_MD).read_text(encoding="utf-8")
    assert "# Meridian Analog - Play store listing" in listing
    assert (root / validate.README_MD).read_text(encoding="utf-8").startswith("# Meridian Analog")


def test_build_face_pack_builds_the_faces_it_is_given(tmp_path: Path) -> None:
    """A pack is one folder per face, in the order handed in."""
    specs = (by_slug(DIGITAL_SLUG), by_slug(BASELINE_SLUG))
    results = build_face_pack(tmp_path, specs, preview_edge=MIN_PREVIEW_EDGE)
    assert [result.slug for result in results] == [DIGITAL_SLUG, BASELINE_SLUG]
    assert all(result.out_dir == str(tmp_path / result.slug) for result in results)
    assert (tmp_path / DIGITAL_SLUG / "manifest.json").is_file()
    assert (tmp_path / BASELINE_SLUG / "manifest.json").is_file()


def test_build_face_pack_defaults_to_the_whole_catalog_signature() -> None:
    """The public default is the shipped catalog, not an empty selection."""
    import inspect

    defaults = inspect.signature(build_face_pack).parameters
    assert defaults["specs"].default is project.WATCH_FACE_CATALOG
    assert defaults["wff_version"].default == 4
    assert defaults["preview_edge"].default == DEFAULT_PREVIEW_EDGE
    assert defaults["size_variants"].default is False
    assert defaults["dry_run"].default is False


def test_clean_is_false_when_the_gate_raises_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A build is only submittable when nothing failed."""
    booby_trap = (validate.Finding(validate.SEVERITY_ERROR, "boom", "on purpose", "README.md"),)
    monkeypatch.setattr(project, "validate_project", lambda _root: booby_trap)
    result = build_face(by_slug(BASELINE_SLUG), tmp_path, preview_edge=MIN_PREVIEW_EDGE)
    assert result.findings == booby_trap
    assert result.clean is False


# --------------------------------------------------------------------------
# selection and the command line
# --------------------------------------------------------------------------


def _args(**overrides: object) -> argparse.Namespace:
    """Build a namespace shaped like the parser's own output.

    Args:
        **overrides: Fields to set on the namespace.

    Returns:
        The parsed-arguments stand-in.
    """
    values: dict[str, object] = {"catalog": None, "face": [], "style": None}
    values.update(overrides)
    return argparse.Namespace(**values)


def test_select_defaults_to_every_shipped_face() -> None:
    """With no filters the whole catalog is the answer."""
    assert _select(_args()) == project.WATCH_FACE_CATALOG


def test_select_keeps_catalog_order_and_only_the_named_slugs() -> None:
    """Repeat flags are a set, and the order is the catalog's."""
    picked = _select(_args(face=[DIGITAL_SLUG, BASELINE_SLUG]))
    assert [spec.slug for spec in picked] == [BASELINE_SLUG, DIGITAL_SLUG]


def test_select_filters_one_style() -> None:
    """One style is a subset of the catalog."""
    picked = _select(_args(style="digital"))
    assert [spec.slug for spec in picked] == ["signal-digital", "tally-digital", DIGITAL_SLUG]


def test_select_names_an_unknown_slug() -> None:
    """A typo is reported as the list of things it does not know."""
    with pytest.raises(ValueError, match=r"unknown face slug or slugs: also-nope, nope"):
        _select(_args(face=["nope", "also-nope", BASELINE_SLUG]))


def test_select_merges_an_operator_catalog(tmp_path: Path) -> None:
    """An override file reaches the build through --catalog."""
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"watch_faces": [{"slug": BASELINE_SLUG, "name": "Renamed"}]}), encoding="utf-8")
    picked = _select(_args(catalog=str(path)))
    by_slug_value = {spec.slug: spec for spec in picked}
    assert by_slug_value[BASELINE_SLUG].name == "Renamed"
    assert len(picked) == len(project.WATCH_FACE_CATALOG)


def test_select_reports_a_malformed_catalog(tmp_path: Path) -> None:
    """A file that is not JSON is a stated problem, not a traceback."""
    path = tmp_path / "broken.json"
    path.write_text("{nope", encoding="utf-8")
    with pytest.raises(ValueError, match="is not valid JSON"):
        _select(_args(catalog=str(path)))


def test_parser_exposes_every_operator_knob() -> None:
    """Each flag the operator console names is really there."""
    parser = build_parser()
    actions = {action.dest for action in parser._actions}
    assert {"out", "face", "style", "catalog", "wff_version", "preview_edge"} <= actions
    assert {"size_variants", "dry_run", "validate_only"} <= actions
    flags = {flag for action in parser._actions for flag in action.option_strings}
    assert {
        "--out",
        "--face",
        "--style",
        "--catalog",
        "--wff-version",
        "--preview-edge",
        "--size-variants",
        "--validate-only",
        "--dry-run",
    } <= flags
    by_dest = {action.dest: action for action in parser._actions}
    assert by_dest["out"].required is True
    assert by_dest["style"].choices == ["analog", "complication-forward", "digital", "hybrid"]
    assert by_dest["wff_version"].type is int
    assert by_dest["preview_edge"].default == DEFAULT_PREVIEW_EDGE
    parsed = parser.parse_args(["--out", "/tmp/x", "--face", "a", "--face", "b"])
    assert parsed.face == ["a", "b"]
    assert parsed.wff_version == 4
    assert (parsed.size_variants, parsed.dry_run, parsed.validate_only) == (False, False, False)


def test_main_writes_a_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI verb emits one face and says so."""
    out = tmp_path / "cli"
    code = main(["--out", str(out), "--face", BASELINE_SLUG, "--preview-edge", str(MIN_PREVIEW_EDGE)])
    assert code == 0
    assert (out / BASELINE_SLUG / "manifest.json").is_file()
    printed = capsys.readouterr().out
    assert printed.startswith(f"ez_watch: wrote {BASELINE_SLUG} into {out / BASELINE_SLUG}")
    assert "18 files" in printed
    assert "illuminated=0." in printed


def test_main_dry_run_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--dry-run reports the plan and leaves the folder absent."""
    out = tmp_path / "dry"
    assert main(["--out", str(out), "--face", BASELINE_SLUG, "--preview-edge", "384", "--dry-run"]) == 0
    assert not out.exists()
    assert "ez_watch: checked meridian-analog" in capsys.readouterr().out


def test_main_validate_only_uses_a_scratch_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--validate-only never writes where the operator pointed."""
    out = tmp_path / "untouched"
    code = main(
        ["--out", str(out), "--face", BASELINE_SLUG, "--preview-edge", "384", "--validate-only"]
    )
    assert code == 0
    assert not out.exists()
    printed = capsys.readouterr().out
    assert "ez_watch: checked meridian-analog" in printed
    assert "ez-watch-" in printed


def test_main_size_variants_reach_the_build(tmp_path: Path) -> None:
    """The shapes file is the visible result of the flag."""
    out = tmp_path / "variants"
    assert main(
        ["--out", str(out), "--face", BASELINE_SLUG, "--preview-edge", "384", "--size-variants"]
    ) == 0
    assert (out / BASELINE_SLUG / "res/xml/watch_face_shapes.xml").is_file()


def test_main_reports_a_gate_error_as_exit_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A face the gate rejects is a failing command, not a silent success."""
    booby_trap = (
        validate.Finding(validate.SEVERITY_ERROR, "boom", "on purpose", "README.md"),
        validate.Finding(validate.SEVERITY_WARNING, "meh", "only polish", "manifest.json"),
    )
    monkeypatch.setattr(project, "validate_project", lambda _root: booby_trap)
    code = main(["--out", str(tmp_path / "bad"), "--face", BASELINE_SLUG, "--preview-edge", "384"])
    assert code == 1
    printed = capsys.readouterr().out
    assert "  error boom: on purpose [README.md]" in printed
    assert "  warning meh: only polish [manifest.json]" in printed


def test_main_rejects_an_unknown_slug_with_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A typo in --face costs exit two and writes nothing."""
    out = tmp_path / "none"
    assert main(["--out", str(out), "--face", "no-such-face"]) == 2
    assert not out.exists()
    assert "ez_watch: unknown face slug or slugs: no-such-face" in capsys.readouterr().out


def test_main_rejects_an_empty_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Nothing matched is a bad request, not an empty success."""
    monkeypatch.setattr(project, "WATCH_FACE_CATALOG", ())
    assert main(["--out", str(tmp_path / "none")]) == 2
    assert "ez_watch: no faces matched" in capsys.readouterr().out


def test_main_filters_one_style(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--style narrows the pack to one layout family."""
    monkeypatch.setattr(project, "WATCH_FACE_CATALOG", (by_slug(DIGITAL_SLUG), by_slug(BASELINE_SLUG)))
    out = tmp_path / "style"
    assert main(["--out", str(out), "--style", "digital", "--preview-edge", "384"]) == 0
    assert [path.name for path in out.iterdir()] == [DIGITAL_SLUG]


def test_main_merges_an_operator_catalog_file(tmp_path: Path) -> None:
    """--catalog reaches the build through the parser."""
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"watch_faces": [{"slug": BASELINE_SLUG, "name": "Renamed"}]}), encoding="utf-8")
    assert main(["--catalog", str(path), "--out", str(tmp_path / "c"), "--face", BASELINE_SLUG, "--preview-edge", "384"]) == 0
    document = json.loads((tmp_path / "c" / BASELINE_SLUG / "manifest.json").read_text(encoding="utf-8"))
    assert document["watch_face"]["name"] == "Renamed"


def test_main_reports_an_unreadable_catalog(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing override file is exit two with the reason."""
    assert main(["--catalog", str(tmp_path / "gone.json"), "--out", str(tmp_path / "c")]) == 2
    assert "cannot read catalog" in capsys.readouterr().out


def test_parser_rejects_a_style_it_does_not_know() -> None:
    """Argparse guards the style domain."""
    with pytest.raises(SystemExit):
        main(["--out", "/tmp/whatever", "--style", "sundial"])


def test_parser_requires_the_out_folder() -> None:
    """--out is the one thing that is never optional."""
    with pytest.raises(SystemExit):
        main(["--face", BASELINE_SLUG])


def test_running_the_module_as_a_script_exits_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The package entry point the operator CLI calls really works."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["ez_watch.project", "--out", str(tmp_path / "runpy"), "--face", BASELINE_SLUG,
         "--preview-edge", "384", "--dry-run"],
    )
    monkeypatch.delitem(sys.modules, "ez_watch.project", raising=False)
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("ez_watch.project", run_name="__main__", alter_sys=True)
    assert caught.value.code == 0
