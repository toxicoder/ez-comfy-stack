"""Hermetic tests for the canonical ``ez_music`` timeline model.

The timeline is the one document every music exporter reads, so these tests
hold its wire contract: the constants a Standard MIDI File is written against,
the range checks that keep a note representable, the seconds-to-ticks maths of
:class:`TempoMap`, and the JSON form ``timeline.json`` carries.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_common.json_value import JsonObject  # noqa: E402
from ez_music.timeline import (  # noqa: E402
    DEFAULT_BPM,
    DRUMS_CHANNEL,
    NOTE_NAMES,
    PITCH_MAX,
    PITCH_MIN,
    PROGRAM_ACOUSTIC_GRAND_PIANO,
    PROGRAM_ELECTRIC_BASS,
    PROGRAM_LEAD_SYNTH,
    PROGRAM_STRINGS,
    TICKS_PER_QUARTER,
    VELOCITY_MAX,
    VELOCITY_MIN,
    KeySignature,
    Note,
    SourceInfo,
    TempoMap,
    TempoPoint,
    Timeline,
    Track,
)

TIMELINE_FORMAT = "ez-comfy-stack.timeline/1"
"""The format tag :meth:`Timeline.from_dict` accepts."""

QUARTER_TICKS = 480
"""Ticks in one quarter note at the default resolution."""


def _map(bpm: float = 120.0) -> TempoMap:
    """Build a fixed-tempo grid at the default resolution.

    Args:
        bpm: Tempo for the whole song.

    Returns:
        A single-mark tempo map.
    """
    return TempoMap.at_tempo(bpm)


def _note(
    pitch: int = 60,
    start_s: float = 0.0,
    duration_s: float = 1.0,
    velocity: int = 96,
) -> Note:
    """Build one note with permissive defaults.

    Args:
        pitch: MIDI note number.
        start_s: Attack time in seconds.
        duration_s: Sounding length in seconds.
        velocity: Attack strength.

    Returns:
        The note.
    """
    return Note(
        pitch=pitch, start_s=start_s, duration_s=duration_s, velocity=velocity
    )


def _track(
    name: str = "Lead",
    channel: int = 0,
    program: int | None = 80,
    notes: tuple[Note, ...] = (),
    is_drums: bool = False,
) -> Track:
    """Build one lane with permissive defaults.

    Args:
        name: Lane name.
        channel: MIDI channel.
        program: General MIDI program, or None.
        notes: Notes of the lane.
        is_drums: True for the percussion lane.

    Returns:
        The lane.
    """
    return Track(
        name=name, channel=channel, program=program, notes=notes, is_drums=is_drums
    )


def _source(bpm_hint: float | None = 120.0) -> SourceInfo:
    """Build a provenance record.

    Args:
        bpm_hint: Tempo the source claimed, or None.

    Returns:
        The provenance record.
    """
    return SourceInfo(
        path="/media/take.wav",
        duration_s=4.0,
        sample_rate=44100,
        artist="Nill Bye",
        title="Test Song",
        album="Singles",
        bpm_hint=bpm_hint,
    )


def _song(
    *,
    title: str = "Test Song",
    duration_s: float = 4.0,
    tempo_map: TempoMap | None = None,
    beats: tuple[float, ...] = (),
    tracks: tuple[Track, ...] = (),
    key: KeySignature | None = None,
    source: SourceInfo | None = None,
    confidence: float | None = None,
) -> Timeline:
    """Build a timeline over a fixed 120 BPM grid unless told otherwise.

    Args:
        title: Song name.
        duration_s: Length of the source in seconds.
        tempo_map: Tempo map, defaulting to a fixed 120 BPM.
        beats: Beat grid times in seconds.
        tracks: Lanes.
        key: Key signature, when one was estimated.
        source: Provenance of the source audio.
        confidence: Mean note-detection confidence.

    Returns:
        The timeline.
    """
    return Timeline(
        title=title,
        duration_s=duration_s,
        tempo_map=tempo_map if tempo_map is not None else _map(),
        beats=beats,
        tracks=tracks,
        key=key,
        source=source,
        confidence=confidence,
    )


def _document() -> JsonObject:
    """Build one complete ``timeline.json`` document.

    Returns:
        A document shaped like :meth:`Timeline.to_dict`, with every optional
        section filled in.
    """
    return {
        "format": TIMELINE_FORMAT,
        "title": "Test Song",
        "duration_s": 4.0,
        "tempo_map": {
            "ticks_per_quarter": TICKS_PER_QUARTER,
            "points": [
                {"time_s": 0.0, "bpm": 120.0},
                {"time_s": 2.0, "bpm": 96.0},
            ],
        },
        "beats": [0.0, 0.5, 1.0, 1.5],
        "key": {"key_number": 6, "major": True},
        "confidence": 0.75,
        "source": {
            "path": "/media/take.wav",
            "duration_s": 4.0,
            "sample_rate": 44100,
            "artist": "Nill Bye",
            "title": "Test Song",
            "album": "Singles",
            "bpm_hint": 120.0,
        },
        "tracks": [
            {
                "name": "Lead",
                "slug": "lead",
                "channel": 0,
                "program": 80,
                "is_drums": False,
                "notes": [
                    {"pitch": 60, "start_s": 0.0, "duration_s": 1.0, "velocity": 100}
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Module constants


def test_constants_match_the_wire_format() -> None:
    """The grid, tempo, range, and General MIDI constants are what the SMF
    header and the wire bytes are written against."""
    assert TICKS_PER_QUARTER == QUARTER_TICKS, "the header division is pinned"
    assert TICKS_PER_QUARTER % 3 == 0, "480 divides by 3 so tuplets survive"
    assert DEFAULT_BPM == 120.0, "an unmeasured song lands at a walking tempo"
    assert (PITCH_MIN, PITCH_MAX) == (0, 127), "MIDI note numbers are 7-bit"
    assert (VELOCITY_MIN, VELOCITY_MAX) == (1, 127), "velocity 0 means note-off"
    assert DRUMS_CHANNEL == 9, "channel 10 is the percussion lane"
    assert (
        PROGRAM_ACOUSTIC_GRAND_PIANO,
        PROGRAM_ELECTRIC_BASS,
        PROGRAM_STRINGS,
        PROGRAM_LEAD_SYNTH,
    ) == (0, 33, 48, 80), "the exporter defaults are General MIDI programs"
    assert len(NOTE_NAMES) == 12, "one name per semitone, sharp-of-C order"
    assert NOTE_NAMES[0] == "C" and NOTE_NAMES[6] == "F#"


# ---------------------------------------------------------------------------
# Note


def test_note_defaults_and_end_time() -> None:
    """A note defaults to a medium attack and reports its release time."""
    note = _note(pitch=60, start_s=0.5, duration_s=0.25)
    assert note.velocity == 96, "an unmeasured attack is medium strength"
    assert note.end_s == 0.75, "the release is attack plus sounding length"


def test_note_accepts_the_edges_of_the_wire_range() -> None:
    """The range checks are inclusive at both ends."""
    low = Note(pitch=PITCH_MIN, start_s=0.0, duration_s=0.001, velocity=VELOCITY_MIN)
    high = Note(pitch=PITCH_MAX, start_s=0.0, duration_s=0.001, velocity=VELOCITY_MAX)
    assert (low.pitch, low.velocity) == (0, 1)
    assert (high.pitch, high.velocity) == (127, 127)


def test_note_rejects_a_pitch_the_wire_cannot_carry() -> None:
    """A note number outside 0..127 cannot be encoded."""
    with pytest.raises(ValueError, match="pitch -1 outside 0..127"):
        _note(pitch=-1)
    with pytest.raises(ValueError, match="pitch 128 outside 0..127"):
        _note(pitch=128)


def test_note_rejects_a_velocity_the_wire_cannot_carry() -> None:
    """Velocity 0 is a note-off, so it is never a legal attack."""
    with pytest.raises(ValueError, match="velocity 0 outside 1..127"):
        _note(velocity=0)
    with pytest.raises(ValueError, match="velocity 128 outside 1..127"):
        _note(velocity=128)


def test_note_rejects_a_negative_attack_or_a_silent_length() -> None:
    """A note must start at or after the top of the song and sound."""
    with pytest.raises(ValueError, match="start_s is negative"):
        _note(start_s=-0.5)
    with pytest.raises(ValueError, match="duration_s must be positive, got 0.0"):
        _note(duration_s=0.0)
    with pytest.raises(ValueError, match="duration_s must be positive, got -1.0"):
        _note(duration_s=-1.0)


def test_note_to_dict_rounds_the_seconds_to_the_wire_precision() -> None:
    """The JSON form keeps four decimals, no more."""
    payload = Note(pitch=61, start_s=1.23456, duration_s=0.987654, velocity=7).to_dict()
    assert payload == {
        "pitch": 61,
        "start_s": 1.2346,
        "duration_s": 0.9877,
        "velocity": 7,
    }


def test_note_from_dict_defaults_the_missing_velocity() -> None:
    """A hand-written document may leave the attack out."""
    note = Note.from_dict({"pitch": 60, "start_s": 0.0, "duration_s": 2.0})
    assert note == _note(pitch=60, start_s=0.0, duration_s=2.0, velocity=96)
    explicit = Note.from_dict(
        {"pitch": 60, "start_s": 0.0, "duration_s": 2.0, "velocity": 33}
    )
    assert explicit.velocity == 33


def test_note_from_dict_rounds_a_fractional_pitch() -> None:
    """A pitch carried as a float is rounded to the nearest semitone."""
    note = Note.from_dict(
        {"pitch": 60.6, "start_s": 0.0, "duration_s": 1.0, "velocity": 96}
    )
    assert note.pitch == 61, "60.6 rounds up to the next semitone"


def test_note_from_dict_rejects_fields_that_are_not_numbers() -> None:
    """Every numeric field is required and must actually be a number."""
    with pytest.raises(ValueError, match="pitch must be a number, got None"):
        Note.from_dict({"start_s": 0.0, "duration_s": 1.0})
    with pytest.raises(ValueError, match="start_s must be a number, got 'now'"):
        Note.from_dict({"pitch": 60, "start_s": "now", "duration_s": 1.0})
    with pytest.raises(ValueError, match="duration_s must be a number"):
        Note.from_dict({"pitch": 60, "start_s": 0.0, "duration_s": []})
    with pytest.raises(ValueError, match="velocity must be a number, got True"):
        Note.from_dict(
            {"pitch": 60, "start_s": 0.0, "duration_s": 1.0, "velocity": True}
        )


# ---------------------------------------------------------------------------
# TempoPoint


def test_tempo_point_converts_to_microseconds_per_beat() -> None:
    """The MIDI meta payload is microseconds per quarter note."""
    assert TempoPoint(0.0, 120.0).microseconds_per_beat() == 500_000
    assert TempoPoint(0.0, 100.0).microseconds_per_beat() == 600_000


def test_tempo_point_rejects_an_unusable_mark() -> None:
    """Time runs forward and the tempo stays inside a playable range."""
    with pytest.raises(ValueError, match="time_s is negative: -0.5"):
        TempoPoint(-0.5, 120.0)
    with pytest.raises(ValueError, match="bpm 19.0 outside 20..300"):
        TempoPoint(0.0, 19.0)
    with pytest.raises(ValueError, match="bpm 301.0 outside 20..300"):
        TempoPoint(0.0, 301.0)
    assert TempoPoint(0.0, 20.0).bpm == 20.0, "the range is inclusive"
    assert TempoPoint(0.0, 300.0).bpm == 300.0, "the range is inclusive"


def test_tempo_point_json_round_trip() -> None:
    """The JSON form rounds and rebuilds to the same mark."""
    point = TempoPoint(1.23456, 123.45678)
    assert point.to_dict() == {"time_s": 1.2346, "bpm": 123.457}
    assert TempoPoint.from_dict(point.to_dict()) == TempoPoint(1.2346, 123.457)


def test_tempo_point_from_dict_requires_both_fields() -> None:
    """A mark without a time or a tempo is not a mark."""
    with pytest.raises(ValueError, match="time_s must be a number"):
        TempoPoint.from_dict({"bpm": 120.0})
    with pytest.raises(ValueError, match="bpm must be a number, got None"):
        TempoPoint.from_dict({"time_s": 0.0})


# ---------------------------------------------------------------------------
# TempoMap


def test_tempo_map_needs_a_point_and_a_real_grid() -> None:
    """An empty map has no tempo and a zero grid has no ticks."""
    with pytest.raises(ValueError, match="tempo map needs at least one point"):
        TempoMap(())
    with pytest.raises(ValueError, match="ticks_per_quarter must be >= 1, got 0"):
        TempoMap((TempoPoint(0.0, 120.0),), 0)


def test_tempo_map_must_start_at_the_top_of_the_song() -> None:
    """Without a mark at zero seconds there is no opening tempo."""
    with pytest.raises(ValueError, match="tempo map must start at time 0"):
        TempoMap((TempoPoint(0.5, 120.0),))


def test_tempo_map_sorts_marks_it_is_handed() -> None:
    """Marks arrive in any order and are held in time order."""
    tempo_map = TempoMap(
        (TempoPoint(4.0, 96.0), TempoPoint(0.0, 120.0)), QUARTER_TICKS
    )
    assert [point.time_s for point in tempo_map.points] == [0.0, 4.0]


def test_tempo_map_at_tempo_is_a_fixed_grid() -> None:
    """One mark converts seconds linearly."""
    tempo_map = TempoMap.at_tempo(120.0)
    assert tempo_map.ticks_per_quarter == QUARTER_TICKS
    assert tempo_map.to_ticks(0.5) == QUARTER_TICKS, "one beat at 120 BPM"
    assert tempo_map.to_ticks(1.0) == 2 * QUARTER_TICKS
    assert tempo_map.to_seconds(2 * QUARTER_TICKS) == 1.0


def test_tempo_map_scales_with_its_own_grid() -> None:
    """A caller may pick a coarser or finer resolution."""
    tempo_map = TempoMap.at_tempo(120.0, 96)
    assert tempo_map.to_ticks(0.5) == 96
    assert tempo_map.to_seconds(96) == 0.5


def test_tempo_map_integrates_a_mid_song_tempo_change() -> None:
    """Ticks accumulate at the tempo in force, so a later mark is slower."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)))
    assert tempo_map.to_ticks(4.0) == 3840, "eight beats at 120 BPM"
    assert tempo_map.to_ticks(5.0) == 4608, "1.6 beats at 96 BPM on top"
    assert tempo_map.to_seconds(3840) == 4.0
    assert tempo_map.to_seconds(4608) == 5.0, "the round trip is exact"


