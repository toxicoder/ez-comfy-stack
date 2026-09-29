"""Hermetic tests for the shared Nill Bye catalog-row factory.

Covers ``ez_music.diss_rows`` (row builder, tag join, SaveAudio prefix) and pins
each per-series ``_ex`` binding to factory output, so the de-duplicated series
builders keep emitting the exact frozen catalog rows.
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music import diss_rows  # noqa: E402
from ez_music.diss_examples import (  # noqa: E402
    DISS_DURATION_S,
    DISS_EXAMPLES,
    NILL_VOICE,
    _desc,
    _progress_desc,
)
from ez_music.diss_rows import (  # noqa: E402
    DissRowSeed,
    TakeDescriber,
    diss_row,
    nill_output_prefix,
    nill_tags,
)

# series key, module, tuple name, phase constant, phase value, describer name.
SeriesCase = tuple[str, str, str, str, int, str]
SERIES_CASES: tuple[SeriesCase, ...] = (
    ("lab", "diss_lab", "DISS_LAB", "LAB_PHASE", 0, "_desc"),
    ("variety", "diss_variety", "DISS_VARIETY", "VARIETY_PHASE", 1, "_desc"),
    ("trap-edm", "diss_trap_edm", "DISS_TRAP_EDM", "TRAP_EDM_PHASE", 2, "_desc"),
    ("civic", "diss_civic", "DISS_CIVIC", "CIVIC_PHASE", 3, "_desc"),
    (
        "civic-club",
        "diss_civic_club",
        "DISS_CIVIC_CLUB",
        "CIVIC_CLUB_PHASE",
        4,
        "_desc",
    ),
    ("federal", "diss_federal", "DISS_FEDERAL", "FEDERAL_PHASE", 5, "_desc"),
    (
        "federal-club",
        "diss_federal_club",
        "DISS_FEDERAL_CLUB",
        "FEDERAL_CLUB_PHASE",
        6,
        "_desc",
    ),
    (
        "progress",
        "diss_progress",
        "DISS_PROGRESS",
        "PROGRESS_PHASE",
        7,
        "_progress_desc",
    ),
    (
        "progress-club",
        "diss_progress_club",
        "DISS_PROGRESS_CLUB",
        "PROGRESS_CLUB_PHASE",
        8,
        "_progress_desc",
    ),
)

ROW_KEYS = (
    "stem",
    "series",
    "title",
    "tags",
    "bpm",
    "duration",
    "seed",
    "phase",
    "prefix",
    "description",
    "lyrics",
)

# Sentinel spliced into a describer to split its fixed prefix from its suffix.
TAKE_MARK = "<<take>>"


def _describe(take: str) -> str:
    """Description stub used by factory unit tests.

    Args:
        take: Short blurb.

    Returns:
        Description text.
    """
    return f"desc: {take}"


def _module(name: str) -> ModuleType:
    """Import one ``ez_music`` module by bare name.

    Args:
        name: Module name without the package prefix.

    Returns:
        The imported module.
    """
    __import__(f"ez_music.{name}")
    module: ModuleType = sys.modules[f"ez_music.{name}"]
    return module


def _take_from(description: str, describer: TakeDescriber) -> str:
    """Recover the authored blurb from one built description.

    Args:
        description: Row ``description`` value.
        describer: Description callable the series binds.

    Returns:
        The ``take`` argument that produced ``description``.

    Raises:
        AssertionError: description does not match the describer shape.
    """
    head, _, tail = describer(TAKE_MARK).partition(TAKE_MARK)
    if not description.startswith(head) or not description.endswith(tail):
        raise AssertionError(f"unexpected description: {description}")
    return description[len(head) : len(description) - len(tail)]


def _series_rows(module_name: str, tuple_name: str) -> tuple[DissRowSeed, ...]:
    """Read one series tuple as pre-album rows.

    Args:
        module_name: Series module name.
        tuple_name: ``DISS_<SERIES>`` constant name.

    Returns:
        The pre-album rows in track order.
    """
    rows: tuple[DissRowSeed, ...] = tuple(getattr(_module(module_name), tuple_name))
    return rows


def test_diss_row_joins_tag_parts_into_tags() -> None:
    row = diss_row(
        "civic",
        3,
        _describe,
        "frozen-ercot",
        "frozen ercot",
        88,
        191,
        "roast of Abbott",
        "LYRICS",
        "boom bap",
        "hip-hop",
    )
    assert row["stem"] == "music-rap-nill-bye-frozen-ercot-lab-example"
    assert row["series"] == "civic"
    assert row["title"] == "frozen ercot"
    assert row["tags"] == nill_tags("boom bap", "hip-hop", bpm=88)
    assert row["bpm"] == 88
    assert row["duration"] == DISS_DURATION_S
    assert row["seed"] == 191
    assert row["phase"] == 3
    assert row["prefix"] == nill_output_prefix("frozen ercot", 3)
    assert row["description"] == "desc: roast of Abbott"
    assert row["lyrics"] == "LYRICS"
    assert tuple(row) == ROW_KEYS


def test_diss_row_tags_override_replaces_joined_parts() -> None:
    row = diss_row(
        "lab",
        0,
        _describe,
        "lab-coat",
        "lab coat lecture",
        88,
        42,
        "roast of Rake",
        "LYRICS",
        "ignored",
        tags="whole tag bed",
    )
    assert row["tags"] == "whole tag bed"


def test_diss_row_without_tag_parts_yields_voice_and_bpm() -> None:
    row = diss_row("lab", 0, _describe, "slug", "title", 90, 1, "blurb", "LYRICS")
    assert row["tags"] == f"{NILL_VOICE}, 90 bpm"


def test_row_seed_declares_every_row_key() -> None:
    assert set(DissRowSeed.__annotations__) == set(ROW_KEYS)
    assert DissRowSeed.__total__ is True


def test_diss_row_signature_keeps_the_original_positional_order() -> None:
    params = inspect.signature(diss_row).parameters
    assert list(params) == [
        "series",
        "phase",
        "desc",
        "slug",
        "title",
        "bpm",
        "seed",
        "take",
        "lyrics",
        "tag_parts",
        "tags",
    ]
    assert params["tag_parts"].kind is inspect.Parameter.VAR_POSITIONAL
    assert params["tags"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["tags"].default is None


def test_take_describer_protocol_accepts_a_plain_callable() -> None:
    describer: TakeDescriber = _describe
    assert describer("x") == "desc: x"


def test_nill_tags_locks_the_dry_booth_voice() -> None:
    assert (
        nill_tags("jazz hop", "brushed drums", bpm=90)
        == "jazz hop, brushed drums, male rap vocals, dry booth, no autotune, 90 bpm"
    )


def test_nill_tags_without_parts_keeps_voice_and_bpm() -> None:
    assert nill_tags(bpm=140) == f"{NILL_VOICE}, 140 bpm"


def test_nill_output_prefix_clamps_tracks_below_one() -> None:
    assert nill_output_prefix("lab coat lecture", 0) == "01 - Lab Coat Lecture"
    assert nill_output_prefix("lab coat lecture", -4) == "01 - Lab Coat Lecture"
    assert nill_output_prefix("peer review", 12) == "12 - Peer Review"


def test_shared_constants_match_the_catalog_values() -> None:
    assert diss_rows.DISS_DURATION_S == DISS_DURATION_S == 180.0
    assert diss_rows.NILL_VOICE == NILL_VOICE
    assert diss_rows.DissExampleRow == dict[str, Any]


def test_diss_examples_reexports_the_shared_objects() -> None:
    examples = _module("diss_examples")
    assert examples.nill_tags is nill_tags
    assert examples.nill_output_prefix is nill_output_prefix
    assert examples.DISS_DURATION_S is diss_rows.DISS_DURATION_S
    assert examples._desc is _desc
    assert examples._progress_desc is _progress_desc


@pytest.mark.parametrize("case", SERIES_CASES)
def test_series_binding_is_a_partial_over_the_factory(case: SeriesCase) -> None:
    series, module_name, _tuple_name, _phase_const, phase, desc_name = case
    bound = getattr(_module(module_name), "_ex")
    assert isinstance(bound, partial)
    assert bound.func is diss_row
    assert bound.args == (series, phase, getattr(_module(module_name), desc_name))
    assert bound.keywords == {}


@pytest.mark.parametrize("case", SERIES_CASES)
def test_series_tuple_shape_stays_frozen(case: SeriesCase) -> None:
    series, module_name, tuple_name, phase_const, phase, _desc_name = case
    assert getattr(_module(module_name), phase_const) == phase
    rows = _series_rows(module_name, tuple_name)
    assert len(rows) == 15
    assert all(tuple(row) == ROW_KEYS for row in rows)
    assert all(row["series"] == series for row in rows)
    assert all(row["phase"] == phase for row in rows)
    assert all(row["duration"] == DISS_DURATION_S for row in rows)
    assert all(row["prefix"] == nill_output_prefix(row["title"], phase) for row in rows)


@pytest.mark.parametrize("case", SERIES_CASES)
def test_series_rows_rebuild_identically_through_the_factory(case: SeriesCase) -> None:
    _series, module_name, tuple_name, _phase_const, _phase, desc_name = case
    describer: TakeDescriber = getattr(_module(module_name), desc_name)
    rows = _series_rows(module_name, tuple_name)
    rebuilt = [
        diss_row(
            row["series"],
            row["phase"],
            describer,
            row["stem"]
            .removeprefix("music-rap-nill-bye-")
            .removesuffix("-lab-example"),
            row["title"],
            row["bpm"],
            row["seed"],
            _take_from(row["description"], describer),
            row["lyrics"],
            tags=row["tags"],
        )
        for row in rows
    ]
    assert rebuilt == list(rows)


@pytest.mark.parametrize("case", SERIES_CASES)
def test_series_rows_are_the_rows_the_catalog_shipped(case: SeriesCase) -> None:
    _series, module_name, tuple_name, _phase_const, _phase, _desc_name = case
    shipped = {row["slug"]: row for row in DISS_EXAMPLES}
    for row in _series_rows(module_name, tuple_name):
        slug = row["stem"].removeprefix("music-rap-nill-bye-").removesuffix(
            "-lab-example"
        )
        final = shipped[slug]
        assert final["title"] == row["title"]
        assert final["tags"] == row["tags"]
        assert final["bpm"] == row["bpm"]
        assert final["seed"] == row["seed"]
        assert final["phase"] == row["phase"]
        assert final["description"] == row["description"]


def test_catalog_keeps_one_hundred_thirty_five_rows() -> None:
    assert DISS_DURATION_S == 180.0
    assert len(DISS_EXAMPLES) == 135
    assert all(row["tracktotal"] == 15 for row in DISS_EXAMPLES)
    assert all(row["duration"] > 0 for row in DISS_EXAMPLES)


def test_diss_rows_import_does_not_start_the_catalog_build() -> None:
    code = (
        "import sys; import ez_music.diss_rows;"
        " print('ez_music.diss_examples' in sys.modules)"
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(CUSTOM)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert done.stdout.strip() == "False"
