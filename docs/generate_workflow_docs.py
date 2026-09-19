#!/usr/bin/env python3
"""Generate per-workflow node and parameter docs from workflows/_lab JSON.

Walks shipped lab graphs, inlines the hand-authored encyclopedia from
``docs/workflow_nodes.py``, and writes MkDocs pages under
``docs/generated/workflows/`` plus ``docs/reference/workflow-nodes.md``.

Stdlib only (plus the encyclopedia module). Session variables stay
``${COMFY_OUTPUT_DIR}``-style. Do not hand-edit generated pages.

Usage:
  python3 docs/generate_workflow_docs.py
  python3 docs/generate_workflow_docs.py --force
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Repo paths for lab graphs, generated pages, encyclopedia, and style catalog.
REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
LAB_DIR = REPO_ROOT / "workflows" / "_lab"
OUT_DIR = DOCS_DIR / "generated" / "workflows"
ENCYCLOPEDIA_PAGE = DOCS_DIR / "reference" / "workflow-nodes.md"
MANIFEST_FILE = OUT_DIR / "manifest.json"
STYLES_FILE = REPO_ROOT / "custom_nodes" / "ez_prompt_enhance" / "styles.json"
FORMATS_FILE = REPO_ROOT / "custom_nodes" / "ez_image" / "js" / "formats.json"
MODES_FILE = REPO_ROOT / "custom_nodes" / "ez_image" / "js" / "modes.json"
VIDEO_FORMATS_FILE = (
    REPO_ROOT / "custom_nodes" / "ez_image" / "js" / "video_formats.json"
)
RECIPES_FILE = (
    REPO_ROOT / "custom_nodes" / "ez_prompt_enhance" / "cinema" / "recipes.json"
)

if str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))

# Whitespace collapse used when quoting widget values in tables.
_WS_RE = re.compile(r"\s+")


def _collapse_blank_lines(text: str) -> str:
    """Collapse runs of blank lines and guarantee a single trailing newline.

    Args:
        text: Markdown page text.

    Returns:
        Normalized page text.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    return normalized.strip() + "\n"


def _cell(value: object, limit: int = 72) -> str:
    """Return a table-safe one-line cell.

    Args:
        value: Raw widget or metadata value.
        limit: Max characters before truncation.

    Returns:
        Escaped cell text.
    """
    if value is None:
        return "—"
    if isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = _WS_RE.sub(" ", str(value).replace("|", "\\|").replace("\n", " "))
    text = text.strip() or "—"
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _fence(value: object) -> str:
    """Return a fenced text block for a long widget value.

    Args:
        value: Raw widget value.

    Returns:
        Markdown fence, or empty string when the value is empty.
    """
    text = "" if value is None else str(value)
    if not text.strip():
        return ""
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text.rstrip()}\n{fence}"


