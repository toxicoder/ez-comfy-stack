"""Hermetic tests for the ez_raster stdlib PNG decode path.

The fast core lane has no ffmpeg on PATH - the hermetic container and the
devcontainer both ship without it - so every PNG this package writes has to
come back out of the package again with nothing but ``zlib`` and ``struct``
behind it. The ffmpeg fall-through is exercised here too, against a scripted
``subprocess.run``, so the two paths are both covered on a host that has no
media binaries at all.
"""

from __future__ import annotations

import struct
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_raster as raster  # noqa: E402
from ez_raster import (  # noqa: E402
    BLACK,
    TRANSPARENT,
    WHITE,
    Canvas,
    RasterError,
    Rgba,
    decode_rgba,
    encode_rgb_png,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""The eight bytes every PNG file starts with."""


class _FakeMedia:
    """Stand-in for the host ffmpeg and ffprobe binaries.

    Args:
        stdout: Bytes ffmpeg writes for a decode job.
        probe_size: The ``WxH`` text ffprobe reports for a native-size probe.
    """

    def __init__(self, stdout: bytes = b"", probe_size: str = "4x4") -> None:
        self.stdout = stdout
        self.probe_size = probe_size
        self.calls: list[list[str]] = []

    def run(
        self, command: list[str], **_kwargs: Any
    ) -> subprocess.CompletedProcess[bytes]:
        """Record the invocation and answer with the scripted payload.

        Args:
            command: The argv ffmpeg or ffprobe was asked to run.
            _kwargs: Ignored subprocess options.

        Returns:
            A completed process carrying the scripted bytes.
        """
        self.calls.append(list(command))
        stdout = self.stdout if command[0] == "ffmpeg" else self.probe_size.encode()
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr=b"")

    @property
    def asked_for_ffmpeg(self) -> bool:
        """True when at least one recorded call invoked ffmpeg."""
        return any(call[0] == "ffmpeg" for call in self.calls)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    """Frame a payload as a PNG chunk.

    Args:
        kind: Four-character chunk type.
        payload: Chunk body.

    Returns:
        Length, type, body, and CRC.
    """
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _png(
    width: int,
    height: int,
    color_type: int,
    rows: bytes,
    bit_depth: int = 8,
    interlace: int = 0,
    extra: tuple[tuple[bytes, bytes], ...] = (),
) -> bytes:
    """Assemble a PNG file from already-filtered scanlines.

    Args:
        width: Frame width.
        height: Frame height.
        color_type: PNG colour type.
        rows: Filter byte plus sample bytes, repeated per scanline.
        bit_depth: Sample depth.
        interlace: Interlace flag; 1 means Adam7.
        extra: Further chunks appended after IDAT.

    Returns:
        Complete PNG file bytes.
    """
    header = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, interlace)
    body = PNG_SIGNATURE + _chunk(b"IHDR", header)
    for kind, payload in extra:
        body += _chunk(kind, payload)
    return body + _chunk(b"IDAT", zlib.compress(rows)) + _chunk(b"IEND", b"")


def _rgba_rows(pixels: list[Rgba], width: int, height: int, filter_type: int = 0) -> bytes:
    """Filter a pixel grid the way a PNG encoder would.

    Args:
        pixels: Row-major pixels, ``width * height`` of them.
        width: Frame width.
        height: Frame height.
        filter_type: One of the five PNG scanline filters.

    Returns:
        Filter byte plus filtered bytes for every scanline.
    """
    stride = width * 4
    previous = bytearray(stride)
    rows = bytearray()
    for row in range(height):
        line = bytearray()
        for column in range(width):
            line += bytes(pixels[row * width + column].as_tuple())
        filtered = bytearray(stride)
        for index in range(stride):
            left = line[index - 4] if index >= 4 else 0
            up = previous[index]
            up_left = previous[index - 4] if index >= 4 else 0
            raw = line[index]
            if filter_type == 0:
                value = raw
            elif filter_type == 1:
                value = raw - left
            elif filter_type == 2:
                value = raw - up
            elif filter_type == 3:
                value = raw - (left + up) // 2
            else:
                value = raw - _paeth(left, up, up_left)
            filtered[index] = value & 0xFF
        rows.append(filter_type)
        rows += filtered
        previous[:] = line
    return bytes(rows)


def _paeth(left: int, above: int, above_left: int) -> int:
    """Return the PNG Paeth predictor for three neighbours.

    Args:
        left: Sample to the left.
        above: Sample above.
        above_left: Sample above and to the left.

    Returns:
        The neighbour closest to ``left + above - above_left``.
    """
    estimate = left + above - above_left
    distances = (abs(estimate - left), abs(estimate - above), abs(estimate - above_left))
    return (left, above, above_left)[distances.index(min(distances))]


def _grid(width: int, height: int, colors: list[Rgba]) -> list[Rgba]:
    """Return a row-major pixel grid.

    Args:
        width: Frame width.
        height: Frame height.
        colors: One colour per pixel, row-major.

    Returns:
        The grid, unchanged, once its size is checked.
    """
    assert len(colors) == width * height, "the grid matches its declared size"
    return colors


def _write(tmp_path: Path, name: str, payload: bytes) -> str:
    """Put bytes on disk and return the path.

    Args:
        tmp_path: Directory to write into.
        name: File name.
        payload: File content.

    Returns:
        The path as a string.
    """
    path = tmp_path / name
    path.write_bytes(payload)
    return str(path)


def test_a_file_this_package_wrote_comes_back_without_a_host_binary(
    tmp_path: Path,
) -> None:
    """The validator has to read its own output on a hermetic host.

    A pack that cannot be validated without ffmpeg is unusable in the fast core
    lane, in the devcontainer, and on any CI runner, so the round trip has to
    close inside the package.
    """
    canvas = Canvas(3, 3)
    canvas.fill(BLACK)
    canvas.set_pixel(0, 0, Rgba(10, 20, 30, 128))
    canvas.set_pixel(2, 2, Rgba(200, 10, 5, 255))
    path = _write(tmp_path, "self.png", canvas.png_bytes())

    decoded = decode_rgba(path)

    assert decoded.width == 3 and decoded.height == 3, "the frame keeps its size"
    assert decoded.pixel(0, 0) == Rgba(10, 20, 30, 128), "the blended pixel survives"
    assert decoded.pixel(2, 2) == Rgba(200, 10, 5, 255), "the opaque pixel survives"
    assert decoded.pixel(1, 0) == BLACK, "the filled pixel survives"


def test_a_written_file_scales_to_the_requested_square(tmp_path: Path) -> None:
    """The layers are measured at a fixed dp edge, so decode scales on the way in.

    ``Canvas.resampled`` is the same box filter the writer uses, which keeps a
    solid glyph exactly its own colour instead of shifting it a step.
    """
    canvas = Canvas(4, 4)
    canvas.fill(Rgba(40, 80, 120, 255))
    path = _write(tmp_path, "solid.png", canvas.png_bytes())

    decoded = decode_rgba(path, 2)

    assert (decoded.width, decoded.height) == (2, 2), "scaled to the asked edge"
    assert decoded.pixel(0, 0) == Rgba(40, 80, 120, 255), "a solid fill stays exact"


def test_a_side_matching_the_native_size_is_not_resampled(tmp_path: Path) -> None:
    """A layer already authored at its measurement edge must survive untouched.

    The safe-zone gate compares pixel columns, so a 108 dp layer decoded at 108
    has to be the identity or the gate measures resampling noise.
    """
    canvas = Canvas(4, 4)
    canvas.fill(TRANSPARENT)
    canvas.fill_rect(0, 0, 2, 2, WHITE)
    path = _write(tmp_path, "identity.png", canvas.png_bytes())

    decoded = decode_rgba(path, 4)

    assert decoded.pixel(0, 0) == WHITE, "the drawn block is where it was"
    assert decoded.pixel(3, 3) == TRANSPARENT, "the untouched corner stays clear"


def test_an_rgb_file_is_promoted_to_opaque_rgba(tmp_path: Path) -> None:
    """A 24-bit alpha-free banner has to be readable too.

    ``encode_rgb_png`` writes the colour type a Play feature graphic is
    required to use, so the decoder promotes it with a fully opaque alpha
    rather than refusing it.
    """
    canvas = Canvas(2, 2)
    canvas.fill(Rgba(7, 14, 21, 255))
    path = _write(tmp_path, "banner.png", encode_rgb_png(canvas))

    decoded = decode_rgba(path)

    assert (decoded.width, decoded.height) == (2, 2), "the frame keeps its size"
    assert decoded.pixel(1, 1) == Rgba(7, 14, 21, 255), "opaque alpha is added"


def test_a_grey_file_becomes_neutral_rgba(tmp_path: Path) -> None:
    """Grayscale is the natural encoding of a monochrome launcher layer.

    A themed layer exported as colour type 0 still has to measure, and grey
    samples land on all three colour channels.
    """
    rows = bytes([0, 0, 64, 0, 192, 255])
    path = _write(tmp_path, "grey.png", _png(2, 2, 0, rows))

    decoded = decode_rgba(path)

    assert decoded.pixel(0, 0) == Rgba(0, 0, 0, 255), "black grey"
    assert decoded.pixel(1, 0) == Rgba(64, 64, 64, 255), "a mid grey on every channel"
    assert decoded.pixel(1, 1) == Rgba(255, 255, 255, 255), "white grey"


def test_a_grey_alpha_file_keeps_its_alpha(tmp_path: Path) -> None:
    """Colour type 4 carries grey and alpha side by side."""
    rows = bytes([0, 200, 40, 0, 20, 0, 0, 0, 0, 0])
    path = _write(tmp_path, "grey_alpha.png", _png(2, 2, 4, rows))

    decoded = decode_rgba(path)

    assert decoded.pixel(0, 0) == Rgba(200, 200, 200, 40), "grey with a partial alpha"
    assert decoded.pixel(1, 1) == TRANSPARENT, "a cleared pixel is fully transparent"


@pytest.mark.parametrize("filter_type", [0, 1, 2, 3, 4])
def test_every_scanline_filter_reconstructs_the_same_pixels(
    tmp_path: Path, filter_type: int
) -> None:
    """Real encoders pick per-row filters, so the gate must follow all five.

    A file from a design tool is free to switch filter per scanline; reading
    only the filter this package writes would call a valid pack unreadable.
    """
    pixels = _grid(
        3,
        3,
        [
            Rgba(10, 20, 30, 255),
            Rgba(200, 100, 50, 128),
            TRANSPARENT,
            Rgba(1, 2, 3, 4),
            Rgba(250, 240, 230, 255),
            Rgba(64, 64, 64, 8),
            Rgba(0, 255, 0, 255),
            Rgba(255, 0, 255, 1),
            Rgba(128, 127, 126, 125),
        ],
    )
    rows = _rgba_rows(pixels, 3, 3, filter_type)
    path = _write(tmp_path, f"filter-{filter_type}.png", _png(3, 3, 6, rows))

    decoded = decode_rgba(path)

    assert [decoded.pixel(x, y) for y in range(3) for x in range(3)] == pixels, (
        f"filter type {filter_type} reconstructs exactly"
    )


def test_a_wide_frame_is_box_averaged_into_a_square(tmp_path: Path) -> None:
    """A feature graphic is 1024x500 and is measured as a square.

    Averaging two half-regions is the arithmetic the store screenshot and the
    alpha gate both rest on, so the expected value is written out here.
    """
    pixels = _grid(
        4,
        2,
        [
            Rgba(0, 0, 0, 255),
            Rgba(200, 100, 50, 255),
            Rgba(200, 100, 50, 255),
            Rgba(0, 0, 0, 255),
            Rgba(0, 0, 0, 255),
            Rgba(200, 100, 50, 255),
            Rgba(200, 100, 50, 255),
            Rgba(0, 0, 0, 255),
        ],
    )
    rows = _rgba_rows(pixels, 4, 2, 0)
    path = _write(tmp_path, "wide.png", _png(4, 2, 6, rows))

    decoded = decode_rgba(path, 2)

    assert decoded.pixel(0, 0) == Rgba(100, 50, 25, 255), "two-sample box average"
    assert decoded.pixel(1, 1) == Rgba(100, 50, 25, 255), "the mirrored box agrees"


def test_a_frame_without_a_requested_side_keeps_its_leading_square(
    tmp_path: Path,
) -> None:
    """A native-size read of a non-square frame crops like the ffmpeg path did.

    ffmpeg handed back the whole raw stream and the wrapper kept the first
    ``min(w, h)`` rows, which is the top-left square; the stdlib path has to
    agree or a native-size read changes meaning between hosts.
    """
    pixels = _grid(
        3,
        1,
        [Rgba(11, 11, 11, 255), Rgba(22, 22, 22, 255), Rgba(33, 33, 33, 255)],
    )
    rows = _rgba_rows(pixels, 3, 1, 0)
    path = _write(tmp_path, "strip.png", _png(3, 1, 6, rows))

    decoded = decode_rgba(path)

    assert (decoded.width, decoded.height) == (1, 1), "the shorter edge wins"
    assert decoded.pixel(0, 0) == Rgba(11, 11, 11, 255), "the crop starts at the top-left"


def test_a_transparent_rgb_colour_is_read_as_transparent(tmp_path: Path) -> None:
    """A 24-bit PNG can still carry transparency through tRNS.

    ffmpeg folds tRNS into the alpha channel it reports, and the feature
    graphic gate depends on that: a banner that claims to be 24-bit while
    hiding a transparent colour is exactly what Play rejects.
    """
    row_one = bytes([0, 255, 0, 0, 0, 255, 0])
    row_two = bytes([0, 0, 0, 255, 1, 2, 3])
    payload = struct.pack(">HHH", 1, 2, 3)
    path = _write(
        tmp_path,
        "trns_rgb.png",
        _png(2, 2, 2, row_one + row_two, extra=((b"tRNS", payload),)),
    )

    decoded = decode_rgba(path)

    assert decoded.pixel(1, 1) == Rgba(1, 2, 3, 0), "the keyed colour is transparent"
    assert decoded.pixel(0, 0) == Rgba(255, 0, 0, 255), "the others stay opaque"


def test_a_keyed_grey_value_is_read_as_transparent(tmp_path: Path) -> None:
    """tRNS keys one grey sample for colour type 0 as well."""
    rows = bytes([0, 0, 128]) + bytes([0, 255, 255])
    path = _write(
        tmp_path, "trns_grey.png", _png(2, 2, 0, rows, extra=((b"tRNS", b"\x00\x80"),))
    )

    decoded = decode_rgba(path)

    assert decoded.pixel(1, 0) == Rgba(128, 128, 128, 0), "the keyed grey is transparent"
    assert decoded.pixel(0, 0) == Rgba(0, 0, 0, 255), "black stays opaque"


def test_an_oversized_png_is_left_to_the_media_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The in-process read is bounded, so no file can exhaust the host's memory.

    The cap sits far above any icon or banner a pack ships. Past it the file
    goes to ffmpeg, which streams rather than buffering the whole thing, which
    is what the operator got before the codec existed.
    """
    canvas = Canvas(8, 8)
    canvas.fill(BLACK)
    path = _write(tmp_path, "big.png", canvas.png_bytes())
    backend = _FakeMedia(stdout=bytes(4 * 4 * 4), probe_size="4x4")
    monkeypatch.setattr(raster.subprocess, "run", backend.run)
    monkeypatch.setattr(raster, "_MAX_DECODE_BYTES", 32)

    decode_rgba(path, 4)

    assert backend.asked_for_ffmpeg, "a file over the cap is ffmpeg's to stream"


def test_a_file_that_is_not_a_png_still_reaches_the_media_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Operator art arrives as JPEG and WebP, which only ffmpeg reads."""
    backend = _FakeMedia(stdout=bytes(range(64)), probe_size="4x4")
    monkeypatch.setattr(raster.subprocess, "run", backend.run)
    path = _write(tmp_path, "photo.jpg", b"\xff\xd8\xff\xe0not a png at all")

    decoded = decode_rgba(path, 4)

    assert backend.asked_for_ffmpeg, "a non-PNG is handed to ffmpeg"
    assert decoded.pixel(3, 3) == Rgba(60, 61, 62, 63), "the ffmpeg stream is wrapped"


def test_a_missing_file_reaches_the_media_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A path that does not exist is ffmpeg's complaint to make."""
    backend = _FakeMedia(stdout=bytes(64), probe_size="4x4")
    monkeypatch.setattr(raster.subprocess, "run", backend.run)

    decoded = decode_rgba("/tmp/no-such-frame.png", 4)

    assert backend.asked_for_ffmpeg, "the probe is what reports the missing file"
    assert decoded.pixel(0, 0) == TRANSPARENT, "the scripted stream wrapped"


@pytest.mark.parametrize(
    ("colour_type", "depth", "interlace"),
    [(6, 16, 0), (6, 8, 1), (3, 8, 0), (0, 4, 0), (2, 4, 0)],
)
def test_a_variant_this_codec_does_not_carry_falls_through_to_the_media_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, colour_type: int, depth: int, interlace: int
) -> None:
    """16-bit, Adam7, palette, and sub-byte grey stay ffmpeg's job.

    Falling through costs nothing where ffmpeg exists and keeps the codec small
    where it does not; the capability ceiling of the hermetic path is stated in
    the module rather than silently lowering what operators could do before.
    """
    channels = {0: 1, 2: 3, 3: 1, 6: 4}[colour_type]
    bytes_per_row = max(1, depth * channels * 4 // 8)
    rows = b"".join(bytes([0]) + bytes([7]) * bytes_per_row for _ in range(2))
    path = _write(
        tmp_path,
        "exotic.png",
        _png(4, 2, colour_type, rows, bit_depth=depth, interlace=interlace),
    )
    backend = _FakeMedia(stdout=bytes(4 * 4 * 4), probe_size="4x4")
    monkeypatch.setattr(raster.subprocess, "run", backend.run)

    decode_rgba(path, 4)

    assert backend.asked_for_ffmpeg, (
        f"colour type {colour_type} depth {depth} interlace {interlace} falls through"
    )


def test_a_variant_the_codec_cannot_read_reports_a_missing_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no ffmpeg either, the operator hears the honest reason.

    A 16-bit icon on a hermetic host is unsupported rather than corrupt, and the
    message has to name the missing tool the way every other ffmpeg path does.
    """
    path = _write(tmp_path, "deep.png", _png(4, 2, 6, bytes(1 + 4 * 8 * 2) * 2, bit_depth=16))

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(raster.subprocess, "run", refuse)

    with pytest.raises(RasterError, match="ffmpeg is not installed"):
        decode_rgba(path, 4)


def test_a_chunk_cut_mid_body_is_reported(tmp_path: Path) -> None:
    """A chunk header that promises more file than exists is corruption."""
    canvas = Canvas(4, 4)
    canvas.fill(WHITE)
    payload = canvas.png_bytes()
    path = _write(tmp_path, "cut-body.png", payload[:-3])

    with pytest.raises(RasterError, match="inside a chunk"):
        decode_rgba(path)


def test_a_truncated_file_reports_the_frame_it_broke_on(tmp_path: Path) -> None:
    """A PNG that stops before IEND never claimed to be complete."""
    canvas = Canvas(4, 4)
    canvas.fill(WHITE)
    payload = canvas.png_bytes()
    path = _write(tmp_path, "half.png", payload[:-6])

    with pytest.raises(RasterError, match="before its IEND"):
        decode_rgba(path)


def test_a_useless_transparency_chunk_is_ignored(tmp_path: Path) -> None:
    """tRNS on a file that already has alpha means nothing and must not bite.

    Some encoders emit the chunk anyway. The colour type decides whether there
    is a sample to key, and a truecolour-with-alpha file has none, so the
    decode proceeds on its own alpha channel.
    """
    rows = bytes([0, 10, 20, 30, 128, 200, 100, 50, 255]) * 2
    path = _write(
        tmp_path,
        "spurious-trns.png",
        _png(2, 2, 6, rows, extra=((b"tRNS", struct.pack(">HHH", 10, 20, 30)),)),
    )

    decoded = decode_rgba(path)

    assert decoded.pixel(0, 0) == Rgba(10, 20, 30, 128), "its own alpha still governs"
    assert decoded.pixel(1, 1) == Rgba(200, 100, 50, 255), "no colour was keyed out"


def test_a_bad_chunk_crc_is_reported(tmp_path: Path) -> None:
    """A chunk whose CRC disagrees with its body is corruption."""
    payload = bytearray(_png(1, 1, 6, bytes([0, 1, 2, 3, 4])))
    payload[-1] ^= 0xFF
    path = _write(tmp_path, "crc.png", bytes(payload))

    with pytest.raises(RasterError, match="(?i)crc"):
        decode_rgba(path)


def test_a_file_without_ihdr_is_reported(tmp_path: Path) -> None:
    """The header chunk has to come first or the frame is unmeasurable."""
    payload = PNG_SIGNATURE + _chunk(b"IDAT", zlib.compress(bytes([0, 1, 2, 3, 4])))
    path = _write(tmp_path, "no-ihdr.png", payload + _chunk(b"IEND", b""))

    with pytest.raises(RasterError, match="(?i)ihdr"):
        decode_rgba(path)


def test_a_second_ihdr_is_reported(tmp_path: Path) -> None:
    """A file that declares its geometry twice is not readable as one frame."""
    header = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    payload = (
        PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes([0, 1, 2, 3, 4])))
        + _chunk(b"IEND", b"")
    )
    path = _write(tmp_path, "two-headers.png", payload)

    with pytest.raises(RasterError, match="twice"):
        decode_rgba(path)


def test_an_ihdr_too_short_to_measure_is_reported(tmp_path: Path) -> None:
    """A truncated header is refused rather than unpacked into nonsense."""
    payload = (
        PNG_SIGNATURE
        + _chunk(b"IHDR", b"\x00\x00\x00\x01")
        + _chunk(b"IDAT", zlib.compress(bytes([0, 1, 2, 3, 4])))
        + _chunk(b"IEND", b"")
    )
    path = _write(tmp_path, "thin-header.png", payload)

    with pytest.raises(RasterError, match="too short"):
        decode_rgba(path)


def test_a_transparency_chunk_before_the_header_is_reported(tmp_path: Path) -> None:
    """tRNS has no meaning until the header says which colour type it keys."""
    payload = (
        PNG_SIGNATURE
        + _chunk(b"tRNS", b"\x00\x80")
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes([0, 0, 128, 255, 255])))
        + _chunk(b"IEND", b"")
    )
    path = _write(tmp_path, "early-trns.png", payload)

    with pytest.raises(RasterError, match="before its IHDR"):
        decode_rgba(path)


def test_an_unknown_scanline_filter_is_reported(tmp_path: Path) -> None:
    """A filter byte outside the five defined types is not a decoding guess."""
    path = _write(tmp_path, "wild-filter.png", _png(1, 1, 6, bytes([9, 1, 2, 3, 4])))

    with pytest.raises(RasterError, match="not a defined filter"):
        decode_rgba(path)


def test_a_file_without_idat_is_reported(tmp_path: Path) -> None:
    """A PNG with no image data has nothing to decode."""
    payload = PNG_SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
    path = _write(tmp_path, "no-idat.png", payload + _chunk(b"IEND", b""))

    with pytest.raises(RasterError, match="(?i)idat"):
        decode_rgba(path)


def test_image_data_split_across_chunks_is_rejoined(tmp_path: Path) -> None:
    """Encoders are allowed to emit several IDAT chunks for one frame.

    An optimiser or a streaming writer splits the zlib stream at will, so the
    decoder has to concatenate before inflating rather than read the first
    chunk and call the rest noise.
    """
    rows = bytes([0, 10, 20, 30, 255, 1, 2, 3, 4]) + bytes([0, 7, 6, 5, 255, 4, 5, 6, 255])
    compressed = zlib.compress(rows)
    header = struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)
    payload = (
        PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", compressed[:3])
        + _chunk(b"IDAT", compressed[3:])
        + _chunk(b"IEND", b"")
    )
    path = _write(tmp_path, "split-idat.png", payload)

    decoded = decode_rgba(path)

    assert decoded.pixel(0, 0) == Rgba(10, 20, 30, 255), "the pieces inflated together"
    assert decoded.pixel(1, 0) == Rgba(1, 2, 3, 4), "the tail survived the split"


def test_a_frame_larger_than_the_module_allows_is_refused(tmp_path: Path) -> None:
    """The allocation ceiling guards a mistyped or hostile header.

    ``_MAX_PIXELS`` already bounds what a canvas may be; a decoder that trusted
    IHDR would let a 32-byte file ask for a 64 million pixel buffer.
    """
    payload = PNG_SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", 8000, 8000, 8, 6, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(bytes([0]))) + _chunk(b"IEND", b"")
    path = _write(tmp_path, "huge.png", payload)

    with pytest.raises(RasterError, match="pixels"):
        decode_rgba(path)


def test_an_idat_that_expands_past_the_frame_is_refused(tmp_path: Path) -> None:
    """A compressed payload far bigger than its own frame is a decompression bomb."""
    payload = PNG_SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(b"\x00" * 400_000)) + _chunk(b"IEND", b"")
    path = _write(tmp_path, "bomb.png", payload)

    with pytest.raises(RasterError, match="larger"):
        decode_rgba(path)


def test_an_unusable_zlib_stream_is_reported(tmp_path: Path) -> None:
    """Inflatable bytes are part of the file format, not a given."""
    payload = PNG_SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0))
    payload += _chunk(b"IDAT", b"this is not a zlib stream") + _chunk(b"IEND", b"")
    path = _write(tmp_path, "raw.png", payload)

    with pytest.raises(RasterError, match="zlib"):
        decode_rgba(path)


def test_a_frame_whose_data_is_too_short_is_reported(tmp_path: Path) -> None:
    """A frame that stops mid-scanline cannot be measured honestly."""
    payload = PNG_SIGNATURE + _chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 6, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(bytes([0, 1, 2, 3, 4]))) + _chunk(b"IEND", b"")
    path = _write(tmp_path, "short.png", payload)

    with pytest.raises(RasterError, match="scanline"):
        decode_rgba(path)
