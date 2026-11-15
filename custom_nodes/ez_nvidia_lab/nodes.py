"""ComfyUI nodes: the NVIDIA lab tier cards, preflight, and job runner.

Import is hermetic on purpose. Comfy auto-loads every pack under
``custom_nodes/`` into every boot, so this module imports stdlib only at
module scope and lazy-imports ``ez_common`` inside functions after
``ensure_custom_nodes_path()``.

The catalog is read with this module's own ``json`` reader. The sibling
reader under the scripts tree is deliberately not imported: compose mounts
only ``workflows/`` and ``custom_nodes/`` into the container, so nothing
under the scripts tree is reachable at boot. A missing or malformed catalog
degrades to a node error string; it never raises at import or at Queue.

Subprocess goes through an injectable
:class:`~ez_common.protocols.SubprocessRunner`, so tests stub the process
instead of spawning one. There is no network probe anywhere in this pack:
"reachable" is checked as the shape of a row's artifact ref.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict, TypeAlias, cast

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes, CompletedProc, Json, JsonMap, SubprocessRunner

# Comfy menu category for every node in this pack.
CATEGORY: Final[str] = "EZ Comfy/NVIDIA Lab"

PACK_ID: Final[str] = "ez_nvidia_lab"
"""Prefix for operator status lines."""

CATALOG_ENV: Final[str] = "EZ_NVIDIA_LAB_CATALOG"
"""Environment override for the catalog path (tests and lab hosts)."""

TIER_ID: Final[str] = "nvidia-lab"
"""The only tier this pack speaks."""

SCHEMA_VERSION: Final[int] = 1
"""Catalog schema this reader accepts, and the only one that exists."""

PACK_DIR: Final[Path] = Path(__file__).resolve().parent
"""This pack's directory."""

REPO_ROOT: Final[Path] = PACK_DIR.parents[1]
"""Repository root as seen from ``custom_nodes/ez_nvidia_lab/nodes.py``."""

DEFAULT_CATALOG_PATH: Final[Path] = PACK_DIR / "catalog.json"
"""Catalog location when :data:`CATALOG_ENV` is unset."""

DEFAULT_CLI_PATH: Final[Path] = REPO_ROOT / "scripts" / "manage.sh"
"""Operator CLI the job node shells out to (host-side, not in the image)."""

CLI_VERB: Final[str] = "nvidia-lab"
"""Verb the operator CLI exposes this tier under."""

AARCH64: Final[str] = "aarch64"
"""The only architecture this tier is built for."""

OPT_IN: Final[str] = "opt-in"
"""The only row status the job node is allowed to run."""

DETAIL_VALUES: Final[tuple[str, ...]] = ("list", "table")
"""Widget values for the catalog node's ``detail`` combo."""

TOP_KEYS: Final[tuple[str, ...]] = (
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
)
"""Required top-level catalog keys; anything else is rejected."""