def test_to_ticks_stops_scanning_at_the_first_mark_in_the_future() -> None:
    """A time before a later mark converts against the earlier tempo."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)))
    assert tempo_map.to_ticks(0.5) == QUARTER_TICKS, "one beat at 120 BPM"
    assert tempo_map.to_ticks(1.0) == 960, "still on the 120 BPM segment"
    assert tempo_map.to_ticks(3.999) == 3839, "one tick short of the mark"


def test_bpm_at_reports_the_latest_mark_at_or_before_the_time() -> None:
    """Before the first mark the opening tempo still holds."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)))
    assert tempo_map.bpm_at(0.0) == 120.0
    assert tempo_map.bpm_at(3.999) == 120.0
    assert tempo_map.bpm_at(4.0) == 96.0, "the mark is inclusive of its own second"
    assert tempo_map.bpm_at(99.0) == 96.0
    assert tempo_map.bpm_at(-1.0) == 120.0, "a time before the top still has a tempo"


def test_to_ticks_clamps_anything_at_or_before_the_top() -> None:
    """No note attacks before tick zero."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)))
    assert tempo_map.to_ticks(0.0) == 0
    assert tempo_map.to_ticks(-12.0) == 0


def test_to_seconds_clamps_anything_at_or_before_tick_zero() -> None:
    """No note attacks before the top of the song."""
    tempo_map = _map()
    assert tempo_map.to_seconds(0) == 0.0
    assert tempo_map.to_seconds(-480) == 0.0


def test_to_seconds_returns_zero_when_no_origin_reaches_the_tick() -> None:
    """The scan answers zero when no segment origin is at or below the tick.

    A map built through :meth:`TempoMap.__init__` always has a zero origin, so
    the tail below the loop is only reachable with origins rewritten after
    construction; pinning it keeps the fallback honest.
    """
    tempo_map = _map()
    tempo_map._origins = (1_000_000.0,)
    assert tempo_map.to_seconds(480) == 0.0, "an unreachable tick maps to the top"


def test_tempo_map_json_round_trip() -> None:
    """The document carries the grid and every mark."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)), 240)
    document = tempo_map.to_dict()
    assert document == {
        "ticks_per_quarter": 240,
        "points": [{"time_s": 0.0, "bpm": 120.0}, {"time_s": 4.0, "bpm": 96.0}],
    }
    rebuilt = TempoMap.from_dict(document)
    assert rebuilt.ticks_per_quarter == 240
    assert rebuilt.points == tempo_map.points


