"""Hermetic tests for the Watch Face Format XML builder."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_watch.catalog import (  # noqa: E402
    COMPLICATION_TYPES,
    DEFAULT_STEP_GOAL,
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
)
from ez_watch.scene import (  # noqa: E402
    AMBIENT_ALPHA_DIM,
    AMBIENT_ALPHA_FULL,
    AMBIENT_ALPHA_HIDDEN,
    AMBIENT_MODE,
    DATE_PARAMETERS,
    DEFAULT_PREVIEW_TIME,
    DEFAULT_WFF_VERSION,
    ELEMENT_VOCABULARY,
    IMAGE_EXPRESSIONS,
    REQUIRED_ELEMENT_ATTRIBUTES,
    SCHEMA_ROOT_URL,
    TEXT_EXPRESSIONS,
    THEME_CONFIGURATION_ID,
    THEME_EXPRESSION,
    VARIANT_MODES,
    WFF_VERSIONS,
    WFF_VERSION_API,
    XSI_NAMESPACE,
    LayoutBox,
    _attr_text,
    _complication_content,
    _el,
    box_of,
    build_watch_face,
    layout,
    numeral_part,
    schema_location,
    serialize,
    string_resources,
    theme_color,
    watch_face_xml,
)

DECORATION_BOXES: tuple[str, ...] = ("dial", "ticks", "arc", "hands")


def _theme(name: str = "Ember", *colors: str) -> ThemePalette:
    """Build one colourway.

    Args:
        name: Colourway name.
        *colors: Hex colour strings.

    Returns:
        The palette.
    """
    return ThemePalette(name=name, colors=colors or ("#FF7A18", "#FFC94D", "#FFF3E0"))


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
        "x": 20,
        "y": 30,
        "width": 100,
        "height": 40,
        "supported_types": ("SHORT_TEXT", "RANGED_VALUE"),
    }
    base.update(overrides)
    return ComplicationSlotSpec(**base)  # type: ignore[arg-type]


def _face(**overrides: object) -> WatchFaceSpec:
    """Build one probe face with fields swapped in.

    Args:
        overrides: Keys to add or replace.

    Returns:
        The spec.
    """
    base: dict[str, object] = {
        "slug": "probe-face",
        "name": "Probe Face",
        "style": STYLE_ANALOG,
        "shape": SHAPE_ROUND,
        "palette": (_theme(),),
        "complications": (_slot(),),
        "typography": Typography(family="sans-serif", time_size=24, label_size=12),
    }
    base.update(overrides)
    return WatchFaceSpec(**base)  # type: ignore[arg-type]


def _scene_root(root: ElementTree.Element) -> ElementTree.Element:
    """The ``Scene`` inside an already built tree.

    Args:
        root: Built ``WatchFace`` element.

    Returns:
        The scene element.

    Raises:
        AssertionError: the tree carries no scene.
    """
    scene_element = _child(root, "Scene")
    return scene_element


def _scene_of(spec: WatchFaceSpec) -> ElementTree.Element:
    """The single ``Scene`` element of one built face.

    Args:
        spec: Face to build.

    Returns:
        The scene element.
    """
    return _scene_root(build_watch_face(spec))


def _group(scene_element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    """Find one named ``Group`` layer inside a scene.

    Args:
        scene_element: The scene to search.
        name: Value of the ``name`` attribute.

    Returns:
        The group, or None when the layer is not emitted.
    """
    for child in scene_element:
        if child.tag == "Group" and child.get("name") == name:
            return child
    return None


def _dial(spec: WatchFaceSpec) -> ElementTree.Element:
    """The decoration layer of one built face.

    Args:
        spec: Face to build.

    Returns:
        The ``dialLayer`` group.

    Raises:
        AssertionError: the face emits no dial layer.
    """
    dial = _group(_scene_of(spec), "dialLayer")
    assert dial is not None, f"face {spec.slug} has no dialLayer"
    return dial


def _child(parent: ElementTree.Element, tag: str) -> ElementTree.Element:
    """Find one child by tag, loudly.

    Args:
        parent: Element to search.
        tag: Element name to find.

    Returns:
        The matching child.

    Raises:
        AssertionError: no child carries that tag.
    """
    child = parent.find(tag)
    assert child is not None, f"no {tag} under {parent.tag}"
    return child


def _named(parent: ElementTree.Element, name: str) -> ElementTree.Element:
    """Find one child by ``name`` attribute, loudly.

    Args:
        parent: Element to search.
        name: Value of the ``name`` attribute.

    Returns:
        The matching child.

    Raises:
        AssertionError: no child carries that name.
    """
    for child in parent:
        if child.get("name") == name:
            return child
    raise AssertionError(f"no child named {name!r} under {parent.tag}")


def _ambient_alpha(element: ElementTree.Element) -> str | None:
    """The ambient alpha an element pins, or None when it pins none.

    Args:
        element: Element to inspect.

    Returns:
        The ``Variant value``, or None when there is no ambient variant.
    """
    for child in element:
        if child.tag == "Variant":
            return child.get("value")
    return None


def _policy(slot_element: ElementTree.Element) -> dict[str, str]:
    """The default provider a slot ships with.

    Args:
        slot_element: The ``ComplicationSlot`` to read.

    Returns:
        The ``DefaultProviderPolicy`` attributes.

    Raises:
        AssertionError: the slot carries no default provider policy.
    """
    policy = _child(slot_element, "DefaultProviderPolicy")
    return dict(policy.attrib)


def _tags(root: ElementTree.Element) -> set[str]:
    """Every element name used anywhere in a tree.

    Args:
        root: Element to walk.

    Returns:
        Set of tag names.
    """
    return {element.tag for element in root.iter()}


# ---------------------------------------------------------------------------
# Constants and the vocabulary tables
# ---------------------------------------------------------------------------


def test_document_constants_name_the_published_rules() -> None:
    """The knobs a reviewer checks are the documented values."""
    assert XSI_NAMESPACE == "http://www.w3.org/2001/XMLSchema-instance"
    assert SCHEMA_ROOT_URL.endswith("/third_party/wff/specification/documents")
    assert (DEFAULT_WFF_VERSION, DEFAULT_PREVIEW_TIME) == (4, "10:09:30")
    assert THEME_CONFIGURATION_ID == "themeColor"
    assert THEME_EXPRESSION == "[CONFIGURATION.themeColor]"
    assert AMBIENT_MODE == "AMBIENT"
    assert (AMBIENT_ALPHA_HIDDEN, AMBIENT_ALPHA_DIM, AMBIENT_ALPHA_FULL) == (0, 96, 255)
    assert WFF_VERSIONS == (1, 2, 3, 4)
    assert dict(WFF_VERSION_API) == {1: 33, 2: 34, 3: 35, 4: 36}
    assert VARIANT_MODES == frozenset({AMBIENT_MODE})
    assert COMPLICATION_TYPES == (
        "SHORT_TEXT",
        "LONG_TEXT",
        "MONOCHROMATIC_IMAGE",
        "SMALL_IMAGE",
        "PHOTO_IMAGE",
        "RANGED_VALUE",
        "EMPTY",
    )


def test_expression_tables_cover_every_complication_type() -> None:
    """Each complication type has its expression or is deliberately empty."""
    assert dict(IMAGE_EXPRESSIONS) == {
        "MONOCHROMATIC_IMAGE": "[COMPLICATION.MONOCHROMATIC_IMAGE]",
        "SMALL_IMAGE": "[COMPLICATION.SMALL_IMAGE]",
        "PHOTO_IMAGE": "[COMPLICATION.PHOTO_IMAGE]",
    }
    assert dict(TEXT_EXPRESSIONS) == {
        "SHORT_TEXT": "[COMPLICATION.TEXT]",
        "LONG_TEXT": "[COMPLICATION.TEXT]",
        "RANGED_VALUE": "[COMPLICATION.RANGED_VALUE_VALUE]",
    }
    assert DATE_PARAMETERS == ("[MONTH_S]", "[DAY]")
    assert set(IMAGE_EXPRESSIONS) | set(TEXT_EXPRESSIONS) | {"EMPTY"} == set(COMPLICATION_TYPES)


def test_every_element_the_builder_emits_is_in_the_vocabulary() -> None:
    """Nothing outside the reference-page word list reaches the document."""
    emitted: set[str] = set()
    for spec in WATCH_FACE_CATALOG:
        emitted |= _tags(build_watch_face(spec, include_numerals=True))
    assert emitted <= set(ELEMENT_VOCABULARY)
    assert {"Arc", "BoundingOval", "PartText", "TimeText", "Variant"} <= emitted
    assert {"BoundingRect", "Gyro", "PhotosConfiguration"} <= set(ELEMENT_VOCABULARY)


def test_every_emitted_element_carries_its_required_attributes() -> None:
    """The attributes the reference pages mark required are always written."""
    for spec in WATCH_FACE_CATALOG:
        for element in build_watch_face(spec, include_numerals=True).iter():
            required = REQUIRED_ELEMENT_ATTRIBUTES.get(element.tag, ())
            assert set(required) <= set(element.attrib), (spec.slug, element.tag)


# ---------------------------------------------------------------------------
# Attribute scalars and colour helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "true"),
        (False, "false"),
        (0, "0"),
        (42, "42"),
        (1.5, "1.5"),
        (2.0, "2"),
        (0.0, "0"),
        (444.6, "444.6"),
        (20.25, "20.25"),
        ("@string/x", "@string/x"),
    ],
)
def test_attr_text_spells_each_scalar_type(value: object, expected: str) -> None:
    """The four attribute scalars are spelled the way WFF reads them."""
    assert _attr_text(value) == expected  # type: ignore[arg-type]


def test_el_sorts_its_attributes_for_stable_output() -> None:
    """Attribute order is deterministic, so the document diffs cleanly."""
    element = _el("Complication", supportedTypes="EMPTY", slotId=3, x=1, enabled=True)
    assert list(element.attrib) == ["enabled", "slotId", "supportedTypes", "x"]
    assert element.get("enabled") == "true"


def test_theme_color_resolves_a_colourway_index() -> None:
    """A literal colour is eight-digit ARGB, clamped into the colourway."""
    spec = _face(palette=(_theme("One", "#FF7A18", "#FFC94D", "#FFF3E0"),))
    assert theme_color(spec, 0) == "#FF7A18FF"
    assert theme_color(spec, 1) == "#FFC94DFF"
    assert theme_color(spec, 2) == "#FFF3E0FF"
    assert theme_color(spec, 99) == "#FFF3E0FF"
    assert theme_color(spec, -1) == "#FFF3E0FF"


def test_theme_color_accepts_the_three_digit_shorthand() -> None:
    """A short hex colour is expanded, not rejected."""
    assert theme_color(_face(palette=(_theme("One", "#ABC", "#fff"),)), 0) == "#AABBCCFF"
    assert theme_color(_face(palette=(_theme("One", "#ABC", "#fff"),)), 1) == "#FFFFFFFF"


def test_theme_reference_dots_the_slot_only_when_the_colourway_has_one() -> None:
    """Slot 0 is the plain configuration; deeper slots need a wider colourway."""
    wide = _face(palette=(_theme("One", "#111111", "#222222", "#333333"),))
    ring_stroke = _child(_child(_named(_dial(wide), "dialRing"), "Ellipse"), "Stroke")
    assert ring_stroke.get("color") == THEME_EXPRESSION
    tick_stroke = _child(_child(_named(_dial(wide), "tick0"), "Line"), "Stroke")
    assert tick_stroke.get("color") == "[CONFIGURATION.themeColor].1"
    thin = _face(palette=(_theme("One", "#111111"),))
    thin_stroke = _child(_child(_named(_dial(thin), "tick0"), "Line"), "Stroke")
    assert thin_stroke.get("color") == THEME_EXPRESSION


# ---------------------------------------------------------------------------
# String resources
# ---------------------------------------------------------------------------


def test_string_resources_lists_every_label_for_an_analog_face() -> None:
    """One row per name the XML references, sorted by name."""
    assert string_resources(by_slug("aurora-analog")) == (
        ("show_battery_display_name", "Battery"),
        ("show_date_display_name", "Date"),
        ("show_ticks_display_name", "Hour markers"),
        ("slot_1_display_name", "Complication 1"),
        ("slot_2_display_name", "Complication 2"),
        ("slot_3_display_name", "Complication 3"),
        ("theme_color_0_display_name", "Ember"),
        ("theme_color_1_display_name", "Aurora"),
        ("theme_color_2_display_name", "Cobalt"),
        ("theme_color_display_name", "Color theme"),
        ("watch_face_name", "Aurora Analog"),
    )


@pytest.mark.parametrize(
    ("style", "has_hour_format"),
    [
        (STYLE_ANALOG, False),
        (STYLE_DIGITAL, True),
        (STYLE_HYBRID, True),
        (STYLE_COMPLICATION, True),
    ],
)
def test_string_resources_adds_the_hour_format_only_for_numeric_faces(
    style: str, has_hour_format: bool
) -> None:
    """Only a face that renders digits offers the 12/24 switch."""
    names = {name for name, _ in string_resources(_face(style=style))}
    assert ("hour_format_display_name" in names) is has_hour_format
    assert ("hour_format_24_display_name" in names) is has_hour_format
    assert ("hour_format_12_display_name" in names) is has_hour_format


def test_string_resources_omits_switches_the_face_hides() -> None:
    """A hidden layer gets no editor label."""
    hidden = _face(
        style=STYLE_ANALOG,
        show_ticks=False,
        show_date=False,
        show_battery=False,
    )
    assert string_resources(hidden) == (
        ("slot_1_display_name", "Complication 1"),
        ("theme_color_0_display_name", "Ember"),
        ("theme_color_display_name", "Color theme"),
        ("watch_face_name", "Probe Face"),
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_layout_places_decoration_then_time_date_and_slots() -> None:
    """Draw order is decoration, time, date, then complications."""
    boxes = layout(by_slug("signal-digital"))
    assert tuple(box.name for box in boxes) == (
        "dial",
        "ticks",
        "arc",
        "hands",
        "time",
        "date",
        "complication-1",
        "complication-2",
    )
    for box in boxes[:4]:
        assert box == LayoutBox(box.name, 0, 0, 450, 450, decorative=True)
    assert all(not box.decorative for box in boxes[4:])
    assert boxes[6] == LayoutBox("complication-1", 150, 280, 150, 44)
    assert boxes[7] == LayoutBox("complication-2", 150, 66, 150, 40)


@pytest.mark.parametrize(
    ("slug", "expected"),
    [
        ("signal-digital", LayoutBox("time", 63, 135, 324, 128)),
        ("harbor-hybrid", LayoutBox("time", 63, 252, 324, 61)),
        ("ledger-forward", LayoutBox("time", 85, 72, 279, 80)),
        ("tally-digital", LayoutBox("time", 56, 120, 288, 151)),
    ],
)
def test_layout_sizes_the_time_readout_per_style(slug: str, expected: LayoutBox) -> None:
    """Each style centres its own read-out band on the design edge."""
    assert box_of(by_slug(slug), "time") == expected


def test_layout_scales_with_the_design_edge() -> None:
    """One number drives the whole layout, so 400 and 450 both work."""
    assert box_of(by_slug("tally-digital"), "dial") == LayoutBox(
        "dial", 0, 0, 400, 400, decorative=True
    )
    assert box_of(by_slug("tally-digital"), "date") == LayoutBox("date", 140, 24, 120, 38)


def test_layout_hides_the_boxes_a_face_does_not_use() -> None:
    """A hand-only face places no time box; a bare face places no date box."""
    assert tuple(box.name for box in layout(by_slug("meridian-analog"))) == (
        "dial",
        "ticks",
        "arc",
        "hands",
        "date",
        "complication-1",
        "complication-2",
    )
    bare = _face(show_date=False)
    assert tuple(box.name for box in layout(bare)) == (*DECORATION_BOXES, "complication-1")


def test_box_of_looks_boxes_up_and_names_a_missing_one() -> None:
    """The lookup answers for placed boxes and refuses the rest."""
    spec = by_slug("aurora-analog")
    assert box_of(spec, "hands") == LayoutBox("hands", 0, 0, 450, 450, decorative=True)
    assert box_of(spec, "complication-3") == LayoutBox("complication-3", 60, 205, 74, 40)
    with pytest.raises(ValueError, match="face aurora-analog has no layout box 'time'"):
        box_of(spec, "time")
    with pytest.raises(ValueError, match="has no layout box 'nowhere'"):
        box_of(_face(), "nowhere")


# ---------------------------------------------------------------------------
# Root element and versions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("shape", "clip_shape", "corner"),
    [
        (SHAPE_ROUND, "CIRCLE", None),
        (SHAPE_SQUARE, "RECTANGLE", "72"),
        (SHAPE_RECT, "RECTANGLE", "72"),
    ],
)
def test_root_carries_the_edge_and_the_clip_shape(
    shape: str, clip_shape: str, corner: str | None
) -> None:
    """``clipShape`` follows the shape and only boxes get corner radii."""
    root = build_watch_face(_face(shape=shape))
    assert root.tag == "WatchFace"
    assert root.get("clipShape") == clip_shape
    assert (root.get("width"), root.get("height")) == ("450", "450")
    assert root.get("cornerRadiusX") == corner
    assert root.get("cornerRadiusY") == corner


def test_a_non_default_edge_scales_the_root_and_the_radii() -> None:
    """A 400 px design emits a 400 px screen and a 64 px corner."""
    root = build_watch_face(_face(shape=SHAPE_RECT, design_edge=400))
    assert (root.get("width"), root.get("height")) == ("400", "400")
    assert root.get("cornerRadiusX") == "64"


def test_schema_location_tracks_the_version_under_the_official_root() -> None:
    """Every published version points inside Google's XSD folder."""
    assert WFF_VERSIONS == (1, 2, 3, 4)
    for version in WFF_VERSIONS:
        assert schema_location(version) == f"{SCHEMA_ROOT_URL}/{version}/watchface.xsd"
    root = build_watch_face(_face(), wff_version=2)
    key = f"{{{XSI_NAMESPACE}}}noNamespaceSchemaLocation"
    assert root.get(key) == schema_location(2)
    assert root.get(key) != schema_location(DEFAULT_WFF_VERSION)


