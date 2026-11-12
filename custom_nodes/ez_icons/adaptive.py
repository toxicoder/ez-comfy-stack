"""Android adaptive-icon layer sets, the mipmap ladder, and the Play assets.

One entry, one layer set: foreground, background, and monochrome PNGs at the
108 / 162 / 216 / 324 / 432 px adaptive ladder, a composited legacy tile at
the 48 / 72 / 96 / 144 / 192 mipmap ladder, and the
``res/mipmap-anydpi-v26/ic_launcher.xml`` that wires them together. The
``<monochrome>`` child is written unconditionally: AEP-TI-GAA requires it and
publishes no exemption, and a pack without it simply does not qualify for
themed icons.

Every size below is a named constant taken from the verified requirements
digest, and every raster goes through :mod:`ez_raster`, so the bytes are
deterministic and a drift test can pin them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from ez_raster import (
    MIPMAP_DENSITIES,
    PLAY_FEATURE_GRAPHIC_HEIGHT,
    PLAY_FEATURE_GRAPHIC_WIDTH,
    PLAY_LAUNCHER_ICON_PX,
    Canvas,
    Rgba,
    hex_to_rgba,
)

from .catalog import IconSpec
from .glyphs import (
    LEGACY_CORNER_RATIO,
    render_background,
    render_foreground,
    render_legacy,
    render_master,
    render_monochrome,
)

Density: TypeAlias = tuple[str, int]
"""One density bucket and the edge in pixels it expects."""

ADAPTIVE_LADDER: tuple[Density, ...] = (
    ("mdpi", 108),
    ("hdpi", 162),
    ("xhdpi", 216),
    ("xxhdpi", 324),
    ("xxxhdpi", 432),
)
"""Adaptive layer edges: 108 dp scaled by the mdpi density ratio."""

LEGACY_LADDER: tuple[Density, ...] = MIPMAP_DENSITIES
"""Launcher tile edges, straight from :data:`ez_raster.MIPMAP_DENSITIES`."""

PLAY_ICON_PX = PLAY_LAUNCHER_ICON_PX
"""Play Store app icon edge: 512 px, square, alpha allowed."""

PLAY_ICON_MAX_BYTES = 1024 * 1024
"""Play Store app icon ceiling: 1024 KB."""

FEATURE_GRAPHIC_WIDTH = PLAY_FEATURE_GRAPHIC_WIDTH
"""Play feature graphic width: 1024 px."""

FEATURE_GRAPHIC_HEIGHT = PLAY_FEATURE_GRAPHIC_HEIGHT
"""Play feature graphic height: 500 px, and it must carry no transparency."""

LAUNCHER_BASE = "ic_launcher"
"""Resource name of the pack's own launcher icon."""

ADAPTIVE_XML_PATH = "mipmap-anydpi-v26/ic_launcher.xml"
"""Location the adaptive-icon XML is read from (digest: anydpi-v26)."""

ROUND_XML_PATH = "mipmap-anydpi-v26/ic_launcher_round.xml"
"""Round variant of the adaptive-icon XML."""

FEATURE_TILE_COUNT = 5
"""Glyph tiles drawn across the feature graphic."""

_MONOCHROME_ELEMENT = "monochrome"
"""Child that AEP-TI-GAA demands; the validator greps for this name."""


@dataclass(frozen=True)
class IconLayers:
    """What one entry contributed to the res tree.

    Args:
        slug: Catalog slug.
        drawable: Resource name of the launcher tile.
        themed_drawable: Resource name of the monochrome layer.
        files: Paths written, relative to the ``res`` directory, sorted.
        densities: Density buckets written.
        adaptive_sizes: Edges used for the three adaptive layers.
        legacy_sizes: Edges used for the legacy tiles.
        master: Master-art path when the operator supplied one, else None.
    """

    slug: str
    drawable: str
    themed_drawable: str
    files: tuple[str, ...]
    densities: tuple[str, ...]
    adaptive_sizes: tuple[int, ...]
    legacy_sizes: tuple[int, ...]
    master: str | None = None


def layer_filename(base: str, suffix: str) -> str:
    """Resource filename for one layer.

    Args:
        base: Resource name, such as ``ic_launcher``.
        suffix: Layer suffix, such as ``_foreground``; empty for the tile.

    Returns:
        A ``.png`` name an Android resource path can hold.
    """
    return f"{base}{suffix}.png"


def density_dir(prefix: str, density: str) -> str:
    """Qualifier directory name for one density.

    Args:
        prefix: ``drawable`` or ``mipmap``.
        density: Bucket name, such as ``xxhdpi``.

    Returns:
        Something like ``drawable-xxhdpi``.
    """
    return f"{prefix}-{density}"