def _mermaid_id(prefix: str, raw: object) -> str:
    """Return a mermaid-safe node id.

    Args:
        prefix: Leading letter so ids do not start with a digit.
        raw: Source id or title.

    Returns:
        ``[A-Za-z0-9_]+`` identifier.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(raw))
    if not cleaned:
        cleaned = "x"
    return f"{prefix}{cleaned}"


def lab_rel_of(path: Path, data: dict[str, Any], lab_root: Path) -> str:
    """Return extra.lab_rel when set, else the _lab-relative stem.

    Args:
        path: Graph JSON path.
        data: Parsed graph.
        lab_root: ``workflows/_lab`` root.

    Returns:
        Catalog id such as ``klein/still-draft``.
    """
    extra = data.get("extra") or {}
    lab_rel = extra.get("lab_rel")
    if isinstance(lab_rel, str) and lab_rel.strip():
        return lab_rel.strip()
    return path.relative_to(lab_root).with_suffix("").as_posix()


def album_key_of(rel: str) -> str | None:
    """Return artist/album key when ``rel`` is under audio/albums/.

    Args:
        rel: ``_lab``-relative path with suffix.

    Returns:
        ``audio/albums/<artist>/<album>`` or None.
    """
    parts = Path(rel).parts
    if len(parts) >= 5 and parts[0] == "audio" and parts[1] == "albums":
        return f"audio/albums/{parts[2]}/{parts[3]}"
    return None


def occupancy_of(data: dict[str, Any]) -> str:
    """Return occupancy from extra.lab_app_mode when present.

    Args:
        data: Parsed graph.

    Returns:
        Occupancy string or ``—``.
    """
    extra = data.get("extra") or {}
    app = extra.get("lab_app_mode")
    if isinstance(app, dict):
        occ = app.get("occupancy")
        if isinstance(occ, str) and occ.strip():
            return occ.strip()
    return "—"


def extract_note(nodes: list[dict[str, Any]]) -> str:
    """Return the first Note or MarkdownNote widget text.

    Args:
        nodes: Graph nodes.

    Returns:
        Note body, possibly empty.
    """
    for node in nodes:
        if node.get("type") not in {"Note", "MarkdownNote"}:
            continue
        widgets = node.get("widgets_values") or []
        if widgets and isinstance(widgets[0], str) and widgets[0].strip():
            return widgets[0].strip()
    return ""


def assign_groups(
    nodes: list[dict[str, Any]], groups: list[dict[str, Any]]
) -> dict[int, str]:
    """Map node id → group title using Comfy bounding boxes.

    Args:
        nodes: Graph nodes with ``pos``.
        groups: Graph ``groups`` entries with ``bounding``.

    Returns:
        Node id to group title. Ungrouped nodes map to ``Ungrouped``.
    """
    out: dict[int, str] = {}
    boxes: list[tuple[str, float, float, float, float]] = []
    for group in groups:
        bound = group.get("bounding") or []
        if len(bound) < 4:
            continue
        title = str(group.get("title") or "Group")
        boxes.append(
            (title, float(bound[0]), float(bound[1]), float(bound[2]), float(bound[3]))
        )
    for node in nodes:
        nid = int(node.get("id") or 0)
        pos = node.get("pos") or [0, 0]
        x = float(pos[0])
        y = float(pos[1])
        title = "Ungrouped"
        for name, gx, gy, gw, gh in boxes:
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                title = name
                break
        out[nid] = title
    return out


def mermaid_for_graph(data: dict[str, Any]) -> str:
    """Return a mermaid flowchart for groups or a small node graph.

    Args:
        data: Parsed graph.

    Returns:
        Fenced mermaid block, or empty when there is nothing to draw.
    """
    nodes = list(data.get("nodes") or [])
    groups = list(data.get("groups") or [])
    if groups and len(nodes) > 25:
        lines = ["```mermaid", "flowchart TB"]
        for group in groups:
            title = str(group.get("title") or "Group")
            gid = _mermaid_id("G", title)
            safe = title.replace('"', "'")
            lines.append(f'  {gid}["{safe}"]')
        lines.append("```")
        return "\n".join(lines)
    if not nodes:
        return ""
    if len(nodes) > 25:
        return ""
    id_to_label: dict[int, str] = {}
    for node in nodes:
        nid = int(node.get("id") or 0)
        label = str(node.get("title") or node.get("type") or nid)
        id_to_label[nid] = label.replace('"', "'")
    lines = ["```mermaid", "flowchart LR"]
    for nid, label in id_to_label.items():
        lines.append(f'  N{nid}["{label}"]')
    seen: set[tuple[int, int]] = set()
    for node in nodes:
        src = int(node.get("id") or 0)
        for output in node.get("outputs") or []:
            for link in output.get("links") or []:
                for other in nodes:
                    dest = int(other.get("id") or 0)
                    for inp in other.get("inputs") or []:
                        if inp.get("link") == link and (src, dest) not in seen:
                            seen.add((src, dest))
                            lines.append(f"  N{src} --> N{dest}")
    lines.append("```")
    return "\n".join(lines)


def load_styles(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load Prompt Enhance style catalog.

    Args:
        path: Optional override of ``styles.json``.

    Returns:
        Style id → entry.
    """
    target = path or STYLES_FILE
    if not target.is_file():
        return {}
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): dict(value) for key, value in raw.items() if isinstance(value, dict)}


def _image_format_choices() -> list[dict[str, str]]:
    """Load EZImageFormat combo rows from formats.json.

    Returns:
        ``{id, description}`` rows (label plus WxH).
    """
    if not FORMATS_FILE.is_file():
        return []
    raw = json.loads(FORMATS_FILE.read_text(encoding="utf-8"))
    rows = raw.get("formats") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        fid = str(item.get("id") or "").strip()
        label = str(item.get("label") or fid)
        if not fid or not label:
            continue
        width = item.get("width") or 0
        height = item.get("height") or 0
        if fid == "custom":
            desc = "Width × Height widgets, snapped to ÷16."
        else:
            desc = f"{int(width)}×{int(height)}. {fid}."
        out.append({"id": label, "description": desc})
    return out


def _modes_payload() -> dict[str, Any]:
    """Load ez_image modes.json as an object.

    Returns:
        Mapping with ``modes`` / ``categories`` lists (empty when missing).
    """
    if not MODES_FILE.is_file():
        return {"modes": [], "categories": []}
    raw = json.loads(MODES_FILE.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {"modes": raw, "categories": []}
    if isinstance(raw, dict):
        return raw
    return {"modes": [], "categories": []}


def _image_mode_choices() -> list[dict[str, str]]:
    """Load EZImageMode combo rows from modes.json.

    Returns:
        ``{id, description}`` rows keyed by label (the stored combo value).
    """
    rows = _modes_payload().get("modes")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("id") or "").strip()
        if not label:
            continue
        instruction = str(item.get("instruction") or "").strip()
        enhance = str(item.get("enhance_mode") or "t2i").strip()
        desc = instruction or f"{enhance}. {item.get('id') or label}."
        out.append({"id": label, "description": desc})
    return out


def _image_mode_category_choices() -> list[dict[str, str]]:
    """Load EZImageMode category combo rows.

    Returns:
        ``{id, description}`` rows keyed by category label.
    """
    payload = _modes_payload()
    rows = payload.get("categories")
    out: list[dict[str, str]] = []
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("id") or "").strip()
            cid = str(item.get("id") or "").strip()
            if label:
                out.append({"id": label, "description": cid or label})
        if out:
            return out
    modes = payload.get("modes")
    seen: set[str] = set()
    if isinstance(modes, list):
        for item in modes:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("category") or "").strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            label = cid.replace("_", " ").title()
            out.append({"id": label, "description": cid})
    return out


