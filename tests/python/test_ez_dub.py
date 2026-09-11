"""Hermetic tests for ez_dub (no Comfy, no network, no Whisper, no TTS)."""

from __future__ import annotations

import math
import os
import shutil
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_dub  # noqa: E402
from ez_dub import align  # noqa: E402
from ez_dub import audio as dub_audio  # noqa: E402
from ez_dub import jobstore  # noqa: E402
from ez_dub import pipeline  # noqa: E402
from ez_dub import srt as dub_srt  # noqa: E402
from ez_dub import turns as dub_turns  # noqa: E402
from ez_dub.nodes import (  # noqa: E402
    DISCLOSURE_TEXT,
    ENGINE_CHATTERBOX,
    EZDubIngest,
    EZDubRender,
    EZDubScript,
    NODE_CLASS_MAPPINGS,
    SEED_SCRIPT,
)
from ez_dub.rights import RightsError, as_bool, require_rights  # noqa: E402

EXAMPLE_TURNS = [
    {
        "id": 1,
        "speaker": "spk00",
        "t0": 0.4,
        "t1": 2.8,
        "text": "Welcome back to the tape.",
        "text_target": "Bienvenidos de nuevo a la cinta.",
        "overlap": False,
        "rms": 0.1,
    },
    {
        "id": 2,
        "speaker": "spk01",
        "t0": 3.0,
        "t1": 6.2,
        "text": "Today we stay on the match in front of us.",
        "text_target": "Hoy nos quedamos en el partido que tenemos delante.",
        "overlap": False,
        "rms": 0.1,
    },
]
EXAMPLE_SCRIPT = dub_turns.dumps_payload(
    {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "",
        "turns": EXAMPLE_TURNS,
    }
)


def _passthrough_ffmpeg(monkeypatch) -> None:
    """Copy ffmpeg -i SRC to DEST so ingest tests do not need a real ffmpeg."""

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
        if dest.endswith(".mp3") or dest.endswith(".loudnorm.wav"):
            shutil.copy(src, dest)
            return 0, ""
        shutil.copy(src, dest)
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _run)


def test_pack_imports_without_whisper() -> None:
    assert ez_dub.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {"EZDubIngest", "EZDubScript", "EZDubRender"}
    for cls in NODE_CLASS_MAPPINGS.values():
        assert cls.CATEGORY == "ez-comfy/dub"
    enhance = EZDubScript.INPUT_TYPES()["required"]["enhance"][1]
    assert enhance["default"] is True
    assert enhance["label_on"] == "On"
    assert enhance["label_off"] == "Off"
    assert ez_dub.WEB_DIRECTORY == "./js"
    js = CUSTOM / "ez_dub" / "js" / "ez_dub_ingest.js"
    body = js.read_text(encoding="utf-8")
    assert "EZDubIngest" in body
    assert "/upload/image" in body
    assert "Upload media" in body
    assert "audio/*" in body
    assert "video/*" in body
    status_js = CUSTOM / "ez_dub" / "js" / "ez_dub_status.js"
    status_body = status_js.read_text(encoding="utf-8")
    assert "EZDubScript" in status_body
    assert "EZDubRender" in status_body
    assert "Dub status" in status_body
    assert "Turns JSON" in status_body
    enhance_js = (CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js").read_text(
        encoding="utf-8"
    )
    assert "EZDubScript" not in enhance_js
    parsed_seed = dub_turns.parse_payload(SEED_SCRIPT)
    assert parsed_seed["turns"] == []


def test_ingest_source_is_input_combo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    spec = EZDubIngest.INPUT_TYPES()["required"]
    source = spec["source"]
    assert isinstance(source[0], list)
    assert source[0][0] == pipeline.SOURCE_NONE
    assert "source_url" in spec
    assert spec["source_url"][0] == "STRING"
    assert spec["source_url"][1]["default"] == ""
    inp = tmp_path / "input"
    inp.mkdir()
    (inp / "keep-me.wav").write_bytes(b"RIFF")
    (inp / "notes.txt").write_text("skip", encoding="utf-8")
    (inp / "clip.mp4").write_bytes(b"ftyp")
    names = pipeline.list_input_media()
    assert names == ["clip.mp4", "keep-me.wav"]
    options = pipeline.source_combo_options()
    assert options[0] == pipeline.SOURCE_NONE
    assert options[1:] == names


def test_disclosure_string_exact() -> None:
    assert DISCLOSURE_TEXT == (
        "This audio is an AI-translated dub. Voices are synthesized from the "
        "original speakers with the rights-holder's authorization."
    )
    assert "original characters" not in DISCLOSURE_TEXT.lower()


def test_disclosure_localized_es_exact() -> None:
    from ez_dub.disclosure import DISCLOSURE_LOCALIZED, disclosure_for

    es = DISCLOSURE_LOCALIZED["es"]
    assert es == (
        "Este audio es un doblaje traducido por IA. "
        "Las voces están sintetizadas a partir de los hablantes originales "
        "con la autorización del titular de los derechos."
    )
    assert DISCLOSURE_TEXT == (
        "This audio is an AI-translated dub. Voices are synthesized from the "
        "original speakers with the rights-holder's authorization."
    )
    assert pipeline.DISCLOSURE_TEXT == DISCLOSURE_TEXT
    assert disclosure_for("es") == es
    assert disclosure_for("ES") == es
    assert disclosure_for("xx") == DISCLOSURE_TEXT
    assert "original characters" not in DISCLOSURE_TEXT.lower()
    assert "original characters" not in es.lower()


def test_apply_spoken_disclosure_does_not_change_length() -> None:
    from ez_dub.disclosure import apply_spoken_disclosure

    rate = 24000
    mix = [0.05] * (rate * 8)
    turns = [{"t0": 0.4, "t1": 2.0, "speaker": "spk00"}]

    def _synth(text: str, language: str, ref_wav: str, engine: str):
        del text, language, ref_wav, engine
        return [0.2] * (rate * 6), rate, ""

    out, status = apply_spoken_disclosure(
        mix,
        rate,
        language="es",
        engine=ENGINE_CHATTERBOX,
        ref_wav="",
        turns=turns,
        synthesize=_synth,
    )
    assert len(out) == len(mix)
    assert status == "spoken disclosure"


