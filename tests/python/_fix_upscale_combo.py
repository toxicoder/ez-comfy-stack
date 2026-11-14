"""Type every Upscale rung slot by the values the combo actually accepts.

Not collected by pytest. The lab patcher imports ``fix_upscale_combo``.

``EZImageUpscale`` lets one node's chosen rung feed its siblings so a multi-save
App shows a single **Upscale** dropdown. ComfyUI types a combo widget input by
the list of values it accepts, so that link has to carry the list in all three
places a graph records a type: the producing output slot, the consuming input
slot, and the link row. A rung typed ``STRING`` is read as an invalid connection,
which marks every save in the App red and blocks Queue outright. ``EZImageMode``
has always shared its ``enhance_mode`` this way; this pass brings the rung up to
the same contract, on wired slots and on the node's own slots alike.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from _lab_paths import lab_graph_paths
from _wire_upscale import UPSCALE_COMBO_TYPE, UPSCALE_TYPE

RUNG_SLOT = "upscale"
"""The combo the rung shares between nodes."""

RUNG_OUTPUT = "output"
"""Kind tag: a producing node's output slot."""

RUNG_INPUT = "input"
"""Kind tag: a consuming node's widget input slot."""

RUNG_LINK = "link"
"""Kind tag: a row in the graph's link table."""


def _nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the node rows of a graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The node list, empty when the graph has none.
    """
    return [node for node in graph.get("nodes") or [] if isinstance(node, dict)]


def _slot_index(node: Mapping[str, Any], name: str, *, inputs: bool) -> int | None:
    """Return the positional index of one named slot.

    Args:
        node: One node row.
        name: Slot name to find.
        inputs: Read ``inputs`` when True, ``outputs`` when False.

    Returns:
        The zero-based slot index, or None when no slot carries that name.
    """
    slots = node.get("inputs" if inputs else "outputs") or []
    for index, slot in enumerate(slots):
        if isinstance(slot, dict) and slot.get("name") == name:
            return index
    return None


def _node_by_id(graph: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """Index a graph's nodes by id.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``node id -> node row``.
    """
    return {int(node["id"]): node for node in _nodes(graph) if "id" in node}


def _rung_links(graph: Mapping[str, Any]) -> list[list[Any]]:
    """Return the link rows that carry one node's rung into another.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Every row whose producer is an ``EZImageUpscale`` rung output and whose
        consumer is an ``EZImageUpscale`` rung input.
    """
    nodes = _node_by_id(graph)
    rows: list[list[Any]] = []
    for row in graph.get("links") or []:
        if not isinstance(row, list) or len(row) < 6:
            continue
        producer = nodes.get(int(row[1]))
        consumer = nodes.get(int(row[3]))
        if producer is None or consumer is None:
            continue
        if str(producer.get("type") or "") != UPSCALE_TYPE:
            continue
        if str(consumer.get("type") or "") != UPSCALE_TYPE:
            continue
        if _slot_index(producer, RUNG_SLOT, inputs=False) != row[2]:
            continue
        if _slot_index(consumer, RUNG_SLOT, inputs=True) != row[4]:
            continue
        rows.append(row)
    return rows


def combo_typed_upscale_links(graph: Mapping[str, Any]) -> list[tuple[str, int, str]]:
    """Return every shared rung slot or link the frontend would read as invalid.

    This is the report an operator is blocked by, so its scope is the rung that
    is actually shared: a link that carries one node's choice into another. An
    ``EZImageUpscale`` output with no link on it draws nothing and validates
    nothing, which is why :func:`fix_upscale_combo` is deliberately wider than
    this finder.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``(kind, id, slot)`` triples, where ``kind`` is one of
        :data:`RUNG_OUTPUT`, :data:`RUNG_INPUT`, or :data:`RUNG_LINK` and ``id``
        is the node id for a slot or the link id for a row.
    """
    expected = list(UPSCALE_COMBO_TYPE)
    nodes = _node_by_id(graph)
    found: list[tuple[str, int, str]] = []
    seen: set[tuple[str, int]] = set()
    for row in _rung_links(graph):
        producer = nodes[int(row[1])]
        consumer = nodes[int(row[3])]
        if row[5] != expected:
            found.append((RUNG_LINK, int(row[0]), RUNG_SLOT))
        for kind, node, index in (
            (RUNG_OUTPUT, producer, row[2]),
            (RUNG_INPUT, consumer, row[4]),
        ):
            key = (kind, int(node["id"]))
            if key in seen:
                continue
            seen.add(key)
            slot = (node.get("outputs" if kind == RUNG_OUTPUT else "inputs") or [])[
                int(index)
            ]
            if slot.get("type") != expected:
                found.append((kind, int(node["id"]), RUNG_SLOT))
    return found


def fix_upscale_combo(graph: dict[str, Any]) -> int:
    """Retype every rung slot and link to the combo's own values.

    Wider than :func:`combo_typed_upscale_links` on purpose. The catalog is
    generated, and the generator types every rung slot on an ``EZImageUpscale``
    node with the combo's values whether or not that slot is wired, so a shipped
    graph is only byte-identical to its generator once every slot agrees. The
    finder stays narrow because it answers the operator's question - what stops
    Queue - while the fixer answers the repo's - what does the generator write.

    Nothing else in the graph is touched: no renumbering, no key reordering, and
    no counter churn, so the pass is safe to re-run and its diff is only types.

    Args:
        graph: Parsed lab JSON (mutated).

    Returns:
        The number of slots and link rows rewritten.
    """
    expected = list(UPSCALE_COMBO_TYPE)
    nodes = _node_by_id(graph)
    changed = 0
    touched: set[tuple[str, int]] = set()
    for row in _rung_links(graph):
        if row[5] != expected:
            row[5] = list(expected)
            changed += 1
        for kind, node, index in (
            (RUNG_OUTPUT, nodes[int(row[1])], row[2]),
            (RUNG_INPUT, nodes[int(row[3])], row[4]),
        ):
            key = (kind, int(node["id"]))
            if key in touched:
                continue
            touched.add(key)
            slot = (node.get("outputs" if kind == RUNG_OUTPUT else "inputs") or [])[
                int(index)
            ]
            if slot.get("type") != expected:
                slot["type"] = list(expected)
                changed += 1
    for node in _nodes(graph):
        if str(node.get("type") or "") != UPSCALE_TYPE:
            continue
        for kind, slots in (
            (RUNG_OUTPUT, node.get("outputs") or []),
            (RUNG_INPUT, node.get("inputs") or []),
        ):
            key = (kind, int(node["id"]))
            if key in touched:
                continue
            touched.add(key)
            for slot in slots:
                if isinstance(slot, dict) and slot.get("name") == RUNG_SLOT:
                    if slot.get("type") != expected:
                        slot["type"] = list(expected)
                        changed += 1
    return changed


def fix_all(root: Path | None = None) -> int:
    """Retype every shared rung across the shipped catalog.

    Globals:
        None.
    Arguments:
        root: Optional directory holding the graphs; defaults to the shipped
            ``workflows/_lab`` tree.
    Outputs:
        One ``fixed <path>`` line per rewritten graph on stdout.
    Returns:
        The number of graphs written.
    """
    paths = lab_graph_paths() if root is None else sorted(Path(root).rglob("*.json"))
    written = 0
    for path in paths:
        graph = json.loads(path.read_text(encoding="utf-8"))
        if fix_upscale_combo(graph):
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            print(f"fixed {path}")
            written += 1
    return written


if __name__ == "__main__":
    sys.exit(0 if fix_all() >= 0 else 1)
