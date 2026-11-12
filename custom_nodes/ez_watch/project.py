"""Emit a complete, submittable Watch Face Format source project.

One call writes everything Play and the platform renderer ask for: the
``AndroidManifest.xml`` shell with ``hasCode="false"``, ``res/raw/watchface.xml``,
``res/xml/watch_face_info.xml``, the string resources, generated preview and
hand drawables, and the store-listing package. The emitted tree carries no
Wear OS application logic, because a bundle that mixes the two is rejected.

Artwork is rastered through :mod:`ez_raster` and every write is deterministic:
same spec in, byte-identical files out.

Hermetic at import: stdlib plus ``ez_raster`` and ``ez_common.json_value``.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ez_common.json_value import Json, JsonObject
from ez_raster import (
    PLAY_FEATURE_GRAPHIC_HEIGHT,
    PLAY_FEATURE_GRAPHIC_WIDTH,
    PLAY_LAUNCHER_ICON_PX,
    BLACK,
    Canvas,
    Rgba,
    WHITE,
    encode_rgb_png,
    hex_to_rgba,
)

from ez_watch.catalog import (
    STYLE_ANALOG,
    STYLES,
    WATCH_FACE_CATALOG,
    ComplicationSlotSpec,
    WatchFaceSpec,
    load_catalog,
)
from ez_watch.scene import (
    DEFAULT_PREVIEW_TIME,
    DEFAULT_WFF_VERSION,
    WFF_VERSION_API,
    LayoutBox,
    box_of,
    string_resources,
    watch_face_xml,
)
from ez_watch.validate import (
    Finding,
    ILLUMINATED_LIMIT,
    MemoryEstimate,
    memory_estimate,
    validate_project,
)

DEFAULT_TOOL_VERSION = "1.0.0"
"""Publisher property value when the operator does not name a tool version."""

DEFAULT_PREVIEW_EDGE = 450
"""Square edge for preview and screenshot assets; Play wants at least 384."""

MIN_PREVIEW_EDGE = 384
"""Smallest 1:1 watch face screenshot Play accepts."""

STORE_ASSET_DIR = "store-assets"
"""Folder the Play listing artwork is written into."""

_APPLICATION_ID_PREFIX = "com.ezcomfy.watchface"
"""Application id prefix; each face gets its own suffix so ids never collide."""

_SHAPE_FILE_VARIANTS: tuple[tuple[str, int], ...] = (("CIRCLE", 300), ("CIRCLE", 450))
"""Round small and large layouts written when an operator asks for variants."""

_HAND_SHAPES: Mapping[str, tuple[float, float]] = {
    "hour": (0.26, 0.020),
    "minute": (0.38, 0.014),
    "second": (0.44, 0.006),
}
"""Length and width fractions of each hand drawable, pointing at 12 o'clock."""

_SEGMENT_MAP: Mapping[str, frozenset[str]] = {
    "0": frozenset("abcdef"),
    "1": frozenset("bc"),
    "2": frozenset("abged"),
    "3": frozenset("abgcd"),
    "4": frozenset("fgbc"),
    "5": frozenset("afgcd"),
    "6": frozenset("afgedc"),
    "7": frozenset("abc"),
    "8": frozenset("abcdefg"),
    "9": frozenset("abcdfg"),
}
"""Which of the seven bars light for each digit of the numeric read-out."""

# The 10:09:30 marketing pose the hands and the digits agree on, so a painted
# preview and the XML preview show the same instant.
_PREVIEW_HOUR = 10
"""Hour of the pose; the hour hand sits just past the 10 as marketing shots do."""

_PREVIEW_MINUTE = 9
"""Minute of the pose; the minute hand lands on the 9 and clears the logo."""

_PREVIEW_SECOND = 30
"""Second of the pose, so a sweep hand reads as a detail rather than noise."""

_STYLE_WORDS: Mapping[str, str] = {
    "analog": "Analog",
    "digital": "Digital",
    "hybrid": "Hybrid",
    "complication-forward": "Complication",
}
"""Store-facing word per style, used in the short description."""

_VOWEL_LETTERS = "aeiou"
"""Letters that make the indefinite article before a word read as ``an``."""


def _article(word: str) -> str:
    """Return the indefinite article that reads correctly before ``word``.

    Store copy names the style right after the article, and three of the four
    styles start with a consonant while ``analog`` does not, so the article has
    to follow the word rather than sit in the template.

    Args:
        word: Word the article precedes; an empty word takes the consonant
            branch, since ``"" in "aeiou"`` is true for an empty prefix.

    Returns:
        ``an`` or ``a``.
    """
    first = word[:1].lower()
    return "an" if first and first in _VOWEL_LETTERS else "a"


@dataclass(frozen=True)
class ProjectResult:
    """What one build produced, and what the compliance gate said about it.

    Attributes:
        slug: Face slug.
        package: Application id written into the build file.
        out_dir: Directory the project was written to, or the intended one.
        files: Project-relative file paths, sorted.
        themes: Colourway names in ``ColorOption`` order.
        slot_ids: Declared ``slotId`` values.
        memory: Estimated ambient and interactive footprint.
        illuminated_ratio: Measured illuminated fraction of the default preview.
        findings: Compliance findings, empty when the face is submittable.
        dry_run: True when nothing was written.
    """

    slug: str
    package: str
    out_dir: str
    files: tuple[str, ...]
    themes: tuple[str, ...]
    slot_ids: tuple[int, ...]
    memory: MemoryEstimate
    illuminated_ratio: float
    findings: tuple[Finding, ...]
    dry_run: bool

    @property
    def clean(self) -> bool:
        """True when the gate raised no error-severity finding.

        Returns:
            Whether the emitted project is ready to package.
        """
        return not any(finding.severity == "error" for finding in self.findings)


