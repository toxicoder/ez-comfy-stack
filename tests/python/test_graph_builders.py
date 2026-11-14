"""The catalog's builders are the source of the shipped graphs; keep them running.

Nothing else executes ``_build_*.py``: the gate scores the shipped JSON, so a
builder that raises on ``ImportError`` or a ``next()`` over a node an operator
deleted can sit broken for weeks and then hand the next regeneration a graph
missing a control. These cases run the builders that only read, so a rename in
``ez_quality.presets`` or a picker the catalog gate retires fails here instead.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from _lab_paths import LAB_ROOT, lab_json

BUILDERS = sorted(Path(__file__).parent.glob("_build_*.py"))
BUILDER_NAMES = [path.name.removesuffix(".py") for path in BUILDERS]


@pytest.mark.parametrize("module_name", BUILDER_NAMES)
def test_a_builder_module_imports(module_name: str) -> None:
    """A preset rename is a defect, not a regeneration surprise.

    Arguments:
        module_name: The ``_build_*.py`` stem under test.
    Outputs:
        Nothing; fails when the module raises on import.
    Returns:
        None.
    """
    assert importlib.import_module(module_name) is not None


def test_the_clay_guide_carries_its_own_picker() -> None:
    """The clay hero owns its upload box; it no longer borrows the seed's.

    ``build_klein_from_clay`` used to take the one ``LoadImage`` its seed graph
    still carried. That box fed no node in the seed and the catalog gate now
    refuses an upload nothing reads, so the builder has to create the picker it
    wires into ``VAEEncode``.
    """
    from _build_dcc_workflows import build_klein_from_clay

    seed = json.loads(lab_json("photos/still-hero.json").read_text(encoding="utf-8"))
    assert [node for node in seed["nodes"] if node.get("type") == "LoadImage"] == [], (
        "the seed carries a picker the gate refuses"
    )

    graph: dict[str, Any] = build_klein_from_clay()
    pickers = [node for node in graph["nodes"] if node.get("type") == "LoadImage"]
    assert len(pickers) == 1, [node.get("title") for node in pickers]
    picker = pickers[0]
    assert picker["mode"] == 0
    assert picker["title"] == "Clay first.png (guide pack)"
    assert picker["outputs"][0]["links"], "the picker feeds nothing"

    encoders = [node for node in graph["nodes"] if node.get("type") == "VAEEncode"]
    assert encoders, "the clay plate is never encoded"
    linked = {
        link[1] for link in graph["links"] if link[3] == encoders[0]["id"]
    }
    assert picker["id"] in linked, "the picker is not wired into VAEEncode"


def test_the_clay_guide_needs_no_node_the_gate_refuses() -> None:
    """Every id the builder hands out is unique, including the appended picker."""
    from _build_dcc_workflows import build_klein_from_clay

    graph = build_klein_from_clay()
    ids = [int(node["id"]) for node in graph["nodes"]]
    assert len(ids) == len(set(ids)), "two nodes share an id"
    assert max(ids) == int(graph["last_node_id"])
    assert LAB_ROOT.name == "_lab"