def test_build_watch_face_rejects_an_unpublished_version() -> None:
    """A version Google does not publish is refused, not guessed at."""
    for bad in (0, 5, -1):
        with pytest.raises(ValueError, match=r"wff_version must be one of \(1, 2, 3, 4\)"):
            build_watch_face(_face(), wff_version=bad)


def test_metadata_rows_state_the_preview_time_clock_type_and_step_goal() -> None:
    """CLOCK_TYPE follows the style and STEP_GOAL follows the slot."""
    rows = {
        element.get("key"): element.get("value")
        for element in build_watch_face(by_slug("harbor-hybrid"))
        if element.tag == "Metadata"
    }
    assert rows == {
        "PREVIEW_TIME": DEFAULT_PREVIEW_TIME,
        "CLOCK_TYPE": "ANALOG",
        "STEP_GOAL": str(DEFAULT_STEP_GOAL),
    }
    plain = {
        element.get("key"): element.get("value")
        for element in build_watch_face(_face(style=STYLE_DIGITAL, show_step_complication=False))
        if element.tag == "Metadata"
    }
    assert plain == {"PREVIEW_TIME": "10:09:30", "CLOCK_TYPE": "DIGITAL"}
    preview = _child(build_watch_face(_face(style=STYLE_ANALOG)), "Metadata")
    assert preview.get("key") == "PREVIEW_TIME"
    assert preview.get("value") == DEFAULT_PREVIEW_TIME


