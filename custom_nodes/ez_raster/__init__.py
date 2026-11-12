"""Sellable Android asset packs: raster canvas and a stdlib PNG codec.

The icon and watch-face packs both need the same two things, and neither is
in the hermetic dependency set: a way to composite RGBA pixels, and a way to
put the result on disk as a PNG. PIL is not pinned for tests, so this module
carries both, on ``zlib`` and ``struct`` only.

Decoding lives here too, for the files this package writes and for the 8-bit
truecolour and greyscale types an icon pack is normally authored as: a pack
that could only be validated by shelling out to ffmpeg could not be validated
in the hermetic fast core lane, in the devcontainer, or on a CI runner at all.
The codec reads chunk framing, all five scanline filters, ``tRNS`` keying, and
promotes to RGBA8888 on ``zlib`` and ``struct`` alone. 16-bit samples, Adam7
interlacing, palette, and sub-byte greyscale files are outside its scope and
fall through to ffmpeg, which reads them where the host has it.

Encoding stays here because the bytes this package writes are simple,
deterministic, and must be byte-identical between runs so a drift test can pin
them.
"""

from __future__ import annotations

import os
import struct
import subprocess
import zlib
from dataclasses import dataclass

# PNG signature, chunk types, and the colour-type constants.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CHUNK_IHDR = b"IHDR"
_CHUNK_IDAT = b"IDAT"
_CHUNK_IEND = b"IEND"
_COLOR_TYPE_RGBA = 6
_COLOR_TYPE_RGB = 2
_BIT_DEPTH_8 = 8
_FILTER_NONE = 0

# The rest of the decode side: the transparency chunk, the IHDR body length,
# the interlace value a non-Adam7 file carries, the four filter types beyond
# "none", and the colour types whose sample count this codec can promote.
_CHUNK_T_RNS = b"tRNS"
_IHDR_BYTES = 13
_INTERLACE_NONE = 0
_FILTER_SUB = 1
_FILTER_UP = 2
_FILTER_AVERAGE = 3
_FILTER_PAETH = 4
_COLOR_TYPE_GRAY = 0
_COLOR_TYPE_GRAY_ALPHA = 4
_CHANNEL_COUNTS: dict[int, int] = {
    _COLOR_TYPE_GRAY: 1,
    _COLOR_TYPE_RGB: 3,
    _COLOR_TYPE_GRAY_ALPHA: 2,
    _COLOR_TYPE_RGBA: 4,
}

# ``tRNS`` stores one 16-bit sample per channel for these colour types, and is
# not defined for the two that already carry an alpha channel.
_TRNS_SAMPLES: dict[int, int] = {_COLOR_TYPE_GRAY: 1, _COLOR_TYPE_RGB: 3}

# Bytes per pixel this module carries. 32-bit RGBA is what the Play Store and
# the Android mipmap tree both expect for launcher icons.
_BYTES_PER_PIXEL = 4

# Largest canvas this module will allocate, in pixels. Guards an operator
# against a typo that asks for a 100000x100000 icon sheet.
_MAX_PIXELS = 16_000_000

# Density buckets an Android launcher resolves, and the launcher icon edge
# each one expects. 48 / 72 / 96 / 144 / 192 is the mipmap ladder.
MIPMAP_DENSITIES: tuple[tuple[str, int], ...] = (
    ("mdpi", 48),
    ("hdpi", 72),
    ("xhdpi", 96),
    ("xxhdpi", 144),
    ("xxxhdpi", 192),
)

# The adaptive-icon canvas is 108 dp with a 72 dp safe zone: 66.7 percent of
# the sheet stays visible once the launcher masks it.
ADAPTIVE_CANVAS_DP = 108
ADAPTIVE_SAFE_DP = 72
ADAPTIVE_SAFE_RATIO = ADAPTIVE_SAFE_DP / ADAPTIVE_CANVAS_DP

# Play Store launcher icon and feature graphic sizes.
PLAY_LAUNCHER_ICON_PX = 512
PLAY_FEATURE_GRAPHIC_WIDTH = 1024
PLAY_FEATURE_GRAPHIC_HEIGHT = 500


class RasterError(RuntimeError):
    """Raised when a canvas or an ffmpeg raster step cannot be completed."""


class _NeedsMediaBackend(RasterError):
    """Raised internally when a PNG is valid but outside the stdlib codec.

    16-bit samples, Adam7 interlacing, palette images, and sub-byte greyscale
    are the variants ffmpeg reads and this module does not. ``decode_rgba``
    catches this and falls through to the media backend, so a healthy file is
    never reported as a corrupt one.
    """


