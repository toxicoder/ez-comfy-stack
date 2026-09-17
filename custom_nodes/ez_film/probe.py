"""ffprobe MediaProbe: duration, size, audio, fps.

Hermetic at import: stdlib only. :func:`ez_film.concat.find_ffprobe` and
:func:`ez_film.concat.log` are read from the concat façade at call time so
``patch.object(concat, "find_ffprobe")`` keeps working.
"""

from __future__ import annotations

import subprocess

from .protocols import FfmpegRunner


def _log(message: str) -> None:
    """Write a pack line via the concat façade.

    Args:
        message: Text after the ``[ez_film]`` prefix.
    """
    from . import concat as _c

    _c.log(message)


def _resolve_ffprobe(ffprobe: str | None) -> str | None:
    """Use ``ffprobe`` when given, else the concat façade locator.

    Args:
        ffprobe: Optional executable path.

    Returns:
        Executable path, or None.
    """
    if ffprobe is not None:
        return ffprobe
    from . import concat as _c

    return _c.find_ffprobe()


def _ffprobe_csv(
    path: str,
    args: list[str],
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
) -> str | None:
    """Run ffprobe and return stripped stdout, or None on failure.

    Args:
        path: Media file.
        args: Extra ffprobe arguments before ``path``.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        Stripped stdout, or None on failure.
    """
    exe = _resolve_ffprobe(ffprobe)
    if not exe:
        return None
    runner: FfmpegRunner = run if run is not None else subprocess.run
    try:
        proc = runner(
            [exe, "-v", "error", *args, path],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        _log(f"ffprobe failed: {exc}")
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    text = (getattr(proc, "stdout", "") or "").strip()
    return text or None


def _parse_float_token(text: str, *, index: int = 0) -> float | None:
    """Parse a CSV token as float.

    Args:
        text: ffprobe CSV stdout.
        index: ``split(",")`` index (0 = first, -1 = last).

    Returns:
        Float, or None on ``ValueError``.
    """
    parts = text.split(",")
    try:
        token = parts[index].strip()
        return float(token)
    except (IndexError, ValueError):
        return None


def _parse_fps(text: str) -> float | None:
    """Parse ``r_frame_rate`` (``24/1`` or ``24.0``).

    Args:
        text: ffprobe CSV stdout.

    Returns:
        Frames per second, or None.
    """
    token = text.split(",")[0].strip()
    if not token:
        return None
    if "/" in token:
        left, right = token.split("/", 1)
        try:
            denom = float(right)
            if denom == 0:
                return None
            return float(left) / denom
        except ValueError:
            return None
    try:
        return float(token)
    except ValueError:
        return None


class FfprobeMediaProbe:
    """ffprobe-backed :class:`MediaProbe` (PATH or injected runner)."""

    def __init__(
        self,
        *,
        ffprobe: str | None = None,
        run: FfmpegRunner | None = None,
    ) -> None:
        """Store locator overrides.

        Args:
            ffprobe: Optional ffprobe executable.
            run: Override ``subprocess.run``.
        """
        self._ffprobe = ffprobe
        self._run = run

    def duration_s(self, path: str) -> float | None:
        """Format duration in seconds.

        Args:
            path: Media file.

        Returns:
            Seconds, or None when unreadable.
        """
        text = _ffprobe_csv(
            path,
            ["-show_entries", "format=duration", "-of", "csv=p=0"],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if not text:
            return None
        return _parse_float_token(text, index=0)

    def size_wh(self, path: str) -> tuple[int, int] | None:
        """First video stream width×height.

        Args:
            path: Media file.

        Returns:
            ``(width, height)``, or None.
        """
        text = _ffprobe_csv(
            path,
            [
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
            ],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if not text or "," not in text:
            return None
        left, right = text.split(",", 1)
        try:
            return int(left), int(right)
        except ValueError:
            return None

    def has_audio(self, path: str) -> bool:
        """True when stream ``a:0`` is audio.

        Args:
            path: Media file.

        Returns:
            False when ffprobe is missing or no audio stream.
        """
        text = _ffprobe_csv(
            path,
            [
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
            ],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if not text:
            return False
        return "audio" in text.lower()

    def audio_hz(self, path: str) -> int | None:
        """Audio sample rate in Hz.

        Args:
            path: Media file.

        Returns:
            Sample rate, or None.
        """
        text = _ffprobe_csv(
            path,
            [
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate",
                "-of",
                "csv=p=0",
            ],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if not text:
            return None
        value = _parse_float_token(text, index=-1)
        if value is None:
            return None
        return int(value)

    def audio_duration_s(self, path: str) -> float | None:
        """Audio stream duration, else format duration.

        Args:
            path: Media file.

        Returns:
            Seconds, or None.
        """
        text = _ffprobe_csv(
            path,
            [
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=duration",
                "-of",
                "csv=p=0",
            ],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if text:
            token = text.split(",")[0].strip()
            if token and token.upper() != "N/A":
                try:
                    return float(token)
                except ValueError:
                    pass
        return self.duration_s(path)

    def fps(self, path: str) -> float | None:
        """First video stream frame rate.

        Args:
            path: Media file.

        Returns:
            Frames per second, or None.
        """
        text = _ffprobe_csv(
            path,
            [
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-of",
                "csv=p=0",
            ],
            ffprobe=self._ffprobe,
            run=self._run,
        )
        if not text:
            return None
        return _parse_fps(text)


def probe_has_audio(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> bool:
    """True when ffprobe reports an audio stream.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        False when ffprobe is missing or no audio stream.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).has_audio(path)


def probe_audio_hz(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> int | None:
    """Audio sample rate in Hz, or None if unavailable.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        Sample rate in Hz, or None.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).audio_hz(path)


def probe_seconds(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> float | None:
    """Duration in seconds, or None if ffprobe is missing/fails.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        Float seconds or None.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).duration_s(path)


def probe_wh(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> tuple[int, int] | None:
    """First video stream width×height, or None.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        ``(width, height)`` or None.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).size_wh(path)


def probe_audio_seconds(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> float | None:
    """Audio stream duration in seconds, or None.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        Audio duration in seconds, or None.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).audio_duration_s(path)


def probe_fps(
    path: str, ffprobe: str | None = None, run: FfmpegRunner | None = None
) -> float | None:
    """First video stream frame rate, or None.

    Args:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        Frames per second, or None.
    """
    return FfprobeMediaProbe(ffprobe=ffprobe, run=run).fps(path)
