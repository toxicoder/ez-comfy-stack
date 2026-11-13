"""Hermetic tests for the DAW hand-off bundle writer.

``ez_music.song_export`` shells out to ffprobe/ffmpeg and reads master tags
through mutagen. Both boundaries are faked here, so the suite pins exactly what
the module writes and raises without a host binary, a real master, or a GPU.
The masters this suite needs are a handful of frames written with ``wave``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import wave
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import cast

import mutagen
import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_common.json_value import Json, JsonObject  # noqa: E402
from ez_music import song_export  # noqa: E402
from ez_music.midi_file import (  # noqa: E402
    MidiEvent,
    ParsedTrack,
    note_rows,
    parse_midi,
    tempo_rows,
)
from ez_music.song_export import (  # noqa: E402
    AUDIO_DIR,
    BUNDLE_FORMAT,
    FALLBACK_SAMPLE_RATE,
    MANIFEST_NAME,
    PROJECT_NOTES_NAME,
    STEMS_DIR,
    STEM_HIGH_HZ,
    STEM_LOW_HZ,
    TIMELINE_NAME,
    ExportError,
    band_for_track,
    export_song,
    main,
    manifest_payload,
    probe_audio,
    project_notes,
    slugify,
    stem_file_name,
    write_bundle,
    write_stem_midi,
    write_stem_wav,
)
from ez_music.timeline import (  # noqa: E402
    KeySignature,
    Note,
    TempoMap,
    TempoPoint,
    Timeline,
    Track,
)
from ez_music.transcribe import AnalysisSettings  # noqa: E402

PROBE_OK = "duration=2.000000\nsample_rate=44100\n"
"""What ffprobe prints for a two-second master."""


class _TagFile:
    """Stand-in for the object mutagen hands back for a tagged master.

    Args:
        values: Tag name to the values a real file would report.
    """

    def __init__(self, values: dict[str, list[str]]) -> None:
        """Store the tags the fake reports.

        Args:
            values: Tag name to the list of values.
        """
        self._values: dict[str, Json] = {name: list(items) for name, items in values.items()}

    def get(self, key: str) -> Json | None:
        """Return one tag the way mutagen's easy interface does.

        Args:
            key: Tag name, already lowercased by the caller.
        Returns:
            The stored values, or None when the tag is absent.
        """
        return self._values.get(key)


def _midi_hz(pitch: int) -> float:
    """Return the frequency of one MIDI pitch.

    Args:
        pitch: MIDI note number.
    Returns:
        Frequency in hertz, equal-tempered against A440.
    """
    return float(440.0 * 2.0 ** ((pitch - 69) / 12.0))


def _tempo_map() -> TempoMap:
    """Return the fixed tempo map every fixture shares.

    Returns:
        A single-mark 120 BPM map at the repo's tick resolution.
    """
    return TempoMap((TempoPoint(0.0, 120.0),))


def _song(title: str = "Probe Song", *, key: KeySignature | None = KeySignature(7)) -> Timeline:
    """Build the hand-authored song every bundle test exports.

    Four lanes: a bass with a program, a lead lane with no program, a
    percussion lane, and an empty pad, so every lane row a guide or a manifest
    renders is exercised by one fixture.

    Args:
        title: Title to give the timeline.
        key: Key signature, or None for an unclassified song.
    Returns:
        A two-second timeline at 120 BPM.
    """
    return Timeline(
        title=title,
        duration_s=2.0,
        tempo_map=_tempo_map(),
        beats=(0.0, 0.5, 1.0, 1.5),
        tracks=(
            Track("Bass", 0, 33, (Note(36, 0.0, 0.45), Note(40, 0.5, 0.45))),
            Track("Lead Synth", 1, None, (Note(72, 0.25, 0.5, 110),)),
            Track("Drums", 9, None, (Note(36, 0.0, 0.1), Note(38, 0.5, 0.1)), is_drums=True),
            Track("Pad", 2, 89),
        ),
        key=key,
    )


def _write_wav(path: Path, frames: int = 16, rate: int = 8000) -> Path:
    """Write a tiny silent master so the module has a real file to copy.

    Args:
        path: Destination ``.wav`` path.
        frames: Number of samples to write.
        rate: Sample rate to put in the header.
    Returns:
        The path written.
    """
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(2 * frames))
    return path


def _process(
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    """Build the result a fake subprocess hands back.

    Args:
        returncode: Exit status to report.
        stdout: Text the command printed.
        stderr: Text the command complained about.
    Returns:
        A CompletedProcess carrying those three fields.
    """
    return subprocess.CompletedProcess(["media"], returncode, stdout, stderr)


def _media_run(
    calls: list[list[str]],
    *,
    probe: subprocess.CompletedProcess[str] | None = None,
    stem_returncode: int = 0,
    stem_stderr: str = "",
) -> Callable[..., subprocess.CompletedProcess[str]]:
    """Stand in for the host ffprobe and ffmpeg binaries.

    Args:
        calls: Every argv the module invoked, appended in call order.
        probe: Answer for an ffprobe call; defaults to a good two-second probe.
        stem_returncode: Exit status ffmpeg reports for a stem render.
        stem_stderr: Text ffmpeg writes on stderr.
    Returns:
        A callable shaped like subprocess.run.
    """

    def _run(command: Sequence[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        """Answer one ffmpeg or ffprobe invocation.

        Args:
            command: argv the module built.
            **_kwargs: The keyword arguments subprocess.run would have taken.
        Returns:
            The scripted result for whichever binary was called.
        """
        argv = [str(part) for part in command]
        calls.append(argv)
        if argv[0] == "ffprobe":
            return probe if probe is not None else _process(stdout=PROBE_OK)
        if stem_returncode == 0:
            _write_wav(Path(argv[-1]))
        return _process(returncode=stem_returncode, stderr=stem_stderr)

    return _run


def _run_that_raises(
    calls: list[list[str]],
    error: BaseException,
) -> Callable[..., subprocess.CompletedProcess[str]]:
    """Stand in for a media binary that never returns.

    Args:
        calls: Every argv the module invoked, appended in call order.
        error: Exception to raise in place of a completed process.
    Returns:
        A callable shaped like subprocess.run.
    """

    def _run(command: Sequence[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        """Record the argv and raise.

        Args:
            command: argv the module built.
            **_kwargs: The keyword arguments subprocess.run would have taken.
        Returns:
            Nothing; this callable always raises.
        Raises:
            BaseException: always, carrying the scripted error.
        """
        calls.append([str(part) for part in command])
        raise error

    return _run


def _rows(value: Json) -> list[JsonObject]:
    """Narrow a JSON value to a list of objects.

    Args:
        value: Value read out of a manifest or timeline document.
    Returns:
        The value as a list of mappings.
    Raises:
        AssertionError: the value is not a list of objects.
    """
    assert isinstance(value, list)
    out: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        out.append(item)
    return out


def _read_json(path: Path) -> JsonObject:
    """Read one JSON document the bundle wrote.

    Args:
        path: File to parse.
    Returns:
        The parsed document.
    Raises:
        AssertionError: the document is not a JSON object.
    """
    document: Json = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _wire_export(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tags: _TagFile | None,
    song: Timeline | None = None,
) -> tuple[list[list[str]], list[tuple[str, str, bool]]]:
    """Fake every boundary ``export_song`` crosses.

    Args:
        monkeypatch: Fixture that reverts every attribute this swaps.
        tags: Tag object mutagen reports, or None for an untagged master.
        song: Timeline the transcriber returns; defaults to the shared song.
    Returns:
        The recorded media argv list and the recorded transcriber calls.
    """
    calls: list[list[str]] = []
    seen: list[tuple[str, str, bool]] = []
    template = _song() if song is None else song

    def _transcribe(
        audio_path: str,
        title: str,
        settings: AnalysisSettings,
    ) -> Timeline:
        """Echo the title it was handed back into a timeline.

        Args:
            audio_path: Master the module is converting.
            title: Title the module settled on for the song.
            settings: Analysis knobs the module was asked to use.
        Returns:
            The fixture timeline carrying that title.
        """
        assert audio_path
        seen.append((audio_path, title, settings.quantize))
        return Timeline(
            title=title,
            duration_s=template.duration_s,
            tempo_map=template.tempo_map,
            beats=template.beats,
            tracks=template.tracks,
            key=template.key,
            confidence=template.confidence,
        )

    def _tag_file(path: str, *, easy: bool = False) -> _TagFile | None:
        """Report the scripted tags for one master.

        Args:
            path: Master mutagen was asked to open.
            easy: Whether the caller asked for the easy tag interface.
        Returns:
            The scripted tag object, or None when the master is untagged.
        """
        assert path
        assert easy
        return tags

    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    monkeypatch.setattr(mutagen, "File", _tag_file)
    monkeypatch.setattr(song_export, "transcribe", _transcribe)
    return calls, seen


# --- slugify ----------------------------------------------------------------


def test_slugify_folds_a_title_to_words() -> None:
    assert slugify("Neon Skyline, Part 2!") == "neon_skyline_part_2"
    assert slugify("__Boom__  Box__") == "boom_box"


def test_slugify_strips_leading_and_trailing_separators() -> None:
    assert slugify("  -- Hello   World!! --  ") == "hello_world"


def test_slugify_rejects_a_title_with_nothing_alphanumeric() -> None:
    with pytest.raises(ValueError, match="no filename-safe characters"):
        slugify(" /// --- !!! ")


# --- stem_file_name ---------------------------------------------------------


def test_stem_file_name_zero_pads_the_lane_order() -> None:
    assert stem_file_name(0, Track("Bass", 0, 33)) == "01-bass"
    assert stem_file_name(9, Track("Lead Synth", 1)) == "10-lead_synth"
    assert stem_file_name(11, Track("FX!!", 2)) == "12-fx"


# --- probe_audio ------------------------------------------------------------


def test_probe_audio_reads_the_duration_and_the_sample_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    reply = _process(stdout="duration=2.500000\nsample_rate=48000\nmetadata=\nduration=\n")
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls, probe=reply))
    duration, sample_rate = probe_audio("/tmp/master.wav")
    assert duration == 2.5
    assert sample_rate == 48000, "the probed rate is the master's own rate"
    assert calls[0][0] == "ffprobe"
    assert calls[0][-1] == "/tmp/master.wav"


def test_probe_audio_falls_back_on_an_unusable_sample_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing, zero, or junk rate leaves the bundle's own default."""
    for stdout in (
        "duration=1.000000\n",
        "duration=1.000000\nsample_rate=0\n",
        "duration=1.000000\nsample_rate=not-a-rate\n",
    ):
        calls: list[list[str]] = []
        reply = _process(stdout=stdout)
        monkeypatch.setattr(
            song_export.subprocess, "run", _media_run(calls, probe=reply)
        )
        duration, sample_rate = probe_audio("/tmp/master.wav")
        assert duration == 1.0
        assert sample_rate == FALLBACK_SAMPLE_RATE, stdout


