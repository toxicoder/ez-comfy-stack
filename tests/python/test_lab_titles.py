"""Gate: every node in every shipped lab graph carries a readable title.

ComfyUI draws a node's ``title`` on the canvas and falls back to the class name
when it is missing, so a graph whose samplers all read ``KSampler`` and whose
conditioning nodes all read ``LTXVConditioning`` gives the operator nothing to
aim at in the node search box or the properties panel. The companion
``_lab_wiring`` gate covers the links between nodes; this one covers what each
node is labelled.

The pass under test is ``_lab_titles.ensure_node_titles`` and the one-shot that
applies it to the shipped tree is ``_title_lab_graphs``.

Two nodes of one class in one graph also may not read the same title. That was
the bigger defect: 964 nodes across 33 shipped graphs shared a label with a
sibling of their own class, 18 ``SaveImage`` nodes all reading ``Save last
frame`` in every film graph among them, and the canvas draws the class name
plus the title, so those 18 tiles are indistinguishable.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from _lab_paths import cached_lab_graph_rows
from _lab_titles import (
    CLASS_TITLES,
    _is_pass_number,
    ensure_node_titles,
    title_for_class,
)
from _title_lab_graphs import _reset_generated_titles

MAX_TITLE_CHARS = 60

# A word is two or more letters: single letters ("x" as a size separator) and
# bare digits ("2.2" in a model name) carry no prose that can be doubled.
_WORD_RX = re.compile(r"[A-Za-z]{2,}")


def _nodes_of(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every node dict in a graph, root nodes and subgraph nodes alike.

    Args:
        graph: Comfy workflow dict.

    Returns:
        The node dicts, in document order.
    """
    nodes = [node for node in graph.get("nodes") or [] if isinstance(node, dict)]
    definitions = graph.get("definitions")
    if isinstance(definitions, dict):
        for sub in definitions.get("subgraphs") or []:
            if isinstance(sub, dict):
                nodes.extend(
                    node for node in sub.get("nodes") or [] if isinstance(node, dict)
                )
    return nodes


def _title_findings(node: dict[str, Any]) -> list[str]:
    """Return the title defects on one node.

    Args:
        node: Node dict from a lab graph.

    Returns:
        One message per defect; empty when the title reads clean.
    """
    title = node.get("title")
    if not isinstance(title, str) or not title.strip():
        return [f"node {node.get('id')} ({node.get('type')}): title is missing"]
    findings: list[str] = []
    if title.strip() != title:
        findings.append(f"node {node.get('id')}: title has stray whitespace")
    if title == node.get("type"):
        findings.append(f"node {node.get('id')}: title repeats the class name")
    words = _WORD_RX.findall(title)
    lowered = [word.lower() for word in words]
    doubled = [a for a, b in zip(lowered, lowered[1:]) if a == b]
    if doubled:
        findings.append(
            f"node {node.get('id')}: title repeats the word(s) "
            + ", ".join(sorted(set(doubled)))
            + f" in {title!r}"
        )
    if len(title) > MAX_TITLE_CHARS:
        findings.append(
            f"node {node.get('id')}: title runs {len(title)} chars, over "
            f"{MAX_TITLE_CHARS}: {title!r}"
        )
    return findings


def _is_table_sourced(title: str, bases: set[str]) -> bool:
    """Whether a title is one the title pass writes for some class.

    Args:
        title: Title text.
        bases: Every label the pass can generate in this graph.

    Returns:
        ``True`` for a label from ``CLASS_TITLES`` and for that label with a
        plain ASCII counting number on the end; an operator's own wording is
        never table-sourced, so a hand-written cross-class pair is nobody's
        defect. A leading zero means the operator wrote the number, so that is
        not table-sourced either. ``_lab_titles._is_table_sourced`` is this
        predicate, built on the same ``_is_pass_number``: it is the cross-class
        half of the duplicate rule, the half that numbers one table label two
        classes both wear, so what this gate calls a duplicate here is exactly
        what the pass renumbers. Repeats inside one class are the wider half,
        and :func:`_same_class_findings` holds that one.
    """
    if title in bases:
        return True
    stem, sep, tail = title.rpartition(" ")
    if not sep or stem not in bases:
        return False
    return _is_pass_number(tail)