def test_apply_spoken_disclosure_uses_target_language_and_ref() -> None:
    from ez_dub.disclosure import apply_spoken_disclosure

    rate = 24000
    mix = [0.05] * (rate * 4)
    seen: list[tuple[str, str]] = []

    def _synth(text: str, language: str, ref_wav: str, engine: str):
        del text, engine
        seen.append((language, ref_wav))
        return [0.2] * (rate // 2), rate, ""

    apply_spoken_disclosure(
        mix,
        rate,
        language="es",
        engine=ENGINE_CHATTERBOX,
        ref_wav="/tmp/spk00.wav",
        turns=[{"t0": 2.0, "t1": 3.0, "speaker": "spk00"}],
        synthesize=_synth,
    )
    assert seen
    assert seen[0][0] == "es"
    assert seen[0][1] == "/tmp/spk00.wav"


def test_apply_spoken_disclosure_does_not_call_fit_turn_three_seconds(
    monkeypatch,
) -> None:
    from ez_dub import disclosure as dub_disclosure

    windows: list[float] = []
    real_fit = dub_disclosure.fit_turn

    def _fit(pcm, rate, window, spill_s=0.0):
        windows.append(float(window))
        return real_fit(pcm, rate, window, spill_s=spill_s)

    monkeypatch.setattr(dub_disclosure, "fit_turn", _fit)
    rate = 24000
    mix = [0.05] * (rate * 8)

    def _synth(text: str, language: str, ref_wav: str, engine: str):
        del text, language, ref_wav, engine
        return [0.2] * (rate * 6), rate, ""

    dub_disclosure.apply_spoken_disclosure(
        mix,
        rate,
        language="es",
        engine=ENGINE_CHATTERBOX,
        ref_wav="",
        turns=[{"t0": 0.4, "t1": 2.0, "speaker": "spk00"}],
        synthesize=_synth,
    )
    assert 3.0 not in windows
    assert all(w != 3.0 for w in windows)
    if windows:
        assert 4.0 in windows


def test_rights_refuse() -> None:
    assert as_bool(False) is False
    assert as_bool("yes") is True
    require_rights(True)
    try:
        require_rights(False)
        raise AssertionError("expected RightsError")
    except RightsError as exc:
        assert "I have rights" in str(exc)


def test_ingest_rights_false_does_not_write(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    wav = tmp_path / "in.wav"
    dub_audio.write_wav(wav, [0.1, -0.1] * 100, 24000)
    out = EZDubIngest().run(str(wav), False, "episode")
    assert out["result"][0] == "episode"
    assert out["ui"]["passthrough"][0] == "rights refused"
    dest = tmp_path / "dubs" / "episode"
    assert not (dest / "source.wav").is_file()
    state = jobstore.load_state(dest)
    assert state["status"] == "rights refused"


def test_resolve_media_source_basename_url_and_none(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    inp = tmp_path / "input"
    inp.mkdir()
    wav = inp / "show.wav"
    dub_audio.write_wav(wav, [0.1] * 100, 24000)
    assert pipeline.resolve_media_source("show.wav") == str(wav)
    assert pipeline.resolve_media_source("show.wav [input]") == str(wav)
    abs_wav = tmp_path / "elsewhere.wav"
    dub_audio.write_wav(abs_wav, [0.2] * 100, 24000)
    assert pipeline.resolve_media_source(str(abs_wav)) == str(abs_wav)
    url = "https://example.invalid/owned.wav"
    assert pipeline.resolve_media_source(pipeline.SOURCE_NONE, url) == url
    assert pipeline.resolve_media_source("show.wav", url) == url
    try:
        pipeline.resolve_media_source(pipeline.SOURCE_NONE)
        raise AssertionError("expected empty source")
    except FileNotFoundError as exc:
        assert "empty source" in str(exc)
    try:
        pipeline.resolve_media_source("missing.wav")
        raise AssertionError("expected missing source")
    except FileNotFoundError as exc:
        assert "source missing" in str(exc)


def test_ingest_none_source_fail_soft(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    out = EZDubIngest().run(pipeline.SOURCE_NONE, True, "episode")
    assert "empty source" in out["ui"]["passthrough"][0]
    dest = tmp_path / "dubs" / "episode"
    assert not (dest / "source.wav").is_file()
    assert "empty source" in jobstore.load_state(dest)["status"]


def test_ingest_wav_and_script_pin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    tone = [0.4 * math.sin(2 * math.pi * 220 * i / 24000) for i in range(24000)]
    wav = tmp_path / "in.wav"
    dub_audio.write_wav(wav, [0.0] * 8000 + tone + [0.0] * 8000, 24000)
    ingested = EZDubIngest().run(str(wav), True, "match-day")
    assert ingested["result"][0] == "match-day"
    dest = tmp_path / "dubs" / "match-day"
    assert (dest / "source.wav").is_file()
    pinned = EZDubScript().run(
        EXAMPLE_SCRIPT,
        False,
        "es",
        "en",
        0,
        "render",
        "match-day",
    )
    text = pinned["result"][0]
    assert "Bienvenidos" in text
    assert pinned["ui"]["passthrough"][0] == "pinned widget"


def test_analyze_energy_vad_and_cluster() -> None:
    rate = 24000
    silence = [0.0] * rate
    tone = [0.5 * math.sin(2 * math.pi * 180 * i / rate) for i in range(rate)]
    samples = silence + tone + silence
    spans = pipeline.energy_vad(samples, rate, thresh=0.05, min_s=0.2)
    assert spans
    assert spans[0][0] >= 0.8
    assert spans[0][1] <= 2.3
    labels = pipeline.cluster_embeddings(
        [[1.0, 0.0], [0.99, 0.01], [0.0, 1.0]],
        max_speakers=2,
        threshold=0.7,
    )
    assert labels[0] == labels[1]
    assert labels[2] != labels[0]


def test_overlap_keeps_louder() -> None:
    turns = [
        dub_turns.normalize_turn(
            {"id": 1, "speaker": "spk00", "t0": 0.0, "t1": 2.0, "rms": 0.1},
            1,
        ),
        dub_turns.normalize_turn(
            {"id": 2, "speaker": "spk01", "t0": 1.0, "t1": 3.0, "rms": 0.4},
            2,
        ),
    ]
    kept = dub_turns.assign_overlap(turns)
    assert len(kept) == 1
    assert kept[0]["speaker"] == "spk01"
    assert kept[0]["overlap"] is True


def test_merge_adjacent_same_speaker_within_gap() -> None:
    turns = [
        dub_turns.normalize_turn(
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 1.0,
                "text": "Hello there.",
                "rms": 0.1,
                "overlap": False,
            },
            1,
        ),
        dub_turns.normalize_turn(
            {
                "id": 2,
                "speaker": "spk00",
                "t0": 1.2,
                "t1": 2.0,
                "text": "We keep going.",
                "rms": 0.4,
                "overlap": True,
            },
            2,
        ),
    ]
    merged = dub_turns.merge_adjacent_turns(turns)
    assert len(merged) == 1
    assert merged[0]["speaker"] == "spk00"
    assert merged[0]["t0"] == 0.0
    assert merged[0]["t1"] == 2.0
    assert merged[0]["text"] == "Hello there. We keep going."
    assert merged[0]["rms"] == 0.4
    assert merged[0]["overlap"] is True


def test_merge_adjacent_does_not_merge_other_speaker() -> None:
    turns = [
        dub_turns.normalize_turn(
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 1.0,
                "text": "Hello.",
            },
            1,
        ),
        dub_turns.normalize_turn(
            {
                "id": 2,
                "speaker": "spk01",
                "t0": 1.1,
                "t1": 2.0,
                "text": "Hi.",
            },
            2,
        ),
    ]
    merged = dub_turns.merge_adjacent_turns(turns)
    assert len(merged) == 2
    assert merged[0]["speaker"] == "spk00"
    assert merged[1]["speaker"] == "spk01"


def test_fit_turn_pad_spill_trim() -> None:
    rate = 24000
    short, flags = align.fit_turn([0.2] * 100, rate, 0.02)
    assert flags["padded"] is True
    assert len(short) == int(round(0.02 * rate))
    window = 0.05
    long_pcm = [0.2] * int(0.2 * rate)
    fitted, meta = align.fit_turn(long_pcm, rate, window, spill_s=0.0)
    assert len(fitted) == int(round(window * rate))
    assert meta["trimmed"] is True or meta["speed"] > 1.0
    spilled, spill_flags = align.fit_turn(long_pcm, rate, window, spill_s=0.2)
    assert spill_flags["spill"] is True
    assert len(spilled) > len(fitted)


def test_raise_to_peak_amplifies_quiet_pcm() -> None:
    quiet = [0.1, -0.2, 0.05]
    out = pipeline.raise_to_peak(quiet, peak=0.89)
    mag = max(abs(x) for x in out)
    assert abs(mag - 0.89) < 1e-6
    assert pipeline.raise_to_peak([0.0, 0.0]) == [0.0, 0.0]
    assert pipeline.raise_to_peak([]) == []


def test_peak_normalize_still_does_not_raise_refs() -> None:
    quiet = [0.1, -0.1, 0.05]
    out = pipeline._peak_normalize(quiet, peak=0.89)
    assert out == [0.1, -0.1, 0.05]
    hot = [0.5, -0.99, 0.2]
    limited = pipeline._peak_normalize(hot, peak=0.89)
    assert abs(max(abs(x) for x in limited) - 0.89) < 1e-6


def test_match_rms_scales_clone_toward_source() -> None:
    clone = [0.05] * 200
    target = align.rms([0.4] * 200)
    out = pipeline.match_rms(clone, target)
    assert align.rms(out) > align.rms(clone)
    assert max(abs(x) for x in out) <= pipeline.REF_PEAK + 1e-6
    assert pipeline.match_rms(clone, 0.0) == clone


def test_lock_duration_and_timeline() -> None:
    source = [0.1] * 1000
    clone = {"t0": 0.0, "pcm": [0.9] * 100}
    mix = align.build_timeline(source, [clone], 1000, keep_bed=True, xfade_ms=10)
    assert len(mix) == 1000
    assert mix[50] != 0.1
    locked, flags = align.lock_duration(mix[:800], 1000, room=[0.01], rate=1000)
    assert len(locked) == 1000
    assert flags["padded"] is True
    trimmed, tflags = align.lock_duration(mix + [0.2] * 50, 1000, rate=1000)
    assert len(trimmed) == 1000
    assert tflags["trimmed"] is True


def test_srt_and_payload_parse() -> None:
    body = dub_srt.turns_to_srt(
        [{"t0": 0.0, "t1": 1.5, "text": "Hello", "text_target": "Hola"}],
        field="text_target",
    )
    assert "00:00:00,000 --> 00:00:01,500" in body
    assert "Hola" in body
    parsed = dub_turns.parse_payload(EXAMPLE_SCRIPT)
    assert parsed["target_language"] == "es"
    assert len(parsed["turns"]) == 2
    bad = dub_turns.parse_payload("{not json")
    assert bad["status"] == "invalid json"
    empty = dub_turns.parse_payload("")
    assert empty["turns"] == []


def test_jobstore_roundtrip(tmp_path: Path) -> None:
    dest = jobstore.dub_dir("My Episode!", root=tmp_path)
    assert dest.name == "My-Episode"
    state = jobstore.new_state(dest.name)
    jobstore.save_state(dest, state)
    loaded = jobstore.load_state(dest)
    assert loaded["slug"] == "My-Episode"
    assert jobstore.sanitize_slug("***") == "episode"


def test_pcm_list_flattens_nested() -> None:
    assert pipeline._pcm_list(None) == []
    assert pipeline._pcm_list(0.5) == [0.5]
    assert pipeline._pcm_list([[0.1, 0.2], [0.3]]) == [0.1, 0.2, 0.3]


def test_is_url_and_language_name() -> None:
    assert pipeline.is_url("https://youtube.com/watch?v=abc")
    assert not pipeline.is_url("/tmp/file.wav")
    assert pipeline.language_name("es") == "Spanish"
    assert pipeline.language_name("Spanish") == "Spanish"
    assert pipeline.language_code("es") == "es"
    assert pipeline.language_code("Spanish") == "es"
    assert pipeline.language_code("auto") == "auto"
    assert pipeline.language_code("") == "auto"


def test_render_uses_tts_hook(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        n = max(100, len(text) * 40)
        return [0.3] * n, rate

    pipeline.tts_hook = _tts
    try:
        mix, out_rate, status = pipeline.render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert out_rate == rate
    assert len(mix) == len(samples)
    assert (dest / "ez_dub_yt.wav").is_file()
    assert (dest / "ez_dub.disclosure.en.txt").read_text(encoding="utf-8").startswith(
        DISCLOSURE_TEXT
    )
    assert (dest / "ez_dub.disclosure.txt").is_file()
    assert (dest / "qc.json").is_file()
    assert (dest / "ez_dub.es.srt").is_file()
    assert "speakers" in status
    assert "cloned" in status


def test_render_mix_yt_wav_equals_source_length(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        n = max(100, len(text) * 40)
        return [0.3] * n, rate

    pipeline.tts_hook = _tts
    try:
        mix, out_rate, status = pipeline.render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=True,
        )
    finally:
        pipeline.tts_hook = None
    assert out_rate == rate
    assert len(mix) == len(samples)
    yt, yt_rate = dub_audio.read_wav(dest / "ez_dub_yt.wav")
    mixed, mix_rate = dub_audio.read_wav(dest / "ez_dub_mix.wav")
    assert yt_rate == rate
    assert mix_rate == rate
    assert len(yt) == len(samples)
    assert len(mixed) == len(samples)
    assert "spoken disclosure" in status or "disclosure skipped" in status


def test_render_mix_optional_48k_mp3_argv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    seen: list[list[str]] = []

    def _run(cmd: list[str]) -> tuple[int, str]:
        seen.append(list(cmd))
        return 1, "fail"

    monkeypatch.setattr(pipeline, "_run", _run)
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        n = max(100, len(text) * 40)
        return [0.3] * n, rate

    pipeline.tts_hook = _tts
    try:
        mix, out_rate, status = pipeline.render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert out_rate == rate
    assert mix
    assert (dest / "ez_dub_yt.wav").is_file()
    mp3_cmds = [c for c in seen if c and str(c[-1]).endswith("ez_dub_yt_48k.mp3")]
    assert mp3_cmds
    argv = mp3_cmds[0]
    assert "-ar" in argv and "48000" in argv
    assert "-b:a" in argv and "320k" in argv
    assert not (dest / "ez_dub_yt_48k.mp3").is_file()
    assert "cloned" in status


def test_mix_loudness_raises_quiet_render(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        n = max(100, len(text) * 40)
        return [0.05] * n, rate

    pipeline.tts_hook = _tts
    try:
        mix, out_rate, status = pipeline.render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert out_rate == rate
    assert mix
    peak = max(abs(x) for x in mix)
    assert peak >= 0.8
    assert "peak=" in status


def test_render_analyze_stage_skips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)
    payload["stage"] = "analyze"
    out = EZDubRender().run(
        dub_turns.dumps_payload(payload),
        ENGINE_CHATTERBOX,
        True,
        False,
        1.0,
        job_id="ep",
    )
    assert out["ui"]["passthrough"][0].startswith("analyze only")


def test_fetch_hook_ingest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    wav = tmp_path / "remote.wav"
    dub_audio.write_wav(wav, [0.2] * 4800, 24000)

    def _fetch(url, dest_dir: Path) -> Path:
        del url
        copied = dest_dir / "download.wav"
        copied.write_bytes(wav.read_bytes())
        return copied

    pipeline.fetch_hook = _fetch
    try:
        dest, status = pipeline.ingest(
            "https://example.invalid/video", True, "url-job", root=tmp_path
        )
        via_url = EZDubIngest().run(
            pipeline.SOURCE_NONE,
            True,
            "url-job-2",
            "https://example.invalid/video",
        )
    finally:
        pipeline.fetch_hook = None
    assert status == "ok"
    assert (dest / "source.wav").is_file()
    assert via_url["result"][0] == "url-job-2"
    assert (tmp_path / "dubs" / "url-job-2" / "source.wav").is_file()


def test_sanitize_strips_think_and_translation_prefix() -> None:
    from ez_dub.sanitize import sanitize_target, strip_model_fences

    fenced = (
        "<think>internal</think>Translation: \"Las calles estaban alineadas.\""
    )
    stripped = strip_model_fences(fenced)
    assert "<think>" not in stripped
    assert not stripped.lower().startswith("translation")
    assert stripped.startswith("Las calles")
    cleaned = sanitize_target(
        "Traducción: 'Bienvenidos de nuevo a la cinta.'",
        source_text="Welcome back to the tape.",
        language="es",
    )
    assert cleaned == "Bienvenidos de nuevo a la cinta."


def test_sanitize_drops_voice_model_tail() -> None:
    from ez_dub.sanitize import strip_leak_tails

    raw = (
        "La ciudad estaba llena de oportunidades y me agradecido por formar "
        "parte de ello experiencia de una manera que te ayude a desarrollar "
        "mi modelo de voz."
    )
    cleaned = strip_leak_tails(raw)
    assert "modelo de voz" not in cleaned.lower()
    assert "te ayude a desarrollar" not in cleaned.lower()
    assert "La ciudad estaba llena de oportunidades" in cleaned


def test_looks_like_target_rejects_english_on_es() -> None:
    from ez_dub.sanitize import looks_like_target

    assert looks_like_target("", "es") is False
    assert (
        looks_like_target(
            "This is the time for you and the rest of the people.",
            "es",
        )
        is False
    )
    assert looks_like_target(
        "El ritmo de la vida diaria lo marcaba el sonido constante del tren "
        "que pasaba por nuestra estación cada mañana y cada tarde.",
        "es",
    )
    gold = (
        "La ciudad estaba llena de oportunidades, y estaba agradecido de "
        "formar parte de esa experiencia."
    )
    assert looks_like_target(gold, "es") is True


def test_qc_flags_leak_and_empty_target() -> None:
    from ez_dub.qc import evaluate_qc

    mix = [0.5] * 24000
    turns = [
        {
            "t0": 0.0,
            "t1": 1.0,
            "text": "Hello there everyone.",
            "text_target": "",
        },
        {
            "t0": 2.0,
            "t1": 3.0,
            "text": "Hi.",
            "text_target": (
                "Hola de una manera que te ayude a desarrollar mi modelo de voz."
            ),
        },
    ]
    report = evaluate_qc(
        mix, 24000, turns, target_language="es", peak=0.89
    )
    ids = {str(item.get("id")) for item in report.get("checks") or []}
    assert "empty_target" in ids
    assert "leak" in ids
    flags = report.get("flags") or []
    assert "empty_target" in flags
    assert "leak" in flags


def test_qc_flags_gap_passthrough_quiet_and_english() -> None:
    from ez_dub.qc import evaluate_qc

    mix = [0.05] * 24000
    turns = [
        {
            "t0": 0.0,
            "t1": 0.5,
            "text": "This is the time for you and the rest.",
            "text_target": "This is the time for you and the rest.",
        },
        {
            "t0": 2.0,
            "t1": 2.5,
            "text": "More English here for the people.",
            "text_target": "More English here for the people.",
        },
    ]
    report = evaluate_qc(
        mix, 24000, turns, target_language="es", peak=0.89
    )
    flags = set(report.get("flags") or [])
    assert "gap" in flags
    assert "passthrough" in flags
    assert "quiet_mix" in flags
    assert "english_left" in flags


def test_qc_never_raises_on_garbage() -> None:
    from ez_dub.qc import evaluate_qc

    report = evaluate_qc([], 0, [None], target_language="es", peak=0.89)  # type: ignore[list-item]
    assert isinstance(report, dict)


def test_banned_strings_absent_from_pack() -> None:
    blob = ""
    for path in (CUSTOM / "ez_dub").rglob("*"):
        if path.suffix.lower() in {".py", ".txt", ".md"}:
            blob += path.read_text(encoding="utf-8")
    for needle in (
        "ElevenLabs",
        "F5-TTS",
        "XTTS",
        "Wav2Lip",
        "Rogan",
        "Ramsay",
        "TTS-Audio-Suite",
        "MiniMax",
        "NLLB",
        "SeamlessM4T",
    ):
        assert needle not in blob, needle


def _two_en_turns() -> list[dict]:
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


def test_translate_turns_per_turn_fills_spanish(monkeypatch) -> None:
    calls: list[tuple[str, int | None, float | None, int | None]] = []

    def _complete(
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout_s: int | None = None,
    ):
        del system
        calls.append((user, max_tokens, temperature, timeout_s))
        source_line = ""
        for line in user.splitlines():
            if line.startswith("Source:"):
                source_line = line
                break
        if "Welcome" in source_line:
            return "Bienvenidos de nuevo a la cinta.", None
        return "Hoy nos quedamos en el partido.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    out, reason = pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=True)
    assert "translated 2/2" in reason
    assert out[0]["text_target"] == "Bienvenidos de nuevo a la cinta."
    assert out[1]["text_target"] == "Hoy nos quedamos en el partido."
    assert len(calls) == 2
    assert "Spanish" in calls[0][0]
    assert "(es)" in calls[0][0]
    assert "Welcome back to the tape." in calls[0][0]
    assert "/no_think" in calls[0][0]
    assert "/no_think" in pipeline.load_translate_prompt()
    assert '"turns"' not in calls[0][0]
    assert calls[0][1] == pipeline.TRANSLATE_MAX_TOKENS
    assert calls[0][2] == pipeline.TRANSLATE_TEMPERATURE
    assert calls[0][3] == pipeline.TRANSLATE_TIMEOUT_S
    assert pipeline.TRANSLATE_MAX_TOKENS == 512


def test_translate_turns_llama_unavailable_leaves_targets_empty(
    monkeypatch,
) -> None:
    calls = {"n": 0}

    def _complete(system: str, user: str, *, max_tokens: int | None = None, **kwargs):
        del system, user, max_tokens, kwargs
        calls["n"] += 1
        return "", "llama.cpp unavailable"

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    out, reason = pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=True)
    assert reason == "llama.cpp unavailable"
    assert out[0]["text_target"] == ""
    assert out[1]["text_target"] == ""
    assert calls["n"] == 1


def test_translate_turns_gguf_load_failed_leaves_targets_empty(
    monkeypatch,
) -> None:
    def _complete(system: str, user: str, *, max_tokens: int | None = None, **kwargs):
        del system, user, max_tokens, kwargs
        return "", "GGUF failed to load"

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    out, reason = pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=True)
    assert reason == "GGUF failed to load"
    assert out[0]["text_target"] == ""
    assert out[1]["text_target"] == ""


def test_translate_turns_empty_model_is_passthrough_not_success(monkeypatch) -> None:
    def _complete(system: str, user: str, *, max_tokens: int | None = None, **kwargs):
        del system, user, max_tokens, kwargs
        return "", "timeout or empty model output"

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    out, reason = pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=True)
    assert reason
    assert "passthrough" in reason or "timeout" in reason
    assert out[0]["text_target"] == "Welcome back to the tape."
    assert out[1]["text_target"] == "Today we stay on the match."


