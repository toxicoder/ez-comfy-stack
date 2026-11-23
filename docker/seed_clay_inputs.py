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

The same applies to every other bare filename a shipped graph defaults to
(``cover.png``, the clip frames ``first.png`` / ``last.png`` / ``canny.png``,
and the film lane's ``ez_<film>_plate.png`` shots). Nothing in ``docker/``,
``scripts/``, or ``tools/`` writes those, so each one is seeded here as a
color-bar placeholder an operator swaps out for a real plate.

The one non-image default is the audio bed ``ez_a2v_bed.wav``, which
``video/av/audio-to-video-8s`` loads on a bare box. Nothing writes that either,
so a soft eight-second pad is seeded in its place; a bed the operator dropped in
first is left alone.

Typical invocation
------------------
    python3 /opt/ez-comfy/seed_clay_inputs.py /inputs
"""

from __future__ import annotations

import math
import os
import struct
import sys
import wave
import zlib
from dataclasses import dataclass
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

# Every other bare filename a shipped graph names as its LoadImage default.
# Derived from ``widgets_values[0]`` of each ``LoadImage`` node under
# ``workflows/_lab``; test_placeholder_table_matches_shipped_graphs fails when
# a graph starts naming one that is not listed here. Sizes follow the lane the
# plate belongs to: square album art, the clip frames the guides and video
# lanes render at, and the film lane's 1280x704 shots.
PLACEHOLDER_HUE_STEP = 53
PLACEHOLDER_BARS_MIN = 3
PLACEHOLDER_BARS_RANGE = 6
PLACEHOLDER_HIGHLIGHT = 0.72
PLACEHOLDER_SHADOW = 0.55
PLACEHOLDER_TOP = (18, 20, 26)
PLACEHOLDER_BAND_DIVISOR = 3
"""The stripe band covers the bottom 1/PLACEHOLDER_BAND_DIVISOR of a plate."""


@dataclass(frozen=True)
class PlaceholderPlate:
    """One placeholder plate a shipped graph points at before an operator does."""

    name: str
    width: int
    height: int


PLACEHOLDER_PLATES: tuple[PlaceholderPlate, ...] = (
    PlaceholderPlate("cover.png", 1024, 1024),
    PlaceholderPlate("first.png", 1280, 704),
    PlaceholderPlate("last.png", 832, 480),
    PlaceholderPlate("canny.png", 1280, 704),
    PlaceholderPlate("ez_breakwater_plate.png", 1280, 704),
    PlaceholderPlate("ez_breakwater_b6_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_breakwater_b12_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_breakwater_b18_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_breakwater_b24_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_glasshouse_plate.png", 1280, 704),
    PlaceholderPlate("ez_glasshouse_b6_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_glasshouse_b12_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_glasshouse_b18_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_glasshouse_b24_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_gosee_plate.png", 1280, 704),
    PlaceholderPlate("ez_lastlane_plate.png", 1280, 704),
    PlaceholderPlate("ez_lastlane_b6_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_lastlane_b12_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_lastlane_b18_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_lastlane_b24_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_nightoven_plate.png", 1280, 704),
    PlaceholderPlate("ez_nightoven_b6_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_nightoven_b12_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_nightoven_b18_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_nightoven_b24_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_stillhere_plate.png", 1280, 704),
    PlaceholderPlate("ez_switchyard_plate.png", 1280, 704),
    PlaceholderPlate("ez_tidetable_plate.png", 1280, 704),
    PlaceholderPlate("ez_tidetable_b6_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_tidetable_b12_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_tidetable_b18_s3_last.png", 1280, 704),
    PlaceholderPlate("ez_tidetable_b24_s3_last.png", 1280, 704),
)
"""Every bare filename a shipped graph defaults a LoadImage to, and the size the
lane that renders it works at. Derived from the graphs, not chosen: the drift test
in tests/python/test_seed_clay_inputs.py fails when a graph names a plate missing
here."""

# Audio bed the audio-to-video App defaults its LoadAudio to. Same story as the
# plates: nothing in the repo wrote it, so Queue failed on a missing file.
AUDIO_BED_NAME = "ez_a2v_bed.wav"
"""The filename video/av/audio-to-video-8s defaults its LoadAudio to."""
AUDIO_BED_RATE = 16000
"""Samples per second; mono 16-bit keeps the seeded file under 300 KB."""
AUDIO_BED_SECONDS = 8
"""Length that matches the eight-second clip this App renders."""
AUDIO_BED_PEAK = 20000
"""Peak sample amplitude; kept under int16 so the bed never clips."""
AUDIO_BED_TONES = (110.0, 165.0, 220.0)
"""A2, E3, A3: a soft pad rather than a test tone."""
AUDIO_BED_SWELL_HZ = 0.25
"""Slow amplitude swell so the pad reads as a bed and not a test tone."""
AUDIO_BED_FADE_SECONDS = 0.12
"""Edge fade so a loop point does not click."""

SEEDED_AUDIO_INPUTS = frozenset({AUDIO_BED_NAME})
"""Every bare audio filename a shipped graph defaults a loader to. The drift test
in tests/python/test_seed_clay_inputs.py fails when a graph names one that is not
seeded here."""


def placeholder_rgb(index: int) -> tuple[int, int, int]:
    """Distinct plate tint for a placeholder index so plates are not alike.

    Args:
        index: 0-based position in ``PLACEHOLDER_PLATES``.

    Returns:
        RGB triple in 0..255; the red channel alone is unique per index.
    """
    return (
        (PLACEHOLDER_HUE_STEP * index + 24) % 256,
        (PLACEHOLDER_HUE_STEP * 2 * index + 70) % 256,
        (PLACEHOLDER_HUE_STEP * 4 * index + 130) % 256,
    )


def placeholder_pixels(width: int, height: int, index: int) -> bytes:
    """Deterministic color-bar backdrop for one placeholder plate.

    The vertical gradient gives the sampler something with tonal range and the
    bottom stripe band gives the operator a count and a tint to read, so two
    plates at the same size still look nothing alike.

    Args:
        width: Pixel width.
        height: Pixel height.
        index: 0-based position in ``PLACEHOLDER_PLATES``.

    Returns:
        ``width * height * 3`` bytes of RGB.
    """
    tint = placeholder_rgb(index)
    light = _blend(tint, (255, 255, 255), PLACEHOLDER_HIGHLIGHT)
    dark = _blend(tint, (0, 0, 0), PLACEHOLDER_SHADOW)
    bars = PLACEHOLDER_BARS_MIN + index % PLACEHOLDER_BARS_RANGE
    band_top = height - max(1, height // PLACEHOLDER_BAND_DIVISOR)
    rows = bytearray()
    for y in range(height):
        bg = _blend(PLACEHOLDER_TOP, tint, y / max(1, height - 1))
        row = bytearray(bytes(bg) * width)
        if y >= band_top:
            for bar in range(bars):
                x0 = bar * width // bars
                x1 = (bar + 1) * width // bars
                stripe = light if bar % 2 == 0 else dark
                row[x0 * 3 : x1 * 3] = bytes(stripe) * (x1 - x0)
        rows += row
    return bytes(rows)


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
    plate is replaced.

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
        dest,
        EXAMPLE_WIDTH,
        EXAMPLE_HEIGHT,
        example_pixels(EXAMPLE_WIDTH, EXAMPLE_HEIGHT),
    )
    return dest


def seed_placeholder_inputs(input_dir: str | Path) -> list[Path]:
    """Ensure every other bare LoadImage default a shipped graph names exists.

    Covers the names in ``PLACEHOLDER_PLATES`` that nothing else writes, so an
    App whose plate was never shipped still Queues instead of failing on a
    missing file. A plate the operator already uploaded is never touched.

    Args:
        input_dir: Container ``/inputs`` (host ``COMFY_OUTPUT_DIR/input``).

    Returns:
        The paths written this run, in table order; empty when every plate was
        already a readable PNG.

    Raises:
        ValueError: Target is under MODELS_DIR.
    """
    target = Path(input_dir)
    if _under_models_dir(target):
        raise ValueError(f"refusing MODELS_DIR target {target}")
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, plate in enumerate(PLACEHOLDER_PLATES):
        dest = target / plate.name
        if example_png_valid(dest):
            continue
        write_rgb_png(
            dest,
            plate.width,
            plate.height,
            placeholder_pixels(plate.width, plate.height, index),
        )
        written.append(dest)
    return written


def audio_bed_frames(seconds: int, rate: int) -> bytes:
    """Deterministic 16-bit mono PCM bed: a soft pad that swells and fades.

    Args:
        seconds: Whole seconds of audio.
        rate: Samples per second.

    Returns:
        ``seconds * rate`` little-endian 16-bit mono samples.
    """
    total = int(seconds) * int(rate)
    fade = max(1, int(AUDIO_BED_FADE_SECONDS * rate))
    steps = len(AUDIO_BED_TONES)
    out = bytearray()
    for index in range(total):
        when = index / rate
        envelope = min(1.0, index / fade, max(0, total - 1 - index) / fade)
        swell = 0.72 + 0.28 * math.sin(2 * math.pi * AUDIO_BED_SWELL_HZ * when)
        voices = sum(math.sin(2 * math.pi * hz * when) for hz in AUDIO_BED_TONES)
        level = AUDIO_BED_PEAK * envelope * swell * voices / steps
        out += struct.pack("<h", int(max(-32768, min(32767, round(level)))))
    return bytes(out)


def write_pcm_wav(path: Path, frames: bytes, rate: int) -> None:
    """Write little-endian 16-bit mono PCM to ``path`` as RIFF/WAVE.

    Args:
        path: Destination file; parents are created.
        frames: Sample bytes, a whole number of 16-bit samples.
        rate: Samples per second.

    Raises:
        ValueError: ``frames`` holds half a sample.
    """
    if len(frames) % 2:
        raise ValueError(f"16-bit PCM frames need whole samples, got {len(frames)} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Opened here rather than handed to ``wave.open`` as a path: a refused open
    # then surfaces as this module's own OSError, and never as a half-built
    # ``Wave_write`` whose ``__del__`` raises on the garbage collector's say-so.
    with path.open("wb") as raw, wave.open(raw, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(rate))
        handle.writeframes(bytes(frames))


def _has_wave_magic(path: Path) -> bool:
    """True when the first twelve bytes read as a RIFF/WAVE container.

    Args:
        path: Candidate bed.

    Returns:
        Whether the file opens and carries the WAV container magic.
    """
    try:
        with path.open("rb") as handle:
            header = handle.read(12)
    except OSError:
        return False
    return len(header) == 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"


def wav_valid(path: Path) -> bool:
    """True when ``path`` already holds audio this module must not touch.

    A bed the operator dropped in stays theirs. 24-bit and multi-channel PCM
    open with the stdlib reader at any bit depth or channel count; a float,
    u-law, or extensible-format export that reader cannot parse still carries
    the WAV container, so it is kept as well. What is left is a file with no
    WAV header at all - a truncated download, a text stub, a 0-byte file - or
    a header whose data chunk holds no frames, and those the seed replaces.

    Args:
        path: Candidate bed.

    Returns:
        Whether ``path`` is a file the seeder should leave alone.
    """
    if not path.is_file():
        return False
    try:
        with wave.open(str(path), "rb") as handle:
            return handle.getnframes() > 0
    except wave.Error:
        return _has_wave_magic(path)
    except (OSError, EOFError):
        return False


def seed_audio_bed_input(input_dir: str | Path) -> Path | None:
    """Ensure the audio-to-video App's default bed exists so Queue works.

    Args:
        input_dir: Container ``/inputs`` (host ``COMFY_OUTPUT_DIR/input``).

    Returns:
        The written path, or ``None`` when a usable bed was already there.

    Raises:
        ValueError: Target is under MODELS_DIR.
    """
    target = Path(input_dir)
    if _under_models_dir(target):
        raise ValueError(f"refusing MODELS_DIR target {target}")
    target.mkdir(parents=True, exist_ok=True)
    dest = target / AUDIO_BED_NAME
    if wav_valid(dest):
        return None
    write_pcm_wav(
        dest,
        audio_bed_frames(AUDIO_BED_SECONDS, AUDIO_BED_RATE),
        AUDIO_BED_RATE,
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

    Never overwrites a valid existing plate. Also seeds the placeholder plates
    behind ``seed_placeholder_inputs``; the returned list stays the clay pack
    in camera order, which is what the caller counts.

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
    seed_placeholder_inputs(target)
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
        0 on success; 1 when the directory is empty (which would mean the
        current one) or any stage refused or hit an IO error.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if args and not args[0].strip():
        # ``Path("")`` is the current directory, so a blank expansion in the
        # entrypoint would seed forty-four plates into whatever the workdir is.
        print("[seed-clay] refusing an empty input directory", file=sys.stderr)
        return 1
    dest = Path(args[0] if args else "/inputs")
    # The three stages are attempted independently: an unwritable plate must
    # not quietly take the audio bed down with it, so every failure is
    # collected and named rather than short-circuiting the run.
    # Every clause is earned by the stage that ran: a summary that counts
    # plates the plate stage never wrote sends the operator looking for a
    # plate problem in the wrong place, so a failed stage prints nothing on
    # stdout at all and its reason stands alone on stderr.
    reports: list[str] = []
    failed = False
    try:
        written = seed_clay_inputs(dest)
    except (OSError, ValueError) as exc:
        # The stage is named because an OSError from write_bytes carries no
        # filename: three identical refusals must still say which of the three
        # things the operator has to go look at.
        print(f"[seed-clay] clay plates not seeded: {exc}", file=sys.stderr)
        failed = True
    else:
        reports.append(f"{len(written)} plates ready in {dest}")
        reports.append(f"{len(PLACEHOLDER_PLATES)} placeholder plates in place")
    try:
        example = seed_example_input(dest)
    except (OSError, ValueError) as exc:
        print(f"[seed-clay] example plate not seeded: {exc}", file=sys.stderr)
        failed = True
    else:
        if example is not None:
            reports.append(f"wrote {EXAMPLE_NAME}")
    try:
        bed = seed_audio_bed_input(dest)
    except (OSError, ValueError) as exc:
        # A bed that will not seed is its own line: the plates really did land
        # and the operator should not be told to go look for a plate problem.
        print(f"[seed-clay] audio bed not seeded: {exc}", file=sys.stderr)
        failed = True
    else:
        if bed is not None:
            reports.append(f"wrote {AUDIO_BED_NAME}")
    if reports:
        print("[seed-clay] " + "; ".join(reports))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
