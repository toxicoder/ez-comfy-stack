"""Deterministic glyph artwork: primitives, recipes, and the four layers.

Every mark is drawn from a small set of stdlib primitives (disc, ring,
rounded rect, bar set, dot grid, line, polygon) onto an :class:`ez_raster.Canvas`.
No model, no font, no third-party raster library: the same catalog entry
renders the same pixels on every host, which is what lets a drift test pin a
pack byte for byte.

The geometry follows the verified requirements digest. The adaptive sheet is
108 dp; only the central 66 dp survives the OEM mask, and artwork must be at
least 48 dp and at most 66 dp, with clean edges and no baked shadow. Every
recipe therefore paints inside :data:`ARTWORK_MAX_DP`, and
:func:`artwork_bounds` is how the validator measures that promise back.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from ez_raster import (
    ADAPTIVE_CANVAS_DP,
    ADAPTIVE_SAFE_RATIO,
    BLACK,
    TRANSPARENT,
    WHITE,
    Canvas,
    Rgba,
    decode_rgba,
    from_rgba_bytes,
    hex_to_rgba,
)

from .catalog import IconSpec

SAFE_ZONE_RATIO = ADAPTIVE_SAFE_RATIO
"""Fraction of the sheet a launcher never masks, straight from :mod:`ez_raster`."""

SHEET_DP = ADAPTIVE_CANVAS_DP
"""Adaptive-icon canvas edge in dp: 108."""

ARTWORK_MAX_DP = 66
"""Largest artwork edge allowed inside the safe zone (digest: 66 dp)."""

ARTWORK_MIN_DP = 48
"""Smallest artwork edge that still reads on a launcher grid (digest: 48 dp)."""

ARTWORK_TARGET_DP = 60
"""Edge every glyph is fitted to: inside 66 dp, comfortably past 48 dp."""

DEFAULT_SHEET_PX = 108
"""Sheet edge in pixels a caller gets when it asks for no size."""

LEGACY_CORNER_RATIO = 0.25
"""Corner radius of the composited legacy launcher tile, as a box fraction."""

_MONO_PRIMARY = WHITE
"""Ink a themed silhouette paints with."""

_MONO_CUT = TRANSPARENT
"""Ink a themed silhouette cuts away instead of painting."""


@dataclass(frozen=True)
class GlyphColors:
    """The three inks a recipe paints with.

    Args:
        primary: The mass of the glyph; never transparent in a colour layer.
        accent: Secondary mark, cut away in a monochrome render.
        detail: Fine strokes, cut away in a monochrome render.
"""

    primary: Rgba
    accent: Rgba
    detail: Rgba


@dataclass(frozen=True)
class Box:
    """Square drawing area a recipe paints into.

    Args:
        left: First column of the box.
        top: First row of the box.
        side: Edge length in pixels.
"""

    left: int
    top: int
    side: int

    def px(self, x: float) -> int:
        """Map a 0..1 horizontal fraction onto a column.

        Args:
            x: Fraction across the box.

        Returns:
            Column index.
        """
        return self.left + round(x * self.side)

    def py(self, y: float) -> int:
        """Map a 0..1 vertical fraction onto a row.

        Args:
            y: Fraction down the box.

        Returns:
            Row index.
        """
        return self.top + round(y * self.side)

    def u(self, fraction: float) -> int:
        """Scale a 0..1 fraction to a length in pixels.

        Args:
            fraction: Length as a fraction of the box.

        Returns:
            Length in pixels, never negative.
        """
        return max(0, round(fraction * self.side))

    @property
    def centre(self) -> float:
        """Centre of the box in pixel coordinates.

        Returns:
            Half the edge, shared by both axes.
        """
        return self.left + self.side / 2.0


GlyphPainter: TypeAlias = Callable[[Canvas, Box, GlyphColors], None]
"""A recipe: draw one glyph into a box with three inks."""


def artwork_side(side: int) -> int:
    """Edge of the artwork box on a sheet of a given size.

    Args:
        side: Sheet edge in pixels.

    Returns:
        Artwork edge, which is the 66 dp safe zone scaled to the sheet.
"""
    return max(1, round(side * ARTWORK_MAX_DP / SHEET_DP))


def artwork_box(side: int) -> Box:
    """Centred artwork box for a sheet of a given size.

    Args:
        side: Sheet edge in pixels.

    Returns:
        Box whose edges sit on the safe-zone boundary.
"""
    inner = artwork_side(side)
    offset = (side - inner) // 2
    return Box(left=offset, top=offset, side=inner)


def legacy_box(side: int) -> Box:
    """Full-bleed box for a composited launcher tile.

    Args:
        side: Tile edge in pixels.

    Returns:
        Box covering the whole tile.
"""
    return Box(left=0, top=0, side=side)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def _disc(canvas: Canvas, box: Box, color: Rgba, cx: float, cy: float, radius: float) -> None:
    """Paint a disc at normalised coordinates.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        cx: Centre column as a box fraction.
        cy: Centre row as a box fraction.
        radius: Radius as a box fraction.
"""
    canvas.fill_circle(box.px(cx), box.py(cy), float(box.u(radius)), color)


def _cut(canvas: Canvas, box: Box, cx: float, cy: float, radius: float) -> None:
    """Punch a transparent hole.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        cx: Centre column as a box fraction.
        cy: Centre row as a box fraction.
        radius: Radius as a box fraction.
"""
    _disc(canvas, box, TRANSPARENT, cx, cy, radius)


def _ring(
    canvas: Canvas, box: Box, color: Rgba, cx: float, cy: float, radius: float, weight: float
) -> None:
    """Paint an annulus.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        cx: Centre column as a box fraction.
        cy: Centre row as a box fraction.
        radius: Outer radius as a box fraction.
        weight: Stroke width as a box fraction.
"""
    _disc(canvas, box, color, cx, cy, radius)
    _cut(canvas, box, cx, cy, radius - weight)


def _rect(canvas: Canvas, box: Box, color: Rgba, x: float, y: float, w: float, h: float) -> None:
    """Paint an axis-aligned block at normalised coordinates.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x: Left edge as a box fraction.
        y: Top edge as a box fraction.
        w: Width as a box fraction.
        h: Height as a box fraction.
"""
    canvas.fill_rect(box.px(x), box.py(y), box.u(w), box.u(h), color)


def _rounded(
    canvas: Canvas,
    box: Box,
    color: Rgba,
    x: float,
    y: float,
    w: float,
    h: float,
    radius: float,
) -> None:
    """Paint a rounded rectangle.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x: Left edge as a box fraction.
        y: Top edge as a box fraction.
        w: Width as a box fraction.
        h: Height as a box fraction.
        radius: Corner radius as a box fraction.