# ---------------------------------------------------------------------------
# User configurations
# ---------------------------------------------------------------------------


def test_user_configurations_offer_the_colourways_and_the_switches() -> None:
    """One ColorOption per colourway plus one switch per offered layer."""
    configurations = _child(build_watch_face(by_slug("aurora-analog")), "UserConfigurations")
    assert [child.tag for child in configurations] == [
        "ColorConfiguration",
        "BooleanConfiguration",
        "BooleanConfiguration",
        "BooleanConfiguration",
    ]
    colour = configurations[0]
    assert colour.attrib == {
        "id": THEME_CONFIGURATION_ID,
        "displayName": "@string/theme_color_display_name",
        "defaultValue": "0",
    }
    assert [child.get("colors") for child in colour] == [
        "#FF7A18FF #FFC94DFF #FFF3E0FF",
        "#2BE0B7FF #7CFFCBFF #E8FFF8FF",
        "#3D7BFFFF #9EC2FFFF #EEF4FFFF",
    ]
    assert [child.get("id") for child in colour] == ["0", "1", "2"]
    assert [child.get("displayName") for child in colour] == [
        "@string/theme_color_0_display_name",
        "@string/theme_color_1_display_name",
        "@string/theme_color_2_display_name",
    ]
    assert [child.get("id") for child in configurations[1:]] == [
        "showTicks",
        "showDate",
        "showBattery",
    ]
    assert [child.get("defaultValue") for child in configurations[1:]] == ["true"] * 3