class _Painter:
    """Opaque pixel writer over an :class:`~ez_raster.Canvas` buffer.

    Only opaque colours are written, which is what the Play screenshot rule
    needs: a watch face screenshot may not carry transparency.

    Args:
        canvas: Canvas to draw into.
        offset_x: Columns to add to every x coordinate.
    """

    def __init__(self, canvas: Canvas, offset_x: int = 0) -> None:
        """Bind the painter to a live pixel buffer."""
        self.canvas = canvas
        self.offset_x = offset_x
        self._pixels = canvas.pixels
        self._width = canvas.width
        self._height = canvas.height

    def point(self, x: int, y: int, quad: bytes) -> None:
        """Write one pixel.

        Args:
            x: Column before the shift.
            y: Row.
            quad: Four bytes of RGBA.
        """
        column = x + self.offset_x
        if 0 <= column < self._width and 0 <= y < self._height:
            offset = (y * self._width + column) * 4
            self._pixels[offset : offset + 4] = quad

    def box(self, x: int, y: int, width: int, height: int, color: Rgba) -> None:
        """Paint an axis-aligned block.

        Args:
            x: Left column before the shift.
            y: Top row.
            width: Block width.
            height: Block height.
            color: Opaque colour.
        """
        self.canvas.fill_rect(x + self.offset_x, y, width, height, color)

    def segment(
        self, x0: float, y0: float, x1: float, y1: float, color: Rgba, thickness: int
    ) -> None:
        """Draw a thick straight run between two points.

        Args:
            x0: Start column before the shift.
            y0: Start row.
            x1: End column before the shift.
            y1: End row.
            color: Opaque colour.
            thickness: Stroke width in pixels.
        """
        self.canvas.draw_line(
            round(x0) + self.offset_x,
            round(y0),
            round(x1) + self.offset_x,
            round(y1),
            color,
            max(1, thickness),
        )

    def ring(
        self,
        centre: float,
        radius: float,
        thickness: float,
        color: Rgba,
        start: float = 0.0,
        end: float = 360.0,
    ) -> None:
        """Draw a ring or an arc around the face centre.

        Angles follow the Watch Face Format: 0 degrees is 12 o'clock and they
        increase clockwise.

        Args:
            centre: Face centre, used for both axes before the shift.
            radius: Ring radius in pixels.
            thickness: Ring width in pixels.
            color: Opaque colour.
            start: Start angle in degrees.
            end: End angle in degrees.
        """
        outer = radius + thickness / 2.0
        inner = max(0.0, radius - thickness / 2.0)
        if outer <= 0.0:
            return
        centre_x = centre + self.offset_x
        full = end - start >= 360.0
        quad = bytes(color.as_tuple())
        left = max(0, int(centre_x - outer) - 1)
        right = min(self._width - 1, int(centre_x + outer) + 1)
        top = max(0, int(centre - outer) - 1)
        bottom = min(self._height - 1, int(centre + outer) + 1)
        for row in range(top, bottom + 1):
            dy = row + 0.5 - centre
            for column in range(left, right + 1):
                dx = column + 0.5 - centre_x
                distance = dx * dx + dy * dy
                if distance < inner * inner or distance > outer * outer:
                    continue
                if not full and not self._in_sweep(dx, dy, start, end):
                    continue
                offset = (row * self._width + column) * 4
                self._pixels[offset : offset + 4] = quad

    @staticmethod
    def _in_sweep(dx: float, dy: float, start: float, end: float) -> bool:
        """True when a pixel angle sits inside an arc sweep.

        Args:
            dx: Horizontal distance from the ring centre.
            dy: Vertical distance from the ring centre.
            start: Start angle in degrees.
            end: End angle in degrees.

        Returns:
            Whether the angle is inside the sweep, which may wrap 0 degrees.
        """
        angle = math.degrees(math.atan2(dx, -dy)) % 360.0
        if start <= end:
            return start <= angle <= end
        return angle >= start or angle <= end

    def disc(self, centre: float, radius: float, color: Rgba) -> None:
        """Paint a hard-edged disc so no antialiased alpha leaks in.

        Args:
            centre: Face centre, used for both axes before the shift.
            radius: Disc radius in pixels.
            color: Opaque colour.
        """
        quad = bytes(color.as_tuple())
        centre_x = centre + self.offset_x
        reach = int(radius) + 1
        left = max(0, int(centre_x) - reach)
        right = min(self._width - 1, int(centre_x) + reach)
        top = max(0, int(centre) - reach)
        bottom = min(self._height - 1, int(centre) + reach)
        stop = radius * radius
        for row in range(top, bottom + 1):
            dy = row + 0.5 - centre
            for column in range(left, right + 1):
                dx = column + 0.5 - centre_x
                if dx * dx + dy * dy <= stop:
                    offset = (row * self._width + column) * 4
                    self._pixels[offset : offset + 4] = quad

    def digits(self, item: LayoutBox, text: str, color: Rgba) -> None:
        """Render a numeric read-out with seven-segment digits.

        Args:
            item: Box the read-out occupies.
            text: Digits and colons, such as ``10:09``.
            color: Opaque glyph colour.
        """
        count = sum(1 for character in text if character != ":")
        if count == 0:
            return
        gap = max(2, item.width // (count * 10))
        width = (item.width - gap * (count - 1)) // count
        stroke = max(2, width // 7)
        quad = bytes(color.as_tuple())
        column = item.x
        for character in text:
            if character == ":":
                self.box(column, item.y + item.height // 3, stroke, stroke, color)
                self.box(column, item.y + 2 * item.height // 3, stroke, stroke, color)
                column += stroke + gap
                continue
            self._digit(column, item.y, width, item.height, stroke, character, quad)
            column += width + gap

    def _digit(
        self, x: int, y: int, width: int, height: int, stroke: int, glyph: str, quad: bytes
    ) -> None:
        """Light the segments one digit needs.

        Args:
            x: Left column before the shift.
            y: Top row.
            width: Digit box width.
            height: Digit box height.
            stroke: Segment thickness.
            glyph: Character to draw; anything unmapped draws nothing.
            quad: Four bytes of RGBA.
        """
        lit = _SEGMENT_MAP.get(glyph)
        if lit is None:
            return
        half = (height - stroke) // 2
        arm = half - 2 * stroke
        if "a" in lit:
            self._bar(x + stroke, y, width - 2 * stroke, stroke, quad)
        if "g" in lit:
            self._bar(x + stroke, y + half, width - 2 * stroke, stroke, quad)
        if "d" in lit:
            self._bar(x + stroke, y + height - stroke, width - 2 * stroke, stroke, quad)
        if "f" in lit:
            self._bar(x, y + stroke, stroke, arm, quad)
        if "b" in lit:
            self._bar(x + width - stroke, y + stroke, stroke, arm, quad)
        if "e" in lit:
            self._bar(x, y + half + stroke, stroke, arm, quad)
        if "c" in lit:
            self._bar(x + width - stroke, y + half + stroke, stroke, arm, quad)

    def _bar(self, x: int, y: int, width: int, height: int, quad: bytes) -> None:
        """Write one segment bar pixel by pixel.

        Args:
            x: Left column before the shift.
            y: Top row.
            width: Bar width.
            height: Bar height.
            quad: Four bytes of RGBA.
        """
        for row in range(y, y + height):
            for column in range(x, x + width):
                self.point(column, row, quad)


def _theme_colors(spec: WatchFaceSpec, theme: int) -> tuple[Rgba, Rgba, Rgba]:
    """Resolve the three drawing colours of one colourway.

    Args:
        spec: Face being drawn.
        theme: Colourway index.

    Returns:
        ``(accent, secondary, text)`` as opaque colours.
    """
    colors = spec.palette[theme % len(spec.palette)].colors
    accent = hex_to_rgba(colors[0]).blended_over(BLACK)
    secondary = hex_to_rgba(colors[min(1, len(colors) - 1)]).blended_over(BLACK)
    text = hex_to_rgba(colors[-1]).blended_over(BLACK)
    return accent, secondary, text


def _paint_face(painter: _Painter, spec: WatchFaceSpec, theme: int, *, bleed: float = 1.0) -> None:
    """Draw one face into an opaque canvas.

    Args:
        painter: Painter bound to a square canvas whose side is the spec edge.
        spec: Face to draw.
        theme: Colourway index.
        bleed: Ring radius multiplier; above 1 makes the dial touch the icon
            edges, which WO-G4 wants.
    """
    edge = spec.design_edge
    accent, secondary, text = _theme_colors(spec, theme)
    centre = edge / 2.0
    if spec.show_ticks:
        inner = edge * (0.40 if spec.style == STYLE_ANALOG else 0.425)
        outer = edge * 0.455
        thickness = max(1, int(edge * 0.008))
        for hour in range(12):
            angle = math.radians(hour * 30.0)
            painter.segment(
                centre + inner * math.sin(angle),
                centre - inner * math.cos(angle),
                centre + outer * math.sin(angle),
                centre - outer * math.cos(angle),
                secondary,
                thickness,
            )
    if any("RANGED_VALUE" in slot.supported_types for slot in spec.complications):
        painter.ring(centre, edge * 0.47, max(1.0, edge * 0.004), secondary)
    painter.ring(centre, edge * 0.455 * bleed, max(2.0, edge * 0.008), accent)
    if spec.show_date:
        _paint_date(painter, spec, text)
    if spec.style != STYLE_ANALOG:
        painter.digits(box_of(spec, "time"), _preview_digits(), accent)
    if spec.show_hands:
        _paint_hands(painter, spec, accent, secondary)
    for slot in spec.complications:
        _paint_slot(painter, slot, accent, secondary, text)


def _preview_digits() -> str:
    """Return the read-out the preview pose shows.

    Returns:
        ``HH:MM`` for the marketing pose.
    """
    return f"{_PREVIEW_HOUR:02d}:{_PREVIEW_MINUTE:02d}"


def _paint_date(painter: _Painter, spec: WatchFaceSpec, color: Rgba) -> None:
    """Draw the date line as two short bars.

    Args:
        painter: Painter for this face.
        spec: Face being drawn.
        color: Opaque text colour.
    """
    item = box_of(spec, "date")
    height = max(2, item.height // 4)
    bar = max(2, item.width // 2 - 2)
    row = item.y + item.height // 2 - height // 2
    painter.box(item.x, row, bar, height, color)
    painter.box(item.x + item.width // 2 + 2, row, bar, height, color)


def _paint_hands(painter: _Painter, spec: WatchFaceSpec, accent: Rgba, secondary: Rgba) -> None:
    """Draw the hour, minute, and second hands at the preview pose.

    Args:
        painter: Painter for this face.
        spec: Face being drawn.
        accent: Colour for the hour and minute hands.
        secondary: Colour for the second hand.
    """
    edge = spec.design_edge
    centre = edge / 2.0
    pose = (
        ((_PREVIEW_HOUR % 12) + _PREVIEW_MINUTE / 60.0) * 30.0,
        _PREVIEW_MINUTE * 6.0,
        _PREVIEW_SECOND * 6.0,
    )
    angles = (pose[0], pose[1], pose[2])
    lengths = (0.26, 0.38, 0.44)
    thicknesses = (max(4, edge // 60), max(3, edge // 80), max(1, edge // 180))
    colors = (accent, accent, secondary)
    for angle, length, thickness, color in zip(angles, lengths, thicknesses, colors, strict=True):
        radians = math.radians(angle)
        painter.segment(
            centre - length * edge * math.sin(radians) * 0.18,
            centre + length * edge * math.cos(radians) * 0.18,
            centre + length * edge * math.sin(radians),
            centre - length * edge * math.cos(radians),
            color,
            thickness,
        )
    painter.disc(centre, max(3.0, edge * 0.014), accent)


def _paint_slot(
    painter: _Painter, slot: ComplicationSlotSpec, accent: Rgba, secondary: Rgba, text: Rgba
) -> None:
    """Draw the placeholder artwork one complication slot shows.

    Args:
        painter: Painter for this face.
        slot: Slot being drawn.
        accent: Colour for the ranged arc.
        secondary: Colour for image placeholders.
        text: Colour for label bars.
    """
    for kind in slot.supported_types:
        if kind in {"SHORT_TEXT", "LONG_TEXT"}:
            height = max(2, slot.height // 6)
            painter.box(
                slot.x + 4, slot.y + slot.height // 2 - height // 2, slot.width - 8, height, text
            )
            return
        if kind in {"MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "PHOTO_IMAGE"}:
            painter.disc(slot.x + slot.width / 2.0, min(slot.width, slot.height) * 0.30, secondary)
            return
        if kind == "RANGED_VALUE":
            painter.ring(
                slot.x + slot.height / 2.0,
                min(slot.width, slot.height) * 0.32,
                max(1.0, slot.height * 0.08),
                accent,
                200.0,
                340.0,
            )
            return


def _scaled_for_edge(spec: WatchFaceSpec, edge: int) -> WatchFaceSpec:
    """Return a copy of a face whose design edge is ``edge``.

    Args:
        spec: Face to rescale.
        edge: New square edge.

    Returns:
        A spec whose slots are scaled to the new edge.
    """
    scale = edge / spec.design_edge
    return WatchFaceSpec(
        slug=spec.slug,
        name=spec.name,
        style=spec.style,
        shape=spec.shape,
        palette=spec.palette,
        complications=tuple(
            ComplicationSlotSpec(
                slot_id=slot.slot_id,
                x=round(slot.x * scale),
                y=round(slot.y * scale),
                width=max(1, round(slot.width * scale)),
                height=max(1, round(slot.height * scale)),
                supported_types=slot.supported_types,
            )
            for slot in spec.complications
        ),
        typography=spec.typography,
        show_ticks=spec.show_ticks,
        show_hands=spec.show_hands,
        show_date=spec.show_date,
        show_battery=spec.show_battery,
        show_step_complication=spec.show_step_complication,
        tags=spec.tags,
        category=spec.category,
        ambient_minimal=spec.ambient_minimal,
        design_edge=edge,
        background=spec.background,
    )


def _face_canvas(spec: WatchFaceSpec, theme: int, edge: int, *, bleed: float = 1.0) -> Canvas:
    """Raster one face at an arbitrary square edge.

    Args:
        spec: Face to draw.
        theme: Colourway index.
        edge: Square edge in pixels.
        bleed: Ring radius multiplier for icon artwork.

    Returns:
        Opaque canvas holding the artwork.
    """
    scaled = _scaled_for_edge(spec, edge)
    canvas = Canvas(edge, edge, fill=hex_to_rgba(spec.background).blended_over(BLACK))
    _paint_face(_Painter(canvas), scaled, theme, bleed=bleed)
    return canvas


def hand_canvas(kind: str, edge: int) -> Canvas:
    """Raster one analog hand drawable, pointing at 12 o'clock.

    The renderer rotates the drawable about its pivot, so the artwork only has
    to show the hand pointing up from the centre. It is written white so the
    ``tintColor`` expression can recolour it per colourway.

    Args:
        kind: One of ``hour``, ``minute``, ``second``.
        edge: Square edge in pixels.

    Returns:
        Canvas carrying the hand on a transparent ground.

    Raises:
        ValueError: the kind is not one of the three hands.
    """
    if kind not in _HAND_SHAPES:
        raise ValueError(f"unknown hand {kind!r}, expected one of {sorted(_HAND_SHAPES)}")
    length, width = _HAND_SHAPES[kind]
    canvas = Canvas(edge, edge)
    painter = _Painter(canvas)
    centre = edge / 2.0
    painter.segment(
        centre,
        centre + edge * length * 0.18,
        centre,
        centre - edge * length,
        WHITE,
        max(2, int(edge * width)),
    )
    painter.disc(centre, max(2.0, edge * 0.012), WHITE)
    return canvas


def _tag(name: str, attrs: Mapping[str, str]) -> str:
    """Render a self-closing tag with sorted attributes.

    Args:
        name: Element name.
        attrs: Attributes.

    Returns:
        Something like ``<Preview value="@drawable/preview" />``.
    """
    head = " ".join(f'{key}="{attrs[key]}"' for key in sorted(attrs))
    return f"<{name} {head} />" if attrs else f"<{name} />"


def _open(name: str, attrs: Mapping[str, str]) -> str:
    """Render an opening tag with sorted attributes.

    Args:
        name: Element name.
        attrs: Attributes.

    Returns:
        Something like ``<application ...>``.
    """
    head = " ".join(f'{key}="{attrs[key]}"' for key in sorted(attrs))
    return f"<{name} {head}>" if attrs else f"<{name}>"


def _nest(name: str, attrs: Mapping[str, str], children: Sequence[str]) -> tuple[str, ...]:
    """Render one element with its children as indented lines.

    Args:
        name: Element name.
        attrs: Attributes.
        children: Already-rendered child lines.

    Returns:
        Lines for the element, indented one level in total.
    """
    lines = [_open(name, attrs)]
    lines.extend(f"  {child}" for child in children)
    lines.append(f"</{name}>")
    return tuple(lines)


def _document(root: str, attrs: Mapping[str, str], children: Sequence[str]) -> str:
    """Render a small hand-written XML document deterministically.

    Args:
        root: Root element name.
        attrs: Root attributes.
        children: Rendered child lines.

    Returns:
        Declaration plus indented body, newline-terminated.
    """
    lines = ['<?xml version="1.0" encoding="utf-8"?>', _open(root, attrs)]
    lines.extend(f"  {child}" for child in children)
    lines.append(f"</{root}>")
    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    """Escape a string resource body.

    Args:
        value: Plain English label.

    Returns:
        Text safe inside an Android string resource.
    """
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _manifest_xml(wff_version: int, tool_version: str) -> str:
    """``AndroidManifest.xml`` for a code-free face package.

    Args:
        wff_version: Format version declared to the platform.
        tool_version: Publisher property value.

    Returns:
        The manifest text.
    """
    application = _nest(
        "application",
        {"android:hasCode": "false", "android:label": "@string/watch_face_name"},
        [
            _tag(
                "meta-data",
                {
                    "android:name": "com.google.android.wearable.standalone",
                    "android:value": "true",
                },
            ),
            _tag(
                "property",
                {
                    "android:name": "com.google.wear.watchface.format.version",
                    "android:value": str(wff_version),
                },
            ),
            _tag(
                "property",
                {
                    "android:name": "com.google.wear.watchface.format.publisher",
                    "android:value": f"ez-comfy-stack-{tool_version}",
                },
            ),
        ],
    )
    return _document(
        "manifest",
        {"xmlns:android": "http://schemas.android.com/apk/res/android"},
        [_tag("uses-feature", {"android:name": "android.hardware.type.watch"}), *application],
    )


def _watch_face_info_xml(spec: WatchFaceSpec, *, flavors: bool) -> str:
    """``res/xml/watch_face_info.xml`` for one face.

    Args:
        spec: Face being packaged.
        flavors: Whether to declare flavour support, a version 2 feature.

    Returns:
        The document text.
    """
    children = [
        _tag("Preview", {"value": "@drawable/preview"}),
        _tag("Category", {"value": spec.category}),
        _tag("AvailableInRetail", {"value": "true"}),
        _tag("MultipleInstancesAllowed", {"value": "true"}),
        _tag("Editable", {"value": "true" if spec.configurable else "false"}),
    ]
    if flavors:
        children.append(_tag("FlavorsSupported", {"value": "true"}))
    return _document("WatchFaceInfo", {}, children)


def _watch_face_shapes_xml() -> str:
    """``res/xml/watch_face_shapes.xml`` with the small and large round pair.

    Returns:
        The document text.
    """
    children = [
        _tag(
            "WatchFace",
            {"file": "@raw/watchface", "height": str(size), "shape": shape, "width": str(size)},
        )
        for shape, size in _SHAPE_FILE_VARIANTS
    ]
    return _document("WatchFaces", {}, children)


def _strings_xml(spec: WatchFaceSpec) -> str:
    """``res/values/strings.xml`` holding every label the XML references.

    Args:
        spec: Face being packaged.

    Returns:
        The document text.
    """
    children = [
        f"{_open('string', {'name': name})}{_escape(value)}</string>"
        for name, value in string_resources(spec)
    ]
    return _document("resources", {}, children)


def _build_gradle(package: str, wff_version: int) -> str:
    """``build.gradle`` for the face-only module.

    Args:
        package: Application id.
        wff_version: Format version, which fixes the minimum API.

    Returns:
        Gradle text that builds a resource-only bundle.
    """
    api = WFF_VERSION_API[wff_version]
    return "\n".join(
        [
            "plugins {",
            '    id "com.android.application"',
            "}",
            "",
            "android {",
            f'    namespace "{package}"',
            "    compileSdk 36",
            "",
            "    defaultConfig {",
            f'        applicationId "{package}"',
            f"        minSdk {api}",
            f"        targetSdk {api}",
            "        versionCode 1",
            '        versionName "1.0"',
            "    }",
            "",
            "    buildTypes {",
            "        release {",
            "            minifyEnabled false",
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def _settings_gradle() -> str:
    """``settings.gradle`` for the single face module.

    Returns:
        Gradle text.
    """
    return 'rootProject.name = "watchface"\n'


def _clip(text: str, limit: int) -> str:
    """Shorten text to a Play field limit on a word edge.

    Args:
        text: Candidate text.
        limit: Character budget.

    Returns:
        Text no longer than the limit, cut at the last space when there is one.
    """
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut if cut else text[:limit]


def _full_description(spec: WatchFaceSpec) -> str:
    """Full store description, kept inside the 4000 character budget.

    Args:
        spec: Face being described.

    Returns:
        The listing body.
    """
    themes = ", ".join(theme.name for theme in spec.palette)
    style_word = spec.style.replace("-", " ")
    return "\n".join(
        [
            f"{spec.name} is {_article(style_word)} {style_word} Wear OS watch face"
            " built with the",
            "Watch Face Format, so it ships as resources only and carries no code.",
            "",
            f"* {len(spec.palette)} colorways to match your strap: {themes}.",
            f"* {len(spec.complications)} complication slots for steps, battery, weather, and more.",
            "* Black background and a legible time read-out for the always-on display.",
            "* Layout authored for the 192 dp and 227 dp round Wear OS devices.",
            "* Personalize it in the Wear OS watch face editor: colorway, markers, date, battery.",
            "",
            "This face is designed for Wear OS and is delivered as a Wear OS app package.",
            "Complications are supported, so you can put your own data on the dial.",
            "Nothing is collected, so the face works the same with no account and no network.",
        ]
    )


def _listing(spec: WatchFaceSpec) -> JsonObject:
    """Play listing fields for one face.

    Args:
        spec: Face being packaged.

    Returns:
        A JSON object ready for ``manifest.json`` and the listing page.
    """
    title = _clip(f"{spec.name} for Wear OS", 30)
    short = _clip(
        f"{_STYLE_WORDS[spec.style]} Wear OS watch face: {len(spec.palette)} colorways, "
        f"{len(spec.complications)} complication slots.",
        80,
    )
    return {
        "title": title,
        "short_description": short,
        "full_description": _full_description(spec),
        "category": spec.category,
        "self_tag": spec.category,
        "tags": list(spec.tags),
        "wear_os_wording": "Wear OS",
        "ads": "This app does not display advertisements.",
        "data_safety": (
            "Data not collected. A Watch Face Format face contains no code, so "
            "nothing runs, nothing is stored, and nothing is shared."
        ),
        "language": "en-US",
    }


def _listing_markdown(spec: WatchFaceSpec, listing: JsonObject) -> str:
    """``store-listing.md`` the operator pastes into Play Console.

    Args:
        spec: Face being described.
        listing: Listing fields from :func:`_listing`.

    Returns:
        Markdown text.
    """
    raw_tags: Json = listing.get("tags", [])
    tags = ", ".join(str(tag) for tag in raw_tags) if isinstance(raw_tags, list) else ""
    return "\n".join(
        [
            f"# {spec.name} - Play store listing",
            "",
            f"- Title ({len(str(listing['title']))}/30): {listing['title']}",
            f"- Short description ({len(str(listing['short_description']))}/80): "
            f"{listing['short_description']}",
            f"- Category and self-tag: {listing['self_tag']}",
            f"- Tags: {tags}",
            f"- Form factor wording: {listing['wear_os_wording']}",
            f"- Ads: {listing['ads']}",
            f"- Data safety: {listing['data_safety']}",
            f"- Language: {listing['language']}",
            "",
            "## Full description",
            "",
            str(listing["full_description"]),
            "",
            "## Assets in this package",
            "",
            f"- ``{STORE_ASSET_DIR}/icon.png`` - 512x512, opaque, circular face touching the edges.",
            f"- ``{STORE_ASSET_DIR}/feature-graphic.png`` - 1024x500, no alpha.",
            f"- ``{STORE_ASSET_DIR}/screenshots/`` - one 1:1 screenshot per colorway,",
            "  watch face only, no device frame, no text, no transparency.",
            "",
        ]
    )


def _readme(spec: WatchFaceSpec, package: str) -> str:
    """``README.md`` that ships with the emitted project.

    Args:
        spec: Face that was emitted.
        package: Application id.

    Returns:
        Markdown text.
    """
    return "\n".join(
        [
            f"# {spec.name}",
            "",
            f"Watch Face Format source project for ``{package}``.",
            "",
            "This package contains resources only, and it must stay that way. There is",
            "no Wear OS application logic here and none may be added: Google Play",
            "rejects an app bundle that carries both a custom watch face and Wear OS",
            "logic, so this project has to be its own bundle, built and uploaded on its",
            "own.",
            "",
            "## Layout",
            "",
            '- ``AndroidManifest.xml`` - watch hardware feature, ``hasCode="false"``, the',
            "  standalone meta-data, and the Watch Face Format version property.",
            "- ``res/raw/watchface.xml`` - the whole face: exactly one ``Scene``, with the",
            "  hands and the complications drawn last so ambient can drop the layers",
            "  underneath them.",
            "- ``res/xml/watch_face_info.xml`` - preview, category, retail availability,",
            "  multiple instances, ``Editable``, and flavour support.",
            "- ``res/xml/watch_face_shapes.xml`` - only present when size variants were",
            "  requested; at most ten ``<WatchFace>`` entries are allowed.",
            "- ``res/drawable/`` - the preview plus the three hand drawables the clock uses.",
            "- ``res/values/strings.xml`` - every editor label.",
            f"- ``{STORE_ASSET_DIR}/`` - Play icon, feature graphic, one screenshot per colorway.",
            "- ``manifest.json`` - what was emitted, the memory estimate, and the measured",
            "  illuminated ratio.",
            "",
            "## Add a face",
            "",
            "Write a JSON override and pass it in as a catalog file. A row that reuses a",
            "catalog slug changes only the keys it states; a row with a new slug adds a",
            "face and must state slug, name, style, shape, and palette.",
            "",
            "## Build the app bundle",
            "",
            "Open this folder in Android Studio, or from a shell with the Android SDK",
            "installed run the Gradle bundle task for the release variant. The ``.aab``",
            "lands under ``build/outputs/bundle/release/`` and is what you upload to a",
            "Wear OS track in Play Console.",
            "",
            "Before you submit, run the official Watch Face Format validator and the",
            "memory footprint evaluator over this folder: both mirror the checks Play",
            "performs, so passing here saves a review round trip.",
            "",
        ]
    )


def _manifest_json(
    spec: WatchFaceSpec,
    package: str,
    wff_version: int,
    tool_version: str,
    files: Sequence[str],
    listing: JsonObject,
    memory: MemoryEstimate,
    illuminated: float,
    preview_edge: int,
) -> str:
    """``manifest.json`` describing the emitted project.

    Args:
        spec: Face that was emitted.
        package: Application id.
        wff_version: Format version declared.
        tool_version: Publisher property value.
        files: Project-relative paths written.
        listing: Play listing fields.
        memory: Estimated footprint.
        illuminated: Measured illuminated ratio of the default preview.
        preview_edge: Square edge the preview and screenshots were rastered at.

    Returns:
        Deterministic JSON text with sorted keys.
    """
    file_rows: list[Json] = [str(name) for name in files]
    document: JsonObject = {
        "generated_by": f"ez-comfy-stack ez_watch {tool_version}",
        "wear_os_wording": "Wear OS",
        "package": package,
        "bundle_separation": "watch-face only; no Wear OS application logic in this bundle",
        "watch_face": {
            "slug": spec.slug,
            "name": spec.name,
            "style": spec.style,
            "shape": spec.shape,
            "category": spec.category,
            "tags": list(spec.tags),
            "design_edge": spec.design_edge,
            "preview_time": DEFAULT_PREVIEW_TIME,
        },
        "wff": {
            "version": wff_version,
            "min_sdk": WFF_VERSION_API[wff_version],
            "publisher": f"ez-comfy-stack-{tool_version}",
            "preview_edge": preview_edge,
        },
        "themes": [
            {"index": index, "name": theme.name, "colors": list(theme.colors)}
            for index, theme in enumerate(spec.palette)
        ],
        "complication_slots": [
            {
                "slot_id": slot.slot_id,
                "x": slot.x,
                "y": slot.y,
                "width": slot.width,
                "height": slot.height,
                "supported_types": list(slot.supported_types),
                "bounding": "BoundingOval" if spec.shape == "round" else "BoundingBox",
            }
            for slot in spec.complications
        ],
        "memory": {
            "design_edge": memory.design_edge,
            "ambient_bytes": memory.ambient_bytes,
            "interactive_bytes": memory.interactive_bytes,
            "illuminated_ratio": round(illuminated, 4),
            "illuminated_limit": ILLUMINATED_LIMIT,
        },
        "listing": listing,
        "files": file_rows,
    }
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def _application_id(spec: WatchFaceSpec) -> str:
    """Application id for one face.

    Args:
        spec: Face being packaged.

    Returns:
        A dotted id unique to the slug.
    """
    return f"{_APPLICATION_ID_PREFIX}.{spec.slug.replace('-', '_')}"


def build_face(
    spec: WatchFaceSpec,
    out_dir: Path | str,
    *,
    wff_version: int = DEFAULT_WFF_VERSION,
    theme: int = 0,
    dry_run: bool = False,
    preview_edge: int = DEFAULT_PREVIEW_EDGE,
    tool_version: str = DEFAULT_TOOL_VERSION,
    size_variants: bool = False,
    include_numerals: bool = False,
) -> ProjectResult:
    """Write one submittable face project, or describe it without writing.

    Args:
        spec: Face to build.
        out_dir: Directory to write ``<slug>/`` into; created when missing.
        wff_version: Format version to declare.
        theme: Colourway the in-package preview shows.
        dry_run: Compute everything and write nothing.
        preview_edge: Square edge for the preview and the screenshots.
        tool_version: Publisher property value.
        size_variants: Emit ``watch_face_shapes.xml`` for the round small and
            large layouts.
        include_numerals: Add literal 12, 3, 6, and 9 numerals to the dial.

    Returns:
        The build result, with the compliance gate's findings.

    Raises:
        ValueError: the preview edge is below the Play screenshot minimum.
    """
    if preview_edge < MIN_PREVIEW_EDGE:
        raise ValueError(f"preview_edge must be at least {MIN_PREVIEW_EDGE}, got {preview_edge}")
    package = _application_id(spec)
    root = Path(out_dir) / spec.slug
    files: dict[str, bytes] = {}

    files["AndroidManifest.xml"] = _manifest_xml(wff_version, tool_version).encode("utf-8")
    files["build.gradle"] = _build_gradle(package, wff_version).encode("utf-8")
    files["settings.gradle"] = _settings_gradle().encode("utf-8")
    files["res/raw/watchface.xml"] = watch_face_xml(
        spec, wff_version=wff_version, include_numerals=include_numerals
    ).encode("utf-8")
    files["res/xml/watch_face_info.xml"] = _watch_face_info_xml(
        spec, flavors=wff_version >= 2
    ).encode("utf-8")
    files["res/values/strings.xml"] = _strings_xml(spec).encode("utf-8")
    if size_variants and spec.shape == "round":
        files["res/xml/watch_face_shapes.xml"] = _watch_face_shapes_xml().encode("utf-8")

    preview = _face_canvas(spec, theme, preview_edge)
    illuminated = preview.illuminated_ratio()
    files["res/drawable/preview.png"] = preview.png_bytes()
    for kind in ("hour", "minute", "second"):
        if spec.show_hands:
            files[f"res/drawable/hand_{kind}.png"] = hand_canvas(kind, preview_edge).png_bytes()
    for index in range(len(spec.palette)):
        shot = _face_canvas(spec, index, preview_edge)
        files[f"{STORE_ASSET_DIR}/screenshots/{spec.slug}-theme-{index}.png"] = shot.png_bytes()
    files[f"{STORE_ASSET_DIR}/icon.png"] = _face_canvas(
        spec, theme, PLAY_LAUNCHER_ICON_PX, bleed=1.09
    ).png_bytes()
    files[f"{STORE_ASSET_DIR}/feature-graphic.png"] = encode_rgb_png(
        _feature_plate(spec, theme)
    )

    listing = _listing(spec)
    files["store-listing.md"] = _listing_markdown(spec, listing).encode("utf-8")
    files["README.md"] = _readme(spec, package).encode("utf-8")
    memory = memory_estimate(
        spec.design_edge,
        hands=spec.show_hands,
        slot_boxes=tuple((slot.width, slot.height) for slot in spec.complications),
    )
    files["manifest.json"] = _manifest_json(
        spec,
        package,
        wff_version,
        tool_version,
        tuple(files),
        listing,
        memory,
        illuminated,
        preview_edge,
    ).encode("utf-8")

    written = sorted(files)
    if dry_run:
        findings: tuple[Finding, ...] = ()
    else:
        for relative in written:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(files[relative])
        findings = validate_project(root)
    return ProjectResult(
        slug=spec.slug,
        package=package,
        out_dir=str(root),
        files=tuple(written),
        themes=tuple(palette.name for palette in spec.palette),
        slot_ids=tuple(slot.slot_id for slot in spec.complications),
        memory=memory,
        illuminated_ratio=illuminated,
        findings=findings,
        dry_run=dry_run,
    )


def _feature_plate(spec: WatchFaceSpec, theme: int) -> Canvas:
    """Feature graphic: the face on an opaque 1024x500 plate.

    Args:
        spec: Face to draw.
        theme: Colourway to show.

    Returns:
        Opaque canvas with no alpha anywhere.
    """
    canvas = Canvas(PLAY_FEATURE_GRAPHIC_WIDTH, PLAY_FEATURE_GRAPHIC_HEIGHT)
    canvas.fill(hex_to_rgba(spec.background).blended_over(BLACK))
    accent, secondary, _text = _theme_colors(spec, theme)
    edge = PLAY_FEATURE_GRAPHIC_HEIGHT
    bar = _Painter(canvas)
    step = max(2, edge // 26)
    for row in range(0, PLAY_FEATURE_GRAPHIC_HEIGHT, step):
        width = 40 + (row * 3) % 200
        bar.box(40, row, width, max(2, step // 2), secondary if row % (2 * step) else accent)
    scaled = _scaled_for_edge(spec, edge)
    _paint_face(_Painter(canvas, PLAY_FEATURE_GRAPHIC_WIDTH - edge), scaled, theme)
    return canvas


def build_face_pack(
    out_dir: Path | str,
    specs: Sequence[WatchFaceSpec] = WATCH_FACE_CATALOG,
    *,
    wff_version: int = DEFAULT_WFF_VERSION,
    preview_edge: int = DEFAULT_PREVIEW_EDGE,
    tool_version: str = DEFAULT_TOOL_VERSION,
    size_variants: bool = False,
    dry_run: bool = False,
) -> tuple[ProjectResult, ...]:
    """Build every face in a pack, one folder each.

    Args:
        out_dir: Folder the per-face projects are written into.
        specs: Faces to build; the whole catalog by default.
        wff_version: Format version to declare.
        preview_edge: Square edge for previews and screenshots.
        tool_version: Publisher property value.
        size_variants: Emit the round small and large shapes file.
        dry_run: Compute everything and write nothing.

    Returns:
        One result per face, in the order given.
    """
    return tuple(
        build_face(
            spec,
            out_dir,
            wff_version=wff_version,
            preview_edge=preview_edge,
            tool_version=tool_version,
            size_variants=size_variants,
            dry_run=dry_run,
        )
        for spec in specs
    )


def _select(args: argparse.Namespace) -> tuple[WatchFaceSpec, ...]:
    """Pick the faces an operator asked for.

    Args:
        args: Parsed command line.

    Returns:
        The chosen specs, catalog order preserved.

    Raises:
        ValueError: a named slug is unknown or the catalog file is malformed.
    """
    pool = load_catalog(args.catalog) if args.catalog else WATCH_FACE_CATALOG
    if args.face:
        wanted = set(args.face)
        unknown = sorted(wanted - {item.slug for item in pool})
        if unknown:
            raise ValueError(f"unknown face slug or slugs: {', '.join(unknown)}")
        return tuple(item for item in pool if item.slug in wanted)
    if args.style:
        return tuple(item for item in pool if item.style == args.style)
    return pool


def build_parser() -> argparse.ArgumentParser:
    """Command line for the generator.

    Returns:
        The parser, with every operator knob.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m ez_watch.project",
        description="Emit a submittable Wear OS Watch Face Format project.",
    )
    parser.add_argument("--out", required=True, help="Folder to write the projects into.")
    parser.add_argument("--face", action="append", default=[], help="Face slug; repeatable.")
    parser.add_argument("--style", choices=sorted(STYLES), help="Build one style only.")
    parser.add_argument("--catalog", help="JSON override file merged over the catalog.")
    parser.add_argument(
        "--wff-version",
        type=int,
        default=DEFAULT_WFF_VERSION,
        help="Format version to declare, 1 to 4.",
    )
    parser.add_argument(
        "--preview-edge",
        type=int,
        default=DEFAULT_PREVIEW_EDGE,
        help=f"Square preview edge, at least {MIN_PREVIEW_EDGE}.",
    )
    parser.add_argument(
        "--size-variants",
        action="store_true",
        help="Write the round small and large shapes file.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute and report, write nothing.")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Build into a scratch folder, run the compliance gate, and report.",
    )
    return parser


def _report(results: Sequence[ProjectResult], *, written: bool) -> int:
    """Print one line per face plus every finding.

    Args:
        results: Build results to report.
        written: Whether files landed on disk.

    Returns:
        Zero when nothing failed, one when any face has an error finding.
    """
    verb = "wrote" if written else "checked"
    failed = False
    for result in results:
        print(
            f"ez_watch: {verb} {result.slug} into {result.out_dir} "
            f"({len(result.files)} files, ambient={result.memory.ambient_bytes}, "
            f"interactive={result.memory.interactive_bytes}, "
            f"illuminated={result.illuminated_ratio:.4f})"
        )
        for finding in result.findings:
            print(f"  {finding.severity} {finding.code}: {finding.message} [{finding.path}]")
        failed = failed or not result.clean
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generator from a command line.

    Args:
        argv: Arguments after the program name; ``sys.argv[1:]`` when None.

    Returns:
        Zero when every selected face is submittable, one on a gate error, and
        two when the selection itself is bad.
    """
    args = build_parser().parse_args(argv)
    try:
        specs = _select(args)
    except ValueError as exc:
        print(f"ez_watch: {exc}")
        return 2
    if not specs:
        print("ez_watch: no faces matched")
        return 2
    if args.validate_only:
        with tempfile.TemporaryDirectory(prefix="ez-watch-") as scratch:
            results = build_face_pack(
                scratch,
                specs,
                wff_version=args.wff_version,
                preview_edge=args.preview_edge,
                size_variants=args.size_variants,
            )
        return _report(results, written=False)
    results = build_face_pack(
        Path(args.out),
        specs,
        wff_version=args.wff_version,
        preview_edge=args.preview_edge,
        size_variants=args.size_variants,
        dry_run=args.dry_run,
    )
    return _report(results, written=not args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