def test_probe_audio_reports_the_last_stderr_line_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    reply = _process(returncode=1, stderr="moar noise\nmoar data: Invalid data found")
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls, probe=reply))
    with pytest.raises(ExportError, match="Invalid data found") as caught:
        probe_audio("/tmp/bad.wav")
    assert "/tmp/bad.wav" in str(caught.value)


def test_probe_audio_reports_the_exit_code_when_stderr_is_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        song_export.subprocess, "run", _media_run(calls, probe=_process(returncode=3))
    )
    with pytest.raises(ExportError, match="exit 3"):
        probe_audio("/tmp/bad.wav")


def test_probe_audio_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    error = subprocess.TimeoutExpired("ffprobe", 30)
    monkeypatch.setattr(song_export.subprocess, "run", _run_that_raises(calls, error))
    with pytest.raises(ExportError, match="ffprobe timed out"):
        probe_audio("/tmp/stuck.wav")
    assert calls[0][0] == "ffprobe"


def test_probe_audio_rejects_an_unusable_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for stdout in ("duration=N/A\n", "duration=0\n", "duration=-1.5\n", "sample_rate=44100\n"):
        calls: list[list[str]] = []
        monkeypatch.setattr(
            song_export.subprocess, "run", _media_run(calls, probe=_process(stdout=stdout))
        )
        with pytest.raises(ExportError, match="reported no duration"):
            probe_audio("/tmp/odd.wav")


