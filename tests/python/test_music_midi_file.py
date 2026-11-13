"""Hermetic tests for the ``ez_music`` Standard MIDI File writer and parser.

The package carries its own wire format so the transcriber needs no third-party
MIDI library, which makes :func:`parse_midi` the only oracle available: every
assertion here is either a byte of the spec's own encoding table or an event
row read back out of the bytes :func:`midi_bytes` wrote. An external probe is
not a validator for these files, so the parser is the check.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.midi_file import (  # noqa: E402
    CC_PAN,
    CC_REVERB,
    CC_VOLUME,
    GM_RESET,
    META_COPYRIGHT,
    META_KEY_SIGNATURE,
    META_MARKER,
    META_TEMPO,
    META_TIME_SIGNATURE,
    META_TRACK_NAME,
    _MAX_DELTA,
    _conductor_events,
    _end_tick,
    _is_off,
    _key_payload,
    _lane_events,
    _meta_text,
    _sorted,
    _track_chunk,
    MidiEvent,
    ParsedTrack,
    build_tracks,
    decode_tempo,
    decode_time_signature,
    decode_vlq,
    encode_key_signature,
    encode_tempo,
    encode_time_signature,
    encode_vlq,
    midi_bytes,
    note_rows,
    parse_midi,
    tempo_rows,
    write_midi,
)
from ez_music.timeline import (  # noqa: E402
    DRUMS_CHANNEL,
    PROGRAM_LEAD_SYNTH,
    TICKS_PER_QUARTER,
    KeySignature,
    Note,
    SourceInfo,
    TempoMap,
    TempoPoint,
    Timeline,
    Track,
)

QUARTER_TICKS = TICKS_PER_QUARTER
"""Ticks per quarter note written into every header this module makes."""

MAX_DELTA = _MAX_DELTA
"""Largest delta time the format allows, spelled without the underscore."""

LEAD_NOTES: tuple[Note, ...] = (
    Note(pitch=60, start_s=0.0, duration_s=1.0, velocity=100),
    Note(pitch=64, start_s=1.0, duration_s=0.5, velocity=90),
    Note(pitch=67, start_s=4.0, duration_s=1.0, velocity=80),
)
"""Melodic lane of the round-trip song, in seconds."""

DRUM_NOTES: tuple[Note, ...] = (
    Note(pitch=36, start_s=0.0, duration_s=0.25, velocity=111),
    Note(pitch=38, start_s=0.5, duration_s=0.25, velocity=95),
    Note(pitch=42, start_s=5.0, duration_s=0.5, velocity=70),
)
"""Percussion lane of the round-trip song, in seconds."""

LEAD_ROWS: list[tuple[int, int, int, int]] = [
    (0, 60, 960, 100),
    (960, 64, 480, 90),
    (3840, 67, 768, 80),
]
"""What :func:`note_rows` must read back for :data:`LEAD_NOTES`."""

DRUM_ROWS: list[tuple[int, int, int, int]] = [
    (0, 36, 240, 111),
    (480, 38, 240, 95),
    (4608, 42, 384, 70),
]
"""What :func:`note_rows` must read back for :data:`DRUM_NOTES`."""


def _smf_bytes(
    tracks: list[bytes], format_id: int = 1, division: int = QUARTER_TICKS
) -> bytes:
    """Assemble a Standard MIDI File around ready-made track bodies.

    Args:
        tracks: One bytes object per track body, without the ``MTrk`` frame.
        format_id: File format written into the header.
        division: Tick division written into the header.

    Returns:
        Complete file bytes.
    """
    body = b"".join(
        b"MTrk" + struct.pack(">I", len(chunk)) + chunk for chunk in tracks
    )
    header = b"MThd" + struct.pack(">IHHH", 6, format_id, len(tracks), division)
    return header + body


def _song() -> Timeline:
    """Build the song the writer tests render.

    Returns:
        A three-track format-1 song: a conductor lane implied by the file, a
        melodic lane on channel 1, and a percussion lane on channel 10, over a
        120 BPM grid that drops to 96 BPM at four seconds.
    """
    return Timeline(
        title="Round Trip",
        duration_s=8.0,
        tempo_map=TempoMap((TempoPoint(0.0, 120.0), TempoPoint(4.0, 96.0))),
        beats=tuple(index * 0.5 for index in range(16)),
        tracks=(
            Track(
                name="Lead Synth",
                channel=0,
                program=PROGRAM_LEAD_SYNTH,
                notes=LEAD_NOTES,
            ),
            Track(name="Drums", channel=DRUMS_CHANNEL, is_drums=True, notes=DRUM_NOTES),
        ),
        key=KeySignature(6),
        source=SourceInfo(
            path="/media/take.wav",
            duration_s=8.0,
            sample_rate=44100,
            artist="Nill Bye",
            title="Round Trip",
            album="Singles",
            bpm_hint=120.0,
        ),
    )


def _events_of(
    parsed: ParsedTrack, kind: str, status: int | None = None
) -> list[MidiEvent]:
    """Pull one family of events out of a parsed track.

    Args:
        parsed: Track read back by :func:`parse_midi`.
        kind: Event family to keep.
        status: Status byte to keep, or None for every status of the family.

    Returns:
        The matching events in tick order.
    """
    return [
        event
        for event in parsed.events
        if event.kind == kind and (status is None or event.status == status)
    ]


# ---------------------------------------------------------------------------
# Constants


def test_constants_match_the_smf_spec() -> None:
    """The status bytes and control numbers are the ones the spec assigns."""
    assert GM_RESET == bytes((0x7E, 0x7F, 0x09, 0x01)), "the General MIDI on message"
    assert (CC_VOLUME, CC_PAN, CC_REVERB) == (7, 10, 91)
    assert META_TRACK_NAME == 0x03 and META_TEMPO == 0x51
    assert META_TIME_SIGNATURE == 0x58 and META_KEY_SIGNATURE == 0x59
    assert META_COPYRIGHT == 0x02 and META_MARKER == 0x06
    assert MAX_DELTA == 0x0FFFFFFF, "a delta is at most four septets"


# ---------------------------------------------------------------------------
# Variable-length quantities


def test_encode_vlq_matches_the_spec_examples() -> None:
    """Each width of the encoding is pinned against the spec's own values."""
    assert encode_vlq(0x00) == b"\x00"
    assert encode_vlq(0x40) == b"\x40"
    assert encode_vlq(0x7F) == b"\x7F"
    assert encode_vlq(0x80) == b"\x81\x00", "one hundred twenty-eight"
    assert encode_vlq(0x3FFF) == b"\xFF\x7F"
    assert encode_vlq(0x4000) == b"\x81\x80\x00", "the three-byte boundary"
    assert encode_vlq(0x7FFFFF) == b"\x83\xFF\xFF\x7F"
    assert encode_vlq(0x800000) == b"\x84\x80\x80\x00", "the four-byte boundary"
    assert encode_vlq(MAX_DELTA) == b"\xFF\xFF\xFF\x7F", "the widest legal delta"