LayerKind: TypeAlias = str
"""Which of the five rasters a plan row writes."""


def _plan(
    base: str,
    folder_prefix: str,
    round_variant: bool,
    monochrome_suffix: str,
) -> tuple[tuple[str, LayerKind, int], ...]:
    """Every raster one entry owns, as ``(res-relative path, kind, edge)``.

    Both the writer and the dry run read this plan, so the two can never
    disagree about what a pack contains.

    Args:
        base: Resource name for the tile.
        folder_prefix: ``drawable`` or ``mipmap``.
        round_variant: Also plan the round legacy tiles.
        monochrome_suffix: Suffix for the monochrome layer.

    Returns:
        Plan rows, sorted by path.
    """
    rows: list[tuple[str, LayerKind, int]] = []
    for density, edge in ADAPTIVE_LADDER:
        folder = density_dir(folder_prefix, density)
        rows.append((f"{folder}/{layer_filename(base, '_foreground')}", "foreground", edge))
        rows.append((f"{folder}/{layer_filename(base, '_background')}", "background", edge))
        rows.append((f"{folder}/{layer_filename(base, monochrome_suffix)}", "monochrome", edge))
    for density, edge in LEGACY_LADDER:
        folder = density_dir(folder_prefix, density)
        rows.append((f"{folder}/{layer_filename(base, '')}", "legacy", edge))
        if round_variant:
            rows.append((f"{folder}/{layer_filename(base, '_round')}", "legacy_round", edge))
    return tuple(sorted(rows))


def icon_layer_paths(
    base: str,
    folder_prefix: str = "drawable",
    round_variant: bool = False,
    monochrome_suffix: str = "_themed",
) -> tuple[str, ...]:
    """The resource paths :func:`write_icon_set` would write, without writing.

    Args:
        base: Resource name for the tile.
        folder_prefix: ``drawable`` or ``mipmap``.
        round_variant: Include the round legacy tiles.
        monochrome_suffix: Suffix for the monochrome layer.

    Returns:
        Res-relative paths, sorted.
    """
    return tuple(path for path, _, _ in _plan(base, folder_prefix, round_variant, monochrome_suffix))


def write_icon_set(
    spec: IconSpec,
    res_dir: Path | str,
    base: str,
    folder_prefix: str = "drawable",
    master: str | None = None,
    round_variant: bool = False,
    monochrome_suffix: str = "_themed",
) -> IconLayers:
    """Write every raster layer one entry owns.

    Args:
        spec: Catalog entry.
        res_dir: The ``app/src/main/res`` directory.
        base: Resource name for the tile.
        folder_prefix: ``drawable`` for pack icons the launcher resolves by
            name, ``mipmap`` for the pack's own launcher icon.
        master: Operator master art used instead of the generated glyph.
        round_variant: Also write ``<base>_round.png`` legacy tiles.
        monochrome_suffix: Suffix for the monochrome layer; ``_monochrome``
            for the launcher icon, ``_themed`` for a Lawnchair map entry.

    Returns:
        The :class:`IconLayers` record for this entry.

    Raises:
        ValueError: the recipe id is unknown or a colour is not hex.
    """
    root = Path(res_dir)
    written: list[str] = []
    for path, kind, edge in _plan(base, folder_prefix, round_variant, monochrome_suffix):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        written.append(_save(target, _render_kind(spec, kind, edge, master), root))
    return IconLayers(
        slug=spec.slug,
        drawable=base,
        themed_drawable=f"{base}{monochrome_suffix}",
        files=tuple(sorted(written)),
        densities=tuple(density for density, _ in ADAPTIVE_LADDER),
        adaptive_sizes=tuple(edge for _, edge in ADAPTIVE_LADDER),
        legacy_sizes=tuple(edge for _, edge in LEGACY_LADDER),
        master=master,
    )


def _render_kind(spec: IconSpec, kind: LayerKind, edge: int, master: str | None) -> Canvas:
    """Render one planned raster.

    Args:
        spec: Catalog entry.
        kind: Which raster to render: foreground, background, monochrome,
            legacy, or legacy_round.
        edge: Raster edge in pixels.
        master: Operator master art, used for the glyph-carrying layers.

    Returns:
        The finished layer canvas.

    Raises:
        ValueError: the recipe id is unknown or a colour is not hex.
    """
    if kind == "background":
        return render_background(spec, edge)
    if kind == "legacy" or kind == "legacy_round":
        return render_legacy(spec, edge, master)
    if kind == "monochrome":
        return (
            render_master(master, edge)
            if master is not None
            else render_monochrome(spec, edge)
        )
    return render_master(master, edge) if master is not None else render_foreground(spec, edge)


