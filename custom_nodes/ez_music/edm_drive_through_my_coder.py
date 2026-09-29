"""Drive-through album My Coder: the coder, read as bass-set cues.

Fictional act. Instrumental. Each take is one slice of
``drive_arrange.py`` and ``edm_examples.py``. The sketch below only
satisfies the score checker; ``finalize_drive_album`` replaces it with
``code_score`` cues.
"""

from __future__ import annotations

from collections.abc import Sequence

from .code_score import CodeSpan, authored_bpm, coder_spans, performance_recipe
from .edm_album import (
    MY_CODER_PHASE,
    DriveRowSpec,
    build_album,
    layout_cycle,
)
from .edm_examples import EdmExampleRow, _ex, format_edm_score

# Fixed seeds, continuing the catalog primes after Secret Homage.
_SEEDS: tuple[int, ...] = (
    719,
    727,
    733,
    739,
    743,
    751,
    757,
    761,
    769,
    773,
    787,
    797,
    809,
    811,
    821,
    823,
)
_SKETCH = format_edm_score(
    ("inst", "heavy warped drop\nstacked 808"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nwreck hats"),
    ("outro", "kick holds\nhats roll"),
)


def _takes(spans: Sequence[CodeSpan]) -> tuple[DriveRowSpec, ...]:
    """Authored take table for the current coder spans.

    Args:
        spans: One coder slice per take, in album order.

    Returns:
        One take record per span, in album order. The seeds continue the
        catalog primes; the recipe and tempo come from that span's words.
    """
    return tuple(
        {
            "slug": span.slug,
            "title": span.title,
            "bpm": authored_bpm(span.tokens),
            "seed": _SEEDS[index],
            "take": f"{span.slug} code warp",
            "lyrics": _SKETCH,
            "recipe": performance_recipe(span.tokens),
        }
        for index, span in enumerate(spans)
    )


def _rows() -> tuple[EdmExampleRow, ...]:
    """Build the sixteen My Coder rows from the current coder source.

    Returns:
        Partial catalog rows for phase 5, each carrying its span's words
        as ``code_tokens`` for ``finalize_drive_album`` to voice.

    Raises:
        ValueError: the span count drifted from the seed list.
    """
    spans = coder_spans()
    if len(spans) != len(_SEEDS):
        raise ValueError(f"my coder spans {len(spans)} != seeds {len(_SEEDS)}")
    rows = build_album(
        _takes(spans),
        phase=MY_CODER_PHASE,
        row_for=_ex,
        layouts=layout_cycle(len(spans)),
    )
    for row, span in zip(rows, spans):
        row["code_tokens"] = span.tokens
    return rows


# Phase 5 rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_MY_CODER: tuple[EdmExampleRow, ...] = _rows()
