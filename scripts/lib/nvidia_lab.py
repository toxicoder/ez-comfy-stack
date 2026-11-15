#!/usr/bin/env python3
"""Typed reader and query CLI for the nvidia-lab opt-in tier catalog.

``custom_nodes/ez_nvidia_lab/catalog.json`` is the single source of truth for
the tier: what each tool is, whether it is installable on this GB10 host, and
what the operator has to run to get it. This module is the only reader. It
fails closed: a document the schema does not describe raises
:class:`CatalogError` instead of degrading into a half-trusted row that a shell
verb or a node pack would act on.

Globals:
  None. Stdlib only; nothing touches disk until a function is called.

Arguments:
  python3 scripts/lib/nvidia_lab.py [--catalog PATH] VERB [ARGS]

  --catalog  Catalog file to read. Defaults to :func:`catalog_path`, which
             honours ``EZ_NVIDIA_LAB_CATALOG``.
  VERB       One of ``list``, ``ids``, ``status``, ``json``, ``fields``,
             ``check``.
  ARGS       The tool id for ``status`` / ``json`` / ``fields``, plus the
             comma-separated field list for ``fields``.

Outputs:
  ``list`` prints ``<id>TAB<status>TAB<title>`` per tool, ``ids`` one id per
  line (both sorted by id); ``status`` prints the status token; ``json`` the
  tool object as compact JSON; ``fields`` ``key=value`` lines; ``check``
  ``ok <n> tools``. Every failure reason goes to stderr.

Returns:
  0 success, 1 catalog missing or invalid, 2 unknown verb, tool id, or field.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ez_common import Json, JsonObject, JsonList, JsonMap

CATALOG_RELPATH: str = "custom_nodes/ez_nvidia_lab/catalog.json"
"""Repo-relative catalog path (kept under ``custom_nodes`` for the compose mount)."""

CATALOG_ENV: str = "EZ_NVIDIA_LAB_CATALOG"
"""Environment variable that overrides the catalog path (fixtures, tests)."""

CATALOG_SCHEMA: int = 1
"""The only catalog schema version this reader accepts."""

GRAPH_PREFIX: str = "labs/nvidia/"
"""Graph-name prefix every tool row must carry before its id."""

OPT_IN_STATUS: str = "opt-in"
"""The single status an operator may install or run."""

BIN: str = "nvidia_lab"
"""Prefix on every stderr line the CLI writes."""

VERBS: tuple[str, ...] = ("list", "ids", "status", "json", "fields", "check")
"""Query verbs the CLI serves."""

HELP_FLAGS: frozenset[str] = frozenset({"--help", "-h"})
"""Flags that print usage instead of querying."""

USAGE: str = f"usage: {BIN}.py [--catalog PATH] {'|'.join(VERBS)} [ARGS]"
"""One-line usage string for stdout and for a bad-argument message."""

_TOP_KEYS: tuple[str, ...] = ("schema", "tier", "tier_title", "updated", "tools")
"""Top-level keys a schema-1 catalog must carry."""

TOOL_ENUM_KEYS: dict[str, str] = {
    "status": "status",
    "commercial_use": "commercial",
    "arm64": "arm64",
    "artifact": "artifact",
    "comfy_shape": "comfy_shape",
}
"""Tool key -> stem of the ``<stem>_values`` list in the file that bounds it."""

_VALUES_KEYS: tuple[str, ...] = tuple(f"{stem}_values" for stem in TOOL_ENUM_KEYS.values())
"""Top-level enum lists the reader validates tool enums against."""

TOP_KEYS: frozenset[str] = frozenset(_TOP_KEYS) | frozenset(_VALUES_KEYS)
"""Every key a schema-1 catalog may carry at the top level."""

TOP_REQUIRED_KEYS: frozenset[str] = frozenset(_TOP_KEYS) | frozenset(_VALUES_KEYS)
"""Top-level keys a schema-1 catalog cannot be without."""

TOOL_KEYS: tuple[str, ...] = (
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
)
"""Every tool key a schema-1 row must carry, in catalog order."""

TOOL_KEY_SET: frozenset[str] = frozenset(TOOL_KEYS)
"""The tool keys as a membership set."""

WEIGHT_KEYS: frozenset[str] = frozenset({"source", "repo", "file", "gb", "gated"})
"""Keys one weight row must carry and may not exceed."""

APP_KEYS: frozenset[str] = frozenset({"mode", "occupancy", "deliverable"})
"""Keys one App block must carry and may not exceed."""

APP_FIELD_KEYS: tuple[str, ...] = ("mode", "occupancy", "deliverable")
"""App field names the ``fields`` verb accepts through ``app.<name>``."""

APP_FIELD_PREFIX: str = "app."
"""Dotted prefix that reaches one App field from the ``fields`` verb."""

GB10_VALUES: frozenset[str] = frozenset({"verified", "unverified", "unsupported"})
"""Allowed ``gb10`` tokens (the file carries no list for this enum)."""

INSTALL_VALUES: frozenset[str] = frozenset(
    {"docker-pull", "git-clone", "pip-install", "none"}
)
"""Allowed ``install`` tokens (the file carries no list for this enum)."""

OCCUPANCY_VALUES: frozenset[str] = frozenset(
    {"llm", "klein", "wan", "ltx", "trellis", "audio", "film", "none"}
)
"""Allowed ``app.occupancy`` tokens; every nvidia-lab App uses ``none``.

