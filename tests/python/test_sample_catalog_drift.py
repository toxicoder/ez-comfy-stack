"""Lock the shipped sample catalogs to their generators.

``js/samples/*.json`` had no equality check against ``_build_sample_catalogs.py``,
so the builders drifted: each emitted 20 rows while the shipped catalogs carried
30, and re-running the generator would have silently deleted 10 hand-authored
recipes from every catalog. These tests make that impossible in both
directions - the generator may not drop rows, and the JSON may not drift from
the builder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _entry in (str(ROOT / "tests" / "python"), str(ROOT / "custom_nodes")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import _build_sample_catalogs as builder  # noqa: E402
from ez_prompt_enhance import samples  # noqa: E402

SAMPLES_DIR = builder.DEST

# Catalogs that are hand-authored on purpose. The background catalogs are
# pinned row-by-row by tests/python/test_background.py, and podcast_learn is a
# text seed, so none of them is generated. Anything else must have a generator.
HAND_AUTHORED = frozenset(
    {"klein_background_swap", "klein_background_edit", "podcast_learn"}
)


def _generated() -> dict[str, list[dict[str, str]]]:
    """Return every catalog the generators own.

    Captures what ``main()`` would write by wrapping its writer instead of
    duplicating the builder's registration list, then folds in the hand
    generator. The completeness check at the end of ``main()`` raises, so the
    capture runs under a guard.

    Returns:
        Catalog stem to rows.
    """
    captured: dict[str, list[dict[str, str]]] = {}

    def _capture(name: str, rows: list[dict[str, str]]) -> None:
        captured[name] = rows

    original = builder._write
    builder._write = _capture  # type: ignore[assignment]
    try:
        try:
            builder.main()
        except SystemExit:
            pass
    finally:
        builder._write = original  # type: ignore[assignment]

    import _build_hand_catalogs as hand

    captured.update(hand.hand_catalogs())
    return captured


def _shipped(name: str) -> list[dict[str, str]]:
    """Return the catalog rows committed on disk.

    Arguments:
        name: Catalog file stem.

    Returns:
        Parsed rows.
    """
    return json.loads((SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _expected(name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return the rows ``_write`` would persist for a builder's output.

    Mirrors the merge the writer performs: the builder authors the head, the
    shipped file supplies any hand-authored tail, and the goal clause is folded
    in last.

    Arguments:
        name: Catalog file stem.
        rows: Rows the builder produced.

    Returns:
        The rows that must be on disk.
    """
    clause = samples.goal_field(builder.CATALOG_GOAL.get(name, ""), "sample_clause")
    shipped = _shipped(name)
    if len(rows) < len(shipped):
        rows = rows + shipped[len(rows) :]
    return builder._with_goal(name, rows)


def test_generator_owns_every_shipped_catalog() -> None:
    """No catalog may be unowned except the documented hand-authored set.

    Seven catalogs used to be hand-authored with nothing behind them, so
    nothing could tell whether they were still reproducible. The exceptions
    here are pinned row-by-row by their own suites instead.
    """
    on_disk = {p.stem for p in SAMPLES_DIR.glob("*.json") if p.name != "index.json"}
    missing = sorted(on_disk - set(_generated()) - HAND_AUTHORED)
    assert missing == [], f"catalogs with no generator: {missing}"
    orphaned = sorted(set(_generated()) - on_disk)
    assert orphaned == [], f"generated catalogs never written: {orphaned}"


def test_committed_json_matches_the_generator() -> None:
    """Every shipped catalog must equal what the generator would write."""
    drift: list[str] = []
    for name, rows in sorted(_generated().items()):
        want = _expected(name, rows)
        have = _shipped(name)
        if json.dumps(want, sort_keys=True) != json.dumps(have, sort_keys=True):
            drift.append(name)
    assert drift == [], f"committed JSON diverged from the generator: {drift}"


def test_generator_never_shrinks_a_catalog() -> None:
    """A builder that emits fewer rows must keep the shipped tail.

    This is the regression that would have deleted 10 recipes from each of
    40 catalogs.
    """
    for name, rows in sorted(_generated().items()):
        shipped = _shipped(name)
        clause = samples.goal_field(builder.CATALOG_GOAL.get(name, ""), "sample_clause")
        head = builder._plain_rows(rows, clause)
        assert len(shipped) >= len(rows), name
        assert json.dumps(head, sort_keys=True) == json.dumps(
            builder._plain_rows(shipped[: len(rows)], clause), sort_keys=True
        ), f"{name}: builder head no longer matches the shipped head"


def test_every_catalog_hits_its_required_count() -> None:
    for name in sorted(_generated()):
        assert len(_shipped(name)) == samples.catalog_expected_count(name), name


def test_registered_goals_exist() -> None:
    for name, goal in sorted(builder.CATALOG_GOAL.items()):
        assert goal in samples.load_goals(), f"{name} registers unknown goal {goal}"


def test_goal_clause_is_present_in_registered_catalogs() -> None:
    for name, goal in sorted(builder.CATALOG_GOAL.items()):
        clause = samples.goal_field(goal, "sample_clause")
        assert clause, name
        blob = (SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8")
        assert clause in blob, f"{name} is missing its goal clause"


def test_goal_clause_absent_from_shared_catalogs() -> None:
    """Catalogs that serve many goals must not carry one goal's advice."""
    shared = ("klein_t2i", "wan_i2v", "ltx_i2v")
    clauses = [
        samples.goal_field(goal, "sample_clause")
        for goal in set(builder.CATALOG_GOAL.values())
    ]
    for name in shared:
        blob = (SAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8")
        for clause in clauses:
            assert clause not in blob, f"{name} picked up goal language it should not"


def test_samples_stay_ascii() -> None:
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        assert path.read_text(encoding="utf-8").isascii(), path.name


def test_generator_is_a_pure_function_of_its_builders(tmp_path: Path) -> None:
    """Writing twice must be a no-op, so a re-run cannot erode the catalogs.

    Arguments:
        tmp_path: Scratch directory, unused by the writer but reserved for
            isolation when the generator grows a destination override.
    """
    before = {
        p.name: p.read_text(encoding="utf-8")
        for p in sorted(SAMPLES_DIR.glob("*.json"))
    }
    for name, rows in sorted(_generated().items()):
        builder._write(name, _expected(name, rows))
    after = {
        p.name: p.read_text(encoding="utf-8")
        for p in sorted(SAMPLES_DIR.glob("*.json"))
    }
    assert after == before