# --- band_for_track ---------------------------------------------------------


def test_band_for_track_uses_the_lane_own_note_range() -> None:
    low, high = band_for_track(Track("Bass", 0, 33, (Note(36, 0.0, 0.5), Note(40, 0.5, 0.5))))
    assert low == pytest.approx(_midi_hz(33) / 1.6)
    assert high == pytest.approx(_midi_hz(43) * 1.6)


def test_band_for_track_gives_an_empty_lane_the_audible_range() -> None:
    assert band_for_track(Track("Pad", 2, 89)) == (STEM_LOW_HZ, STEM_HIGH_HZ)


def test_band_for_track_clamps_a_low_lane_to_the_audible_floor() -> None:
    low, high = band_for_track(Track("Sub", 0, None, (Note(0, 0.0, 0.5), Note(2, 0.5, 0.5))))
    assert low == STEM_LOW_HZ
    assert high == low + 20.0


def test_band_for_track_clamps_a_high_lane_to_the_audible_ceiling() -> None:
    low, high = band_for_track(Track("Air", 1, 80, (Note(125, 0.0, 0.5), Note(127, 0.5, 0.5))))
    assert low == pytest.approx(_midi_hz(122) / 1.6)
    assert high == STEM_HIGH_HZ


def test_band_for_track_keeps_a_minimum_band_width() -> None:
    low, high = band_for_track(Track("Sub", 0, None, (Note(12, 0.0, 0.5),)))
    assert (low, high) == (STEM_LOW_HZ, 40.0)
    assert high - low == 20.0


