"""Canned 180s Drive-through EDM takes for ACE-Step lab graphs.

Fictional act only. Original warped hybrid-trap arrangements.
No living-artist names.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from .albums import album_rel, drive_album_for_phase
from .naming import music_output_prefix

EDM_DURATION_S = 180.0
DRIVE_LOCK = (
    "instrumental, no vocals, no singing, no choir, no vocal chops, "
    "original composition"
)
DRIVE_TREAT_LOCK = "sparse vocal chop, DJ shout, no rap, original composition"
EdmSeries = Literal["drive-through"]
EdmAceMode = Literal["instrumental", "vocal"]

SCORE_LABELS = frozenset({"intro", "inst", "outro", "chorus"})
EDM_LAYOUTS = frozenset(
    {"column", "wide-stage", "stacked-tower", "prompt-left", "output-rail"}
)
DROP_WEIGHT_NEEDLES = (
    "heavy",
    "wreck",
    "harder",
    "stacked",
    "full send",
)
BASS_NEEDLES = (
    "bass",
    "808",
    "sub",
    "reese",
    "wobble",
    "growl",
)
DROP_SHOW_NEEDLES = (
    "warp",
    "warped",
    "wobble",
    "growl",
    "reese",
    "formant",
)
WARP_NEEDLES = (
    "warp",
    "warped",
    "wobble",
    "growl",
    "reese",
    "formant",
)
HIPHOP_DRUM_NEEDLES = (
    "trap hats",
    "hat roll",
    "hats roll",
    "snare roll",
    "trap drums",
)
HEADLINER_BOUNCE_NEEDLES = (
    "chest",
    "808",
    "trap",
    "warp",
)
HIGH_PITCH_NEEDLES = (
    "supersaw",
    "arpeggio",
    "sparkle",
    "whistle",
    "chipmunk",
    "pluck",
    "bell",
    "chime",
    "piano",
    "strings",
    "flute",
    "saw lead",
    "bright lead",
    "anthem",
    "spark",
    "piccolo",
    "violin",
    "donk",
)
SUB_WEIGHT_NEEDLES = (
    "sub",
    "chest",
    "low",
    "808",
    "rumble",
)
SECRET_HOMAGE_NEEDLES = (
    "dirty dubstep",
    "brostep",
    "riddim",
    "tearout",
    "wobble",
    "warp",
    "growl",
)
MOTION_NEEDLES = (
    "hats",
    "bass",
    "kick",
    "roll",
    "amen",
    "808",
    "sub",
    "pedal",
    "snare",
    "trap",
    "warp",
    "growl",
    "wobble",
    "reese",
)
PAUSE_ONLY_TOKENS = frozenset({"air", "space", "rest", "hush", "quiet", "fade"})
PEDAL_BASS_NEEDLE = "dual-action pedal"
BANNED_STYLE_NEEDLES = (
    "techno",
    "trance",
    "progressive house",
    "big room",
    "electro house",
    "future bass",
    "slap house",
    "melbourne bounce",
    "bounce house",
    "bass house",
    "four on the floor",
    "festival anthem",
    "festival pyro",
    "festival bass",
    "mainstage",
    "hardstyle",
    "dirty electro",
)
QUIET_NEEDLES = (
    "hush",
    "quiet",
    "fade",
    "mix-in",
    "filter in",
    "filter down",
    "filter out",
    "sunrise",
    "fog",
    "mute",
    "blend out",
    "blend next",
    "hats stop",
    "amen stop",
    "kick rest",
    "kick out",
    "dust rest",
    "half-time",
)
BED_CUT_NEEDLES = (
    "bass cut",
    "sub cut",
    "chest cut",
    "808 cut",
    "hats skip",
    "hats cut",
    "filter cut",
    "wobble cut",
    "growl cut",
    "bounce cut",
)
ACT_NEEDLES = (
    "drive-through",
    "drive through",
)
FORBIDDEN_SCORE_NEEDLES = (
    *HIGH_PITCH_NEEDLES,
    *BANNED_STYLE_NEEDLES,
    *QUIET_NEEDLES,
    *BED_CUT_NEEDLES,
    *ACT_NEEDLES,
)


class EdmExample(TypedDict):
    stem: str
    slug: str
    rel: str
    series: EdmSeries
    title: str
    tags: str
    bpm: int
    duration: float
    seed: int
    phase: int
    prefix: str
    description: str
    lyrics: str
    ace_mode: EdmAceMode
    layout: str
    artist: str
    artist_slug: str
    album: str
    album_slug: str
    track: int
    tracktotal: int
    year: int
    cover_prompt: str


def drive_tags(*parts: str, bpm: int, treat: bool = False) -> str:
    """Join style tags with the Drive-through bed lock and bpm.

    Arguments:
        parts: Genre and production tags for this take.
        bpm: Tempo written into the tags line.
        treat: If True, use the sparse DJ-shout lock instead of no-vocals.
    Returns:
        Comma-separated ACE-Step tags line.
    """
    lock = DRIVE_TREAT_LOCK if treat else DRIVE_LOCK
    return ", ".join([*parts, lock, f"{bpm} bpm"])


def _desc(take: str, *, treat: bool = False) -> str:
    vocal = "sparse DJ vocal chop" if treat else "instrumental"
    return (
        f"US-safe EDM 180s: Drive-through {take}, "
        f"ACE-Step 1.5 turbo AIO, {vocal}, warped bass, invented timbre"
    )


def _ex(
    slug: str,
    title: str,
    bpm: int,
    seed: int,
    phase: int,
    take: str,
    lyrics: str,
    *tag_parts: str,
    treat: bool = False,
    layout: str = "column",
) -> EdmExample:
    """Build one Drive-through catalog row.

    Arguments:
        slug: Kebab title used in the lab stem.
        title: Operator-facing take name.
        bpm: Tempo written into tags and the ACE encoder.
        seed: Fixed ACE / sampler seed.
        phase: Live-set hour index (maps to an album).
        take: Short blurb for the lab description.
        lyrics: Arrangement score from ``format_edm_score``.
        tag_parts: Genre and production tags (warp bass + trap drums).
        treat: If True, sparse DJ-shout lock and vocal ACE mode.
        layout: Comfy node placement name (phase2+ experiments; default column).
    Returns:
        One ``EdmExample`` row.
    Raises:
        ValueError: unknown layout name.
    """
    if layout not in EDM_LAYOUTS:
        raise ValueError(f"unknown layout {layout}")
    return {
        "stem": slug,
        "slug": slug,
        "rel": "",
        "series": "drive-through",
        "title": title,
        "tags": drive_tags(*tag_parts, bpm=bpm, treat=treat),
        "bpm": bpm,
        "duration": EDM_DURATION_S,
        "seed": seed,
        "phase": phase,
        "prefix": "",
        "description": _desc(take, treat=treat),
        "lyrics": _uniquify_score(seed, lyrics),
        "ace_mode": "vocal" if treat else "instrumental",
        "layout": layout,
        "artist": "",
        "artist_slug": "",
        "album": "",
        "album_slug": "",
        "track": 0,
        "tracktotal": 0,
        "year": 0,
        "cover_prompt": "",
    }


def _uniquify_score(seed: int, lyrics: str) -> str:
    """Stamp each non-chorus block so drop and fill bodies stay unique.

    Arguments:
        seed: Take seed used as the uniqueness token.
        lyrics: Score from ``format_edm_score``.
    Returns:
        Score with a ``grid <seed> <index>`` cue on every bed block.
    """
    parts: list[str] = []
    for index, block in enumerate(lyrics.split("\n\n")):
        lines = block.splitlines()
        if lines and lines[0] == "[chorus]":
            parts.append(block)
            continue
        parts.append(f"{block}\ngrid {seed} {index}")
    return "\n\n".join(parts)


def format_edm_score(*sections: tuple[str, str]) -> str:
    """Build a 180s ACE-Step score from labeled sections.

    Labels are intro, inst, outro, and chorus (DJ-shout treats only).
    This is not the Nill Bye verse/chorus loop and not a fixed
    melody-drop-break-drop skeleton. First section is a named drop.

    Arguments:
        sections: (label, body) pairs. Bodies are production cues.
    Returns:
        ACE-Step lyrics with labeled blocks.
    Raises:
        ValueError: too few sections, unknown label, empty body, fewer
            than two named drops, a drop without a weight or warp
            needle, a quiet/tinny/mainstage cue, a first section that
            is not a drop, or a chorus chop that is too long.
    """
    if len(sections) < 3:
        raise ValueError("score needs at least three sections")
    drop_count = 0
    parts: list[str] = []
    for index, (label, body) in enumerate(sections):
        if label not in SCORE_LABELS:
            raise ValueError(f"unknown score label {label}")
        text = body.strip()
        if not text:
            raise ValueError(f"{label} body is empty")
        low = text.lower()
        for needle in FORBIDDEN_SCORE_NEEDLES:
            if needle in low:
                raise ValueError(f"score forbids {needle}")
        if index == 0 and "drop" not in low:
            raise ValueError("first section must be a drop")
        if "drop" in low:
            drop_count += 1
            if not any(needle in low for needle in DROP_WEIGHT_NEEDLES):
                raise ValueError("drop must hit a weight needle")
            if not any(needle in low for needle in WARP_NEEDLES):
                raise ValueError("drop must hit a warp needle")
        if label == "chorus":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if len(lines) != 1:
                raise ValueError("chorus must be one short chop")
            if len(lines[0].split()) > 2:
                raise ValueError("chorus chop is too long")
        parts.append(f"[{label}]\n{text}")
    if drop_count < 2:
        raise ValueError("score needs at least two named drops")
    return "\n\n".join(parts)


def drive_slug_from_stem(stem: str) -> str:
    """Kebab slug from a legacy or short Drive-through stem."""
    text = stem.removeprefix("music-edm-drive-through-").removesuffix("-lab-example")
    if text[:1].isdigit() and "-" in text:
        return text.split("-", 1)[1]
    return text


def finalize_drive_album(rows: tuple[EdmExample, ...]) -> tuple[EdmExample, ...]:
    """Number tracks and attach album metadata for one live-set hour."""
    if not rows:
        return ()
    info = drive_album_for_phase(int(rows[0]["phase"]))
    total = len(rows)
    out: list[EdmExample] = []
    for index, row in enumerate(rows, 1):
        slug = drive_slug_from_stem(str(row.get("slug") or row["stem"]))
        stem = f"{index:02d}-{slug}"
        out.append(
            {
                **row,
                "slug": slug,
                "stem": stem,
                "rel": album_rel(info["artist_slug"], info["slug"], stem),
                "artist": info["artist"],
                "artist_slug": info["artist_slug"],
                "album": info["title"],
                "album_slug": info["slug"],
                "track": index,
                "tracktotal": total,
                "year": info["year"],
                "cover_prompt": info["cover_prompt"],
                "prefix": music_output_prefix(row["title"], index),
            }
        )
    return tuple(out)


def _catalog() -> tuple[EdmExample, ...]:
    from .edm_drive_through import EDM_DRIVE_THROUGH
    from .edm_drive_through_afterparty import EDM_DRIVE_THROUGH_AFTERPARTY
    from .edm_drive_through_bass import EDM_DRIVE_THROUGH_BASS
    from .edm_drive_through_headliner import EDM_DRIVE_THROUGH_HEADLINER
    from .edm_drive_through_secret_homage import EDM_DRIVE_THROUGH_SECRET_HOMAGE

    groups = (
        EDM_DRIVE_THROUGH,
        EDM_DRIVE_THROUGH_BASS,
        EDM_DRIVE_THROUGH_HEADLINER,
        EDM_DRIVE_THROUGH_AFTERPARTY,
        EDM_DRIVE_THROUGH_SECRET_HOMAGE,
    )
    out: list[EdmExample] = []
    for group in groups:
        out.extend(finalize_drive_album(group))
    return tuple(out)


EDM_EXAMPLES: tuple[EdmExample, ...] = _catalog()