def test_vlq_round_trips_every_width() -> None:
    """Every width encodes and decodes back to the value it started as."""
    for value in (0x00, 0x7F, 0x80, 0x3FFF, 0x4000, 0x7FFFFF, 0x800000, MAX_DELTA):
        encoded = encode_vlq(value)
        assert 1 <= len(encoded) <= 4, f"{value} needs one to four bytes"
        decoded, offset = decode_vlq(encoded, 0)
        assert decoded == value, f"{value} survives the round trip"
        assert offset == len(encoded), "the decoder stops just past the quantity"


def test_encode_vlq_rejects_values_the_format_cannot_hold() -> None:
    """A negative delta has no encoding and neither does a 29-bit one."""
    with pytest.raises(ValueError, match="VLQ cannot be negative: -1"):
        encode_vlq(-1)
    with pytest.raises(ValueError, match=f"VLQ {MAX_DELTA + 1} exceeds {MAX_DELTA}"):
        encode_vlq(MAX_DELTA + 1)


def test_decode_vlq_reads_at_an_offset_and_stops_early() -> None:
    """The decoder reads anywhere in a track buffer."""
    data = b"\x00\x81\x00"
    assert decode_vlq(data, 0) == (0, 1)
    assert decode_vlq(data, 1) == (128, 3), "the delta after the first one"


def test_decode_vlq_rejects_a_truncated_or_overlong_quantity() -> None:
    """A stream that ends mid-quantity, or runs past four bytes, is broken."""
    with pytest.raises(ValueError, match="ended inside a variable-length quantity"):
        decode_vlq(b"\x80", 0)
    with pytest.raises(ValueError, match="ended inside a variable-length quantity"):
        decode_vlq(b"\x00\x80", 1)
    with pytest.raises(ValueError, match="longer than four bytes"):
        decode_vlq(b"\xFF\xFF\xFF\xFF\x00", 0)


# ---------------------------------------------------------------------------
# Tempo, meter, and key payloads


def test_encode_tempo_writes_microseconds_per_beat() -> None:
    """The three-byte payload is big-endian microseconds."""
    assert encode_tempo(120.0) == b"\x07\xA1\x20", "500000 microseconds"
    assert encode_tempo(60.0) == b"\x0F\x42\x40", "1000000 microseconds"
    assert len(encode_tempo(96.0)) == 3, "always exactly three bytes"


def test_encode_tempo_never_writes_a_zero_payload() -> None:
    """A tempo fast enough to round to zero still writes one microsecond."""
    assert encode_tempo(60_000_000_000.0) == b"\x00\x00\x01"


def test_decode_tempo_round_trips_a_written_tempo() -> None:
    """Microseconds come back as the beats per minute that wrote them."""
    assert decode_tempo(encode_tempo(120.0)) == 120.0
    assert decode_tempo(encode_tempo(96.0)) == 96.0
    assert decode_tempo(bytes((0x07, 0xA1, 0x20))) == 120.0


def test_decode_tempo_rejects_a_payload_it_cannot_read() -> None:
    """The payload is exactly three bytes and never zero."""
    with pytest.raises(ValueError, match="tempo payload must be 3 bytes, got 2"):
        decode_tempo(b"\x07\xa1")
    with pytest.raises(ValueError, match="tempo payload must be 3 bytes, got 4"):
        decode_tempo(b"\x00\x07\xa1\x20")
    with pytest.raises(ValueError, match="tempo payload is zero"):
        decode_tempo(b"\x00\x00\x00")


def test_encode_time_signature_matches_the_meta_layout() -> None:
    """Numerator, log2 denominator, then the metronome defaults."""
    assert encode_time_signature(4, 4) == bytes((4, 2, 24, 8))
    assert encode_time_signature(3, 8) == bytes((3, 3, 24, 8))
    assert encode_time_signature(7, 16) == bytes((7, 4, 24, 8))
    assert encode_time_signature(1, 1) == bytes((1, 0, 24, 8))


def test_encode_time_signature_rejects_an_impossible_meter() -> None:
    """There is at least one beat and the beat value is a power of two."""
    with pytest.raises(ValueError, match="numerator must be >= 1, got 0"):
        encode_time_signature(0, 4)
    with pytest.raises(ValueError, match="numerator must be >= 1, got -4"):
        encode_time_signature(-4, 4)
    with pytest.raises(ValueError, match="power of two, got 0"):
        encode_time_signature(4, 0)
    with pytest.raises(ValueError, match="power of two, got -4"):
        encode_time_signature(4, -4)
    with pytest.raises(ValueError, match="power of two, got 3"):
        encode_time_signature(4, 3)


