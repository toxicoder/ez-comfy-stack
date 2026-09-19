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

# Whole-file needles (US-excluded / API / never mention in lab JSON).
BANNED_ANYWHERE = (
    "MiniMax",
    "Seedance",
    "Kling",
)
# Authored loader widgets only (opt-in NC may appear in notes/docs, never as the pin).
BANNED_LOADER = (
    "z_image_turbo",
    "FLUX.2-dev",
    "flux-2-dev",
    "flux2_dev",
    "flux2-dev",
    "klein-9b",
    "flux-2-klein-9b",
)
LOADER_TYPES = ("UNETLoader", "CLIPLoader", "VAELoader")


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
        for needle in BANNED_ANYWHERE:
            if needle in text:
                raise SystemExit(f"{path}: banned {needle!r}")
        for node in data.get("nodes") or []:
            ntype = str(node.get("type") or "")
            if ntype not in LOADER_TYPES:
                continue
            blob = " ".join(str(v) for v in (node.get("widgets_values") or []))
            lower = blob.lower()
            for needle in BANNED_LOADER:
                if needle.lower() in lower:
                    raise SystemExit(f"{path}: pinned banned loader {needle!r}")
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
