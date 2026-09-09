"""Canned 180s Drive-through EDM takes for ACE-Step lab graphs.

Fictional act only. Original instrumental arrangements. No living-artist names.
"""

from __future__ import annotations

from typing import Literal, TypedDict

EDM_DURATION_S = 180.0
DRIVE_LOCK = "instrumental, no vocals, original composition"
EdmSeries = Literal["drive-through"]

_DROP_DURATION_NEEDLES = ("thirty second", "30 second")
_INSPIRE_NEEDLES = ("vast", "horizon", "open", "heart")


class EdmExample(TypedDict):
    stem: str
    series: EdmSeries
    title: str
    tags: str
    bpm: int
    duration: float
    seed: int
    prefix: str
    description: str
    lyrics: str


def drive_tags(*parts: str, bpm: int) -> str:
    """Join style tags with the locked instrumental Drive-through bed and bpm."""
    return ", ".join([*parts, DRIVE_LOCK, f"{bpm} bpm"])


def _desc(take: str) -> str:
    return (
        f"US-safe EDM 180s: Drive-through {take}, "
        "ACE-Step 1.5 turbo AIO, instrumental, invented timbre"
    )


def format_edm_arrangement(
    *,
    intro: str,
    melody: str,
    build: str,
    drop: str,
    break_: str,
    build2: str,
    drop2: str,
    outro: str,
) -> str:
    """Build a 180s instrumental score: melody, 30s drop, break, repeat.

    Arguments:
        intro: Atmosphere before the first melody.
        melody: Adventurous / inspiring bed (must invoke vast/horizon/open/heart).
        build: Tension into drop 1.
        drop: First ~30 s hard drop (must name a thirty-second drop).
        break_: Return to the vast bed (same inspire needles as melody).
        build2: Tension into drop 2.
        drop2: Second ~30 s hard drop (same duration needle as drop).
        outro: Tail after the second drop.
    Returns:
        ACE-Step lyrics with [intro], six [inst] blocks, and [outro].
    Raises:
        ValueError: if a drop is not ~30 s, or melody/break skip the inspire lock.
    """
    for name, block in (("drop", drop), ("drop2", drop2)):
        low = block.lower()
        if "drop" not in low:
            raise ValueError(f"{name} must name a drop")
        if not any(needle in low for needle in _DROP_DURATION_NEEDLES):
            raise ValueError(f"{name} must last about thirty seconds")
    for name, block in (("melody", melody), ("break_", break_)):
        low = block.lower()
        if not any(needle in low for needle in _INSPIRE_NEEDLES):
            raise ValueError(f"{name} must invoke vast/horizon/open/heart")
    parts = [
        "[intro]\n" + intro.strip(),
        "[inst]\n" + melody.strip(),
        "[inst]\n" + build.strip(),
        "[inst]\n" + drop.strip(),
        "[inst]\n" + break_.strip(),
        "[inst]\n" + build2.strip(),
        "[inst]\n" + drop2.strip(),
        "[outro]\n" + outro.strip(),
    ]
    return "\n\n".join(parts)


def _catalog() -> tuple[EdmExample, ...]:
    from .edm_drive_through import EDM_DRIVE_THROUGH

    return EDM_DRIVE_THROUGH


EDM_EXAMPLES: tuple[EdmExample, ...] = _catalog()