@dataclass(frozen=True)
class Rgba:
    """One 8-bit RGBA colour.

    Args:
        red: 0 to 255.
        green: 0 to 255.
        blue: 0 to 255.
        alpha: 0 to 255, where 0 is fully transparent.
    """

    red: int = 0
    green: int = 0
    blue: int = 0
    alpha: int = 255

    def __post_init__(self) -> None:
        """Reject a channel the format cannot carry.

        Raises:
            ValueError: any channel is outside 0 to 255.
        """
        for name, value in (
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
            ("alpha", self.alpha),
        ):
            if not 0 <= value <= 255:
                raise ValueError(f"{name} {value} outside 0..255")

    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return the channel quad.

        Returns:
            ``(red, green, blue, alpha)``.
        """
        return (self.red, self.green, self.blue, self.alpha)

    def blended_over(self, base: Rgba) -> Rgba:
        """Composite this colour over an opaque base.

        Args:
            base: Colour underneath.
        Returns:
            The visible colour after alpha compositing.
        """
        source = self.alpha / 255.0
        behind = 1.0 - source
        return Rgba(
            red=round(self.red * source + base.red * behind),
            green=round(self.green * source + base.green * behind),
            blue=round(self.blue * source + base.blue * behind),
            alpha=255,
        )


TRANSPARENT = Rgba(0, 0, 0, 0)
"""Fully clear pixel, the canvas default."""

BLACK = Rgba(0, 0, 0, 255)
"""Opaque black, the ambient watch-face ground."""

WHITE = Rgba(255, 255, 255, 255)
"""Opaque white, used for key lines and masks."""


def hex_to_rgba(value: str) -> Rgba:
    """Parse a CSS-style hex colour.

    Args:
        value: ``#RGB``, ``#RRGGBB``, or ``#RRGGBBAA``; the hash is optional.
    Returns:
        Parsed colour, opaque when no alpha was given.
    Raises:
        ValueError: the string is not one of the three accepted shapes.
    """
    text = value.strip().removeprefix("#").strip()
    if len(text) == 3:
        text = "".join(character * 2 for character in text)
    if len(text) not in (6, 8):
        raise ValueError(f"not a hex colour: {value!r}")
    try:
        channels = [int(text[index : index + 2], 16) for index in range(0, len(text), 2)]
    except ValueError as exc:
        raise ValueError(f"not a hex colour: {value!r}") from exc
    if len(channels) == 3:
        channels.append(255)
    return Rgba(*channels)


def rgba_to_hex(color: Rgba, include_alpha: bool = False) -> str:
    """Format a colour as the uppercase hex string the asset XML uses.

    Args:
        color: Colour to format.
        include_alpha: Append the alpha byte, which is what the Watch Face
            Format's ``colors`` attribute wants.
    Returns:
        Something like ``#1A2B3C`` or ``#1A2B3CFF``.
    """
    if include_alpha:
        return f"#{color.red:02X}{color.green:02X}{color.blue:02X}{color.alpha:02X}"
    return f"#{color.red:02X}{color.green:02X}{color.blue:02X}"


class Canvas:
    """An RGBA pixel buffer this module can draw into and encode.

    Args:
        width: Canvas width in pixels, at least 1.
        height: Canvas height in pixels, at least 1.
        fill: Colour every pixel starts as.
    """

    def __init__(self, width: int, height: int, fill: Rgba = TRANSPARENT) -> None:
        """Allocate the buffer.

        Raises:
            ValueError: a side is below 1 or the area is past the guard.
        """
        if width < 1 or height < 1:
            raise ValueError(f"canvas {width}x{height} must be at least 1x1")
        if width * height > _MAX_PIXELS:
            raise ValueError(f"canvas {width}x{height} exceeds {_MAX_PIXELS} pixels")
        self.width = width
        self.height = height
        self._pixels = bytearray(width * height * _BYTES_PER_PIXEL)
        self.fill(fill)

    @property
    def pixels(self) -> bytearray:
        """Return the raw row-major RGBA bytes.

        Returns:
            The live buffer, so a caller may bulk-edit it.
        """
        return self._pixels

    def to_bytes(self) -> bytes:
        """Return a copy of the raw RGBA bytes.

        Returns:
            ``width * height * 4`` bytes.
        """
        return bytes(self._pixels)

    def fill(self, color: Rgba) -> None:
        """Paint every pixel one colour.

        Args:
            color: Colour to write.
        """
        quad = bytes(color.as_tuple())
        self._pixels[:] = quad * (self.width * self.height)

    def set_pixel(self, x: int, y: int, color: Rgba) -> None:
        """Write one pixel, ignoring a coordinate outside the canvas.

        Args:
            x: Column.
            y: Row.
            color: Colour to write.
        """
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return
        offset = (y * self.width + x) * _BYTES_PER_PIXEL
        self._pixels[offset : offset + _BYTES_PER_PIXEL] = bytes(color.as_tuple())

    def pixel(self, x: int, y: int) -> Rgba:
        """Read one pixel.

        Args:
            x: Column.
            y: Row.
        Returns:
            Colour at that position, or fully transparent outside the canvas.
        """
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return TRANSPARENT
        offset = (y * self.width + x) * _BYTES_PER_PIXEL
        chunk = self._pixels[offset : offset + _BYTES_PER_PIXEL]
        return Rgba(chunk[0], chunk[1], chunk[2], chunk[3])

    def fill_rect(self, x: int, y: int, width: int, height: int, color: Rgba) -> None:
        """Paint an axis-aligned block.

        Args:
            x: Left column.
            y: Top row.
            width: Block width.
            height: Block height.
            color: Colour to write.
        """
        for row in range(max(0, y), min(self.height, y + height)):
            base = (row * self.width + max(0, x)) * _BYTES_PER_PIXEL
            stop = (row * self.width + min(self.width, x + width)) * _BYTES_PER_PIXEL
            self._pixels[base:stop] = bytes(color.as_tuple()) * ((stop - base) // 4)

    def fill_circle(
        self, centre_x: float, centre_y: float, radius: float, color: Rgba
    ) -> None:
        """Paint a disc with a one-pixel antialiased rim.

        Args:
            centre_x: Disc centre column.
            centre_y: Disc centre row.
            radius: Radius in pixels; nothing is drawn at or below zero.
            color: Colour to write.
        """
        if radius <= 0.0:
            return
        left = max(0, int(centre_x - radius))
        right = min(self.width - 1, int(centre_x + radius))
        top = max(0, int(centre_y - radius))
        bottom = min(self.height - 1, int(centre_y + radius))
        inner = (radius - 1.0) * (radius - 1.0)
        outer = (radius + 1.0) * (radius + 1.0)
        for row in range(top, bottom + 1):
            dy = row + 0.5 - centre_y - 0.5
            for column in range(left, right + 1):
                dx = column + 0.5 - centre_x - 0.5
                distance = dx * dx + dy * dy
                if distance <= inner:
                    self.set_pixel(column, row, color)
                elif distance <= outer:
                    coverage = (outer - distance) / (outer - inner)
                    self.set_pixel(column, row, _scale_alpha(color, coverage))

    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: Rgba,
        thickness: int = 1,
    ) -> None:
        """Draw a line with an integer thickness.

        Args:
            x0: Start column.
            y0: Start row.
            x1: End column.
            y1: End row.
            color: Colour to write.
            thickness: Stroke width in pixels, at least 1.
        """
        half = max(0, (thickness - 1) // 2)
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for step in range(steps + 1):
            column = x0 + round((x1 - x0) * step / steps)
            row = y0 + round((y1 - y0) * step / steps)
            self.fill_rect(column - half, row - half, thickness, thickness, color)

    def masked(self, mask: Canvas) -> Canvas:
        """Return a copy with another canvas used as an alpha mask.

        Args:
            mask: Mask of the same size; its red channel drives alpha.
        Returns:
            New canvas whose alpha is this canvas's alpha times the mask.
        Raises:
            ValueError: the mask is not the same size.
        """
        if mask.width != self.width or mask.height != self.height:
            raise ValueError(f"mask {mask.width}x{mask.height} does not match canvas")
        out = Canvas(self.width, self.height)
        for index in range(self.width * self.height):
            offset = index * _BYTES_PER_PIXEL
            alpha = self._pixels[offset + 3] * mask._pixels[offset] // 255
            out._pixels[offset : offset + 4] = bytes(
                (
                    self._pixels[offset],
                    self._pixels[offset + 1],
                    self._pixels[offset + 2],
                    alpha,
                )
            )
        return out

    def composited_over(self, base: Canvas) -> Canvas:
        """Return this canvas alpha-composited onto an opaque base.

        Args:
            base: Canvas underneath; must be the same size.
        Returns:
            New canvas holding the result.
        Raises:
            ValueError: the two canvases differ in size.
        """
        if base.width != self.width or base.height != self.height:
            raise ValueError("canvases must be the same size to composite")
        out = Canvas(self.width, self.height)
        for index in range(self.width * self.height):
            offset = index * _BYTES_PER_PIXEL
            source = Rgba(
                self._pixels[offset],
                self._pixels[offset + 1],
                self._pixels[offset + 2],
                self._pixels[offset + 3],
            )
            behind = Rgba(
                base._pixels[offset],
                base._pixels[offset + 1],
                base._pixels[offset + 2],
                255,
            )
            out._pixels[offset : offset + 4] = bytes(source.blended_over(behind).as_tuple())
        return out

    def resampled(self, width: int, height: int) -> Canvas:
        """Return the canvas rescaled with a box filter.

        Box averaging is the right filter for shrinking icon art: it keeps a
        dense glyph from aliasing into a moire the way a point sample would.

        Args:
            width: Target width.
            height: Target height.
        Returns:
            New canvas at the target size.
        """
        if (width, height) == (self.width, self.height):
            out = Canvas(width, height)
            out._pixels[:] = self._pixels[:]
            return out
        result = Canvas(width, height)
        for row in range(height):
            source_top = row * self.height // height
            source_bottom = max(source_top + 1, (row + 1) * self.height // height)
            for column in range(width):
                source_left = column * self.width // width
                source_right = max(source_left + 1, (column + 1) * self.width // width)
                total = [0, 0, 0, 0]
                count = 0
                for source_row in range(source_top, source_bottom):
                    for source_column in range(source_left, source_right):
                        offset = (source_row * self.width + source_column) * _BYTES_PER_PIXEL
                        for channel in range(4):
                            total[channel] += self._pixels[offset + channel]
                        count += 1
                target = (row * width + column) * _BYTES_PER_PIXEL
                result._pixels[target : target + 4] = bytes(
                    min(255, value // count) for value in total
                )
        return result

    def illuminated_ratio(self) -> float:
        """Estimate how much of the canvas a watch face lights up.

        The Wear quality guideline WO-P7 caps an always-on face at about 15
        percent illuminated pixels, so a generator has to be able to report
        its own figure before submission.

        Returns:
            Fraction of pixels whose alpha and luma both clear the threshold,
            between 0.0 and 1.0.
        """
        total = self.width * self.height
        if total == 0:
            return 0.0
        lit = 0
        for index in range(total):
            offset = index * _BYTES_PER_PIXEL
            if self._pixels[offset + 3] < 8:
                continue
            luma = (
                self._pixels[offset] * 299
                + self._pixels[offset + 1] * 587
                + self._pixels[offset + 2] * 114
            )
            if luma >= 255 * 40:
                lit += 1
        return lit / total

    def png_bytes(self) -> bytes:
        """Encode the canvas as a PNG.

        Returns:
            Complete PNG file bytes, deterministic for the same pixels.
        """
        rows = bytearray()
        stride = self.width * _BYTES_PER_PIXEL
        for row in range(self.height):
            rows.append(_FILTER_NONE)
            rows += self._pixels[row * stride : (row + 1) * stride]
        header = struct.pack(
            ">IIBBBBB",
            self.width,
            self.height,
            _BIT_DEPTH_8,
            _COLOR_TYPE_RGBA,
            0,
            0,
            0,
        )
        return (
            _PNG_SIGNATURE
            + _chunk(_CHUNK_IHDR, header)
            + _chunk(_CHUNK_IDAT, zlib.compress(bytes(rows), 9))
            + _chunk(_CHUNK_IEND, b"")
        )

    def write_png(self, path: str) -> int:
        """Encode and write the canvas to disk.

        Args:
            path: Destination ``.png`` path.
        Returns:
            Bytes written.
        """
        data = self.png_bytes()
        with open(path, "wb") as handle:
            handle.write(data)
        return len(data)

    def save(self, path: str, max_side: int | None = None) -> int:
        """Write the canvas, optionally down first, as PNG.

        Args:
            path: Destination path.
            max_side: Square edge to resample to before writing, or None to
                write at the canvas size.
        Returns:
            Bytes written.
        """
        if max_side is None or (max_side == self.width and max_side == self.height):
            return self.write_png(path)
        return self.resampled(max_side, max_side).write_png(path)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    """Wrap a payload in a PNG chunk.

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


