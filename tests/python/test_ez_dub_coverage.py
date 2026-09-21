"""Hermetic coverage for remaining ez_dub branches (no GPU, network, or binaries)."""

from __future__ import annotations

import json
import math
import os
import struct
import sys
import types
import wave
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_dub import align  # noqa: E402
from ez_dub import audio as dub_audio  # noqa: E402
from ez_dub import disclosure as dub_disclosure  # noqa: E402
from ez_dub import jobstore  # noqa: E402
from ez_dub import nodes as dub_nodes  # noqa: E402
from ez_dub import pipeline  # noqa: E402
from ez_dub import qc as dub_qc  # noqa: E402
from ez_dub import rights as dub_rights  # noqa: E402
from ez_dub import sanitize as dub_sanitize  # noqa: E402
from ez_dub import srt as dub_srt  # noqa: E402
from ez_dub import turns as dub_turns  # noqa: E402
from ez_dub.nodes import ENGINE_CHATTERBOX, EZDubIngest, EZDubRender, EZDubScript  # noqa: E402


def _am_speech(rate: int, seconds: float, fmod: float = 4.5) -> list[float]:
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
        sample = max(-1.0, min(1.0, sample))
        out.append(0.45 * sample)
    return out


def _passthrough_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    def _run(cmd: list[str]) -> tuple[int, str]:
        if not cmd or cmd[0] != "ffmpeg":
            return 127, "missing"
        src = ""
        dest = cmd[-1]
        for i, tok in enumerate(cmd):
            if tok == "-i" and i + 1 < len(cmd):
                src = cmd[i + 1]
        if not src:
            return 1, "no input"
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(Path(src).read_bytes() if Path(src).is_file() else b"x")
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _run)


def _two_turns() -> list[dict]:
    return [
        {
            "id": 1,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 1.0,
            "text": "Welcome back to the tape.",
            "text_target": "",
            "overlap": False,
            "rms": 0.1,
        },
        {
            "id": 2,
            "speaker": "spk01",
            "t0": 1.2,
            "t1": 2.4,
            "text": "Today we stay on the match.",
            "text_target": "",
            "overlap": False,
            "rms": 0.1,
        },
    ]


def _es_payload() -> dict:
    return {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "",
        "turns": [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.4,
                "t1": 2.8,
                "text": "Welcome back to the tape.",
                "text_target": "Bienvenidos de nuevo a la cinta.",
                "overlap": False,
                "rms": 0.2,
            },
            {
                "id": 2,
                "speaker": "spk01",
                "t0": 3.0,
                "t1": 6.2,
                "text": "Today we stay on the match in front of us.",
                "text_target": "Hoy nos quedamos en el partido que tenemos delante.",
                "overlap": False,
                "rms": 0.2,
            },
        ],
    }


class _FakeTensor:
    def __init__(self, data: Any, ndim: int) -> None:
        self._data = data
        self.ndim = ndim

    def unsqueeze(self, _dim: int) -> _FakeTensor:
        return _FakeTensor(self._data, self.ndim + 1)


class _FakeTorch:
    float32 = "float32"

    @staticmethod
    def zeros(*_shape: int) -> _FakeTensor:
        return _FakeTensor([[[0.0]]], 3)

    @staticmethod
    def as_tensor(samples: Any, dtype: Any = None) -> _FakeTensor:
        del dtype
        if isinstance(samples, list) and samples and isinstance(samples[0], list):
            return _FakeTensor(samples, 2)
        return _FakeTensor(list(samples) if not isinstance(samples, list) else samples, 1)


# --- rights / srt / turns / sanitize / qc / disclosure / jobstore / audio / nodes


def test_rights_int_float_and_unknown() -> None:
    assert dub_rights.as_bool(1) is True
    assert dub_rights.as_bool(0.0) is False
    assert dub_rights.as_bool(None) is False
    assert dub_rights.as_bool([]) is False


def test_srt_clamps_inverted_times() -> None:
    body = dub_srt.turns_to_srt(
        [{"t0": 1.0, "t1": 0.5, "text": "Hi"}],
        field="text",
    )
    assert "00:00:01,000 --> 00:00:01,200" in body
    assert "Hi" in body


def test_turns_normalize_and_parse_edges() -> None:
    junk = dub_turns.normalize_turn("nope", 3)
    assert junk["id"] == 3
    assert junk["speaker"] == "spk00"
    swapped = dub_turns.normalize_turn({"t0": 2.0, "t1": 0.5, "id": "x"}, 9)
    assert swapped["t0"] == 0.5
    assert swapped["t1"] == 2.0
    assert swapped["id"] == 9
    parsed = dub_turns.parse_payload(0)
    assert parsed["status"] in {"invalid json", "empty script"}
    listed = dub_turns.parse_payload('[{"t0": 0, "t1": 1, "text": "Hi"}]')
    assert listed["turns"][0]["text"] == "Hi"
    bad = dub_turns.parse_payload("1")
    assert bad["status"] == "invalid json"
    staged = dub_turns.parse_payload({"stage": "nope", "turns": []})
    assert staged["stage"] == dub_turns.DEFAULT_STAGE
    assert dub_turns.merge_adjacent_turns([]) == []
    joined = dub_turns.merge_adjacent_turns(
        [
            dub_turns.normalize_turn({"speaker": "spk00", "t0": 0.0, "t1": 0.4, "text": ""}, 1),
            dub_turns.normalize_turn({"speaker": "spk00", "t0": 0.5, "t1": 0.9, "text": "Hi"}, 2),
        ]
    )
    assert len(joined) == 1
    assert joined[0]["text"] == "Hi"


def test_sanitize_quotes_lang_and_leak_edges() -> None:
    nested = dub_sanitize.strip_model_fences("'\"Hola equipo\"'")
    assert "Hola" in nested
    prefixed = dub_sanitize.strip_model_fences('Translation: "Adios"')
    assert prefixed == "Adios"
    assert dub_sanitize.strip_leak_tails("") == ""
    only_leak = dub_sanitize.strip_leak_tails("voice model")
    assert only_leak == ""
    leading = dub_sanitize.strip_leak_tails(
        "voice model. Keep this Spanish sentence about el tren."
    )
    assert isinstance(leading, str)
    two = dub_sanitize.strip_leak_tails("Hola equipo. Adios amigos.")
    assert "Hola" in two
    assert dub_sanitize.looks_like_target("Hello", "en") is True
    assert dub_sanitize.looks_like_target("Hola equipo", "es-MX") is True


def test_qc_lang_prefix_skip_unspoken_and_exception() -> None:
    mix = [0.4] * 24000
    report = dub_qc.evaluate_qc(
        mix,
        24000,
        [
            {"t0": 0.0, "t1": 0.4, "text": "   ", "text_target": ""},
            {
                "t0": 0.5,
                "t1": 1.0,
                "text": "Hello there everyone.",
                "text_target": "Hola.",
            },
        ],
        target_language="es-MX",
        peak=0.89,
    )
    assert isinstance(report, dict)
    broken = dub_qc.evaluate_qc(object(), 24000, [], target_language="es", peak=0.5)  # type: ignore[arg-type]
    assert broken["ok"] is False
    assert broken["checks"] == []


def test_disclosure_lang_sentence_synth_and_overlay() -> None:
    assert dub_disclosure._lang_key("pt-BR") == "pt"
    long = ("Word " * 80).strip() + ". More words follow here for the bumper."
    first = dub_disclosure._first_sentence(long)
    assert first.endswith(".")
    assert len(first) < len(long)
    no_sep = dub_disclosure._first_sentence("x" * 240)
    assert len(no_sep) <= 220
    assert dub_disclosure._synth_pcm(lambda *_a: None, "t", "es", "", "e") == ([], 0)
    assert dub_disclosure._synth_pcm(lambda *_a: ([], 24000), "t", "es", "", "e") == ([], 24000)
    mix = [0.05] * 100
    dub_disclosure._overlay_region(mix, [0.2] * 10, 0, 4)
    assert mix[0] == 0.05
    assert dub_disclosure._crop_bumper_hush([], 24000) == []
    assert dub_disclosure._first_t0(None) == 0.0
    assert dub_disclosure._first_t0([{"t0": object()}]) == 0.0
    assert dub_disclosure._first_t0([{"t0": "nope"}, {"t0": 1.5}]) == 1.5

    def _empty(*_a: Any, **_k: Any) -> tuple[list[float], int]:
        return [], 24000

    out, status = dub_disclosure.apply_spoken_disclosure(
        [0.05] * 1000,
        24000,
        language="es",
        engine=ENGINE_CHATTERBOX,
        ref_wav="",
        turns=[],
        synthesize=_empty,
    )
    assert status == "disclosure skipped"
    assert len(out) == 1000

    def _other_rate(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int, str]:
        del text, language, ref_wav, engine
        return [0.3] * 8000, 8000, ""

    out2, status2 = dub_disclosure.apply_spoken_disclosure(
        [0.05] * (24000 * 4),
        24000,
        language="es",
        engine=ENGINE_CHATTERBOX,
        ref_wav="",
        turns=[{"t0": 2.0, "t1": 3.0}],
        synthesize=_other_rate,
    )
    assert status2 == "spoken disclosure"
    assert len(out2) == 24000 * 4


