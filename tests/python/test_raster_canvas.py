"""Hermetic tests for the ez_raster RGBA canvas and stdlib PNG codec.

The module reads artwork through ffmpeg and writes PNGs itself. Every ffmpeg
and ffprobe call is faked here, and the PNG bytes are checked by hand against
the chunk framing the spec requires, so the suite needs neither a host binary
nor PIL.
"""

from __future__ import annotations

import subprocess
import sys
import zlib
from collections.abc import Sequence
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_raster as raster  # noqa: E402
from ez_raster import (  # noqa: E402
    ADAPTIVE_CANVAS_DP,
    ADAPTIVE_SAFE_DP,
    ADAPTIVE_SAFE_RATIO,
    BLACK,
    MIPMAP_DENSITIES,
    PLAY_FEATURE_GRAPHIC_HEIGHT,
    PLAY_FEATURE_GRAPHIC_WIDTH,
    PLAY_LAUNCHER_ICON_PX,
    TRANSPARENT,
    WHITE,
    Canvas,
    RasterError,
    Rgba,
    decode_rgba,
    encode_rgb_png,
    encode_png,
    from_rgba_bytes,
    hex_to_rgba,
    rgba_to_hex,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""The eight bytes every PNG file starts with."""


class _MediaBackend:
    """Stand-in for the host ffmpeg and ffprobe binaries.

    Args:
        decode_stdout: Raw RGBA bytes ffmpeg prints for a decode job.
        decode_returncode: Exit status ffmpeg reports for a decode job.
        probe_size: The ``WxH`` text ffprobe reports.
        probe_returncode: Exit status ffprobe reports.
        encode_payload: Bytes written to the destination of an encode job.
        encode_returncode: Exit status ffmpeg reports for an encode job.
        stderr: Text both binaries write on stderr.
        missing: Raise FileNotFoundError instead of answering, as a host
            without the binaries would.
        missing_probe: Raise FileNotFoundError for ffprobe calls only.
    """

    def __init__(
        self,
        *,
        decode_stdout: bytes = b"",
        decode_returncode: int = 0,
        probe_size: str = "4x4",
        probe_returncode: int = 0,
        encode_payload: bytes = b"",
        encode_returncode: int = 0,
        stderr: bytes = b"",
        missing: bool = False,
        missing_probe: bool = False,
    ) -> None:
        """Store the scripted answers.

        Args:
            decode_stdout: Raw RGBA bytes ffmpeg prints for a decode job.
            decode_returncode: Exit status ffmpeg reports for a decode job.
            probe_size: The ``WxH`` text ffprobe reports.
            probe_returncode: Exit status ffprobe reports.
            encode_payload: Bytes written to the destination of an encode job.
            encode_returncode: Exit status ffmpeg reports for an encode job.
            stderr: Text both binaries write on stderr.
            missing: Raise FileNotFoundError for every call.
            missing_probe: Raise FileNotFoundError for ffprobe calls only.
        """
        self.calls: list[list[str]] = []
        self._decode_stdout = decode_stdout
        self._decode_returncode = decode_returncode
        self._probe_size = probe_size
        self._probe_returncode = probe_returncode
        self._encode_payload = encode_payload
        self._encode_returncode = encode_returncode
        self._stderr = stderr
        self._missing = missing
        self._missing_probe = missing_probe

    def __call__(
        self, command: Sequence[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        """Answer one ffmpeg or ffprobe invocation.

        Args:
            command: argv the module built.
            **_kwargs: The keyword arguments subprocess.run would have taken.
        Returns:
            The scripted result for whichever binary was called.
        Raises:
            FileNotFoundError: always, when the backend is scripted missing.
        """
        argv = [str(part) for part in command]
        self.calls.append(argv)
        if self._missing or (self._missing_probe and argv[0] == "ffprobe"):
            raise FileNotFoundError(argv[0])
        if argv[0] == "ffprobe":
            return _process(
                returncode=self._probe_returncode,
                stdout=self._probe_size.encode("ascii"),
                stderr=self._stderr,
            )
        if argv[-1].endswith(".png"):
            Path(argv[-1]).write_bytes(self._encode_payload)
            return _process(returncode=self._encode_returncode, stderr=self._stderr)
        return _process(
            returncode=self._decode_returncode, stdout=self._decode_stdout, stderr=self._stderr
        )


def _process(
    *,
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
) -> subprocess.CompletedProcess[bytes]:
    """Build the result a fake media binary hands back.

    Args:
        returncode: Exit status to report.
        stdout: Bytes the command printed.
        stderr: Bytes the command complained about.
    Returns:
        A CompletedProcess carrying those three fields.
    """
    return subprocess.CompletedProcess(["media"], returncode, stdout, stderr)


def _png_parts(data: bytes, *, colour_type: int) -> tuple[int, int, list[bytes]]:
    """Split the PNG bytes this module writes into verified chunks and rows.

    The encoder only ever emits filter-zero rows, so this reader has to check
    the chunk framing and peel one filter byte per row. Checking the CRC of
    every chunk is what makes the round trip a real test of the encoder.

    Args:
        data: Complete PNG file bytes.
        colour_type: The colour type the encoder must have written, 6 for RGBA
            or 2 for the alpha-free banner path.
    Returns:
        ``(width, height, rows)``, one raw scanline per row without its filter
        byte.
    Raises:
        AssertionError: the signature, a chunk CRC, or the layout is wrong.
    """
    channels = 4 if colour_type == 6 else 3
    assert data[:8] == PNG_SIGNATURE, "png signature is missing"
    cursor = 8
    width = 0
    height = 0
    rows = bytearray()
    kinds: list[str] = []
    while cursor < len(data):
        length = int.from_bytes(data[cursor : cursor + 4], "big")
        kind = data[cursor + 4 : cursor + 8]
        payload = data[cursor + 8 : cursor + 8 + length]
        tail = data[cursor + 8 + length : cursor + 12 + length]
        assert int.from_bytes(tail, "big") == zlib.crc32(kind + payload) & 0xFFFFFFFF
        kinds.append(kind.decode("ascii"))
        if kind == b"IHDR":
            assert len(payload) == 13
            width = int.from_bytes(payload[0:4], "big")
            height = int.from_bytes(payload[4:8], "big")
            assert payload[8] == 8, "bit depth must be 8"
            assert payload[9] == colour_type, f"colour type must be {colour_type}"
        elif kind == b"IDAT":
            rows += zlib.decompress(payload)
        cursor += 12 + length
    assert kinds == ["IHDR", "IDAT", "IEND"]
    stride = width * channels
    scanlines: list[bytes] = []
    for row in range(height):
        start = row * (stride + 1)
        assert rows[start] == 0, "every row must use the none filter"
        scanlines.append(bytes(rows[start + 1 : start + 1 + stride]))
    return width, height, scanlines


def _png_to_rgba(data: bytes) -> tuple[int, int, bytes]:
    """Decode an RGBA PNG written by this module back into raw pixels.

    Args:
        data: Complete PNG file bytes.
    Returns:
        ``(width, height, rgba_bytes)``.
    Raises:
        AssertionError: the file is not a colour-type-6 PNG.
    """
    width, height, rows = _png_parts(data, colour_type=6)
    return width, height, b"".join(rows)


def _png_to_rgb(data: bytes) -> tuple[int, int, bytes]:
    """Decode an alpha-free PNG written by this module back into raw pixels.

    Args:
        data: Complete PNG file bytes.
    Returns:
        ``(width, height, rgb_bytes)``.
    Raises:
        AssertionError: the file is not a colour-type-2 PNG.
    """
    width, height, rows = _png_parts(data, colour_type=2)
    return width, height, b"".join(rows)


def _solid(width: int, height: int, color: Rgba) -> Canvas:
    """Build a canvas painted one colour throughout.

    Args:
        width: Canvas width.
        height: Canvas height.
        color: Colour every pixel carries.
    Returns:
        The painted canvas.
    """
    return Canvas(width, height, color)


def _rgba_rows(*rows: tuple[tuple[int, int, int, int], ...]) -> bytes:
    """Lay out per-row pixel quads as the raw RGBA stream ffmpeg would emit.

    Args:
        *rows: One tuple per row, each holding ``(red, green, blue, alpha)``.
    Returns:
        The concatenated row-major RGBA bytes.
    """
    flat = bytearray()
    for row in rows:
        for quad in row:
            flat += bytes(quad)
    return bytes(flat)


# --- palette constants ------------------------------------------------------


def test_named_colours_and_the_mipmap_ladder() -> None:
    assert TRANSPARENT.as_tuple() == (0, 0, 0, 0)
    assert BLACK.as_tuple() == (0, 0, 0, 255)
    assert WHITE.as_tuple() == (255, 255, 255, 255)
    assert MIPMAP_DENSITIES == (
        ("mdpi", 48),
        ("hdpi", 72),
        ("xhdpi", 96),
        ("xxhdpi", 144),
        ("xxxhdpi", 192),
    )
    assert (ADAPTIVE_CANVAS_DP, ADAPTIVE_SAFE_DP) == (108, 72)
    assert ADAPTIVE_SAFE_RATIO == pytest.approx(72 / 108)
    assert PLAY_LAUNCHER_ICON_PX == 512
    assert (PLAY_FEATURE_GRAPHIC_WIDTH, PLAY_FEATURE_GRAPHIC_HEIGHT) == (1024, 500)


# --- Rgba -------------------------------------------------------------------


def test_rgba_defaults_to_opaque_black_channel_zero() -> None:
    assert Rgba().as_tuple() == (0, 0, 0, 255)
    assert Rgba(1, 2, 3, 4).as_tuple() == (1, 2, 3, 4)


def test_rgba_rejects_a_channel_the_format_cannot_carry() -> None:
    with pytest.raises(ValueError, match="red 256 outside 0..255"):
        Rgba(256, 0, 0, 255)
    with pytest.raises(ValueError, match="green -1 outside 0..255"):
        Rgba(0, -1, 0, 255)
    with pytest.raises(ValueError, match="blue 300 outside 0..255"):
        Rgba(0, 0, 300, 255)
    with pytest.raises(ValueError, match="alpha 256 outside 0..255"):
        Rgba(0, 0, 0, 256)


def test_blended_over_composites_against_an_opaque_base() -> None:
    half = Rgba(255, 0, 0, 128)
    assert half.blended_over(Rgba(0, 0, 255, 255)).as_tuple() == (128, 0, 127, 255)
    assert Rgba(10, 20, 30, 0).blended_over(BLACK).as_tuple() == (0, 0, 0, 255)
    assert WHITE.blended_over(BLACK).as_tuple() == (255, 255, 255, 255)
    assert TRANSPARENT.blended_over(WHITE).as_tuple() == (255, 255, 255, 255)


# --- hex colours ------------------------------------------------------------


def test_hex_to_rgba_reads_the_three_accepted_shapes() -> None:
    assert hex_to_rgba("#f00").as_tuple() == (255, 0, 0, 255)
    assert hex_to_rgba("#1a2b3c").as_tuple() == (26, 43, 60, 255)
    assert hex_to_rgba("#11223344").as_tuple() == (17, 34, 51, 68)
    assert hex_to_rgba("aabbcc").as_tuple() == (170, 187, 204, 255)
    assert hex_to_rgba("#aabbcc\n").as_tuple() == (170, 187, 204, 255)


def test_hex_to_rgba_rejects_every_shape_it_cannot_parse() -> None:
    for value in (
        "",
        "#",
        "12",
        "#1234",
        "#12345",
        "#1234567",
        "gggggg",
        "#123456gg",
        "#12g45",
    ):
        with pytest.raises(ValueError, match="not a hex colour"):
            hex_to_rgba(value)


def test_hex_to_rgba_tolerates_the_padding_a_list_can_carry() -> None:
    """A colour lifted from JSON may arrive with spaces around it."""
    assert hex_to_rgba(" #aabbcc") == hex_to_rgba("#aabbcc")
    assert hex_to_rgba("\t#abc\n") == hex_to_rgba("#aabbcc")


def test_rgba_to_hex_round_trips_the_asset_xml_spellings() -> None:
    color = Rgba(26, 43, 60, 205)
    assert rgba_to_hex(color) == "#1A2B3C"
    assert rgba_to_hex(color, include_alpha=True) == "#1A2B3CCD"
    assert hex_to_rgba(rgba_to_hex(color, include_alpha=True)) == color


# --- canvas allocation ------------------------------------------------------


def test_canvas_rejects_a_side_below_one() -> None:
    with pytest.raises(ValueError, match="must be at least 1x1"):
        Canvas(0, 4)
    with pytest.raises(ValueError, match="must be at least 1x1"):
        Canvas(4, 0)


def test_canvas_rejects_an_area_past_the_pixel_guard() -> None:
    edge = raster._MAX_PIXELS + 1
    with pytest.raises(ValueError, match=f"exceeds {raster._MAX_PIXELS} pixels"):
        Canvas(edge, 1)


def test_pixels_exposes_the_live_buffer_and_to_bytes_copies_it() -> None:
    canvas = Canvas(2, 1, TRANSPARENT)
    assert canvas.pixels == bytearray(8)
    snapshot = canvas.to_bytes()
    canvas.pixels[0:4] = bytes(WHITE.as_tuple())
    assert snapshot == bytes(8)
    assert canvas.to_bytes() == bytes(WHITE.as_tuple()) + bytes(4)
    assert canvas.pixel(0, 0) == WHITE


def test_from_rgba_bytes_wraps_a_matching_stream_only() -> None:
    data = _rgba_rows(((1, 2, 3, 4), (5, 6, 7, 8)))
    canvas = from_rgba_bytes(data, 2, 1)
    assert (canvas.width, canvas.height) == (2, 1)
    assert canvas.to_bytes() == data
    assert canvas.pixel(1, 0) == Rgba(5, 6, 7, 8)
    with pytest.raises(ValueError, match="expected 8 RGBA bytes, got 7"):
        from_rgba_bytes(data[:-1], 2, 1)


# --- pixel writes -----------------------------------------------------------


def test_fill_paints_every_pixel_one_colour() -> None:
    canvas = Canvas(3, 2, TRANSPARENT)
    canvas.fill(BLACK)
    assert canvas.to_bytes() == bytes(BLACK.as_tuple()) * 6
    canvas.fill(Rgba(9, 8, 7, 1))
    assert canvas.pixel(2, 1) == Rgba(9, 8, 7, 1)


def test_set_pixel_and_pixel_ignore_a_coordinate_outside_the_canvas() -> None:
    canvas = Canvas(2, 2, TRANSPARENT)
    canvas.set_pixel(-1, 0, WHITE)
    canvas.set_pixel(0, 2, WHITE)
    canvas.set_pixel(2, 0, WHITE)
    canvas.set_pixel(0, -1, WHITE)
    assert canvas.to_bytes() == bytes(16)
    assert canvas.pixel(-1, 0) == TRANSPARENT
    assert canvas.pixel(0, 9) == TRANSPARENT
    canvas.set_pixel(1, 1, BLACK)
    assert canvas.pixel(1, 1) == BLACK


def test_fill_rect_clips_to_the_canvas() -> None:
    canvas = Canvas(4, 4, TRANSPARENT)
    canvas.fill_rect(-2, -2, 4, 4, WHITE)
    assert canvas.pixel(0, 0) == WHITE
    assert canvas.pixel(1, 1) == WHITE
    assert canvas.pixel(2, 2) == TRANSPARENT
    canvas.fill_rect(3, 3, 5, 5, BLACK)
    assert canvas.pixel(3, 3) == BLACK
    assert canvas.pixel(2, 3) == TRANSPARENT


def test_fill_circle_fills_the_disc_and_antialiases_the_rim() -> None:
    canvas = Canvas(11, 11, TRANSPARENT)
    canvas.fill_circle(5.0, 5.0, 3.0, WHITE)
    assert canvas.pixel(5, 5) == WHITE
    assert canvas.pixel(7, 5) == WHITE
    rim = canvas.pixel(8, 5)
    assert 0 < rim.alpha < 255
    assert (rim.red, rim.green, rim.blue) == (255, 255, 255)
    assert canvas.pixel(2, 2) == TRANSPARENT
    assert canvas.pixel(10, 10) == TRANSPARENT


def test_fill_circle_fades_the_rim_by_coverage() -> None:
    canvas = Canvas(11, 11, TRANSPARENT)
    canvas.fill_circle(5.0, 5.0, 3.0, Rgba(0, 0, 0, 255))
    assert canvas.pixel(8, 5).alpha == round(255 * (16.0 - 9.0) / 12.0)
    assert canvas.pixel(5, 5).alpha == 255


def test_fill_circle_draws_nothing_at_or_below_zero_radius() -> None:
    canvas = Canvas(4, 4, TRANSPARENT)
    canvas.fill_circle(2.0, 2.0, 0.0, WHITE)
    canvas.fill_circle(2.0, 2.0, -1.0, WHITE)
    assert canvas.to_bytes() == bytes(64)


def test_fill_circle_clamps_to_the_canvas_edges() -> None:
    canvas = Canvas(4, 4, TRANSPARENT)
    canvas.fill_circle(0.0, 0.0, 5.0, BLACK)
    assert canvas.pixel(0, 0) == BLACK
    assert canvas.pixel(1, 1) == BLACK
    rim = canvas.pixel(3, 3)
    assert 0 < rim.alpha < 255


# --- lines ------------------------------------------------------------------


def test_draw_line_paints_each_step() -> None:
    canvas = Canvas(6, 3, TRANSPARENT)
    canvas.draw_line(0, 0, 4, 0, WHITE)
    for column in range(5):
        assert canvas.pixel(column, 0) == WHITE
    assert canvas.pixel(5, 0) == TRANSPARENT
    assert canvas.pixel(0, 1) == TRANSPARENT


def test_draw_line_strokes_at_the_requested_thickness() -> None:
    canvas = Canvas(6, 6, TRANSPARENT)
    canvas.draw_line(2, 2, 2, 4, BLACK, thickness=3)
    assert canvas.pixel(2, 3) == BLACK
    assert canvas.pixel(1, 2) == BLACK
    assert canvas.pixel(3, 4) == BLACK
    assert canvas.pixel(0, 3) == TRANSPARENT
    assert canvas.pixel(4, 3) == TRANSPARENT


def test_draw_line_of_a_single_point_still_paints() -> None:
    canvas = Canvas(3, 3, TRANSPARENT)
    canvas.draw_line(1, 1, 1, 1, WHITE)
    assert canvas.pixel(1, 1) == WHITE
    assert canvas.pixel(0, 1) == TRANSPARENT


def test_draw_line_follows_a_diagonal() -> None:
    canvas = Canvas(4, 4, TRANSPARENT)
    canvas.draw_line(0, 0, 3, 3, BLACK)
    for index in range(4):
        assert canvas.pixel(index, index) == BLACK
    assert canvas.pixel(0, 3) == TRANSPARENT


# --- masks and compositing --------------------------------------------------


def test_masked_scales_alpha_by_the_mask_red_channel() -> None:
    canvas = _solid(2, 1, Rgba(10, 20, 30, 255))
    mask = Canvas(2, 1)
    mask.fill(Rgba(128, 0, 0, 255))
    cut = canvas.masked(mask)
    assert cut.pixel(0, 0) == Rgba(10, 20, 30, 128)
    assert cut.pixel(1, 0) == Rgba(10, 20, 30, 128)
    assert canvas.pixel(0, 0).alpha == 255


def test_masked_rejects_a_mask_of_another_size() -> None:
    canvas = Canvas(2, 2)
    with pytest.raises(ValueError, match="mask 1x2 does not match canvas"):
        canvas.masked(Canvas(1, 2))


def test_composited_over_blends_onto_an_opaque_base() -> None:
    top = _solid(1, 2, Rgba(255, 0, 0, 128))
    base = _solid(1, 2, Rgba(0, 0, 255, 255))
    out = top.composited_over(base)
    assert out.pixel(0, 0).as_tuple() == (128, 0, 127, 255)
    assert out.pixel(0, 1).as_tuple() == (128, 0, 127, 255)
    assert base.pixel(0, 0) == Rgba(0, 0, 255, 255)


def test_composited_over_rejects_a_base_of_another_size() -> None:
    with pytest.raises(ValueError, match="canvases must be the same size"):
        Canvas(2, 2).composited_over(Canvas(3, 2))


# --- resampling -------------------------------------------------------------


def test_resampled_down_averages_with_a_box_filter() -> None:
    canvas = from_rgba_bytes(
        _rgba_rows(
            ((0, 0, 0, 255), (255, 255, 255, 255)),
            ((0, 0, 0, 255), (255, 255, 255, 255)),
        ),
        2,
        2,
    )
    small = canvas.resampled(1, 1)
    assert (small.width, small.height) == (1, 1)
    assert small.pixel(0, 0).as_tuple() == (127, 127, 127, 255)


def test_resampled_up_repeats_the_source_pixel() -> None:
    canvas = _solid(1, 1, Rgba(10, 20, 30, 40))
    big = canvas.resampled(2, 3)
    assert (big.width, big.height) == (2, 3)
    assert all(big.pixel(x, y) == Rgba(10, 20, 30, 40) for x in range(2) for y in range(3))


def test_resampled_to_the_same_size_copies_the_pixels() -> None:
    canvas = _solid(2, 2, Rgba(5, 6, 7, 8))
    copy = canvas.resampled(2, 2)
    assert copy is not canvas
    assert copy.to_bytes() == canvas.to_bytes()


def test_resampled_averages_a_wide_downscale() -> None:
    canvas = from_rgba_bytes(
        _rgba_rows(
            ((0, 0, 0, 255), (0, 0, 0, 255), (200, 100, 50, 255), (200, 100, 50, 255)),
            ((0, 0, 0, 255), (0, 0, 0, 255), (200, 100, 50, 255), (200, 100, 50, 255)),
            ((0, 0, 0, 255), (0, 0, 0, 255), (200, 100, 50, 255), (200, 100, 50, 255)),
            ((0, 0, 0, 255), (0, 0, 0, 255), (200, 100, 50, 255), (200, 100, 50, 255)),
        ),
        4,
        4,
    )
    small = canvas.resampled(2, 2)
    for column in range(2):
        for row in range(2):
            expected = Rgba(0, 0, 0, 255) if column == 0 else Rgba(200, 100, 50, 255)
            assert small.pixel(column, row) == expected


# --- illuminated ratio ------------------------------------------------------


def test_illuminated_ratio_of_an_empty_canvas_is_zero() -> None:
    assert Canvas(4, 4, TRANSPARENT).illuminated_ratio() == 0.0


def test_illuminated_ratio_of_a_fully_lit_canvas_is_one() -> None:
    assert _solid(4, 4, WHITE).illuminated_ratio() == 1.0


def test_illuminated_ratio_counts_only_lit_opaque_enough_pixels() -> None:
    canvas = Canvas(2, 1)
    canvas.set_pixel(0, 0, Rgba(200, 200, 200, 255))
    canvas.set_pixel(1, 0, Rgba(200, 200, 200, 4))
    assert canvas.illuminated_ratio() == 0.5
    dim = _solid(1, 1, Rgba(5, 5, 5, 255))
    assert dim.illuminated_ratio() == 0.0


def test_illuminated_ratio_of_a_zero_area_canvas_is_zero() -> None:
    degenerate = object.__new__(Canvas)
    degenerate.width = 0
    degenerate.height = 0
    degenerate._pixels = bytearray()
    assert degenerate.illuminated_ratio() == 0.0


# --- PNG encoding -----------------------------------------------------------


def test_png_bytes_is_a_well_formed_deterministic_file() -> None:
    canvas = Canvas(3, 2, TRANSPARENT)
    canvas.fill_circle(1.0, 0.5, 1.0, WHITE)
    data = canvas.png_bytes()
    assert data[:8] == PNG_SIGNATURE
    assert data == canvas.png_bytes()
    width, height, rgba = _png_to_rgba(data)
    assert (width, height) == (3, 2)
    assert rgba == canvas.to_bytes()


def test_encode_rgb_png_writes_an_alpha_free_banner() -> None:
    canvas = _solid(3, 2, Rgba(10, 20, 30, 255))
    canvas.set_pixel(0, 0, Rgba(200, 0, 0, 255))
    data = encode_rgb_png(canvas)
    assert data[:8] == PNG_SIGNATURE
    assert data == encode_rgb_png(canvas)
    width, height, rgb = _png_to_rgb(data)
    assert (width, height) == (3, 2)
    assert rgb == bytes((200, 0, 0)) + bytes((10, 20, 30)) * 5
    assert b"\xff" not in rgb


def test_encode_rgb_png_refuses_a_canvas_with_transparency() -> None:
    clear = _solid(2, 2, Rgba(10, 20, 30, 255))
    clear.set_pixel(1, 1, Rgba(10, 20, 30, 0))
    with pytest.raises(RasterError, match="needs an opaque canvas"):
        encode_rgb_png(clear)
    faded = _solid(1, 1, Rgba(10, 20, 30, 254))
    with pytest.raises(RasterError, match="needs an opaque canvas"):
        encode_rgb_png(faded)


def test_write_png_writes_the_same_bytes_it_returns(tmp_path: Path) -> None:
    canvas = _solid(2, 3, Rgba(1, 2, 3, 4))
    destination = tmp_path / "icon.png"
    written = canvas.write_png(str(destination))
    assert written == destination.stat().st_size
    assert destination.read_bytes() == canvas.png_bytes()
    assert written == len(canvas.png_bytes())


def test_save_writes_the_canvas_at_its_own_size(tmp_path: Path) -> None:
    canvas = _solid(3, 3, Rgba(10, 20, 30, 255))
    destination = tmp_path / "mipmap.png"
    assert canvas.save(str(destination)) == destination.stat().st_size
    _, _, rgba = _png_to_rgba(destination.read_bytes())
    assert rgba == canvas.to_bytes()


def test_save_resamples_to_a_square_edge(tmp_path: Path) -> None:
    canvas = _solid(4, 2, Rgba(10, 20, 30, 255))
    destination = tmp_path / "mipmap.png"
    assert canvas.save(str(destination), max_side=2) == destination.stat().st_size
    width, height, rgba = _png_to_rgba(destination.read_bytes())
    assert (width, height) == (2, 2)
    assert rgba == canvas.resampled(2, 2).to_bytes()


def test_save_skips_the_resample_when_the_edge_already_matches(tmp_path: Path) -> None:
    canvas = _solid(2, 2, BLACK)
    destination = tmp_path / "same.png"
    assert canvas.save(str(destination), max_side=2) == destination.stat().st_size
    assert destination.read_bytes() == canvas.png_bytes()


# --- decoding through ffmpeg ------------------------------------------------


def test_decode_rgba_scales_and_wraps_the_raw_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rgba = _rgba_rows(((1, 2, 3, 4), (5, 6, 7, 8)), ((9, 10, 11, 12), (13, 14, 15, 16)))
    backend = _MediaBackend(decode_stdout=rgba)
    monkeypatch.setattr(raster.subprocess, "run", backend)
    decoded = decode_rgba("/tmp/art.png", side=2)
    assert (decoded.width, decoded.height) == (2, 2)
    assert decoded.to_bytes() == rgba
    assert backend.calls[0][0] == "ffmpeg"
    assert backend.calls[0][backend.calls[0].index("-i") + 1] == "/tmp/art.png"
    assert backend.calls[0][backend.calls[0].index("-vf") + 1] == "scale=2:2:flags=area"
    assert backend.calls[0][-5:] == ["-f", "rawvideo", "-pix_fmt", "rgba", "-"]


def test_decode_rgba_asks_ffprobe_for_the_native_size(monkeypatch: pytest.MonkeyPatch) -> None:
    rgba = _rgba_rows(((1, 2, 3, 4), (5, 6, 7, 8)), ((9, 10, 11, 12), (13, 14, 15, 16)))
    backend = _MediaBackend(decode_stdout=rgba, probe_size="2x3")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    decoded = decode_rgba("/tmp/art.png")
    assert (decoded.width, decoded.height) == (2, 2)
    assert [call[0] for call in backend.calls] == ["ffmpeg", "ffprobe"]
    assert backend.calls[1][-1] == "/tmp/art.png"


def test_decode_rgba_round_trips_the_encoder_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    canvas = Canvas(3, 3, TRANSPARENT)
    canvas.draw_line(0, 0, 2, 2, WHITE)
    canvas.fill_circle(1.0, 2.0, 1.0, Rgba(200, 30, 10, 200))
    data = canvas.png_bytes()
    width, height, rgba = _png_to_rgba(data)
    backend = _MediaBackend(decode_stdout=rgba, probe_size=f"{width}x{height}")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    decoded = decode_rgba("/tmp/icon.png")
    assert (decoded.width, decoded.height) == (3, 3)
    assert decoded.to_bytes() == canvas.to_bytes()


def test_decode_rgba_reports_a_refused_file(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _MediaBackend(decode_returncode=1, stderr=b"Invalid data found")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    with pytest.raises(RasterError, match="could not decode /tmp/bad.png: Invalid data found"):
        decode_rgba("/tmp/bad.png", side=4)


def test_decode_rgba_reports_a_missing_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _MediaBackend(missing=True)
    monkeypatch.setattr(raster.subprocess, "run", backend)
    with pytest.raises(RasterError, match="ffmpeg is not installed") as caught:
        decode_rgba("/tmp/art.png", side=4)
    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_decode_rgba_rejects_a_truncated_raw_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """A short ffmpeg stream is a codec failure, reported as one."""
    backend = _MediaBackend(decode_stdout=b"\x00" * 15)
    monkeypatch.setattr(raster.subprocess, "run", backend)
    with pytest.raises(RasterError, match="too short for a 2x2 RGBA image") as caught:
        decode_rgba("/tmp/art.png", side=2)
    assert isinstance(caught.value.__cause__, ValueError)
    assert backend.calls[0][0] == "ffmpeg"


# --- encoding through ffmpeg ------------------------------------------------


def test_encode_png_scales_on_disk_and_reports_the_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = _solid(2, 2, BLACK).png_bytes()
    backend = _MediaBackend(encode_payload=payload)
    monkeypatch.setattr(raster.subprocess, "run", backend)
    destination = tmp_path / "out.png"
    assert encode_png(str(tmp_path / "in.png"), str(destination), 96) == len(payload)
    assert destination.read_bytes() == payload
    argv = backend.calls[0]
    assert argv[0] == "ffmpeg"
    assert argv[argv.index("-vf") + 1] == "scale=96:96:flags=area"
    assert argv[-1] == str(destination)


def test_encode_png_reports_a_refused_job(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _MediaBackend(encode_returncode=1, stderr=b"codec not supported")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    with pytest.raises(RasterError, match="could not write /tmp/out.png: codec not supported"):
        encode_png("/tmp/in.png", "/tmp/out.png", 64)
    assert backend.calls[0][0] == "ffmpeg"


def test_encode_png_reports_a_missing_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(raster.subprocess, "run", _MediaBackend(missing=True))
    with pytest.raises(RasterError, match="ffmpeg is not installed") as caught:
        encode_png(str(tmp_path / "in.png"), str(tmp_path / "out.png"), 48)
    assert isinstance(caught.value.__cause__, FileNotFoundError)


# --- probing through ffprobe ------------------------------------------------


def test_probe_size_takes_the_smaller_edge(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _MediaBackend(probe_size="320x200")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    assert raster._probe_size("/tmp/art.png") == 200
    assert backend.calls[0][0] == "ffprobe"
    assert backend.calls[0][-1] == "/tmp/art.png"


def test_probe_size_reports_a_failed_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _MediaBackend(probe_returncode=1, stderr=b"No such file")
    monkeypatch.setattr(raster.subprocess, "run", backend)
    with pytest.raises(RasterError, match="could not measure /tmp/art.png: No such file"):
        raster._probe_size("/tmp/art.png")


def test_probe_size_reports_an_unusable_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    for text in ("", "wide", "NxH", "12"):
        backend = _MediaBackend(probe_size=text)
        monkeypatch.setattr(raster.subprocess, "run", backend)
        with pytest.raises(RasterError, match="unusable size"):
            raster._probe_size("/tmp/art.png")


def test_probe_size_reports_a_missing_ffprobe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(raster.subprocess, "run", _MediaBackend(missing=True))
    with pytest.raises(RasterError, match="ffprobe is not installed") as caught:
        raster._probe_size("/tmp/art.png")
    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_decode_rgba_reports_a_missing_ffprobe_from_the_probe_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The native-size path reaches ffprobe, which may be absent too."""
    monkeypatch.setattr(
        raster.subprocess, "run", _MediaBackend(decode_stdout=bytes(16), missing_probe=True)
    )
    with pytest.raises(RasterError, match="ffprobe is not installed") as caught:
        decode_rgba("/tmp/art.png")
    assert isinstance(caught.value.__cause__, FileNotFoundError)


# --- error type -------------------------------------------------------------


def test_raster_error_is_a_runtime_error() -> None:
    assert issubclass(RasterError, RuntimeError)
    assert str(RasterError("boom")) == "boom"
