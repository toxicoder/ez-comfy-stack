"""Canonical song timeline shared by the MIDI, MusicXML, and DAW exporters.

The transcriber produces a :class:`Timeline`; every exporter reads that one
document, so the DAW bundle, the ``.mid``, and the ``timeline.json`` can never
drift apart. Times are seconds on the way in (that is what the DSP measures)
and ticks on the way out (that is what a MIDI file stores); :class:`TempoMap`
is the single place that converts.

Tick resolution is :data:`TICKS_PER_QUARTER` for every file this package
writes, so a DAW that imports two artefacts from one export sees one grid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from ez_common.json_value import JsonMap, JsonObject

# One parsed ``timeline.json`` object on its way in, and one object on its way
# out. Both come from the repo-wide JSON vocabulary so this module never
# reaches for ``Any``.
_Record: TypeAlias = JsonMap
_Document: TypeAlias = JsonObject

# Quarter-note resolution written into every Standard MIDI File header. 480
# divides evenly by 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, so tuplets survive a
# quantize pass in any DAW.
TICKS_PER_QUARTER = 480

# Default tempo for a timeline nobody measured one for.
DEFAULT_BPM = 120.0

# MIDI note number range.
PITCH_MIN = 0
PITCH_MAX = 127

# MIDI velocity range; 0 means "note off" in the wire format, so it is never a
# legal attack.
VELOCITY_MIN = 1
VELOCITY_MAX = 127

# General MIDI channel 9 (0-based) is the percussion lane and ignores program
# changes.
DRUMS_CHANNEL = 9

# General MIDI programs the export lanes default to.
PROGRAM_ACOUSTIC_GRAND_PIANO = 0
PROGRAM_ELECTRIC_BASS = 33
PROGRAM_STRINGS = 48
PROGRAM_LEAD_SYNTH = 80

# Note names used by the key signature, sharp-of-C order.
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Accidentals of a major key signature, indexed by tonic pitch class. Every
# tonic whose sharp spelling stays inside the -7..7 a key signature can carry
# is spelled sharp to match :data:`NOTE_NAMES`; D#, G#, and A# are notated by
# their flat enharmonic because 9, 8, and 10 sharps are not writable.
_MAJOR_FIFTHS: tuple[int, ...] = (0, 7, 2, -3, 4, -1, 6, 1, -4, 3, -2, 5)


def _require_number(data: _Record, key: str) -> float:
    """Read a required numeric field out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The value as a float.
    Raises:
        ValueError: the field is absent or is not a number.
    """
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number, got {value!r}")
    return float(value)


def _require_int(data: _Record, key: str) -> int:
    """Read a required integer field out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The value as an int.
    Raises:
        ValueError: the field is absent or is not a number.
    """
    return round(_require_number(data, key))


def _optional_number(data: _Record, key: str) -> float | None:
    """Read an optional numeric field out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The value as a float, or None when the field is absent or null.
    Raises:
        ValueError: the field is present but is not a number.
    """
    if data.get(key) is None:
        return None
    return _require_number(data, key)


def _require_text(data: _Record, key: str) -> str:
    """Read a required string field out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The value as a string.
    Raises:
        ValueError: the field is absent or is not a string.
    """
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string, got {value!r}")
    return value


def _require_flag(data: _Record, key: str, default: bool = False) -> bool:
    """Read an optional boolean field out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
        default: Value to use when the field is absent.
    Returns:
        The value as a bool.
    Raises:
        ValueError: the field is present but is not a bool.
    """
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a bool, got {value!r}")
    return value


def _require_records(data: _Record, key: str) -> list[_Record]:
    """Read a list of nested records out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The nested records, empty when the field is absent.
    Raises:
        ValueError: the field is not a list, or holds a non-object entry.
    """
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list, got {value!r}")
    rows: list[_Record] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{key} must hold objects, got {item!r}")
        rows.append(item)
    return rows


def _require_record(data: _Record, key: str) -> _Record:
    """Read a required nested record out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The nested record.
    Raises:
        ValueError: the field is absent or is not an object.
    """
    record = _optional_record(data, key)
    if record is None:
        raise ValueError(f"{key} must be an object, got None")
    return record


def _optional_record(data: _Record, key: str) -> _Record | None:
    """Read an optional nested record out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The nested record, or None when the field is absent or null.
    Raises:
        ValueError: the field is present but is not an object.
    """
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object, got {value!r}")
    return value


def _require_numbers(data: _Record, key: str) -> list[float]:
    """Read a list of numbers out of a parsed record.

    Args:
        data: Parsed record.
        key: Field name.
    Returns:
        The numbers, empty when the field is absent.
    Raises:
        ValueError: the field is not a list, or holds a non-number.
    """
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list, got {value!r}")
    numbers: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{key} must hold numbers, got {item!r}")
        numbers.append(float(item))
    return numbers


@dataclass(frozen=True)
class Note:
    """One pitched event on the timeline.

    Args:
        pitch: MIDI note number.
        start_s: Attack time in seconds from the top of the song.
        duration_s: Sounding length in seconds.
        velocity: Attack strength, 1 to 127.
    """

    pitch: int
    start_s: float
    duration_s: float
    velocity: int = 96

    def __post_init__(self) -> None:
        """Reject a note the wire format cannot carry.

        Raises:
            ValueError: pitch, velocity, or duration is out of range.
        """
        if not PITCH_MIN <= self.pitch <= PITCH_MAX:
            raise ValueError(f"pitch {self.pitch} outside {PITCH_MIN}..{PITCH_MAX}")
        if not VELOCITY_MIN <= self.velocity <= VELOCITY_MAX:
            raise ValueError(
                f"velocity {self.velocity} outside {VELOCITY_MIN}..{VELOCITY_MAX}"
            )
        if self.start_s < 0.0:
            raise ValueError(f"start_s is negative: {self.start_s}")
        if self.duration_s <= 0.0:
            raise ValueError(f"duration_s must be positive, got {self.duration_s}")

    @property
    def end_s(self) -> float:
        """Return the release time.

        Returns:
            ``start_s + duration_s``.
        """
        return self.start_s + self.duration_s

    def to_dict(self) -> _Document:
        """Return the JSON form written to ``timeline.json``.

        Returns:
            Mapping with pitch, timing, and velocity.
        """
        return {
            "pitch": self.pitch,
            "start_s": round(self.start_s, 4),
            "duration_s": round(self.duration_s, 4),
            "velocity": self.velocity,
        }

    @staticmethod
    def from_dict(data: _Record) -> Note:
        """Rebuild a note from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent note.
        Raises:
            ValueError: a required key is absent or holds the wrong type.
        """
        return Note(
            pitch=_require_int(data, "pitch"),
            start_s=_require_number(data, "start_s"),
            duration_s=_require_number(data, "duration_s"),
            velocity=_require_int(data, "velocity") if "velocity" in data else 96,
        )


@dataclass(frozen=True)
class TempoPoint:
    """A tempo mark: ``bpm`` holds from ``time_s`` until the next mark.

    Args:
        time_s: Seconds from the top of the song.
        bpm: Beats per minute in force from ``time_s``.
    """

    time_s: float
    bpm: float

    def __post_init__(self) -> None:
        """Reject an unusable tempo mark.

        Raises:
            ValueError: time is negative or bpm is out of the sane range.
        """
        if self.time_s < 0.0:
            raise ValueError(f"time_s is negative: {self.time_s}")
        if not 20.0 <= self.bpm <= 300.0:
            raise ValueError(f"bpm {self.bpm} outside 20..300")

    def microseconds_per_beat(self) -> int:
        """Return the MIDI meta value for this mark.

        Returns:
            Microseconds per quarter note, rounded.
        """
        return round(60_000_000.0 / self.bpm)

    def to_dict(self) -> _Document:
        """Return the JSON form.

        Returns:
            Mapping with time and tempo.
        """
        return {"time_s": round(self.time_s, 4), "bpm": round(self.bpm, 3)}

    @staticmethod
    def from_dict(data: _Record) -> TempoPoint:
        """Rebuild a tempo mark from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent tempo mark.
        """
        return TempoPoint(
            time_s=_require_number(data, "time_s"), bpm=_require_number(data, "bpm")
        )


class TempoMap:
    """Seconds-to-ticks conversion driven by an ordered tempo list.

    Args:
        tempo_points: Marks in increasing time order; the first must start at
            time 0, and a single point is the ordinary fixed-tempo case.
        ticks_per_quarter: Tick resolution to convert against.
    """

    def __init__(
        self,
        tempo_points: tuple[TempoPoint, ...],
        ticks_per_quarter: int = TICKS_PER_QUARTER,
    ) -> None:
        """Build the map and precompute each segment's tick origin."""
        if not tempo_points:
            raise ValueError("tempo map needs at least one point")
        if ticks_per_quarter < 1:
            raise ValueError(f"ticks_per_quarter must be >= 1, got {ticks_per_quarter}")
        ordered = tuple(sorted(tempo_points, key=lambda p: p.time_s))
        if ordered[0].time_s != 0.0:
            raise ValueError("tempo map must start at time 0")
        self.points: tuple[TempoPoint, ...] = ordered
        self.ticks_per_quarter = ticks_per_quarter
        # Ticks at the exact second each point begins, so a lookup is a scan
        # of a short list with no re-integration.
        origins: list[float] = [0.0]
        for index in range(1, len(ordered)):
            elapsed = ordered[index].time_s - ordered[index - 1].time_s
            beats = elapsed * ordered[index - 1].bpm / 60.0
            origins.append(origins[index - 1] + beats * ticks_per_quarter)
        self._origins = tuple(origins)

    @classmethod
    def at_tempo(
        cls, bpm: float, ticks_per_quarter: int = TICKS_PER_QUARTER
    ) -> TempoMap:
        """Build a fixed-tempo map.

        Args:
            bpm: Tempo for the whole song.
            ticks_per_quarter: Tick resolution.
        Returns:
            Map with one mark at time 0.
        """
        return cls((TempoPoint(0.0, bpm),), ticks_per_quarter)

    def bpm_at(self, time_s: float) -> float:
        """Return the tempo in force at a time.

        Args:
            time_s: Seconds from the top of the song.
        Returns:
            Beats per minute of the latest mark at or before ``time_s``.
        """
        bpm = self.points[0].bpm
        for point in self.points:
            if point.time_s <= time_s:
                bpm = point.bpm
            else:
                break
        return bpm

    def to_ticks(self, time_s: float) -> int:
        """Convert a time in seconds to an absolute tick.

        Args:
            time_s: Seconds from the top of the song.
        Returns:
            Absolute tick, never negative.
        """
        if time_s <= 0.0:
            return 0
        index = 0
        for position, point in enumerate(self.points):
            if point.time_s <= time_s:
                index = position
            else:
                break
        point = self.points[index]
        beats = (time_s - point.time_s) * point.bpm / 60.0
        return max(0, round(self._origins[index] + beats * self.ticks_per_quarter))

    def to_seconds(self, tick: int) -> float:
        """Convert an absolute tick back to seconds.

        Args:
            tick: Absolute tick.
        Returns:
            Seconds from the top of the song.
        """
        if tick <= 0:
            return 0.0
        for index in range(len(self.points) - 1, -1, -1):
            if self._origins[index] <= tick:
                point = self.points[index]
                beats = (tick - self._origins[index]) / self.ticks_per_quarter
                return point.time_s + beats * 60.0 / point.bpm
        return 0.0

    def to_dict(self) -> _Document:
        """Return the JSON form.

        Returns:
            Mapping with the tick resolution and the mark list.
        """
        return {
            "ticks_per_quarter": self.ticks_per_quarter,
            "points": [point.to_dict() for point in self.points],
        }

    @staticmethod
    def from_dict(data: _Record) -> TempoMap:
        """Rebuild a map from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent map.
        """
        return TempoMap(
            tuple(TempoPoint.from_dict(item) for item in _require_records(data, "points")),
            _require_int(data, "ticks_per_quarter")
            if "ticks_per_quarter" in data
            else TICKS_PER_QUARTER,
        )