def test_decode_time_signature_round_trips_a_written_meter() -> None:
    """A written signature reads back as the pair that made it."""
    assert decode_time_signature(encode_time_signature(4, 4)) == (4, 4)
    assert decode_time_signature(encode_time_signature(6, 8)) == (6, 8)
    assert decode_time_signature(bytes((3, 2, 24, 8)) + b"\x00") == (3, 4), (
        "a longer payload still reads its first four bytes"
    )


def test_decode_time_signature_rejects_a_short_payload() -> None:
    """Four bytes is the smallest meter the meta event can carry."""
    message = "time signature payload must be 4 bytes, got 3"
    with pytest.raises(ValueError, match=message):
        decode_time_signature(b"\x04\x02\x18")


def test_encode_key_signature_uses_a_signed_accidental_count() -> None:
    """Sharps are positive, flats are two's complement, and the mode follows."""
    assert encode_key_signature(0, False) == bytes((0x00, 0x00, 0x00))
    assert encode_key_signature(7, False) == bytes((0x07, 0x00, 0x00))
    assert encode_key_signature(-7, True) == bytes((0xF9, 0x01, 0x00))
    assert encode_key_signature(1, True) == bytes((0x01, 0x01, 0x00))


def test_encode_key_signature_rejects_an_outside_accidental_count() -> None:
    """The circle of fifths stops at seven accidentals either way."""
    with pytest.raises(ValueError, match="sharps_flats 8 outside -7..7"):
        encode_key_signature(8, False)
    with pytest.raises(ValueError, match="sharps_flats -8 outside -7..7"):
        encode_key_signature(-8, True)


def test_key_payload_encodes_every_key_on_the_circle_of_fifths() -> None:
    """Every key number produces a three-byte payload inside the legal range.

    The accidental counts are asserted rather than derived, so retuning the
    circle is a failing test instead of a silent change of key in an export.
    A minor key carries its relative major's signature: C minor three flats,
    A minor none.
    """
    assert _key_payload(KeySignature(0, True)) == bytes((0x00, 0x00, 0x00))
    assert _key_payload(KeySignature(1, True)) == bytes((0x07, 0x00, 0x00))
    assert _key_payload(KeySignature(6, True)) == bytes((0x06, 0x00, 0x00))
    assert _key_payload(KeySignature(12, False)) == bytes((0xFD, 0x01, 0x00))
    assert _key_payload(KeySignature(21, False)) == bytes((0x00, 0x01, 0x00))
    for key_number in range(24):
        for major in (True, False):
            payload = _key_payload(KeySignature(key_number, major))
            assert len(payload) == 3, f"key {key_number} encodes three bytes"
            accidentals = payload[0] - 256 if payload[0] > 127 else payload[0]
            assert -7 <= accidentals <= 7, f"key {key_number} stays on the circle"
            assert payload[1] == (0 if major else 1), "the mode byte follows the key"
            assert payload[2] == 0, "the reserved third byte stays zero"


def test_meta_text_frames_the_body_with_its_length() -> None:
    """A text meta event is 0xFF, the type, a VLQ length, then the bytes."""
    assert _meta_text(0x01, "Hi") == b"\xFF\x01\x02Hi"
    assert _meta_text(0x03, "") == b"\xFF\x03\x00", "an empty name still frames"
    long_name = "x" * 200
    framed = _meta_text(0x03, long_name)
    assert framed[:2] == b"\xFF\x03"
    assert framed[2:4] == b"\x81\x48", "two hundred needs two septets"
    assert framed[4:] == long_name.encode("ascii")


# ---------------------------------------------------------------------------
# MidiEvent


def test_midi_event_constructors_build_the_three_families() -> None:
    """Note-ons, note-offs, and meta events carry what the writer needs."""
    on = MidiEvent.note_on(48, 3, 60, 100)
    assert on == MidiEvent(48, "voice", 0x93, 60, 100)
    off = MidiEvent.note_off(96, 3, 60)
    assert off == MidiEvent(96, "voice", 0x83, 60, 64), "a default release velocity"
    meta = MidiEvent.meta(0, 0x51, b"\x07\xa1\x20")
    assert meta == MidiEvent(0, "meta", 0x51, payload=b"\x07\xa1\x20")


def test_midi_event_channel_reads_the_low_nibble() -> None:
    """The channel is the low nibble, whatever family the event is in."""
    assert MidiEvent.note_on(0, 9, 36, 100).channel == 9
    assert MidiEvent.note_off(0, 0, 60).channel == 0
    assert MidiEvent(0, "meta", 0x51).channel == 1, "a meta type is not a channel"


def test_is_note_only_reports_note_events() -> None:
    """Only the two note families count as notes for the collapse pass."""
    assert MidiEvent.note_on(0, 0, 60, 100).is_note is True
    assert MidiEvent.note_off(0, 0, 60).is_note is True
    assert MidiEvent(0, "voice", 0xB0, CC_VOLUME, 100).is_note is False
    assert MidiEvent(0, "meta", 0x51).is_note is False


# ---------------------------------------------------------------------------
# Sorting and release classification


def test_sorted_puts_a_release_ahead_of_a_strike_at_one_tick() -> None:
    """Releasing before striking keeps a repeated pitch from cutting itself."""
    strike = MidiEvent.note_on(10, 0, 60, 100)
    release = MidiEvent.note_off(10, 0, 60)
    assert _sorted([strike, release]) == [release, strike]
    quiet = MidiEvent.note_on(10, 0, 62, 0)
    assert _sorted([strike, quiet]) == [quiet, strike], (
        "a zero-velocity note-on is a release too"
    )