def test_tempo_map_from_dict_defaults_the_grid() -> None:
    """A document that names no resolution gets the package default."""
    rebuilt = TempoMap.from_dict({"points": [{"time_s": 0.0, "bpm": 120.0}]})
    assert rebuilt.ticks_per_quarter == TICKS_PER_QUARTER


def test_tempo_map_from_dict_rejects_a_broken_point_list() -> None:
    """The marks must be a list of objects."""
    with pytest.raises(ValueError, match="points must be a list, got 'fast'"):
        TempoMap.from_dict({"points": "fast"})
    with pytest.raises(ValueError, match="points must hold objects, got 120"):
        TempoMap.from_dict({"points": [120]})
    with pytest.raises(ValueError, match="bpm must be a number"):
        TempoMap.from_dict({"points": [{"time_s": 0.0}]})


# ---------------------------------------------------------------------------
# KeySignature


def test_key_signature_rejects_a_key_the_meta_cannot_encode() -> None:
    """The meta event encodes 24 keys and no more."""
    with pytest.raises(ValueError, match="key_number -1 outside 0..23"):
        KeySignature(-1)
    with pytest.raises(ValueError, match="key_number 24 outside 0..23"):
        KeySignature(24)


def test_key_signature_names_both_modes() -> None:
    """Twelve majors then twelve minors, wrapped by semitone."""
    assert KeySignature(6).name == "F# major"
    assert KeySignature(0).name == "C major"
    assert KeySignature(23, major=False).name == "B minor"
    assert KeySignature(12, major=False).name == "C minor", "12 wraps to C"