# --- write_stem_midi --------------------------------------------------------


def test_write_stem_midi_writes_the_solo_lane_alone(tmp_path: Path) -> None:
    song = _song()
    destination = tmp_path / "01-bass.mid"
    size = write_stem_midi(song, song.tracks[0], str(destination))
    assert size == destination.stat().st_size
    parsed = parse_midi(destination.read_bytes())
    assert len(parsed) == 2
    conductor, lane = parsed
    assert lane.name == "Bass"
    assert [row[1] for row in note_rows(lane)] == [36, 40]
    assert all(row[1] not in (72,) for row in note_rows(lane))
    assert tempo_rows(conductor) == [(0, 120.0)]


def _program_events(lane: ParsedTrack) -> list[MidiEvent]:
    """Return the program-change events of one parsed lane track.

    Args:
        lane: Parsed single-lane MIDI track.
    Returns:
        Voice events whose status high nibble is a program change.
    """
    return [
        event
        for event in lane.events
        if event.kind == "voice" and (event.status & 0xF0) == 0xC0
    ]


def test_write_stem_midi_keeps_the_lane_program_and_channel(tmp_path: Path) -> None:
    song = _song()
    destination = tmp_path / "04-pad.mid"
    write_stem_midi(song, song.tracks[3], str(destination))
    lane = parse_midi(destination.read_bytes())[1]
    assert [(event.data1, event.channel) for event in _program_events(lane)] == [(89, 2)]


def test_write_stem_midi_leaves_a_program_less_lane_alone(tmp_path: Path) -> None:
    song = _song()
    destination = tmp_path / "02-lead_synth.mid"
    write_stem_midi(song, song.tracks[1], str(destination))
    lane = parse_midi(destination.read_bytes())[1]
    assert _program_events(lane) == []
    assert lane.name == "Lead Synth"


# --- write_stem_wav ---------------------------------------------------------


def test_write_stem_wav_filters_to_the_lane_band_and_returns_the_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    master = _write_wav(tmp_path / "master.wav")
    destination = tmp_path / "01-bass.wav"
    lane = Track("Bass", 0, 33, (Note(36, 0.0, 0.5),))
    size = write_stem_wav(str(master), lane, str(destination))
    assert size == destination.stat().st_size
    assert size > 0
    assert calls[0][0] == "ffmpeg"
    assert calls[0][calls[0].index("-i") + 1] == str(master)
    low, high = band_for_track(lane)
    assert calls[0][calls[0].index("-af") + 1] == f"highpass=f={low:.1f},lowpass=f={high:.1f}"
    assert calls[0][-1] == str(destination)