"""
    left, top = box.px(x), box.py(y)
    width, height = box.u(w), box.u(h)
    corner = min(box.u(radius), width // 2, height // 2)
    canvas.fill_rect(left + corner, top, width - 2 * corner, height, color)
    canvas.fill_rect(left, top + corner, width, height - 2 * corner, color)
    centres = (
        (left + corner, top + corner),
        (left + width - corner - 1, top + corner),
        (left + corner, top + height - corner - 1),
        (left + width - corner - 1, top + height - corner - 1),
    )
    for centre_x, centre_y in centres:
        canvas.fill_circle(centre_x, centre_y, float(corner), color)


def _frame(
    canvas: Canvas,
    box: Box,
    color: Rgba,
    x: float,
    y: float,
    w: float,
    h: float,
    radius: float,
    weight: float,
) -> None:
    """Paint a rounded rectangular outline.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x: Left edge as a box fraction.
        y: Top edge as a box fraction.
        w: Width as a box fraction.
        h: Height as a box fraction.
        radius: Corner radius as a box fraction.
        weight: Stroke width as a box fraction.
"""
    _rounded(canvas, box, color, x, y, w, h, radius)
    _rounded(
        canvas,
        box,
        TRANSPARENT,
        x + weight,
        y + weight,
        w - 2 * weight,
        h - 2 * weight,
        radius - weight,
    )


def _line(
    canvas: Canvas,
    box: Box,
    color: Rgba,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    weight: float,
) -> None:
    """Paint a straight stroke at normalised coordinates.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x0: Start column as a box fraction.
        y0: Start row as a box fraction.
        x1: End column as a box fraction.
        y1: End row as a box fraction.
        weight: Stroke width as a box fraction.
"""
    canvas.draw_line(
        box.px(x0), box.py(y0), box.px(x1), box.py(y1), color, max(1, box.u(weight))
    )


def _dots(
    canvas: Canvas,
    box: Box,
    color: Rgba,
    x: float,
    y: float,
    w: float,
    h: float,
    rows: int,
    cols: int,
    radius: float,
) -> None:
    """Paint a grid of dots, centred in their cells.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x: Left edge of the grid as a box fraction.
        y: Top edge of the grid as a box fraction.
        w: Grid width as a box fraction.
        h: Grid height as a box fraction.
        rows: Number of rows, at least 1.
        cols: Number of columns, at least 1.
        radius: Dot radius as a box fraction.
"""
    for row in range(rows):
        for column in range(cols):
            centre_x = x + w * (column + 0.5) / cols
            centre_y = y + h * (row + 0.5) / rows
            _disc(canvas, box, color, centre_x, centre_y, radius)


def _bars(
    canvas: Canvas,
    box: Box,
    color: Rgba,
    x: float,
    w: float,
    heights: Sequence[float],
    base: float = 1.0,
    thickness: float = 0.6,
) -> None:
    """Paint a bar set standing on a baseline.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        x: Left edge of the set as a box fraction.
        w: Set width as a box fraction.
        heights: Bar heights as box fractions, left to right.
        base: Baseline row as a box fraction.
        thickness: Bar width as a fraction of each slot.
"""
    slots = len(heights)
    slot = w / slots
    for index, height in enumerate(heights):
        bar_w = slot * thickness
        centre = x + slot * (index + 0.5)
        _rect(canvas, box, color, centre - bar_w / 2.0, base - height, bar_w, height)


def _fill_polygon(canvas: Canvas, points: Sequence[tuple[int, int]], color: Rgba) -> None:
    """Fill a polygon with the even-odd scanline rule.

    Args:
        canvas: Target canvas.
        points: Vertices in pixel coordinates, closed implicitly.
        color: Colour to write.
"""
    top = max(0, min(point[1] for point in points))
    bottom = min(canvas.height - 1, max(point[1] for point in points))
    count = len(points)
    for row in range(top, bottom + 1):
        height = row + 0.5
        crossings: list[float] = []
        for index in range(count):
            ax, ay = points[index]
            bx, by = points[(index + 1) % count]
            if (ay > height) != (by > height):
                crossings.append(ax + (height - ay) * (bx - ax) / (by - ay))
        crossings.sort()
        for pair in range(0, len(crossings) - 1, 2):
            left = round(crossings[pair] - 0.5)
            right = round(crossings[pair + 1] - 0.5)
            canvas.fill_rect(left, row, max(1, right - left + 1), 1, color)


def _polygon(canvas: Canvas, box: Box, color: Rgba, points: Sequence[tuple[float, float]]) -> None:
    """Fill a polygon given in normalised coordinates.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        points: Vertices as box fractions, closed implicitly.
"""
    _fill_polygon(canvas, [(box.px(x), box.py(y)) for x, y in points], color)


def _star_points(points: int, inner: float) -> tuple[tuple[float, float], ...]:
    """Build a normalised star outline.

    Args:
        points: Number of star points.
        inner: Radius of the inner vertices, as a box fraction.

    Returns:
        Vertices around the star, in box fractions.
"""
    vertices: list[tuple[float, float]] = []
    for index in range(points * 2):
        angle = math.pi * index / points - math.pi / 2.0
        radius = 0.5 if index % 2 == 0 else inner
        vertices.append((0.5 + radius * math.cos(angle), 0.5 + radius * math.sin(angle)))
    return tuple(vertices)


def _rays(
    canvas: Canvas, box: Box, color: Rgba, count: int, weight: float, inner: float, outer: float
) -> None:
    """Paint radial spokes around the centre.

    Args:
        canvas: Target canvas.
        box: Drawing area.
        color: Colour to write.
        count: Number of spokes.
        weight: Stroke width as a box fraction.
        inner: Radius the spokes start at, as a box fraction.
        outer: Radius the spokes end at, as a box fraction.