def test_hidden_layers_get_no_editor_switch() -> None:
    """A face that hides ticks, date, and battery only sells the colourway."""
    configurations = build_watch_face(
        _face(show_ticks=False, show_date=False, show_battery=False)
    ).find("UserConfigurations")
    assert configurations is not None
    assert [child.tag for child in configurations] == ["ColorConfiguration"]


@pytest.mark.parametrize(
    "style",
    [STYLE_DIGITAL, STYLE_HYBRID, STYLE_COMPLICATION],
)
def test_numeric_faces_append_the_hour_format_list(style: str) -> None:
    """Numeric faces offer exactly the two documented hour formats."""
    configurations = build_watch_face(_face(style=style)).find("UserConfigurations")
    assert configurations is not None
    listing = configurations[-1]
    assert listing.tag == "ListConfiguration"
    assert listing.attrib == {
        "id": "hourFormat",
        "displayName": "@string/hour_format_display_name",
        "defaultValue": "H24",
    }
    assert [(child.tag, child.get("id")) for child in listing] == [
        ("ListOption", "H24"),
        ("ListOption", "H12"),
    ]
    assert [child.get("displayName") for child in listing] == [
        "@string/hour_format_24_display_name",
        "@string/hour_format_12_display_name",
    ]


def test_an_analog_face_offers_no_hour_format() -> None:
    """Hands do not need a 12/24 switch."""
    configurations = build_watch_face(_face(style=STYLE_ANALOG)).find("UserConfigurations")
    assert configurations is not None
    assert "ListConfiguration" not in [child.tag for child in configurations]


