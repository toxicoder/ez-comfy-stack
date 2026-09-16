"""Generate Cinema Rack encyclopedia pages from JSON catalogs.

Run from repo root:

  python3 docs/generate_cinema_docs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CINEMA = ROOT / "custom_nodes" / "ez_prompt_enhance" / "cinema"
OUT = ROOT / "docs" / "generated" / "cinema"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cell(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    text = text.replace("|", "\\|")
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _flags(row: dict[str, Any]) -> str:
    bits: list[str] = []
    if row.get("still_ok", True):
        bits.append("still")
    if row.get("motion_ok", True):
        bits.append("motion")
    if row.get("av_ok", True):
        bits.append("av")
    return ", ".join(bits) or "—"


def write_axis_page(axis_id: str, meta: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """Write one axis markdown page.

    Args:
        axis_id: Axis key.
        meta: axes.json entry.
        rows: Technique objects.

    Returns:
        Relative docs path.
    """
    label = str(meta.get("label") or axis_id)
    rel = f"generated/cinema/{axis_id}.md"
    path = OUT / f"{axis_id}.md"
    lines = [
        "---",
        f"title: {label}",
        f"description: Cinema Rack catalog — {label} ({len(rows)} spliceable techniques).",
        "tags: [cinema, prompting, catalog]",
        "---",
        "",
        f"# {label}",
        "",
        "**What's on this page**",
        "",
        f"- {len(rows)} spliceable techniques for **{label}**",
        f"- Still mode `{meta.get('still_mode')}`; I2V include `{meta.get('i2v_include')}`",
        "- Ids for the Cinema Rack combo (pick one per axis)",
        "",
        "**What this enables**",
        "",
        "- Picking a professional cinematography clause instead of guessing camera language",
        "- Seeing conflicts, still/motion/AV flags, and the Wan token when present",
        "",
        "Do not hand-edit this file. Re-run `python3 docs/generate_cinema_docs.py`.",
        "Operator playbook: [Cinema Rack](../../create/cinema-rack.md).",
        "",
        "| Id | Label | Clause | Use on | Conflicts |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        conflicts = ", ".join(str(item) for item in (row.get("conflicts") or []) if item)
        lines.append(
            "| `{id}` | {label} | {clause} | {flags} | {conflicts} |".format(
                id=_cell(row.get("id"), 48),
                label=_cell(row.get("label"), 40),
                clause=_cell(row.get("clause"), 140),
                flags=_flags(row),
                conflicts=_cell(conflicts or "—", 60),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return rel


def write_index(pages: list[dict[str, str]]) -> None:
    lines = [
        "---",
        "title: Cinema technique catalogs",
        "description: Generated encyclopedia of Cinema Rack axes.",
        "tags: [cinema, prompting, catalog]",
        "---",
        "",
        "# Cinema technique catalogs",
        "",
        "**What's on this page**",
        "",
        "- One generated page per Cinema Rack axis",
        "- Counts and splice order",
        "",
        "**What this enables**",
        "",
        "- Browsing the catalogs without opening JSON",
        "",
        "Operator playbook: [Cinema Rack](../../create/cinema-rack.md).",
        "",
        "| Axis | Techniques | Page |",
        "| --- | --- | --- |",
    ]
    for page in pages:
        if page.get("kind") == "index":
            continue
        lines.append(
            f"| {page['label']} | {page['count']} | [{page['id']}]({Path(page['path']).name}) |"
        )
    (OUT / "index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    axes = _load(CINEMA / "axes.json")
    if not isinstance(axes, dict):
        raise SystemExit("axes.json must be an object")
    pages: list[dict[str, str]] = [
        {
            "id": "index",
            "path": "generated/cinema/index.md",
            "kind": "index",
            "label": "Overview",
            "count": "0",
        }
    ]
    ordered = sorted(
        axes.items(),
        key=lambda item: int(item[1].get("splice_order") or 0)
        if isinstance(item[1], dict)
        else 0,
    )
    for axis_id, meta in ordered:
        if not isinstance(meta, dict):
            continue
        filename = str(meta.get("file") or f"{axis_id}.json")
        path = CINEMA / filename
        rows = _load(path) if path.is_file() else []
        if not isinstance(rows, list):
            raise SystemExit(f"{filename} must be a list")
        rel = write_axis_page(axis_id, meta, rows)
        pages.append(
            {
                "id": axis_id,
                "path": rel,
                "kind": "axis",
                "label": str(meta.get("label") or axis_id),
                "count": str(len(rows)),
            }
        )
    write_index(pages)
    manifest = {"pages": pages}
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(pages) - 1} cinema axis pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
