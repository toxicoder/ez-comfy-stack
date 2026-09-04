"""ffmpeg stitch for 18 × 5.00s LTX MP4s with a 90s publish cap.

Hermetic at import: stdlib only. ffmpeg is resolved at call time.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .shots import DEFAULT_CAP_SECONDS, SHOT_COUNT, film_slug

LOUDNORM_FILTER = "loudnorm=I=-14:LRA=11:TP=-1.5"
AAC_BITRATE = "192k"
AAC_RATE = "48000"


def log(message: str) -> None:
    """Write a pack line to stderr.

    Arguments:
        message: Text after the ``[ez_film]`` prefix.
    Returns:
        None
    """
    print(f"[ez_film] {message}", file=sys.stderr)


def output_directory() -> Path:
    """Comfy output dir, then ``COMFY_OUTPUT_DIR``, then ``output``.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        import folder_paths  # type: ignore[import-not-found]

        return Path(folder_paths.get_output_directory())
    except Exception:  # noqa: BLE001 — Comfy is optional in unit tests
        env = os.environ.get("COMFY_OUTPUT_DIR")
        if env:
            return Path(env)
        return Path("output")


def find_ffmpeg() -> str:
    """Resolve ffmpeg: PATH, then imageio-ffmpeg (VHS dependency).

    Returns:
        Executable path.
    Raises:
        RuntimeError: no ffmpeg available.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return str(exe)
    except Exception as exc:  # noqa: BLE001 — optional dep
        log(f"imageio_ffmpeg unavailable: {exc}")
    raise RuntimeError("ffmpeg not on PATH")


def find_ffprobe() -> str | None:
    """Resolve ffprobe on PATH, or None.

    Returns:
        Executable path or None.
    """
    return shutil.which("ffprobe")


def resolve_shot_path(value: object) -> str:
    """First MP4 path from a VHS_FILENAMES payload or a plain path.

    Arguments:
        value: str path, ``(saved, [paths])`` tuple, list, or dict.
    Returns:
        Path string.
    Raises:
        ValueError: empty / unusable payload.
    """
    if value is None:
        raise ValueError("missing shot file")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty shot path")
        return text
    if isinstance(value, dict):
        for key in ("filename", "path", "file"):
            raw = value.get(key)
            if raw:
                return resolve_shot_path(raw)
        raise ValueError("shot dict has no filename")
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError("empty shot list")
        if len(value) == 2 and isinstance(value[0], bool):
            return resolve_shot_path(value[1])
        return resolve_shot_path(value[0])
    raise ValueError(f"unusable shot payload: {type(value).__name__}")


def concat_list_line(path: str) -> str:
    """One concat-demuxer line with escaped single quotes.

    Arguments:
        path: Absolute or relative MP4 path.
    Returns:
        ``file '…'`` line without newline.
    """
    escaped = path.replace("'", "'\\''")
    return f"file '{escaped}'"


def ffmpeg_stitch_argv(
    list_path: str,
    out_mp4: str,
    cap_seconds: float,
    ffmpeg: str,
) -> list[str]:
    """Build the stitch command (video copy, AAC + YouTube loudnorm).

    Arguments:
        list_path: Concat demuxer list file.
        out_mp4: Destination MP4.
        cap_seconds: ffmpeg ``-t`` cap.
        ffmpeg: ffmpeg executable.
    Returns:
        Argument vector.
    """
    cap = str(cap_seconds)
    return [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-t",
        cap,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-ar",
        AAC_RATE,
        "-ac",
        "2",
        "-b:a",
        AAC_BITRATE,
        "-af",
        LOUDNORM_FILTER,
        out_mp4,
    ]


def probe_seconds(path: str, ffprobe: str | None = None) -> float | None:
    """Duration in seconds, or None if ffprobe is missing/fails.

    Arguments:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
    Returns:
        Float seconds or None.
    """
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [
                exe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                path,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        log(f"ffprobe failed: {exc}")
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def stitch_film(
    shot_paths: list[str],
    out_mp4: str,
    cap_seconds: float = DEFAULT_CAP_SECONDS,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: Any = None,
) -> str:
    """Concat 18 shot MP4s, cap duration, fail if probe exceeds cap.

    Arguments:
        shot_paths: Exactly 18 MP4 paths in beat/shot order.
        out_mp4: Destination path.
        cap_seconds: Publish cap (default 90).
        ffmpeg: Override ffmpeg path.
        ffprobe: Override ffprobe path.
        run: Override ``subprocess.run`` (tests).
    Returns:
        ``out_mp4``.
    Raises:
        ValueError: wrong shot count.
        RuntimeError: ffmpeg missing/fails, or duration over cap.
    """
    if len(shot_paths) != SHOT_COUNT:
        raise ValueError(f"expected {SHOT_COUNT} shots, found {len(shot_paths)}")
    exe = ffmpeg or find_ffmpeg()
    runner = run or subprocess.run
    list_file = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".txt", delete=False
    )
    try:
        for path in shot_paths:
            list_file.write(concat_list_line(path) + "\n")
        list_file.close()
        argv = ffmpeg_stitch_argv(list_file.name, out_mp4, cap_seconds, exe)
        log(" ".join(argv))
        proc = runner(argv, check=False, capture_output=True, text=True)
        if getattr(proc, "returncode", 1) != 0:
            err = getattr(proc, "stderr", "") or getattr(proc, "stdout", "") or ""
            raise RuntimeError(f"ffmpeg stitch failed: {err.strip() or 'exit 1'}")
    finally:
        Path(list_file.name).unlink(missing_ok=True)

    dur = probe_seconds(out_mp4, ffprobe=ffprobe)
    if dur is not None and dur > float(cap_seconds) + 0.05:
        raise RuntimeError(
            f"concat duration {dur}s exceeds cap {cap_seconds}s"
        )
    return out_mp4


def publish_path(film: str, output_dir: Path | None = None) -> Path:
    """``ez_{slug}_90s.mp4`` under the output directory.

    Arguments:
        film: Film id.
        output_dir: Override output directory.
    Returns:
        Destination path.
    """
    dest = output_dir if output_dir is not None else output_directory()
    return dest / f"ez_{film_slug(film)}_90s.mp4"