# ---------------------------------------------------------------------------
# Dial layer
# ---------------------------------------------------------------------------


def test_dial_layer_draws_the_ring_markers_and_arc() -> None:
    """Decoration is ring, twelve markers, then the edge arc."""
    dial = _dial(by_slug("aurora-analog"))
    assert dial.attrib == {"name": "dialLayer", "x": "0", "y": "0", "width": "450", "height": "450"}
    assert [child.get("name") for child in dial if child.tag == "PartDraw"] == [
        "dialRing",
        *[f"tick{hour}" for hour in range(12)],
        "progressArc",
    ]
    assert _ambient_alpha(dial) == str(AMBIENT_ALPHA_FULL)


def test_ring_and_arc_are_stroked_at_the_documented_thickness() -> None:
    """The ring insets by half its own stroke; the arc hugs the edge."""
    dial = _dial(by_slug("aurora-analog"))
    ring = _named(dial, "dialRing")
    ellipse = _child(ring, "Ellipse")
    assert ellipse.attrib == {"x": "2.7", "y": "2.7", "width": "444.6", "height": "444.6"}
    stroke = _child(ellipse, "Stroke")
    assert stroke.attrib == {
        "color": THEME_EXPRESSION,
        "thickness": "5.4",
        "cap": "ROUND",
    }
    arc = _child(_named(dial, "progressArc"), "Arc")
    assert arc.attrib == {
        "centerX": "225",
        "centerY": "225",
        "width": "423",
        "height": "423",
        "startAngle": "0",
        "endAngle": "360",
        "direction": "CLOCKWISE",
    }
    arc_stroke = _child(arc, "Stroke")
    assert arc_stroke.attrib == {
        "color": "[CONFIGURATION.themeColor].1",
        "thickness": "1.8",
        "cap": "BUTT",
    }
    assert _ambient_alpha(_named(dial, "progressArc")) == str(AMBIENT_ALPHA_DIM)


def test_marker_geometry_is_twelve_lines_around_the_centre() -> None:
    """Markers sit on a 30 degree fan, shorter on a hand-only dial."""
    dial = _dial(by_slug("aurora-analog"))
    top = _child(_named(dial, "tick0"), "Line")
    assert top.attrib == {"startX": "225", "startY": "45", "endX": "225", "endY": "20.25"}
    three = _child(_named(dial, "tick3"), "Line")
    assert three.attrib == {"startX": "405", "startY": "225", "endX": "429.75", "endY": "225"}
    stroke = _child(three, "Stroke")
    assert stroke.get("thickness") == "4.5"
    hybrid_dial = _dial(by_slug("harbor-hybrid"))
    hybrid_line = _child(_named(hybrid_dial, "tick0"), "Line")
    assert hybrid_line.get("startY") == "33.75"


def test_a_face_without_markers_has_only_the_ring_and_the_arc() -> None:
    """``show_ticks`` off leaves the dial clean."""
    dial = _dial(by_slug("signal-digital"))
    assert [child.get("name") for child in dial if child.tag == "PartDraw"] == [
        "dialRing",
        "progressArc",
    ]


def test_the_arc_is_skipped_when_no_slot_offers_a_ranged_value() -> None:
    """No gauge data means no edge arc."""
    dial = _dial(by_slug("meridian-analog"))
    names = [child.get("name") for child in dial if child.tag == "PartDraw"]
    assert "progressArc" not in names
    assert names[0] == "dialRing"