The GPU work runs outside the Comfy process, so no App in this tier claims the
XOR. This is the catalog's own vocabulary, not
:data:`ez_common.occupancy.VALID_MODES`: it adds ``llm`` / ``audio`` / ``film``
/ ``none`` and drops the idle and desk modes.
"""


class CatalogError(ValueError):
    """The catalog exists but does not satisfy the schema-1 contract."""


@dataclass(frozen=True)
class WeightRecord:
    """One model file a tool needs.

    Attributes:
        source: Where the file is fetched from (``huggingface``, ``github``).
        repo: Owning repo or organisation slug.
        file: Filename inside that repo.
        gb: Size in gigabytes; ``0`` means upstream publishes no figure.
        gated: Whether the fetch needs an accepted license first; ``None``
            means nobody checked the repo's gating.
    """

    source: str
    repo: str
    file: str
    gb: float
    gated: bool | None

    def label(self) -> str:
        """Render the weight the way the CLI and the operator see it.

        Returns:
            ``repo/file@GB`` with the size trimmed of a trailing ``.0``.
        """
        return f"{self.repo}/{self.file}@{self.gb:g}"


@dataclass(frozen=True)
class AppConfig:
    """What the tool's Comfy App hands the operator.

    Attributes:
        mode: Short verb phrase describing what the App does.
        occupancy: GPU occupancy the App expects; ``none`` for this tier.
        deliverable: The sentence the App shows as its outcome.
    """

    mode: str
    occupancy: str
    deliverable: str

    def label(self) -> str:
        """Render the whole App block as one field value.

        Returns:
            ``mode|occupancy|deliverable``.
        """
        return f"{self.mode}|{self.occupancy}|{self.deliverable}"

    def field(self, name: str) -> str | None:
        """Read one App field by name.

        Args:
            name: One of :data:`APP_FIELD_KEYS`.

        Returns:
            The value text, or ``None`` when ``name`` is not an App field.
        """
        if name == "mode":
            return self.mode
        if name == "occupancy":
            return self.occupancy
        if name == "deliverable":
            return self.deliverable
        return None


@dataclass(frozen=True)
class Tool:
    """One catalog row: a tool in the nvidia-lab tier.

    The fields are the catalog keys, in catalog order, so ``json <id>`` hands
    back exactly the object the file carries.

    Attributes:
        id: Kebab-case tool id; unique, and the tail of ``graph``.
        title: Display name.
        status: One of the file's ``status_values``.
        task: One sentence on what the tool does.
        input: What the operator supplies.
        output: What the tool produces.
        upstream: Upstream project URL.
        see_also: Further URLs (may be empty).
        code_license: License the source ships under.
        weights_license: License the weights ship under, or ``none``.
        commercial_use: One of the file's ``commercial_values``.
        weights: Model files the tool needs (may be empty).
        artifact: One of the file's ``artifact_values``.
        artifact_ref: Pull ref or git URL, or ``""``.
        arm64: One of the file's ``arm64_values``.
        gb10: Whether the tool is verified on GB10.
        install: How the operator installs it.
        cmd: Operator hint command, or ``""``.
        vram_gb: VRAM the tool needs.
        disk_gb: Disk the tool needs.
        comfy_shape: One of the file's ``comfy_shape_values``.
        nodes: Node class names this tool uses.
        graph: ``labs/nvidia/<id>``, no ``.json``.
        app: The App block.
        gate_notes: Why the row is blocked, or ``""``.
        reopen: The condition that reopens a blocked row.
        verify: How to prove a working install.
        sources: URLs the verdict was researched from.
    """

    id: str
    title: str
    status: str
    task: str
    input: str
    output: str
    upstream: str
    see_also: list[str]
    code_license: str
    weights_license: str
    commercial_use: str
    weights: list[WeightRecord]
    artifact: str
    artifact_ref: str
    arm64: str
    gb10: str
    install: str
    cmd: str
    vram_gb: int
    disk_gb: int
    comfy_shape: str
    nodes: list[str]
    graph: str
    app: AppConfig
    gate_notes: str
    reopen: str
    verify: str
    sources: list[str]


@dataclass(frozen=True)
class Catalog:
    """The whole validated catalog document.

    Attributes:
        schema: Schema version, always :data:`CATALOG_SCHEMA` once parsed.
        tier: Tier id (``nvidia-lab``).
        tier_title: Display name for the tier.
        updated: ``YYYY-MM-DD`` the catalog was last researched.
        tools: Every tool row, in file order.
    """

    schema: int
    tier: str
    tier_title: str
    updated: str
    tools: list[Tool]


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


def catalog_path(*, env: Mapping[str, str] | None = None) -> Path:
    """Locate the catalog file.

    ``EZ_NVIDIA_LAB_CATALOG`` overrides the repo default so a test or a
    container can point the reader at a fixture.

    Args:
        env: Environment mapping to read. Defaults to :data:`os.environ`.

    Returns:
        Path to the catalog; existence is not checked here.
    """
    source = os.environ if env is None else env
    raw = (source.get(CATALOG_ENV) or "").strip()
    if raw:
        return Path(raw)
    return _repo_root() / CATALOG_RELPATH


def _fail(where: str, problem: str) -> CatalogError:
    """Build a catalog error that names the offending location.

    Args:
        where: Dotted location in the document (``tools[3].weights[0].gb``).
        problem: What is wrong there.

    Returns:
        The error for the caller to raise.
    """
    return CatalogError(f"{where}: {problem}")


def _loads(path: Path) -> Json:
    """Parse a catalog file as JSON.

    Args:
        path: File to read.

    Returns:
        The parsed document.

    Raises:
        CatalogError: The file is not valid JSON.
        OSError: The file cannot be read.
    """
    try:
        parsed: Json = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise _fail(str(path), f"invalid JSON: {exc}") from exc
    return parsed


def _as_map(value: Json, where: str) -> JsonMap:
    """Narrow a parsed value to a JSON object.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The value read as a mapping.

    Raises:
        CatalogError: The value is not an object.
    """
    if not isinstance(value, dict):
        raise _fail(where, "expected an object")
    return value


def _as_list(value: Json, where: str) -> JsonList:
    """Narrow a parsed value to a JSON array.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The value read as a sequence.

    Raises:
        CatalogError: The value is not an array.
    """
    if not isinstance(value, list):
        raise _fail(where, "expected an array")
    return value


def _as_str(value: Json, where: str) -> str:
    """Narrow a parsed value to a string.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The string.

    Raises:
        CatalogError: The value is not a string.
    """
    if not isinstance(value, str):
        raise _fail(where, f"expected a string, got {type(value).__name__}")
    return value


def _as_str_list(value: Json, where: str) -> list[str]:
    """Narrow a parsed value to a list of strings.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The string list.

    Raises:
        CatalogError: The value is not an array of strings.
    """
    return [
        _as_str(item, f"{where}[{index}]") for index, item in enumerate(_as_list(value, where))
    ]


def _as_int(value: Json, where: str) -> int:
    """Narrow a parsed value to an integer.

    ``bool`` is rejected on purpose: ``True`` is an ``int`` to Python, but a
    gigabyte figure written as a boolean is a typo, not a size.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The integer.

    Raises:
        CatalogError: The value is not an integer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise _fail(where, f"expected an integer, got {type(value).__name__}")
    return value


