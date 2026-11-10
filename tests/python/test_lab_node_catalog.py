"""Gate: every shipped lab graph speaks classes the node encyclopedia knows.

A graph the pinned ComfyUI image cannot resolve is a Queue-time failure, and a
widget list one entry too long silently shifts every value after it - a wrong
weight, a wrong step count, a wrong denoise. Both are provable offline against
``docs/workflow_nodes_*.py``, which is what this gate does.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from _lab_node_catalog import documented_widget_widths, graph_findings
from _lab_paths import cached_lab_graph_rows


def _node(node_id: int, ntype: str, *values: Any) -> dict[str, Any]:
    """Build one node dict the way a lab graph stores it.

    Args:
        node_id: LiteGraph node id.
        ntype: ``class_type`` to claim.
        *values: Widget values to store.

    Returns:
        A node dict shaped for :func:`graph_findings`.
    """
    return {"id": node_id, "type": ntype, "widgets_values": list(values)}


def _graph(*nodes: dict[str, Any]) -> dict[str, Any]:
    """Wrap nodes in a graph dict.

    Args:
        *nodes: Node dicts to place in the graph.

    Returns:
        A graph dict shaped for :func:`graph_findings`.
    """
    return {"nodes": list(nodes)}


WIDTHS: dict[str, int] = documented_widget_widths()


def test_the_encyclopedia_is_readable_and_wide() -> None:
    """A broken docs import would make every check below pass vacuously."""
    assert len(WIDTHS) > 80
    assert WIDTHS["KSampler"] == 7
    assert "Trellis2TextureStage" in WIDTHS
    assert "EZImageMode" in WIDTHS


def test_a_class_the_encyclopedia_never_named_is_a_finding() -> None:
    findings = graph_findings(
        _graph(_node(1, "VaeDecodeShapeTrellis2", "anything")),
        {"UNETLoader": 2},
    )
    assert findings == ["node 1 (VaeDecodeShapeTrellis2): no encyclopedia entry"]


def test_a_node_without_a_type_is_a_finding() -> None:
    findings = graph_findings(_graph({"id": 7, "widgets_values": []}), {"KSampler": 7})
    assert findings == ["node 7 carries no type"]


def test_widget_values_past_the_documented_width_are_a_finding() -> None:
    """One extra value shifts every widget after it, silently."""
    ok = graph_findings(_graph(_node(1, "UNETLoader", "a.safetensors", "default")), {"UNETLoader": 2})
    assert ok == []
    too_long = graph_findings(
        _graph(_node(1, "UNETLoader", "a.safetensors", "default", "extra")),
        {"UNETLoader": 2},
    )
    assert too_long == ["node 1 (UNETLoader): 3 widget values for 2 documented widgets"]


def test_a_loader_with_an_unauthored_weight_is_a_finding() -> None:
    """An empty weight picker queues a file-not-found after the GPU spins up."""
    for blank in ("", "   ", None, 12):
        findings = graph_findings(_graph(_node(3, "VAELoader", blank)), {"VAELoader": 1})
        assert findings == ["node 3 (VAELoader): weight widget is not authored"], blank
    assert graph_findings(_graph(_node(3, "VAELoader", "vae.safetensors")), {"VAELoader": 1}) == []


def test_a_non_loader_keeps_its_empty_widgets() -> None:
    """Blank prompt and note text are authored values, not missing weights."""
    assert graph_findings(_graph(_node(4, "Note", "")), {"Note": 1}) == []


def test_a_variant_layout_raises_the_width_ceiling() -> None:
    """MeshToFile3D and VHS_VideoCombine document a second, wider layout."""
    assert WIDTHS["MeshToFile3D"] == 1
    assert graph_findings(
        _graph(_node(9, "MeshToFile3D", "assets/objects/_lab-blockout/blockout")),
        WIDTHS,
    ) == []
    assert WIDTHS["VHS_VideoCombine"] == 10


@pytest.mark.parametrize("lab_rel,path,graph", cached_lab_graph_rows())
def test_shipped_graph_matches_the_encyclopedia(
    lab_rel: str,
    path: Path,
    graph: dict[str, Any],
) -> None:
    """No shipped App queues a class the docs never documented."""
    del path
    findings = graph_findings(graph, WIDTHS)
    assert not findings, f"{lab_rel}: " + "; ".join(findings)
