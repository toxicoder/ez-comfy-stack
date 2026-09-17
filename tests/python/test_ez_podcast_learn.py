"""Hermetic tests for the learning-podcast ingest, digest, loop, and nodes."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_podcast import digest as digest_mod  # noqa: E402
from ez_podcast import ingest as ingest_mod  # noqa: E402
from ez_podcast.digest import (  # noqa: E402
    DEFAULT_DURATION,
    DEFAULT_FORMAT,
    DURATION_BRIEFING,
    DURATION_COMMUTE,
    FORMAT_EXPLAINER,
    FORMAT_LECTURE,
    naive_script,
    resolve_duration,
    resolve_format,
    run_learn,
    section_count,
    word_budget,
    write_digest,
    write_script,
)
from ez_podcast.ingest import (  # noqa: E402
    MAX_URLS,
    SourceRecord,
    collect_urls,
    format_sources_block,
    ingest_paste,
    is_video_url,
    parse_captions,
)
from ez_podcast.loop import loop_to_match  # noqa: E402
from ez_podcast.nodes import (  # noqa: E402
    EZAudioLoopToMatch,
    EZPodcastLearn,
    SEED_SOURCES,
)


def _rec(
    *,
    kind: str = "paste",
    title: str = "notes",
    url: str = "",
    text: str = "A fact.",
    status: str = "ok",
) -> SourceRecord:
    return {
        "kind": kind,
        "title": title,
        "url": url,
        "text": text,
        "status": status,
    }


def test_collect_urls_keeps_prose_and_caps() -> None:
    paste = (
        "Read this first. https://example.com/a "
        "http://insecure.example/x https://example.com/a "
        + " ".join(f"https://example.com/n{i}" for i in range(10))
        + " leftover notes"
    )
    kept, dropped, prose = collect_urls(paste)
    assert kept[0] == "https://example.com/a"
    assert "http://insecure.example/x" in kept
    assert len(kept) == MAX_URLS
    assert dropped
    assert "Read this first." in prose
    assert "leftover notes" in prose
    assert "https://" not in prose


def test_parse_captions_vtt_and_srt() -> None:
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:01.000\n"
        "Hello <b>there</b>\n\n"
        "00:00:01.000 --> 00:00:02.000\n"
        "Hello there\n\n"
        "00:00:02.000 --> 00:00:03.000\n"
        "Next line\n"
    )
    assert parse_captions(vtt) == "Hello there Next line"
    srt = "1\n00:00:00,000 --> 00:00:01,000\nAlpha\n\n2\n00:00:01,000 --> 00:00:02,000\nBeta\n"
    assert parse_captions(srt) == "Alpha Beta"


def test_is_video_url() -> None:
    assert is_video_url("https://www.youtube.com/watch?v=abc")
    assert is_video_url("https://youtu.be/abc")
    assert is_video_url("https://vimeo.com/123")
    assert is_video_url("https://cdn.example.com/talk.mp4")
    assert not is_video_url("https://example.com/article")


def test_ingest_mixed_paste_hooks(tmp_path: Path) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("Local file claim about occupancy.", encoding="utf-8")
    paste = (
        f"Intro sentence.\nhttps://example.com/doc\n"
        f"https://www.youtube.com/watch?v=abc\n"
        f"http://insecure.example/x\n"
        f"{notes}\n"
        "Closing sentence."
    )
    ingest_mod.page_fetch_hook = lambda url: f"PAGE BODY for {url}"
    ingest_mod.caption_fetch_hook = lambda url: "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nSpoken line\n"
    try:
        records = ingest_paste(paste, fetch_links=True)
    finally:
        ingest_mod.page_fetch_hook = None
        ingest_mod.caption_fetch_hook = None
    kinds = {rec["kind"] for rec in records}
    assert "page" in kinds
    assert "captions" in kinds
    assert "file" in kinds
    assert "paste" in kinds
    skipped = [rec for rec in records if rec["kind"] == "skipped"]
    statuses = " ".join(rec["status"] for rec in skipped)
    assert "https only" in statuses
    page = next(rec for rec in records if rec["kind"] == "page")
    assert "PAGE BODY" in page["text"]
    caps = next(rec for rec in records if rec["kind"] == "captions")
    assert "Spoken line" in caps["text"]
    local = next(rec for rec in records if rec["kind"] == "file")
    assert "occupancy" in local["text"]
    prose = next(rec for rec in records if rec["kind"] == "paste")
    assert "Intro sentence." in prose["text"]
    assert "Closing sentence." in prose["text"]


def test_ingest_fetch_off_skips_urls(tmp_path: Path) -> None:
    notes = tmp_path / "keep.md"
    notes.write_text("Only local.", encoding="utf-8")
    ingest_mod.page_fetch_hook = lambda url: "SHOULD NOT FETCH"
    try:
        records = ingest_paste(
            f"Hello https://example.com/doc {notes}", fetch_links=False
        )
    finally:
        ingest_mod.page_fetch_hook = None
    assert any(rec["status"] == "fetch off" for rec in records)
    assert all("SHOULD NOT FETCH" not in rec["text"] for rec in records)
    assert any(rec["kind"] == "file" for rec in records)


def test_ingest_blocked_https_skips_without_fetch() -> None:
    with patch("ez_research.search.is_blocked_url", return_value="blocked host"):
        records = ingest_paste("https://localhost/secret", fetch_links=True)
    assert records[0]["kind"] == "skipped"
    assert "blocked" in records[0]["status"]
    assert records[0]["text"] == ""


def test_ingest_missing_captions_fail_soft() -> None:
    ingest_mod.caption_fetch_hook = lambda url: ""
    try:
        records = ingest_paste(
            "https://www.youtube.com/watch?v=none", fetch_links=True
        )
    finally:
        ingest_mod.caption_fetch_hook = None
    assert records[0]["kind"] == "skipped"
    assert records[0]["status"] == "no captions"


def test_ingest_drops_extra_urls() -> None:
    paste = " ".join(f"https://example.com/n{i}" for i in range(MAX_URLS + 3))
    ingest_mod.page_fetch_hook = lambda url: f"body {url}"
    try:
        records = ingest_paste(paste, fetch_links=True)
    finally:
        ingest_mod.page_fetch_hook = None
    dropped = next(rec for rec in records if rec["title"] == "extra URLs")
    assert "dropped 3 extra URLs" in dropped["status"]
    pages = [rec for rec in records if rec["kind"] == "page"]
    assert len(pages) == MAX_URLS


def test_format_sources_block_skips_empty_and_caps() -> None:
    records = [
        _rec(kind="skipped", text="", status="no captions"),
        _rec(title="A", url="https://example.com/a", text="Alpha claim."),
        _rec(title="B", url="https://example.com/a", text="Alpha claim."),
    ]
    block = format_sources_block(records)
    assert "[1] A" in block
    assert "Alpha claim." in block
    assert "no captions" not in block


def test_resolve_format_and_duration() -> None:
    assert resolve_format("explainer") == FORMAT_EXPLAINER
    assert resolve_format("Quick recap") == "Quick recap"
    assert resolve_format("nope") == DEFAULT_FORMAT
    assert resolve_duration("briefing") == DURATION_BRIEFING
    assert resolve_duration("3 min commute") == DURATION_COMMUTE
    assert word_budget(DURATION_COMMUTE) == 450
    assert section_count(DURATION_BRIEFING) == 3
    assert section_count(DURATION_COMMUTE) == 1


def test_naive_script_lecture_and_budget() -> None:
    digest = " ".join(f"Sentence number {i} is here." for i in range(40))
    lecture = naive_script(digest, fmt=FORMAT_LECTURE, duration=DURATION_COMMUTE)
    assert "Speaker B:" not in lecture
    assert lecture.startswith("Speaker A:")
    assert len(lecture.split()) <= word_budget(DURATION_COMMUTE) + 40
    duo = naive_script("One thought. Two thought.", fmt=FORMAT_EXPLAINER, duration=DURATION_COMMUTE)
    assert "Speaker A:" in duo
    assert "Speaker B:" in duo


def test_write_digest_enhance_off_concatenates() -> None:
    records = [
        _rec(title="A", url="https://a.example", text="First unique claim."),
        _rec(title="B", url="https://b.example", text="Second unique claim."),
    ]
    text, status = write_digest(records, enhance=False)
    assert status == "enhance off"
    assert "First unique claim." in text
    assert "Second unique claim." in text


def test_write_digest_missing_gguf_passthrough() -> None:
    records = [_rec(text="Keep me.")]
    with patch.object(digest_mod, "_complete", return_value=("", "GGUF missing")):
        text, status = write_digest(records, enhance=True)
    assert "Keep me." in text
    assert "GGUF missing" in status


def test_write_script_section_count_and_unload() -> None:
    calls: list[str] = []

    def fake_complete(system: str, user: str) -> tuple[str, str]:
        calls.append(user)
        idx = len(calls)
        return f"Speaker A: Section {idx}.\nSpeaker B: Ack {idx}.", "ok"

    with (
        patch.object(digest_mod, "_complete", side_effect=fake_complete),
        patch.object(digest_mod, "_close_writer") as close,
    ):
        script, status = write_script(
            "A digest about occupancy.",
            fmt=FORMAT_EXPLAINER,
            duration=DURATION_BRIEFING,
            enhance=True,
        )
    close.assert_called()
    assert status == "ok"
    assert len(calls) == 3
    assert "Section 1 of 3" in calls[0]
    assert "Speaker A: Section 1." in script
    assert "Section 3." in script


def test_write_script_format_changes_system() -> None:
    captured: list[str] = []

    def fake_complete(system: str, user: str) -> tuple[str, str]:
        captured.append(system)
        return "Speaker A: Only me.", "ok"

    with (
        patch.object(digest_mod, "_complete", side_effect=fake_complete),
        patch.object(digest_mod, "_close_writer"),
    ):
        write_script("Digest.", fmt=FORMAT_LECTURE, duration=DURATION_COMMUTE, enhance=True)
    assert captured
    assert "Speaker A only" in captured[0] or "Solo lecture" in captured[0]


def test_run_learn_enhance_off() -> None:
    payload = run_learn(
        [_rec(text="Occupancy is one job.")],
        fmt="explainer",
        duration="commute",
        enhance=False,
    )
    assert "Occupancy is one job." in payload["digest"]
    assert payload["script"].startswith("Speaker A:")
    assert payload["format"] == FORMAT_EXPLAINER
    assert payload["duration"] == DURATION_COMMUTE


def test_loop_matches_speech_length() -> None:
    speech = {"waveform": [[[0.1, 0.2, 0.3, 0.4, 0.5]]], "sample_rate": 24000}
    bed = {"waveform": [[[0.9, -0.9]]], "sample_rate": 24000}
    out = loop_to_match(speech, bed)
    pcm = out["waveform"][0][0]
    assert len(pcm) == 5
    assert pcm[0] == 0.9
    assert pcm[1] == -0.9
    assert pcm[2] == 0.9
    empty = loop_to_match({"waveform": [[[]]], "sample_rate": 24000}, bed)
    assert empty["waveform"][0][0] == [0.0]


def test_ez_audio_loop_node() -> None:
    speech = {"waveform": [[[0.1, 0.2, 0.3]]], "sample_rate": 24000}
    bed = {"waveform": [[[1.0]]], "sample_rate": 24000}
    out = EZAudioLoopToMatch().run(speech, bed)[0]
    assert len(out["waveform"][0][0]) == 3


def test_ez_podcast_learn_enhance_off_and_sample() -> None:
    types = EZPodcastLearn.INPUT_TYPES()
    required = types["required"]
    assert required["enhance"][1]["default"] is True
    assert required["fetch_links"][1]["default"] is True
    assert DEFAULT_FORMAT in required["format"][0]
    assert DEFAULT_DURATION in required["duration"][0]
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZPodcastLearn().run(
            SEED_SOURCES,
            FORMAT_EXPLAINER,
            DURATION_COMMUTE,
            False,
            False,
        )
    complete.assert_not_called()
    digest, script = out["result"]
    assert "Kokoro" in digest or "occupancy" in digest.lower()
    assert script.startswith("Speaker A:")
    assert "enhance off" in out["ui"]["passthrough"][0]


def test_ez_podcast_learn_unloads_writer() -> None:
    with (
        patch.object(
            digest_mod,
            "_complete",
            return_value=("Speaker A: Hi.\nSpeaker B: Yo.", "ok"),
        ),
        patch.object(digest_mod, "_close_writer") as close,
    ):
        out = EZPodcastLearn().run("lazy occupancy notes", enhance=True, fetch_links=False)
    close.assert_called()
    assert "Speaker A: Hi." in out["result"][1]


def test_learn_prompts_exist() -> None:
    digest = digest_mod.load_prompt("learn_digest")
    script = digest_mod.load_prompt("learn_script")
    assert "deduplicate" in digest.lower() or "Deduplicate" in digest
    assert "Speaker A:" in script
    assert "news copy" in script.lower()
    assert "medical" in script.lower()


def test_ingest_paste_empty() -> None:
    assert ingest_paste("", fetch_links=True) == []


def test_loop_empty_bed_silences_to_speech() -> None:
    speech = {"waveform": [[[0.1, 0.2]]], "sample_rate": 24000}
    bed = {"waveform": [[[]]], "sample_rate": 24000}
    out = loop_to_match(speech, bed)
    assert out["waveform"][0][0] == [0.0, 0.0]


def test_ingest_helpers_and_caps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_podcast.ingest import (
        MAX_PASTE_CHARS,
        MAX_TOTAL_SOURCE_CHARS,
        _as_bool,
        _ensure_lab_custom_nodes_path,
        _fetch_captions,
        _fetch_page,
        _looks_like_path,
        _read_local_file,
        _yt_dlp_captions,
        format_status,
        strip_html,
        truncate_text,
    )

    assert _as_bool(1) is True
    assert _as_bool("yes") is True
    assert _as_bool("no") is False
    assert _as_bool(None) is False
    assert strip_html("<p>Hi&nbsp;there</p>") == "Hi there"
    assert truncate_text("abc", 10) == "abc"
    assert truncate_text("abcdefghij", 4) == "abcd"
    assert truncate_text(None) == ""  # type: ignore[arg-type]
    assert not _looks_like_path("")
    assert not _looks_like_path("https://x")
    vtt = tmp_path / "talk.vtt"
    vtt.write_text(
        "WEBVTT\nNOTE hello\nSTYLE\nKind: captions\nLanguage: en\n"
        "00:00:00.000 --> 00:00:01.000\n<b></b>\n"
        "not-a-time --> still\n"
        "00:00:01.000 --> 00:00:02.000\nHi\n",
        encoding="utf-8",
    )
    rec = _read_local_file(vtt)
    assert rec["kind"] == "captions"
    assert "Hi" in rec["text"]
    mp4 = tmp_path / "clip.mp4"
    mp4.write_bytes(b"xxxx")
    skipped = _read_local_file(mp4)
    assert skipped["status"] == "no captions"
    monkeypatch.setattr(Path, "read_text", lambda self, **k: (_ for _ in ()).throw(OSError("boom")))
    failed = _read_local_file(vtt)
    assert "read failed" in failed["status"]
    monkeypatch.undo()
    long_paste = "x" * (MAX_PASTE_CHARS + 10) + " https://example.com/z"
    ingest_mod.page_fetch_hook = lambda url: "ok"
    try:
        ingest_paste(long_paste, fetch_links=True)
    finally:
        ingest_mod.page_fetch_hook = None
    ingest_mod.page_fetch_hook = lambda url: ""
    try:
        empty = ingest_paste("https://example.com/empty", fetch_links=True)
    finally:
        ingest_mod.page_fetch_hook = None
    assert empty[0]["status"] == "empty page"
    huge = "n" * (MAX_TOTAL_SOURCE_CHARS)
    block = format_sources_block(
        [
            _rec(title="A", url="https://a.example", text=huge),
            _rec(title="B", url="https://b.example", text=huge),
        ]
    )
    assert len(block) <= MAX_TOTAL_SOURCE_CHARS
    almost = "n" * (MAX_TOTAL_SOURCE_CHARS - 40)
    capped = format_sources_block(
        [
            _rec(title="A", text=almost),
            _rec(title="B", text="second source that cannot fit"),
        ]
    )
    assert "second source" not in capped
    ingest_paste("see ./no-such-notes.md please", fetch_links=False)
    assert format_status([_rec(title="A", status="ok")]) == "paste: A — ok"
    monkeypatch.setattr(sys, "path", [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()])
    _ensure_lab_custom_nodes_path()
    assert Path(sys.path[0]).resolve() == CUSTOM.resolve()
    _ensure_lab_custom_nodes_path()
    ingest_mod.page_fetch_hook = None
    with (
        patch("ez_research.search.is_blocked_url", return_value="blocked host"),
        patch("ez_research.search.http_get", return_value="<p>no</p>"),
    ):
        assert _fetch_page("https://localhost/x") == ""
    with (
        patch("ez_research.search.is_blocked_url", return_value=None),
        patch("ez_research.search.http_get", return_value="<p>Hello</p>"),
    ):
        assert "Hello" in _fetch_page("https://example.com/ok")
    with patch("ez_research.search.http_get", side_effect=ImportError("no")):
        pass
    with patch.dict("sys.modules", {"ez_research.search": None}):
        # Import of a None module raises; production fail-softs.
        text = _fetch_page("https://example.com/x")
        assert text == ""
    import subprocess

    class Proc:
        returncode = 1
        stderr = "miss"
        stdout = ""

    def fake_run_fail(*_a: object, **_k: object) -> Proc:
        return Proc()

    with patch("subprocess.run", side_effect=fake_run_fail):
        assert _yt_dlp_captions("https://youtu.be/x") == ""

    def fake_run_timeout(*_a: object, **_k: object) -> Proc:
        raise subprocess.TimeoutExpired(cmd="yt-dlp", timeout=1)

    with patch("subprocess.run", side_effect=fake_run_timeout):
        assert _yt_dlp_captions("https://youtu.be/x") == ""

    def fake_run_ok(cmd: list[str], **_k: object) -> Proc:
        dest = Path(cmd[cmd.index("-o") + 1])
        dest.parent.mkdir(parents=True, exist_ok=True)
        (dest.parent / "captions.en.vtt").write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nCaption hi\n",
            encoding="utf-8",
        )
        (dest.parent / "ignore.bin").write_bytes(b"x")
        (dest.parent / "nested").mkdir(exist_ok=True)
        ok = Proc()
        ok.returncode = 0
        return ok

    with patch("subprocess.run", side_effect=fake_run_ok):
        assert "Caption hi" in _yt_dlp_captions("https://youtu.be/x")
        assert "Caption hi" in _fetch_captions("https://youtu.be/x")

    def fake_run_unreadable(cmd: list[str], **_k: object) -> Proc:
        dest = Path(cmd[cmd.index("-o") + 1])
        dest.parent.mkdir(parents=True, exist_ok=True)
        (dest.parent / "captions.en.vtt").write_text("WEBVTT\n", encoding="utf-8")
        ok = Proc()
        ok.returncode = 0
        return ok

    real_read = Path.read_text

    def fail_vtt(self: Path, **kwargs: object) -> str:
        if self.suffix == ".vtt":
            raise OSError("unreadable")
        return real_read(self, **kwargs)  # type: ignore[arg-type]

    with (
        patch("subprocess.run", side_effect=fake_run_unreadable),
        patch.object(Path, "read_text", fail_vtt),
    ):
        assert _yt_dlp_captions("https://youtu.be/x") == ""
    with patch.dict("sys.modules", {"ez_research.search": None}):
        records = ingest_paste("https://example.com/open", fetch_links=True)
    assert records
    assert records[0]["kind"] in {"skipped", "page"}
    ingest_paste(123, fetch_links="on")
    types = EZAudioLoopToMatch.INPUT_TYPES()
    assert "speech" in types["required"]


def test_digest_helpers_and_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_podcast.digest import (
        _as_bool,
        _close_writer,
        _complete,
        _ensure_lab_custom_nodes_path,
        fallback_digest,
        write_digest,
        write_script,
    )

    assert _as_bool(0) is False
    assert _as_bool("ON") is True
    assert _as_bool([]) is False
    assert "No usable sources" in fallback_digest([])
    empty_script = naive_script("   ", fmt=FORMAT_LECTURE, duration=DURATION_COMMUTE)
    assert "Paste sources" in empty_script
    punct = naive_script("...", fmt=FORMAT_EXPLAINER, duration=DURATION_COMMUTE)
    assert punct.startswith("Speaker A:")
    many = naive_script(
        " ".join(f"Word{i}." for i in range(800)),
        fmt=FORMAT_EXPLAINER,
        duration=DURATION_COMMUTE,
    )
    assert "Speaker A:" in many
    overflow = naive_script(
        ("alpha " * 400) + ". " + ("beta " * 80) + ".",
        fmt=FORMAT_EXPLAINER,
        duration=DURATION_COMMUTE,
    )
    assert "beta" not in overflow.lower()
    text, status = write_digest([], enhance=True)
    assert status == "no sources"
    with (
        patch.object(digest_mod, "_complete", return_value=("", "")),
        patch.object(digest_mod, "_close_writer"),
    ):
        script, st = write_script("", fmt=FORMAT_EXPLAINER, duration=DURATION_COMMUTE, enhance=True)
    assert st == "no digest"
    assert "Paste sources" in script
    with (
        patch.object(digest_mod, "_complete", return_value=("", "passthrough")),
        patch.object(digest_mod, "_close_writer"),
    ):
        script, st = write_script("Digest body.", fmt=FORMAT_EXPLAINER, duration=DURATION_COMMUTE, enhance=True)
    assert st == "passthrough"
    with (
        patch.object(
            digest_mod,
            "_complete",
            return_value=("Speaker A: Hi.", "GGUF missing"),
        ),
        patch.object(digest_mod, "_close_writer"),
    ):
        script, st = write_script(
            "Digest body.", fmt=FORMAT_EXPLAINER, duration=DURATION_COMMUTE, enhance=True
        )
    assert st == "GGUF missing"
    monkeypatch.setattr(sys, "path", [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()])
    _ensure_lab_custom_nodes_path()
    _ensure_lab_custom_nodes_path()
    with patch.dict("sys.modules", {"ez_prompt_enhance.client": None}):
        text, reason = _complete("sys", "user")
        assert text == ""
        assert "unavailable" in reason
        _close_writer()
    class Boom:
        @staticmethod
        def complete(*_a: object, **_k: object) -> tuple[str, str]:
            return "  hi  ", None  # type: ignore[return-value]

        @staticmethod
        def _close_llm() -> None:
            raise RuntimeError("close")

    fake = type("mod", (), {"complete": Boom.complete, "_close_llm": Boom._close_llm})
    with patch.dict("sys.modules", {"ez_prompt_enhance.client": fake}):
        text, reason = _complete("sys", "user")
        assert text == "hi"
        _close_writer()


def test_loop_pcm_shapes_and_trim() -> None:
    from ez_podcast.loop import _as_pcm, _sample_rate, _waveform, pack_audio

    class Blob:
        def detach(self) -> Blob:
            return self

        def cpu(self) -> Blob:
            return self

        def numpy(self) -> list[float]:
            raise RuntimeError("no numpy")

        def reshape(self, *_a: object) -> Blob:
            raise RuntimeError("no reshape")

    assert _as_pcm(None) == []
    assert _as_pcm(Blob()) == []
    assert _as_pcm(1.5) == [1.5]
    assert _as_pcm(object()) == []

    class Shaped:
        def reshape(self, *_a: object) -> Shaped:
            return self

        def tolist(self) -> list[float]:
            return [0.2, 0.4]

    assert _as_pcm(Shaped()) == [0.2, 0.4]
    assert _sample_rate("no") == 24000
    assert _sample_rate({"sample_rate": "bad"}) == 24000
    assert _sample_rate({"sample_rate": 0}) == 24000
    assert _waveform("no") is None
    speech = {"waveform": [[[0.1, 0.2]]], "sample_rate": 24000}
    bed = {"waveform": [[[9.0, 8.0, 7.0]]], "sample_rate": 24000}
    trimmed = loop_to_match(speech, bed)
    assert trimmed["waveform"][0][0] == [9.0, 8.0]
    packed = pack_audio([], 0)
    assert packed["sample_rate"] == 24000

    class FakeTensor:
        def __init__(self, data: object, ndim: int = 1) -> None:
            self._data = data
            self.ndim = ndim

        def unsqueeze(self, _dim: int) -> FakeTensor:
            return FakeTensor(self._data, self.ndim + 1)

    class FakeTorch:
        float32 = "float32"
        next_ndim = 1

        @staticmethod
        def as_tensor(body: object, dtype: object = None) -> FakeTensor:
            del dtype
            ndim = FakeTorch.next_ndim
            FakeTorch.next_ndim = 2
            return FakeTensor(body, ndim)

    with patch.dict("sys.modules", {"torch": FakeTorch()}):
        from ez_podcast import loop as loop_mod

        one = loop_mod.pack_audio([0.1, 0.2], 24000)
        assert one["sample_rate"] == 24000
        two = loop_mod.pack_audio([0.3, 0.4], 24000)
        assert two["sample_rate"] == 24000