def test_translate_turns_same_language_skips_llm(monkeypatch) -> None:
    def _complete(system: str, user: str, *, max_tokens: int | None = None, **kwargs):
        del system, user, max_tokens, kwargs
        raise AssertionError("LLM should not run when source == target")

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    out, reason = pipeline.translate_turns(_two_en_turns(), "en", "en", enhance=True)
    assert reason == "same language"
    assert out[0]["text_target"] == "Welcome back to the tape."


def test_translate_turns_enhance_off_copies() -> None:
    out, reason = pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=False)
    assert reason == "enhance off"
    assert out[0]["text_target"] == "Welcome back to the tape."


def test_translate_turns_passes_previous_turn_context(monkeypatch) -> None:
    calls: list[str] = []

    def _complete(
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout_s: int | None = None,
    ):
        del system, max_tokens, temperature, timeout_s
        calls.append(user)
        source_line = ""
        for line in user.splitlines():
            if line.startswith("Source:"):
                source_line = line
                break
        if "Welcome" in source_line:
            return "Bienvenidos de nuevo a la cinta.", None
        return "Hoy nos quedamos en el partido.", None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    pipeline.translate_turns(_two_en_turns(), "es", "en", enhance=True)
    assert len(calls) == 2
    assert "Welcome back to the tape." in calls[0]
    assert "Context (previous turn" not in calls[0]
    assert "Welcome back to the tape." in calls[1]
    assert "Context (previous turn" in calls[1]
    assert "Bienvenidos de nuevo a la cinta." in calls[1]


