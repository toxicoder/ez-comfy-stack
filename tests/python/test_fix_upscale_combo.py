"""One shared Upscale dropdown stays Queueable across every save it serves.

The invariant: a combo shared between nodes is typed by the list of values the
combo accepts, in the producing output slot, the consuming input slot, and the
link row. Typed ``STRING``, ComfyUI's frontend reads each clone as an invalid
connection, marks the whole App red, and Queue never starts.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from _fix_upscale_combo import (
    RUNG_INPUT,
    RUNG_LINK,
    RUNG_OUTPUT,
    RUNG_SLOT,
    combo_typed_upscale_links,
    fix_all,
    fix_upscale_combo,
)
from _lab_paths import lab_graph_paths, lab_json
from _wire_upscale import UPSCALE_COMBO_TYPE, UPSCALE_TYPE

CHAIN_GRAPH = "photos/cutout"
"""A shipped App whose saves share one rung across an EZImageUpscale chain."""

SOLO_GRAPH = "photos/thumbnail"
"""A shipped App with one upscale node and nothing sharing its rung."""

_LINK_TYPE_PATH = re.compile(r"\.links\[\d+\]\[5\]")
"""JSON path of a link row's type cell, the only link field the pass owns."""


def _graph(stem: str) -> dict[str, Any]:
    """Load a shipped graph as a fresh dict the test may mutate.

    Args:
        stem: Lab-relative id, such as ``photos/cutout``.

    Returns:
        The parsed graph, owned by the caller.
    """
    return json.loads(lab_json(stem).read_text(encoding="utf-8"))


