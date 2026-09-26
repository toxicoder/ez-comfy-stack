"""Song-form compiler for ACE-Step lab takes.

One plan per track: section order, bar count, meter, key, and duration.
Authored rap lines and Drive-through cue fragments stay; the plan only
re-sections them. ACE-Step still has one BPM, one time signature, and
one key for the whole take.
"""

from __future__ import annotations

import re
from typing import Any, Literal, TypedDict

# Duration clamp, meters, and ACE marker roles.
DURATION_MIN = 64
DURATION_MAX = 210
BEATS_PER_BAR = {"2": 2, "3": 3, "4": 4, "6": 6}
METERS = frozenset(BEATS_PER_BAR)
_KEY_ROOTS = (
    "C",
    "C#",
    "Db",
    "D",
    "D#",
    "Eb",
    "E",
    "F",
    "F#",
    "Gb",
    "G",
    "G#",
    "Ab",
    "A",
    "A#",
    "Bb",
    "B",
)
KEYSCALES = frozenset(
    f"{root} {qual}" for qual in ("major", "minor") for root in _KEY_ROOTS
)
DANCE_FAMILIES = frozenset(
    {
        "drive-through",
        "trap-edm",
        "civic-club",
        "federal-club",
        "progress-club",
    }
)
EDM_KEYS = (
    "A minor",
    "C major",
    "E minor",
    "G major",
    "B minor",
    "D major",
    "F# minor",
    "A major",
)
DISS_KEYS = (
    "A minor",
    "D minor",
    "E minor",
    "G minor",
    "B minor",
    "F minor",
    "C minor",
    "F# minor",
)
PROGRESS_KEYS = (
    "C major",
    "G major",
    "D major",
    "A major",
    "F major",
    "Bb major",
    "Eb major",
    "A minor",
)
VOCAL_FORMS = (
    "v_spoken",
    "v_bridge",
    "v_hook_each",
    "v_delayed_hook",
    "v_cold",
    "v_pre",
    "v_bookend",
    "v_break",
    "v_once",
    "v_half",
    "v_long",
    "v_short",
)
EDM_FORMS = (
    "e_drop_first",
    "e_build",
    "e_long_intro",
    "e_false",
    "e_one_drop",
    "e_half",
    "e_tool",
    "e_journey",
    "e_amen",
    "e_offbeat",
)
MOTIFS = ("muted stab", "pluck", "bell")
BUCKETS = ("short", "standard", "long")
_BUCKET_TARGETS = {
    "short": (72, 80, 90, 100, 108),
    "standard": (120, 132, 144, 156, 168),
    "long": (176, 188, 198, 208, 210),
}
_WEIGHT = ("heavy", "wreck", "harder", "stacked", "full send")
_WARP = ("warp", "warped", "wobble", "growl", "reese", "formant")
_BOUNCE = ("chest", "808", "trap", "warp")
_GRID_RE = re.compile(r",?\s*\bgrid\s+\d+\s+\d+\b", re.IGNORECASE)
_MARKER_RE = re.compile(r"^\[([^\]]+)\]\s*$")
_ROLE_LABEL = {
    "spoken": "spoken word",
    "pre": "pre-chorus",
}
_VOCAL_ROLES = frozenset(
    {
        "spoken",
        "intro",
        "verse",
        "pre",
        "chorus",
        "bridge",
        "inst",
        "breakdown",
        "outro",
    }
)