def _scale_alpha(color: Rgba, coverage: float) -> Rgba:
    """Fade a colour by a coverage fraction.

    Args:
        color: Colour to fade.
        coverage: 0.0 to 1.0 of the pixel the colour covers.
    Returns:
        Colour with a scaled alpha.
    """
    return Rgba(
        color.red,
        color.green,
        color.blue,
        max(0, min(255, round(color.alpha * coverage))),
    )


def encode_rgb_png(canvas: Canvas) -> bytes:
    """Encode an opaque canvas as a 24-bit alpha-free PNG.

    Store banners are the one asset a listing demands without an alpha
    channel, and ``Canvas.png_bytes`` writes RGBA only, so the RGB path lives
    beside it in this codec.

    Args:
        canvas: Canvas to encode; every pixel has to be fully opaque.

    Returns:
        Complete PNG file bytes, deterministic for the same pixels.

    Raises:
        RasterError: The canvas carries transparency, which this format
            cannot represent without silently flattening it onto black.
    """
    pixels = canvas.to_bytes()
    opaque = b"\xff" * (canvas.width * canvas.height)
    if pixels[3::_BYTES_PER_PIXEL] != opaque:
        raise RasterError("encode_rgb_png needs an opaque canvas")
    rows = bytearray()
    stride = canvas.width * _BYTES_PER_PIXEL
    for row in range(canvas.height):
        rows.append(_FILTER_NONE)
        for column in range(canvas.width):
            offset = row * stride + column * _BYTES_PER_PIXEL
            rows += pixels[offset : offset + 3]
    header = struct.pack(
        ">IIBBBBB",
        canvas.width,
        canvas.height,
        _BIT_DEPTH_8,
        _COLOR_TYPE_RGB,
        0,
        0,
        0,
    )
    return (
        _PNG_SIGNATURE
        + _chunk(_CHUNK_IHDR, header)
        + _chunk(_CHUNK_IDAT, zlib.compress(bytes(rows), 9))
        + _chunk(_CHUNK_IEND, b"")
    )