def _table_sourced_findings(graph: dict[str, Any]) -> list[str]:
    """Return the generated labels one graph hands to more than one node.

    The pass takes a node's label from ``CLASS_TITLES`` (or, for a class the
    table does not carry, from a reading of its class name) and numbers a label
    a sibling already wears. Two nodes reading the same table label - three
    ``EZImageUpscale`` nodes all reading ``Upscale still`` in
    ``photos/camera-angles.json`` - is that numbering missing: the operator
    gets nothing to aim at in the node search box. This is the half of the rule
    that reaches across classes, because one table label belongs to one class;
    :func:`_same_class_findings` covers the repeats of any provenance inside
    one class.

    Args:
        graph: Comfy workflow dict.

    Returns:
        One message per title the graph repeats; empty when every generated
        label is worn by exactly one node.
    """
    nodes = _nodes_of(graph)
    bases = set(CLASS_TITLES.values())
    bases.update(title_for_class(str(node.get("type") or ""), 0, 1) for node in nodes)
    worn: dict[str, list[Any]] = {}
    for node in nodes:
        title = str(node.get("title") or "").strip()
        if title and _is_table_sourced(title, bases):
            worn.setdefault(title, []).append(node.get("id"))
    return [
        f"title {title!r} is carried by nodes " + ", ".join(str(i) for i in ids)
        for title, ids in worn.items()
        if len(ids) > 1
    ]


def _same_class_findings(graph: dict[str, Any]) -> list[str]:
    """Return the labels one graph hands to two nodes of the same class.

    The canvas draws ``title`` beside the class name, so two ``SaveImage``
    nodes both reading ``Save last frame`` - 18 of each in every shipped film
    graph - give the operator nothing to aim at in the node search box or the
    properties panel. Provenance does not matter here: a label two nodes share
    is unreadable whether the table wrote it or an operator did. Two nodes of
    *different* classes wearing one label is a different thing and is not a
    defect (see :func:`_table_sourced_findings` for the narrower rule that
    still applies to the table's own labels).

    Args:
        graph: Comfy workflow dict.

    Returns:
        One message per (class, title) pair the graph repeats; empty when every
        class reads its nodes apart.
    """
    worn: dict[tuple[str, str], list[Any]] = {}
    for node in _nodes_of(graph):
        title = str(node.get("title") or "").strip()
        if title:
            worn.setdefault((str(node.get("type") or ""), title), []).append(
                node.get("id")
            )
    return [
        "nodes " + ", ".join(str(i) for i in ids) + f" of class {cls!r} all read "
        f"{title!r}"
        for (cls, title), ids in worn.items()
        if len(ids) > 1
    ]


def _node(node_id: int, ntype: str, title: Any = None) -> dict[str, Any]:
    """Build one node dict, titled only when ``title`` is given.

    Args:
        node_id: LiteGraph node id.
        ntype: Node ``type``.
        title: Value stored under ``title``; omitted when ``None``.

    Returns:
        A node dict shaped for :func:`ensure_node_titles`.
    """
    node: dict[str, Any] = {"id": node_id, "type": ntype, "mode": 0}
    if title is not None:
        node["title"] = title
    return node


def _graph(*nodes: dict[str, Any]) -> dict[str, Any]:
    """Wrap nodes in a root-only graph dict.

    Args:
        *nodes: Node dicts for ``nodes[]``.

    Returns:
        A minimal workflow dict.
    """
    return {"id": "probe", "nodes": list(nodes)}


@pytest.mark.parametrize("lab_rel,path,graph", cached_lab_graph_rows())
def test_every_shipped_graph_titles_every_node(
    lab_rel: str,
    path: Path,
    graph: dict[str, Any],
) -> None:
    """No shipped App leaves a node reading its class name or doubling a word."""
    del path
    findings: list[str] = []
    for node in _nodes_of(graph):
        findings.extend(_title_findings(node))
    findings.extend(_table_sourced_findings(graph))
    findings.extend(_same_class_findings(graph))
    assert not findings, f"{lab_rel}: " + "; ".join(findings)


def test_a_missing_title_is_filled_from_the_class() -> None:
    """A node with no title gets the label the corpus uses for its class."""
    graph = _graph(_node(1, "VAEDecode"))
    assert ensure_node_titles(graph) == 1
    assert graph["nodes"][0]["title"] == CLASS_TITLES["VAEDecode"]


def test_a_title_equal_to_the_class_name_is_replaced() -> None:
    """A node titled with its own class name reads as untitled."""
    graph = _graph(_node(1, "LTXVConditioning", "LTXVConditioning"))
    assert ensure_node_titles(graph) == 1
    assert graph["nodes"][0]["title"] == CLASS_TITLES["LTXVConditioning"]


