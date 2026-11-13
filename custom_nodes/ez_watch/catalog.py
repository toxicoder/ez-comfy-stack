"""Sellable Wear OS watch face catalog: styles, colourways, complication slots.

Every face an operator sells is data here, so a face can be retuned or added
with a JSON override file instead of a Python edit. Constants that encode a
published Wear or Play rule name the rule they come from; the digest this pack
implements is the Wear OS watch face requirements note.

Hermetic at import: stdlib plus :mod:`ez_common.json_value`. No nodes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ez_common.json_value import Json, JsonMap, JsonObject

STYLE_ANALOG = "analog"
"""Hand-and-dial face: the time is read from the hand angles."""

STYLE_DIGITAL = "digital"
"""Numeric face: the time is rendered as digits."""

STYLE_HYBRID = "hybrid"
"""Hands for the hour and minute plus a numeric read-out."""

STYLE_COMPLICATION = "complication-forward"
"""Sparse dial whose data density comes from complication slots."""

STYLES: tuple[str, ...] = (
    STYLE_ANALOG,
    STYLE_DIGITAL,
    STYLE_HYBRID,
    STYLE_COMPLICATION,
)
"""The four layouts this catalog can emit."""

SHAPE_ROUND = "round"
"""Circular face; ``clipShape="CIRCLE"``."""

SHAPE_SQUARE = "square"
"""Equal-sided face; ``clipShape="RECTANGLE"`` with round corners."""

SHAPE_RECT = "rect"
"""Tall rectangle for the non-square Wear displays."""

SHAPES: tuple[str, ...] = (SHAPE_ROUND, SHAPE_SQUARE, SHAPE_RECT)
"""The three shapes an operator can pick."""

COMPLICATION_TYPES: tuple[str, ...] = (
    "SHORT_TEXT",
    "LONG_TEXT",
    "MONOCHROMATIC_IMAGE",
    "SMALL_IMAGE",
    "PHOTO_IMAGE",
    "RANGED_VALUE",
    "EMPTY",
)
"""``ComplicationSlot supportedTypes`` enum, per the WFF reference page."""

MAX_COMPLICATION_SLOTS = 8
"""WO-P10: a watch face may declare no more than eight complication slots."""

MAX_COLOR_OPTIONS = 100
"""``ColorConfiguration`` accepts between 1 and 100 ``ColorOption`` children."""

DESIGN_EDGE_MIN_DP = 192
"""WO-V16: the design must fill at least a 192 dp circle."""

DESIGN_EDGE_LARGE_DP = 227
"""The large round reference emulator is 227 dp; layout must survive both."""

DEFAULT_DESIGN_EDGE = 450
"""Virtual screen edge used when a face does not state one.

