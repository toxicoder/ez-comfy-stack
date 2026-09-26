"""Generate Cinema Rack encyclopedia pages from JSON catalogs.

Run from repo root:

  python3 docs/generate_cinema_docs.py
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any

# Repo root, Cinema Rack JSON catalogs, generated markdown, and clip assets.
ROOT = Path(__file__).resolve().parents[1]
CINEMA = ROOT / "custom_nodes" / "ez_prompt_enhance" / "cinema"
OUT = ROOT / "docs" / "generated" / "cinema"
ASSETS = ROOT / "docs" / "assets" / "cinema"


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
        return text[: limit - 1] + "..."
    return text


def _flags(row: dict[str, Any]) -> str:
    """Format still/motion/AV flags for a technique row.

    Args:
        row: Technique object from an axis catalog.

    Returns:
        Comma-separated flag labels, or an em dash when none apply.
    """
    bits: list[str] = []
    if row.get("still_ok", True):
        bits.append("still")
    if row.get("motion_ok", True):
        bits.append("motion")
    if row.get("av_ok", True):
        bits.append("av")
    return ", ".join(bits) or "-"


def _yaml_str(value: object) -> str:
    """Quote a YAML scalar.

    Args:
        value: Raw title or description.

    Returns:
        Double-quoted YAML string.
    """
    text = str(value or "").replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def clip_files(axis_id: str, technique_id: str) -> tuple[Path, Path]:
    """Return mp4 and poster paths for a technique.

    Args:
        axis_id: Axis key.
        technique_id: Technique id.

    Returns:
        ``(mp4, jpg)`` paths under ``ASSETS``.
    """
    folder = ASSETS / axis_id
    return folder / f"{technique_id}.mp4", folder / f"{technique_id}.jpg"


def has_clip(axis_id: str, technique_id: str) -> bool:
    """True when both the mp4 and poster exist.

    Args:
        axis_id: Axis key.
        technique_id: Technique id.

    Returns:
        Whether illustration media is shipped.
    """
    mp4, jpg = clip_files(axis_id, technique_id)
    return mp4.is_file() and jpg.is_file()


def _example_cell(axis_id: str, row: dict[str, Any]) -> str:
    """Axis-table Example cell: poster link or em dash.

    Args:
        axis_id: Axis key.
        row: Technique object.

    Returns:
        HTML thumbnail link or ``-``.
    """
    tid = str(row.get("id") or "")
    if not tid or not has_clip(axis_id, tid):
        return "-"
    label = html.escape(str(row.get("label") or tid), quote=True)
    poster = f"../assets/cinema/{axis_id}/{tid}.jpg"
    href = f"{axis_id}/{tid}.md"
    return (
        f'<a href="{href}"><img class="ez-cinema-thumb" src="{poster}" '
        f'alt="{label}" width="160"></a>'
    )


def write_technique_page(axis_id: str, axis_label: str, row: dict[str, Any]) -> str:
    """Write one technique illustration page.

    Args:
        axis_id: Axis key.
        axis_label: Axis display label.
        row: Technique object.

    Returns:
        Relative docs path.
    """
    tid = str(row.get("id") or "")
    label = str(row.get("label") or tid)
    rel = f"generated/cinema/{axis_id}/{tid}.md"
    path = OUT / axis_id / f"{tid}.md"
    poster = f"../../../assets/cinema/{axis_id}/{tid}.jpg"
    video = f"../../../assets/cinema/{axis_id}/{tid}.mp4"
    conflicts = ", ".join(str(item) for item in (row.get("conflicts") or []) if item)
    lines = [
        "---",
        f"title: {_yaml_str(label)}",
        f"description: {_yaml_str('Cinema Rack illustration - ' + label + '.')}",
        "tags: [cinema, prompting, catalog, clip]",
        "---",
        "",
        f"# {label}",
        "",
        "**What's on this page**",
        "",
        f"- A muted 5s illustration of **{label}** (`{tid}`)",
        f"- Catalog clause and still/motion/AV flags on **{axis_label}**",
        "",
        "**What this enables**",
        "",
        "- Seeing the pick before splicing it on Cinema Rack",
        "- Copying the clause next to a concrete camera example",
        "",
        "Do not hand-edit this file. Re-run `python3 docs/generate_cinema_docs.py`.",
        f"Axis: [{axis_label}](../{axis_id}.md). Playbook: [Cinema Rack](../../../create/cinema-rack.md).",
        "",
        '<div class="ez-cinema-clip">',
        (
            f'<video controls preload="none" playsinline poster="{poster}">'
            f'<source src="{video}" type="video/mp4"></video>'
        ),
        "</div>",
        "",
        "## Clause",
        "",
        str(row.get("clause") or "-"),
        "",
        "## Use on",
        "",
        _flags(row),
        "",
        "## Conflicts",
        "",
        conflicts or "-",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return rel


def write_axis_page(axis_id: str, meta: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """Write one axis markdown page and any shipped technique pages.

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
    typed_rows = [row for row in rows if isinstance(row, dict)]
    clip_n = sum(1 for row in typed_rows if has_clip(axis_id, str(row.get("id") or "")))
    lines = [
        "---",
        f"title: {label}",
        f"description: Cinema Rack catalog - {label} ({len(rows)} spliceable techniques).",
        "tags: [cinema, prompting, catalog]",
        "---",
        "",
        f"# {label}",
        "",
        "**What's on this page**",
        "",
        f"- {len(rows)} spliceable techniques for **{label}**",
        f"- Still mode `{meta.get('still_mode')}`; I2V include `{meta.get('i2v_include')}`",
        f"- {clip_n} muted 5s illustration clips shipped",
        "- Ids for the Cinema Rack combo (pick one per axis)",
        "",
        "**What this enables**",
        "",
        "- Picking a professional cinematography clause instead of guessing camera language",
        "- Opening a technique page to watch a 5s example when the clip is shipped",
        "- Seeing conflicts, still/motion/AV flags, and the Wan token when present",
        "",
        "Do not hand-edit this file. Re-run `python3 docs/generate_cinema_docs.py`.",
        "Operator playbook: [Cinema Rack](../../create/cinema-rack.md).",
        "",
        "| Id | Label | Example | Clause | Use on | Conflicts |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("id") or "")
        conflicts = ", ".join(str(item) for item in (row.get("conflicts") or []) if item)
        lines.append(
            "| `{id}` | {label} | {example} | {clause} | {flags} | {conflicts} |".format(
                id=_cell(tid, 48),
                label=_cell(row.get("label"), 40),
                example=_example_cell(axis_id, row),
                clause=_cell(row.get("clause"), 140),
                flags=_flags(row),
                conflicts=_cell(conflicts or "-", 60),
            )
        )
        if tid and has_clip(axis_id, tid):
            write_technique_page(axis_id, label, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return rel


def write_index(pages: list[dict[str, str]]) -> None:
    """Write the cinema catalog index page.

    Args:
        pages: Manifest rows including the index stub.
    """
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
        "- Counts, shipped 5s clips, and splice order",
        "",
        "**What this enables**",
        "",
        "- Browsing the catalogs without opening JSON",
        "- Opening a technique page when an illustration clip is shipped",
        "",
        "Operator playbook: [Cinema Rack](../../create/cinema-rack.md).",
        "",
        "| Axis | Techniques | Clips | Page |",
        "| --- | --- | --- | --- |",
    ]
    for page in pages:
        if page.get("kind") == "index":
            continue
        lines.append(
            f"| {page['label']} | {page['count']} | {page.get('clips', '0')} | "
            f"[{page['id']}]({Path(page['path']).name}) |"
        )
    (OUT / "index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    """Generate cinema axis pages and the catalog index.

    Returns:
        Process exit status (always 0 on success).
    """
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
            "clips": "0",
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
        typed_rows = [row for row in rows if isinstance(row, dict)]
        clip_n = sum(1 for row in typed_rows if has_clip(axis_id, str(row.get("id") or "")))
        pages.append(
            {
                "id": axis_id,
                "path": rel,
                "kind": "axis",
                "label": str(meta.get("label") or axis_id),
                "count": str(len(rows)),
                "clips": str(clip_n),
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