def _as_float(value: Json, where: str) -> float:
    """Narrow a parsed value to a number.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The value as a float (``2`` and ``2.0`` are the same size).

    Raises:
        CatalogError: The value is not a number.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _fail(where, f"expected a number, got {type(value).__name__}")
    return float(value)


def _as_bool(value: Json, where: str) -> bool:
    """Narrow a parsed value to a boolean.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The boolean.

    Raises:
        CatalogError: The value is not a boolean.
    """
    if not isinstance(value, bool):
        raise _fail(where, f"expected a boolean, got {type(value).__name__}")
    return value


def _as_bool_or_none(value: Json, where: str) -> bool | None:
    """Narrow a parsed value to a boolean or to ``None``.

    ``None`` is a value of its own, not a missing one: it records that nobody
    checked the field, which is different from a checked answer of ``False``.

    Args:
        value: Parsed value.
        where: Location used in the failure message.

    Returns:
        The boolean, or ``None`` when the document says ``null``.

    Raises:
        CatalogError: The value is neither a boolean nor ``null``.
    """
    if value is None:
        return None
    return _as_bool(value, where)


def _as_enum(value: Json, where: str, allowed: frozenset[str], label: str) -> str:
    """Narrow a parsed value to one of the tokens the schema allows.

    Args:
        value: Parsed value.
        where: Location used in the failure message.
        allowed: Tokens the schema allows, read from the file's own
            ``*_values`` list or from the fixed vocabulary this module pins.
        label: Field name named in the failure message.

    Returns:
        The token.

    Raises:
        CatalogError: The value is not a string, or not one of ``allowed``.
    """
    token = _as_str(value, where)
    if token not in allowed:
        raise _fail(where, f"{label} {token!r} is not one of {sorted(allowed)}")
    return token


def _check_keys(doc: JsonMap, where: str, keys: frozenset[str]) -> None:
    """Reject unknown and missing keys in one parsed object.

    Args:
        doc: Parsed object.
        where: Location used in the failure message.
        keys: The exact key set this level must hold.

    Raises:
        CatalogError: A key is unknown, or a required key is absent.
    """
    for key in sorted(doc):
        if key not in keys:
            raise _fail(where, f"unknown key {key}")
    missing = sorted(keys - set(doc))
    if missing:
        raise _fail(where, f"missing key {missing[0]}")


def _load_weight(value: Json, where: str) -> WeightRecord:
    """Validate one weight row.

    Args:
        value: Parsed weight object.
        where: Location used in the failure message.

    Returns:
        The validated weight.

    Raises:
        CatalogError: A key or type is wrong, or ``gb`` is negative.
    """
    doc = _as_map(value, where)
    _check_keys(doc, where, WEIGHT_KEYS)
    gb = _as_float(doc["gb"], f"{where}.gb")
    if gb < 0.0:
        raise _fail(f"{where}.gb", f"expected a size of 0 or more, got {gb:g}")
    return WeightRecord(
        source=_as_str(doc["source"], f"{where}.source"),
        repo=_as_str(doc["repo"], f"{where}.repo"),
        file=_as_str(doc["file"], f"{where}.file"),
        gb=gb,
        gated=_as_bool_or_none(doc["gated"], f"{where}.gated"),
    )


def _load_app(value: Json, where: str) -> AppConfig:
    """Validate one App block.

    Args:
        value: Parsed App object.
        where: Location used in the failure message.

    Returns:
        The validated App block.

    Raises:
        CatalogError: A key or type is wrong, the mode is empty, or the
            occupancy is outside :data:`OCCUPANCY_VALUES`.
    """
    doc = _as_map(value, where)
    _check_keys(doc, where, APP_KEYS)
    mode = _as_str(doc["mode"], f"{where}.mode")
    if not mode:
        raise _fail(f"{where}.mode", "expected a non-empty mode")
    return AppConfig(
        mode=mode,
        occupancy=_as_enum(doc["occupancy"], f"{where}.occupancy", OCCUPANCY_VALUES, "occupancy"),
        deliverable=_as_str(doc["deliverable"], f"{where}.deliverable"),
    )


def _load_tool(value: Json, where: str, enums: dict[str, frozenset[str]]) -> Tool:
    """Validate one tool row against the enum lists the file declares.

    Args:
        value: Parsed tool object.
        where: Location used in the failure message.
        enums: Allowed tokens per tool enum key, read from the document.

    Returns:
        The validated tool.

    Raises:
        CatalogError: A key or type is wrong, an enum token is outside its
            declared values, or ``graph`` does not name its own id.
    """
    doc = _as_map(value, where)
    _check_keys(doc, where, TOOL_KEY_SET)
    tool_id = _as_str(doc["id"], f"{where}.id")
    graph = _as_str(doc["graph"], f"{where}.graph")
    expected_graph = f"{GRAPH_PREFIX}{tool_id}"
    if graph != expected_graph:
        raise _fail(f"{where}.graph", f"expected {expected_graph}, got {graph}")
    return Tool(
        id=tool_id,
        title=_as_str(doc["title"], f"{where}.title"),
        status=_as_enum(doc["status"], f"{where}.status", enums["status"], "status"),
        task=_as_str(doc["task"], f"{where}.task"),
        input=_as_str(doc["input"], f"{where}.input"),
        output=_as_str(doc["output"], f"{where}.output"),
        upstream=_as_str(doc["upstream"], f"{where}.upstream"),
        see_also=_as_str_list(doc["see_also"], f"{where}.see_also"),
        code_license=_as_str(doc["code_license"], f"{where}.code_license"),
        weights_license=_as_str(doc["weights_license"], f"{where}.weights_license"),
        commercial_use=_as_enum(
            doc["commercial_use"],
            f"{where}.commercial_use",
            enums["commercial_use"],
            "commercial_use",
        ),
        weights=[
            _load_weight(item, f"{where}.weights[{index}]")
            for index, item in enumerate(_as_list(doc["weights"], f"{where}.weights"))
        ],
        artifact=_as_enum(doc["artifact"], f"{where}.artifact", enums["artifact"], "artifact"),
        artifact_ref=_as_str(doc["artifact_ref"], f"{where}.artifact_ref"),
        arm64=_as_enum(doc["arm64"], f"{where}.arm64", enums["arm64"], "arm64"),
        gb10=_as_enum(doc["gb10"], f"{where}.gb10", GB10_VALUES, "gb10"),
        install=_as_enum(doc["install"], f"{where}.install", INSTALL_VALUES, "install"),
        cmd=_as_str(doc["cmd"], f"{where}.cmd"),
        vram_gb=_as_int(doc["vram_gb"], f"{where}.vram_gb"),
        disk_gb=_as_int(doc["disk_gb"], f"{where}.disk_gb"),
        comfy_shape=_as_enum(
            doc["comfy_shape"], f"{where}.comfy_shape", enums["comfy_shape"], "comfy_shape"
        ),
        nodes=_as_str_list(doc["nodes"], f"{where}.nodes"),
        graph=graph,
        app=_load_app(doc["app"], f"{where}.app"),
        gate_notes=_as_str(doc["gate_notes"], f"{where}.gate_notes"),
        reopen=_as_str(doc["reopen"], f"{where}.reopen"),
        verify=_as_str(doc["verify"], f"{where}.verify"),
        sources=_as_str_list(doc["sources"], f"{where}.sources"),
    )


def load_catalog(path: Path) -> Catalog:
    """Read and validate the nvidia-lab catalog.

    Every rule in the schema contract is checked here and nowhere else: the
    schema version, the exact key set at each level, each enum against the
    ``*_values`` list the file itself carries, unique ids, a ``graph`` that
    names its own id, a weight size that is never negative, a non-empty App
    mode, and an occupancy inside :data:`OCCUPANCY_VALUES`.

    Args:
        path: Catalog file to read.

    Returns:
        The validated catalog.

    Raises:
        CatalogError: The document is not JSON or breaks the schema-1 contract.
        OSError: The file cannot be read.
    """
    source = str(path)
    doc = _as_map(_loads(path), source)
    _check_keys(doc, source, TOP_REQUIRED_KEYS)
    schema = _as_int(doc["schema"], "schema")
    if schema != CATALOG_SCHEMA:
        raise _fail("schema", f"expected {CATALOG_SCHEMA}, got {schema}")
    enums = {
        key: frozenset(_as_str_list(doc[f"{stem}_values"], f"{stem}_values"))
        for key, stem in TOOL_ENUM_KEYS.items()
    }
    tools: list[Tool] = []
    seen: set[str] = set()
    for index, item in enumerate(_as_list(doc["tools"], "tools")):
        tool = _load_tool(item, f"tools[{index}]", enums)
        if tool.id in seen:
            raise _fail(f"tools[{index}].id", f"duplicate id {tool.id}")
        seen.add(tool.id)
        tools.append(tool)
    return Catalog(
        schema=schema,
        tier=_as_str(doc["tier"], "tier"),
        tier_title=_as_str(doc["tier_title"], "tier_title"),
        updated=_as_str(doc["updated"], "updated"),
        tools=tools,
    )


def tool_by_id(catalog: Catalog, tool_id: str) -> Tool:
    """Find one tool by id.

    Args:
        catalog: Parsed catalog.
        tool_id: Kebab-case id to look up.

    Returns:
        The matching tool.

    Raises:
        CatalogError: No tool carries that id.
    """
    for tool in catalog.tools:
        if tool.id == tool_id:
            return tool
    raise CatalogError(f"unknown tool id {tool_id!r}")


def opt_in(catalog: Catalog) -> list[Tool]:
    """List the tools an operator may actually install and run.

    Args:
        catalog: Parsed catalog.

    Returns:
        Every tool whose status is :data:`OPT_IN_STATUS`, in file order.
    """
    return [tool for tool in catalog.tools if tool.status == OPT_IN_STATUS]


def status_counts(catalog: Catalog) -> dict[str, int]:
    """Tally the tools by status.

    Only statuses the catalog really carries appear, in first-seen order, so
    the counts always add up to the tool total.

    Args:
        catalog: Parsed catalog.

    Returns:
        Status token -> number of tools.
    """
    counts: dict[str, int] = {}
    for tool in catalog.tools:
        counts[tool.status] = counts.get(tool.status, 0) + 1
    return counts


def _render_value(value: Json) -> str:
    """Render one parsed catalog value as ``fields`` verb text.

    Args:
        value: A value taken from a tool object.

    Returns:
        Scalars as text (floats trimmed, booleans lowercase), a list joined by
        commas, an object joined by pipes, and ``None`` as the empty string.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{value:g}" if isinstance(value, float) else str(value)
    if isinstance(value, list):
        return ",".join(_render_value(item) for item in value)
    if isinstance(value, dict):
        return "|".join(_render_value(item) for item in value.values())
    return ""