def test_ambient_minimal_drops_the_markers_and_dims_the_dial() -> None:
    """An ambient-minimal face keeps the ring faint and loses the markers."""
    dial = _dial(by_slug("meridian-analog"))
    assert _ambient_alpha(_named(dial, "tick0")) == str(AMBIENT_ALPHA_HIDDEN)
    assert _ambient_alpha(_named(dial, "dialRing")) == str(AMBIENT_ALPHA_DIM)
    assert _ambient_alpha(dial) == str(AMBIENT_ALPHA_DIM)
    plain = _dial(by_slug("harbor-hybrid"))
    assert _ambient_alpha(_named(plain, "dialRing")) is None
    assert _ambient_alpha(_named(plain, "tick0")) is None


# ---------------------------------------------------------------------------
# Read-out layer
# ---------------------------------------------------------------------------


def test_digital_clock_is_skipped_for_a_hand_only_face() -> None:
    """An analog face has no DigitalClock; a numeric one centres its text."""
    assert _group(_scene_of(by_slug("meridian-analog")), "readoutLayer") is not None
    scene_element = _scene_of(by_slug("signal-digital"))
    readout = _group(scene_element, "readoutLayer")
    assert readout is not None
    clock = _child(readout, "DigitalClock")
    assert clock.attrib == {"x": "63", "y": "135", "width": "324", "height": "128"}
    time_text = _child(clock, "TimeText")
    assert time_text.attrib == {
        "align": "CENTER",
        "format": "HH:mm",
        "height": "128",
        "hourFormat": "SYNC_TO_DEVICE",
        "tintColor": "[CONFIGURATION.themeColor]",
        "width": "324",
        "x": "63",
        "y": "135",
    }
    assert _ambient_alpha(clock) == str(AMBIENT_ALPHA_FULL)
    hand_only = _scene_of(by_slug("meridian-analog"))
    hand_readout = _group(hand_only, "readoutLayer")
    assert hand_readout is not None
    assert hand_readout.find("DigitalClock") is None


def test_date_line_is_a_template_of_month_and_day() -> None:
    """The date line substitutes two expressions and takes the light colour."""
    scene_element = _scene_of(by_slug("aurora-analog"))
    readout = _group(scene_element, "readoutLayer")
    assert readout is not None
    date = _named(readout, "dateLine")
    assert date.attrib == {
        "name": "dateLine",
        "x": "157",
        "y": "27",
        "width": "135",
        "height": "32",
        "tintColor": "[CONFIGURATION.themeColor].1",
    }
    font = date.find("Text/Font")
    assert font is not None
    assert font.attrib == {
        "family": "sans-serif-light",
        "size": "20",
        "color": "#FFF3E0FF",
    }
    assert font.text is None
    template = _child(font, "Template")
    assert template.text == "%s %s"
    assert [child.get("expression") for child in template] == list(DATE_PARAMETERS)


def test_readout_layer_is_omitted_when_an_analog_face_shows_nothing() -> None:
    """No digits and no date means no read-out layer at all."""
    bare = _face(style=STYLE_ANALOG, show_date=False)
    scene_element = _scene_of(bare)
    assert _group(scene_element, "readoutLayer") is None
    assert [child.tag for child in scene_element] == [
        "Group",
        "AnalogClock",
        "ComplicationSlot",
    ]


# ---------------------------------------------------------------------------
# Hands
# ---------------------------------------------------------------------------


def test_analog_clock_emits_three_hands_in_draw_order() -> None:
    """Hour, minute, then second, each with its own drawable."""
    scene_element = _scene_of(by_slug("aurora-analog"))
    clock = _child(scene_element, "AnalogClock")
    assert clock.attrib == {"x": "0", "y": "0", "width": "450", "height": "450"}
    assert [child.tag for child in clock] == ["HourHand", "MinuteHand", "SecondHand", "Variant"]
    assert [child.get("resource") for child in clock[:3]] == [
        "@drawable/hand_hour",
        "@drawable/hand_minute",
        "@drawable/hand_second",
    ]
    assert [child.get("alpha") for child in clock[:3]] == ["255", "255", str(AMBIENT_ALPHA_DIM)]
    assert [child.get("tintColor") for child in clock[:3]] == [
        THEME_EXPRESSION,
        THEME_EXPRESSION,
        "[CONFIGURATION.themeColor].1",
    ]
    assert clock[0].get("pivotX") == "0.5"
    assert clock[0].get("pivotY") == "0.5"
    assert _ambient_alpha(clock) == str(AMBIENT_ALPHA_FULL)


def test_a_face_without_hands_has_no_analog_clock() -> None:
    """``show_hands`` off drops the whole element."""
    assert _scene_of(by_slug("signal-digital")).find("AnalogClock") is None
    assert _scene_of(_face(style=STYLE_HYBRID, show_hands=False)).find("AnalogClock") is None


# ---------------------------------------------------------------------------
# Complications
# ---------------------------------------------------------------------------