def _video_format_choices() -> list[dict[str, str]]:
    """Load EZVideoFormat combo rows from video_formats.json.

    Returns:
        ``{id, description}`` rows (label plus WxH).
    """
    if not VIDEO_FORMATS_FILE.is_file():
        return []
    raw = json.loads(VIDEO_FORMATS_FILE.read_text(encoding="utf-8"))
    rows = raw.get("formats") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        fid = str(item.get("id") or "").strip()
        label = str(item.get("label") or fid)
        if not fid or not label:
            continue
        width = item.get("width") or 0
        height = item.get("height") or 0
        family = str(item.get("family") or "").strip()
        if fid == "custom":
            desc = "Width × Height widgets, snapped to the Family VAE grid."
        else:
            desc = f"{int(width)}×{int(height)}. {family or fid}."
        out.append({"id": label, "description": desc})
    return out


def _video_family_choices() -> list[dict[str, str]]:
    """Load EZVideoFormat family combo rows.

    Returns:
        ``{id, description}`` rows.
    """
    if not VIDEO_FORMATS_FILE.is_file():
        return []
    raw = json.loads(VIDEO_FORMATS_FILE.read_text(encoding="utf-8"))
    families = raw.get("families") if isinstance(raw, dict) else None
    if not isinstance(families, dict):
        return []
    out: list[dict[str, str]] = []
    for fid, item in families.items():
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or fid).strip()
        grid = item.get("grid") or 0
        out.append(
            {
                "id": label,
                "description": f"{fid} VAE grid ÷{int(grid)}.",
            }
        )
    return out


def _cinema_recipe_choices() -> list[dict[str, str]]:
    """Load Cinema Rack recipe combo rows.

    Returns:
        ``none`` plus recipe ids.
    """
    rows = [
        {
            "id": "none",
            "description": "Off. Style + Prompt own look.",
        }
    ]
    if not RECIPES_FILE.is_file():
        return rows
    raw = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return rows
    for item in raw:
        if not isinstance(item, dict):
            continue
        rid = str(item.get("id") or "").strip()
        label = str(item.get("label") or rid)
        if rid and label:
            rows.append({"id": label, "description": rid})
    return rows