def _field_text(tool: Tool, key: str) -> str | None:
    """Render one requested field of one tool.

    ``weights`` renders each file as ``repo/file@GB``, ``app`` renders the
    whole block as ``mode|occupancy|deliverable``, and ``app.<field>`` reaches
    a single App field.

    Args:
        tool: The tool the field was asked for.
        key: A catalog key, or one of :data:`APP_FIELD_KEYS` behind
            :data:`APP_FIELD_PREFIX`.

    Returns:
        The value text, or ``None`` when ``key`` is not a field of the row.
    """
    if key.startswith(APP_FIELD_PREFIX):
        return tool.app.field(key[len(APP_FIELD_PREFIX) :])
    if key not in TOOL_KEY_SET:
        return None
    if key == "weights":
        return ",".join(weight.label() for weight in tool.weights)
    if key == "app":
        return tool.app.label()
    return _render_value(_tool_row(tool)[key])


def _tool_row(tool: Tool) -> JsonObject:
    """Render one tool as the catalog object it was parsed from.

    Args:
        tool: The tool to render.

    Returns:
        Field-name -> value mapping in catalog key order.
    """
    row: JsonObject = asdict(tool)
    return row


def _run_fields(tool: Tool, keys: list[str]) -> int:
    """Print ``key=value`` lines for the requested fields.

    Args:
        tool: The tool the keys were asked for.
        keys: Field names, already split on the comma.

    Returns:
        Process status: 0 when every key resolved, 2 on the first unknown one.
    """
    lines: list[str] = []
    for key in keys:
        text = _field_text(tool, key)
        if text is None:
            print(f"{BIN}: unknown field {key!r} for tool {tool.id}", file=sys.stderr)
            return 2
        lines.append(f"{key}={text}")
    print("\n".join(lines))
    return 0


