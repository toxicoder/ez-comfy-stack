"""Runtime film catalog for ez_film (Comfy + host).

YAML bibles under ``workflows/shorts/*.shots.yaml`` must match these rows
(enforced in tests). The catalog is baked into the pack so Comfy can
resolve film widgets without host YAML (entrypoint does not copy shot
bibles into the container).
"""

from __future__ import annotations

import argparse
import sys
from typing import TypedDict


class FilmRow(TypedDict):
    """One shipped film.

    Attributes:
        slug: Output prefix (``ez_<slug>_...``).
        total_shots: Printer count (18 for 90s; 90 for 7.5 min).
        publish_cap_s: ffmpeg ``-t`` cap for the film master.
        beats: Beat count (6 per 90s act; 30 for five-act films).
        shots_per_beat: Always 3 (enter / traverse / exit).
        acts: 1 for 90s one-click; 5 for festival shorts.
    """

    slug: str
    total_shots: int
    publish_cap_s: float
    beats: int
    shots_per_beat: int
    acts: int


ONE_CLICK_SHOT_COUNT = 18
"""EZFilmConcat VHS inputs / 90s printer count."""
DEFAULT_CAP_SECONDS = 90.0
"""Default stitch cap for one-click 90s films."""
SHOTS_PER_BEAT = 3
"""Enter / traverse / exit."""
ACT_SHOT_COUNT = 18
"""Printers in one 90s act graph."""
ACT_CAP_SECONDS = 90.0
"""Stitch cap for one act."""
LONG_SHOT_COUNT = 90
"""Printers in a 7.5 min film (5 acts)."""
LONG_CAP_SECONDS = 450.0
"""Publish cap for a 7.5 min film master."""
LONG_BEATS = 30
"""Beat count for a 7.5 min film."""
LONG_ACTS = 5
"""Act count for a 7.5 min film."""

_NINETY: FilmRow = {
    "slug": "",
    "total_shots": ONE_CLICK_SHOT_COUNT,
    "publish_cap_s": DEFAULT_CAP_SECONDS,
    "beats": 6,
    "shots_per_beat": SHOTS_PER_BEAT,
    "acts": 1,
}
"""Template row for 90s one-click films (slug filled by ``_row``)."""
_LONG: FilmRow = {
    "slug": "",
    "total_shots": LONG_SHOT_COUNT,
    "publish_cap_s": LONG_CAP_SECONDS,
    "beats": LONG_BEATS,
    "shots_per_beat": SHOTS_PER_BEAT,
    "acts": LONG_ACTS,
}
"""Template row for 7.5 min five-act films (slug filled by ``_row``)."""


def _row(slug: str, *, long: bool = False) -> FilmRow:
    """Return a catalog row with ``slug`` filled.

    Args:
        slug: Output prefix.
        long: True for 7.5 min five-act films.

    Returns:
        FilmRow copy.
    """
    base = _LONG if long else _NINETY
    return {
        "slug": slug,
        "total_shots": base["total_shots"],
        "publish_cap_s": base["publish_cap_s"],
        "beats": base["beats"],
        "shots_per_beat": base["shots_per_beat"],
        "acts": base["acts"],
    }


FILMS: dict[str, FilmRow] = {
    "go-see": _row("gosee"),
    "still-here": _row("stillhere"),
    "switchyard": _row("switchyard"),
    "tide-table": _row("tidetable", long=True),
    "night-oven": _row("nightoven", long=True),
    "glasshouse": _row("glasshouse", long=True),
    "last-lane": _row("lastlane", long=True),
    "breakwater": _row("breakwater", long=True),
}
"""Shipped film ids -> slug, shot count, publish cap, beat map."""

FILM_SLUGS: dict[str, str] = {film: row["slug"] for film, row in FILMS.items()}
"""Film id -> output prefix."""
FILM_CHOICES: tuple[str, ...] = tuple(FILMS)
"""Ordered film ids for Comfy combo widgets."""
NINETY_S_FILMS: tuple[str, ...] = tuple(
    film for film, row in FILMS.items() if row["acts"] == 1
)
"""90s one-click titles."""
LONG_FILMS: tuple[str, ...] = tuple(
    film for film, row in FILMS.items() if row["acts"] > 1
)
"""7.5 min five-act titles."""


