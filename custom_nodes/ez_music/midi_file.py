"""Standard MIDI File 1.0 writer and parser for the transcribed timeline.

Everything here is pure standard library: the transcriber has to run in the
hermetic test lane, where only pytest and mutagen are pinned, so the package
carries its own wire format instead of pulling in mido or pretty_midi.

:func:`write_midi` turns a :class:`~ez_music.timeline.Timeline` into a format
1 file - one conductor track for the tempo map, then one track per lane.
:func:`parse_midi` reads a file back into :class:`MidiEvent` rows. The parser
exists so the writer can be tested against what a sequencer would actually
see, which is the only way to catch a broken delta time or a dropped running
status without a third-party dependency.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Literal, Sequence

from ez_music.timeline import (
    TICKS_PER_QUARTER,
    KeySignature,
    Note,
    TempoMap,
    Timeline,
    Track,
)

# Chunk ids.
_HEADER_ID = b"MThd"
_TRACK_ID = b"MTrk"

# Voice status high nibbles.
_NOTE_OFF = 0x80
_NOTE_ON = 0x90
_PROGRAM_CHANGE = 0xC0
_CONTROL_CHANGE = 0xB0

# Control change numbers worth sending: expression, pan, and reverb send.
CC_VOLUME = 7
CC_PAN = 10
CC_REVERB = 91

# Meta event types this module writes.
META_SEQUENCE_NUMBER = 0x00
META_TEXT = 0x01
META_COPYRIGHT = 0x02
META_TRACK_NAME = 0x03
META_INSTRUMENT = 0x04
META_MARKER = 0x06
META_CUE = 0x07
META_PROGRAM_NAME = 0x08
META_CHANNEL_PREFIX = 0x20
META_END_OF_TRACK = 0x2F
META_TEMPO = 0x51
META_KEY_SIGNATURE = 0x59
META_TIME_SIGNATURE = 0x58

# Meta types that carry no payload length beyond the length byte itself.
_EventKind = Literal["voice", "meta", "sysex"]

# A note that would not fit in one delta is split; no delta ever exceeds this.
_MAX_DELTA = 0x0FFFFFFF

# General MIDI reset, sent first so a hardware or soft synth lands channel 10
# on the percussion map before the first drum hit.
GM_RESET = bytes((0x7E, 0x7F, 0x09, 0x01))


@dataclass(frozen=True)
class MidiEvent:
    """One parsed or to-be-written MIDI event with an absolute tick.

    Args:
        tick: Absolute tick from the top of the track.
        kind: Which of the three event families this is.
        status: Voice status byte (high nibble plus channel) for a voice
            event, or the meta type byte for a meta event.
        data1: First data byte of a voice event.
        data2: Second data byte of a voice event.
        payload: Meta payload bytes, or SysEx body without the framing bytes.
    """

    tick: int
    kind: _EventKind
    status: int = 0
    data1: int | None = None
    data2: int | None = None
    payload: bytes = b""

    @staticmethod
    def note_on(tick: int, channel: int, pitch: int, velocity: int) -> MidiEvent:
        """Build a note-on.

        Args:
            tick: Absolute tick.
            channel: MIDI channel, 0 to 15.
            pitch: Note number.
            velocity: Attack, 1 to 127.
        Returns:
            Voice event ready to sort into a track.
        """
        return MidiEvent(tick, "voice", _NOTE_ON | channel, pitch, velocity)

    @staticmethod
    def note_off(tick: int, channel: int, pitch: int) -> MidiEvent:
        """Build a note-off at the default release velocity.

        Args:
            tick: Absolute tick.
            channel: MIDI channel, 0 to 15.
            pitch: Note number.
        Returns:
            Voice event ready to sort into a track.
        """
        return MidiEvent(tick, "voice", _NOTE_OFF | channel, pitch, 64)

    @staticmethod
    def meta(tick: int, meta_type: int, payload: bytes) -> MidiEvent:
        """Build a meta event.

        Args:
            tick: Absolute tick.
            meta_type: Meta type byte, one of the ``META_*`` constants.
            payload: Meta body bytes.
        Returns:
            Meta event ready to sort into a track.
        """
        return MidiEvent(tick, "meta", meta_type, payload=payload)

    @property
    def channel(self) -> int:
        """Return the channel of a voice event.

        Returns:
            Low nibble of the status byte, or 0 for a meta or SysEx event.
        """
        return self.status & 0x0F

    @property
    def is_note(self) -> bool:
        """Report whether this event starts or stops a note.

        Returns:
            True for a note-on or note-off voice event.
        """
        return self.kind == "voice" and (self.status & 0xF0) in (
            _NOTE_ON,
            _NOTE_OFF,
        )


@dataclass
class ParsedTrack:
    """Events of one parsed MIDI track.

    Args:
        events: Events in increasing tick order.
        name: Track name meta text, when the track carried one.
    """

    events: list[MidiEvent] = field(default_factory=list)
    name: str = ""


def encode_vlq(value: int) -> bytes:
    """Encode a delta time or length as a MIDI variable-length quantity.

    Args:
        value: Non-negative integer that fits in 28 bits.
    Returns:
        One to four big-endian septet bytes with continuation bits set.
    Raises:
        ValueError: value is negative or will not fit.
    """
    if value < 0:
        raise ValueError(f"VLQ cannot be negative: {value}")
    if value > _MAX_DELTA:
        raise ValueError(f"VLQ {value} exceeds {_MAX_DELTA}")
    out = bytearray([value & 0x7F])
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def decode_vlq(data: bytes, offset: int) -> tuple[int, int]:
    """Decode a variable-length quantity.

    Args:
        data: Track bytes.
        offset: Index of the first byte of the quantity.
    Returns:
        The decoded value and the index just past it.
    Raises:
        ValueError: the stream ends mid-quantity or the quantity is too long.
    """
    value = 0
    read = 0
    while True:
        if offset >= len(data):
            raise ValueError("track ended inside a variable-length quantity")
        byte = data[offset]
        offset += 1
        read += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            break
        if read == 4:
            raise ValueError("variable-length quantity longer than four bytes")
    return value, offset


def encode_tempo(bpm: float) -> bytes:
    """Encode a tempo as the three-byte meta payload.

    Args:
        bpm: Beats per minute.
    Returns:
        Big-endian microseconds per quarter note.
    """
    microseconds = max(1, round(60_000_000.0 / bpm))
    return struct.pack(">I", microseconds)[1:]


def decode_tempo(payload: bytes) -> float:
    """Decode a three-byte tempo payload.

    Args:
        payload: Exactly three bytes.
    Returns:
        Beats per minute.
    Raises:
        ValueError: payload is not three bytes.
    """
    if len(payload) != 3:
        raise ValueError(f"tempo payload must be 3 bytes, got {len(payload)}")
    microseconds = int.from_bytes(payload, "big")
    if microseconds == 0:
        raise ValueError("tempo payload is zero")
    return 60_000_000.0 / microseconds


def encode_time_signature(numerator: int, denominator: int) -> bytes:
    """Encode a time signature meta payload.

    Args:
        numerator: Beats per measure.
        denominator: Note value of one beat; must be a power of two.
    Returns:
        Four-byte payload: numerator, log2 denominator, metronome, ticks per
        quarter-note of the metronome click.
    Raises:
        ValueError: numerator is not positive or the denominator is not a
            power of two.
    """
    if numerator < 1:
        raise ValueError(f"numerator must be >= 1, got {numerator}")
    if denominator <= 0 or denominator & (denominator - 1):
        raise ValueError(f"denominator must be a power of two, got {denominator}")
    return bytes((numerator & 0xFF, denominator.bit_length() - 1, 24, 8))


def decode_time_signature(payload: bytes) -> tuple[int, int]:
    """Decode a time signature meta payload.

    Args:
        payload: Four bytes or longer.
    Returns:
        Numerator and denominator.
    Raises:
        ValueError: payload is shorter than four bytes.
    """
    if len(payload) < 4:
        raise ValueError(f"time signature payload must be 4 bytes, got {len(payload)}")
    return int(payload[0]), 1 << int(payload[1])


def encode_key_signature(sharps_flats: int, minor: bool) -> bytes:
    """Encode a key signature meta payload.

    Args:
        sharps_flats: -7 to 7; negative counts flats, positive counts sharps.
        minor: True for a minor key.
    Returns:
        Three-byte payload.
    Raises:
        ValueError: the accidental count is out of range.
    """
    if not -7 <= sharps_flats <= 7:
        raise ValueError(f"sharps_flats {sharps_flats} outside -7..7")
    return bytes((sharps_flats & 0xFF, 1 if minor else 0, 0))


def _meta_text(meta_type: int, text: str) -> bytes:
    """Encode meta text as bytes a sequencer can show.

    Args:
        meta_type: Meta type byte.
        text: Text to embed.
    Returns:
        Ready-made meta event bytes without the delta time.
    """
    body = text.encode("ascii", "replace")
    return bytes((0xFF, meta_type)) + encode_vlq(len(body)) + body


def _conductor_events(
    timeline: Timeline,
    tempo_map: TempoMap,
    time_signature: tuple[int, int],
    copyright_text: str,
) -> list[MidiEvent]:
    """Build the click track: tempo, meter, key, markers, and text.

    Args:
        timeline: Song to render.
        tempo_map: Tempo the file encodes.
        time_signature: Numerator and denominator for the opening measure.
        copyright_text: Copyright line, or empty to omit it.
    Returns:
        Conductor track events in tick order.
    """
    events = [
        MidiEvent(0, "sysex", payload=GM_RESET),
        _text_meta(0, META_TEXT, timeline.title),
    ]
    if copyright_text:
        events.append(_text_meta(0, META_COPYRIGHT, copyright_text))
    for point in tempo_map.points:
        tick = tempo_map.to_ticks(point.time_s)
        events.append(
            MidiEvent.meta(tick, META_TEMPO, encode_tempo(point.bpm))
        )
    numerator, denominator = time_signature
    events.append(
        MidiEvent.meta(0, META_TIME_SIGNATURE, encode_time_signature(numerator, denominator))
    )
    if timeline.key is not None:
        events.append(
            MidiEvent.meta(0, META_KEY_SIGNATURE, _key_payload(timeline.key))
        )
    for index, beat in enumerate(timeline.beats):
        if index % numerator != 0:
            continue
        measure = index // numerator + 1
        events.append(_text_meta(tempo_map.to_ticks(beat), META_MARKER, f"Measure {measure}"))
    events.append(MidiEvent.meta(tempo_map.to_ticks(timeline.duration_s), META_END_OF_TRACK, b""))
    return _sorted(events)


def _key_payload(key: KeySignature) -> bytes:
    """Encode a key signature object into its meta payload.

    The accidental count comes from :attr:`KeySignature.fifths`, which is also
    what MusicXML writes, so one timeline cannot export two different keys.

    Args:
        key: Key signature to encode.
    Returns:
        Three-byte payload.
    """
    return encode_key_signature(key.fifths, not key.major)


def _text_meta(tick: int, meta_type: int, text: str) -> MidiEvent:
    """Build a text-family meta event.

    Args:
        tick: Absolute tick.
        meta_type: One of the text-family ``META_*`` constants.
        text: Text to embed.
    Returns:
        Meta event.
    """
    return MidiEvent(tick, "meta", meta_type, payload=text.encode("ascii", "replace"))


def _lane_events(
    track: Track,
    tempo_map: TempoMap,
    notes: Sequence[Note] | None = None,
) -> list[MidiEvent]:
    """Build one lane's track events.

    A note-off and a following note-on on the same pitch are emitted at the
    same tick, which is how a sequencer shows a tied or adjacent note without
    a stuck voice.

    Args:
        track: Lane to render.
        tempo_map: Tempo used to convert seconds to ticks.
        notes: Notes to write, defaulting to the lane's own notes.
    Returns:
        Track events in tick order.
    """
    chosen = track.notes if notes is None else tuple(notes)
    events: list[MidiEvent] = [
        _text_meta(0, META_TRACK_NAME, track.name),
        MidiEvent(0, "meta", META_CHANNEL_PREFIX, payload=bytes((track.channel,))),
    ]
    if track.program is not None:
        events.append(
            MidiEvent(
                0,
                "voice",
                _PROGRAM_CHANGE | track.channel,
                track.program,
            )
        )
    for control, value in ((CC_VOLUME, 100), (CC_PAN, 64), (CC_REVERB, 30)):
        events.append(
            MidiEvent(
                0,
                "voice",
                _CONTROL_CHANGE | track.channel,
                control,
                value,
            )
        )
    for note in chosen:
        start = tempo_map.to_ticks(note.start_s)
        end = max(start + 1, tempo_map.to_ticks(note.end_s))
        events.append(MidiEvent.note_on(start, track.channel, note.pitch, note.velocity))
        events.append(MidiEvent.note_off(end, track.channel, note.pitch))
    events.append(MidiEvent.meta(_end_tick(chosen, tempo_map), META_END_OF_TRACK, b""))
    return _sorted(events)


def _end_tick(notes: Sequence[Note], tempo_map: TempoMap) -> int:
    """Return the tick the track must stay open until.

    Args:
        notes: Notes of the lane.
        tempo_map: Tempo used to convert seconds to ticks.
    Returns:
        Tick of the last note release, or 0 for an empty lane.
    """
    latest = 0.0
    for note in notes:
        latest = max(latest, note.end_s)
    return tempo_map.to_ticks(latest)


def _sorted(events: list[MidiEvent]) -> list[MidiEvent]:
    """Sort events by tick, keeping note-offs ahead of note-ons.

    Releasing before striking at the same tick keeps a repeated pitch from
    cutting its own attack on sequencers that allocate one voice per pitch.

    Args:
        events: Events in any order.
    Returns:
        New list in the order the writer should emit them.
    """
    return sorted(events, key=lambda event: (event.tick, 0 if _is_off(event) else 1))


def _is_off(event: MidiEvent) -> bool:
    """Report whether an event releases a note.

    Args:
        event: Event to classify.
    Returns:
        True for a note-off, or for a note-on carrying zero velocity.
    """
    if event.kind != "voice":
        return False
    high = event.status & 0xF0
    if high == _NOTE_OFF:
        return True
    return high == _NOTE_ON and event.data2 == 0


def build_tracks(
    timeline: Timeline,
    time_signature: tuple[int, int] = (4, 4),
    copyright_text: str = "",
) -> list[list[MidiEvent]]:
    """Assemble every track of the file.

    Args:
        timeline: Song to render.
        time_signature: Numerator and denominator written to the conductor
            track.
        copyright_text: Copyright line for the conductor track.
    Returns:
        Conductor track first, then one track per lane in timeline order.
    """
    tempo_map = timeline.tempo_map
    tracks: list[list[MidiEvent]] = [
        _conductor_events(timeline, tempo_map, time_signature, copyright_text)
    ]
    for lane in timeline.tracks:
        tracks.append(_lane_events(lane, tempo_map))
    return tracks


def midi_bytes(
    timeline: Timeline,
    time_signature: tuple[int, int] = (4, 4),
    copyright_text: str = "",
) -> bytes:
    """Render the whole file in memory.

    Args:
        timeline: Song to render.
        time_signature: Numerator and denominator for the opening measure.
        copyright_text: Copyright line for the conductor track.
    Returns:
        Complete Standard MIDI File 1.0 bytes.
    """
    tracks = build_tracks(timeline, time_signature, copyright_text)
    header = _HEADER_ID + struct.pack(">IHHH", 6, 1, len(tracks), TICKS_PER_QUARTER)
    body = b"".join(_track_chunk(events) for events in tracks)
    return header + body


def write_midi(
    timeline: Timeline,
    path: str,
    time_signature: tuple[int, int] = (4, 4),
    copyright_text: str = "",
) -> int:
    """Write the timeline to a Standard MIDI File.

    Args:
        timeline: Song to render.
        path: Destination ``.mid`` path.
        time_signature: Numerator and denominator for the opening measure.
        copyright_text: Copyright line for the conductor track.
    Returns:
        Bytes written, so a caller can log a size without a second stat.
    """
    data = midi_bytes(timeline, time_signature, copyright_text)
    with open(path, "wb") as handle:
        handle.write(data)
    return len(data)


def _track_chunk(events: Sequence[MidiEvent]) -> bytes:
    """Serialize one track chunk with running status folded in.

    Args:
        events: Track events in the order they should be emitted.
    Returns:
        ``MTrk`` chunk bytes.
    """
    body = bytearray()
    previous_tick = 0
    running = -1
    for event in events:
        delta = event.tick - previous_tick
        if delta < 0:
            raise ValueError(f"track events out of order at tick {event.tick}")
        previous_tick = event.tick
        body += encode_vlq(delta)
        if event.kind == "meta":
            body += bytes((0xFF, event.status)) + encode_vlq(len(event.payload))
            body += event.payload
            running = -1
            continue
        if event.kind == "sysex":
            body += b"\xF0" + encode_vlq(len(event.payload)) + event.payload + b"\xF7"
            running = -1
            continue
        if event.status != running:
            body.append(event.status)
            running = event.status
        body.append(event.data1 or 0)
        if _takes_two_bytes(event.status):
            body.append(event.data2 or 0)
    return _TRACK_ID + struct.pack(">I", len(body)) + bytes(body)


def _takes_two_bytes(status: int) -> bool:
    """Report whether a voice status byte carries two data bytes.

    Args:
        status: Voice status byte.
    Returns:
        True for note-on, note-off, aftertouch, control change, and pitch
            bend; False for program change and channel pressure.
    """
    return (status & 0xF0) in (0x80, 0x90, 0xA0, 0xB0, 0xE0)


def parse_midi(data: bytes) -> list[ParsedTrack]:
    """Parse Standard MIDI File bytes into per-track event rows.

    Args:
        data: Complete file bytes.
    Returns:
        One :class:`ParsedTrack` per chunk, conductor track first.
    Raises:
        ValueError: header is missing or a chunk is truncated.
    """
    if len(data) < 14 or data[0:4] != _HEADER_ID:
        raise ValueError("not a Standard MIDI File")
    size, format_id, ntracks, division = struct.unpack(">IHHH", data[4:14])
    if size < 6:
        raise ValueError(f"header chunk too small: {size}")
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported")
    offset = 8 + size
    tracks: list[ParsedTrack] = []
    for _ in range(ntracks):
        if data[offset : offset + 4] != _TRACK_ID:
            raise ValueError(f"missing MTrk at offset {offset}")
        length = struct.unpack(">I", data[offset + 4 : offset + 8])[0]
        offset += 8
        tracks.append(_parse_track(data, offset, offset + length))
        offset += length
    return tracks


def _parse_track(data: bytes, start: int, end: int) -> ParsedTrack:
    """Parse one track chunk.

    Args:
        data: Complete file bytes.
        start: First event byte.
        end: One past the last event byte.
    Returns:
        Parsed track with absolute ticks.
    Raises:
        ValueError: the chunk ends mid-event, including a declared chunk
            length that runs past the buffer.
    """
    parsed = ParsedTrack()
    tick = 0
    running = -1
    if end > len(data):
        raise ValueError("the chunk ends mid-event")
    cursor = start
    while cursor < end:
        delta, cursor = decode_vlq(data, cursor)
        tick += delta
        if cursor >= end:
            raise ValueError("the chunk ends mid-event")
        status = data[cursor]
        if status == 0xFF:
            if cursor + 2 > end:
                raise ValueError("the chunk ends mid-event")
            meta_type = data[cursor + 1]
            length, cursor = decode_vlq(data, cursor + 2)
            if cursor + length > end:
                raise ValueError("the chunk ends mid-event")
            payload = data[cursor : cursor + length]
            cursor += length
            parsed.events.append(MidiEvent(tick, "meta", meta_type, payload=payload))
            if meta_type == META_TRACK_NAME:
                parsed.name = payload.decode("ascii", "replace")
            running = -1
            continue
        if status in (0xF0, 0xF7):
            cursor += 1
            if cursor >= end:
                raise ValueError("the chunk ends mid-event")
            length, cursor = decode_vlq(data, cursor)
            if cursor + length > end:
                raise ValueError("the chunk ends mid-event")
            payload = data[cursor : cursor + length]
            cursor += length + 1
            parsed.events.append(MidiEvent(tick, "sysex", payload=payload))
            running = -1
            continue
        if status & 0x80:
            cursor += 1
            if cursor >= end:
                raise ValueError("the chunk ends mid-event")
        elif running < 0:
            raise ValueError(f"running status with no prior status byte at {cursor}")
        else:
            status = running
        running = status
        high = status & 0xF0
        if high in (0xC0, 0xD0):
            parsed.events.append(MidiEvent(tick, "voice", status, data[cursor]))
            cursor += 1
        else:
            if cursor + 2 > end:
                raise ValueError("the chunk ends mid-event")
            parsed.events.append(
                MidiEvent(tick, "voice", status, data[cursor], data[cursor + 1])
            )
            cursor += 2
    return parsed


def note_rows(track: ParsedTrack) -> list[tuple[int, int, int, int]]:
    """Collapse a parsed track's note events into note rows.

    Args:
        track: Parsed track, already sorted by tick.
    Returns:
        ``(start_tick, pitch, duration_ticks, velocity)`` rows sorted by
        attack, then pitch.
    """
    open_notes: dict[int, tuple[int, int]] = {}
    rows: list[tuple[int, int, int, int]] = []
    for event in track.events:
        if not event.is_note:
            continue
        pitch = int(event.data1 or 0)
        if event.status & 0xF0 == _NOTE_ON and (event.data2 or 0) > 0:
            open_notes[pitch] = (event.tick, int(event.data2 or 0))
            continue
        opened = open_notes.pop(pitch, None)
        if opened is None:
            continue
        start, velocity = opened
        rows.append((start, pitch, max(1, event.tick - start), velocity))
    return sorted(rows)


def tempo_rows(conductor: ParsedTrack) -> list[tuple[int, float]]:
    """Pull the tempo map out of a parsed conductor track.

    Args:
        conductor: Parsed conductor track.
    Returns:
        ``(tick, bpm)`` rows in tick order.
    """
    rows: list[tuple[int, float]] = []
    for event in conductor.events:
        if event.kind == "meta" and event.status == META_TEMPO:
            rows.append((event.tick, decode_tempo(event.payload)))
    return rows
