#!/usr/bin/env python3
"""Backstop the LoadImage plates the lab Apps default to.

Host ``manage.sh start`` still prefers layout-accurate clay plates via
``house_layout.py``. This module runs inside the container (stdlib only) when
``/inputs/ez_house_clay_NN.png`` are missing or not 1024x1280.

It also guarantees ``/inputs/example.png``. ComfyUI ships that file in its own
``input/`` directory, but the stack remaps the input dir to the ``/inputs``
bind-mount and the install excludes ``/input/`` from the prebuilt sync, so a
fresh box has no ``example.png`` at all. 293 of the 577 ``LoadImage`` widgets
across the lab Apps sit on that default, and Queue fails on a missing file.

Typical invocation
------------------
    python3 /opt/ez-comfy/seed_clay_inputs.py /inputs
"""

from __future__ import annotations

import os
import struct
import sys
import zlib
from pathlib import Path

# LoadImage plate size, camera count, and ez_house_clay filename prefix.
PACK_WIDTH = 1024
PACK_HEIGHT = 1280
CLAY_COUNT = 10
CLAY_PREFIX = "ez_house_clay"

# Default LoadImage plate that ComfyUI's own input/ dir would have supplied.
EXAMPLE_NAME = "example.png"
EXAMPLE_WIDTH = 1024
EXAMPLE_HEIGHT = 1024
EXAMPLE_TOP = (26, 32, 44)
EXAMPLE_BOTTOM = (96, 108, 126)
EXAMPLE_SUBJECT = (228, 228, 228)
EXAMPLE_INSET = 0.18
"""Fraction of each edge left as backdrop around the subject block."""


def clay_copy_name(index: int) -> str:
    """Return ez_house_clay_NN.png for a 0-based camera index.

    Args:
        index: Camera index in ``0..CLAY_COUNT-1``.

    Returns:
        Filename for Comfy LoadImage.
    """
    return f"{CLAY_PREFIX}_{index + 1:02d}.png"