def from_rgba_bytes(data: bytes, width: int, height: int) -> Canvas:
    """Wrap raw RGBA bytes from ffmpeg into a canvas.

    Args:
        data: ``width * height * 4`` bytes of RGBA8888.
        width: Image width.
        height: Image height.
    Returns:
        Canvas holding those pixels.
    Raises:
        ValueError: the byte count does not match the size.
    """
    expected = width * height * _BYTES_PER_PIXEL
    if len(data) != expected:
        raise ValueError(f"expected {expected} RGBA bytes, got {len(data)}")
    canvas = Canvas(width, height)
    canvas._pixels[:] = bytearray(data)
    return canvas


@dataclass(frozen=True)
class _Frame:
    """One PNG frame at its native size, before promotion to RGBA.

    Attributes:
        width: Frame width in pixels.
        height: Frame height in pixels.
        colour_type: The PNG colour type the header declared.
        channels: Samples per pixel, one of the values in ``_CHANNEL_COUNTS``.
        samples: Row-major samples as the scanline filters left them.
        transparent: The ``tRNS`` keyed samples, or None when the file has none.
    """

    width: int
    height: int
    colour_type: int
    channels: int
    samples: bytearray
    transparent: tuple[int, ...] | None


def _paeth_predictor(left: int, above: int, above_left: int) -> int:
    """Return the PNG Paeth predictor for three neighbours.

    Args:
        left: Sample to the left in this scanline.
        above: Sample above, in the previous scanline.
        above_left: Sample above and to the left.

    Returns:
        Whichever neighbour is closest to ``left + above - above_left``.
    """
    estimate = left + above - above_left
    distances = (abs(estimate - left), abs(estimate - above), abs(estimate - above_left))
    return (left, above, above_left)[distances.index(min(distances))]