"""
    for index in range(count):
        angle = 2.0 * math.pi * index / count
        _line(
            canvas,
            box,
            color,
            0.5 + inner * math.cos(angle),
            0.5 + inner * math.sin(angle),
            0.5 + outer * math.cos(angle),
            0.5 + outer * math.sin(angle),
            weight,
        )


# ---------------------------------------------------------------------------
# Recipes. The mass is always primary so a monochrome render keeps a solid
# silhouette; accent and detail only ever sit on top of it.
# ---------------------------------------------------------------------------


def _paint_speech(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a single chat bubble with three dots.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.04, 0.14, 0.92, 0.58, 0.18)
    _polygon(canvas, box, inks.primary, ((0.22, 0.68), (0.44, 0.68), (0.26, 0.92)))
    _dots(canvas, box, inks.accent, 0.20, 0.34, 0.60, 0.18, 1, 3, 0.055)


def _paint_speech_pair(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw two overlapping chat bubbles.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.02, 0.10, 0.64, 0.44, 0.14)
    _polygon(canvas, box, inks.primary, ((0.16, 0.50), (0.36, 0.50), (0.20, 0.70)))
    _rounded(canvas, box, inks.primary, 0.34, 0.44, 0.64, 0.42, 0.14)
    _polygon(canvas, box, inks.primary, ((0.66, 0.82), (0.86, 0.82), (0.80, 0.98)))
    _dots(canvas, box, inks.accent, 0.44, 0.60, 0.44, 0.12, 1, 3, 0.045)


def _paint_phone(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a handset held at an angle.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.24, 0.24, 0.20)
    _disc(canvas, box, inks.primary, 0.76, 0.76, 0.20)
    _line(canvas, box, inks.primary, 0.30, 0.32, 0.70, 0.68, 0.20)
    _disc(canvas, box, inks.accent, 0.24, 0.24, 0.08)
    _disc(canvas, box, inks.accent, 0.76, 0.76, 0.08)


def _paint_camera(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a camera body with a lens.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.02, 0.22, 0.96, 0.62, 0.14)
    _rect(canvas, box, inks.primary, 0.30, 0.12, 0.24, 0.14)
    _ring(canvas, box, inks.accent, 0.50, 0.53, 0.20, 0.07)
    _disc(canvas, box, inks.accent, 0.50, 0.53, 0.07)
    _disc(canvas, box, inks.detail, 0.79, 0.34, 0.045)


def _paint_gallery(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a framed mountain and sun.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _frame(canvas, box, inks.primary, 0.04, 0.10, 0.92, 0.80, 0.12, 0.09)
    _polygon(canvas, box, inks.primary, ((0.16, 0.76), (0.44, 0.40), (0.62, 0.62), (0.84, 0.36), (0.84, 0.76)))
    _disc(canvas, box, inks.accent, 0.68, 0.30, 0.09)


def _paint_gallery_stack(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw three stacked photo cards.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.16, 0.06, 0.70, 0.24, 0.08)
    _rounded(canvas, box, inks.primary, 0.10, 0.34, 0.76, 0.24, 0.08)
    _rounded(canvas, box, inks.primary, 0.04, 0.62, 0.82, 0.30, 0.08)
    _disc(canvas, box, inks.accent, 0.24, 0.76, 0.055)


def _paint_pin(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a map pin.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.50, 0.36, 0.34)
    _polygon(canvas, box, inks.primary, ((0.24, 0.52), (0.76, 0.52), (0.50, 0.98)))
    _cut(canvas, box, 0.50, 0.36, 0.14)
    _disc(canvas, box, inks.accent, 0.50, 0.36, 0.08)


def _paint_map(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a folded map in three panels.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    for index, shade in enumerate((inks.primary, inks.accent, inks.primary)):
        _rect(canvas, box, shade, 0.06 + 0.30 * index, 0.16 + 0.04 * (index % 2), 0.29, 0.68)
    _line(canvas, box, inks.detail, 0.10, 0.30, 0.55, 0.72, 0.05)
    _disc(canvas, box, inks.detail, 0.72, 0.34, 0.08)


def _paint_compass(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a compass rose.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.50, 0.50, 0.48, 0.08)
    _polygon(canvas, box, inks.accent, ((0.50, 0.14), (0.66, 0.52), (0.50, 0.86), (0.34, 0.52)))
    _cut(canvas, box, 0.50, 0.50, 0.07)


def _paint_dot_path(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a dotted route with two stops.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _dots(canvas, box, inks.primary, 0.06, 0.60, 0.88, 0.10, 1, 6, 0.045)
    _disc(canvas, box, inks.accent, 0.14, 0.30, 0.13)
    _disc(canvas, box, inks.accent, 0.86, 0.30, 0.13)
    _line(canvas, box, inks.detail, 0.14, 0.42, 0.86, 0.42, 0.05)


def _paint_cloud(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a cloud.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.34, 0.52, 0.22)
    _disc(canvas, box, inks.primary, 0.58, 0.42, 0.28)
    _disc(canvas, box, inks.primary, 0.74, 0.58, 0.18)
    _rect(canvas, box, inks.primary, 0.24, 0.56, 0.54, 0.22)
    _rect(canvas, box, inks.accent, 0.30, 0.74, 0.40, 0.06)


def _paint_rain(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a cloud with three drops.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.34, 0.36, 0.20)
    _disc(canvas, box, inks.primary, 0.60, 0.30, 0.24)
    _disc(canvas, box, inks.primary, 0.74, 0.44, 0.16)
    _rect(canvas, box, inks.primary, 0.26, 0.40, 0.50, 0.18)
    for index in range(3):
        _line(canvas, box, inks.accent, 0.30 + 0.16 * index, 0.66, 0.24 + 0.16 * index, 0.92, 0.07)


def _paint_sun(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a sun with spokes.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rays(canvas, box, inks.accent, 8, 0.07, 0.34, 0.44)
    _disc(canvas, box, inks.primary, 0.50, 0.50, 0.28)


def _paint_note(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a beamed pair of music notes.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _line(canvas, box, inks.primary, 0.30, 0.16, 0.30, 0.70, 0.07)
    _line(canvas, box, inks.primary, 0.74, 0.10, 0.74, 0.64, 0.07)
    _rect(canvas, box, inks.primary, 0.30, 0.12, 0.44, 0.10)
    _disc(canvas, box, inks.primary, 0.24, 0.74, 0.14)
    _disc(canvas, box, inks.primary, 0.68, 0.68, 0.14)
    _cut(canvas, box, 0.24, 0.74, 0.05)


def _paint_waveform(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a symmetric waveform.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    heights = (0.28, 0.52, 0.86, 0.62, 0.34, 0.70, 0.44, 0.20)
    _bars(canvas, box, inks.primary, 0.02, 0.96, heights, base=0.78, thickness=0.55)
    _bars(canvas, box, inks.accent, 0.02, 0.96, heights, base=0.22, thickness=0.55)


def _paint_ring(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a vinyl disc.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.50, 0.50, 0.48)
    _ring(canvas, box, inks.accent, 0.50, 0.50, 0.34, 0.03)
    _ring(canvas, box, inks.accent, 0.50, 0.50, 0.24, 0.03)
    _cut(canvas, box, 0.50, 0.50, 0.10)


def _paint_mic(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a studio microphone.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.36, 0.06, 0.28, 0.48, 0.14)
    _ring(canvas, box, inks.accent, 0.50, 0.44, 0.30, 0.06)
    _rect(canvas, box, inks.primary, 0.30, 0.44, 0.40, 0.10)
    _rect(canvas, box, inks.primary, 0.46, 0.56, 0.08, 0.24)
    _rect(canvas, box, inks.primary, 0.28, 0.80, 0.44, 0.09)


def _paint_play(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a play triangle in a frame.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _frame(canvas, box, inks.primary, 0.04, 0.04, 0.92, 0.92, 0.16, 0.09)
    _polygon(canvas, box, inks.accent, ((0.38, 0.28), (0.38, 0.72), (0.72, 0.50)))


def _paint_film(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a film strip.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.10, 0.88, 0.80, 0.10)
    _dots(canvas, box, inks.accent, 0.12, 0.16, 0.14, 0.68, 4, 1, 0.045)
    _dots(canvas, box, inks.accent, 0.74, 0.16, 0.14, 0.68, 4, 1, 0.045)
    _rect(canvas, box, inks.detail, 0.32, 0.30, 0.36, 0.40)


def _paint_share_nodes(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw three linked network nodes.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _line(canvas, box, inks.primary, 0.26, 0.50, 0.74, 0.24, 0.06)
    _line(canvas, box, inks.primary, 0.26, 0.50, 0.74, 0.76, 0.06)
    _disc(canvas, box, inks.primary, 0.26, 0.50, 0.16)
    _disc(canvas, box, inks.accent, 0.74, 0.24, 0.14)
    _disc(canvas, box, inks.accent, 0.74, 0.76, 0.14)


def _paint_person(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a single person.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.50, 0.30, 0.22)
    _rounded(canvas, box, inks.primary, 0.14, 0.56, 0.72, 0.44, 0.22)


def _paint_people(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw two people.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.34, 0.30, 0.18)
    _rounded(canvas, box, inks.primary, 0.06, 0.52, 0.56, 0.40, 0.20)
    _disc(canvas, box, inks.accent, 0.72, 0.34, 0.15)
    _rounded(canvas, box, inks.accent, 0.50, 0.56, 0.46, 0.36, 0.18)


def _paint_envelope(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a sealed envelope.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.04, 0.20, 0.92, 0.60, 0.10)
    _polygon(canvas, box, inks.accent, ((0.04, 0.24), (0.50, 0.58), (0.96, 0.24), (0.96, 0.34), (0.50, 0.68), (0.04, 0.34)))


def _paint_calendar(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a month calendar.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.14, 0.88, 0.80, 0.10)
    _rect(canvas, box, inks.accent, 0.06, 0.14, 0.88, 0.16)
    _rect(canvas, box, inks.primary, 0.22, 0.04, 0.08, 0.18)
    _rect(canvas, box, inks.primary, 0.70, 0.04, 0.08, 0.18)
    _dots(canvas, box, inks.detail, 0.16, 0.38, 0.68, 0.44, 3, 4, 0.045)


def _paint_clock(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw an analogue clock face.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.50, 0.50, 0.48, 0.08)
    _line(canvas, box, inks.accent, 0.50, 0.50, 0.50, 0.26, 0.06)
    _line(canvas, box, inks.accent, 0.50, 0.50, 0.70, 0.58, 0.06)
    _disc(canvas, box, inks.detail, 0.50, 0.50, 0.05)


def _paint_alarm(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw an alarm clock with bells.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.22, 0.20, 0.12)
    _disc(canvas, box, inks.primary, 0.78, 0.20, 0.12)
    _ring(canvas, box, inks.primary, 0.50, 0.54, 0.38, 0.08)
    _line(canvas, box, inks.accent, 0.50, 0.54, 0.50, 0.34, 0.06)
    _line(canvas, box, inks.accent, 0.50, 0.54, 0.66, 0.60, 0.06)
    _line(canvas, box, inks.primary, 0.24, 0.86, 0.14, 0.98, 0.07)
    _line(canvas, box, inks.primary, 0.76, 0.86, 0.86, 0.98, 0.07)


def _paint_notes(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a lined note page.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.10, 0.04, 0.80, 0.92, 0.08)
    _polygon(canvas, box, inks.accent, ((0.66, 0.04), (0.90, 0.04), (0.90, 0.28)))
    for index in range(4):
        _rect(canvas, box, inks.detail, 0.22, 0.30 + 0.14 * index, 0.50, 0.05)


def _paint_pencil(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a pencil laid diagonally.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.20, 0.80), (0.76, 0.24), (0.90, 0.38), (0.34, 0.94)))
    _polygon(canvas, box, inks.accent, ((0.76, 0.24), (0.90, 0.10), (0.90, 0.38)))
    _line(canvas, box, inks.detail, 0.28, 0.72, 0.80, 0.20, 0.04)


def _paint_check(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a bold check mark.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.06, 0.88, 0.88, 0.18)
    _line(canvas, box, inks.accent, 0.26, 0.52, 0.44, 0.70, 0.10)
    _line(canvas, box, inks.accent, 0.44, 0.70, 0.76, 0.30, 0.10)


def _paint_board(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a three-column board.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    for index in range(3):
        _rounded(canvas, box, inks.primary, 0.04 + 0.33 * index, 0.10, 0.27, 0.80, 0.06)
    _rect(canvas, box, inks.accent, 0.08, 0.18, 0.19, 0.10)
    _rect(canvas, box, inks.accent, 0.41, 0.18, 0.19, 0.24)
    _rect(canvas, box, inks.accent, 0.74, 0.18, 0.19, 0.16)


def _paint_chart(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a bar chart with a rising trend.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _bars(canvas, box, inks.primary, 0.06, 0.88, (0.28, 0.46, 0.66, 0.90), base=0.90, thickness=0.5)
    _line(canvas, box, inks.accent, 0.06, 0.92, 0.94, 0.92, 0.05)
    _line(canvas, box, inks.accent, 0.16, 0.52, 0.84, 0.20, 0.06)


def _paint_wallet(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a wallet with a card slot.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.04, 0.18, 0.92, 0.64, 0.12)
    _rect(canvas, box, inks.primary, 0.04, 0.26, 0.60, 0.10)
    _rounded(canvas, box, inks.accent, 0.56, 0.42, 0.40, 0.22, 0.08)
    _disc(canvas, box, inks.detail, 0.86, 0.53, 0.05)


def _paint_bank(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a bank front.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.04, 0.34), (0.50, 0.06), (0.96, 0.34)))
    _bars(canvas, box, inks.primary, 0.10, 0.80, (0.44,) * 4, base=0.80, thickness=0.42)
    _rect(canvas, box, inks.accent, 0.04, 0.82, 0.92, 0.10)


def _paint_coin(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a stack of coins.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.14, 0.14, 0.72, 0.18, 0.09)
    _rounded(canvas, box, inks.primary, 0.14, 0.38, 0.72, 0.18, 0.09)
    _disc(canvas, box, inks.accent, 0.50, 0.70, 0.28)
    _ring(canvas, box, inks.detail, 0.50, 0.70, 0.18, 0.04)


def _paint_dumbbell(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a dumbbell.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rect(canvas, box, inks.primary, 0.26, 0.46, 0.48, 0.08)
    _rounded(canvas, box, inks.primary, 0.10, 0.26, 0.16, 0.48, 0.05)
    _rounded(canvas, box, inks.primary, 0.74, 0.26, 0.16, 0.48, 0.05)
    _rect(canvas, box, inks.accent, 0.02, 0.38, 0.08, 0.24)
    _rect(canvas, box, inks.accent, 0.90, 0.38, 0.08, 0.24)


def _paint_pulse(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a heart with a heartbeat trace.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.30, 0.34, 0.24)
    _disc(canvas, box, inks.primary, 0.70, 0.34, 0.24)
    _polygon(canvas, box, inks.primary, ((0.07, 0.42), (0.93, 0.42), (0.50, 0.94)))
    _line(canvas, box, inks.accent, 0.16, 0.48, 0.36, 0.48, 0.05)
    _line(canvas, box, inks.accent, 0.36, 0.48, 0.48, 0.28, 0.05)
    _line(canvas, box, inks.accent, 0.48, 0.28, 0.60, 0.66, 0.05)
    _line(canvas, box, inks.accent, 0.60, 0.66, 0.72, 0.48, 0.05)
    _line(canvas, box, inks.accent, 0.72, 0.48, 0.86, 0.48, 0.05)


def _paint_shoe(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a running shoe.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.06, 0.52), (0.42, 0.36), (0.62, 0.58), (0.94, 0.64), (0.94, 0.82), (0.06, 0.82)))
    for index in range(3):
        _line(canvas, box, inks.accent, 0.20 + 0.12 * index, 0.52, 0.32 + 0.12 * index, 0.62, 0.05)
    _rect(canvas, box, inks.detail, 0.06, 0.82, 0.88, 0.10)


def _paint_heart(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a heart.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.30, 0.34, 0.26)
    _disc(canvas, box, inks.primary, 0.70, 0.34, 0.26)
    _polygon(canvas, box, inks.primary, ((0.04, 0.40), (0.96, 0.40), (0.50, 0.96)))


def _paint_cross(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a medical cross.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.06, 0.88, 0.88, 0.16)
    _rect(canvas, box, inks.accent, 0.40, 0.18, 0.20, 0.64)
    _rect(canvas, box, inks.accent, 0.18, 0.40, 0.64, 0.20)


def _paint_leaf(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a leaf with a midrib.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.50, 0.04), (0.90, 0.44), (0.50, 0.96), (0.10, 0.44)))
    _line(canvas, box, inks.accent, 0.50, 0.12, 0.50, 0.88, 0.05)
    _line(canvas, box, inks.accent, 0.50, 0.40, 0.70, 0.30, 0.04)
    _line(canvas, box, inks.accent, 0.50, 0.58, 0.30, 0.48, 0.04)


def _paint_cup(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a cup with steam.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.16, 0.36), (0.72, 0.36), (0.66, 0.92), (0.22, 0.92)))
    _ring(canvas, box, inks.primary, 0.74, 0.54, 0.16, 0.06)
    _line(canvas, box, inks.accent, 0.32, 0.10, 0.26, 0.26, 0.05)
    _line(canvas, box, inks.accent, 0.52, 0.08, 0.46, 0.24, 0.05)


def _paint_fork(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a fork beside a knife.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rect(canvas, box, inks.primary, 0.16, 0.34, 0.10, 0.60)
    for index in range(3):
        _rect(canvas, box, inks.primary, 0.13 + 0.06 * index, 0.06, 0.04, 0.30)
    _polygon(canvas, box, inks.accent, ((0.66, 0.06), (0.82, 0.30), (0.74, 0.94), (0.64, 0.94)))


def _paint_basket(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a shopping basket.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.10, 0.42), (0.90, 0.42), (0.78, 0.94), (0.22, 0.94)))
    _line(canvas, box, inks.accent, 0.30, 0.42, 0.34, 0.16, 0.05)
    _line(canvas, box, inks.accent, 0.70, 0.42, 0.66, 0.16, 0.05)
    _rect(canvas, box, inks.accent, 0.32, 0.12, 0.36, 0.06)


def _paint_plane(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw an airplane seen from above.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.50, 0.04), (0.62, 0.44), (0.96, 0.62), (0.62, 0.60), (0.58, 0.86), (0.42, 0.86), (0.38, 0.60), (0.04, 0.62), (0.38, 0.44)))
    _cut(canvas, box, 0.50, 0.28, 0.06)


def _paint_train(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a commuter train car.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.14, 0.12, 0.72, 0.66, 0.16)
    _dots(canvas, box, inks.accent, 0.22, 0.22, 0.56, 0.18, 1, 3, 0.055)
    _rect(canvas, box, inks.accent, 0.20, 0.52, 0.60, 0.08)
    _line(canvas, box, inks.primary, 0.24, 0.82, 0.16, 0.96, 0.06)
    _line(canvas, box, inks.primary, 0.76, 0.82, 0.84, 0.96, 0.06)


def _paint_bed(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a made bed.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rect(canvas, box, inks.primary, 0.04, 0.42, 0.12, 0.46)
    _rounded(canvas, box, inks.primary, 0.10, 0.48, 0.86, 0.28, 0.08)
    _rounded(canvas, box, inks.accent, 0.18, 0.34, 0.30, 0.18, 0.07)
    _rect(canvas, box, inks.primary, 0.10, 0.76, 0.86, 0.10)


def _paint_bag(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a shopping bag.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.10, 0.26, 0.80, 0.68, 0.08)
    _ring(canvas, box, inks.accent, 0.50, 0.30, 0.20, 0.06)
    _rect(canvas, box, inks.primary, 0.28, 0.20, 0.44, 0.12)


def _paint_tag(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a price tag.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.08, 0.08), (0.54, 0.08), (0.94, 0.48), (0.48, 0.94), (0.08, 0.54)))
    _cut(canvas, box, 0.30, 0.30, 0.09)
    _line(canvas, box, inks.accent, 0.56, 0.66, 0.78, 0.44, 0.06)


def _paint_gift(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a wrapped gift.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.08, 0.30, 0.84, 0.62, 0.06)
    _rect(canvas, box, inks.accent, 0.44, 0.30, 0.12, 0.62)
    _ring(canvas, box, inks.accent, 0.34, 0.22, 0.14, 0.06)
    _ring(canvas, box, inks.accent, 0.66, 0.22, 0.14, 0.06)


def _paint_news(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a newspaper page.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.08, 0.88, 0.84, 0.06)
    _rect(canvas, box, inks.accent, 0.16, 0.16, 0.68, 0.12)
    _rect(canvas, box, inks.detail, 0.16, 0.34, 0.30, 0.24)
    for index in range(3):
        _rect(canvas, box, inks.detail, 0.52, 0.36 + 0.10 * index, 0.32, 0.05)


def _paint_globe(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a globe.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.50, 0.50, 0.46, 0.07)
    _line(canvas, box, inks.accent, 0.06, 0.50, 0.94, 0.50, 0.05)
    _ring(canvas, box, inks.accent, 0.50, 0.50, 0.24, 0.04)
    _line(canvas, box, inks.detail, 0.50, 0.06, 0.50, 0.94, 0.05)


def _paint_book(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw an open book.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.04, 0.20), (0.50, 0.30), (0.50, 0.88), (0.04, 0.78)))
    _polygon(canvas, box, inks.primary, ((0.96, 0.20), (0.50, 0.30), (0.50, 0.88), (0.96, 0.78)))
    _line(canvas, box, inks.accent, 0.50, 0.30, 0.50, 0.88, 0.05)
    _line(canvas, box, inks.detail, 0.14, 0.34, 0.42, 0.40, 0.04)
    _line(canvas, box, inks.detail, 0.58, 0.40, 0.86, 0.34, 0.04)


def _paint_bookshelf(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a shelf of books.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rect(canvas, box, inks.primary, 0.04, 0.10, 0.92, 0.06)
    _rect(canvas, box, inks.primary, 0.04, 0.50, 0.92, 0.06)
    _rect(canvas, box, inks.primary, 0.04, 0.88, 0.92, 0.06)
    for index in range(4):
        _rect(canvas, box, inks.accent, 0.12 + 0.19 * index, 0.18, 0.12, 0.30)
    for index in range(3):
        _rect(canvas, box, inks.detail, 0.18 + 0.24 * index, 0.58, 0.14, 0.28)


def _paint_puzzle(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a puzzle piece.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.14, 0.22, 0.62, 0.62, 0.08)
    _disc(canvas, box, inks.primary, 0.45, 0.18, 0.14)
    _disc(canvas, box, inks.accent, 0.82, 0.52, 0.14)


def _paint_gamepad(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a game controller.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.02, 0.28, 0.96, 0.44, 0.20)
    _rect(canvas, box, inks.primary, 0.06, 0.60, 0.16, 0.24)
    _rect(canvas, box, inks.primary, 0.78, 0.60, 0.16, 0.24)
    _rect(canvas, box, inks.accent, 0.18, 0.44, 0.16, 0.06)
    _rect(canvas, box, inks.accent, 0.23, 0.39, 0.06, 0.16)
    _disc(canvas, box, inks.accent, 0.68, 0.42, 0.06)
    _disc(canvas, box, inks.accent, 0.80, 0.54, 0.06)


def _paint_star(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a five-pointed star.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, _star_points(5, 0.22))
    _disc(canvas, box, inks.accent, 0.50, 0.50, 0.10)


def _paint_blocks(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw three building blocks.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.06, 0.52, 0.36, 0.36, 0.06)
    _rounded(canvas, box, inks.accent, 0.48, 0.52, 0.36, 0.36, 0.06)
    _rounded(canvas, box, inks.primary, 0.27, 0.10, 0.36, 0.36, 0.06)
    _disc(canvas, box, inks.detail, 0.45, 0.28, 0.06)


def _paint_cap(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a graduation cap.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.50, 0.10), (0.98, 0.34), (0.50, 0.58), (0.02, 0.34)))
    _polygon(canvas, box, inks.accent, ((0.24, 0.46), (0.24, 0.76), (0.50, 0.88), (0.76, 0.76), (0.76, 0.46), (0.50, 0.58)))
    _line(canvas, box, inks.detail, 0.90, 0.38, 0.90, 0.72, 0.05)
    _disc(canvas, box, inks.detail, 0.90, 0.76, 0.06)


def _paint_search(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a magnifier.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.42, 0.42, 0.32, 0.09)
    _line(canvas, box, inks.primary, 0.64, 0.64, 0.94, 0.94, 0.12)
    _disc(canvas, box, inks.accent, 0.42, 0.42, 0.12)


def _paint_bolt(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a lightning bolt.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.56, 0.02), (0.20, 0.56), (0.44, 0.56), (0.36, 0.98), (0.80, 0.42), (0.54, 0.42)))


def _paint_calc(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a calculator.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.12, 0.04, 0.76, 0.92, 0.08)
    _rect(canvas, box, inks.accent, 0.20, 0.12, 0.60, 0.16)
    _dots(canvas, box, inks.detail, 0.20, 0.36, 0.60, 0.50, 3, 3, 0.055)


def _paint_folder(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a folder.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.04, 0.24), (0.34, 0.24), (0.44, 0.36), (0.96, 0.36), (0.96, 0.86), (0.04, 0.86)))
    _rect(canvas, box, inks.accent, 0.04, 0.46, 0.92, 0.08)


def _paint_gear(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a gear.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rays(canvas, box, inks.primary, 8, 0.14, 0.30, 0.42)
    _disc(canvas, box, inks.primary, 0.50, 0.50, 0.34)
    _cut(canvas, box, 0.50, 0.50, 0.14)
    _ring(canvas, box, inks.accent, 0.50, 0.50, 0.24, 0.04)


def _paint_sliders(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw three fader sliders.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    for index in range(3):
        _rect(canvas, box, inks.primary, 0.04, 0.18 + 0.28 * index, 0.92, 0.06)
    _disc(canvas, box, inks.accent, 0.28, 0.21, 0.09)
    _disc(canvas, box, inks.accent, 0.66, 0.49, 0.09)
    _disc(canvas, box, inks.accent, 0.42, 0.77, 0.09)


def _paint_terminal(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a terminal window.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.02, 0.10, 0.96, 0.80, 0.08)
    _polygon(canvas, box, inks.accent, ((0.16, 0.34), (0.36, 0.48), (0.16, 0.62), (0.16, 0.52), (0.26, 0.48), (0.16, 0.44)))
    _rect(canvas, box, inks.accent, 0.42, 0.58, 0.30, 0.07)
    _dots(canvas, box, inks.detail, 0.72, 0.16, 0.20, 0.08, 1, 3, 0.025)


def _paint_code(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a pair of angle brackets.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.36, 0.16), (0.46, 0.26), (0.26, 0.50), (0.46, 0.74), (0.36, 0.84), (0.08, 0.50)))
    _polygon(canvas, box, inks.primary, ((0.64, 0.16), (0.54, 0.26), (0.74, 0.50), (0.54, 0.74), (0.64, 0.84), (0.92, 0.50)))


def _paint_house(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a house.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.50, 0.04), (0.98, 0.48), (0.84, 0.48), (0.84, 0.94), (0.16, 0.94), (0.16, 0.48), (0.02, 0.48)))
    _rect(canvas, box, inks.accent, 0.40, 0.62, 0.20, 0.32)


def _paint_bulb(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a light bulb.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.50, 0.38, 0.30)
    _rect(canvas, box, inks.accent, 0.36, 0.64, 0.28, 0.08)
    _rect(canvas, box, inks.accent, 0.38, 0.76, 0.24, 0.08)
    _rays(canvas, box, inks.detail, 6, 0.05, 0.36, 0.44)


def _paint_plug(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a charging plug.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _rounded(canvas, box, inks.primary, 0.20, 0.30, 0.60, 0.44, 0.10)
    _rect(canvas, box, inks.accent, 0.32, 0.10, 0.09, 0.24)
    _rect(canvas, box, inks.accent, 0.59, 0.10, 0.09, 0.24)
    _line(canvas, box, inks.primary, 0.50, 0.74, 0.50, 0.96, 0.10)


def _paint_car(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a car in side view.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.04, 0.62), (0.16, 0.36), (0.62, 0.36), (0.86, 0.56), (0.96, 0.62), (0.96, 0.78), (0.04, 0.78)))
    _disc(canvas, box, inks.accent, 0.26, 0.80, 0.13)
    _disc(canvas, box, inks.accent, 0.74, 0.80, 0.13)
    _rect(canvas, box, inks.detail, 0.26, 0.42, 0.28, 0.14)


def _paint_lock(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a padlock.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.50, 0.34, 0.24, 0.09)
    _rounded(canvas, box, inks.primary, 0.16, 0.42, 0.68, 0.52, 0.10)
    _cut(canvas, box, 0.50, 0.62, 0.07)
    _rect(canvas, box, inks.accent, 0.46, 0.62, 0.08, 0.18)


def _paint_shield(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a shield with a check.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _polygon(canvas, box, inks.primary, ((0.50, 0.04), (0.94, 0.20), (0.86, 0.62), (0.50, 0.96), (0.14, 0.62), (0.06, 0.20)))
    _line(canvas, box, inks.accent, 0.30, 0.48, 0.44, 0.62, 0.09)
    _line(canvas, box, inks.accent, 0.44, 0.62, 0.70, 0.32, 0.09)


def _paint_key(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a key.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _ring(canvas, box, inks.primary, 0.30, 0.30, 0.24, 0.10)
    _line(canvas, box, inks.primary, 0.44, 0.44, 0.90, 0.90, 0.11)
    _rect(canvas, box, inks.accent, 0.68, 0.62, 0.16, 0.08)
    _rect(canvas, box, inks.accent, 0.80, 0.74, 0.12, 0.08)


def _paint_disc(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a disc with a cut ring and an open hub.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _disc(canvas, box, inks.primary, 0.50, 0.50, 0.46)
    _cut(canvas, box, 0.50, 0.50, 0.31)
    _disc(canvas, box, inks.primary, 0.50, 0.50, 0.23)
    _cut(canvas, box, 0.50, 0.50, 0.07)


def _paint_chevron(canvas: Canvas, box: Box, inks: GlyphColors) -> None:
    """Draw a double chevron.

    Args:
        canvas: Sheet the glyph is painted onto.
        box: Centred artwork box the recipe draws inside.
        inks: The three inks the recipe paints with.