``<WatchFace width/height>`` is the visual screen, not physical pixels, so one
450 x 450 design scales onto every device.
"""

DEFAULT_STEP_GOAL = 10000
"""``Metadata`` ``STEP_GOAL`` value emitted for faces with a step slot."""

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
"""Package-safe slug shape."""

_REQUIRED_ROW_KEYS: frozenset[str] = frozenset(
    {"slug", "name", "style", "shape", "palette"}
)
"""Keys a row must carry when it introduces a face the catalog does not know."""

_KNOWN_ROW_KEYS: frozenset[str] = frozenset(
    {
        "ambient_minimal",
        "background",
        "category",
        "complications",
        "design_edge",
        "name",
        "palette",
        "shape",
        "show_battery",
        "show_date",
        "show_hands",
        "show_step_complication",
        "show_ticks",
        "slug",
        "style",
        "tags",
        "typography",
    }
)
"""Every key an override row may use; anything else is a typo."""


@dataclass(frozen=True)
class ThemePalette:
    """One selectable colourway offered in the watch face editor.

    Attributes:
        name: Colourway name; also seeds the string resource name.
        colors: Hex strings (``#RGB`` or ``#RRGGBB``) written out as the
            space-separated ARGB list ``ColorOption colors=`` wants.
    """

    name: str
    colors: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject a colourway that cannot render.

        Raises:
            ValueError: the name is blank or no colours were given.
        """
        if self.name.strip() == "":
            raise ValueError("theme name is empty")
        if not self.colors:
            raise ValueError(f"theme {self.name!r} has no colors")


@dataclass(frozen=True)
class ComplicationSlotSpec:
    """Where a user-addible complication sits and what it can render.

    Attributes:
        slot_id: Unique numeric id, required by ``ComplicationSlot slotId``.
        x: Left edge in visual-screen pixels.
        y: Top edge in visual-screen pixels.
        width: Slot width in visual-screen pixels.
        height: Slot height in visual-screen pixels.
        supported_types: Entries from :data:`COMPLICATION_TYPES`.
    """

    slot_id: int
    x: int
    y: int
    width: int
    height: int
    supported_types: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject a slot the renderer would refuse.

        Raises:
            ValueError: the id or box is not positive, or a type is unknown.
        """
        if self.slot_id < 1:
            raise ValueError(f"slot_id must be >= 1, got {self.slot_id}")
        if self.width < 1 or self.height < 1:
            raise ValueError(
                f"slot {self.slot_id} box must be positive, "
                f"got {self.width}x{self.height}"
            )
        if not self.supported_types:
            raise ValueError(f"slot {self.slot_id} declares no types")
        for kind in self.supported_types:
            if kind not in COMPLICATION_TYPES:
                raise ValueError(f"slot {self.slot_id} has unknown type {kind!r}")


@dataclass(frozen=True)
class Typography:
    """Type used for every ``PartText`` in one face.

    Attributes:
        family: WFF font family name, resolved against the device fonts.
        time_size: Point size for the time read-out.
        label_size: Point size for labels, dates, and complication text.
    """

    family: str
    time_size: int
    label_size: int

    def __post_init__(self) -> None:
        """Reject type the renderer cannot size.

        Raises:
            ValueError: the family is blank or a size is not positive.
        """
        if self.family.strip() == "":
            raise ValueError("font family is empty")
        if self.time_size < 1 or self.label_size < 1:
            raise ValueError("font sizes must be >= 1")


_DEFAULT_TYPOGRAPHY = Typography("sans-serif", 48, 20)
"""Typography used when a new face row omits ``typography``."""


@dataclass(frozen=True)
class WatchFaceSpec:
    """Everything the generator needs to emit one sellable face.

    Attributes:
        slug: Package-safe id; the merge key for an operator override file.
        name: Store-facing name.
        style: One of :data:`STYLES`.
        shape: One of :data:`SHAPES`.
        palette: Colourways offered to the buyer, one ``ColorOption`` each.
        complications: Slots in draw order, at most :data:`MAX_COMPLICATION_SLOTS`.
        typography: Fonts and sizes for every text part.
        show_ticks: Draw the hour ticks around the dial.
        show_hands: Draw the analog hands.
        show_date: Draw the date line.
        show_battery: Offer a battery complication.
        show_step_complication: Offer a step-count complication.
        tags: Store-listing keywords.
        category: Play self-tag and picker category.
        ambient_minimal: Drop decoration to alpha 0 in ambient.
        design_edge: Visual-screen edge in pixels; square faces use it for both
            sides, so the layout is one number.
        background: Opaque scene background, black per WO-V13.
    """

    slug: str
    name: str
    style: str
    shape: str
    palette: tuple[ThemePalette, ...]
    complications: tuple[ComplicationSlotSpec, ...]
    typography: Typography
    show_ticks: bool = True
    show_hands: bool = True
    show_date: bool = True
    show_battery: bool = True
    show_step_complication: bool = False
    tags: tuple[str, ...] = ()
    category: str = "Minimal"
    ambient_minimal: bool = False
    design_edge: int = DEFAULT_DESIGN_EDGE
    background: str = "#000000"

    def __post_init__(self) -> None:
        """Reject a spec the generator could not turn into a valid face.

        Raises:
            ValueError: the slug, style, shape, palette, or slots are malformed.
        """
        if not _SLUG_RE.match(self.slug):
            raise ValueError(f"slug {self.slug!r} must match {_SLUG_RE.pattern}")
        if self.name.strip() == "":
            raise ValueError("name is empty")
        if self.style not in STYLES:
            raise ValueError(f"style {self.style!r} not in {STYLES}")
        if self.shape not in SHAPES:
            raise ValueError(f"shape {self.shape!r} not in {SHAPES}")
        if not self.palette:
            raise ValueError(f"face {self.slug} needs at least one colourway")
        if len(self.palette) > MAX_COLOR_OPTIONS:
            raise ValueError(f"face {self.slug} has over {MAX_COLOR_OPTIONS} themes")
        if len(self.complications) > MAX_COMPLICATION_SLOTS:
            raise ValueError(f"face {self.slug} has over {MAX_COMPLICATION_SLOTS} slots")
        if self.design_edge < 1:
            raise ValueError(f"design_edge must be >= 1, got {self.design_edge}")
        seen: set[int] = set()
        for slot in self.complications:
            if slot.slot_id in seen:
                raise ValueError(f"face {self.slug} repeats slot_id {slot.slot_id}")
            seen.add(slot.slot_id)

    @property
    def configurable(self) -> bool:
        """True when the face exposes at least one editor setting.

        Returns:
            Whether ``watch_face_info.xml`` must carry ``Editable value="true"``.
        """
        return bool(self.palette) or self.show_ticks or self.show_date or self.show_battery


def _slot(
    slot_id: int,
    x: int,
    y: int,
    width: int,
    height: int,
    *types: str,
) -> ComplicationSlotSpec:
    """Compact spell for one complication slot.

    Args:
        slot_id: Unique numeric id.
        x: Left edge.
        y: Top edge.
        width: Slot width.
        height: Slot height.
        *types: Supported complication type names.

    Returns:
        The slot spec.
    """
    return ComplicationSlotSpec(
        slot_id=slot_id,
        x=x,
        y=y,
        width=width,
        height=height,
        supported_types=tuple(types),
    )


def _theme(name: str, *colors: str) -> ThemePalette:
    """Compact spell for one colourway.

    Args:
        name: Colourway name.
        *colors: Hex colour strings.

    Returns:
        The theme palette.
    """
    return ThemePalette(name=name, colors=tuple(colors))


def _type(family: str, time_size: int, label_size: int) -> Typography:
    """Compact spell for the face typography.

    Args:
        family: WFF font family name.
        time_size: Time read-out size.
        label_size: Label size.

    Returns:
        The typography record.
    """
    return Typography(family=family, time_size=time_size, label_size=label_size)


# Thirteen faces: four analog, three digital, three hybrid, three
# complication-forward, across round, square, and rect. Each carries several
# colourways so the set can be sold as-is with the permutations Play asks for.
WATCH_FACE_CATALOG: tuple[WatchFaceSpec, ...] = (
    WatchFaceSpec(
        slug="aurora-analog",
        name="Aurora Analog",
        style=STYLE_ANALOG,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Ember", "#FF7A18", "#FFC94D", "#FFF3E0"),
            _theme("Aurora", "#2BE0B7", "#7CFFCB", "#E8FFF8"),
            _theme("Cobalt", "#3D7BFF", "#9EC2FF", "#EEF4FF"),
        ),
        complications=(
            _slot(1, 168, 132, 114, 46, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 168, 274, 114, 46, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
            _slot(3, 60, 205, 74, 40, "SHORT_TEXT", "EMPTY"),
        ),
        typography=_type("sans-serif-light", 34, 20),
        show_step_complication=True,
        tags=("analog", "minimal", "elegant"),
        category="Minimal",
    ),
    WatchFaceSpec(
        slug="foundry-analog",
        name="Foundry Analog",
        style=STYLE_ANALOG,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Brass", "#D6A24A", "#F2D498", "#FFF8EA"),
            _theme("Iron", "#9AA4AF", "#D5DBE0", "#FFFFFF"),
            _theme("Oxide", "#C05621", "#F0A170", "#FFF1E6"),
            _theme("Slate", "#5C6B73", "#A7B8C0", "#EFF3F5"),
        ),
        complications=(
            _slot(1, 176, 246, 98, 40, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 66, 202, 70, 40, "SHORT_TEXT", "SMALL_IMAGE"),
            _slot(3, 314, 202, 70, 40, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
        ),
        typography=_type("serif", 30, 18),
        show_step_complication=True,
        tags=("analog", "industrial", "serif"),
        category="Classic",
    ),
    WatchFaceSpec(
        slug="lumen-analog",
        name="Lumen Analog",
        style=STYLE_ANALOG,
        shape=SHAPE_SQUARE,
        palette=(
            _theme("Neon", "#00E5FF", "#7CFFCB", "#FFFFFF"),
            _theme("Magenta", "#FF3D81", "#FF9EC4", "#FFF0F6"),
        ),
        complications=(
            _slot(1, 60, 300, 330, 52, "SHORT_TEXT", "LONG_TEXT"),
            _slot(2, 60, 96, 90, 46, "RANGED_VALUE", "SHORT_TEXT"),
        ),
        typography=_type("sans-serif-medium", 32, 20),
        show_hands=True,
        tags=("analog", "square", "neon"),
        category="Sport",
    ),
    WatchFaceSpec(
        slug="meridian-analog",
        name="Meridian Analog",
        style=STYLE_ANALOG,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Gold", "#E0B155", "#F7E0A8", "#FFFBF0"),
            _theme("Silver", "#B8C2CC", "#EBF0F5", "#FFFFFF"),
            _theme("Jade", "#3FBF8F", "#A5F0CE", "#EEFFF8"),
        ),
        complications=(
            _slot(1, 186, 150, 78, 34, "SHORT_TEXT", "EMPTY"),
            _slot(2, 186, 268, 78, 34, "SHORT_TEXT", "EMPTY"),
        ),
        typography=_type("sans-serif-condensed", 26, 16),
        show_battery=False,
        ambient_minimal=True,
        tags=("analog", "dress", "dressy"),
        category="Classic",
    ),
    WatchFaceSpec(
        slug="signal-digital",
        name="Signal Digital",
        style=STYLE_DIGITAL,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Terminal", "#39FF6A", "#B7FFC9", "#F0FFF4"),
            _theme("Amber", "#FFB000", "#FFD97A", "#FFF8E7"),
            _theme("Ice", "#7FD4FF", "#D3EEFF", "#FFFFFF"),
        ),
        complications=(
            _slot(1, 150, 280, 150, 44, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 150, 66, 150, 40, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
        ),
        typography=_type("sans-serif", 92, 22),
        show_ticks=False,
        show_hands=False,
        show_step_complication=True,
        tags=("digital", "retro", "bold"),
        category="Retro",
    ),
    WatchFaceSpec(
        slug="tally-digital",
        name="Tally Digital",
        style=STYLE_DIGITAL,
        shape=SHAPE_RECT,
        palette=(
            _theme("Paper", "#F2F2F2", "#B7B7B7", "#FFFFFF"),
            _theme("Ink", "#8AA1FF", "#C7D2FF", "#FFFFFF"),
        ),
        complications=(
            _slot(1, 96, 280, 208, 48, "SHORT_TEXT", "LONG_TEXT"),
            _slot(2, 96, 66, 96, 40, "SHORT_TEXT", "SMALL_IMAGE"),
            _slot(3, 208, 66, 96, 40, "RANGED_VALUE", "SHORT_TEXT"),
        ),
        typography=_type("sans-serif-light", 108, 24),
        design_edge=400,
        show_ticks=False,
        show_hands=False,
        tags=("digital", "tall", "clean"),
        category="Minimal",
    ),
    WatchFaceSpec(
        slug="vector-digital",
        name="Vector Digital",
        style=STYLE_DIGITAL,
        shape=SHAPE_SQUARE,
        palette=(
            _theme("Volt", "#C6FF00", "#EBFF9E", "#FFFFFF"),
            _theme("Cyan", "#00D8FF", "#A6F0FF", "#FFFFFF"),
            _theme("Coral", "#FF6B4A", "#FFC0AE", "#FFF4F1"),
        ),
        complications=(
            _slot(1, 72, 268, 306, 56, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 72, 76, 96, 44, "SHORT_TEXT", "EMPTY"),
        ),
        typography=_type("sans-serif-black", 86, 22),
        show_ticks=False,
        show_hands=False,
        tags=("digital", "square", "sport"),
        category="Sport",
    ),
    WatchFaceSpec(
        slug="harbor-hybrid",
        name="Harbor Hybrid",
        style=STYLE_HYBRID,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Nautical", "#4FA3FF", "#B5D8FF", "#F2F8FF"),
            _theme("Sunset", "#FF8A3D", "#FFD1A8", "#FFF6EE"),
            _theme("Kelp", "#4CC38A", "#B4F0D5", "#EFFFF8"),
        ),
        complications=(
            _slot(1, 74, 196, 84, 40, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 292, 196, 84, 40, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
            _slot(3, 168, 322, 114, 44, "SHORT_TEXT", "LONG_TEXT"),
        ),
        typography=_type("sans-serif-medium", 44, 20),
        show_step_complication=True,
        tags=("hybrid", "hands", "data"),
        category="Classic",
    ),
    WatchFaceSpec(
        slug="atrium-hybrid",
        name="Atrium Hybrid",
        style=STYLE_HYBRID,
        shape=SHAPE_SQUARE,
        palette=(
            _theme("Marble", "#E8E8E8", "#A8A8A8", "#FFFFFF"),
            _theme("Bronze", "#CD9B5A", "#EAD1A8", "#FFF8EE"),
        ),
        complications=(
            _slot(1, 66, 332, 318, 54, "SHORT_TEXT", "LONG_TEXT"),
            _slot(2, 66, 92, 100, 44, "SHORT_TEXT", "SMALL_IMAGE"),
        ),
        typography=_type("serif-monospace", 52, 20),
        show_ticks=True,
        tags=("hybrid", "square", "architecture"),
        category="Classic",
    ),
    WatchFaceSpec(
        slug="transit-hybrid",
        name="Transit Hybrid",
        style=STYLE_HYBRID,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Rip", "#FFD400", "#FFF0A6", "#FFFDF0"),
            _theme("Lane", "#00C2A8", "#9DF0E2", "#F0FFFC"),
            _theme("Signal", "#FF5A5F", "#FFB6B8", "#FFF3F3"),
        ),
        complications=(
            _slot(1, 156, 118, 138, 40, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 156, 328, 138, 40, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
        ),
        typography=_type("sans-serif-condensed-medium", 48, 18),
        show_ticks=False,
        ambient_minimal=True,
        tags=("hybrid", "commute", "legible"),
        category="Sport",
    ),
    WatchFaceSpec(
        slug="ledger-forward",
        name="Ledger Forward",
        style=STYLE_COMPLICATION,
        shape=SHAPE_ROUND,
        palette=(
            _theme("Graphite", "#C9D1D9", "#8B949E", "#FFFFFF"),
            _theme("Teal", "#2DD4BF", "#A5F3E4", "#F0FFFC"),
            _theme("Plum", "#C084FC", "#E9D5FF", "#FBF5FF"),
        ),
        complications=(
            _slot(1, 150, 164, 150, 46, "SHORT_TEXT", "LONG_TEXT"),
            _slot(2, 84, 220, 110, 46, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(3, 256, 220, 110, 46, "SHORT_TEXT", "SMALL_IMAGE"),
            _slot(4, 150, 276, 150, 46, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
            _slot(5, 310, 164, 56, 34, "EMPTY"),
        ),
        typography=_type("sans-serif-light", 64, 18),
        show_ticks=False,
        show_hands=False,
        show_step_complication=True,
        tags=("complications", "data", "dashboard"),
        category="Dashboard",
    ),
    WatchFaceSpec(
        slug="atrium-forward",
        name="Atrium Forward",
        style=STYLE_COMPLICATION,
        shape=SHAPE_RECT,
        palette=(
            _theme("Chalk", "#F5F5F5", "#BABABA", "#FFFFFF"),
            _theme("Olive", "#A3B565", "#DCE7B4", "#F7FBEA"),
        ),
        complications=(
            _slot(1, 90, 196, 220, 44, "SHORT_TEXT", "LONG_TEXT"),
            _slot(2, 90, 250, 104, 44, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(3, 206, 250, 104, 44, "SHORT_TEXT", "SMALL_IMAGE"),
            _slot(4, 90, 304, 104, 44, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
            _slot(5, 206, 304, 104, 44, "LONG_TEXT", "EMPTY"),
            _slot(6, 334, 196, 56, 44, "SHORT_TEXT", "EMPTY"),
        ),
        typography=_type("sans-serif", 96, 20),
        design_edge=400,
        show_ticks=False,
        show_hands=False,
        tags=("complications", "tall", "dashboard"),
        category="Dashboard",
    ),
    WatchFaceSpec(
        slug="cadence-forward",
        name="Cadence Forward",
        style=STYLE_COMPLICATION,
        shape=SHAPE_SQUARE,
        palette=(
            _theme("Track", "#F25C05", "#FFB27A", "#FFF3E9"),
            _theme("Pace", "#12B5A5", "#9BE8DE", "#F0FFFD"),
            _theme("Split", "#8B5CF6", "#D6BCFA", "#F8F4FF"),
        ),
        complications=(
            _slot(1, 64, 156, 322, 54, "SHORT_TEXT", "RANGED_VALUE"),
            _slot(2, 64, 220, 156, 54, "SHORT_TEXT", "MONOCHROMATIC_IMAGE"),
            _slot(3, 230, 220, 156, 54, "SHORT_TEXT", "SMALL_IMAGE"),
            _slot(4, 64, 284, 322, 54, "LONG_TEXT", "EMPTY"),
            _slot(5, 64, 348, 156, 44, "RANGED_VALUE", "SHORT_TEXT"),
        ),
        typography=_type("sans-serif-medium", 58, 20),
        show_ticks=False,
        show_hands=False,
        show_step_complication=True,
        tags=("complications", "fitness", "square"),
        category="Sport",
    ),
)


def faces_for(style: str) -> tuple[WatchFaceSpec, ...]:
    """Every catalog face laid out one way.

    Args:
        style: One of :data:`STYLES`.

    Returns:
        Catalog faces in catalog order.

    Raises:
        ValueError: the style is not one this catalog emits.
    """
    if style not in STYLES:
        raise ValueError(f"style {style!r} not in {STYLES}")
    return tuple(face for face in WATCH_FACE_CATALOG if face.style == style)


def by_slug(slug: str) -> WatchFaceSpec:
    """Look one catalog face up by slug.

    Args:
        slug: Catalog slug.

    Returns:
        The matching spec.

    Raises:
        ValueError: no catalog face carries that slug.
    """
    for face in WATCH_FACE_CATALOG:
        if face.slug == slug:
            return face
    raise ValueError(f"unknown watch face slug {slug!r}")


def categories() -> tuple[str, ...]:
    """Self-tag categories the catalog uses.

    Returns:
        Sorted unique ``category`` values, ready for a Play self-tag list.
    """
    return tuple(sorted({face.category for face in WATCH_FACE_CATALOG}))


def _as_str(row: JsonMap, key: str, default: str = "") -> str:
    """Read a required-or-defaulted string field out of a parsed row.

    Args:
        row: Parsed override row.
        key: Field name.
        default: Value used when the key is absent.

    Returns:
        The stripped string.

    Raises:
        ValueError: the key holds something that is not a string.
    """
    value = row.get(key)
    if value is None and key not in row:
        return default
    if isinstance(value, str):
        return value.strip()
    raise ValueError(f"{key} must be a string, got {type(value).__name__}")


def _as_int(row: JsonMap, key: str, default: int) -> int:
    """Read an integer field out of a parsed row.

    Args:
        row: Parsed override row.
        key: Field name.
        default: Value used when the key is absent.

    Returns:
        The integer.

    Raises:
        ValueError: the key holds a non-int or a boolean.
    """
    value = row.get(key)
    if value is None and key not in row:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer, got {value!r}")
    return value


def _as_bool(row: JsonMap, key: str, default: bool) -> bool:
    """Read a boolean field out of a parsed row.

    Args:
        row: Parsed override row.
        key: Field name.
        default: Value used when the key is absent.

    Returns:
        The flag.

    Raises:
        ValueError: the key holds neither a bool nor a yes/no string.
    """
    value = row.get(key)
    if value is None and key not in row:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    raise ValueError(f"{key} must be a boolean, got {value!r}")


def _as_strings(row: JsonMap, key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Read a list-of-strings field out of a parsed row.

    Args:
        row: Parsed override row.
        key: Field name.
        default: Value used when the key is absent.

    Returns:
        The strings, trimmed.

    Raises:
        ValueError: the key is not a list of strings.
    """
    value = row.get(key)
    if value is None and key not in row:
        return default
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list, got {type(value).__name__}")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} must hold strings, got {item!r}")
        out.append(item.strip())
    return tuple(out)