def _unfilter(stream: bytes, width: int, height: int, channels: int) -> bytearray:
    """Reconstruct scanlines from a filtered image data stream.

    Every filter a conforming encoder may pick is handled here, not just the
    one this module writes: a PNG from a design tool is free to change filter
    from row to row, and a validator that read only its own output would call
    a sellable pack unreadable.

    Args:
        stream: Inflated bytes, one filter byte then one scanline per row.
        width: Frame width in pixels.
        height: Frame height in pixels.
        channels: Samples per pixel.

    Returns:
        Row-major samples with the filters removed.

    Raises:
        RasterError: The stream is short, or names a filter the spec does not
            define.
    """
    stride = width * channels
    expected = height * (stride + 1)
    if len(stream) < expected:
        raise RasterError(
            f"PNG scanline data is too short: expected {expected} bytes, got {len(stream)}"
        )
    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    offset = 0
    for row in range(height):
        kind = stream[offset]
        offset += 1
        line = bytearray(stream[offset : offset + stride])
        offset += stride
        if kind == _FILTER_NONE:
            pass
        elif kind == _FILTER_SUB:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                line[index] = (line[index] + left) & 0xFF
        elif kind == _FILTER_UP:
            for index in range(stride):
                line[index] = (line[index] + previous[index]) & 0xFF
        elif kind == _FILTER_AVERAGE:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                line[index] = (line[index] + ((left + previous[index]) >> 1)) & 0xFF
        elif kind == _FILTER_PAETH:
            for index in range(stride):
                left = line[index - channels] if index >= channels else 0
                above_left = previous[index - channels] if index >= channels else 0
                line[index] = (
                    line[index] + _paeth_predictor(left, previous[index], above_left)
                ) & 0xFF
        else:
            raise RasterError(f"PNG scanline filter {kind} is not a defined filter type")
        base = row * stride
        pixels[base : base + stride] = line
        previous = line
    return pixels


