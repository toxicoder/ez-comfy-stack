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
    ensure_group_title_inset,
    group,
    group_overlap_hits,
    title_inset_hits,
)


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
    return sorted(WF.rglob("*-lab-example.json"))


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_group_title_bar_clears_member_nodes(path: Path) -> None:
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = title_inset_hits(graph)
    assert hits == [], f"{path.name}: {hits} (need {GROUP_TITLE_INSET}px)"


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(WF)))
def test_groups_do_not_overlap(path: Path) -> None:
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = group_overlap_hits(graph)
    assert hits == [], f"{path.name}: {hits}"
