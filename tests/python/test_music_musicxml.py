"""MusicXML 4.0 writer: score head, note order, kit instruments, and bars.

The writer is checked structurally rather than by string diff: every test
parses the bytes back with :mod:`xml.etree.ElementTree` and asserts the child
order the MusicXML 4.0 ``score-partwise`` content model demands, because that
order is what makes MuseScore, Finale, and Dorico open the file at all. The
facts pinned here are the ones the writer was written against - no
``<velocity>`` and no ``<midi-unpitched>`` inside a ``<note>``, one
``<score-instrument>`` per drum, and ``<sound tempo=...>`` as a sibling of
``<direction-type>``.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from ez_music.midi_file import META_KEY_SIGNATURE, midi_bytes, parse_midi
from ez_music.musicxml import (
    DIVISIONS_PER_QUARTER,
    Column,
    _drum_display,
    _duration_divisions,
    _midi_instruments,
    _prepend_tempo_direction,
    _trim_overflow,
    build_columns,
    instrument_ids,
    measure_count,
    measure_index,
    note_type,
    quarter_position,
    score_bytes,
    write_score,
)
from ez_music.timeline import KeySignature, Note, SourceInfo, TempoMap, Timeline, Track

_BPM = 120.0
_BEAT_S = 60.0 / _BPM
_BAR_S = _BEAT_S * 4.0
_SIXTEENTH = DIVISIONS_PER_QUARTER // 4
_DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC '
    '"-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)


def _at(quarters: float) -> float:
    """Return the attack time of a spot on the quarter grid.

    Args:
        quarters: Quarter notes from the top of the song.
    Returns:
        Seconds at the probe tempo.
    """
    return quarters * _BEAT_S


def _timeline(
    tracks: tuple[Track, ...],
    duration_s: float = 8.0,
    key: KeySignature | None = None,
    source: SourceInfo | None = None,
    title: str = "Probe Song",
) -> Timeline:
    """Build a fixed-tempo timeline for the writer to engrave.

    Args:
        tracks: Lanes the score carries.
        duration_s: Length of the take in seconds.
        key: Key signature, when one was estimated.
        source: Provenance of the audio, when the take came from a tagged file.
        title: Song title for the score header.
    Returns:
        Timeline at 120 BPM in common time.
    """
    return Timeline(
        title=title,
        duration_s=duration_s,
        tempo_map=TempoMap.at_tempo(_BPM),
        tracks=tracks,
        key=key,
        source=source,
    )


def _empty_timeline() -> Timeline:
    """Return a timeline with no lanes for the pure-math helpers.

    Returns:
        Eight-second timeline at 120 BPM and no tracks.
    """
    return _timeline(())


def _lead(notes: tuple[Note, ...], name: str = "Lead", channel: int = 3) -> Track:
    """Return a melodic lane.

    Args:
        notes: Notes to carry, in attack order.
        name: Lane name.
        channel: MIDI channel to write the lane to.
    Returns:
        Track with a lead-synth program and no percussion flag.
    """
    return Track(name=name, channel=channel, program=80, notes=notes)


def _kit(notes: tuple[Note, ...], name: str = "Drums") -> Track:
    """Return a percussion lane.

    Args:
        notes: Drum hits, whose pitch is the General MIDI number.
        name: Lane name.
    Returns:
        Track flagged as the percussion lane, which carries no program.
    """
    return Track(name=name, channel=9, program=None, notes=notes, is_drums=True)


def _root(
    tracks: tuple[Track, ...],
    duration_s: float = 8.0,
    key: KeySignature | None = None,
    source: SourceInfo | None = None,
    beats_per_bar: int = 4,
    denominator: int = 4,
    creator: str = "ez-comfy-stack",
) -> ET.Element:
    """Render a score and parse it back.

    Args:
        tracks: Lanes the score carries.
        duration_s: Length of the take in seconds.
        key: Key signature to write.
        source: Provenance to write into ``<identification>``.
        beats_per_bar: Numerator of the written time signature.
        denominator: Denominator of the written time signature.
        creator: Attribution written into ``<identification>``.
    Returns:
        Parsed ``score-partwise`` root element.
    """
    data = score_bytes(
        _timeline(tracks, duration_s, key, source), beats_per_bar, denominator, creator
    )
    return ET.fromstring(data)


def _tags(element: ET.Element) -> tuple[str, ...]:
    """Return the tag of each direct child.

    Args:
        element: Element to inspect.
    Returns:
        Child tags in document order.
    """
    return tuple(child.tag for child in element)


def _measure(root: ET.Element, part_index: int, measure_number: int) -> ET.Element:
    """Return one measure of one part.

    Args:
        root: Parsed score.
        part_index: Zero-based position of the part.
        measure_number: One-based measure number.
    Returns:
        The matching ``<measure>`` element.
    """
    part = root.findall("part")[part_index]
    matches = [
        measure
        for measure in part.findall("measure")
        if measure.get("number") == str(measure_number)
    ]
    assert matches, f"part {part_index} has no measure {measure_number}"
    return matches[0]


def _notes(root: ET.Element, part_index: int, measure_number: int) -> list[ET.Element]:
    """Return the notes of one measure.

    Args:
        root: Parsed score.
        part_index: Zero-based position of the part.
        measure_number: One-based measure number.
    Returns:
        ``<note>`` elements in document order.
    """
    return list(_measure(root, part_index, measure_number).findall("note"))


def _instrument_refs(notes: list[ET.Element]) -> list[str]:
    """Return the instrument ids the notes reference, rests skipped.

    Args:
        notes: Note elements to read.
    Returns:
        The ``id`` of each note's ``<instrument>`` child, in document order.
    """
    refs: list[str] = []
    for note in notes:
        element = note.find("instrument")
        if element is None:
            continue
        instrument_id = element.get("id")
        assert instrument_id, "an instrument reference names its instrument"
        refs.append(instrument_id)
    return refs


def _child(element: ET.Element, path: str) -> ET.Element:
    """Return a child element that the schema makes required.

    Args:
        element: Parent to search.
        path: Child path to look up.
    Returns:
        The matching child element.
    Raises:
        AssertionError: nothing under element matches the path.
    """
    child = element.find(path)
    assert child is not None, f"no {path} under <{element.tag}>"
    return child


def _unpitched_parent_tags(root: ET.Element) -> set[str]:
    """Return the tags of the elements that own a ``<midi-unpitched>`` child.

    Args:
        root: Parsed score.
    Returns:
        Tag name of every parent holding a ``<midi-unpitched>`` element.
    """
    return {
        parent.tag
        for parent in root.iter()
        if any(child.tag == "midi-unpitched" for child in parent)
    }


def _note_shape(note: ET.Element) -> tuple[tuple[str, ...], str, str]:
    """Summarise one written note.

    Args:
        note: The ``<note>`` element to read.
    Returns:
        Child tags, written duration, and note type.
    """
    return (
        _tags(note),
        str(note.findtext("duration")),
        str(note.findtext("type")),
    )


def test_document_opens_with_the_declaration_and_doctype() -> None:
    """The W3C still asks writers to keep the DOCTYPE for older readers."""
    text = score_bytes(_empty_timeline()).decode("utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
    assert _DOCTYPE in text
    assert text.splitlines()[2].startswith('<score-partwise version="4.0">')
    assert text.endswith("</score-partwise>\n")


def test_a_take_with_no_lanes_still_writes_a_readable_score() -> None:
    """A silent take must not hand a DAW a document the schema rejects.

    ``score-partwise`` requires at least one ``score-part`` in the part list
    and one matching ``part``, so a take the transcriber found nothing in
    still has to arrive as one empty staff rather than an unopenable file.
    """
    score = ET.fromstring(score_bytes(_empty_timeline()))
    declared = score.findall("part-list/score-part")
    body = score.findall("part")
    assert len(declared) == 1, f"an empty take still declares one part: {len(declared)}"
    assert len(body) == 1, f"the document carries the matching part: {len(body)}"
    assert declared[0].get("id") == body[0].get("id"), "the part id matches its declaration"
    assert body[0].findall("measure"), "the silent part still carries its measures"


def test_quarter_position_uses_the_tempo_map() -> None:
    """Seconds land on the quarter grid the tempo map defines."""
    timeline = _empty_timeline()
    assert quarter_position(0.0, timeline) == 0.0
    assert quarter_position(_BEAT_S, timeline) == pytest.approx(1.0)
    assert quarter_position(_BAR_S, timeline) == pytest.approx(4.0)


@pytest.mark.parametrize(
    ("quarters", "expected"),
    [
        (4.0, "whole"),
        (3.0, "half"),
        (2.0, "half"),
        (1.0, "quarter"),
        (0.75, "eighth"),
        (0.5, "eighth"),
        (0.25, "16th"),
        (0.1, "32nd"),
        (0.0, "32nd"),
        (-1.0, "32nd"),
    ],
)
def test_note_type_table(quarters: float, expected: str) -> None:
    """The longest exact match wins, and the floor is a 32nd."""
    assert note_type(quarters) == expected


def test_empty_lane_builds_no_columns() -> None:
    """A measure with no notes yields no onset columns."""
    assert build_columns((), _empty_timeline(), 1, 4) == []


def test_build_columns_buckets_on_the_sixteenth_grid() -> None:
    """Notes in the same sixteenth share a column, lowest pitch first."""
    timeline = _timeline(())
    notes = (
        Note(64, _at(0.55), 0.25),
        Note(60, _at(0.00), 0.25),
        Note(67, _at(0.60), 0.25),
        Note(72, _at(3.80), 0.25),
    )
    columns = build_columns(notes, timeline, 1, 4)
    assert [column.start_division for column in columns] == [0, 2 * _SIXTEENTH, 15 * _SIXTEENTH]
    assert [len(column.notes) for column in columns] == [1, 2, 1]
    assert [note.pitch for note in columns[1].notes] == [64, 67]


def test_build_columns_clamps_an_early_note_to_the_barline() -> None:
    """A note that leaked from the previous bar is written at the bar start."""
    timeline = _timeline(())
    columns = build_columns((Note(60, _BAR_S - 0.05, 0.25),), timeline, 2, 4)
    assert len(columns) == 1
    assert columns[0].start_division == 0


def test_duration_of_an_empty_chord_is_one_division() -> None:
    """A column with no members still needs a writable duration."""
    assert _duration_divisions((), _empty_timeline(), 0, 4) == 1


def test_trim_overflow_clamps_at_the_barline() -> None:
    """Columns past the bar are dropped and the last one is cut short."""
    note = Note(60, 0.0, 4.0)
    columns = [
        Column(0, DIVISIONS_PER_QUARTER, (note,)),
        Column(400, DIVISIONS_PER_QUARTER, (note,)),
        Column(300, 999, (note,)),
    ]
    kept = _trim_overflow(columns, 4)
    assert [column.start_division for column in kept] == [0, 300]
    assert [column.duration_divisions for column in kept] == [
        DIVISIONS_PER_QUARTER,
        4 * DIVISIONS_PER_QUARTER - 300,
    ]


def test_measure_index_places_notes_and_caps_at_the_final_bar() -> None:
    """A note is never written into a bar the song does not have."""
    timeline = _timeline(())
    assert measure_index(Note(60, 0.0, 0.5), timeline, 4, 8.0) == 1
    assert measure_index(Note(60, _at(10.0), 0.5), timeline, 4, 8.0) == 3
    assert measure_index(Note(60, _at(60.0), 0.5), timeline, 4, 8.0) == 5


def test_measure_count_rounds_up_a_partial_bar() -> None:
    """A part-bar tail still gets a measure, and a silent song gets one."""
    assert measure_count(_timeline((), duration_s=5.0), 4) == 3
    assert measure_count(_timeline((), duration_s=0.0), 4) == 1
    assert measure_count(_timeline((), duration_s=8.0), 3) == 6


def test_score_head_orders_work_identification_part_list_then_parts() -> None:
    """The score head is a fixed sequence with part-list last."""
    root = _root((_lead((Note(60, 0.0, 0.5),)), _kit((Note(36, 0.0, 0.5),))))
    assert root.tag == "score-partwise"
    assert root.get("version") == "4.0"
    assert _tags(root) == (
        "work",
        "movement-title",
        "identification",
        "part-list",
        "part",
        "part",
    )
    assert root.findtext("work/work-title") == "Probe Song"
    assert root.findtext("movement-title") == "Probe Song"


def test_attributes_children_follow_divisions_key_time_clef() -> None:
    """The attributes block is a strict sequence and names the division grid."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),), key=KeySignature(0, True))
    attributes = _measure(root, 0, 1).find("attributes")
    assert attributes is not None
    assert _tags(attributes) == ("divisions", "key", "time", "clef")
    assert attributes.findtext("divisions") == str(DIVISIONS_PER_QUARTER)
    assert DIVISIONS_PER_QUARTER % 32 == 0
    assert _tags(_child(attributes, "key")) == ("fifths", "mode")
    assert _tags(_child(attributes, "time")) == ("beats", "beat-type")
    assert attributes.findtext("time/beats") == "4"
    assert attributes.findtext("time/beat-type") == "4"


