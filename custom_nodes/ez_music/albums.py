"""Album titles, slugs, and cover prompts for catalog music.

Fictional acts only. Cover prompts forbid living-person likeness.
"""

from __future__ import annotations

from typing import TypedDict

from .naming import DRIVE_THROUGH_ARTIST, NILL_BYE_ARTIST

# Shared release year stamped on every catalog album.
ALBUM_YEAR = 2026


class AlbumInfo(TypedDict):
    """One shipped album row (artist, slug, cover prompt).

    Attributes:
        artist: Branded act name.
        artist_slug: Folder slug under ``audio/albums``.
        title: Album title.
        slug: Folder slug for the album.
        series: Catalog series key.
        phase: Zero-based series or live-set index.
        year: Release year stamped on masters.
        cover_prompt: US-safe cover-art prompt (no living likeness).
    """

    artist: str
    artist_slug: str
    title: str
    slug: str
    series: str
    phase: int
    year: int
    cover_prompt: str


def _cover(artist: str, album: str, scene: str) -> str:
    """Build a US-safe square cover prompt (no living likeness).

    Args:
        artist: Fictional act name.
        album: Album title.
        scene: Graphic-print scene (no faces).

    Returns:
        Cover-art prompt string.
    """
    return (
        f"square album cover, graphic print, {scene}, "
        f"fictional act {artist}, album {album}, no text, no letters, "
        "no logos, no living person likeness, no celebrity, no photograph"
    )


# Shipped Nill Bye and Drive-through album rows.
NILL_BYE_ALBUMS: dict[str, AlbumInfo] = {
    "lab": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Peer Review",
        "slug": "peer-review",
        "series": "lab",
        "phase": 0,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Peer Review",
            "chalkboard, lab coat silhouette, beaker, cool fluorescent light",
        ),
    },
    "variety": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Citation Needed",
        "slug": "citation-needed",
        "series": "variety",
        "phase": 1,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Citation Needed",
            "empty footnote, stacked papers, warm desk lamp",
        ),
    },
    "trap-edm": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "False Drop",
        "slug": "false-drop",
        "series": "trap-edm",
        "phase": 2,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "False Drop",
            "club fog, dry booth silhouette, magenta strobe, no crowd faces",
        ),
    },
    "civic": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Frozen Ercot",
        "slug": "frozen-ercot",
        "series": "civic",
        "phase": 3,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Frozen Ercot",
            "iced power lines, Texas winter grid, cold blue night",
        ),
    },
    "civic-club": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Lone Star Tab",
        "slug": "lone-star-tab",
        "series": "civic-club",
        "phase": 4,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Lone Star Tab",
            "receipt roll, lone star outline, club light on paper",
        ),
    },
    "federal": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Thirty Four Counts",
        "slug": "thirty-four-counts",
        "series": "federal",
        "phase": 5,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Thirty Four Counts",
            "ledger book, tally marks, marble courthouse steps, no faces",
        ),
    },
    "federal-club": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Pardon Flood",
        "slug": "pardon-flood",
        "series": "federal-club",
        "phase": 6,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Pardon Flood",
            "flooded document stack, gold stamp, dark club wash",
        ),
    },
    "progress": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Winterize Wells",
        "slug": "winterize-wells",
        "series": "progress",
        "phase": 7,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Winterize Wells",
            "wellhead jacket, frost, measurement clipboard, dawn light",
        ),
    },
    "progress-club": {
        "artist": NILL_BYE_ARTIST,
        "artist_slug": "nill-bye",
        "title": "Duty Switch",
        "slug": "duty-switch",
        "series": "progress-club",
        "phase": 8,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            NILL_BYE_ARTIST,
            "Duty Switch",
            "breaker switch, statute book, club magenta on steel",
        ),
    },
}

DRIVE_THROUGH_ALBUMS: dict[int, AlbumInfo] = {
    0: {
        "artist": DRIVE_THROUGH_ARTIST,
        "artist_slug": "drive-through",
        "title": "Hour 1",
        "slug": "hour-1",
        "series": "drive-through",
        "phase": 0,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            DRIVE_THROUGH_ARTIST,
            "Hour 1",
            "night highway overpass, warped neon bass, wet asphalt",
        ),
    },
    1: {
        "artist": DRIVE_THROUGH_ARTIST,
        "artist_slug": "drive-through",
        "title": "Hour 2",
        "slug": "hour-2",
        "series": "drive-through",
        "phase": 1,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            DRIVE_THROUGH_ARTIST,
            "Hour 2",
            "toll booth glow, chest-sub night, long exposure headlights",
        ),
    },
    2: {
        "artist": DRIVE_THROUGH_ARTIST,
        "artist_slug": "drive-through",
        "title": "Headliner",
        "slug": "headliner",
        "series": "drive-through",
        "phase": 2,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            DRIVE_THROUGH_ARTIST,
            "Headliner",
            "forest canopy rave lights, no faces, warped bass wall",
        ),
    },
    3: {
        "artist": DRIVE_THROUGH_ARTIST,
        "artist_slug": "drive-through",
        "title": "Afterparty",
        "slug": "afterparty",
        "series": "drive-through",
        "phase": 3,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            DRIVE_THROUGH_ARTIST,
            "Afterparty",
            "empty lot sodium lamps, trailer hitch, grit steel",
        ),
    },
    4: {
        "artist": DRIVE_THROUGH_ARTIST,
        "artist_slug": "drive-through",
        "title": "Secret Homage",
        "slug": "secret-homage",
        "series": "drive-through",
        "phase": 4,
        "year": ALBUM_YEAR,
        "cover_prompt": _cover(
            DRIVE_THROUGH_ARTIST,
            "Secret Homage",
            "hidden alley stencil, sealed ramp, fog vault, no faces",
        ),
    },
}


def nill_album_for_series(series: str) -> AlbumInfo:
    """Return the Nill Bye album row for a catalog series.

    Args:
        series: Diss series key (``lab``, ``civic``, …).
    Returns:
        Album metadata.
    Raises:
        KeyError: unknown series.
    """
    return NILL_BYE_ALBUMS[series]


def drive_album_for_phase(phase: int) -> AlbumInfo:
    """Return the Drive-through album row for a catalog phase.

    Args:
        phase: Zero-based live-set hour index.
    Returns:
        Album metadata.
    Raises:
        KeyError: unknown phase.
    """
    return DRIVE_THROUGH_ALBUMS[phase]


def shipped_albums() -> tuple[AlbumInfo, ...]:
    """Nill Bye albums in catalog order, then Drive-through hours.

    Returns:
        Album metadata rows in ship order.
    """
    nill = tuple(NILL_BYE_ALBUMS[key] for key in NILL_BYE_ALBUMS)
    drive = tuple(DRIVE_THROUGH_ALBUMS[key] for key in sorted(DRIVE_THROUGH_ALBUMS))
    return nill + drive


def album_rel(artist_slug: str, album_slug: str, stem: str) -> str:
    """Lab-relative id under ``audio/albums``.

    Args:
        artist_slug: Folder name (``nill-bye``).
        album_slug: Folder name (``peer-review``).
        stem: File stem (``01-lab-coat``, ``album``, ``cover``).
    Returns:
        ``audio/albums/<artist>/<album>/<stem>``.
    """
    return f"audio/albums/{artist_slug}/{album_slug}/{stem}"
