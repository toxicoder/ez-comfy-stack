"""Reference-window selection, tune overrides, and Chatterbox conditional cache."""

from __future__ import annotations

import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest

from ez_dub import audio as dub_audio
from ez_dub import pipeline
from ez_dub import speech as dub_speech


def _am_speech(rate: int, seconds: float, fmod: float = 4.5) -> list[float]:
    """Speech-shaped PCM matching the dub suite's formant-plus-noise fixture."""
    n = max(1, int(round(rate * seconds)))
    out: list[float] = []
    seed = 12345
    sr = float(rate)
    for i in range(n):
        t = i / sr
        env = 0.40 + 0.60 * abs(math.sin(2.0 * math.pi * fmod * t))
        voiced = (
            math.sin(2.0 * math.pi * 540.0 * t)
            + 0.55 * math.sin(2.0 * math.pi * 1650.0 * t)
            + 0.30 * math.sin(2.0 * math.pi * 2450.0 * t)
        )
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
        burst = abs(math.sin(2.0 * math.pi * 9.0 * t))
        sample = env * (0.55 * voiced + 0.45 * noise * burst)
        if sample > 1.0:
            sample = 1.0
        elif sample < -1.0:
            sample = -1.0
        out.append(0.45 * sample)
    return out


def _turn(
    ident: int,
    t0: float,
    t1: float,
    text: str,
    *,
    rms: float = 0.2,
    overlap: bool = False,
    words: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One JSON turn."""
    item: dict[str, Any] = {
        "id": ident,
        "speaker": "spk00",
        "t0": t0,
        "t1": t1,
        "overlap": overlap,
        "rms": rms,
        "text": text,
    }
    if words is not None:
        item["words"] = words
    return item


def _passing() -> dict[str, float]:
    """Component vector that clears every hard gate."""
    return {
        "voiced": 0.8,
        "band": 0.6,
        "tonal": 0.9,
        "noise": 0.5,
        "envelope": 0.5,
        "zc": 0.5,
        "clip": 1.0,
        "purity": 1.0,
    }


def test_tuned_float_valid_blank_and_rejected(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    dub_speech._TUNE_WARNED.clear()
    monkeypatch.delenv("EZ_DUB_TUNE_CLONE_TOP_P", raising=False)
    assert dub_speech.tuned_float("CLONE_TOP_P", 0.95, 0.0, 1.0) == 0.95
    monkeypatch.setenv("EZ_DUB_TUNE_CLONE_TOP_P", "0.8")
    assert dub_speech.tuned_float("CLONE_TOP_P", 0.95, 0.0, 1.0) == 0.8
    monkeypatch.setenv("EZ_DUB_TUNE_CLONE_TOP_P", "nope")
    assert dub_speech.tuned_float("CLONE_TOP_P", 0.95, 0.0, 1.0) == 0.95
    assert dub_speech.tuned_float("CLONE_TOP_P", 0.95, 0.0, 1.0) == 0.95
    err = capsys.readouterr().err
    assert err.count("EZ_DUB_TUNE_CLONE_TOP_P") == 1
    dub_speech._TUNE_WARNED.clear()
    monkeypatch.setenv("EZ_DUB_TUNE_CLONE_TOP_P", "1.5")
    assert dub_speech.tuned_float("CLONE_TOP_P", 0.95, 0.0, 1.0) == 0.95
    assert "1.5" in capsys.readouterr().err


def test_percentile_clip_unit_and_dc() -> None:
    assert dub_speech._percentile([], 0.5) == 0.0
    assert dub_speech._percentile([2.0], 0.9) == 2.0
    assert dub_speech._percentile([0.0, 10.0], 0.5) == 5.0
    assert dub_speech._clipping_fraction([]) == 0.0
    assert dub_speech._clipping_fraction([0.1, 0.2]) == 0.0
    assert dub_speech._clipping_fraction([1.0, 0.1, -1.0]) == pytest.approx(2 / 3)
    assert dub_speech._unit_ratio(0.0, 0.6) == 0.0
    assert dub_speech._unit_ratio(0.3, 0.6) == pytest.approx(0.5)
    assert dub_speech._unit_ratio(2.0, 0.6) == 1.0
    assert dub_speech._remove_dc_offset([]) == []
    assert dub_speech._remove_dc_offset([0.4, 0.4, 0.4]) == [0.4, 0.4, 0.4]
    shifted = dub_speech._remove_dc_offset([0.2, -0.2, 0.4, -0.0])
    assert abs(sum(shifted)) < 1e-9


def test_noise_score_branches() -> None:
    rate = 1000
    assert dub_speech._noise_score([0.2] * 10, rate) == 0.0
    assert dub_speech._noise_score([0.0] * rate, rate) == 0.0
    assert dub_speech._noise_score([0.0] * (rate // 2) + [0.4] * (rate // 2), rate) == 1.0
    assert dub_speech._noise_score([0.5] * rate, rate) == 0.0
    assert dub_speech._noise_score([0.001] * rate, rate) == 0.0
    quiet = [0.01] * (rate // 2)
    loud = [0.056] * (rate // 2)
    mid = dub_speech._noise_score(quiet + loud, rate)
    assert 0.0 < mid < 1.0


def test_reject_and_assess_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    assert dub_speech._reject_reason(_passing() | {"clip": 0.9}) == "clip"
    assert dub_speech._reject_reason(_passing() | {"tonal": 0.5}) == "tonal"
    assert dub_speech._reject_reason(_passing() | {"band": 0.1}) == "band"
    assert dub_speech._reject_reason(_passing() | {"voiced": 0.1}) == "unvoiced"
    assert dub_speech._reject_reason(_passing()) == ""
    monkeypatch.setattr(dub_speech, "_window_components", lambda *_a, **_k: _passing())
    monkeypatch.setattr(dub_speech, "is_speech_like", lambda *_a, **_k: False)
    reason, score, _comps = dub_speech._assess_ref_window([0.2], 16000, 1.0)
    assert reason == "not_speech"
    assert score == 0.0
    monkeypatch.setattr(dub_speech, "is_speech_like", lambda *_a, **_k: True)
    reason, score, comps = dub_speech._assess_ref_window([0.2], 16000, 1.0)
    assert reason == ""
    assert score == pytest.approx(dub_speech._window_score(comps))
    assert dub_speech._window_score(_passing()) > 0.5


def test_spans_text_purity_and_prepare() -> None:
    assert dub_speech._iter_ref_spans(0, 10, 1) == []
    assert dub_speech._iter_ref_spans(5, 0, 1) == [(0, 5)]
    assert dub_speech._iter_ref_spans(5, 10, 1) == [(0, 5)]
    assert dub_speech._iter_ref_spans(10, 4, 0)[0] == (0, 4)
    exact = dub_speech._iter_ref_spans(8, 4, 4)
    assert exact == [(0, 4), (4, 8)]
    tailed = dub_speech._iter_ref_spans(11, 4, 4)
    assert tailed[-1] == (7, 11)
    assert dub_speech._window_text({"text": "whole"}, 0.0, 1.0) == "whole"
    assert dub_speech._window_text({"text": "whole", "words": []}, 0.0, 1.0) == "whole"
    assert dub_speech._window_text({"text": "whole", "words": ["nope"]}, 0.0, 1.0) == "whole"
    words = [
        {"t0": 0.0, "t1": 0.4, "text": "keep"},
        {"start": "bad", "end": None, "text": "skip"},
        {"t0": "bad", "t1": "nope", "text": "skip"},
        {"t0": 2.0, "t1": 2.4, "word": "drop"},
        {"t0": 0.5, "t1": 0.9, "text": "  "},
        {"t0": 0.6, "t1": 1.0, "word": "also"},
    ]
    assert dub_speech._window_text({"text": "whole", "words": words}, 0.0, 1.2) == "keep also"
    assert dub_speech._window_text({"text": "whole", "words": words}, 3.0, 4.0) == ""
    assert dub_speech._turn_purity({}) == 1.0
    assert dub_speech._turn_purity({"_embed": [], "_centroid": [1.0]}) == 1.0
    assert dub_speech._turn_purity({"_embed": [1.0, 0.0], "_centroid": [-1.0, 0.0]}) == 0.0
    assert dub_speech._turn_purity({"_embed": [1.0], "_centroid": [1.0]}) == 1.0
    rate = 8000
    speech = [0.2] * (rate * 5)
    parent = [0.0] * rate + speech
    prepared = dub_speech._prepare_window_pcm(parent, rate, 0, rate + rate)
    assert prepared is not None
    piece, start, end = prepared
    assert start >= rate - 200
    assert len(piece) >= int(dub_speech.REF_MIN_S * rate) - 200
    assert end > start
    assert dub_speech._prepare_window_pcm([], rate, 0, 0) is None
    short = [0.0] * rate + [0.2] * rate
    assert dub_speech._prepare_window_pcm(short, rate, 0, len(short)) is None
    plain = dub_speech._prepare_window_pcm(speech, rate, 0, len(speech))
    assert plain is not None
    assert plain[1] == 0


def test_pick_join_and_dominant_reject() -> None:
    windows = [
        {"ok": True, "score": 0.2, "t0": 0.0, "t1": 2.0, "pcm": [0.1] * 10, "reason": ""},
        {"ok": False, "score": 0.0, "t0": 2.0, "t1": 3.0, "pcm": [0.1], "reason": "tonal"},
        {"ok": True, "score": 0.9, "t0": 3.0, "t1": 5.0, "pcm": [0.2] * 10, "reason": ""},
        {"ok": False, "score": 0.0, "t0": 5.0, "t1": 6.0, "pcm": [0.1], "reason": "clip"},
    ]
    chosen = dub_speech._pick_ref_windows(windows, 15)
    assert [item["score"] for item in chosen] == [0.9, 0.2]
    long = [{"ok": True, "score": 0.4, "t0": 0.0, "t1": 7.0, "pcm": [0.1], "reason": ""}]
    assert dub_speech._pick_ref_windows(long, 100) == long
    assert dub_speech._pick_ref_windows([windows[1]], 10) == []
    assert dub_speech._dominant_reject([]) == ""
    assert dub_speech._dominant_reject(windows) == "clip"
    assert dub_speech._join_ref_text(["", "a", "a", " b "]) == "a b"
    used, chunks = dub_speech._loudness_ref_chunks(
        [
            {"t0": 0.0, "t1": 2.0, "rms": 0.2, "_pcm": []},
            {"t0": 2.0, "t1": 4.0, "rms": 0.4, "_pcm": [0.2, 0.2]},
        ],
        10,
    )
    assert chunks == [[0.2, 0.2]]
    assert used[0]["t0"] == 2.0


def test_extract_prefers_clean_window_over_clipped(tmp_path: Path) -> None:
    rate = 24000
    clean = _am_speech(rate, 6.0)
    dirty = [1.0 if i % 2 == 0 else -1.0 for i in range(rate * 6)]
    samples = clean + dirty
    turns = [
        _turn(1, 0.0, 6.0, "clean"),
        _turn(2, 6.0, 12.0, "dirty"),
    ]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    side = json.loads(refs["spk00"].with_suffix(".ref.json").read_text(encoding="utf-8"))
    assert side["degraded"] is False
    assert side["text"] == "clean"
    assert side["score"] > 0.0
    assert "voiced" in side["components"]
    note = refs["spk00"].with_suffix(".txt").read_text(encoding="utf-8")
    assert note.strip() == "clean"
    info, extra = pipeline._reference_qc(tmp_path / "speakers")
    assert extra == []
    assert info["spk00"]["speaker"] == "spk00"


def test_extract_extends_past_leading_silence(tmp_path: Path) -> None:
    rate = 24000
    silence = [0.0] * (rate * 2)
    speech = _am_speech(rate, 6.0)
    samples = silence + speech
    turns = [_turn(1, 0.0, 8.0, "padded")]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    wav, sr = dub_audio.read_wav(refs["spk00"])
    side = json.loads(refs["spk00"].with_suffix(".ref.json").read_text(encoding="utf-8"))
    assert sr == rate
    assert side["degraded"] is False
    assert side["t0"] >= 1.5
    head = wav[: int(sr * 0.1)]
    assert max(abs(x) for x in head) > 0.05
    assert len(wav) / sr >= dub_speech.REF_MIN_S - 0.05


def test_extract_sidecar_drops_words_outside_the_window(tmp_path: Path) -> None:
    rate = 24000
    samples = _am_speech(rate, 12.0)
    words = [
        {"t0": 0.2, "t1": 0.6, "text": "early"},
        {"t0": 11.2, "t1": 11.6, "text": "late"},
    ]
    turns = [_turn(1, 0.0, 12.0, "early late", words=words)]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    side = json.loads(refs["spk00"].with_suffix(".ref.json").read_text(encoding="utf-8"))
    assert side["degraded"] is False
    assert "early" in side["text"] or "late" in side["text"]
    if side["t1"] < 11.0:
        assert "late" not in side["text"]
    if side["t0"] > 1.0:
        assert "early" not in side["text"]
    assert side["text"] != "early late"


def test_extract_degraded_constant_and_diagnostics(tmp_path: Path) -> None:
    rate = 24000
    samples = [0.25] * (rate * 8)
    turns = [
        _turn(1, 0.0, 3.0, "a"),
        _turn(2, 3.0, 6.0, "b"),
    ]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers", max_s=0)
    side = json.loads((tmp_path / "speakers" / "spk00.ref.json").read_text(encoding="utf-8"))
    assert side["degraded"] is True
    assert side["score"] is None
    assert "a" in side["text"] and "b" in side["text"]
    assert refs["spk00"].is_file()
    info, extra = pipeline._reference_qc(tmp_path / "speakers")
    assert extra == ["ref_degraded"]
    assert info["spk00"]["degraded"] is True
    missing, none_extra = pipeline._reference_qc(tmp_path / "absent")
    assert missing == {}
    assert none_extra == []
    (tmp_path / "speakers" / "spk01.ref.json").write_text("[1, 2]", encoding="utf-8")
    (tmp_path / "speakers" / "spk02.ref.json").write_text("{", encoding="utf-8")
    loaded = dub_speech.ref_diagnostics(tmp_path / "speakers")
    assert "spk01" not in loaded
    assert "spk02" not in loaded
    assert loaded["spk00"]["degraded"] is True


def test_zc_interval_cv_zero_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    gaps = dub_speech.ZC_INTERVAL_MIN_GAPS + 2
    monkeypatch.setattr(dub_speech, "_zero_cross_indices", lambda _pcm: [4] * gaps)
    assert dub_speech.zc_interval_cv([0.1, -0.1, 0.1]) == 0.0


def test_ref_windows_skip_empty_pcm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert dub_speech._ref_windows({"t0": 0.0, "_pcm": []}, 24000) == []
    monkeypatch.setattr(dub_speech, "_slice_pcm", lambda *_a, **_k: [])
    turns = [_turn(i, float(i), float(i) + 1.5, "") for i in range(3)]
    refs = dub_speech._extract_refs([0.2] * 24000, 24000, turns, tmp_path / "empty")
    assert refs == {}


def test_ensure_conditionals_caches_and_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    seen: list[dict[str, Any]] = []

    class _Model:
        sr = 24000

        def __init__(self) -> None:
            self.conds: object | None = None
            self.preps: list[tuple[str, float]] = []

        def prepare_conditionals(self, path: str, exaggeration: float = 0.5) -> None:
            self.preps.append((path, exaggeration))
            self.conds = object()

        def generate(self, text: str, **kwargs: Any) -> list[float]:
            del text
            seen.append(dict(kwargs))
            return [0.1] * 240

    model = _Model()
    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (model, ""))
    pipeline._CHATTERBOX_COND_KEY = ""
    ref = tmp_path / "spk.wav"
    dub_audio.write_wav(ref, [0.2] * 2400, 24000)
    for text in ("uno", "dos", "tres"):
        pcm, _rate, err = pipeline._try_chatterbox(text, "es", str(ref), exaggeration=0.5)
        assert err == ""
        assert pcm
    assert len(model.preps) == 1
    assert "audio_prompt_path" not in seen[-1]
    pcm, _rate, err = pipeline._try_chatterbox("cuatro", "es", str(ref), exaggeration=0.8)
    assert err == "" and pcm
    assert len(model.preps) == 2
    assert model.preps[1][1] == pytest.approx(0.8)
    model.conds = None
    pipeline._try_chatterbox("cinco", "es", str(ref), exaggeration=0.8)
    assert len(model.preps) == 3

    class _PathOnly:
        sr = 24000

        def __init__(self) -> None:
            self.conds: object | None = None
            self.preps: list[str] = []

        def prepare_conditionals(self, path: str) -> None:
            self.preps.append(path)
            self.conds = object()

        def generate(self, text: str, **kwargs: Any) -> list[float]:
            del text, kwargs
            return [0.2] * 80

    path_only = _PathOnly()
    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (path_only, ""))
    pipeline._CHATTERBOX_COND_KEY = ""
    pcm, _rate, err = pipeline._try_chatterbox("seis", "es", str(ref))
    assert err == "" and pcm
    assert path_only.preps == [str(ref)]

    class _Boom:
        sr = 24000

        def prepare_conditionals(self, path: str, exaggeration: float = 0.5) -> None:
            del path, exaggeration
            raise RuntimeError("nope")

        def generate(self, text: str, **kwargs: Any) -> list[float]:
            del text
            seen.append(dict(kwargs))
            return [0.1] * 40

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Boom(), ""))
    pipeline._CHATTERBOX_COND_KEY = ""
    pcm, _rate, err = pipeline._try_chatterbox("siete", "es", str(ref))
    assert err == "" and pcm
    assert seen[-1]["audio_prompt_path"] == str(ref)
    assert "prepare_conditionals failed" in capsys.readouterr().err


def test_ensure_conditionals_under_local_ckpt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered: list[Path] = []

    @contextmanager
    def _null(ckpt: Path) -> Iterator[None]:
        entered.append(ckpt)
        yield

    class _Model:
        sr = 24000

        def __init__(self) -> None:
            self.conds: object | None = None
            self.n = 0

        def prepare_conditionals(self, path: str, exaggeration: float = 0.5) -> None:
            del path, exaggeration
            self.n += 1
            self.conds = object()

        def generate(self, text: str, **kwargs: Any) -> list[float]:
            del text, kwargs
            return [0.1] * 20

    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: tmp_path)
    monkeypatch.setattr(pipeline, "_chatterbox_local_only", _null)
    model = _Model()
    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (model, ""))
    pipeline._CHATTERBOX_COND_KEY = ""
    ref = tmp_path / "ref.wav"
    dub_audio.write_wav(ref, [0.2] * 800, 8000)
    pcm, _rate, err = pipeline._try_chatterbox("ocho", "es", str(ref))
    assert err == "" and pcm
    assert entered == [tmp_path, tmp_path]
    assert model.n == 1
    assert pipeline._CHATTERBOX_COND_KEY.startswith(str(ref))


def test_sampling_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dub_speech._TUNE_WARNED.clear()
    seen: list[dict[str, Any]] = []

    class _Model:
        sr = 24000

        def generate(self, text: str, **kwargs: Any) -> list[float]:
            del text
            seen.append(dict(kwargs))
            return [0.1] * 40

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Model(), ""))
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    monkeypatch.setenv("EZ_DUB_TUNE_CLONE_TOP_P", "0.7")
    monkeypatch.setenv("EZ_DUB_TUNE_TEMPERATURE", "0.4")
    monkeypatch.setenv("EZ_DUB_TUNE_REPETITION_PENALTY", "1.4")
    monkeypatch.setenv("EZ_DUB_TUNE_MIN_P", "0.02")
    monkeypatch.setenv("EZ_DUB_TUNE_EXAGGERATION", "0.7")
    monkeypatch.setenv("EZ_DUB_TUNE_CFG_CROSS", "0.4")
    assert pipeline.clone_cfg_weight("en", "es", -1) == pytest.approx(0.4)
    ref = tmp_path / "none.wav"
    pcm, _rate, err = pipeline._try_chatterbox(
        "nueve", "es", str(ref), exaggeration=0.5, temperature=0.8
    )
    assert err == "" and pcm
    assert seen[-1]["top_p"] == pytest.approx(0.7)
    assert seen[-1]["temperature"] == pytest.approx(0.4)
    assert seen[-1]["repetition_penalty"] == pytest.approx(1.4)
    assert seen[-1]["min_p"] == pytest.approx(0.02)
    assert seen[-1]["exaggeration"] == pytest.approx(0.7)
    seen.clear()
    pipeline._try_chatterbox("diez", "es", "", exaggeration=0.9, temperature=0.6)
    assert seen[-1]["exaggeration"] == pytest.approx(0.9)
    assert seen[-1]["temperature"] == pytest.approx(0.4)
    monkeypatch.setenv("EZ_DUB_TUNE_CFG_CROSS", "9")
    assert pipeline.clone_cfg_weight("en", "es", -1) == pipeline.CFG_CROSS_LANG


def test_qc_report_includes_reference() -> None:
    from ez_dub.qc import evaluate_qc

    report = evaluate_qc(
        [0.5] * 8000,
        8000,
        [{"t0": 0.0, "t1": 1.0, "text": "Hola.", "text_target": "Hola."}],
        target_language="es",
        peak=0.5,
        reference={"spk00": {"degraded": False, "score": 0.5}},
    )
    assert report["reference"]["spk00"]["score"] == 0.5
    plain = evaluate_qc(
        [0.5] * 8000,
        8000,
        [],
        target_language="en",
        peak=0.5,
    )
    assert plain["reference"] == {}
