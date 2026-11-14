"""Give every Describe image toggle a still it can actually caption.

Not collected by pytest. Builders and the lab patcher import
``wire_describe_ref``. ``EZImageDescribe`` takes ``image`` lazily and asks
ComfyUI for it the moment ``enable`` is on, so a graph that ships the toggle
with nothing linked into that slot has an App row the operator cannot honor:
Queue demands a source the canvas never carried. That is GitHub issue #342. The
catalog already solves this on the graphs that kept their upload box, so this
pass brings the rest up to that same shape rather than inventing a second one.

The picker here feeds the captioner only. It deliberately stays out of
``EZImageFormat.image``, because that slot is what **Match input** measures: a
still picked to be captioned must not silently move the output pixels.

A graph that already owns one picker has a still the author can point at, so it
is linked rather than duplicated. A graph that owns several is left alone -
choosing which plate a multi-plate tour captions is an author's call, and the
builder pass skips those graphs for the same reason.

Run it over the catalog with ``PYTHONPATH=custom_nodes:tests/python``::

    python3 tests/python/_wire_describe_ref.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _lab_layout import LAB_X0, ensure_node_spacing, node_pos, set_node_pos
from _lab_paths import lab_graph_paths
from _stamp_app_mode import (
    CAPTION_PICKER_DESCRIPTION,
    CAPTION_PICKER_LABEL,
    CAPTION_PICKER_TITLE,
    NODE_MODE_BYPASS,
    picker_panel_copy,
)
from _wire_format import _link_out, _next_node_id, _nodes_of
from _wire_optional_ref import (
    OPT_SIZE,
    OPT_WIDGETS,
    OPTIONAL_TYPE,
    _stamp_panel_inputs,
)

DESCRIBE_TYPE = "EZImageDescribe"
"""The captioner whose lazy IMAGE the App panel has to be able to fill."""

IMAGE_SLOT = "image"
"""Name of the captioner's optional still input and the picker's first output."""

PANEL_LABEL = CAPTION_PICKER_LABEL
"""App row label the operator sees beside the Describe image toggle."""

PANEL_DESCRIPTION = CAPTION_PICKER_DESCRIPTION
"""App row help: what the box feeds, and what happens when it is empty."""

PANEL_WIDGET = "filename"
"""The picker widget the App row addresses (frozen slot 0 of the node)."""

LOAD_IMAGE_TYPE = "LoadImage"
"""Core Comfy picker, reusable as a caption source when it is the graph's only one."""

SOURCE_TYPES: tuple[str, ...] = (
    LOAD_IMAGE_TYPE,
    OPTIONAL_TYPE,
    "VHS_LoadVideo",
    "EZSnapImage",
)
"""Node classes that already hand a graph a still, so it needs no new picker."""

PICKER_TITLE = CAPTION_PICKER_TITLE
"""Canvas title of the optional picker this pass hands a captioner.

It is what :func:`_stamp_app_mode.picker_panel_copy` reads to tell a caption box
from a Klein reference plate, so the App copy for the two roles stays distinct
through a re-stamp.
"""

PICKER_X_OFFSET = 430.0
"""How far left of the captioner an appended picker sits, in canvas px.

The lane clamps at :data:`~_lab_layout.LAB_X0`: a node left of that margin
would sit further left than the Operator note, which every layout gate reads as
a misplaced header.
"""


def _muted(node: dict[str, Any]) -> bool:
    """True when a node sits outside the live lane, so it demands no input.

    Args:
        node: One node row.

    Returns:
        True for the LiteGraph bypass mode (4).
    """
    return int(node.get("mode") or 0) == NODE_MODE_BYPASS