def test_melodic_clef_is_treble_and_percussion_clef_has_no_line() -> None:
    """A drum staff carries the percussion sign and no staff line."""
    root = _root((_lead((Note(60, 0.0, 0.5),)), _kit((Note(36, 0.0, 0.5),))))
    melody_clef = _measure(root, 0, 1).find("attributes/clef")
    drums_clef = _measure(root, 1, 1).find("attributes/clef")
    assert melody_clef is not None and drums_clef is not None
    assert _tags(melody_clef) == ("sign", "line")
    assert melody_clef.findtext("sign") == "G"
    assert melody_clef.findtext("line") == "2"
    assert _tags(drums_clef) == ("sign",)
    assert drums_clef.findtext("sign") == "percussion"


@pytest.mark.parametrize(
    ("key_number", "major", "fifths", "mode"),
    [
        (0, True, "0", "major"),
        (7, True, "1", "major"),
        (5, True, "-1", "major"),
        (11, True, "5", "major"),
        (9, False, "0", "minor"),
        (2, True, "2", "major"),
        (8, True, "-4", "major"),
        (8, False, "5", "minor"),
    ],
)
def test_key_signature_writes_fifths_and_mode(
    key_number: int, major: bool, fifths: str, mode: str
) -> None:
    """Both modes are written, and a key signature survives to the score."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),), key=KeySignature(key_number, major))
    key = _measure(root, 0, 1).find("attributes/key")
    assert key is not None
    assert key.findtext("fifths") == fifths
    assert key.findtext("mode") == mode


def test_missing_key_falls_back_to_no_accidentals() -> None:
    """A timeline that measured no key still writes a legal signature."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),))
    key = _measure(root, 0, 1).find("attributes/key")
    assert key is not None
    assert key.findtext("fifths") == "0"
    assert key.findtext("mode") == "major"


