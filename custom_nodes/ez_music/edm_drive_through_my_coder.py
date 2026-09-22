"""Drive-through album My Coder: the coder, read as bass-set cues.

Fictional act. Instrumental. Each take is one slice of
``drive_arrange.py`` and ``edm_examples.py``. The sketch below only
satisfies the score checker; ``finalize_drive_album`` replaces it with
``code_score`` cues.
"""

from __future__ import annotations

from .code_score import CodeSpan, authored_bpm, coder_spans, performance_recipe
from .edm_examples import EdmExample, _ex, format_edm_score

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
_LAYOUTS: tuple[str, ...] = (
    "column",
    "wide-stage",
    "stacked-tower",
    "prompt-left",
    "output-rail",
)
_SKETCH = format_edm_score(
    ("inst", "heavy warped drop\nstacked 808"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nwreck hats"),
    ("outro", "kick holds\nhats roll"),
)


def _row(index: int, span: CodeSpan) -> EdmExample:
    """One catalog row whose cues will be rewritten from ``span``.

    Args:
        index: Zero-based take index. Selects the seed and the layout.
        span: Coder slice for this take.

    Returns:
        A partial ``EdmExample`` with ``code_tokens`` set.
    """
    row = _ex(
        span.slug,
        span.title,
        authored_bpm(span.tokens),
        _SEEDS[index],
        5,
        f"{span.slug} code warp",
        _SKETCH,
        recipe=performance_recipe(span.tokens),
        layout=_LAYOUTS[index % len(_LAYOUTS)],
    )
    row["code_tokens"] = span.tokens
    return row


def _rows() -> tuple[EdmExample, ...]:
    """Build the sixteen My Coder rows from the current coder source.

    Returns:
        Partial catalog rows for phase 5.

    Raises:
        ValueError: the span count drifted from the seed list.
    """
    spans = coder_spans()
    if len(spans) != len(_SEEDS):
        raise ValueError(f"my coder spans {len(spans)} != seeds {len(_SEEDS)}")
    return tuple(_row(index, span) for index, span in enumerate(spans))


# Phase 5 rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_MY_CODER: tuple[EdmExample, ...] = _rows()
