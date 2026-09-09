"""Canned 180s Drive-through EDM takes for ACE-Step lab graphs.

Fictional act only. Original dance arrangements. No living-artist names.
"""

from __future__ import annotations

from typing import Literal, TypedDict

EDM_DURATION_S = 180.0
DRIVE_LOCK = "instrumental, no vocals, no singing, original composition"
DRIVE_TREAT_LOCK = "sparse vocal chop, DJ shout, no rap, original composition"
EdmSeries = Literal["drive-through"]
EdmAceMode = Literal["instrumental", "vocal"]

SCORE_LABELS = frozenset({"intro", "inst", "outro", "chorus"})
DROP_WEIGHT_NEEDLES = (
    "heavy",
    "wreck",
    "harder",
    "stacked",
    "full send",
    "mainstage",
)


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
    ace_mode: EdmAceMode


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
        f"ACE-Step 1.5 turbo AIO, {vocal}, invented timbre"
    )


def format_edm_score(*sections: tuple[str, str]) -> str:
    """Build a 180s ACE-Step score from labeled sections.

    Labels are intro, inst, outro, and chorus (DJ-shout treats only).
    This is not the Nill Bye verse/chorus loop and not a fixed
    melody-drop-break-drop skeleton.

    Arguments:
        sections: (label, body) pairs. Bodies are production cues.
    Returns:
        ACE-Step lyrics with labeled blocks.
    Raises:
        ValueError: too few sections, unknown label, empty body, fewer
            than two named drops, or a drop without a weight needle.
    """
    if len(sections) < 3:
        raise ValueError("score needs at least three sections")
    drop_count = 0
    parts: list[str] = []
    for label, body in sections:
        if label not in SCORE_LABELS:
            raise ValueError(f"unknown score label {label}")
        text = body.strip()
        if not text:
            raise ValueError(f"{label} body is empty")
        low = text.lower()
        if "drop" in low:
            drop_count += 1
            if not any(needle in low for needle in DROP_WEIGHT_NEEDLES):
                raise ValueError("drop must hit a weight needle")
        parts.append(f"[{label}]\n{text}")
    if drop_count < 2:
        raise ValueError("score needs at least two named drops")
    return "\n\n".join(parts)


def _catalog() -> tuple[EdmExample, ...]:
    from .edm_drive_through import EDM_DRIVE_THROUGH

    return EDM_DRIVE_THROUGH


EDM_EXAMPLES: tuple[EdmExample, ...] = _catalog()
