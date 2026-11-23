"""One-shot: give every node in every shipped lab graph a human title.

Not imported by pytest collection (leading underscore). Run from repo root:
  python3 tests/python/_title_lab_graphs.py

It walks every ``*.json`` under ``workflows/_lab``, applies
``_lab_titles.ensure_node_titles``, and rewrites only the files whose text
actually moved. The serialization is the one ``_lab_paths.write_lab_graph``
uses, so an untouched graph comes back byte-identical and a touched graph moves
nothing but its titles. The pass is idempotent: the second run sets nothing and
rewrites nothing.

The walk is its own ``rglob`` rather than ``_lab_paths.lab_graph_paths`` so the
one-shot needs nothing beyond the stdlib and ``_lab_titles`` to run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_titles import ensure_node_titles

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
