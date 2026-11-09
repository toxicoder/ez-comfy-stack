"""Tests for the lab-graph auditor's note-reference gate.

A note that tells the operator to load a graph which does not ship is a dead
end in the App: they follow the instruction, find nothing, and the graph looks
broken. The auditor resolves every bolded lane path in lab_note /
lab_description against the shipped ids, so these tests pin both directions.
"""

from __future__ import annotations

from typing import Any

from _audit_lab_graphs import (
    note_reference_violations,
    shipped_graph_ids,
)
from _lab_paths import LAB_ROOT, cached_lab_graph_rows, lab_graph_paths


def _graph(note: str) -> dict[str, Any]:
    return {"extra": {"lab_note": note, "lab_description": ""}}


def _shipped() -> frozenset[str]:
    return frozenset({"photos/still-daily", "film/go-see/act-01"})


def test_a_ref_to_a_shipped_graph_passes() -> None:
    assert note_reference_violations(_graph("Next: **photos/still-daily**."), _shipped()) == []


def test_a_ref_to_a_missing_graph_is_reported() -> None:
    problems = note_reference_violations(_graph("Next: **film/go-see/feature**."), _shipped())
    assert problems == ["note names graph 'film/go-see/feature' that does not ship"]


def test_a_json_suffix_still_resolves() -> None:
    assert note_reference_violations(_graph("Next: **photos/still-daily.json**."), _shipped()) == []


def test_bolded_prose_without_a_slash_is_never_a_ref() -> None:
    note = "Occupancy **audio** only; Enhance **off**; queue **on its own**."
    assert note_reference_violations(_graph(note), _shipped()) == []


def test_a_bolded_path_outside_the_lanes_is_not_a_ref() -> None:
    assert note_reference_violations(_graph("See **docs/studio-apps.mdx**."), _shipped()) == []


def test_the_description_is_scanned_too() -> None:
    graph: dict[str, Any] = {
        "extra": {"lab_note": "", "lab_description": "Pair with **video/silent/nope**."}
    }
    assert note_reference_violations(graph, _shipped()) == [
        "note names graph 'video/silent/nope' that does not ship"
    ]


def test_shipped_graph_ids_are_lane_relative() -> None:
    files = [LAB_ROOT / "photos" / "still-daily.json", LAB_ROOT / "film" / "go-see" / "00-plate.json"]
    assert shipped_graph_ids(files, LAB_ROOT) >= {
        "photos/still-daily",
        "film/go-see/00-plate",
    }


def test_every_shipped_note_reference_resolves() -> None:
    shipped = shipped_graph_ids(lab_graph_paths(), LAB_ROOT)
    for rel, _path, data in cached_lab_graph_rows():
        for problem in note_reference_violations(data, shipped):
            raise AssertionError(f"{rel}: {problem}")