"""
    _line(canvas, box, inks.primary, 0.14, 0.08, 0.52, 0.50, 0.12)
    _line(canvas, box, inks.primary, 0.52, 0.50, 0.14, 0.92, 0.12)
    _line(canvas, box, inks.accent, 0.56, 0.08, 0.94, 0.50, 0.12)
    _line(canvas, box, inks.accent, 0.94, 0.50, 0.56, 0.92, 0.12)


# Recipe id -> painter. Every id the catalog may name has to appear here.
GLYPH_RECIPES: dict[str, GlyphPainter] = {
    "alarm": _paint_alarm,
    "bag": _paint_bag,
    "bank": _paint_bank,
    "basket": _paint_basket,
    "bed": _paint_bed,
    "blocks": _paint_blocks,
    "board": _paint_board,
    "bolt": _paint_bolt,
    "book": _paint_book,
    "bookshelf": _paint_bookshelf,
    "bulb": _paint_bulb,
    "calc": _paint_calc,
    "calendar": _paint_calendar,
    "camera": _paint_camera,
    "cap": _paint_cap,
    "car": _paint_car,
    "chart": _paint_chart,
    "check": _paint_check,
    "clock": _paint_clock,
    "cloud": _paint_cloud,
    "code": _paint_code,
    "coin": _paint_coin,
    "compass": _paint_compass,
    "cross": _paint_cross,
    "cup": _paint_cup,
    "chevron": _paint_chevron,
    "disc": _paint_disc,
    "dot_path": _paint_dot_path,
    "dumbbell": _paint_dumbbell,
    "envelope": _paint_envelope,
    "film": _paint_film,
    "folder": _paint_folder,
    "fork": _paint_fork,
    "gallery": _paint_gallery,
    "gallery_stack": _paint_gallery_stack,
    "gamepad": _paint_gamepad,
    "gear": _paint_gear,
    "gift": _paint_gift,
    "globe": _paint_globe,
    "heart": _paint_heart,
    "house": _paint_house,
    "key": _paint_key,
    "leaf": _paint_leaf,
    "lock": _paint_lock,
    "map": _paint_map,
    "mic": _paint_mic,
    "news": _paint_news,
    "note": _paint_note,
    "notes": _paint_notes,
    "pencil": _paint_pencil,
    "people": _paint_people,
    "person": _paint_person,
    "phone": _paint_phone,
    "pin": _paint_pin,
    "plane": _paint_plane,
    "play": _paint_play,
    "plug": _paint_plug,
    "pulse": _paint_pulse,
    "puzzle": _paint_puzzle,
    "rain": _paint_rain,
    "ring": _paint_ring,
    "search": _paint_search,
    "share_nodes": _paint_share_nodes,
    "shield": _paint_shield,
    "shoe": _paint_shoe,
    "sliders": _paint_sliders,
    "speech": _paint_speech,
    "speech_pair": _paint_speech_pair,
    "star": _paint_star,
    "sun": _paint_sun,
    "tag": _paint_tag,
    "terminal": _paint_terminal,
    "train": _paint_train,
    "wallet": _paint_wallet,
    "waveform": _paint_waveform,
}


def glyph_recipes() -> tuple[str, ...]:
    """Every registered recipe id.

    Returns:
        Sorted recipe names.