def test_both_exporters_write_the_same_key() -> None:
    """One timeline cannot export two songs in two different keys.

    The MIDI key meta event and the MusicXML ``<fifths>`` both read
    :attr:`KeySignature.fifths`, so a drift between the writers is caught here
    rather than in a DAW that imports something else than the score shows.
    """
    tracks = (_lead((Note(60, 0.0, 0.5),)),)
    for key_number in range(24):
        for major in (True, False):
            key = KeySignature(key_number, major)
            timeline = _timeline(tracks, 8.0, key, None)
            score = ET.fromstring(score_bytes(timeline, 4, 4, "ez-comfy-stack"))
            element = _measure(score, 0, 1).find("attributes/key")
            assert element is not None, f"{key.name} writes a key signature"
            fifths = int(element.findtext("fifths") or "0")
            conductor = parse_midi(midi_bytes(timeline))[0]
            payloads = [
                event.payload
                for event in conductor.events
                if event.kind == "meta" and event.status == META_KEY_SIGNATURE
            ]
            assert len(payloads) == 1, f"{key.name} writes one key event"
            raw = payloads[0][0]
            signed = raw - 256 if raw > 127 else raw
            assert signed == fifths, f"{key.name}: MIDI {signed}, score {fifths}"
            assert payloads[0][1] == (0 if major else 1), f"{key.name} mode byte"