@dataclass(frozen=True)
class KeySignature:
    """A key signature for the score and the MIDI meta event.

    Args:
        key_number: 0 to 11 for C through B, then 12 to 23 for the minor keys.
        major: True for a major key, False for minor.
    """

    key_number: int
    major: bool = True

    def __post_init__(self) -> None:
        """Reject a key the MIDI meta event cannot encode.

        Raises:
            ValueError: key_number is out of range.
        """
        if not 0 <= self.key_number <= 23:
            raise ValueError(f"key_number {self.key_number} outside 0..23")

    @property
    def name(self) -> str:
        """Return a human-readable key name.

        Returns:
            Something like ``F# major`` or ``B minor``.
        """
        if self.major:
            return f"{NOTE_NAMES[self.key_number % 12]} major"
        return f"{NOTE_NAMES[self.key_number % 12]} minor"

    @property
    def fifths(self) -> int:
        """Return the accidental count this key's signature carries.

        This is the one circle-of-fifths number both exporters write: the MIDI
        key meta event takes it directly, and MusicXML writes it as
        ``<fifths>``. A minor key carries its relative major's signature, so
        the count comes from the tonic three semitones up.

        Returns:
            Between -7 and 7; negative counts flats.
        """
        tonic = self.key_number % 12
        if self.major:
            return _MAJOR_FIFTHS[tonic]
        return _MAJOR_FIFTHS[(tonic + 3) % 12]

    def to_dict(self) -> _Document:
        """Return the JSON form.

        Returns:
            Mapping with the key number and mode.
        """
        return {"key_number": self.key_number, "major": self.major}

    @staticmethod
    def from_dict(data: _Record) -> KeySignature:
        """Rebuild a key from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent key.
        """
        return KeySignature(
            key_number=_require_int(data, "key_number"),
            major=_require_flag(data, "major", True),
        )