"""
    return tuple(sorted(GLYPH_RECIPES))


def colors_for(palette: Sequence[str], monochrome: bool = False) -> GlyphColors:
    """Turn a palette into the three inks a recipe needs.

    Args:
        palette: Hex colours, primary first. A one- or two-colour palette has
            its missing inks reused from the last colour given.
        monochrome: Render as a themed-icon silhouette: everything primary,
            the secondary inks cut away instead of painted.

    Returns:
        Inks ready for a recipe.

    Raises:
        ValueError: the palette is empty or a colour is not hex.
"""
    if not palette:
        raise ValueError("palette is empty")
    parsed = [hex_to_rgba(colour) for colour in palette]
    primary = parsed[0]
    accent = parsed[1] if len(parsed) > 1 else primary
    detail = parsed[2] if len(parsed) > 2 else accent
    if monochrome:
        return GlyphColors(primary=_MONO_PRIMARY, accent=_MONO_CUT, detail=_MONO_CUT)
    return GlyphColors(primary=primary, accent=accent, detail=detail)


def render_foreground(spec: IconSpec, size: int = DEFAULT_SHEET_PX) -> Canvas:
    """Render the adaptive foreground layer.

    Args:
        spec: Catalog entry.
        size: Sheet edge in pixels.

    Returns:
        Transparent sheet with the glyph fitted inside the safe zone.

    Raises:
        ValueError: the recipe id is unknown or a colour is not hex.