GOLD_ES = (
    "El ritmo de la vida diaria lo marcaba el sonido constante del tren que "
    "pasaba por nuestra estación cada mañana y cada tarde.",
    "Las calles estaban alineadas con casas de ladrillo antiguo, las fachadas "
    "erosionadas por el tiempo, y la panadería del barrio era siempre la "
    "primera parada de quienes iban a trabajar.",
    "Por las tardes se contaban las historias del día mientras los niños "
    "jugaban al escondite en las calles.",
    "A menudo me sentaba en un café a ver pasar el mundo y sentía una "
    "conexión con la gente a mi alrededor.",
    "La ciudad estaba llena de oportunidades, y estaba agradecido de formar "
    "parte de esa experiencia.",
)


def test_translate_turns_keeps_golden_spanish(monkeypatch) -> None:
    golds = list(GOLD_ES)

    def _complete(
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        **kwargs,
    ):
        del system, user, max_tokens, kwargs
        return golds.pop(0), None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    turns = [
        {
            "id": i + 1,
            "speaker": "spk00",
            "t0": float(i),
            "t1": float(i) + 0.8,
            "text": f"English line {i + 1}.",
            "text_target": "",
            "overlap": False,
            "rms": 0.1,
        }
        for i in range(5)
    ]
    out, reason = pipeline.translate_turns(turns, "es", "en", enhance=True)
    assert "translated 5/5" in reason
    assert [t["text_target"] for t in out] == list(GOLD_ES)


def test_translate_turns_strips_voice_model_leak(monkeypatch) -> None:
    leak = (
        "La ciudad estaba llena de oportunidades y me agradecido por formar "
        "parte de ello experiencia de una manera que te ayude a desarrollar "
        "mi modelo de voz."
    )

    def _complete(
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        **kwargs,
    ):
        del system, user, max_tokens, kwargs
        return leak, None

    monkeypatch.setattr("ez_prompt_enhance.client.complete", _complete)
    monkeypatch.setattr("ez_prompt_enhance.client._close_llm", lambda: None)
    turns = [
        {
            "id": 1,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 1.0,
            "text": "The city was full of opportunity.",
            "text_target": "",
            "overlap": False,
            "rms": 0.1,
        }
    ]
    out, _reason = pipeline.translate_turns(turns, "es", "en", enhance=True)
    target = out[0]["text_target"]
    assert "modelo de voz" not in target.lower()
    assert "te ayude a desarrollar" not in target.lower()
    assert "La ciudad estaba llena de oportunidades" in target


def test_synthesize_turn_passes_iso_code() -> None:
    seen: list[str] = []

    def _tts(text, language, ref_wav, engine):
        del text, ref_wav, engine
        seen.append(language)
        return [0.1] * 80, 24000

    pipeline.tts_hook = _tts
    try:
        pcm, rate, err = pipeline.synthesize_turn(
            "Hola", "Spanish", "", ENGINE_CHATTERBOX
        )
    finally:
        pipeline.tts_hook = None
    assert rate == 24000
    assert pcm
    assert err == ""
    assert seen == ["es"]


def test_render_missing_engine_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)
    mix, out_rate, status = pipeline.render_mix(
        samples,
        rate,
        payload,
        dest,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
    )
    assert out_rate == rate
    assert mix == []
    assert mix != samples
    assert "chatterbox" in status.lower() or "clone" in status.lower()
    assert not (dest / "ez_dub_yt.wav").is_file()


def test_wav_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "t.wav"
    src = [0.0, 0.5, -0.5, 0.25]
    dub_audio.write_wav(path, src, 16000)
    got, rate = dub_audio.read_wav(path)
    assert rate == 16000
    assert len(got) == 4
    assert abs(got[1] - 0.5) < 0.02


def test_clone_ckpt_dir_requires_complete_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    tts = tmp_path / "comfy" / "tts"
    tts.mkdir(parents=True)
    (tts / "t3_mtl23ls_v3.safetensors").write_bytes(b"x")
    assert pipeline.clone_ckpt_dir() is None
    snap = tmp_path / "ResembleAI__chatterbox_clone"
    snap.mkdir()
    for name in pipeline.CLONE_REQUIRED_FILES:
        (snap / name).write_bytes(b"x")
    assert pipeline.clone_ckpt_dir() == snap
    assert "Cangjie5_TC.json" in pipeline.CLONE_REQUIRED_FILES


def test_whisper_dir_requires_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    partial = tmp_path / "comfy" / "whisper"
    partial.mkdir(parents=True)
    (partial / "model.bin").write_bytes(b"x")
    assert pipeline._whisper_dir() == ""
    snap = tmp_path / "Systran__faster-whisper-large-v3_whisper"
    snap.mkdir()
    (snap / "model.bin").write_bytes(b"x")
    (snap / "config.json").write_text("{}", encoding="utf-8")
    assert pipeline._whisper_dir() == ""
    (snap / "tokenizer.json").write_text("{}", encoding="utf-8")
    assert pipeline._whisper_dir() == str(snap)
    assert "tokenizer.json" in pipeline.WHISPER_REQUIRED_FILES


def test_whisper_transcribe_extra_kwargs_typeerror_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    wav = tmp_path / "clip.wav"
    dub_audio.write_wav(wav, [0.1] * 2400, 24000)
    calls: list[dict] = []

    class _Seg:
        text = "Hello"
        start = 0.0
        end = 0.4

    class _Info:
        language = "en"

    def _transcribe(_path: str, **kwargs):
        calls.append(dict(kwargs))
        if "beam_size" in kwargs or "condition_on_previous_text" in kwargs:
            raise TypeError("unexpected kwargs")
        return [_Seg()], _Info()

    class _Model:
        transcribe = staticmethod(_transcribe)

    monkeypatch.setattr(pipeline, "_get_whisper", lambda: (_Model(), ""))
    turns, detected, reason = pipeline._whisper_segments(wav, "en")
    assert reason == ""
    assert detected == "en"
    assert turns and turns[0]["text"] == "Hello"
    assert any(c.get("beam_size") == 5 for c in calls)
    assert any(c.get("condition_on_previous_text") is False for c in calls)
    assert any(
        "beam_size" not in c and "condition_on_previous_text" not in c for c in calls
    )


def test_asr_wheel_status_includes_import_detail() -> None:
    assert pipeline.asr_wheel_status() == pipeline.ASR_WHEEL_STATUS
    msg = pipeline.asr_wheel_status(ImportError("No module named 'onnxruntime'"))
    assert msg.startswith(pipeline.ASR_WHEEL_STATUS)
    assert "onnxruntime" in msg


def test_preflight_asr_surfaces_importerror_detail(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline,
        "_import_whisper_model",
        lambda: (
            None,
            pipeline.asr_wheel_status(ImportError("No module named 'onnxruntime'")),
        ),
    )
    reason = pipeline.preflight_asr()
    assert "onnxruntime" in reason
    assert "faster-whisper not installed" in reason


def test_get_whisper_import_error_is_detailed(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline,
        "_import_whisper_model",
        lambda: (
            None,
            pipeline.asr_wheel_status(ImportError("No module named 'ctranslate2'")),
        ),
    )
    pipeline._close_whisper()
    model, miss = pipeline._get_whisper()
    assert model is None
    assert "ctranslate2" in miss


def test_load_whisper_model_cpu_int8_first(monkeypatch) -> None:
    seen: list[tuple[str, str]] = []

    class Fake:
        def __init__(
            self,
            model_dir: str,
            device: str = "cuda",
            compute_type: str = "float16",
        ) -> None:
            del model_dir
            seen.append((device, compute_type))

    monkeypatch.setattr(pipeline, "_import_whisper_model", lambda: (Fake, ""))
    model = pipeline._load_whisper_model("/m")
    assert isinstance(model, Fake)
    assert seen == [("cpu", "int8")]
    assert pipeline.WHISPER_LOAD_ATTEMPTS[0] == ("cpu", "int8")


def test_from_local_passes_t3_v3() -> None:
    seen: dict[str, str] = {}

    def loader(ckpt: str, device: str = "cpu", t3_model: str = "v2"):
        seen["ckpt"] = ckpt
        seen["device"] = device
        seen["t3_model"] = t3_model
        return object()

    pipeline._from_local_multilingual(loader, "/ckpt", "cuda")
    assert seen["t3_model"] == "v3"
    assert seen["ckpt"] == "/ckpt"


