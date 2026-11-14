"""Tests for the Describe image source pass.

The pass owns one claim: a live ``EZImageDescribe`` toggle is honest only when
the graph can hand it a still the operator chose (GitHub issue #342). The rules
below are that claim, tested on graphs copied out of the shipped catalog and
then broken - a hand-written 17-node graph would test the fixture rather than
the catalog. Nothing here writes into ``workflows/``.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from _lab_layout import LAB_X0
from _lab_paths import cached_lab_graph_rows, lab_json
from _stamp_app_mode import display_label, picker_panel_copy, widget_description
from _wire_describe_ref import (
    DESCRIBE_TYPE,
    OPTIONAL_TYPE,
    PANEL_DESCRIPTION,
    PANEL_LABEL,
    PICKER_TITLE,
    SOURCE_TYPES,
    describe_needs_source,
    wire_all,
    wire_describe_ref,
)
from _wire_optional_ref import (
    OPT_SIZE,
    OPT_WIDGETS,
    REF_TOGGLE,
    REF_TOGGLE_DESCRIPTION,
    REF_TOGGLE_LABEL,
)

WIRED_APP = "business/b2b-saas/case-cover"
STARVED_APP = "photos/thumbnail"
FORMAT_TYPE = "EZImageFormat"


def _shipped(rel: str) -> dict[str, Any]:
    """Deep copy of a shipped graph, so no pass can reach ``workflows/``."""
    return copy.deepcopy(json.loads(lab_json(rel).read_text(encoding="utf-8")))


def _broken() -> dict[str, Any]:
    """The wired App above, broken into the #342 shape: picker gone, toggle live."""
    graph = _shipped(WIRED_APP)
    picker_id = int(_only(graph, OPTIONAL_TYPE)["id"])
    dropped = {int(row[0]) for row in graph["links"] if int(row[1]) == picker_id}
    graph["links"] = [row for row in graph["links"] if int(row[0]) not in dropped]
    for node in graph["nodes"]:
        for slot in node.get("inputs") or []:
            if slot.get("link") in dropped:
                slot["link"] = None
    graph["nodes"] = [node for node in graph["nodes"] if int(node["id"]) != picker_id]
    rows = graph["extra"]["linearData"]["inputs"]
    graph["extra"]["linearData"]["inputs"] = [row for row in rows if row[0] != picker_id]
    return graph


def _only(graph: dict[str, Any], ntype: str) -> dict[str, Any]:
    """The single node of ``ntype``, which these fixtures keep singular."""
    hits: list[dict[str, Any]] = [
        node for node in graph["nodes"] if node.get("type") == ntype
    ]
    assert len(hits) == 1, f"expected one {ntype}, found {len(hits)}"
    return hits[0]


def _slot(node: dict[str, Any], name: str) -> dict[str, Any]:
    """One input slot by name."""
    slots: list[dict[str, Any]] = node.get("inputs") or []
    return next(slot for slot in slots if slot.get("name") == name)


def _rows(graph: dict[str, Any]) -> list[Any]:
    """The App Mode input rows."""
    rows: list[Any] = graph["extra"]["linearData"]["inputs"]
    return rows


def _link_rows(graph: dict[str, Any], src_id: int) -> list[Any]:
    """Link rows produced by one node."""
    return [row for row in graph["links"] if int(row[1]) == src_id]


