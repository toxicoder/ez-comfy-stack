"""Gate: every node in every shipped lab graph carries a readable title.

ComfyUI draws a node's ``title`` on the canvas and falls back to the class name
when it is missing, so a graph whose samplers all read ``KSampler`` and whose
conditioning nodes all read ``LTXVConditioning`` gives the operator nothing to
aim at in the node search box or the properties panel. The companion
``_lab_wiring`` gate covers the links between nodes; this one covers what each
node is labelled.

The pass under test is ``_lab_titles.ensure_node_titles`` and the one-shot that
applies it to the shipped tree is ``_title_lab_graphs``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from _lab_paths import cached_lab_graph_rows
from _lab_titles import CLASS_TITLES, ensure_node_titles, title_for_class

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