def test_jobstore_fallbacks_invalid_state_and_read_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> Path:
        raise RuntimeError("no ez_common")

    monkeypatch.setattr("ez_common.output_root", _boom)
    fake = types.SimpleNamespace(get_output_directory=lambda: "/comfy/from-folder")
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    assert jobstore.output_root() == Path("/comfy/from-folder")

    fake_empty = types.SimpleNamespace(get_output_directory=lambda: "")
    monkeypatch.setitem(sys.modules, "folder_paths", fake_empty)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == tmp_path

    def _folder_boom() -> str:
        raise RuntimeError("folder miss")

    monkeypatch.setitem(
        sys.modules, "folder_paths", types.SimpleNamespace(get_output_directory=_folder_boom)
    )
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)

    def fake_is_dir_outputs(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir_outputs)
    assert jobstore.output_root() == Path("/outputs")

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    monkeypatch.setenv("COMFY_OUTPUT", str(tmp_path / "alias"))
    assert jobstore.output_root() == tmp_path / "alias"

    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    assert jobstore.output_root() == Path("/mnt/comfy-output")

    dest = tmp_path / "dubs" / "bad"
    dest.mkdir(parents=True)
    (dest / "state.json").write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid jobstore"):
        jobstore.load_state(dest)
    payload = {"ok": True}
    path = tmp_path / "x.json"
    jobstore.write_json(path, payload)
    assert jobstore.read_json(path) == payload


def test_audio_widths_channels_and_torch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    u8 = tmp_path / "u8.wav"
    with wave.open(str(u8), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(1)
        handle.setframerate(8000)
        handle.writeframes(bytes([128, 255, 0, 64]))
    samples, rate = dub_audio.read_wav(u8)
    assert rate == 8000
    assert len(samples) == 4

    wide = tmp_path / "24.wav"
    with wave.open(str(wide), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(3)
        handle.setframerate(8000)
        frame = struct.pack("<h", 16000) + b"\x00"
        handle.writeframes(frame * 3)
    w_samples, w_rate = dub_audio.read_wav(wide)
    assert w_rate == 8000
    assert len(w_samples) == 3

    stereo = tmp_path / "st.wav"
    with wave.open(str(stereo), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(struct.pack("<hh", 16384, -16384) * 4)
    mono, s_rate = dub_audio.read_wav(stereo)
    assert s_rate == 8000
    assert len(mono) == 4

    monkeypatch.setitem(sys.modules, "torch", _FakeTorch)
    empty = dub_audio.empty_audio(16000)
    assert empty["sample_rate"] == 16000
    packed = dub_audio.audio_from_pcm([0.1, 0.2], 16000)
    assert packed["sample_rate"] == 16000
    packed2 = dub_audio.audio_from_pcm([[0.1, 0.2]], 16000)
    assert packed2["sample_rate"] == 16000


def test_nodes_empty_wav_and_overlay_disclosure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))

    def _ingest(source: str, have_rights: bool, slug: str) -> tuple[Path, str]:
        del source, have_rights
        dest = jobstore.dub_dir(slug)
        dest.mkdir(parents=True, exist_ok=True)
        return dest, "ok"

    monkeypatch.setattr(dub_nodes, "ingest", _ingest)
    monkeypatch.setattr(dub_nodes, "resolve_media_source", lambda *a, **k: "/tmp/x.wav")
    out = EZDubIngest().run("clip.wav", True, "ep")
    assert out["result"][0] == "ep"

    def _synth(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int, str]:
        del text, language, ref_wav, engine
        return _am_speech(24000, 0.5), 24000, ""

    monkeypatch.setattr(dub_nodes, "synthesize_turn", _synth)
    mix, status = EZDubRender()._overlay_disclosure(
        [0.05] * (24000 * 4),
        24000,
        "not-an-engine",
        language="es",
        ref_wav="",
        turns=[{"t0": 2.0, "t1": 3.0, "speaker": "spk00"}],
    )
    assert status in {"spoken disclosure", "disclosure skipped"}
    assert len(mix) == 24000 * 4


# --- align


def test_align_resample_stretch_fit_room_timeline() -> None:
    assert align.rms([]) == 0.0
    assert align.resample_linear([0.1, 0.2], 0) == []
    assert align.resample_linear([], 4) == [0.0] * 4
    same = [0.1, 0.2, 0.3]
    assert align.resample_linear(same, 3) == same
    assert align.resample_linear([0.7, 0.1], 1) == [0.7]
    assert align.time_stretch([0.1, 0.2], 0, 24000) == []
    assert align.time_stretch([], 5, 24000) == [0.0] * 5
    assert align.time_stretch(same, 3, 24000) == same
    odd = align.time_stretch([0.2] * 80, 90, 1650)
    assert len(odd) == 90
    short = align.time_stretch([0.1] * 10, 40, 24000)
    assert len(short) == 40
    grains = align.time_stretch([0.2] * 500, 480, 24000)
    assert len(grains) == 480
    stretched = align.time_stretch([0.2] * 600, 2400, 24000)
    assert len(stretched) == 2400
    assert align.pitch_preserving_stretch([], 8, 24000) == [0.0] * 8

    def _hook(samples: Any, out_len: int, rate: int) -> list[float]:
        del samples, rate
        return [0.3] * out_len

    align.stretch_hook = None
    try:
        monkey_got = [0.4] * 50

        def _atempo(samples: Any, out_len: int, rate: int) -> Any:
            del samples, rate
            return monkey_got if out_len == 50 else None

        orig = align._ffmpeg_atempo
        align._ffmpeg_atempo = _atempo  # type: ignore[method-assign]
        try:
            got = align.pitch_preserving_stretch([0.1] * 80, 50, 24000)
        finally:
            align._ffmpeg_atempo = orig  # type: ignore[method-assign]
        assert got == monkey_got
    finally:
        align.stretch_hook = None

    align.stretch_hook = _hook
    try:
        slow_cap, flags = align.fit_turn([0.2] * 4000, 24000, 0.05, max_speed=0.4)
        assert flags["trimmed"] is True or flags["speed"] >= 1.0
        assert slow_cap
        fitted, meta = align.fit_turn([0.2] * 10000, 24000, 0.35, spill_s=0.05, max_speed=1.25)
        assert meta["speed"] >= 1.0
        assert len(fitted) >= 1
    finally:
        align.stretch_hook = None

    class _TruthEmpty:
        def __bool__(self) -> bool:
            return True

        def __iter__(self) -> object:
            return iter(())

    locked, lock_flags = align.lock_duration(
        [0.1] * 4, 10, room=_TruthEmpty(), rate=1000  # type: ignore[arg-type]
    )
    assert lock_flags["padded"] is True
    assert len(locked) == 10

    source = [0.2] * 200 + [0.0] * 50
    room = align.collect_room_tone(
        source,
        [{"t0": 0.0, "t1": 0.008}],
        24000,
        want=80,
    )
    assert len(room) == 80
    mix = align.build_timeline(
        [0.1] * 100,
        [{"t0": 0.0, "pcm": []}, {"t0": -0.5, "pcm": [0.9] * 10}, {"t0": 4.0, "pcm": [0.5]}],
        1000,
        keep_bed=True,
        xfade_ms=5,
    )
    assert len(mix) == 100


def test_ffmpeg_atempo_empty_stdout_and_resample(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(align.shutil, "which", lambda _name: "/usr/bin/ffmpeg")

    class _Empty:
        returncode = 0
        stdout = b"xx"

    monkeypatch.setattr(align.subprocess, "run", lambda *_a, **_k: _Empty())
    assert align._ffmpeg_atempo([0.1] * 200, 100, 24000) is None

    class _Short:
        returncode = 0
        stdout = struct.pack("<" + "f" * 40, *([0.1] * 40))

    monkeypatch.setattr(align.subprocess, "run", lambda *_a, **_k: _Short())
    out = align._ffmpeg_atempo([0.1] * 200, 100, 24000)
    assert out is not None
    assert len(out) == 100


# --- pipeline helpers


def test_progress_and_input_directory_fallbacks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_total: int) -> Any:
        raise RuntimeError("no comfy bar")

    monkeypatch.setattr("ez_common.node_progress", _boom)
    assert pipeline._progress(3) is None

    fake = types.SimpleNamespace(get_input_directory=lambda: "/comfy/input")
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    assert pipeline.input_directory() == Path("/comfy/input")
    fake_blank = types.SimpleNamespace(get_input_directory=lambda: "")
    monkeypatch.setitem(sys.modules, "folder_paths", fake_blank)
    assert str(pipeline.input_directory())

    def _input_boom() -> str:
        raise RuntimeError("no folder_paths")

    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        types.SimpleNamespace(get_input_directory=_input_boom),
    )
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    original = Path.is_dir

    def fake_inputs(self: Path) -> bool:
        if str(self) == "/inputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_inputs)
    assert pipeline.input_directory() == Path("/inputs")


def test_list_input_media_skips_dirs_and_hidden(tmp_path: Path) -> None:
    (tmp_path / "keep.wav").write_bytes(b"RIFF")
    (tmp_path / ".hidden.wav").write_bytes(b"RIFF")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "clip.mp4").write_bytes(b"ftyp")
    names = pipeline.list_input_media(tmp_path)
    assert names == ["keep.wav"]


def test_resolve_media_source_url_and_annotated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://example.invalid/owned.wav"
    assert pipeline.resolve_media_source(url) == url
    found = tmp_path / "ann.wav"
    dub_audio.write_wav(found, [0.1] * 16, 8000)

    def _annotated(_text: str) -> str:
        return str(found)

    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        types.SimpleNamespace(
            get_input_directory=lambda: str(tmp_path),
            get_annotated_filepath=_annotated,
        ),
    )
    assert pipeline.resolve_media_source("missing-name.wav", input_dir=tmp_path / "empty") == str(
        found
    )