def _as_rows(row: JsonMap, key: str) -> tuple[JsonMap, ...]:
    """Read a list-of-objects field out of a parsed row.

    Args:
        row: Parsed override row.
        key: Field name.

    Returns:
        The child rows; empty when the key is absent.

    Raises:
        ValueError: the key is not a list of objects.
    """
    value = row.get(key)
    if value is None and key not in row:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list, got {type(value).__name__}")
    out: list[JsonMap] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{key} must hold objects, got {item!r}")
        out.append(item)
    return tuple(out)


def _themes_from_row(row: JsonMap, default: tuple[ThemePalette, ...]) -> tuple[ThemePalette, ...]:
    """Build the colourway tuple from an override row.

    Args:
        row: Parsed override row.
        default: Colourways used when the row omits ``palette``.

    Returns:
        One palette per ``palette`` entry.

    Raises:
        ValueError: an entry is missing a name or its colours.
    """
    rows = _as_rows(row, "palette")
    if not rows:
        return default
    out: list[ThemePalette] = []
    for entry in rows:
        name = _as_str(entry, "name")
        colors = _as_strings(entry, "colors", ())
        if name == "" or not colors:
            raise ValueError(f"palette entry needs a name and colors, got {entry!r}")
        out.append(ThemePalette(name=name, colors=colors))
    return tuple(out)