def test_key_signature_json_round_trip_and_major_default() -> None:
    """A document that names no mode is read as major."""
    key = KeySignature(3, major=False)
    assert key.to_dict() == {"key_number": 3, "major": False}
    assert KeySignature.from_dict(key.to_dict()) == key
    assert KeySignature.from_dict({"key_number": 8}).major is True


def test_key_signature_from_dict_rejects_a_non_bool_mode() -> None:
    """The mode flag has to be a bool, not a string that looks like one."""
    with pytest.raises(ValueError, match="major must be a bool, got 'minor'"):
        KeySignature.from_dict({"key_number": 0, "major": "minor"})
    with pytest.raises(ValueError, match="key_number must be a number, got None"):
        KeySignature.from_dict({})


# ---------------------------------------------------------------------------
# Track


def test_track_rejects_a_blank_name() -> None:
    """The name becomes the track name, the stem file, and the part name."""
    with pytest.raises(ValueError, match="track name is blank"):
        _track(name="   ")
    with pytest.raises(ValueError, match="track name is blank"):
        _track(name="")


def test_track_rejects_an_off_range_channel_or_program() -> None:
    """Channels are 0..15 and programs are 7-bit."""
    with pytest.raises(ValueError, match="channel 16 outside 0..15"):
        _track(channel=16)
    with pytest.raises(ValueError, match="channel -1 outside 0..15"):
        _track(channel=-1)
    with pytest.raises(ValueError, match="program 128 outside 0..127"):
        _track(program=128)