def test_a_doubled_word_is_collapsed_once() -> None:
    """The ``Negative Negative ...`` prefix the wiring pass wrote is halved."""
    graph = _graph(_node(1, "EZNegativePromptEnhance", "Negative Negative SHOT CLOSE"))
    assert ensure_node_titles(graph) == 1
    assert graph["nodes"][0]["title"] == "Negative SHOT CLOSE"
    assert not _title_findings(graph["nodes"][0])


def test_a_human_title_is_never_rewritten() -> None:
    """Existing operator-facing labels survive the pass untouched."""
    kept = [
        _node(1, "SaveAudio", "Save stem mix (host stem-mix.sh)"),
        _node(2, "UNETLoader", "Wan 2.2 TI2V-5B"),
        _node(3, "Wan22ImageToVideoLatent", "I2V size 832x480 x 121"),
        _node(4, "KSampler", "Sampler CLOSE"),
        _node(5, "KSampler", "ACE sampler (pass 2)"),
        _node(6, "Note", "Operator note"),
    ]
    before = [dict(node) for node in kept]
    assert ensure_node_titles(_graph(*kept)) == 0
    assert kept == before


def test_one_sampler_reads_sampler_and_several_are_numbered() -> None:
    """Samplers follow the corpus rule: one is ``Sampler``, N are ``Sampler n``."""
    single = _graph(_node(7, "KSampler", "KSampler"))
    ensure_node_titles(single)
    assert single["nodes"][0]["title"] == "Sampler"

    many = _graph(
        _node(34, "KSampler", "KSampler"),
        _node(7, "KSampler", "KSampler"),
        _node(20, "KSampler", "Sampler packshot"),
        _node(27, "KSampler", "KSampler"),
    )
    ensure_node_titles(many)
    by_id = {node["id"]: node["title"] for node in many["nodes"]}
    assert by_id == {
        7: "Sampler 1",
        20: "Sampler packshot",
        27: "Sampler 2",
        34: "Sampler 3",
    }


def test_the_pass_is_idempotent() -> None:
    """A second pass over a titled graph changes nothing."""
    graph = _graph(
        _node(1, "VAEDecode"),
        _node(2, "KSampler", "KSampler"),
        _node(3, "EZNegativePromptEnhance", "Negative Negative SHOT WIDE"),
    )
    assert ensure_node_titles(graph) == 3
    assert ensure_node_titles(graph) == 0


def test_the_pass_walks_subgraph_nodes() -> None:
    """Nodes inside ``definitions.subgraphs[]`` are titled too."""
    graph: dict[str, Any] = {
        "id": "probe",
        "nodes": [_node(1, "VAEDecode")],
        "definitions": {"subgraphs": [{"nodes": [_node(2, "LTXVConditioning")]}]},
    }
    assert ensure_node_titles(graph) == 2
    assert graph["nodes"][0]["title"] == CLASS_TITLES["VAEDecode"]
    assert (
        graph["definitions"]["subgraphs"][0]["nodes"][0]["title"]
        == (CLASS_TITLES["LTXVConditioning"])
    )


def test_a_returned_count_only_covers_changed_titles() -> None:
    """The count is the number of nodes whose title actually moved."""
    graph = _graph(_node(1, "Note", "Operator note"), _node(2, "EZModelCheck"))
    assert ensure_node_titles(graph) == 1


def test_repeated_generated_titles_are_numbered() -> None:
    """Three untitled nodes of one class read ``X`` / ``X 2`` / ``X 3``."""
    graph = _graph(
        _node(1, "EZImageUpscale"),
        _node(2, "EZImageUpscale", "EZImageUpscale"),
        _node(3, "EZImageUpscale"),
    )
    assert ensure_node_titles(graph) == 3
    titles = [node["title"] for node in graph["nodes"]]
    assert titles == ["Upscale still", "Upscale still 2", "Upscale still 3"]
    assert not _table_sourced_findings(graph)


def test_a_generated_title_yields_to_an_authored_one() -> None:
    """The untitled nodes number clear of both labels the operator wrote."""
    graph = _graph(
        _node(1, "EZImageUpscale", "Upscale still"),
        _node(2, "EZImageUpscale"),
        _node(3, "EZImageUpscale", "Upscale still 2"),
        _node(4, "EZImageUpscale"),
    )
    assert ensure_node_titles(graph) == 2
    titles = [node["title"] for node in graph["nodes"]]
    assert titles == [
        "Upscale still",
        "Upscale still 3",
        "Upscale still 2",
        "Upscale still 4",
    ]
    assert not _table_sourced_findings(graph)