def _rung_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the rung nodes of a graph.

    Args:
        graph: Parsed lab graph.

    Returns:
        Every ``EZImageUpscale`` node row.
    """
    return [node for node in graph["nodes"] if node.get("type") == UPSCALE_TYPE]


def _diff_paths(before: Any, after: Any, where: str = "") -> list[str]:
    """Return the JSON paths where two loaded graphs differ.

    Args:
        before: The graph as it was read.
        after: The graph after the pass ran.
        where: Path prefix, used by recursion.

    Returns:
        One readable path per differing leaf, list, or dict key.
    """
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        found: list[str] = []
        for key in sorted(set(before) | set(after)):
            if key not in before:
                found.append(f"{where}.{key} added")
            elif key not in after:
                found.append(f"{where}.{key} removed")
            else:
                found.extend(_diff_paths(before[key], after[key], f"{where}.{key}"))
        return found
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return [f"{where} length {len(before)} -> {len(after)}"]
        found = []
        for index, (left, right) in enumerate(zip(before, after)):
            found.extend(_diff_paths(left, right, f"{where}[{index}]"))
        return found
    return [f"{where}: {before!r} -> {after!r}"]


def _break_rung(graph: dict[str, Any]) -> int:
    """Retype a converged shared rung back to the shape the bug shipped in.

    The catalog is fixed, so a test that wants the defect has to author it. The
    three places a graph records the rung's type all go back to ``STRING``, which
    is what made the frontend mark every clone invalid.

    Args:
        graph: Parsed lab graph (mutated).

    Returns:
        The number of slots and rows retyped.
    """
    nodes = {int(node["id"]): node for node in graph["nodes"]}
    changed = 0
    for row in _rung_link_rows(graph):
        if row[5] != "STRING":
            row[5] = "STRING"
            changed += 1
        for node, index in ((nodes[int(row[1])], row[2]), (nodes[int(row[3])], row[4])):
            key = "outputs" if node is nodes[int(row[1])] else "inputs"
            slot = node[key][int(index)]
            if slot.get("type") != "STRING":
                slot["type"] = "STRING"
                changed += 1
    return changed


def _broken_chain() -> dict[str, Any]:
    """Load the chain App and put the reported defect back into it.

    Returns:
        A graph whose shared rung is typed ``STRING`` in all three places.
    """
    graph = _graph(CHAIN_GRAPH)
    assert _break_rung(graph) > 0, "the seed graph has a rung to break"
    return graph


def test_a_string_rung_is_reported() -> None:
    """The shape behind the bug is the shape the pass reports."""
    graph = _broken_chain()
    found = combo_typed_upscale_links(graph)
    assert found, "the seeded defect went unreported"
    assert {kind for kind, _nid, _slot in found} == {
        RUNG_OUTPUT,
        RUNG_INPUT,
        RUNG_LINK,
    }, found
    assert all(slot == RUNG_SLOT for _kind, _nid, slot in found)


def test_a_solo_rung_needs_nothing() -> None:
    """An upscale node that shares nothing is typed by the node definition."""
    graph = _graph(SOLO_GRAPH)
    node = _rung_nodes(graph)[0]
    assert [slot.get("name") for slot in node.get("inputs") or []] == ["image"]
    before = copy.deepcopy(graph)
    assert combo_typed_upscale_links(graph) == []
    assert fix_upscale_combo(graph) == 0
    assert graph == before


def test_the_fixer_rewrites_all_three_places() -> None:
    """Producer slot, consumer slot, and link row land on the combo values."""
    graph = _broken_chain()
    assert fix_upscale_combo(graph) > 0
    assert combo_typed_upscale_links(graph) == []

    rung_rows = [row for row in graph["links"] if isinstance(row[5], list)]
    assert rung_rows, "the shared rung link carries the values list"
    assert all(row[5] == UPSCALE_COMBO_TYPE for row in rung_rows)
    nodes = {int(node["id"]): node for node in graph["nodes"]}
    for row in rung_rows:
        producer = nodes[int(row[1])]
        consumer = nodes[int(row[3])]
        produced = producer["outputs"][int(row[2])]
        consumed = consumer["inputs"][int(row[4])]
        assert produced["name"] == RUNG_SLOT
        assert produced["type"] == UPSCALE_COMBO_TYPE
        assert consumed["name"] == RUNG_SLOT
        assert consumed["type"] == UPSCALE_COMBO_TYPE
        assert consumed.get("widget") == {"name": RUNG_SLOT}


def test_the_fix_is_idempotent() -> None:
    """A second pass over a converged graph changes nothing at all."""
    graph = _broken_chain()
    assert fix_upscale_combo(graph) > 0
    settled = copy.deepcopy(graph)
    assert fix_upscale_combo(settled) == 0
    assert settled == graph


def test_nothing_but_the_rung_types_changes() -> None:
    """The pass rewrites types and leaves counters, order, and layout alone."""
    before = _broken_chain()
    after = copy.deepcopy(before)
    assert fix_upscale_combo(after) > 0
    changed = _diff_paths(before, after)
    assert changed, "the seed graph had work for the pass"
    for entry in changed:
        where = entry.split(": ", 1)[0]
        allowed = where.endswith(".type") or _LINK_TYPE_PATH.fullmatch(where)
        assert allowed, entry
    for key in ("last_node_id", "last_link_id"):
        assert before[key] == after[key]
    assert [node["id"] for node in before["nodes"]] == [
        node["id"] for node in after["nodes"]
    ]
    assert len(before["links"]) == len(after["links"])


def test_an_unshared_rung_is_still_typed_by_its_values() -> None:
    """A rung no neighbour reads blocks nothing, and is typed anyway.

    An unlinked output slot validates nothing, so the finder keeps its report to
    the rungs that actually block Queue. The fixer is wider: the generator types
    every rung slot with the combo's own values, and a shipped graph is only
    byte-identical to its generator once this slot agrees with that.
    """
    graph = _graph(SOLO_GRAPH)
    node = _rung_nodes(graph)[0]
    rung_out = next(
        slot for slot in node["outputs"] if slot.get("name") == RUNG_SLOT
    )
    assert rung_out["links"] in ([], None), "the seed rung shares nothing"
    rung_out["type"] = "STRING"
    assert combo_typed_upscale_links(graph) == []
    assert fix_upscale_combo(graph) == 1
    assert rung_out["type"] == UPSCALE_COMBO_TYPE


def _rung_link_rows(graph: dict[str, Any]) -> list[list[Any]]:
    """Return the link rows that carry a rung out of an upscale node.

    Args:
        graph: Parsed lab graph.

    Returns:
        Every row whose producer slot is an ``EZImageUpscale`` rung output.
    """
    nodes = {int(node["id"]): node for node in graph["nodes"]}
    rows: list[list[Any]] = []
    for row in graph["links"]:
        producer = nodes.get(int(row[1]))
        if producer is None or producer.get("type") != UPSCALE_TYPE:
            continue
        slots = producer.get("outputs") or []
        if isinstance(row[2], int) and 0 <= row[2] < len(slots):
            if slots[int(row[2])].get("name") == RUNG_SLOT:
                rows.append(row)
    return rows


def test_a_combo_named_upscale_on_another_class_is_nobody_s_business() -> None:
    """Only an EZImageUpscale rung shared between its own kind is in scope."""
    graph = _broken_chain()
    victim = next(
        node
        for node in graph["nodes"]
        if node.get("type") not in {UPSCALE_TYPE, "Note", "EZModelCheck"}
        and node.get("inputs")
    )
    rung_link = _rung_link_rows(graph)[0]
    victim["inputs"].append(
        {
            "name": RUNG_SLOT,
            "type": "STRING",
            "link": rung_link[0],
            "widget": {"name": RUNG_SLOT},
        }
    )
    rung_link[3] = victim["id"]
    found = combo_typed_upscale_links(graph)
    assert (RUNG_INPUT, int(victim["id"]), RUNG_SLOT) not in found


def test_the_node_types_its_rung_by_its_values() -> None:
    """The node contract matches what the graphs link, or the link drifts."""
    from ez_image.nodes import EZImageUpscale

    assert EZImageUpscale.RETURN_TYPES[1] == UPSCALE_COMBO_TYPE
    assert EZImageUpscale.RETURN_NAMES == ("image", RUNG_SLOT)


def test_fix_all_writes_only_the_graph_that_changed(tmp_path: Path) -> None:
    """The catalog walk leaves a converged graph's bytes untouched."""
    broken = _broken_chain()
    settled = _graph(SOLO_GRAPH)
    rough = tmp_path / "cutout.json"
    rough.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")
    quiet = tmp_path / "thumbnail.json"
    quiet.write_text(json.dumps(settled, indent=2) + "\n", encoding="utf-8")
    before = quiet.read_bytes()

    assert fix_all(tmp_path) == 1
    assert quiet.read_bytes() == before
    written = json.loads(rough.read_text(encoding="utf-8"))
    assert combo_typed_upscale_links(written) == []
    assert rough.read_text(encoding="utf-8") == json.dumps(written, indent=2) + "\n", (
        "the canonical write form holds"
    )


def test_the_shipped_catalog_shares_no_string_rung() -> None:
    """Every graph in the catalog links its shared rung under the combo values."""
    for path in lab_graph_paths():
        graph = json.loads(path.read_text(encoding="utf-8"))
        assert combo_typed_upscale_links(graph) == [], f"{path} shares a STRING rung"