def test_track_rejects_a_program_on_the_percussion_lane() -> None:
    """Channel 10 ignores program changes, so the lane must not claim one."""
    with pytest.raises(ValueError, match="drum track must not carry a program change"):
        _track(name="Kit", channel=DRUMS_CHANNEL, program=0, is_drums=True)


def test_track_slug_folds_punctuation_to_single_underscores() -> None:
    """The filename form is lowercase with one separator per run."""
    assert _track(name="Bass   Guitar!!").slug == "bass_guitar"
    assert _track(name="  Lead - Synth  ").slug == "lead_synth"
    assert _track(name="Strings").slug == "strings"


def test_track_slug_falls_back_when_the_name_has_no_letters() -> None:
    """A name of nothing but punctuation cannot name a file."""
    assert _track(name="!!!").slug == "track"


def test_track_note_counts_its_own_notes() -> None:
    """The lane reports how many notes it carries."""
    assert _track().note_count == 0
    assert _track(notes=(_note(), _note(pitch=64))).note_count == 2


def test_track_json_round_trip_keeps_the_optional_program() -> None:
    """The document carries the lane identity and its notes."""
    lane = _track(name="Bass", channel=1, program=33, notes=(_note(pitch=41),))
    document = lane.to_dict()
    assert document == {
        "name": "Bass",
        "slug": "bass",
        "channel": 1,
        "program": 33,
        "is_drums": False,
        "notes": [
            {"pitch": 41, "start_s": 0.0, "duration_s": 1.0, "velocity": 96}
        ],
    }
    assert Track.from_dict(document) == lane


