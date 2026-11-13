"""Watch Face Format XML builder: the document the platform renderer reads.

Element and attribute names follow the published WFF reference pages, and the
vocabulary tables at the bottom of this module are what :mod:`ez_watch.validate`
checks a generated document against. ``layout`` is the single source of
geometry, so the preview artwork and the XML always agree and one design
scales onto both the 192 dp and the 227 dp round reference devices.

Hermetic at import: stdlib plus ``ez_raster`` and ``ez_common.json_value``.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ElementTree
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ez_raster import hex_to_rgba, rgba_to_hex

from ez_watch.catalog import (
    DEFAULT_STEP_GOAL,
    STYLE_ANALOG,
    STYLE_COMPLICATION,
    STYLE_DIGITAL,
    STYLE_HYBRID,
    COMPLICATION_TYPES,
    ComplicationSlotSpec,
    WatchFaceSpec,
)

XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
"""Namespace bound to the ``xsi`` prefix on the root element."""

SCHEMA_ROOT_URL = (
    "https://raw.githubusercontent.com/google/watchface/main/third_party/wff"
    "/specification/documents"
)
"""Root of the official per-version XSD folder.

The path is the one the requirements digest confirms; the file name inside each
version folder is derived, so the value is advisory (it drives Android Studio
completion) and can be replaced wholesale by a caller.
"""

WFF_VERSIONS: tuple[int, ...] = (1, 2, 3, 4)
"""Format versions Google documents, mapped to the Wear OS API they need."""

WFF_VERSION_API: Mapping[int, int] = {1: 33, 2: 34, 3: 35, 4: 36}
"""WFF version to ``minSdkVersion``: v1/API 33 through v4/API 36."""

DEFAULT_WFF_VERSION = 4
"""Version emitted when the operator does not name one.

From January 2026 the format is required for every install, so new faces ship
on the current version and the operator can drop it for wider reach.
"""

DEFAULT_PREVIEW_TIME = "10:09:30"
"""``Metadata`` ``PREVIEW_TIME`` value: the classic marketing hand position."""

THEME_CONFIGURATION_ID = "themeColor"
"""``ColorConfiguration id`` every face emits."""

THEME_EXPRESSION = "[CONFIGURATION.themeColor]"
"""Expression that resolves to the buyer's chosen colourway."""

AMBIENT_MODE = "AMBIENT"
"""The only ``Variant mode`` value Google documents."""

AMBIENT_ALPHA_HIDDEN = 0
"""Alpha used to drop a decorative layer out of the ambient frame."""

AMBIENT_ALPHA_DIM = 96
"""Alpha used to keep a decorative layer faintly present in ambient."""

AMBIENT_ALPHA_FULL = 255
"""Alpha used for the time, hands, and complications in ambient."""

IMAGE_EXPRESSIONS: Mapping[str, str] = {
    "MONOCHROMATIC_IMAGE": "[COMPLICATION.MONOCHROMATIC_IMAGE]",
    "SMALL_IMAGE": "[COMPLICATION.SMALL_IMAGE]",
    "PHOTO_IMAGE": "[COMPLICATION.PHOTO_IMAGE]",
}
"""``Image resource`` expression per image complication type."""

TEXT_EXPRESSIONS: Mapping[str, str] = {
    "SHORT_TEXT": "[COMPLICATION.TEXT]",
    "LONG_TEXT": "[COMPLICATION.TEXT]",
    "RANGED_VALUE": "[COMPLICATION.RANGED_VALUE_VALUE]",
}
"""``Parameter expression`` per text-bearing complication type."""

DATE_PARAMETERS: tuple[str, ...] = ("[MONTH_S]", "[DAY]")
"""Date expression pair, taken from the ``PartText`` reference example."""

_HAND_TAGS: tuple[str, ...] = ("HourHand", "MinuteHand", "SecondHand")
"""``AnalogClock`` hand elements, in draw order."""

_HAND_DRAWABLES: tuple[str, ...] = ("hand_hour", "hand_minute", "hand_second")
"""Drawable names :mod:`ez_watch.project` generates for the three hands."""

ElementTree.register_namespace("xsi", XSI_NAMESPACE)
"""Bind the ``xsi`` prefix so the schema location writes out readable."""


@dataclass(frozen=True)
class LayoutBox:
    """One placed element in a face.

    Attributes:
        name: Stable key the builder looks the box up by.
        x: Left edge in visual-screen pixels.
        y: Top edge in visual-screen pixels.
        width: Box width in visual-screen pixels.
        height: Box height in visual-screen pixels.
        decorative: True for a full-screen layer a sibling may sit inside, so
            the overlap check only compares content boxes.
    """

    name: str
    x: int
    y: int
    width: int
    height: int
    decorative: bool = False


