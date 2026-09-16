"""One-process auditor for shipped lab JSON (used by workflow.bats).

Hermetic: stdlib only. Walks workflows/_lab once and checks parse, id stem,
banned model needles, and AABB overlaps (except DCC envelopes and TRELLIS).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BANNED = (
    "z_image_turbo",
    "FLUX.2-dev",
    "klein-9b",
    "flux-2-klein-9b",
    "MiniMax",
    "Seedance",
    "Kling",
)
PAD = 20


def _skip_aabb(path: Path, lab_root: Path) -> bool:
    rel = path.relative_to(lab_root).as_posix()
    if rel.startswith("dcc/"):
        return True
    return rel == "optional/klein/trellis2.json"


def _overlap_hit(graph: dict) -> str | None:
    boxes: list[tuple[object, object, float, float, float, float]] = []
    for node in graph.get("nodes") or []:
        pos = node.get("pos") or [0, 0]
        x, y = float(pos[0]), float(pos[1])
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (
                node.get("id"),
                node.get("type"),
                x - PAD,
                y - PAD,
                x + width + PAD,
                y + height + PAD,
            )
        )
    for i, left in enumerate(boxes):
        for right in boxes[i + 1 :]:
            if (
                left[2] < right[4]
                and left[4] > right[2]
                and left[3] < right[5]
                and left[5] > right[3]
            ):
                return f"overlap {left[0]}({left[1]}) vs {right[0]}({right[1]})"
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
        if _skip_aabb(path, lab_root):
            continue
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
