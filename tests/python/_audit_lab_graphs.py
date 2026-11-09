"""One-process auditor for shipped lab JSON (used by workflow.bats).

Hermetic: stdlib only. Walks workflows/_lab once and checks parse, id stem,
banned model needles, the one-model-stack-per-App rule, and estimated Vue AABB
overlaps (every lane, including DCC).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_PY = Path(__file__).resolve().parent
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

from _lab_families import stack_violations  # noqa: E402
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

# Lanes that a note may name as a graph. Anything outside this set is prose in
# bold, so a bolded word never trips the reference check.
LANE_WORDS = (
    "photos",
    "video",
    "social",
    "business",
    "film",
    "audio",
    "3d",
    "guides",
    "labs",
)

# A note points the operator at the next graph as **lane/dir/id**. A bolded
# word (an occupancy slot, an emphasis) has no slash, so it is never a ref.
NOTE_GRAPH_REF = re.compile(r"\*\*(?P<ref>[A-Za-z0-9][A-Za-z0-9._/-]*/[A-Za-z0-9._/-]*)\*\*")


def _note_refs(graph: dict[str, Any]) -> list[str]:
    """Bold graph ids a note tells the operator to load next."""
    extra = graph.get("extra") or {}
    refs: list[str] = []
    for key in ("lab_note", "lab_description"):
        for match in NOTE_GRAPH_REF.finditer(str(extra.get(key) or "")):
            ref = match.group("ref").strip()
            if ref.endswith(".json"):
                ref = ref[: -len(".json")]
            first = ref.split("/", 1)[0]
            if first in LANE_WORDS:
                refs.append(ref)
    return refs


def note_reference_violations(graph: dict[str, Any], shipped: frozenset[str]) -> list[str]:
    """Names the note asks the operator to open that no graph backs."""
    problems: list[str] = []
    for ref in _note_refs(graph):
        if ref not in shipped:
            problems.append(f"note names graph {ref!r} that does not ship")
    return problems


def shipped_graph_ids(files: list[Path], lab_root: Path) -> frozenset[str]:
    """Lane-relative ids (``photos/still-daily``) for every lab JSON."""
    ids: set[str] = set()
    for path in files:
        try:
            rel = path.relative_to(lab_root).with_suffix("")
        except ValueError:  # pragma: no cover - rglob keeps this inside the root
            continue
        ids.add("/".join(rel.parts))
    return frozenset(ids)


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
    shipped = shipped_graph_ids(files, lab_root)
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
        for problem in stack_violations(data):
            raise SystemExit(f"{path}: {problem}")
        for problem in note_reference_violations(data, shipped):
            raise SystemExit(f"{path}: {problem}")
    return len(files)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    lab = root / "workflows" / "_lab"
    count = audit_lab_graphs(lab)
    print(f"audited {count} lab graphs")


if __name__ == "__main__":
    main()
