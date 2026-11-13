"""Hermetic tests for the adaptive layer ladder, its XML, and the Play assets."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_icons import adaptive  # noqa: E402
from ez_icons.adaptive import (  # noqa: E402
    ADAPTIVE_LADDER,
    ADAPTIVE_XML_PATH,
    FEATURE_GRAPHIC_HEIGHT,
    FEATURE_GRAPHIC_WIDTH,
    FEATURE_TILE_COUNT,
    LAUNCHER_BASE,
    LEGACY_LADDER,
    PLAY_ICON_MAX_BYTES,
    PLAY_ICON_PX,
    ROUND_XML_PATH,
    IconLayers,
    adaptive_icon_xml,
    density_dir,
    feature_graphic,
    icon_layer_paths,
    layer_filename,
    play_icon_canvas,
    write_feature_graphic,
    write_icon_set,
    write_launcher_icon_set,
    write_launcher_xml,
    write_play_icon,
)
from ez_icons.catalog import IconSpec  # noqa: E402
from ez_raster import Canvas, Rgba, TRANSPARENT, WHITE, decode_rgba  # noqa: E402

ENTRY = IconSpec(
    slug="probe-icon",
    name="Probe Icon",
    package="com.probe.app",
    category="utilities",
    glyph="star",
    palette=("#F2F5F7", "#7FC8F8"),
    background="linear:#101C2A>#3E6B8F",
)


def png_shape(path: Path) -> tuple[int, int, int, int]:
    """Read width, height, bit depth, and colour type from a PNG.

    Args:
        path: File to inspect.

    Returns:
        The IHDR fields.
    """
    head = path.read_bytes()[:26]
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">IIBB", head[16:26])


def master_sheet(path: Path, colour: Rgba = WHITE) -> str:
    """Write a solid master-art PNG for an operator drop-in.

    Args:
        path: Destination file.
        colour: Fill colour.

    Returns:
        The path as text.
    """
    canvas = Canvas(64, 64, TRANSPARENT)
    canvas.fill_circle(32.0, 32.0, 30.0, colour)
    canvas.write_png(str(path))
    return str(path)


def test_ladder_constants_come_from_the_digest() -> None:
    assert tuple(edge for _, edge in ADAPTIVE_LADDER) == (108, 162, 216, 324, 432)
    assert tuple(name for name, _ in ADAPTIVE_LADDER) == (
        "mdpi",
        "hdpi",
        "xhdpi",
        "xxhdpi",
        "xxxhdpi",
    )
    assert tuple(edge for _, edge in LEGACY_LADDER) == (48, 72, 96, 144, 192)
    assert PLAY_ICON_PX == 512
    assert PLAY_ICON_MAX_BYTES == 1024 * 1024
    assert (FEATURE_GRAPHIC_WIDTH, FEATURE_GRAPHIC_HEIGHT) == (1024, 500)
    assert FEATURE_TILE_COUNT == 5


def test_layer_filename_and_density_dir() -> None:
    assert layer_filename("ic_launcher", "") == "ic_launcher.png"
    assert layer_filename("ic_launcher", "_foreground") == "ic_launcher_foreground.png"
    assert density_dir("drawable", "xxhdpi") == "drawable-xxhdpi"


def test_icon_layer_paths_plan() -> None:
    plain = icon_layer_paths("probe")
    assert len(plain) == 20
    assert "drawable-mdpi/probe_foreground.png" in plain
    assert "drawable-xxxhdpi/probe_background.png" in plain
    assert "drawable-mdpi/probe_themed.png" in plain
    assert "drawable-mdpi/probe.png" in plain
    assert "drawable-mdpi/probe_round.png" not in plain
    assert plain == tuple(sorted(plain))
    rounded = icon_layer_paths("probe", "mipmap", True, "_monochrome")
    assert len(rounded) == 25
    assert "mipmap-mdpi/probe_round.png" in rounded
    assert "mipmap-mdpi/probe_monochrome.png" in rounded


def test_write_icon_set_writes_the_whole_ladder(tmp_path: Path) -> None:
    record = write_icon_set(ENTRY, tmp_path, ENTRY.drawable)
    assert isinstance(record, IconLayers)
    assert record.slug == "probe-icon"
    assert record.drawable == "probe_icon"
    assert record.themed_drawable == "probe_icon_themed"
    assert record.master is None
    assert len(record.files) == 20
    assert record.files == tuple(sorted(record.files))
    assert record.densities == tuple(name for name, _ in ADAPTIVE_LADDER)
    assert record.adaptive_sizes == (108, 162, 216, 324, 432)
    assert record.legacy_sizes == (48, 72, 96, 144, 192)
    for name, edge in ADAPTIVE_LADDER:
        for suffix in ("_foreground", "_background", "_themed"):
            path = tmp_path / f"drawable-{name}" / f"probe_icon{suffix}.png"
            assert png_shape(path)[:2] == (edge, edge)
    for name, edge in LEGACY_LADDER:
        path = tmp_path / f"drawable-{name}" / "probe_icon.png"
        assert png_shape(path)[:2] == (edge, edge)


def test_write_icon_set_uses_master_art_and_round_tiles(
    tmp_path: Path,
) -> None:
    master = master_sheet(tmp_path / "art.png")
    record = write_icon_set(
        ENTRY, tmp_path, ENTRY.drawable, "drawable", master, True, "_themed"
    )
    assert record.master == master
    assert len(record.files) == 25
    assert f"drawable-mdpi/{ENTRY.drawable}_round.png" in record.files
    front = tmp_path / "drawable-mdpi" / f"{ENTRY.drawable}_foreground.png"
    assert front.is_file()


def test_write_launcher_icon_set(tmp_path: Path) -> None:
    record = write_launcher_icon_set(ENTRY, tmp_path)
    assert record.drawable == LAUNCHER_BASE
    assert record.themed_drawable == "ic_launcher_monochrome"
    assert "mipmap-xxxhdpi/ic_launcher_round.png" in record.files
    assert png_shape(tmp_path / "mipmap-mdpi" / "ic_launcher.png")[:2] == (48, 48)
    assert png_shape(tmp_path / "mipmap-mdpi" / "ic_launcher_monochrome.png")[:2] == (108, 108)


def test_write_launcher_icon_set_without_round(tmp_path: Path) -> None:
    record = write_launcher_icon_set(ENTRY, tmp_path, None, False)
    assert "mipmap-mdpi/ic_launcher_round.png" not in record.files


def test_adaptive_icon_xml_always_carries_monochrome() -> None:
    text = adaptive_icon_xml()
    assert "<adaptive-icon" in text
    assert '<background android:drawable="@mipmap/ic_launcher_background" />' in text
    assert '<foreground android:drawable="@mipmap/ic_launcher_foreground" />' in text
    assert '<monochrome android:drawable="@mipmap/ic_launcher_monochrome" />' in text
    custom = adaptive_icon_xml("@drawable/a", "@drawable/f", "@drawable/m")
    assert '@drawable/m"' in custom


def test_write_launcher_xml(tmp_path: Path) -> None:
    written = write_launcher_xml(tmp_path)
    assert written == (ADAPTIVE_XML_PATH, ROUND_XML_PATH)
    body = (tmp_path / ADAPTIVE_XML_PATH).read_text(encoding="utf-8")
    assert "<monochrome" in body
    assert (tmp_path / ROUND_XML_PATH).is_file()
    assert write_launcher_xml(tmp_path, False) == (ADAPTIVE_XML_PATH,)


def test_play_icon_canvas_is_a_full_square() -> None:
    canvas = play_icon_canvas(ENTRY)
    assert (canvas.width, canvas.height) == (PLAY_ICON_PX, PLAY_ICON_PX)
    assert min(canvas.pixels[3::4]) == 255


def test_play_icon_canvas_with_master(tmp_path: Path) -> None:
    canvas = play_icon_canvas(ENTRY, master_sheet(tmp_path / "art.png", Rgba(10, 20, 30, 255)))
    assert canvas.pixel(256, 256) == Rgba(10, 20, 30, 255)


def test_write_play_icon_and_byte_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "store" / "play-icon.png"
    written = write_play_icon(ENTRY, destination)
    assert written == destination.stat().st_size
    assert written < PLAY_ICON_MAX_BYTES
    assert png_shape(destination) == (512, 512, 8, 6)
    monkeypatch.setattr(adaptive, "PLAY_ICON_MAX_BYTES", 64)
    with pytest.raises(ValueError, match="over the 64 ceiling"):
        write_play_icon(ENTRY, destination)


def test_feature_graphic_is_opaque_at_the_play_shape() -> None:
    canvas = feature_graphic((ENTRY,) * 3, "#16212B")
    assert (canvas.width, canvas.height) == (FEATURE_GRAPHIC_WIDTH, FEATURE_GRAPHIC_HEIGHT)
    assert min(canvas.pixels[3::4]) == 255
    assert canvas.pixel(4, 0) == Rgba(22, 33, 43, 255)
    assert canvas.pixel(4, FEATURE_GRAPHIC_HEIGHT - 1).red < 22


def test_feature_graphic_honours_custom_size() -> None:
    canvas = feature_graphic((ENTRY,), "#101010", 600, 300)
    assert (canvas.width, canvas.height) == (600, 300)
    assert canvas.pixel(5, 0) == Rgba(16, 16, 16, 255)
    assert canvas.pixel(5, 299) == Rgba(0, 0, 0, 255)


def test_write_feature_graphic(tmp_path: Path) -> None:
    destination = tmp_path / "store" / "feature-graphic.png"
    written = write_feature_graphic((ENTRY,), destination, "#101820")
    assert written == destination.stat().st_size
    assert png_shape(destination)[:2] == (FEATURE_GRAPHIC_WIDTH, FEATURE_GRAPHIC_HEIGHT)
    decoded = decode_rgba(str(destination), FEATURE_GRAPHIC_HEIGHT)
    assert min(decoded.pixels[3::4]) == 255