# The four scalars the Watch Face Format spells into an attribute.
AttrValue = str | int | float | bool


def _el(tag: str, **attrs: AttrValue) -> ElementTree.Element:
    """Build an element with its attributes sorted for stable output.

    Args:
        tag: Element name from the WFF vocabulary.
        **attrs: Attribute values; booleans become ``true`` / ``false``.

    Returns:
        The element, children still to be appended.
    """
    element = ElementTree.Element(tag)
    for key in sorted(attrs):
        element.set(key, _attr_text(attrs[key]))
    return element


def _attr_text(value: AttrValue) -> str:
    """Render one attribute value the way WFF spells it.

    Args:
        value: Value handed to :func:`_el`.

    Returns:
        The string written into the document.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def theme_color(spec: WatchFaceSpec, index: int) -> str:
    """Default colourway colour, used where an expression is not allowed.

    Args:
        spec: Face being built.
        index: Colour position in the colourway; clamped to the colourway.

    Returns:
        An eight-digit ARGB hex string.
    """
    colors = spec.palette[0].colors
    return rgba_to_hex(hex_to_rgba(colors[min(index, len(colors) - 1)]), include_alpha=True)


def _theme_reference(spec: WatchFaceSpec, index: int) -> str:
    """Expression for one colour slot of the buyer's colourway.

    Args:
        spec: Face being built.
        index: Colour position; falls back to the first colour when the
            colourway is too short to have one.

    Returns:
        Something like ``[CONFIGURATION.themeColor.1]``.
    """
    widest = max(len(theme.colors) for theme in spec.palette)
    if index < 1 or index >= widest:
        return THEME_EXPRESSION
    return f"{THEME_EXPRESSION}.{index}"


def _ambient(target: str, value: int) -> ElementTree.Element:
    """One ambient-mode attribute override.

    Args:
        target: Transformable attribute to change in ambient.
        value: Value to use in ambient.

    Returns:
        The ``Variant`` element.
    """
    return _el("Variant", mode=AMBIENT_MODE, target=target, value=value)


def string_resources(spec: WatchFaceSpec) -> tuple[tuple[str, str], ...]:
    """String resources the emitted XML references.

    Args:
        spec: Face being built.

    Returns:
        ``(name, english value)`` pairs sorted by name, ready for
        ``res/values/strings.xml``.
    """
    rows: list[tuple[str, str]] = [("watch_face_name", spec.name)]
    rows.append(("theme_color_display_name", "Color theme"))
    for index, theme in enumerate(spec.palette):
        rows.append((f"theme_color_{index}_display_name", theme.name))
    for slot in spec.complications:
        rows.append((f"slot_{slot.slot_id}_display_name", f"Complication {slot.slot_id}"))
    if spec.show_ticks:
        rows.append(("show_ticks_display_name", "Hour markers"))
    if spec.show_date:
        rows.append(("show_date_display_name", "Date"))
    if spec.show_battery:
        rows.append(("show_battery_display_name", "Battery"))
    if spec.style in {STYLE_DIGITAL, STYLE_HYBRID, STYLE_COMPLICATION}:
        rows.append(("hour_format_display_name", "Hour format"))
        rows.append(("hour_format_24_display_name", "24 hour"))
        rows.append(("hour_format_12_display_name", "12 hour"))
    return tuple(sorted(rows))


def layout(spec: WatchFaceSpec) -> tuple[LayoutBox, ...]:
    """Place every element of one face from its spec alone.

    Everything is a fraction of ``design_edge``, so the same spec lays out the
    same way on the 192 dp and the 227 dp round device.

    Args:
        spec: Face being laid out.

    Returns:
        Boxes in draw order: decoration first, then the time read-out, the
        date, the hands, and the complications last.
    """
    edge = spec.design_edge
    boxes: list[LayoutBox] = [
        LayoutBox("dial", 0, 0, edge, edge, decorative=True),
        LayoutBox("ticks", 0, 0, edge, edge, decorative=True),
        LayoutBox("arc", 0, 0, edge, edge, decorative=True),
        LayoutBox("hands", 0, 0, edge, edge, decorative=True),
    ]
    if spec.style != STYLE_ANALOG:
        if spec.style == STYLE_HYBRID:
            width = int(edge * 0.72)
            top = int(edge * 0.56)
            height = int(spec.typography.time_size * 1.4)
        elif spec.style == STYLE_COMPLICATION:
            width = int(edge * 0.62)
            top = int(edge * 0.16)
            height = int(spec.typography.time_size * 1.25)
        else:
            width = int(edge * 0.72)
            top = int(edge * 0.30)
            height = int(spec.typography.time_size * 1.4)
        boxes.append(LayoutBox("time", (edge - width) // 2, top, width, height))
    if spec.show_date:
        width = int(edge * 0.30)
        height = int(spec.typography.label_size * 1.6)
        boxes.append(LayoutBox("date", (edge - width) // 2, int(edge * 0.06), width, height))
    for slot in spec.complications:
        boxes.append(
            LayoutBox(f"complication-{slot.slot_id}", slot.x, slot.y, slot.width, slot.height)
        )
    return tuple(boxes)


def box_of(spec: WatchFaceSpec, name: str) -> LayoutBox:
    """Look one laid-out box up by name.

    Args:
        spec: Face that was laid out.
        name: Box name from :func:`layout`.

    Returns:
        The matching box.

    Raises:
        ValueError: the face does not place a box with that name.
    """
    for item in layout(spec):
        if item.name == name:
            return item
    raise ValueError(f"face {spec.slug} has no layout box {name!r}")


def _metadata(spec: WatchFaceSpec) -> list[ElementTree.Element]:
    """``Metadata`` rows for the preview time and the step goal.

    Args:
        spec: Face being built.

    Returns:
        Metadata elements in document order.
    """
    clock_type = "ANALOG" if spec.style in {STYLE_ANALOG, STYLE_HYBRID} else "DIGITAL"
    rows = [
        _el("Metadata", key="PREVIEW_TIME", value=DEFAULT_PREVIEW_TIME),
        _el("Metadata", key="CLOCK_TYPE", value=clock_type),
    ]
    if spec.show_step_complication:
        rows.append(_el("Metadata", key="STEP_GOAL", value=DEFAULT_STEP_GOAL))
    return rows


def _color_configuration(spec: WatchFaceSpec) -> ElementTree.Element:
    """The colourway picker: one ``ColorOption`` per palette entry.

    Args:
        spec: Face being built.

    Returns:
        The ``ColorConfiguration`` element.
    """
    configuration = _el(
        "ColorConfiguration",
        id=THEME_CONFIGURATION_ID,
        displayName="@string/theme_color_display_name",
        defaultValue=0,
    )
    for index, theme in enumerate(spec.palette):
        colors = " ".join(
            rgba_to_hex(hex_to_rgba(color), include_alpha=True) for color in theme.colors
        )
        configuration.append(
            _el(
                "ColorOption",
                id=index,
                displayName=f"@string/theme_color_{index}_display_name",
                colors=colors,
            )
        )
    return configuration


def _boolean_configuration(
    config_id: str, display_name: str, default: bool
) -> ElementTree.Element:
    """One editor on/off switch.

    Args:
        config_id: Configuration id referenced by expressions.
        display_name: String resource name shown in the editor.
        default: Switch position when the buyer has not touched it.

    Returns:
        The ``BooleanConfiguration`` element.
    """
    return _el(
        "BooleanConfiguration",
        id=config_id,
        displayName=f"@string/{display_name}",
        defaultValue=default,
    )


def _hour_format_configuration(spec: WatchFaceSpec) -> ElementTree.Element:
    """The 12/24 hour list offered to numeric faces.

    Args:
        spec: Face being built.

    Returns:
        The ``ListConfiguration`` element with its two options.
    """
    configuration = _el(
        "ListConfiguration",
        id="hourFormat",
        displayName="@string/hour_format_display_name",
        defaultValue="H24",
    )
    configuration.append(
        _el(
            "ListOption",
            id="H24",
            displayName="@string/hour_format_24_display_name",
        )
    )
    configuration.append(
        _el(
            "ListOption",
            id="H12",
            displayName="@string/hour_format_12_display_name",
        )
    )
    return configuration


def _user_configurations(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """The editor settings block, or None when the face offers nothing.

    Args:
        spec: Face being built.

    Returns:
        The ``UserConfigurations`` element, or None.
    """
    children: list[ElementTree.Element] = [_color_configuration(spec)]
    if spec.show_ticks:
        children.append(_boolean_configuration("showTicks", "show_ticks_display_name", True))
    if spec.show_date:
        children.append(_boolean_configuration("showDate", "show_date_display_name", True))
    if spec.show_battery:
        children.append(_boolean_configuration("showBattery", "show_battery_display_name", True))
    if spec.style in {STYLE_DIGITAL, STYLE_HYBRID, STYLE_COMPLICATION}:
        children.append(_hour_format_configuration(spec))
    return _element_list("UserConfigurations", children)


def _element_list(tag: str, children: Sequence[ElementTree.Element]) -> ElementTree.Element:
    """Build an element and append children in the order given.

    Args:
        tag: Element name.
        children: Children to append.

    Returns:
        The parent element.
    """
    element = _el(tag)
    for child in children:
        element.append(child)
    return element


def _ring_part(spec: WatchFaceSpec) -> ElementTree.Element:
    """The dial ring: one stroked ellipse across the whole face.

    Args:
        spec: Face being built.

    Returns:
        The ``PartDraw`` element.
    """
    edge = spec.design_edge
    thickness = max(2.0, edge * 0.012)
    inset = thickness / 2.0
    ellipse = _el(
        "Ellipse",
        x=inset,
        y=inset,
        width=edge - thickness,
        height=edge - thickness,
    )
    ellipse.append(
        _el("Stroke", color=_theme_reference(spec, 0), thickness=thickness, cap="ROUND")
    )
    part = _element_list("PartDraw", [ellipse])
    part.set("x", "0")
    part.set("y", "0")
    part.set("width", str(edge))
    part.set("height", str(edge))
    part.set("name", "dialRing")
    if spec.ambient_minimal:
        part.append(_ambient("alpha", AMBIENT_ALPHA_DIM))
    return part


def _tick_parts(spec: WatchFaceSpec) -> list[ElementTree.Element]:
    """Twelve hour markers drawn as stroked lines.

    Args:
        spec: Face being built.

    Returns:
        One ``PartDraw`` per marker.
    """
    edge = spec.design_edge
    centre = edge / 2.0
    outer = edge * 0.455
    inner = edge * (0.40 if spec.style == STYLE_ANALOG else 0.425)
    thickness = max(2.0, edge * 0.010)
    parts: list[ElementTree.Element] = []
    for hour in range(12):
        angle = math.radians(hour * 30.0)
        dx = float(centre + outer * math.sin(angle))
        dy = float(centre - outer * math.cos(angle))
        sx = float(centre + inner * math.sin(angle))
        sy = float(centre - inner * math.cos(angle))
        line = _el("Line", startX=sx, startY=sy, endX=dx, endY=dy)
        line.append(
            _el("Stroke", color=_theme_reference(spec, 1), thickness=thickness, cap="ROUND")
        )
        part = _element_list("PartDraw", [line])
        part.set("x", "0")
        part.set("y", "0")
        part.set("width", str(edge))
        part.set("height", str(edge))
        part.set("name", f"tick{hour}")
        if spec.ambient_minimal:
            part.append(_ambient("alpha", AMBIENT_ALPHA_HIDDEN))
        parts.append(part)
    return parts


def _progress_arc(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """Edge arc that frames the ranged-value complications.

    Args:
        spec: Face being built.

    Returns:
        The ``PartDraw`` holding the arc, or None when no slot is ranged.
    """
    if not any("RANGED_VALUE" in slot.supported_types for slot in spec.complications):
        return None
    edge = spec.design_edge
    arc = _el(
        "Arc",
        centerX=edge / 2.0,
        centerY=edge / 2.0,
        width=edge * 0.94,
        height=edge * 0.94,
        startAngle=0.0,
        endAngle=360.0,
        direction="CLOCKWISE",
    )
    arc.append(
        _el(
            "Stroke",
            color=_theme_reference(spec, 1),
            thickness=max(1.0, edge * 0.004),
            cap="BUTT",
        )
    )
    part = _element_list("PartDraw", [arc])
    part.set("x", "0")
    part.set("y", "0")
    part.set("width", str(edge))
    part.set("height", str(edge))
    part.set("name", "progressArc")
    part.append(_ambient("alpha", AMBIENT_ALPHA_DIM))
    return part


def _text_part(
    spec: WatchFaceSpec,
    name: str,
    item: LayoutBox,
    text: str | None,
    parameters: Sequence[str],
    size: int,
    color: str,
    *,
    tint: str | None = None,
    ambient_alpha: int = AMBIENT_ALPHA_FULL,
) -> ElementTree.Element:
    """One ``PartText`` with either literal text or a template.

    Args:
        spec: Face being built; only used for the ambient policy.
        name: Element name so a ``Reference`` could find it.
        item: Box the text occupies.
        text: Literal string, when the part is not templated.
        parameters: Expressions substituted into the template's ``%s`` slots.
        size: Font size in pixels.
        color: Literal font colour as ARGB hex.
        tint: Theme expression the glyphs are tinted with.
        ambient_alpha: Alpha to hold in ambient.

    Returns:
        The ``PartText`` element.
    """
    font = _el("Font", family=spec.typography.family, size=size, color=color)
    if text is not None:
        font.text = text
    else:
        template = _el("Template")
        template.text = " ".join("%s" for _ in parameters) if parameters else ""
        for expression in parameters:
            template.append(_el("Parameter", expression=expression))
        font.append(template)
    text_element = _element_list("Text", [font])
    part = _element_list("PartText", [text_element])
    part.set("name", name)
    part.set("x", str(item.x))
    part.set("y", str(item.y))
    part.set("width", str(item.width))
    part.set("height", str(item.height))
    if tint is not None:
        part.set("tintColor", tint)
    part.append(_ambient("alpha", ambient_alpha))
    return part


def _digital_clock(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """The numeric time read-out, or None for a hand-only face.

    Args:
        spec: Face being built.

    Returns:
        The ``DigitalClock`` element, or None.
    """
    if spec.style == STYLE_ANALOG:
        return None
    item = box_of(spec, "time")
    time_text = _el(
        "TimeText",
        align="CENTER",
        format="HH:mm",
        height=item.height,
        hourFormat="SYNC_TO_DEVICE",
        tintColor=_theme_reference(spec, 0),
        width=item.width,
        x=item.x,
        y=item.y,
    )
    clock = _element_list("DigitalClock", [time_text])
    for key, value in (
        ("x", item.x),
        ("y", item.y),
        ("width", item.width),
        ("height", item.height),
    ):
        clock.set(key, str(value))
    clock.append(_ambient("alpha", AMBIENT_ALPHA_FULL))
    return clock


def _date_part(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """The date line, or None when the face hides it.

    Args:
        spec: Face being built.

    Returns:
        The ``PartText`` element, or None.
    """
    if not spec.show_date:
        return None
    item = box_of(spec, "date")
    return _text_part(
        spec,
        "dateLine",
        item,
        None,
        DATE_PARAMETERS,
        spec.typography.label_size,
        theme_color(spec, -1),
        tint=_theme_reference(spec, 1),
    )


def _analog_clock(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """The hand stack, drawn after the decoration and before complications.

    Args:
        spec: Face being built.

    Returns:
        The ``AnalogClock`` element, or None for a numeric-only face.
    """
    if not spec.show_hands:
        return None
    item = box_of(spec, "hands")
    hands: list[ElementTree.Element] = []
    for tag, drawable, alpha in zip(
        _HAND_TAGS, _HAND_DRAWABLES, (255, 255, AMBIENT_ALPHA_DIM), strict=True
    ):
        hand = _el(
            tag,
            alpha=alpha,
            height=item.height,
            pivotX=0.5,
            pivotY=0.5,
            resource=f"@drawable/{drawable}",
            tintColor=_theme_reference(spec, 0 if tag != "SecondHand" else 1),
            width=item.width,
            x=item.x,
            y=item.y,
        )
        hands.append(hand)
    clock = _element_list("AnalogClock", hands)
    for key, value in (
        ("x", item.x),
        ("y", item.y),
        ("width", item.width),
        ("height", item.height),
    ):
        clock.set(key, str(value))
    clock.append(_ambient("alpha", AMBIENT_ALPHA_FULL))
    return clock


def _complication_content(
    spec: WatchFaceSpec, slot: ComplicationSlotSpec, kind: str
) -> list[ElementTree.Element]:
    """The parts that render one complication type inside its slot.

    Args:
        spec: Face being built.
        slot: Slot the complication belongs to.
        kind: One entry from ``supported_types``.

    Returns:
        Parts to nest inside the ``Complication`` element.
    """
    if kind == "EMPTY":
        return []
    image = IMAGE_EXPRESSIONS.get(kind)
    if image is not None:
        image_element = _el("Image", resource=image)
        part = _element_list("PartImage", [image_element])
        for key, value in (
            ("x", 0),
            ("y", 0),
            ("width", slot.width),
            ("height", slot.height),
        ):
            part.set(key, str(value))
        part.append(_ambient("alpha", AMBIENT_ALPHA_FULL))
        return [part]
    expression = TEXT_EXPRESSIONS.get(kind)
    if expression is None:
        return []
    part = _text_part(
        spec,
        f"slot{slot.slot_id}{kind.lower()}",
        LayoutBox("content", 0, 0, slot.width, slot.height),
        None,
        (expression,),
        spec.typography.label_size,
        theme_color(spec, -1),
        tint=_theme_reference(spec, 0),
    )
    return [part]


def _bounding_shape(spec: WatchFaceSpec, slot: ComplicationSlotSpec) -> ElementTree.Element:
    """The single bounding area that clips one slot.

    Args:
        spec: Face being built.
        slot: Slot being bounded.

    Returns:
        A ``BoundingOval`` for a round face, a ``BoundingBox`` otherwise.
    """
    if spec.shape == "round":
        return _el("BoundingOval", x=0, y=0, width=slot.width, height=slot.height)
    return _el("BoundingBox", x=0, y=0, width=slot.width, height=slot.height)


def _complication_slot(
    spec: WatchFaceSpec, slot: ComplicationSlotSpec
) -> ElementTree.Element:
    """One ``ComplicationSlot`` with a bounding shape and its complications.

    Args:
        spec: Face being built.
        slot: Slot to emit.

    Returns:
        The element, ready to append last inside the scene.
    """
    children: list[ElementTree.Element] = [_bounding_shape(spec, slot)]
    for kind in slot.supported_types:
        complication = _element_list(
            "Complication", _complication_content(spec, slot, kind)
        )
        complication.set("type", kind)
        children.append(complication)
    policy = _default_provider(spec, slot)
    if policy is not None:
        provider, provider_type = policy
        children.append(
            _el(
                "DefaultProviderPolicy",
                defaultSystemProvider=provider,
                defaultSystemProviderType=provider_type,
            )
        )
    element = _element_list("ComplicationSlot", children)
    for key, value in (
        ("displayName", f"@string/slot_{slot.slot_id}_display_name"),
        ("height", slot.height),
        ("slotId", slot.slot_id),
        ("supportedTypes", " ".join(slot.supported_types)),
        ("tintColor", _theme_reference(spec, 0)),
        ("width", slot.width),
        ("x", slot.x),
        ("y", slot.y),
    ):
        element.set(key, str(value))
    element.append(_ambient("alpha", AMBIENT_ALPHA_FULL))
    return element


def _battery_slot_id(spec: WatchFaceSpec) -> int | None:
    """Slot the battery provider should default into.

    The lowest slot id that renders a ranged value is the natural gauge, and
    only that one takes the battery provider so a face with a step arc still
    gets a step default.

    Args:
        spec: Face being built.

    Returns:
        Slot id, or None when the face shows no battery or no ranged slot.
    """
    if not spec.show_battery:
        return None
    ranged = [slot.slot_id for slot in spec.complications if "RANGED_VALUE" in slot.supported_types]
    return min(ranged) if ranged else None


def _default_provider(
    spec: WatchFaceSpec, slot: ComplicationSlotSpec
) -> tuple[str, str] | None:
    """Default provider policy for one slot.

    Args:
        spec: Face being built.
        slot: Slot being defaulted.

    Returns:
        ``(provider, provider_type)``, or None for an EMPTY-only slot.
    """
    if "EMPTY" in slot.supported_types:
        return None
    if slot.slot_id == _battery_slot_id(spec):
        return ("BATTERY", "RANGED_VALUE")
    if "RANGED_VALUE" in slot.supported_types:
        return ("STEP_COUNT", "RANGED_VALUE")
    return ("STEP_COUNT", "SHORT_TEXT")


def _dial_group(spec: WatchFaceSpec) -> ElementTree.Element:
    """The background layer: ring, markers, and the edge arc.

    Args:
        spec: Face being built.

    Returns:
        The ``Group`` element holding the decoration.
    """
    children: list[ElementTree.Element] = [_ring_part(spec)]
    if spec.show_ticks:
        children.extend(_tick_parts(spec))
    arc = _progress_arc(spec)
    if arc is not None:
        children.append(arc)
    group = _element_list("Group", children)
    edge = spec.design_edge
    for key, value in (
        ("height", edge),
        ("name", "dialLayer"),
        ("width", edge),
        ("x", 0),
        ("y", 0),
    ):
        group.set(key, str(value))
    group.append(_ambient("alpha", AMBIENT_ALPHA_DIM if spec.ambient_minimal else AMBIENT_ALPHA_FULL))
    return group


def _readout_group(spec: WatchFaceSpec) -> ElementTree.Element | None:
    """The time and date layer, drawn above the dial.

    Args:
        spec: Face being built.

    Returns:
        The ``Group`` element, or None when the face shows no text.
    """
    children: list[ElementTree.Element] = []
    clock = _digital_clock(spec)
    if clock is not None:
        children.append(clock)
    date = _date_part(spec)
    if date is not None:
        children.append(date)
    if not children:
        return None
    group = _element_list("Group", children)
    edge = spec.design_edge
    for key, value in (
        ("height", edge),
        ("name", "readoutLayer"),
        ("width", edge),
        ("x", 0),
        ("y", 0),
    ):
        group.set(key, str(value))
    group.append(_ambient("alpha", AMBIENT_ALPHA_FULL))
    return group


def _scene(spec: WatchFaceSpec) -> ElementTree.Element:
    """The single ``Scene``: decoration, read-out, hands, then complications.

    Draw order is deliberate: hands and complications come last so the ambient
    memory model can drop the layers underneath them.

    Args:
        spec: Face being built.

    Returns:
        The ``Scene`` element.
    """
    children: list[ElementTree.Element] = [_dial_group(spec)]
    readout = _readout_group(spec)
    if readout is not None:
        children.append(readout)
    clock = _analog_clock(spec)
    if clock is not None:
        children.append(clock)
    for slot in spec.complications:
        children.append(_complication_slot(spec, slot))
    scene = _element_list("Scene", children)
    scene.set("backgroundColor", _scene_background(spec))
    return scene


def _scene_background(spec: WatchFaceSpec) -> str:
    """Opaque scene background, black per WO-V13.

    Args:
        spec: Face being built.

    Returns:
        Eight-digit ARGB hex.
    """
    return rgba_to_hex(hex_to_rgba(spec.background), include_alpha=True)


def numeral_part(spec: WatchFaceSpec, numeral: str) -> ElementTree.Element:
    """A literal hour numeral, for faces that want numerals over markers.

    Args:
        spec: Face being built.
        numeral: The digits to draw, such as ``12``.

    Returns:
        The ``PartText`` element holding literal text.
    """
    edge = spec.design_edge
    size = spec.typography.label_size * 2
    side = size * 2
    offsets: Mapping[str, tuple[int, int]] = {
        "12": (edge // 2 - side // 2, int(edge * 0.10)),
        "3": (int(edge * 0.80), edge // 2 - side // 2),
        "6": (edge // 2 - side // 2, int(edge * 0.78)),
        "9": (int(edge * 0.10), edge // 2 - side // 2),
    }
    x, y = offsets[numeral]
    return _text_part(
        spec,
        f"numeral{numeral}",
        LayoutBox(f"numeral{numeral}", x, y, side, side),
        numeral,
        (),
        size,
        theme_color(spec, -1),
        tint=_theme_reference(spec, 1),
    )


def build_watch_face(
    spec: WatchFaceSpec,
    *,
    wff_version: int = DEFAULT_WFF_VERSION,
    include_numerals: bool = False,
) -> ElementTree.Element:
    """Build the ``<WatchFace>`` tree for one face.

    Args:
        spec: Face to emit.
        wff_version: Format version the document targets.
        include_numerals: Add literal 12, 3, 6, and 9 numerals to the dial.

    Returns:
        The root element.

    Raises:
        ValueError: the format version is not one Google publishes.
    """
    if wff_version not in WFF_VERSIONS:
        raise ValueError(f"wff_version must be one of {WFF_VERSIONS}, got {wff_version}")
    edge = spec.design_edge
    root_attributes: dict[str, AttrValue] = {
        "clipShape": _clip_shape(spec),
        "height": edge,
        "width": edge,
        f"{{{XSI_NAMESPACE}}}noNamespaceSchemaLocation": schema_location(wff_version),
    }
    root = _el("WatchFace", **root_attributes)
    if spec.shape != "round":
        root.set("cornerRadiusX", _attr_text(edge * 0.16))
        root.set("cornerRadiusY", _attr_text(edge * 0.16))
    for item in _metadata(spec):
        root.append(item)
    configurations = _user_configurations(spec)
    if configurations is not None:
        root.append(configurations)
    scene = _scene(spec)
    if include_numerals:
        dial = scene[0]
        for numeral in ("12", "3", "6", "9"):
            dial.append(numeral_part(spec, numeral))
    root.append(scene)
    return root


def _clip_shape(spec: WatchFaceSpec) -> str:
    """``clipShape`` for a face shape.

    Args:
        spec: Face being built.

    Returns:
        ``CIRCLE`` or ``RECTANGLE``.
    """
    return "CIRCLE" if spec.shape == "round" else "RECTANGLE"


def schema_location(wff_version: int) -> str:
    """Advisory schema location written onto the root element.

    Args:
        wff_version: Format version the document targets.

    Returns:
        A URL inside the official XSD folder.
    """
    return f"{SCHEMA_ROOT_URL}/{wff_version}/watchface.xsd"


def serialize(root: ElementTree.Element) -> str:
    """Render a tree the way the Android resource compiler expects it.

    Args:
        root: Element to write.

    Returns:
        An XML declaration plus an indented document, newline-terminated.
    """
    ElementTree.indent(root, space="  ")
    body = ElementTree.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="utf-8"?>\n{body}\n'


def watch_face_xml(
    spec: WatchFaceSpec,
    *,
    wff_version: int = DEFAULT_WFF_VERSION,
    include_numerals: bool = False,
) -> str:
    """Render ``res/raw/watchface.xml`` for one face.

    Args:
        spec: Face to emit.
        wff_version: Format version the document targets.
        include_numerals: Add literal hour numerals to the dial.

    Returns:
        The complete document text.
    """
    return serialize(
        build_watch_face(spec, wff_version=wff_version, include_numerals=include_numerals)
    )


# The published element vocabulary. Anything outside it is a generator bug or a
# hand edit, and ez_watch.validate reports it rather than shipping it.
ELEMENT_VOCABULARY: frozenset[str] = frozenset(
    {
        "AnalogClock",
        "AvailableInRetail",
        "Arc",
        "BitmapFonts",
        "Bitmap",
        "BooleanConfiguration",
        "BoundingBox",
        "BoundingOval",
        "BoundingRoundBox",
        "BoundingRect",
        "BoundingArc",
        "Category",
        "ColorConfiguration",
        "ColorOption",
        "Complication",
        "ComplicationSlot",
        "Condition",
        "DefaultProviderPolicy",
        "DigitalClock",
        "Editable",
        "Ellipse",
        "Fill",
        "Flavor",
        "FlavorsSupported",
        "Font",
        "Frame",
        "Group",
        "Gyro",
        "HourHand",
        "Image",
        "Launch",
        "Line",
        "LinearGradient",
        "ListConfiguration",
        "ListOption",
        "Localization",
        "Metadata",
        "MinuteHand",
        "MultipleInstancesAllowed",
        "Outline",
        "Parameter",
        "PartAnimatedImage",
        "PartDraw",
        "PartImage",
        "PartText",
        "PhotosConfiguration",
        "Preview",
        "Rectangle",
        "Reference",
        "RoundRectangle",
        "Scene",
        "ScreenReader",
        "SecondHand",
        "Stroke",
        "Template",
        "Text",
        "TextCircular",
        "TimeText",
        "Transform",
        "Upper",
        "UserConfigurations",
        "Variant",
        "WatchFace",
        "WatchFaceInfo",
        "WatchFaces",
        "WeightedStroke",
    }
)
"""Every WFF element name this pack may emit, from the reference pages."""

REQUIRED_ELEMENT_ATTRIBUTES: Mapping[str, tuple[str, ...]] = {
    "AnalogClock": ("x", "y", "width", "height"),
    "Arc": ("centerX", "centerY", "width", "height", "startAngle", "endAngle"),
    "ColorConfiguration": ("id", "displayName", "defaultValue"),
    "ColorOption": ("id", "displayName", "colors"),
    "Complication": ("type",),
    "ComplicationSlot": ("x", "y", "width", "height", "slotId", "supportedTypes"),
    "DigitalClock": ("x", "y", "width", "height"),
    "Ellipse": ("x", "y", "width", "height"),
    "Group": ("name", "x", "y", "width", "height"),
    "HourHand": ("resource", "x", "y", "width", "height"),
    "Line": ("startX", "startY", "endX", "endY"),
    "MinuteHand": ("resource", "x", "y", "width", "height"),
    "PartDraw": ("x", "y", "width", "height"),
    "PartImage": ("x", "y", "width", "height"),
    "PartText": ("x", "y", "width", "height"),
    "Preview": ("value",),
    "SecondHand": ("resource", "x", "y", "width", "height"),
    "Stroke": ("color", "thickness"),
    "TimeText": ("format", "x", "y", "width", "height"),
    "Variant": ("mode", "target", "value"),
    "WatchFace": ("width", "height"),
}
"""Attributes the reference pages mark required, per element."""

VARIANT_MODES: frozenset[str] = frozenset({AMBIENT_MODE})
"""``Variant mode`` values Google documents."""

COMPLICATION_TYPE_SET: frozenset[str] = frozenset(COMPLICATION_TYPES)
"""``ComplicationSlot supportedTypes`` values, shared with the validator."""