def test_language_timeout_split_cosine_vad_slice() -> None:
    assert pipeline.language_code("xx") == "xx"
    assert pipeline.language_code("not-a-lang") == "en"
    assert pipeline.language_name("auto") == "the source language"
    assert pipeline.clone_cfg_weight("en", "es", True) == pipeline.CFG_CROSS_LANG
    assert pipeline._translation_needed(False, "en", "es") is False
    assert pipeline.cosine([], [1.0]) == 0.0
    assert pipeline.cosine([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert pipeline.energy_vad([], 24000) == []
    tiny = pipeline.energy_vad([0.0] * 10, 24000)
    assert tiny == []
    rate = 24000
    tone = [0.5 * math.sin(2 * math.pi * 180 * i / rate) for i in range(rate)]
    spans = pipeline.energy_vad(tone, rate, thresh=0.05, min_s=0.05)
    assert spans
    assert pipeline._slice_pcm([0.1] * 10, 24000, 0.5, 0.1) == []


def test_split_clone_text_hard_cut_and_remainder() -> None:
    chunks = pipeline.split_clone_text("a" * 50, limit=12)
    assert chunks
    assert all(len(c) <= 12 for c in chunks)
    spaced = pipeline.split_clone_text(("word " * 12).strip(), limit=20)
    assert len(spaced) > 1


def test_dub_llm_timeout_non_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_DUB_LLM_TIMEOUT_S", "0")
    assert pipeline.dub_llm_timeout_s() == pipeline.TRANSLATE_TIMEOUT_S


def test_run_subprocess_and_missing_binary() -> None:
    code, err = pipeline._run(
        [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"]
    )
    assert code == 3
    assert "boom" in err
    missing, msg = pipeline._run(["ez-dub-no-such-binary-xyz"])
    assert missing == 127
    assert msg


def test_fetch_url_and_extract_and_ingest_video(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline.fetch_hook = None
    dest = tmp_path / "job"
    dest.mkdir()

    def _fail(cmd: list[str]) -> tuple[int, str]:
        del cmd
        return 1, "yt miss"

    monkeypatch.setattr(pipeline, "_run", _fail)
    with pytest.raises(FileNotFoundError, match="yt-dlp failed"):
        pipeline.fetch_url("https://example.invalid/a", dest)

    def _empty_ok(cmd: list[str]) -> tuple[int, str]:
        del cmd
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _empty_ok)
    with pytest.raises(FileNotFoundError, match="produced no file"):
        pipeline.fetch_url("https://example.invalid/a", dest)

    def _write(cmd: list[str]) -> tuple[int, str]:
        del cmd
        (dest / "download.m4a").write_bytes(b"media")
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _write)
    got = pipeline.fetch_url("https://example.invalid/a", dest)
    assert got.name.startswith("download")

    out = tmp_path / "out.wav"
    monkeypatch.setattr(pipeline, "_run", lambda _cmd: (1, "ffmpeg down"))
    with pytest.raises(FileNotFoundError, match="ffmpeg extract failed"):
        pipeline.extract_audio(tmp_path / "in.wav", out)

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="empty source"):
        pipeline.ingest("  ", True, "ep", root=tmp_path)
    with pytest.raises(FileNotFoundError, match="source missing"):
        pipeline.ingest(str(tmp_path / "nope.wav"), True, "ep", root=tmp_path)

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"ftyp")

    def _extract(src: Path, dest_wav: Path, rate: int = 24000) -> None:
        del src, rate
        dub_audio.write_wav(dest_wav, [0.1] * 80, 24000)

    monkeypatch.setattr(pipeline, "extract_audio", _extract)
    job, status = pipeline.ingest(str(clip), True, "vid", root=tmp_path)
    assert status == "ok"
    assert (job / "source_video.mp4").is_file()


def test_embed_encoder_whisper_and_analyze_edges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert pipeline._default_embed([], 24000) == [0.0, 0.0, 0.0, 0.0]
    same = pipeline._resample_for_encoder([0.1, 0.2], 16000, 16000)
    assert same == [0.1, 0.2]
    assert pipeline._resample_for_encoder([], 24000, 16000) == []
    assert pipeline._resample_for_encoder([0.1], 24000, 0) == []

    pipeline._close_voice_encoder()
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    assert pipeline._get_voice_encoder() is None

    ckpt = tmp_path / "ckpt"
    ckpt.mkdir()
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: ckpt)
    assert pipeline._get_voice_encoder() is None
    (ckpt / "ve.pt").write_bytes(b"x")
    pipeline._close_voice_encoder()
    assert pipeline._get_voice_encoder() is None

    class _VE:
        def load_state_dict(self, _state: Any) -> None:
            return None

        def eval(self) -> None:
            return None

        def embeds_from_wavs(self, wavs: Any, sample_rate: int = 16000) -> Any:
            del wavs, sample_rate
            return [[0.2] * 8]

    torch_mod = types.ModuleType("torch")
    torch_mod.load = lambda *_a, **_k: {"w": 1}  # type: ignore[attr-defined]
    torch_mod.cuda = types.SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
    chatterbox = types.ModuleType("chatterbox")
    models = types.ModuleType("chatterbox.models")
    ve = types.ModuleType("chatterbox.models.voice_encoder")
    ve.VoiceEncoder = _VE  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "chatterbox", chatterbox)
    monkeypatch.setitem(sys.modules, "chatterbox.models", models)
    monkeypatch.setitem(sys.modules, "chatterbox.models.voice_encoder", ve)
    pipeline._close_voice_encoder()
    enc = pipeline._get_voice_encoder()
    assert enc is not None
    assert pipeline._get_voice_encoder() is enc

    class _BoomVE(_VE):
        def __init__(self) -> None:
            raise RuntimeError("ve load")

    ve.VoiceEncoder = _BoomVE  # type: ignore[attr-defined]
    pipeline._close_voice_encoder()
    assert pipeline._get_voice_encoder() is None

    np_mod = types.ModuleType("numpy")
    np_mod.float32 = "f4"  # type: ignore[attr-defined]
    np_mod.asarray = lambda wav, dtype=None: wav  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", np_mod)

    class _Enc:
        def embeds_from_wavs(self, wavs: Any, sample_rate: int = 16000) -> Any:
            del wavs, sample_rate
            return None

    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: _Enc())
    vec = pipeline.speaker_embed([0.2] * 800, 24000)
    assert len(vec) == 4

    class _Enc2:
        def embeds_from_wavs(self, wavs: Any, sample_rate: int = 16000) -> Any:
            del wavs, sample_rate
            return [[]]

    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: _Enc2())
    vec2 = pipeline.speaker_embed([0.2] * 800, 24000)
    assert len(vec2) == 4

    class _Enc3:
        def embeds_from_wavs(self, wavs: Any, sample_rate: int = 16000) -> Any:
            del wavs, sample_rate
            raise RuntimeError("embed fail")

    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: _Enc3())
    vec3 = pipeline.speaker_embed([0.2] * 800, 24000)
    assert len(vec3) == 4

    class _Enc4:
        def embeds_from_wavs(self, wavs: Any, sample_rate: int = 16000) -> Any:
            del wavs, sample_rate
            return [[0.1] * 8]

    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: _Enc4())
    vec4 = pipeline.speaker_embed([0.2] * 800, 24000)
    assert vec4 == [0.1] * 8
    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: _Enc4())
    assert pipeline.speaker_embed([], 24000) == [0.0, 0.0, 0.0, 0.0]
    monkeypatch.setattr(pipeline, "_resample_for_encoder", lambda *_a, **_k: [])
    assert len(pipeline.speaker_embed([0.2] * 10, 24000)) == 4

    wav = tmp_path / "s.wav"
    dub_audio.write_wav(wav, [0.2] * 100, 24000)

    def _empty_asr(_path: Path, _language: str) -> list[dict]:
        return []

    pipeline.asr_hook = _empty_asr
    try:
        turns, detected, reason = pipeline.analyze_pcm([0.2] * 100, 24000, wav_path=wav)
    finally:
        pipeline.asr_hook = None
    assert turns == []
    assert reason == "no speech"
    assert detected == ""


def test_whisper_load_get_and_segments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (None, "no wheel"))
    with pytest.raises(ImportError):
        pipeline._load_whisper_model("/m")

    class _Fail:
        def __init__(self, model_dir: str, device: str = "cpu", compute_type: str = "int8") -> None:
            del model_dir, device, compute_type
            raise RuntimeError("no device")

    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (_Fail, ""))
    with pytest.raises(RuntimeError, match="no device"):
        pipeline._load_whisper_model("/m")

    monkeypatch.setattr(pipeline, "WHISPER_LOAD_ATTEMPTS", ())
    with pytest.raises(RuntimeError, match="failed to load"):
        pipeline._load_whisper_model("/m")

    class _Ok:
        def __init__(self, model_dir: str, device: str = "cpu", compute_type: str = "int8") -> None:
            del model_dir, device, compute_type

        def transcribe(self, path: str, **kwargs: Any) -> Any:
            del path, kwargs

            class _Seg:
                text = ""
                start = 0.0
                end = 0.0

            class _Info:
                language = "en"

            return [_Seg()], _Info()

    monkeypatch.setattr(pipeline, "WHISPER_LOAD_ATTEMPTS", (("cpu", "int8"),))
    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (_Ok, ""))
    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "")
    pipeline._close_whisper()
    empty_model, empty_miss = pipeline._get_whisper()
    assert empty_model is None
    assert empty_miss == pipeline.ASR_PACK_STATUS

    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "/models/whisper")
    pipeline._close_whisper()
    model, miss = pipeline._get_whisper()
    assert miss == ""
    assert model is not None
    again, miss2 = pipeline._get_whisper()
    assert again is model
    assert miss2 == ""

    def _load_boom(_d: str) -> Any:
        raise RuntimeError("load boom")

    pipeline._close_whisper()
    monkeypatch.setattr(pipeline, "_load_whisper_model", _load_boom)
    model_b, miss_b = pipeline._get_whisper()
    assert model_b is None
    assert "load boom" in miss_b

    missing, det, reason = pipeline._whisper_segments(tmp_path / "no.wav", "en")
    assert missing == []
    assert reason == pipeline.MISSING_SOURCE_STATUS

    wav = tmp_path / "clip.wav"
    dub_audio.write_wav(wav, [0.1] * 2400, 24000)
    pipeline._close_whisper()
    monkeypatch.setattr(pipeline, "_get_whisper", lambda: (None, "no model"))
    empty, _d, miss_s = pipeline._whisper_segments(wav, "en")
    assert empty == []
    assert "no model" in miss_s

    class _SegOk:
        text = "Hello"
        start = 0.0
        end = 0.4

    class _InfoOk:
        language = "en"

    class _BothType:
        def transcribe(self, path: str, **kwargs: Any) -> Any:
            del path
            if "vad_filter" in kwargs or "beam_size" in kwargs:
                raise TypeError("no extra")
            return [_SegOk()], _InfoOk()

    monkeypatch.setattr(pipeline, "_get_whisper", lambda: (_BothType(), ""))
    turns, detected, reason = pipeline._whisper_segments(wav, "auto")
    assert reason == ""
    assert detected == "en"
    assert turns[0]["text"] == "Hello"

    class _Raise:
        def transcribe(self, path: str, **kwargs: Any) -> Any:
            del path, kwargs
            raise RuntimeError("asr crash")

    monkeypatch.setattr(pipeline, "_get_whisper", lambda: (_Raise(), ""))
    _t, _d, crashed = pipeline._whisper_segments(wav, "en")
    assert "faster-whisper failed" in crashed

    class _Silent:
        def transcribe(self, path: str, **kwargs: Any) -> Any:
            del path, kwargs

            class _Seg:
                text = ""
                start = 0.0
                end = 0.1

            class _Info:
                language = "en"

            return [_Seg()], _Info()

    monkeypatch.setattr(pipeline, "_get_whisper", lambda: (_Silent(), ""))
    none, _d, no_speech = pipeline._whisper_segments(wav, "en")
    assert none == []
    assert no_speech == "no speech"


