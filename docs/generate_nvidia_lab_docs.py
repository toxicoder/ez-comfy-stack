#!/usr/bin/env python3
"""Render the opt-in NVIDIA lab tier reference from the single-source catalog.

Reads ``custom_nodes/ez_nvidia_lab/catalog.json`` and writes
``docs/generated/nvidia-lab/tier.md``: one section per status, one table row per
tool, then one card per tool carrying its task, input, output, upstream link,
see-also links, weights, artifact ref, gate notes, reopen condition, and
sources.

The reader fails closed. A document whose ``schema`` is not 1, whose ``tier``
is not the tier this page documents, that carries a missing or unknown key at
any level, or that holds a value outside the enums the catalog itself declares,
raises ``ValueError`` naming the offending key rather than publishing a partial
page.

Output is deterministic: rows sort by tool id, status sections follow the order
the catalog declares, line endings are LF, and the page ends in a single
trailing newline. Re-running over an unchanged catalog leaves the file
byte-identical.

A size of ``0`` in the catalog means upstream published no figure, so the page
renders :data:`NOT_PUBLISHED` in that column rather than a zero an operator
would read as "no download needed". The catalog keeps the integer.

A ``gated`` of ``null`` means nobody checked the repo, so the page renders
:data:`GATING_NOT_CHECKED` rather than the "ungated" a row would otherwise
assert. A weight ``file`` names one of three shapes - a path, a directory
behind a trailing ``/``, or a shard set behind a ``*`` - and only a path
prints as one bare file.

Usage:
  bazelisk run //docs:generate_nvidia_lab   # this file only
  bazelisk run //docs:generate              # every generated docs page

The catalog path comes from ``--catalog``, else ``$EZ_NVIDIA_LAB_CATALOG``, else
the repo default above; ``--out`` redirects the page (tests).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

# JSON vocabulary the reader narrows against. Stdlib only, and no Any: every
# value entering from json.loads is checked before it reaches the renderer.
Json = Union[None, bool, int, float, str, "list[Json]", "dict[str, Json]"]

# Repo layout. The catalog lives under custom_nodes/ on purpose: compose mounts
# ../custom_nodes, so the same file is readable in the container and on the host.
REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_ENV = "EZ_NVIDIA_LAB_CATALOG"
DEFAULT_CATALOG_PATH = REPO_ROOT / "custom_nodes" / "ez_nvidia_lab" / "catalog.json"
OUTPUT_DIR = REPO_ROOT / "docs" / "generated" / "nvidia-lab"
OUTPUT_FILE = OUTPUT_DIR / "tier.md"

# The only document shape this reader accepts; anything else is a reader error.
SUPPORTED_SCHEMA = 1
EXPECTED_TIER = "nvidia-lab"

# Keys accepted at each level of the document. A key absent here is missing; a
# key present but not listed here is unknown. Both are fatal.
TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "tier",
        "tier_title",
        "updated",
        "status_values",
        "commercial_values",
        "arm64_values",
        "artifact_values",
        "comfy_shape_values",
        "tools",
    }
)
TOOL_KEYS = frozenset(
    {
        "id",
        "title",
        "status",
        "task",
        "input",
        "output",
        "upstream",
        "see_also",
        "code_license",
        "weights_license",
        "commercial_use",
        "weights",
        "artifact",
        "artifact_ref",
        "arm64",
        "gb10",
        "install",
        "cmd",
        "vram_gb",
        "disk_gb",
        "comfy_shape",
        "nodes",
        "graph",
        "app",
        "gate_notes",
        "reopen",
        "verify",
        "sources",
    }
)
WEIGHT_KEYS = frozenset({"source", "repo", "file", "gb", "gated"})
APP_KEYS = frozenset({"mode", "occupancy", "deliverable"})

# Tool field -> the top-level key whose list holds the values that field may
# take. The enums are read from the document, never hardcoded here.
ENUM_FIELDS: tuple[tuple[str, str], ...] = (
    ("status", "status_values"),
    ("commercial_use", "commercial_values"),
    ("arm64", "arm64_values"),
    ("artifact", "artifact_values"),
    ("comfy_shape", "comfy_shape_values"),
)

# Column order of the master table; the per-row cells come from _table_cells().
TABLE_HEADER: tuple[str, ...] = (
    "id",
    "title",
    "status",
    "code license",
    "weights license",
    "commercial use",
    "arm64",
    "gb10",
    "artifact",
    "comfy shape",
    "VRAM GB",
    "disk GB",
)

# The catalog encodes "upstream publishes no figure" as the integer 0, which is
# a fact about the data, not a size. The reader keeps 0; the page says this
# instead, because a printed 0 reads to an operator as "nothing to download".
NOT_PUBLISHED = "not published"
"""What a size column or weight says when the catalog records 0."""

GATING_NOT_CHECKED = "gating not checked"
"""What the gating cell says when the catalog records null (nobody looked)."""


@dataclass(frozen=True)
class Weight:
    """One published weight artifact a tool row depends on."""

    source: str
    repo: str
    file: str
    gb: float
    gated: bool | None


@dataclass(frozen=True)
class Tool:
    """One validated catalog row, in the shape the renderer wants."""

    tool_id: str
    title: str
    status: str
    task: str
    input_text: str
    output_text: str
    upstream: str
    see_also: list[str]
    code_license: str
    weights_license: str
    commercial_use: str
    weights: list[Weight]
    artifact: str
    artifact_ref: str
    arm64: str
    gb10: str
    vram_gb: int
    disk_gb: int
    comfy_shape: str
    gate_notes: str
    reopen: str
    sources: list[str]


@dataclass(frozen=True)
class Catalog:
    """The validated catalog document, with rows sorted by tool id."""

    tier_title: str
    updated: str
    status_values: list[str]
    tools: list[Tool]


def _object(value: Json, where: str) -> dict[str, Json]:
    """Return ``value`` as a mapping or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a mapping.

    Raises:
        ValueError: The value is not a JSON object.
    """
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected a JSON object")
    return value


def _array(value: Json, where: str) -> list[Json]:
    """Return ``value`` as a list or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a list.

    Raises:
        ValueError: The value is not a JSON array.
    """
    if not isinstance(value, list):
        raise ValueError(f"{where}: expected a JSON array")
    return value


def _text(value: Json, where: str) -> str:
    """Return ``value`` as a string or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a string.

    Raises:
        ValueError: The value is not a string.
    """
    if not isinstance(value, str):
        raise ValueError(f"{where}: expected a string")
    return value


def _text_list(value: Json, where: str) -> list[str]:
    """Return ``value`` as a list of strings or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a list of strings.

    Raises:
        ValueError: The value is not an array, or holds a non-string.
    """
    items: list[str] = []
    for item in _array(value, where):
        if not isinstance(item, str):
            raise ValueError(f"{where}: expected an array of strings")
        items.append(item)
    return items


def _flag(value: Json, where: str) -> bool:
    """Return ``value`` as a boolean or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a boolean.

    Raises:
        ValueError: The value is not a boolean.
    """
    if not isinstance(value, bool):
        raise ValueError(f"{where}: expected a boolean")
    return value


def _flag_or_none(value: Json, where: str) -> bool | None:
    """Return ``value`` as a boolean, or ``None`` when the catalog says null.

    Null is a value here, not a missing key: it records that nobody checked
    the repo's gating, which is not the same claim as ``False``.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a boolean, or ``None``.

    Raises:
        ValueError: The value is neither a boolean nor null.
    """
    if value is None:
        return None
    return _flag(value, where)


def _amount(value: Json, where: str) -> float:
    """Return ``value`` as a float or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as a float.

    Raises:
        ValueError: The value is not a number (a boolean counts as one).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: expected a number")
    return float(value)