def _read_ihdr(payload: bytes, already_seen: bool) -> tuple[int, int, int, int, int]:
    """Read an IHDR body.

    Args:
        payload: Chunk body, which should carry ``_IHDR_BYTES`` bytes.
        already_seen: True when a header has already been parsed.

    Returns:
        ``(width, height, bit_depth, colour_type, interlace)``.

    Raises:
        RasterError: The header is a duplicate or too short to measure with.
    """
    if already_seen:
        raise RasterError("PNG file declares its IHDR header twice")
    if len(payload) < _IHDR_BYTES:
        raise RasterError("PNG IHDR is too short to measure the frame")
    width, height, depth, colour, _compression, _filter, interlace = struct.unpack(
        ">IIBBBBB", payload[:_IHDR_BYTES]
    )
    return (width, height, depth, colour, interlace)


def _read_trns(
    payload: bytes, header: tuple[int, int, int, int, int] | None
) -> tuple[int, ...] | None:
    """Read the optional transparency chunk.

    Args:
        payload: Chunk body holding one 16-bit sample per channel.
        header: The parsed IHDR, or None when it has not arrived yet.

    Returns:
        The keyed samples, or None for a colour type that has no alpha to key
        and for a chunk whose length does not match its colour type.

    Raises:
        RasterError: The chunk arrived before the header that defines its shape.
    """
    if header is None:
        raise RasterError("PNG tRNS chunk arrived before its IHDR header")
    count = _TRNS_SAMPLES.get(header[3])
    if count is None or len(payload) != 2 * count:
        return None
    return tuple(
        int.from_bytes(payload[2 * index : 2 * index + 2], "big") for index in range(count)
    )


def _inflate_idat(idat: bytes, expected: int) -> bytes:
    """Inflate the image data stream, capped at what the frame can use.

    The cap is the reason a 400 KB IDAT claiming a single pixel is refused
    rather than decompressed: a validator reads files it did not write, and an
    unbounded inflate is the cheapest way to exhaust the process.

    Args:
        idat: Concatenated IDAT chunk bodies.
        expected: Byte count the scanlines need, filter bytes included.

    Returns:
        The inflated stream, no longer than ``expected``.

    Raises:
        RasterError: The stream is not inflatable, or is larger than the frame.
    """
    try:
        stream = zlib.decompressobj().decompress(idat, expected + 1)
    except zlib.error as exc:
        raise RasterError(f"PNG image data is not a usable zlib stream: {exc}") from exc
    if len(stream) > expected:
        raise RasterError(
            f"PNG image data decompresses to a stream larger than the"
            f" {expected} bytes the frame needs"
        )
    return stream


