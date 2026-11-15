"""Tests for the NVIDIA lab tier graphs the generator emits.

Hermetic: reads the committed catalog and the JSON under
``workflows/_lab/labs/nvidia``, and re-runs the generator into the working tree
to prove it is byte-stable. No Comfy, Docker, network, or GPU.

The catalog is the contract these graphs answer to: one graph per row, the row's
own ``nodes`` list on the canvas, ``occupancy="none"`` on every App, the one
unwired ``EZModelCheck`` every lab graph carries, the
``extra.lab_optional_unwired`` declaration that makes the informational cards
legal isolates, and the lab identity keys the auditor and the sidebar read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import nvidia_lab  # noqa: E402

from _build_nvidia_lab_apps import build_graph, emit  # noqa: E402
from _lab_layout import (  # noqa: E402
    LAB_NODE_Y0,
    LAB_X0,
    group_overlap_hits,
    node_overlap_hits,
    operator_note,
    node_pos,
    title_inset_hits,
)
from _lab_paths import WORKFLOW_RENDERER_VERSION  # noqa: E402
from _nvidia_lab_specs import (  # noqa: E402
    CATALOG_TYPE,
    JOB_TYPE,
    LANE,
    NOTE_TYPE,
    OCCUPANCY,
    PREFLIGHT_TYPE,
    TIER_DETAIL_LABEL,
    VERDICT_TYPE,
    optional_unwired_for,
    spec_for,
)
from _wire_model_check import (  # noqa: E402
    CHECK_DEFAULT,
    CHECK_TITLE,
    CHECK_TYPE,
    CHECK_WIDGET,
)

REAL_CATALOG = ROOT / nvidia_lab.CATALOG_RELPATH
TIER_DIR = ROOT / "workflows" / "_lab" / "labs" / "nvidia"
CARD_TYPES = (PREFLIGHT_TYPE, VERDICT_TYPE, JOB_TYPE)
TERMINAL_TYPES = frozenset({CATALOG_TYPE, VERDICT_TYPE})

CATALOG = nvidia_lab.load_catalog(REAL_CATALOG)
ROWS: list[tuple[str, nvidia_lab.Tool]] = [
    (tool.id, tool) for tool in CATALOG.tools
]
ROW_IDS: list[str] = [tool.id for tool in CATALOG.tools]
PARAM = "tool_id,tool"


def _graph_of(tool: nvidia_lab.Tool) -> dict[str, Any]:
    """Load the shipped graph for one catalog row.

    Args:
        tool: The catalog row.

    Returns:
        The parsed graph dict.

    Raises:
        FileNotFoundError: the row has no graph on disk.
    """
    path = TIER_DIR / f"{tool.id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"{tool.id}: no graph at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{tool.id}: graph is not a JSON object"
    return data


def _nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a graph's node rows.

    Args:
        graph: Parsed graph.

    Returns:
        The node dicts.
    """
    return [node for node in (graph.get("nodes") or []) if isinstance(node, dict)]


def _node_of_type(graph: dict[str, Any], ntype: str) -> dict[str, Any]:
    """Return the single node of one class.

    Args:
        graph: Parsed graph.
        ntype: ``class_type`` to find.

    Returns:
        The node row.

    Raises:
        AssertionError: the class appears zero or several times.
    """
    hits = [node for node in _nodes(graph) if str(node.get("type") or "") == ntype]
    assert len(hits) == 1, f"{ntype}: expected one node, found {len(hits)}"
    return hits[0]


def _node_of_id(graph: dict[str, Any], node_id: int) -> dict[str, Any]:
    """Return the node with one id.

    Args:
        graph: Parsed graph.
        node_id: LiteGraph node id.

    Returns:
        The node row.

    Raises:
        AssertionError: the id is absent or duplicated.
    """
    hits = [node for node in _nodes(graph) if int(node["id"]) == node_id]
    assert len(hits) == 1, f"node {node_id}: expected one, found {len(hits)}"
    return hits[0]


def _widgets(graph: dict[str, Any], ntype: str) -> list[Any]:
    """Return one node class's stored widget values.

    Args:
        graph: Parsed graph.
        ntype: ``class_type`` to read.

    Returns:
        The ``widgets_values`` list.
    """
    values = _node_of_type(graph, ntype).get("widgets_values")
    assert isinstance(values, list), f"{ntype}: widgets_values is not a list"
    return values