@dataclass(frozen=True)
class Track:
    """One lane of notes, mapped to one MIDI track and one score part.

    Args:
        name: Lane name, used as the track name, the stem filename, and the
            score part name.
        channel: MIDI channel, 0 to 15.
        program: General MIDI program, or None to leave the channel program
            alone (the percussion lane carries no program change).
        notes: Notes in attack order.
        is_drums: True for the percussion lane, which ignores program changes.
    """

    name: str
    channel: int
    program: int | None = None
    notes: tuple[Note, ...] = ()
    is_drums: bool = False

    def __post_init__(self) -> None:
        """Reject a lane the wire format cannot carry.

        Raises:
            ValueError: name is blank, channel is out of range, or a program
                is set on the percussion lane.
        """
        if self.name.strip() == "":
            raise ValueError("track name is blank")
        if not 0 <= self.channel <= 15:
            raise ValueError(f"channel {self.channel} outside 0..15")
        if self.program is not None and not 0 <= self.program <= 127:
            raise ValueError(f"program {self.program} outside 0..127")
        if self.is_drums and self.program is not None:
            raise ValueError("drum track must not carry a program change")

    @property
    def slug(self) -> str:
        """Return the filename-safe lane name.

        Returns:
            Lowercase name with runs of non-alphanumerics folded to one
            underscore and stripped at both ends.
        """
        out: list[str] = []
        for char in self.name.lower():
            if char.isalnum():
                out.append(char)
            elif out and out[-1] != "_":
                out.append("_")
        return "".join(out).strip("_") or "track"

    @property
    def note_count(self) -> int:
        """Return how many notes the lane holds.

        Returns:
            Length of :attr:`notes`.
        """
        return len(self.notes)

    def to_dict(self) -> _Document:
        """Return the JSON form.

        Returns:
            Mapping with the lane identity and its notes.
        """
        return {
            "name": self.name,
            "slug": self.slug,
            "channel": self.channel,
            "program": self.program,
            "is_drums": self.is_drums,
            "notes": [note.to_dict() for note in self.notes],
        }

    @staticmethod
    def from_dict(data: _Record) -> Track:
        """Rebuild a lane from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent lane.
        """
        program = data.get("program")
        return Track(
            name=_require_text(data, "name"),
            channel=_require_int(data, "channel"),
            program=None if program is None else _require_int(data, "program"),
            notes=tuple(Note.from_dict(item) for item in _require_records(data, "notes")),
            is_drums=_require_flag(data, "is_drums"),
        )


