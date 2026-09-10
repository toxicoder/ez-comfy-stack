"""SaveAudio prefixes for artist catalog graphs.

Format: ``Artist - Song Title - vN`` where N is the catalog phase.
"""

from __future__ import annotations

NILL_BYE_ARTIST = "Nill Bye"
DRIVE_THROUGH_ARTIST = "Drive-through"
_SMALL_WORDS = frozenset({"a", "an", "and", "of", "or", "the", "vs"})


def title_case_song(title: str) -> str:
    """Title-case a catalog song title, including hyphenated tokens.

    Arguments:
        title: Catalog ``title`` field (usually lowercase).
    Returns:
        Title-cased song name for SaveAudio prefixes.
    Raises:
        ValueError: empty title after strip.
    """
    text = title.strip()
    if text == "":
        raise ValueError("song title is empty")
    raw = text.split()
    last = len(raw) - 1
    words: list[str] = []
    for index, word in enumerate(raw):
        lower = word.lower()
        if 0 < index < last and "-" not in word and lower in _SMALL_WORDS:
            words.append(lower)
            continue
        parts: list[str] = []
        for part in word.split("-"):
            if part == "":
                parts.append("")
            else:
                parts.append(part[:1].upper() + part[1:])
        words.append("-".join(parts))
    return " ".join(words)


def music_output_prefix(artist: str, title: str, phase: int) -> str:
    """Build the SaveAudio prefix for one artist take.

    Arguments:
        artist: Branded act name (``Nill Bye``, ``Drive-through``).
        title: Catalog song title.
        phase: Zero-based change-group index (matches ``phaseN/``).
    Returns:
        ``Artist - Song Title - vN``.
    Raises:
        ValueError: empty artist, empty title, or negative phase.
    """
    if phase < 0:
        raise ValueError(f"phase must be >= 0, got {phase}")
    artist_s = artist.strip()
    if artist_s == "":
        raise ValueError("artist is empty")
    return f"{artist_s} - {title_case_song(title)} - v{phase}"
