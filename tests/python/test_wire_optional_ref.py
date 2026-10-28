"""Optional reference stills wiring: node literals and the App Mode toggle row.

Hermetic: stdlib. Builds synthetic graphs and never touches ComfyUI.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _wire_optional_ref import (  # noqa: E402
    CANVAS_SIZE,
    CANVAS_WIDGETS,
    OPT_SIZE,
    OPT_WIDGETS,
    REF_TOGGLE,
    REF_TOGGLE_LABEL,
    refresh_optional_ref_widgets,
    wire_optional_ref,
)


def _tiny_klein_graph() -> dict[str, Any]:
    """Build the smallest graph wire_optional_ref recognises.

    Returns:
        A serialized graph with a latent, a VAE loader, and a KSampler.
    """
    return {
        "last_node_id": 3,
        "last_link_id": 1,
        "links": [[1, 1, 0, 3, 3, "LATENT"]],
        "nodes": [
            {"id": 1, "type": "EmptyFlux2LatentImage", "order": 0, "pos": [0, 0]},
            {
                "id": 2,
                "type": "VAELoader",
                "order": 1,
                "pos": [0, 0],
                "outputs": [{"name": "VAE", "type": "VAE", "links": []}],
            },
            {
                "id": 3,
                "type": "KSampler",
                "order": 2,
                "pos": [0, 0],
                "inputs": [{"name": "latent_image", "type": "LATENT", "link": 1}],
            },
        ],
        "extra": {},
    }


def _legacy_graph() -> dict[str, Any]:
    """Build a graph as committed before the reference card shipped.

    Returns:
        A serialized graph with single-picker ref nodes and one stamped row.
    """
    return {
        "last_node_id": 6,
        "last_link_id": 9,
        "links": [],
        "nodes": [
            {
                "id": 5,
                "type": "EZOptionalImage",
                "size": [360.0, 120.0],
                "widgets_values": [""],
            },
            {
                "id": 6,
                "type": "EZKleinRefCanvas",
                "size": [360.0, 140.0],
                "widgets_values": [False],
            },
        ],
        "extra": {
            "linearData": {
                "inputs": [
                    [1, "prompt", {"label": "Prompt"}],
                    [
                        5,
                        "filename",
                        {"label": "Example / reference (optional)", "description": "keep me"},
                    ],
                ]
            }
        },
    }


def _rows(graph: dict[str, Any]) -> list[Any]:
    """Panel rows for a graph.

    Args:
        graph: Serialized graph.

    Returns:
        The extra.linearData.inputs list.
    """
    return graph["extra"]["linearData"]["inputs"]


def test_new_nodes_carry_the_full_widget_literals() -> None:
    """A freshly wired graph stores every optional widget positionally."""
    graph = wire_optional_ref(_tiny_klein_graph())
    opt = next(n for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    canvas = next(n for n in graph["nodes"] if n["type"] == "EZKleinRefCanvas")
    assert list(opt["widgets_values"]) == OPT_WIDGETS
    assert list(opt["size"]) == OPT_SIZE
    assert list(canvas["widgets_values"]) == CANVAS_WIDGETS
    assert list(canvas["size"]) == CANVAS_SIZE


def test_new_graph_stamps_the_toggle_next_to_the_picker() -> None:
    """The App Mode panel shows the mute directly after the reference picker."""
    graph = wire_optional_ref(_tiny_klein_graph())
    opt_id = next(n["id"] for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    names = [(row[0], row[1]) for row in _rows(graph)]
    assert (opt_id, "filename") in names
    assert (opt_id, REF_TOGGLE) in names
    assert names.index((opt_id, REF_TOGGLE)) == names.index((opt_id, "filename")) + 1
    toggle = next(row for row in _rows(graph) if row[1] == REF_TOGGLE)
    assert toggle[2]["label"] == REF_TOGGLE_LABEL
    assert toggle[2]["description"]


def test_refresh_upgrades_a_legacy_graph() -> None:
    """A committed single-picker graph gains widgets, heights, and the toggle."""
    graph = _legacy_graph()
    assert refresh_optional_ref_widgets(graph) is True
    opt = next(n for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    canvas = next(n for n in graph["nodes"] if n["type"] == "EZKleinRefCanvas")
    assert list(opt["widgets_values"]) == OPT_WIDGETS
    assert list(opt["size"]) == OPT_SIZE
    assert list(canvas["widgets_values"]) == CANVAS_WIDGETS
    assert list(canvas["size"]) == CANVAS_SIZE
    names = [(row[0], row[1]) for row in _rows(graph)]
    assert names.index((5, REF_TOGGLE)) == names.index((5, "filename")) + 1


def test_refresh_keeps_the_existing_picker_wording() -> None:
    """Refresh adds rows and never rewrites copy an operator already tuned."""
    graph = _legacy_graph()
    before = next(row for row in _rows(graph) if row[1] == "filename")
    saved = copy.deepcopy(before)
    refresh_optional_ref_widgets(graph)
    after = next(row for row in _rows(graph) if row[1] == "filename")
    assert after == saved


def test_refresh_is_idempotent() -> None:
    """A second pass reports no work so a rebuild cannot churn the tree."""
    graph = _legacy_graph()
    assert refresh_optional_ref_widgets(graph) is True
    snapshot = copy.deepcopy(graph)
    assert refresh_optional_ref_widgets(graph) is False
    assert graph == snapshot


def test_refresh_on_a_current_graph_reports_no_change() -> None:
    """Wiring then refreshing is a no-op, so builders stay stable."""
    graph = wire_optional_ref(_tiny_klein_graph())
    assert refresh_optional_ref_widgets(graph) is False


def test_refresh_ignores_graphs_without_reference_nodes() -> None:
    """Graphs that never had the node stay byte-identical."""
    graph = {"nodes": [{"id": 1, "type": "KSampler"}], "extra": {}}
    snapshot = copy.deepcopy(graph)
    assert refresh_optional_ref_widgets(graph) is False
    assert graph == snapshot


def test_widget_literals_match_the_node_definition_order() -> None:
    """Positional literals must track INPUT_TYPES or saved values land wrong."""
    sys.path.insert(0, str(ROOT / "custom_nodes"))
    from ez_image.refs import EZKleinRefCanvas, EZOptionalImage  # noqa: E402

    optional = EZOptionalImage.INPUT_TYPES()
    opt_order = list(optional["required"]) + list(optional["optional"])
    opt_widgets = [k for k in opt_order if k != "image"]
    assert opt_widgets == ["filename", REF_TOGGLE, "filename_2", "filename_3"]
    assert len(OPT_WIDGETS) == len(opt_widgets)

    canvas = EZKleinRefCanvas.INPUT_TYPES()
    canvas_order = list(canvas["required"]) + list(canvas["optional"])
    canvas_widgets = [k for k in canvas_order if k not in ("latent", "vae", "image")]
    assert canvas_widgets == ["has_image", "max_refs"]
    assert len(CANVAS_WIDGETS) == len(canvas_widgets)


def test_refresh_rejects_a_mismatched_toggle_name() -> None:
    """Guard the seam: the panel row name has to equal the widget name."""
    graph = _legacy_graph()
    refresh_optional_ref_widgets(graph)
    opt = next(n for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    assert opt["widgets_values"][1] is True
    assert any(row[1] == REF_TOGGLE for row in _rows(graph))


@pytest.mark.parametrize("widget", ["", "still.png"])
def test_empty_and_filled_first_slot_both_survive_refresh(widget: str) -> None:
    """A preset first picker is not reset by the upgrade pass.

    Args:
        widget: Filename to leave in slot one.
    """
    graph = _legacy_graph()
    opt = next(n for n in graph["nodes"] if n["type"] == "EZOptionalImage")
    opt["widgets_values"] = [widget]
    refresh_optional_ref_widgets(graph)
    assert opt["widgets_values"][0] == widget
