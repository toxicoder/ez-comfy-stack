"""Bundle a song into the files a human finishes in a real DAW.

This module is the hand-off. The stack prototypes a track with AI; a person
then finishes it in a conventional sequencer, and a sequencer needs the notes,
not a flattened mix. Every song therefore ships twice: once as the rendered
master, and once as this bundle - Standard MIDI File, MusicXML, the timeline
JSON it was derived from, one MIDI plus one band-limited WAV stem per lane, and
a short import guide.

Nothing here needs a third-party DSP or MIDI library. MIDI and MusicXML are
written from :mod:`ez_music.timeline`, which is the single source of truth, so
the bundle can be regenerated from the JSON alone. ffmpeg supplies the stems
because it is already the stack's audio decoder.

The bundle is self-contained on purpose: the master is copied in, and
``manifest.json`` records a SHA-256 per file, so a bundle handed to a mixing
engineer can be checked byte for byte after the trip.
"""

from __future__ import annotations

import hashlib
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ez_common.json_value import Json, JsonObject
from ez_music.fs import write_json
from ez_music.midi_file import write_midi
from ez_music.musicxml import write_score
from ez_music.timeline import PITCH_MAX, PITCH_MIN, SourceInfo, Timeline, Track
from ez_music.transcribe import AnalysisSettings, transcribe

BUNDLE_FORMAT = "ez-comfy-stack.daw-bundle/1"
"""Version tag written into every manifest."""

STEMS_DIR = "stems"
"""Subdirectory holding per-lane MIDI and WAV stems."""

AUDIO_DIR = "audio"
"""Subdirectory holding the copied master."""

MANIFEST_NAME = "manifest.json"
"""Machine-readable inventory at the bundle root."""

PROJECT_NOTES_NAME = "project.md"
"""Human-facing import guide at the bundle root."""

TIMELINE_NAME = "timeline.json"
"""The timeline JSON the whole bundle is derived from."""

FALLBACK_SAMPLE_RATE = 44100
"""Sample rate assumed when a master reports none."""

STEM_LOW_HZ = 20.0
"""Audible floor a stem's band split may reach."""

STEM_HIGH_HZ = 20000.0
"""Audible ceiling a stem's band split may reach."""

_STEM_BAND_MARGIN = 1.6
"""How far past the lane's own pitch range the band split reaches."""

_PROBE_TIMEOUT_S = 30
"""How long ffprobe may take to report one master."""

_DAW_NOTES: tuple[tuple[str, str], ...] = (
    (
        "Ableton Live",
        "Drag the .mid in and choose \"Extract and Merge Audio/MIDI\" only if "
        "you want the master aligned to the grid; a plain drag lands every lane "
        "on its own MIDI track with the tempo map already set.",
    ),
    (
        "GarageBand / Logic Pro",
        "File > Import > Audio File and pick the .mid. Logic asks whether to "
        "import as one track or one track per MIDI channel; choose one per "
        "channel, then swap each Software Instrument's patch.",
    ),
    (
        "Reaper",
        "Insert > Media Item and pick the .mid; accept \"stretch loops to "
        "match project tempo\" = No so the embedded tempo map survives. Open "
        "the MIDI items in the built-in editor or click through to ReaControl.",
    ),
    (
        "FL Studio",
        "Drag the .mid into the playlist, then use File > Export > MusicXML "
        "only as a round trip; FL reads the MIDI and maps channels from the "
        "MIDI channels written here.",
    ),
    (
        "MuseScore / notation",
        "Open the .musicxml directly. Drum notes arrive as unpitched notes on "
        "a 5-line percussion staff with the MIDI number attached, so the "
        "kit maps onto a mapped percussion instrument without redrawing.",
    ),
)
"""Import steps for the sequencers a human finishes a prototype in.

Named here as nominative references in a guide, never as catalog prompts or
model pins.
"""


class ExportError(RuntimeError):
    """Raised when a bundle cannot be written."""


