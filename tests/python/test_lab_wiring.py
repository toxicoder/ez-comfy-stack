"""Gate: every shipped lab graph wires its nodes consistently.

ComfyUI resolves a graph at Queue time: a link row that disagrees with the slot
bookkeeping, a type mismatch between a socket pair, a required sampler input
left unwired, or an App with no terminal node all fail on the GPU box after the
operator pressed Run. Every one of those is provable offline against the JSON,
which is what this gate does. The companion ``_lab_node_catalog`` gate covers
class names and widget widths; this one covers the wiring between nodes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from _lab_paths import cached_lab_graph_rows
from _lab_wiring import custom_output_node_types
from _lab_wiring import wiring_findings


def _slot(**kwargs: Any) -> dict[str, Any]:
    """Build one slot dict with sane defaults.

    Args:
        **kwargs: Overrides merged into the slot dict.

    Returns:
        A slot dict shaped for :func:`wiring_findings`.
    """
    slot: dict[str, Any] = {"name": "out", "type": "LATENT", "links": []}
    slot.update(kwargs)
    return slot


def _in(**kwargs: Any) -> dict[str, Any]:
    """Build one input slot dict with sane defaults.

    Args:
        **kwargs: Overrides merged into the slot dict.

    Returns:
        An input slot dict shaped for :func:`wiring_findings`.
    """
    slot: dict[str, Any] = {"name": "in", "type": "LATENT", "link": None}
    slot.update(kwargs)
    return slot


def _node(
    node_id: int,
    ntype: str,
    *,
    inputs: list[dict[str, Any]] | None = None,
    outputs: list[dict[str, Any]] | None = None,
    widgets: list[Any] | None = None,
) -> dict[str, Any]:
    """Build one node dict the way a lab graph stores it.

    Args:
        node_id: LiteGraph node id.
        ntype: ``class_type`` to claim.
        inputs: Input slot dicts.
        outputs: Output slot dicts.
        widgets: ``widgets_values`` to store.

    Returns:
        A node dict shaped for :func:`wiring_findings`.
    """
    return {
        "id": node_id,
        "type": ntype,
        "inputs": inputs if inputs is not None else [],
        "outputs": outputs if outputs is not None else [],
        "widgets_values": widgets if widgets is not None else [],
    }


def _link(link_id: int, origin: int, oslot: int, target: int, tslot: int, ltype: str) -> list[Any]:
    """Build one link row in ComfyUI order.

    Args:
        link_id: Link id.
        origin: Origin node id.
        oslot: Origin output slot index.
        target: Target node id.
        tslot: Target input slot index.
        ltype: Link type string.

    Returns:
        A link row shaped for :func:`wiring_findings`.
    """
    return [link_id, origin, oslot, target, tslot, ltype]


def _chain() -> dict[str, Any]:
    """A clean KSampler -> VAEDecode -> SaveImage graph.

    Returns:
        A graph dict shaped for :func:`wiring_findings`, with every required
        input wired from a Note stand-in that owns the matching outputs.
    """
    return {
        "nodes": [
            _node(
                1,
                "KSampler",
                inputs=[
                    _in(name="model", type="MODEL", link=11),
                    _in(name="positive", type="CONDITIONING", link=12),
                    _in(name="negative", type="CONDITIONING", link=13),
                    _in(name="latent_image", type="LATENT", link=14),
                ],
                outputs=[_slot(name="LATENT", links=[1])],
                widgets=[42, "fixed", 4, 1.0, "euler", "simple", 1.0],
            ),
            _node(
                2,
                "SaveImage",
                inputs=[_in(name="images", type="IMAGE", link=3)],
            ),
            _node(
                3,
                "VAEDecode",
                inputs=[
                    _in(name="samples", type="LATENT", link=1),
                    _in(name="vae", type="VAE", link=2),
                ],
                outputs=[_slot(name="IMAGE", type="IMAGE", links=[3])],
            ),
            _node(
                4,
                "VAELoader",
                outputs=[_slot(name="VAE", type="VAE", links=[2])],
                widgets=["vae.safetensors"],
            ),
            _node(
                9,
                "Note",
                outputs=[
                    _slot(name="MODEL", type="MODEL", links=[11]),
                    _slot(name="pos", type="CONDITIONING", links=[12]),
                    _slot(name="neg", type="CONDITIONING", links=[13]),
                    _slot(name="lat", type="LATENT", links=[14]),
                ],
            ),
        ],
        "links": [
            _link(1, 1, 0, 3, 0, "LATENT"),
            _link(2, 4, 0, 3, 1, "VAE"),
            _link(3, 3, 0, 2, 0, "IMAGE"),
            _link(11, 9, 0, 1, 0, "MODEL"),
            _link(12, 9, 1, 1, 1, "CONDITIONING"),
            _link(13, 9, 2, 1, 2, "CONDITIONING"),
            _link(14, 9, 3, 1, 3, "LATENT"),
        ],
    }


# --- happy path -------------------------------------------------------------


def test_a_consistent_graph_has_no_findings() -> None:
    assert wiring_findings(_chain()) == []


# --- link table integrity ---------------------------------------------------


def test_a_malformed_link_row_is_a_finding() -> None:
    graph = _chain()
    graph["links"][0] = [1, 1, 0, 3, 0]
    assert wiring_findings(graph) == ["link 1: row is not a 6-field link"]


def test_a_duplicate_link_id_is_a_finding() -> None:
    graph = _chain()
    graph["links"].append(_link(1, 1, 0, 3, 0, "LATENT"))
    assert wiring_findings(graph) == ["link 1: duplicate link id"]


def test_a_link_naming_a_missing_node_is_a_finding() -> None:
    graph = _chain()
    graph["links"][0] = _link(1, 1, 0, 99, 0, "LATENT")
    findings = wiring_findings(graph)
    assert "link 1: target node 99 does not exist" in findings


def test_a_self_link_is_a_finding() -> None:
    graph = {
        "nodes": [
            _node(
                1,
                "SaveImage",
                inputs=[_in(name="images", type="IMAGE", link=1)],
                outputs=[_slot(name="IMAGE", type="IMAGE", links=[1])],
            )
        ],
        "links": [_link(1, 1, 0, 1, 0, "IMAGE")],
    }
    assert wiring_findings(graph) == ["link 1: node 1 links to itself"]


def test_a_slot_index_past_the_node_slots_is_a_finding() -> None:
    graph = _chain()
    graph["links"][0] = _link(1, 1, 3, 3, 0, "LATENT")
    findings = wiring_findings(graph)
    assert "link 1: origin slot 3 out of range on node 1 (1 outputs)" in findings


def test_a_link_missing_from_the_origin_slot_bookkeeping_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][0]["outputs"][0]["links"] = []
    findings = wiring_findings(graph)
    assert "link 1: absent from node 1 output slot 0 links" in findings


def test_a_link_missing_from_the_target_slot_bookkeeping_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][2]["inputs"][0]["link"] = None
    findings = wiring_findings(graph)
    assert "link 1: absent from node 3 input slot 0" in findings


def test_a_dangling_input_reference_is_a_finding() -> None:
    graph = _chain()
    graph["links"] = [row for row in graph["links"] if row[0] != 3]
    findings = wiring_findings(graph)
    assert "node 2 input slot 0 claims link 3 that is not in the link table" in findings


def test_a_dangling_output_reference_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][0]["outputs"][0]["links"] = [1, 77]
    findings = wiring_findings(graph)
    assert "node 1 output slot 0 claims link 77 that is not in the link table" in findings


# --- type agreement ---------------------------------------------------------


def test_a_link_type_mismatch_against_a_socket_is_a_finding() -> None:
    graph = _chain()
    graph["links"][2] = _link(3, 3, 0, 2, 0, "MASK")
    findings = wiring_findings(graph)
    assert "link 3: type MASK does not match node 3 output slot 0 type IMAGE" in findings
    assert "link 3: type MASK does not match node 2 input slot 0 type IMAGE" in findings


def test_a_typeless_slot_does_not_trip_the_type_check() -> None:
    graph = _chain()
    del graph["nodes"][2]["inputs"][0]["type"]
    del graph["nodes"][0]["outputs"][0]["type"]
    assert wiring_findings(graph) == []


# --- required inputs --------------------------------------------------------


def test_an_unwired_required_sampler_input_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][0]["inputs"][2]["link"] = None
    graph["links"] = [row for row in graph["links"] if row[0] != 13]
    graph["nodes"][4]["outputs"][2]["links"] = []
    findings = wiring_findings(graph)
    assert "node 1 (KSampler): required input 'negative' is unwired" in findings


def test_a_missing_required_input_slot_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][0]["inputs"].pop(1)
    graph["nodes"][0]["inputs"][1]["link"] = None
    graph["nodes"][0]["inputs"][2]["link"] = None
    graph["links"] = [row for row in graph["links"] if row[0] not in (12, 13, 14)]
    graph["nodes"][4]["outputs"][1]["links"] = []
    graph["nodes"][4]["outputs"][2]["links"] = []
    graph["nodes"][4]["outputs"][3]["links"] = []
    findings = wiring_findings(graph)
    assert "node 1 (KSampler): required input 'positive' has no slot" in findings


def test_a_second_slot_with_a_link_satisfies_the_requirement() -> None:
    """Repeater sockets stack: any linked slot with the name counts."""
    graph = _chain()
    graph["nodes"][0]["inputs"].append(_in(name="model", type="MODEL", link=None))
    assert wiring_findings(graph) == []


# --- terminals --------------------------------------------------------------


def test_a_graph_with_no_output_node_is_a_finding() -> None:
    graph = {
        "nodes": [
            _node(
                1,
                "EmptyFlux2LatentImage",
                outputs=[_slot(name="LATENT")],
                widgets=[1024, 1024, 1],
            )
        ],
        "links": [],
    }
    assert wiring_findings(graph) == ["graph has no terminal output node"]


# --- loader authoring -------------------------------------------------------


def test_an_unauthored_load_image_widget_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"].append(_node(10, "LoadImage", widgets=[""]))
    findings = wiring_findings(graph)
    assert "node 10 (LoadImage): image widget is not authored" in findings


def test_a_linked_load_image_skips_the_widget_authoring_check() -> None:
    graph = _chain()
    graph["nodes"].append(
        _node(
            10,
            "LoadImage",
            inputs=[{"name": "image", "type": "STRING", "link": 40, "widget": {"name": "image"}}],
            outputs=[_slot(name="IMAGE", type="IMAGE", links=[])],
            widgets=[""],
        )
    )
    graph["links"].append(_link(40, 9, 0, 10, 0, "STRING"))
    graph["nodes"][4]["outputs"][0]["links"] = [11, 40]
    findings = wiring_findings(graph)
    assert not [f for f in findings if "LoadImage" in f]


# --- widget sanity ----------------------------------------------------------


def test_an_out_of_range_sampler_widget_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"][0]["widgets_values"] = [42, "fixed", 0, 1.0, "euler", "simple", 1.5]
    findings = wiring_findings(graph)
    assert "node 1 (KSampler): steps must be >= 1, got 0" in findings
    assert "node 1 (KSampler): denoise must be in (0, 1], got 1.5" in findings


def test_a_linked_sampler_widget_skips_the_range_check() -> None:
    graph = _chain()
    graph["nodes"][0]["widgets_values"][2] = 0
    graph["nodes"][0]["inputs"].append(
        {"name": "steps", "type": "INT", "link": 41, "widget": {"name": "steps"}}
    )
    graph["nodes"].append(
        _node(10, "PrimitiveNode", outputs=[_slot(name="value", type="INT", links=[41])])
    )
    graph["links"].append(_link(41, 10, 0, 1, 4, "INT"))
    findings = wiring_findings(graph)
    assert not [f for f in findings if "steps" in f]


def test_an_off_grid_latent_size_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"].append(
        _node(10, "EmptyFlux2LatentImage", outputs=[_slot(name="LATENT")], widgets=[423, 512, 1])
    )
    findings = wiring_findings(graph)
    assert "node 10 (EmptyFlux2LatentImage): width 423 is off the 8 px latent grid" in findings


def test_an_empty_video_filename_prefix_is_a_finding() -> None:
    graph = _chain()
    graph["nodes"].append(
        _node(
            10,
            "VHS_VideoCombine",
            inputs=[_in(name="images", type="IMAGE", link=42)],
            widgets=[24, 0, "", "video/h264-mp4", "yuv420p", 19, True, False, False, True],
        )
    )
    graph["nodes"][2]["outputs"][0]["links"] = [3, 42]
    graph["links"].append(_link(42, 3, 0, 10, 0, "IMAGE"))
    findings = wiring_findings(graph)
    assert "node 10 (VHS_VideoCombine): filename_prefix is not authored" in findings


def test_dict_shaped_widgets_are_read_by_key() -> None:
    """Newer frontend saves store widgets_values as a name-keyed dict."""
    graph = _chain()
    video_node = _node(
        10,
        "VHS_VideoCombine",
        inputs=[_in(name="images", type="IMAGE", link=42)],
    )
    video_node["widgets_values"] = {"filename_prefix": "", "format": "video/h264-mp4"}
    graph["nodes"].append(video_node)
    graph["nodes"][2]["outputs"][0]["links"] = [3, 42]
    graph["links"].append(_link(42, 3, 0, 10, 0, "IMAGE"))
    findings = wiring_findings(graph)
    assert "node 10 (VHS_VideoCombine): filename_prefix is not authored" in findings


# --- terminal harvest -------------------------------------------------------


def test_custom_output_nodes_count_as_terminals(tmp_path: Path) -> None:
    source = tmp_path / "ez_demo" / "nodes.py"
    source.parent.mkdir()
    source.write_text(
        "class PlainNode:\n    def run(self):\n        return 1\n\n"
        "class ShowyNode:\n    OUTPUT_NODE = True\n\n"
        "class LaterNode:\n    OTHER = True\n",
        encoding="utf-8",
    )
    assert custom_output_node_types(tmp_path) == frozenset({"ShowyNode"})


# --- shipped graphs ---------------------------------------------------------


@pytest.mark.parametrize("lab_rel,path,graph", cached_lab_graph_rows())
def test_shipped_graph_wires_cleanly(
    lab_rel: str,
    path: Path,
    graph: dict[str, Any],
) -> None:
    """No shipped App queues a graph whose links disagree with their slots."""
    del path
    findings = wiring_findings(graph)
    assert not findings, f"{lab_rel}: " + "; ".join(findings)