def test_pitched_note_children_follow_the_musicxml_sequence() -> None:
    """Children are (chord), pitch, duration, instrument, voice, type."""
    root = _root((_lead((Note(60, 0.0, 0.5), Note(61, 0.0, 0.5))),))
    notes = _notes(root, 0, 1)
    assert _tags(notes[0]) == ("pitch", "duration", "voice", "type")
    assert _tags(notes[1]) == ("chord", "pitch", "duration", "voice", "type")
    assert notes[0].findtext("voice") == "1"
    assert notes[0].findtext("type") == "quarter"
    assert notes[0].find("chord") is None


def test_chromatic_pitch_carries_an_alter_and_natural_pitch_omits_it() -> None:
    """Spelling is by sharps, and an unaltered step writes no alter."""
    root = _root((_lead((Note(61, _at(0.0), 0.5), Note(60, _at(1.0), 0.5))),))
    sharp, natural = _notes(root, 0, 1)[:2]
    assert _tags(_child(sharp, "pitch")) == ("step", "alter", "octave")
    assert sharp.findtext("pitch/step") == "C"
    assert sharp.findtext("pitch/alter") == "1"
    assert sharp.findtext("pitch/octave") == "4"
    assert _tags(_child(natural, "pitch")) == ("step", "octave")
    assert natural.findtext("pitch/step") == "C"
    assert natural.findtext("pitch/octave") == "4"


