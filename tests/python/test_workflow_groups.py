"""Lab workflow groups leave room for the ComfyUI title bar."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_layout import (  # noqa: E402
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    LAB_NODE_Y0,
    LAB_X0,
    ensure_group_title_inset,
    group,
    group_overlap_hits,
    node_overlap_hits,
    node_pos,
    operator_note,
    title_inset_hits,
)
from _lab_paths import lab_graph_paths, load_lab_graph  # noqa: E402


def test_lab_group_y0_clears_default_node_row() -> None:
    assert LAB_NODE_Y0 - LAB_GROUP_Y0 == GROUP_TITLE_INSET
    assert GROUP_TITLE_INSET >= 56


def test_ensure_group_title_inset_shifts_box_up_without_moving_nodes() -> None:
    graph = {
        "nodes": [
            {
                "id": 1,
                "type": "UNETLoader",
                "pos": [40, 80],
                "size": [360, 82],
            }
        ],
        "groups": [group(1, "MODEL", 20, 40, 430, 430, "#3f789e")],
    }
    ensure_group_title_inset(graph)
    box = graph["groups"][0]["bounding"]
    assert box[1] == LAB_GROUP_Y0
    assert box[3] == 430
    assert graph["nodes"][0]["pos"] == [40, 80]
    assert title_inset_hits(graph) == []
    assert group_overlap_hits(graph) == []


def test_ensure_group_title_inset_does_not_overlap_stacked_groups() -> None:
    graph = {
        "nodes": [
            {"id": 1, "type": "UNETLoader", "pos": [40, 80], "size": [360, 82]},
            {"id": 2, "type": "LoadImage", "pos": [40, 520], "size": [320, 314]},
        ],
        "groups": [
            group(1, "Load models", 20, 40, 400, 430, "#3f789e"),
            group(2, "LoadImage", 20, 480, 400, 380, "#3f789e"),
        ],
    }
    ensure_group_title_inset(graph)
    assert title_inset_hits(graph) == []
    assert group_overlap_hits(graph) == []
    assert graph["nodes"][0]["pos"][1] == 80
    assert graph["nodes"][1]["pos"][1] == 520


def _graphs() -> list[Path]:
    return lab_graph_paths()


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_group_title_bar_clears_member_nodes(path: Path) -> None:
    graph = load_lab_graph(path)
    hits = title_inset_hits(graph)
    assert hits == [], f"{path.name}: {hits} (need {GROUP_TITLE_INSET}px)"


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_groups_do_not_overlap(path: Path) -> None:
    graph = load_lab_graph(path)
    hits = group_overlap_hits(graph)
    assert hits == [], f"{path.name}: {hits}"


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_nodes_do_not_overlap(path: Path) -> None:
    graph = load_lab_graph(path)
    hits = node_overlap_hits(graph)
    assert hits == [], f"{path.name}: {hits[:8]}"
    for sub in (graph.get("definitions") or {}).get("subgraphs") or []:
        sub_hits = node_overlap_hits(sub)
        assert sub_hits == [], f"{path.name} subgraph: {sub_hits[:8]}"


_TOPLEFT_EPS = 0.5

_NAMED_TITLE_NEEDLES: dict[str, tuple[str, ...]] = {
    "films/go-see.json": ("1. Identity", "Beat", "Publish"),
    "motion/av/clip-chain.json": ("Beat", "LTX models"),
    "stills/dream-house.json": ("SHOT", "HOUSE IDENTITY"),
    "inspire/cinema-rack.json": ("RACK", "KLEIN", "WAN", "LTX"),
}


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_operator_note_is_top_left(path: Path) -> None:
    graph = load_lab_graph(path)
    note = operator_note(graph)
    assert note is not None, path.name
    nx, ny = node_pos(note)
    assert nx == LAB_X0, path.name
    assert ny == LAB_NODE_Y0, path.name
    for node in graph.get("nodes") or []:
        x, y = node_pos(node)
        assert y + _TOPLEFT_EPS >= ny, (path.name, node.get("id"), node.get("type"), y, ny)
        assert x + _TOPLEFT_EPS >= nx, (path.name, node.get("id"), node.get("type"), x, nx)


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_header_groups_cover_note_quality_check(path: Path) -> None:
    graph = load_lab_graph(path)
    titles = {str(grp.get("title") or "") for grp in graph.get("groups") or []}
    types = {str(n.get("type") or "") for n in graph.get("nodes") or []}
    if any(t in {"Note", "MarkdownNote"} for t in types):
        assert "NOTE" in titles, path.name
    if "EZQuality" in types or "EZModelCheck" in types:
        assert "QUALITY" in titles, path.name
    rel = str(path.relative_to(WF / "_lab"))
    needles = _NAMED_TITLE_NEEDLES.get(rel)
    if needles:
        blob = " ".join(titles)
        for needle in needles:
            assert needle in blob, (rel, needle, sorted(titles))
