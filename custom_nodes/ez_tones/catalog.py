"""Data-driven tone catalog the operator can extend without code.

:data:`TONE_CATALOG` is the shipped pack: ringtone, notification, and
alarm rows across seven timbres, each validated against the duration
budgets Android tone packs are expected to meet. New tones come from a
JSON file: :func:`write_catalog_template` emits a file a human can edit
and :func:`load_catalog` merges it over the built-in rows, so adding a
tone never means editing Python.

Rows are frozen dataclasses, so a catalog can be handed to
:mod:`ez_tones.pack` and shared across renders safely.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, TypeAlias

from ez_common.json_value import Json, JsonMap, JsonObject

from .synth import TIMBRES, Motif, Timbre, motif_duration

ToneKind: TypeAlias = Literal["ringtone", "notification", "alarm"]
"""The three Android tone roles a pack ships."""

KINDS: tuple[ToneKind, ...] = ("ringtone", "notification", "alarm")
"""Every kind :class:`ToneSpec` accepts, in manifest order."""

KIND_FOLDERS: dict[ToneKind, str] = {
    "ringtone": "ringtones",
    "notification": "notifications",
    "alarm": "alarms",
}
"""Folder name each kind is exported into (Android convention)."""

NOTIFICATION_MIN_S = 2.0
"""Shortest notification tone: anything shorter is inaudible in a pocket."""

NOTIFICATION_MAX_S = 5.0
"""Longest notification tone: notifications loop, so they must not drone."""

RINGTONE_MIN_S = 3.0
"""Shortest ringtone a caller will actually notice."""

RINGTONE_MAX_S = 30.0
"""Android truncates ringtone previews past half a minute."""

ALARM_MIN_S = 4.0
"""Shortest alarm loop that can wake a sleeper."""

ALARM_MAX_S = 30.0
"""Longest alarm bed before it has to loop."""

BPM_MIN = 40
"""Slowest tempo the catalog accepts."""

BPM_MAX = 240
"""Fastest tempo the catalog accepts."""

PITCH_MIN = 21
"""Lowest MIDI note that stays audible on a phone speaker."""

PITCH_MAX = 108
"""Highest MIDI note the catalog accepts."""

TAG_MAX = 12
"""Store keyword budget per tone."""

DEFAULT_VELOCITY = 0.85
"""Velocity an operator row gets when it does not name one."""

DEFAULT_GAP_RATIO = 0.15
"""Fraction of every beat left as a rest, so steps do not blur together."""


@dataclass(frozen=True)
class ToneSpec:
    """One tone in the catalog.

    Attributes:
        slug: Stable file-safe id; also the export basename.
        name: Display name for the store listing.
        kind: Android role this tone is meant for.
        category: Store category bucket, for example ``organic``.
        mood: One-word feel, shown next to the name in the picker.
        timbre: Voice the synthesiser renders the motif with.
        bpm: Tempo the motif was written at.
        motif: Steps to render, in order.
        duration_s: Total motif length in seconds.
        loopable: True when the file is cut to loop cleanly.
        tags: Store keywords.
        channels: 1 for mono, 2 for stereo.
    """

    slug: str
    name: str
    kind: ToneKind
    category: str
    mood: str
    timbre: Timbre
    bpm: int
    motif: Motif
    duration_s: float
    loopable: bool
    tags: tuple[str, ...]
    channels: int = 1


def _motif(
    pitches: Sequence[int | None],
    beat_s: float,
    velocity: float = DEFAULT_VELOCITY,
    gap_ratio: float = DEFAULT_GAP_RATIO,
) -> Motif:
    """Expand a pitch list into evenly spaced steps.

    Args:
        pitches: MIDI notes to play in order; ``None`` is a rest.
        beat_s: Length of one beat in seconds.
        velocity: Gain every pitched step gets.
        gap_ratio: Fraction of each beat left silent between steps.

    Returns:
        Immutable motif.
    """
    hold = beat_s * (1.0 - min(max(gap_ratio, 0.0), 0.9))
    return tuple((pitch, round(hold, 4), velocity) for pitch in pitches)


def _tone(
    slug: str,
    name: str,
    kind: ToneKind,
    category: str,
    mood: str,
    timbre: Timbre,
    bpm: int,
    pitches: Sequence[int | None],
    tags: Sequence[str],
    *,
    velocity: float = DEFAULT_VELOCITY,
    gap_ratio: float = DEFAULT_GAP_RATIO,
    loopable: bool = False,
    channels: int = 1,
) -> ToneSpec:
    """Build one validated catalog row from a pitch list.

    Args:
        slug: Stable file-safe id.
        name: Display name.
        kind: Android role.
        category: Store category bucket.
        mood: One-word feel.
        timbre: Voice to render with.
        bpm: Tempo the pitches were written at.
        pitches: MIDI notes, ``None`` for a rest.
        tags: Store keywords.
        velocity: Gain for pitched steps.
        gap_ratio: Rest fraction of each beat.
        loopable: True when the export is cut to loop.
        channels: 1 for mono, 2 for stereo.

    Returns:
        A :class:`ToneSpec` whose duration is the sum of its steps.
    """
    motif = _motif(pitches, 60.0 / bpm, velocity, gap_ratio)
    return ToneSpec(
        slug=slug,
        name=name,
        kind=kind,
        category=category,
        mood=mood,
        timbre=timbre,
        bpm=bpm,
        motif=motif,
        duration_s=motif_duration(motif),
        loopable=loopable,
        tags=tuple(tag.strip().lower() for tag in tags if tag.strip()),
        channels=channels,
    )


# Each motif is written to sit inside its kind's duration budget; the
# catalog test asserts that budget holds for every row.
TONE_CATALOG: tuple[ToneSpec, ...] = (
    _tone(
        "soft-triple-tap",
        "Soft Triple Tap",
        "notification",
        "organic",
        "gentle",
        "marimba",
        132,
        (76, 79, 83, None, 83, 88),
        ("soft", "wood", "short", "chat"),
        loopable=True,
    ),
    _tone(
        "glass-hello",
        "Glass Hello",
        "notification",
        "bright",
        "airy",
        "glass",
        120,
        (84, None, 88, 91, None, 88),
        ("glass", "clean", "mail"),
        loopable=True,
    ),
    _tone(
        "woody-knock",
        "Woody Knock",
        "notification",
        "organic",
        "dry",
        "woody",
        150,
        (67, 67, None, 72, 67, None, 72, 76),
        ("wood", "knock", "todo"),
        loopable=True,
    ),
    _tone(
        "sine-chime",
        "Sine Chime",
        "notification",
        "minimal",
        "plain",
        "sine",
        126,
        (81, 86, 90, 86, 81, 93),
        ("minimal", "sine", "quiet"),
        loopable=True,
    ),
    _tone(
        "bell-post",
        "Bell Post",
        "notification",
        "bright",
        "clear",
        "bell",
        108,
        (88, 83, 91, 88, 83, 86),
        ("bell", "post", "clear"),
        loopable=True,
    ),
    _tone(
        "pluck-ping",
        "Pluck Ping",
        "notification",
        "playful",
        "snappy",
        "pluck",
        160,
        (79, None, 86, 84, 79, 86, None, 88),
        ("pluck", "snappy", "chat"),
        loopable=True,
    ),
    _tone(
        "synth-blip",
        "Synth Blip",
        "notification",
        "synth",
        "retro",
        "synth",
        168,
        (72, 79, 72, 84, 79, 72, 86, 79),
        ("synth", "retro", "blip"),
        loopable=True,
    ),
    _tone(
        "marimba-rise",
        "Marimba Rise",
        "notification",
        "organic",
        "upbeat",
        "marimba",
        144,
        (72, 74, 76, 79, 76, 79, 83, 79),
        ("marimba", "upbeat", "reward"),
        loopable=True,
    ),
    _tone(
        "glass-two-note",
        "Glass Two Note",
        "notification",
        "minimal",
        "calm",
        "glass",
        100,
        (83, 90, 83, 88, 95),
        ("minimal", "glass", "calm"),
        loopable=True,
    ),
    _tone(
        "message-harp",
        "Message Harp",
        "notification",
        "warm",
        "warm",
        "pluck",
        96,
        (76, 83, 88, None, 91),
        ("harp", "message", "warm"),
        loopable=True,
    ),
    _tone(
        "marimba-grove",
        "Marimba Grove",
        "ringtone",
        "organic",
        "warm",
        "marimba",
        112,
        (72, 76, 79, 76, 74, 79, 83, 79, 72, 76, 79, 84),
        ("marimba", "warm", "call", "world"),
        channels=2,
    ),
    _tone(
        "bell-tower",
        "Bell Tower",
        "ringtone",
        "bright",
        "stately",
        "bell",
        84,
        (76, 83, 88, 83, 76, None, 83, 88, 91, 88, 83, 79, 76, 83, 88, 91),
        ("bell", "classic", "call"),
    ),
    _tone(
        "glass-current",
        "Glass Current",
        "ringtone",
        "minimal",
        "flowing",
        "glass",
        120,
        (83, 86, 90, 86, 88, 90, 95, 90, 86, 88, 90, 93),
        ("glass", "ambient", "call"),
        channels=2,
    ),
    _tone(
        "pluck-drift",
        "Pluck Drift",
        "ringtone",
        "playful",
        "bouncy",
        "pluck",
        128,
        (74, 78, 81, 78, 74, 81, 78, 83, 81, 78, 74, 76),
        ("pluck", "playful", "call"),
    ),
    _tone(
        "woody-pulse",
        "Woody Pulse",
        "ringtone",
        "organic",
        "driving",
        "woody",
        138,
        (62, None, 69, 74, 69, None, 62, 74, 69, 76, 74, 69),
        ("wood", "percussive", "call"),
    ),
    _tone(
        "synth-orbit",
        "Synth Orbit",
        "ringtone",
        "synth",
        "wide",
        "synth",
        104,
        (67, 74, 79, 86, 79, 74, 67, 72, 79, 84, 79, 72),
        ("synth", "retro", "call"),
        channels=2,
    ),
    _tone(
        "sine-drift",
        "Sine Drift",
        "ringtone",
        "minimal",
        "plain",
        "sine",
        96,
        (72, 76, 79, 84, 79, 76, 74, 79, 81, 79, 76, 72),
        ("minimal", "sine", "quiet", "call"),
    ),
    _tone(
        "marimba-ascend",
        "Marimba Ascend",
        "ringtone",
        "upbeat",
        "bright",
        "marimba",
        124,
        (67, 71, 74, 79, 83, 86, 83, 79, 74, 71, 74, 86),
        ("marimba", "upbeat", "call"),
    ),
    _tone(
        "cedar-caller",
        "Cedar Caller",
        "ringtone",
        "warm",
        "mellow",
        "woody",
        92,
        (64, 71, 76, 71, 69, 76, 81, 76, 71, 69, 64, 71, 69, 76, 81, 83),
        ("wood", "mellow", "call"),
        channels=2,
    ),
    _tone(
        "sunrise-alarum",
        "Sunrise Alarum",
        "alarm",
        "bright",
        "firm",
        "bell",
        120,
        (84, 84, 88, 84, 91, 88, 84, 88, 91, 96, 91, 88),
        ("alarm", "bell", "wake"),
        loopable=True,
    ),
    _tone(
        "urgent-marimba",
        "Urgent Marimba",
        "alarm",
        "urgent",
        "insistent",
        "marimba",
        144,
        (76, 79, 76, 83, 79, 76, 83, 79, 76, 84, 83, 79),
        ("alarm", "urgent", "marimba"),
        loopable=True,
    ),
    _tone(
        "glass-siren",
        "Glass Siren",
        "alarm",
        "urgent",
        "piercing",
        "glass",
        150,
        (95, 98, 95, 98, 95, 100, 98, 100, 98, 100, 98, 95),
        ("alarm", "siren", "alert"),
        loopable=True,
    ),
    _tone(
        "pluck-urgent",
        "Pluck Urgent",
        "alarm",
        "urgent",
        "sharp",
        "pluck",
        150,
        (81, 81, 88, 81, 90, 88, 81, 88, 81, 90, 88, 81),
        ("alarm", "pluck", "alert"),
        loopable=True,
    ),
    _tone(
        "synth-wake",
        "Synth Wake",
        "alarm",
        "synth",
        "punchy",
        "synth",
        150,
        (72, 72, 79, 84, 79, 72, 84, 79, 72, 79, 84, 86),
        ("alarm", "synth", "wake"),
        loopable=True,
        channels=2,
    ),
    _tone(
        "woody-march",
        "Woody March",
        "alarm",
        "urgent",
        "steady",
        "woody",
        144,
        (65, 65, 72, 77, 72, 65, 77, 72, 65, 72, 77, 80),
        ("alarm", "wood", "march"),
        loopable=True,
    ),
)

_TEMPLATE_FIELDS: tuple[str, ...] = (
    "slug: file-safe id, unique, becomes the export basename",
    "name: display name in the store listing",
    "kind: ringtone | notification | alarm",
    "category: store bucket, for example organic or minimal",
    "mood: one-word feel shown in the picker",
    "timbre: " + " | ".join(TIMBRES),
    "bpm: tempo, 40..240",
    "motif: [[midi_or_null, duration_s, velocity], ...] (explicit steps)",
    "pitches: [midi_or_null, ...] (simple alternative to motif)",
    "beat_s: seconds per step; defaults to 60 / bpm (pitches form only)",
    "velocity: 0..1 gain for the pitches form",
    "gap_ratio: 0..0.9 rest fraction between steps (pitches form only)",
    "loopable: true when the file is cut to loop cleanly",
    "channels: 1 or 2",
    "tags: up to 12 store keywords",
)
"""Field reference written into the operator catalog template."""

_ALLOWED_KEYS = frozenset(
    {
        "slug",
        "name",
        "kind",
        "category",
        "mood",
        "timbre",
        "bpm",
        "tags",
        "motif",
        "pitches",
        "beat_s",
        "velocity",
        "gap_ratio",
        "loopable",
        "channels",
    }
)
"""Keys an operator row may use; anything else is a typo worth naming."""


def validate(spec: ToneSpec) -> None:
    """Check one row against the Play-friendly budgets.

    Args:
        spec: Catalog row to check.

    Raises:
        ValueError: any field is outside the budget its kind allows.
    """
    if spec.slug.strip() == "":
        raise ValueError("tone slug is empty")
    if spec.name.strip() == "":
        raise ValueError(f"{spec.slug}: name is empty")
    if spec.kind not in KINDS:
        raise ValueError(f"{spec.slug}: kind must be one of {KINDS}")
    if spec.timbre not in TIMBRES:
        raise ValueError(f"{spec.slug}: timbre must be one of {TIMBRES}")
    if not BPM_MIN <= spec.bpm <= BPM_MAX:
        raise ValueError(f"{spec.slug}: bpm must be {BPM_MIN}..{BPM_MAX}")
    if len(spec.tags) > TAG_MAX:
        raise ValueError(f"{spec.slug}: at most {TAG_MAX} tags")
    if spec.channels not in (1, 2):
        raise ValueError(f"{spec.slug}: channels must be 1 or 2")
    if not spec.motif:
        raise ValueError(f"{spec.slug}: motif is empty")
    for index, (pitch, duration_s, velocity) in enumerate(spec.motif):
        if pitch is not None and not PITCH_MIN <= pitch <= PITCH_MAX:
            raise ValueError(
                f"{spec.slug}: step {index} pitch {pitch} is outside "
                f"{PITCH_MIN}..{PITCH_MAX}"
            )
        if duration_s <= 0.0:
            raise ValueError(f"{spec.slug}: step {index} duration must be > 0")
        if pitch is not None and not 0.0 < velocity <= 1.0:
            raise ValueError(f"{spec.slug}: step {index} velocity must be in (0, 1]")
    _validate_duration(spec)


def _validate_duration(spec: ToneSpec) -> None:
    """Check the total length against the kind's budget.

    Args:
        spec: Catalog row to check.

    Raises:
        ValueError: the tone is too short or too long for its kind.
    """
    bounds = {
        "notification": (NOTIFICATION_MIN_S, NOTIFICATION_MAX_S),
        "ringtone": (RINGTONE_MIN_S, RINGTONE_MAX_S),
        "alarm": (ALARM_MIN_S, ALARM_MAX_S),
    }[spec.kind]
    if not bounds[0] <= spec.duration_s <= bounds[1]:
        raise ValueError(
            f"{spec.slug}: {spec.kind} must be {bounds[0]}..{bounds[1]} s, "
            f"got {spec.duration_s}"
        )


def tones_for(kind: ToneKind, catalog: Sequence[ToneSpec] = TONE_CATALOG) -> tuple[ToneSpec, ...]:
    """Rows of one kind, in catalog order.

    Args:
        kind: Kind to keep.
        catalog: Rows to filter; the shipped pack by default.

    Returns:
        Matching rows (empty when the kind is unused).
    """
    return tuple(spec for spec in catalog if spec.kind == kind)


def by_slug(slug: str, catalog: Sequence[ToneSpec] = TONE_CATALOG) -> ToneSpec | None:
    """Find one row by slug.

    Args:
        slug: Id to look up.
        catalog: Rows to search; the shipped pack by default.

    Returns:
        The row, or ``None`` when no slug matches.
    """
    for spec in catalog:
        if spec.slug == slug:
            return spec
    return None


def categories(catalog: Sequence[ToneSpec] = TONE_CATALOG) -> tuple[str, ...]:
    """Distinct category names.

    Args:
        catalog: Rows to read; the shipped pack by default.

    Returns:
        Sorted category names.
    """
    return tuple(sorted({spec.category for spec in catalog}))


def _as_str(value: Json, where: str, key: str) -> str:
    """Narrow a parsed value to a non-empty string.

    Args:
        value: Parsed value, or ``None`` when the key was absent.
        where: Row label for the error message.
        key: Field name being read.

    Returns:
        Stripped string.

    Raises:
        ValueError: the value is missing or not a string.
    """
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{where}: '{key}' must be a non-empty string")
    return value.strip()


def _as_float(value: Json, where: str, key: str) -> float:
    """Narrow a parsed value to a float.

    Args:
        value: Parsed value.
        where: Row label for the error message.
        key: Field name being read.

    Returns:
        The number as a float.

    Raises:
        ValueError: the value is missing, a bool, or not a number.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: '{key}' must be a number")
    return float(value)