def _input_slot(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Return one named input slot of a node.

    Args:
        node: One node row.
        name: Slot name to find.

    Returns:
        The slot dict, or None when the node has no such input.
    """
    for slot in node.get("inputs") or []:
        if isinstance(slot, dict) and slot.get("name") == name:
            return slot
    return None


def _graph_has_source(graph: dict[str, Any]) -> bool:
    """True when the graph already owns an image source of any kind.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Whether any node is one of :data:`SOURCE_TYPES`.
    """
    return any(
        str(node.get("type") or "") in SOURCE_TYPES for node in graph.get("nodes") or []
    )


def _starved_captioners(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Captioners that are live and whose still slot carries no link.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The ``EZImageDescribe`` rows in canvas order, muted and already-fed ones
        excluded.
    """
    starved: list[dict[str, Any]] = []
    for node in _nodes_of(graph, DESCRIBE_TYPE):
        if _muted(node):
            continue
        slot = _input_slot(node, IMAGE_SLOT)
        if slot is None or slot.get("link") is not None:
            continue
        starved.append(node)
    return starved


def describe_needs_source(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the captioners whose still no operator can ever supply.

    Pure: the graph is not touched. A node is reported only when it is not
    bypassed, its ``image`` slot carries no link, and the graph owns no image
    source at all - the shape GitHub issue #342 shipped with. A graph that owns a
    picker is excluded: it has a still, and pointing a captioner at one plate of
    a multi-plate tour would have Queue caption the whole table.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The ``EZImageDescribe`` rows that need a source, in canvas order.
    """
    if _graph_has_source(graph):
        return []
    return _starved_captioners(graph)


def _reusable_picker(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the one picker this graph already owns, when there is exactly one.

    Args:
        graph: Parsed lab JSON.

    Returns:
        An ``EZOptionalImage``, else a ``LoadImage``, or None when the graph owns
        none or owns several and picking one would be a guess.
    """
    optional = _nodes_of(graph, OPTIONAL_TYPE)
    if len(optional) == 1:
        return optional[0]
    loads = _nodes_of(graph, LOAD_IMAGE_TYPE)
    if len(loads) == 1:
        return loads[0]
    return None


def _whole_px(value: float) -> float:
    """Return a canvas coordinate as an int when it lands on a whole pixel.

    Args:
        value: Coordinate as computed from the captioner.

    Returns:
        The coordinate, kept to one decimal when it is not whole.
    """
    rounded = round(value)
    return rounded if abs(value - rounded) < 0.05 else round(value, 1)


def _picker_pos(captioner: dict[str, Any]) -> list[float]:
    """Return where an appended picker sits relative to the node it feeds.

    Args:
        captioner: The ``EZImageDescribe`` node the picker will feed.

    Returns:
        ``[x, y]`` one column left of the captioner, held to the lane margin.
    """
    x, y = node_pos(captioner)
    return [_whole_px(max(LAB_X0, x - PICKER_X_OFFSET)), _whole_px(y)]


def _make_picker(nid: int, *, pos: list[float], order: int) -> dict[str, Any]:
    """Build the canonical optional-still picker node.

    Args:
        nid: Node id to assign.
        pos: Canvas position, one column left of the captioner it feeds.
        order: LiteGraph draw order hint, below the captioner's own.

    Returns:
        A node row in the shape the catalog already ships.
    """
    return {
        "id": nid,
        "type": OPTIONAL_TYPE,
        "pos": pos,
        "size": list(OPT_SIZE),
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": IMAGE_SLOT, "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "count", "type": "INT", "links": None, "slot_index": 1},
            {"name": "has_image", "type": "BOOLEAN", "links": [], "slot_index": 2},
        ],
        "properties": {"Node name for S&R": OPTIONAL_TYPE},
        "widgets_values": list(OPT_WIDGETS),
        "title": PICKER_TITLE,
    }


def _append_picker(graph: dict[str, Any], captioner: dict[str, Any]) -> dict[str, Any]:
    """Append the canonical picker that will feed one captioner.

    Args:
        graph: Parsed lab JSON (mutated).
        captioner: The ``EZImageDescribe`` node the picker feeds.

    Returns:
        The appended node.
    """
    node = _make_picker(
        _next_node_id(graph),
        pos=_picker_pos(captioner),
        order=int(captioner.get("order") or 0) - 1,
    )
    graph.setdefault("nodes", []).append(node)
    return node


def _image_consumers(graph: dict[str, Any], picker: dict[str, Any]) -> list[str]:
    """Return the node types reading this picker's still.

    Args:
        graph: Parsed lab JSON.
        picker: One picker node row.

    Returns:
        The consumer types, empty when nothing is linked to the still output.
    """
    link_ids: set[int] = set()
    for slot in picker.get("outputs") or []:
        if isinstance(slot, dict) and slot.get("name") == IMAGE_SLOT:
            link_ids = {int(row) for row in slot.get("links") or []}
    if not link_ids:
        return []
    by_id = {
        int(node["id"]): node
        for node in graph.get("nodes") or []
        if isinstance(node, dict) and "id" in node
    }
    types: list[str] = []
    for row in graph.get("links") or []:
        if isinstance(row, list) and len(row) > 3 and int(row[0]) in link_ids:
            node = by_id.get(int(row[3]))
            if node is not None:
                types.append(str(node.get("type") or ""))
    return types


def _mark_caption_feeders(graph: dict[str, Any]) -> bool:
    """Title the pickers whose only job is to feed a captioner.

    A picker that also feeds Klein is a reference plate and keeps its author's
    title; one whose still goes nowhere but the captioner is the caption box, and
    the title is what the stamp reads when it writes the panel copy. Marking here
    means a re-stamp reproduces the same label instead of reverting the box to
    reference-plate wording.

    Args:
        graph: Parsed lab JSON (mutated).

    Returns:
        Whether any picker ``title`` changed.
    """
    moved = False
    for node in _nodes_of(graph, OPTIONAL_TYPE):
        consumers = _image_consumers(graph, node)
        if not consumers or any(kind != DESCRIBE_TYPE for kind in consumers):
            continue
        if str(node.get("title") or "") != PICKER_TITLE:
            node["title"] = PICKER_TITLE
            moved = True
    return moved