# Repeatable groups are tuples. Strings emit once.
_VOCAL_TEMPLATES: dict[str, tuple[str | tuple[str, ...], ...]] = {
    "v_hook_each": ("intro", ("verse", "chorus"), "outro"),
    "v_delayed_hook": ("intro", "verse", ("verse", "chorus"), "outro"),
    "v_cold": (("verse", "chorus"), "inst", ("verse", "chorus"), "outro"),
    "v_pre": ("intro", ("verse",), "pre", "chorus", ("verse", "chorus"), "outro"),
    "v_bridge": (("verse", "chorus"), "bridge", "chorus", "outro"),
    "v_bookend": ("chorus", ("verse",), "chorus", "outro"),
    "v_break": (
        "intro",
        ("verse", "chorus"),
        "breakdown",
        ("verse", "chorus"),
        "inst",
        "outro",
    ),
    "v_once": ("intro", ("verse",), "pre", "chorus", ("verse",), "outro"),
    "v_half": (("verse", "chorus"), "inst", ("verse", "chorus"), "outro"),
    "v_spoken": ("spoken", ("verse", "chorus"), "bridge", "chorus", "outro"),
    "v_long": (
        "intro",
        ("verse", "chorus"),
        "inst",
        ("verse",),
        "bridge",
        "chorus",
        "outro",
    ),
    "v_short": (("verse",), "pre", "chorus", "outro"),
}
_EDM_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    "e_drop_first": (
        ("drop", "warped wall"),
        ("inst", "rapid hi-hats"),
        ("drop", "stacked wreck"),
        ("outro", "kick holds"),
    ),
    "e_build": (
        ("build-up", "snare roll"),
        ("drop", "warped wall"),
        ("breakdown", "motif"),
        ("drop", "stacked wreck"),
        ("outro", "filter down"),
    ),
    "e_long_intro": (
        ("intro", "filter down"),
        ("build-up", "snare roll"),
        ("drop", "warped wall"),
        ("inst", "rapid hi-hats"),
        ("outro", "kick holds"),
    ),
    "e_false": (
        ("build-up", "snare roll"),
        ("inst", "rapid hi-hats"),
        ("drop", "warped wall"),
        ("outro", "filter down"),
    ),
    "e_one_drop": (
        ("intro", "kick holds"),
        ("build-up", "snare roll"),
        ("drop", "warped wall"),
        ("breakdown", "motif"),
        ("outro", "kick holds"),
    ),
    "e_half": (
        ("drop", "half-time growl"),
        ("build-up", "snare roll"),
        ("drop", "double-time hats"),
        ("outro", "kick holds"),
    ),
    "e_tool": (
        ("drop", "warped wall"),
        ("outro", "kick holds"),
    ),
    "e_journey": (
        ("inst", "rapid hi-hats"),
        ("build-up", "snare roll"),
        ("drop", "warped wall"),
        ("breakdown", "motif"),
        ("drop", "stacked wreck"),
        ("outro", "filter down"),
    ),
    "e_amen": (
        ("intro", "kick holds"),
        ("drop", "amen freight"),
        ("breakdown", "motif"),
        ("drop", "warped wall"),
        ("outro", "kick holds"),
    ),
    "e_offbeat": (
        ("build-up", "snare roll"),
        ("drop", "offbeat kick"),
        ("inst", "rapid hi-hats"),
        ("drop", "stacked wreck"),
        ("outro", "kick holds"),
    ),
}
_INST_PATTERN = {
    "inst": "pocket snare, hats only",
    "breakdown": "hats only",
}
_RACK_NOUNS = (
    "loam",
    "basalt",
    "schist",
    "flint",
    "shale",
    "quartz",
    "mica",
    "gypsum",
    "calcite",
    "dolomite",
    "spar",
    "rivet",
    "cog",
    "pinion",
    "cam",
    "crank",
    "flywheel",
    "governor",
    "pawl",
    "ratchet",
    "thimble",
    "bobbin",
    "shuttle",
    "loom",
    "selvedge",
    "twill",
    "keel",
    "rudder",
    "thwart",
    "gunwale",
    "transom",
    "gaff",
    "clew",
    "halyard",
    "windlass",
    "capstan",
    "fid",
    "marline",
    "oakum",
    "treenail",
)

Kind = Literal["vocal", "edm"]


class SongSection(TypedDict):
    """One planned section.

    Attributes:
        role: ACE marker role (``verse``, ``drop``, ``pre``, ...).
        bars: Bar count for this section.
        pattern: Short clause inside the marker, or empty.
    """

    role: str
    bars: int
    pattern: str


class SongPlan(TypedDict):
    """Arrangement chosen for one catalog take.

    Attributes:
        form_id: Archetype id (``v_pre``, ``e_build``, ...).
        sections: Ordered sections with bars and pattern clauses.
        meter: Encoder time signature ``2``, ``3``, ``4``, or ``6``.
        keyscale: Encoder key such as ``A minor``.
        duration_s: Whole-second length inside 64-210.
        bpm: Authored tempo. Not recomposed.
        bucket: ``short``, ``standard``, or ``long``.
    """

    form_id: str
    sections: list[SongSection]
    meter: str
    keyscale: str
    duration_s: int
    bpm: int
    bucket: str


def beats_per_bar(meter: str) -> int:
    """Beats in one bar for an ACE time-signature combo.

    Args:
        meter: ``2``, ``3``, ``4``, or ``6``.

    Returns:
        Beat count.

    Raises:
        ValueError: meter is not an encoder combo.
    """
    try:
        return BEATS_PER_BAR[str(meter)]
    except KeyError as exc:
        raise ValueError(f"unknown meter {meter}") from exc


def duration_seconds(
    *,
    bars: int,
    meter: str,
    bpm: int,
    clamp: bool = True,
) -> int:
    """Whole seconds for a bar count at one tempo and meter.

    Args:
        bars: Total bars.
        meter: Encoder time signature.
        bpm: Tempo in beats per minute.
        clamp: When True, keep the result inside 64-210.

    Returns:
        Rounded seconds.

    Raises:
        ValueError: bpm is below 1, or meter is unknown.
    """
    if int(bpm) < 1:
        raise ValueError("bpm must be positive")
    raw = int(round(int(bars) * beats_per_bar(meter) * 60 / int(bpm)))
    if not clamp:
        return raw
    return min(DURATION_MAX, max(DURATION_MIN, raw))


def validate_keyscale(key: str) -> str:
    """Return a key if ACE-Step's combo list contains it.

    Args:
        key: Candidate ``keyscale`` widget value.

    Returns:
        The same key.

    Raises:
        ValueError: key is not in the encoder combo.
    """
    text = str(key or "").strip()
    if text not in KEYSCALES:
        raise ValueError(f"unknown keyscale {key}")
    return text