def test_generated_titles_stay_unique_across_subgraphs() -> None:
    """A root node and a subgraph node of one class do not read the same."""
    graph: dict[str, Any] = {
        "id": "probe",
        "nodes": [_node(1, "VAEDecode")],
        "definitions": {"subgraphs": [{"nodes": [_node(2, "VAEDecode")]}]},
    }
    assert ensure_node_titles(graph) == 2
    assert [node["title"] for node in _nodes_of(graph)] == [
        "VAE Decode",
        "VAE Decode 2",
    ]
    assert not _table_sourced_findings(graph)


def test_an_authored_table_label_is_numbered_after_its_sibling() -> None:
    """Four nodes that arrive wearing ``Upscale still`` rebuild as 1..4.

    ``_wire_upscale`` stamps ``Upscale still`` on every node it inserts, so a
    builder graph with four of them hands the pass the table's own label four
    times and the pass is the only place that sees all four.
    """
    graph = _graph(
        *[
            _node(node_id, "EZImageUpscale", "Upscale still")
            for node_id in (35, 36, 37, 38)
        ]
    )
    assert ensure_node_titles(graph) == 3
    titles = [str(node["title"]) for node in graph["nodes"]]
    assert titles == [
        "Upscale still",
        "Upscale still 2",
        "Upscale still 3",
        "Upscale still 4",
    ]
    assert not _table_sourced_findings(graph)


def test_authored_duplicates_number_in_node_id_order() -> None:
    """The numbering follows the node id, not where the node sits in the file."""
    graph = _graph(
        _node(37, "EZImageUpscale", "Upscale still"),
        _node(35, "EZImageUpscale", "Upscale still"),
        _node(36, "EZImageUpscale", "Upscale still"),
    )
    assert ensure_node_titles(graph) == 2
    assert {node["id"]: node["title"] for node in graph["nodes"]} == {
        35: "Upscale still",
        36: "Upscale still 2",
        37: "Upscale still 3",
    }


def test_a_hand_written_duplicate_on_two_classes_is_left_alone() -> None:
    """The ``Negative SHOT WIDE`` pair two shot rows share is prose, not the table."""
    graph = _graph(
        _node(1, "EZNegativePromptEnhance", "Negative SHOT WIDE"),
        _node(2, "CLIPTextEncode", "Negative SHOT WIDE"),
        _node(3, "Note", "Handoff to wrap"),
        _node(4, "MarkdownNote", "Handoff to wrap"),
    )
    before = [dict(node) for node in graph["nodes"]]
    assert ensure_node_titles(graph) == 0
    assert graph["nodes"] == before
    assert not _table_sourced_findings(graph)
    assert not _same_class_findings(graph)


def test_the_gate_flags_a_repeated_generated_title() -> None:
    """The defect this gate exists for: two nodes wearing one table label."""
    graph = _graph(
        _node(9, "EZImageUpscale", "Upscale still"),
        _node(11, "EZImageUpscale", "Upscale still"),
    )
    findings = _table_sourced_findings(graph)
    assert findings == ["title 'Upscale still' is carried by nodes 9, 11"]


def test_the_reset_only_blanks_titles_the_pass_could_have_written() -> None:
    """The one-shot re-derives its own labels and leaves the operator's alone.

    ``Sampler 01``..``Sampler 06`` is vocabulary the corpus ships with and the
    pass numbers with ``str(int)``, so a leading zero marks a title that is not
    the pass's and must survive every re-run untouched.
    """
    graph = _graph(
        _node(1, "KSampler", "Sampler 01"),
        _node(2, "KSampler", "Sampler 02"),
        _node(3, "KSampler", "Sampler 2"),
        _node(4, "EZImageUpscale", "Upscale still"),
        _node(5, "KSampler", "Sampler CLOSE"),
    )
    authored = ["Sampler 01", "Sampler 02", "Sampler CLOSE"]

    _reset_generated_titles(graph)
    assert [node["title"] for node in graph["nodes"]] == [
        "Sampler 01",
        "Sampler 02",
        "",
        "",
        "Sampler CLOSE",
    ]
    assert ensure_node_titles(graph) == 2
    titles = [str(node["title"]) for node in graph["nodes"]]
    assert titles == [
        "Sampler 01",
        "Sampler 02",
        "Sampler 1",
        "Upscale still",
        "Sampler CLOSE",
    ]
    assert not _table_sourced_findings(graph)

    _reset_generated_titles(graph)
    assert [node["title"] for node in graph["nodes"]][:2] == authored[:2]
    assert [node["title"] for node in graph["nodes"]][4] == authored[2]
    assert ensure_node_titles(graph) == 2
    assert [str(node["title"]) for node in graph["nodes"]] == titles