def test_chord_shares_the_shortest_duration_of_the_column() -> None:
    """Every voice in a chord takes the shortest written length."""
    root = _root((_lead((Note(60, 0.0, 1.0), Note(64, 0.0, 0.5), Note(67, 0.0, 1.0))),))
    notes = _notes(root, 0, 1)
    assert len(notes) == 4, "the chord plus the rest that fills to the barline"
    chord = notes[:3]
    assert [_tags(note) for note in chord] == [
        ("pitch", "duration", "voice", "type"),
        ("chord", "pitch", "duration", "voice", "type"),
        ("chord", "pitch", "duration", "voice", "type"),
    ]
    assert [_note_shape(note)[1:] for note in chord] == [("96", "quarter")] * 3
    assert [note.findtext("pitch/octave") for note in chord] == ["4", "4", "4"]
    assert _note_shape(notes[3]) == (("rest", "duration", "voice", "type"), "288", "half")


def test_document_never_writes_velocity_or_midi_unpitched_in_a_note() -> None:
    """Neither element exists in MusicXML 4.0, so a note may not hold one."""
    root = _root(
        (
            _lead((Note(60, 0.0, 0.5), Note(61, 0.0, 0.5))),
            _kit((Note(36, 0.0, 0.5), Note(38, _at(1), 0.5))),
        )
    )
    forbidden = frozenset({"velocity", "midi-unpitched"})
    for note in root.iter("note"):
        inside = {child.tag for child in note} | {
            grandchild.tag for child in note for grandchild in child
        }
        assert not forbidden.intersection(inside), f"note holds a non-4.0 child: {inside}"
    assert list(root.iter("midi-unpitched")), "the kit must still declare its MIDI numbers"
    assert _unpitched_parent_tags(root) == {"midi-instrument"}


def test_unpitched_note_references_its_own_drum_instrument() -> None:
    """Each kit piece is one score instrument carrying its MIDI number."""
    kit = _kit((Note(36, 0.0, 0.5), Note(38, _at(1), 0.5), Note(70, _at(2), 0.5)))
    root = _root((kit,))
    score_part = root.find("part-list/score-part")
    assert score_part is not None
    declared = score_part.findall("score-instrument")
    assert [instrument.get("id") for instrument in declared] == ["P1-I1", "P1-I2", "P1-I3"]
    assert [instrument.findtext("instrument-name") for instrument in declared] == [
        "Drums 36",
        "Drums 38",
        "Drums 70",
    ]
    midi = score_part.findall("midi-instrument")
    assert [instrument.get("id") for instrument in midi] == ["P1-I1", "P1-I2", "P1-I3"]
    assert [instrument.findtext("midi-unpitched") for instrument in midi] == ["36", "38", "70"]
    assert [instrument.findtext("midi-channel") for instrument in midi] == ["10", "10", "10"]
    assert all(instrument.find("midi-program") is None for instrument in midi)
    assert [_tags(instrument) for instrument in midi] == [
        ("midi-channel", "midi-unpitched", "volume", "pan")
    ] * 3
    notes = _notes(root, 0, 1)
    assert _tags(notes[0]) == ("unpitched", "duration", "instrument", "voice", "type")
    assert _instrument_refs(notes) == ["P1-I1", "P1-I2", "P1-I3"]