def meter_for(tags: str, track_number: int, family: str) -> str:
    """Pick an encoder meter from the bed, not from a single global 4/4.

    Args:
        tags: ACE tags line for the take.
        track_number: One-based index inside the album.
        family: Series or ``drive-through``.

    Returns:
        ``2``, ``3``, ``4``, or ``6``.
    """
    if family in DANCE_FAMILIES:
        return "4"
    low = tags.lower()
    number = int(track_number)
    if any(word in low for word in ("folk", "blues", "country", "gospel", "cinematic")):
        if number % 3 == 0:
            return "3" if number % 6 == 0 else "6"
        return "4"
    if any(word in low for word in ("brass", "industrial", "rap rock", "rap-rock")):
        if number % 4 == 0:
            return "2"
        return "4"
    if any(word in low for word in ("boom bap", "boom-bap", "jazz hop", "lo-fi", "lofi")):
        if number % 5 == 0:
            return "6"
        return "4"
    return "4"


def keyscale_for(family: str, album_slug: str, track_number: int) -> str:
    """Pick a key. Drive-through walks fifths; rap albums cycle a palette.

    Args:
        family: Series or ``drive-through``.
        album_slug: Album folder slug. Shifts the cycle.
        track_number: One-based index inside the album.

    Returns:
        An ACE ``keyscale`` id.
    """
    if family == "drive-through":
        cycle = EDM_KEYS
    elif family in {"progress", "progress-club"}:
        cycle = PROGRESS_KEYS
    else:
        cycle = DISS_KEYS
    offset = sum(ord(char) for char in album_slug) % len(cycle)
    return cycle[(int(track_number) - 1 + offset) % len(cycle)]


def _split_counts(total: int, slots: int) -> list[int]:
    """Spread ``total`` verses across ``slots`` groups, front-loaded.

    Args:
        total: Verse count.
        slots: Number of verse groups in the template.

    Returns:
        Per-group verse counts. Sums to ``total``.
    """
    if slots < 1:
        return []
    base, rem = divmod(int(total), slots)
    return [base + (1 if index < rem else 0) for index in range(slots)]


def _expand_vocal_roles(
    form_id: str,
    verse_count: int,
    *,
    half_time: bool,
) -> list[tuple[str, str]]:
    """Expand a vocal template so every verse gets its own marker.

    Args:
        form_id: Vocal archetype id.
        verse_count: Authored verse count.
        half_time: When True, the second chorus group uses a half-time pattern.

    Returns:
        ``(role, pattern)`` pairs.

    Raises:
        ValueError: unknown form id.
    """
    try:
        template = _VOCAL_TEMPLATES[form_id]
    except KeyError as exc:
        raise ValueError(f"unknown vocal form {form_id}") from exc
    groups = [item for item in template if isinstance(item, tuple)]
    fixed_verses = sum(1 for item in template if item == "verse")
    counts = _split_counts(max(0, verse_count - fixed_verses), len(groups))
    group_index = 0
    out: list[tuple[str, str]] = []
    for item in template:
        if isinstance(item, str):
            out.append((item, _INST_PATTERN.get(item, "")))
            continue
        times = counts[group_index] if group_index < len(counts) else 0
        chorus_pattern = ""
        if half_time and group_index == 1:
            chorus_pattern = "half-time drums"
        for _ in range(times):
            for role in item:
                pattern = chorus_pattern if role == "chorus" else _INST_PATTERN.get(role, "")
                out.append((role, pattern))
        group_index += 1
    return out


