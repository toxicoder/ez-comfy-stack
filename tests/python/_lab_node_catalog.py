"""Static contract between shipped lab graphs and the node encyclopedia.

A ``class_type`` is resolved only inside the pinned ComfyUI image, so a typo in a
shipped graph (`VaeDecodeShapeTrellis2` for `VaeDecodeShapeTrellis`) lands green
and dies at Queue with an unknown-node error - the worst possible time to find it
in a demo. ``docs/workflow_nodes_*.py`` already names every class the Apps use,
and ComfyUI maps ``widgets_values`` positionally, so that table can prove three
things offline: the class is real, the widget list is not longer than the node
owns, and a weight picker was actually authored.
"""

from __future__ import annotations

from typing import Any, Mapping

from _lab_families import LOADER_TYPES
from workflow_nodes_core import core_nodes
from workflow_nodes_enhance import enhance_nodes
from workflow_nodes_ltx import ltx_nodes
from workflow_nodes_packs import pack_nodes
from workflow_nodes_trellis import trellis_nodes
from workflow_nodes_vhs_ace import vhs_ace_nodes

# The encyclopedia split by pack; every lab class lives in exactly one of them.
_CATALOG_BUILDERS = (
    core_nodes,
    enhance_nodes,
    ltx_nodes,
    pack_nodes,
    trellis_nodes,
    vhs_ace_nodes,
)


def documented_widget_widths() -> dict[str, int]:
    """Return the largest documented widget list per node class.

    A node that ships more than one layout lists alternates under ``variants``;
    the widest one is the ceiling a graph may fill.

    Returns:
        ``{class_type: widget count}`` over every encyclopedia entry.
    """
    widths: dict[str, int] = {}
    for builder in _CATALOG_BUILDERS:
        for ntype, spec in builder().items():
            candidates = [len(spec.get("widgets") or [])]
            for variant in spec.get("variants") or []:
                candidates.append(len(variant.get("widgets") or []))
            widths[ntype] = max(widths.get(ntype, 0), max(candidates))
    return widths


def graph_findings(graph: Mapping[str, Any], widths: Mapping[str, int]) -> list[str]:
    """Check one loaded graph against the encyclopedia.

    Args:
        graph: A parsed lab graph dict.
        widths: Output of :func:`documented_widget_widths`.

    Returns:
        One line per violation, naming the node id and class. Empty when the
        graph satisfies the contract.
    """
    problems: list[str] = []
    for node in graph.get("nodes") or []:
        ntype = str(node.get("type") or "")
        node_id = node.get("id")
        if not ntype:
            problems.append(f"node {node_id} carries no type")
            continue
        documented = ntype in widths
        if not documented:
            problems.append(f"node {node_id} ({ntype}): no encyclopedia entry")
        values = node.get("widgets_values")
        if documented and isinstance(values, list) and len(values) > widths[ntype]:
            problems.append(
                f"node {node_id} ({ntype}): {len(values)} widget values for "
                f"{widths[ntype]} documented widgets"
            )
        if ntype in LOADER_TYPES:
            first = values[0] if isinstance(values, list) and values else None
            if not (isinstance(first, str) and first.strip()):
                problems.append(f"node {node_id} ({ntype}): weight widget is not authored")
    return problems