def test_the_gate_leaves_a_cross_class_untabled_twin_alone() -> None:
    """A hand-written label two operators happened to pick on two classes is clean."""
    graph = _graph(
        _node(1, "Note", "Handoff to wrap"),
        _node(2, "MarkdownNote", "Handoff to wrap"),
    )
    assert not _table_sourced_findings(graph)
    assert not _same_class_findings(graph)


def test_the_gate_flags_two_nodes_of_one_class_reading_one_title() -> None:
    """The canvas defect: two ``SaveImage`` nodes both reading ``Save last frame``."""
    graph = _graph(
        _node(41, "SaveImage", "Save last frame"),
        _node(42, "SaveImage", "Save last frame"),
    )
    assert _same_class_findings(graph) == [
        "nodes 41, 42 of class 'SaveImage' all read 'Save last frame'"
    ]


def test_two_nodes_of_one_class_wearing_one_authored_title_are_numbered() -> None:
    """``Save last frame`` is nobody's table label, and it still gets numbered."""
    graph = _graph(
        _node(41, "SaveImage", "Save last frame"),
        _node(42, "SaveImage", "Save last frame"),
        _node(43, "SaveImage", "Save last frame"),
    )
    assert ensure_node_titles(graph) == 2
    titles = [str(node["title"]) for node in graph["nodes"]]
    assert titles == ["Save last frame", "Save last frame 2", "Save last frame 3"]
    assert not _same_class_findings(graph)
    assert not _table_sourced_findings(graph)


def test_authored_numbering_survives_a_second_pass() -> None:
    """Re-running never stacks a number onto the number it wrote."""
    graph = _graph(
        _node(1, "SaveImage", "Save last frame"),
        _node(2, "SaveImage", "Save last frame"),
        _node(3, "SaveImage", "Save last frame"),
    )
    assert ensure_node_titles(graph) == 2
    first = [str(node["title"]) for node in graph["nodes"]]
    assert ensure_node_titles(graph) == 0
    assert [str(node["title"]) for node in graph["nodes"]] == first
    assert first == ["Save last frame", "Save last frame 2", "Save last frame 3"]


def test_cross_class_twins_sharing_a_word_stay_untouched() -> None:
    """Two classes that both read ``Negative SHOT WIDE`` are by design."""
    graph = _graph(
        _node(1, "CLIPTextEncode", "Negative SHOT WIDE"),
        _node(2, "EZNegativePromptEnhance", "Negative SHOT WIDE"),
        _node(3, "CLIPTextEncode", "Positive SHOT WIDE"),
    )
    before = [dict(node) for node in graph["nodes"]]
    assert ensure_node_titles(graph) == 0
    assert graph["nodes"] == before


def test_a_lone_node_keeps_its_authored_title_verbatim() -> None:
    """A singleton is nobody's duplicate: the pass does not so much as strip it."""
    graph = _graph(
        _node(9, "VHS_VideoCombine", "Save video (MP4) - open node for preview")
    )
    assert ensure_node_titles(graph) == 0
    assert graph["nodes"][0]["title"] == "Save video (MP4) - open node for preview"


def test_a_generated_title_never_repeats_the_class_or_a_word() -> None:
    """Whatever the pass invents still has to satisfy the gate."""
    for node_type in list(CLASS_TITLES) + [
        "KSampler",
        "",
        "Node",
        "WeirdWeird",
        "Very" + "Long" * 14 + "Class",
    ]:
        for index, total in ((0, 1), (2, 4)):
            title = title_for_class(node_type, index, total)
            findings = _title_findings({"id": 1, "type": node_type, "title": title})
            assert not findings, (
                f"{node_type!r} index={index} total={total}: {findings}"
            )


def test_every_seeded_class_title_reads_clean() -> None:
    """``CLASS_TITLES`` was mined from the corpus, not invented, and is valid."""
    assert CLASS_TITLES, "the seed dict must be mined from the shipped corpus"
    for node_type, title in CLASS_TITLES.items():
        assert title.strip() == title, f"{node_type}: seeded title has stray whitespace"
        assert not _title_findings({"id": 1, "type": node_type, "title": title}), (
            node_type
        )
        assert title_for_class(node_type, 0, 1) == title
