"""Generate Audio Rack encyclopedia pages from JSON catalogs.

Run from repo root:

  python3 docs/generate_audio_docs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Repo root, Audio Rack JSON catalogs, and generated markdown output dir.
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "custom_nodes" / "ez_prompt_enhance" / "audio"
OUT = ROOT / "docs" / "generated" / "audio"


def _load(path: Path) -> Any:
    """Read JSON from ``path``.

    Args:
        path: JSON file.

    Returns:
        Parsed JSON value.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _cell(value: object, limit: int = 160) -> str:
    """Collapse whitespace and escape pipes for a Markdown table cell.

    Args:
        value: Cell contents (stringified).
        limit: Maximum character length before ellipsis.

    Returns:
        Single-line table cell text.
    """
    text = " ".join(str(value or "").split())
    text = text.replace("|", "\\|")
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _flags(row: dict[str, Any]) -> str:
    """Format vocal/instrumental/podcast flags for a technique row.

    Args:
        row: Technique object from an axis catalog.

    Returns:
        Comma-separated flag labels, or an em dash when none apply.
    """
    bits: list[str] = []
    if row.get("vocal_ok", True):
        bits.append("vocal")
    if row.get("instrumental_ok", True):
        bits.append("instrumental")
    if row.get("podcast_ok", True):
        bits.append("podcast")
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
    rel = f"generated/audio/{axis_id}.md"
    path = OUT / f"{axis_id}.md"
    lines = [
        "---",
        f"title: {label}",
        f"description: Audio Rack catalog — {label} ({len(rows)} spliceable techniques).",
        "tags: [audio, music, prompting, catalog]",
        "---",
        "",
        f"# {label}",
        "",
        "**What's on this page**",
        "",
        f"- {len(rows)} spliceable techniques for **{label}**",
        f"- Vocal include `{meta.get('vocal_include')}`; instrumental `{meta.get('instrumental_include')}`",
        "- Ids for the Audio Rack combo (pick one per axis)",
        "",
        "**What this enables**",
        "",
        "- Picking a professional music-production clause instead of guessing ACE tags",
        "- Seeing conflicts, vocal/instrumental/podcast flags, and BPM when present",
        "",
        "Do not hand-edit this file. Re-run `python3 docs/generate_audio_docs.py`.",
        "Operator playbook: [Audio Rack](../../create/audio-rack.md).",
        "",
        "| Id | Label | Tags / clause | Use on | Conflicts |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        conflicts = ", ".join(str(item) for item in (row.get("conflicts") or []) if item)
        clause = str(row.get("tags") or "").strip() or str(row.get("clause") or "")
        lines.append(
            "| `{id}` | {label} | {clause} | {flags} | {conflicts} |".format(
                id=_cell(row.get("id"), 48),
                label=_cell(row.get("label"), 40),
                clause=_cell(clause, 140),
                flags=_flags(row),
                conflicts=_cell(conflicts or "—", 60),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return rel


def write_index(pages: list[dict[str, str]]) -> None:
    """Write the audio catalog index page.

    Args:
        pages: Manifest rows including the index stub.
    """
    lines = [
        "---",
        "title: Audio technique catalogs",
        "description: Generated encyclopedia of Audio Rack axes.",
        "tags: [audio, music, prompting, catalog]",
        "---",
        "",
        "# Audio technique catalogs",
        "",
        "**What's on this page**",
        "",
        "- One generated page per Audio Rack axis",
        "- Counts and splice order",
        "",
        "**What this enables**",
        "",
        "- Browsing the catalogs without opening JSON",
        "",
        "Operator playbook: [Audio Rack](../../create/audio-rack.md).",
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
    """Generate audio axis pages and the catalog index.

    Returns:
        Process exit status (always 0 on success).
    """
    axes = _load(AUDIO / "axes.json")
    if not isinstance(axes, dict):
        raise SystemExit("axes.json must be an object")
    pages: list[dict[str, str]] = [
        {
            "id": "index",
            "path": "generated/audio/index.md",
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
        path = AUDIO / filename
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
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(pages) - 1} audio axis pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
