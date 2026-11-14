"""Tests for the dead-picker pass.

The pass owns one claim: an image picker a live graph reads nothing from is a
defect, and an opt-in picker is honest only when the graph says so out loud. The
rules below are the three conditions of that claim, tested on graphs small
enough to read, plus the operator copy that has to go with a deleted control.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_paths import lab_graph_paths
from _strip_dead_pickers import (
    NOTE_FIXES,
    PICKER_TYPES,
    dead_pickers,
    fix_dead_picker_notes,
    strip_all,
    strip_dead_pickers,
)


def _picker(node_id: int, ntype: str = "LoadImage", mode: int = 0, linked: bool = False) -> dict[str, Any]:
    """One picker node, optionally with a live IMAGE link."""
    return {
        "id": node_id,
        "type": ntype,
        "title": f"picker {node_id}",
        "mode": mode,
        "widgets_values": ["cover.png", "image"],
        "inputs": [],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "links": [7] if linked else []},
            {"name": "MASK", "type": "MASK", "links": []},
        ],
    }


def _consumer(node_id: int, slot: str = "cover", slot_type: str = "IMAGE", link: int | None = None) -> dict[str, Any]:
    """A node with one image slot, wired or free."""
    return {
        "id": node_id,
        "type": "EZAudioMetadata",
        "mode": 0,
        "inputs": [{"name": slot, "type": slot_type, "link": link}],
        "outputs": [{"name": "AUDIO", "type": "AUDIO", "links": []}],
        "widgets_values": ["artist"],
    }


def _graph(*nodes: dict[str, Any], optional: list[str] | None = None) -> dict[str, Any]:
    """A graph dict over ``nodes`` with the opt-in declaration the pass reads."""
    links = [
        [7, node["id"], 0, consumer["id"], 0, "IMAGE"]
        for node in nodes
        for consumer in nodes
        if consumer is not node
        and any((out.get("links") or []) for out in node.get("outputs") or [])
        and any(inp.get("link") == 7 for inp in consumer.get("inputs") or [])
    ]
    return {
        "nodes": list(nodes),
        "links": links,
        "extra": {"lab_optional_unwired": optional or []},
    }


def test_every_picker_class_the_gate_scores_is_covered() -> None:
    """The pass and the catalog gate agree on what a picker is."""
    assert {"LoadImage", "EZOptionalImage", "EZSnapImage"} <= PICKER_TYPES


def test_linked_picker_of_any_class_survives() -> None:
    """A picker that feeds something is never touched, whatever its mode."""
    for ntype in sorted(PICKER_TYPES):
        graph = _graph(_picker(1, ntype, mode=4, linked=True), _consumer(2, link=7))
        assert dead_pickers(graph) == [], ntype


def test_unmuted_picker_with_no_consumer_is_dead() -> None:
    """Nothing on the graph can read it, so the widget changes no output."""
    graph = _graph(_picker(1))
    assert dead_pickers(graph) == [1]


def test_declared_opt_in_stays_when_it_is_muted_and_has_a_slot() -> None:
    """The album cover pattern: declared, switched off, with a free slot."""
    graph = _graph(_picker(1, mode=4), _consumer(2), optional=["LoadImage"])
    assert dead_pickers(graph) == []


def test_declared_but_unmuted_picker_is_still_dead() -> None:
    """A declaration without the muted flag is a graph that pretends to read it."""
    graph = _graph(_picker(1, mode=0), _consumer(2), optional=["LoadImage"])
    assert dead_pickers(graph) == [1]


def test_declared_and_muted_picker_without_a_slot_is_dead() -> None:
    """No slot to wire it into means no operator action can ever use it."""
    graph = _graph(_picker(1, mode=4), _consumer(2, slot="title", slot_type="STRING"), optional=["LoadImage"])
    assert dead_pickers(graph) == [1]


def test_undeclared_picker_with_a_free_slot_is_dead() -> None:
    """A slot alone does not make a live picker an opt-in; the graph must say so."""
    graph = _graph(_picker(1, mode=0), _consumer(2))
    assert dead_pickers(graph) == [1]


def test_free_slot_named_without_a_type_still_counts() -> None:
    """A slot that carries a familiar name but no type is still a place to wire."""
    consumer = _consumer(2, slot="start_image")
    del consumer["inputs"][0]["type"]
    graph = _graph(_picker(1, mode=4), consumer, optional=["LoadImage"])
    assert dead_pickers(graph) == []


def test_the_picker_itself_never_counts_as_its_own_consumer() -> None:
    """Its own unwired input is not a slot that could receive it."""
    picker = _picker(1, mode=4)
    picker["inputs"] = [{"name": "image", "type": "IMAGE", "link": None}]
    graph = _graph(picker, optional=["LoadImage"])
    assert dead_pickers(graph) == [1]


def test_a_non_picker_node_is_none_of_this_pass_business() -> None:
    """Only the picker classes are scored, so a dead KSampler is left alone."""
    graph = _graph({"id": 3, "type": "KSampler", "mode": 0, "outputs": []})
    assert dead_pickers(graph) == []


def test_strip_removes_the_node_and_its_bookkeeping() -> None:
    """Deleting leaves no orphan node entry and no link that referenced it."""
    graph = _graph(_picker(1), _consumer(2))
    graph["links"] = [[7, 1, 0, 2, 0, "IMAGE"]]
    assert strip_dead_pickers(graph, "photos/nope") == 1
    assert [n["id"] for n in graph["nodes"]] == [2]
    assert graph["links"] == []
    assert graph["nodes"][0]["inputs"][0]["link"] is None


def test_strip_is_idempotent() -> None:
    """Running the pass twice over the same graph changes it once."""
    graph = _graph(_picker(1))
    assert strip_dead_pickers(graph, "photos/nope") == 1
    assert strip_dead_pickers(graph, "photos/nope") == 0


def test_note_copy_that_promised_a_dead_control_is_rewritten() -> None:
    """The sentence telling the operator to use a control goes with the node."""
    lab_rel = next(iter(NOTE_FIXES))
    needle, replacement = NOTE_FIXES[lab_rel][0]
    graph = {
        "nodes": [
            {"id": 9, "type": "Note", "widgets_values": [f"Intro. {needle} Trailing."]},
            {"id": 10, "type": "MarkdownNote", "widgets_values": [{"text": "not a string"}]},
            {"id": 11, "type": "Note", "widgets_values": []},
            {"id": 12, "type": "Note"},
        ]
    }
    assert fix_dead_picker_notes(graph, lab_rel) == 1
    assert graph["nodes"][0]["widgets_values"][0] == f"Intro. {replacement} Trailing."
    assert graph["nodes"][1]["widgets_values"] == [{"text": "not a string"}]


def test_note_copy_for_an_unknown_graph_is_untouched() -> None:
    """A graph with no entry in the copy table keeps its Note verbatim."""
    graph = {"nodes": [{"id": 9, "type": "Note", "widgets_values": ["keep me"]}]}
    assert fix_dead_picker_notes(graph, "no/such/graph") == 0
    assert graph["nodes"][0]["widgets_values"] == ["keep me"]


def test_strip_all_rewrites_only_the_graphs_that_change(tmp_path: Path) -> None:
    """The file-level entrypoint writes the dead graph and leaves the clean one."""
    lab = tmp_path / "_lab"
    lab.mkdir(parents=True)
    dead = _graph(_picker(1))
    clean = _graph(_picker(2, linked=True), _consumer(3, link=7))
    for name, payload in (("dead.json", dead), ("clean.json", clean)):
        (lab / name).write_text(json.dumps(payload), encoding="utf-8")
    before = (lab / "clean.json").read_text(encoding="utf-8")
    assert strip_all(tmp_path) == 1
    assert json.loads((lab / "dead.json").read_text(encoding="utf-8"))["nodes"] == []
    assert (lab / "clean.json").read_text(encoding="utf-8") == before


def test_the_shipped_catalog_ships_no_dead_picker() -> None:
    """The pass has run over the real catalog, so nothing dead is left in it."""
    dead: list[str] = []
    for path in lab_graph_paths():
        graph = json.loads(path.read_text(encoding="utf-8"))
        if dead_pickers(graph):
            dead.append(str(path))
    assert dead == []


def test_a_declaration_whose_picker_is_gone_is_dropped() -> None:
    """An App must not advertise an upload box it no longer contains."""
    graph = _graph(_consumer(2), optional=["LoadImage"])
    assert strip_dead_pickers(graph) == 1
    assert "lab_optional_unwired" not in graph["extra"]


def test_a_declaration_whose_picker_survives_is_kept() -> None:
    graph = _graph(
        _picker(1, "EZOptionalImage", mode=4), _consumer(2), optional=["EZOptionalImage"]
    )
    assert strip_dead_pickers(graph) == 0
    assert graph["extra"]["lab_optional_unwired"] == ["EZOptionalImage"]


def test_a_non_picker_declaration_is_nobody_s_business() -> None:
    """Only picker classes are pruned; another node's contract is left alone."""
    graph = _graph(_consumer(2), optional=["SaveAudio"])
    assert strip_dead_pickers(graph) == 0
    assert graph["extra"]["lab_optional_unwired"] == ["SaveAudio"]


def test_the_dead_declaration_leaves_and_the_live_one_stays() -> None:
    graph = _graph(
        _picker(1, "EZOptionalImage", mode=4),
        _consumer(2),
        optional=["EZOptionalImage", "LoadImage"],
    )
    assert strip_dead_pickers(graph) == 1
    assert graph["extra"]["lab_optional_unwired"] == ["EZOptionalImage"]


def test_a_graph_with_no_extra_block_is_left_alone() -> None:
    """The prune tolerates a graph that never declared anything."""
    graph: dict[str, Any] = {"nodes": [_consumer(2)], "links": []}
    assert strip_dead_pickers(graph) == 0