def test_is_off_classifies_every_event_family() -> None:
    """A release is a note-off or a note-on that attacks with no velocity."""
    assert _is_off(MidiEvent.note_off(0, 0, 60)) is True
    assert _is_off(MidiEvent.note_on(0, 0, 60, 1)) is False
    assert _is_off(MidiEvent.note_on(0, 0, 60, 0)) is True
    assert _is_off(MidiEvent(0, "voice", 0xB0, CC_VOLUME, 100)) is False
    assert _is_off(MidiEvent(0, "meta", 0x2F)) is False
    assert _is_off(MidiEvent(0, "sysex", payload=GM_RESET)) is False


# ---------------------------------------------------------------------------
# Conductor track


def test_conductor_events_open_with_gm_reset_and_the_title() -> None:
    """A soft synth needs the General MIDI on message before the first hit."""
    song = _song()
    events = _conductor_of(song, copyright_text="")
    assert events[0] == MidiEvent(0, "sysex", payload=GM_RESET)
    assert events[1] == MidiEvent(0, "meta", 0x01, payload=b"Round Trip")
    assert _events_of_text(events, META_COPYRIGHT) == []


def test_conductor_events_add_the_copyright_only_when_given() -> None:
    """An empty copyright line writes no meta event at all."""
    song = _song()
    events = _conductor_of(song, copyright_text="P 2026 Nill Bye")
    assert _events_of_text(events, META_COPYRIGHT) == [b"P 2026 Nill Bye"]


def test_conductor_events_write_one_tempo_per_mark() -> None:
    """Each mark lands on the tick its second falls on."""
    events = _conductor_of(_song())
    assert _events_payloads(events, META_TEMPO) == [
        (0, encode_tempo(120.0)),
        (3840, encode_tempo(96.0)),
    ]


def test_conductor_events_mark_only_the_downbeats() -> None:
    """A marker lands on beat one of each measure, not on every beat."""
    events = _conductor_of(_song())
    assert _events_payloads(events, META_MARKER) == [
        (0, b"Measure 1"),
        (1920, b"Measure 2"),
        (3840, b"Measure 3"),
        (5376, b"Measure 4"),
    ], "the grid is half a second, four beats to the bar"


def test_conductor_events_write_the_meter_and_the_key() -> None:
    """The conductor carries the time signature and the estimated key."""
    events = _conductor_of(_song())
    assert _events_payloads(events, META_TIME_SIGNATURE) == [
        (0, encode_time_signature(4, 4))
    ]
    assert _events_payloads(events, META_KEY_SIGNATURE) == [
        (0, _key_payload(KeySignature(6)))
    ]
    without_key = _conductor_of(_song_without_key(), time_signature=(6, 8))
    assert _events_payloads(without_key, META_KEY_SIGNATURE) == []
    assert _events_payloads(without_key, META_TIME_SIGNATURE) == [
        (0, encode_time_signature(6, 8))
    ]


def test_conductor_events_close_at_the_end_of_the_song() -> None:
    """The click track stays open until the source runs out."""
    events = _conductor_of(_song())
    assert events[-1] == MidiEvent.meta(6912, 0x2F, b""), "eight seconds out"
    assert _sorted(events)[-1].kind == "meta"


def _conductor_of(
    song: Timeline,
    copyright_text: str = "",
    time_signature: tuple[int, int] = (4, 4),
) -> list[MidiEvent]:
    """Build the conductor track of a song.

    Args:
        song: Song to render.
        copyright_text: Copyright line, or empty to omit it.
        time_signature: Numerator and denominator for the opening measure.

    Returns:
        Conductor events in the order the writer emits them.
    """
    return _conductor_events(song, song.tempo_map, time_signature, copyright_text)


def _song_without_key() -> Timeline:
    """Build the round-trip song with no estimated key.

    Returns:
        A timeline whose key is None.
    """
    song = _song()
    return Timeline(
        title="No Key",
        duration_s=song.duration_s,
        tempo_map=song.tempo_map,
        beats=song.beats,
        tracks=song.tracks,
    )


def _events_of_text(events: list[MidiEvent], status: int) -> list[bytes]:
    """Collect the payloads of one meta type.

    Args:
        events: Events to walk.
        status: Meta type to keep.

    Returns:
        The payloads in tick order.
    """
    return [
        event.payload
        for event in events
        if event.kind == "meta" and event.status == status
    ]


def _events_payloads(events: list[MidiEvent], status: int) -> list[tuple[int, bytes]]:
    """Collect tick and payload pairs of one meta type.

    Args:
        events: Events to walk.
        status: Meta type to keep.

    Returns:
        ``(tick, payload)`` rows in tick order.
    """
    return [
        (event.tick, event.payload)
        for event in events
        if event.kind == "meta" and event.status == status
    ]


# ---------------------------------------------------------------------------
# Lane track


def test_lane_events_name_the_channel_and_set_the_mixer() -> None:
    """A lane announces itself, its channel, and three controller defaults."""
    lane = Track(name="Bass", channel=1, program=33, notes=())
    events = _lane_events(lane, TempoMap.at_tempo(120.0))
    assert events[0] == MidiEvent(0, "meta", META_TRACK_NAME, payload=b"Bass")
    assert events[1] == MidiEvent(0, "meta", 0x20, payload=b"\x01")
    assert events[2] == MidiEvent(0, "voice", 0xC1, 33)
    assert [
        (event.status, event.data1, event.data2) for event in events[3:6]
    ] == [
        (0xB1, CC_VOLUME, 100),
        (0xB1, CC_PAN, 64),
        (0xB1, CC_REVERB, 30),
    ]
    assert events[6] == MidiEvent.meta(0, 0x2F, b""), "an empty lane closes at zero"