"""
    painter = GLYPH_RECIPES.get(spec.glyph)
    if painter is None:
        raise ValueError(f"unknown glyph {spec.glyph!r} for {spec.slug!r}")
    canvas = Canvas(size, size, TRANSPARENT)
    painter(canvas, artwork_box(size), colors_for(spec.palette))
    return fit_to_safe_zone(canvas, size)


def render_monochrome(spec: IconSpec, size: int = DEFAULT_SHEET_PX) -> Canvas:
    """Render the monochrome layer a themed icon needs.

    A single-colour silhouette on a transparent sheet, which is what
    AEP-TI-GAA requires for themed icons.

    Args:
        spec: Catalog entry.
        size: Sheet edge in pixels.

    Returns:
        Transparent sheet carrying the white silhouette.

    Raises:
        ValueError: the recipe id is unknown.
"""
    painter = GLYPH_RECIPES.get(spec.glyph)
    if painter is None:
        raise ValueError(f"unknown glyph {spec.glyph!r} for {spec.slug!r}")
    canvas = Canvas(size, size, TRANSPARENT)
    painter(canvas, artwork_box(size), colors_for(spec.palette, monochrome=True))
    return fit_to_safe_zone(canvas, size)


def render_background(spec: IconSpec, size: int = DEFAULT_SHEET_PX) -> Canvas:
    """Render the adaptive background layer.

    Args:
        spec: Catalog entry.
        size: Sheet edge in pixels.

    Returns:
        Opaque sheet painted solid, as a vertical gradient, or as a vignette.