def _repair_picker_geometry(graph: dict[str, Any]) -> bool:
    """Keep the pickers this pass appends inside the lane and off their neighbours.

    The canvas rules the catalog is gated on are the lane margin (nothing sits
    further left than the Operator note) and a ``NODE_GAP`` clearance between
    node boxes. A picker dropped one column left of its captioner can break
    both, so the pass places it and then asks the layout module for the same
    clearance pass ``write_lab_graph`` gives every graph it writes. Only nodes
    carrying this pass's own title are moved: a picker an author placed stays
    where it was put.

    Args:
        graph: Parsed lab JSON (mutated).

    Returns:
        Whether any picker ``pos`` changed.
    """
    if not any(
        str(node.get("type") or "") == DESCRIBE_TYPE for node in graph.get("nodes") or []
    ):
        return False
    moved = False
    for node in graph.get("nodes") or []:
        if node.get("type") != OPTIONAL_TYPE or node.get("title") != PICKER_TITLE:
            continue
        x, y = node_pos(node)
        if x < LAB_X0:
            set_node_pos(node, LAB_X0, y)
            moved = True
    if moved:
        ensure_node_spacing(graph)
    return moved


def _panel_rows(graph: dict[str, Any]) -> list[Any]:
    """Return the App panel's input rows, creating the containers it lacks.

    Args:
        graph: Parsed lab JSON (mutated to add the containers it lacks).

    Returns:
        The live input-row list of ``extra.linearData``.
    """
    extra = graph.get("extra")
    if not isinstance(extra, dict):
        extra = {}
        graph["extra"] = extra
    linear = extra.get("linearData")
    if not isinstance(linear, dict):
        linear = {}
        extra["linearData"] = linear
    rows = linear.get("inputs")
    if not isinstance(rows, list):
        rows = []
        linear["inputs"] = rows
    return rows


def _has_row(rows: list[Any], node_id: int, widget: str) -> bool:
    """True when the panel already carries a row for that node and widget.

    Args:
        rows: App Mode input rows.
        node_id: Node the row would target.
        widget: Widget name the row would name.

    Returns:
        Whether such a row exists.
    """
    return any(len(row) > 1 and row[0] == node_id and row[1] == widget for row in rows)


def _stamp_picker_rows(graph: dict[str, Any], picker: dict[str, Any]) -> bool:
    """Put the picker that feeds the captioner on the App panel once.

    Only an ``EZOptionalImage`` gets rows. Its upload widget is ``filename``,
    while a reused ``LoadImage`` names its upload widget ``image`` and the
    catalog gate refuses a row that names a widget the node does not carry, so a
    loader keeps whatever row its author stamped. An author-stamped filename row
    is kept too: this pass adds a missing control, it does not rewrite copy a
    lane chose on purpose.

    Args:
        graph: Parsed lab JSON (mutated).
        picker: The picker node now feeding a captioner.

    Returns:
        True when a row was added.
    """
    if str(picker.get("type") or "") != OPTIONAL_TYPE:
        return False
    picker_id = int(picker["id"])
    rows = _panel_rows(graph)
    added = False
    if not _has_row(rows, picker_id, PANEL_WIDGET):
        label, description = picker_panel_copy(picker)
        rows.append([picker_id, PANEL_WIDGET, {"label": label, "description": description}])
        added = True
    before = len(rows)
    _stamp_panel_inputs(graph, picker_id)
    return added or len(rows) != before


def wire_describe_ref(graph: dict[str, Any]) -> int:
    """Give every captioner in this graph a still the operator can choose.

    A graph that already owns exactly one picker has a still: the captioner is
    linked to it. A graph that owns none gains the canonical ``EZOptionalImage``
    and its App rows, so the panel offers the box the toggle demands. A graph
    that owns several pickers is left alone.

    Args:
        graph: Parsed lab JSON (mutated).

    Returns:
        Edits applied: pickers appended, stills linked, and panel rows stamped.
        Zero means the graph already holds the invariant, so callers can use the
        count as a changed flag.
    """
    changes = 0
    for captioner in _starved_captioners(graph):
        picker = _reusable_picker(graph)
        if picker is None:
            if _graph_has_source(graph):
                continue
            picker = _append_picker(graph, captioner)
            changes += 1
        _link_out(graph, picker, 0, captioner, IMAGE_SLOT, "IMAGE", widget=False)
        changes += 1
        if _stamp_picker_rows(graph, picker):
            changes += 1
    if _mark_caption_feeders(graph):
        changes += 1
    if _repair_picker_geometry(graph):
        changes += 1
    return changes


def wire_all(root: Path | None = None) -> int:
    """Give every shipped captioner a still, across the catalog.

    Globals:
        None.
    Arguments:
        root: Optional workflows tree whose ``_lab`` directory holds the graphs;
            defaults to the shipped ``workflows/_lab`` tree.
    Outputs:
        One ``wired <path>`` line per rewritten graph on stdout.
    Returns:
        The number of graphs written. An unchanged graph is left byte for byte.
    """
    base = root if root is not None else Path(__file__).resolve().parents[2] / "workflows"
    written = 0
    for path in lab_graph_paths(base):
        graph = json.loads(path.read_text(encoding="utf-8"))
        if wire_describe_ref(graph):
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            print(f"wired {path}")
            written += 1
    return written


if __name__ == "__main__":
    sys.exit(0 if wire_all() >= 0 else 1)