def known_films() -> tuple[str, ...]:
    """Return shipped film ids in catalog order.

    Returns:
        Film id tuple.
    """
    return FILM_CHOICES


def film_row(film: str) -> FilmRow:
    """Return the catalog row for ``film``.

    Args:
        film: Film id (``go-see``, ``tide-table``, ...).

    Returns:
        FilmRow.

    Raises:
        ValueError: unknown film id.
    """
    row = FILMS.get(film)
    if row is None:
        known = "|".join(FILM_CHOICES)
        raise ValueError(f"unknown film: {film} ({known})")
    return row


def film_slug(film: str) -> str:
    """Map film id to output prefix slug.

    Args:
        film: Film id.

    Returns:
        Slug string.

    Raises:
        ValueError: unknown film id.
    """
    return film_row(film)["slug"]


def film_total_shots(film: str) -> int:
    """Return printer count for ``film``.

    Args:
        film: Film id.

    Returns:
        Shot count.
    """
    return int(film_row(film)["total_shots"])


def film_publish_cap(film: str) -> float:
    """Return publish cap seconds for ``film``.

    Args:
        film: Film id.

    Returns:
        Cap in seconds (90.0 or 450.0).
    """
    return float(film_row(film)["publish_cap_s"])


def film_beats(film: str) -> int:
    """Return beat count for ``film``.

    Args:
        film: Film id.

    Returns:
        Beat count.
    """
    return int(film_row(film)["beats"])


def film_acts(film: str) -> int:
    """Return act count for ``film``.

    Args:
        film: Film id.

    Returns:
        Act count (1 or 5).
    """
    return int(film_row(film)["acts"])


def film_id_for_slug(slug: str) -> str | None:
    """Return film id for an output slug, or None.

    Args:
        slug: Output prefix (``gosee``, ``tidetable``, ...).

    Returns:
        Film id, or None when unknown.
    """
    for film, row in FILMS.items():
        if row["slug"] == slug:
            return film
    return None


def master_filename(film: str, *, act: int = 0) -> str:
    """Return the published MP4 basename for ``film``.

    Args:
        film: Film id.
        act: 1-based act index; 0 means the whole-film master.

    Returns:
        Basename such as ``ez_gosee_90s.mp4`` or ``ez_tidetable_act1_90s.mp4``.
    """
    slug = film_slug(film)
    if act > 0:
        return f"ez_{slug}_act{act}_90s.mp4"
    cap = film_publish_cap(film)
    return f"ez_{slug}_{int(round(cap))}s.mp4"


def _cli(argv: list[str] | None = None) -> int:
    """Print one catalog field for shell helpers.

    Args:
        argv: Argument vector, or None for ``sys.argv``.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(prog="ez_film.catalog")
    parser.add_argument(
        "field",
        choices=("slug", "cap", "shots", "beats", "acts", "master", "ids"),
        help="Field to print",
    )
    parser.add_argument("film", nargs="?", default="", help="Film id")
    parser.add_argument(
        "--act",
        type=int,
        default=0,
        help="Act index for master filenames (0 = film master)",
    )
    args = parser.parse_args(argv)
    try:
        if args.field == "ids":
            print(" ".join(FILM_CHOICES))
            return 0
        if not args.film:
            print("film id required", file=sys.stderr)
            return 1
        if args.field == "slug":
            print(film_slug(args.film))
        elif args.field == "cap":
            print(f"{film_publish_cap(args.film):.2f}")
        elif args.field == "shots":
            print(str(film_total_shots(args.film)))
        elif args.field == "beats":
            print(str(film_beats(args.film)))
        elif args.field == "acts":
            print(str(film_acts(args.film)))
        else:
            print(master_filename(args.film, act=int(args.act)))
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
