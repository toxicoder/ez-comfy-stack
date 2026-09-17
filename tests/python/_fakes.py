"""Hermetic fakes that satisfy production Protocols.

Point pack tests at these instead of one-off lambdas when convenient.
Coverage megatests may keep their local doubles.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any


class FakeProgress:
    """``ProgressReporter`` stand-in."""

    def update(self, n: int = 1) -> None:
        del n

    def update_absolute(self, value: int) -> None:
        del value


class FakeFfmpegRun:
    """``FfmpegRun`` stand-in (always succeeds, empty stdout)."""

    def __call__(
        self, argv: list[str], /, *args: object, **kwargs: object
    ) -> SimpleNamespace:
        del argv, args, kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")


class FakeChatCompleter:
    """``ChatCompleter`` stand-in (passthrough text)."""

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 800,
        unload: bool = False,
    ) -> tuple[str, str | None]:
        del system, max_tokens, unload
        return (user, None)


class FakeSidecarResponse:
    """Minimal sidecar HTTP response."""

    def read(self) -> bytes:
        return b"{}"

    def __enter__(self) -> FakeSidecarResponse:
        return self

    def __exit__(self, *args: object) -> None:
        del args


class FakeSidecarTransport:
    """``SidecarTransport`` stand-in."""

    def urlopen(self, request: object, timeout: float) -> FakeSidecarResponse:
        del request, timeout
        return FakeSidecarResponse()


class FakeFolderPaths:
    """Narrow folder_paths.get_output_directory stand-in."""

    def __init__(self, output: Path) -> None:
        self._output = output

    def get_output_directory(self) -> str:
        return str(self._output)


class FakeWhisperModel:
    """faster-whisper transcribe stand-in."""

    def transcribe(self, wav_path: object, language: str = "en") -> list[dict[str, Any]]:
        del wav_path, language
        return []