def _free_picker(node_id: int, *, ntype: str = OPTIONAL_TYPE) -> dict[str, Any]:
    """An unwired picker, the shape left behind when its consumer went away."""
    outputs: list[dict[str, Any]] = (
        [
            {"name": "image", "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "count", "type": "INT", "links": None, "slot_index": 1},
            {"name": "has_image", "type": "BOOLEAN", "links": [], "slot_index": 2},
        ]
        if ntype == OPTIONAL_TYPE
        else [
            {"name": "IMAGE", "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "MASK", "type": "MASK", "links": [], "slot_index": 1},
        ]
    )
    return {
        "id": node_id,
        "type": ntype,
        "title": PICKER_TITLE if ntype == OPTIONAL_TYPE else "Upload",
        "pos": [0, 0],
        "size": list(OPT_SIZE),
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [],
        "outputs": outputs,
        "properties": {"Node name for S&R": ntype},
        "widgets_values": (
            list(OPT_WIDGETS) if ntype == OPTIONAL_TYPE else ["example.png", "image"]
        ),
    }


def test_an_already_wired_graph_needs_nothing() -> None:
    """The shipped working shape is reported clean and left untouched."""
    graph = _shipped(WIRED_APP)
    assert describe_needs_source(graph) == []
    assert wire_describe_ref(graph) == 0


def test_the_broken_shape_is_reported() -> None:
    """A live toggle with a free image slot and no picker is the defect."""
    graph = _broken()
    assert [node["id"] for node in describe_needs_source(graph)] == [
        int(_only(graph, DESCRIBE_TYPE)["id"])
    ]


def test_the_finder_does_not_mutate_the_graph() -> None:
    """Scoring is a read: the same bytes go in and come out."""
    graph = _broken()
    before = json.dumps(graph, sort_keys=True)
    assert describe_needs_source(graph)
    assert json.dumps(graph, sort_keys=True) == before


def test_a_bypassed_captioner_is_nobody_s_business() -> None:
    """A muted node demands nothing, so it needs no still behind its toggle."""
    graph = _broken()
    _only(graph, DESCRIBE_TYPE)["mode"] = 4
    assert describe_needs_source(graph) == []
    assert wire_describe_ref(graph) == 0


def test_a_captioner_without_the_slot_is_not_reported() -> None:
    """No declared image slot means there is nothing for this pass to link into."""
    graph = _broken()
    node = _only(graph, DESCRIBE_TYPE)
    node["inputs"] = [slot for slot in node["inputs"] if slot.get("name") != "image"]
    assert describe_needs_source(graph) == []
    assert wire_describe_ref(graph) == 0


def test_the_picker_is_appended_once_and_linked_both_ways() -> None:
    """The appended node is the one the graphs that kept a picker already ship."""
    graph = _broken()
    captioner = _only(graph, DESCRIBE_TYPE)
    slot_index = captioner["inputs"].index(_slot(captioner, "image"))
    before_nodes, before_links = int(graph["last_node_id"]), int(graph["last_link_id"])

    assert wire_describe_ref(graph) == 3

    picker = _only(graph, OPTIONAL_TYPE)
    assert picker["title"] == PICKER_TITLE
    assert picker["size"] == [360.0, 120.0]
    assert picker["widgets_values"] == ["", True, "", ""]
    assert picker["mode"] == 0
    assert picker["flags"] == {}
    assert picker["properties"] == {"Node name for S&R": OPTIONAL_TYPE}
    assert picker["order"] == int(captioner["order"]) - 1
    assert picker["pos"] == [
        max(LAB_X0, captioner["pos"][0] - 430),
        captioner["pos"][1],
    ]
    assert [out["name"] for out in picker["outputs"]] == ["image", "count", "has_image"]
    assert [out["type"] for out in picker["outputs"]] == ["IMAGE", "INT", "BOOLEAN"]
    link_id = _slot(captioner, "image")["link"]
    assert link_id is not None
    assert _link_rows(graph, int(picker["id"])) == [
        [link_id, int(picker["id"]), 0, int(captioner["id"]), slot_index, "IMAGE"]
    ]
    assert picker["outputs"][0]["links"] == [link_id]
    assert int(graph["last_node_id"]) == before_nodes + 1
    assert int(graph["last_link_id"]) == before_links + 1


def test_the_box_lands_on_the_app_panel_once() -> None:
    """The box the toggle demands is the box the App offers, and only once."""
    graph = _broken()
    wire_describe_ref(graph)
    picker_id = int(_only(graph, OPTIONAL_TYPE)["id"])
    filename = [row for row in _rows(graph) if row[0] == picker_id and row[1] == "filename"]
    toggle = [row for row in _rows(graph) if row[0] == picker_id and row[1] == REF_TOGGLE]
    assert filename == [
        [picker_id, "filename", {"label": PANEL_LABEL, "description": PANEL_DESCRIPTION}]
    ]
    assert toggle == [
        [
            picker_id,
            REF_TOGGLE,
            {"label": REF_TOGGLE_LABEL, "description": REF_TOGGLE_DESCRIPTION},
        ]
    ]
    assert wire_describe_ref(graph) == 0
    assert [row for row in _rows(graph) if row[0] == picker_id] == filename + toggle


def test_wiring_is_idempotent() -> None:
    """The second run finds nothing left to do and changes nothing."""
    graph = _broken()
    assert wire_describe_ref(graph) > 0
    once = json.dumps(graph, sort_keys=True)
    assert wire_describe_ref(graph) == 0
    assert json.dumps(graph, sort_keys=True) == once
    assert len([node for node in graph["nodes"] if node.get("type") == OPTIONAL_TYPE]) == 1


def test_an_existing_optional_picker_is_reused() -> None:
    """A graph that already owns the box is linked to it, not given a second one."""
    graph = _broken()
    free = _free_picker(99)
    graph["nodes"].append(free)
    before_nodes = int(graph["last_node_id"])

    # link + row + the lane-margin repair the pass owes a box parked at x=0.
    assert wire_describe_ref(graph) == 3

    assert [node for node in graph["nodes"] if node.get("type") == OPTIONAL_TYPE] == [free]
    assert int(graph["last_node_id"]) == before_nodes
    assert free["pos"][0] == LAB_X0, "the caption box stays inside the lane margin"
    assert free["title"] == PICKER_TITLE, "the stamp reads the role off the title"
    link_id = _slot(_only(graph, DESCRIBE_TYPE), "image")["link"]
    assert link_id is not None
    assert free["outputs"][0]["links"] == [link_id]


def test_an_author_stamped_row_keeps_its_own_copy() -> None:
    """The pass adds a missing control; it does not rewrite one that exists."""
    graph = _broken()
    graph["nodes"].append(_free_picker(99))
    _rows(graph).append([99, "filename", {"label": "Plate", "description": "yours"}])

    wire_describe_ref(graph)

    row = next(row for row in _rows(graph) if row[0] == 99 and row[1] == "filename")
    assert row[2]["label"] == "Plate"


def test_a_single_load_image_is_reused_without_a_filename_row() -> None:
    """A loader uploads through ``image``, so a filename row would name a widget it lacks."""
    graph = _broken()
    graph["nodes"].append(_free_picker(99, ntype="LoadImage"))

    assert wire_describe_ref(graph) == 1

    assert _only(graph, "LoadImage")["outputs"][0]["links"]
    assert [row for row in _rows(graph) if row[0] == 99] == []


def test_several_plates_are_left_to_their_author() -> None:
    """Choosing which plate a tour captions is not this pass's call."""
    graph = _broken()
    graph["nodes"].extend(
        [_free_picker(98, ntype="LoadImage"), _free_picker(99, ntype="LoadImage")]
    )

    assert describe_needs_source(graph) == []
    assert wire_describe_ref(graph) == 0
    assert _slot(_only(graph, DESCRIBE_TYPE), "image")["link"] is None


def test_a_graph_with_another_source_class_is_left_alone() -> None:
    """A video loader is a source, so the graph is not this pass's scope."""
    graph = _broken()
    graph["nodes"].append(_free_picker(99, ntype="VHS_LoadVideo"))

    assert describe_needs_source(graph) == []
    assert wire_describe_ref(graph) == 0


def test_two_captioners_share_the_one_box() -> None:
    """A second captioner reuses the picker the pass just appended."""
    graph = _broken()
    first = _only(graph, DESCRIBE_TYPE)
    second = copy.deepcopy(first)
    second["id"] = int(graph["last_node_id"]) + 1
    graph["nodes"].append(second)

    assert wire_describe_ref(graph) == 4

    assert len([node for node in graph["nodes"] if node.get("type") == OPTIONAL_TYPE]) == 1
    picker = _only(graph, OPTIONAL_TYPE)
    assert sorted(picker["outputs"][0]["links"]) == sorted(
        [_slot(first, "image")["link"], _slot(second, "image")["link"]]
    )


def test_a_graph_with_no_extra_block_still_gets_its_row() -> None:
    """A graph that never declared an App still gets a valid row list."""
    graph = _broken()
    del graph["extra"]

    assert wire_describe_ref(graph) > 0

    picker_id = int(_only(graph, OPTIONAL_TYPE)["id"])
    assert _rows(graph) == [
        [picker_id, "filename", {"label": PANEL_LABEL, "description": PANEL_DESCRIPTION}],
        [
            picker_id,
            REF_TOGGLE,
            {"label": REF_TOGGLE_LABEL, "description": REF_TOGGLE_DESCRIPTION},
        ],
    ]


def test_a_broken_extra_block_is_replaced_not_crashed() -> None:
    """A junk ``extra`` is a broken graph, not a crash."""
    graph = _broken()
    graph["extra"] = "not a mapping"

    assert wire_describe_ref(graph) > 0

    extra: Any = graph["extra"]
    assert isinstance(extra, dict)
    assert isinstance(extra["linearData"]["inputs"], list)


def test_the_caption_still_stays_out_of_the_format_node() -> None:
    """The box feeds the captioner only, so Match input keeps measuring the render.

    ``EZImageFormat`` reads an optional still to pick the canvas; wiring the
    caption box into it would let a still chosen for its caption silently resize
    the deliverable.
    """
    graph = _broken()
    fmt = _only(graph, FORMAT_TYPE)
    fmt["inputs"] = [{"name": "image", "type": "IMAGE", "link": None}]

    wire_describe_ref(graph)

    assert _slot(fmt, "image")["link"] is None
    picker_id = int(_only(graph, OPTIONAL_TYPE)["id"])
    assert [row for row in _link_rows(graph, picker_id) if int(row[3]) == int(fmt["id"])] == []


def test_wire_all_writes_only_the_graph_that_changed(tmp_path: Path) -> None:
    """The file-level entrypoint leaves a converged graph byte for byte."""
    lab = tmp_path / "_lab"
    lab.mkdir(parents=True)
    broken = lab / "broken.json"
    clean = lab / "clean.json"
    broken.write_text(json.dumps(_broken(), indent=2) + "\n", encoding="utf-8")
    clean.write_text(json.dumps(_shipped(WIRED_APP), indent=2) + "\n", encoding="utf-8")
    broken_bytes, clean_bytes = broken.read_bytes(), clean.read_bytes()

    assert wire_all(tmp_path) == 1

    assert broken.read_bytes() != broken_bytes
    assert clean.read_bytes() == clean_bytes
    text = broken.read_text(encoding="utf-8")
    assert text.endswith("}\n")
    assert describe_needs_source(json.loads(text)) == []
    assert wire_all(tmp_path) == 0


def test_the_shipped_graph_behind_the_report_holds_the_invariant() -> None:
    """The graph named in GitHub issue #342 has a still behind its toggle."""
    graph = _shipped(STARVED_APP)

    assert wire_describe_ref(graph) == 0, "the shipped graph still owes a caption still"
    assert describe_needs_source(graph) == []
    assert _slot(_only(graph, DESCRIBE_TYPE), "image")["link"] is not None


def test_no_shipped_graph_is_left_without_a_source() -> None:
    """After the pass, nothing in the catalog demands a still it cannot get."""
    starved: list[str] = []
    for lab_rel, _path, graph in cached_lab_graph_rows():
        working = copy.deepcopy(graph)
        wire_describe_ref(working)
        if describe_needs_source(working):
            starved.append(lab_rel)
    assert starved == []


def test_the_shipped_catalog_needs_no_further_wiring() -> None:
    """The pass has run over the real catalog, so nothing still owes a still."""
    outstanding: list[str] = []
    for lab_rel, _path, graph in cached_lab_graph_rows():
        if wire_describe_ref(copy.deepcopy(graph)):
            outstanding.append(lab_rel)
    assert outstanding == []


def test_the_pass_names_no_source_class_the_catalog_does_not_score() -> None:
    """The pass only ever links from a class that can hand over a still."""
    graph = _broken()
    wire_describe_ref(graph)

    assert _only(graph, OPTIONAL_TYPE)["type"] in SOURCE_TYPES
    assert OPTIONAL_TYPE in SOURCE_TYPES


def test_the_stamp_writes_the_same_copy_the_pass_wired() -> None:
    """A re-stamp cannot quietly revert the caption box to reference-plate copy.

    ``stamp_app_mode`` rebuilds every App row from its own tables, so the words
    the pass puts on the box have to be the words the stamp derives from the
    node. They come from one place here, which is what makes the shipped rows
    survive the next ``stamp_app_mode`` run unchanged.
    """
    caption_box = {"type": OPTIONAL_TYPE, "title": PICKER_TITLE}
    reference_plate = {"type": OPTIONAL_TYPE, "title": "Klein plate"}

    assert display_label(caption_box, "filename") == PANEL_LABEL
    assert widget_description("filename", caption_box) == PANEL_DESCRIPTION
    assert picker_panel_copy(caption_box) == (PANEL_LABEL, PANEL_DESCRIPTION)

    plate_label, plate_text = picker_panel_copy(reference_plate)
    assert display_label(reference_plate, "filename") == plate_label
    assert widget_description("filename", reference_plate) == plate_text
    assert plate_label != PANEL_LABEL, "the two roles must not read the same"