def test_write_stem_wav_reports_the_last_stderr_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        song_export.subprocess,
        "run",
        _media_run(calls, stem_returncode=1, stem_stderr="first line\nno filter registered"),
    )
    with pytest.raises(ExportError, match="no filter registered"):
        write_stem_wav(str(_write_wav(tmp_path / "m.wav")), Track("B", 0), str(tmp_path / "s.wav"))


def test_write_stem_wav_reports_the_exit_code_when_stderr_is_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls, stem_returncode=2))
    with pytest.raises(ExportError, match="exit 2"):
        write_stem_wav(str(_write_wav(tmp_path / "m.wav")), Track("B", 0), str(tmp_path / "s.wav"))


def test_write_stem_wav_times_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    error = subprocess.TimeoutExpired("ffmpeg", 120)
    monkeypatch.setattr(song_export.subprocess, "run", _run_that_raises(calls, error))
    with pytest.raises(ExportError, match="timed out rendering stem"):
        write_stem_wav(str(_write_wav(tmp_path / "m.wav")), Track("B", 0), str(tmp_path / "s.wav"))


# --- project_notes ----------------------------------------------------------


def test_project_notes_carries_the_session_lanes_and_files() -> None:
    song = _song()
    text = project_notes(song, ("probe_song.mid", f"{STEMS_DIR}/01-bass.wav"))
    assert "# Probe Song" in text
    assert "- Tempo: 120.0 BPM" in text
    assert "- Key: G major" in text
    assert "- Notes: 5 across 4 lanes" in text
    for row in (
        "| Bass | 0 | 33 | 2 | melodic |",
        "| Lead Synth | 1 | - | 1 | melodic |",
        "| Drums | 9 | - | 2 | drum map |",
        "| Pad | 2 | 89 | 0 | melodic |",
    ):
        assert row in text
    assert "- `probe_song.mid`" in text
    assert f"- `{STEMS_DIR}/01-bass.wav`" in text
    for daw, _ in song_export._DAW_NOTES:
        assert f"### {daw}" in text
    assert "## What to fix by hand" in text
    assert f"`{TIMELINE_NAME}`" in text


def test_project_notes_calls_an_unclassified_key_unclassified() -> None:
    text = project_notes(_song(key=None), ())
    assert "- Key: unclassified" in text
    assert "## Files" in text


# --- manifest_payload -------------------------------------------------------


def test_manifest_payload_sorts_digests_and_records_lanes() -> None:
    digests = {f"{STEMS_DIR}/b.wav": "bb", "probe_song.mid": "aa", "a.mid": "cc"}
    payload = manifest_payload(_song(), "probe_song", digests, source_audio="/media/master.wav")
    assert payload["format"] == BUNDLE_FORMAT
    assert payload["slug"] == "probe_song"
    assert payload["title"] == "Probe Song"
    assert payload["bpm"] == 120.0
    assert payload["key"] == "G major"
    assert payload["duration_s"] == 2.0
    assert payload["ticks_per_quarter"] == 480
    assert payload["note_count"] == 5
    assert payload["source_audio"] == "master.wav"
    assert [entry["path"] for entry in _rows(payload["files"])] == [
        "a.mid",
        "probe_song.mid",
        f"{STEMS_DIR}/b.wav",
    ]
    assert [entry["sha256"] for entry in _rows(payload["files"])] == ["cc", "aa", "bb"]
    lanes = _rows(payload["lanes"])
    assert [lane["name"] for lane in lanes] == ["Bass", "Lead Synth", "Drums", "Pad"]
    assert [lane["program"] for lane in lanes] == [33, -1, -1, 89]
    assert [lane["notes"] for lane in lanes] == [2, 1, 2, 0]
    assert [lane["drums"] for lane in lanes] == [False, False, True, False]