def test_track_from_dict_fills_every_default() -> None:
    """A hand-written lane needs only a name and a channel."""
    lane = Track.from_dict({"name": "Pad", "channel": 2})
    assert lane == Track(name="Pad", channel=2, program=None, notes=(), is_drums=False)
    drums = Track.from_dict(
        {"name": "Kit", "channel": DRUMS_CHANNEL, "program": None, "is_drums": True}
    )
    assert drums.is_drums is True and drums.program is None


def test_track_from_dict_rejects_malformed_lanes() -> None:
    """A lane without a name, an off-range channel, or junk notes is rejected."""
    with pytest.raises(ValueError, match="name must be a string, got 7"):
        Track.from_dict({"name": 7, "channel": 0})
    with pytest.raises(ValueError, match="channel must be a number, got None"):
        Track.from_dict({"name": "Lead"})
    with pytest.raises(ValueError, match="notes must be a list, got 4"):
        Track.from_dict({"name": "Lead", "channel": 0, "notes": 4})
    with pytest.raises(ValueError, match="notes must hold objects, got 'C4'"):
        Track.from_dict({"name": "Lead", "channel": 0, "notes": ["C4"]})
    with pytest.raises(ValueError, match="is_drums must be a bool"):
        Track.from_dict({"name": "Lead", "channel": 0, "is_drums": 1})


# ---------------------------------------------------------------------------
# SourceInfo


def test_source_info_json_round_trip_keeps_the_bpm_hint() -> None:
    """Provenance carries the tags and the claimed tempo."""
    source = _source(bpm_hint=123.4567)
    document = source.to_dict()
    assert document == {
        "path": "/media/take.wav",
        "duration_s": 4.0,
        "sample_rate": 44100,
        "artist": "Nill Bye",
        "title": "Test Song",
        "album": "Singles",
        "bpm_hint": 123.457,
    }
    assert SourceInfo.from_dict(document) == _source(bpm_hint=123.457), (
        "the document keeps three decimals of the claimed tempo"
    )


def test_source_info_round_trips_without_a_bpm_hint() -> None:
    """A source that claimed no tempo stays unclaimed."""
    source = _source(bpm_hint=None)
    assert source.to_dict()["bpm_hint"] is None
    assert SourceInfo.from_dict(source.to_dict()) == source


def test_source_info_from_dict_fills_the_optional_tags() -> None:
    """Tags the file never carried read back as empty strings."""
    source = SourceInfo.from_dict(
        {"path": "/media/a.wav", "duration_s": 1.0, "sample_rate": 48000}
    )
    assert source == SourceInfo(
        path="/media/a.wav",
        duration_s=1.0,
        sample_rate=48000,
        artist="",
        title="",
        album="",
        bpm_hint=None,
    )


def test_source_info_from_dict_rejects_bad_fields() -> None:
    """Path is text, sample rate is a number, the hint is a number or null."""
    with pytest.raises(ValueError, match="path must be a string, got None"):
        SourceInfo.from_dict({"duration_s": 1.0, "sample_rate": 44100})
    with pytest.raises(ValueError, match="sample_rate must be a number"):
        SourceInfo.from_dict({"path": "/a.wav", "duration_s": 1.0})
    with pytest.raises(ValueError, match="artist must be a string, got 3"):
        SourceInfo.from_dict(
            {"path": "/a.wav", "duration_s": 1.0, "sample_rate": 1, "artist": 3}
        )
    with pytest.raises(ValueError, match="bpm_hint must be a number, got 'fast'"):
        SourceInfo.from_dict(
            {"path": "/a.wav", "duration_s": 1.0, "sample_rate": 1, "bpm_hint": "fast"}
        )