def test_unpitched_note_carries_a_display_position() -> None:
    """An unpitched note needs its staff position spelled out."""
    root = _root((_kit((Note(36, 0.0, 0.5), Note(70, _at(1), 0.5))),))
    kick, unknown = _notes(root, 0, 1)[:2]
    assert _tags(_child(kick, "unpitched")) == ("display-step", "display-octave")
    assert (
        kick.findtext("unpitched/display-step"),
        kick.findtext("unpitched/display-octave"),
    ) == ("C", "1")
    assert (
        unknown.findtext("unpitched/display-step"),
        unknown.findtext("unpitched/display-octave"),
    ) == ("B", "2")


def test_drum_display_uses_the_kit_table_and_a_fallback() -> None:
    """Known pads read as a kit; anything else lands on the middle space."""
    assert _drum_display(36) == ("C", 1)
    assert _drum_display(49) == ("A", 3)
    assert _drum_display(70) == ("B", 2)


def test_instrument_ids_are_empty_for_a_melodic_or_silent_lane() -> None:
    """Only a kit lane with hits needs one instrument per drum."""
    assert instrument_ids(_lead((Note(60, 0.0, 0.5),)), "P1") == {}
    assert instrument_ids(_kit(()), "P1") == {}
    assert instrument_ids(_kit((Note(38, 0.0, 0.5), Note(36, _at(1), 0.5))), "P1") == {
        36: "P1-I1",
        38: "P1-I2",
    }


def test_midi_instruments_cover_program_and_unpitched_lanes() -> None:
    """The two pitch fields are mutually exclusive per declaration."""
    assert _midi_instruments(_lead((Note(60, 0.0, 0.5),)), "P2") == [("P2-I1", 80, None)]
    assert _midi_instruments(_kit(()), "P1") == [("P1-I1", None, None)]
    assert _midi_instruments(_kit((Note(36, 0.0, 0.5),)), "P1") == [("P1-I1", None, 36)]


