"""Dub Protocol hooks: contracts, speech/media façade, ONSET_PAD_S patch."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from ez_dub import align, hooks, media, pipeline, speech


def test_pipeline_reexports_speech_and_media() -> None:
    assert pipeline.is_url is media.is_url
    assert pipeline.ingest is media.ingest
    assert pipeline.is_speech_like is speech.is_speech_like
    assert pipeline.speech_onset_slice is speech.speech_onset_slice
    assert pipeline.cosine is speech.cosine


def test_hook_protocols_execute() -> None:
    dummy = object()
    cast(Any, hooks.FetchHook.__dict__["__call__"])(dummy, "https://x", Path("."))
    cast(Any, hooks.AsrHook.__dict__["__call__"])(dummy, Path("a.wav"), "en")
    cast(Any, hooks.EmbedHook.__dict__["__call__"])(dummy, [0.0], 24000)
    cast(Any, hooks.TranslateHook.__dict__["__call__"])(dummy, [], "es", "en")
    cast(Any, hooks.TtsHook.__dict__["__call__"])(
        dummy, "hi", "en", "", "chatterbox-ml"
    )
    cast(Any, hooks.StretchHook.__dict__["__call__"])(dummy, [0.0], 10, 24000)
    cast(Any, hooks.SynthesizeFn.__dict__["__call__"])(
        dummy, "hi", "en", "", "chatterbox-ml"
    )
    assert align.stretch_hook is None
    assert pipeline.tts_hook is None


def test_speech_ref_and_zc_edge_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "spk"
    dest.mkdir()
    rate = 24000
    samples = [0.2] * rate * 5

    def _empty_chunks(
        group: list[dict[str, object]],
        src: list[float],
        sr: int,
    ) -> list[dict[str, object]]:
        del group, src, sr
        return [
            {"t0": 0.0, "t1": 1.0, "text": "", "_pcm": [], "rms": 0.2},
            {"t0": 1.0, "t1": 2.0, "text": "hi", "_pcm": [0.1] * 10, "rms": 0.2},
        ]

    monkeypatch.setattr(speech, "_filter_ref_turns", _empty_chunks)
    speech._extract_refs(samples, rate, [{"speaker": "spk00", "t0": 0, "t1": 1}], dest)

    def _one_short(
        group: list[dict[str, object]],
        src: list[float],
        sr: int,
    ) -> list[dict[str, object]]:
        del group, src, sr
        return [{"t0": 0.0, "t1": 1.0, "text": "x", "_pcm": [0.1] * 10, "rms": 0.2}]

    monkeypatch.setattr(speech, "_filter_ref_turns", _one_short)
    monkeypatch.setattr(speech, "_concat_crossfade", lambda *_a, **_k: [])
    speech._extract_refs(samples, rate, [{"speaker": "spk00", "t0": 0, "t1": 1}], dest)

    monkeypatch.setattr(speech, "_zero_cross_indices", lambda _pcm: [0] * 20)
    assert speech.zc_interval_cv([0.1] * 20) == 0.0