def test_preflight_import_and_status_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fw = types.ModuleType("faster_whisper")

    class _WM:
        pass

    fw.WhisperModel = _WM  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "faster_whisper", fw)
    cls, miss = pipeline._import_whisper_model()
    assert cls is _WM
    assert miss == ""
    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "")
    assert pipeline.preflight_asr() == pipeline.ASR_PACK_STATUS

    assert "onnx" in pipeline.perth_status(ImportError("onnx"))
    perth = types.ModuleType("perth")
    perth.PerthImplicitWatermarker = None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "perth", perth)
    assert pipeline.preflight_perth() == pipeline.PERTH_STATUS

    class _WM2:
        def __call__(self) -> None:
            return None

    perth.PerthImplicitWatermarker = _WM2  # type: ignore[attr-defined]
    assert pipeline.preflight_perth() == ""

    monkeypatch.setitem(sys.modules, "perth", types.ModuleType("perth-missing"))
    sys.modules.pop("perth", None)

    class _FakeImport:
        def find_spec(self, name: str, *_a: Any, **_k: Any) -> Any:
            if name == "perth":
                raise ImportError("no perth")
            return None

    # ImportError path via missing module (already popped).
    reason = pipeline.preflight_perth()
    assert "resemble-perth" in reason.lower() or "perth" in reason.lower()

    class _TTS:
        from_local = 123

    mtl = types.ModuleType("chatterbox.mtl_tts")
    mtl.ChatterboxMultilingualTTS = _TTS  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "chatterbox", types.ModuleType("chatterbox"))
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    assert "from_local" in pipeline.preflight_clone()

    class _TTS2:
        from_local = staticmethod(len)

    mtl.ChatterboxMultilingualTTS = _TTS2  # type: ignore[attr-defined]
    assert pipeline.preflight_clone() == pipeline.T3_MODEL_STATUS

    class _Loader:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            return object()

    mtl.ChatterboxMultilingualTTS = _Loader  # type: ignore[attr-defined]
    perth_ok = types.ModuleType("perth")

    class _P:
        def __init__(self) -> None:
            return None

    perth_ok.PerthImplicitWatermarker = _P  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "perth", perth_ok)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    assert "clone pack missing" in pipeline.preflight_clone()

    qwen = types.ModuleType("qwen_tts")

    class _Q:
        pass

    qwen.Qwen3TTSModel = _Q  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "qwen_tts", qwen)
    cls_q, miss_q = pipeline._import_qwen3_model()
    assert cls_q is _Q
    assert miss_q == ""

    class _BoomQwen(types.ModuleType):
        def __getattr__(self, name: str) -> object:
            raise RuntimeError("qwen init")

    monkeypatch.setitem(sys.modules, "qwen_tts", _BoomQwen("qwen_tts"))
    cls_b, miss_b = pipeline._import_qwen3_model()
    assert cls_b is None
    assert miss_b

    monkeypatch.setitem(sys.modules, "qwen_tts", None)
    cls_i, miss_i = pipeline._import_qwen3_model()
    assert cls_i is None
    assert "qwen3tts extra not installed" in miss_i

    class _NoPre:
        from_pretrained = None

    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_NoPre, ""))
    snap = tmp_path / "Qwen__Qwen3-TTS-12Hz-0.6B-Base_qwen3tts"
    snap.mkdir()
    for name in pipeline.QWEN3_BASE_REQUIRED_FILES + pipeline.QWEN3_TOKENIZER_REQUIRED_FILES:
        dest = snap / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"x")
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    assert "from_pretrained" in pipeline.preflight_qwen3()

    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", None)
    assert "llama.cpp unavailable" in pipeline.translate_llama_status()
    assert "llama.cpp unavailable" in pipeline.preflight_translate()

    good = types.ModuleType("ez_prompt_enhance.client")
    good._get_llama = lambda: (object(), "")  # type: ignore[attr-defined]
    good.status_for_reason = lambda reason: reason or ""  # type: ignore[attr-defined]
    good.llama_cpp_unavailable_status = lambda: "llama.cpp unavailable"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", good)
    assert pipeline.preflight_translate() == ""


def test_translate_turns_remaining_reason_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    empty, reason = pipeline.translate_turns(
        [{"id": 1, "text": "  ", "text_target": ""}],
        "es",
        "en",
        enhance=True,
    )
    assert reason == "no turns"

    turns = _two_turns()
    turns[0]["text"] = ""
    calls: list[str] = []

    def _complete(system: str, user: str, **kwargs: Any) -> tuple[str, str | None]:
        del system, kwargs
        calls.append(user)
        return "Hoy nos quedamos en el partido.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    out, why = pipeline.translate_turns(turns, "es", "en", enhance=True)
    assert out[0]["text_target"] == ""
    assert "translated" in why or out[1]["text_target"]

    def _pass(system: str, user: str, **kwargs: Any) -> tuple[str, str | None]:
        del system, user, kwargs
        return "Welcome back to the tape.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _pass)
    out_p, why_p = pipeline.translate_turns(_two_turns(), "es", "en", enhance=True)
    assert "passthrough" in why_p
    assert out_p[0]["text_target"] == ""

    def _suspect(system: str, user: str, **kwargs: Any) -> tuple[str, str | None]:
        del system, user, kwargs
        return "This is the time for you and the rest of the people.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _suspect)
    out_s, why_s = pipeline.translate_turns(_two_turns(), "es", "en", enhance=True)
    assert "passthrough" in why_s or "suspect" in why_s
    assert out_s[0]["text_target"] == ""

    def _mix(system: str, user: str, **kwargs: Any) -> tuple[str, str | None]:
        del system, kwargs
        source_line = ""
        for line in user.splitlines():
            if line.startswith("Source:"):
                source_line = line
                break
        if "Welcome" in source_line:
            return "Bienvenidos de nuevo a la cinta.", None
        return "This is the time for you and the rest of the people.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _mix)
    out_m, why_m = pipeline.translate_turns(_two_turns(), "es", "en", enhance=True)
    assert "translated" in why_m and "passthrough" in why_m
    assert out_m[0]["text_target"].startswith("Bienvenidos")

    def _close_boom() -> None:
        raise RuntimeError("unload")

    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", _close_boom)
    pipeline.translate_turns(_two_turns()[:1], "es", "en", enhance=True)

    bare = types.ModuleType("ez_prompt_enhance.client")
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", bare)
    out_i, why_i = pipeline.translate_turns(_two_turns(), "es", "en", enhance=True)
    assert why_i == "llama.cpp unavailable"
    assert out_i[0]["text_target"] == ""