def _as_int(value: Json, where: str, key: str) -> int:
    """Narrow a parsed value to a whole number.

    Args:
        value: Parsed value.
        where: Row label for the error message.
        key: Field name being read.

    Returns:
        The number as an int.

    Raises:
        ValueError: the value is missing, a bool, or not a number.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: '{key}' must be a whole number")
    if float(value) != float(int(value)):
        raise ValueError(f"{where}: '{key}' must be a whole number")
    return int(value)


def _opt_float(value: Json, default: float, where: str, key: str) -> float:
    """Read an optional number, falling back to ``default``.

    Args:
        value: Parsed value, or ``None`` when the key was absent.
        default: Value to use when the key is absent.
        where: Row label for the error message.
        key: Field name being read.

    Returns:
        The parsed number, or ``default``.

    Raises:
        ValueError: the value is present but not a number.
    """
    if value is None:
        return default
    return _as_float(value, where, key)


def _opt_flag(value: Json, default: bool, where: str, key: str) -> bool:
    """Read an optional boolean, falling back to ``default``.

    Args:
        value: Parsed value, or ``None`` when the key was absent.
        default: Value to use when the key is absent.
        where: Row label for the error message.
        key: Field name being read.

    Returns:
        The parsed flag, or ``default``.

    Raises:
        ValueError: the value is present but not a boolean.
    """
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{where}: '{key}' must be true or false")
    return value


def _as_tags(value: Json, where: str) -> tuple[str, ...]:
    """Read the keyword list.

    Args:
        value: Parsed ``tags`` value; ``None`` means no tags.
        where: Row label for the error message.

    Returns:
        Lower-cased, de-duplicated tags in order.

    Raises:
        ValueError: the value is present but not a list of strings.
    """
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{where}: 'tags' must be a list of strings")
    seen: list[str] = []
    for item in value:
        if not isinstance(item, str) or item.strip() == "":
            raise ValueError(f"{where}: 'tags' must be a list of strings")
        tag = item.strip().lower()
        if tag not in seen:
            seen.append(tag)
    return tuple(seen)


def _as_pitch_list(value: Json, where: str) -> tuple[int | None, ...]:
    """Read the simple ``pitches`` form.

    Args:
        value: Parsed ``pitches`` value.
        where: Row label for the error message.

    Returns:
        MIDI notes with ``None`` for rests.

    Raises:
        ValueError: the value is not a list of whole numbers or nulls.
    """
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where}: 'pitches' must be a non-empty list")
    out: list[int | None] = []
    for item in value:
        out.append(None if item is None else _as_int(item, where, "pitches"))
    return tuple(out)


def _as_motif(value: Json, where: str) -> Motif:
    """Read the explicit ``motif`` form.

    Args:
        value: Parsed ``motif`` value.
        where: Row label for the error message.

    Returns:
        Steps as ``(pitch_or_None, duration_s, velocity)``.

    Raises:
        ValueError: the value is not a list of three-item steps.
    """
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where}: 'motif' must be a non-empty list")
    steps: list[tuple[int | None, float, float]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, list) or len(raw) != 3:
            raise ValueError(f"{where}: motif step {index} must be [pitch, duration, velocity]")
        pitch, duration_s, velocity = raw
        steps.append(
            (
                None if pitch is None else _as_int(pitch, where, f"motif[{index}][0]"),
                _as_float(duration_s, where, f"motif[{index}][1]"),
                _as_float(velocity, where, f"motif[{index}][2]"),
            )
        )
    return tuple(steps)


def _row_to_spec(row: JsonMap, index: int) -> ToneSpec:
    """Turn one parsed JSON object into a validated row.

    Args:
        row: Parsed object from the operator file.
        index: Row position, used in error messages.

    Returns:
        Validated :class:`ToneSpec`.

    Raises:
        ValueError: a key is unknown, a field has the wrong type, or the
            row fails :func:`validate`.
    """
    where = f"tone {index}"
    unknown = sorted(set(row) - _ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"{where}: unknown key(s) {', '.join(unknown)}")
    slug = _as_str(row.get("slug"), where, "slug")
    where = f"tone {index} ({slug})"
    kind_value = row.get("kind")
    if not isinstance(kind_value, str) or kind_value not in KINDS:
        raise ValueError(f"{where}: 'kind' must be one of {', '.join(KINDS)}")
    timbre_value = row.get("timbre")
    if not isinstance(timbre_value, str) or timbre_value not in TIMBRES:
        raise ValueError(f"{where}: 'timbre' must be one of {', '.join(TIMBRES)}")
    kind: ToneKind = kind_value
    timbre: Timbre = timbre_value
    bpm = _as_int(row.get("bpm"), where, "bpm")
    motif = _motif_for(row, where, bpm)
    spec = ToneSpec(
        slug=slug,
        name=_as_str(row.get("name"), where, "name"),
        kind=kind,
        category=_as_str(row.get("category"), where, "category"),
        mood=_as_str(row.get("mood"), where, "mood"),
        timbre=timbre,
        bpm=bpm,
        motif=motif,
        duration_s=motif_duration(motif),
        loopable=_opt_flag(row.get("loopable"), kind == "notification", where, "loopable"),
        tags=_as_tags(row.get("tags"), where),
        channels=_as_channels(row.get("channels"), where),
    )
    validate(spec)
    return spec


def _as_channels(value: Json, where: str) -> int:
    """Read the optional channel count.

    Args:
        value: Parsed ``channels`` value.
        where: Row label for the error message.

    Returns:
        1 or 2.

    Raises:
        ValueError: the value is present and is not 1 or 2.
    """
    if value is None:
        return 1
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: 'channels' must be 1 or 2")
    if int(value) not in (1, 2):
        raise ValueError(f"{where}: 'channels' must be 1 or 2")
    return int(value)


def _motif_for(row: JsonMap, where: str, bpm: int) -> Motif:
    """Build the motif from either ``motif`` or the simple ``pitches`` form.

    Args:
        row: Parsed operator row.
        where: Row label for the error message.
        bpm: Tempo the row declares.

    Returns:
        Steps to render.

    Raises:
        ValueError: neither form is present, or the form given is malformed.
    """
    raw_motif = row.get("motif")
    if raw_motif is not None:
        return _as_motif(raw_motif, where)
    raw_pitches = row.get("pitches")
    if raw_pitches is None:
        raise ValueError(f"{where}: needs a 'motif' or a 'pitches' list")
    beat_s = _opt_float(row.get("beat_s"), 60.0 / bpm, where, "beat_s")
    velocity = _opt_float(row.get("velocity"), DEFAULT_VELOCITY, where, "velocity")
    gap_ratio = _opt_float(row.get("gap_ratio"), DEFAULT_GAP_RATIO, where, "gap_ratio")
    return _motif(_as_pitch_list(raw_pitches, where), beat_s, velocity, gap_ratio)


def load_catalog(path: str) -> tuple[ToneSpec, ...]:
    """Load an operator catalog and merge it over the shipped pack.

    The file is ``{"tones": [ ... ]}``; keys starting with an underscore
    are prose the template writes and are ignored. A row whose slug
    already exists replaces that row in place, so an operator can re-cut
    a shipped tone as well as add new ones.

    Args:
        path: JSON file an operator dropped in.

    Returns:
        Shipped rows with operator rows merged in.

    Raises:
        ValueError: the file is not valid JSON, has no ``tones`` list, or
            carries a row that fails validation.
    """
    source = Path(path)
    try:
        parsed = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"catalog file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"catalog is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("catalog must be a JSON object with a 'tones' list")
    rows = parsed.get("tones")
    if not isinstance(rows, list):
        raise ValueError("catalog needs a 'tones' list")
    merged: dict[str, ToneSpec] = {spec.slug: spec for spec in TONE_CATALOG}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"tone {index} must be a JSON object")
        spec = _row_to_spec(row, index)
        merged[spec.slug] = spec
    return tuple(merged.values())


def write_catalog_template(path: str) -> Path:
    """Emit a JSON file an operator can edit to add tones.

    The template carries the field reference, one worked example in each
    kind, and the full shipped pack under a disabled key so nobody has to
    guess the shape.

    Args:
        path: Where to write the template (parents are created).

    Returns:
        The path written.
    """
    template: JsonObject = {
        "_comment": "Edit 'tones' to add or override catalog rows, then run the tone export verb with --catalog pointing here.",
        "_fields": list(_TEMPLATE_FIELDS),
        "tones": [
            {
                "slug": "my-new-ping",
                "name": "My New Ping",
                "kind": "notification",
                "category": "organic",
                "mood": "friendly",
                "timbre": "marimba",
                "bpm": 132,
                "pitches": [76, 79, 83, None, 83, 88],
                "tags": ["mine", "chat"],
                "loopable": True,
                "channels": 1,
            },
            {
                "slug": "my-new-ring",
                "name": "My New Ring",
                "kind": "ringtone",
                "category": "minimal",
                "mood": "calm",
                "timbre": "glass",
                "bpm": 96,
                "motif": [
                    [83, 1.2, 0.9],
                    [None, 0.6, 0.0],
                    [88, 1.2, 0.8],
                    [90, 1.5, 0.7],
                ],
                "tags": ["mine", "call"],
                "channels": 2,
            },
        ],
    }
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    return dest