def test_melodic_lane_declares_one_instrument_with_a_program() -> None:
    """A melodic part is one instrument, and MIDI programs are one-based."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),))
    score_part = root.find("part-list/score-part")
    assert score_part is not None
    assert _tags(score_part) == ("part-name", "score-instrument", "midi-instrument")
    assert score_part.findtext("part-name") == "Lead"
    instrument = _child(score_part, "midi-instrument")
    assert instrument.get("id") == "P1-I1"
    assert instrument.findtext("midi-program") == "81"
    assert instrument.findtext("midi-channel") == "4"
    assert instrument.findtext("volume") == "80"
    assert instrument.findtext("pan") == "0"
    assert instrument.find("midi-unpitched") is None


def test_rests_fill_before_the_first_note_and_to_the_barline() -> None:
    """Silence around a note is written as real rests, not left blank."""
    root = _root((_lead((Note(60, _at(2.0), 0.5),)),))
    assert [_note_shape(note) for note in _notes(root, 0, 1)] == [
        (("rest", "duration", "voice", "type"), "192", "half"),
        (("pitch", "duration", "voice", "type"), "96", "quarter"),
        (("rest", "duration", "voice", "type"), "96", "quarter"),
    ]


def test_a_note_crossing_the_barline_is_trimmed_not_tied() -> None:
    """Overflow is cut at the bar rather than split into a tie pair."""
    root = _root((_lead((Note(60, _at(3.5), 3.0),)),), duration_s=2 * _BAR_S)
    assert [_note_shape(note) for note in _notes(root, 0, 1)] == [
        (("rest", "duration", "voice", "type"), "336", "half"),
        (("pitch", "duration", "voice", "type"), "48", "eighth"),
    ]
    assert [_note_shape(note) for note in _notes(root, 0, 2)] == [
        (("rest", "duration", "voice", "type"), "384", "whole")
    ]


def test_empty_lane_still_writes_every_bar_as_a_rest() -> None:
    """A silent lane parses: one whole-bar rest per measure."""
    root = _root((_lead(()),), duration_s=6.0)
    measures = root.findall("part")[0].findall("measure")
    assert [measure.get("number") for measure in measures] == ["1", "2", "3", "4"]
    assert _tags(measures[0]) == ("direction", "attributes", "note")
    for measure in measures:
        assert _note_shape(_child(measure, "note")) == (
            ("rest", "duration", "voice", "type"),
            "384",
            "whole",
        )


def test_direction_holds_metronome_with_sound_as_a_sibling() -> None:
    """``<sound tempo=...>`` sits beside ``<direction-type>``, not inside it."""
    root = _root((_lead((Note(60, 0.0, 0.5),)), _kit((Note(36, 0.0, 0.5),))))
    for part_index in (0, 1):
        measure = _measure(root, part_index, 1)
        assert _tags(measure)[0] == "direction"
        direction = measure.find("direction")
        assert direction is not None
        assert direction.get("placement") == "above"
        assert _tags(direction) == ("direction-type", "sound")
        assert _tags(_child(direction, "direction-type")) == ("metronome",)
        assert _tags(_child(direction, "direction-type/metronome")) == (
            "beat-unit",
            "per-minute",
        )
        assert direction.findtext("direction-type/metronome/beat-unit") == "quarter"
        assert direction.findtext("direction-type/metronome/per-minute") == "120"
        assert _child(direction, "sound").get("tempo") == "120"
    assert _tags(_measure(root, 0, 1)) == ("direction", "attributes", "note", "note")
    assert _measure(root, 0, 2).find("direction") is None


def test_prepend_tempo_direction_skips_a_part_without_measures() -> None:
    """A part that holds nothing gets nothing, and its neighbour still plays."""
    timeline = _timeline((_lead((Note(60, 0.0, 0.5),)),))
    score = ET.Element("score-partwise")
    empty = ET.SubElement(score, "part")
    empty.set("id", "P0")
    filled = ET.SubElement(score, "part")
    filled.set("id", "P1")
    ET.SubElement(filled, "measure").set("number", "1")
    _prepend_tempo_direction(score, timeline)
    assert list(empty) == []
    assert _tags(filled) == ("measure",)
    measure = filled.find("measure")
    assert measure is not None
    assert _tags(measure) == ("direction",)
    assert _child(measure, "direction/sound").get("tempo") == "120"


def test_identification_writes_artist_and_album() -> None:
    """Tags the source carried become a performer and a rights line."""
    source = SourceInfo(
        path="take.wav",
        duration_s=8.0,
        sample_rate=16000,
        artist="Ada Sparks",
        album="Night Set",
    )
    root = _root((_lead((Note(60, 0.0, 0.5),)),), source=source)
    identification = root.find("identification")
    assert identification is not None
    assert _tags(identification) == ("creator", "rights", "encoding")
    creator = identification.find("creator")
    assert creator is not None
    assert creator.get("type") == "performer"
    assert creator.text == "Ada Sparks"
    assert identification.findtext("rights") == "Album: Night Set"
    assert identification.findtext("encoding/software") == "ez-comfy-stack"


def test_identification_omits_blank_tags_and_keeps_the_encoding() -> None:
    """Untagged audio writes no creator and no rights line."""
    blank = SourceInfo(path="take.wav", duration_s=8.0, sample_rate=16000)
    for track_source in (blank, None):
        root = _root((_lead((Note(60, 0.0, 0.5),)),), source=track_source)
        identification = root.find("identification")
        assert identification is not None
        assert _tags(identification) == ("encoding",)
        assert root.find("identification/creator") is None
        assert root.find("identification/rights") is None


def test_creator_attribution_reaches_the_encoding_element() -> None:
    """The caller names the software line of ``<identification>``."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),), creator="studio-tui")
    assert root.findtext("identification/encoding/software") == "studio-tui"


def test_time_signature_is_written_from_the_caller() -> None:
    """A waltz lane is notated in three, not smuggled into four."""
    root = _root((_lead((Note(60, 0.0, 0.5),)),), beats_per_bar=3, denominator=4)
    time = _measure(root, 0, 1).find("attributes/time")
    assert time is not None
    assert (time.findtext("beats"), time.findtext("beat-type")) == ("3", "4")
    assert _note_shape(_notes(root, 0, 1)[-1]) == (
        ("rest", "duration", "voice", "type"),
        "192",
        "half",
    )


def test_write_score_returns_the_bytes_it_wrote(tmp_path: Path) -> None:
    """The return value is the file size, and the file is the score."""
    timeline = _timeline((_lead((Note(60, 0.0, 0.5),)),))
    destination = tmp_path / "song.musicxml"
    written = write_score(timeline, str(destination))
    data = score_bytes(timeline)
    assert written == len(data)
    assert destination.read_bytes() == data
    assert written > 200