@dataclass(frozen=True)
class ExportResult:
    """What one bundle run produced.

    Attributes:
        directory: Absolute path of the bundle folder.
        title: Song title used for file names.
        slug: Filename-safe title.
        files: Bundle-relative paths written, manifest last.
        lanes: Lane names, in bundle order.
        note_count: Notes carried into the bundle.
        bpm: Opening tempo.
        key_name: Key name, or an empty string when unclassified.
        duration_s: Master length in seconds.
    """

    directory: str
    title: str
    slug: str
    files: tuple[str, ...]
    lanes: tuple[str, ...]
    note_count: int
    bpm: float
    key_name: str
    duration_s: float

    def path(self, relative: str) -> str:
        """Return the absolute path of one bundle-relative file.

        Args:
            relative: Path as recorded in :attr:`files`.
        Returns:
            Joined absolute path.
        """
        return str(Path(self.directory) / relative)


def slugify(text: str) -> str:
    """Fold a title into a filename-safe slug.

    Args:
        text: Song title.
    Returns:
        Lowercase alphanumeric words joined by single underscores.
    Raises:
        ValueError: nothing alphanumeric survived.
    """
    out: list[str] = []
    for char in text.lower():
        if char.isalnum():
            out.append(char)
        elif out and out[-1] != "_":
            out.append("_")
    while out and out[-1] == "_":
        out.pop()
    slug = "".join(out)
    if slug == "":
        raise ValueError(f"title has no filename-safe characters: {text!r}")
    return slug


def stem_file_name(index: int, track: Track) -> str:
    """Return the ordered stem basename for one lane.

    Args:
        index: Zero-based lane position.
        track: Lane being exported.
    Returns:
        ``NN-lane`` with no extension, so the caller can add ``.mid`` or
        ``.wav`` and the two always sort together.
    """
    return f"{index + 1:02d}-{track.slug}"


