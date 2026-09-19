"""Lab graphs and subgraph blueprints are Nodes 2.0 (Vue-corrected)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from _lab_paths import (
    WORKFLOW_RENDERER_VERSION,
    apply_lab_identity,
    lab_graph_paths,
    load_lab_graph,
    stamp_nodes2,
)

ROOT = Path(__file__).resolve().parents[2]
BLOCKS = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs"


def _graphs() -> list[Path]:
    return lab_graph_paths()


def _blueprints() -> list[Path]:
    return sorted(BLOCKS.glob("*.json"))


def test_workflow_renderer_version_is_vue_corrected() -> None:
    assert WORKFLOW_RENDERER_VERSION == "Vue-corrected"


def test_stamp_nodes2_sets_root_and_nested_subgraph_extra() -> None:
    graph: dict[str, Any] = {
        "extra": {"lab_rel": "stills/still-draft"},
        "definitions": {"subgraphs": [{"id": "sg", "extra": {"lab_occupancy": "klein"}}]},
    }
    stamp_nodes2(graph)
    assert graph["extra"]["workflowRendererVersion"] == "Vue-corrected"
    assert graph["extra"]["lab_rel"] == "stills/still-draft"
    assert graph["definitions"]["subgraphs"][0]["extra"]["workflowRendererVersion"] == (
        "Vue-corrected"
    )
    assert graph["definitions"]["subgraphs"][0]["extra"]["lab_occupancy"] == "klein"


def test_apply_lab_identity_stamps_nodes2() -> None:
    graph: dict[str, Any] = {"nodes": []}
    apply_lab_identity(graph, "stills/still-draft")
    assert graph["id"] == "still-draft"
    assert graph["extra"]["lab_rel"] == "stills/still-draft"
    assert graph["extra"]["workflowRendererVersion"] == "Vue-corrected"


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: str(p.relative_to(ROOT)))
def test_lab_graph_is_nodes2(path: Path) -> None:
    graph = load_lab_graph(path)
    extra = graph.get("extra") or {}
    assert graph.get("version") == 0.4, path
    assert extra.get("workflowRendererVersion") == "Vue-corrected", path
    for sub in ((graph.get("definitions") or {}).get("subgraphs") or []):
        sub_extra = sub.get("extra") or {}
        assert sub_extra.get("workflowRendererVersion") == "Vue-corrected", path


@pytest.mark.parametrize("path", _blueprints(), ids=lambda p: p.name)
def test_studio_block_is_nodes2(path: Path) -> None:
    graph = json.loads(path.read_text(encoding="utf-8"))
    extra = graph.get("extra") or {}
    assert graph.get("version") == 0.4, path.name
    assert extra.get("workflowRendererVersion") == "Vue-corrected", path.name
    defs = (graph.get("definitions") or {}).get("subgraphs") or []
    assert defs, path.name
    for sub in defs:
        sub_extra = sub.get("extra") or {}
        assert sub_extra.get("workflowRendererVersion") == "Vue-corrected", path.name