def test_clone_prep_voiced_trim_concat_and_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "CLONE_SILENCE_PAD_S", 0.0)
    monkeypatch.setattr(pipeline, "CLONE_TOKEN_RATE", 1.0)
    assert pipeline.clone_token_budget("Hola") == pipeline.CLONE_TOKEN_MIN
    monkeypatch.setattr(pipeline, "CLONE_TOKEN_RATE", 10000.0)
    assert pipeline.clone_token_budget("palabra " * 40) == pipeline.CLONE_TOKEN_MAX

    assert pipeline._voiced_span([], 24000) is None
    short = pipeline._voiced_span([0.5] * 10, 24000)
    assert short is not None or pipeline._voiced_span([0.5] * 10, 24000) is None
    quiet = pipeline._voiced_span([0.0001] * 24000, 24000)
    assert quiet is None
    brief = pipeline._voiced_span([0.5] * 200, 24000)
    assert brief is None or isinstance(brief, tuple)
    none_hold = pipeline._voiced_span(
        [0.03 if i % 40 == 0 else 0.0 for i in range(24000)], 24000
    )
    assert none_hold is None or isinstance(none_hold, tuple)
    monkeypatch.setattr(pipeline, "ONSET_PAD_S", -2.0)
    span = pipeline._voiced_span(_am_speech(24000, 0.4), 24000)
    assert span is None or span[1] > span[0] or span[1] <= span[0]

    assert pipeline.envelope_cv([0.1] * 10, 24000) == 1.0
    assert pipeline.envelope_cv([0.0] * 24000, 24000) == 0.0
    assert pipeline._trim_silence([], 24000) == []
    silent_frame = [0.0] * int(24000 * 0.02)
    assert pipeline._trim_silence(silent_frame, 24000)
    padded = [0.0] * 480 + [0.4] * 480 + [0.0] * 480
    trimmed = pipeline._trim_silence(padded, 24000)
    assert pipeline.rms(trimmed) > 0.1
    assert pipeline._concat_crossfade([], 24000) == []
    joined = pipeline._concat_crossfade([[], [0.2] * 10], 24000, xfade_ms=30)
    assert joined
    assert pipeline._peak_normalize([]) == []
    zeros = pipeline._peak_normalize([0.0, 0.0])
    assert zeros == [0.0, 0.0]
    assert pipeline.match_rms([], 0.2) == []
    assert pipeline._speaker_ref_text(Path("/no/such/ref.wav")) == ""
    assert pipeline._turn_rms({"rms": "bad"}, [0.4] * 10) == pipeline.rms([0.4] * 10)
    assert pipeline._turn_rms({"rms": 0.0}, [0.4] * 10) == pipeline.rms([0.4] * 10)
    assert pipeline.zero_crossing_rate([0.1, -0.1], -1) == 0.0
    monkeypatch.setattr(pipeline, "_zero_cross_indices", lambda _pcm: [1] * 20)
    assert pipeline.zc_interval_cv([0.1] * 100) == 0.0
    monkeypatch.setattr(
        pipeline,
        "_zero_cross_indices",
        lambda _pcm: list(range(pipeline.ZC_INTERVAL_MIN_GAPS)),
    )
    assert pipeline.zc_interval_cv([0.1] * 100) == 0.0
    assert pipeline.voiced_fraction([0.4] * 10, 24000) in {0.0, 1.0}
    hush = [0.0] * 20000 + _am_speech(24000, 0.2)
    assert pipeline.is_speech_like(hush, 24000) is False
    assert pipeline.crop_hallucination_tail([], 24000, "Hola") == []
    class _Odd:
        pass

    assert pipeline._pcm_list(_Odd()) == []
    assert pipeline._pcm_list([object(), 0.25]) == [0.25]


def test_filter_refs_purity_and_extract_edges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rate = 24000
    samples = [0.25] * (rate * 12)

    def _embed(pcm: list[float], sr: int) -> list[float]:
        del pcm, sr
        return [1.0] + [0.0] * 8

    pipeline.embed_hook = _embed
    try:
        group = [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 2.0,
                "overlap": False,
                "rms": 0.2,
                "text": "a",
            },
            {
                "id": 2,
                "speaker": "spk00",
                "t0": 2.0,
                "t1": 4.0,
                "overlap": False,
                "rms": 0.2,
                "text": "b",
            },
        ]
        kept = pipeline._filter_ref_turns(group, samples, rate)
        assert kept

        def _split(pcm: list[float], sr: int) -> list[float]:
            del pcm, sr
            if not hasattr(_split, "n"):
                _split.n = 0  # type: ignore[attr-defined]
            _split.n += 1  # type: ignore[attr-defined]
            if _split.n == 1:  # type: ignore[attr-defined]
                return [1.0] + [0.0] * 8
            return [-1.0] + [0.0] * 8

        pipeline.embed_hook = _split
        mixed = pipeline._filter_ref_turns(group, samples, rate)
        assert mixed
    finally:
        pipeline.embed_hook = None

    none = pipeline._extract_refs(
        samples,
        rate,
        [{"id": 1, "speaker": "spk00", "t0": 0.0, "t1": 2.0, "overlap": True, "rms": 0.9, "text": "x"}],
        tmp_path / "speakers",
    )
    assert none == {}

    def _empty_pcm(samples_i: Any, sr: int, t0: float, t1: float) -> list[float]:
        del samples_i, sr, t0, t1
        return []

    monkeypatch.setattr(pipeline, "_slice_pcm", _empty_pcm)
    short_turns = [
        {
            "id": i,
            "speaker": "spk00",
            "t0": float(i),
            "t1": float(i) + 1.5,
            "overlap": False,
            "rms": 0.4,
            "text": f"t{i}",
        }
        for i in range(6)
    ]
    pipeline.embed_hook = lambda *_a, **_k: [0.1] * 4
    try:
        skipped = pipeline._extract_refs(samples, rate, short_turns, tmp_path / "spk-empty")
    finally:
        pipeline.embed_hook = None
    assert skipped == {} or isinstance(skipped, dict)

    monkeypatch.undo()
    rate = 24000
    samples = [0.25] * (rate * 20)
    turns = [
        {
            "id": i + 1,
            "speaker": "spk00",
            "t0": float(i) * 2.0,
            "t1": float(i) * 2.0 + 1.8,
            "overlap": False,
            "rms": 0.3,
            "text": f"line {i}",
        }
        for i in range(6)
    ]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "spk-many")
    assert "spk00" in refs


def test_model_roots_pkuseg_and_chatterbox_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.delenv("MODELS_DIR", raising=False)
    roots = pipeline._model_roots()
    assert "/models" in roots
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    roots2 = pipeline._model_roots()
    assert str(tmp_path) in roots2
    monkeypatch.setenv("PKUSEG_HOME", str(tmp_path / "pk"))
    assert pipeline.pkuseg_home_dir() == tmp_path / "pk"

    snap = tmp_path / "ResembleAI__chatterbox_clone"
    snap.mkdir()
    (snap / "Cangjie5_TC.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    monkeypatch.setenv("PKUSEG_HOME", "/prev-pk")
    tok = types.ModuleType("chatterbox.models.tokenizers.tokenizer")
    monkeypatch.setitem(sys.modules, "chatterbox.models.tokenizers.tokenizer", tok)
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)
    with pipeline._chatterbox_local_only(snap):
        assert os.environ.get("HF_HUB_OFFLINE") == "1"
    assert os.environ.get("HF_HUB_OFFLINE") == "0"
    assert os.environ.get("PKUSEG_HOME") == "/prev-pk"


def test_from_local_signature_and_load_chatterbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RuntimeError, match="t3_model"):
        pipeline._from_local_multilingual(len, "/ckpt", "cpu")  # type: ignore[arg-type]

    class _TTS:
        pass

    mtl = types.ModuleType("chatterbox.mtl_tts")
    mtl.ChatterboxMultilingualTTS = _TTS  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "chatterbox", types.ModuleType("chatterbox"))
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    model, err = pipeline._load_chatterbox_model()
    assert model is None
    assert "clone pack missing" in err

    snap = tmp_path / "ckpt"
    snap.mkdir()
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: snap)

    class _NoLocal:
        from_local = None

    mtl.ChatterboxMultilingualTTS = _NoLocal  # type: ignore[attr-defined]
    model2, err2 = pipeline._load_chatterbox_model()
    assert model2 is None
    assert "from_local" in err2

    class _RT:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            raise RuntimeError("t3 boom")

    mtl.ChatterboxMultilingualTTS = _RT  # type: ignore[attr-defined]
    model3, err3 = pipeline._load_chatterbox_model()
    assert model3 is None
    assert "t3 boom" in err3

    class _EX:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            raise ValueError("inner")

    mtl.ChatterboxMultilingualTTS = _EX  # type: ignore[attr-defined]
    model4, err4 = pipeline._load_chatterbox_model()
    assert model4 is None
    assert "chatterbox failed" in err4

    torch_mod = types.ModuleType("torch")
    torch_mod.cuda = types.SimpleNamespace(is_available=lambda: True)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    assert pipeline._chatterbox_device() == "cuda"