def probe_audio(path: str) -> tuple[float, int]:
    """Read a master's duration and sample rate with ffprobe.

    Args:
        path: Audio file to probe.
    Returns:
        ``(duration_s, sample_rate)``.
    Raises:
        ExportError: ffprobe failed or reported nothing usable.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=sample_rate",
        "-of",
        "default=noprint_wrappers=1",
        path,
    ]
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, host ffmpeg
            command,
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExportError(f"ffprobe timed out on {path}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        reason = detail[-1] if detail else f"exit {completed.returncode}"
        raise ExportError(f"ffprobe failed on {path}: {reason}")
    duration = 0.0
    sample_rate = FALLBACK_SAMPLE_RATE
    for line in completed.stdout.splitlines():
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not value:
            continue
        try:
            if key == "duration":
                duration = float(value)
            elif key == "sample_rate" and int(value) > 0:
                sample_rate = int(value)
        except ValueError:
            continue
    if duration <= 0.0:
        raise ExportError(f"ffprobe reported no duration for {path}")
    return duration, sample_rate


def band_for_track(track: Track) -> tuple[float, float]:
    """Return the band to isolate when rendering one lane's stem.

    The band comes from the lane's own notes rather than from the analyser's
    lane spec, so a hand-authored timeline gets a sensible stem too.

    Args:
        track: Lane to size.
    Returns:
        ``(low_hz, high_hz)`` clamped into the audible range.
    """
    pitches = [note.pitch for note in track.notes]
    if not pitches:
        return (STEM_LOW_HZ, STEM_HIGH_HZ)
    low_pitch = max(PITCH_MIN, min(pitches) - 3)
    high_pitch = min(PITCH_MAX, max(pitches) + 3)
    low_hz = _pitch_hz(low_pitch) / _STEM_BAND_MARGIN
    high_hz = _pitch_hz(high_pitch) * _STEM_BAND_MARGIN
    low = max(STEM_LOW_HZ, min(low_hz, STEM_HIGH_HZ))
    high = max(low + 20.0, min(high_hz, STEM_HIGH_HZ))
    return (low, high)


def _pitch_hz(pitch: int) -> float:
    """Return the frequency of a MIDI pitch.

    Args:
        pitch: MIDI note number.
    Returns:
        Frequency in hertz.
    """
    return 440.0 * math.pow(2.0, (pitch - 69) / 12.0)


def write_stem_midi(timeline: Timeline, track: Track, path: str) -> int:
    """Write one lane as its own single-track MIDI file.

    Args:
        timeline: Song the lane belongs to (supplies the tempo map).
        track: Lane to render.
        path: Destination ``.mid`` path.
    Returns:
        Bytes written.
    """
    solo = Track(
        name=track.name,
        channel=track.channel,
        program=track.program,
        notes=track.notes,
        is_drums=track.is_drums,
    )
    single = Timeline(
        title=f"{timeline.title} - {track.name}",
        duration_s=timeline.duration_s,
        tempo_map=timeline.tempo_map,
        beats=timeline.beats,
        tracks=(solo,),
        key=timeline.key,
        source=timeline.source,
        confidence=timeline.confidence,
    )
    return write_midi(single, path)


def write_stem_wav(source_audio: str, track: Track, path: str) -> int:
    """Render one lane's band-limited WAV stem with ffmpeg.

    Args:
        source_audio: Master to filter.
        track: Lane whose band defines the filter.
        path: Destination ``.wav`` path.
    Returns:
        Bytes written.
    Raises:
        ExportError: ffmpeg reported a failure.
    """
    low, high = band_for_track(track)
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        source_audio,
        "-af",
        f"highpass=f={low:.1f},lowpass=f={high:.1f}",
        "-ac",
        "2",
        path,
    ]
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, host ffmpeg
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExportError(f"ffmpeg timed out rendering stem {path}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        reason = detail[-1] if detail else f"exit {completed.returncode}"
        raise ExportError(f"ffmpeg failed on stem {path}: {reason}")
    return Path(path).stat().st_size


def project_notes(timeline: Timeline, bundle_files: tuple[str, ...]) -> str:
    """Render the import guide that ships inside the bundle.

    Args:
        timeline: Song the bundle carries.
        bundle_files: Relative paths to list in the inventory section.
    Returns:
        Markdown text.
    """
    key_name = timeline.key.name if timeline.key is not None else "unclassified"
    lines = [
        f"# {timeline.title}",
        "",
        "AI-prototyped master with its note data, ready for a human pass.",
        "",
        "## Session",
        "",
        f"- Tempo: {timeline.bpm:.1f} BPM",
        f"- Key: {key_name}",
        f"- Length: {timeline.duration_s:.2f} s ({timeline.end_beat:.1f} beats)",
        f"- Notes: {timeline.note_count} across {len(timeline.tracks)} lanes",
        "",
        "## Lanes",
        "",
        "| Lane | MIDI ch | Program | Notes | Kit |",
        "| --- | --- | --- | --- | --- |",
    ]
    for track in timeline.tracks:
        program = "-" if track.program is None else str(track.program)
        kit = "drum map" if track.is_drums else "melodic"
        lines.append(
            f"| {track.name} | {track.channel} | {program} | "
            f"{track.note_count} | {kit} |"
        )
    lines += ["", "## Files", ""]
    for relative in bundle_files:
        lines.append(f"- `{relative}`")
    lines += ["", "## Import", ""]
    for daw, instruction in _DAW_NOTES:
        lines.append(f"### {daw}")
        lines.append("")
        lines.append(instruction)
        lines.append("")
    lines += [
        "## What to fix by hand",
        "",
        "The transcriber is a fast first pass, not a proofread score:",
        "",
        "- Monophonic lanes (bass, topline) are the most reliable; keep their",
        "  phrasing and replace the patches.",
        "- Chord lanes are read three voices at a time, so expect missing inner",
        "  voices and duplicated octaves. Thin them out by ear.",
        "- Drums carry the kit map on channel 10, but ghost notes and hi-hat",
        "  pedalling are usually under-detected; redraw the groove where it",
        "  needs to feel human.",
        "- Tempo is estimated globally. If the master drifts, quantise the",
        "  lanes to a fixed grid and drop the tempo track.",
        "",
        "## Timeline",
        "",
        f"`{TIMELINE_NAME}` is the source of every MIDI and MusicXML file in",
        f"this folder, so `{BUNDLE_FORMAT}` consumers can rebuild the bundle",
        "without re-listening to the audio.",
        "",
    ]
    return "\n".join(lines)


def _digest(path: str) -> str:
    """Return the SHA-256 of a file.

    Args:
        path: File to hash.
    Returns:
        Lowercase hex digest.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_payload(
    timeline: Timeline,
    slug: str,
    digests: dict[str, str],
    *,
    source_audio: str | None,
) -> JsonObject:
    """Build the manifest document for a finished bundle.

    Args:
        timeline: Song the bundle carries.
        slug: Filename-safe title.
        digests: SHA-256 per bundle-relative path.
        source_audio: Master the bundle came from, when one was copied in.
    Returns:
        JSON-ready mapping.
    """
    key_name = timeline.key.name if timeline.key is not None else ""
    files: list[Json] = []
    for relative in sorted(digests):
        files.append({"path": relative, "sha256": digests[relative]})
    lanes: list[Json] = []
    for track in timeline.tracks:
        lanes.append(
            {
                "name": track.name,
                "channel": track.channel,
                "program": -1 if track.program is None else track.program,
                "notes": track.note_count,
                "drums": track.is_drums,
            }
        )
    payload: JsonObject = {
        "format": BUNDLE_FORMAT,
        "slug": slug,
        "title": timeline.title,
        "bpm": timeline.bpm,
        "key": key_name,
        "duration_s": timeline.duration_s,
        "ticks_per_quarter": timeline.tempo_map.ticks_per_quarter,
        "note_count": timeline.note_count,
        "lanes": lanes,
        "files": files,
    }
    if source_audio is not None:
        payload["source_audio"] = Path(source_audio).name
    return payload