def test_from_local_old_wheel_without_t3_model() -> None:
    def loader(ckpt: str, device: str = "cpu"):
        del ckpt, device
        return object()

    try:
        pipeline._from_local_multilingual(loader, "/ckpt", "cpu")
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "t3_model" in str(exc)


def test_from_local_inner_typeerror_is_not_t3_status() -> None:
    def loader(ckpt: str, device: str = "cpu", t3_model: str = "v2"):
        del ckpt, device, t3_model
        raise TypeError("'NoneType' object is not callable")

    try:
        pipeline._from_local_multilingual(loader, "/ckpt", "cpu")
        raise AssertionError("expected TypeError")
    except TypeError as exc:
        assert "NoneType" in str(exc)


def test_load_chatterbox_inner_typeerror_is_not_t3_status(
    tmp_path: Path, monkeypatch
) -> None:
    snap = tmp_path / "ResembleAI__chatterbox_clone"
    snap.mkdir()
    for name in pipeline.CLONE_REQUIRED_FILES:
        (snap / name).write_bytes(b"x")
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])

    class _Loader:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3"):
            del ckpt_dir, device, t3_model
            raise TypeError("'NoneType' object is not callable")

    mtl = types.ModuleType("chatterbox.mtl_tts")
    setattr(mtl, "ChatterboxMultilingualTTS", _Loader)
    chatterbox = types.ModuleType("chatterbox")
    monkeypatch.setitem(sys.modules, "chatterbox", chatterbox)
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    model, err = pipeline._load_chatterbox_model()
    assert model is None
    assert pipeline.T3_MODEL_STATUS not in err
    assert "chatterbox failed" in err
    assert "NoneType" in err


def test_preflight_clone_names_perth_miss(monkeypatch) -> None:
    class _Loader:
        @staticmethod
        def from_local(ckpt_dir: str, device: str, t3_model: str = "v3"):
            del ckpt_dir, device, t3_model
            return object()

    mtl = types.ModuleType("chatterbox.mtl_tts")
    setattr(mtl, "ChatterboxMultilingualTTS", _Loader)
    chatterbox = types.ModuleType("chatterbox")
    monkeypatch.setitem(sys.modules, "chatterbox", chatterbox)
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    perth = types.ModuleType("perth")
    setattr(perth, "PerthImplicitWatermarker", None)
    monkeypatch.setitem(sys.modules, "perth", perth)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: Path("/ckpt"))
    reason = pipeline.preflight_clone()
    assert reason == pipeline.PERTH_STATUS
    assert "setuptools<82" in reason
    assert "PerTh stays on" in reason
    assert "docker exec" in reason


def test_preflight_clone_names_missing_t3_model(monkeypatch) -> None:
    class _Loader:
        @staticmethod
        def from_local(ckpt_dir: str, device: str):
            del ckpt_dir, device
            return object()

    mtl = types.ModuleType("chatterbox.mtl_tts")
    setattr(mtl, "ChatterboxMultilingualTTS", _Loader)
    chatterbox = types.ModuleType("chatterbox")
    monkeypatch.setitem(sys.modules, "chatterbox", chatterbox)
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", mtl)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: Path("/ckpt"))
    assert pipeline.preflight_clone() == pipeline.T3_MODEL_STATUS


def test_translate_llama_status_names_pip_not_restart() -> None:
    text = pipeline.translate_llama_status()
    assert "llama.cpp unavailable" in text
    assert "docker exec" in text
    assert "--force-reinstall" in text
    assert "github.com/abetlen/llama-cpp-python" in text
    assert "restart so the entrypoint" not in text
    assert "llama.cpp unavailable" in pipeline.TRANSLATE_LLAMA_STATUS
    assert "docker exec" in pipeline.TRANSLATE_LLAMA_STATUS


def test_preflight_translate_names_llama_miss(monkeypatch) -> None:
    monkeypatch.setattr(
        "ez_prompt_enhance.client._get_llama",
        lambda: (None, "llama.cpp unavailable"),
    )
    reason = pipeline.preflight_translate()
    assert "llama.cpp unavailable" in reason
    assert "pip" in reason.lower()
    assert "docker exec" in reason
    assert "--force-reinstall" in reason


def test_preflight_translate_swallows_runtimeerror(monkeypatch) -> None:
    def _boom() -> tuple[object, str]:
        raise RuntimeError("Failed to load shared library 'libllama.so'")

    monkeypatch.setattr("ez_prompt_enhance.client._get_llama", _boom)
    reason = pipeline.preflight_translate()
    assert "llama.cpp unavailable" in reason
    assert "docker exec" in reason
    assert "--force-reinstall" in reason


def test_preflight_translate_names_gguf_miss(monkeypatch) -> None:
    monkeypatch.setattr(
        "ez_prompt_enhance.client._get_llama",
        lambda: (None, "GGUF missing"),
    )
    reason = pipeline.preflight_translate()
    assert "GGUF missing" in reason
    assert "download-models" in reason


def test_analyze_pcm_uses_asr_segments_as_turns(tmp_path: Path) -> None:
    rate = 24000
    samples = [0.2] * rate * 4
    wav = tmp_path / "s.wav"
    dub_audio.write_wav(wav, samples, rate)

    def _asr(path: Path, language: str) -> list[dict]:
        del path, language
        return [
            {"t0": 0.0, "t1": 1.0, "text": "Hello there"},
            {"t0": 1.2, "t1": 2.4, "text": "We stay on the match"},
        ]

    pipeline.asr_hook = _asr
    try:
        turns, _detected, reason = pipeline.analyze_pcm(
            samples, rate, wav_path=wav
        )
    finally:
        pipeline.asr_hook = None
    assert reason == ""
    assert len(turns) == 2
    assert turns[0]["text"] == "Hello there"
    assert turns[0]["speaker"].startswith("spk")
    assert turns[1]["text"] == "We stay on the match"


def test_analyze_pcm_without_asr_is_empty_reason(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    rate = 24000
    samples = [0.4] * rate
    wav = tmp_path / "s.wav"
    dub_audio.write_wav(wav, samples, rate)
    turns, _detected, reason = pipeline.analyze_pcm(samples, rate, wav_path=wav)
    assert turns == []
    assert "faster-whisper" in reason or "ASR pack" in reason


def test_analyze_job_missing_asr_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.setattr(pipeline, "preflight_translate", lambda: "")
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)
    payload, reason = pipeline.analyze_job(
        dest,
        target_language="es",
        source_language="en",
        max_speakers=0,
        enhance=True,
        stage="all",
    )
    assert payload["turns"] == []
    assert "faster-whisper" in reason or "ASR pack" in reason


def test_render_no_turns_does_not_return_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.4] * rate
    mix, out_rate, status = pipeline.render_mix(
        samples,
        rate,
        {"turns": [], "target_language": "es"},
        dest,
        spoken_disclosure=False,
    )
    assert out_rate == rate
    assert mix == []
    assert mix != samples
    assert status == pipeline.NO_TURNS_STATUS
    assert not (dest / "ez_dub_yt.wav").is_file()