def test_lane_events_send_no_program_for_the_percussion_lane() -> None:
    """Channel 10 ignores program changes, so none is written."""
    lane = Track(name="Kit", channel=DRUMS_CHANNEL, is_drums=True, notes=())
    events = _lane_events(lane, TempoMap.at_tempo(120.0))
    assert [event for event in events if event.status & 0xF0 == 0xC0] == []
    assert events[1] == MidiEvent(0, "meta", 0x20, payload=b"\x09")


def test_lane_events_pair_each_note_with_a_release() -> None:
    """Every attack gets its release at the tick the note ends."""
    lane = Track(name="Lead", channel=0, program=None, notes=(LEAD_NOTES[2],))
    events = _lane_events(lane, _song().tempo_map)
    notes = [event for event in events if event.is_note]
    assert notes == [
        MidiEvent.note_on(3840, 0, 67, 80),
        MidiEvent.note_off(4608, 0, 67),
    ]


def test_lane_events_keep_a_note_open_for_at_least_one_tick() -> None:
    """A note shorter than one tick still gets a release after its attack."""
    tiny = Note(pitch=60, start_s=0.0, duration_s=0.0001, velocity=88)
    lane = Track(name="Blip", channel=0, program=None, notes=(tiny,))
    events = _lane_events(lane, TempoMap.at_tempo(120.0), notes=(tiny,))
    notes = [event for event in events if event.is_note]
    assert notes == [
        MidiEvent.note_on(0, 0, 60, 88),
        MidiEvent.note_off(1, 0, 60),
    ], "a zero-length delta would leave a stuck voice"


def test_lane_events_honour_notes_handed_to_them() -> None:
    """A caller may render notes that are not the lane's own."""
    lane = Track(name="Lead", channel=0, program=None, notes=LEAD_NOTES)
    own = _lane_events(lane, TempoMap.at_tempo(120.0))
    borrowed = _lane_events(lane, TempoMap.at_tempo(120.0), notes=(LEAD_NOTES[0],))
    assert len(borrowed) < len(own), "one note is fewer events than three"
    assert [event.tick for event in borrowed if event.is_note] == [0, 960]


def test_end_tick_is_the_last_release_or_zero_for_an_empty_lane() -> None:
    """The lane stays open until its latest note lets go."""
    tempo_map = TempoMap.at_tempo(120.0)
    assert _end_tick((), tempo_map) == 0
    assert _end_tick(LEAD_NOTES, tempo_map) == 4800, "the lead ends at five seconds"
    assert _end_tick((LEAD_NOTES[0],), tempo_map) == 960


# ---------------------------------------------------------------------------
# build_tracks, midi_bytes, write_midi


def test_build_tracks_puts_the_conductor_first() -> None:
    """One track per lane plus the click track, in timeline order."""
    tracks = build_tracks(_song())
    assert len(tracks) == 3
    assert tracks[0][0].kind == "sysex", "the conductor leads with GM reset"
    assert tracks[1][0] == MidiEvent(0, "meta", META_TRACK_NAME, payload=b"Lead Synth")
    assert tracks[2][0] == MidiEvent(0, "meta", META_TRACK_NAME, payload=b"Drums")
    for events in tracks:
        assert events == _sorted(events), "each track is already in emit order"
        assert events[-1].status == 0x2F, "every track ends with an end-of-track"


def test_midi_bytes_writes_a_format_one_header() -> None:
    """The header names the format, the track count, and the tick grid."""
    data = midi_bytes(_song())
    assert data[:4] == b"MThd"
    size, format_id, ntracks, division = struct.unpack(">IHHH", data[4:14])
    assert (size, format_id, ntracks, division) == (6, 1, 3, QUARTER_TICKS)
    assert data[14:18] == b"MTrk"
    assert data.count(b"MTrk") == 3, "one chunk per track"


def test_track_chunk_frames_the_body_and_folds_running_status() -> None:
    """A repeated voice status is sent once, and the length counts the body."""
    chunk = _track_chunk(
        [MidiEvent.note_on(0, 0, 60, 100), MidiEvent.note_on(10, 0, 62, 100)]
    )
    assert chunk[:4] == b"MTrk"
    body = chunk[8:]
    assert body == bytes((0x00, 0x90, 0x3C, 0x64, 0x0A, 0x3E, 0x64))
    assert struct.unpack(">I", chunk[4:8])[0] == len(body)
    programs = _track_chunk(
        [
            MidiEvent(0, "voice", 0xC0, 5),
            MidiEvent(0, "voice", 0xC0, 7),
        ]
    )[8:]
    assert programs == bytes((0x00, 0xC0, 0x05, 0x00, 0x07)), "one status byte, twice"


def test_track_chunk_resets_running_status_for_meta_and_sysex() -> None:
    """A meta or SysEx event between two notes cancels the running status."""
    chunk = _track_chunk(
        [
            MidiEvent.note_on(0, 0, 60, 100),
            MidiEvent(0, "meta", 0x03, payload=b"x"),
            MidiEvent.note_on(0, 0, 62, 100),
            MidiEvent(0, "sysex", payload=GM_RESET),
            MidiEvent.note_on(0, 0, 64, 100),
        ]
    )
    body = chunk[8:]
    assert body == bytes(
        (
            0x00, 0x90, 0x3C, 0x64,
            0x00, 0xFF, 0x03, 0x01, 0x78,
            0x00, 0x90, 0x3E, 0x64,
            0x00, 0xF0, 0x04, 0x7E, 0x7F, 0x09, 0x01, 0xF7,
            0x00, 0x90, 0x40, 0x64,
        )
    )


