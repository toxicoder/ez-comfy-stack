"""MusicXML 4.0 writer for the transcribed timeline.

A ``.mid`` carries the performance; a score is what a human opens when they
want to read the song and hand it to a player. MuseScore, Finale, and Dorico
all take ``score-partwise``, so this module emits that shape directly from the
:class:`~ez_music.timeline.Timeline` - one ``<part>` per lane, tempo in a
``<sound tempo=...>`` direction, and the percussion lane written as
``<unpitched>`` notes with their General MIDI numbers.

Two honesty notes the export guide repeats, because they are properties of
notation rather than of this writer. Notes that start inside the same
quantized column become one chord, so every voice in the chord takes the
shortest duration in the group. A note that crosses a barline is trimmed at
the barline rather than tied, because a tied note needs two ``<note>``
elements and a prototype transcription should not pretend to engraving
fidelity it does not have.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET

from ez_music.timeline import TICKS_PER_QUARTER, Note, Timeline, Track

# Document identity. MusicXML 4.0 prefers a schema, but the W3C still tells
# writers to keep the DOCTYPE so older readers accept the file.
_MUSICXML_DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC '
    '"-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)
_ROOT_TAG = "score-partwise"
_VERSION = "4.0"

# Divisions per quarter note. 96 divides by 2, 3, 4, 6, 8, 12, 16, 24, 32, 48,
# so a sixteenth and a triplet eighth are both exact integers.
DIVISIONS_PER_QUARTER = 96

# Step and alteration for each pitch class, spelled with sharps.
_STEPS: tuple[tuple[str, int], ...] = (
    ("C", 0),
    ("C", 1),
    ("D", 0),
    ("D", 1),
    ("E", 0),
    ("F", 0),
    ("F", 1),
    ("G", 0),
    ("G", 1),
    ("A", 0),
    ("A", 1),
    ("B", 0),
)

# Where each General MIDI drum sits on a 5-line percussion staff, as
# (display-step, display-octave). Positions follow the usual GM kit engraving
# so a score opened in MuseScore or Dorico reads as a kit and not as one line.
_DRUM_STAFF: dict[int, tuple[str, int]] = {
    35: ("G", 1),
    36: ("C", 1),
    37: ("D", 2),
    38: ("C", 2),
    39: ("E", 2),
    40: ("E", 2),
    41: ("A", 1),
    42: ("A", 2),
    43: ("B", 1),
    44: ("A", 2),
    45: ("G", 2),
    46: ("A", 2),
    47: ("B", 2),
    48: ("D", 3),
    49: ("A", 3),
    50: ("E", 3),
    51: ("E", 3),
    52: ("C", 4),
    55: ("C", 4),
    56: ("G", 3),
    57: ("A", 3),
    59: ("F", 3),
}
_DRUM_FALLBACK: tuple[str, int] = ("B", 2)

# Note type names by quarter-note length, longest first so the longest exact
# match wins. ``<duration>`` carries the real length in divisions; ``<type>``
# only drives how a reader draws the notehead, so the nearest power-of-two
# value is the honest answer.
_NOTE_TYPES: tuple[tuple[float, str], ...] = (
    (4.0, "whole"),
    (2.0, "half"),
    (1.0, "quarter"),
    (0.5, "eighth"),
    (0.25, "16th"),
    (0.0, "32nd"),
)

_CLEF_SIGN = "G"
_CLEF_LINE = 2
_PERCUSSION_CLEF_SIGN = "percussion"
# The written beat unit in the opening metronome mark. The timeline carries no
# metre beyond the caller's beat count, so the quarter is the honest default.
_METRONOME_BEAT_UNIT = "quarter"


@dataclass(frozen=True)
class Column:
    """Notes that share one quantized onset inside a measure.

    Args:
        start_division: Onset as divisions from the measure start.
        duration_divisions: Shared written duration of the chord.
        notes: Notes sounding together, lowest pitch first.
    """

    start_division: int
    duration_divisions: int
    notes: tuple[Note, ...]


def quarter_position(time_s: float, timeline: Timeline) -> float:
    """Return where a time falls on the quarter-note grid.

    Args:
        time_s: Seconds from the top of the song.
        timeline: Timeline whose tempo map defines the grid.
    Returns:
        Quarter notes from the top of the song.
    """
    return timeline.tempo_map.to_ticks(time_s) / TICKS_PER_QUARTER


def note_type(quarters: float) -> str:
    """Return the note-type name nearest a quarter-note length.

    Args:
        quarters: Length in quarter notes.
    Returns:
        A MusicXML ``<type>`` value: whole, half, quarter, eighth, 16th, or
        32nd.
    """
    for threshold, name in _NOTE_TYPES:
        if quarters >= threshold:
            return name
    return "32nd"


def _subdivisions_per_step() -> float:
    """Return the quantization step used for onsets, in quarters.

    Returns:
        One sixteenth of a quarter note.
    """
    return 0.25


def build_columns(
    notes: tuple[Note, ...],
    timeline: Timeline,
    measure: int,
    beats_per_bar: int,
) -> list[Column]:
    """Group one measure's notes into onset columns.

    Args:
        notes: Notes that belong to this measure, in any order.
        timeline: Timeline providing the tempo map.
        measure: One-based measure number.
        beats_per_bar: Numerator of the time signature.
    Returns:
        Columns in onset order, each spanning whole divisions.
    """
    if not notes:
        return []
    measure_start = (measure - 1) * beats_per_bar
    step = _subdivisions_per_step()
    grouped: dict[int, list[Note]] = {}
    for note in notes:
        position = quarter_position(note.start_s, timeline) - measure_start
        if position < 0.0:
            position = 0.0
        bucket = int(position / step)
        grouped.setdefault(bucket, []).append(note)
    columns: list[Column] = []
    for bucket in sorted(grouped):
        start = int(bucket * step * DIVISIONS_PER_QUARTER)
        members = tuple(sorted(grouped[bucket], key=lambda item: item.pitch))
        duration = _duration_divisions(members, timeline, start, beats_per_bar)
        columns.append(Column(start, max(1, duration), members))
    return _trim_overflow(columns, beats_per_bar)


def _duration_divisions(
    members: tuple[Note, ...],
    timeline: Timeline,
    start: int,
    beats_per_bar: int,
) -> int:
    """Return the shared written duration of a chord in divisions.

    The shortest note in the group wins, and the result is cut off at the
    barline, which is why a note that crosses the barline is trimmed rather
    than tied.

    Args:
        members: Notes sounding together.
        timeline: Timeline providing the tempo map.
        start: Onset as divisions from the measure start.
        beats_per_bar: Numerator of the time signature.
    Returns:
        Duration in divisions, at least 1.
    """
    if not members:
        return 1
    shortest = min(member.duration_s for member in members)
    length = int(round(quarter_position(shortest, timeline) * DIVISIONS_PER_QUARTER))
    bar_length = int(round(beats_per_bar * DIVISIONS_PER_QUARTER))
    return max(1, min(length, bar_length - start))


def _trim_overflow(columns: list[Column], beats_per_bar: int) -> list[Column]:
    """Drop columns that start past the barline and clamp the last one.

    Args:
        columns: Columns built for one measure.
        beats_per_bar: Numerator of the time signature.
    Returns:
        Columns that fit inside the measure.
    """
    bar_length = int(round(beats_per_bar * DIVISIONS_PER_QUARTER))
    kept: list[Column] = []
    for column in columns:
        if column.start_division >= bar_length:
            continue
        duration = min(column.duration_divisions, bar_length - column.start_division)
        kept.append(Column(column.start_division, max(1, duration), column.notes))
    return kept


def measure_index(
    note: Note, timeline: Timeline, beats_per_bar: int, duration_s: float
) -> int:
    """Return the one-based measure a note belongs to.

    Args:
        note: Note to place.
        timeline: Timeline providing the tempo map.
        beats_per_bar: Numerator of the time signature.
        duration_s: Length of the song, used to keep a late note inside the
            final measure instead of inventing one.
    Returns:
        Measure number, at least 1.
    """
    position = quarter_position(note.start_s, timeline)
    last = max(1.0, quarter_position(duration_s, timeline))
    measure = int(position // beats_per_bar) + 1
    final_measure = int(last // beats_per_bar) + 1
    return max(1, min(measure, final_measure))


def measure_count(timeline: Timeline, beats_per_bar: int) -> int:
    """Return how many measures the song needs.

    Args:
        timeline: Timeline to measure.
        beats_per_bar: Numerator of the time signature.
    Returns:
        At least one measure, so an empty song still parses.
    """
    last = quarter_position(timeline.duration_s, timeline)
    return max(1, int(last // beats_per_bar) + 1)


def _drum_display(pitch: int) -> tuple[str, int]:
    """Return the staff position a drum is notated at.

    An unpitched note needs an explicit display position, and a kit reads as
    mush when every pad lands on the same line. The table covers the kit pieces
    the transcriber emits; anything else lands on the middle space.

    Args:
        pitch: MIDI number of the drum.
    Returns:
        ``(step, octave)`` for ``<display-step>`` and ``<display-octave>``.
    """
    return _DRUM_STAFF.get(pitch, _DRUM_FALLBACK)


def _pitch_elements(note_el: ET.Element, note: Note, is_drums: bool) -> None:
    """Add the pitched or unpitched child of a note element.

    Args:
        note_el: The ``<note>`` element to extend.
        note: Note being written.
        is_drums: True for the percussion lane, which has no pitch.
    """
    if is_drums:
        step, octave = _drum_display(note.pitch)
        unpitched = ET.SubElement(note_el, "unpitched")
        ET.SubElement(unpitched, "display-step").text = step
        ET.SubElement(unpitched, "display-octave").text = str(octave)
        return
    step, alter = _STEPS[note.pitch % 12]
    pitch = ET.SubElement(note_el, "pitch")
    ET.SubElement(pitch, "step").text = step
    if alter:
        ET.SubElement(pitch, "alter").text = str(alter)
    ET.SubElement(pitch, "octave").text = str(note.pitch // 12 - 1)


def _note_element(
    note: Note,
    duration: int,
    is_drums: bool,
    chord: bool,
    instrument_id: str | None = None,
) -> ET.Element:
    """Build one ``<note>`` element.

    The child order follows the MusicXML 4.0 ``note`` type: chord, pitch or
    unpitched, duration, instruments, voice, type. MIDI velocity has no
    MusicXML counterpart, so the ``.mid`` file is the artifact that carries
    dynamics.

    Args:
        note: Note to write.
        duration: Written duration in divisions.
        is_drums: True for the percussion lane.
        chord: True for every voice after the first in a column.
        instrument_id: ``<instrument>`` reference for a percussion note.
    Returns:
        A ``<note>`` element ready to append.
    """
    element = ET.Element("note")
    if chord:
        ET.SubElement(element, "chord")
    _pitch_elements(element, note, is_drums)
    ET.SubElement(element, "duration").text = str(duration)
    if instrument_id is not None:
        ET.SubElement(element, "instrument").set("id", instrument_id)
    ET.SubElement(element, "voice").text = "1"
    ET.SubElement(element, "type").text = note_type(
        duration / DIVISIONS_PER_QUARTER
    )
    return element


def _rest_element(duration: int) -> ET.Element:
    """Build a ``<note>`` rest.

    Args:
        duration: Rest length in divisions.
    Returns:
        A ``<note>`` element holding a ``<rest/>``.
    """
    element = ET.Element("note")
    ET.SubElement(element, "rest")
    ET.SubElement(element, "duration").text = str(duration)
    ET.SubElement(element, "voice").text = "1"
    ET.SubElement(element, "type").text = note_type(duration / DIVISIONS_PER_QUARTER)
    return element


def _attributes_element(
    measures: ET.Element,
    track: Track,
    timeline: Timeline,
    beats_per_bar: int,
    denominator: int,
) -> None:
    """Add the first measure's ``<attributes>`` block.

    Args:
        measures: The measure element to extend.
        track: Lane the block belongs to, which decides the clef.
        timeline: Timeline providing the key.
        beats_per_bar: Numerator of the time signature.
        denominator: Denominator of the time signature.
    """
    attributes = ET.SubElement(measures, "attributes")
    ET.SubElement(attributes, "divisions").text = str(DIVISIONS_PER_QUARTER)
    key = ET.SubElement(attributes, "key")
    fifths = 0
    mode = "major"
    if timeline.key is not None:
        fifths = timeline.key.fifths
        mode = "major" if timeline.key.major else "minor"
    ET.SubElement(key, "fifths").text = str(fifths)
    ET.SubElement(key, "mode").text = mode
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = str(beats_per_bar)
    ET.SubElement(time, "beat-type").text = str(denominator)
    clef = ET.SubElement(attributes, "clef")
    if track.is_drums:
        ET.SubElement(clef, "sign").text = _PERCUSSION_CLEF_SIGN
    else:
        ET.SubElement(clef, "sign").text = _CLEF_SIGN
        ET.SubElement(clef, "line").text = str(_CLEF_LINE)


def instrument_ids(track: Track, part_id: str) -> dict[int, str]:
    """Return the score-instrument id that carries each pitch of a lane.

    A melodic lane is one instrument. A percussion lane needs one instrument
    per drum, because MusicXML stores the MIDI number of an unpitched note on
    the instrument (``<midi-unpitched>``) rather than on the note, so a single
    instrument could only ever sound one drum.

    Args:
        track: Lane to lay out.
        part_id: Identifier of the lane's ``<score-part>``.
    Returns:
        Mapping of pitch to instrument id, empty for a melodic or silent lane.
    """
    if not track.is_drums:
        return {}
    pitches = sorted({note.pitch for note in track.notes})
    return {pitch: f"{part_id}-I{index + 1}" for index, pitch in enumerate(pitches)}


def _midi_instruments(
    track: Track,
    part_id: str,
) -> list[tuple[str, int | None, int | None]]:
    """Return the instrument declarations one lane needs.

    Args:
        track: Lane to declare instruments for.
        part_id: Identifier of the lane's ``<score-part>``.
    Returns:
        ``(id, midi-program, midi-unpitched)`` per instrument, with the two
        pitch fields mutually exclusive.
    """
    ids = instrument_ids(track, part_id)
    if ids:
        return [(ids[pitch], None, pitch) for pitch in sorted(ids)]
    return [(f"{part_id}-I1", track.program, None)]


def _part_element(
    score: ET.Element,
    track: Track,
    part_id: str,
    timeline: Timeline,
    beats_per_bar: int,
    denominator: int,
) -> None:
    """Write one lane as one ``<part>``.

    Args:
        score: The ``score-partwise`` root.
        track: Lane to write.
        part_id: Identifier shared with the matching ``<score-part>``.
        timeline: Timeline providing the tempo map and duration.
        beats_per_bar: Numerator of the time signature.
        denominator: Denominator of the time signature.
    """
    part = ET.SubElement(score, "part")
    part.set("id", part_id)
    ids = instrument_ids(track, part_id)
    measures_total = measure_count(timeline, beats_per_bar)
    for measure in range(1, measures_total + 1):
        measure_el = ET.SubElement(part, "measure")
        measure_el.set("number", str(measure))
        if measure == 1:
            _attributes_element(measure_el, track, timeline, beats_per_bar, denominator)
        in_measure = tuple(
            note
            for note in track.notes
            if measure_index(note, timeline, beats_per_bar, timeline.duration_s) == measure
        )
        cursor = 0
        for column in build_columns(in_measure, timeline, measure, beats_per_bar):
            if column.start_division > cursor:
                measure_el.append(_rest_element(column.start_division - cursor))
            for index, note in enumerate(column.notes):
                measure_el.append(
                    _note_element(
                        note,
                        column.duration_divisions,
                        track.is_drums,
                        index > 0,
                        ids.get(note.pitch),
                    )
                )
            cursor = column.start_division + column.duration_divisions
        bar_length = int(round(beats_per_bar * DIVISIONS_PER_QUARTER))
        if cursor < bar_length:
            measure_el.append(_rest_element(bar_length - cursor))


def score_bytes(
    timeline: Timeline,
    beats_per_bar: int = 4,
    denominator: int = 4,
    creator: str = "ez-comfy-stack",
) -> bytes:
    """Render the whole score as MusicXML 4.0 bytes.

    Args:
        timeline: Song to engrave.
        beats_per_bar: Numerator of the written time signature.
        denominator: Denominator of the written time signature.
        creator: Attribution written into ``<identification>``.
    Returns:
        UTF-8 encoded document, XML declaration and DOCTYPE included.
    """
    score = ET.Element(_ROOT_TAG)
    score.set("version", _VERSION)
    work = ET.SubElement(score, "work")
    ET.SubElement(work, "work-title").text = timeline.title
    movement = ET.SubElement(score, "movement-title")
    movement.text = timeline.title
    # The score-partwise content model is fixed: work, movement-title,
    # identification, defaults/credit, part-list, then the parts.
    identification = ET.SubElement(score, "identification")
    if timeline.source is not None and timeline.source.artist:
        creator_tag = ET.SubElement(identification, "creator")
        creator_tag.set("type", "performer")
        creator_tag.text = timeline.source.artist
    if timeline.source is not None and timeline.source.album:
        ET.SubElement(identification, "rights").text = f"Album: {timeline.source.album}"
    encoding = ET.SubElement(identification, "encoding")
    ET.SubElement(encoding, "software").text = creator
    part_list = ET.SubElement(score, "part-list")
    for index, track in enumerate(timeline.tracks):
        part_id = f"P{index + 1}"
        score_part = ET.SubElement(part_list, "score-part")
        score_part.set("id", part_id)
        ET.SubElement(score_part, "part-name").text = track.name
        declared = _midi_instruments(track, part_id)
        # score-part is a strict sequence: every score-instrument first, then
        # the midi-instrument block. Interleaving them is schema-invalid.
        for instrument_id, _program, unpitched in declared:
            label = track.name if unpitched is None else f"{track.name} {unpitched}"
            instrument = ET.SubElement(score_part, "score-instrument")
            instrument.set("id", instrument_id)
            ET.SubElement(instrument, "instrument-name").text = label
        for instrument_id, program, unpitched in declared:
            midi_instrument = ET.SubElement(score_part, "midi-instrument")
            midi_instrument.set("id", instrument_id)
            ET.SubElement(midi_instrument, "midi-channel").text = str(track.channel + 1)
            if program is not None:
                ET.SubElement(midi_instrument, "midi-program").text = str(program + 1)
            if unpitched is not None:
                ET.SubElement(midi_instrument, "midi-unpitched").text = str(unpitched)
            ET.SubElement(midi_instrument, "volume").text = "80"
            ET.SubElement(midi_instrument, "pan").text = "0"
    for index, track in enumerate(timeline.tracks):
        _part_element(score, track, f"P{index + 1}", timeline, beats_per_bar, denominator)
    _prepend_tempo_direction(score, timeline)
    body = ET.tostring(score, encoding="unicode")
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + _MUSICXML_DOCTYPE
        + "\n"
        + body
        + "\n"
    )
    return document.encode("utf-8")


def _prepend_tempo_direction(score: ET.Element, timeline: Timeline) -> None:
    """Write the tempo into the first measure of every part.

    MuseScore and Dorico read a ``<sound tempo=...>`` direction more reliably
    than they read a MIDI meta event inside a MusicXML file, so the tempo goes
    into the score itself.

    Args:
        score: The ``score-partwise`` root, already holding its parts.
        timeline: Timeline providing the opening tempo.
    """
    for part in score.findall("part"):
        measure = part.find("measure")
        if measure is None:
            continue
        direction = ET.Element("direction")
        direction.set("placement", "above")
        direction_type = ET.SubElement(direction, "direction-type")
        metronome = ET.SubElement(direction_type, "metronome")
        ET.SubElement(metronome, "beat-unit").text = _METRONOME_BEAT_UNIT
        ET.SubElement(metronome, "per-minute").text = f"{timeline.bpm:.0f}"
        sound = ET.SubElement(direction, "sound")
        sound.set("tempo", f"{timeline.bpm:.0f}")
        measure.insert(0, direction)


def write_score(
    timeline: Timeline,
    path: str,
    beats_per_bar: int = 4,
    denominator: int = 4,
    creator: str = "ez-comfy-stack",
) -> int:
    """Write the timeline to a MusicXML file.

    Args:
        timeline: Song to engrave.
        path: Destination ``.musicxml`` path.
        beats_per_bar: Numerator of the written time signature.
        denominator: Denominator of the written time signature.
        creator: Attribution written into ``<identification>``.
    Returns:
        Bytes written.
    """
    data = score_bytes(timeline, beats_per_bar, denominator, creator)
    with open(path, "wb") as handle:
        handle.write(data)
    return len(data)
