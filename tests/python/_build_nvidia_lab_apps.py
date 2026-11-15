"""Emit one App-stamped lab graph per NVIDIA lab catalog row.

Not collected by pytest (leading underscore). Run from the repo root:

  python3 tests/python/_build_nvidia_lab_apps.py

The catalog (``custom_nodes/ez_nvidia_lab/catalog.json``) is the single source
of truth and is read through ``nvidia_lab.load_catalog``; this file writes one
``workflows/_lab/labs/nvidia/<id>.json`` per row and nothing else. No graph JSON
is hand-written: ``_lab_paths`` owns the lab identity and the write,
``_stamp_app_mode`` owns the App stamp, and ``_lab_layout.finalize_layout``
owns positions and groups, which is what keeps this lane inside the auditor's
AABB overlap check.

Every App in the tier is stamped ``occupancy="none"``: the GPU work runs outside
the Comfy process, so the one-heavy-job XOR belongs to the operator CLI, not to
the graph. The disk check every lab graph carries is not authored here either:
every lane gets it from ``_stamp_app_mode.apply_lab_completeness_flags``, which
writes it through ``_wire_model_check.ensure_model_check_node``, so its widget
text and its unwired shape cannot drift from the auditor's. That stamper is also
what records this tier's informational cards as declared opt-ins in
``extra.lab_optional_unwired``, so the auditor reads them as intentional rather
than as dead chrome.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_LIB = ROOT / "scripts" / "lib"
CUSTOM_NODES = ROOT / "custom_nodes"
if str(SCRIPTS_LIB) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_LIB))
if str(CUSTOM_NODES) not in sys.path:
    sys.path.insert(0, str(CUSTOM_NODES))

from _lab_layout import LAB_NODE_Y0, LAB_X0, finalize_layout  # noqa: E402
from _lab_paths import (  # noqa: E402
    apply_lab_identity,
    lab_dest,
    write_lab_graph,
)
from _nvidia_lab_specs import (  # noqa: E402
    CANVAS_TITLES,
    CATALOG_TYPE,
    JOB_TYPE,
    LANE,
    NOTE_TYPE,
    OCCUPANCY,
    PREFLIGHT_TYPE,
    VERDICT_TYPE,
    GraphSpec,
    optional_unwired_for,
    spec_for,
)
from _stamp_app_mode import (  # noqa: E402
    apply_lab_completeness_flags,
    ensure_occupancy_note,
    stamp_app_mode,
)
from nvidia_lab import Catalog, Tool, catalog_path, load_catalog  # noqa: E402

NOTE_SIZE: tuple[float, float] = (720.0, 460.0)
PREFLIGHT_SIZE: tuple[float, float] = (360.0, 130.0)
JOB_SIZE: tuple[float, float] = (380.0, 200.0)
VERDICT_SIZE: tuple[float, float] = (380.0, 150.0)
CATALOG_SIZE: tuple[float, float] = (760.0, 230.0)

SIZES: dict[str, tuple[float, float]] = {
    NOTE_TYPE: NOTE_SIZE,
    PREFLIGHT_TYPE: PREFLIGHT_SIZE,
    JOB_TYPE: JOB_SIZE,
    VERDICT_TYPE: VERDICT_SIZE,
    CATALOG_TYPE: CATALOG_SIZE,
}

SOCKETS: dict[str, tuple[tuple[str, str], ...]] = {
    NOTE_TYPE: (),
    PREFLIGHT_TYPE: (("report", "STRING"), ("ok", "BOOLEAN")),
    JOB_TYPE: (("report", "STRING"), ("ok", "BOOLEAN")),
    VERDICT_TYPE: (("verdict", "STRING"),),
    CATALOG_TYPE: (("report", "STRING"),),
}

COLUMN_STEP = 460.0


def _slot_output(name: str, typ: str, slot: int) -> dict[str, Any]:
    """Return one serialized output socket with empty links.

    Args:
        name: Socket name.
        typ: Comfy type string.
        slot: Slot index.

    Returns:
        The socket dict the Vue renderer reads.
    """
    return {"name": name, "type": typ, "links": [], "slot_index": slot}


def _node(nid: int, ntype: str, *, column: int, widgets: list[Any]) -> dict[str, Any]:
    """Return one serialized node row.

    Positions are provisional: ``finalize_layout`` restages every node into the
    lane's columns and groups before the file is written.

    Args:
        nid: LiteGraph node id.
        ntype: ``class_type``.
        column: Provisional column index, used only to seed x.
        widgets: Positional ``widgets_values``.

    Returns:
        The node dict.
    """
    width, height = SIZES[ntype]
    node: dict[str, Any] = {
        "id": nid,
        "type": ntype,
        "pos": [LAB_X0 + column * COLUMN_STEP, float(LAB_NODE_Y0)],
        "size": [width, height],
        "flags": {},
        "order": nid - 1,
        "mode": 0,
        "inputs": [],
        "outputs": [
            _slot_output(name, typ, slot)
            for slot, (name, typ) in enumerate(SOCKETS[ntype])
        ],
        "properties": {"Node name for S&R": ntype},
        "widgets_values": list(widgets),
    }
    if ntype == NOTE_TYPE:
        node["properties"]["cnr_id"] = "comfy-core"
    title = CANVAS_TITLES.get(ntype)
    if title:
        node["title"] = title
    return node


def _widgets_for(ntype: str, tool: Tool) -> list[Any]:
    """Return the authored widget values for one node class.

    Args:
        ntype: ``class_type``.
        tool: The catalog row that pins the ids.

    Returns:
        Positional widget values in the node's documented order.
    """
    if ntype == NOTE_TYPE:
        return []
    if ntype == JOB_TYPE:
        return [tool.id, "", "{}"]
    if ntype == CATALOG_TYPE:
        return ["table"]
    return [tool.id]


def build_graph(catalog: Catalog, tool: Tool) -> dict[str, Any]:
    """Return the finished, stamped graph dict for one catalog row.

    Args:
        catalog: The parsed catalog, for the tier size and the opt-in check.
        tool: The row to emit.

    Returns:
        A serialized Comfy graph, laid out, App-stamped, carrying its unwired
        Check models node, and declaring its unwired cards.
    """
    spec: GraphSpec = spec_for(catalog, tool)
    node_types: list[str] = [NOTE_TYPE, *spec.node_types]
    nodes = [
        _node(nid, ntype, column=nid - 1, widgets=_widgets_for(ntype, tool))
        for nid, ntype in enumerate(node_types, start=1)
    ]
    note_node = nodes[0]
    graph: dict[str, Any] = {
        "id": tool.id,
        "revision": 0,
        "last_node_id": len(nodes),
        "last_link_id": 0,
        "nodes": nodes,
        "links": [],
        "groups": [],
        "config": {},
        "extra": {
            "lab_note": spec.note,
            "lab_profile": spec.graph_rel,
            "lab_description": spec.description,
        },
        "version": 0.4,
    }
    note_node["widgets_values"] = [spec.note]
    apply_lab_identity(graph, spec.graph_rel)
    ensure_occupancy_note(graph, OCCUPANCY)
    graph["extra"]["lab_optional_unwired"] = list(optional_unwired_for(spec.node_types))
    stamp_app_mode(
        graph,
        inputs=[row.as_input_spec() for row in spec.panel_rows],
        outputs=list(spec.output_types),
        lane=LANE,
        occupancy=OCCUPANCY,
        handoff=(),
        default_view="app",
    )
    apply_lab_completeness_flags(graph)
    finalize_layout(graph)
    return graph


def dest_for(tool: Tool) -> Path:
    """Return the path one row's graph is written to.

    Args:
        tool: The catalog row.

    Returns:
        ``workflows/_lab/labs/nvidia/<id>.json``.
    """
    return lab_dest(tool.graph, lane=LANE, subdir="nvidia")


def emit(catalog: Catalog) -> list[tuple[Path, str]]:
    """Write every row's graph and return what was written.

    Args:
        catalog: The parsed catalog.

    Returns:
        ``(path, text)`` per row, in catalog order.
    """
    written: list[tuple[Path, str]] = []
    for tool in catalog.tools:
        graph = build_graph(catalog, tool)
        dest = write_lab_graph(dest_for(tool), graph)
        written.append((dest, dest.read_text(encoding="utf-8")))
    return written


def main() -> int:
    """Emit the tier's graphs and print each path written.

    Returns:
        ``0``.
    """
    catalog = load_catalog(catalog_path())
    for dest, _text in emit(catalog):
        print(dest.relative_to(ROOT).as_posix())
    print(f"emitted {len(catalog.tools)} nvidia lab graphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