def _slots_from_row(
    row: JsonMap,
    default: tuple[ComplicationSlotSpec, ...],
) -> tuple[ComplicationSlotSpec, ...]:
    """Build the slot tuple from an override row.

    Args:
        row: Parsed override row.
        default: Slots used when the row omits ``complications``.

    Returns:
        One slot per ``complications`` entry.
    """
    rows = _as_rows(row, "complications")
    if not rows:
        return default
    out: list[ComplicationSlotSpec] = []
    for entry in rows:
        out.append(
            ComplicationSlotSpec(
                slot_id=_as_int(entry, "slot_id", 0),
                x=_as_int(entry, "x", 0),
                y=_as_int(entry, "y", 0),
                width=_as_int(entry, "width", 0),
                height=_as_int(entry, "height", 0),
                supported_types=_as_strings(entry, "supported_types", ()),
            )
        )
    return tuple(out)


def _typography_from_row(row: JsonMap, default: Typography) -> Typography:
    """Build the typography record from an override row.

    Args:
        row: Parsed override row.
        default: Typography used when the row omits ``typography``.

    Returns:
        The face typography.
    """
    rows = _as_rows(row, "typography")
    if not rows:
        return default
    entry = rows[0]
    return Typography(
        family=_as_str(entry, "family", default.family),
        time_size=_as_int(entry, "time_size", default.time_size),
        label_size=_as_int(entry, "label_size", default.label_size),
    )