"""
    parsed = spec.parsed_background
    canvas = Canvas(size, size, hex_to_rgba(parsed.top))
    if parsed.style == "solid":
        return canvas
    top = hex_to_rgba(parsed.top)
    bottom = hex_to_rgba(parsed.bottom)
    if parsed.style == "linear":
        for row in range(size):
            fraction = row / max(1, size - 1)
            canvas.fill_rect(0, row, size, 1, _mix(top, bottom, fraction))
    else:
        centre = (size - 1) / 2.0
        reach = max(1.0, math.hypot(centre, centre))
        for row in range(size):
            for column in range(size):
                distance = math.hypot(column - centre, row - centre) / reach
                canvas.set_pixel(column, row, _mix(top, bottom, min(1.0, distance * 1.4)))
    return canvas


def render_legacy(spec: IconSpec, size: int = 48, master: str | None = None) -> Canvas:
    """Render a composited legacy launcher tile.

    Optional: a pack that ships adaptive layers everywhere still writes these
    for launchers that only read the plain mipmap tree.

    Args:
        spec: Catalog entry.
        size: Tile edge in pixels.
        master: Path to operator master art; the glyph is used when None.

    Returns:
        Rounded-square tile with the corners cut away.

    Raises:
        ValueError: the recipe id is unknown.