def test_slot_carries_a_bounding_shape_and_one_complication_per_type() -> None:
    """Every supported type gets its own Complication, in declared order."""
    slot = _scene_of(by_slug("aurora-analog"))[3]
    assert slot.tag == "ComplicationSlot"
    assert slot.attrib == {
        "displayName": "@string/slot_1_display_name",
        "height": "46",
        "slotId": "1",
        "supportedTypes": "SHORT_TEXT RANGED_VALUE",
        "tintColor": THEME_EXPRESSION,
        "width": "114",
        "x": "168",
        "y": "132",
    }
    assert [child.tag for child in slot] == [
        "BoundingOval",
        "Complication",
        "Complication",
        "DefaultProviderPolicy",
        "Variant",
    ]
    assert slot[0].attrib == {"x": "0", "y": "0", "width": "114", "height": "46"}
    assert [child.get("type") for child in slot[1:3]] == ["SHORT_TEXT", "RANGED_VALUE"]
    part = _child(slot[1], "PartText")
    assert part.attrib == {
        "name": "slot1short_text",
        "x": "0",
        "y": "0",
        "width": "114",
        "height": "46",
        "tintColor": THEME_EXPRESSION,
    }
    template = part.find("Text/Font/Template")
    assert template is not None
    assert [child.get("expression") for child in template] == ["[COMPLICATION.TEXT]"]


def test_a_boxed_face_clips_with_a_bounding_box() -> None:
    """Only a round face clips with an oval."""
    for shape, tag in ((SHAPE_SQUARE, "BoundingBox"), (SHAPE_RECT, "BoundingBox")):
        slot = [child for child in _scene_of(_face(shape=shape)) if child.tag == "ComplicationSlot"]
        assert len(slot) == 1, shape
        assert slot[0][0].tag == tag, shape
    round_slot = [child for child in _scene_of(_face()) if child.tag == "ComplicationSlot"]
    assert round_slot[0][0].tag == "BoundingOval"


def test_image_complications_render_one_image_part() -> None:
    """Each image type points at its own complication expression."""
    slot = _slot(slot_id=6, width=60, height=30, supported_types=tuple(IMAGE_EXPRESSIONS))
    for kind, expression in IMAGE_EXPRESSIONS.items():
        parts = _complication_content(_face(), slot, kind)
        assert len(parts) == 1
        part = parts[0]
        assert part.tag == "PartImage"
        assert part.attrib == {"x": "0", "y": "0", "width": "60", "height": "30"}
        image = _child(part, "Image")
        assert image.get("resource") == expression
        assert _ambient_alpha(part) == str(AMBIENT_ALPHA_FULL)


def test_text_complications_use_their_documented_expression() -> None:
    """Short text, long text, and a ranged value each pull their own token."""
    slot = _slot(slot_id=2, width=90, height=28)
    for kind, expression in TEXT_EXPRESSIONS.items():
        part = _complication_content(_face(), slot, kind)[0]
        assert part.tag == "PartText"
        assert part.get("name") == f"slot2{kind.lower()}"
        template = part.find("Text/Font/Template")
        assert template is not None
        assert template.text == "%s"
        assert [child.get("expression") for child in template] == [expression]


def test_empty_slots_render_nothing_inside_their_complication() -> None:
    """An EMPTY type is a placeholder the buyer fills or leaves blank."""
    slot_element = _scene_of(by_slug("meridian-analog"))[3]
    assert slot_element.get("supportedTypes") == "SHORT_TEXT EMPTY"
    assert [child.tag for child in slot_element] == [
        "BoundingOval",
        "Complication",
        "Complication",
        "Variant",
    ]
    empty = slot_element[2]
    assert empty.get("type") == "EMPTY"
    assert len(empty) == 0
    assert _ambient_alpha(slot_element) == str(AMBIENT_ALPHA_FULL)


def test_a_kind_outside_both_expression_tables_renders_no_parts() -> None:
    """A type with no expression is dropped rather than emitting a bad part."""
    assert _complication_content(_face(), _slot(), "EMPTY") == []
    assert _complication_content(_face(), _slot(), "SIREN") == []


def test_default_provider_policy_prefers_the_battery_on_the_lowest_ranged_slot() -> None:
    """One gauge is the battery; the next ranged slot defaults to steps."""
    spec = _face(
        complications=(
            _slot(slot_id=2, supported_types=("SHORT_TEXT", "RANGED_VALUE")),
            _slot(slot_id=5, supported_types=("SHORT_TEXT", "RANGED_VALUE")),
            _slot(slot_id=9, supported_types=("SHORT_TEXT", "SMALL_IMAGE")),
        )
    )
    slots = [child for child in _scene_of(spec) if child.tag == "ComplicationSlot"]
    assert [child.get("slotId") for child in slots] == ["2", "5", "9"]
    assert _policy(slots[0]) == {
        "defaultSystemProvider": "BATTERY",
        "defaultSystemProviderType": "RANGED_VALUE",
    }
    assert _policy(slots[1]) == {
        "defaultSystemProvider": "STEP_COUNT",
        "defaultSystemProviderType": "RANGED_VALUE",
    }
    assert _policy(slots[2]) == {
        "defaultSystemProvider": "STEP_COUNT",
        "defaultSystemProviderType": "SHORT_TEXT",
    }