def test_manifest_payload_omits_source_audio_and_blanks_an_unknown_key() -> None:
    payload = manifest_payload(_song(key=None), "probe_song", {}, source_audio=None)
    assert "source_audio" not in payload
    assert payload["key"] == ""
    assert payload["files"] == []
    assert [lane["name"] for lane in _rows(payload["lanes"])] == [
        "Bass",
        "Lead Synth",
        "Drums",
        "Pad",
    ]


# --- write_bundle -----------------------------------------------------------


def test_write_bundle_writes_every_declared_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    master = _write_wav(tmp_path / "Probe Song.wav")
    result = write_bundle(_song(), str(tmp_path / "out"), source_audio=str(master))
    assert result.slug == "probe_song"
    assert result.title == "Probe Song"
    assert result.lanes == ("Bass", "Lead Synth", "Drums", "Pad")
    assert result.note_count == 5
    assert result.bpm == 120.0
    assert result.key_name == "G major"
    assert result.duration_s == 2.0
    assert Path(result.directory) == (tmp_path / "out" / "probe_song").resolve()
    assert result.files == (
        "probe_song.mid",
        "probe_song.musicxml",
        TIMELINE_NAME,
        f"{STEMS_DIR}/01-bass.mid",
        f"{STEMS_DIR}/02-lead_synth.mid",
        f"{STEMS_DIR}/03-drums.mid",
        f"{STEMS_DIR}/04-pad.mid",
        f"{AUDIO_DIR}/Probe Song.wav",
        f"{STEMS_DIR}/01-bass.wav",
        f"{STEMS_DIR}/02-lead_synth.wav",
        f"{STEMS_DIR}/03-drums.wav",
        f"{STEMS_DIR}/04-pad.wav",
        PROJECT_NOTES_NAME,
        MANIFEST_NAME,
    )
    for relative in result.files:
        assert Path(result.path(relative)).is_file()
    assert len(calls) == 4
    assert [call[0] for call in calls] == ["ffmpeg"] * 4


def test_write_bundle_digests_match_the_files_on_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    master = _write_wav(tmp_path / "master.wav")
    result = write_bundle(_song(), str(tmp_path / "out"), source_audio=str(master))
    manifest = _read_json(Path(result.path(MANIFEST_NAME)))
    entries = _rows(manifest["files"])
    assert [str(entry["path"]) for entry in entries] == sorted(
        relative for relative in result.files if relative != MANIFEST_NAME
    )
    for entry in entries:
        path = entry["path"]
        assert isinstance(path, str)
        digest = entry["sha256"]
        assert isinstance(digest, str)
        on_disk = hashlib.sha256(Path(result.path(path)).read_bytes()).hexdigest()
        assert digest == on_disk


def test_write_bundle_copies_the_master_and_the_timeline_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    master = _write_wav(tmp_path / "master.wav", frames=24, rate=8000)
    result = write_bundle(_song(), str(tmp_path / "out"), source_audio=str(master))
    copied = Path(result.path(f"{AUDIO_DIR}/master.wav"))
    assert copied.read_bytes() == master.read_bytes()
    document = _read_json(Path(result.path(TIMELINE_NAME)))
    assert document["title"] == "Probe Song"
    assert [str(track["name"]) for track in _rows(document["tracks"])] == [
        "Bass",
        "Lead Synth",
        "Drums",
        "Pad",
    ]


def test_write_bundle_is_idempotent_over_the_same_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    master = _write_wav(tmp_path / "master.wav")
    out_dir = str(tmp_path / "out")
    first = write_bundle(_song(), out_dir, source_audio=str(master))
    snapshot = {relative: Path(first.path(relative)).read_bytes() for relative in first.files}
    again = write_bundle(_song(), out_dir, source_audio=str(master))
    assert again.files == first.files
    assert again.directory == first.directory
    for relative, blob in snapshot.items():
        assert Path(again.path(relative)).read_bytes() == blob