def test_track_chunk_rejects_events_out_of_tick_order() -> None:
    """A negative delta time would corrupt every later event."""
    with pytest.raises(ValueError, match="track events out of order at tick 5"):
        _track_chunk(
            [MidiEvent.note_on(10, 0, 60, 100), MidiEvent.note_on(5, 0, 62, 100)]
        )


def test_write_midi_lands_the_same_bytes_the_writer_rendered(
    tmp_path: Path,
) -> None:
    """The file on disk is the buffer, and the return is its size."""
    song = _song()
    target = tmp_path / "round-trip.mid"
    written = write_midi(song, str(target))
    data = midi_bytes(song)
    assert written == len(data), "the caller logs a size without a second stat"
    assert target.read_bytes() == data
    assert written > 100, "a real file is more than its header"
    assert write_midi(song, str(target), (3, 4), "P 2026") == len(
        midi_bytes(song, (3, 4), "P 2026")
    ), "the extra arguments reach the conductor track"


# ---------------------------------------------------------------------------
# parse_midi: structure and error paths


def test_parse_midi_rejects_a_file_that_is_not_standard_midi() -> None:
    """Too short for a header, or the wrong chunk id, is not a MIDI file."""
    with pytest.raises(ValueError, match="not a Standard MIDI File"):
        parse_midi(b"")
    with pytest.raises(ValueError, match="not a Standard MIDI File"):
        parse_midi(b"RIFF" + bytes(10))
    with pytest.raises(ValueError, match="not a Standard MIDI File"):
        parse_midi(b"MThd")


def test_parse_midi_rejects_a_header_it_cannot_trust() -> None:
    """A tiny header chunk and SMPTE division are both unreadable."""
    short = (
        b"MThd"
        + struct.pack(">IHHH", 4, 1, 1, QUARTER_TICKS)
        + b"MTrk"
        + b"\x00" * 7
    )
    with pytest.raises(ValueError, match="header chunk too small: 4"):
        parse_midi(short)
    smpte = _smf_bytes([b""], division=0x8000 | 0x0060)
    with pytest.raises(ValueError, match="SMPTE time division is not supported"):
        parse_midi(smpte)


def test_parse_midi_rejects_a_missing_track_chunk() -> None:
    """A header that promises a track and delivers junk is truncated."""
    broken = (
        b"MThd"
        + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
        + b"XXXX"
        + b"\x00" * 4
    )
    with pytest.raises(ValueError, match="missing MTrk at offset 14"):
        parse_midi(broken)


def test_parse_midi_rejects_a_track_that_ends_mid_event() -> None:
    """A chunk length longer than the file stops the decoder inside an event.

    Each case promises more track bytes than the file holds, and the decoder
    reports the overrun before it walks into a delta, a meta length, or a
    SysEx length. A chunk whose declared length runs past the end of the file
    with a complete delta is covered by
    :func:`test_parse_midi_rejects_a_chunk_longer_than_the_file`.
    """
    truncated_delta = b"MThd" + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
    truncated_delta += b"MTrk" + struct.pack(">I", 6) + b"\x80"
    with pytest.raises(ValueError, match="the chunk ends mid-event"):
        parse_midi(truncated_delta)

    truncated_meta = b"MThd" + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
    truncated_meta += b"MTrk" + struct.pack(">I", 6) + b"\x00\xFF\x80"
    with pytest.raises(ValueError, match="the chunk ends mid-event"):
        parse_midi(truncated_meta)

    truncated_sysex = b"MThd" + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
    truncated_sysex += b"MTrk" + struct.pack(">I", 6) + b"\x00\xF0\x80"
    with pytest.raises(ValueError, match="the chunk ends mid-event"):
        parse_midi(truncated_sysex)


def _ragged_track(declared: int, body: bytes) -> bytes:
    """Frame a track body with a length the caller chooses.

    Args:
        declared: Length written into the ``MTrk`` frame, which may be longer
            than the bytes that follow it inside this one track.
        body: Track bytes the parser is meant to walk.

    Returns:
        Complete file bytes with two trailing bytes so a cut inside ``body``
        is a mid-event truncation and not a short buffer.
    """
    header = b"MThd" + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
    return header + b"MTrk" + struct.pack(">I", declared) + body + b"\x00\x00"


def test_parse_midi_rejects_a_chunk_longer_than_the_file() -> None:
    """A declared length past the end of the buffer is a truncation."""
    header = b"MThd" + struct.pack(">IHHH", 6, 1, 1, QUARTER_TICKS)
    short = header + b"MTrk" + struct.pack(">I", 6) + b"\x00\xFF\x00"
    with pytest.raises(ValueError, match="the chunk ends mid-event"):
        parse_midi(short)


def test_parse_midi_rejects_each_event_cut_in_half() -> None:
    """Every event family reports its own truncation as a ValueError."""
    cases = {
        "delta with no status byte": b"\x00",
        "meta with no type or length": b"\x00\xFF",
        "meta payload shorter than declared": b"\x00\xFF\x02\x2F",
        "sysex with no length": b"\x00\xF0",
        "sysex payload shorter than declared": b"\x00\xF0\x03\x01",
        "voice status with no data byte": b"\x00\x90",
        "voice message missing its second byte": b"\x00\x90\x40",
    }
    for label, body in cases.items():
        with pytest.raises(ValueError, match="the chunk ends mid-event"):
            parse_midi(_ragged_track(len(body), body))


def test_parse_midi_rejects_running_status_with_no_prior_status() -> None:
    """A data byte cannot open a track on its own."""
    body = bytes((0x00, 0x40, 0x64))
    with pytest.raises(ValueError, match="running status with no prior status byte"):
        parse_midi(_smf_bytes([body]))