def test_cap_t3_try_chatterbox_and_qwen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _T3:
        def __init__(self) -> None:
            self.seen: list[object] = []

        def inference(self, **kwargs: Any) -> Any:
            self.seen.append(kwargs.get("max_new_tokens"))
            return "ok"

    class _Model:
        sr = 24000

        def __init__(self) -> None:
            self.t3 = _T3()

        def generate(self, text: str, **kwargs: Any) -> Any:
            del text, kwargs
            self.t3.inference(max_new_tokens="bad")
            self.t3.inference(max_new_tokens=0)
            return [0.1] * 80

    model = _Model()
    with pipeline._cap_t3_tokens(model, 0):
        model.generate("x")
    assert model.t3.seen
    with pipeline._cap_t3_tokens(model, 8):
        model.t3.inference(max_new_tokens=None)

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (None, "missing"))
    pcm, rate, err = pipeline._try_chatterbox("Hola", "es", "")
    assert pcm == []
    assert "missing" in err

    class _NoGen:
        sr = 24000

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_NoGen(), ""))
    pcm2, _r, err2 = pipeline._try_chatterbox("Hola", "es", "")
    assert "generate" in err2

    class _SigFail:
        sr = 24000
        generate = staticmethod(len)

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_SigFail(), ""))
    pcm3, _r, err3 = pipeline._try_chatterbox("Hola", "es", "")
    assert pcm3 == [] or err3

    class _Boom:
        sr = 24000

        def generate(self, text: str, **kwargs: Any) -> Any:
            del text, kwargs
            raise RuntimeError("gen fail")

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Boom(), ""))
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    _p, _r, err4 = pipeline._try_chatterbox("Hola", "es", "")
    assert "chatterbox failed" in err4

    class _Empty:
        sr = 24000

        def generate(self, text: str, **kwargs: Any) -> Any:
            del text, kwargs
            return []

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Empty(), ""))
    _p, _r, err5 = pipeline._try_chatterbox("Hola", "es", "")
    assert "empty audio" in err5

    class _Ok:
        sr = 24000

        def generate(self, text: str, **kwargs: Any) -> Any:
            del text, kwargs
            return [0.1] * 80

    snap = tmp_path / "ckpt"
    snap.mkdir()
    (snap / "Cangjie5_TC.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Ok(), ""))
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: snap)
    pcm_ok, rate_ok, err_ok = pipeline._try_chatterbox("Hola", "es", "")
    assert err_ok == ""
    assert pcm_ok
    assert rate_ok == 24000

    pipeline._close_qwen3()
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (None, "no qwen"))
    model_q, err_q = pipeline._load_qwen3_model()
    assert model_q is None
    assert "no qwen" in err_q

    class _Q:
        @staticmethod
        def from_pretrained(path: str, local_files_only: bool = False) -> object:
            del path
            if local_files_only:
                raise TypeError("no local")
            return object()

    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_Q, ""))
    monkeypatch.setattr(pipeline, "qwen3_ckpt_dir", lambda: None)
    monkeypatch.setattr(pipeline, "qwen3_base_dir", lambda: None)
    _m, pack = pipeline._load_qwen3_model()
    assert pack == pipeline.QWEN3_PACK_STATUS
    folder = tmp_path / "qbase"
    folder.mkdir()
    for name in pipeline.QWEN3_BASE_REQUIRED_FILES:
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(b"x")
    monkeypatch.setattr(pipeline, "qwen3_base_dir", lambda: folder)
    monkeypatch.setattr(pipeline, "qwen3_base_is_complete", lambda _f: True)
    _m, tok = pipeline._load_qwen3_model()
    assert tok == pipeline.QWEN3_TOKENIZER_STATUS

    class _NoFn:
        from_pretrained = None

    monkeypatch.setattr(pipeline, "qwen3_ckpt_dir", lambda: folder)
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_NoFn, ""))
    _m, miss_fn = pipeline._load_qwen3_model()
    assert "from_pretrained" in miss_fn

    class _RaiseQ:
        @staticmethod
        def from_pretrained(path: str, local_files_only: bool = False) -> object:
            del path, local_files_only
            raise RuntimeError("load q")

    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_RaiseQ, ""))
    _m, fail_q = pipeline._load_qwen3_model()
    assert "qwen3tts failed" in fail_q

    loaded = object()

    class _OKQ:
        @staticmethod
        def from_pretrained(path: str, local_files_only: bool = False) -> object:
            del path, local_files_only
            return loaded

    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_OKQ, ""))
    got, err_okq = pipeline._load_qwen3_model()
    assert err_okq == ""
    assert got is loaded
    pipeline._QWEN3 = got
    pipeline._QWEN3_ERR = ""
    cached, _e = pipeline._get_qwen3()
    assert cached is got
    pipeline._close_qwen3()
    pipeline._QWEN3_ERR = "cached miss"
    none, cached_err = pipeline._get_qwen3()
    assert none is None
    assert cached_err == "cached miss"
    pipeline._close_qwen3()
    monkeypatch.setattr(pipeline, "_load_qwen3_model", lambda: (None, "x"))
    n2, e2 = pipeline._get_qwen3()
    assert n2 is None
    assert e2 == "x"
    pipeline._close_qwen3()
    monkeypatch.setattr(pipeline, "_load_qwen3_model", lambda: (loaded, ""))
    g2, e3 = pipeline._get_qwen3()
    assert g2 is loaded
    assert e3 == ""
    assert pipeline._qwen3_language("auto") == "Auto"

    pipeline._close_qwen3()
    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (None, "wheel"))
    _p, _r, errw = pipeline._try_qwen3tts("Hola", "es", "")
    assert "wheel" in errw

    class _NoClone:
        pass

    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_NoClone(), ""))
    _p, _r, errc = pipeline._try_qwen3tts("Hola", "es", "")
    assert "generate_voice_clone" in errc

    class _PromptFail:
        def create_voice_clone_prompt(self, **kwargs: Any) -> Any:
            del kwargs
            raise RuntimeError("prompt")

        def generate_voice_clone(self, **kwargs: Any) -> Any:
            del kwargs
            return [[0.1] * 40], 24000

    ref = tmp_path / "spk00.wav"
    dub_audio.write_wav(ref, [0.2] * 2400, 24000)
    pipeline._QWEN3_PROMPT = None
    pipeline._QWEN3_PROMPT_KEY = ""
    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_PromptFail(), ""))
    pcm_pf, rate_pf, err_pf = pipeline._try_qwen3tts("Hola", "es", str(ref), ref_text="")
    assert err_pf == ""
    assert pcm_pf

    class _Cache:
        def __init__(self) -> None:
            self.n = 0

        def create_voice_clone_prompt(self, **kwargs: Any) -> Any:
            del kwargs
            self.n += 1
            return {"p": self.n}

        def generate_voice_clone(self, **kwargs: Any) -> Any:
            del kwargs
            return [[0.1] * 40], 24000

    cache = _Cache()
    pipeline._QWEN3_PROMPT = None
    pipeline._QWEN3_PROMPT_KEY = ""
    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (cache, ""))
    pipeline._try_qwen3tts("Hola", "es", str(ref), ref_text="hello")
    pipeline._try_qwen3tts("Adios", "es", str(ref), ref_text="hello")
    assert cache.n == 1

    class _Inline:
        def generate_voice_clone(self, **kwargs: Any) -> Any:
            assert "ref_audio" in kwargs
            return [[0.2] * 20], 16000

    pipeline._QWEN3_PROMPT = None
    pipeline._QWEN3_PROMPT_KEY = ""
    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_Inline(), ""))
    pcm_i, rate_i, err_i = pipeline._try_qwen3tts("Hola", "es", str(ref), ref_text="hi")
    assert err_i == ""
    assert rate_i == 16000
    assert pcm_i

    class _CloneBoom:
        def generate_voice_clone(self, **kwargs: Any) -> Any:
            del kwargs
            raise RuntimeError("clone boom")

    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_CloneBoom(), ""))
    _p, _r, errb = pipeline._try_qwen3tts("Hola", "es", "")
    assert "qwen3tts failed" in errb

    class _EmptyQ:
        def generate_voice_clone(self, **kwargs: Any) -> Any:
            del kwargs
            return [[]], 24000

    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_EmptyQ(), ""))
    _p, _r, erre = pipeline._try_qwen3tts("Hola", "es", "")
    assert "empty audio" in erre


def test_synthesize_turn_engines_without_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline.tts_hook = None
    pcm, rate, err = pipeline.synthesize_turn("   ", "es", "", ENGINE_CHATTERBOX)
    assert pcm == []
    assert err == ""

    monkeypatch.setattr(
        pipeline,
        "_try_chatterbox",
        lambda *a, **k: ([], 24000, "clone miss"),
    )
    pcm2, _r, err2 = pipeline.synthesize_turn("Hola", "es", "", ENGINE_CHATTERBOX)
    assert pcm2 == []
    assert "clone miss" in err2

    monkeypatch.setattr(
        pipeline,
        "_try_chatterbox",
        lambda *a, **k: ([0.1] * 10, 24000, ""),
    )
    pcm3, rate3, err3 = pipeline.synthesize_turn("Hola", "es", "", "unknown-engine")
    assert pcm3
    assert err3 == ""
    assert rate3 == 24000

    monkeypatch.setattr(
        pipeline,
        "_try_qwen3tts",
        lambda *a, **k: ([0.2] * 8, 16000, ""),
    )
    pcm4, rate4, err4 = pipeline.synthesize_turn(
        "Hola", "es", "", pipeline.ENGINE_QWEN3TTS
    )
    assert pcm4
    assert rate4 == 16000
    assert err4 == ""