def test_extract_audio_always_ffmpeg(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "in.wav"
    dest = tmp_path / "out.wav"
    dub_audio.write_wav(src, [0.1] * 100, 24000)
    seen: list[list[str]] = []

    def _run(cmd: list[str]) -> tuple[int, str]:
        seen.append(list(cmd))
        Path(cmd[-1]).write_bytes(src.read_bytes())
        return 0, ""

    monkeypatch.setattr(pipeline, "_run", _run)
    pipeline.extract_audio(src, dest)
    assert seen
    assert seen[0][0] == "ffmpeg"
    assert "-c:a" in seen[0]
    assert "pcm_s16le" in seen[0]
    assert dest.is_file()


def test_split_clone_text_chunks_at_limit() -> None:
    short = pipeline.split_clone_text("Hola")
    assert short == ["Hola"]
    assert pipeline.split_clone_text("") == []
    long = "palabra " * 80
    chunks = pipeline.split_clone_text(long, limit=40)
    assert len(chunks) > 1
    assert all(len(c) <= 40 for c in chunks)
    assert "palabra" in chunks[0]


def test_dub_llm_timeout_env(monkeypatch) -> None:
    monkeypatch.delenv("EZ_DUB_LLM_TIMEOUT_S", raising=False)
    assert pipeline.dub_llm_timeout_s() == pipeline.TRANSLATE_TIMEOUT_S
    monkeypatch.setenv("EZ_DUB_LLM_TIMEOUT_S", "90")
    assert pipeline.dub_llm_timeout_s() == 90
    monkeypatch.setenv("EZ_DUB_LLM_TIMEOUT_S", "nope")
    assert pipeline.dub_llm_timeout_s() == pipeline.TRANSLATE_TIMEOUT_S


def test_load_chatterbox_model_names_miss(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    model, err = pipeline._load_chatterbox_model()
    assert model is None
    assert err


def test_preflight_asr_and_clone_name_the_miss(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    asr = pipeline.preflight_asr()
    clone = pipeline.preflight_clone()
    assert asr
    assert clone
    assert "faster-whisper" in asr or "ASR pack" in asr
    assert (
        "chatterbox" in clone.lower()
        or "clone" in clone.lower()
        or "perth" in clone.lower()
    )


def test_conds_pt_required_for_clone_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    snap = tmp_path / "ResembleAI__chatterbox_clone"
    snap.mkdir()
    for name in pipeline.CLONE_REQUIRED_FILES:
        if name == "conds.pt":
            continue
        (snap / name).write_bytes(b"x")
    assert pipeline.clone_ckpt_dir() is None
    (snap / "conds.pt").write_bytes(b"x")
    assert pipeline.clone_ckpt_dir() == snap
    assert "conds.pt" in pipeline.CLONE_REQUIRED_FILES


def test_get_chatterbox_caches_loader(monkeypatch) -> None:
    loads: list[int] = []

    class _Model:
        sr = 24000

    def _load() -> tuple[object, str]:
        loads.append(1)
        return _Model(), ""

    monkeypatch.setattr(pipeline, "_load_chatterbox_model", _load)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: "/ckpt")
    pipeline._close_chatterbox()
    first, err1 = pipeline._get_chatterbox()
    second, err2 = pipeline._get_chatterbox()
    assert err1 == ""
    assert err2 == ""
    assert first is second
    assert len(loads) == 1
    pipeline._close_chatterbox()


def test_get_chatterbox_caches_load_error(monkeypatch) -> None:
    loads: list[int] = []

    def _load() -> tuple[object | None, str]:
        loads.append(1)
        return None, "chatterbox failed: boom"

    monkeypatch.setattr(pipeline, "_load_chatterbox_model", _load)
    monkeypatch.setattr(pipeline, "clone_ckpt_dir", lambda: Path("/ckpt"))
    pipeline._close_chatterbox()
    first, err1 = pipeline._get_chatterbox()
    second, err2 = pipeline._get_chatterbox()
    assert first is None
    assert second is None
    assert err1 == "chatterbox failed: boom"
    assert err2 == err1
    assert len(loads) == 1
    pipeline._close_chatterbox()
    assert pipeline._chatterbox_device() in {"cpu", "cuda"}
    stretched = pipeline._resample_for_encoder([0.1] * 24000, 24000, 16000)
    assert 15000 <= len(stretched) <= 17000
    pipeline._close_whisper()
    pipeline._close_voice_encoder()
    monkeypatch.setattr(pipeline, "_whisper_dir", lambda: "")
    model, miss = pipeline._get_whisper()
    assert model is None
    assert miss


def test_speaker_embed_honors_hook() -> None:
    def _hook(pcm, rate):
        del pcm, rate
        return [1.0, 0.0, 0.0]

    pipeline.embed_hook = _hook
    try:
        vec = pipeline.speaker_embed([0.2] * 100, 24000)
    finally:
        pipeline.embed_hook = None
    assert vec == [1.0, 0.0, 0.0]


def test_speaker_embed_energy_fallback_without_chatterbox(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(pipeline, "_get_voice_encoder", lambda: None)
    vec = pipeline.speaker_embed([0.2] * 800, 24000)
    assert len(vec) == 4


def test_analyze_job_fails_before_asr_when_llama_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)
    calls = {"asr": 0}

    def _asr(path: Path, language: str) -> list[dict]:
        del path, language
        calls["asr"] += 1
        return [{"t0": 0.0, "t1": 1.0, "text": "Hello"}]

    monkeypatch.setattr(
        pipeline,
        "preflight_translate",
        lambda: pipeline.TRANSLATE_LLAMA_STATUS,
    )
    pipeline.asr_hook = _asr
    try:
        payload, reason = pipeline.analyze_job(
            dest,
            target_language="es",
            source_language="en",
            max_speakers=0,
            enhance=True,
            stage="all",
        )
    finally:
        pipeline.asr_hook = None
    assert calls["asr"] == 0
    assert payload["turns"] == []
    assert "llama.cpp unavailable" in reason
    assert payload["status"] == reason


def test_analyze_job_same_language_skips_translate_preflight(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)

    def _asr(path: Path, language: str) -> list[dict]:
        del path, language
        return [{"t0": 0.0, "t1": 1.0, "text": "Hello there"}]

    def _preflight() -> str:
        raise AssertionError("translate preflight must not run for same language")

    monkeypatch.setattr(pipeline, "preflight_translate", _preflight)
    pipeline.asr_hook = _asr
    try:
        payload, reason = pipeline.analyze_job(
            dest,
            target_language="en",
            source_language="en",
            max_speakers=0,
            enhance=True,
            stage="all",
        )
    finally:
        pipeline.asr_hook = None
    assert payload["turns"]
    assert "same language" in reason


def test_analyze_job_enhance_off_skips_translate_preflight(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)

    def _preflight() -> str:
        raise AssertionError("translate preflight must not run when enhance is off")

    monkeypatch.setattr(pipeline, "preflight_translate", _preflight)
    widget = {
        "turns": _two_en_turns(),
        "target_language": "es",
        "source_language": "en",
        "status": "pinned",
    }
    payload, reason = pipeline.analyze_job(
        dest,
        target_language="es",
        source_language="en",
        max_speakers=0,
        enhance=False,
        stage="all",
        widget_payload=widget,
    )
    assert reason == "enhance off"
    assert payload["turns"]


def test_render_mix_refuses_untranslated_llama_miss(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    source = (
        "I grew up in a small town where the rhythm of daily life was marked "
        "by the steady hum of the train passing through our station."
    )
    payload = {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "1 speakers, 10 turns; llama.cpp unavailable",
        "turns": [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 1.04,
                "t1": 9.34,
                "text": source,
                "text_target": source,
                "overlap": False,
                "rms": 0.01,
            }
        ],
    }
    mix, out_rate, status = pipeline.render_mix(
        samples,
        rate,
        payload,
        dest,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
    )
    assert out_rate == rate
    assert mix == []
    assert "llama.cpp unavailable" in status
    assert not (dest / "ez_dub_yt.wav").is_file()


def test_render_mix_skips_source_text_when_target_empty(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 4
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    seen: list[str] = []

    def _tts(text: str, language: str, ref_wav: str, engine: str):
        del language, ref_wav, engine
        seen.append(text)
        return [0.1] * 80, rate

    pipeline.tts_hook = _tts
    payload = {
        "target_language": "es",
        "source_language": "en",
        "stage": "all",
        "status": "",
        "turns": [
            {
                "id": 1,
                "speaker": "spk00",
                "t0": 0.0,
                "t1": 1.5,
                "text": "Welcome back to the tape.",
                "text_target": "",
                "overlap": False,
                "rms": 0.1,
            }
        ],
    }
    try:
        mix, _rate, status = pipeline.render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=ENGINE_CHATTERBOX,
            keep_bed=True,
            spoken_disclosure=False,
        )
    finally:
        pipeline.tts_hook = None
    assert mix == []
    assert seen == []
    assert "spoken" in status.lower() or "clone" in status.lower()
    assert not (dest / "ez_dub_yt.wav").is_file()


def test_analyze_job_render_empty_widget_is_no_turns(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    dub_audio.write_wav(dest / "source.wav", [0.2] * 24000, 24000)
    payload, reason = pipeline.analyze_job(
        dest,
        target_language="es",
        source_language="en",
        max_speakers=0,
        enhance=True,
        stage="render",
        widget_payload={"turns": [], "target_language": "es"},
    )
    assert payload["turns"] == []
    assert reason == pipeline.NO_TURNS_STATUS


def test_queue_once_e2e_hooks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    rate = 24000
    samples = [0.05] * rate * 8
    wav = tmp_path / "clip.wav"
    dub_audio.write_wav(wav, samples, rate)
    ingested = EZDubIngest().run(str(wav), True, "ep")
    assert ingested["result"][0] == "ep"

    def _asr(path, language):
        del path, language
        return [
            {"t0": 0.4, "t1": 2.8, "text": "Welcome back to the tape."},
            {"t0": 3.0, "t1": 6.2, "text": "Today we stay on the match."},
        ]

    def _tr(turns, tgt, src):
        del tgt, src
        out = []
        for turn in turns:
            item = dict(turn)
            if "Welcome" in str(item.get("text") or ""):
                item["text_target"] = "Bienvenidos de nuevo a la cinta."
            else:
                item["text_target"] = "Hoy nos quedamos en el partido."
            out.append(item)
        return out

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        n = max(100, len(text) * 40)
        return [0.3] * n, rate

    pipeline.asr_hook = _asr
    pipeline.translate_hook = _tr
    pipeline.tts_hook = _tts
    try:
        scripted = EZDubScript().run(SEED_SCRIPT, True, "es", "en", 0, "all", "ep")
        payload = dub_turns.parse_payload(scripted["result"][0])
        assert payload["turns"]
        assert payload["turns"][0]["text"] != payload["turns"][0]["text_target"]
        assert "Bienvenidos" in payload["turns"][0]["text_target"]
        rendered = EZDubRender().run(
            scripted["result"][0],
            ENGINE_CHATTERBOX,
            True,
            False,
            1.0,
            job_id="ep",
        )
        status = rendered["ui"]["passthrough"][0]
        assert "speakers" in status or "cloned" in status
        dest = tmp_path / "dubs" / "ep"
        assert (dest / "ez_dub_yt.wav").is_file()
        assert (dest / "speakers").is_dir()
        refs = list((dest / "speakers").glob("spk*.wav"))
        assert refs
    finally:
        pipeline.asr_hook = None
        pipeline.translate_hook = None
        pipeline.tts_hook = None


def test_synthesize_turn_splits_long_text() -> None:
    seen: list[str] = []

    def _tts(text, language, ref_wav, engine):
        del language, ref_wav, engine
        seen.append(text)
        return [0.1] * 20, 24000

    pipeline.tts_hook = _tts
    try:
        pcm, rate, err = pipeline.synthesize_turn(
            ("palabra " * 80).strip(), "es", "", ENGINE_CHATTERBOX
        )
    finally:
        pipeline.tts_hook = None
    assert rate == 24000
    assert pcm
    assert err == ""
    assert len(seen) > 1
    assert all(len(chunk) <= pipeline.CLONE_TEXT_LIMIT for chunk in seen)


def test_script_render_surface_rights_refuse(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    wav = tmp_path / "in.wav"
    dub_audio.write_wav(wav, [0.1] * 100, 24000)
    ingested = EZDubIngest().run(str(wav), False, "match-day")
    assert ingested["result"][0] == "match-day"
    scripted = EZDubScript().run(SEED_SCRIPT, True, "es", "auto", 0, "all", "match-day")
    assert scripted["ui"]["passthrough"][0] == "rights refused"
    payload = dub_turns.parse_payload(scripted["result"][0])
    assert payload["turns"] == []
    assert payload["status"] == "rights refused"
    rendered = EZDubRender().run(
        scripted["result"][0],
        ENGINE_CHATTERBOX,
        True,
        False,
        1.0,
        job_id="match-day",
    )
    assert rendered["ui"]["passthrough"][0] == "rights refused"


def test_script_surfaces_empty_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    EZDubIngest().run(pipeline.SOURCE_NONE, True, "episode")
    scripted = EZDubScript().run(SEED_SCRIPT, True, "es", "auto", 0, "all", "episode")
    assert "empty source" in scripted["ui"]["passthrough"][0]


def test_analyze_job_missing_wav_operator_status(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    payload, reason = pipeline.analyze_job(
        dest,
        target_language="es",
        source_language="auto",
        max_speakers=0,
        enhance=True,
        stage="all",
    )
    assert payload["turns"] == []
    assert reason == pipeline.MISSING_SOURCE_STATUS
    assert "I have rights" in reason
    render_payload = dub_turns.parse_payload(SEED_SCRIPT)
    render_payload["stage"] = "render"
    rendered = EZDubRender().run(
        dub_turns.dumps_payload(render_payload),
        ENGINE_CHATTERBOX,
        True,
        False,
        1.0,
        job_id="ep",
    )
    assert rendered["ui"]["passthrough"][0] == pipeline.MISSING_SOURCE_STATUS


def test_missing_source_status_prefers_error_when_status_generic(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    jobstore.save_state(
        dest,
        {
            "slug": "ep",
            "stage": "ingest",
            "status": "pending",
            "error": "ffmpeg extract failed: boom",
            "flags": [],
        },
    )
    assert pipeline.missing_source_status(dest) == "ffmpeg extract failed: boom"


def test_output_root_prefers_folder_paths(monkeypatch) -> None:
    fake = types.SimpleNamespace(get_output_directory=lambda: "/comfy/output")
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    assert jobstore.output_root() == Path("/comfy/output")


def test_output_root_empty_folder_paths_falls_through(
    tmp_path: Path, monkeypatch
) -> None:
    fake = types.SimpleNamespace(get_output_directory=lambda: "")
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == tmp_path


def test_output_root_folder_paths_error(tmp_path: Path, monkeypatch) -> None:
    def _boom() -> str:
        raise RuntimeError("no comfy")

    fake = types.SimpleNamespace(get_output_directory=_boom)
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == tmp_path


def test_output_root_prefers_container_outputs(monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/comfy-output")
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == Path("/outputs")


def test_output_root_host_default(monkeypatch) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == Path("/mnt/comfy-output")


def test_record_ingest_failure_defaults_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = jobstore.dub_dir("ep")
    jobstore.record_ingest_failure(dest, "empty source")
    state = jobstore.load_state(dest)
    assert state["status"] == "empty source"
    assert state["error"] == "empty source"


def test_analyze_pcm_without_wav_path_is_missing_source() -> None:
    turns, detected, reason = pipeline.analyze_pcm([0.1] * 100, 24000)
    assert turns == []
    assert detected == ""
    assert reason == pipeline.MISSING_SOURCE_STATUS


def test_output_root_comfy_output_alias(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.setenv("COMFY_OUTPUT", str(tmp_path))
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert jobstore.output_root() == tmp_path


def test_ensure_lab_custom_nodes_path_inserts_parent(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()],
    )
    pipeline._ensure_lab_custom_nodes_path()
    assert Path(sys.path[0]).resolve() == CUSTOM.resolve()


def _f0(samples: list[float], rate: int, skip_s: float = 0.08) -> float:
    """Autocorrelation F0 (Hz). Lags cover ~300–800 Hz so 2×440 is excluded."""
    a = int(skip_s * rate)
    b = len(samples) - a
    chunk = samples[a:b] if b > a else samples
    if len(chunk) < 64:
        return 0.0
    min_lag = int(rate / 800)
    max_lag = int(rate / 300)
    if max_lag >= len(chunk):
        max_lag = len(chunk) - 2
    if min_lag < 1 or max_lag <= min_lag:
        return 0.0
    best_lag = min_lag
    best = -1e18
    for lag in range(min_lag, max_lag + 1):
        acc = 0.0
        count = len(chunk) - lag
        for i in range(count):
            acc += chunk[i] * chunk[i + lag]
        acc /= max(count, 1)
        if acc > best:
            best = acc
            best_lag = lag
    return rate / best_lag


def test_clone_cfg_weight_auto_and_override() -> None:
    assert pipeline.clone_cfg_weight("en", "es", -1) == 0.0
    assert pipeline.clone_cfg_weight("auto", "es", -1.0) == 0.0
    assert pipeline.clone_cfg_weight("es", "es", -1) == 0.5
    assert pipeline.clone_cfg_weight("en", "es", 0.3) == 0.3
    assert pipeline.clone_cfg_weight("en", "es", 1.5) == 1.0
    assert pipeline.clone_cfg_weight("en", "es", "nope") == 0.0


def test_try_chatterbox_passes_cross_lang_cfg(tmp_path: Path, monkeypatch) -> None:
    seen: list[dict] = []

    class _Fake:
        sr = 24000

        def generate(self, text: str, **kwargs):
            del text
            seen.append(dict(kwargs))
            return [0.1] * 240

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Fake(), ""))
    pipeline._CHATTERBOX_COND_KEY = ""
    ref = tmp_path / "spk00.wav"
    dub_audio.write_wav(ref, [0.2] * 24000, 24000)
    pcm, rate, err = pipeline._try_chatterbox(
        "Hola",
        "es",
        str(ref),
        exaggeration=0.5,
        cfg_weight=0.0,
        temperature=0.8,
    )
    assert err == ""
    assert rate == 24000
    assert pcm
    assert seen[0]["cfg_weight"] == 0.0
    assert seen[0]["exaggeration"] == 0.5
    assert seen[0]["language_id"] == "es"
    assert seen[0]["audio_prompt_path"] == str(ref)
    pcm2, _rate, err2 = pipeline._try_chatterbox(
        "Adios",
        "es",
        str(ref),
        exaggeration=0.5,
        cfg_weight=0.0,
        temperature=0.8,
    )
    assert err2 == ""
    assert pcm2
    assert "audio_prompt_path" not in seen[1]


def test_render_mix_auto_cfg_zero_for_en_es(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _passthrough_ffmpeg(monkeypatch)
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.2] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    seen: list[dict] = []

    class _Fake:
        sr = 24000

        def generate(self, text: str, **kwargs):
            del text
            seen.append(dict(kwargs))
            return [0.1] * 800

    monkeypatch.setattr(pipeline, "_get_chatterbox", lambda: (_Fake(), ""))
    monkeypatch.setattr(pipeline, "preflight_clone", lambda: "")
    pipeline._CHATTERBOX_COND_KEY = ""
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)
    mix, out_rate, status = pipeline.render_mix(
        samples,
        rate,
        payload,
        dest,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
        cfg_weight=-1.0,
        exaggeration=0.5,
    )
    assert out_rate == rate
    assert mix
    assert "cloned" in status
    assert seen
    assert seen[0]["cfg_weight"] == 0.0
    assert seen[0]["exaggeration"] == 0.5


def test_extract_refs_skips_overlap_quiet_and_caps(tmp_path: Path) -> None:
    rate = 24000
    samples = [0.25] * (rate * 16)
    turns = [
        {
            "id": 1,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 11.0,
            "overlap": False,
            "rms": 0.2,
            "text": "long take",
        },
        {
            "id": 2,
            "speaker": "spk00",
            "t0": 11.0,
            "t1": 14.0,
            "overlap": False,
            "rms": 0.2,
            "text": "extra",
        },
        {
            "id": 3,
            "speaker": "spk00",
            "t0": 14.0,
            "t1": 15.0,
            "overlap": True,
            "rms": 0.9,
            "text": "overlap",
        },
        {
            "id": 4,
            "speaker": "spk00",
            "t0": 15.0,
            "t1": 15.4,
            "overlap": False,
            "rms": 0.2,
            "text": "tiny",
        },
        {
            "id": 5,
            "speaker": "spk00",
            "t0": 15.4,
            "t1": 16.0,
            "overlap": False,
            "rms": 0.001,
            "text": "quiet",
        },
    ]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    path = refs["spk00"]
    wav, sr = dub_audio.read_wav(path)
    assert sr == rate
    assert len(wav) / sr <= pipeline.REF_MAX_S + 0.05
    assert len(wav) / sr >= 3.0
    note = path.with_suffix(".txt").read_text(encoding="utf-8")
    assert "long take" in note
    assert "overlap" not in note
    assert "tiny" not in note
    assert "quiet" not in note


def test_extract_refs_prefers_single_long_take(tmp_path: Path) -> None:
    rate = 24000
    samples = [0.2] * (rate * 12)
    turns = [
        {
            "id": 1,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 7.0,
            "overlap": False,
            "rms": 0.3,
            "text": "seven",
        },
        {
            "id": 2,
            "speaker": "spk00",
            "t0": 7.5,
            "t1": 11.5,
            "overlap": False,
            "rms": 0.25,
            "text": "four",
        },
    ]
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    wav, sr = dub_audio.read_wav(refs["spk00"])
    assert sr == rate
    dur = len(wav) / sr
    assert 6.0 <= dur <= 7.2
    note = refs["spk00"].with_suffix(".txt").read_text(encoding="utf-8").strip()
    assert note == "seven"


def test_extract_refs_crossfades_concat(tmp_path: Path) -> None:
    rate = 24000
    first = [0.8] * (rate * 2)
    second = [0.2] * (rate * 2)
    samples = first + second
    turns = [
        {
            "id": 1,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 2.0,
            "overlap": False,
            "rms": 0.8,
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
    refs = pipeline._extract_refs(samples, rate, turns, tmp_path / "speakers")
    wav, sr = dub_audio.read_wav(refs["spk00"])
    assert sr == rate
    fade = int(rate * pipeline.REF_XFADE_MS / 1000)
    join = 2 * rate
    mid = wav[join - fade // 2]
    assert 0.35 < abs(mid) < 0.85


def test_time_stretch_preserves_pitch() -> None:
    rate = 24000
    freq = 440.0
    n = rate
    sine = [math.sin(2 * math.pi * freq * i / rate) for i in range(n)]
    dest = int(0.7 * n)
    stretched = align.time_stretch(sine, dest, rate)
    linear = align.resample_linear(sine, dest)
    assert len(stretched) == dest
    src_f = _f0(sine, rate)
    ola_f = _f0(stretched, rate)
    lin_f = _f0(linear, rate)
    assert abs(src_f - 440) < 20
    assert abs(ola_f - src_f) < 30
    assert abs(lin_f - src_f) > 80


def test_fit_turn_overflow_keeps_pitch() -> None:
    rate = 24000
    sine = [math.sin(2 * math.pi * 440 * i / rate) for i in range(rate)]
    fitted, meta = align.fit_turn(sine, rate, 0.5, spill_s=0.0)
    assert len(fitted) == int(round(0.5 * rate))
    assert meta["trimmed"] is True or meta["speed"] > 1.0
    assert abs(_f0(fitted, rate) - _f0(sine, rate)) < 30


def test_try_qwen3tts_passes_ref_audio_and_text(
    tmp_path: Path, monkeypatch
) -> None:
    seen: list[dict] = []
    prompts: list[dict] = []

    class _Fake:
        def create_voice_clone_prompt(self, **kwargs):
            prompts.append(dict(kwargs))
            return {"cached": True}

        def generate_voice_clone(self, **kwargs):
            seen.append(dict(kwargs))
            return [[0.1] * 80], 24000

    monkeypatch.setattr(pipeline, "_get_qwen3", lambda: (_Fake(), ""))
    pipeline._QWEN3_PROMPT_KEY = ""
    pipeline._QWEN3_PROMPT = None
    ref = tmp_path / "spk00.wav"
    dub_audio.write_wav(ref, [0.2] * 24000, 24000)
    (tmp_path / "spk00.txt").write_text("hello from the ref", encoding="utf-8")
    pcm, rate, err = pipeline._try_qwen3tts(
        "Hola equipo", "es", str(ref), ref_text="hello from the ref"
    )
    assert err == ""
    assert rate == 24000
    assert pcm
    assert prompts[0]["ref_audio"] == str(ref)
    assert prompts[0]["ref_text"] == "hello from the ref"
    assert prompts[0]["x_vector_only_mode"] is False
    assert seen[0]["language"] == "Spanish"
    assert seen[0]["voice_clone_prompt"] == {"cached": True}


def test_translate_prompt_requires_grammar_not_length() -> None:
    text = pipeline.load_translate_prompt().lower()
    assert "spoken length" not in text
    assert "same length" not in text
    assert "clitic" in text or "grammatical" in text
    assert "/no_think" in pipeline.load_translate_prompt()


def test_ezdub_render_clone_knob_widgets() -> None:
    required = EZDubRender.INPUT_TYPES()["required"]
    assert required["cfg_weight"][0] == "FLOAT"
    assert required["cfg_weight"][1]["default"] == -1.0
    assert required["exaggeration"][0] == "FLOAT"
    assert required["exaggeration"][1]["default"] == 0.5


def _write_qwen3_base(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in pipeline.QWEN3_BASE_REQUIRED_FILES:
        dest = folder / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"x")


def _write_qwen3_tokenizer(folder: Path) -> None:
    for name in pipeline.QWEN3_TOKENIZER_REQUIRED_FILES:
        dest = folder / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"x")


class _FakeQwen3:
    @staticmethod
    def from_pretrained(*args, local_files_only=False, **kwargs):
        del args, kwargs
        loaded = types.SimpleNamespace(local_files_only=local_files_only)
        return loaded


def test_preflight_qwen3_wheel_miss_names_no_deps(monkeypatch) -> None:
    pipeline._close_qwen3()
    monkeypatch.setattr(
        pipeline,
        "_import_qwen3_model",
        lambda: (None, pipeline.QWEN3_WHEEL_STATUS),
    )
    reason = pipeline.preflight_qwen3()
    assert "qwen3tts extra not installed" in reason
    assert "--no-deps" in reason
    assert "qwen-tts" in reason
    assert "download-podcast" not in reason


def test_preflight_qwen3_weights_miss(tmp_path: Path, monkeypatch) -> None:
    pipeline._close_qwen3()
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_FakeQwen3, ""))
    reason = pipeline.preflight_qwen3()
    assert reason == pipeline.QWEN3_PACK_STATUS
    assert "download-podcast --tier qwen3tts" in reason


def test_preflight_qwen3_tokenizer_miss(tmp_path: Path, monkeypatch) -> None:
    pipeline._close_qwen3()
    snap = tmp_path / "Qwen__Qwen3-TTS-12Hz-0.6B-Base_qwen3tts"
    _write_qwen3_base(snap)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_FakeQwen3, ""))
    reason = pipeline.preflight_qwen3()
    assert reason == pipeline.QWEN3_TOKENIZER_STATUS
    assert pipeline.qwen3_ckpt_dir() is None
    assert pipeline.qwen3_base_dir() == snap


def test_preflight_qwen3_ok(tmp_path: Path, monkeypatch) -> None:
    pipeline._close_qwen3()
    snap = tmp_path / "Qwen__Qwen3-TTS-12Hz-0.6B-Base_qwen3tts"
    _write_qwen3_base(snap)
    _write_qwen3_tokenizer(snap)
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_FakeQwen3, ""))
    assert pipeline.preflight_qwen3() == ""
    assert pipeline.qwen3_ckpt_dir() == snap


