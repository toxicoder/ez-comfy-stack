"""Canned 180s Nill Bye vs Rake diss takes for ACE-Step rap lab graphs.

Fictional MCs only. Original lyrics. No living-artist names.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence, TypedDict

from .albums import album_rel, nill_album_for_series
from .naming import music_output_prefix

BOOM_BAP_TAGS_88 = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 88 bpm"
)
BOOM_BAP_TAGS_92 = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 92 bpm"
)
TRAP_TAGS = (
    "trap, 808 bass, rapid hi-hats, dark pads, male rap vocals, half-time, 140 bpm"
)
LOFI_TAGS = (
    "lo-fi hip-hop, dusty drums, rhodes, vinyl crackle, laid-back male rap vocals, 86 bpm"
)

DISS_DURATION_S = 180.0
NILL_VOICE = "male rap vocals, dry booth, no autotune"
DissSeries = Literal[
    "lab",
    "variety",
    "trap-edm",
    "civic",
    "civic-club",
    "federal",
    "federal-club",
    "progress",
    "progress-club",
]


class DissExample(TypedDict):
    stem: str
    slug: str
    rel: str
    series: DissSeries
    title: str
    tags: str
    bpm: int
    duration: float
    seed: int
    phase: int
    prefix: str
    description: str
    lyrics: str
    artist: str
    artist_slug: str
    album: str
    album_slug: str
    track: int
    tracktotal: int
    year: int
    cover_prompt: str


def nill_output_prefix(title: str, track: int) -> str:
    """SaveAudio prefix for a Nill Bye take."""
    return music_output_prefix(title, track if track >= 1 else 1)


def nill_tags(*parts: str, bpm: int) -> str:
    """Join style tags with the locked Nill Bye vocal and bpm."""
    return ", ".join([*parts, NILL_VOICE, f"{bpm} bpm"])


def _desc(take: str) -> str:
    return (
        f"US-safe rap 180s diss: Nill Bye {take}, "
        "ACE-Step 1.5 turbo AIO, invented vocal"
    )


def _progress_desc(take: str) -> str:
    return (
        f"US-safe rap 180s progress: Nill Bye {take}, "
        "ACE-Step 1.5 turbo AIO, invented vocal"
    )


def format_diss_lyrics(
    *,
    intro: str,
    verses: tuple[str, ...],
    chorus: str,
    outro: str,
    spoken: str | None = None,
) -> str:
    """Build a 180s diss lyric block with repeating choruses."""
    if len(verses) < 3:
        raise ValueError("diss lyrics need at least 3 verses")
    parts: list[str] = []
    if spoken is not None:
        parts.append("[spoken word]\n" + spoken.strip())
    parts.append("[intro]\n" + intro.strip())
    for verse in verses:
        parts.append("[verse]\n" + verse.strip())
        parts.append("[chorus]\n" + chorus.strip())
    parts.append("[outro]\n" + outro.strip())
    return "\n\n".join(parts)


def nill_slug_from_stem(stem: str) -> str:
    """Kebab slug from a legacy or short Nill Bye stem."""
    text = stem.removeprefix("music-rap-nill-bye-").removesuffix("-lab-example")
    if text[:1].isdigit() and "-" in text:
        return text.split("-", 1)[1]
    return text


def finalize_nill_album(rows: Sequence[Mapping[str, Any]]) -> tuple[DissExample, ...]:
    """Number tracks, set album metadata, and rewrite stems for one series."""
    if not rows:
        return ()
    info = nill_album_for_series(rows[0]["series"])
    total = len(rows)
    out: list[DissExample] = []
    for index, row in enumerate(rows, 1):
        slug = nill_slug_from_stem(str(row.get("slug") or row["stem"]))
        stem = f"{index:02d}-{slug}"
        payload: dict[str, Any] = dict(row)
        payload.update(
            {
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
                "phase": info["phase"],
                "prefix": music_output_prefix(str(row["title"]), index),
            }
        )
        out.append(payload)  # type: ignore[arg-type]
    return tuple(out)


def _catalog() -> tuple[DissExample, ...]:
    from .diss_civic import DISS_CIVIC
    from .diss_civic_club import DISS_CIVIC_CLUB
    from .diss_federal import DISS_FEDERAL
    from .diss_federal_club import DISS_FEDERAL_CLUB
    from .diss_lab import DISS_LAB
    from .diss_progress import DISS_PROGRESS
    from .diss_progress_club import DISS_PROGRESS_CLUB
    from .diss_trap_edm import DISS_TRAP_EDM
    from .diss_variety import DISS_VARIETY

    groups = (
        DISS_LAB,
        DISS_VARIETY,
        DISS_TRAP_EDM,
        DISS_CIVIC,
        DISS_CIVIC_CLUB,
        DISS_FEDERAL,
        DISS_FEDERAL_CLUB,
        DISS_PROGRESS,
        DISS_PROGRESS_CLUB,
    )
    out: list[DissExample] = []
    for group in groups:
        out.extend(finalize_nill_album(group))  # type: ignore[arg-type]
    return tuple(out)


DISS_EXAMPLES: tuple[DissExample, ...] = _catalog()
