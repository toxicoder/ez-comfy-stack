"""One-shot: give every node in every shipped lab graph a human title.

Not imported by pytest collection (leading underscore). Run from repo root:
  python3 tests/python/_title_lab_graphs.py

It walks every ``*.json`` under ``workflows/_lab``, applies
``_lab_titles.ensure_node_titles``, and rewrites only the files whose text
actually moved. The serialization is the one ``_lab_paths.write_lab_graph``
uses, so an untouched graph comes back byte-identical and a touched graph moves
nothing but its titles.

A title the pass wrote is not "needs setting" any more, so the pass alone can
never renumber one. Each run therefore first blanks every title that reads like
one the pass wrote - the label ``title_for_class`` gives the class, or that
label with a number on the end - and lets the pass re-derive the whole set from
scratch, which is what renumbers a title that collides with a sibling. The run
is still idempotent: the second pass derives the same titles, the text matches,
and nothing is written.

A label the operator wrote is never blanked here. The pass numbers a repeat of
one inside a single class on its own, so 18 ``SaveImage`` nodes all authored
``Save last frame`` come back ``Save last frame`` .. ``Save last frame 18`` and
read the same on every later run.

The walk is its own ``rglob`` rather than ``_lab_paths.lab_graph_paths`` so the
one-shot needs nothing beyond the stdlib and ``_lab_titles`` to run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _lab_titles import authored_number_widths, ensure_node_titles
from _lab_titles import title_for_class

ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = ROOT / "workflows" / "_lab"


def _load(path: Path) -> dict[str, object] | None:
    """Parse one graph file.

    Arguments:
        path: Lab graph JSON.
    Returns:
        The graph dict, or ``None`` when the file holds something other than an
        object (which the caller reports rather than rewrites).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _nodes_of(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every node dict in a graph, root nodes and subgraph nodes alike.

    Walked here rather than through ``_lab_titles._iter_nodes`` so the one-shot
    leans on the package's pinned surface only.

    Arguments:
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


def _is_generated_title(title: str, node_type: str, widths: frozenset[int]) -> bool:
    """Whether a title is one the title pass wrote rather than an operator typed.

    Blanking a title is the one way a re-run can renumber a node, so the two
    sides of this have to agree with ``_lab_titles._is_table_sourced``: what
    this blanks, the pass re-derives.

    Arguments:
        title: The title a node carries, already stripped.
        node_type: Node ``type``.
        widths: The padded digit widths this node's generated label wears,
            from ``authored_number_widths``.
    Returns:
        ``True`` for the label ``title_for_class`` gives this class and for that
        label with a plain ASCII counting number on the end, which is everything
        a re-run has to recompute to stay collision-free. A leading zero is the
        operator's numbering (the corpus ships ``Sampler 01``..``Sampler 06``),
        never the pass's, and so is any number at the width that padded run
        uses - blanking ``Sampler 10`` beside ``Sampler 09`` would re-derive it
        as ``Sampler 1``. With a padded run present, even the bare label is the
        operator's: the pass only writes that for a class with one node.
    """
    base = title_for_class(node_type, 0, 1)
    if title == base:
        return not widths
    prefix = f"{base} "
    tail = title[len(prefix) :] if title.startswith(prefix) else ""
    return (
        tail.isdigit()
        and tail.isascii()
        and not tail.startswith("0")
        and len(tail) not in widths
    )


def _reset_generated_titles(graph: dict[str, object]) -> None:
    """Blank every title the pass could have written so the pass rewrites it.

    Blanking in place, rather than dropping the key, keeps each node's JSON key
    order, so the diff a re-run leaves behind stays on the title lines.

    Arguments:
        graph: Comfy workflow dict (mutated).
    """
    nodes = _nodes_of(graph)
    widths = authored_number_widths(nodes)
    for node in nodes:
        raw = node.get("title")
        title = raw.strip() if isinstance(raw, str) else ""
        if not title:
            continue
        node_type = str(node.get("type") or "")
        run_widths = widths.get(title_for_class(node_type, 0, 1), frozenset())
        if _is_generated_title(title, node_type, run_widths):
            node["title"] = ""


def main() -> int:
    """Title every untitled node across the shipped lab tree.

    Returns:
        ``0``, or ``1`` when a graph did not parse to an object.
    """
    paths = sorted(path for path in LAB_ROOT.rglob("*.json") if path.is_file())
    rewritten = 0
    retitled = 0
    for path in paths:
        graph = _load(path)
        if graph is None:
            print(f"not a JSON object, left alone: {path}", file=sys.stderr)
            return 1
        _reset_generated_titles(graph)
        changed = ensure_node_titles(graph)
        if not changed:
            continue
        text = json.dumps(graph, indent=2) + "\n"
        if text == path.read_text(encoding="utf-8"):
            continue
        path.write_text(text, encoding="utf-8")
        rewritten += 1
        retitled += changed
    print(f"titled {retitled} nodes across {rewritten} of {len(paths)} lab graphs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