def write_launcher_icon_set(
    spec: IconSpec,
    res_dir: Path | str,
    master: str | None = None,
    round_variant: bool = True,
) -> IconLayers:
    """Write the pack's own launcher icon into the mipmap tree.

    Args:
        spec: Entry used for the pack icon.
        res_dir: The ``app/src/main/res`` directory.
        master: Operator master art for the pack icon.
        round_variant: Also write the round legacy tiles.

    Returns:
        The :class:`IconLayers` record, whose drawable is ``ic_launcher``.

    Raises:
        ValueError: the recipe id is unknown or a colour is not hex.
    """
    return write_icon_set(
        spec,
        res_dir,
        LAUNCHER_BASE,
        folder_prefix="mipmap",
        master=master,
        round_variant=round_variant,
        monochrome_suffix="_monochrome",
    )


def adaptive_icon_xml(
    background: str = f"@mipmap/{LAUNCHER_BASE}_background",
    foreground: str = f"@mipmap/{LAUNCHER_BASE}_foreground",
    monochrome: str = f"@mipmap/{LAUNCHER_BASE}_monochrome",
) -> str:
    """Render the ``<adaptive-icon>`` XML.

    The monochrome child is always present, which is what qualifies the pack
    for themed icons.

    Args:
        background: Drawable reference for the background layer.
        foreground: Drawable reference for the foreground layer.
        monochrome: Drawable reference for the monochrome layer.

    Returns:
        An XML document for ``res/mipmap-anydpi-v26``.
    """
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- Generated by ez_icons. Adaptive layers are 108dp with a 66dp"
        " artwork safe zone. -->\n"
        "<adaptive-icon xmlns:android=\"http://schemas.android.com/apk/res/android\">\n"
        f'    <background android:drawable="{background}" />\n'
        f'    <foreground android:drawable="{foreground}" />\n'
        f'    <{_MONOCHROME_ELEMENT} android:drawable="{monochrome}" />\n'
        "</adaptive-icon>\n"
    )


def write_launcher_xml(res_dir: Path | str, round_variant: bool = True) -> tuple[str, ...]:
    """Write the adaptive-icon XML for the pack launcher.

    Args:
        res_dir: The ``app/src/main/res`` directory.
        round_variant: Also write ``ic_launcher_round.xml``.

    Returns:
        Written paths, relative to ``res_dir``, sorted.
    """
    root = Path(res_dir)
    written: list[str] = []
    folder = root / "mipmap-anydpi-v26"
    folder.mkdir(parents=True, exist_ok=True)
    written.append(_write_text(folder / "ic_launcher.xml", adaptive_icon_xml(), root))
    if round_variant:
        written.append(_write_text(folder / "ic_launcher_round.xml", adaptive_icon_xml(), root))
    return tuple(sorted(written))


def play_icon_canvas(spec: IconSpec, master: str | None = None) -> Canvas:
    """Build the 512 px Play Store app icon.

    Full square, no rounded corners, no baked shadow: Play masks the asset
    itself and rejects a pre-rounded or shadowed one.

    Args:
        spec: Entry to render.
        master: Operator master art, used instead of the generated glyph.

    Returns:
        Opaque 512 x 512 canvas.

    Raises:
        ValueError: the recipe id is unknown or a colour is not hex.
    """
    base = render_background(spec, PLAY_ICON_PX)
    front = (
        render_master(master, PLAY_ICON_PX)
        if master is not None
        else render_foreground(spec, PLAY_ICON_PX)
    )
    return _force_opaque(front.composited_over(base))