"""
    base = render_background(spec, size)
    front = render_master(master, size) if master is not None else render_foreground(spec, size)
    composited = front.composited_over(base)
    mask = Canvas(size, size, BLACK)
    _rounded(mask, legacy_box(size), WHITE, 0.0, 0.0, 1.0, 1.0, LEGACY_CORNER_RATIO)
    return composited.masked(mask)


def fit_to_safe_zone(canvas: Canvas, size: int) -> Canvas:
    """Crop, scale, and re-centre a sheet's artwork into the safe zone.

    Every glyph, generated or dropped in by the operator, passes through
    here. That is what makes the digest's 48 dp floor and 66 dp ceiling hold
    for a recipe nobody has reviewed yet: the longest edge of the artwork
    lands on :data:`ARTWORK_TARGET_DP`, centred on the sheet.

    Args:
        canvas: Sheet carrying artwork.
        size: Sheet edge in pixels.

    Returns:
        A new sheet whose artwork is centred and fitted; a sheet with no
        visible pixel comes back unchanged.
"""
    bounds = artwork_bounds(canvas)
    if bounds is None:
        return canvas
    left, top, right, bottom = bounds
    width = right - left + 1
    height = bottom - top + 1
    stride = width * 4
    block = bytearray(stride * height)
    for row in range(height):
        start = ((top + row) * canvas.width + left) * 4
        block[row * stride : (row + 1) * stride] = canvas.pixels[start : start + stride]
    edge = max(1, round(size * ARTWORK_TARGET_DP / SHEET_DP))
    scale = edge / max(width, height)
    target_width = max(1, round(width * scale))
    target_height = max(1, round(height * scale))
    scaled = from_rgba_bytes(bytes(block), width, height).resampled(target_width, target_height)
    sheet = Canvas(size, size, TRANSPARENT)
    offset_x = (size - target_width) // 2
    offset_y = (size - target_height) // 2
    row_bytes = target_width * 4
    for row in range(target_height):
        start = row * row_bytes
        stop = ((offset_y + row) * size + offset_x) * 4
        sheet.pixels[stop : stop + row_bytes] = scaled.pixels[start : start + row_bytes]
    return sheet


def render_master(path: str, size: int = DEFAULT_SHEET_PX) -> Canvas:
    """Render operator master art into the safe zone.

    The file is decoded through :func:`ez_raster.decode_rgba`, so any format
    ffmpeg reads works, and then fitted, so an oversized or loosely cropped
    drop-in can never bleed past the 66 dp safe zone.

    Args:
        path: Master art path.
        size: Sheet edge in pixels.

    Returns:
        Transparent sheet carrying the artwork.

    Raises:
        RasterError: ffmpeg is missing or refused the file.
"""
    return fit_to_safe_zone(decode_rgba(path, size), size)


def artwork_bounds(canvas: Canvas) -> tuple[int, int, int, int] | None:
    """Measure the opaque extent of a layer.

    This is how the validator checks the digest's promise that artwork stays
    between 48 dp and 66 dp inside the 108 dp sheet.

    Args:
        canvas: Layer to measure.

    Returns:
        ``(left, top, right, bottom)`` in pixels, or None when the canvas
        carries no visible pixel at all.
"""
    left = canvas.width
    top = canvas.height
    right = -1
    bottom = -1
    pixels = canvas.pixels
    for row in range(canvas.height):
        for column in range(canvas.width):
            if pixels[(row * canvas.width + column) * 4 + 3] < 8:
                continue
            left = min(left, column)
            right = max(right, column)
            top = min(top, row)
            bottom = max(bottom, row)
    if right < left or bottom < top:
        return None
    return (left, top, right, bottom)


def _mix(top: Rgba, bottom: Rgba, fraction: float) -> Rgba:
    """Blend two colours linearly.

    Args:
        top: Colour at fraction 0.
        bottom: Colour at fraction 1.
        fraction: Blend position, 0.0 to 1.0.

    Returns:
        The blended colour, keeping the top alpha.
"""
    edge = min(1.0, max(0.0, fraction))
    return Rgba(
        red=round(top.red + (bottom.red - top.red) * edge),
        green=round(top.green + (bottom.green - top.green) * edge),
        blue=round(top.blue + (bottom.blue - top.blue) * edge),
        alpha=top.alpha,
    )
