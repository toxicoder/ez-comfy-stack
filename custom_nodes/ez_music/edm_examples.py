"""Canned 180s Drive-through EDM takes for ACE-Step lab graphs.

Fictional act only. Original warped hybrid-trap arrangements.
No living-artist names.
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict

from .albums import album_rel, drive_album_for_phase
from .naming import music_output_prefix

# Take length and Drive-through vocal locks.
EDM_DURATION_S = 180.0
DRIVE_LOCK = (
    "instrumental, no vocals, no singing, no choir, no vocal chops, "
    "original composition"
)
DRIVE_TREAT_LOCK = "sparse vocal chop, DJ shout, no rap, original composition"
EdmSeries = Literal["drive-through"]
EdmAceMode = Literal["instrumental", "vocal"]

# Score labels, layouts, and forbidden-cue needles.
SCORE_LABELS = frozenset({"intro", "inst", "drop", "build-up", "outro", "chorus"})
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
    "rapid hi-hats",
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
    """One Drive-through catalog take (score, tags, album fields).

    Attributes:
        stem: Lab filename stem (``NN-slug``).
        slug: Kebab title without the track prefix.
        rel: Lab-relative id under ``audio/albums``.
        series: Catalog series key (``drive-through``).
        title: Operator-facing take name.
        tags: ACE-Step tags line.
        bpm: Tempo written into tags.
        duration: Take length in seconds.
        seed: Fixed ACE / sampler seed.
        phase: Live-set hour index.
        prefix: SaveAudio stem ``NN - Title``.
        description: Lab graph description.
        lyrics: Arrangement score.
        ace_mode: ``instrumental`` or ``vocal``.
        layout: Comfy node placement name.
        artist: Branded act name.
        artist_slug: Artist folder slug.
        album: Album title.
        album_slug: Album folder slug.
        track: One-based track number.
        tracktotal: Album track count.
        year: Release year.
        cover_prompt: US-safe cover-art prompt.
        recipe: Audio Rack recipe id.
        picks: Axis overrides spliced with the recipe.
    """

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
    recipe: str
    picks: dict[str, str]


def _tempo_id(bpm: int) -> str:
    """Audio Rack tempo id for a Drive-through BPM.

    Args:
        bpm: Integer tempo.

    Returns:
        ``tmp_<bpm>`` technique id.
    """
    return f"tmp_{int(bpm)}"


def _splice_drive(
    *,
    bpm: int,
    recipe: str,
    picks: dict[str, str] | None,
    treat: bool,
) -> tuple[str, int, dict[str, str]]:
    """Splice Audio Rack picks into Drive-through ACE tags.

    Args:
        bpm: Take tempo (written as ``tmp_<bpm>``).
        recipe: Named recipe; fills empty axes only.
        picks: Explicit axis overrides.
        treat: If True, DJ-shout vocal flavor.

    Returns:
        Tags line, integer BPM from the splice, and the merged picks.
    """
    from ez_prompt_enhance.audio import (
        FLAVOR_ACE_INSTRUMENTAL,
        FLAVOR_ACE_VOCAL,
        splice,
    )

    merged = {str(key): str(value) for key, value in dict(picks or {}).items()}
    merged["tempo_groove"] = _tempo_id(bpm)
    if treat:
        merged.setdefault("vocal_identity", "voc_dj_shout")
        merged.setdefault("mix_production", "mix_drive_treat")
    else:
        merged.setdefault("mix_production", "mix_drive_lock")
    flavor = FLAVOR_ACE_VOCAL if treat else FLAVOR_ACE_INSTRUMENTAL
    result = splice(merged, flavor=flavor, recipe=recipe)
    token = str(result.bpm or "").strip() or f"{int(bpm)} bpm"
    match = re.search(r"(\d{2,3})", token)
    bpm_n = int(match.group(1)) if match else int(bpm)
    return result.tags, bpm_n, merged


def drive_tags(*, bpm: int, treat: bool = False, recipe: str = "") -> str:
    """Splice Drive-through ACE tags from the Audio Rack lock recipe.

    Args:
        bpm: Tempo written into the tags line.
        treat: If True, use the DJ-shout lock instead of no-vocals.
        recipe: Optional recipe override.
    Returns:
        Comma-separated ACE-Step tags line.
    """
    rid = recipe or ("rec_drive_dj_shout" if treat else "rec_drive_through_drop")
    tags, _, _ = _splice_drive(bpm=bpm, recipe=rid, picks=None, treat=treat)
    return tags


def _desc(take: str, *, treat: bool = False) -> str:
    """Lab graph description for one Drive-through take.

    Args:
        take: Short arrangement blurb.
        treat: If True, mention a sparse DJ vocal chop.

    Returns:
        Operator-facing description string.
    """
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
    *,
    recipe: str,
    picks: dict[str, str] | None = None,
    treat: bool = False,
    layout: str = "column",
) -> EdmExample:
    """Build one Drive-through catalog row from Audio Rack picks.

    Args:
        slug: Kebab title used in the lab stem.
        title: Operator-facing take name.
        bpm: Tempo written into tags and the ACE encoder.
        seed: Fixed ACE / sampler seed.
        phase: Live-set hour index (maps to an album).
        take: Short blurb for the lab description.
        lyrics: Arrangement score from ``format_edm_score``.
        recipe: Audio Rack recipe id (fills empty axes).
        picks: Axis overrides; tempo is always ``tmp_<bpm>``.
        treat: If True, sparse DJ-shout lock and vocal ACE mode.
        layout: Comfy node placement name (phase2+ experiments; default column).
    Returns:
        One ``EdmExample`` row.
    Raises:
        ValueError: unknown layout name.
    """
    if layout not in EDM_LAYOUTS:
        raise ValueError(f"unknown layout {layout}")
    tags, bpm_n, merged = _splice_drive(
        bpm=bpm, recipe=recipe, picks=picks, treat=treat
    )
    return {
        "stem": slug,
        "slug": slug,
        "rel": "",
        "series": "drive-through",
        "title": title,
        "tags": tags,
        "bpm": bpm_n,
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
        "recipe": recipe,
        "picks": merged,
    }


def _cues_from_body(text: str) -> str:
    """Join production-cue lines into one comma-separated bracket body.

    Args:
        text: Multiline production cues.

    Returns:
        Single comma-separated cue string.
    """
    parts = [line.strip() for line in text.splitlines() if line.strip()]
    return ", ".join(parts)


def _uniquify_score(seed: int, lyrics: str) -> str:
    """Stamp each non-chorus marker so drop and fill cues stay unique.

    Args:
        seed: Take seed used as the uniqueness token.
        lyrics: Score from ``format_edm_score``.
    Returns:
        Score with ``grid <seed> <index>`` folded into each bed bracket.
    """
    parts: list[str] = []
    for index, block in enumerate(lyrics.split("\n\n")):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        head = lines[0].strip()
        if head == "[chorus]" or head.startswith("[chorus"):
            parts.append(block)
            continue
        if head.startswith("[") and head.endswith("]"):
            inner = head[1:-1].rstrip()
            parts.append(f"[{inner}, grid {seed} {index}]")
            continue
        parts.append(f"{block}\ngrid {seed} {index}")
    return "\n\n".join(parts)


# Unofficial score phrases rewritten onto Audio Rack tag spelling.
_SCORE_SPELLING = (
    ("hybrid trap", "warped hybrid-trap"),
    ("trap hats", "rapid hi-hats"),
    ("chest sub", "chest-sub"),
    ("bass growl", "growl bass"),
    ("amen chops", "amen break"),
    ("amen keep", "amen break"),
    ("trap 808", "trap drums 808"),
    ("dirty 808", "dirty bass 808"),
    ("chest 808", "chest-sub 808"),
    ("rolling 808", "stacked 808"),
    ("heavy sub", "heavy chest-sub"),
)


def _spell_score_body(text: str) -> str:
    """Rewrite unofficial timbre phrases onto Audio Rack tag spelling.

    Args:
        text: Raw score body.

    Returns:
        Body with catalog-facing timbre tokens.
    """
    out = text
    for old, new in _SCORE_SPELLING:
        out = out.replace(old, new)
    return out


def format_edm_score(*sections: tuple[str, str]) -> str:
    """Build a 180s ACE-Step score from labeled sections.

    Labels are intro, inst, drop, build-up, outro, and chorus (DJ-shout
    treats only). Instrumental sections emit empty-body markers with
    production cues inside the brackets so ACE-Step does not sing them.
    An ``inst`` body that names a drop is promoted to ``[drop - …]``.
    This is not the Nill Bye verse/chorus loop and not a fixed
    melody-drop-break-drop skeleton. First section is a named drop.

    Args:
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
        text = _spell_score_body(body.strip())
        if not text:
            raise ValueError(f"{label} body is empty")
        low = text.lower()
        for needle in FORBIDDEN_SCORE_NEEDLES:
            if needle in low:
                raise ValueError(f"score forbids {needle}")
        is_drop = label == "drop" or "drop" in low
        if index == 0 and not is_drop:
            raise ValueError("first section must be a drop")
        if is_drop:
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
            parts.append(f"[chorus]\n{text}")
            continue
        marker = "drop" if is_drop and label in {"inst", "drop"} else label
        parts.append(f"[{marker} - {_cues_from_body(text)}]")
    if drop_count < 2:
        raise ValueError("score needs at least two named drops")
    return "\n\n".join(parts)


def drive_slug_from_stem(stem: str) -> str:
    """Kebab slug from a legacy or short Drive-through stem.

    Args:
        stem: Lab filename stem (legacy prefix optional).

    Returns:
        Title slug without the numeric track prefix.
    """
    text = stem.removeprefix("music-edm-drive-through-").removesuffix("-lab-example")
    if text[:1].isdigit() and "-" in text:
        return text.split("-", 1)[1]
    return text


def finalize_drive_album(rows: tuple[EdmExample, ...]) -> tuple[EdmExample, ...]:
    """Number tracks and attach album metadata for one live-set hour.

    Args:
        rows: Partial catalog rows sharing one phase.

    Returns:
        Completed ``EdmExample`` rows for that album.
    """
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
    """Assemble every Drive-through hour into numbered album rows.

    Returns:
        All EDM examples in catalog order.
    """
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


# Numbered Drive-through catalog (all hours).
EDM_EXAMPLES: tuple[EdmExample, ...] = _catalog()