def test_write_bundle_overrides_the_title_for_file_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(song_export.subprocess, "run", _media_run(calls))
    result = write_bundle(_song(), str(tmp_path / "out"), title="B-Side #3!")
    assert result.slug == "b_side_3"
    assert result.title == "B-Side #3!"
    assert Path(result.path("b_side_3.mid")).is_file()
    assert result.files[0] == "b_side_3.mid"
    assert calls == []


def test_write_bundle_without_a_master_skips_audio_and_stems(tmp_path: Path) -> None:
    result = write_bundle(_song(key=None), str(tmp_path / "out"), beats_per_bar=3)
    assert not any(relative.startswith(f"{AUDIO_DIR}/") for relative in result.files)
    assert not any(relative.endswith(".wav") for relative in result.files)
    assert not (Path(result.directory) / AUDIO_DIR).exists()
    assert result.key_name == ""
    manifest = _read_json(Path(result.path(MANIFEST_NAME)))
    assert "source_audio" not in manifest
    assert [entry["path"] for entry in _rows(manifest["files"])] == sorted(
        name for name in result.files if name != MANIFEST_NAME
    )


# --- export_song ------------------------------------------------------------


def test_export_song_rejects_a_missing_master(tmp_path: Path) -> None:
    with pytest.raises(ExportError, match="no such audio file"):
        export_song(str(tmp_path / "gone.wav"), str(tmp_path / "out"))