def write_bundle(
    timeline: Timeline,
    out_dir: str,
    *,
    source_audio: str | None = None,
    beats_per_bar: int = 4,
    title: str | None = None,
) -> ExportResult:
    """Write every DAW-facing file for one song.

    Args:
        timeline: Song to export.
        out_dir: Directory the bundle is written into (created if needed).
        source_audio: Master to copy in and render stems from.
        beats_per_bar: Bar length used for the MusicXML engraving.
        title: Overrides the timeline title for file names.
    Returns:
        What was written.
    Raises:
        ExportError: a required file could not be produced.
    """
    name = timeline.title if title is None else title
    slug = slugify(name)
    bundle = Path(out_dir) / slug
    stems = bundle / STEMS_DIR
    bundle.mkdir(parents=True, exist_ok=True)
    stems.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    midi_path = f"{slug}.mid"
    write_midi(timeline, str(bundle / midi_path))
    written.append(midi_path)
    score_path = f"{slug}.musicxml"
    write_score(timeline, str(bundle / score_path), beats_per_bar=beats_per_bar)
    written.append(score_path)
    write_json(bundle / TIMELINE_NAME, timeline.to_dict())
    written.append(TIMELINE_NAME)

    for index, track in enumerate(timeline.tracks):
        stem = stem_file_name(index, track)
        relative_mid = f"{STEMS_DIR}/{stem}.mid"
        write_stem_midi(timeline, track, str(bundle / relative_mid))
        written.append(relative_mid)

    if source_audio is not None:
        audio_dir = bundle / AUDIO_DIR
        audio_dir.mkdir(parents=True, exist_ok=True)
        master_name = Path(source_audio).name
        shutil.copy2(source_audio, str(audio_dir / master_name))
        written.append(f"{AUDIO_DIR}/{master_name}")
        for index, track in enumerate(timeline.tracks):
            stem = stem_file_name(index, track)
            relative_wav = f"{STEMS_DIR}/{stem}.wav"
            write_stem_wav(source_audio, track, str(bundle / relative_wav))
            written.append(relative_wav)

    notes_text = project_notes(timeline, tuple(written))
    (bundle / PROJECT_NOTES_NAME).write_text(notes_text, encoding="utf-8")
    written.append(PROJECT_NOTES_NAME)

    digests = {relative: _digest(str(bundle / relative)) for relative in written}
    payload = manifest_payload(timeline, slug, digests, source_audio=source_audio)
    write_json(bundle / MANIFEST_NAME, payload)
    written.append(MANIFEST_NAME)

    key_name = timeline.key.name if timeline.key is not None else ""
    return ExportResult(
        directory=str(bundle.resolve()),
        title=name,
        slug=slug,
        files=tuple(written),
        lanes=tuple(track.name for track in timeline.tracks),
        note_count=timeline.note_count,
        bpm=timeline.bpm,
        key_name=key_name,
        duration_s=timeline.duration_s,
    )


def _source_info(
    path: str, duration_s: float, sample_rate: int
) -> SourceInfo:
    """Read a master's tags into a source record.

    Args:
        path: Master to tag-read.
        duration_s: Duration ffprobe reported.
        sample_rate: Sample rate ffprobe reported.

    Returns:
        A :class:`ez_music.timeline.SourceInfo` for the master.
    """
    artist = ""
    title_tag = ""
    album = ""
    try:
        # ``File`` reaches the mutagen top level through a private module, so
        # pyright calls it an unexported name while mypy sees the real symbol.
        from mutagen import File as MutagenFile  # pyright: ignore[reportPrivateImportUsage]

        tags = MutagenFile(path, easy=True)
    except Exception:  # noqa: BLE001 - a tag read must never break an export
        tags = None
    if tags is not None:
        artist = _first_tag(tags.get("artist"))
        title_tag = _first_tag(tags.get("title"))
        album = _first_tag(tags.get("album"))
    return SourceInfo(
        path=path,
        duration_s=duration_s,
        sample_rate=sample_rate,
        artist=artist,
        title=title_tag,
        album=album,
    )