@pytest.mark.parametrize(
    ("overrides", "providers"),
    [
        (
            {
                "show_battery": False,
                "complications": (
                    _slot(slot_id=1, supported_types=("SHORT_TEXT", "RANGED_VALUE")),
                    _slot(slot_id=2, supported_types=("SHORT_TEXT", "MONOCHROMATIC_IMAGE")),
                ),
            },
            ["STEP_COUNT", "STEP_COUNT"],
        ),
        (
            {
                "show_battery": True,
                "complications": (
                    _slot(slot_id=1, supported_types=("SHORT_TEXT", "LONG_TEXT")),
                    _slot(slot_id=2, supported_types=("LONG_TEXT",)),
                ),
            },
            ["STEP_COUNT", "STEP_COUNT"],
        ),
    ],
)
def test_the_battery_default_needs_both_the_switch_and_a_ranged_slot(
    overrides: dict[str, object], providers: list[str]
) -> None:
    """Without a gauge to fill, every slot defaults to the step counter."""
    spec = _face(**overrides)
    slots = [child for child in _scene_of(spec) if child.tag == "ComplicationSlot"]
    assert len(slots) == len(providers)
    assert [_policy(child)["defaultSystemProvider"] for child in slots] == providers


def test_an_empty_slot_gets_no_default_provider_policy() -> None:
    """A slot the buyer may leave blank is never pre-filled."""
    slots = [
        child for child in _scene_of(by_slug("meridian-analog")) if child.tag == "ComplicationSlot"
    ]
    assert len(slots) == 2
    assert all(child.find("DefaultProviderPolicy") is None for child in slots)


# ---------------------------------------------------------------------------
# Numerals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("numeral", "x", "y"),
    [("12", 185, 45), ("3", 360, 185), ("6", 185, 351), ("9", 45, 185)],
)
def test_numeral_part_places_literal_digits_at_the_cardinals(
    numeral: str, x: int, y: int
) -> None:
    """Numerals are literal text in a square box at the four cardinal points."""
    part = numeral_part(by_slug("aurora-analog"), numeral)
    assert part.tag == "PartText"
    assert part.attrib == {
        "name": f"numeral{numeral}",
        "x": str(x),
        "y": str(y),
        "width": "80",
        "height": "80",
        "tintColor": "[CONFIGURATION.themeColor].1",
    }
    font = part.find("Text/Font")
    assert font is not None
    assert font.get("size") == "40"
    assert font.get("color") == "#FFF3E0FF"
    assert font.text == numeral
    assert font.find("Template") is None


def test_numerals_are_opt_in_and_land_in_the_dial_layer() -> None:
    """The plain document has no numerals; the opt-in adds four to the dial."""
    plain = _dial(by_slug("aurora-analog"))
    assert [child.tag for child in plain if child.tag == "PartText"] == []
    numbered = build_watch_face(by_slug("aurora-analog"), include_numerals=True)
    dial = _group(_scene_root(numbered), "dialLayer")
    assert dial is not None
    assert [child.get("name") for child in dial if child.tag == "PartText"] == [
        "numeral12",
        "numeral3",
        "numeral6",
        "numeral9",
    ]
    assert len(dial) == 19


# ---------------------------------------------------------------------------
# Serialising
# ---------------------------------------------------------------------------


def test_serialize_writes_the_declaration_and_indents_two_spaces() -> None:
    """The resource compiler wants a declaration and an indented body."""
    text = watch_face_xml(_face())
    lines = text.splitlines()
    assert lines[0] == '<?xml version="1.0" encoding="utf-8"?>'
    assert lines[1].startswith("<WatchFace ")
    assert lines[2] == '  <Metadata key="PREVIEW_TIME" value="10:09:30" />'
    assert lines[-1] == "</WatchFace>"
    assert text.endswith("\n")
    assert f'xmlns:xsi="{XSI_NAMESPACE}"' in lines[1]
    assert "xsi:noNamespaceSchemaLocation=" in lines[1]
    assert ElementTree.fromstring(text).tag == "WatchFace"


def test_watch_face_xml_is_the_tree_serialised() -> None:
    """The text helper is build plus serialize, nothing else."""
    spec = by_slug("ledger-forward")
    assert watch_face_xml(spec) == serialize(build_watch_face(spec))
    numbered = watch_face_xml(by_slug("cadence-forward"), include_numerals=True, wff_version=1)
    assert "numeral12" in numbered
    assert f"/{1}/watchface.xsd" in numbered


def test_scene_background_is_opaque_black_per_the_visual_rule() -> None:
    """WO-V13: the scene paints its own opaque background."""
    scene_element = _scene_of(_face())
    assert scene_element.get("backgroundColor") == "#000000FF"
    assert _scene_of(_face(background="#102030")).get("backgroundColor") == "#102030FF"


def test_every_shipped_face_builds_parses_and_stays_in_vocabulary() -> None:
    """All thirteen faces emit on every published format version."""
    for spec in WATCH_FACE_CATALOG:
        for version in WFF_VERSIONS:
            text = watch_face_xml(spec, wff_version=version, include_numerals=True)
            root = ElementTree.fromstring(text)
            assert root.tag == "WatchFace"
            assert root.get("clipShape") == ("CIRCLE" if spec.shape == "round" else "RECTANGLE")
            assert _tags(root) <= set(ELEMENT_VOCABULARY)
        assert f'backgroundColor="{spec.background.upper()}FF"' in watch_face_xml(spec)
    assert len(WATCH_FACE_CATALOG) == 13
    assert {spec.style for spec in WATCH_FACE_CATALOG} == set(STYLES)
    assert {spec.shape for spec in WATCH_FACE_CATALOG} == set(SHAPES)