def test_export_song_prefers_an_explicit_title(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls, seen = _wire_export(monkeypatch, tags=_TagFile({"title": ["Tagged Name"]}))
    master = _write_wav(tmp_path / "master.wav")
    result = export_song(str(master), str(tmp_path / "out"), title="Hit Single")
    assert result.slug == "hit_single"
    assert seen == [(str(master), "Hit Single", True)]
    assert calls[0][0] == "ffprobe"
    manifest = _read_json(Path(result.path(MANIFEST_NAME)))
    assert manifest["source_audio"] == "master.wav"


def test_export_song_falls_back_to_the_title_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tags = _TagFile({"artist": ["Some Artist"], "title": ["Tagged  Name!"], "album": ["Al"]})
    _wire_export(monkeypatch, tags=tags)
    master = _write_wav(tmp_path / "master.wav")
    result = export_song(str(master), str(tmp_path / "out"))
    assert result.slug == "tagged_name"
    assert result.title == "Tagged  Name!"
    document = _read_json(Path(result.path(TIMELINE_NAME)))
    source = document["source"]
    assert isinstance(source, dict)
    assert source["artist"] == "Some Artist"
    assert source["title"] == "Tagged  Name!"
    assert source["album"] == "Al"
    assert source["sample_rate"] == FALLBACK_SAMPLE_RATE
    assert source["duration_s"] == 2.0


def test_export_song_falls_back_to_the_file_name_stem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _wire_export(monkeypatch, tags=None)
    master = _write_wav(tmp_path / "Midnight Drive.wav")
    result = export_song(str(master), str(tmp_path / "out"))
    assert result.slug == "midnight_drive"
    document = _read_json(Path(result.path(TIMELINE_NAME)))
    source = document["source"]
    assert isinstance(source, dict)
    assert source["title"] == ""
    assert source["path"] == str(master)


def test_export_song_survives_a_tag_reader_that_blows_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls, seen = _wire_export(monkeypatch, tags=_TagFile({}))

    def _boom(path: str, *, easy: bool = False) -> _TagFile | None:
        """Refuse every tag read.

        Args:
            path: Master mutagen was asked to open.
            easy: Whether the caller asked for the easy tag interface.
        Returns:
            Nothing; this callable always raises.
        Raises:
            RuntimeError: always, standing in for a corrupt tag block.
        """
        raise RuntimeError("corrupt tag block")

    monkeypatch.setattr(mutagen, "File", _boom)
    master = _write_wav(tmp_path / "rescue_me.wav")
    result = export_song(str(master), str(tmp_path / "out"))
    assert result.slug == "rescue_me"
    assert seen[0][1] == "rescue_me"
    assert calls[0][0] == "ffprobe"


def test_export_song_without_stems_skips_the_wavs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls, _seen = _wire_export(monkeypatch, tags=None)
    master = _write_wav(tmp_path / "master.wav")
    result = export_song(str(master), str(tmp_path / "out"), with_stems=False)
    assert not any(relative.endswith(".wav") for relative in result.files)
    assert [call[0] for call in calls] == ["ffprobe"]
    manifest = _read_json(Path(result.path(MANIFEST_NAME)))
    assert "source_audio" not in manifest


def test_export_song_honours_the_analysis_and_bar_knobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _calls, seen = _wire_export(monkeypatch, tags=None)
    master = _write_wav(tmp_path / "master.wav")
    export_song(
        str(master),
        str(tmp_path / "out"),
        settings=AnalysisSettings(quantize=False),
        beats_per_bar=3,
    )
    assert seen[0][2] is False


# --- main -------------------------------------------------------------------


def test_main_writes_a_bundle_and_reports_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _calls, seen = _wire_export(monkeypatch, tags=_TagFile({"title": ["Ignored"]}))
    master = _write_wav(tmp_path / "master.wav")
    code = main(
        [
            str(master),
            str(tmp_path / "out"),
            "--title",
            "Live Take",
            "--beats-per-bar",
            "3",
            "--no-quantize",
        ]
    )
    assert code == 0
    assert seen[0][2] is False
    printed = capsys.readouterr().out
    assert f"bundle {Path(tmp_path / 'out' / 'live_take').resolve()}" in printed
    assert "  title   Live Take" in printed
    assert "  tempo   120.0 BPM    key G major" in printed
    assert "  length  2.00 s   notes 5" in printed
    assert "  lanes   Bass, Lead Synth, Drums, Pad" in printed
    assert f"    {STEMS_DIR}/01-bass.wav" in printed
    assert f"    {AUDIO_DIR}/master.wav" in printed
    assert f"    {MANIFEST_NAME}" in printed


def test_main_skips_stems_when_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _calls, seen = _wire_export(monkeypatch, tags=None)
    master = _write_wav(tmp_path / "master.wav")
    code = main([str(master), str(tmp_path / "out"), "--no-stems"])
    assert code == 0
    assert seen[0][2] is True
    printed = capsys.readouterr().out
    assert ".wav" not in printed
    assert not (tmp_path / "out" / "master" / AUDIO_DIR).exists()
    assert (tmp_path / "out" / "master" / STEMS_DIR / "01-bass.mid").is_file()


def test_main_reports_a_bad_path_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([str(tmp_path / "missing.wav"), str(tmp_path / "out")])
    assert code == 1
    printed = capsys.readouterr().out
    assert printed.startswith("error:")
    assert "no such audio file" in printed


def test_main_reports_an_unsluggable_title(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _wire_export(monkeypatch, tags=None)
    master = _write_wav(tmp_path / "master.wav")
    code = main([str(master), str(tmp_path / "out"), "--title", "???"])
    assert code == 1
    printed = capsys.readouterr().out
    assert printed.startswith("error:")
    assert "no filename-safe characters" in printed


# --- tag helper -------------------------------------------------------------


def test_first_tag_takes_the_first_string_only() -> None:
    assert song_export._first_tag("solo") == "solo"
    assert song_export._first_tag(["first", "second"]) == "first"
    assert song_export._first_tag(cast(Json, ("only",))) == "only"
    assert song_export._first_tag([]) == ""
    assert song_export._first_tag([7]) == ""
    assert song_export._first_tag({"artist": "no"}) == ""
    assert song_export._first_tag(None) == ""


# --- result shape -----------------------------------------------------------


def test_export_result_path_joins_the_bundle_directory() -> None:
    result = song_export.ExportResult(
        directory="/bundles/probe_song",
        title="Probe Song",
        slug="probe_song",
        files=(MANIFEST_NAME,),
        lanes=("Bass",),
        note_count=2,
        bpm=120.0,
        key_name="G major",
        duration_s=2.0,
    )
    assert result.path(f"{STEMS_DIR}/01-bass.mid") == "/bundles/probe_song/stems/01-bass.mid"
    assert result.path(MANIFEST_NAME) == "/bundles/probe_song/manifest.json"