def expand_choices(
    widget: dict[str, Any],
    *,
    styles: dict[str, dict[str, Any]],
    ace_language: list[dict[str, str]],
    ace_keyscale: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return choice rows for a widget, expanding catalog hooks.

    Args:
        widget: Encyclopedia widget spec.
        styles: Style catalog.
        ace_language: ACE language rows.
        ace_keyscale: ACE keyscale rows.

    Returns:
        List of ``{id, description}``.
    """
    source = widget.get("choices_from")
    if source == "styles":
        rows = [
            {
                "id": "none",
                "description": "Off. Do not weave a look reference into the CLIP prompt.",
            }
        ]
        for style_id, entry in styles.items():
            label = str(entry.get("label") or style_id)
            suffix = str(entry.get("suffix") or "")
            medium = str(entry.get("medium") or "")
            desc = suffix or medium or label
            rows.append({"id": style_id, "description": desc})
        return rows
    if source == "ace_language":
        return list(ace_language)
    if source == "ace_keyscale":
        return list(ace_keyscale)
    if source == "image_formats":
        return _image_format_choices()
    if source == "image_modes":
        return _image_mode_choices()
    if source == "image_mode_categories":
        return _image_mode_category_choices()
    if source == "video_formats":
        return _video_format_choices()
    if source == "video_families":
        return _video_family_choices()
    if source == "cinema_recipes":
        return _cinema_recipe_choices()
    raw = widget.get("choices") or []
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict) and "id" in item:
            out.append(
                {
                    "id": str(item["id"]),
                    "description": str(item.get("description") or ""),
                }
            )
        elif isinstance(item, str):
            out.append({"id": item, "description": ""})
    return out


def widget_layouts(spec: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Return primary widget list plus any variants.

    Args:
        spec: Encyclopedia node spec.

    Returns:
        One or more widget-layout lists.
    """
    layouts = [list(spec.get("widgets") or [])]
    for variant in spec.get("variants") or []:
        if isinstance(variant, dict):
            layouts.append(list(variant.get("widgets") or []))
    return layouts


def match_layout(
    spec: dict[str, Any], values: object
) -> list[dict[str, Any]] | None:
    """Pick the encyclopedia widget layout that matches stored values.

    Args:
        spec: Encyclopedia node spec.
        values: ``widgets_values`` from the graph (list, dict, or empty).

    Returns:
        Matching widget specs, or None when no layout fits.
    """
    layouts = widget_layouts(spec)
    if values is None:
        values = []
    if isinstance(values, dict):
        keys = set(values)
        exact: list[list[dict[str, Any]]] = []
        subset: list[list[dict[str, Any]]] = []
        for layout in layouts:
            layout_keys = {
                str(item.get("key"))
                for item in layout
                if item.get("storage") == "dict" and item.get("key")
            }
            if layout_keys == keys or (not layout_keys and not keys):
                exact.append(layout)
            elif layout_keys and (
                keys.issubset(layout_keys) or layout_keys.issubset(keys)
            ):
                subset.append(layout)
        if exact:
            return exact[0]
        if subset:
            subset.sort(
                key=lambda layout: len(
                    [item for item in layout if item.get("storage") == "dict"]
                )
            )
            return subset[0]
        return None
    if not isinstance(values, list):
        return None
    for layout in layouts:
        indexed = [item for item in layout if item.get("storage") == "list"]
        if len(indexed) == len(values):
            return layout
    return None


def read_widget_value(
    values: object, widget: dict[str, Any]
) -> object:
    """Read one widget value from list or dict storage.

    Args:
        values: Graph ``widgets_values``.
        widget: Encyclopedia widget spec.

    Returns:
        Stored value, or None.
    """
    storage = widget.get("storage")
    if storage == "dict" and isinstance(values, dict):
        key = widget.get("key")
        if isinstance(key, str):
            return values.get(key)
        return None
    if storage == "list" and isinstance(values, list):
        index = widget.get("index")
        if isinstance(index, int) and 0 <= index < len(values):
            return values[index]
    return None


def _frontmatter(title: str, description: str, tags: list[str]) -> str:
    """Return YAML frontmatter for a generated docs page.

    Args:
        title: Page title (also used as H1).
        description: One-line description.
        tags: Frontmatter tags.

    Returns:
        Frontmatter block including trailing newline.
    """
    tag_s = ", ".join(tags)
    desc = description.replace("\n", " ").strip()
    return (
        "---\n"
        f"title: {title}\n"
        f"description: {desc}\n"
        f"tags: [{tag_s}]\n"
        "---\n"
    )


def _chrome(whats: list[str], enables: list[str]) -> str:
    """Return What's on this page / What this enables lists.

    Args:
        whats: Bold-lead bullets for the page brief.
        enables: Bold-lead bullets for outcomes.

    Returns:
        Markdown lists.
    """
    lines = ["**What's on this page**", ""]
    for item in whats:
        lines.append(f"- {item}")
    lines.extend(["", "**What this enables**", ""])
    for item in enables:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_param_reference(
    types_used: list[str],
    nodes: list[dict[str, Any]],
    encyclopedia: dict[str, Any],
    *,
    styles: dict[str, dict[str, Any]],
    ace_language: list[dict[str, str]],
    ace_keyscale: list[dict[str, str]],
) -> str:
    """Render the bottom node-parameter encyclopedia for types on a graph.

    Args:
        types_used: Unique node types in graph order.
        nodes: Graph nodes.
        encyclopedia: Node specs keyed by type.
        styles: Style catalog.
        ace_language: ACE language rows.
        ace_keyscale: ACE keyscale rows.

    Returns:
        Markdown section.
    """
    parts = [
        "## Node parameter reference",
        "",
        "Every unique node type on this graph. Widgets are in lab JSON order. "
        "Choices are ComfyUI v0.34.6 / lab `INPUT_TYPES` — not SD1.5 folklore.",
        "",
    ]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        by_type[str(node.get("type") or "")].append(node)
    for ntype in types_used:
        spec = encyclopedia.get(ntype) or {}
        display = str(spec.get("display_name") or ntype)
        parts.append(f"### `{ntype}` — {display}")
        parts.append("")
        summary = str(spec.get("summary") or "").strip()
        if summary:
            parts.append(summary)
            parts.append("")
        lab_notes = str(spec.get("lab_notes") or "").strip()
        if lab_notes:
            parts.append(f"!!! warning \"Lab notes\"")
            parts.append("")
            for line in lab_notes.splitlines():
                parts.append(f"    {line}")
            parts.append("")
        sockets = list(spec.get("sockets") or [])
        if sockets:
            parts.append("| Socket | Dir | Type | What it carries |")
            parts.append("| --- | --- | --- | --- |")
            for sock in sockets:
                parts.append(
                    f"| `{_cell(sock.get('name'))}` | {_cell(sock.get('dir'))} | "
                    f"`{_cell(sock.get('type'))}` | {_cell(sock.get('description'), 120)} |"
                )
            parts.append("")
        instances = by_type.get(ntype) or []
        layout: list[dict[str, Any]] | None = None
        for inst in instances:
            layout = match_layout(spec, inst.get("widgets_values"))
            if layout is not None:
                break
        if layout is None:
            layout = list(spec.get("widgets") or [])
        if not layout:
            parts.append("No widgets. Sockets only.")
            parts.append("")
            continue
        for widget in layout:
            name = str(widget.get("name") or "widget")
            wtype = str(widget.get("type") or "")
            wrange = str(widget.get("range") or "")
            desc = str(widget.get("description") or "").strip()
            gen = str(widget.get("generation") or "").strip()
            parts.append(f"#### `{name}`")
            parts.append("")
            meta = f"Type `{wtype}`."
            if wrange:
                meta += f" Range / default: {wrange}."
            parts.append(meta)
            parts.append("")
            if desc:
                parts.append(desc)
                parts.append("")
            if gen:
                parts.append(f"**How it affects generation:** {gen}")
                parts.append("")
            values: list[tuple[str, object]] = []
            for inst in instances:
                label = str(inst.get("title") or inst.get("id") or name)
                values.append(
                    (label, read_widget_value(inst.get("widgets_values"), widget))
                )
            unique = {json.dumps(val, sort_keys=True, default=str) for _, val in values}
            has_value = any(val not in (None, "", [], {}) for _, val in values)
            if not has_value:
                pass
            elif len(values) == 1:
                parts.append(f"**This graph:** `{_cell(values[0][1], 200)}`")
                parts.append("")
                fence = _fence(values[0][1])
                if fence and len(str(values[0][1])) > 72:
                    parts.append(fence)
                    parts.append("")
            elif len(unique) == 1 and values:
                parts.append(f"**This graph (all {len(values)} instances):** `{_cell(values[0][1], 200)}`")
                parts.append("")
            elif values:
                parts.append("| Instance | Value |")
                parts.append("| --- | --- |")
                for label, val in values:
                    parts.append(f"| {_cell(label, 40)} | `{_cell(val, 80)}` |")
                parts.append("")
            choices = expand_choices(
                widget,
                styles=styles,
                ace_language=ace_language,
                ace_keyscale=ace_keyscale,
            )
            if choices:
                parts.append("**Other choices**")
                parts.append("")
                parts.append("| Choice | What it does |")
                parts.append("| --- | --- |")
                for choice in choices:
                    parts.append(
                        f"| `{_cell(choice.get('id'))}` | {_cell(choice.get('description'), 160)} |"
                    )
                parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _node_table(
    nodes: list[dict[str, Any]], group_of: dict[int, str]
) -> str:
    """Return a node inventory table.

    Args:
        nodes: Graph nodes.
        group_of: Node id to group title.

    Returns:
        Markdown table.
    """
    lines = [
        "| Id | Title | Type | Group |",
        "| --- | --- | --- | --- |",
    ]
    for node in nodes:
        nid = int(node.get("id") or 0)
        lines.append(
            f"| {nid} | {_cell(node.get('title') or node.get('type'), 40)} | "
            f"`{_cell(node.get('type'))}` | {_cell(group_of.get(nid, 'Ungrouped'), 32)} |"
        )
    return "\n".join(lines)


def _types_in_order(nodes: list[dict[str, Any]]) -> list[str]:
    """Return unique node types in first-seen order.

    Args:
        nodes: Graph nodes.

    Returns:
        Type names.
    """
    seen: list[str] = []
    for node in nodes:
        ntype = str(node.get("type") or "")
        if ntype and ntype not in seen:
            seen.append(ntype)
    return seen


def render_graph_page(
    lab_rel: str,
    data: dict[str, Any],
    encyclopedia: dict[str, Any],
    *,
    styles: dict[str, dict[str, Any]],
    ace_language: list[dict[str, str]],
    ace_keyscale: list[dict[str, str]],
) -> str:
    """Render one non-album workflow details page.

    Args:
        lab_rel: Catalog id.
        data: Parsed graph.
        encyclopedia: Node specs.
        styles: Style catalog.
        ace_language: ACE language rows.
        ace_keyscale: ACE keyscale rows.

    Returns:
        Markdown page text.
    """
    nodes = list(data.get("nodes") or [])
    groups = list(data.get("groups") or [])
    extra = data.get("extra") or {}
    desc = str(extra.get("lab_description") or f"Lab graph {lab_rel}").strip()
    occ = occupancy_of(data)
    note = extract_note(nodes)
    types_used = _types_in_order(nodes)
    group_of = assign_groups(nodes, groups)
    mermaid = mermaid_for_graph(data)
    title = lab_rel
    body = [
        _frontmatter(
            title,
            desc[:158],
            ["workflows", "generated", "comfyui", lab_rel.split("/", 1)[0]],
        ),
        f"# {title}",
        "",
        _chrome(
            [
                "**Purpose, occupancy, and models** from the on-canvas Note",
                "**Graph flow** (groups when the canvas is large)",
                "**Every node id** on this graph",
                "**Node parameter reference** for each type, with this graph's values and the other legal choices",
            ],
            [
                "**Queuing this filename** with known widgets",
                "**Changing a parameter** with a documented generation effect",
            ],
        ),
        "",
        f"**Who this is for:** studio users who loaded `{lab_rel}` from Apps or Workflows.",
        "",
        "> Generated from `workflows/_lab/"
        + lab_rel
        + ".json`. Do not hand-edit this file. Re-run `python3 docs/generate_workflow_docs.py` (or `make docs`).",
        "",
        "## Purpose",
        "",
        f"Occupancy **{occ}**. Outputs under `${{COMFY_OUTPUT_DIR}}`. Unload the previous family before Queue.",
        "",
    ]
    if note:
        body.append(_fence(note))
        body.append("")
    else:
        body.append(desc)
        body.append("")
    body.extend(
        [
            "## How to Queue",
            "",
            "1. `./scripts/manage.sh start` so `_lab` is seeded",
            f"2. Load **{lab_rel}** from **Apps** or **Workflows**",
            "3. Read the on-canvas Note, change widgets, Queue",
            "",
            "Do not edit raw `_lab` JSON. Save keepers under `_user/`.",
            "",
        ]
    )
    if mermaid:
        body.extend(["## Graph", "", mermaid, ""])
    body.extend(
        [
            "## Nodes on this graph",
            "",
            _node_table(nodes, group_of),
            "",
            render_param_reference(
                types_used,
                nodes,
                encyclopedia,
                styles=styles,
                ace_language=ace_language,
                ace_keyscale=ace_keyscale,
            ),
        ]
    )
    return _collapse_blank_lines("\n".join(body))


def _track_widgets(data: dict[str, Any]) -> str:
    """Return a compact widget dump for one album graph.

    Args:
        data: Parsed track/cover/album graph.

    Returns:
        Markdown fragment.
    """
    lines: list[str] = []
    for node in data.get("nodes") or []:
        ntype = str(node.get("type") or "")
        title = str(node.get("title") or ntype)
        values = node.get("widgets_values")
        if values in (None, [], {}):
            continue
        if ntype in {"Note", "MarkdownNote"}:
            continue
        lines.append(f"**{title}** (`{ntype}`)")
        lines.append("")
        if isinstance(values, dict):
            lines.append("| Key | Value |")
            lines.append("| --- | --- |")
            for key, val in values.items():
                lines.append(f"| `{_cell(key)}` | `{_cell(val, 80)}` |")
            lines.append("")
        elif isinstance(values, list):
            long_strings = [
                val for val in values if isinstance(val, str) and len(val) > 80
            ]
            lines.append("| Slot | Value |")
            lines.append("| --- | --- |")
            for index, val in enumerate(values):
                lines.append(f"| {index} | `{_cell(val, 80)}` |")
            lines.append("")
            for val in long_strings[:2]:
                lines.append(_fence(val))
                lines.append("")
    return "\n".join(lines)


def render_album_page(
    album_id: str,
    graphs: list[tuple[str, Path, dict[str, Any]]],
    encyclopedia: dict[str, Any],
    *,
    styles: dict[str, dict[str, Any]],
    ace_language: list[dict[str, str]],
    ace_keyscale: list[dict[str, str]],
) -> str:
    """Render one album page covering every track, cover, and album-pack graph.

    Args:
        album_id: ``audio/albums/<artist>/<album>``.
        graphs: ``(lab_rel, path, data)`` sorted by stem.
        encyclopedia: Node specs.
        styles: Style catalog.
        ace_language: ACE language rows.
        ace_keyscale: ACE keyscale rows.

    Returns:
        Markdown page text.
    """
    # Use the first track (not cover/album) for the shared topology mermaid.
    topology = graphs[0][2]
    for lab_rel, _path, data in graphs:
        stem = Path(lab_rel).name
        if stem not in {"cover", "album"}:
            topology = data
            break
    nodes = list(topology.get("nodes") or [])
    all_nodes: list[dict[str, Any]] = []
    types_used: list[str] = []
    for _lab_rel, _path, data in graphs:
        for node in data.get("nodes") or []:
            all_nodes.append(node)
            ntype = str(node.get("type") or "")
            if ntype and ntype not in types_used:
                types_used.append(ntype)
    occ = occupancy_of(topology)
    note = extract_note(nodes)
    mermaid = mermaid_for_graph(topology)
    title = album_id
    desc = f"Album graphs under {album_id} (tracks, cover, album pack)."
    body = [
        _frontmatter(
            title,
            desc,
            ["workflows", "generated", "comfyui", "audio", "album"],
        ),
        f"# {title}",
        "",
        _chrome(
            [
                "**Every track, cover, and album-pack graph** in this folder",
                "**Shared ACE-Step topology** (one printer, unique widgets per take)",
                "**Node parameter reference** for the types on these graphs",
            ],
            [
                "**Queuing one numbered take** or `album-render`",
                "**Reading tags, lyrics, seed, BPM** without opening raw JSON",
            ],
        ),
        "",
        f"**Who this is for:** studio users after `download-music`. Occupancy **{occ}** (cover stills are **klein** — separate session).",
        "",
        "> Generated from `workflows/_lab/"
        + album_id
        + "/`. Do not hand-edit this file.",
        "",
        "## Purpose",
        "",
        f"Numbered takes under `{album_id}/`. Queue one track, or "
        f"`./scripts/manage.sh album-render --album {album_id.removeprefix('audio/albums/')}`.",
        "",
    ]
    if note:
        body.append(_fence(note))
        body.append("")
    if mermaid:
        body.extend(["## Shared graph", "", mermaid, ""])
    body.extend(["## Graphs in this album", ""])
    body.append("| Graph | Nodes | Occupancy |")
    body.append("| --- | --- | --- |")
    for lab_rel, _path, data in graphs:
        body.append(
            f"| `{lab_rel}` | {len(data.get('nodes') or [])} | {occupancy_of(data)} |"
        )
    body.append("")
    for lab_rel, _path, data in graphs:
        stem = Path(lab_rel).name
        body.extend([f"## `{stem}`", "", f"Catalog id `{lab_rel}`.", ""])
        extra = data.get("extra") or {}
        desc_one = str(extra.get("lab_description") or "").strip()
        if desc_one:
            body.append(desc_one)
            body.append("")
        body.append(_track_widgets(data))
        body.append("")
    body.append(
        render_param_reference(
            types_used,
            all_nodes,
            encyclopedia,
            styles=styles,
            ace_language=ace_language,
            ace_keyscale=ace_keyscale,
        )
    )
    return _collapse_blank_lines("\n".join(body))


def render_encyclopedia_page(
    encyclopedia: dict[str, Any],
    *,
    styles: dict[str, dict[str, Any]],
    ace_language: list[dict[str, str]],
    ace_keyscale: list[dict[str, str]],
) -> str:
    """Render the cross-graph node encyclopedia page.

    Args:
        encyclopedia: Node specs.
        styles: Style catalog.
        ace_language: ACE language rows.
        ace_keyscale: ACE keyscale rows.

    Returns:
        Markdown page text.
    """
    body = [
        _frontmatter(
            "Workflow node parameters",
            "Every Comfy node type used in workflows/_lab, with widgets, choices, and generation effects.",
            ["workflows", "generated", "comfyui", "reference"],
        ),
        "# Workflow node parameters",
        "",
        _chrome(
            [
                "**Every node type** that appears in `workflows/_lab/`",
                "**Widgets in lab JSON order**, including combo choices",
                "**Lab notes** (CFG 1.0 on distilled Klein, LTX ÷32, occupancy XOR)",
            ],
            [
                "**Looking up a widget** without opening `nodes.py`",
                "**Seeing legal choices** before changing a seeded graph",
            ],
        ),
        "",
        "**Who this is for:** studio users who already Queued a lab graph. Pack catalog: [Custom nodes](custom-nodes.md). Per-graph pages: [Workflow details](../create/workflows-index.md).",
        "",
        "> Generated from `docs/workflow_nodes.py`. Do not hand-edit this file.",
        "",
        "ComfyUI pin **v0.34.6**. MiniMax is banned. Klein 9B / FLUX.2-dev are opt-in NC, not lab defaults.",
        "",
    ]
    dummy_nodes = [
        {"id": 1, "type": ntype, "title": ntype, "widgets_values": []}
        for ntype in encyclopedia
    ]
    body.append(
        render_param_reference(
            sorted(encyclopedia),
            dummy_nodes,
            encyclopedia,
            styles=styles,
            ace_language=ace_language,
            ace_keyscale=ace_keyscale,
        )
    )
    return _collapse_blank_lines("\n".join(body))


def render_generated_index(
    pages: list[dict[str, str]],
) -> str:
    """Render the generated TOC of every details page.

    Args:
        pages: Manifest page rows.

    Returns:
        Markdown page text.
    """
    body = [
        _frontmatter(
            "Generated workflow pages",
            "Index of generated per-workflow node and parameter pages for every _lab graph.",
            ["workflows", "generated", "comfyui"],
        ),
        "# Generated workflow pages",
        "",
        _chrome(
            [
                "**Every generated details page** (one per unique graph, one per album)",
                "**Lane grouping** matching `_lab/<lane>/`",
            ],
            [
                "**Opening the node parameter page** for a seeded filename",
            ],
        ),
        "",
        "> Generated. Do not hand-edit. Hub: [Workflow details](../../create/workflows-index.md).",
        "",
    ]
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for page in pages:
        by_lane[page.get("lane") or "other"].append(page)
    for lane in sorted(by_lane):
        body.append(f"## {lane}")
        body.append("")
        body.append("| Graph | Page |")
        body.append("| --- | --- |")
        for page in by_lane[lane]:
            rel = page["path"]
            href = Path(rel).name
            # Nested album paths need relative href from this index.
            href = Path(rel).relative_to("generated/workflows").as_posix()
            body.append(f"| `{page['id']}` | [{href}]({href}) |")
        body.append("")
    return _collapse_blank_lines("\n".join(body))


def iter_lab_graphs(
    lab_root: Path,
) -> list[tuple[str, Path, dict[str, Any]]]:
    """Load every JSON graph under ``lab_root``.

    Args:
        lab_root: ``workflows/_lab``.

    Returns:
        Sorted ``(lab_rel, path, data)`` tuples.
    """
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    for path in sorted(lab_root.rglob("*.json")):
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        rel = lab_rel_of(path, data, lab_root)
        rows.append((rel, path, data))
    return rows


def _partition_lab_graphs(
    lab: Path,
    graphs: list[tuple[str, Path, dict[str, Any]]],
) -> tuple[
    dict[str, list[tuple[str, Path, dict[str, Any]]]],
    list[tuple[str, Path, dict[str, Any]]],
]:
    """Split lab graphs into album groups vs standalone pages.

    Args:
        lab: ``workflows/_lab`` root.
        graphs: ``(lab_rel, path, data)`` rows.

    Returns:
        ``(albums, singles)``.
    """
    albums: dict[str, list[tuple[str, Path, dict[str, Any]]]] = defaultdict(list)
    singles: list[tuple[str, Path, dict[str, Any]]] = []
    for lab_rel, path, data in graphs:
        rel_file = path.relative_to(lab).as_posix()
        key = album_key_of(rel_file)
        if key:
            albums[key].append((lab_rel, path, data))
        else:
            singles.append((lab_rel, path, data))
    return albums, singles


def _write_generated_pages(
    pages: dict[str, str],
    dest: Path,
    enc_page: Path,
    manifest_pages: list[dict[str, str]],
    graph_count: int,
) -> None:
    """Write Markdown pages and ``manifest.json``.

    Args:
        pages: Repo-relative path → markdown.
        dest: ``docs/generated/workflows``.
        enc_page: ``docs/reference/workflow-nodes.md``.
        manifest_pages: Manifest rows.
        graph_count: Number of lab graphs walked.
    """
    dest.mkdir(parents=True, exist_ok=True)
    if dest.is_dir():
        for old in dest.rglob("*.md"):
            old.unlink()
    for rel, text in pages.items():
        if rel == "reference/workflow-nodes.md":
            target = enc_page
        else:
            suffix = rel.removeprefix("generated/workflows/")
            target = dest / suffix
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    manifest_path = dest / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "pages": manifest_pages,
                "graph_count": graph_count,
                "page_count": len(pages),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def generate(
    repo_root: Path | None = None,
    *,
    lab_root: Path | None = None,
    out_dir: Path | None = None,
    encyclopedia_page: Path | None = None,
    encyclopedia: dict[str, Any] | None = None,
    styles_path: Path | None = None,
    write: bool = True,
) -> dict[str, str]:
    """Build all workflow-details Markdown pages.

    Args:
        repo_root: Repository root (default: parent of ``docs/``).
        lab_root: Override for ``workflows/_lab``.
        out_dir: Override for ``docs/generated/workflows``.
        encyclopedia_page: Override for ``docs/reference/workflow-nodes.md``.
        encyclopedia: Optional preloaded node specs (tests).
        styles_path: Optional ``styles.json`` override.
        write: When true, write files and the manifest.

    Returns:
        Mapping of repo-relative posix path → markdown body.
    """
    root = repo_root or REPO_ROOT
    lab = lab_root or (root / "workflows" / "_lab")
    dest = out_dir or (root / "docs" / "generated" / "workflows")
    enc_page = encyclopedia_page or (root / "docs" / "reference" / "workflow-nodes.md")
    if encyclopedia is None:
        from workflow_nodes import encyclopedia as load_enc

        encyclopedia = load_enc()
    styles = load_styles(styles_path)
    from workflow_nodes import ACE_KEYSCALE_CHOICES, ACE_LANGUAGE_CHOICES

    graphs = iter_lab_graphs(lab)
    pages: dict[str, str] = {}
    manifest_pages: list[dict[str, str]] = []
    albums, singles = _partition_lab_graphs(lab, graphs)

    for lab_rel, _path, data in singles:
        md = render_graph_page(
            lab_rel,
            data,
            encyclopedia,
            styles=styles,
            ace_language=ACE_LANGUAGE_CHOICES,
            ace_keyscale=ACE_KEYSCALE_CHOICES,
        )
        rel = f"generated/workflows/{lab_rel}.md"
        pages[rel] = md
        lane = lab_rel.split("/", 1)[0]
        manifest_pages.append({"id": lab_rel, "path": rel, "lane": lane, "kind": "graph"})

    for album_id, album_graphs in sorted(albums.items()):
        md = render_album_page(
            album_id,
            album_graphs,
            encyclopedia,
            styles=styles,
            ace_language=ACE_LANGUAGE_CHOICES,
            ace_keyscale=ACE_KEYSCALE_CHOICES,
        )
        rel = f"generated/workflows/{album_id}.md"
        pages[rel] = md
        manifest_pages.append(
            {"id": album_id, "path": rel, "lane": "audio-albums", "kind": "album"}
        )

    index_md = render_generated_index(manifest_pages)
    pages["generated/workflows/index.md"] = index_md
    manifest_pages.insert(
        0,
        {
            "id": "index",
            "path": "generated/workflows/index.md",
            "lane": "index",
            "kind": "index",
        },
    )
    pages["reference/workflow-nodes.md"] = render_encyclopedia_page(
        encyclopedia,
        styles=styles,
        ace_language=ACE_LANGUAGE_CHOICES,
        ace_keyscale=ACE_KEYSCALE_CHOICES,
    )

    if write:
        _write_generated_pages(
            pages, dest, enc_page, manifest_pages, len(graphs)
        )
    return pages


def inject_nav(nav: list[Any], manifest_pages: list[dict[str, str]]) -> list[Any]:
    """Replace the Workflow details nav entry with a nested tree.

    Args:
        nav: MkDocs ``nav`` list.
        manifest_pages: Manifest page rows.

    Returns:
        New nav list (shallow-copied at the mutated branches).
    """
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for page in manifest_pages:
        if page.get("kind") == "index":
            continue
        by_lane[page.get("lane") or "other"].append(page)

    children: list[Any] = [
        {"Overview": "create/workflows-index.md"},
        {"All graphs": "generated/workflows/index.md"},
        {"Node parameter encyclopedia": "reference/workflow-nodes.md"},
    ]
    lane_order = [
        "klein",
        "wan",
        "ltx",
        "shorts",
        "dcc",
        "optional",
        "inspire",
        "audio",
        "audio-albums",
    ]
    seen_lanes = [lane for lane in lane_order if lane in by_lane]
    for lane in sorted(by_lane):
        if lane not in seen_lanes:
            seen_lanes.append(lane)
    for lane in seen_lanes:
        items = []
        for page in by_lane[lane]:
            label = page["id"].rsplit("/", 1)[-1]
            items.append({label: page["path"]})
        children.append({lane: items})

    def walk(items: list[Any]) -> list[Any]:
        """Rebuild a nav list, substituting the Workflow details subtree.

        Args:
            items: MkDocs nav entries (strings or single-key dicts).

        Returns:
            A new nav list with generated children under Workflow details.
        """
        out: list[Any] = []
        for item in items:
            if isinstance(item, dict) and "Workflow details" in item:
                out.append({"Workflow details": children})
                continue
            if isinstance(item, dict):
                rebuilt: dict[str, Any] = {}
                for key, value in item.items():
                    if isinstance(value, list):
                        rebuilt[key] = walk(value)
                    else:
                        rebuilt[key] = value
                out.append(rebuilt)
                continue
            out.append(item)
        return out

    return walk(nav)


def main(argv: list[str] | None = None) -> int:
    """Generate workflow details Markdown.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit status (always 0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Generate docs/generated/workflows pages from workflows/_lab"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite even when content is unchanged (always writes)",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    del args
    pages = generate(write=True)
    print(f"Generated {len(pages)} workflow doc pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