def _spec_from_row(row: JsonMap, base: WatchFaceSpec | None) -> WatchFaceSpec:
    """Merge one override row onto a catalog face, or build a new face.

    Args:
        row: Parsed override row.
        base: Catalog face with the same slug, or None for a new face.

    Returns:
        The merged spec.

    Raises:
        ValueError: the row uses an unknown key, or a new face omits a
            required key.
    """
    unknown = sorted(set(row) - _KNOWN_ROW_KEYS)
    if unknown:
        raise ValueError(f"row {row.get('slug')!r} has unknown keys {unknown}")
    if base is None:
        missing = sorted(_REQUIRED_ROW_KEYS - set(row))
        if missing:
            raise ValueError(f"new face row is missing required keys {missing}")
    return WatchFaceSpec(
        slug=_as_str(row, "slug", base.slug if base else ""),
        name=_as_str(row, "name", base.name if base else ""),
        style=_as_str(row, "style", base.style if base else ""),
        shape=_as_str(row, "shape", base.shape if base else ""),
        palette=_themes_from_row(row, base.palette if base else ()),
        complications=_slots_from_row(row, base.complications if base else ()),
        typography=_typography_from_row(row, base.typography if base else _DEFAULT_TYPOGRAPHY),
        show_ticks=_as_bool(row, "show_ticks", base.show_ticks if base else True),
        show_hands=_as_bool(row, "show_hands", base.show_hands if base else True),
        show_date=_as_bool(row, "show_date", base.show_date if base else True),
        show_battery=_as_bool(row, "show_battery", base.show_battery if base else True),
        show_step_complication=_as_bool(
            row, "show_step_complication", base.show_step_complication if base else False
        ),
        tags=_as_strings(row, "tags", base.tags if base else ()),
        category=_as_str(row, "category", base.category if base else "Minimal"),
        ambient_minimal=_as_bool(
            row, "ambient_minimal", base.ambient_minimal if base else False
        ),
        design_edge=_as_int(row, "design_edge", base.design_edge if base else DEFAULT_DESIGN_EDGE),
        background=_as_str(row, "background", base.background if base else "#000000"),
    )


