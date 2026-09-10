#!/usr/bin/env python3
"""Backstop LoadImage plates for klein-dream-house-clay-lab-example.

Host ``manage.sh start`` still prefers layout-accurate plates via
``house_layout.py``. This module runs inside the container (stdlib only) when
``/inputs/ez_house_clay_NN.png`` are missing or not 1024×1280.

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

PACK_WIDTH = 1024
PACK_HEIGHT = 1280
CLAY_COUNT = 10
CLAY_PREFIX = "ez_house_clay"


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
    """Write a solid RGB PNG."""
    write_rgb_png(path, width, height, bytes(rgb) * (width * height))


def png_size(path: Path) -> tuple[int, int] | None:
    """Read IHDR width x height, or None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def clay_plate_valid(path: Path) -> bool:
    """True when path is a 1024x1280 PNG."""
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


def _under_models_dir(path: Path) -> bool:
    """True when path is under MODELS_DIR / MODELS_ROOT."""
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
    except (OSError, ValueError) as exc:
        print(f"[seed-clay] failed: {exc}", file=sys.stderr)
        return 1
    print(f"[seed-clay] {len(written)} plates ready in {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
