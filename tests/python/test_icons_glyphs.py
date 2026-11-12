"""Hermetic tests for the glyph recipes, the safe zone, and the painters."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_icons.catalog import ICON_CATALOG, IconSpec  # noqa: E402
from ez_icons.glyphs import (  # noqa: E402
    ARTWORK_MAX_DP,
    ARTWORK_MIN_DP,
    ARTWORK_TARGET_DP,
    DEFAULT_SHEET_PX,
    LEGACY_CORNER_RATIO,
    SAFE_ZONE_RATIO,
    SHEET_DP,
    artwork_bounds,
    artwork_box,
    artwork_side,
    colors_for,
    fit_to_safe_zone,
    glyph_recipes,
    legacy_box,
    render_background,
    render_foreground,
    render_legacy,
    render_master,
    render_monochrome,
)
from ez_raster import ADAPTIVE_SAFE_RATIO, BLACK, Canvas, RasterError, Rgba, TRANSPARENT, WHITE  # noqa: E402

RESERVED = (SHEET_DP - ARTWORK_MAX_DP) // 2
TOLERANCE = 2


def probe(glyph: str = "star", **overrides: object) -> IconSpec:
    """Build one entry for rendering.

    Args:
        glyph: Recipe id to draw.
        overrides: Field values to replace.

    Returns:
        A validated spec.
    """
    fields: dict[str, object] = {
        "slug": "probe-" + glyph.replace("_", "-"),
        "name": "Probe",
        "package": "com.probe.app",
        "glyph": glyph,
    }
    fields.update(overrides)
    return IconSpec(**fields)  # type: ignore[arg-type]


def test_digest_constants() -> None:
    assert SAFE_ZONE_RATIO == ADAPTIVE_SAFE_RATIO
    assert SHEET_DP == 108
    assert ARTWORK_MAX_DP == 66
    assert ARTWORK_MIN_DP == 48
    assert ARTWORK_TARGET_DP == 60
    assert DEFAULT_SHEET_PX == 108
    assert 0.0 < LEGACY_CORNER_RATIO < 0.5


def test_artwork_geometry() -> None:
    assert artwork_side(108) == ARTWORK_MAX_DP
    assert artwork_side(0) == 1
    box = artwork_box(108)
    assert (box.left, box.top, box.side) == (21, 21, 66)
    assert box.px(0.5) == 54 and box.py(0.5) == 54
    assert box.u(0.5) == 33 and box.u(-1.0) == 0
    assert box.centre == 54.0
    assert legacy_box(48) == legacy_box(48)
    assert (legacy_box(48).left, legacy_box(48).side) == (0, 48)


def test_colors_for_every_palette_shape() -> None:
    one = colors_for(("#010203",))
    assert one.primary == one.accent == one.detail
    two = colors_for(("#010203", "#040506"))
    assert two.detail == two.accent
    three = colors_for(("#010203", "#040506", "#070809"))
    assert three.primary == Rgba(1, 2, 3, 255)
    assert three.accent == Rgba(4, 5, 6, 255)
    assert three.detail == Rgba(7, 8, 9, 255)
    mono = colors_for(("#010203", "#040506", "#070809"), monochrome=True)
    assert mono.primary == WHITE
    assert mono.accent == TRANSPARENT and mono.detail == TRANSPARENT


def test_colors_for_rejects_a_bad_palette() -> None:
    with pytest.raises(ValueError, match="palette is empty"):
        colors_for(())
    with pytest.raises(ValueError, match="not a hex colour"):
        colors_for(("nope",))


def test_every_recipe_draws_a_bounded_silhouette() -> None:
    assert glyph_recipes() == tuple(sorted(glyph_recipes()))
    for glyph in glyph_recipes():
        spec = probe(glyph)
        for canvas, tag in (
            (render_foreground(spec, DEFAULT_SHEET_PX), "foreground"),
            (render_monochrome(spec, DEFAULT_SHEET_PX), "monochrome"),
        ):
            assert canvas.width == DEFAULT_SHEET_PX
            bounds = artwork_bounds(canvas)
            assert bounds is not None, (glyph, tag, "empty layer")
            left, top, right, bottom = bounds
            edge = max(right - left + 1, bottom - top + 1)
            assert edge >= ARTWORK_MIN_DP - TOLERANCE, (glyph, tag, edge)
            assert left >= RESERVED - TOLERANCE, (glyph, tag, bounds)
            assert top >= RESERVED - TOLERANCE, (glyph, tag, bounds)
            assert right <= SHEET_DP - 1 - RESERVED + TOLERANCE, (glyph, tag, bounds)
            assert bottom <= SHEET_DP - 1 - RESERVED + TOLERANCE, (glyph, tag, bounds)


def test_shipped_catalog_glyphs_are_all_recipes() -> None:
    known = set(glyph_recipes())
    assert {entry.glyph for entry in ICON_CATALOG} <= known


def test_monochrome_uses_one_ink() -> None:
    canvas = render_monochrome(probe("star"))
    seen = {canvas.pixel(column, row) for row in range(canvas.height) for column in range(canvas.width)}
    visible = {pixel for pixel in seen if pixel.alpha >= 8}
    assert visible
    assert all(pixel.red == pixel.green == pixel.blue for pixel in visible)
    assert WHITE in visible
    assert canvas.illuminated_ratio() > 0.0


def test_unknown_glyph_is_rejected() -> None:
    broken = IconSpec(slug="probe-broken", name="Probe", package="com.probe.app", glyph="nope")
    with pytest.raises(ValueError, match="unknown glyph 'nope'"):
        render_foreground(broken)
    with pytest.raises(ValueError, match="unknown glyph 'nope'"):
        render_monochrome(broken)


def test_render_background_solid() -> None:
    canvas = render_background(probe(background="#102030"), 8)
    assert canvas.pixel(0, 0) == Rgba(16, 32, 48, 255)
    assert canvas.pixel(7, 7) == Rgba(16, 32, 48, 255)


def test_render_background_linear_and_radial() -> None:
    linear = render_background(probe(background="linear:#000000>#FFFFFF"), 9)
    assert linear.pixel(4, 0).red < 8
    assert linear.pixel(4, 8).red > 247
    assert linear.pixel(4, 4).red == 128
    radial = render_background(probe(background="radial:#FFFFFF>#000000"), 9)
    assert radial.pixel(4, 4).red > 247
    assert radial.pixel(0, 0).red < 8


def test_render_legacy_cuts_the_corners() -> None:
    canvas = render_legacy(probe(background="#102030"), 48)
    assert canvas.width == 48 and canvas.height == 48
    assert canvas.pixel(0, 0).alpha == 0
    assert canvas.pixel(24, 24).alpha == 255


def test_render_legacy_uses_master_art(tmp_path: Path) -> None:
    master = tmp_path / "master.png"
    sheet = Canvas(64, 64, TRANSPARENT)
    sheet.fill_circle(32.0, 32.0, 28.0, BLACK)
    sheet.write_png(str(master))
    canvas = render_legacy(probe(background="#102030"), 48, str(master))
    assert canvas.pixel(24, 24) == BLACK


def test_fit_to_safe_zone_passes_an_empty_sheet_through() -> None:
    empty = Canvas(108, 108, TRANSPARENT)
    assert fit_to_safe_zone(empty, 108) is empty
    assert artwork_bounds(empty) is None


def test_fit_to_safe_zone_shrinks_oversized_art() -> None:
    loud = Canvas(108, 108, TRANSPARENT)
    loud.fill_rect(0, 0, 108, 108, WHITE)
    fitted = fit_to_safe_zone(loud, 108)
    bounds = artwork_bounds(fitted)
    assert bounds is not None
    left, top, right, bottom = bounds
    assert left >= RESERVED - TOLERANCE
    assert right <= SHEET_DP - 1 - RESERVED + TOLERANCE
    assert artwork_bounds(fitted) is not None


def test_fit_to_safe_zone_grows_a_tiny_mark() -> None:
    tiny = Canvas(108, 108, TRANSPARENT)
    tiny.fill_rect(53, 53, 2, 2, WHITE)
    fitted = fit_to_safe_zone(tiny, 108)
    bounds = artwork_bounds(fitted)
    assert bounds is not None
    assert max(bounds[2] - bounds[0], bounds[3] - bounds[1]) >= ARTWORK_MIN_DP - TOLERANCE


def test_render_master_fits_operator_art(tmp_path: Path) -> None:
    master = tmp_path / "art.png"
    loud = Canvas(64, 64, TRANSPARENT)
    loud.fill_rect(0, 0, 64, 64, WHITE)
    loud.write_png(str(master))
    canvas = render_master(str(master), 108)
    bounds = artwork_bounds(canvas)
    assert bounds is not None
    assert bounds[0] >= RESERVED - TOLERANCE
    assert canvas.pixel(0, 0) == TRANSPARENT


def test_render_master_reports_a_decode_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ez_icons.glyphs as glyphs

    def refuse(path: str, side: int | None = None) -> Canvas:
        del path, side
        raise RasterError("ffmpeg refused the file")

    monkeypatch.setattr(glyphs, "decode_rgba", refuse)
    with pytest.raises(RasterError, match="refused"):
        render_master(str(tmp_path / "missing.png"))