def _parse_png(data: bytes) -> _Frame:
    """Parse PNG bytes into a frame this module can promote.

    Args:
        data: Complete file bytes, signature included.

    Returns:
        The decoded frame at its native size.

    Raises:
        RasterError: The framing, header, or pixel data of this PNG is broken.
        _NeedsMediaBackend: The PNG is well formed and outside this codec's
            scope, so ffmpeg has to read it.
    """
    header: tuple[int, int, int, int, int] | None = None
    idat = bytearray()
    transparent: tuple[int, ...] | None = None
    complete = False
    position = len(_PNG_SIGNATURE)
    while position + 8 <= len(data):
        length = int.from_bytes(data[position : position + 4], "big")
        kind = data[position + 4 : position + 8]
        body_end = position + 8 + length
        if body_end + 4 > len(data):
            raise RasterError("PNG file is truncated inside a chunk")
        payload = data[position + 8 : body_end]
        if int.from_bytes(data[body_end : body_end + 4], "big") != (
            zlib.crc32(kind + payload) & 0xFFFFFFFF
        ):
            raise RasterError(f"PNG chunk {kind!r} does not match its CRC")
        position = body_end + 4
        if kind == _CHUNK_IHDR:
            header = _read_ihdr(payload, header is not None)
        elif kind == _CHUNK_IDAT:
            idat += payload
        elif kind == _CHUNK_T_RNS:
            transparent = _read_trns(payload, header)
        elif kind == _CHUNK_IEND:
            complete = True
            break
    if header is None:
        raise RasterError("PNG file has no IHDR header chunk to measure it")
    if not complete:
        raise RasterError("PNG file is truncated before its IEND chunk")
    if not idat:
        raise RasterError("PNG file has no IDAT image data chunk")
    width, height, depth, colour, interlace = header
    if interlace != _INTERLACE_NONE:
        raise _NeedsMediaBackend("interlaced PNG files need ffmpeg")
    if depth != _BIT_DEPTH_8:
        raise _NeedsMediaBackend(f"PNG bit depth {depth} needs ffmpeg")
    channels = _CHANNEL_COUNTS.get(colour)
    if channels is None:
        raise _NeedsMediaBackend(f"PNG colour type {colour} needs ffmpeg")
    if width * height > _MAX_PIXELS:
        raise RasterError(
            f"PNG frame of {width}x{height} is more pixels than this module allows"
        )
    stream = _inflate_idat(bytes(idat), height * (width * channels + 1))
    return _Frame(
        width,
        height,
        colour,
        channels,
        _unfilter(stream, width, height, channels),
        transparent,
    )


def _promote(frame: _Frame) -> bytearray:
    """Expand a frame's samples to RGBA8888.

    Args:
        frame: The decoded frame.

    Returns:
        Four bytes per pixel, with any ``tRNS`` key folded into the alpha
        channel the same way ffmpeg folds it, so an alpha gate reads the same
        answer from either path.
    """
    if frame.colour_type == _COLOR_TYPE_RGBA:
        return frame.samples
    channels = frame.channels
    keyed = frame.transparent
    greyscale = frame.colour_type in (_COLOR_TYPE_GRAY, _COLOR_TYPE_GRAY_ALPHA)
    pixels = bytearray(frame.width * frame.height * _BYTES_PER_PIXEL)
    for index in range(frame.width * frame.height):
        source = index * channels
        if greyscale:
            sample = frame.samples[source]
            red = green = blue = sample
            alpha = frame.samples[source + 1] if channels == 2 else 255
            if keyed is not None and keyed[0] == sample:
                alpha = 0
        else:
            red = frame.samples[source]
            green = frame.samples[source + 1]
            blue = frame.samples[source + 2]
            keyed_rgb = keyed is not None and keyed == (red, green, blue)
            alpha = 0 if keyed_rgb else 255
        target = index * _BYTES_PER_PIXEL
        pixels[target] = red
        pixels[target + 1] = green
        pixels[target + 2] = blue
        pixels[target + 3] = alpha
    return pixels


def _leading_square(pixels: bytes, width: int, edge: int) -> Canvas:
    """Crop the leading square out of a decoded frame.

    The ffmpeg path returned the whole raw stream and the wrapper kept its
    first rows, which is this same top-left crop; a native-size read has to
    mean the same thing whichever path served it.

    Args:
        pixels: RGBA bytes at the native size.
        width: Native width.
        edge: Square edge to keep.

    Returns:
        Canvas holding the leading ``edge`` rows and columns.
    """
    source_stride = width * _BYTES_PER_PIXEL
    target_stride = edge * _BYTES_PER_PIXEL
    crop = bytearray(edge * target_stride)
    for row in range(edge):
        crop[row * target_stride : (row + 1) * target_stride] = pixels[
            row * source_stride : row * source_stride + target_stride
        ]
    return from_rgba_bytes(bytes(crop), edge, edge)


