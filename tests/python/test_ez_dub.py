"""Hermetic tests for ez_dub (no Comfy, no network, no Whisper, no TTS)."""

from __future__ import annotations

import math
import sys
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
    assert out["result"][0] == ""
    assert out["ui"]["passthrough"][0] == "rights refused"
    assert not (tmp_path / "dubs" / "episode" / "source.wav").is_file()


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
    assert not (tmp_path / "dubs" / "episode" / "source.wav").is_file()


def test_ingest_wav_and_script_pin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    tone = [0.4 * math.sin(2 * math.pi * 220 * i / 24000) for i in range(24000)]
    wav = tmp_path / "in.wav"
    dub_audio.write_wav(wav, [0.0] * 8000 + tone + [0.0] * 8000, 24000)
    ingested = EZDubIngest().run(str(wav), True, "match-day")
    assert ingested["result"][0] == "match-day"
    dest = tmp_path / "dubs" / "match-day"
    assert (dest / "source.wav").is_file()
    pinned = EZDubScript().run(
        SEED_SCRIPT,
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
    parsed = dub_turns.parse_payload(SEED_SCRIPT)
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


def test_is_url_and_language_name() -> None:
    assert pipeline.is_url("https://youtube.com/watch?v=abc")
    assert not pipeline.is_url("/tmp/file.wav")
    assert pipeline.language_name("es") == "Spanish"
    assert pipeline.language_name("Spanish") == "Spanish"


def test_render_uses_tts_hook(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "dubs" / "ep"
    dest.mkdir(parents=True)
    rate = 24000
    samples = [0.05] * rate * 8
    dub_audio.write_wav(dest / "source.wav", samples, rate)
    payload = dub_turns.parse_payload(SEED_SCRIPT)

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
    assert (dest / "ez_dub.disclosure.txt").read_text(encoding="utf-8").startswith(
        DISCLOSURE_TEXT
    )
    assert (dest / "ez_dub.es.srt").is_file()
    assert "ok" in status or status == "ok"


def test_render_analyze_stage_skips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    payload = dub_turns.parse_payload(SEED_SCRIPT)
    payload["stage"] = "analyze"
    out = EZDubRender().run(dub_turns.dumps_payload(payload), ENGINE_CHATTERBOX, True, False, 1.0, "ep")
    assert out["ui"]["passthrough"][0].startswith("analyze only")


def test_fetch_hook_ingest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
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


def test_wav_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "t.wav"
    src = [0.0, 0.5, -0.5, 0.25]
    dub_audio.write_wav(path, src, 16000)
    got, rate = dub_audio.read_wav(path)
    assert rate == 16000
    assert len(got) == 4
    assert abs(got[1] - 0.5) < 0.02
