"""Shared catalog-row builder for the Nill Bye diss series modules.

Logic only: lyrics, tag beds, and series data stay in the ``diss_*`` modules.
One call to :func:`diss_row` builds one pre-album catalog row, so the nine
per-series ``_ex`` helpers are thin bindings over it instead of nine copies of
the same dict. ``ez_music.diss_examples`` re-exports :data:`DISS_DURATION_S`,
:data:`NILL_VOICE`, :func:`nill_output_prefix`, and :func:`nill_tags` from
here, so ``from ez_music.diss_examples import X`` keeps working.

Import stays hermetic (stdlib plus :mod:`ez_music.naming`) so importing this
module never starts the catalog build in ``diss_examples``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypedDict

from .naming import music_output_prefix

if TYPE_CHECKING:
    from .diss_examples import DissExample

    # Completed row: ``diss_examples.finalize_nill_album`` fills the album keys.
    DissExampleRow: TypeAlias = DissExample
else:
    # At runtime a finalized row is a plain dict (``DissExample`` is a TypedDict).
    DissExampleRow: TypeAlias = dict[str, Any]

# Take length and the locked dry-booth vocal for every Nill Bye row.
DISS_DURATION_S = 180.0
NILL_VOICE = "male rap vocals, dry booth, no autotune"


class DissRowSeed(TypedDict):
    """One pre-album catalog row built by :func:`diss_row`.

    Attributes:
        stem: Lab filename stem (``music-rap-nill-bye-<slug>-lab-example``).
        series: Catalog series key.
        title: Operator-facing song title.
        tags: ACE-Step tags line.
        bpm: Tempo written into tags.
        duration: Take length in seconds.
        seed: Fixed ACE / sampler seed.
        phase: Album phase index.
        prefix: SaveAudio stem ``NN - Title``.
        description: Lab graph description.
        lyrics: Formatted lyric block.
    """

    stem: str
    series: str
    title: str
    tags: str
    bpm: int
    duration: float
    seed: int
    phase: int
    prefix: str
    description: str
    lyrics: str


class TakeDescriber(Protocol):
    """Builds a lab graph description from one short take blurb."""

    def __call__(self, take: str) -> str:
        """Return the operator-facing description for one take.

        Args:
            take: Short blurb naming the roast subject.

        Returns:
            Description text for the lab graph.
        """
        ...


def nill_output_prefix(title: str, track: int) -> str:
    """SaveAudio prefix for a Nill Bye take.

    Args:
        title: Catalog song title.
        track: One-based track number (values below 1 become 1).

    Returns:
        ``NN - Song Title``.
    """
    return music_output_prefix(title, track if track >= 1 else 1)


def nill_tags(*parts: str, bpm: int) -> str:
    """Join style tags with the locked Nill Bye vocal and bpm.

    Args:
        parts: Genre and production tags for this take.
        bpm: Tempo written into the tags line.

    Returns:
        Comma-separated ACE-Step tags line.
    """
    return ", ".join([*parts, NILL_VOICE, f"{bpm} bpm"])


def diss_row(
    series: str,
    phase: int,
    desc: TakeDescriber,
    slug: str,
    title: str,
    bpm: int,
    seed: int,
    take: str,
    lyrics: str,
    *tag_parts: str,
    tags: str | None = None,
) -> DissRowSeed:
    """Build one catalog row for a Nill Bye series.

    Series, phase, and description callable come first so each series module
    can bind them once (``functools.partial``) and keep its per-take calls
    positional. ``tags`` replaces the joined ``tag_parts`` for rows that reuse
    a whole tag bed verbatim.

    Args:
        series: Catalog series key (a ``DissSeries`` value).
        phase: Album phase index, also the temporary SaveAudio track number.
        desc: Description builder for the lab graph.
        slug: Kebab title used in the lab stem.
        title: Operator-facing take name.
        bpm: Tempo written into tags.
        seed: Fixed ACE / sampler seed.
        take: Short blurb for the lab description.
        lyrics: Formatted lyric block.
        tag_parts: Style tags joined with the locked vocal.
        tags: Finished tags line that replaces the joined ``tag_parts``.

    Returns:
        Partial catalog row (album fields filled later).
    """
    return {
        "stem": f"music-rap-nill-bye-{slug}-lab-example",
        "series": series,
        "title": title,
        "tags": tags if tags is not None else nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": phase,
        "prefix": nill_output_prefix(title, phase),
        "description": desc(take),
        "lyrics": lyrics,
    }