TOOL_KEYS: Final[tuple[str, ...]] = (
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
"""Required keys on every tool row; anything else is rejected."""

WEIGHT_KEYS: Final[tuple[str, ...]] = ("source", "repo", "file", "gb", "gated")
"""Required keys on every weight entry."""

APP_KEYS: Final[tuple[str, ...]] = ("mode", "occupancy", "deliverable")
"""Required keys on every app entry."""

STATUS_VALUES: Final[tuple[str, ...]] = (
    "opt-in",
    "blocked-license",
    "blocked-platform",
    "deferred",
)
"""Row statuses the reader accepts."""

COMMERCIAL_VALUES: Final[tuple[str, ...]] = (
    "permitted",
    "conditional",
    "non-commercial",
    "unknown",
    "none",
)
"""Commercial-use vocabularies the reader accepts."""

ARM64_VALUES: Final[tuple[str, ...]] = (
    "published",
    "partial",
    "absent",
    "unknown",
    "na",
)
"""arm64 availability vocabularies the reader accepts."""

ARTIFACT_VALUES: Final[tuple[str, ...]] = (
    "custom-nodes",
    "source-build",
    "container-image",
    "host-cli",
    "viewer",
    "paper-only",
)
"""Artifact kinds the reader accepts."""

COMFY_SHAPE_VALUES: Final[tuple[str, ...]] = (
    "node-pack",
    "host-cli",
    "sidecar",
    "viewer",
    "none",
)
"""Comfy integration shapes the reader accepts."""

INSTALL_VALUES: Final[tuple[str, ...]] = (
    "docker-pull",
    "git-clone",
    "pip-install",
    "none",
)
"""Install verbs the reader accepts."""

GB10_VALUES: Final[tuple[str, ...]] = ("verified", "unverified", "unsupported")
"""GB10 verdicts the reader accepts."""

OCCUPANCY_VALUES: Final[tuple[str, ...]] = (
    "llm",
    "klein",
    "wan",
    "ltx",
    "trellis",
    "audio",
    "film",
    "none",
)
"""Occupancies an app entry may name; this tier only ever uses ``none``."""

INSTALL_BINARIES: Final[dict[str, str]] = {
    "docker-pull": "docker",
    "git-clone": "git",
    "pip-install": "pip",
    "none": "",
}
"""External binary each install verb needs on PATH ("" for none)."""

CONTAINER_ARTIFACT = "container-image"
"""Artifact kind whose ref is a pull spec rather than a clone URL."""

OUTPUT_CLIP: Final[int] = 1200
"""Max characters of captured stdout/stderr kept in a job report."""

LICENSE_CLIP: Final[int] = 56
"""Max characters of a license cell kept in the table view."""

NOT_PUBLISHED: Final[str] = "not published"
"""What a size field says when the catalog records 0 (no published figure)."""

GATING_NOT_CHECKED: Final[str] = "gating not checked"
"""What the gating cell says when the catalog records null (nobody looked)."""

TREE_MARK: Final[str] = "tree: "
"""Prefix on a weight file value that names a directory."""

SHARD_MARK: Final[str] = "shards: "
"""Prefix on a weight file value that names a shard set."""

KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
"""Tool id shape: kebab-case."""

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
"""Catalog ``updated`` shape: YYYY-MM-DD."""

PathLookup: TypeAlias = Callable[[str], str | None]
"""``shutil.which``-shaped PATH lookup."""

MachineLookup: TypeAlias = Callable[[], str]
"""``platform.machine``-shaped architecture lookup."""


class CatalogError(ValueError):
    """The catalog is missing, malformed, or outside the shipped schema.

    Carries the offending key in its message, so a node can print the reason
    instead of raising at Queue.
    """


class WeightRow(TypedDict):
    """One published weight artifact."""

    source: str
    repo: str
    file: str
    gb: float
    gated: bool | None


class AppRow(TypedDict):
    """The App card a row ships beside its graph."""

    mode: str
    occupancy: str
    deliverable: str


class ToolRow(TypedDict):
    """One NVIDIA lab tool as the catalog records it."""

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
    weights: list[WeightRow]
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
    app: AppRow
    gate_notes: str
    reopen: str
    verify: str
    sources: list[str]


class ReportPayload(TypedDict):
    """Comfy output-node payload carrying one STRING report."""

    ui: dict[str, tuple[str, ...]]
    result: tuple[str, ...]


class Catalog(TypedDict):
    """The whole single-source-of-truth catalog document."""

    schema: int
    tier: str
    tier_title: str
    updated: str
    status_values: list[str]
    commercial_values: list[str]
    arm64_values: list[str]
    artifact_values: list[str]
    comfy_shape_values: list[str]
    tools: list[ToolRow]


# --------------------------------------------------------------------------- #
# Catalog reading (stdlib json only; this is the container-safe reader)
# --------------------------------------------------------------------------- #


def catalog_path() -> Path:
    """Where to read the catalog from for this run.

    Returns:
        :data:`CATALOG_ENV` when set, else the catalog shipped in this pack.
    """
    raw = (os.environ.get(CATALOG_ENV) or "").strip()
    return Path(raw) if raw else DEFAULT_CATALOG_PATH


def load_catalog(path: Path | None = None) -> Catalog:
    """Read and validate the catalog from disk.

    Args:
        path: Catalog file; ``None`` uses :func:`catalog_path`.

    Returns:
        The validated document.

    Raises:
        CatalogError: The file cannot be read, is not JSON, or fails the
            schema-1 rules.
    """
    target = catalog_path() if path is None else path
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise CatalogError(f"catalog: cannot read {target}: {reason}") from exc
    return parse_catalog(text)


def parse_catalog(text: str) -> Catalog:
    """Parse and validate catalog text.

    Args:
        text: JSON document text.

    Returns:
        The validated document.

    Raises:
        CatalogError: The text is not JSON, or it fails the schema-1 rules.
    """
    try:
        parsed: Json = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CatalogError(
            f"catalog: malformed JSON at line {exc.lineno}: {exc.msg}"
        ) from exc
    if not isinstance(parsed, dict):
        raise CatalogError("catalog: top level must be a JSON object")
    return _validate_catalog(parsed)


def find_tool(catalog: Catalog, tool_id: str) -> ToolRow | None:
    """Look one row up by id.

    Args:
        catalog: Validated catalog.
        tool_id: Row id.

    Returns:
        The row, or ``None`` when no row carries that id.
    """
    for row in catalog["tools"]:
        if row["id"] == tool_id:
            return row
    return None


def _expect_keys(doc: JsonMap, required: Sequence[str], where: str) -> None:
    """Require exactly ``required`` on a parsed object.

    Args:
        doc: Parsed object.
        required: Exact key set.
        where: Path used in the message.

    Raises:
        CatalogError: A key is missing or is not in ``required``.
    """
    for key in required:
        if key not in doc:
            raise CatalogError(f"{where}.{key}: missing")
    for key in doc:
        if key not in required:
            raise CatalogError(f"{where}.{key}: unknown key")


def _str(doc: JsonMap, key: str, where: str) -> str:
    """Read a required string field.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value.

    Raises:
        CatalogError: The field is not a string.
    """
    value = doc[key]
    if not isinstance(value, str):
        raise CatalogError(f"{where}.{key}: expected a string")
    return value


def _enum(doc: JsonMap, key: str, where: str, allowed: Sequence[str]) -> str:
    """Read a required field pinned to a vocabulary.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.
        allowed: Accepted values.

    Returns:
        The field value.

    Raises:
        CatalogError: The field is not a string, or is outside ``allowed``.
    """
    value = _str(doc, key, where)
    if value not in allowed:
        raise CatalogError(f"{where}.{key}: expected one of {list(allowed)}")
    return value


def _int(doc: JsonMap, key: str, where: str) -> int:
    """Read a required integer field.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value.

    Raises:
        CatalogError: The field is not an integer.
    """
    value = doc[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogError(f"{where}.{key}: expected an integer")
    return value


def _float(doc: JsonMap, key: str, where: str) -> float:
    """Read a required number field.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value as a float.

    Raises:
        CatalogError: The field is not a number.
    """
    value = doc[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CatalogError(f"{where}.{key}: expected a number")
    return float(value)


def _bool(doc: JsonMap, key: str, where: str) -> bool:
    """Read a required boolean field.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value.

    Raises:
        CatalogError: The field is not a boolean.
    """
    value = doc[key]
    if not isinstance(value, bool):
        raise CatalogError(f"{where}.{key}: expected a boolean")
    return value


def _bool_or_none(doc: JsonMap, key: str, where: str) -> bool | None:
    """Read a required tri-state boolean field.

    ``null`` is a value of its own here, not a missing one: it records that
    nobody checked the field, which the card must not print as ``False``.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value, or ``None`` when the catalog records null.

    Raises:
        CatalogError: The field is neither a boolean nor null.
    """
    if doc[key] is None:
        return None
    return _bool(doc, key, where)


def _str_list(doc: JsonMap, key: str, where: str) -> list[str]:
    """Read a required array of strings.

    Args:
        doc: Parsed object.
        key: Field name.
        where: Path used in the message.

    Returns:
        The field value.

    Raises:
        CatalogError: The field is not an array of strings.
    """
    value = doc[key]
    if not isinstance(value, list):
        raise CatalogError(f"{where}.{key}: expected an array")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise CatalogError(f"{where}.{key}: expected only strings")
        items.append(item)
    return items


def _vocabulary(doc: JsonMap, key: str, allowed: Sequence[str]) -> list[str]:
    """Read a top-level ``*_values`` list and pin it to the shipped one.

    Args:
        doc: Parsed top level.
        key: Field name.
        allowed: The vocabulary this reader implements.

    Returns:
        The declared vocabulary.

    Raises:
        CatalogError: The declared list differs from ``allowed``.
    """
    declared = _str_list(doc, key, "catalog")
    if declared != list(allowed):
        raise CatalogError(f"catalog.{key}: expected {list(allowed)}")
    return declared


def _weights(doc: JsonMap, where: str) -> list[WeightRow]:
    """Validate a row's weights array.

    Args:
        doc: The tool row.
        where: Path used in the message.

    Returns:
        The validated weight entries.

    Raises:
        CatalogError: An entry is not an object or fails the entry schema.
    """
    raw = doc["weights"]
    if not isinstance(raw, list):
        raise CatalogError(f"{where}.weights: expected an array")
    out: list[WeightRow] = []
    for index, item in enumerate(raw):
        spot = f"{where}.weights[{index}]"
        if not isinstance(item, dict):
            raise CatalogError(f"{spot}: expected an object")
        _expect_keys(item, WEIGHT_KEYS, spot)
        out.append(
            WeightRow(
                source=_str(item, "source", spot),
                repo=_str(item, "repo", spot),
                file=_str(item, "file", spot),
                gb=_float(item, "gb", spot),
                gated=_bool_or_none(item, "gated", spot),
            )
        )
    return out


def _app(doc: JsonMap, where: str) -> AppRow:
    """Validate a row's app entry.

    Args:
        doc: The tool row.
        where: Path used in the message.

    Returns:
        The validated app entry.

    Raises:
        CatalogError: The entry is not an object, fails its schema, or names
            a GPU occupancy (this tier runs its work outside Comfy).
    """
    raw = doc["app"]
    if not isinstance(raw, dict):
        raise CatalogError(f"{where}.app: expected an object")
    _expect_keys(raw, APP_KEYS, f"{where}.app")
    occupancy = _enum(raw, "occupancy", f"{where}.app", OCCUPANCY_VALUES)
    if occupancy != "none":
        raise CatalogError(
            f"{where}.app.occupancy: expected 'none' - this tier runs outside "
            "the Comfy process"
        )
    return AppRow(
        mode=_str(raw, "mode", f"{where}.app"),
        occupancy=occupancy,
        deliverable=_str(raw, "deliverable", f"{where}.app"),
    )


def _validate_tool(doc: JsonMap, where: str) -> ToolRow:
    """Validate one tool row against the schema-1 key set and vocabularies.

    Args:
        doc: The parsed row.
        where: Path used in the message.

    Returns:
        The validated row.

    Raises:
        CatalogError: A key is missing or unknown, a value has the wrong type
            or sits outside its vocabulary, the id is not kebab-case, the
            graph does not match the id, or the row names a node this pack
            does not ship.
    """
    _expect_keys(doc, TOOL_KEYS, where)
    tool_id = _str(doc, "id", where)
    if not KEBAB_RE.match(tool_id):
        raise CatalogError(f"{where}.id: expected kebab-case")
    nodes = _str_list(doc, "nodes", where)
    for name in nodes:
        if name not in NODE_CLASS_MAPPINGS:
            raise CatalogError(f"{where}.nodes: unknown node class '{name}'")
    graph = _str(doc, "graph", where)
    if graph != f"labs/nvidia/{tool_id}":
        raise CatalogError(f"{where}.graph: expected 'labs/nvidia/{tool_id}'")
    return ToolRow(
        id=tool_id,
        title=_str(doc, "title", where),
        status=_enum(doc, "status", where, STATUS_VALUES),
        task=_str(doc, "task", where),
        input=_str(doc, "input", where),
        output=_str(doc, "output", where),
        upstream=_str(doc, "upstream", where),
        see_also=_str_list(doc, "see_also", where),
        code_license=_str(doc, "code_license", where),
        weights_license=_str(doc, "weights_license", where),
        commercial_use=_enum(doc, "commercial_use", where, COMMERCIAL_VALUES),
        weights=_weights(doc, where),
        artifact=_enum(doc, "artifact", where, ARTIFACT_VALUES),
        artifact_ref=_str(doc, "artifact_ref", where),
        arm64=_enum(doc, "arm64", where, ARM64_VALUES),
        gb10=_enum(doc, "gb10", where, GB10_VALUES),
        install=_enum(doc, "install", where, INSTALL_VALUES),
        cmd=_str(doc, "cmd", where),
        vram_gb=_int(doc, "vram_gb", where),
        disk_gb=_int(doc, "disk_gb", where),
        comfy_shape=_enum(doc, "comfy_shape", where, COMFY_SHAPE_VALUES),
        nodes=nodes,
        graph=graph,
        app=_app(doc, where),
        gate_notes=_str(doc, "gate_notes", where),
        reopen=_str(doc, "reopen", where),
        verify=_str(doc, "verify", where),
        sources=_str_list(doc, "sources", where),
    )


def _validate_catalog(doc: JsonMap) -> Catalog:
    """Validate a parsed catalog document.

    Args:
        doc: Parsed top level.

    Returns:
        The validated document.

    Raises:
        CatalogError: The schema is not 1, the tier is not this tier, a key is
            missing or unknown, or a row fails validation.
    """
    _expect_keys(doc, TOP_KEYS, "catalog")
    if _int(doc, "schema", "catalog") != SCHEMA_VERSION:
        raise CatalogError(f"catalog.schema: expected {SCHEMA_VERSION}")
    if _str(doc, "tier", "catalog") != TIER_ID:
        raise CatalogError(f"catalog.tier: expected '{TIER_ID}'")
    if not DATE_RE.match(_str(doc, "updated", "catalog")):
        raise CatalogError("catalog.updated: expected YYYY-MM-DD")
    raw_tools = doc["tools"]
    if not isinstance(raw_tools, list):
        raise CatalogError("catalog.tools: expected an array")
    tools: list[ToolRow] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_tools):
        spot = f"catalog.tools[{index}]"
        if not isinstance(item, dict):
            raise CatalogError(f"{spot}: expected an object")
        row = _validate_tool(item, spot)
        if row["id"] in seen:
            raise CatalogError(f"{spot}.id: duplicate id '{row['id']}'")
        seen.add(row["id"])
        tools.append(row)
    return Catalog(
        schema=SCHEMA_VERSION,
        tier=TIER_ID,
        tier_title=_str(doc, "tier_title", "catalog"),
        updated=_str(doc, "updated", "catalog"),
        status_values=_vocabulary(doc, "status_values", STATUS_VALUES),
        commercial_values=_vocabulary(doc, "commercial_values", COMMERCIAL_VALUES),
        arm64_values=_vocabulary(doc, "arm64_values", ARM64_VALUES),
        artifact_values=_vocabulary(doc, "artifact_values", ARTIFACT_VALUES),
        comfy_shape_values=_vocabulary(doc, "comfy_shape_values", COMFY_SHAPE_VALUES),
        tools=tools,
    )


def _read_catalog() -> tuple[Catalog | None, str]:
    """Load the catalog for one node run, degrading to a reason string.

    Returns:
        ``(catalog, "")`` when the document is good, else ``(None, reason)``.
        This never raises: a missing or malformed catalog is a node error.
    """
    try:
        return load_catalog(), ""
    except (CatalogError, OSError) as exc:
        reason = str(exc)
        _log(f"catalog error: {reason}")
        return None, reason


# --------------------------------------------------------------------------- #
# Fail-soft helpers (ez_common is lazy-imported; nothing here may raise)
# --------------------------------------------------------------------------- #


def _ensure_custom_nodes_path() -> None:
    """Put ``custom_nodes/`` on ``sys.path`` so the sibling pack imports.

    Comfy registers a directory pack by filesystem path and does not add
    ``custom_nodes/`` to ``sys.path``, so ``ez_common`` needs this first.
    """
    text = str(PACK_DIR.parent)
    try:
        from ez_common import ensure_custom_nodes_path

        ensure_custom_nodes_path(anchor=PACK_DIR)
    except Exception:  # noqa: BLE001 - ez_common is itself a sibling pack
        if text not in sys.path:
            sys.path.insert(0, text)


def _log(message: str) -> None:
    """Write one operator status line, falling back to stderr.

    Args:
        message: Status text without a trailing newline.
    """
    _ensure_custom_nodes_path()
    try:
        from ez_common import node_log

        node_log(PACK_ID, message)
    except Exception:  # noqa: BLE001 - fail-soft under pytest / bare hosts
        print(f"[{PACK_ID}] {message}", file=sys.stderr)


def _default_runner(
    argv: list[str], *, check: bool, capture_output: bool, text: bool
) -> CompletedProc:
    """Run one command with the real :mod:`subprocess` module.

    Args:
        argv: Command vector.
        check: Raise on non-zero.
        capture_output: Capture stdout/stderr.
        text: Decode as text.

    Returns:
        Completed process with ``returncode`` / ``stdout`` / ``stderr``.
    """
    return cast(
        "CompletedProc",
        subprocess.run(argv, check=check, capture_output=capture_output, text=text),
    )


def _ui(text: str) -> ReportPayload:
    """Wrap a report string in a Comfy output-node payload.

    Args:
        text: Report text.

    Returns:
        Comfy ``ui`` / ``result`` payload.
    """
    return {"ui": {"text": (text,)}, "result": (text,)}


def _clip(text: str, *, limit: int = OUTPUT_CLIP) -> str:
    """Bound captured command output.

    Args:
        text: Captured output.
        limit: Maximum characters kept from the tail.

    Returns:
        ``text``, or its tail behind an ellipsis.
    """
    if len(text) <= limit:
        return text
    return "..." + text[-limit:]


def _verdict_lines(
    title: str,
    lines: Sequence[str],
    reasons: Sequence[str],
    *,
    ok_word: str = "ready",
    bad_word: str = "blocked",
) -> str:
    """Assemble a report with its detail lines, blockers, and verdict.

    Args:
        title: First line.
        lines: Detail lines already indented.
        reasons: Blocking reasons.
        ok_word: Verdict word when nothing blocks.
        bad_word: Verdict word when something blocks.

    Returns:
        Newline-joined report ending in a verdict line.
    """
    out = [title, *lines]
    out.extend(f"  blocked: {reason}" for reason in reasons)
    out.append(f"  verdict: {ok_word if not reasons else bad_word}")
    return "\n".join(out)


def _job_lines(title: str, lines: Sequence[str], reasons: Sequence[str]) -> str:
    """A job report: :func:`_verdict_lines` with the job's verdict words.

    Args:
        title: First line.
        lines: Detail lines already indented.
        reasons: Blocking reasons.

    Returns:
        Newline-joined report ending in ``verdict: ok`` or ``verdict: refused``.
    """
    return _verdict_lines(title, lines, reasons, ok_word="ok", bad_word="refused")


def artifact_ref_reason(row: ToolRow) -> str:
    """Explain why a row's artifact ref is unusable.

    There is no network probe: the container has no egress guarantee, so
    "reachable" is the shape of the ref (a registry pull spec or a cloneable
    URL).

    Args:
        row: Validated catalog row.

    Returns:
        One ASCII sentence, or ``""`` when the ref is fine.
    """
    if row["install"] == "none":
        return ""
    ref = row["artifact_ref"].strip()
    if not ref:
        return f"install '{row['install']}' needs an artifact_ref and the row has none"
    if any(character.isspace() for character in ref):
        return f"artifact_ref '{ref}' contains whitespace"
    if row["artifact"] == CONTAINER_ARTIFACT:
        if "/" not in ref:
            return f"container ref '{ref}' is not a registry/repo pull spec"
        return ""
    if "://" not in ref:
        return f"source ref '{ref}' is not a URL to fetch"
    return ""


def render_catalog(catalog: Catalog, *, detail: str) -> str:
    """Render every row as an ASCII report.

    Args:
        catalog: Validated catalog.
        detail: ``table`` for aligned columns, ``list`` for one block per row.

    Returns:
        Newline report naming each tool, its status, and its licenses.
    """
    tools = catalog["tools"]
    head = (
        f"{catalog['tier_title']} - {len(tools)} rows "
        f"(catalog {catalog['updated']}, schema {catalog['schema']})"
    )
    if not tools:
        return f"{head}\n  (no rows)"
    if detail == "list":
        blocks: list[str] = [head]
        for row in tools:
            blocks.append("")
            blocks.extend(f"  {line}" for line in _list_block(row))
        return "\n".join(blocks)
    return "\n".join([head, *_table(tools)])


def _footprint_field(value: int, label: str) -> str:
    """Render one footprint figure for the list view.

    A catalog ``0`` is not a size: it is the pack's encoding for "upstream
    publishes no figure", so the line says that rather than printing zero,
    which an operator reads as "no download needed".

    Args:
        value: Catalog gigabytes for one axis.
        label: Which axis this is (``vram`` or ``disk``).

    Returns:
        ``"<n> GB <label>"``, or ``"<label> not published"`` for ``0``.
    """
    return f"{value} GB {label}" if value else f"{label} {NOT_PUBLISHED}"


def _weight_size_field(value: float) -> str:
    """Render one weight size for the list view.

    Args:
        value: Catalog gigabytes for one weight.

    Returns:
        ``"<n> GB"``, or :data:`NOT_PUBLISHED` for ``0``.
    """
    return f"{value:g} GB" if value else NOT_PUBLISHED


def _weight_file_field(value: str) -> str:
    """Render one weight file value as the shape it actually names.

    The catalog records three shapes in one field: a single path, a directory
    behind a trailing ``/``, and a shard set behind a ``*``. Printing all three
    as a bare path makes a tree and a shard set read like one file.

    Args:
        value: The catalog file value.

    Returns:
        The path, or the path behind :data:`TREE_MARK` / :data:`SHARD_MARK`.
    """
    if value.endswith("/"):
        return f"{TREE_MARK}{value}"
    if "*" in value:
        return f"{SHARD_MARK}{value}"
    return value


def _weight_gating_field(value: bool | None) -> str:
    """Render one weight's gating state for the list view.

    Args:
        value: ``True`` gated, ``False`` ungated, ``None`` never checked.

    Returns:
        ``"gated"``, ``"ungated"``, or :data:`GATING_NOT_CHECKED`.
    """
    if value is None:
        return GATING_NOT_CHECKED
    return "gated" if value else "ungated"


def _weights_field(weights: Sequence[WeightRow]) -> str:
    """Render the weights line of the list view.

    The wording matches the tier page, so a card read in Comfy and the same
    card read on the site say one thing about a size, a file shape, and a
    gating answer nobody checked.

    Args:
        weights: The row's weight entries.

    Returns:
        ``"0 entries"``, or ``"<n> entries: <repo>/<file> (<size>, <gating>)"``
        with one part per weight.
    """
    if not weights:
        return "0 entries"
    parts = [
        f"{weight['repo']}/{_weight_file_field(weight['file'])} "
        f"({_weight_size_field(weight['gb'])}, {_weight_gating_field(weight['gated'])})"
        for weight in weights
    ]
    noun = "entry" if len(weights) == 1 else "entries"
    return f"{len(weights)} {noun}: " + "; ".join(parts)


def _list_block(row: ToolRow) -> list[str]:
    """One row as labelled lines.

    Args:
        row: Validated catalog row.

    Returns:
        Lines without indentation.
    """
    return [
        f"{row['id']} - {row['title']}",
        f"status: {row['status']}",
        f"code license: {row['code_license']}",
        f"weights license: {row['weights_license']}",
        f"commercial use: {row['commercial_use']}",
        f"arm64: {row['arm64']}  gb10: {row['gb10']}",
        f"install: {row['install']}  artifact: {row['artifact']}",
        f"footprint: {_footprint_field(row['vram_gb'], 'vram')}, "
        f"{_footprint_field(row['disk_gb'], 'disk')}",
        f"weights: {_weights_field(row['weights'])}",
        f"graph: {row['graph']}",
    ]


TABLE_HEADERS: Final[tuple[str, ...]] = (
    "id",
    "status",
    "code license",
    "weights license",
    "commercial",
)
"""Column heads for the table view."""


def _shorten(text: str, *, limit: int = LICENSE_CLIP) -> str:
    """Keep the head of a long table cell.

    Args:
        text: Cell text.
        limit: Maximum characters kept.

    Returns:
        ``text``, or its head behind an ellipsis.
    """
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _table(tools: Sequence[ToolRow]) -> list[str]:
    """Rows as aligned columns.

    Args:
        tools: Non-empty rows.

    Returns:
        Indented header and data lines.
    """
    rows = [
        (row["id"], row["status"], _shorten(row["code_license"]),
         _shorten(row["weights_license"]), row["commercial_use"])
        for row in tools
    ]
    widths = [
        max(len(head), *(len(row[column]) for row in rows))
        for column, head in enumerate(TABLE_HEADERS)
    ]
    lines = [
        "  " + "  ".join(
            head.ljust(widths[column]) for column, head in enumerate(TABLE_HEADERS)
        ).rstrip()
    ]
    for row in rows:
        lines.append(
            "  "
            + "  ".join(
                cell.ljust(widths[column]) for column, cell in enumerate(row)
            ).rstrip()
        )
    return lines


def preflight_report(
    row: ToolRow,
    *,
    path_lookup: PathLookup = shutil.which,
    machine: MachineLookup = platform.machine,
) -> tuple[str, bool]:
    """Preflight one validated row on this host.

    Args:
        row: Validated catalog row.
        path_lookup: PATH lookup for the install verb's binary.
        machine: Architecture lookup.

    Returns:
        ``(report, ok)``. Missing upstream tooling is ``False`` plus a reason;
        this never raises.
    """
    lines: list[str] = []
    reasons: list[str] = []
    lines.append(f"  row: {row['title']} (status {row['status']})")
    if row["status"] != OPT_IN:
        reasons.append(
            f"status is '{row['status']}', not '{OPT_IN}' - this row is a card, "
            "not an install path"
        )
    arch = machine()
    lines.append(f"  host: {arch}")
    if arch != AARCH64:
        reasons.append(f"this tier targets {AARCH64}; the host reports '{arch}'")
    binary = INSTALL_BINARIES[row["install"]]
    if binary:
        found = path_lookup(binary)
        lines.append(
            f"  install {row['install']}: {binary} "
            f"{'at ' + found if found else 'not on PATH'}"
        )
        if found is None:
            reasons.append(f"{binary} is not on PATH, which {row['install']} needs")
    else:
        lines.append(f"  install {row['install']}: no external tool needed")
    ref_reason = artifact_ref_reason(row)
    lines.append(f"  artifact: {row['artifact']} ref {row['artifact_ref'] or '(none)'}")
    if ref_reason:
        reasons.append(ref_reason)
    lines.append(f"  gb10: {row['gb10']}")
    if row["gb10"] == "unsupported":
        reasons.append("upstream marks this tool unsupported on GB10")
    elif row["gb10"] == "unverified":
        lines.append("  note: no GB10 run reported upstream yet")
    lines.append(f"  graph: {row['graph']}")
    report = _verdict_lines(f"preflight {row['id']}", lines, reasons)
    return (report, not reasons)


def job_command(
    cli: Path, tool_id: str, input_path: str, params_json: str
) -> list[str]:
    """Build the operator CLI argv for one job.

    Args:
        cli: Operator CLI path.
        tool_id: Row id.
        input_path: Input file path handed to the CLI.
        params_json: JSON parameter blob handed to the CLI.

    Returns:
        Command vector for the runner.
    """
    return [
        str(cli),
        CLI_VERB,
        "run",
        tool_id,
        "--input",
        input_path,
        "--params",
        params_json,
    ]


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #


class EZNvidiaLabCatalog:
    """Print the whole NVIDIA lab tier: every row, its status, its licenses."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (the ``detail`` combo).
        """
        return {
            "required": {
                "detail": (list(DETAIL_VALUES), {"default": "table"}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("report",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Every NVIDIA lab row with its status, code license, weights license, "
        "and commercial-use verdict. table is one aligned line per row, list "
        "is a block per row with arm64, gb10, install, footprint, and graph. "
        "Reads the pack's own catalog.json with stdlib json; a missing or "
        "malformed catalog prints the reason instead of failing the Queue. "
        "Nothing is installed and nothing is downloaded."
    )

    def run(self, detail: str = "table") -> ReportPayload:
        """Render the tier report.

        Args:
            detail: ``table`` or ``list``.

        Returns:
            Comfy output-node payload carrying the report string.
        """
        choice = detail.strip().lower()
        _log(f"catalog report detail={choice or '(empty)'}")
        if choice not in DETAIL_VALUES:
            return _ui(
                f"nvidia-lab: detail must be one of {list(DETAIL_VALUES)}, "
                f"got '{detail}'"
            )
        catalog, error = _read_catalog()
        if catalog is None:
            return _ui(f"nvidia-lab catalog: {error}")
        return _ui(render_catalog(catalog, detail=choice))


class EZNvidiaLabPreflight:
    """Answer whether one NVIDIA lab row could run on this Spark today."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (the ``tool_id`` string).
        """
        return {
            "required": {
                "tool_id": ("STRING", {"default": "artifixer", "multiline": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("report", "ok")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Checks the catalog row exists, the host is aarch64, the binary the "
        "row's install verb needs is on PATH (docker for docker-pull, git for "
        "git-clone), the artifact ref is shaped like a pull spec or a clone "
        "URL, and what upstream says about GB10. Missing tooling is ok=False "
        "with a reason, never an error. Installs nothing."
    )

    def __init__(
        self,
        *,
        path_lookup: PathLookup | None = None,
        machine: MachineLookup | None = None,
    ) -> None:
        """Bind injectable host probes.

        Args:
            path_lookup: PATH lookup; ``None`` uses ``shutil.which``.
            machine: Architecture lookup; ``None`` uses
                ``platform.machine``.
        """
        self._path_lookup = path_lookup if path_lookup is not None else shutil.which
        self._machine = machine if machine is not None else platform.machine

    def run(self, tool_id: str = "") -> tuple[str, bool]:
        """Preflight one row.

        Args:
            tool_id: Catalog row id.

        Returns:
            ``(report, ok)`` - the report names every check and each blocking
            reason, and ``ok`` is False whenever a reason exists.
        """
        wanted = tool_id.strip()
        _log(f"preflight {wanted or '(no tool_id)'}")
        catalog, error = _read_catalog()
        if catalog is None:
            return (_verdict_lines(f"preflight {wanted or '(no tool_id)'}", [], [error]), False)
        if not wanted:
            return (
                _verdict_lines(
                    "preflight (no tool_id)",
                    [],
                    ["widget tool_id is empty - pick a catalog id"],
                ),
                False,
            )
        row = find_tool(catalog, wanted)
        if row is None:
            return (
                _verdict_lines(
                    f"preflight {wanted}",
                    [],
                    [f"no catalog row with id '{wanted}'"],
                ),
                False,
            )
        return preflight_report(
            row, path_lookup=self._path_lookup, machine=self._machine
        )


class EZNvidiaLabJob:
    """Run one opt-in NVIDIA lab tool through the operator CLI."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (``tool_id``, ``input_path``, ``params_json``).
        """
        return {
            "required": {
                "tool_id": ("STRING", {"default": "artifixer", "multiline": False}),
                "input_path": ("STRING", {"default": "", "multiline": False}),
                "params_json": (
                    "STRING",
                    {"default": "{}", "multiline": True, "dynamicPrompts": False},
                ),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("report", "ok")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Runs one catalog row through the operator CLI's nvidia-lab verb. "
        "Refuses any row whose status is not opt-in before anything runs, and "
        "refuses an empty or missing input path and malformed params_json. "
        "The CLI does the heavy confirm, the headroom preflight, and the "
        "occupancy XOR; this node spawns nothing of its own and touches no "
        "Compose, restart policy, or memory limit. Exit code and output tail "
        "come back as the report."
    )

    def __init__(
        self,
        *,
        runner: SubprocessRunner | None = None,
        cli_path: Path | None = None,
    ) -> None:
        """Bind the injectable process runner and CLI path.

        Args:
            runner: ``subprocess.run`` stand-in; ``None`` uses subprocess.
            cli_path: Operator CLI path; ``None`` uses the one under the
                repository root.
        """
        self._runner = runner
        self._cli_path = cli_path if cli_path is not None else DEFAULT_CLI_PATH

    def run(
        self, tool_id: str = "", input_path: str = "", params_json: str = "{}"
    ) -> tuple[str, bool]:
        """Run one row, refusing anything that is not opt-in.

        Args:
            tool_id: Catalog row id.
            input_path: Existing input file for the tool.
            params_json: JSON parameters passed through to the CLI.

        Returns:
            ``(report, ok)`` - ``ok`` is True only when the CLI exited 0.
        """
        wanted = tool_id.strip()
        source = input_path.strip()
        params = params_json.strip() or "{}"
        title = f"job {wanted or '(no tool_id)'}"
        _log(f"run {wanted or '(no tool_id)'}")
        catalog, error = _read_catalog()
        if catalog is None:
            return (_job_lines(title, [], [error]), False)
        if not wanted:
            return (
                _job_lines(
                    title, [], ["widget tool_id is empty - pick a catalog id"]
                ),
                False,
            )
        row = find_tool(catalog, wanted)
        if row is None:
            return (
                _job_lines(title, [], [f"no catalog row with id '{wanted}'"]),
                False,
            )
        if row["status"] != OPT_IN:
            return (
                _job_lines(
                    title,
                    [f"  row: {row['title']} (status {row['status']})"],
                    [
                        f"status is '{row['status']}', not '{OPT_IN}' - the tier "
                        "refuses to run a row that is not opt-in"
                    ],
                ),
                False,
            )
        if not source:
            return (
                _job_lines(title, [], ["widget input_path is empty"]),
                False,
            )
        if not Path(source).is_file():
            return (
                _job_lines(
                    title, [], [f"input_path '{source}' is not a readable file"]
                ),
                False,
            )
        try:
            json.loads(params)
        except json.JSONDecodeError as exc:
            return (
                _job_lines(
                    title,
                    [],
                    [f"params_json is not valid JSON at line {exc.lineno}: {exc.msg}"],
                ),
                False,
            )
        argv = job_command(self._cli_path, wanted, source, params)
        lines = [f"  argv: {' '.join(argv)}"]
        return self._execute(title, lines, argv)

    def _execute(
        self, title: str, lines: list[str], argv: list[str]
    ) -> tuple[str, bool]:
        """Hand one argv to the injected runner and report the result.

        Args:
            title: First report line.
            lines: Detail lines already built.
            argv: Command vector.

        Returns:
            ``(report, ok)`` - a CLI that cannot start is a reason, not a raise.
        """
        runner = self._runner if self._runner is not None else _default_runner
        try:
            proc = runner(argv, check=False, capture_output=True, text=True)
        except OSError as exc:
            reason = exc.strerror or str(exc)
            return (_job_lines(title, lines, [f"cannot start {argv[0]}: {reason}"]), False)
        details = list(lines)
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if out:
            details.append(f"  stdout: {_clip(out)}")
        if err:
            details.append(f"  stderr: {_clip(err)}")
        ok = proc.returncode == 0
        reasons: list[str] = []
        if not ok:
            reasons.append(f"{argv[0]} exited {proc.returncode}")
        return (_job_lines(title, details, reasons), ok)


class EZNvidiaLabVerdict:
    """Print why one NVIDIA lab row is off the install path, and its reopen line."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (the ``tool_id`` string).
        """
        return {
            "required": {
                "tool_id": ("STRING", {"default": "nurec-ga", "multiline": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("verdict",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "The blocking reason for one row (its gate notes) plus the sentence "
        "that says what would reopen it, and the command that re-checks it. An "
        "opt-in row says nothing blocks it. Reads the catalog only; runs "
        "nothing."
    )

    def run(self, tool_id: str = "") -> ReportPayload:
        """Report the blocking reason and the reopen sentence.

        Args:
            tool_id: Catalog row id.

        Returns:
            Comfy output-node payload carrying the verdict string.
        """
        wanted = tool_id.strip()
        _log(f"verdict {wanted or '(no tool_id)'}")
        catalog, error = _read_catalog()
        if catalog is None:
            return _ui(f"verdict {wanted or '(no tool_id)'}: {error}")
        if not wanted:
            return _ui("verdict (no tool_id): widget tool_id is empty - pick a catalog id")
        row = find_tool(catalog, wanted)
        if row is None:
            return _ui(f"verdict {wanted}: no catalog row with id '{wanted}'")
        lines = [
            f"verdict {row['id']} - {row['title']} ({row['status']})",
            f"  reason: {row['gate_notes']}"
            if row["status"] != OPT_IN
            else (
                f"  reason: nothing blocks this row - it is opt-in, install it "
                f"with the {CLI_VERB} verbs"
            ),
            f"  reopen: {row['reopen']}",
            f"  verify: {row['verify']}",
        ]
        return _ui("\n".join(lines))


# Comfy custom-node registries.
NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZNvidiaLabCatalog": EZNvidiaLabCatalog,
    "EZNvidiaLabPreflight": EZNvidiaLabPreflight,
    "EZNvidiaLabJob": EZNvidiaLabJob,
    "EZNvidiaLabVerdict": EZNvidiaLabVerdict,
}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZNvidiaLabCatalog": "NVIDIA lab catalog",
    "EZNvidiaLabPreflight": "NVIDIA lab preflight",
    "EZNvidiaLabJob": "NVIDIA lab job",
    "EZNvidiaLabVerdict": "NVIDIA lab verdict",
}

__all__ = [
    "CATEGORY",
    "EZNvidiaLabCatalog",
    "EZNvidiaLabJob",
    "EZNvidiaLabPreflight",
    "EZNvidiaLabVerdict",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