def test_parse_midi_reads_an_empty_track_as_no_events() -> None:
    """A zero-length chunk is legal and yields nothing."""
    parsed = parse_midi(_smf_bytes([b""], format_id=0))
    assert len(parsed) == 1
    assert parsed[0].events == [] and parsed[0].name == ""
    assert note_rows(parsed[0]) == []
    assert tempo_rows(parsed[0]) == []


def test_parse_midi_reads_the_voice_families_and_running_status() -> None:
    """Program change and channel pressure take one byte, the rest take two."""
    body = bytes(
        (
            0x00, 0xC0, 0x50,  # program change 80
            0x00, 0xD0, 0x40,  # channel pressure 64
            0x00, 0xE0, 0x40, 0x40,  # pitch bend
            0x00, 0x90, 0x3C, 0x64,  # note on 60
            0x0A, 0x3C, 0x00,  # running status: note on 60, velocity 0
            0x81, 0x00, 0x80, 0x3E, 0x64,  # delta 128: note off 62
        )
    )
    parsed = parse_midi(_smf_bytes([body]))[0]
    assert parsed.events == [
        MidiEvent(0, "voice", 0xC0, 0x50),
        MidiEvent(0, "voice", 0xD0, 0x40),
        MidiEvent(0, "voice", 0xE0, 0x40, 0x40),
        MidiEvent(0, "voice", 0x90, 0x3C, 0x64),
        MidiEvent(10, "voice", 0x90, 0x3C, 0x00),
        MidiEvent(138, "voice", 0x80, 0x3E, 0x64),
    ]


def test_parse_midi_reads_a_sysex_and_a_meta_event() -> None:
    """Both non-voice families keep their payloads and the running status."""
    body = bytes(
        (
            0x00, 0xF0, 0x04, 0x7E, 0x7F, 0x09, 0x01, 0xF7,
            0x00, 0xFF, 0x03, 0x02, 0x48, 0x69,
            0x00, 0x90, 0x3C, 0x64,
        )
    )
    parsed = parse_midi(_smf_bytes([body]))[0]
    assert parsed.name == "Hi"
    assert parsed.events[0] == MidiEvent(0, "sysex", payload=GM_RESET)
    assert parsed.events[1] == MidiEvent(0, "meta", 0x03, payload=b"Hi")
    assert parsed.events[2] == MidiEvent(0, "voice", 0x90, 0x3C, 0x64)


# ---------------------------------------------------------------------------
# note_rows and tempo_rows


def test_note_rows_pairs_an_attack_with_its_release() -> None:
    """A row is attack tick, pitch, length, and the velocity that struck it."""
    track = ParsedTrack(
        events=[
            MidiEvent.note_on(0, 0, 60, 100),
            MidiEvent.note_off(480, 0, 60),
            MidiEvent.note_on(480, 0, 64, 90),
            MidiEvent.note_off(960, 0, 64),
        ]
    )
    assert note_rows(track) == [(0, 60, 480, 100), (480, 64, 480, 90)]


def test_note_rows_keeps_a_note_open_for_at_least_one_tick() -> None:
    """A release in the same delta as its attack still measures one tick."""
    track = ParsedTrack(
        events=[
            MidiEvent.note_on(100, 0, 60, 100),
            MidiEvent.note_off(100, 0, 60),
        ]
    )
    assert note_rows(track) == [(100, 60, 1, 100)]


def test_note_rows_collapses_simultaneous_notes_of_one_pitch() -> None:
    """Two attacks on one pitch leave one row, taken from the later attack.

    One open note is tracked per pitch, so the second note-on overwrites the
    first and the release closes only the row that survived. This is the
    documented collapse: a chord of doubled pitches reads back as one row.
    """
    track = ParsedTrack(
        events=[
            MidiEvent.note_on(0, 0, 60, 100),
            MidiEvent.note_on(20, 0, 60, 110),
            MidiEvent.note_off(40, 0, 60),
        ]
    )
    assert note_rows(track) == [(20, 60, 20, 110)], (
        "the later attack and its velocity win the single row"
    )


def test_note_rows_ignores_events_that_are_not_notes() -> None:
    """Controllers, meta, and SysEx never become rows."""
    track = ParsedTrack(
        events=[
            MidiEvent(0, "meta", META_TRACK_NAME, payload=b"Lead"),
            MidiEvent(0, "voice", 0xB0, CC_VOLUME, 100),
            MidiEvent(0, "sysex", payload=GM_RESET),
            MidiEvent.note_on(0, 0, 60, 100),
            MidiEvent.note_off(10, 0, 60),
        ]
    )
    assert note_rows(track) == [(0, 60, 10, 100)]


def test_note_rows_drops_a_release_that_opened_nothing() -> None:
    """A note-off with no attack, or a zero-velocity attack, is not a note."""
    track = ParsedTrack(
        events=[
            MidiEvent.note_off(0, 0, 60),
            MidiEvent.note_on(10, 0, 62, 0),
            MidiEvent.note_off(20, 0, 62),
            MidiEvent.note_on(30, 0, 64, 90),
            MidiEvent.note_off(40, 0, 64),
        ]
    )
    assert note_rows(track) == [(30, 64, 10, 90)]


def test_note_rows_sorts_by_attack_then_pitch() -> None:
    """The rows come back in the order a score would read them."""
    track = ParsedTrack(
        events=[
            MidiEvent.note_on(10, 0, 72, 90),
            MidiEvent.note_off(20, 0, 72),
            MidiEvent.note_on(0, 0, 60, 100),
            MidiEvent.note_off(10, 0, 60),
            MidiEvent.note_on(0, 0, 48, 110),
            MidiEvent.note_off(10, 0, 48),
        ]
    )
    assert note_rows(track) == [(0, 48, 10, 110), (0, 60, 10, 100), (10, 72, 10, 90)]