def write_play_icon(spec: IconSpec, path: Path | str, master: str | None = None) -> int:
    """Write the Play Store app icon.

    Args:
        spec: Entry to render.
        path: Destination ``.png`` path; parents are created.
        master: Operator master art, used instead of the generated glyph.

    Returns:
        Bytes written.

    Raises:
        ValueError: the asset would exceed the 1024 KB Play ceiling, or the
            recipe id is unknown.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    written = play_icon_canvas(spec, master).write_png(str(destination))
    if written > PLAY_ICON_MAX_BYTES:
        raise ValueError(
            f"play icon {destination} is {written} bytes, over the {PLAY_ICON_MAX_BYTES} ceiling"
        )
    return written


def feature_graphic(
    specs: tuple[IconSpec, ...],
    accent: str,
    width: int = FEATURE_GRAPHIC_WIDTH,
    height: int = FEATURE_GRAPHIC_HEIGHT,
) -> Canvas:
    """Build the 1024 x 500 Play feature graphic.

    The graphic carries no transparency: it is painted onto an opaque field
    and every alpha byte is then forced to full, which is what "24-bit PNG,
    no alpha" asks for.

    Args:
        specs: Entries whose glyphs tile across the right-hand side.
        accent: Hex colour of the backing field.
        width: Canvas width.
        height: Canvas height.

    Returns:
        Opaque canvas at the Play feature graphic size.

    Raises:
        ValueError: a recipe id is unknown or a colour is not hex.
    """
    canvas = Canvas(width, height, hex_to_rgba(accent))
    tone = hex_to_rgba(accent)
    shade = Rgba(max(0, tone.red - 24), max(0, tone.green - 24), max(0, tone.blue - 24), 255)
    for row in range(height):
        canvas.fill_rect(0, row, width, 1, _mix(tone, shade, row / max(1, height - 1)))
    tiles = specs[:FEATURE_TILE_COUNT]
    margin = 60
    gap = 40
    available = width - 2 * margin - gap * (len(tiles) - 1)
    tile_side = max(16, min(height - 80, available // max(1, len(tiles))))
    row = max(0, (height - tile_side) // 2)
    left = max(0, width - margin - (tile_side * len(tiles) + gap * (len(tiles) - 1)))
    for index, spec in enumerate(tiles):
        _paste_tile(canvas, _render_tile(spec, tile_side), left + index * (tile_side + gap), row)
    return _force_opaque(canvas)


def _render_tile(spec: IconSpec, side: int) -> Canvas:
    """Render one feature-graphic tile: its field plus its glyph.

    Args:
        spec: Entry to draw.
        side: Tile edge in pixels.

    Returns:
        Opaque tile canvas.

    Raises:
        ValueError: a recipe id is unknown or a colour is not hex.
    """
    field = Canvas(side, side, hex_to_rgba(spec.parsed_background.top))
    art = render_foreground(spec, side)
    return art.composited_over(field)


def _paste_tile(canvas: Canvas, tile: Canvas, left: int, top: int) -> None:
    """Copy an opaque tile into a canvas at a pixel offset.

    Args:
        canvas: Destination canvas.
        tile: Opaque tile to copy.
        left: Destination column.
        top: Destination row.
    """
    stride = tile.width * 4
    for row in range(tile.height):
        start = row * stride
        stop = ((top + row) * canvas.width + left) * 4
        canvas.pixels[stop : stop + stride] = tile.pixels[start : start + stride]


def write_feature_graphic(
    specs: tuple[IconSpec, ...],
    path: Path | str,
    accent: str = "#16212B",
) -> int:
    """Write the Play feature graphic.

    Args:
        specs: Entries whose glyphs tile across the graphic.
        path: Destination ``.png`` path; parents are created.
        accent: Hex colour of the backing field.

    Returns:
        Bytes written.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return feature_graphic(specs, accent).write_png(str(destination))


def _force_opaque(canvas: Canvas) -> Canvas:
    """Set every alpha byte to fully opaque.

    Args:
        canvas: Canvas to modify in place.

    Returns:
        The same canvas, for chaining.
    """
    pixels = canvas.pixels
    for index in range(3, len(pixels), 4):
        pixels[index] = 255
    return canvas


def _mix(top: Rgba, bottom: Rgba, fraction: float) -> Rgba:
    """Blend two colours linearly.

    Args:
        top: Colour at fraction 0.
        bottom: Colour at fraction 1.
        fraction: Blend position.

    Returns:
        The blended colour.
    """
    edge = min(1.0, max(0.0, fraction))
    return Rgba(
        red=round(top.red + (bottom.red - top.red) * edge),
        green=round(top.green + (bottom.green - top.green) * edge),
        blue=round(top.blue + (bottom.blue - top.blue) * edge),
        alpha=255,
    )


def _save(path: Path, canvas: Canvas, root: Path) -> str:
    """Write a canvas and report its res-relative resource path.

    Args:
        path: Destination file.
        canvas: Layer to encode.
        root: The ``res`` directory the path sits under.

    Returns:
        The path relative to ``root``, with forward slashes.
    """
    canvas.write_png(str(path))
    return path.relative_to(root).as_posix()


def _write_text(path: Path, text: str, root: Path) -> str:
    """Write a text asset.

    Args:
        path: Destination file.
        text: Document body.
        root: The ``res`` directory the path sits under.

    Returns:
        The path relative to ``root``, with forward slashes.
    """
    path.write_text(text, encoding="utf-8")
    return path.relative_to(root).as_posix()
