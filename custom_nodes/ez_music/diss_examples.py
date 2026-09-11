"""Canned 180s Nill Bye vs Rake diss takes for ACE-Step rap lab graphs.

Fictional MCs only. Original lyrics. No living-artist names.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from .naming import NILL_BYE_ARTIST, music_output_prefix

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


def nill_output_prefix(title: str, phase: int) -> str:
    """SaveAudio prefix for a Nill Bye take."""
    return music_output_prefix(NILL_BYE_ARTIST, title, phase)


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

    return (
        DISS_LAB
        + DISS_VARIETY
        + DISS_TRAP_EDM
        + DISS_CIVIC
        + DISS_CIVIC_CLUB
        + DISS_FEDERAL
        + DISS_FEDERAL_CLUB
        + DISS_PROGRESS
        + DISS_PROGRESS_CLUB
    )


DISS_EXAMPLES: tuple[DissExample, ...] = _catalog()