def _canvas_from_frame(frame: _Frame, side: int | None) -> Canvas:
    """Wrap a decoded frame in a canvas, scaled the way the caller asked.

    Args:
        frame: The decoded frame.
        side: Square edge to resample to, or None to keep the native size.

    Returns:
        Canvas of RGBA pixels at the requested size.
    """
    pixels = bytes(_promote(frame))
    native = (frame.width, frame.height)
    if side is not None:
        if (side, side) == native:
            return from_rgba_bytes(pixels, side, side)
        return from_rgba_bytes(pixels, frame.width, frame.height).resampled(side, side)
    edge = min(frame.width, frame.height)
    if (edge, edge) == native:
        return from_rgba_bytes(pixels, edge, edge)
    return _leading_square(pixels, frame.width, edge)


def _read_frame(path: str) -> _Frame | None:
    """Read a PNG through the stdlib codec.

    Args:
        path: File to read.

    Returns:
        The decoded frame, or None when the path is absent, unreadable, or not
        a PNG at all, which leaves the file to the media backend.

    Raises:
        RasterError: The file carries the PNG signature and is broken.
        _NeedsMediaBackend: The file is a PNG variant this codec does not read.
    """
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return None
    if len(data) < len(_PNG_SIGNATURE) or not data.startswith(_PNG_SIGNATURE):
        return None
    return _parse_png(data)


def decode_rgba(path: str, side: int | None = None) -> Canvas:
    """Decode an image file to RGBA, using ffmpeg only where it is needed.

    A PNG this module can read is decoded in-process, which is what lets a
    generated pack validate itself on a host with no media binaries: the fast
    core lane, the devcontainer, and a CI runner all ship without ffmpeg.
    Everything else - JPEG and WebP artwork, a 16-bit, interlaced, or palette
    PNG - goes to ffmpeg, and an operator without it hears the plain reason.

    Args:
        path: Source image.
        side: Square edge to scale to while decoding, or None for the native
            size.
    Returns:
        Decoded canvas.
    Raises:
        RasterError: The file is a broken PNG, or ffmpeg is missing or refused
            the file.
    """
    try:
        frame = _read_frame(path)
        if frame is not None:
            return _canvas_from_frame(frame, side)
    except _NeedsMediaBackend:
        pass
    command = ["ffmpeg", "-v", "error", "-i", path]
    if side is not None:
        command += ["-vf", f"scale={side}:{side}:flags=area"]
    command += ["-f", "rawvideo", "-pix_fmt", "rgba", "-"]
    try:
        completed = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except FileNotFoundError as exc:
        raise RasterError("ffmpeg is not installed") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RasterError(f"ffmpeg could not decode {path}: {detail}")
    edge = side if side is not None else _probe_size(path)
    try:
        return from_rgba_bytes(completed.stdout, edge, edge)
    except ValueError as exc:
        raise RasterError(
            f"ffmpeg returned a stream too short for a {edge}x{edge} RGBA image: {exc}"
        ) from exc


def encode_png(source: str, destination: str, side: int) -> int:
    """Scale an image on disk to a square PNG through ffmpeg.

    Args:
        source: Input image path.
        destination: Output ``.png`` path.
        side: Square edge in pixels.
    Returns:
        Bytes written.
    Raises:
        RasterError: ffmpeg is missing or refused the job.
    """
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        source,
        "-vf",
        f"scale={side}:{side}:flags=area",
        destination,
    ]
    try:
        completed = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False
        )
    except FileNotFoundError as exc:
        raise RasterError("ffmpeg is not installed") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RasterError(f"ffmpeg could not write {destination}: {detail}")
    return os.path.getsize(destination)


def _probe_size(path: str) -> int:
    """Return the square edge of an image through ffprobe.

    Args:
        path: Image to measure.
    Returns:
        The smaller of width and height, which is the edge a square canvas
        should use.
    Raises:
        RasterError: ffprobe is missing, failed, or reported a non-square
            image this module cannot wrap.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        path,
    ]
    try:
        completed = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except FileNotFoundError as exc:
        raise RasterError("ffprobe is not installed") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RasterError(f"ffprobe could not measure {path}: {detail}")
    text = completed.stdout.decode("ascii", "replace").strip()
    try:
        width_text, height_text = text.split("x", 1)
        width, height = int(width_text), int(height_text)
    except ValueError as exc:
        raise RasterError(f"ffprobe reported an unusable size {text!r}") from exc
    return min(width, height)