def _first_tag(values: Json | None) -> str:
    """Return the first value of a tag list.

    Args:
        values: Whatever a tag reader handed back.
    Returns:
        First string in the list, or an empty string.
    """
    if isinstance(values, str):
        return values
    if isinstance(values, (list, tuple)) and values:
        first = values[0]
        if isinstance(first, str):
            return first
    return ""


def export_song(
    audio_path: str,
    out_dir: str,
    *,
    title: str | None = None,
    settings: AnalysisSettings | None = None,
    beats_per_bar: int = 4,
    with_stems: bool = True,
) -> ExportResult:
    """Transcribe one master and write its DAW bundle.

    Args:
        audio_path: Master to convert.
        out_dir: Directory the bundle is written into.
        title: Song title, defaulting to the master's tag or filename.
        settings: Analysis overrides.
        beats_per_bar: Bar length used for the MusicXML engraving.
        with_stems: Render band-limited WAV stems alongside the MIDI.
    Returns:
        What was written.
    Raises:
        ExportError: the master could not be probed or converted.
    """
    source = Path(audio_path)
    if not source.is_file():
        raise ExportError(f"no such audio file: {audio_path}")
    duration, sample_rate = probe_audio(audio_path)
    tag_title = title
    if tag_title is None:
        tag_title = _tagged_title(audio_path) or source.stem
    timeline = transcribe(audio_path, tag_title, settings or AnalysisSettings())
    timeline = Timeline(
        title=timeline.title,
        duration_s=timeline.duration_s,
        tempo_map=timeline.tempo_map,
        beats=timeline.beats,
        tracks=timeline.tracks,
        key=timeline.key,
        source=_source_info(audio_path, duration, sample_rate),
        confidence=timeline.confidence,
    )
    return write_bundle(
        timeline,
        out_dir,
        source_audio=audio_path if with_stems else None,
        beats_per_bar=beats_per_bar,
    )


def _tagged_title(audio_path: str) -> str:
    """Return a master's title tag when it has one.

    Args:
        audio_path: Master to tag-read.
    Returns:
        Title tag text, or an empty string.
    """
    info = _source_info(audio_path, 0.0, FALLBACK_SAMPLE_RATE)
    return str(getattr(info, "title", ""))


def _report(result: ExportResult) -> None:
    """Print a bundle summary for an operator.

    Args:
        result: Bundle to describe.
    """
    print(f"bundle {result.directory}")
    print(f"  title   {result.title}")
    print(f"  tempo   {result.bpm:.1f} BPM    key {result.key_name or '-'}")
    print(f"  length  {result.duration_s:.2f} s   notes {result.note_count}")
    print(f"  lanes   {', '.join(result.lanes)}")
    for relative in result.files:
        print(f"    {relative}")


def main(argv: list[str]) -> int:
    """Convert one master into a DAW bundle.

    Args:
        argv: Arguments after the program name.
    Returns:
        Process exit code.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="song-export",
        description="Convert a song into MIDI, MusicXML, and stems for a DAW.",
    )
    parser.add_argument("audio", help="master audio file to convert")
    parser.add_argument("out_dir", help="directory to write the bundle into")
    parser.add_argument("--title", default=None, help="song title override")
    parser.add_argument(
        "--beats-per-bar", type=int, default=4, help="bar length for MusicXML"
    )
    parser.add_argument(
        "--no-stems",
        action="store_true",
        help="skip the band-limited WAV stems",
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="keep the transcriber's raw note timing",
    )
    args = parser.parse_args(argv)
    settings = AnalysisSettings(quantize=not args.no_quantize)
    try:
        result = export_song(
            args.audio,
            args.out_dir,
            title=args.title,
            settings=settings,
            beats_per_bar=args.beats_per_bar,
            with_stems=not args.no_stems,
        )
    except (ExportError, ValueError) as exc:
        print(f"error: {exc}")
        return 1
    _report(result)
    return 0
