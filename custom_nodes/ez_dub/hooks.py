"""Dub test/production seams as ``typing.Protocol`` interfaces.

Hook *variables* stay on :mod:`ez_dub.pipeline` so existing
``pipeline.tts_hook = ...`` monkeypatches keep working. This module is the
contract those callables must match.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol


class FetchHook(Protocol):
    """URL ingest stand-in (yt-dlp in production)."""

    def __call__(self, url: str, dest_dir: Path, /) -> Path:
        """Fetch ``url`` into ``dest_dir``.

        Args:
            url: http(s) URL.
            dest_dir: Job directory.

        Returns:
            Local media path.
        """
        ...


class AsrHook(Protocol):
    """ASR stand-in (faster-whisper in production)."""

    def __call__(
        self, wav_path: Path, language: str, /
    ) -> Sequence[Mapping[str, object]]:
        """Transcribe a wav.

        Args:
            wav_path: Source wav.
            language: ISO language or ``auto``.

        Returns:
            Turn-like mappings (``t0`` / ``t1`` / ``text`` / ``speaker``).
            Open mapping on purpose: a hook fills four of :class:`Turn`'s
            keys, and :func:`ez_dub.turns.normalize_turn` fills the rest.
        """
        ...


class EmbedHook(Protocol):
    """Speaker-embedding stand-in."""

    def __call__(self, pcm: list[float], rate: int, /) -> list[float]:
        """Embed a PCM window.

        Args:
            pcm: Mono PCM.
            rate: Sample rate.

        Returns:
            Speaker vector.
        """
        ...


class TranslateHook(Protocol):
    """Turn-translation stand-in (GGUF in production)."""

    def __call__(
        self, turns: Sequence[Mapping[str, object]], target: str, source: str, /
    ) -> Sequence[Mapping[str, object]]:
        """Translate ``turns`` into ``target``.

        Args:
            turns: Normalized turns.
            target: ISO target.
            source: ISO source or ``auto``.

        Returns:
            Turns with ``text_target`` filled. Open mapping on purpose: a
            hook may hand back a subset of the keys it was given.
        """
        ...


class TtsHook(Protocol):
    """Clone/TTS stand-in (Chatterbox / Qwen3 in production)."""

    def __call__(
        self, text: str, language: str, ref_wav: str, engine: str, /
    ) -> tuple[list[float], int]:
        """Synthesize one clone chunk.

        Args:
            text: Spoken line.
            language: ISO language id.
            ref_wav: Speaker reference path (may be empty).
            engine: ``chatterbox-ml`` or ``qwen3tts``.

        Returns:
            ``(pcm, sample_rate)``.
        """
        ...


class StretchHook(Protocol):
    """Time-stretch stand-in (WSOLA / atempo in production)."""

    def __call__(
        self, samples: list[float], out_len: int, rate: int, /
    ) -> list[float]:
        """Stretch ``samples`` to ``out_len``.

        Args:
            samples: Mono PCM.
            out_len: Target length in samples.
            rate: Sample rate.

        Returns:
            Stretched PCM.
        """
        ...


class SynthesizeFn(Protocol):
    """Clone callback used by render and the disclosure bumper."""

    def __call__(
        self, text: str, language: str, ref_wav: str, engine: str, /
    ) -> tuple[list[float], int] | tuple[list[float], int, str] | None:
        """Synthesize one line.

        Args:
            text: Spoken line.
            language: ISO language id.
            ref_wav: Speaker reference path.
            engine: Clone engine id.

        Returns:
            ``(pcm, rate)``, ``(pcm, rate, err)``, or ``None`` when the hook
            declined to synthesize.
        """
        ...