# ---------------------------------------------------------------------------
# Timeline


def test_timeline_rejects_a_blank_title() -> None:
    """The title is the score header and the MIDI text event."""
    with pytest.raises(ValueError, match="title is blank"):
        _song(title="  ")


def test_timeline_rejects_a_negative_duration() -> None:
    """A source cannot be shorter than nothing."""
    with pytest.raises(ValueError, match="duration_s is negative: -1.0"):
        _song(duration_s=-1.0)


def test_timeline_rejects_two_lanes_on_one_channel() -> None:
    """Two lanes sharing a channel would fight over one instrument."""
    with pytest.raises(ValueError, match="channel 0 used by two lanes"):
        _song(tracks=(_track(name="A", channel=0), _track(name="B", channel=0)))


def test_timeline_bpm_is_the_opening_tempo() -> None:
    """The song tempo the exporters report is the first mark."""
    tempo_map = TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0)))
    assert _song(tempo_map=tempo_map).bpm == 120.0


def test_timeline_note_count_sums_the_lanes() -> None:
    """The total is the sum over every lane, empty lanes included."""
    song = _song(
        tracks=(_track(notes=(_note(), _note(pitch=62))), _track(name="B", channel=1))
    )
    assert song.note_count == 2
    assert _song().note_count == 0


def test_end_beat_counts_the_grid_when_beats_exist() -> None:
    """With a measured grid the end beat is how many marks the song spans."""
    song = _song(
        duration_s=1.0,
        beats=(0.0, 0.5, 1.0, 1.5, 2.0),
        tracks=(_track(notes=(_note(start_s=0.0, duration_s=1.25),)),),
    )
    assert song.end_beat == 3.0, "the note ends inside the third beat"


def test_end_beat_falls_back_to_the_tempo_when_the_grid_is_empty() -> None:
    """Without a grid the end beat is seconds converted at the opening tempo."""
    assert _song(duration_s=2.0).end_beat == 4.0, "2 s at 120 BPM is four beats"
    late = _song(
        duration_s=1.0,
        tracks=(_track(notes=(_note(start_s=0.0, duration_s=3.0),)),),
    )
    assert late.end_beat == 6.0, "the latest note release wins over the duration"


def test_note_events_pairs_each_note_with_its_lane_in_time_order() -> None:
    """Notes come back sorted by attack, then pitch, across every lane."""
    early_low = _note(pitch=48, start_s=0.0, duration_s=0.5)
    early_high = _note(pitch=72, start_s=0.0, duration_s=0.5)
    later = _note(pitch=60, start_s=1.0, duration_s=0.5)
    a = _track(name="A", channel=0, notes=(later, early_high))
    b = _track(name="B", channel=1, program=None, notes=(early_low,))
    events = _song(tracks=(a, b)).note_events()
    assert [(track.name, note.pitch, note.start_s) for track, note in events] == [
        ("B", 48, 0.0),
        ("A", 72, 0.0),
        ("A", 60, 1.0),
    ], "attack time first, then pitch, whichever lane the note came from"


def test_timeline_json_round_trip_carries_every_section() -> None:
    """The document writes out and rebuilds into an equal song."""
    song = _song(
        beats=(0.0, 0.5),
        tracks=(_track(name="Lead", notes=(_note(),)),),
        key=KeySignature(6),
        source=_source(),
        confidence=0.876543,
    )
    document = song.to_dict()
    assert document["format"] == TIMELINE_FORMAT
    assert document["title"] == "Test Song"
    assert document["duration_s"] == 4.0
    assert document["beats"] == [0.0, 0.5]
    assert document["key"] == {"key_number": 6, "major": True}
    assert document["confidence"] == 0.8765
    assert document["source"] == _source().to_dict()
    assert document["tracks"] == [_track(name="Lead", notes=(_note(),)).to_dict()]

    rebuilt = Timeline.from_dict(document)
    assert rebuilt.title == song.title
    assert rebuilt.duration_s == song.duration_s
    assert rebuilt.beats == (0.0, 0.5)
    assert rebuilt.key == song.key
    assert rebuilt.source == song.source
    assert rebuilt.confidence == 0.8765
    assert rebuilt.tracks == song.tracks
    assert rebuilt.tempo_map.points == song.tempo_map.points