def write_rgb_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    """Write an RGB8 PNG (stdlib zlib). Filter none, no ancillary chunks.

    Args:
        path: Destination file.
        width: Pixel width.
        height: Pixel height.
        rgb: Packed RGB bytes, length width*height*3.

    Raises:
        ValueError: Buffer length does not match width*height*3.
    """
    expected = width * height * 3
    if len(rgb) != expected:
        raise ValueError(f"rgb buffer length {len(rgb)} != {expected}")
    path.parent.mkdir(parents=True, exist_ok=True)
    row = width * 3
    raw = b"".join(b"\x00" + rgb[y * row : (y + 1) * row] for y in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        """Return one PNG chunk (length, tag, data, CRC).

        Args:
            tag: Four-byte chunk type.
            data: Chunk payload.

        Returns:
            On-disk chunk bytes.
        """
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def write_solid_png(
    path: Path, width: int, height: int, rgb: tuple[int, int, int]
) -> None:
    """Write a solid RGB PNG.

    Args:
        path: Destination file.
        width: Pixel width.
        height: Pixel height.
        rgb: Fill color as an 8-bit RGB triple.
    """
    write_rgb_png(path, width, height, bytes(rgb) * (width * height))


def png_size(path: Path) -> tuple[int, int] | None:
    """Read IHDR width x height, or None.

    Args:
        path: PNG file to inspect.

    Returns:
        ``(width, height)`` from IHDR, or ``None`` when unreadable.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def clay_plate_valid(path: Path) -> bool:
    """True when path is a 1024x1280 PNG.

    Args:
        path: Candidate LoadImage plate.

    Returns:
        Whether ``path`` is a file whose IHDR is ``PACK_WIDTH`` x ``PACK_HEIGHT``.
    """
    return path.is_file() and png_size(path) == (PACK_WIDTH, PACK_HEIGHT)


def plate_rgb(index: int) -> tuple[int, int, int]:
    """Distinct grey-clay RGB for a camera index so plates are not identical.

    Args:
        index: 0-based camera index.

    Returns:
        RGB triple in 0..255.
    """
    step = 18 * (index + 1)
    return (min(255, 48 + step), min(255, 52 + step // 2), min(255, 56 + step // 3))


def _blend(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    """Linearly mix two RGB triples.

    Args:
        a: Color at t=0.
        b: Color at t=1.
        t: Mix factor in 0..1.

    Returns:
        Blended 8-bit RGB triple.
    """
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def example_pixels(width: int, height: int) -> bytes:
    """Deterministic studio-backdrop pixels for the default LoadImage plate.

    A vertical gradient keeps the row write cheap; the centred block gives
    Klein something with edges to re-render instead of a flat field.

    Args:
        width: Pixel width.
        height: Pixel height.

    Returns:
        ``width * height * 3`` bytes of RGB.
    """
    pad_x = max(1, int(width * EXAMPLE_INSET))
    pad_y = max(1, int(height * EXAMPLE_INSET))
    subject_w = max(1, width - 2 * pad_x)
    subject_h = max(1, height - 2 * pad_y)
    rows = bytearray()
    for y in range(height):
        bg = _blend(EXAMPLE_TOP, EXAMPLE_BOTTOM, y / max(1, height - 1))
        if not pad_y <= y < pad_y + subject_h:
            rows += bytes(bg) * width
            continue
        row = bytearray(bytes(bg) * width)
        for x in range(pad_x, pad_x + subject_w):
            shade = 0.35 + 0.5 * (x - pad_x) / max(1, subject_w - 1)
            row[x * 3 : x * 3 + 3] = bytes(_blend(bg, EXAMPLE_SUBJECT, shade))
        rows += row
    return bytes(rows)


def example_png_valid(path: Path) -> bool:
    """True when path already holds a readable PNG of any size.

    A plate the operator uploaded stays put; only a missing or corrupt
    ``example.png`` is replaced.

    Args:
        path: Candidate default plate.

    Returns:
        Whether ``path`` is a file with a readable PNG header.
    """
    return path.is_file() and png_size(path) is not None


def seed_example_input(input_dir: str | Path) -> Path | None:
    """Ensure example.png exists so LoadImage defaults can Queue.

    Args:
        input_dir: Container ``/inputs`` (host ``COMFY_OUTPUT_DIR/input``).

    Returns:
        The written path, or ``None`` when a usable plate was already there.

    Raises:
        ValueError: Target is under MODELS_DIR.
    """
    target = Path(input_dir)
    if _under_models_dir(target):
        raise ValueError(f"refusing MODELS_DIR target {target}")
    target.mkdir(parents=True, exist_ok=True)
    dest = target / EXAMPLE_NAME
    if example_png_valid(dest):
        return None
    write_rgb_png(
        dest, EXAMPLE_WIDTH, EXAMPLE_HEIGHT, example_pixels(EXAMPLE_WIDTH, EXAMPLE_HEIGHT)
    )
    return dest


def _under_models_dir(path: Path) -> bool:
    """True when path is under MODELS_DIR / MODELS_ROOT.

    Args:
        path: Directory that would receive plates.

    Returns:
        Whether ``path`` resolves under a models-root env var.
    """
    roots: list[Path] = []
    for key in ("MODELS_DIR", "MODELS_ROOT"):
        raw = os.environ.get(key, "").strip()
        if raw:
            roots.append(Path(raw).resolve())
    dest = path.resolve()
    for root in roots:
        try:
            dest.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def seed_clay_inputs(input_dir: str | Path) -> list[Path]:
    """Ensure ez_house_clay_01..10.png exist at lab LoadImage size.

    Never overwrites a valid existing plate.

    Args:
        input_dir: Container ``/inputs`` (host ``COMFY_OUTPUT_DIR/input``).

    Returns:
        Paths under input_dir, in camera order.

    Raises:
        ValueError: Target is under MODELS_DIR.
    """
    target = Path(input_dir)
    if _under_models_dir(target):
        raise ValueError(f"refusing MODELS_DIR target {target}")
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index in range(CLAY_COUNT):
        dest = target / clay_copy_name(index)
        if clay_plate_valid(dest):
            written.append(dest)
            continue
        write_solid_png(dest, PACK_WIDTH, PACK_HEIGHT, plate_rgb(index))
        written.append(dest)
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI: seed_clay_inputs.py [input_dir].

    Args:
        argv: Optional args without program name. Default ``/inputs``.

    Returns:
        0 on success; 1 on refuse / IO error.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    dest = Path(args[0] if args else "/inputs")
    try:
        written = seed_clay_inputs(dest)
        example = seed_example_input(dest)
    except (OSError, ValueError) as exc:
        print(f"[seed-clay] failed: {exc}", file=sys.stderr)
        return 1
    seeded = f"; wrote {EXAMPLE_NAME}" if example is not None else ""
    print(f"[seed-clay] {len(written)} plates ready in {dest}{seeded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
