"""One-process auditor for shipped lab JSON (used by workflow.bats).

Hermetic: stdlib only. Walks workflows/_lab once and checks parse, id stem,
banned model needles, and estimated Vue AABB overlaps (every lane, including DCC).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

_PY = Path(__file__).resolve().parent
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

from _lab_layout import node_overlap_hits  # noqa: E402

BANNED = (
    "z_image_turbo",
    "FLUX.2-dev",
    "klein-9b",
    "flux-2-klein-9b",
    "MiniMax",
    "Seedance",
    "Kling",
)


def _overlap_hit(graph: dict[str, Any]) -> str | None:
    hits = node_overlap_hits(graph)
    if hits:
        return f"overlap {hits[0]}"
    for sub in (graph.get("definitions") or {}).get("subgraphs") or []:
        sub_hits = node_overlap_hits(sub)
        if sub_hits:
            return f"subgraph overlap {sub_hits[0]}"
    return None


def audit_lab_graphs(lab_root: Path) -> int:
    """Validate every lab JSON. Returns graph count."""
    files = sorted(path for path in lab_root.rglob("*.json") if path.is_file())
    if len(files) < 8:
        raise SystemExit(f"expected at least 8 lab graphs, found {len(files)}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        stem = os.path.splitext(path.name)[0]
        if data.get("id") != stem:
            raise SystemExit(f"{path}: id {data.get('id')!r} != {stem!r}")
        for needle in BANNED:
            if needle in text:
                raise SystemExit(f"{path}: banned {needle!r}")
        hit = _overlap_hit(data)
        if hit:
            raise SystemExit(f"{path}: {hit}")
    return len(files)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    lab = root / "workflows" / "_lab"
    count = audit_lab_graphs(lab)
    print(f"audited {count} lab graphs")


if __name__ == "__main__":
    main()