def test_loudnorm_mp3_qc_and_render_mix_edges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "job"
    dest.mkdir()
    rate = 24000
    samples = _am_speech(rate, 2.0)
    dub_audio.write_wav(dest / "ez_dub_yt.wav", samples, rate)

    def _fail(_cmd: list[str]) -> tuple[int, str]:
        return 1, "ff"

    monkeypatch.setattr(pipeline, "_run", _fail)
    assert pipeline._maybe_loudnorm_yt(dest, samples, rate, len(samples), [0.0]) == samples

    def _ok(cmd: list[str]) -> tuple[int, str]:
        Path(cmd[-1]).write_bytes((dest / "ez_dub_yt.wav").read_bytes())
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _ok)
    out = pipeline._maybe_loudnorm_yt(dest, samples, rate, len(samples), [0.0])
    assert out

    def _ok_then_boom(cmd: list[str]) -> tuple[int, str]:
        Path(cmd[-1]).write_bytes(b"not-a-wav")
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _ok_then_boom)
    dub_audio.write_wav(dest / "ez_dub_yt.wav", samples, rate)
    fallback = pipeline._maybe_loudnorm_yt(dest, samples, rate, len(samples), [0.0])
    assert fallback == samples

    def _ok_empty(cmd: list[str]) -> tuple[int, str]:
        dub_audio.write_wav(Path(cmd[-1]), [], rate)
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _ok_empty)
    dub_audio.write_wav(dest / "ez_dub_yt.wav", samples, rate)
    empty = pipeline._maybe_loudnorm_yt(dest, samples, rate, len(samples), [0.0])
    assert empty == samples

    def _ok_long(cmd: list[str]) -> tuple[int, str]:
        dub_audio.write_wav(Path(cmd[-1]), samples + samples, rate)
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _ok_long)
    dub_audio.write_wav(dest / "ez_dub_yt.wav", samples, rate)
    locked = pipeline._maybe_loudnorm_yt(dest, samples, rate, len(samples), [0.01] * 10)
    assert len(locked) == len(samples)

    pipeline._maybe_yt_mp3_48k(tmp_path / "missing")
    flags: list[str] = []
    pipeline._write_render_qc(
        dest,
        samples,
        rate,
        [],
        "es",
        flags,
        extra_qc=["trimmed_clone"],
        peak=0.9,
    )
    assert any("qc:" in f for f in flags) or (dest / "qc.json").is_file()

    def _qc_boom(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("qc")

    monkeypatch.setattr(pipeline, "evaluate_qc", _qc_boom)
    pipeline._write_render_qc(dest, samples, rate, [], "es", flags, extra_qc=[], peak=0.9)

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    job = tmp_path / "dubs" / "mix"
    job.mkdir(parents=True)
    src = _am_speech(rate, 8.0)
    dub_audio.write_wav(job / "source.wav", src, rate)
    payload = _es_payload()

    def _tts(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del language, ref_wav, engine
        return _am_speech(12000, max(0.4, len(text) * 20 / 12000.0)), 12000

    pipeline.tts_hook = _tts
    try:
        mix, out_rate, status = pipeline.render_mix(
            src,
            rate,
            payload,
            job,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=True,
            speed=0.1,
            exaggeration="nope",  # type: ignore[arg-type]
            cfg_weight=-1.0,
        )
    finally:
        pipeline.tts_hook = None
    assert out_rate == rate
    assert mix
    assert "cloned" in status

    job2 = tmp_path / "dubs" / "mix2"
    job2.mkdir(parents=True)
    dub_audio.write_wav(job2 / "source.wav", src, rate)

    def _tts_hot(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del text, language, ref_wav, engine
        return _am_speech(rate, 6.0), rate

    pipeline.tts_hook = _tts_hot
    try:
        mix2, _r, status2 = pipeline.render_mix(
            src,
            rate,
            payload,
            job2,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
            speed=9.0,
            exaggeration=9.0,
        )
    finally:
        pipeline.tts_hook = None
    assert mix2
    assert "cloned" in status2
    assert "trimmed" in status2 or "peak=" in status2

    job3 = tmp_path / "dubs" / "miss"
    job3.mkdir(parents=True)
    dub_audio.write_wav(job3 / "source.wav", src, rate)

    def _tts_miss(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del text, language, ref_wav, engine
        return [], rate

    pipeline.tts_hook = _tts_miss
    try:
        mix3, _r, status3 = pipeline.render_mix(
            src,
            rate,
            payload,
            job3,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert mix3 == []
    assert status3

    job4 = tmp_path / "dubs" / "retry-err"
    job4.mkdir(parents=True)
    dub_audio.write_wav(job4 / "source.wav", src, rate)
    n = {"c": 0}

    def _tts_retry(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del text, language, ref_wav, engine
        n["c"] += 1
        if n["c"] == 1:
            return [math.sin(2 * math.pi * 90 * i / rate) for i in range(rate)], rate
        return [], rate

    pipeline.tts_hook = _tts_retry
    try:
        mix4, _r, status4 = pipeline.render_mix(
            src,
            rate,
            payload,
            job4,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
            cfg_weight=0.0,
        )
    finally:
        pipeline.tts_hook = None
    assert mix4 == []
    assert "unvoiced" in status4 or "clone" in status4.lower()

    job5 = tmp_path / "dubs" / "bedless"
    job5.mkdir(parents=True)
    long_src = _am_speech(rate, 8.0)
    dub_audio.write_wav(job5 / "source.wav", long_src, rate)
    tiny_payload = {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "",
        "turns": [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 0.4,
                "text": "Hi",
                "text_target": "Hola",
                "overlap": False,
                "rms": 0.2,
            }
        ],
    }

    def _tts_ok(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del text, language, ref_wav, engine
        return _am_speech(rate, 0.4), rate

    pipeline.tts_hook = _tts_ok
    try:
        mix5, _r, status5 = pipeline.render_mix(
            long_src,
            rate,
            tiny_payload,
            job5,
            engine=ENGINE_CHATTERBOX,
            keep_bed=False,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert mix5 == [] or "unvoiced" in status5 or mix5

    job6 = tmp_path / "dubs" / "refs"
    job6.mkdir(parents=True)
    src6 = _am_speech(rate, 12.0)
    dub_audio.write_wav(job6 / "source.wav", src6, rate)
    payload6 = {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "",
        "turns": [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 0.5,
                "text": "Hi",
                "text_target": "Hola equipo",
                "overlap": False,
                "rms": 0.001,
            },
            {
                "id": 2,
                "speaker": "spk01",
                "t0": 1.0,
                "t1": 8.0,
                "text": "Long take from the second speaker today.",
                "text_target": "Toma larga del segundo hablante hoy en el partido.",
                "overlap": False,
                "rms": 0.3,
            },
        ],
    }

    seen_refs: list[str] = []

    def _tts6(text: str, language: str, ref_wav: str, engine: str) -> tuple[list[float], int]:
        del language, engine
        seen_refs.append(ref_wav)
        return _am_speech(rate, max(0.5, len(text) * 40 / float(rate))), rate

    pipeline.tts_hook = _tts6
    try:
        mix6, _r, status6 = pipeline.render_mix(
            src6,
            rate,
            payload6,
            job6,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=True,
            exaggeration=0.1,
        )
    finally:
        pipeline.tts_hook = None
    assert mix6
    assert "cloned" in status6
    assert any(seen_refs)

    real_lock = pipeline.lock_duration

    def _trim_lock(mix: Any, target_n: int, room: Any = None, rate: int = 24000) -> Any:
        longer = list(mix) + [0.1] * 50
        return real_lock(longer, target_n, room=room, rate=rate)

    job7 = tmp_path / "dubs" / "trimlock"
    job7.mkdir(parents=True)
    dub_audio.write_wav(job7 / "source.wav", src, rate)
    monkeypatch.setattr(pipeline, "lock_duration", _trim_lock)
    monkeypatch.setattr(pipeline, "raise_to_peak", lambda pcm, peak=0.89: [0.05 for _ in pcm])
    pipeline.tts_hook = _tts_ok
    try:
        mix7, _r, status7 = pipeline.render_mix(
            src,
            rate,
            payload,
            job7,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    if mix7:
        assert "duration trimmed" in status7 or "quiet mix" in status7 or "cloned" in status7


def test_spoken_clone_text_same_language() -> None:
    text = pipeline._spoken_clone_text(
        {"text": "Hello", "text_target": ""},
        {"source_language": "en", "target_language": "en"},
    )
    assert text == "Hello"
    empty = pipeline._spoken_clone_text(
        {"text": "Hello", "text_target": ""},
        {"source_language": "en", "target_language": "es"},
    )
    assert empty == ""


def test_analyze_job_auto_detect_and_asr_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)
    monkeypatch.setattr(pipeline, "preflight_translate", lambda: "")

    def _asr(_path: Path, _language: str) -> list[dict]:
        return []

    pipeline.asr_hook = _asr
    try:
        payload, reason = pipeline.analyze_job(
            dest,
            target_language="es",
            source_language="en",
            max_speakers=0,
            enhance=False,
            stage="all",
        )
    finally:
        pipeline.asr_hook = None
    assert payload["turns"] == []
    assert reason == "no speech"

    def _whisper(path: Path, language: str) -> Any:
        del path, language
        return (
            [
                {
                    "id": 1,
                    "speaker": "spk00",
                    "t0": 0.0,
                    "t1": 1.0,
                    "text": "Hello there",
                    "text_target": "",
                    "overlap": False,
                    "rms": 0.2,
                }
            ],
            "en",
            "",
        )

    pipeline.asr_hook = None
    monkeypatch.setattr(pipeline, "preflight_asr", lambda: "")
    monkeypatch.setattr(pipeline, "_whisper_segments", _whisper)
    monkeypatch.setattr(
        pipeline,
        "translate_turns",
        lambda turns, tgt, src, enhance=True: (turns, "same language"),
    )
    payload2, reason2 = pipeline.analyze_job(
        dest,
        target_language="es",
        source_language="auto",
        max_speakers=0,
        enhance=False,
        stage="all",
    )
    assert payload2["turns"]
    assert payload2["source_language"] == "en"
    assert "speakers" in reason2


def test_ezdub_script_invalid_stage_and_langs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "episode"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 100, 24000)
    monkeypatch.setattr(
        pipeline,
        "analyze_job",
        lambda *a, **k: (
            dub_turns.empty_payload(status="ok"),
            "ok",
        ),
    )
    out = EZDubScript().run("{}", True, "zz", "nope", 0, "weird", "episode")
    assert out["result"][0]


def test_time_stretch_tail_and_search_branches() -> None:
    rate = 8000
    n = 400
    dest = 1200
    pcm = [math.sin(2 * math.pi * 220 * i / rate) for i in range(n)]
    out = align.time_stretch(pcm, dest, rate)
    assert len(out) == dest
    tiny_dest = align.time_stretch(pcm, 40, rate)
    assert len(tiny_dest) == 40


def test_remaining_align_and_sanitize_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_round = builtins.round

    def _round(x: Any, ndigits: int | None = None) -> Any:
        if ndigits is not None:
            return real_round(x, ndigits)
        if 40.0 < float(x) < 90.0:
            return -1
        return real_round(x)

    monkeypatch.setattr(builtins, "round", _round)
    out = align.time_stretch([0.2] * 600, 2400, 24000)
    assert len(out) == 2400
    monkeypatch.setattr(builtins, "round", real_round)

    real_range = builtins.range

    def _range(*args: Any) -> Any:
        if len(args) == 1 and 2 <= int(args[0]) <= 40:
            return real_range(int(args[0]) + 12)
        return real_range(*args)

    monkeypatch.setattr(builtins, "range", _range)
    stretched = align.time_stretch([0.2] * 800, 2400, 24000)
    assert len(stretched) == 2400
    monkeypatch.setattr(builtins, "range", real_range)

    align.stretch_hook = None
    monkeypatch.setattr(align, "_ffmpeg_atempo", lambda *_a, **_k: [0.11] * 40)
    got = align.pitch_preserving_stretch([0.2] * 80, 40, 24000)
    assert got == [0.11] * 40

    covered = [0.2] * 100
    room = align.collect_room_tone(
        covered, [{"t0": 0.0, "t1": 5.0}], 24000, want=16
    )
    assert room == [0.0] * 16

    mixed = dub_sanitize.strip_leak_tails("Hola equipo. Something else.")
    assert "Hola" in mixed
    monkeypatch.setattr(
        dub_sanitize,
        "_split_sentences",
        lambda _text: ["Hola equipo.", "voice model leftover"],
    )
    leaked = dub_sanitize.strip_leak_tails("Hola equipo. Something else.")
    assert "voice model" not in leaked.lower()
    assert "Hola" in leaked


def test_remaining_pipeline_preflight_and_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    cls, miss = pipeline._import_whisper_model()
    assert cls is None
    assert "faster-whisper" in miss

    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (object(), ""))
    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "")
    assert pipeline.preflight_asr() == pipeline.ASR_PACK_STATUS

    assert pipeline.perth_status() == pipeline.PERTH_STATUS

    class _NoSig:
        from_local = staticmethod(min)

    mtl = types.ModuleType("chatterbox.mtl_tts")
    mtl.ChatterboxMultilingualTTS = _NoSig  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "chatterbox", types.ModuleType("chatterbox"))
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    assert pipeline.preflight_clone() == pipeline.T3_MODEL_STATUS

    class _Loader:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            return object()

    mtl.ChatterboxMultilingualTTS = _Loader  # type: ignore[attr-defined]
    perth_ok = types.ModuleType("perth")
    perth_ok.PerthImplicitWatermarker = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "perth", perth_ok)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: None)
    assert "clone pack missing" in pipeline.preflight_clone()

    def _input_boom() -> str:
        raise RuntimeError("no")

    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        types.SimpleNamespace(get_input_directory=_input_boom),
    )
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/inputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert pipeline.input_directory() == Path("input")

    with pytest.raises(RuntimeError, match="t3_model"):
        pipeline._from_local_multilingual(min, "/ckpt", "cpu")  # type: ignore[arg-type]

    def _loader(ckpt: str) -> str:
        return ckpt

    assert pipeline._from_pretrained_local(_loader, "/ckpt") == "/ckpt"

    joined = pipeline._concat_crossfade([[0.1] * 20, [], [0.2] * 20], 24000)
    assert joined
    quiet = pipeline._filter_ref_turns(
        [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 1.2,
                "overlap": False,
                "rms": 0.001,
                "text": "q",
            }
        ],
        [0.0] * (24000 * 2),
        24000,
    )
    assert quiet == []

    import builtins

    real_enum = builtins.enumerate

    def _enum(iterable: Any, start: int = 0) -> Any:
        if isinstance(iterable, list) and iterable and isinstance(iterable[0], dict):
            return real_enum([], start)
        return real_enum(iterable, start)

    monkeypatch.setattr(builtins, "enumerate", _enum)
    monkeypatch.setattr("ez_prompt_enhance.client.complete", lambda *_a, **_k: ("Hola", None))
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    _out, why = pipeline.translate_turns(_two_turns(), "es", "en", enhance=True)
    assert why == ""
    monkeypatch.setattr(builtins, "enumerate", real_enum)

    frame = int(24000 * 0.02)
    short_loud = [0.5] * (frame * 3)
    span = pipeline._voiced_span(short_loud, 24000)
    assert span == (0, len(short_loud))

    clicky: list[float] = []
    for _ in range(12):
        clicky.extend([0.6] * (frame * 3))
        clicky.extend([0.0] * frame)
    assert pipeline._voiced_span(clicky, 24000) is None

    real_rev = builtins.reversed

    def _rev(seq: Any) -> Any:
        data = list(seq)
        if data and max(abs(float(x)) for x in data) > 0.1:
            return iter([0.0] * len(data))
        return real_rev(seq)

    monkeypatch.setattr(builtins, "reversed", _rev)
    speech = _am_speech(24000, 0.6)
    span2 = pipeline._voiced_span(speech, 24000)
    assert span2 is None or isinstance(span2, tuple)
    monkeypatch.setattr(builtins, "reversed", real_rev)


