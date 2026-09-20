"""One-shot: wire format, upscale, and image describe across shipped lab JSON.

Run from repo root:
  python3 tests/python/_patch_lab_apps.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "tests" / "python"
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from _lab_paths import lab_graph_paths, lab_rel_of  # noqa: E402
from _wire_format import dump_wired_graph, wire_lab_graph  # noqa: E402
from _wire_image_describe import wire_image_describe  # noqa: E402
from _wire_upscale import wire_upscale  # noqa: E402


def main() -> None:
    """Patch every shipped lab graph in place."""
    skip_prefixes = ("audio/", "films/", "inspire/", "optional/")
    counts = {"format": 0, "upscale": 0, "describe": 0, "wrote": 0}
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        if any(rel.startswith(prefix) for prefix in skip_prefixes):
            continue
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            continue
        extra = graph.get("extra") or {}
        if extra.get("lab_stub") is True:
            continue
        added_fmt = wire_lab_graph(graph)
        added_up = wire_upscale(graph, rel)
        added_desc = wire_image_describe(graph)
        if added_fmt:
            counts["format"] += 1
        if added_up:
            counts["upscale"] += 1
        if added_desc:
            counts["describe"] += 1
        dump_wired_graph(path, graph)
        counts["wrote"] += 1
    print(
        "patched {wrote} graphs (format +{format}, upscale +{upscale}, "
        "describe +{describe})".format(**counts)
    )


if __name__ == "__main__":
    main()
