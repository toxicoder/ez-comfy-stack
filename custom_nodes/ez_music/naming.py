"""SaveAudio filenames and album output folders.

Format: ``NN - Song Title`` (zero-padded track). Artist and album live
in tags, not the filename. Output dir: ``albums/<Artist>/<Album>/``.
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


def music_output_prefix(title: str, track: int) -> str:
    """Build the SaveAudio filename stem for one catalog take.

    Arguments:
        title: Catalog song title.
        track: One-based track number on the album.
    Returns:
        ``NN - Song Title``.
    Raises:
        ValueError: empty title or track < 1.
    """
    if track < 1:
        raise ValueError(f"track must be >= 1, got {track}")
    return f"{track:02d} - {title_case_song(title)}"


def album_output_dir(artist: str, album: str) -> str:
    """Relative output folder under Comfy output dir.

    Arguments:
        artist: Branded act name.
        album: Album title.
    Returns:
        ``albums/<Artist>/<Album>``.
    Raises:
        ValueError: empty artist or album.
    """
    artist_s = artist.strip()
    album_s = album.strip()
    if artist_s == "":
        raise ValueError("artist is empty")
    if album_s == "":
        raise ValueError("album is empty")
    return f"albums/{artist_s}/{album_s}"