def test_timeline_json_round_trip_without_the_optional_sections() -> None:
    """A song with no key, no provenance, and no confidence still round trips."""
    song = _song()
    document = song.to_dict()
    assert document["key"] is None
    assert document["source"] is None
    assert document["confidence"] is None
    assert document["tempo_map"] == {
        "ticks_per_quarter": TICKS_PER_QUARTER,
        "points": [{"time_s": 0.0, "bpm": 120.0}],
    }
    rebuilt = Timeline.from_dict(document)
    assert (rebuilt.key, rebuilt.source, rebuilt.confidence) == (None, None, None)
    assert rebuilt.tracks == ()
    assert rebuilt.beats == ()


def test_timeline_from_dict_reads_a_full_document() -> None:
    """Every optional key present is read back into the model."""
    song = Timeline.from_dict(_document())
    assert song.title == "Test Song"
    assert song.beats == (0.0, 0.5, 1.0, 1.5)
    assert song.key == KeySignature(6)
    assert song.source == _source()
    assert song.confidence == 0.75
    assert song.note_count == 1
    assert song.tracks[0].slug == "lead", "the lane recomputes its own slug"


def test_timeline_from_dict_accepts_a_document_with_no_format_tag() -> None:
    """An untagged document is still this package's shape."""
    document = _document()
    document.pop("format")
    assert Timeline.from_dict(document).title == "Test Song"


def test_timeline_from_dict_rejects_a_document_it_does_not_write() -> None:
    """A foreign format tag means the file is not a timeline."""
    document = _document()
    document["format"] = "other/1"
    with pytest.raises(ValueError, match="unknown timeline format 'other/1'"):
        Timeline.from_dict(document)


def test_timeline_from_dict_requires_the_core_fields() -> None:
    """Title, duration, and the tempo map cannot be missing."""
    missing_title = _document()
    missing_title.pop("title")
    with pytest.raises(ValueError, match="title must be a string, got None"):
        Timeline.from_dict(missing_title)

    missing_duration = _document()
    missing_duration.pop("duration_s")
    with pytest.raises(ValueError, match="duration_s must be a number"):
        Timeline.from_dict(missing_duration)

    missing_tempo = _document()
    missing_tempo.pop("tempo_map")
    with pytest.raises(ValueError, match="tempo_map must be an object, got None"):
        Timeline.from_dict(missing_tempo)


def test_timeline_from_dict_rejects_malformed_optional_sections() -> None:
    """Each optional section is checked before it is rebuilt."""
    bad_key = _document()
    bad_key["key"] = "F# major"
    with pytest.raises(ValueError, match="key must be an object, got 'F# major'"):
        Timeline.from_dict(bad_key)

    bad_source = _document()
    bad_source["source"] = 3
    with pytest.raises(ValueError, match="source must be an object, got 3"):
        Timeline.from_dict(bad_source)

    bad_beats = _document()
    bad_beats["beats"] = "one two"
    with pytest.raises(ValueError, match="beats must be a list, got 'one two'"):
        Timeline.from_dict(bad_beats)

    junk_beat = _document()
    junk_beat["beats"] = [0.0, "off grid"]
    with pytest.raises(ValueError, match="beats must hold numbers, got 'off grid'"):
        Timeline.from_dict(junk_beat)

    flag_beat = _document()
    flag_beat["beats"] = [True]
    with pytest.raises(ValueError, match="beats must hold numbers, got True"):
        Timeline.from_dict(flag_beat)

    bad_confidence = _document()
    bad_confidence["confidence"] = "high"
    with pytest.raises(ValueError, match="confidence must be a number, got 'high'"):
        Timeline.from_dict(bad_confidence)

    empty_confidence = _document()
    empty_confidence["confidence"] = None
    assert Timeline.from_dict(empty_confidence).confidence is None

    bad_tracks = _document()
    bad_tracks["tracks"] = {"name": "Lead"}
    with pytest.raises(ValueError, match="tracks must be a list"):
        Timeline.from_dict(bad_tracks)