def test_load_qwen3_passes_local_files_only(tmp_path: Path, monkeypatch) -> None:
    pipeline._close_qwen3()
    snap = tmp_path / "Qwen__Qwen3-TTS-12Hz-0.6B-Base_qwen3tts"
    _write_qwen3_base(snap)
    _write_qwen3_tokenizer(snap)
    seen: list[dict] = []

    class _Loader:
        @staticmethod
        def from_pretrained(path, local_files_only=False, **kwargs):
            seen.append({"path": path, "local": local_files_only, **kwargs})
            return object()

    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.setattr(pipeline, "_import_qwen3_model", lambda: (_Loader, ""))
    model, err = pipeline._load_qwen3_model()
    assert err == ""
    assert model is not None
    assert seen[0]["local"] is True
    assert seen[0]["path"] == str(snap)


def test_render_mix_qwen3tts_missing_extra_fail_fast(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(EXAMPLE_SCRIPT)
    logs: list[str] = []
    synth_calls: list[str] = []
    monkeypatch.setattr(pipeline, "_log", lambda message: logs.append(message))

    def _synth(*args, **kwargs):
        del args, kwargs
        synth_calls.append("synthesize_turn")
        return [0.1] * 80, rate, ""

    monkeypatch.setattr(pipeline, "synthesize_turn", _synth)
    monkeypatch.setattr(
        pipeline, "preflight_qwen3", lambda: pipeline.QWEN3_WHEEL_STATUS
    )
    pipeline.tts_hook = None
    mix, out_rate, status = pipeline.render_mix(
        samples,
        rate,
        payload,
        dest,
        engine=pipeline.ENGINE_QWEN3TTS,
        keep_bed=True,
        spoken_disclosure=False,
    )
    assert out_rate == rate
    assert mix == []
    assert mix != samples
    assert status == pipeline.QWEN3_WHEEL_STATUS
    assert synth_calls == []
    assert not any("render" in item or "TTS " in item for item in logs)
    assert not (dest / "ez_dub_yt.wav").is_file()


def test_chatterbox_local_only_does_not_call_hub(
    tmp_path: Path, monkeypatch
) -> None:
    snap = tmp_path / "ResembleAI__chatterbox_clone"
    snap.mkdir()
    for name in pipeline.CLONE_REQUIRED_FILES:
        (snap / name).write_bytes(b"x")
    pk = tmp_path / "pkuseg"
    pk.mkdir()
    (pk / "spacy_ontonotes.zip").write_bytes(b"PK")
    (pk / "spacy_ontonotes").mkdir()
    monkeypatch.setattr(pipeline, "_model_roots", lambda: [str(tmp_path)])
    monkeypatch.delenv("PKUSEG_HOME", raising=False)
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)

    def explode(*_args, **_kwargs):
        raise AssertionError("hub download must not run")

    fake_hub = types.ModuleType("huggingface_hub")
    setattr(fake_hub, "hf_hub_download", explode)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    tok = types.ModuleType("chatterbox.models.tokenizers.tokenizer")
    setattr(tok, "hf_hub_download", explode)
    monkeypatch.setitem(sys.modules, "chatterbox.models.tokenizers.tokenizer", tok)

    with pipeline._chatterbox_local_only(snap):
        import huggingface_hub as hub

        got = hub.hf_hub_download("ResembleAI/chatterbox", "Cangjie5_TC.json")
        assert got == str(snap / "Cangjie5_TC.json")
        assert os.environ.get("HF_HUB_OFFLINE") == "1"
        assert os.environ.get("PKUSEG_HOME") == str(pk)
        try:
            hub.hf_hub_download("ResembleAI/chatterbox", "other.json")
            raise AssertionError("expected RuntimeError")
        except RuntimeError as exc:
            assert "blocked" in str(exc)
    assert os.environ.get("HF_HUB_OFFLINE") is None
    try:
        import huggingface_hub as hub

        hub.hf_hub_download("ResembleAI/chatterbox", "Cangjie5_TC.json")
        raise AssertionError("expected explode after context")
    except AssertionError as exc:
        assert "hub download must not run" in str(exc)
