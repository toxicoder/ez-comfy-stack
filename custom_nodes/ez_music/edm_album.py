"""Album-template knowledge shared by the Drive-through EDM catalogs.

One live-set hour per album module, one shape of take across all of
them. This module holds that shape: the placement cycle, the live-set
hour indexes, the per-take record, and ``build_album``. An album module
keeps only its docstring, its scores, and its take table.

Leaf module: stdlib and ``typing`` only. Album modules hand ``_ex`` from
``edm_examples`` to ``build_album``, so nothing here imports back into
the catalog and no cycle can form through ``drive_arrange`` (which
imports ``edm_examples`` lazily, inside a function).

Attributes:
    EDM_LAYOUTS: Comfy node placement names a Drive-through take may use.
    DRIVE_THROUGH_PHASE: Live-set hour index of Hour 1.
    BASS_PHASE: Live-set hour index of Hour 2.
    HEADLINER_PHASE: Live-set hour index of the Headliner album.
    AFTERPARTY_PHASE: Live-set hour index of the Afterparty album.
    SECRET_HOMAGE_PHASE: Live-set hour index of the Secret Homage album.
    MY_CODER_PHASE: Live-set hour index of the My Coder album.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NotRequired, Protocol, TypedDict, TypeVar

T_co = TypeVar("T_co", covariant=True)

# Placement cycle. Order matters: it is the order an hour's takes walk,
# and the first name is the placement every take gets by default.
_LAYOUT_ORDER: tuple[str, ...] = (
    "column",
    "wide-stage",
    "stacked-tower",
    "prompt-left",
    "output-rail",
)

# Valid Comfy node placements, derived from the cycle above.
EDM_LAYOUTS = frozenset(_LAYOUT_ORDER)

# Live-set hour indexes, in catalog order (albums.py keys on these).
DRIVE_THROUGH_PHASE = 0
BASS_PHASE = 1
HEADLINER_PHASE = 2
AFTERPARTY_PHASE = 3
SECRET_HOMAGE_PHASE = 4
MY_CODER_PHASE = 5

# Legacy lab stem prefix a take table must not repeat.
_LEGACY_STEM_PREFIX = "music-edm-drive-through-"


class DriveRowSpec(TypedDict):
    """One authored Drive-through take, as an album module writes it.

    ``build_album`` fills the optional fields before handing the record
    to the row builder, so a table lists only what differs from one
    track to the next.

    Attributes:
        slug: Kebab title used in the lab stem.
        bpm: Tempo written into tags and the ACE encoder.
        seed: Fixed ACE / sampler seed.
        take: Short blurb for the lab graph description.
        lyrics: Arrangement score from ``format_edm_score``.
        recipe: Audio Rack recipe id (fills empty axes).
        title: Operator-facing take name; defaults to the spaced slug.
        picks: Axis overrides; tempo is always ``tmp_<bpm>``.
        layout: Comfy node placement name; defaults to this track's slot
            in the album's layout sequence.
    """

    slug: str
    bpm: int
    seed: int
    take: str
    lyrics: str
    recipe: str
    title: NotRequired[str]
    picks: NotRequired[dict[str, str]]
    layout: NotRequired[str]


class DriveRowBuilder(Protocol[T_co]):
    """Callable turning one take's fields into a catalog row.

    The arguments mirror ``edm_examples._ex``, which satisfies this seam
    as written: the positional fields are ``slug``, ``title``, ``bpm``,
    ``seed``, ``phase``, ``take``, and ``lyrics``; the keyword-only
    fields are ``recipe``, ``picks``, and ``layout``. An album module can
    therefore hand ``_ex`` to ``build_album`` unchanged.
    """

    def __call__(
        self,
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
        layout: str = "column",
    ) -> T_co: ...


def title_from_slug(slug: str) -> str:
    """Operator-facing take name for a kebab slug.

    Args:
        slug: Kebab title used in the lab stem.

    Returns:
        The slug with every hyphened word spaced apart.
    """
    return slug.replace("-", " ")


def drive_slug(prefix: str, stem: str) -> str:
    """Kebab title slug from a legacy or short Drive-through stem.

    Args:
        prefix: Legacy lab stem prefix to strip (album-scoped).
        stem: Lab filename stem (legacy prefix optional).

    Returns:
        Title slug without the legacy affixes or the numeric track prefix.
    """
    text = stem.removeprefix(prefix).removesuffix("-lab-example")
    if text[:1].isdigit() and "-" in text:
        return text.split("-", 1)[1]
    return text


def layout_cycle(count: int, *, offset: int = 0) -> tuple[str, ...]:
    """Placement sequence for one hour's tracks.

    Args:
        count: Track count of the album.
        offset: How far along the cycle the album starts, in placements.

    Returns:
        One placement per track, walking the cycle.
    """
    span = len(_LAYOUT_ORDER)
    return tuple(_LAYOUT_ORDER[(index + offset) % span] for index in range(count))


def build_album(
    takes: Sequence[DriveRowSpec],
    *,
    phase: int,
    row_for: DriveRowBuilder[T_co],
    layouts: Sequence[str] | None = None,
) -> tuple[T_co, ...]:
    """Build one live-set hour's rows from its authored take table.

    Titles default to the spaced slug and layouts default to the album's
    own sequence, so a table names neither a track number nor a
    placement it did not choose. ``layouts`` stays ``None`` for an hour
    that stages every take in the default placement.
    ``finalize_drive_album`` numbers and labels the rows later.

    Args:
        takes: Authored takes, in track order.
        phase: Live-set hour index shared by the album's takes.
        row_for: Row builder, typically ``edm_examples._ex``.
        layouts: Placement per track; ``None`` stages every take the same.

    Returns:
        One partial catalog row per take, in track order.

    Raises:
        ValueError: a table pasted a lab stem or a numbered stem instead
            of a bare kebab title, ``layouts`` is shorter than the take
            table, or a named placement is outside ``EDM_LAYOUTS``.
    """
    if layouts is not None and len(layouts) < len(takes):
        raise ValueError(f"phase {phase} needs {len(takes)} layouts, got {len(layouts)}")
    rows: list[T_co] = []
    for index, take in enumerate(takes):
        slug = take["slug"]
        if drive_slug(_LEGACY_STEM_PREFIX, slug) != slug:
            raise ValueError(f"take {index} of phase {phase} has stem {slug!r}")
        layout = take.get("layout") or (_LAYOUT_ORDER[0] if layouts is None else layouts[index])
        if layout not in EDM_LAYOUTS:
            raise ValueError(f"take {index} of phase {phase} has layout {layout!r}")
        picks = take.get("picks")
        rows.append(
            row_for(
                slug,
                take.get("title") or title_from_slug(slug),
                take["bpm"],
                take["seed"],
                phase,
                take["take"],
                take["lyrics"],
                recipe=take["recipe"],
                picks=None if picks is None else dict(picks),
                layout=layout,
            )
        )
    return tuple(rows)