def test_tempo_rows_reads_only_the_tempo_meta_events() -> None:
    """Every tempo mark becomes a tick and a beats-per-minute row."""
    conductor = ParsedTrack(
        events=[
            MidiEvent(0, "sysex", payload=GM_RESET),
            MidiEvent(0, "meta", META_TEMPO, payload=encode_tempo(120.0)),
            MidiEvent(0, "meta", META_MARKER, payload=b"Measure 1"),
            MidiEvent(3840, "meta", META_TEMPO, payload=encode_tempo(96.0)),
            MidiEvent(3840, "voice", 0x90, 60, 100),
        ]
    )
    assert tempo_rows(conductor) == [(0, 120.0), (3840, 96.0)]


# ---------------------------------------------------------------------------
# Round trip


def test_round_trip_writes_and_reads_back_a_three_track_song() -> None:
    """Everything the writer put into the file comes out of the parser."""
    song = _song()
    data = midi_bytes(song)
    parsed = parse_midi(data)

    assert len(parsed) == 3, "conductor, melodic lane, percussion lane"
    assert parsed[0].name == "", "the click track carries text, not a name"
    assert _events_of_text(parsed[0].events, 0x01) == [b"Round Trip"]
    assert parsed[1].name == "Lead Synth"
    assert parsed[2].name == "Drums"

    assert note_rows(parsed[1]) == LEAD_ROWS
    assert note_rows(parsed[2]) == DRUM_ROWS

    assert tempo_rows(parsed[0]) == [(0, 120.0), (3840, 96.0)], (
        "the mid-song tempo change survives the file"
    )

    gm = [(event.tick, event.payload) for event in _events_of(parsed[0], "sysex")]
    assert gm == [(0, GM_RESET)], "General MIDI on, ahead of every drum hit"

    assert _events_payloads(parsed[0].events, META_TIME_SIGNATURE) == [
        (0, encode_time_signature(4, 4))
    ]
    assert _events_payloads(parsed[0].events, META_KEY_SIGNATURE) == [
        (0, _key_payload(song.key) if song.key is not None else b"")
    ]
    assert _events_payloads(parsed[0].events, META_MARKER) == [
        (0, b"Measure 1"),
        (1920, b"Measure 2"),
        (3840, b"Measure 3"),
        (5376, b"Measure 4"),
    ]

    assert [
        (event.tick, event.status, event.data1, event.data2)
        for event in _events_of(parsed[1], "voice", 0xC0)
    ] == [(0, 0xC0, PROGRAM_LEAD_SYNTH, None)], (
        "the lane claims its General MIDI voice"
    )
    program_changes = [
        event
        for event in _events_of(parsed[2], "voice")
        if event.status & 0xF0 == 0xC0
    ]
    assert program_changes == [], "channel 10 carries no program change"

    assert [
        (event.status, event.data1, event.data2)
        for event in _events_of(parsed[1], "voice", 0xB0)
    ] == [(0xB0, CC_VOLUME, 100), (0xB0, CC_PAN, 64), (0xB0, CC_REVERB, 30)]
    assert _events_payloads(parsed[1].events, 0x20) == [(0, b"\x00")]
    assert _events_payloads(parsed[2].events, 0x20) == [(0, b"\x09")]

    assert parsed[1].events[-1] == MidiEvent.meta(4608, 0x2F, b"")
    assert parsed[2].events[-1] == MidiEvent.meta(4992, 0x2F, b"")
    assert parsed[0].events[-1] == MidiEvent.meta(6912, 0x2F, b"")


def test_round_trip_releases_a_pitch_before_restriking_it() -> None:
    """At the tick where one note ends and the next begins, the off comes first."""
    parsed = parse_midi(midi_bytes(_song()))[1]
    at_handoff = [event for event in parsed.events if event.tick == 960]
    assert at_handoff == [
        MidiEvent.note_off(960, 0, 60),
        MidiEvent.note_on(960, 0, 64, 90),
    ], "a tied or adjacent pitch cannot cut its own attack"


def test_round_trip_survives_a_write_to_disk(tmp_path: Path) -> None:
    """The bytes read back off disk parse to the same rows as the buffer."""
    song = _song()
    target = tmp_path / "song.mid"
    written = write_midi(song, str(target), (6, 8), "P 2026 Nill Bye")
    assert written == target.stat().st_size, "the return is the bytes on disk"
    from_disk = parse_midi(target.read_bytes())
    assert [track.name for track in from_disk] == ["", "Lead Synth", "Drums"]
    assert note_rows(from_disk[1]) == LEAD_ROWS
    assert note_rows(from_disk[2]) == DRUM_ROWS
    assert _events_of_text(from_disk[0].events, META_COPYRIGHT) == [b"P 2026 Nill Bye"]
    assert _events_payloads(from_disk[0].events, META_TIME_SIGNATURE) == [
        (0, encode_time_signature(6, 8))
    ]


def test_round_trip_reads_a_file_with_no_lanes_at_all() -> None:
    """A song with nothing but the click track still parses cleanly."""
    empty = Timeline(
        title="Silence",
        duration_s=1.0,
        tempo_map=TempoMap.at_tempo(120.0),
    )
    parsed = parse_midi(midi_bytes(empty))
    assert len(parsed) == 1
    assert _events_of_text(parsed[0].events, 0x01) == [b"Silence"]
    assert tempo_rows(parsed[0]) == [(0, 120.0)]
    assert parsed[0].events[-1] == MidiEvent.meta(960, 0x2F, b"")