def _run_id_verb(catalog: Catalog, args: list[str]) -> int:
    """Serve the verbs that name one tool.

    Args:
        catalog: Parsed catalog.
        args: ``[verb]``, or ``[verb, id]``, plus the key list for ``fields``.

    Returns:
        Process status: 0 on success, 2 for a missing or unknown id or key.
    """
    verb = args[0]
    if len(args) < 2:
        print(f"{BIN}: {verb} needs a tool id", file=sys.stderr)
        return 2
    try:
        tool = tool_by_id(catalog, args[1])
    except CatalogError as exc:
        print(f"{BIN}: {exc}", file=sys.stderr)
        return 2
    if verb == "status":
        print(tool.status)
        return 0
    if verb == "json":
        print(json.dumps(_tool_row(tool), separators=(",", ":")))
        return 0
    if len(args) < 3:
        print(f"{BIN}: fields needs a comma-separated key list", file=sys.stderr)
        return 2
    return _run_fields(tool, args[2].split(","))


def main(argv: list[str]) -> int:
    """Run one query verb against the catalog.

    Args:
        argv: Arguments after the program name.

    Returns:
        Process status: 0 success, 1 catalog missing or invalid, 2 unknown
        verb, tool id, or field name.
    """
    args = list(argv)
    if args and args[0] in HELP_FLAGS:
        print(USAGE)
        return 0
    path: Path | None = None
    if args and args[0] == "--catalog":
        if len(args) < 2:
            print(f"{BIN}: --catalog needs a path", file=sys.stderr)
            return 2
        path = Path(args[1])
        args = args[2:]
    if not args:
        print(f"{BIN}: {USAGE}", file=sys.stderr)
        return 2
    verb = args[0]
    if verb not in VERBS:
        print(f"{BIN}: unknown verb {verb!r}; {USAGE}", file=sys.stderr)
        return 2
    if path is None:
        path = catalog_path()
    try:
        catalog = load_catalog(path)
    except CatalogError as exc:
        print(f"{BIN}: {path}: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"{BIN}: {path}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    if verb == "check":
        print(f"ok {len(catalog.tools)} tools")
        return 0
    if verb == "list":
        for tool in sorted(catalog.tools, key=lambda row: row.id):
            print(f"{tool.id}\t{tool.status}\t{tool.title}")
        return 0
    if verb == "ids":
        for tool in sorted(catalog.tools, key=lambda row: row.id):
            print(tool.id)
        return 0
    return _run_id_verb(catalog, args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