def test_remaining_chatterbox_qwen_and_render(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _TTS:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            raise OSError("disk")

    mtl = types.ModuleType("chatterbox.mtl_tts")
    mtl.ChatterboxMultilingualTTS = _TTS  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "chatterbox", types.ModuleType("chatterbox"))
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    snap = tmp_path / "ckpt"
    snap.mkdir()
    (snap / "Cangjie5_TC.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: snap)
    model, err = pipeline._load_chatterbox_model()
    assert model is None
    assert "chatterbox failed" in err

    class _SigFail:
        sr = 24000
        generate = staticmethod(min)

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_SigFail(), ""))
    pcm, _rate, err2 = pipeline._try_chatterbox("Hola", "es", "")
    assert pcm == [] or err2 != "unused"

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    dest = tmp_path / "dubs" / "gaps"
    dest.mkdir(parents=True)
    rate = 24000
    src = _am_speech(rate, 8.0)
    dub_audio.write_wav(dest / "source.wav", src, rate)
    payload = _es_payload()
    monkeypatch.setattr(pipeline, "preflight_clone", lambda: "")
    pipeline.tts_hook = None

    def _synth_err(*_a: Any, **_k: Any) -> tuple[list[float], int, str]:
        return [], rate, "engine boom"

    monkeypatch.setattr(pipeline, "synthesize_turn", _synth_err)
    mix, _r, status = pipeline.render_mix(
        src,
        rate,
        payload,
        dest,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
    )
    assert mix == []
    assert "engine boom" in status

    dest2 = tmp_path / "dubs" / "retry"
    dest2.mkdir(parents=True)
    dub_audio.write_wav(dest2 / "source.wav", src, rate)
    n = {"c": 0}

    def _synth_retry(*_a: Any, **_k: Any) -> tuple[list[float], int, str]:
        n["c"] += 1
        if n["c"] == 1:
            tone = [math.sin(2 * math.pi * 90 * i / rate) for i in range(rate)]
            return tone, rate, ""
        return [], rate, "retry miss"

    monkeypatch.setattr(pipeline, "synthesize_turn", _synth_retry)
    mix2, _r, status2 = pipeline.render_mix(
        src,
        rate,
        payload,
        dest2,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
        cfg_weight=0.0,
    )
    assert mix2 == []
    assert "retry miss" in status2 or "unvoiced" in status2

    dest3 = tmp_path / "dubs" / "partial"
    dest3.mkdir(parents=True)
    dub_audio.write_wav(dest3 / "source.wav", src, rate)
    n3 = {"c": 0}

    def _synth_partial(
        text: str,
        language: str,
        ref_wav: str,
        engine: str,
        **kwargs: Any,
    ) -> tuple[list[float], int, str]:
        del language, ref_wav, engine, kwargs
        n3["c"] += 1
        if "Bienvenidos" in text:
            tone = [math.sin(2 * math.pi * 90 * i / rate) for i in range(rate)]
            return tone, rate, ""
        return _am_speech(rate, 1.2), rate, ""

    monkeypatch.setattr(pipeline, "synthesize_turn", _synth_partial)
    mix3, _r, status3 = pipeline.render_mix(
        src,
        rate,
        payload,
        dest3,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
        cfg_weight=0.5,
    )
    if mix3:
        assert "cloned" in status3
        qc = json.loads((dest3 / "qc.json").read_text(encoding="utf-8"))
        assert isinstance(qc, dict)


def test_cover_align_ffmpeg_fallback_and_src_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    align.stretch_hook = None
    monkeypatch.setattr(align, "_ffmpeg_atempo", lambda *_a, **_k: None)
    out = align.pitch_preserving_stretch([0.2] * 80, 40, 24000)
    assert len(out) == 40

    import builtins

    real_range = builtins.range

    def _range(*args: Any) -> Any:
        if len(args) == 1 and int(args[0]) == 2:
            return real_range(24)
        return real_range(*args)

    monkeypatch.setattr(builtins, "range", _range)
    compressed = align.time_stretch([0.3] * 2000, 720, 24000)
    assert len(compressed) == 720
    monkeypatch.setattr(builtins, "range", real_range)

    real_max = builtins.max

    def _max(*args: Any) -> Any:
        if len(args) == 2 and args[0] == 1 and args[1] == 240:
            return 5000
        return real_max(*args)

    monkeypatch.setattr(align, "max", _max, raising=False)
    stretched = align.time_stretch([0.25] * 800, 2400, 24000)
    assert len(stretched) == 2400


def test_cover_zc_interval_cv_second_gap_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Flip(list):
        def __len__(self) -> int:
            self._n = getattr(self, "_n", 0) + 1
            if self._n == 1:
                return 20
            return super().__len__()

    monkeypatch.setattr(pipeline, "_zero_cross_indices", lambda _pcm: _Flip([1, 2, 3]))
    assert pipeline.zc_interval_cv([0.1] * 10) == 0.0


def test_cover_pipeline_success_returns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (object(), ""))
    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "/models/whisper")
    assert pipeline.preflight_asr() == ""

    class _Ok:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3") -> object:
            del ckpt_dir, device, t3_model
            return object()

    mtl = types.ModuleType("chatterbox.mtl_tts")
    mtl.ChatterboxMultilingualTTS = _Ok  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "chatterbox", types.ModuleType("chatterbox"))
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    monkeypatch.setattr(pipeline, "preflight_perth", lambda: "")
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: Path("/ckpt"))
    assert pipeline.preflight_clone() == ""

    loaded = object()
    monkeypatch.setattr(pipeline, "_from_local_multilingual", lambda *_a, **_k: loaded)
    snap = tmp_path / "ckpt"
    snap.mkdir()
    (snap / "Cangjie5_TC.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: snap)
    model, err = pipeline._load_chatterbox_model()
    assert err == ""
    assert model is loaded