def _theme_to_row(theme: ThemePalette) -> JsonObject:
    """Serialise one colourway.

    Args:
        theme: Colourway to write.

    Returns:
        A JSON object row.
    """
    return {"name": theme.name, "colors": list(theme.colors)}


def _slot_to_row(slot: ComplicationSlotSpec) -> JsonObject:
    """Serialise one slot.

    Args:
        slot: Slot to write.

    Returns:
        A JSON object row.
    """
    return {
        "slot_id": slot.slot_id,
        "x": slot.x,
        "y": slot.y,
        "width": slot.width,
        "height": slot.height,
        "supported_types": list(slot.supported_types),
    }


def _spec_to_row(spec: WatchFaceSpec) -> JsonObject:
    """Serialise a face with every field spelled out.

    Args:
        spec: Face to write.

    Returns:
        A JSON object row that :func:`load_catalog` reads back unchanged.
    """
    return {
        "slug": spec.slug,
        "name": spec.name,
        "style": spec.style,
        "shape": spec.shape,
        "palette": [_theme_to_row(theme) for theme in spec.palette],
        "complications": [_slot_to_row(slot) for slot in spec.complications],
        "typography": [
            {
                "family": spec.typography.family,
                "time_size": spec.typography.time_size,
                "label_size": spec.typography.label_size,
            }
        ],
        "show_ticks": spec.show_ticks,
        "show_hands": spec.show_hands,
        "show_date": spec.show_date,
        "show_battery": spec.show_battery,
        "show_step_complication": spec.show_step_complication,
        "tags": list(spec.tags),
        "category": spec.category,
        "ambient_minimal": spec.ambient_minimal,
        "design_edge": spec.design_edge,
        "background": spec.background,
    }