def test_the_tier_dir_holds_exactly_one_graph_per_row() -> None:
    """No row is missing a graph and no graph sits outside the catalog."""
    assert CATALOG.tier == "nvidia-lab"
    assert CATALOG.schema == nvidia_lab.CATALOG_SCHEMA
    on_disk = sorted(path.stem for path in TIER_DIR.glob("*.json"))
    assert on_disk == sorted(ROW_IDS), "one graph per catalog row, none extra"
    assert len(on_disk) == len(CATALOG.tools) == 18


def test_the_graph_paths_follow_the_catalog_graph_field() -> None:
    """Each row's ``graph`` id is the file the generator writes.

    The catalog pins ``labs/nvidia/<id>``; a row whose field drifted would leave
    App Forge and the docs pointing at a file that does not exist.
    """
    for tool in CATALOG.tools:
        assert tool.graph == f"labs/nvidia/{tool.id}", tool.id
        assert (ROOT / "workflows" / "_lab" / f"{tool.graph}.json").is_file()


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_the_canvas_carries_the_rows_node_set(
    tool_id: str, tool: nvidia_lab.Tool
) -> None:
    """The canvas nodes are the row's list plus the note, cards, table, check.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    types = {str(node.get("type") or "") for node in _nodes(_graph_of(tool))}
    expected = {NOTE_TYPE, PREFLIGHT_TYPE, CATALOG_TYPE, CHECK_TYPE, *tool.nodes}
    assert types == expected, tool_id
    assert (JOB_TYPE in types) is (JOB_TYPE in tool.nodes), tool_id
    assert (VERDICT_TYPE in types) is (VERDICT_TYPE in tool.nodes), tool_id
    assert len(_nodes(_graph_of(tool))) == len(types), f"{tool_id}: class repeated"


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_the_widgets_are_pinned_to_the_row(tool_id: str, tool: nvidia_lab.Tool) -> None:
    """Every card names its own row, and the table opens on the tier view.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    graph = _graph_of(tool)
    present = {str(node.get("type") or "") for node in _nodes(graph)}
    for card in CARD_TYPES:
        if card in present:
            assert _widgets(graph, card)[0] == tool.id, f"{tool_id}: {card} tool_id"
    assert _widgets(graph, CATALOG_TYPE)[0] in {"table", "list"}, tool_id
    if JOB_TYPE in present:
        values = _widgets(graph, JOB_TYPE)
        assert len(values) == 3, tool_id
        assert values[1] == "", f"{tool_id}: input_path is the operator's to type"
        assert json.loads(str(values[2])) == {}, f"{tool_id}: params_json"


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_every_app_claims_no_occupancy(tool_id: str, tool: nvidia_lab.Tool) -> None:
    """This tier's GPU work runs outside Comfy, so no App holds the card.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    extra = _graph_of(tool).get("extra") or {}
    mode = extra.get("lab_app_mode")
    assert isinstance(mode, dict), f"{tool_id}: not stamped as an App"
    assert mode.get("enabled") is True, tool_id
    assert mode.get("occupancy") == OCCUPANCY, tool_id
    assert mode.get("lane") == LANE, tool_id
    assert mode.get("default_view") == "app", tool_id
    assert list(mode.get("handoff") or []) == [], f"{tool_id}: no handoff in this tier"
    assert f"Occupancy: {OCCUPANCY} -" in str(extra.get("lab_note") or ""), tool_id


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_the_app_panel_lists_the_tier_table(tool_id: str, tool: nvidia_lab.Tool) -> None:
    """``linearData.outputs`` carries the table, and only real output cards.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    graph = _graph_of(tool)
    linear = (_graph_of(tool).get("extra") or {}).get("linearData")
    assert isinstance(linear, dict), f"{tool_id}: no linearData"
    ids = {int(node["id"]) for node in _nodes(graph)}
    outputs = [int(entry) for entry in linear.get("outputs") or []]
    expected = {int(_node_of_type(graph, CATALOG_TYPE)["id"])}
    if VERDICT_TYPE in tool.nodes:
        expected.add(int(_node_of_type(graph, VERDICT_TYPE)["id"]))
    assert set(outputs) == expected, tool_id
    assert set(outputs) <= ids, f"{tool_id}: an output names no node"
    for node_id in outputs:
        assert str(_node_of_id(graph, node_id).get("type") or "") in TERMINAL_TYPES, (
            f"{tool_id}: output {node_id} is not an OUTPUT_NODE card"
        )
    labels: list[str] = []
    for entry in linear.get("inputs") or []:
        assert isinstance(entry, list) and len(entry) >= 3, f"{tool_id}: {entry!r}"
        node = _node_of_id(graph, int(entry[0]))
        assert str(node.get("type") or "") in TERMINAL_TYPES, (
            f"{tool_id}: an App row sits on {node.get('type')}, which reports "
            "into nothing, so the control would change nothing"
        )
        config = entry[2]
        assert isinstance(config, dict), f"{tool_id}: row config is not a map"
        label = str(config.get("label") or "").strip()
        assert label, f"{tool_id}: row has no label"
        assert str(config.get("description") or "").strip(), f"{tool_id}: row help"
        labels.append(label)
    assert labels == [TIER_DETAIL_LABEL] or TIER_DETAIL_LABEL in labels, tool_id
    assert len(labels) == len(set(labels)), f"{tool_id}: duplicate App labels"


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_every_graph_carries_the_lab_identity(
    tool_id: str, tool: nvidia_lab.Tool
) -> None:
    """The identity keys the auditor and the sidebar read are all present.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    graph = _graph_of(tool)
    extra = graph.get("extra") or {}
    assert graph.get("id") == tool_id, tool_id
    assert extra.get("lab_rel") == f"labs/nvidia/{tool_id}", tool_id
    assert extra.get("lab_profile") == f"labs/nvidia/{tool_id}", tool_id
    assert extra.get("workflowRendererVersion") == WORKFLOW_RENDERER_VERSION, tool_id
    assert str(extra.get("lab_description") or "").strip(), f"{tool_id}: no description"
    note = str(extra.get("lab_note") or "")
    assert note.strip(), f"{tool_id}: no note"
    assert tool.title in note, f"{tool_id}: the note never names the tool"
    assert tool.verify in note, f"{tool_id}: the note drops the verify line"
    card = operator_note(graph)
    assert card is not None, f"{tool_id}: no operator note"
    assert node_pos(card) == (float(LAB_X0), float(LAB_NODE_Y0)), tool_id
    assert card.get("title") == "Operator note", tool_id
    assert card.get("widgets_values") == [note], (
        f"{tool_id}: the canvas note and extra.lab_note differ"
    )
    titles = {str(group.get("title") or "") for group in graph.get("groups") or []}
    assert "NOTE" in titles, f"{tool_id}: {sorted(titles)}"


@pytest.mark.parametrize("tool_id", ROW_IDS)
def test_every_graph_carries_one_unwired_model_check_node(tool_id: str) -> None:
    """Each card graph holds the disk check the operator clicks before Queue.

    Every row in this tier needs weights on disk, so the auditor's one
    ``EZModelCheck`` per lab graph applies here too: exactly one, unwired, and
    off the App panel, where its status widget would be a control the graph
    never reads.

    Args:
        tool_id: Catalog row id.
    """
    graph = _graph_of(nvidia_lab.tool_by_id(CATALOG, tool_id))
    hits = [
        node for node in _nodes(graph) if str(node.get("type") or "") == CHECK_TYPE
    ]
    assert len(hits) == 1, f"{tool_id}: expected one {CHECK_TYPE} node"
    check = hits[0]
    assert check.get("title") == CHECK_TITLE, tool_id
    assert check.get("widgets_values") == [CHECK_DEFAULT], tool_id
    assert check.get("inputs") == [], f"{tool_id}: the check takes no input"
    assert check.get("outputs") == [], f"{tool_id}: the check feeds nothing"
    linear = (graph.get("extra") or {}).get("linearData") or {}
    outputs = {int(entry) for entry in linear.get("outputs") or []}
    assert int(check["id"]) not in outputs, f"{tool_id}: the check is no deliverable"
    names = [
        str(entry[1])
        for entry in (linear.get("inputs") or [])
        if isinstance(entry, (list, tuple)) and len(entry) > 1
    ]
    assert CHECK_WIDGET not in names, f"{tool_id}: the check is no App control"


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_every_card_is_a_declared_unwired_opt_in(
    tool_id: str, tool: nvidia_lab.Tool
) -> None:
    """The auditor's isolate rule is met by a declaration, not an exemption.

    Every card here is a terminal informational ``OUTPUT_NODE``: it prints into
    the Queue log and offers no socket another node could read, so nothing on
    these graphs is wired to anything. The completeness auditor allows an unwired
    node only when it is a note, a quality picker, the disk check, or a class the
    graph names in ``extra.lab_optional_unwired`` - so that list is the whole
    contract, and it has to name exactly the cards the canvas carries.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    graph = _graph_of(tool)
    declared = (graph.get("extra") or {}).get("lab_optional_unwired")
    assert isinstance(declared, list), f"{tool_id}: no declared unwired cards"
    assert declared == list(
        optional_unwired_for(spec_for(CATALOG, tool).node_types)
    ), tool_id
    chrome = {NOTE_TYPE, CHECK_TYPE}
    on_canvas = {
        str(node.get("type") or "")
        for node in _nodes(graph)
        if str(node.get("type") or "") not in chrome
    }
    assert set(declared) == on_canvas, (
        f"{tool_id}: the declaration is not the canvas's card set"
    )


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_no_node_or_group_rectangles_overlap(
    tool_id: str, tool: nvidia_lab.Tool
) -> None:
    """The auditor's AABB check passes on this lane like every other one.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    graph = _graph_of(tool)
    assert node_overlap_hits(graph) == [], tool_id
    assert group_overlap_hits(graph) == [], tool_id
    assert title_inset_hits(graph) == [], tool_id


@pytest.mark.parametrize(PARAM, ROWS, ids=ROW_IDS)
def test_the_graph_is_unlinked_and_ascii_only(
    tool_id: str, tool: nvidia_lab.Tool
) -> None:
    """Nothing links to nothing, and no confusable punctuation ships.

    Args:
        tool_id: Catalog row id.
        tool: The catalog row.
    """
    path = TIER_DIR / f"{tool_id}.json"
    graph = json.loads(path.read_text(encoding="utf-8"))
    assert graph.get("links") == [], f"{tool_id}: this tier wires nothing"
    assert graph.get("last_link_id") == 0, tool_id
    nodes = _nodes(graph)
    assert graph.get("last_node_id") == len(nodes), tool_id
    assert max(int(node["id"]) for node in nodes) == len(nodes), tool_id
    for node in nodes:
        assert node.get("inputs") == [], f"{tool_id}: these cards have no sockets"
        assert int(node.get("mode") or 0) == 0, f"{tool_id}: a node is muted"
        for slot in node.get("outputs") or []:
            assert slot.get("links") == [], f"{tool_id}: dangling output link"
    assert all(byte < 128 for byte in path.read_bytes()), (
        f"{tool_id}: non-ASCII byte in the graph"
    )


def test_re_running_the_generator_writes_identical_bytes() -> None:
    """The generator is a pure function of the catalog, so a re-run is a no-op.

    ``emit`` is the call ``main`` makes, so the text it returns after writing is
    what a second ``python3 tests/python/_build_nvidia_lab_apps.py`` puts on
    disk, and it must match what was already there byte for byte.
    """
    before = {path.name: path.read_bytes() for path in TIER_DIR.glob("*.json")}
    assert before, "the tier was never emitted"
    written = {path.name: text.encode("utf-8") for path, text in emit(CATALOG)}
    assert set(written) == set(before)
    for name in sorted(before):
        assert written[name] == before[name], f"{name}: a re-run changed bytes"


def test_build_graph_is_deterministic_off_disk() -> None:
    """Two builds of the same row serialize the same JSON.

    A dict built from an unsorted set or a timestamp would shuffle on every
    regeneration and turn a no-op re-run into a whole-tier diff.
    """
    for tool in CATALOG.tools:
        first = json.dumps(build_graph(CATALOG, tool), indent=2) + "\n"
        second = json.dumps(build_graph(CATALOG, tool), indent=2) + "\n"
        assert first == second, tool.id
        on_disk = (TIER_DIR / f"{tool.id}.json").read_text(encoding="utf-8")
        assert first == on_disk, f"{tool.id}: the file drifted from the generator"


def test_the_generator_refuses_a_job_card_on_a_blocked_row(tmp_path: Path) -> None:
    """A row that is not opt-in cannot ask for the CLI job card.

    Args:
        tmp_path: Scratch directory for the doctored catalog.
    """
    doc = json.loads(REAL_CATALOG.read_text(encoding="utf-8"))
    row = next(tool for tool in doc["tools"] if tool["status"] != "opt-in")
    row["nodes"] = [PREFLIGHT_TYPE, JOB_TYPE]
    fixture = tmp_path / "catalog.json"
    fixture.write_text(json.dumps(doc), encoding="utf-8")
    tampered = nvidia_lab.load_catalog(fixture)
    with pytest.raises(ValueError, match="reserved for opt-in"):
        build_graph(tampered, nvidia_lab.tool_by_id(tampered, row["id"]))