@dataclass(frozen=True)
class SourceInfo:
    """Provenance for the audio the timeline was transcribed from.

    Args:
        path: Path of the source audio file.
        duration_s: Measured length of the source in seconds.
        sample_rate: Sample rate the analysis ran at.
        artist: Artist tag read from the source, when it carried one.
        title: Title tag read from the source, when it carried one.
        album: Album tag read from the source, when it carried one.
        bpm_hint: Tempo the source claimed, when a tag or an operator gave one.
    """

    path: str
    duration_s: float
    sample_rate: int
    artist: str = ""
    title: str = ""
    album: str = ""
    bpm_hint: float | None = None

    def to_dict(self) -> _Document:
        """Return the JSON form.

        Returns:
            Mapping with the source identity and tags.
        """
        return {
            "path": self.path,
            "duration_s": round(self.duration_s, 4),
            "sample_rate": self.sample_rate,
            "artist": self.artist,
            "title": self.title,
            "album": self.album,
            "bpm_hint": None if self.bpm_hint is None else round(self.bpm_hint, 3),
        }

    @staticmethod
    def from_dict(data: _Record) -> SourceInfo:
        """Rebuild provenance from its JSON form.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent provenance record.
        """
        return SourceInfo(
            path=_require_text(data, "path"),
            duration_s=_require_number(data, "duration_s"),
            sample_rate=_require_int(data, "sample_rate"),
            artist=_require_text(data, "artist") if "artist" in data else "",
            title=_require_text(data, "title") if "title" in data else "",
            album=_require_text(data, "album") if "album" in data else "",
            bpm_hint=_optional_number(data, "bpm_hint"),
        )