def load_catalog(path: Path | str) -> tuple[WatchFaceSpec, ...]:
    """Read an operator override file and merge it into the catalog by slug.

    A row whose slug the catalog knows replaces only the keys it states; a row
    with a new slug adds a face and must state every required key.

    Args:
        path: JSON file, either a list of rows or an object with a
            ``watch_faces`` list.

    Returns:
        The catalog with overrides applied, in catalog order with new faces
        appended.

    Raises:
        ValueError: the file cannot be read, is not JSON, or holds a malformed
            row.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read catalog {path}: {exc}") from exc
    try:
        payload: Json = json.loads(text)
    except ValueError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if isinstance(payload, dict):
        rows_value: Json = payload.get("watch_faces", [])
    elif isinstance(payload, list):
        rows_value = payload
    else:
        raise ValueError(f"{path} must hold a list or an object with watch_faces")
    if not isinstance(rows_value, list):
        raise ValueError(f"{path}: watch_faces must be a list")
    merged: dict[str, WatchFaceSpec] = {face.slug: face for face in WATCH_FACE_CATALOG}
    order: list[str] = [face.slug for face in WATCH_FACE_CATALOG]
    for item in rows_value:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: each watch face row must be an object")
        slug = item.get("slug")
        if not isinstance(slug, str) or slug.strip() == "":
            raise ValueError(f"{path}: each watch face row needs a slug")
        spec = _spec_from_row(item, merged.get(slug.strip()))
        if slug.strip() not in merged:
            order.append(slug.strip())
        merged[slug.strip()] = spec
    return tuple(merged[slug] for slug in order)


def write_catalog_template(path: Path | str) -> int:
    """Write a worked override example carrying every supported field.

    Args:
        path: Destination ``.json`` path; parents are created.

    Returns:
        Bytes written.
    """
    destination = Path(path)
    example = _spec_to_row(WATCH_FACE_CATALOG[0])
    document = {
        "readme": (
            "Merge these rows over the built-in catalog by slug. A row may "
            "state only the keys it wants to change; a row with a new slug "
            "must state slug, name, style, shape, and palette."
        ),
        "watch_faces": [example],
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    destination.write_bytes(data)
    return len(data)