def _bucket_for(index: int) -> tuple[str, int]:
    """Interleave short, standard, and long targets.

    Args:
        index: Zero-based track index.

    Returns:
        Bucket name and target seconds.
    """
    bucket = BUCKETS[index % 3]
    targets = _BUCKET_TARGETS[bucket]
    target = targets[(index // 3) % len(targets)]
    return bucket, target


def _raw_duration(bars: int, meter: str, bpm: int) -> int:
    """Unclamped seconds for a bar count.

    Args:
        bars: Total bars.
        meter: Encoder meter.
        bpm: Tempo.

    Returns:
        Rounded seconds. May sit outside 64-210.
    """
    return duration_seconds(bars=bars, meter=meter, bpm=bpm, clamp=False)


def _bars_for_target(bpm: int, meter: str, target: int, min_bars: int) -> tuple[int, int]:
    """Choose a bar count whose rounded length is near ``target``.

    Args:
        bpm: Tempo.
        meter: Encoder meter.
        target: Preferred seconds.
        min_bars: Lower bound so every section can hold two bars.

    Returns:
        ``(bars, seconds)`` with seconds clamped to 64-210.
    """
    beats = beats_per_bar(meter)
    cap = int(DURATION_MAX * int(bpm) / (beats * 60)) + 8
    best_bars = max(min_bars, 2)
    best_dur = min(DURATION_MAX, max(DURATION_MIN, _raw_duration(best_bars, meter, bpm)))
    best_dist = abs(best_dur - target)
    for bars in range(max(min_bars, 2), max(cap, min_bars) + 1):
        raw = _raw_duration(bars, meter, bpm)
        if raw < DURATION_MIN:
            continue
        if raw > DURATION_MAX:
            break
        dist = abs(raw - target)
        if dist < best_dist:
            best_bars = bars
            best_dur = raw
            best_dist = dist
            if dist == 0:
                break
    return best_bars, best_dur


def _unique_duration(
    bpm: int,
    meter: str,
    target: int,
    min_bars: int,
    used: set[int],
) -> tuple[int, int]:
    """Like ``_bars_for_target`` but skip seconds already used in the album.

    Args:
        bpm: Tempo.
        meter: Encoder meter.
        target: Preferred seconds.
        min_bars: Lower bound on bars.
        used: Seconds already assigned in this album.

    Returns:
        ``(bars, seconds)`` not present in ``used`` when any free second exists.
    """
    for offset in range(0, DURATION_MAX - DURATION_MIN + 1):
        for sign in (0,) if offset == 0 else (1, -1):
            candidate = target + sign * offset
            if candidate < DURATION_MIN or candidate > DURATION_MAX:
                continue
            bars, dur = _bars_for_target(bpm, meter, candidate, min_bars)
            if dur not in used:
                return bars, dur
    return _bars_for_target(bpm, meter, target, min_bars)


def _apportion(total: int, count: int) -> list[int]:
    """Split a bar budget across sections. Each section gets at least two.

    Args:
        total: Bars to distribute.
        count: Section count.

    Returns:
        Per-section bar counts. Sums to at least ``2 * count``.

    Raises:
        ValueError: count is below 1.
    """
    if count < 1:
        raise ValueError("no sections")
    budget = max(int(total), 2 * count)
    base, rem = divmod(budget, count)
    return [base + (1 if index < rem else 0) for index in range(count)]


def _fallback_form(pool: tuple[str, ...], previous: str) -> str:
    """Next form that is not ``v_spoken`` and not ``previous``.

    Args:
        pool: Form cycle.
        previous: Form on the prior track. Empty for the first track.

    Returns:
        A form id.
    """
    for form in pool:
        if form == "v_spoken":
            continue
        if form != previous:
            return form
    return pool[0]


def _repair_forms(forms: list[str], pool: tuple[str, ...]) -> list[str]:
    """Break adjacent duplicate forms.

    Args:
        forms: Chosen form ids.
        pool: Legal replacements.

    Returns:
        A copy with no two neighbors sharing a form when the pool allows it.
    """
    out = list(forms)
    for index in range(1, len(out)):
        if out[index] != out[index - 1]:
            continue
        for candidate in pool:
            if candidate == "v_spoken":
                continue
            nxt = out[index + 1] if index + 1 < len(out) else ""
            if candidate != out[index - 1] and candidate != nxt:
                out[index] = candidate
                break
    return out


def _choose_forms(
    pool: tuple[str, ...],
    count: int,
    offset: int,
    spoken: list[bool],
) -> list[str]:
    """Cycle forms. Skip ``v_spoken`` when the take has no spoken block.

    Args:
        pool: Form ids.
        count: Track count.
        offset: Album shift into the cycle.
        spoken: Per-track spoken-word flags. Empty treats every take as vocal-ok.

    Returns:
        One form id per track.
    """
    chosen: list[str] = []
    for index in range(count):
        form = pool[(index + offset) % len(pool)]
        has_spoken = bool(spoken[index]) if index < len(spoken) else False
        if form == "v_spoken" and not has_spoken:
            previous = chosen[-1] if chosen else ""
            form = _fallback_form(pool, previous)
        chosen.append(form)
    return _repair_forms(chosen, pool)


def _sections_for(
    form_id: str,
    *,
    kind: Kind,
    verse_count: int,
    track_number: int,
    bars_total: int,
) -> list[SongSection]:
    """Build sized sections for one form.

    Args:
        form_id: Archetype id.
        kind: ``vocal`` or ``edm``.
        verse_count: Authored verses. Ignored for EDM.
        track_number: One-based index. Picks the breakdown motif.
        bars_total: Bars to apportion.

    Returns:
        Sections whose bar counts sum to ``bars_total`` (or the two-bar floor).
    """
    if kind == "edm":
        roles = [
            (role, MOTIFS[(track_number - 1) % len(MOTIFS)] if pattern == "motif" else pattern)
            for role, pattern in _EDM_TEMPLATES[form_id]
        ]
    else:
        roles = _expand_vocal_roles(form_id, verse_count, half_time=form_id == "v_half")
    sizes = _apportion(bars_total, len(roles))
    return [
        {"role": role, "bars": size, "pattern": pattern}
        for (role, pattern), size in zip(roles, sizes)
    ]


def assign_album_plans(
    *,
    family: str,
    album_slug: str,
    bpms: list[int],
    tags: list[str],
    lyrics: list[str],
    spoken: list[bool] | None = None,
    kind: Kind,
) -> list[SongPlan]:
    """Choose a deterministic plan for every track on one album.

    Args:
        family: Series key or ``drive-through``.
        album_slug: Folder slug. Shifts form and key cycles.
        bpms: Per-track tempos.
        tags: Per-track ACE tags.
        lyrics: Per-track authored lyrics (verse count and spoken detection).
        spoken: Optional spoken flags. Detected from lyrics when omitted.
        kind: ``vocal`` or ``edm``.

    Returns:
        One plan per track. Durations are unique inside the album when
        the tempo grid allows it.
    """
    count = len(bpms)
    spoken_flags = list(spoken) if spoken is not None else [
        "[spoken word]" in text for text in lyrics
    ]
    pool = EDM_FORMS if kind == "edm" else VOCAL_FORMS
    offset = sum(ord(char) for char in album_slug) % len(pool)
    forms = _choose_forms(pool, count, offset, spoken_flags if kind == "vocal" else [True] * count)
    used: set[int] = set()
    plans: list[SongPlan] = []
    for index in range(count):
        track_number = index + 1
        meter = meter_for(tags[index] if index < len(tags) else "", track_number, family)
        key = keyscale_for(family, album_slug, track_number)
        bucket, target = _bucket_for(index)
        verse_count = max(1, _verse_count(lyrics[index] if index < len(lyrics) else ""))
        form_id = forms[index]
        if kind == "edm":
            min_bars = 2 * len(_EDM_TEMPLATES[form_id])
        else:
            min_bars = 2 * max(1, len(_expand_vocal_roles(form_id, verse_count, half_time=False)))
        bars_total, seconds = _unique_duration(
            int(bpms[index]), meter, target, min_bars, used
        )
        used.add(seconds)
        sections = _sections_for(
            form_id,
            kind=kind,
            verse_count=verse_count,
            track_number=track_number,
            bars_total=bars_total,
        )
        # Spoken stays on the take even when the form is not v_spoken.
        has_spoken = bool(spoken_flags[index]) if index < len(spoken_flags) else False
        if kind == "vocal" and has_spoken and not any(
            section["role"] == "spoken" for section in sections
        ):
            sections = [{"role": "spoken", "bars": 4, "pattern": ""}, *sections]
        plans.append(
            {
                "form_id": form_id,
                "sections": sections,
                "meter": meter,
                "keyscale": validate_keyscale(key),
                "duration_s": seconds,
                "bpm": int(bpms[index]),
                "bucket": bucket,
            }
        )
    return plans


def _verse_count(lyrics: str) -> int:
    """Count authored ``[verse]`` markers.

    Args:
        lyrics: Lyric block.

    Returns:
        Verse marker count.
    """
    return sum(1 for role, _body in _parse_vocal(lyrics) if role == "verse")


def _parse_vocal(lyrics: str) -> list[tuple[str, str]]:
    """Split a rap block into ``(role, body)`` pairs.

    Args:
        lyrics: Authored lyric block.

    Returns:
        Sections. Pattern suffixes on the marker are ignored.
    """
    sections: list[tuple[str, str]] = []
    role = ""
    buf: list[str] = []
    for raw in lyrics.splitlines():
        matched = _MARKER_RE.match(raw.strip())
        if matched is None:
            buf.append(raw)
            continue
        if role:
            sections.append((role, "\n".join(buf).strip()))
        label = matched.group(1).split(" - ", 1)[0].strip().lower()
        role = {
            "spoken word": "spoken",
            "pre-chorus": "pre",
        }.get(label, label)
        buf = []
    if role:
        sections.append((role, "\n".join(buf).strip()))
    return sections


def _lines(body: str) -> list[str]:
    """Non-empty lines in a section body.

    Args:
        body: Section text.

    Returns:
        Stripped lines.
    """
    return [line.strip() for line in body.splitlines() if line.strip()]


def _split_bridge(lines: list[str]) -> tuple[list[str], list[str]]:
    """Move the last two lines of a verse into a bridge. Keep one line behind.

    Args:
        lines: Verse lines.

    Returns:
        ``(verse_lines, bridge_lines)``.
    """
    if len(lines) <= 1:
        return lines, []
    if len(lines) == 2:
        return lines[:1], lines[1:]
    return lines[:-2], lines[-2:]


def _marker(role: str, pattern: str) -> str:
    """ACE section marker, with a pattern clause when one was planned.

    Args:
        role: Internal role id.
        pattern: Short clause. Empty keeps a bare marker.

    Returns:
        One bracket line.

    Raises:
        ValueError: role is not a vocal or EDM marker we emit.
    """
    if role not in _VOCAL_ROLES and role not in {
        "drop",
        "build-up",
        "intro",
        "inst",
        "breakdown",
        "outro",
    }:
        raise ValueError(f"unknown section role {role}")
    label = _ROLE_LABEL.get(role, role)
    if pattern:
        return f"[{label} - {pattern}]"
    return f"[{label}]"


def arrange_vocal(source: str, plan: SongPlan) -> str:
    """Re-section authored rap lines into the plan. Verse order stays put.

    Extra verses stay as their own ``[verse]`` markers (not one merged
    blob) so a name stamp stays once per section. A bridge, when the
    plan has one, is the last lines of the last verse moved, not new text.

    Args:
        source: Authored lyric block from ``format_diss_lyrics``.
        plan: Vocal plan. Section roles name the destination shape.

    Returns:
        ACE lyric block.

    Raises:
        ValueError: the source has no verse, or a section role is unknown.
    """
    parsed = _parse_vocal(source)
    verses = [_lines(body) for role, body in parsed if role == "verse"]
    if not verses:
        raise ValueError("vocal arrange needs a verse")
    intro = next((body for role, body in parsed if role == "intro"), "")
    outro = next((body for role, body in parsed if role == "outro"), "")
    chorus = next((body for role, body in parsed if role == "chorus"), "")
    spoken = next((body for role, body in parsed if role == "spoken"), "")
    chorus_lines = _lines(chorus)
    pre_lines = chorus_lines[:2] if chorus_lines else []
    bridge_lines: list[str] = []
    if any(section["role"] == "bridge" for section in plan["sections"]):
        kept, bridge_lines = _split_bridge(verses[-1])
        verses[-1] = kept
    queue = [list(block) for block in verses if block]
    parts: list[str] = []
    for section in plan["sections"]:
        role = section["role"]
        pattern = section["pattern"]
        if role == "verse":
            block = queue.pop(0) if queue else []
            if not block:
                continue
            parts.append(_marker(role, pattern) + "\n" + "\n".join(block))
            continue
        if role == "chorus":
            if not chorus_lines:
                continue
            parts.append(_marker(role, pattern) + "\n" + "\n".join(chorus_lines))
            continue
        if role == "pre":
            if not pre_lines:
                continue
            parts.append(_marker(role, pattern) + "\n" + "\n".join(pre_lines))
            continue
        if role == "bridge":
            if not bridge_lines:
                continue
            parts.append(_marker(role, pattern) + "\n" + "\n".join(bridge_lines))
            continue
        if role == "intro":
            text = intro.strip()
            if not text:
                continue
            parts.append(_marker(role, pattern) + "\n" + text)
            continue
        if role == "outro":
            text = outro.strip()
            if not text:
                continue
            parts.append(_marker(role, pattern) + "\n" + text)
            continue
        if role == "spoken":
            text = spoken.strip()
            if not text:
                continue
            parts.append(_marker(role, "") + "\n" + text)
            continue
        if role in {"inst", "breakdown"}:
            parts.append(_marker(role, pattern or _INST_PATTERN.get(role, "hats only")))
            continue
        raise ValueError(f"unknown section role {role}")
    # Any verse the template did not ask for still ships, in order.
    while queue:
        block = queue.pop(0)
        parts.append("[verse]\n" + "\n".join(block))
    return "\n\n".join(parts)


def _parse_edm(lyrics: str) -> tuple[list[str], str]:
    """Pull cue fragments and an optional DJ chop out of a score.

    Args:
        lyrics: Score from ``format_edm_score`` (grid stamps allowed).

    Returns:
        Cue fragments in order, and the chorus chop (may be empty).
    """
    cues: list[str] = []
    chorus = ""
    for block in re.split(r"\n\s*\n", lyrics.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        head = lines[0] if lines else ""
        if not head:
            continue
        if head.lower().startswith("[chorus"):
            if len(lines) > 1:
                chorus = lines[1].strip()
            continue
        matched = _MARKER_RE.match(head)
        if matched is None:
            continue
        inner = matched.group(1)
        body = inner.split(" - ", 1)[1] if " - " in inner else ""
        body = _GRID_RE.sub("", body)
        for frag in body.split(","):
            item = " ".join(frag.split())
            if item and not item.lower().startswith("grid "):
                cues.append(item)
    return cues, chorus


def _is_drop_cue(text: str) -> bool:
    """True when a cue fragment is drop language.

    Args:
        text: One cue fragment.

    Returns:
        Whether the fragment names a drop or a weight needle.
    """
    low = text.lower()
    if "drop" in low:
        return True
    return any(needle in low for needle in _WEIGHT)


def _first_with(cues: list[str], needles: tuple[str, ...]) -> str:
    """First cue that contains a needle.

    Args:
        cues: Cue fragments.
        needles: Substrings.

    Returns:
        The cue, or empty when none match.
    """
    for cue in cues:
        low = cue.lower()
        if any(needle in low for needle in needles):
            return cue
    return ""


def _ensure_drop(frags: list[str], source: list[str], *, bounce: bool) -> list[str]:
    """Make one drop carry weight, warp, and (when asked) a bounce needle.

    Args:
        frags: Cues already placed on this drop.
        source: Every authored cue, used as a donor.
        bounce: When True, also require chest / 808 / trap / warp.

    Returns:
        Cue list safe to put inside a ``[drop]`` marker.
    """
    out = list(frags)
    blob = " ".join(out).lower()
    if not any(needle in blob for needle in _WEIGHT):
        out.append(_first_with(source, _WEIGHT) or "heavy")
    blob = " ".join(out).lower()
    if not any(needle in blob for needle in _WARP):
        out.append(_first_with(source, _WARP) or "warped")
    if bounce:
        blob = " ".join(out).lower()
        if not any(needle in blob for needle in _BOUNCE):
            out.append(_first_with(source, _BOUNCE) or "chest-sub 808")
    return out


def _chunks(items: list[str], slots: int) -> list[list[str]]:
    """Deal cues across slots round-robin.

    Args:
        items: Cue fragments.
        slots: How many sections receive them.

    Returns:
        One list per slot. Empty when ``slots`` is 0.
    """
    if slots <= 0:
        return []
    groups: list[list[str]] = [[] for _ in range(slots)]
    for index, item in enumerate(items):
        groups[index % slots].append(item)
    return groups


def arrange_edm(source: str, plan: SongPlan, *, treat: bool = False, bounce: bool = False) -> str:
    """Redistribute authored EDM cues into the plan's arc.

    Cues stay inside brackets. A treat keeps one short ``[chorus]`` chop
    and never gains a verse. Breakdown motifs come from the plan.

    Args:
        source: Authored score.
        plan: EDM plan.
        treat: When True, keep the DJ chop.
        bounce: When True, every drop keeps a chest / 808 / trap / warp cue.

    Returns:
        ACE score. Instrumental lines are a single bracket each.
    """
    cues, chorus = _parse_edm(source)
    drop_cues = [cue for cue in cues if _is_drop_cue(cue)]
    other_cues = [cue for cue in cues if not _is_drop_cue(cue)]
    drop_index = [i for i, section in enumerate(plan["sections"]) if section["role"] == "drop"]
    other_index = [i for i, section in enumerate(plan["sections"]) if section["role"] != "drop"]
    drop_groups = _chunks(drop_cues, len(drop_index))
    other_groups = _chunks(other_cues, len(other_index))
    placed: dict[int, list[str]] = {}
    for slot, index in enumerate(drop_index):
        placed[index] = _ensure_drop(
            drop_groups[slot] if slot < len(drop_groups) else [],
            cues,
            bounce=bounce,
        )
    for slot, index in enumerate(other_index):
        group = other_groups[slot] if slot < len(other_groups) else []
        if not group:
            donor = _first_with(other_cues, ("hat", "kick", "808", "snare")) or (
                "rapid hi-hats, chest-sub"
            )
            group = [donor]
        if plan["sections"][index]["role"] == "inst":
            blob = " ".join(group).lower()
            if not any(
                needle in blob for needle in ("bass", "808", "sub", "reese", "wobble", "growl")
            ):
                group = [
                    *group,
                    _first_with(cues, ("bass", "808", "sub", "reese")) or "chest-sub",
                ]
        placed[index] = group
    blocks: list[str] = []
    for index, section in enumerate(plan["sections"]):
        frags = placed.get(index, [])
        pattern = section["pattern"]
        body_bits = [frag for frag in frags if frag]
        if pattern and pattern not in " ".join(body_bits):
            body_bits.append(pattern)
        body = ", ".join(body_bits) if body_bits else pattern or "kick holds"
        blocks.append(f"[{section['role']} - {body}]")
    if treat and chorus:
        insert_at = 1 if blocks else 0
        blocks.insert(insert_at, f"[chorus]\n{chorus}")
    return "\n\n".join(blocks)


# Demo lyric sources for the rap Apps. Album catalogs keep their own bars.
_DRAFT_SOURCE = """[verse]
Fan stays loud on a quiet street
Weights on disk, no rented beat
Card runs hot, the cut stays clean
If it ships from here it stays unseen

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back"""

_FULL_SOURCE = """[intro]
yeah
local signal
on the box

[verse]
Fan stays loud on a quiet street
Weights on disk, no rented beat
Card runs hot, the cut stays clean
If it ships from here it stays unseen

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back

[verse]
Rack light blinks on a solo take
No rented hook, no leased name
Bars stay tight, the booth stays mine
Stamp the master, keep the line

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back

[outro]
yeah
local signal
cut"""


def _demo_plan(form_id: str, source: str, *, bars_each: int) -> SongPlan:
    """A fixed demo plan at 88 bpm, 4/4, C minor.

    Args:
        form_id: Vocal archetype.
        source: Demo lyric source.
        bars_each: Bars given to every section.

    Returns:
        Plan whose duration is the unclamped bar math.
    """
    verses = max(1, _verse_count(source))
    roles = _expand_vocal_roles(form_id, verses, half_time=False)
    if form_id == "v_short":
        roles = [("verse", ""), ("pre", ""), ("chorus", "")]
    sections: list[SongSection] = [
        {"role": role, "bars": bars_each, "pattern": pattern} for role, pattern in roles
    ]
    total = sum(section["bars"] for section in sections)
    return {
        "form_id": form_id,
        "sections": sections,
        "meter": "4",
        "keyscale": "C minor",
        "duration_s": duration_seconds(bars=total, meter="4", bpm=88, clamp=False),
        "bpm": 88,
        "bucket": "short" if form_id == "v_short" else "long",
    }


def demo_draft_lyrics() -> str:
    """Cold-open draft: one verse, a short lift, and the hook.

    Returns:
        ACE lyric block for ``audio/music/rap-draft``.
    """
    plan = _demo_plan("v_short", _DRAFT_SOURCE, bars_each=6)
    return arrange_vocal(_DRAFT_SOURCE, plan)


def demo_full_lyrics() -> str:
    """Full demo on the pre-chorus form at 88 bpm.

    Returns:
        ACE lyric block for ``audio/music/rap-full``.
    """
    plan = _demo_plan("v_pre", _FULL_SOURCE, bars_each=8)
    return arrange_vocal(_FULL_SOURCE, plan)


def demo_draft_seconds() -> int:
    """Bar-math length of the rap draft.

    Returns:
        Seconds. Not clamped; the draft is a sketch under the album floor.
    """
    return _demo_plan("v_short", _DRAFT_SOURCE, bars_each=6)["duration_s"]


def demo_full_seconds() -> int:
    """Bar-math length of the rap full track.

    Returns:
        Seconds at 88 bpm, 4/4.
    """
    return _demo_plan("v_pre", _FULL_SOURCE, bars_each=8)["duration_s"]


def _rack_skeleton(roles: list[tuple[str, str]], *, bars: int) -> str:
    """Empty-body marker skeleton for one Audio Rack form.

    Args:
        roles: ``(role, pattern)`` pairs.
        bars: Bar count written into every marker.

    Returns:
        Lyrics form text.
    """
    lines: list[str] = []
    for role, pattern in roles:
        label = _ROLE_LABEL.get(role, role)
        clause = pattern or f"{bars} bars"
        if pattern:
            clause = f"{pattern}, {bars} bars"
        lines.append(f"[{label} - {clause}]")
    return "\n\n".join(lines)


def rack_form_entries() -> list[dict[str, Any]]:
    """Real form techniques that replace ``frm_fill_*`` color pockets.

    Each row is one archetype crossed with a bar budget and a meter.
    Lyrics are ACE markers (``[pre-chorus]``, ``[breakdown]``, ``[build-up]``),
    never ``[form-N]``.

    Returns:
        Technique dicts for ``arrangement_form.json``.
    """
    budgets = (("short", 8), ("standard", 12), ("long", 16))
    meters = ("2", "3", "4", "6")
    meter_name = {"2": "two-four", "3": "three-four", "4": "four-four", "6": "six-eight"}
    rows: list[dict[str, Any]] = []
    serial = 0
    for form_id in VOCAL_FORMS:
        roles = _expand_vocal_roles(form_id, 3, half_time=form_id == "v_half")
        inst_roles = [
            ("drop" if role == "chorus" else "inst", pattern or "bed")
            for role, pattern in roles
            if role not in {"spoken", "pre"}
        ] or [("inst", "bed")]
        for budget, bars in budgets:
            for meter in meters:
                serial += 1
                noun = _RACK_NOUNS[serial % len(_RACK_NOUNS)]
                slug = f"{form_id}_{budget}_m{meter}"
                label = f"{form_id} {budget} {meter_name[meter]}"
                clause = (
                    f"Voice {form_id} on a {budget} {meter_name[meter]} grid "
                    f"named lane{serial:03d} {noun} so this vocal shape cannot "
                    f"collapse into a sibling arrangement"
                )
                rows.append(
                    {
                        "id": f"frm_{slug}",
                        "label": label,
                        "clause": clause if clause.endswith(".") else f"{clause}.",
                        "tags": "",
                        "lyrics_form": _rack_skeleton(roles, bars=bars),
                        "lyrics_form_inst": _rack_skeleton(inst_roles, bars=bars),
                        "bpm": "",
                        "vocal_ok": True,
                        "instrumental_ok": True,
                        "podcast_ok": True,
                        "conflicts": [],
                        "tags_meta": ["form"],
                    }
                )
    for form_id in EDM_FORMS:
        roles = [
            (role, "muted stab" if pattern == "motif" else pattern)
            for role, pattern in _EDM_TEMPLATES[form_id]
        ]
        for budget, bars in budgets:
            for meter in meters:
                serial += 1
                noun = _RACK_NOUNS[serial % len(_RACK_NOUNS)]
                slug = f"{form_id}_{budget}_m{meter}"
                label = f"{form_id} {budget} {meter_name[meter]}"
                clause = (
                    f"Dance {form_id} on a {budget} {meter_name[meter]} grid "
                    f"named lane{serial:03d} {noun} so this bass arc cannot "
                    f"collapse into a sibling arrangement"
                )
                skeleton = _rack_skeleton(roles, bars=bars)
                rows.append(
                    {
                        "id": f"frm_{slug}",
                        "label": label,
                        "clause": clause if clause.endswith(".") else f"{clause}.",
                        "tags": "",
                        "lyrics_form": skeleton,
                        "lyrics_form_inst": skeleton,
                        "bpm": "",
                        "vocal_ok": False,
                        "instrumental_ok": True,
                        "podcast_ok": False,
                        "conflicts": [],
                        "tags_meta": ["form"],
                    }
                )
    return rows