@dataclass(frozen=True)
class Timeline:
    """The transcribed song: tempo, grid, key, and lanes.

    Args:
        title: Song name for the score header and the MIDI marker track.
        duration_s: Length of the source in seconds.
        tempo_map: Tempo the export writes.
        beats: Beat grid times in seconds, the raw timeline a human edits.
        tracks: Lanes, in the order they are written to disk.
        key: Key signature, when one was estimated.
        source: Provenance of the audio behind the timeline.
        confidence: Mean note-detection confidence, 0 to 1, when the
            transcriber could score its own work.
    """

    title: str
    duration_s: float
    tempo_map: TempoMap
    beats: tuple[float, ...] = ()
    tracks: tuple[Track, ...] = ()
    key: KeySignature | None = None
    source: SourceInfo | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        """Reject a timeline an exporter could not write.

        Raises:
            ValueError: title is blank, duration is not positive, or two lanes
                share a MIDI channel.
        """
        if self.title.strip() == "":
            raise ValueError("title is blank")
        if self.duration_s < 0.0:
            raise ValueError(f"duration_s is negative: {self.duration_s}")
        seen: set[int] = set()
        for track in self.tracks:
            if track.channel in seen:
                raise ValueError(f"channel {track.channel} used by two lanes")
            seen.add(track.channel)

    @property
    def bpm(self) -> float:
        """Return the opening tempo.

        Returns:
            Tempo of the first tempo mark.
        """
        return self.tempo_map.points[0].bpm

    @property
    def note_count(self) -> int:
        """Return the total notes across every lane.

        Returns:
            Sum of the lane note counts.
        """
        return sum(track.note_count for track in self.tracks)

    @property
    def end_beat(self) -> float:
        """Return the beat number the song ends on.

        Returns:
            Beat index of the last note release, or 0.0 for an empty song.
        """
        latest = 0.0
        for track in self.tracks:
            for note in track.notes:
                latest = max(latest, note.end_s)
        latest = max(latest, self.duration_s)
        if self.beats:
            return float(sum(1 for beat in self.beats if beat <= latest))
        return latest * self.bpm / 60.0

    def note_events(self) -> tuple[tuple[Track, Note], ...]:
        """Return every note paired with its lane.

        Returns:
            Lane and note pairs, sorted by attack time then pitch.
        """
        pairs = [(track, note) for track in self.tracks for note in track.notes]
        return tuple(sorted(pairs, key=lambda pair: (pair[1].start_s, pair[1].pitch)))

    def to_dict(self) -> _Document:
        """Return the document written to ``timeline.json``.

        Returns:
            Mapping holding the whole song.
        """
        return {
            "format": "ez-comfy-stack.timeline/1",
            "title": self.title,
            "duration_s": round(self.duration_s, 4),
            "tempo_map": self.tempo_map.to_dict(),
            "beats": [round(beat, 4) for beat in self.beats],
            "key": None if self.key is None else self.key.to_dict(),
            "confidence": None if self.confidence is None else round(self.confidence, 4),
            "source": None if self.source is None else self.source.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks],
        }

    @staticmethod
    def from_dict(data: _Record) -> Timeline:
        """Rebuild a timeline from the ``timeline.json`` document.

        Args:
            data: Mapping produced by :meth:`to_dict`.
        Returns:
            Equivalent timeline.
        Raises:
            ValueError: the document is not a timeline this package writes.
        """
        flavour = data.get("format")
        if flavour not in (None, "ez-comfy-stack.timeline/1"):
            raise ValueError(f"unknown timeline format {flavour!r}")
        key = _optional_record(data, "key")
        source = _optional_record(data, "source")
        tempo_map = _require_record(data, "tempo_map")
        return Timeline(
            title=_require_text(data, "title"),
            duration_s=_require_number(data, "duration_s"),
            tempo_map=TempoMap.from_dict(tempo_map),
            beats=tuple(_require_numbers(data, "beats")),
            tracks=tuple(Track.from_dict(item) for item in _require_records(data, "tracks")),
            key=None if key is None else KeySignature.from_dict(key),
            source=None if source is None else SourceInfo.from_dict(source),
            confidence=_optional_number(data, "confidence"),
        )
