"""Film stitch/probe seams (PEP 544).

``subprocess.run`` overrides and ffprobe fakes stay injectable on
:mod:`ez_film.concat` (``run=`` / ``probe_seconds`` monkeypatches). This
module is the contract those callables must match.
"""

from __future__ import annotations

from typing import Callable, Protocol, TypeAlias


class FfmpegRun(Protocol):
    """``subprocess.run`` or a hermetic test double."""

    def __call__(self, argv: list[str], /, *args: object, **kwargs: object) -> object:
        """Run ``argv`` and return a completed-process-shaped object.

        Args:
            argv: Command vector.
            *args: Extra positional args (ignored by production ffmpeg paths).
            **kwargs: ``check`` / ``capture_output`` / ``text`` in production.

        Returns:
            Object with ``returncode`` / ``stdout`` / ``stderr``.
        """
        ...


# mypy models a ``...`` parameter list as ``Any[]``, so disallow_any_explicit
# flags the alias even though every value that crosses it is an ``object``.
# The alternative arms all fail: no Protocol shape admits the overloaded
# ``subprocess.run`` (mypy rejects an overloaded callable as a Protocol
# implementation), and ``Callable[..., Any]`` would make every ``run(...)``
# call return ``Any``.
RunFn: TypeAlias = Callable[..., object]  # type: ignore[explicit-any]
"""Any callable shaped like ``subprocess.run``.

The return is ``object``: a call site has to narrow before it reads
``returncode`` / ``stdout``, which is what keeps the seam checked.
"""

FfmpegRunner: TypeAlias = FfmpegRun | RunFn
"""``subprocess.run``, a test double, or any ffmpeg runner."""


class FfmpegTools(Protocol):
    """Locate ffmpeg/ffprobe. Missing binary returns None (does not raise).

    Concat's :func:`ez_film.concat.find_ffmpeg` is the required wrapper
    (raises, then imageio-ffmpeg). Accept/stems keep the Optional locator.
    """

    def ffmpeg(self) -> str | None:
        """Return ffmpeg path, or None when missing.

        Returns:
            Executable path, or None.
        """
        ...

    def ffprobe(self) -> str | None:
        """Return ffprobe path, or None when missing.

        Returns:
            Executable path, or None.
        """
        ...


class MediaProbe(Protocol):
    """ffprobe-backed media facts used by concat, accept, and jobstore."""

    def duration_s(self, path: str) -> float | None:
        """Format duration in seconds.

        Args:
            path: Media file.

        Returns:
            Seconds, or None when unreadable.
        """
        ...

    def size_wh(self, path: str) -> tuple[int, int] | None:
        """First video stream widthxheight.

        Args:
            path: Media file.

        Returns:
            ``(width, height)``, or None.
        """
        ...

    def has_audio(self, path: str) -> bool:
        """True when stream ``a:0`` is audio.

        Args:
            path: Media file.

        Returns:
            False when ffprobe is missing or no audio stream.
        """
        ...

    def audio_hz(self, path: str) -> int | None:
        """Audio sample rate in Hz.

        Args:
            path: Media file.

        Returns:
            Sample rate, or None.
        """
        ...

    def audio_duration_s(self, path: str) -> float | None:
        """Audio stream duration, else format duration.

        Args:
            path: Media file.

        Returns:
            Seconds, or None.
        """
        ...

    def fps(self, path: str) -> float | None:
        """First video stream frame rate.

        Args:
            path: Media file.

        Returns:
            Frames per second, or None.
        """
        ...