def _count(value: Json, where: str) -> int:
    """Return ``value`` as an integer or fail.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.

    Returns:
        The value typed as an integer.

    Raises:
        ValueError: The value is not an integer (a boolean counts as one).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{where}: expected an integer")
    return value


def _choice(value: Json, where: str, allowed: frozenset[str]) -> str:
    """Return ``value`` when it is one of the declared enum members.

    Args:
        value: Value read from the catalog.
        where: Document location used in the error message.
        allowed: The values the catalog declares for this field.

    Returns:
        The value typed as a string.

    Raises:
        ValueError: The value is not a string, or is outside ``allowed``.
    """
    text = _text(value, where)
    if text not in allowed:
        raise ValueError(f"{where}: value {text} is outside the declared values")
    return text


def _require_keys(entry: dict[str, Json], required: frozenset[str], where: str) -> None:
    """Check a mapping for exactly the keys it is allowed to carry.

    Args:
        entry: Mapping to check.
        required: The exact key set this level accepts.
        where: Document location used in the error message.

    Returns:
        None.

    Raises:
        ValueError: A required key is missing, or a key is not in ``required``.
    """
    missing = sorted(required - set(entry))
    if missing:
        raise ValueError(f"{where}: missing key {missing[0]}")
    unknown = sorted(set(entry) - required)
    if unknown:
        raise ValueError(f"{where}: unknown key {unknown[0]}")


def _validate_weight(value: Json, where: str) -> Weight:
    """Build one :class:`Weight` from a catalog entry.

    Args:
        value: The weight entry.
        where: Document location used in the error message.

    Returns:
        The validated weight.

    Raises:
        ValueError: The entry is malformed, per the reader rule.
    """
    entry = _object(value, where)
    _require_keys(entry, WEIGHT_KEYS, where)
    return Weight(
        source=_text(entry["source"], f"{where}.source"),
        repo=_text(entry["repo"], f"{where}.repo"),
        file=_text(entry["file"], f"{where}.file"),
        gb=_amount(entry["gb"], f"{where}.gb"),
        gated=_flag_or_none(entry["gated"], f"{where}.gated"),
    )


def _validate_tool(value: Json, position: int, enums: dict[str, frozenset[str]]) -> Tool:
    """Build one :class:`Tool` from a catalog entry.

    Args:
        value: The tool entry.
        position: Index of the entry, used in the error message.
        enums: Declared value sets keyed by tool field.

    Returns:
        The validated row.

    Raises:
        ValueError: The entry is malformed, per the reader rule.
    """
    where = f"tools[{position}]"
    entry = _object(value, where)
    _require_keys(entry, TOOL_KEYS, where)
    for field, _ in ENUM_FIELDS:
        _choice(entry[field], f"{where}.{field}", enums[field])
    app_where = f"{where}.app"
    app = _object(entry["app"], app_where)
    _require_keys(app, APP_KEYS, app_where)
    weights = [
        _validate_weight(item, f"{where}.weights[{index}]")
        for index, item in enumerate(_array(entry["weights"], f"{where}.weights"))
    ]
    # Fields the renderer does not print still have to be the right shape: the
    # reader checks the whole row, not only the columns this page shows.
    _text(entry["install"], f"{where}.install")
    _text(entry["cmd"], f"{where}.cmd")
    _text(entry["graph"], f"{where}.graph")
    _text(entry["verify"], f"{where}.verify")
    _text_list(entry["nodes"], f"{where}.nodes")
    for field in ("mode", "occupancy", "deliverable"):
        _text(app[field], f"{app_where}.{field}")
    return Tool(
        tool_id=_text(entry["id"], f"{where}.id"),
        title=_text(entry["title"], f"{where}.title"),
        status=_text(entry["status"], f"{where}.status"),
        task=_text(entry["task"], f"{where}.task"),
        input_text=_text(entry["input"], f"{where}.input"),
        output_text=_text(entry["output"], f"{where}.output"),
        upstream=_text(entry["upstream"], f"{where}.upstream"),
        see_also=_text_list(entry["see_also"], f"{where}.see_also"),
        code_license=_text(entry["code_license"], f"{where}.code_license"),
        weights_license=_text(entry["weights_license"], f"{where}.weights_license"),
        commercial_use=_text(entry["commercial_use"], f"{where}.commercial_use"),
        weights=weights,
        artifact=_text(entry["artifact"], f"{where}.artifact"),
        artifact_ref=_text(entry["artifact_ref"], f"{where}.artifact_ref"),
        arm64=_text(entry["arm64"], f"{where}.arm64"),
        gb10=_text(entry["gb10"], f"{where}.gb10"),
        vram_gb=_count(entry["vram_gb"], f"{where}.vram_gb"),
        disk_gb=_count(entry["disk_gb"], f"{where}.disk_gb"),
        comfy_shape=_text(entry["comfy_shape"], f"{where}.comfy_shape"),
        gate_notes=_text(entry["gate_notes"], f"{where}.gate_notes"),
        reopen=_text(entry["reopen"], f"{where}.reopen"),
        sources=_text_list(entry["sources"], f"{where}.sources"),
    )


def validate_catalog(payload: Json) -> Catalog:
    """Check a parsed catalog against the schema and return it ready to render.

    Args:
        payload: The parsed JSON document.

    Returns:
        The validated catalog with its rows sorted by tool id.

    Raises:
        ValueError: The document is not a catalog this reader accepts; the
            message names the offending key.
    """
    document = _object(payload, "catalog")
    _require_keys(document, TOP_LEVEL_KEYS, "catalog")
    schema = _count(document["schema"], "catalog.schema")
    if schema != SUPPORTED_SCHEMA:
        raise ValueError(f"catalog.schema: expected {SUPPORTED_SCHEMA}, found {schema}")
    tier = _text(document["tier"], "catalog.tier")
    if tier != EXPECTED_TIER:
        raise ValueError(f"catalog.tier: expected {EXPECTED_TIER}, found {tier}")
    enums = {
        field: frozenset(_text_list(document[source], f"catalog.{source}"))
        for field, source in ENUM_FIELDS
    }
    rows = _array(document["tools"], "catalog.tools")
    tools = [_validate_tool(item, index, enums) for index, item in enumerate(rows)]
    seen: set[str] = set()
    duplicates: list[str] = []
    for tool in tools:
        if tool.tool_id in seen:
            duplicates.append(tool.tool_id)
        seen.add(tool.tool_id)
    if duplicates:
        raise ValueError(f"catalog.tools: duplicate tool id {duplicates[0]}")
    return Catalog(
        tier_title=_text(document["tier_title"], "catalog.tier_title"),
        updated=_text(document["updated"], "catalog.updated"),
        status_values=_text_list(document["status_values"], "catalog.status_values"),
        tools=sorted(tools, key=lambda tool: tool.tool_id),
    )


def load_catalog(path: Path) -> Catalog:
    """Read and validate the catalog at ``path``.

    Args:
        path: Catalog JSON file.

    Returns:
        The validated catalog.

    Raises:
        ValueError: The file is absent, is not valid JSON, or fails the reader
            rule.
    """
    if not path.is_file():
        raise ValueError(f"catalog not found: {path}")
    return validate_catalog(json.loads(path.read_text(encoding="utf-8")))


def _cell(value: str) -> str:
    """Make a value safe for one markdown table cell.

    Args:
        value: Cell text.

    Returns:
        The text with any pipe escaped.
    """
    return value.replace("|", "\\|")


def _gb_column(value: int) -> str:
    """Render one footprint figure for the master table.

    The column header already names the unit, so the cell is the bare number.

    Args:
        value: Catalog gigabytes; ``0`` means upstream publishes no figure.

    Returns:
        The number as text, or :data:`NOT_PUBLISHED`.
    """
    return str(value) if value else NOT_PUBLISHED


def _gb_weight(value: float) -> str:
    """Render one weight size for the card's weights line.

    Args:
        value: Catalog gigabytes; ``0`` means upstream publishes no figure.

    Returns:
        The trimmed number with its unit, or :data:`NOT_PUBLISHED`.
    """
    return f"{value:g} GB" if value else NOT_PUBLISHED


def _weight_file(value: str) -> str:
    """Render one weight ``file`` value as the shape it actually names.

    The catalog records three shapes in one field: a single path, a directory
    behind a trailing ``/``, and a shard set behind a ``*``. Wrapping all three
    in backticks as a path makes a tree and a shard set read like one file.

    Args:
        value: The catalog file value.

    Returns:
        The path in backticks, or the path behind a ``tree:`` / ``shards:``
        marker.
    """
    if value.endswith("/"):
        return f"tree: `{value}`"
    if "*" in value:
        return f"shards: `{value}`"
    return f"`{value}`"


def _weight_gating(value: bool | None) -> str:
    """Render one weight's gating state.

    Args:
        value: ``True`` gated, ``False`` ungated, ``None`` never checked.

    Returns:
        ``gated``, ``ungated``, or :data:`GATING_NOT_CHECKED`.
    """
    if value is None:
        return GATING_NOT_CHECKED
    return "gated" if value else "ungated"


def _table_cells(tool: Tool) -> list[str]:
    """Return the master-table cells for one row, in column order.

    Args:
        tool: The row.

    Returns:
        One string per column in ``TABLE_HEADER``.
    """
    return [
        tool.tool_id,
        tool.title,
        tool.status,
        tool.code_license,
        tool.weights_license,
        tool.commercial_use,
        tool.arm64,
        tool.gb10,
        tool.artifact,
        tool.comfy_shape,
        _gb_column(tool.vram_gb),
        _gb_column(tool.disk_gb),
    ]


def _weights_line(weights: list[Weight]) -> str:
    """Render the weights line of a tool card.

    Args:
        weights: The row's weight artifacts.

    Returns:
        Repo, file, size, and gating per weight, semicolon separated, or
        ``none`` when the row carries no weights.
    """
    if not weights:
        return "none"
    parts = [
        f"`{weight.repo}` / {_weight_file(weight.file)} "
        f"({_gb_weight(weight.gb)}, {_weight_gating(weight.gated)})"
        for weight in weights
    ]
    return "; ".join(parts)


def _header(catalog: Catalog) -> list[str]:
    """Return the frontmatter and page chrome.

    Args:
        catalog: The validated catalog.

    Returns:
        Markdown lines for the page head.
    """
    return [
        "---",
        "title: NVIDIA lab tier reference",
        (
            "description: \"Generated per-row reference for the opt-in NVIDIA lab "
            "tier: status, licenses, artifact, arm64, GB10, footprint, and the "
            "reopen condition for every catalog row.\""
        ),
        "tags: [nvidia, generated, reference, license, splat, world-models]",
        "---",
        "",
        f"# {catalog.tier_title} tier reference",
        "",
        "**What's on this page**",
        "",
        "- **Rows by status** - every tool id grouped under the status it carries",
        "- **Master table** - licenses, artifact, platform, and footprint per row",
        "- **Tool cards** - task, input, output, weights, gate notes, and the reopen sentence",
        "",
        "**What this enables**",
        "",
        "- **Reading** one row without opening the catalog JSON",
        "- **Telling** an installable row from a card that only records a verdict",
        "- **Quoting** the gate notes and the reopen condition a decision rests on",
        "",
        f"Catalog schema {SUPPORTED_SCHEMA}, tier `{EXPECTED_TIER}`, updated "
        f"{catalog.updated}. The operator-facing page is "
        "[NVIDIA lab tier](../../nvidia-lab.md).",
        "",
        "> Generated from `custom_nodes/ez_nvidia_lab/catalog.json`. Do not hand-edit "
        "this file: edit the catalog, then run "
        "`bazelisk run //docs:generate_nvidia_lab` and commit the diff.",
        "",
    ]


def _status_section(catalog: Catalog) -> list[str]:
    """Return the per-status grouping.

    Args:
        catalog: The validated catalog.

    Returns:
        Markdown lines, one subsection per declared status.
    """
    lines = ["## Rows by status", ""]
    for status in catalog.status_values:
        rows = [tool for tool in catalog.tools if tool.status == status]
        lines.append(f"### {status}")
        lines.append("")
        if rows:
            lines.extend(f"- `{tool.tool_id}` - {tool.title}" for tool in rows)
        else:
            lines.append("- none")
        lines.append("")
    return lines


def _table(tools: list[Tool]) -> list[str]:
    """Return the master table.

    Args:
        tools: Rows in render order.

    Returns:
        Markdown lines for one twelve-column table.
    """
    lines = ["## Master table", ""]
    lines.append("| " + " | ".join(TABLE_HEADER) + " |")
    lines.append("| " + " | ".join("---" for _ in TABLE_HEADER) + " |")
    for tool in tools:
        lines.append("| " + " | ".join(_cell(cell) for cell in _table_cells(tool)) + " |")
    lines.append("")
    return lines


def _card(tool: Tool) -> list[str]:
    """Return one tool card.

    Args:
        tool: The row.

    Returns:
        Markdown lines for the card.
    """
    lines = [f"### `{tool.tool_id}` - {tool.title}", ""]
    lines.append(f"- **Task**: {tool.task}")
    lines.append(f"- **Input**: {tool.input_text}")
    lines.append(f"- **Output**: {tool.output_text}")
    lines.append(f"- **Upstream**: <{tool.upstream}>")
    if tool.see_also:
        lines.append("- **See also**: " + ", ".join(f"<{url}>" for url in tool.see_also))
    else:
        lines.append("- **See also**: none")
    lines.append(f"- **Weights**: {_weights_line(tool.weights)}")
    lines.append(f"- **Artifact ref**: `{tool.artifact_ref}`" if tool.artifact_ref else "- **Artifact ref**: none")
    lines.append(f"- **Gate notes**: {tool.gate_notes}")
    lines.append(f"- **Reopen**: {tool.reopen}")
    lines.append("")
    lines.append("**Sources**")
    lines.append("")
    lines.extend(f"- <{url}>" for url in tool.sources)
    lines.append("")
    return lines


def render_tier(catalog: Catalog) -> str:
    """Build the whole generated page.

    Args:
        catalog: The validated catalog.

    Returns:
        Page text with LF endings and one trailing newline.
    """
    lines = _header(catalog)
    lines.extend(_status_section(catalog))
    lines.extend(_table(catalog.tools))
    lines.extend(["## Tool cards", ""])
    for tool in catalog.tools:
        lines.extend(_card(tool))
    text = "\n".join(lines)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"


def resolve_catalog_path(cli_value: str | None) -> Path:
    """Pick the catalog file to read.

    Args:
        cli_value: The ``--catalog`` value, when the operator passed one.

    Returns:
        The flag path, else ``$EZ_NVIDIA_LAB_CATALOG``, else the repo default.
    """
    if cli_value is not None:
        return Path(cli_value)
    from_env = os.environ.get(CATALOG_ENV, "")
    if from_env:
        return Path(from_env)
    return DEFAULT_CATALOG_PATH


def resolve_output_path(cli_value: str | None) -> Path:
    """Pick the page to write.

    Args:
        cli_value: The ``--out`` value, when the caller passed one.

    Returns:
        The flag path, else the committed generated page.
    """
    if cli_value is not None:
        return Path(cli_value)
    return OUTPUT_FILE


def main(argv: list[str] | None = None) -> int:
    """Generate the tier reference page.

    Args:
        argv: Optional argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit status (always 0 on success).

    Raises:
        ValueError: The catalog failed the reader rule.
    """
    parser = argparse.ArgumentParser(description="Generate docs/generated/nvidia-lab/tier.md")
    parser.add_argument("--catalog", default=None, help=f"catalog JSON (default: ${CATALOG_ENV} or custom_nodes/ez_nvidia_lab/catalog.json)")
    parser.add_argument("--out", default=None, help="output page (default: docs/generated/nvidia-lab/tier.md)")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    catalog = load_catalog(resolve_catalog_path(args.catalog))
    text = render_tier(catalog)
    out_path = resolve_output_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = out_path.read_text(encoding="utf-8") if out_path.is_file() else ""
    if existing == text:
        print(f"NVIDIA lab tier reference is up to date: {out_path}")
        return 0
    out_path.write_text(text, encoding="utf-8")
    print(f"Generated {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
